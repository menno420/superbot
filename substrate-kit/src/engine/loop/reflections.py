"""Reflection buffer — the loop's compact learned-lesson memory (plan lane B2).

Reflections are small ``{"lesson", "evidence", "tags"}`` records mined from
session logs or added deliberately, stored in one atomically-written JSON file
(``<state_dir>/reflections.json``). The buffer is deliberately tiny — a hard
``buffer_size`` cap keeps the orientation injection cheap — and fail-open: a
missing or corrupt file reads as an empty list, never a crash. The miner is
deterministic and read-only; the caller decides what (if anything) becomes a
stored reflection.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from engine.lib.atomicio import atomic_write_text

REFLECTIONS_FILENAME = "reflections.json"

_REF_ID_RE = re.compile(r"^R-(\d+)$")
_REF_IDEA_MARK = "\N{ELECTRIC LIGHT BULB}"  # 💡 — session-idea lines
_REF_FLAG_MARK = "\N{BLACK FLAG}"  # ⚑ — self-initiated / friction flags
_REF_PATH_SUFFIXES = (".py", ".md", ".js", ".ts", ".yml", ".json")
_REF_STRIP_CHARS = "`'\"()[]<>,;:!?."


def load_reflections(path: Path) -> list[dict]:
    """Return the reflection entries at ``path`` — ``[]`` on absent/corrupt."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def _ref_save(path: Path, entries: list[dict]) -> None:
    """Write ``entries`` to ``path`` atomically as pretty-printed JSON."""
    atomic_write_text(path, json.dumps(entries, indent=2) + "\n")


def _ref_next_id(entries: list[dict]) -> str:
    """Return the next ``R-NNNN`` id, monotonic over the ids already present."""
    highest = 0
    for entry in entries:
        match = _REF_ID_RE.match(str(entry.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"R-{highest + 1:04d}"


def _ref_is_inactive(entry: dict) -> bool:
    """True when an entry is deprecated or superseded (prune/skip candidate)."""
    return entry.get("status") == "deprecated" or bool(entry.get("superseded_by"))


def _ref_prune(entries: list[dict], buffer_size: int) -> list[dict]:
    """Drop overflow beyond ``buffer_size``: oldest inactive first, then oldest.

    ``buffer_size`` is clamped to at least 1 — a zero/negative host config must
    never silently discard every lesson (or crash), and the entry just added is
    never its own prune victim.
    """
    buffer_size = max(1, int(buffer_size))
    pruned = list(entries)
    while len(pruned) > buffer_size:
        victim = next((e for e in pruned[:-1] if _ref_is_inactive(e)), pruned[0])
        pruned.remove(victim)
    return pruned


def add_reflection(
    path: Path,
    *,
    lesson: str,
    evidence: str,
    tags: list[str],
    status: str = "provisional",
    buffer_size: int = 5,
) -> dict:
    """Append a reflection to the buffer at ``path`` and return the new entry.

    Assigns the next monotonic ``R-NNNN`` id, stamps today's ISO date, and
    prunes overflow beyond ``buffer_size`` (oldest superseded/deprecated
    entries first, then oldest overall). ``status`` is ``provisional`` until a
    later session confirms the lesson held up.
    """
    entries = load_reflections(path)
    entry = {
        "id": _ref_next_id(entries),
        "lesson": lesson,
        "evidence": evidence,
        "tags": list(tags),
        "status": status,
        "date": date.today().isoformat(),
    }
    entries.append(entry)
    _ref_save(path, _ref_prune(entries, buffer_size))
    return entry


def active_lessons(entries: list[dict], buffer_size: int) -> list[dict]:
    """Return live lessons newest-first, capped at ``buffer_size``.

    Skips entries whose status is ``deprecated`` and entries carrying a
    ``superseded_by`` stamp.
    """
    live = [entry for entry in entries if not _ref_is_inactive(entry)]
    live.reverse()
    return live[:buffer_size]


def supersede_reflection(path: Path, old_id: str, new_id: str) -> bool:
    """Stamp ``superseded_by`` on ``old_id``'s entry; False when it is absent."""
    entries = load_reflections(path)
    for entry in entries:
        if entry.get("id") == old_id:
            entry["superseded_by"] = new_id
            _ref_save(path, entries)
            return True
    return False


def lessons_block(entries: list[dict]) -> str:
    """Render the "Learned lessons" orientation block ("" when nothing active).

    Provisional entries are flagged ``(provisional)`` so the reading agent
    weighs them as candidates, not settled rules.
    """
    live = active_lessons(entries, len(entries))
    if not live:
        return ""
    lines = ["## Learned lessons", ""]
    for entry in live:
        flag = " (provisional)" if entry.get("status") == "provisional" else ""
        lines.append(f"- [{entry.get('id', '?')}] {entry.get('lesson', '')}{flag}")
    return "\n".join(lines) + "\n"


def _ref_newest_logs(sessions_dir: Path, last_n: int) -> list[Path]:
    """Return the newest ``last_n`` logs by mtime (name-tiebroken), oldest first."""
    if not sessions_dir.is_dir() or last_n < 1:
        return []
    logs = [p for p in sessions_dir.glob("*.md") if p.name != "README.md"]
    logs.sort(key=lambda p: (p.stat().st_mtime, p.name))
    return logs[-last_n:]


def _ref_clean_line(line: str) -> str:
    """Strip bullets, blockquote marks, and the emoji markers from a mined line."""
    text = line.strip().lstrip("-*> ").strip()
    for mark in (_REF_IDEA_MARK, _REF_FLAG_MARK):
        text = text.replace(mark, "")
    return text.strip().lstrip(":").strip()


def _ref_marker_tags(line: str) -> list[str]:
    """Return the candidate tags for a line's emoji markers (may be empty)."""
    tags: list[str] = []
    if _REF_IDEA_MARK in line:
        tags.append("idea")
    if _REF_FLAG_MARK in line:
        tags.append("flag")
    return tags


def _ref_path_tokens(line: str) -> list[str]:
    """Return file-path tokens: contain ``/`` and end in a known code/doc suffix."""
    tokens: list[str] = []
    for raw in line.split():
        token = raw.strip(_REF_STRIP_CHARS)
        if "/" in token and token.endswith(_REF_PATH_SUFFIXES):
            tokens.append(token)
    return tokens


def _ref_mine_log(log: Path) -> tuple[list[dict], dict[str, str]]:
    """Mine one log: (marker-line candidates, first evidence per cited path)."""
    candidates: list[dict] = []
    paths_seen: dict[str, str] = {}
    try:
        lines = log.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return candidates, paths_seen
    for lineno, line in enumerate(lines, 1):
        if "[DEPRECATED]" in line:
            continue
        evidence = f"{log.name}:L{lineno}"
        tags = _ref_marker_tags(line)
        if tags:
            candidates.append(
                {"lesson": _ref_clean_line(line), "evidence": evidence, "tags": tags},
            )
        for token in _ref_path_tokens(line):
            paths_seen.setdefault(token, evidence)
    return candidates, paths_seen


def mine_reflections(sessions_dir: Path, *, last_n: int = 5) -> list[dict]:
    """Mine candidate lessons from the newest ``last_n`` session logs.

    Deterministic and read-only — never writes state; the caller decides what
    to promote into the buffer. Three extraction passes:

      1. 💡 idea lines → ``{"lesson", "evidence", "tags": ["idea"]}``.
      2. ⚑ flag lines → the same shape, tagged ``flag``.
      3. Any file path cited in >= 2 different logs → one
         ``Recurring attention on <path>`` candidate.

    Lines containing ``[DEPRECATED]`` are skipped entirely.
    """
    candidates: list[dict] = []
    sightings: dict[str, dict[str, str]] = {}
    for log in _ref_newest_logs(sessions_dir, last_n):
        mined, paths_seen = _ref_mine_log(log)
        candidates.extend(mined)
        for token, evidence in paths_seen.items():
            sightings.setdefault(token, {})[log.name] = evidence
    for token in sorted(sightings):
        seen = sightings[token]
        if len(seen) < 2:
            continue
        evidence = ", ".join(seen[name] for name in sorted(seen))
        candidates.append(
            {
                "lesson": f"Recurring attention on {token}",
                "evidence": evidence,
                "tags": ["recurring-path"],
            },
        )
    return candidates
