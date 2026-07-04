"""Tests for the episodic session-log index (loop lane B2).

Covers filename parsing (conforming and non-conforming), tag extraction
(heading words minus stopwords + marker emojis), summary truncation, atomic
rebuild, dedupe-on-append, tag search hit/miss, and corrupt-index fail-open.
"""

import json
from pathlib import Path

from engine.loop.episodes import (
    EPISODIC_INDEX_FILENAME,
    append_episode,
    index_session,
    rebuild_episodic_index,
    search_episodes,
)


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _index(tmp_path: Path) -> Path:
    return tmp_path / EPISODIC_INDEX_FILENAME


# ---------------------------------------------------------------------------
# index_session
# ---------------------------------------------------------------------------


def test_index_session_parses_conforming_name(tmp_path):
    log = tmp_path / "2026-06-05-fix-drift.md"
    _write(log, "# The drift fix session\n\nRepaired two ledger entries.\n\n💡 idea line\n")
    entry = index_session(log)
    assert entry["slug"] == "fix-drift"
    assert entry["date"] == "2026-06-05"
    assert entry["summary"] == "Repaired two ledger entries."


def test_index_session_tags_heading_words_minus_stopwords(tmp_path):
    log = tmp_path / "2026-06-05-x.md"
    _write(log, "# The drift fix of a session\n\nbody\n")
    entry = index_session(log)
    assert entry["tags"] == ["drift", "fix", "session"]


def test_index_session_tags_include_marker_emojis(tmp_path):
    log = tmp_path / "2026-06-05-y.md"
    _write(log, "# Y\n\nbody 💡 one ⚑ two ⟲ three 📊 four\n")
    tags = index_session(log)["tags"]
    for mark in ("💡", "⚑", "⟲", "📊"):
        assert mark in tags


def test_index_session_non_conforming_name_uses_stem(tmp_path):
    log = tmp_path / "notes.md"
    _write(log, "# Loose notes\n\nfree-form text\n")
    entry = index_session(log)
    assert entry["slug"] == "notes"
    assert entry["date"] == ""
    assert entry["summary"] == "free-form text"


def test_index_session_summary_truncated_to_140(tmp_path):
    log = tmp_path / "2026-06-05-long.md"
    _write(log, "# L\n\n" + "x" * 200 + "\n")
    assert len(index_session(log)["summary"]) == 140


def test_index_session_missing_file_degrades(tmp_path):
    entry = index_session(tmp_path / "2026-06-05-ghost.md")
    assert entry == {"slug": "ghost", "date": "2026-06-05", "tags": [], "summary": ""}


# ---------------------------------------------------------------------------
# rebuild_episodic_index
# ---------------------------------------------------------------------------


def test_rebuild_scans_sorted_and_skips_readme(tmp_path):
    sessions = tmp_path / ".sessions"
    _write(sessions / "README.md", "# Convention\n\nnot a session\n")
    _write(sessions / "2026-06-02-second.md", "# Second\n\ntwo\n")
    _write(sessions / "2026-06-01-first.md", "# First\n\none\n")
    entries = rebuild_episodic_index(sessions, _index(tmp_path))
    assert [e["slug"] for e in entries] == ["first", "second"]
    on_disk = json.loads(_index(tmp_path).read_text(encoding="utf-8"))
    assert on_disk == entries


def test_rebuild_absent_dir_writes_empty_index(tmp_path):
    entries = rebuild_episodic_index(tmp_path / "nope", _index(tmp_path))
    assert entries == []
    assert json.loads(_index(tmp_path).read_text(encoding="utf-8")) == []


# ---------------------------------------------------------------------------
# append_episode — dedupe by slug
# ---------------------------------------------------------------------------


def test_append_adds_then_replaces_by_slug(tmp_path):
    index = _index(tmp_path)
    append_episode(index, {"slug": "a", "date": "2026-06-01", "tags": [], "summary": "v1"})
    append_episode(index, {"slug": "b", "date": "2026-06-02", "tags": [], "summary": "b"})
    append_episode(index, {"slug": "a", "date": "2026-06-01", "tags": ["x"], "summary": "v2"})
    entries = json.loads(index.read_text(encoding="utf-8"))
    assert [e["slug"] for e in entries] == ["a", "b"]
    assert entries[0]["summary"] == "v2"
    assert entries[0]["tags"] == ["x"]


def test_append_on_corrupt_index_starts_fresh(tmp_path):
    index = _index(tmp_path)
    index.write_text("not json", encoding="utf-8")
    append_episode(index, {"slug": "a", "date": "", "tags": [], "summary": ""})
    assert [e["slug"] for e in json.loads(index.read_text(encoding="utf-8"))] == ["a"]


# ---------------------------------------------------------------------------
# search_episodes
# ---------------------------------------------------------------------------


def test_search_hit_and_miss(tmp_path):
    index = _index(tmp_path)
    append_episode(index, {"slug": "a", "date": "", "tags": ["drift", "💡"], "summary": ""})
    append_episode(index, {"slug": "b", "date": "", "tags": ["economy"], "summary": ""})
    assert [e["slug"] for e in search_episodes(index, "drift")] == ["a"]
    assert [e["slug"] for e in search_episodes(index, "💡")] == ["a"]
    assert search_episodes(index, "nonexistent-tag") == []


def test_search_missing_or_corrupt_index_fails_open(tmp_path):
    assert search_episodes(_index(tmp_path), "drift") == []
    _index(tmp_path).write_text("[{broken", encoding="utf-8")
    assert search_episodes(_index(tmp_path), "drift") == []
