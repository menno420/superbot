#!/usr/bin/env python3.10
"""Scan the bot's settings-key constants into a catalogue (stdlib only, read-only).

The developer dashboard (``docs/planning/developer-dashboard-plan.md``) wants to
show **every per-guild setting the bot exposes**: which configuration keys exist,
what subsystem owns each, and the stable string key behind each constant. That
inventory already lives, one source of truth, in ``disbot/utils/settings_keys/``
— each submodule groups the keys for one subsystem as ``NAME = "stable_key"``
module-level constants, with a docstring naming the owning subsystem.

This scanner AST-parses those submodules (so quoting/formatting never matters)
and emits one record per domain::

    {
        "domain": "xp",
        "purpose": "Settings keys owned by the XP subsystem (cogs.xp_cog).",
        "keys": [
            {"constant": "XP_MIN", "key": "xp_min"},
            {"constant": "XP_MAX", "key": "xp_max"},
            ...
        ],
    }

It reads only constant **names and their stable key strings** — never a *value*
a guild has set (those live in the bot's database, behind the runtime). Pure
stdlib so it runs in CI with no extra dependencies, mirroring
``scripts/scan_env_usage.py`` / ``scripts/scan_commands.py`` (which
``scripts/export_dashboard_data.py`` embeds in ``dashboard/data/dashboard.json``).

Run standalone to print the catalogue::

    python3.10 scripts/scan_settings.py            # human-readable summary
    python3.10 scripts/scan_settings.py --json     # the raw JSON payload

Reliability (Q-0105): **unverified** — confirm the catalogue against
``disbot/utils/settings_keys/`` a few times across sessions before trusting it,
and delete this seam if it proves unreliable. It is a convenience generator, not
load-bearing runtime code.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KEYS_DIR = REPO_ROOT / "disbot" / "utils" / "settings_keys"


def _first_doc_line(tree: ast.Module) -> str:
    """First line of a module docstring (the owning-subsystem note), or ''."""
    doc = ast.get_docstring(tree)
    if not doc:
        return ""
    return doc.strip().splitlines()[0].strip()


def _string_constants(tree: ast.Module) -> list[tuple[str, str]]:
    """Module-level ``NAME = "value"`` string constants, in source order.

    A settings key is always a ``str`` (it is the DB column key). Non-string
    module constants (the occasional tuple/int) are skipped — they are not keys.
    """
    out: list[tuple[str, str]] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        value = node.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            out.append((target.id, value.value))
    return out


def scan_settings(keys_dir: Path = DEFAULT_KEYS_DIR) -> list[dict]:
    """Build the settings-key catalogue from ``settings_keys/*.py``.

    One record per submodule (domain), sorted by domain name; the package
    ``__init__`` is skipped (it only re-exports the per-domain surface).
    Returns names + stable keys only — never a guild's stored value.
    """
    records: list[dict] = []
    for path in sorted(keys_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        keys = [
            {"constant": const, "key": key} for const, key in _string_constants(tree)
        ]
        if not keys:
            continue
        records.append(
            {
                "domain": path.stem,
                "purpose": _first_doc_line(tree),
                "keys": keys,
            },
        )
    records.sort(key=lambda r: r["domain"])
    return records


def _format_summary(records: list[dict]) -> str:
    """Render a short human-readable catalogue for the CLI."""
    total = sum(len(r["keys"]) for r in records)
    lines = [f"{total} setting key(s) across {len(records)} domain(s):\n"]
    for record in records:
        lines.append(
            f"  {record['domain']} ({len(record['keys'])}) — {record['purpose']}",
        )
        for entry in record["keys"]:
            lines.append(f"    {entry['constant']:<34} {entry['key']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: print the settings catalogue (summary / JSON)."""
    parser = argparse.ArgumentParser(
        description="Scan the bot's settings-key constants (names + stable keys only).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the raw JSON payload instead of the human summary",
    )
    args = parser.parse_args(argv)

    records = scan_settings()
    if args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        print(_format_summary(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
