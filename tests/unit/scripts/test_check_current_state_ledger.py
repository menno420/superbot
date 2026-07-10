"""Tests for ``scripts/check_current_state_ledger.py`` — the ledger drift guard."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = REPO_ROOT / "scripts" / "check_current_state_ledger.py"

_spec = importlib.util.spec_from_file_location("check_current_state_ledger", _MOD)
assert _spec and _spec.loader
csl = importlib.util.module_from_spec(_spec)
sys.modules["check_current_state_ledger"] = csl
_spec.loader.exec_module(csl)


def test_standalone_refs() -> None:
    nums = csl.ledger_pr_numbers("shipped **#730** and PR #733, also (#729)")
    assert {729, 730, 733} <= nums


def test_range_expansion_en_dash() -> None:
    nums = csl.ledger_pr_numbers("- **#715–#723** the map set")
    assert {715, 716, 717, 718, 719, 720, 721, 722, 723} <= nums
    assert 724 not in nums


def test_range_expansion_hyphen_and_bare_hi() -> None:
    assert {685, 686, 698} <= csl.ledger_pr_numbers("#685-#698")
    assert {700, 701, 702} <= csl.ledger_pr_numbers("#700–702")


def test_absurd_range_is_ignored() -> None:
    # A stray "#1–#9999" must not balloon into thousands of entries.
    nums = csl.ledger_pr_numbers("#1–#9999")
    assert 5000 not in nums


def test_merge_subject_extraction(monkeypatch) -> None:
    subjects = "\n".join(
        [
            "Merge pull request #734 from menno420/branch",
            "fix: something (#733)",
            "chore: no pr number here",
            "Merge pull request #730 from menno420/other",
            # The MCP merge style ("Merge PR #N: title") — five real merges
            # went invisible to this check before the 2026-06-12 regex fix.
            "Merge PR #762: UX Lab PR C — mock studio",
            # A cross-repo PR reference inside an ordinary branch-commit subject
            # (reaches main via a true merge commit) must NOT read as a landing —
            # the 2026-07-10 phantom-"#104" false-red.
            "docs: never-ask ruling (superbot-next ORDER 010, PR #104); pkg updated",
        ]
    )

    class _R:
        returncode = 0
        stdout = subjects

    monkeypatch.setattr(csl.subprocess, "run", lambda *a, **k: _R())
    nums = csl._git_merged_pr_numbers(10)
    assert nums == [734, 733, 730, 762]  # order preserved, de-duped, non-PR skipped


def test_merge_subject_map(monkeypatch) -> None:
    subjects = "\n".join(
        [
            "Merge pull request #734 from menno420/branch",
            "Merge PR #762: UX Lab PR C — mock studio",
            "chore: no pr number here",
            # A second, older subject for #734 must NOT overwrite the newest one.
            "Merge pull request #734 from menno420/dup",
        ]
    )

    class _R:
        returncode = 0
        stdout = subjects

    monkeypatch.setattr(csl.subprocess, "run", lambda *a, **k: _R())
    mapping = csl._git_merged_pr_map(10)
    assert mapping == {
        734: "Merge pull request #734 from menno420/branch",
        762: "Merge PR #762: UX Lab PR C — mock studio",
    }
    # The number list derives from the map, order preserved.
    assert csl._git_merged_pr_numbers(10) == [734, 762]


def test_main_prints_missing_pr_subjects(monkeypatch, capsys) -> None:
    monkeypatch.setattr(csl, "find_missing", lambda window: [814, 999])
    monkeypatch.setattr(
        csl,
        "_git_merged_pr_map",
        lambda limit: {814: "Merge PR #814: ci — cut code-quality cost"},
    )
    assert csl.main([]) == 0
    out = capsys.readouterr().out
    # The known PR shows its merge subject; an unmapped one degrades gracefully.
    assert "#814  Merge PR #814: ci — cut code-quality cost" in out
    assert "#999  (no merge commit found — closed/unmerged?)" in out


def test_find_missing_flags_unlisted(monkeypatch) -> None:
    monkeypatch.setattr(
        csl,
        "_git_merged_pr_map",
        lambda limit: {
            734: "Merge pull request #734 from menno420/feat-x",
            733: "",
            730: "",
        },
    )
    monkeypatch.setattr(csl, "known_ledger_numbers", lambda: {733, 730})
    assert csl.find_missing(window=15) == [734]


def test_find_missing_empty_when_all_present(monkeypatch) -> None:
    monkeypatch.setattr(csl, "_git_merged_pr_map", lambda limit: {733: "", 730: ""})
    monkeypatch.setattr(csl, "known_ledger_numbers", lambda: {730, 733})
    assert csl.find_missing() == []


def test_is_reconciliation_subject() -> None:
    # Every form the reconciliation routine ships: GitHub-web branch-name merge, the MCP
    # title styles, and a ledger-reconcile branch.
    assert csl._is_reconciliation_subject(
        "Merge pull request #942 from menno420/claude/ledger-reconcile-932-939"
    )
    assert csl._is_reconciliation_subject(
        "docs(current-state): reconcile ledger — add #932"
    )
    assert csl._is_reconciliation_subject(
        "docs reconciliation (band-#930, ninth Q-0107 pass)"
    )
    # A plain "ledger" feature PR must NOT be exempted (command-surface-ledger, settings parity…).
    assert not csl._is_reconciliation_subject(
        "Merge pull request #918 from menno420/claude/command-surface-ledger"
    )
    assert not csl._is_reconciliation_subject(
        "feat(ai): deterministic BTD6 cost-comparison floor"
    )


def test_find_missing_exempts_self_referential_reconciliation_pr(monkeypatch) -> None:
    # A reconcile PR cannot list its own number, so its absence is expected, not drift —
    # only the real feature PR is flagged. (Q-0151)
    monkeypatch.setattr(
        csl,
        "_git_merged_pr_map",
        lambda limit: {
            950: "Merge pull request #950 from menno420/claude/btd6-difficulty-cost",
            942: "Merge pull request #942 from menno420/claude/ledger-reconcile-932-939",
        },
    )
    monkeypatch.setattr(csl, "known_ledger_numbers", lambda: set())
    assert csl.find_missing(window=15) == [950]  # 942 exempt


def test_range_in_recently_shipped_covers_member() -> None:
    cs = "## Recently shipped\n- **#715–#723** the map set"
    assert 719 in csl.known_ledger_numbers(current_state_text=cs, archive_text="")


def test_planning_range_in_next_action_does_not_mask_band() -> None:
    # The band-#800 false-green: a forward-looking range *above* ## Recently shipped
    # must NOT mark its interior present (only its endpoints match as bare #N refs).
    cs = (
        "> ▶ Next action — the band #900–#919 decade queue\n\n"
        "## Recently shipped\n- nothing here yet"
    )
    known = csl.known_ledger_numbers(current_state_text=cs, archive_text="")
    assert 905 not in known  # interior no longer masked
    assert 910 not in known


def test_range_in_archive_covers_member() -> None:
    assert 719 in csl.known_ledger_numbers(
        current_state_text="## Recently shipped\n", archive_text="- **#715–#723**"
    )


def test_strict_exit_code(monkeypatch) -> None:
    # 999 is at/under any current/future marker → real drift → strict fails.
    monkeypatch.setattr(csl, "find_missing", lambda window: [999])
    assert csl.main(["--strict"]) == 1
    assert csl.main([]) == 0  # advisory default never fails


# --- marker / lag-vs-drift (ledger-guard-benign-lag + window-scale ideas) ---


def test_marker_pr_parses() -> None:
    txt = "> **Last reconciliation pass:** PR #1094 (2026-06-19, thirteenth pass)"
    assert csl.marker_pr(current_state_text=txt) == 1094
    assert csl.marker_pr(current_state_text="no marker on this line") is None


def test_classify_missing_splits_on_marker() -> None:
    drift, lag = csl.classify_missing([990, 1005, 1000, 1010], marker=1000)
    assert drift == [990, 1000]  # at/under the marker = real drift
    assert lag == [1005, 1010]  # newer than the marker = benign lag


def test_classify_missing_no_marker_is_all_drift() -> None:
    # No parseable marker → conservative: treat everything as drift (prior behaviour).
    assert csl.classify_missing([1, 2, 3], marker=None) == ([1, 2, 3], [])


def test_band_window_floors_and_scales(monkeypatch) -> None:
    monkeypatch.setattr(
        csl,
        "_git_merged_pr_map",
        lambda limit: {n: "" for n in range(1001, 1031)},  # 30 merges, all > marker
    )
    assert csl.band_window(1000) == 30  # scales to the band
    assert csl.band_window(1025) == csl.DEFAULT_WINDOW  # small band → 15 floor
    assert csl.band_window(None) == csl.DEFAULT_WINDOW  # no marker → 15


def test_strict_passes_on_benign_lag_only(monkeypatch) -> None:
    # The core win: PRs newer than the marker are benign lag → --strict must NOT fail.
    monkeypatch.setattr(csl, "marker_pr", lambda *a, **k: 1000)
    monkeypatch.setattr(csl, "find_missing", lambda window: [1005, 1006])
    monkeypatch.setattr(csl, "_git_merged_pr_map", lambda limit: {1005: "a", 1006: "b"})
    assert csl.main(["--strict"]) == 0


def test_strict_fails_on_real_drift_below_marker(monkeypatch) -> None:
    monkeypatch.setattr(csl, "marker_pr", lambda *a, **k: 1000)
    monkeypatch.setattr(csl, "find_missing", lambda window: [990])
    monkeypatch.setattr(csl, "_git_merged_pr_map", lambda limit: {990: "old feature"})
    assert csl.main(["--strict"]) == 1


def test_benign_lag_is_still_printed(monkeypatch, capsys) -> None:
    # Lag never fails strict, but it IS printed so the reconciliation routine reads the band.
    monkeypatch.setattr(csl, "marker_pr", lambda *a, **k: 1000)
    monkeypatch.setattr(csl, "find_missing", lambda window: [1005])
    monkeypatch.setattr(
        csl, "_git_merged_pr_map", lambda limit: {1005: "Merge PR #1005: x"}
    )
    assert csl.main([]) == 0
    out = capsys.readouterr().out
    assert "benign lag" in out and "#1005  Merge PR #1005: x" in out
