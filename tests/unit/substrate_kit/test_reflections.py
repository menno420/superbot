"""Tests for the reflection buffer (loop lane B2).

Covers id monotonicity, overflow-pruning order, supersede skipping in
``active_lessons``, provisional flagging in the orientation block, corrupt-JSON
fail-open, and the deterministic session-log miner.
"""

import datetime
import json
import os
from pathlib import Path

from engine.loop.reflections import (
    REFLECTIONS_FILENAME,
    active_lessons,
    add_reflection,
    lessons_block,
    load_reflections,
    mine_reflections,
    supersede_reflection,
)


def _buf(tmp_path: Path) -> Path:
    return tmp_path / REFLECTIONS_FILENAME


def _add(path: Path, n: int, **kwargs) -> dict:
    return add_reflection(
        path,
        lesson=f"lesson {n}",
        evidence=f"log-{n}.md:L1",
        tags=["idea"],
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Load — fail open
# ---------------------------------------------------------------------------


def test_load_absent_returns_empty(tmp_path):
    assert load_reflections(_buf(tmp_path)) == []


def test_load_corrupt_json_returns_empty(tmp_path):
    _buf(tmp_path).write_text("{ not json at all", encoding="utf-8")
    assert load_reflections(_buf(tmp_path)) == []


def test_load_non_list_document_returns_empty(tmp_path):
    _buf(tmp_path).write_text('{"id": "R-0001"}', encoding="utf-8")
    assert load_reflections(_buf(tmp_path)) == []


# ---------------------------------------------------------------------------
# Add — ids, date stamp, status
# ---------------------------------------------------------------------------


def test_add_assigns_monotonic_ids(tmp_path):
    path = _buf(tmp_path)
    ids = [_add(path, n)["id"] for n in range(3)]
    assert ids == ["R-0001", "R-0002", "R-0003"]


def test_add_ids_stay_monotonic_after_prune(tmp_path):
    path = _buf(tmp_path)
    for n in range(3):
        _add(path, n, buffer_size=2)
    # R-0001 was pruned, but the counter never reuses its number.
    assert [e["id"] for e in load_reflections(path)] == ["R-0002", "R-0003"]
    assert _add(path, 3, buffer_size=2)["id"] == "R-0004"


def test_add_stamps_today_and_default_status(tmp_path):
    entry = _add(_buf(tmp_path), 0)
    assert entry["date"] == datetime.date.today().isoformat()
    assert entry["status"] == "provisional"
    assert entry["lesson"] == "lesson 0"
    assert entry["tags"] == ["idea"]


def test_add_accepts_confirmed_status(tmp_path):
    entry = _add(_buf(tmp_path), 0, status="confirmed")
    assert entry["status"] == "confirmed"


def test_add_recovers_from_corrupt_file(tmp_path):
    path = _buf(tmp_path)
    path.write_text("not json", encoding="utf-8")
    assert _add(path, 0)["id"] == "R-0001"
    assert len(load_reflections(path)) == 1


# ---------------------------------------------------------------------------
# Pruning order
# ---------------------------------------------------------------------------


def test_prune_drops_oldest_inactive_first(tmp_path):
    path = _buf(tmp_path)
    for n in range(3):
        _add(path, n, buffer_size=10)
    assert supersede_reflection(path, "R-0002", "R-0003")
    _add(path, 3, buffer_size=3)
    # R-0002 (superseded) goes before R-0001 (older but still active).
    assert [e["id"] for e in load_reflections(path)] == ["R-0001", "R-0003", "R-0004"]


def test_prune_falls_back_to_oldest_active(tmp_path):
    path = _buf(tmp_path)
    for n in range(3):
        _add(path, n, buffer_size=2)
    assert [e["id"] for e in load_reflections(path)] == ["R-0002", "R-0003"]


# ---------------------------------------------------------------------------
# Active lessons + supersede
# ---------------------------------------------------------------------------


def test_active_lessons_skips_deprecated_and_superseded_newest_first(tmp_path):
    path = _buf(tmp_path)
    for n in range(4):
        _add(path, n, buffer_size=10)
    entries = load_reflections(path)
    entries[0]["status"] = "deprecated"
    entries[1]["superseded_by"] = "R-0003"
    active = active_lessons(entries, buffer_size=10)
    assert [e["id"] for e in active] == ["R-0004", "R-0003"]


def test_active_lessons_caps_at_buffer_size(tmp_path):
    path = _buf(tmp_path)
    for n in range(4):
        _add(path, n, buffer_size=10)
    active = active_lessons(load_reflections(path), buffer_size=2)
    assert [e["id"] for e in active] == ["R-0004", "R-0003"]


def test_supersede_stamps_old_entry(tmp_path):
    path = _buf(tmp_path)
    _add(path, 0, buffer_size=10)
    _add(path, 1, buffer_size=10)
    assert supersede_reflection(path, "R-0001", "R-0002") is True
    entries = load_reflections(path)
    assert entries[0]["superseded_by"] == "R-0002"
    assert "superseded_by" not in entries[1]


def test_supersede_missing_id_returns_false(tmp_path):
    path = _buf(tmp_path)
    _add(path, 0)
    assert supersede_reflection(path, "R-9999", "R-0001") is False


# ---------------------------------------------------------------------------
# Lessons block
# ---------------------------------------------------------------------------


def test_lessons_block_flags_provisional_only(tmp_path):
    path = _buf(tmp_path)
    _add(path, 0, status="confirmed", buffer_size=10)
    _add(path, 1, status="provisional", buffer_size=10)
    block = lessons_block(load_reflections(path))
    assert "## Learned lessons" in block
    assert "- [R-0002] lesson 1 (provisional)" in block
    assert "- [R-0001] lesson 0" in block
    assert "lesson 0 (provisional)" not in block


def test_lessons_block_empty_when_nothing_active(tmp_path):
    assert lessons_block([]) == ""
    path = _buf(tmp_path)
    _add(path, 0)
    entries = load_reflections(path)
    entries[0]["status"] = "deprecated"
    assert lessons_block(entries) == ""


# ---------------------------------------------------------------------------
# Miner
# ---------------------------------------------------------------------------


def _fixture_sessions(tmp_path: Path) -> Path:
    """Three fake logs with distinct, deterministic mtimes (oldest -> newest)."""
    sessions = tmp_path / ".sessions"
    sessions.mkdir()
    logs = {
        "2026-06-01-a.md": ("# A\n\n💡 Session idea: cache the map\nsome text docs/plan.md here\n"),
        "2026-06-02-b.md": (
            "# B\n\n⚑ Self-initiated: built the thing\nsee docs/plan.md again\n"
            "[DEPRECATED] 💡 stale idea, do not mine\n"
        ),
        "2026-06-03-c.md": "# C\n\nplain line, nothing to mine\n",
    }
    sessions.joinpath("README.md").write_text("💡 convention doc\n", encoding="utf-8")
    for i, name in enumerate(sorted(logs)):
        p = sessions / name
        p.write_text(logs[name], encoding="utf-8")
        os.utime(p, (1000 + i, 1000 + i))
    return sessions


def test_mine_extracts_idea_and_flag_lines(tmp_path):
    candidates = mine_reflections(_fixture_sessions(tmp_path))
    idea = next(c for c in candidates if "idea" in c["tags"])
    assert idea["lesson"] == "Session idea: cache the map"
    assert idea["evidence"] == "2026-06-01-a.md:L3"
    flag = next(c for c in candidates if "flag" in c["tags"])
    assert flag["lesson"] == "Self-initiated: built the thing"
    assert flag["evidence"] == "2026-06-02-b.md:L3"


def test_mine_skips_deprecated_lines(tmp_path):
    candidates = mine_reflections(_fixture_sessions(tmp_path))
    assert not any("stale idea" in c["lesson"] for c in candidates)


def test_mine_finds_recurring_paths(tmp_path):
    candidates = mine_reflections(_fixture_sessions(tmp_path))
    recurring = [c for c in candidates if c["tags"] == ["recurring-path"]]
    assert len(recurring) == 1
    assert recurring[0]["lesson"] == "Recurring attention on docs/plan.md"
    assert recurring[0]["evidence"] == "2026-06-01-a.md:L4, 2026-06-02-b.md:L4"


def test_mine_is_deterministic(tmp_path):
    sessions = _fixture_sessions(tmp_path)
    assert mine_reflections(sessions) == mine_reflections(sessions)


def test_mine_last_n_limits_window(tmp_path):
    sessions = _fixture_sessions(tmp_path)
    # Newest two logs only: flag line yes, but docs/plan.md is cited once.
    candidates = mine_reflections(sessions, last_n=2)
    assert any("flag" in c["tags"] for c in candidates)
    assert not any(c["tags"] == ["recurring-path"] for c in candidates)
    assert not any("idea" in c["tags"] for c in candidates)
    # Newest single log has nothing minable.
    assert mine_reflections(sessions, last_n=1) == []


def test_mine_absent_dir_and_never_writes(tmp_path):
    assert mine_reflections(tmp_path / "nope") == []
    sessions = _fixture_sessions(tmp_path)
    before = sorted(p.name for p in tmp_path.rglob("*"))
    mine_reflections(sessions)
    assert sorted(p.name for p in tmp_path.rglob("*")) == before


def test_buffer_file_is_valid_json_on_disk(tmp_path):
    path = _buf(tmp_path)
    _add(path, 0)
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk[0]["id"] == "R-0001"
