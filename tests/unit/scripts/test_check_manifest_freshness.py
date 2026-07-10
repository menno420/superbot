"""Tests for scripts/check_manifest_freshness.py — the fleet-manifest staleness checker.

The pure halves (manifest-row parsing, status-header parsing, verdict
classification) run on inline fixtures plus the real committed manifest; the
git-transport half (``fetch_lane_state``) is exercised against *local* fixture
repos by repointing ``_repo_url`` — no test touches the network. Fail-open is
pinned: a row whose every fetch fails is SKIP and never fails ``--strict``.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "scripts" / "check_manifest_freshness.py"
_MANIFEST = _REPO / "docs" / "eap" / "fleet-manifest.md"


def _load():
    spec = importlib.util.spec_from_file_location("check_manifest_freshness_ut", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass introspects the owning module via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mod():
    return _load()


SAMPLE_TABLE = """\
# Fleet manifest

| Project | Repo(s) | Model | Routine cadence | Last-seen | Notes |
|---|---|---|---|---|---|
| **alpha** | owner/alpha-repo (home; prose) | — | daily | 2026-07-09 (seeded) | notes |
| beta | owner/shared · owner/beta-extra | default | hourly | 2026-07-10 | see docs/x.md |
| gamma | owner/shared | default | planned | 2026-07-08 | second row on shared |
| no-repo-row | (repo pending) | — | planned | 2026-07-09 | skipped: no token |
| no-date-row | owner/nodate | — | planned | soon | kept: SKIP verdict |
"""


# ---------------------------------------------------------------- parsing


def test_parse_manifest_rows_sample(mod):
    rows = mod.parse_manifest_rows(SAMPLE_TABLE)
    by_project = {r.project: r for r in rows}
    # header/separator and the token-less row are skipped; bold is stripped
    assert set(by_project) == {"alpha", "beta", "gamma", "no-date-row"}
    assert by_project["alpha"].repos == ("owner/alpha-repo",)
    assert by_project["alpha"].last_seen == date(2026, 7, 9)
    # multi-repo cell keeps declaration order, deduped
    assert by_project["beta"].repos == ("owner/shared", "owner/beta-extra")
    assert by_project["no-date-row"].last_seen is None


def test_parse_committed_manifest(mod):
    """The real docs/eap/fleet-manifest.md parses: every row has repos + a date."""
    rows = mod.parse_manifest_rows(_MANIFEST.read_text(encoding="utf-8"))
    assert len(rows) >= 6  # the six core lanes at minimum
    projects = {r.project for r in rows}
    assert "manager" in projects
    assert "kit-lab" in projects
    for row in rows:
        assert row.repos, f"row {row.project!r} parsed without repos"
        assert row.last_seen is not None, f"row {row.project!r} has no Last-seen date"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("updated: 2026-07-09T18:55:00Z\n", datetime(2026, 7, 9, 18, 55, tzinfo=timezone.utc)),
        (
            "# head\nupdated: 2026-07-10T03:26:55+02:00\n",
            datetime.fromisoformat("2026-07-10T03:26:55+02:00"),
        ),
        # naive timestamps are pinned to UTC
        ("updated: 2026-07-09T12:00:00\n", datetime(2026, 7, 9, 12, 0, tzinfo=timezone.utc)),
        ("no header here\n", None),
        ("updated: not-a-date\n", None),
    ],
)
def test_parse_status_updated(mod, text, expected):
    assert mod.parse_status_updated(text) == expected


def test_parse_status_updated_mid_document(mod):
    """The header needn't be line 1 (venture-lab carries it at line 8)."""
    text = "# title\n\n> blurb\n\n---\n\nupdated: 2026-07-10T03:26:55Z\nstatus: green\n"
    got = mod.parse_status_updated(text)
    assert got == datetime(2026, 7, 10, 3, 26, 55, tzinfo=timezone.utc)


# ---------------------------------------------------------------- classify


def _row(mod, last_seen, project="p"):
    return mod.ManifestRow(project, ("o/r",), last_seen, 1)


def _state(mod, updated, from_status=True, error=None, repo="o/r"):
    return mod.LaneState(repo=repo, updated=updated, from_status=from_status, error=error)


def test_classify_stale_fresh_sameday(mod):
    row = _row(mod, date(2026, 7, 9))
    later = _state(mod, datetime(2026, 7, 10, 1, 0, tzinfo=timezone.utc))
    same_day = _state(mod, datetime(2026, 7, 9, 23, 59, tzinfo=timezone.utc))
    earlier = _state(mod, datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc))
    assert mod.classify(row, [later]).verdict == mod.STALE
    assert mod.classify(row, [same_day]).verdict == mod.FRESH  # day precision
    assert mod.classify(row, [earlier]).verdict == mod.FRESH


def test_classify_head_fallback_is_drift_not_stale(mod):
    row = _row(mod, date(2026, 7, 9))
    head_only = _state(mod, datetime(2026, 7, 10, tzinfo=timezone.utc), from_status=False)
    v = mod.classify(row, [head_only])
    assert v.verdict == mod.DRIFT
    assert "activity signal" in v.detail


def test_classify_status_outranks_head(mod):
    """A fresh status.md beats a newer HEAD-only sibling (superbot's own churn)."""
    row = _row(mod, date(2026, 7, 9))
    fresh_status = _state(mod, datetime(2026, 7, 9, tzinfo=timezone.utc))
    newer_head = _state(
        mod, datetime(2026, 7, 10, tzinfo=timezone.utc), from_status=False, repo="o/other"
    )
    assert mod.classify(row, [fresh_status, newer_head]).verdict == mod.FRESH


def test_classify_skips(mod):
    all_failed = _state(mod, None, error="boom")
    assert mod.classify(_row(mod, date(2026, 7, 9)), [all_failed]).verdict == mod.SKIP
    ok = _state(mod, datetime(2026, 7, 9, tzinfo=timezone.utc))
    assert mod.classify(_row(mod, None), [ok]).verdict == mod.SKIP  # no Last-seen


# ---------------------------------------------------------------- git transport (local fixtures)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env={
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": str(cwd),
        },
    )


@pytest.fixture()
def fixture_repos(tmp_path):
    """Two local repos: one with control/status.md, one without."""
    with_status = tmp_path / "with-status"
    (with_status / "control").mkdir(parents=True)
    (with_status / "control" / "status.md").write_text(
        "# lane · status\nupdated: 2026-07-10T03:00:00Z\nhealth: green\n", encoding="utf-8"
    )
    _git(with_status, "init", "-q")
    _git(with_status, "add", "-A")
    _git(with_status, "commit", "-q", "-m", "seed")

    without_status = tmp_path / "without-status"
    without_status.mkdir()
    (without_status / "README.md").write_text("hi\n", encoding="utf-8")
    _git(without_status, "init", "-q")
    _git(without_status, "add", "-A")
    _git(without_status, "commit", "-q", "-m", "seed")
    return {"o/with-status": with_status, "o/without-status": without_status}


def test_fetch_lane_state_local(mod, fixture_repos, monkeypatch):
    monkeypatch.setattr(mod, "_repo_url", lambda repo: str(fixture_repos[repo]))

    got = mod.fetch_lane_state("o/with-status")
    assert got.from_status is True
    assert got.error is None
    assert got.updated == datetime(2026, 7, 10, 3, 0, tzinfo=timezone.utc)

    fallback = mod.fetch_lane_state("o/without-status")
    assert fallback.from_status is False
    assert fallback.updated is not None  # HEAD committer date


def test_fetch_lane_state_unreachable_is_fail_open(mod, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_repo_url", lambda repo: str(tmp_path / "nope"))
    got = mod.fetch_lane_state("o/gone")
    assert got.updated is None
    assert got.error  # captured, not raised


# ---------------------------------------------------------------- check_manifest / main


def _fake_fetcher(states: dict):
    calls: list[str] = []

    def fetch(repo: str, timeout: int = 60):
        calls.append(repo)
        return states[repo]

    fetch.calls = calls  # type: ignore[attr-defined]
    return fetch


def test_check_manifest_dedups_shared_repo(mod, tmp_path):
    manifest = tmp_path / "m.md"
    manifest.write_text(SAMPLE_TABLE, encoding="utf-8")
    states = {
        "owner/alpha-repo": _state(mod, datetime(2026, 7, 9, tzinfo=timezone.utc)),
        "owner/shared": _state(mod, datetime(2026, 7, 11, tzinfo=timezone.utc)),
        "owner/beta-extra": _state(mod, None, error="down"),
        "owner/nodate": _state(mod, datetime(2026, 7, 9, tzinfo=timezone.utc)),
    }
    fetch = _fake_fetcher(states)
    verdicts = {v.row.project: v.verdict for v in mod.check_manifest(manifest, fetcher=fetch)}
    assert verdicts == {
        "alpha": mod.FRESH,
        "beta": mod.STALE,  # shared moved 07-11 > 07-10
        "gamma": mod.STALE,  # same shared state, cached
        "no-date-row": mod.SKIP,
    }
    assert fetch.calls.count("owner/shared") == 1  # cached across rows


def test_check_manifest_only_filter(mod, tmp_path):
    manifest = tmp_path / "m.md"
    manifest.write_text(SAMPLE_TABLE, encoding="utf-8")
    states = {"owner/alpha-repo": _state(mod, datetime(2026, 7, 9, tzinfo=timezone.utc))}
    got = mod.check_manifest(manifest, only="ALPH", fetcher=_fake_fetcher(states))
    assert [v.row.project for v in got] == ["alpha"]


def test_main_strict_exit_codes(mod, tmp_path, monkeypatch, capsys):
    manifest = tmp_path / "m.md"
    manifest.write_text(SAMPLE_TABLE, encoding="utf-8")
    states = {
        "owner/alpha-repo": _state(mod, datetime(2026, 7, 12, tzinfo=timezone.utc)),
        "owner/shared": _state(mod, None, error="offline"),
        "owner/beta-extra": _state(mod, None, error="offline"),
        "owner/nodate": _state(mod, None, error="offline"),
    }
    monkeypatch.setattr(mod, "fetch_lane_state", _fake_fetcher(states))

    assert mod.main(["--manifest", str(manifest)]) == 0  # advisory default
    assert mod.main(["--manifest", str(manifest), "--strict"]) == 1  # alpha STALE
    out = capsys.readouterr().out
    assert "STALE" in out and "re-stamp" in out

    # strict + only-unreachable rows (fail-open): SKIPs never red a session
    assert mod.main(["--manifest", str(manifest), "--strict", "--only", "beta"]) == 0


def test_main_missing_manifest_is_skip(mod, tmp_path, capsys):
    assert mod.main(["--manifest", str(tmp_path / "absent.md")]) == 0
    assert "SKIP" in capsys.readouterr().out


def test_main_drift_never_fails_strict(mod, tmp_path, monkeypatch):
    manifest = tmp_path / "m.md"
    manifest.write_text(
        "| Project | Repo(s) | Model | Routine cadence | Last-seen | Notes |\n"
        "|---|---|---|---|---|---|\n"
        "| solo | owner/headonly | — | daily | 2026-07-01 | n |\n",
        encoding="utf-8",
    )
    states = {
        "owner/headonly": _state(
            mod, datetime(2026, 7, 12, tzinfo=timezone.utc), from_status=False
        )
    }
    monkeypatch.setattr(mod, "fetch_lane_state", _fake_fetcher(states))
    assert mod.main(["--manifest", str(manifest), "--strict"]) == 0  # DRIFT ≠ STALE
