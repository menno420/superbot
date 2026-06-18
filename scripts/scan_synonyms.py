#!/usr/bin/env python3.10
"""Scan the bot's command-synonym map into a catalogue (stdlib only, read-only).

The bot resolves "soft" command aliases through a single dict,
``COMMAND_SYNONYMS`` in ``disbot/utils/synonyms.py`` (canonical command name →
the synonyms that resolve to it on the command-not-found path, via
``find_command``). The developer dashboard's **alias-suggestion** page
(`/aliases`) needs this map so it can show what already resolves and reject a
suggestion that collides with an existing synonym.

This scanner ``literal_eval``s that dict (it is all string literals) and emits::

    [{"canonical": "help", "synonyms": ["hilfe", "commands", "cmds", ...]}, ...]

Pure stdlib so it runs in CI with no extra dependencies, mirroring the other
``scripts/scan_*.py`` seams (which ``scripts/export_dashboard_data.py`` embeds in
``dashboard/data/dashboard.json``).

Run standalone::

    python3.10 scripts/scan_synonyms.py            # human-readable summary
    python3.10 scripts/scan_synonyms.py --json     # the raw JSON payload

Reliability (Q-0105): **unverified** — confirm the map against
``disbot/utils/synonyms.py`` a few times across sessions before trusting it, and
delete this seam if it proves unreliable. Convenience generator, not runtime code.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SYNONYMS = REPO_ROOT / "disbot" / "utils" / "synonyms.py"


def scan_synonyms(path: Path = DEFAULT_SYNONYMS) -> list[dict]:
    """Return the ``COMMAND_SYNONYMS`` map as canonical→synonyms records."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    for node in ast.walk(tree):
        # ``COMMAND_SYNONYMS = {...}`` (Assign) or the annotated
        # ``COMMAND_SYNONYMS: dict[...] = {...}`` (AnnAssign) form.
        value: ast.expr | None = None
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "COMMAND_SYNONYMS"
                for t in node.targets
            )
            or (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == "COMMAND_SYNONYMS"
            )
        ):
            value = node.value
        if value is not None:
            try:
                mapping = ast.literal_eval(value)
            except (ValueError, TypeError, SyntaxError):
                return []
            if not isinstance(mapping, dict):
                return []
            return [
                {"canonical": str(canonical), "synonyms": [str(s) for s in syns]}
                for canonical, syns in sorted(mapping.items())
                if isinstance(syns, (list, tuple))
            ]
    return []


def _format_summary(records: list[dict]) -> str:
    """Render a short human-readable map for the CLI."""
    total = sum(len(r["synonyms"]) for r in records)
    lines = [f"{total} synonym(s) over {len(records)} command(s):\n"]
    for record in records:
        lines.append(f"  {record['canonical']:<16} ← {', '.join(record['synonyms'])}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: print the synonym map (summary / JSON)."""
    parser = argparse.ArgumentParser(
        description="Scan the bot's COMMAND_SYNONYMS map (read-only).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the raw JSON payload instead of the human summary",
    )
    args = parser.parse_args(argv)

    records = scan_synonyms()
    if args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        print(_format_summary(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
