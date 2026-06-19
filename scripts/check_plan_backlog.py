#!/usr/bin/env python3.10
"""PLAN-BACKLOG-THIN reporter — is the band plan deep enough to reach the next pass? (stdlib, read-only).

WHY (Q-0164, added 2026-06-19): the reconciliation pass plans **enough genuine buildable
work to reach the next pass (depth ≥ the 30-PR cadence)**; when the idea backlog *genuinely
can't* fill the band, that is the signal to raise a loud ``⚠️ PLAN BACKLOG THIN`` flag so the
owner drops ideas or a dedicated planning session runs. Today that judgment is made by hand
each pass ("are we running low on plans?" — a vibe). This guard turns it into a **number**:
it parses the live ``reconciliation-pass-*-bandNNNN.md`` plan's §4 "next band" section,
counts the **buildable** slices (gate-tagged ``ready`` or ``plan-first``), and prints the THIN
condition when the buildable depth falls short of the target. It is the depth-axis
verified-signal sibling of the hand-written Q-0164 paragraph; the balance-axis sibling
(``⚑ Product lanes gated``) is a separate, later idea.

How the buildable depth is computed (the parse, so it can be checked by hand):

* The live band plan is the single non-``historical`` ``reconciliation-pass-*.md`` whose
  Status badge is ``plan`` and whose filename carries the highest ``bandNNNN``.
* Inside its ``## 4.`` … ``## 5.`` section, every queue-table **slice row** (first cell an
  ``A1`` / ``B2`` / ``C5``-style lane-slice id) is classified by the gate tag in its own row,
  or — when the row has none — the gate declared in its ``**Lane X — …**`` header. Buildable =
  ``ready`` or ``plan-first``; gated = ``creds`` / ``owner`` / ``data`` (work that needs an
  owner decision, prod creds, or sourced data first).
* Plans bundle multi-PR initiatives into a single table row (e.g. "Batches 2–4") and list
  some lanes as prose, not tables, so the **row count is a floor**. When the §4 section states
  an explicit ``Depth check … ~N[-M] … slices`` estimate, that count's **lower bound** is read
  too (the conservative reading) and the **effective buildable depth is the larger of the two**
  — respecting the planner's own honest judgment rather than under-counting it.

THIN fires when the effective buildable depth is below ``--min-buildable`` (default
``MIN_BUILDABLE_DEFAULT`` — a margin below the full cadence, because the planner has treated a
high-teens count as "enough to reach the next pass" in practice; pass ``--min-buildable 30`` to
demand a full band).

Run::

    python3.10 scripts/check_plan_backlog.py                    # warn-only (always exit 0)
    python3.10 scripts/check_plan_backlog.py --strict           # exit 1 when THIN
    python3.10 scripts/check_plan_backlog.py --min-buildable 30 # demand a full-cadence band
    python3.10 scripts/check_plan_backlog.py --json             # machine-readable summary

**Warn-only by design.** A THIN backlog is a *planning* signal for the reconciliation routine
/ a dedicated planning session, never a per-push merge blocker — so the default exit is 0 and
``--strict`` is the opt-in cadence gate. The check reasons over the *plan* docs, so it never
touches runtime code and never has to run a bot.

Reliability (Q-0105): **unverified** — this is a convenience nudge for the Q-0164 cadence,
not load-bearing runtime code. The "buildable depth" it reports is a *parse* of human-written
plan tables, so confirm its count against the §4 queue by hand a few times across sessions
before trusting its verdict, and **delete this script if it proves unreliable** over multiple
sessions rather than working around it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLANNING_DIR = REPO_ROOT / "docs" / "planning"

# The cadence: the next reconciliation pass fires every STEP-th merged PR (Q-0134, 30-PR band
# — kept identical to check_reconciliation_due.STEP on purpose; if that retunes, retune here).
STEP = 30

# Default THIN threshold. The Q-0164 rule is "depth ≥ the cadence", but in practice the planner
# has judged a high-teens buildable count as "enough to reach the next pass without inventing
# filler" (band-#1050's §4 Depth check: "~18–22 … No PLAN BACKLOG THIN flag"). So the default
# demands only *half* a cadence band — low enough to agree with that lived non-THIN judgment
# (the conservative 18-lower-bound reading still clears it), high enough to fire on a genuine
# drain. Pass --min-buildable 30 for a strict full-cadence demand.
MIN_BUILDABLE_DEFAULT = STEP // 2  # 15 at STEP=30

# Gate-state tags used in the §4 queue tables. Buildable = work an agent can pick up now;
# gated = needs an owner decision / prod creds / sourced data first (Q-0164 §3).
BUILDABLE_TAGS = ("ready", "plan-first")
GATED_TAGS = ("creds", "owner", "data")
_ALL_TAGS = BUILDABLE_TAGS + GATED_TAGS

# A live band plan: `reconciliation-pass-YYYY-MM-DD-bandNNNN.md`. The trailing bandNNNN is the
# cadence-band marker; the newest one with a `plan` Status badge is the live queue.
_BAND_FILE_RE = re.compile(r"reconciliation-pass-.*-band(\d+)\.md$")
_STATUS_RE = re.compile(r">\s*\*\*Status:\*\*\s*`([a-z]+)`")
# A queue-table slice row: a markdown table row whose first cell is a lane-slice id like
# `A1`, `B12`, `C5` (one uppercase letter + digits). Bold wrappers / whitespace tolerated.
_SLICE_ROW_RE = re.compile(r"^\|\s*\**([A-Z]\d+)\**\s*\|")
# A lane header: `**Lane A — consistency-linter (… all `ready`):**`
_LANE_HEADER_RE = re.compile(r"^\*\*Lane\s+([A-Z])\b")
# The §4 "next band" section header, and the next-section sentinel that ends it.
_NEXT_BAND_HEADER_RE = re.compile(r"^##\s*4\.")
_SECTION_HEADER_RE = re.compile(r"^##\s")
# An explicit author depth-check estimate inside §4: a count *anchored to the word "slices"*,
# e.g. "~18–22 genuine `ready`/`plan-first` slices" or "12 buildable slices". Anchoring on
# "slices" avoids picking up unrelated digits on the same line (PR numbers, "Q-0164"). For a
# range like "18–22" the **lower** bound is read — the conservative reading (the backlog must
# clear the threshold even at the pessimistic end of the author's own estimate).
_DEPTH_LINE_RE = re.compile(r"(?i)\bdepth check\b")
_SLICES_COUNT_RE = re.compile(
    r"~?\s*(\d+)\s*(?:[–\-]\s*\d+)?\s*(?:\S+\s+){0,4}?slices?\b",
    re.IGNORECASE,
)


def _tags_in(text: str) -> set[str]:
    """Gate tags appearing as backtick tokens (`` `ready` ``) in a line of plan text."""
    return {t for t in _ALL_TAGS if f"`{t}`" in text}


def _classify(row_tags: set[str], lane_tags: set[str]) -> str:
    """Classify one slice → 'buildable' | 'gated'.

    A slice is *gated* only when its own row (or, failing that, its lane header) carries a
    gated tag and **no** buildable tag — so a "plan-first → then ready" lane reads buildable.
    A slice with no tag at all inherits its lane's tags; if neither has any tag, the §4
    contract ("every slot is a real, ungated slice unless tagged") makes it buildable.
    """
    tags = row_tags or lane_tags
    if tags & set(BUILDABLE_TAGS):
        return "buildable"
    if tags & set(GATED_TAGS):
        return "gated"
    return "buildable"  # untagged → ungated by the §4 convention


@dataclass(frozen=True)
class Slice:
    slice_id: str
    classification: str  # 'buildable' | 'gated'
    tags: tuple[str, ...]


@dataclass(frozen=True)
class BacklogReport:
    plan_path: Path | None
    band: int | None
    buildable_rows: int  # buildable slices counted from the queue tables (a floor)
    gated_rows: int
    total_rows: int
    stated_depth: (
        int | None
    )  # the author's "Depth check" lower bound, if the plan states one
    effective_depth: (
        int  # max(buildable_rows, stated_depth or 0) — the depth THIN compares
    )
    threshold: int
    thin: bool
    slices: tuple[Slice, ...]


def find_live_band_plan(planning_dir: Path = PLANNING_DIR) -> Path | None:
    """The newest live (`Status: plan`) `reconciliation-pass-*-bandNNNN.md` by band number."""
    best: tuple[int, Path] | None = None
    for path in sorted(planning_dir.glob("reconciliation-pass-*.md")):
        match = _BAND_FILE_RE.search(path.name)
        if not match:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        status = _STATUS_RE.search(text)
        if not status or status.group(1) != "plan":
            continue
        band = int(match.group(1))
        if best is None or band > best[0]:
            best = (band, path)
    return best[1] if best else None


def _next_band_lines(text: str) -> list[str]:
    """The lines inside the `## 4.` (next band) section, up to the next `## ` header."""
    lines = text.splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        if _NEXT_BAND_HEADER_RE.match(line):
            in_section = True
            continue
        if in_section and _SECTION_HEADER_RE.match(line):
            break
        if in_section:
            out.append(line)
    return out


def parse_slices(lines: list[str]) -> list[Slice]:
    """Parse the §4 queue-table slice rows into classified Slices.

    Walks the next-band section top-to-bottom, tracking the current lane header's gate tags;
    each slice row inherits them when its own row is untagged.
    """
    slices: list[Slice] = []
    lane_tags: set[str] = set()
    for line in lines:
        header = _LANE_HEADER_RE.match(line)
        if header:
            lane_tags = _tags_in(line)
            continue
        row = _SLICE_ROW_RE.match(line)
        if not row:
            continue
        row_tags = _tags_in(line)
        classification = _classify(row_tags, lane_tags)
        effective = sorted(row_tags or lane_tags)
        slices.append(Slice(row.group(1), classification, tuple(effective)))
    return slices


def parse_stated_depth(lines: list[str]) -> int | None:
    """The author's explicit 'Depth check … ~N[-M] … slices' lower bound, if §4 states one.

    Anchored to a 'Depth check' line (the note often wraps onto the following line, so a
    2-line window is searched), then to the first count that precedes the word 'slices' — so
    PR numbers / 'Q-0164' on the same line are ignored. A range like '~18–22 … slices' yields
    its **lower** bound (18), the conservative reading.
    """
    for idx, line in enumerate(lines):
        if not _DEPTH_LINE_RE.search(line):
            continue
        window = " ".join(lines[idx : idx + 2])  # the depth note often wraps one line
        match = _SLICES_COUNT_RE.search(window)
        if match:
            return int(match.group(1))
    return None


def build_report(
    plan_path: Path | None = None,
    threshold: int = MIN_BUILDABLE_DEFAULT,
    planning_dir: Path = PLANNING_DIR,
) -> BacklogReport:
    """Compute the buildable-depth backlog report against ``threshold``."""
    if plan_path is None:
        plan_path = find_live_band_plan(planning_dir)
    if plan_path is None:
        return BacklogReport(
            plan_path=None,
            band=None,
            buildable_rows=0,
            gated_rows=0,
            total_rows=0,
            stated_depth=None,
            effective_depth=0,
            threshold=threshold,
            thin=False,
            slices=(),
        )
    band_match = _BAND_FILE_RE.search(plan_path.name)
    band = int(band_match.group(1)) if band_match else None
    lines = _next_band_lines(plan_path.read_text(encoding="utf-8"))
    slices = parse_slices(lines)
    buildable = sum(1 for s in slices if s.classification == "buildable")
    gated = sum(1 for s in slices if s.classification == "gated")
    stated = parse_stated_depth(lines)
    effective = max(buildable, stated or 0)
    return BacklogReport(
        plan_path=plan_path,
        band=band,
        buildable_rows=buildable,
        gated_rows=gated,
        total_rows=len(slices),
        stated_depth=stated,
        effective_depth=effective,
        threshold=threshold,
        thin=effective < threshold,
        slices=tuple(slices),
    )


def _report_dict(report: BacklogReport) -> dict[str, object]:
    return {
        "plan": (
            str(report.plan_path.relative_to(REPO_ROOT)) if report.plan_path else None
        ),
        "band": report.band,
        "buildable_rows": report.buildable_rows,
        "gated_rows": report.gated_rows,
        "total_rows": report.total_rows,
        "stated_depth": report.stated_depth,
        "effective_depth": report.effective_depth,
        "cadence": STEP,
        "threshold": report.threshold,
        "thin": report.thin,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="PLAN-BACKLOG-THIN reporter (Q-0164): is the band plan deep enough?",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when the buildable backlog is THIN (below --min-buildable)",
    )
    parser.add_argument(
        "--min-buildable",
        type=int,
        default=MIN_BUILDABLE_DEFAULT,
        metavar="N",
        help=(
            "minimum effective buildable depth before THIN fires "
            f"(default {MIN_BUILDABLE_DEFAULT}; pass {STEP} to demand a full cadence band)"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print a machine-readable summary instead of prose",
    )
    args = parser.parse_args(argv)

    report = build_report(threshold=args.min_buildable)

    if args.json:
        print(json.dumps(_report_dict(report), indent=2))
        return 1 if (args.strict and report.thin) else 0

    if report.plan_path is None:
        print(
            "check_plan_backlog: no live `reconciliation-pass-*-bandNNNN.md` plan "
            "(Status: `plan`) found in docs/planning/ — can't compute buildable depth. "
            "This is informational; the next reconciliation pass writes the band plan.",
        )
        return 0

    rel = report.plan_path.relative_to(REPO_ROOT)
    stated = (
        f", author depth-check ~{report.stated_depth}"
        if report.stated_depth is not None
        else ""
    )
    detail = (
        f"effective buildable depth {report.effective_depth} "
        f"({report.buildable_rows} buildable queue rows{stated}; "
        f"{report.gated_rows} gated, {report.total_rows} total rows) "
        f"vs. threshold {report.threshold} (cadence {STEP})"
    )
    if report.thin:
        print(
            f"check_plan_backlog: ⚠️ PLAN BACKLOG THIN — band #{report.band} plan ({rel}): "
            f"{detail}. Per Q-0164, raise the `⚠️ PLAN BACKLOG THIN` flag (current-state "
            "▶ Next action + the run-report ⚑ Owner-decisions line): promote what's honest, "
            "then ask the owner to drop ideas or run a dedicated planning session.",
        )
        return 1 if args.strict else 0

    print(
        f"check_plan_backlog: OK — band #{report.band} plan ({rel}): {detail}. "
        "Backlog is deep enough to reach the next reconciliation pass.",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
