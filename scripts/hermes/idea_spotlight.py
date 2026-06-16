#!/usr/bin/env python3
"""Pick today's SuperBot "idea spotlight" — one active idea, deterministically.

This owns the *mechanical* half of the ``superbot-idea-spotlight`` Hermes skill:
the **selection** of which idea to surface today, and the extraction of its title /
status / one-line summary / "relates" hints. The skill prompt then does the
*reasoning* half (pros, cons, options & expansions) over the idea this script
picked. Same split as ``log_triage.py`` / ``dispatch_menu.py``: the deterministic
layer owns the answer the model would otherwise assemble by eyeballing the backlog.

Selection is **deterministic per calendar day** so a re-run on the same day surfaces
the same idea (idempotent — a scheduled fire and a manual ``--date`` agree), and it
**rotates** through the whole active backlog as the days advance (index =
``date.toordinal() % len(active)`` over a name-sorted list, so every active idea is
covered across one cycle).

"Active" = an idea file whose ``> **Status:** `badge``` is *not* a terminal-lifecycle
badge (``historical`` / ``rejected`` / ``shipped`` / ``superseded`` / ``done``).
``ideas`` / ``raw`` / ``captured`` / no-badge all count as active. This mirrors the
``docs/ideas/`` lifecycle: a capture is re-badged ``historical`` once it ships.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: the owner wants one fresh idea per day to mull over and report back on (live
  request, 2026-06-16). Picking it by hand is the "model assembles the answer" class;
  this makes it deterministic, content-free, and testable.
- Added: 2026-06-16. **Unverified** — confirm a few daily picks look sensible before
  trusting it unattended. **Delete this script if the ``docs/ideas/`` badge convention
  changes or it proves unreliable**; it is a disposable convenience reporter, read-only.

Stdlib-only so the unit tests run in CI without installing anything. Invoke with
**``python3``** (version-agnostic) like the rest of ``scripts/hermes/`` — the Hermes
VPS has Python 3.11, not the repo's CI-pinned 3.10, and this is a stdlib text tool,
NOT one of the CI-parity tools. Do not "correct" the usage lines to ``python3.10``.

Usage::

    python3 scripts/hermes/idea_spotlight.py                 # today's pick (markdown)
    python3 scripts/hermes/idea_spotlight.py --json          # today's pick (JSON)
    python3 scripts/hermes/idea_spotlight.py --date 2026-06-16
    python3 scripts/hermes/idea_spotlight.py --list          # all active ideas + indices
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
IDEAS_DIR = REPO_ROOT / "docs" / "ideas"

#: Status badges that mean the idea has reached a terminal lifecycle outcome and
#: should NOT be spotlighted as live backlog. Everything else counts as active.
_TERMINAL_BADGES = {"historical", "rejected", "shipped", "superseded", "done"}

_STATUS_RE = re.compile(r">\s*\*\*Status:\*\*\s*`([^`]+)`")
_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$")
_RELATES_RE = re.compile(r"(→\s*relates|^##\s+Connections)", re.IGNORECASE)

_MAX_SUMMARY_LEN = 320


@dataclass(frozen=True)
class Idea:
    """One parsed idea-capture file."""

    path: Path
    title: str
    status: str
    summary: str
    relates: str

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def is_active(self) -> bool:
        return self.status.lower() not in _TERMINAL_BADGES


def _first_title(lines: list[str]) -> str:
    for line in lines:
        m = _TITLE_RE.match(line)
        if m:
            return m.group(1).strip()
    return "(untitled idea)"


def _first_status(text: str) -> str:
    m = _STATUS_RE.search(text)
    return m.group(1).strip() if m else ""


def _first_summary(lines: list[str]) -> str:
    """Return the first real prose paragraph (skip title, blockquotes, headings)."""
    para: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if para:  # paragraph ended
                break
            continue
        if stripped.startswith(("#", ">", "```", "|", "- ", "* ", "1.")):
            if para:
                break
            continue
        para.append(stripped)
    summary = " ".join(para)
    if len(summary) > _MAX_SUMMARY_LEN:
        summary = summary[: _MAX_SUMMARY_LEN - 1].rstrip() + "…"
    return summary


def _first_relates(lines: list[str]) -> str:
    """Return the first 'relates'/'Connections' hint line, if any (trimmed)."""
    for line in lines:
        if _RELATES_RE.search(line):
            hint = line.strip().lstrip("#").strip()
            return hint[:200]
    return ""


def parse_idea(path: Path) -> Idea:
    """Parse one ``docs/ideas/<file>.md`` into an :class:`Idea`."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    return Idea(
        path=path,
        title=_first_title(lines),
        status=_first_status(text),
        summary=_first_summary(lines),
        relates=_first_relates(lines),
    )


def load_ideas(ideas_dir: Path) -> list[Idea]:
    """Load every idea file (excluding README), name-sorted for stable ordering."""
    files = sorted(p for p in ideas_dir.glob("*.md") if p.name.lower() != "readme.md")
    return [parse_idea(p) for p in files]


def active_ideas(ideas: list[Idea]) -> list[Idea]:
    """Return only the live-backlog ideas (terminal badges filtered out)."""
    return [i for i in ideas if i.is_active]


def select(ideas: list[Idea], day: _dt.date) -> tuple[int, Idea | None]:
    """Return ``(index, idea)`` for *day*'s deterministic pick over active ideas.

    Index is ``day.toordinal() % len(active)`` against the name-sorted active list,
    so the choice is stable per day and cycles through the whole backlog. Returns
    ``(-1, None)`` when there is nothing active to surface.
    """
    active = active_ideas(ideas)
    if not active:
        return -1, None
    index = day.toordinal() % len(active)
    return index, active[index]


def _rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def render_markdown(idea: Idea | None, index: int, total: int, day: _dt.date) -> str:
    """Render the spotlight block the skill reasons over and delivers."""
    head = f"## 💡 Idea spotlight — {day.isoformat()}"
    if idea is None:
        return f"{head}\n\nNo active ideas in the backlog right now. 🎉"
    out = [
        head,
        f"**Idea {index + 1} of {total} active:** {idea.title}",
        "",
        f"- **File:** {_rel_path(idea.path)}",
        f"- **Status:** `{idea.status or 'ideas'}`",
    ]
    if idea.relates:
        out.append(f"- **Relates:** {idea.relates}")
    if idea.summary:
        out += ["", idea.summary]
    return "\n".join(out)


def to_dict(idea: Idea | None, index: int, total: int, day: _dt.date) -> dict:
    """JSON-serialisable view of the pick (``--json``)."""
    return {
        "date": day.isoformat(),
        "total_active": total,
        "index": index,
        "idea": (
            None
            if idea is None
            else {
                "title": idea.title,
                "file": _rel_path(idea.path),
                "status": idea.status,
                "summary": idea.summary,
                "relates": idea.relates,
            }
        ),
    }


def _parse_date(value: str | None) -> _dt.date:
    if not value:
        return _dt.datetime.now(_dt.timezone.utc).date()
    return _dt.date.fromisoformat(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pick today's SuperBot idea spotlight (deterministic per day).",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="ISO date (YYYY-MM-DD) to pick for; default: today (UTC)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON instead of markdown",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list every active idea with its rotation index instead of one pick",
    )
    args = parser.parse_args(argv)

    if not IDEAS_DIR.is_dir():
        print(f"idea_spotlight: cannot find ideas dir at {IDEAS_DIR}")
        return 1

    day = _parse_date(args.date)
    ideas = load_ideas(IDEAS_DIR)
    active = active_ideas(ideas)

    if args.list:
        if args.json:
            print(
                json.dumps(
                    [
                        {"index": i, "title": idea.title, "file": _rel_path(idea.path)}
                        for i, idea in enumerate(active)
                    ],
                    indent=2,
                ),
            )
        else:
            print(f"Active ideas ({len(active)}):")
            for i, idea in enumerate(active):
                print(f"  [{i:>3}] {idea.title}  ({_rel_path(idea.path)})")
        return 0

    index, idea = select(ideas, day)
    if args.json:
        print(json.dumps(to_dict(idea, index, len(active), day), indent=2))
    else:
        print(render_markdown(idea, index, len(active), day))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
