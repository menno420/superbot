#!/usr/bin/env python3
"""Triage the AI review-log backlog exported by ``!aireview export``.

The bot records every question it got wrong or couldn't answer in ``ai_review_log``
(#1494). ``!aireview export`` dumps that backlog as JSON; this script turns the dump
into an actionable work-list — the bridge that generalizes the BTD6 "miss → regression
probe" loop (``tests/evals/btd6_corpus.py``) to any task.

It does three things, all **read-only** and offline:

1. **Group** entries by ``task`` / ``reason_code`` so the shape of the backlog is visible.
2. **Dedupe** by normalized question (``utils.ai_text_normalize``) so a question asked
   five times is one work item with five ids.
3. **Classify** each unique question into a suggested action:
     * ``preset`` — a user *corrected* the bot, so a vetted answer already exists (the
       correction). Author it as a preset (``!aireview preset from <id> …``).
     * ``fix``    — the bot didn't know (grounding/route gap). Root-cause fix + a probe.
     * ``infra``  — a provider outage / error, not a knowledge gap. Usually no action.

With ``--scaffold`` it also prints probe / preset stubs ready to paste.

Provenance: built 2026-06-30 (AI review-log answer-loop session). Disposable per
Q-0105 — confirm its grouping against a real export a couple of times before trusting
it; delete it if it proves unreliable. Stdlib-only (+ the repo's normalizer).

Usage:
    !aireview export            # in Discord → download / copy the JSON
    python3.10 scripts/ai_review_triage.py export.json
    python3.10 scripts/ai_review_triage.py < export.json
    python3.10 scripts/ai_review_triage.py export.json --scaffold
    python3.10 scripts/ai_review_triage.py export.json --json   # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DISBOT = _REPO_ROOT / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.ai_text_normalize import normalize_question  # noqa: E402

# reason_codes that mean "the provider/runtime failed", not "the bot lacked
# knowledge" — these are infra, not answerable by data/grounding.
_INFRA_REASONS = frozenset({"provider_unavailable", "errored", "degraded"})

ACTION_PRESET = "preset"
ACTION_FIX = "fix"
ACTION_INFRA = "infra"


def classify(entry: dict[str, Any]) -> str:
    """Suggested action for one raw export entry."""
    kind = (entry.get("kind") or "").lower()
    if kind == "correction" and (entry.get("correction") or "").strip():
        return ACTION_PRESET
    reason = (entry.get("reason_code") or "").lower()
    if reason in _INFRA_REASONS:
        return ACTION_INFRA
    return ACTION_FIX


def domain_of(entry: dict[str, Any]) -> str:
    """Coarse knowledge domain from the routed task (robust to exact strings)."""
    task = (entry.get("task") or "").lower()
    if "btd6" in task:
        return "btd6"
    if "projmoon" in task or "limbus" in task:
        return "projmoon"
    if "video" in task:
        return "video"
    if task:
        return "general"
    return "unrouted"


def load_entries(raw: str) -> list[dict[str, Any]]:
    """Parse an export blob — accepts the ``{schema, entries}`` wrapper or a bare list."""
    data = json.loads(raw)
    if isinstance(data, dict):
        entries = data.get("entries", [])
    elif isinstance(data, list):
        entries = data
    else:
        raise ValueError("export must be a JSON object or list")
    if not isinstance(entries, list):
        raise ValueError("'entries' must be a list")
    return [e for e in entries if isinstance(e, dict)]


class Item:
    """One deduped question + every raw entry that shares its normalized key."""

    def __init__(self, key: str) -> None:
        self.key = key
        self.entries: list[dict[str, Any]] = []

    def add(self, entry: dict[str, Any]) -> None:
        self.entries.append(entry)

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def ids(self) -> list[int]:
        out: list[int] = []
        for e in self.entries:
            try:
                out.append(int(e["id"]))
            except (KeyError, TypeError, ValueError):
                continue
        return out

    @property
    def question(self) -> str:
        for e in self.entries:
            q = (e.get("question") or "").strip()
            if q:
                return q
        return self.key or "(no question text captured)"

    @property
    def action(self) -> str:
        # If any entry carries a correction, a vetted answer exists → preset.
        actions = [classify(e) for e in self.entries]
        if ACTION_PRESET in actions:
            return ACTION_PRESET
        if ACTION_FIX in actions:
            return ACTION_FIX
        return ACTION_INFRA

    @property
    def domain(self) -> str:
        return domain_of(self.entries[0]) if self.entries else "unrouted"

    @property
    def correction(self) -> str:
        for e in self.entries:
            c = (e.get("correction") or "").strip()
            if c:
                return c
        return ""


def dedupe(entries: list[dict[str, Any]]) -> list[Item]:
    """Group entries by normalized question; most-repeated first."""
    items: OrderedDict[str, Item] = OrderedDict()
    for entry in entries:
        key = normalize_question(entry.get("question")) or f"__id_{entry.get('id')}"
        items.setdefault(key, Item(key)).add(entry)
    return sorted(items.values(), key=lambda it: (-it.count, it.key))


def build_report(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """The machine-readable triage summary (used by both text + --json output)."""
    items = dedupe(entries)
    by_task = Counter((e.get("task") or "(unrouted)") for e in entries)
    by_reason = Counter((e.get("reason_code") or "(none)") for e in entries)
    by_action = Counter(it.action for it in items)
    return {
        "total_entries": len(entries),
        "unique_questions": len(items),
        "by_task": dict(by_task.most_common()),
        "by_reason": dict(by_reason.most_common()),
        "by_action": dict(by_action.most_common()),
        "items": [
            {
                "action": it.action,
                "domain": it.domain,
                "count": it.count,
                "ids": it.ids,
                "question": it.question,
                "correction": it.correction,
                "key": it.key,
            }
            for it in items
        ],
    }


_ACTION_NOTE = {
    ACTION_PRESET: "user correction available → author a vetted preset",
    ACTION_FIX: "root-cause: add grounding/data/routing, then pin a regression probe",
    ACTION_INFRA: "provider/error — not a knowledge gap (no action unless recurring)",
}


def render_text(report: dict[str, Any]) -> str:
    """Human-readable triage report."""
    lines: list[str] = []
    lines.append(
        f"AI review backlog triage — {report['total_entries']} entries, "
        f"{report['unique_questions']} unique questions",
    )
    lines.append("")
    lines.append("By task:")
    for task, n in report["by_task"].items():
        lines.append(f"  {n:>4}  {task}")
    lines.append("")
    lines.append("By reason:")
    for reason, n in report["by_reason"].items():
        lines.append(f"  {n:>4}  {reason}")
    lines.append("")
    lines.append("Suggested actions:")
    for action, n in report["by_action"].items():
        lines.append(f"  {n:>4}  {action:<7} — {_ACTION_NOTE.get(action, '')}")
    lines.append("")
    lines.append("--- Unique questions (most-repeated first) ---")
    for item in report["items"]:
        ids = ",".join(str(i) for i in item["ids"]) or "?"
        head = f"[{item['action']} · {item['domain']} · x{item['count']} · ids {ids}]"
        lines.append(head)
        lines.append(f"  Q: {item['question']}")
        if item["correction"]:
            lines.append(f"  ↳ user correction: {item['correction']}")
    return "\n".join(lines)


def render_scaffold(report: dict[str, Any]) -> str:
    """Probe / preset stubs ready to paste into the corpus or a preset seed."""
    lines: list[str] = ["", "=== SCAFFOLD ===", ""]
    presets = [it for it in report["items"] if it["action"] == ACTION_PRESET]
    fixes = [it for it in report["items"] if it["action"] == ACTION_FIX]
    if presets:
        lines.append("# Preset candidates — a user already gave the right answer.")
        lines.append("# Author each with:  !aireview preset from <id> <answer>")
        for it in presets:
            first_id = it["ids"][0] if it["ids"] else "<id>"
            lines.append(f"#   !aireview preset from {first_id}")
            lines.append(f"#     Q: {it['question']}")
            lines.append(f"#     A: {it['correction'] or '<paste vetted answer>'}")
        lines.append("")
    if fixes:
        lines.append("# Root-cause fixes — add a regression probe per question.")
        lines.append("# BTD6 → tests/evals/btd6_corpus.py GROUNDING_PROBES:")
        for it in fixes:
            if it["domain"] != "btd6":
                continue
            q = it["question"].replace('"', '\\"')
            lines.append("GroundingProbe(")
            lines.append(f'    question="{q}",')
            lines.append('    expect=("<answer-bearing fact substring>",),')
            lines.append('    rubric="<what a correct live answer must say>",')
            lines.append(f"    note=\"from review-log ids {it['ids']}\",")
            lines.append("),")
        other = [it for it in fixes if it["domain"] != "btd6"]
        if other:
            lines.append("")
            lines.append("# Non-BTD6 fixes (general/projmoon/video) — triage by hand:")
            for it in other:
                lines.append(
                    f"#   [{it['domain']}] {it['question']}  (ids {it['ids']})",
                )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to the exported JSON (default: read stdin).",
    )
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="Also print probe/preset stubs ready to paste.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the machine-readable triage summary instead of text.",
    )
    args = parser.parse_args(argv)

    raw = (
        Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    )
    if not raw.strip():
        print("No input — paste an !aireview export JSON.", file=sys.stderr)
        return 2
    try:
        entries = load_entries(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Could not parse export: {exc}", file=sys.stderr)
        return 2

    report = build_report(entries)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    print(render_text(report))
    if args.scaffold:
        print(render_scaffold(report))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
