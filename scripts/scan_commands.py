#!/usr/bin/env python3.10
"""Scan ``disbot/cogs/**`` for the command surface (stdlib, AST only).

Produces the data behind the dashboard's `/commands` cog-and-command explorer:
every cog, the commands it declares, each command's **invocation type**
(prefix / slash / both), and whether it is **button-backed** (a panel action or a
command that opens a Discord UI view). Never imports ``disbot`` — pure AST, so it
runs in CI with no extra dependencies.

Invocation type is read from the decorator:

* ``@commands.command`` / ``@commands.group``            -> ``prefix``
* ``@app_commands.command`` / ``@app_commands.group``    -> ``slash``
* ``@commands.hybrid_command`` / ``@commands.hybrid_group`` -> ``both``
* ``@<group>.command`` / ``@<group>.group``              -> subcommand (inherits
  the parent group's type)

Button-backed is the project's own model (see
``core/runtime/command_surface_ledger.py``): a command declared
``extras={"classification": "panel_action"}`` *is* a panel button's action, and a
command whose body opens a view (``panel_manager`` / ``send_panel`` / ``*View(`` /
``view=``) shows buttons. Either makes ``button_backed`` true.

Reliability (Q-0105): **unverified** — confirm against the live ledger a few times
before trusting it; delete this seam if it drifts. It is a convenience generator.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COGS_DIR = REPO_ROOT / "disbot" / "cogs"

# decorator path -> (invocation type, is_group)
_COMMAND_DECORATORS: dict[str, tuple[str, bool]] = {
    "commands.command": ("prefix", False),
    "command": ("prefix", False),
    "commands.hybrid_command": ("both", False),
    "hybrid_command": ("both", False),
    "app_commands.command": ("slash", False),
    "commands.group": ("prefix", True),
    "group": ("prefix", True),
    "commands.hybrid_group": ("both", True),
    "hybrid_group": ("both", True),
    "app_commands.group": ("slash", True),
    # module-level registrations (e.g. bot1.py's @bot.command / @bot.tree.command)
    "bot.command": ("prefix", False),
    "bot.group": ("prefix", True),
    "bot.tree.command": ("slash", False),
    "tree.command": ("slash", False),
}
_SUBCOMMAND_LEAVES = {"command", "group", "subcommand"}
_PANEL_TOKENS = ("panel_manager", "send_panel", "View(", "view=")
# Acronym-aware CamelCase -> snake_case: split before a Capitalised word that
# follows an acronym run (HTTPServer -> HTTP_Server) and between a lower/digit
# and a capital (RockPaper -> Rock_Paper); an acronym (+digit) run stays whole.
_ACRONYM_BOUNDARY_RE = re.compile(r"([A-Z]+)([A-Z][a-z])")
_WORD_BOUNDARY_RE = re.compile(r"([a-z0-9])([A-Z])")

# Cog classes whose derived snake_case name is NOT their registry subsystem key.
# These cogs belong to a parent subsystem (the split into sub-cogs is an
# implementation detail), so the dashboard joins them to the parent's registry
# entry (emoji / display name / routing key) instead of rendering them generic.
# Verified against utils/subsystem_registry.py: ``btd6`` ("BTD6 Assistant") and
# ``rps_tournament`` ("Rock Paper Scissors") are real subsystem keys. Cogs whose
# parent is genuinely ambiguous (ParagonCog / SetupCog / HermesCog) are NOT mapped
# here — they stay in check_dashboard_data's unresolved allow-list, by intent.
_COG_SUBSYSTEM_OVERRIDES: dict[str, str] = {
    "BTD6EventsCog": "btd6",
    "BTD6OpsCog": "btd6",
    "BTD6ReferenceCog": "btd6",
    "BTD6StrategyCog": "btd6",
    "RockPaperScissorsCog": "rps_tournament",
}


def _truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _cog_to_subsystem(class_name: str) -> str:
    """Normalise a cog class name to its snake_case subsystem key.

    An explicit override wins first (a sub-cog whose registry subsystem is its
    parent's, e.g. ``BTD6EventsCog`` -> ``btd6``). Otherwise acronym-aware so a
    run of capitals stays together: ``AICog`` -> ``ai``, ``BTD6Cog`` -> ``btd6``,
    ``XPCog`` -> ``xp`` — the snake_case keys the SUBSYSTEMS registry actually
    uses, not ``a_i`` / ``b_t_d6`` / ``x_p``. This makes the dashboard's
    cog->subsystem join (header emoji/name + the routing key) resolve instead of
    silently falling back to a generic card.
    """
    if class_name in _COG_SUBSYSTEM_OVERRIDES:
        return _COG_SUBSYSTEM_OVERRIDES[class_name]
    base = class_name[:-3] if class_name.endswith("Cog") else class_name
    step1 = _ACRONYM_BOUNDARY_RE.sub(r"\1_\2", base)
    return _WORD_BOUNDARY_RE.sub(r"\1_\2", step1).lower()


def _is_cog(class_node: ast.ClassDef) -> bool:
    """True if the class subclasses ``commands.Cog`` (a real, loadable cog).

    A command-bearing *mixin* (e.g. ``PlatformCommandsMixin``) returns False — its
    commands are real (inherited by a cog) but it is not itself a loaded cog, so it
    must not inflate the cog count.
    """
    for base in class_node.bases:
        node: ast.expr = base
        while isinstance(node, ast.Attribute):
            if node.attr.endswith("Cog"):
                return True
            node = node.value
        if isinstance(node, ast.Name) and node.id.endswith("Cog"):
            return True
    return False


def _decorator_path(dec: ast.expr) -> str:
    """Dotted path of a decorator, e.g. ``commands.command`` or ``mygroup.command``."""
    node = dec.func if isinstance(dec, ast.Call) else dec
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _kwarg(call: ast.Call | None, name: str) -> object:
    if call is None:
        return None
    for kw in call.keywords:
        if kw.arg == name:
            try:
                return ast.literal_eval(kw.value)
            except (ValueError, TypeError, SyntaxError):
                return None
    return None


def _classification(call: ast.Call | None) -> str:
    extras = _kwarg(call, "extras")
    if isinstance(extras, dict):
        value = extras.get("classification") or extras.get("alias_classification")
        if isinstance(value, str):
            return value
    return ""


def _docstring_first_line(method: ast.AST) -> str:
    doc = (
        ast.get_docstring(method)
        if isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef)
        else None
    )
    return doc.strip().splitlines()[0] if doc else ""


def _find_groups(class_node: ast.ClassDef) -> dict[str, tuple[str, str]]:
    """Map a group *method* name -> (command name, invocation type)."""
    groups: dict[str, tuple[str, str]] = {}
    for item in class_node.body:
        if not isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for dec in item.decorator_list:
            path = _decorator_path(dec)
            spec = _COMMAND_DECORATORS.get(path)
            if spec and spec[1]:  # is a group
                call = dec if isinstance(dec, ast.Call) else None
                name = _kwarg(call, "name")
                gname = name if isinstance(name, str) else item.name
                groups[item.name] = (gname, spec[0])
    return groups


def _scan_method(
    method: ast.AST,
    source: str,
    groups: dict[str, tuple[str, str]],
) -> dict | None:
    if not isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef):
        return None
    kind: str | None = None
    is_group = False
    parent: str | None = None
    call: ast.Call | None = None
    for dec in method.decorator_list:
        path = _decorator_path(dec)
        spec = _COMMAND_DECORATORS.get(path)
        if spec is not None:
            kind, is_group = spec
            call = dec if isinstance(dec, ast.Call) else None
            break
        parts = path.split(".")
        if len(parts) == 2 and parts[0] in groups and parts[1] in _SUBCOMMAND_LEAVES:
            parent, kind = groups[parts[0]]
            is_group = parts[1] == "group"
            call = dec if isinstance(dec, ast.Call) else None
            break
    if kind is None:
        return None
    name = _kwarg(call, "name")
    cmd_name = name if isinstance(name, str) else method.name
    aliases = _kwarg(call, "aliases")
    brief = _kwarg(call, "brief") or _kwarg(call, "description") or _kwarg(call, "help")
    if not isinstance(brief, str) or not brief:
        brief = _docstring_first_line(method)
    classification = _classification(call)
    body = ast.get_source_segment(source, method) or ""
    has_panel = any(tok in body for tok in _PANEL_TOKENS)
    return {
        "name": cmd_name,
        "type": kind,
        "is_group": is_group,
        "parent": parent,
        "aliases": (
            [a for a in aliases if isinstance(a, str)]
            if isinstance(aliases, list)
            else []
        ),
        "brief": _truncate(brief, 160),
        "classification": classification,
        "has_panel": has_panel,
        "button_backed": classification == "panel_action" or has_panel,
    }


def _scan_class(class_node: ast.ClassDef, source: str, rel_path: str) -> dict | None:
    groups = _find_groups(class_node)
    commands: list[dict] = []
    for item in class_node.body:
        cmd = _scan_method(item, source, groups)
        if cmd is not None:
            commands.append(cmd)
    if not commands:
        return None
    commands.sort(key=lambda c: (c["parent"] or "", c["name"]))
    return {
        "cog": class_node.name,
        "file": rel_path,
        "subsystem": _cog_to_subsystem(class_node.name),
        "is_cog": _is_cog(class_node),
        "commands": commands,
    }


def _scan_module(tree: ast.Module, source: str, rel_path: str) -> dict | None:
    """Scan module-level functions (e.g. ``bot1.py``'s ``@bot.command``)."""
    commands: list[dict] = []
    for item in tree.body:
        cmd = _scan_method(item, source, {})
        if cmd is not None:
            commands.append(cmd)
    if not commands:
        return None
    commands.sort(key=lambda c: (c["parent"] or "", c["name"]))
    return {
        "cog": f"({Path(rel_path).name})",
        "file": rel_path,
        "subsystem": "",
        "is_cog": False,
        "commands": commands,
    }


def scan_commands(repo_root: Path = REPO_ROOT) -> list[dict]:
    """Return one record per cog/module that declares commands."""
    cogs_dir = repo_root / "disbot" / "cogs"
    files = sorted(cogs_dir.rglob("*.py"))
    bot1 = repo_root / "disbot" / "bot1.py"
    if bot1.exists():
        files.append(bot1)
    out: list[dict] = []
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue
        rel = str(path.relative_to(repo_root))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                cog = _scan_class(node, source, rel)
                if cog is not None:
                    out.append(cog)
        module = _scan_module(tree, source, rel)
        if module is not None:
            out.append(module)
    out.sort(key=lambda c: c["cog"])
    return out


def summarise(cogs: list[dict]) -> dict:
    """Aggregate counts across all scanned cogs/commands."""
    cmds = [c for cog in cogs for c in cog["commands"]]
    by_type: dict[str, int] = {}
    for c in cmds:
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1
    return {
        "cogs": sum(1 for cog in cogs if cog.get("is_cog")),
        "command_classes": len(cogs),
        "commands": len(cmds),
        "top_level_prefix": sum(
            1 for c in cmds if c["type"] in ("prefix", "both") and not c["parent"]
        ),
        "subcommands": sum(1 for c in cmds if c["parent"]),
        "slash": sum(1 for c in cmds if c["type"] == "slash" and not c["parent"]),
        "by_type": by_type,
        "button_backed": sum(1 for c in cmds if c["button_backed"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan the cog command surface.")
    parser.add_argument("--summary", action="store_true", help="print counts only")
    args = parser.parse_args(argv)
    cogs = scan_commands()
    if args.summary:
        print(json.dumps(summarise(cogs), indent=2))
    else:
        print(json.dumps({"summary": summarise(cogs), "cogs": cogs}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
