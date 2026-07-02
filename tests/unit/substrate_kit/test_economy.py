"""Tests for the context-economy engine (economy lane B4).

Covers classification (globs / badges / the ``_unbadged`` bucket), each gauge
kind over and under its cap, inbound-reference detection (id-pattern +
filename, self-citation excluded), the TRIPLE FILTER with each blocker
exercised individually, the shadow-maturity and lock-file refusals, and a
real ``apply`` run that deletes one eligible file, writes its tombstone
shard, leaves the ineligible file untouched, and removes the lock.
"""

import os
import time
from datetime import date
from pathlib import Path

from engine.economy.engine import (
    DEFAULT_CLASSES,
    EconomyFinding,
    classify_docs,
    economy_actuate,
    economy_check,
    economy_gauges,
    inbound_references,
    issue_body,
    tombstone_line,
)
from engine.lib.config import Config


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _age(p: Path, days: float) -> None:
    """Backdate a file's mtime by ``days`` days."""
    t = time.time() - days * 86400
    os.utime(p, (t, t))


def _session(root: Path, slug: str, days_old: float, text: str = "log body\n") -> Path:
    p = root / ".sessions" / f"{slug}.md"
    _write(p, text)
    _age(p, days_old)
    return p


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def test_classify_default_sessions_by_glob(tmp_path):
    log = _session(tmp_path, "2026-06-01-a", 1)
    buckets = classify_docs(tmp_path, Config())
    assert buckets["sessions"] == [log]


def test_classify_by_badge(tmp_path):
    plan = tmp_path / "docs" / "p.md"
    living = tmp_path / "docs" / "l.md"
    _write(plan, "# P\n\n> **Status:** `plan`\n")
    _write(living, "# L\n\n> **Status:** `living-ledger`\n")
    buckets = classify_docs(tmp_path, Config())
    assert buckets["plans"] == [plan]
    assert buckets["living"] == [living]
    assert buckets["_unbadged"] == []


def test_classify_unbadged_bucket(tmp_path):
    bare = tmp_path / "docs" / "bare.md"
    _write(bare, "# No badge here\n")
    # A badged doc matching no class is NOT unbadged.
    _write(tmp_path / "docs" / "old.md", "# Old\n\n> **Status:** `historical`\n")
    buckets = classify_docs(tmp_path, Config())
    assert buckets["_unbadged"] == [bare]


def test_classify_custom_classes_override_default(tmp_path):
    cfg = Config()
    cfg.economy["classes"] = [
        {"name": "notes", "globs": ["notes/*.md"], "mode": "keep"},
    ]
    note = tmp_path / "notes" / "n.md"
    _write(note, "note\n")
    _session(tmp_path, "2026-06-01-a", 1)
    buckets = classify_docs(tmp_path, cfg)
    assert buckets["notes"] == [note]
    assert "sessions" not in buckets  # DEFAULT_CLASSES not in play


def test_classify_first_matching_class_wins(tmp_path):
    cfg = Config()
    cfg.economy["classes"] = [
        {"name": "first", "badges": ["plan"], "mode": "keep"},
        {"name": "second", "badges": ["plan"], "mode": "keep"},
    ]
    doc = tmp_path / "docs" / "p.md"
    _write(doc, "# P\n\n> **Status:** `plan`\n")
    buckets = classify_docs(tmp_path, cfg)
    assert buckets["first"] == [doc]
    assert buckets["second"] == []


def test_default_classes_shape():
    names = [c["name"] for c in DEFAULT_CLASSES]
    assert names == ["sessions", "plans", "living"]
    modes = {c["name"]: c["mode"] for c in DEFAULT_CLASSES}
    assert modes == {"sessions": "delete_tomb", "plans": "archive", "living": "keep"}


# ---------------------------------------------------------------------------
# Gauges
# ---------------------------------------------------------------------------


def test_gauge_word_cap_file_over_and_under(tmp_path):
    _write(tmp_path / "docs" / "big.md", "w " * 50)
    cfg = Config()
    cfg.economy["gauges"] = [
        {"name": "big", "kind": "word_cap", "path": "docs/big.md", "cap": 10},
    ]
    (gauge,) = economy_gauges(tmp_path, cfg)
    assert gauge["over"] is True and gauge["value"] == 50 and gauge["cap"] == 10
    cfg.economy["gauges"][0]["cap"] = 100
    (gauge,) = economy_gauges(tmp_path, cfg)
    assert gauge["over"] is False


def test_gauge_word_cap_sums_over_dir(tmp_path):
    _write(tmp_path / "docs" / "a.md", "one two three")
    _write(tmp_path / "docs" / "sub" / "b.md", "four five")
    cfg = Config()
    cfg.economy["gauges"] = [
        {"name": "docs", "kind": "word_cap", "path": "docs", "cap": 4},
    ]
    (gauge,) = economy_gauges(tmp_path, cfg)
    assert gauge["value"] == 5 and gauge["over"] is True


def test_gauge_count_cap_over_and_under(tmp_path):
    for i in range(3):
        _write(tmp_path / "docs" / f"f{i}.md", "x\n")
    cfg = Config()
    cfg.economy["gauges"] = [
        {"name": "pile", "kind": "count_cap", "glob": "docs/*.md", "cap": 2},
    ]
    (gauge,) = economy_gauges(tmp_path, cfg)
    assert gauge["value"] == 3 and gauge["over"] is True
    cfg.economy["gauges"][0]["cap"] = 5
    (gauge,) = economy_gauges(tmp_path, cfg)
    assert gauge["over"] is False


def test_gauge_route_budget_fallback_when_gauges_empty(tmp_path):
    _write(tmp_path / "docs" / "AGENT_ORIENTATION.md", "w " * 30)
    _write(tmp_path / "docs" / "current-state.md", "w " * 20)
    cfg = Config()
    cfg.orientation["budget_words"] = 40
    (gauge,) = economy_gauges(tmp_path, cfg)
    assert gauge["kind"] == "route_budget"
    assert gauge["value"] == 50 and gauge["cap"] == 40 and gauge["over"] is True
    cfg.orientation["budget_words"] = 7000
    (gauge,) = economy_gauges(tmp_path, cfg)
    assert gauge["over"] is False


def test_gauge_route_budget_uses_boot_docs_when_set(tmp_path):
    _write(tmp_path / "docs" / "boot.md", "w " * 10)
    _write(tmp_path / "docs" / "AGENT_ORIENTATION.md", "w " * 999)
    cfg = Config()
    cfg.orientation["boot_docs"] = ["boot.md"]
    (gauge,) = economy_gauges(tmp_path, cfg)
    assert gauge["value"] == 10


def test_gauge_unknown_kind_skipped(tmp_path):
    cfg = Config()
    cfg.economy["gauges"] = [{"name": "x", "kind": "mystery", "cap": 1}]
    assert economy_gauges(tmp_path, cfg) == []


# ---------------------------------------------------------------------------
# Inbound references
# ---------------------------------------------------------------------------


def test_inbound_ref_by_id_pattern(tmp_path):
    target = tmp_path / "docs" / "Q-0123-widget.md"
    _write(target, "# Widget decision\n")
    _write(tmp_path / "docs" / "citer.md", "See Q-0123 for the ruling.\n")
    refs = inbound_references(tmp_path, Config(), [target])
    assert refs["docs/Q-0123-widget.md"] == ["docs/citer.md"]


def test_inbound_ref_by_filename_stem(tmp_path):
    target = _session(tmp_path, "2026-06-01-fix", 1)
    _write(tmp_path / "docs" / "ledger.md", "Shipped in 2026-06-01-fix session.\n")
    refs = inbound_references(tmp_path, Config(), [target])
    assert refs[".sessions/2026-06-01-fix.md"] == ["docs/ledger.md"]


def test_inbound_ref_self_citation_excluded(tmp_path):
    target = tmp_path / "docs" / "self.md"
    _write(target, "# self\n\nThis file mentions self by its own stem.\n")
    refs = inbound_references(tmp_path, Config(), [target])
    assert refs["docs/self.md"] == []


def test_inbound_ref_scans_reference_roots(tmp_path):
    target = _session(tmp_path, "2026-06-01-fix", 1)
    _write(tmp_path / "scripts" / "tool.py", "# see 2026-06-01-fix\n")
    cfg = Config()
    cfg.economy["reference_roots"] = ["scripts"]
    refs = inbound_references(tmp_path, cfg, [target])
    assert refs[".sessions/2026-06-01-fix.md"] == ["scripts/tool.py"]
    # Without the reference root the citation is invisible.
    assert inbound_references(tmp_path, Config(), [target])[
        ".sessions/2026-06-01-fix.md"
    ] == []


# ---------------------------------------------------------------------------
# economy_check — census, findings, debt, triple filter
# ---------------------------------------------------------------------------


def test_check_census_and_unbadged_finding(tmp_path):
    _write(tmp_path / "docs" / "bare.md", "one two three\n")
    report = economy_check(tmp_path, Config())
    assert report["census"]["_unbadged"] == {"files": 1, "words": 3}
    kinds = [f.kind for f in report["findings"]]
    assert kinds.count("unbadged") == 1


def test_check_over_cap_finding(tmp_path):
    _write(tmp_path / "docs" / "AGENT_ORIENTATION.md", "w " * 10)
    cfg = Config()
    cfg.orientation["budget_words"] = 5
    report = economy_check(tmp_path, cfg)
    over = [f for f in report["findings"] if f.kind == "over_cap"]
    assert len(over) == 1 and over[0].path == "route_budget"


def test_check_expired_finding_and_debt(tmp_path):
    _session(tmp_path, "2026-01-01-old", 30)
    _session(tmp_path, "2026-06-30-new", 1)
    report = economy_check(tmp_path, Config())
    expired = [f for f in report["findings"] if f.kind == "expired"]
    assert [f.path for f in expired] == [".sessions/2026-01-01-old.md"]
    assert report["debt"] == 1


def test_triple_filter_all_pass_is_eligible(tmp_path):
    _session(tmp_path, "2026-01-01-old", 30)
    report = economy_check(tmp_path, Config(), harvested={"2026-01-01-old"})
    (row,) = report["would_act"]
    assert row["action"] == "delete"
    assert row["eligible"] is True and row["blockers"] == []


def test_triple_filter_blocker_not_harvested(tmp_path):
    _session(tmp_path, "2026-01-01-old", 30)
    report = economy_check(tmp_path, Config())
    (row,) = report["would_act"]
    assert row["eligible"] is False and row["blockers"] == ["not harvested"]


def test_triple_filter_blocker_window_not_reached(tmp_path):
    _session(tmp_path, "2026-06-30-new", 1)
    report = economy_check(tmp_path, Config(), harvested={"2026-06-30-new"})
    (row,) = report["would_act"]
    assert row["eligible"] is False and row["blockers"] == ["window not reached"]


def test_triple_filter_blocker_inbound_refs(tmp_path):
    _session(tmp_path, "2026-01-01-old", 30)
    _write(tmp_path / "docs" / "cite.md", "history: 2026-01-01-old\n")
    report = economy_check(tmp_path, Config(), harvested={"2026-01-01-old"})
    (row,) = report["would_act"]
    assert row["eligible"] is False and row["blockers"] == ["inbound refs: 1"]
    with_refs = [f for f in report["findings"] if f.kind == "delete_with_refs"]
    assert [f.path for f in with_refs] == [".sessions/2026-01-01-old.md"]


def test_archive_class_rows_gate_on_window_only(tmp_path):
    old = tmp_path / "docs" / "old-plan.md"
    _write(old, "# Old plan\n\n> **Status:** `plan`\n")
    _age(old, 90)
    fresh = tmp_path / "docs" / "new-plan.md"
    _write(fresh, "# New plan\n\n> **Status:** `plan`\n")
    report = economy_check(tmp_path, Config())
    rows = {r["path"]: r for r in report["would_act"] if r["action"] == "archive"}
    assert rows["docs/old-plan.md"]["eligible"] is True
    assert rows["docs/new-plan.md"]["blockers"] == ["window not reached"]


# ---------------------------------------------------------------------------
# economy_actuate — dry run, refusals, real apply
# ---------------------------------------------------------------------------


def test_actuate_dry_run_touches_nothing(tmp_path):
    log = _session(tmp_path, "2026-01-01-old", 30)
    report = economy_check(tmp_path, Config(), harvested={"2026-01-01-old"})
    lines = economy_actuate(tmp_path, Config(), report)
    assert lines == [
        "would delete .sessions/2026-01-01-old.md (class 'sessions' (14d window))",
    ]
    assert log.exists()


def test_actuate_apply_refused_in_shadow_maturity(tmp_path):
    log = _session(tmp_path, "2026-01-01-old", 30)
    cfg = Config()  # maturity defaults to "shadow"
    report = economy_check(tmp_path, cfg, harvested={"2026-01-01-old"})
    lines = economy_actuate(tmp_path, cfg, report, apply=True)
    assert len(lines) == 1 and "refused" in lines[0] and "shadow" in lines[0]
    assert log.exists()


def test_actuate_apply_refused_when_lock_exists(tmp_path):
    log = _session(tmp_path, "2026-01-01-old", 30)
    cfg = Config()
    cfg.economy["maturity"] = "normal"
    lock = tmp_path / cfg.state_dir / "economy.lock"
    _write(lock, "held\n")
    report = economy_check(tmp_path, cfg, harvested={"2026-01-01-old"})
    lines = economy_actuate(tmp_path, cfg, report, apply=True)
    assert len(lines) == 1 and "economy.lock" in lines[0]
    assert log.exists()
    assert lock.exists()  # a pre-existing lock is never stolen


def test_actuate_real_apply_deletes_tombstones_and_unlocks(tmp_path):
    eligible = _session(tmp_path, "2026-01-01-old", 30, "# Old work log\n\nbody\n")
    ineligible = _session(tmp_path, "2026-06-30-new", 1)
    cfg = Config()
    cfg.economy["maturity"] = "normal"
    report = economy_check(
        tmp_path,
        cfg,
        harvested={"2026-01-01-old", "2026-06-30-new"},
    )
    lines = economy_actuate(tmp_path, cfg, report, apply=True)
    assert not eligible.exists()
    assert ineligible.exists()
    band = date.today().strftime("%Y%m")
    shard = tmp_path / ".sessions" / "pruned" / f"band-{band}.md"
    assert shard.exists()
    text = shard.read_text(encoding="utf-8")
    assert text.startswith("# Tombstones")  # dated banner header
    assert "2026-01-01-old" in text and "Old work log" in text
    assert not (tmp_path / cfg.state_dir / "economy.lock").exists()
    assert any(line.startswith("deleted") for line in lines)
    assert any("hold .sessions/2026-06-30-new.md" in line for line in lines)


def test_actuate_apply_appends_to_existing_shard(tmp_path):
    _session(tmp_path, "2026-01-01-a", 30)
    _session(tmp_path, "2026-01-02-b", 30)
    cfg = Config()
    cfg.economy["maturity"] = "normal"
    report = economy_check(tmp_path, cfg, harvested={"2026-01-01-a", "2026-01-02-b"})
    economy_actuate(tmp_path, cfg, report, apply=True)
    band = date.today().strftime("%Y%m")
    text = (tmp_path / ".sessions" / "pruned" / f"band-{band}.md").read_text(
        encoding="utf-8",
    )
    assert text.count("# Tombstones") == 1  # one banner, both lines appended
    assert "2026-01-01-a" in text and "2026-01-02-b" in text


# ---------------------------------------------------------------------------
# Tombstone line + issue body
# ---------------------------------------------------------------------------


def test_tombstone_line_format():
    line = tombstone_line(Path(".sessions/2026-01-01-old.md"), "Old work log")
    today = date.today().isoformat()
    assert line == (
        f"- 2026-01-01-old - {today} - .sessions/2026-01-01-old.md - Old work log"
    )


def test_tombstone_line_truncates_long_summaries():
    line = tombstone_line(Path("a.md"), "w " * 40)
    assert len(line.split()) <= 20


def test_issue_body_carries_census_debt_and_rows(tmp_path):
    _session(tmp_path, "2026-01-01-old", 30)
    report = economy_check(tmp_path, Config())
    body = issue_body(report)
    assert "## Context-economy retention debt" in body
    assert "**Debt (expired files): 1**" in body
    assert "| sessions | 1 |" in body
    assert "hold .sessions/2026-01-01-old.md: not harvested" in body


def test_economy_finding_is_a_named_triple():
    f = EconomyFinding("p.md", "expired", "msg")
    assert (f.path, f.kind, f.message) == ("p.md", "expired", "msg")
