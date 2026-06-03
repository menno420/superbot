#!/usr/bin/env python3.10
"""Propose BTD6 stat-file edits from patch-notes text — review, never apply.

Patch notes (Steam / r/btd6) are *prose deltas*: "x5x Permacharge damage 8 > 10".
The runtime stat files (``disbot/data/btd6/stats/*.json``) are the *full* state.
This tool bridges the two as a **curation accelerator**: it parses every
``old > new`` line, locates the target tower/hero file, checks whether the
stated "old" value actually matches what's on disk, and buckets each change by
how safely it could be applied. It writes nothing — bloonswiki (via
``fetch_bloonswiki.py``) remains the authoritative source for the real numbers.

Confidence buckets
------------------
* ``CLEAN``   — a cost field whose current value equals the note's "old".
                Deterministic; safe to apply as a provisional patch.
* ``LIKELY``  — a combat stat whose "old" value is present in the file and the
                file is at a trusted baseline (>= v54). Needs field-locating.
* ``STALE``   — the file's ``game_version`` predates the patch baseline, so the
                note's "old" value can't be trusted to match. Use the wiki.
* ``REVIEW``  — additive ("+4"), relative ("doubled"), reworks, or "old" not
                found — a human must decide.
* ``NO_FILE`` — the subject (e.g. a hero we don't carry stats for) has no file.
* ``SCOPE``   — Powers / Bosses / Rogue / cosmetic: not a tower-stat file.

Usage
-----
    python3.10 scripts/btd6_patch_diff.py --notes-file v55.txt
    pbpaste | python3.10 scripts/btd6_patch_diff.py --notes-file -
    python3.10 scripts/btd6_patch_diff.py --notes-file v55.txt --json > proposed.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DATA = _REPO_ROOT / "disbot" / "data" / "btd6"

# Patch notes assume roughly the previous full release as a baseline; a file
# older than this can't be trusted to hold the note's stated "old" values.
_MIN_TRUSTED_BASELINE = (54, 0)

# "8 > 10", "$85,000 > $90,000", "600k > 650k", "6s > 18s", "+15 > +20".
_TRANSITION_RE = re.compile(
    r"(?P<old>[+\-]?\$?\d[\d,]*\.?\d*\s*[kKmMsS%]?)\s*(?:>|→|->)\s*"
    r"(?P<new>[+\-]?\$?\d[\d,]*\.?\d*\s*[kKmMsS%]?)",
)
# Leading tier/level token of a change line.
_TIER_RE = re.compile(
    r"^\s*(?:\((?P<paren>Paragon)\)|(?P<code>xx\d|x\dx|\dxx|\d{3})|Lv\s?(?P<lv>\d+))",
    re.IGNORECASE,
)
_BULLET_RE = re.compile(r"^\s*[*\-+]\s+")
_COST_RE = re.compile(r"\b(price|cost)\b", re.IGNORECASE)

# Section headers that scope subsequent lines out of tower-stat territory.
_SCOPE_HEADERS = {"powers", "bosses", "rogue"}
# Headers that merely precede real subjects (skip, don't treat as a subject).
_PASSTHROUGH_HEADERS = {"balance changes", "hero balance"}


@dataclass(frozen=True)
class Subject:
    name: str
    kind: str  # "tower" | "hero" | "scope"
    target_id: str | None


@dataclass
class Change:
    subject: str
    kind: str
    target_id: str | None
    tier: str | None
    text: str
    old_raw: str
    new_raw: str


@dataclass
class Assessment:
    bucket: str
    subject: str
    text: str
    detail: str
    file: str | None = None
    field: str | None = None
    old: float | None = None
    new: float | None = None


# ---------------------------------------------------------------------------
# Parsing helpers (pure)
# ---------------------------------------------------------------------------


def to_number(raw: str) -> float | None:
    """Normalise a note value (``$90,000`` / ``600k`` / ``18s`` / ``+4``)."""
    s = raw.strip().lower().replace("$", "").replace(",", "").replace("+", "")
    mult = 1.0
    if s.endswith("k"):
        mult, s = 1000.0, s[:-1]
    elif s.endswith("m"):
        mult, s = 1_000_000.0, s[:-1]
    elif s.endswith(("s", "%")):
        s = s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


def extract_transition(text: str) -> tuple[str, str] | None:
    """Return the last ``old > new`` pair in *text*, or ``None``.

    Uses the *last* match so a leading tier code (``xx4 ... 8 > 6``) or a
    descriptive number can't be mistaken for the transition.
    """
    matches = list(_TRANSITION_RE.finditer(text))
    if not matches:
        return None
    last = matches[-1]
    return last.group("old").strip(), last.group("new").strip()


def parse_tier(text: str) -> str | None:
    """Extract the leading tier/level token (``x5x``, ``Lv20``, ``Paragon``)."""
    m = _TIER_RE.match(text)
    if not m:
        return None
    if m.group("paren"):
        return "Paragon"
    if m.group("lv"):
        return f"Lv{m.group('lv')}"
    return m.group("code")


def tier_to_path(code: str | None) -> tuple[int, int] | None:
    """Map a single-upgrade code (``xx5``/``5xx``/``x4x``) to ``(path, tier)``.

    Crosspath states like ``052`` are not single upgrades, so they return
    ``None`` (cost lines never use that form).
    """
    if not code or len(code) != 3 or code.isdigit():
        return None
    for idx, ch in enumerate(code):
        if ch.isdigit() and ch != "0":
            return idx + 1, int(ch)
    return None


def build_index() -> dict[str, Subject]:
    """Lowercased canonical+alias name -> Subject, from towers.json/heroes.json."""
    index: dict[str, Subject] = {}

    def add(entries: list[dict[str, Any]], kind: str) -> None:
        for e in entries:
            names = [e["canonical"], *(e.get("aliases") or [])]
            for n in names:
                index[str(n).lower()] = Subject(e["canonical"], kind, e["id"])

    towers = json.loads((_DATA / "towers.json").read_text())
    heroes = json.loads((_DATA / "heroes.json").read_text())
    add(towers["towers"] if isinstance(towers, dict) else towers, "tower")
    add(heroes["heroes"] if isinstance(heroes, dict) else heroes, "hero")
    return index


def resolve_subject(line: str, index: dict[str, Subject]) -> Subject | None:
    """If *line* is a section/subject header, return the Subject it introduces."""
    if _BULLET_RE.match(line):
        return None
    stripped = line.strip()
    low = stripped.lower()
    if low in _PASSTHROUGH_HEADERS:
        return None
    for header in _SCOPE_HEADERS:
        if low == header or low.startswith(header + " "):
            return Subject(stripped.split()[0], "scope", None)
    # Longest known name that is a word-prefix of the line wins.
    for name in sorted(index, key=len, reverse=True):
        if low == name or low.startswith(name + " "):
            return index[name]
    return None


def parse_notes(text: str, index: dict[str, Subject]) -> list[Change]:
    """Walk the notes, attaching each ``old > new`` line to its subject."""
    changes: list[Change] = []
    subject: Subject | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        header = resolve_subject(line, index)
        if header is not None:
            subject = header
            continue
        if subject is None:
            continue
        body = _BULLET_RE.sub("", line).strip()
        transition = extract_transition(body)
        if transition is None:
            continue
        old_raw, new_raw = transition
        changes.append(
            Change(
                subject=subject.name,
                kind=subject.kind,
                target_id=subject.target_id,
                tier=parse_tier(body),
                text=body,
                old_raw=old_raw,
                new_raw=new_raw,
            ),
        )
    return changes


# ---------------------------------------------------------------------------
# Assessment (reads the stat files)
# ---------------------------------------------------------------------------


def _version_tuple(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in str(version).split("."):
        if chunk.isdigit():
            parts.append(int(chunk))
        else:
            break
    return tuple(parts)


def _collect_numbers(obj: Any, out: set[float]) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        out.add(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_numbers(v, out)


def _stats_path(change: Change, stats_dir: Path) -> Path:
    sub = "heroes/" if change.kind == "hero" else ""
    return stats_dir / f"{sub}{change.target_id}.json"


def _match_cost_field(
    data: dict[str, Any],
    change: Change,
    old: float | None,
) -> tuple[str, float] | None:
    """Locate the cost field a cost-line targets.

    Order: explicit paragon -> upgrade named in the note -> tier code -> a
    unique cost field whose current value equals the stated "old". The last
    fallback catches lines like "Upgrade cost 650k > 600k" whose paragon
    context lives in the section prose rather than the bullet itself.
    """
    low = change.text.lower()
    if "paragon" in low or change.tier == "Paragon":
        if "paragon_cost" in data:
            return "paragon_cost", float(data["paragon_cost"])
    upgrades = data.get("upgrades") or []
    for up in upgrades:
        name = str(up.get("name", "")).lower()
        if name and name in low:
            return f"upgrades[{up['path']}-{up['tier']}].cost", float(up["cost"])
    pt = tier_to_path(change.tier)
    if pt is not None:
        for up in upgrades:
            if (up.get("path"), up.get("tier")) == pt:
                return f"upgrades[{pt[0]}-{pt[1]}].cost", float(up["cost"])
    if old is not None:
        candidates: dict[str, float] = {}
        if "paragon_cost" in data:
            candidates["paragon_cost"] = float(data["paragon_cost"])
        for up in upgrades:
            candidates[f"upgrades[{up['path']}-{up['tier']}].cost"] = float(up["cost"])
        hits = [(k, v) for k, v in candidates.items() if abs(v - old) < 1e-6]
        if len(hits) == 1:
            return hits[0]
    return None


def assess(change: Change, stats_dir: Path) -> Assessment:
    base = Assessment(
        bucket="REVIEW",
        subject=change.subject,
        text=change.text,
        detail="",
    )
    old = to_number(change.old_raw)
    new = to_number(change.new_raw)
    base.old, base.new = old, new

    if change.kind == "scope":
        base.bucket = "SCOPE"
        base.detail = "Powers/Bosses/Rogue — not a tower-stat file."
        return base

    path = _stats_path(change, stats_dir)
    if change.target_id is None or not path.exists():
        base.bucket = "NO_FILE"
        base.detail = f"no stats file for {change.subject!r}"
        return base
    try:
        base.file = str(path.relative_to(_REPO_ROOT))
    except ValueError:
        base.file = str(path)

    if old is None or new is None:
        base.detail = "non-numeric / additive change — decide manually"
        return base

    data = json.loads(path.read_text())
    stale = _version_tuple(data.get("game_version", "0")) < _MIN_TRUSTED_BASELINE
    version = data.get("game_version", "?")

    if _COST_RE.search(change.text):
        found = _match_cost_field(data, change, old)
        if found is None:
            base.detail = "cost line but no matching cost field found"
            return base
        base.field, current = found
        if abs(current - old) < 1e-6:
            base.bucket = "CLEAN"
            base.detail = f"{base.field} = {current:g} matches old; set -> {new:g}"
        elif stale:
            base.bucket = "STALE"
            base.detail = f"file v{version}; {base.field}={current:g} != old {old:g}"
        else:
            base.detail = f"{base.field}={current:g} != note old {old:g} — verify"
        return base

    # Combat stat: gauge applicability by whether "old" appears in the file.
    numbers: set[float] = set()
    _collect_numbers(data, numbers)
    present = any(abs(n - old) < 1e-6 for n in numbers)
    if stale:
        base.bucket = "STALE"
        base.detail = f"file v{version} predates baseline — old value unreliable" + (
            "" if present else "; old value also absent"
        )
    elif present:
        base.bucket = "LIKELY"
        base.detail = (
            f"old {old:g} present in file (v{version}); locate field + crosspaths"
        )
    else:
        base.detail = f"old {old:g} not found in file (v{version}) — already changed or different field"
    return base


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_BUCKET_ORDER = ("CLEAN", "LIKELY", "STALE", "REVIEW", "NO_FILE", "SCOPE")
_BUCKET_BLURB = {
    "CLEAN": "verified — current value matches the note's old; safe provisional apply",
    "LIKELY": "old value present at a trusted baseline; needs field-locating",
    "STALE": "file predates the patch baseline; use bloonswiki",
    "REVIEW": "additive / relative / rework / not found — human decides",
    "NO_FILE": "no stat file for this subject",
    "SCOPE": "not a tower/hero stat (Powers/Bosses/Rogue/cosmetic)",
}


def render(assessments: list[Assessment]) -> str:
    by_bucket: dict[str, list[Assessment]] = {b: [] for b in _BUCKET_ORDER}
    for a in assessments:
        by_bucket.setdefault(a.bucket, []).append(a)
    lines: list[str] = ["", "BTD6 patch-notes → proposed stat edits (review only)", ""]
    counts = ", ".join(f"{b}:{len(by_bucket[b])}" for b in _BUCKET_ORDER)
    lines.append(f"  {counts}   (total {len(assessments)})")
    lines.append("")
    for b in _BUCKET_ORDER:
        items = by_bucket[b]
        if not items:
            continue
        lines.append(f"== {b} ({len(items)}) — {_BUCKET_BLURB[b]}")
        for a in items:
            head = f"  [{a.subject}] {a.text}"
            lines.append(head if len(head) <= 100 else head[:97] + "...")
            lines.append(f"      → {a.detail}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--notes-file",
        required=True,
        help="Path to the patch-notes text, or '-' for stdin.",
    )
    parser.add_argument(
        "--stats-dir",
        default=str(_DATA / "stats"),
        help="Override the stats directory (default: disbot/data/btd6/stats).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable proposed edits as JSON.",
    )
    args = parser.parse_args(argv)

    text = (
        sys.stdin.read()
        if args.notes_file == "-"
        else Path(args.notes_file).read_text(encoding="utf-8")
    )
    index = build_index()
    changes = parse_notes(text, index)
    assessments = [assess(c, Path(args.stats_dir)) for c in changes]

    if args.json:
        print(json.dumps([asdict(a) for a in assessments], indent=2))
    else:
        print(render(assessments))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
