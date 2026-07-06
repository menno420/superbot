#!/usr/bin/env python3.10
"""Render the live per-sector dispatch menu from the roadmap.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: the #880 dispatch test showed that "what would a worker dispatched to sector SX
  actually pick up?" is answerable by hand in 2-3 hops, but only by reading prose. This is
  the machine version (the #880 Q-0089 idea): parse the ``roadmap.md`` per-sector dispatch
  index and print, per sector, the first **▶ startable** item, its executor, and a flag for
  a "starving" sector whose ``Now`` is entirely blocked (⛔/👤). A dispatcher (or Hermes)
  picks from this generated, always-fresh menu instead of re-reading the roadmap.
- Added: 2026-06-14 (Q-0143 follow-on). **Unverified** — confirm its output against the
  roadmap a few times before trusting it. **Delete this script if it proves unreliable**;
  it is a disposable convenience reporter, read-only, not load-bearing.

The parsing helpers here intentionally mirror ``check_sector_map.py`` (each script stays a
self-contained single file — the repo's standalone-script convention; cross-script
imports are brittle). If a third consumer appears, factor a shared module.

Usage::

    python3.10 scripts/dispatch_menu.py            # all sectors
    python3.10 scripts/dispatch_menu.py S2          # one sector
    python3.10 scripts/dispatch_menu.py --unattended  # the empty-fire pick (#1285): which
                                                      # lane can a scheduled run finish & merge?
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP = REPO_ROOT / "docs" / "roadmap.md"
STATE_DIR = REPO_ROOT / "docs" / "current-state"

# The per-item offline-fit tag the per-sector live-state files carry on each ▶ Next item
# (convention: repo-sector-map.md § "the offline-fit startability tag"; guarded by
# scripts/check_startability_tags.py). ``[offline]`` = offline-verifiable + self-mergeable —
# the concrete item an empty-fire run should build. Surfacing it here closes the loop the
# roadmap's sector-level unattended-fit tag left open: a run gets the actual item to build
# without opening the sector file by hand (the 2026-06-26 Q-0102 review's friction).
_OFFLINE_TAG = "[offline]"
_NEXT_HEADING = re.compile(r"^\*\*▶ Next\b")
_BOLD_HEADING = re.compile(r"^\*\*[^*].*:\*\*")
_SECTOR_STEM = re.compile(r"^(S\d)\b")

_SECTOR_HEADING = re.compile(r"^###\s+(S\d)\s+—\s+(.+?)\s+·")
_BULLET_HEAD = re.compile(r"^- \*\*([^:*]+):\*\*")
_EXECUTOR = re.compile(r"executor \*\*([^*]+)\*\*")
_UNATTENDED_FIT = re.compile(r"unattended-fit \*\*([^*]+)\*\*")
_ITEM_SEP = re.compile(r" · | — | \(")

# The unattended-fit keyword → can a *scheduled empty-fire* run complete AND merge it?
# (Orthogonal to the ▶/⛔/👤 startability glyph, which only says "may Claude *begin* it?".)
# Contract: docs/repo-sector-map.md § "the unattended-fit tag".
_FIT_KEYWORDS = ("auto", "review", "live", "ext-data")


def _read(path: Path) -> str:
    """Return file text, or empty string if unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def by_sector_section(text: str) -> str:
    """Return the roadmap text between '## By sector' and the next '## ' heading."""
    start = text.find("## By sector")
    if start == -1:
        return ""
    rest = text[start + len("## By sector") :]
    nxt = rest.find("\n## ")
    return rest if nxt == -1 else rest[:nxt]


def sector_blocks(section: str) -> list[tuple[str, str, str]]:
    """Return ordered ``(id, name, block_text)`` tuples for each ``### S<n>`` block."""
    blocks: list[tuple[str, str, str]] = []
    cur_id: str | None = None
    cur_name = ""
    buf: list[str] = []
    for line in section.splitlines():
        m = _SECTOR_HEADING.match(line)
        if m:
            if cur_id:
                blocks.append((cur_id, cur_name, "\n".join(buf)))
            cur_id, cur_name = m.group(1), m.group(2).strip()
            buf = [line]
        elif cur_id:
            buf.append(line)
    if cur_id:
        blocks.append((cur_id, cur_name, "\n".join(buf)))
    return blocks


def bullet_text(block: str, label: str) -> str:
    """Return the text of the ``- **<label>...:**`` bullet (incl. continuation lines)."""
    out: list[str] = []
    grabbing = False
    for line in block.splitlines():
        m = _BULLET_HEAD.match(line)
        if m:
            if grabbing:
                break
            if m.group(1).strip().startswith(label):
                grabbing = True
                out.append(line)
        elif grabbing:
            out.append(line)
    return "\n".join(out)


def first_startable(bullet: str) -> str | None:
    """Return the first ▶-tagged item's short label in a bullet, or None.

    Tolerates the markup variants (``**▶ X**``, ``**▶** the … **X**``): collapse
    whitespace, drop markdown link targets and emphasis/bracket punctuation, then take
    the text up to the first item separator (·, em-dash, or an opening paren).
    """
    if "▶" not in bullet:
        return None
    after = " ".join(bullet.split("▶", 1)[1].split())
    after = re.sub(r"\]\([^)]*\)", "]", after)  # drop link targets
    after = after.replace("**", "").replace("[", "").replace("]", "")
    after = _ITEM_SEP.split(after, maxsplit=1)[0]
    after = after.strip(" *:-")
    return after[:60].strip() or None


def resolve(block: str) -> tuple[str, str]:
    """Return ``(executor, dispatch_line)`` for a sector block."""
    dispatch = bullet_text(block, "Dispatch")
    m = _EXECUTOR.search(dispatch)
    executor = m.group(1).strip() if m else "?"
    return executor, dispatch


def unattended_fit(block: str) -> str | None:
    """Return the sector's unattended-fit keyword (``auto``/``review``/``live``/``ext-data``).

    Reads the ``unattended-fit **<glyph> <keyword>**`` token on the ``Dispatch`` line and
    returns the bare keyword; ``None`` when the tag is absent (``check_sector_map.py``
    forbids that, so a ``None`` in live output is a roadmap drift signal).
    """
    m = _UNATTENDED_FIT.search(bullet_text(block, "Dispatch"))
    if not m:
        return None
    value = m.group(1).strip().lower()
    for keyword in _FIT_KEYWORDS:
        if keyword in value:
            return keyword
    return None


def menu_line(block: str) -> str:
    """Return the one-line 'what's dispatchable' summary for a sector block."""
    now = bullet_text(block, "Now")
    now_item = first_startable(now)
    if now_item:
        return f"▶ Now: {now_item}"
    nxt_item = first_startable(bullet_text(block, "Next"))
    if "⛔" in now or "👤" in now:
        if nxt_item:
            return f"⛔/👤 Now blocked → ▶ Next: {nxt_item}"
        return (
            "⛔/👤 Now blocked — no ▶ startable item (route to executor / surface one)"
        )
    if nxt_item:
        return f"▶ Next: {nxt_item}"
    return "(no ▶ startable item found — check the roadmap)"


def sector_record(sid: str, name: str, block: str) -> dict[str, str | None]:
    """Return the machine-readable resolution for one sector block.

    The JSON sibling of :func:`menu_line` — the read-side of the
    ``dispatch-resolution-json-hermes`` idea, so the Hermes ``dispatch-resolve``
    skill can route a vague "work on SX" by the resolved **executor** instead of a
    human reading a table. ``state`` is one of: ``startable`` (▶ in Now, run by
    Claude-in-repo) · ``now_blocked_fallthrough`` (Now had no ▶, the item is from
    Next) · ``maintainer_or_hermes`` (a startable item but the executor isn't
    Claude-in-repo → don't fire a repo-editing agent) · ``starving`` (no ▶ anywhere).
    """
    executor, _ = resolve(block)
    now_item = first_startable(bullet_text(block, "Now"))
    next_item = first_startable(bullet_text(block, "Next"))
    if now_item:
        item, source = now_item, "Now"
    elif next_item:
        item, source = next_item, "Next"
    else:
        item, source = None, None

    is_claude = "claude-in-repo" in executor.lower()
    if item is None:
        state = "starving"
    elif not is_claude:
        state = "maintainer_or_hermes"
    elif source == "Next":
        state = "now_blocked_fallthrough"
    else:
        state = "startable"

    return {
        "sector": sid,
        "name": name,
        "executor": executor,
        "state": state,
        "startable_item": item,
        "source": source,
        "unattended_fit": unattended_fit(block),
    }


def build_records(
    text: str,
    only: str | None = None,
) -> list[dict[str, str | None]]:
    """Return the structured per-sector resolution (all sectors, or one)."""
    blocks = sector_blocks(by_sector_section(text))
    records: list[dict[str, str | None]] = []
    for sid, name, block in blocks:
        if only and sid != only:
            continue
        records.append(sector_record(sid, name, block))
    return records


def build_menu(text: str, only: str | None = None) -> list[str]:
    """Return the rendered menu lines for all sectors (or one, if ``only`` given)."""
    blocks = sector_blocks(by_sector_section(text))
    if not blocks:
        return ["(no '## By sector' dispatch index found in roadmap.md)"]
    lines: list[str] = []
    for sid, name, block in blocks:
        if only and sid != only:
            continue
        executor, _ = resolve(block)
        fit = unattended_fit(block) or "?(untagged — roadmap drift)"
        lines.append(f"{sid}  {name:<22}  exec: {executor}  fit: {fit}")
        lines.append(f"      {menu_line(block)}")
    if only and not any(line.startswith(only) for line in lines):
        return [f"(sector {only} not found — valid: S1..S5)"]
    return lines


def _sector_file(sid: str) -> Path | None:
    """Return the per-sector live-state file for ``sid`` (``S2`` → ``S2-btd6.md``)."""
    matches = sorted(
        p
        for p in STATE_DIR.glob(f"{sid}-*.md")
        if _SECTOR_STEM.match(p.stem) and _SECTOR_STEM.match(p.stem).group(1) == sid
    )
    return matches[0] if matches else None


def _next_block(text: str) -> str:
    """Return the ``▶ Next`` block of a sector live-state file (heading → next bold heading)."""
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if _NEXT_HEADING.match(line)),
        None,
    )
    if start is None:
        return ""
    out = [lines[start]]
    for line in lines[start + 1 :]:
        if _BOLD_HEADING.match(line):
            break
        out.append(line)
    return "\n".join(out)


def _offline_item_label(line: str) -> str:
    """Short label for an ``[offline]``-tagged ▶ item bullet line."""
    after = line.split(_OFFLINE_TAG, 1)[1]
    after = re.sub(r"\]\([^)]*\)", "]", after)  # drop link targets
    after = after.replace("**", "").replace("[", "").replace("]", "")
    after = _ITEM_SEP.split(after, maxsplit=1)[0]
    return after.strip(" *:-—`")[:60].strip()


def sector_offline_pick(sid: str) -> str | None:
    """Return the first ``[offline]`` startable item in a sector's live-state file, or ``None``.

    The concrete answer to "what offline thing do I build in this sector?" — read straight from
    the per-item offline-fit tag so an empty-fire run skips the by-hand sector-file spelunk.
    """
    path = _sector_file(sid)
    if path is None:
        return None
    block = _next_block(_read(path))
    for line in block.splitlines():
        if line.lstrip().startswith("-") and _OFFLINE_TAG in line:
            label = _offline_item_label(line)
            if label:
                return label
    return None


def build_unattended_summary(text: str) -> list[str]:
    """Answer one question for a *scheduled empty-fire* run: can I complete-and-merge a lane now?

    Aggregates the per-sector resolution + unattended-fit tag and ranks the sectors a
    truly-unattended run can actually finish. The point (the #1274/#1285 lesson): a `▶`
    glyph means "may begin", not "can finish unattended" — so an empty-fire run should pick
    from the 🟢 ``auto`` lanes, fall back to a 🟡 ``review`` lane (build + open PR, do not
    self-merge), and only then consider promoting an idea → plan → build (Q-0172).
    """
    records = build_records(text)
    # Only Claude-in-repo sectors with a resolved startable lane can be built in-repo at all.
    buildable = [
        r for r in records if r["state"] in ("startable", "now_blocked_fallthrough")
    ]
    by_fit: dict[str, list[dict[str, str | None]]] = {k: [] for k in _FIT_KEYWORDS}
    untagged: list[dict[str, str | None]] = []
    for rec in buildable:
        fit = rec["unattended_fit"]
        if fit in by_fit:
            by_fit[fit].append(rec)
        else:
            untagged.append(rec)

    header = "Unattended-fire pick (can an empty-fire run finish & merge a lane?)"
    out: list[str] = [header, "-" * 72]

    def _fmt(rec: dict[str, str | None]) -> str:
        return f"{rec['sector']} ({rec['source']}): {rec['startable_item']}"

    if by_fit["auto"]:
        out.append("🟢 SELF-MERGEABLE now (offline-verifiable, auto-merge on green):")
        out.extend(f"   {_fmt(r)}" for r in by_fit["auto"])
    else:
        out.append("🟢 auto: none — no offline-verifiable + self-mergeable lane.")

    if by_fit["review"]:
        out.append("🟡 build PR (auto-merges on green; worth a second look):")
        out.extend(f"   {_fmt(r)}" for r in by_fit["review"])
    if by_fit["live"]:
        out.append("🔵 weak fit (needs a live guild walk / runtime creds to verify):")
        out.extend(f"   {_fmt(r)}" for r in by_fit["live"])
    if by_fit["ext-data"]:
        out.append("🟠 owner-confirm first (commits externally-sourced data):")
        out.extend(f"   {_fmt(r)}" for r in by_fit["ext-data"])
    if untagged:
        out.append("?  untagged (roadmap drift — run check_sector_map.py):")
        out.extend(f"   {_fmt(r)}" for r in untagged)

    # Bridge sector → concrete item: read the first [offline]-tagged ▶ item from each buildable
    # sector's live-state file, so the run gets the actual thing to build, not just the sector.
    offline_picks = [
        (rec["sector"], pick)
        for rec in buildable
        if (pick := sector_offline_pick(str(rec["sector"]))) is not None
    ]
    if offline_picks:
        out.append("-" * 72)
        out.append("Concrete [offline] items (from the per-sector live-state files):")
        out.extend(f"   {sid}: {pick}" for sid, pick in offline_picks)

    out.append("-" * 72)
    if by_fit["auto"]:
        out.append("→ pick a 🟢 lane: build it, let auto-merge fire on green.")
    elif by_fit["review"]:
        out.append("→ no 🟢 lane: build a 🟡 review lane OR promote an idea (Q-0172).")
    else:
        out.append("→ no lane: promote a docs/ideas/ entry → plan → build (Q-0172).")
    return out


def main() -> int:
    """CLI entry point: print the dispatch menu."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sector",
        nargs="?",
        help="optional single sector id (e.g. S2) to show only that sector",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the per-sector resolution as JSON (for the dispatch-resolve skill)",
    )
    parser.add_argument(
        "--unattended",
        action="store_true",
        help="rank lanes a scheduled empty-fire run can complete & merge (the #1285 lens)",
    )
    args = parser.parse_args()

    text = _read(ROADMAP)
    if not text:
        print(f"dispatch_menu: cannot read {ROADMAP}")
        return 1

    only = args.sector.upper() if args.sector else None

    if args.json:
        print(json.dumps(build_records(text, only), indent=2))
        return 0

    if args.unattended:
        for line in build_unattended_summary(text):
            print(line)
        return 0

    print("SuperBot — sector dispatch menu  (live, from docs/roadmap.md § By sector)")
    print("=" * 72)
    for line in build_menu(text, only):
        print(line)
    print("=" * 72)
    print(
        "tags: ▶ startable · ⛔ gated · 👤 maintainer  |  unattended-fit: "
        "🟢 auto · 🟡 review · 🔵 live · 🟠 ext-data  |  --unattended for the empty-fire pick",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
