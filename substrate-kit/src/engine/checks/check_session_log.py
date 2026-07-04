"""Generic session-log completeness checker (config-driven port).

The session workflow asks every session to end with a
``<sessions_dir>/<date>-<slug>.md`` log that carries a set of required markers
(by default: a Status badge, a session-idea flag, and a previous-session review).
Each marker is a ``{"label", "needle"}`` pair from ``substrate.config.json``, so a
host tunes the ritual without touching engine code.

Unlike the host's version this port does **not** shell out to ``git`` to pick the
"current" log — ``subprocess`` is banned in engine code and is host-CI sugar
anyway. The current log is the newest ``*.md`` by mtime under ``sessions_dir``
(the CLI also accepts an explicit ``--file``). Pure stdlib; returns the missing
markers rather than printing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path


def missing_markers(text: str, markers: Sequence[Mapping[str, str]]) -> list[str]:
    """Return the labels of markers whose needle is absent from ``text``.

    Tolerant of partial host-config entries: a marker without a ``needle`` is
    skipped (nothing to search for) rather than raising, and a missing
    ``label`` reports as ``"?"``.
    """
    lower = text.lower()
    return [
        m.get("label", "?")
        for m in markers
        if m.get("needle") and m.get("needle", "").lower() not in lower
    ]


def latest_session_log(sessions_dir: Path) -> Path | None:
    """Best guess at this session's log: newest ``*.md`` by mtime (skip README)."""
    if not sessions_dir.is_dir():
        return None
    candidates = [p for p in sessions_dir.glob("*.md") if p.name != "README.md"]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def check_log(path: Path, markers: Sequence[Mapping[str, str]]) -> list[str]:
    """Return the missing-marker labels for one log file (all if unreadable)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return [m["label"] for m in markers]
    return missing_markers(text, markers)
