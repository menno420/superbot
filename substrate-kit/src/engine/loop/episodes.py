"""Episodic index — a tiny searchable memory over session logs (plan lane B2).

Each session log becomes one compact ``{"slug", "date", "tags", "summary"}``
record in ``<state_dir>/episodic_index.json``, so an agent can grep *which*
past session touched a topic without reading every log top-to-bottom. Tags
come from the log's first heading (minus stopwords) plus the workflow's marker
emojis (💡 idea, ⚑ flag, ⟲ review, 📊 telemetry). The index is a derived
artifact: rebuildable from the logs at any time, written atomically, and
fail-open on absence/corruption.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from engine.lib.atomicio import atomic_write_text

EPISODIC_INDEX_FILENAME = "episodic_index.json"

_EPI_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
_EPI_WORD_RE = re.compile(r"[a-z0-9][\w-]*")
_EPI_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "at",
        "by",
        "for",
        "from",
        "in",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    },
)
_EPI_MARKERS = (
    "\N{ELECTRIC LIGHT BULB}",  # 💡 session idea
    "\N{BLACK FLAG}",  # ⚑ self-initiated / friction flag
    "\N{ANTICLOCKWISE GAPPED CIRCLE ARROW}",  # ⟲ previous-session review
    "\N{BAR CHART}",  # 📊 telemetry / KPI footer
)
_EPI_SUMMARY_LIMIT = 140


def _epi_load(index_path: Path) -> list[dict]:
    """Return the index entries at ``index_path`` — ``[]`` on absent/corrupt."""
    try:
        raw = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def _epi_save(index_path: Path, entries: list[dict]) -> None:
    """Write ``entries`` to ``index_path`` atomically as pretty-printed JSON."""
    atomic_write_text(index_path, json.dumps(entries, indent=2) + "\n")


def _epi_tags(text: str) -> list[str]:
    """Tags: first ``# `` heading words minus stopwords, plus marker emojis."""
    tags: list[str] = []
    for line in text.splitlines():
        if line.startswith("# "):
            words = _EPI_WORD_RE.findall(line[2:].lower())
            tags.extend(word for word in words if word not in _EPI_STOPWORDS)
            break
    tags.extend(mark for mark in _EPI_MARKERS if mark in text)
    return list(dict.fromkeys(tags))


def _epi_summary(text: str) -> str:
    """Return the first non-blank non-heading line, truncated to 140 chars."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:_EPI_SUMMARY_LIMIT]
    return ""


def index_session(log_path: Path) -> dict:
    """Summarise one session log into ``{"slug", "date", "tags", "summary"}``.

    ``slug`` and ``date`` parse from the ``YYYY-MM-DD-<slug>.md`` filename
    convention; a non-conforming name degrades gracefully to the whole stem as
    the slug with an empty date. An unreadable file yields empty tags/summary.
    """
    match = _EPI_NAME_RE.match(log_path.stem)
    if match:
        session_date, slug = match.group(1), match.group(2)
    else:
        session_date, slug = "", log_path.stem
    try:
        text = log_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    return {
        "slug": slug,
        "date": session_date,
        "tags": _epi_tags(text),
        "summary": _epi_summary(text),
    }


def rebuild_episodic_index(sessions_dir: Path, index_path: Path) -> list[dict]:
    """Rebuild the whole index from ``sessions_dir`` and write it atomically.

    Scans ``*.md`` excluding ``README.md``, sorted by filename (the date-first
    naming convention makes that chronological). Returns the entries written;
    an absent sessions dir yields an empty index.
    """
    logs: list[Path] = []
    if sessions_dir.is_dir():
        logs = sorted(p for p in sessions_dir.glob("*.md") if p.name != "README.md")
    entries = [index_session(p) for p in logs]
    _epi_save(index_path, entries)
    return entries


def append_episode(index_path: Path, entry: dict) -> None:
    """Add ``entry`` to the index, replacing an existing (slug, date) match.

    Keyed on slug *and* date: re-indexing the same log updates in place, while
    a same-slug session from a different day appends instead of silently
    deleting the earlier episode.
    """
    entries = _epi_load(index_path)
    key = (entry.get("slug"), entry.get("date"))
    for i, existing in enumerate(entries):
        if (existing.get("slug"), existing.get("date")) == key:
            entries[i] = entry
            break
    else:
        entries.append(entry)
    _epi_save(index_path, entries)


def search_episodes(index_path: Path, tag: str) -> list[dict]:
    """Return every indexed episode carrying ``tag`` in its tag list."""
    return [entry for entry in _epi_load(index_path) if tag in entry.get("tags", [])]
