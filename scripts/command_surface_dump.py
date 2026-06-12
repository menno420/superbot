#!/usr/bin/env python3
"""Offline command-surface dump for SuperBot.

Reads cog source via AST and emits every prefix/slash/group command by
subsystem — no live bot or Postgres connection required.

    python3.10 scripts/command_surface_dump.py               # table (default)
    python3.10 scripts/command_surface_dump.py --json        # JSON
    python3.10 scripts/command_surface_dump.py --diff-checklist  # gap report
    python3.10 scripts/command_surface_dump.py --cog economy_cog.py

Fills the gap noted in .sessions/2026-06-12-untested-surface-checklist.md:
the untested-surface checklist was built by manual AST-grep; this script
makes it machine-verifiable so new commands are never silently missed.

Read-only; no Discord / database dependency; usable in CI pre-checks.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parent.parent
COGS_DIR = REPO_ROOT / "disbot" / "cogs"
CHECKLIST_PATH = REPO_ROOT / "docs" / "audits" / "untested-surface-checklist.md"

Kind = Literal["prefix", "slash", "group"]


# ---------------------------------------------------------------------------
# Permission-hint classification
# ---------------------------------------------------------------------------

_ADMIN_MARKERS = {
    "is_admin_or_owner",
    "is_owner",
}
_PERM_KEYWORDS = {
    "administrator": "admin",
    "manage_guild": "manage_guild",
    "manage_channels": "manage_channels",
    "manage_roles": "manage_roles",
    "manage_messages": "manage_messages",
    "manage_members": "manage_members",
    "moderate_members": "moderate_members",
    "create_instant_invite": "create_invite",
}


def _perm_hint_from_decorators(decorator_list: list[ast.expr]) -> str:
    """Best-effort permission tier from a method's decorator list."""
    for dec in decorator_list:
        # @is_admin_or_owner() / @commands.is_owner() / @is_owner()
        func = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(func, ast.Name) and func.id in _ADMIN_MARKERS:
            return "admin"
        if isinstance(func, ast.Attribute) and func.attr in {"is_owner"}:
            return "admin"
        # @commands.has_permissions(...) / @app_commands.checks.has_permissions(...)
        if isinstance(dec, ast.Call):
            for kw in dec.keywords:
                if kw.arg in _PERM_KEYWORDS:
                    return _PERM_KEYWORDS[kw.arg]
    return "member"


# ---------------------------------------------------------------------------
# AST extraction
# ---------------------------------------------------------------------------


@dataclass
class CommandEntry:
    name: str
    aliases: list[str]
    kind: Kind
    perm: str  # admin | manage_* | member
    cog_file: str  # relative to COGS_DIR parent
    lineno: int


def _decorator_kind_and_name(
    dec: ast.expr,
) -> tuple[Kind, str | None, list[str]] | None:
    """Return (kind, explicit_name, aliases) if the decorator is a command decorator, else None."""
    if not isinstance(dec, ast.Call):
        return None

    func = dec.func
    if not isinstance(func, ast.Attribute):
        return None

    attr = func.attr
    parent = func.value

    # Determine kind
    if attr == "command":
        if isinstance(parent, ast.Name) and parent.id == "app_commands":
            kind: Kind = "slash"
        elif isinstance(parent, ast.Attribute) and parent.attr == "checks":
            return None  # app_commands.checks.has_permissions etc.
        elif isinstance(parent, ast.Name) and parent.id == "commands":
            kind = "prefix"
        else:
            return None
    elif attr == "group" and isinstance(parent, ast.Name) and parent.id == "commands":
        kind = "group"
    else:
        return None

    # Extract name= and aliases= kwargs
    name_val: str | None = None
    aliases: list[str] = []
    for kw in dec.keywords:
        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
            name_val = str(kw.value.value)
        elif kw.arg == "aliases" and isinstance(kw.value, (ast.List, ast.Tuple)):
            aliases = [
                str(elt.value) for elt in kw.value.elts if isinstance(elt, ast.Constant)
            ]

    return kind, name_val, aliases


def _extract_from_file(path: Path) -> list[CommandEntry]:
    """Parse one cog file and return its CommandEntry list."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []

    rel = str(path.relative_to(REPO_ROOT / "disbot"))
    entries: list[CommandEntry] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in ast.walk(node):
            if not isinstance(item, ast.AsyncFunctionDef):
                continue
            for dec in item.decorator_list:
                result = _decorator_kind_and_name(dec)
                if result is None:
                    continue
                kind, explicit_name, aliases = result
                name = explicit_name if explicit_name else item.name
                perm = _perm_hint_from_decorators(item.decorator_list)
                entries.append(
                    CommandEntry(
                        name=name,
                        aliases=aliases,
                        kind=kind,
                        perm=perm,
                        cog_file=rel,
                        lineno=item.lineno,
                    ),
                )
                break  # one command decorator per method is the norm

    return entries


def collect(cog_filter: str | None = None) -> list[CommandEntry]:
    """Return all CommandEntry objects across all cog files."""
    all_entries: list[CommandEntry] = []
    for path in sorted(COGS_DIR.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        if cog_filter and path.name != cog_filter:
            continue
        all_entries.extend(_extract_from_file(path))
    return all_entries


# ---------------------------------------------------------------------------
# Checklist diff
# ---------------------------------------------------------------------------

_CMD_PATTERN = re.compile(r"`([!/][a-z][a-z0-9_\-]*)`")


def _checklist_commands() -> set[str]:
    """Names mentioned in the untested-surface checklist (without ! or / prefix)."""
    if not CHECKLIST_PATH.exists():
        return set()
    names: set[str] = set()
    for m in _CMD_PATTERN.finditer(CHECKLIST_PATH.read_text(encoding="utf-8")):
        names.add(m.group(1).lstrip("!/"))
    return names


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

_KIND_LABEL = {"prefix": "!", "slash": "/", "group": "!grp"}
_PERM_ORDER = [
    "admin",
    "manage_guild",
    "manage_channels",
    "manage_roles",
    "manage_messages",
    "manage_members",
    "moderate_members",
    "create_invite",
    "member",
]


def _table(entries: list[CommandEntry]) -> None:
    # Group by cog_file
    by_cog: dict[str, list[CommandEntry]] = {}
    for e in entries:
        by_cog.setdefault(e.cog_file, []).append(e)

    for cog_file, group in sorted(by_cog.items()):
        print(f"\n{cog_file}")
        print("-" * len(cog_file))
        for e in sorted(group, key=lambda x: x.name):
            prefix = _KIND_LABEL.get(e.kind, e.kind)
            alias_str = f"  aliases: {', '.join(e.aliases)}" if e.aliases else ""
            print(f"  {prefix}{e.name:<28} [{e.perm}]{alias_str}")


def _json_output(entries: list[CommandEntry]) -> None:
    data = [
        {
            "name": e.name,
            "aliases": e.aliases,
            "kind": e.kind,
            "perm": e.perm,
            "cog_file": e.cog_file,
            "lineno": e.lineno,
        }
        for e in entries
    ]
    print(json.dumps(data, indent=2))


def _diff_checklist(entries: list[CommandEntry]) -> int:
    """Print commands present in source but absent from the checklist. Returns exit code."""
    checklist_names = _checklist_commands()
    missing: list[CommandEntry] = []
    for e in entries:
        all_names = {e.name} | set(e.aliases)
        if not all_names & checklist_names:
            missing.append(e)

    if not missing:
        print("All source commands have a checklist entry.")
        return 0

    print(f"{len(missing)} command(s) in source with no checklist entry:\n")
    for e in sorted(missing, key=lambda x: (x.cog_file, x.name)):
        prefix = _KIND_LABEL.get(e.kind, e.kind)
        alias_str = f" (aliases: {', '.join(e.aliases)})" if e.aliases else ""
        print(f"  {prefix}{e.name}{alias_str}  [{e.perm}]  ({e.cog_file}:{e.lineno})")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dump the bot's command surface from cog source (no live bot needed).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a table.",
    )
    parser.add_argument(
        "--diff-checklist",
        action="store_true",
        help="Report commands present in source but absent from the untested-surface checklist.",
    )
    parser.add_argument(
        "--cog",
        metavar="FILENAME",
        help="Restrict to a single cog file (e.g. economy_cog.py).",
    )
    args = parser.parse_args(argv)

    entries = collect(cog_filter=args.cog)

    if not entries:
        print("No command entries found.", file=sys.stderr)
        return 1

    if args.diff_checklist:
        return _diff_checklist(entries)
    if args.json:
        _json_output(entries)
    else:
        print(
            f"Command surface — {len(entries)} entries from {COGS_DIR.relative_to(REPO_ROOT)}",
        )
        _table(entries)
    return 0


if __name__ == "__main__":
    sys.exit(main())
