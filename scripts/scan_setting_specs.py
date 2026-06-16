#!/usr/bin/env python3.10
"""Scan the bot's typed ``SettingSpec`` declarations (stdlib only, read-only).

The bot already has a typed, validated, audited settings system: each editable
scalar setting is a ``core.runtime.subsystem_schema.SettingSpec`` declared
statically in a ``disbot/cogs/<subsystem>/schemas.py`` module
(``value_type`` / ``default`` / ``settings_key`` / ``hint`` / ``allowed_values``
/ …). That is the **metadata a settings editor needs** — type, default, the
human hint, and any enum choices — and it is the source of truth the in-Discord
editor (``views/settings/``) and the audited ``services.settings_mutation``
pipeline both consume.

This scanner AST-reads those ``SettingSpec(...)`` declarations so the developer
dashboard can surface them (enriching ``/settings`` beyond bare key names, and
serving as the read-model for the future web editor) **without importing
``disbot``**. It resolves two kinds of references statically:

* ``settings_key=XP_MIN`` -> ``"xp_min"`` via ``disbot/utils/settings_keys/``;
* ``default=DEFAULT_ENABLED`` -> the constant's literal value, following a
  ``from services.automod_config import DEFAULT_ENABLED`` import to read it.

A default it cannot resolve statically is reported with ``default_known=False``
(never a misleading ``None``).

Emits one record per spec::

    {"subsystem": "xp", "name": "xp_min", "settings_key": "xp_min",
     "value_type": "int", "default": 15, "default_known": true,
     "hint": "Minimum XP awarded …", "capability_required": "xp.settings.configure",
     "allowed_values": []}

Pure stdlib, mirroring the other ``scripts/scan_*.py`` seams (which
``scripts/export_dashboard_data.py`` embeds in ``dashboard/data/dashboard.json``).

Run standalone::

    python3.10 scripts/scan_setting_specs.py            # human-readable summary
    python3.10 scripts/scan_setting_specs.py --json     # the raw JSON payload

Reliability (Q-0105): **unverified** — confirm against the ``cogs/*/schemas.py``
declarations a few times across sessions before trusting it, and delete this seam
if it proves unreliable. Convenience generator, not load-bearing runtime code.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DISBOT_DIR = REPO_ROOT / "disbot"
DEFAULT_COGS_DIR = DISBOT_DIR / "cogs"
DEFAULT_KEYS_DIR = DISBOT_DIR / "utils" / "settings_keys"

_STR_FIELDS = ("capability_required", "hint", "input_hint")

# Sentinel distinguishing "unresolved default" from a literal ``None`` default.
_UNRESOLVED = object()


def _literal(node: ast.AST) -> object:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return _UNRESOLVED


def _settings_key_map(keys_dir: Path) -> dict[str, str]:
    """``XP_MIN = "xp_min"`` -> ``{"XP_MIN": "xp_min"}`` over settings_keys/."""
    mapping: dict[str, str] = {}
    if not keys_dir.is_dir():
        return mapping
    for path in keys_dir.glob("*.py"):
        for name, value in _module_string_constants(path).items():
            mapping[name] = value
    return mapping


def _module_string_constants(path: Path) -> dict[str, str]:
    """Module-level ``NAME = "literal"`` string constants of one file."""
    out: dict[str, str] = {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return out
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            out[node.targets[0].id] = node.value.value
    return out


class _ConstResolver:
    """Resolve a ``default=NAME`` reference to its literal value.

    Looks in the schemas module's own constants first, then follows a
    ``from <module> import NAME`` to read the constant from that module.
    Parsed modules are cached; unknown names return :data:`_UNRESOLVED`.
    """

    def __init__(self, schema_tree: ast.Module) -> None:
        self._local: dict[str, object] = _module_constants(schema_tree)
        self._imports: dict[str, str] = {}
        for node in schema_tree.body:
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    self._imports[alias.asname or alias.name] = node.module
        self._module_cache: dict[str, dict[str, object]] = {}

    def resolve(self, name: str) -> object:
        if name in self._local:
            return self._local[name]
        module = self._imports.get(name)
        if module is None:
            return _UNRESOLVED
        consts = self._module_cache.get(module)
        if consts is None:
            path = DISBOT_DIR / (module.replace(".", "/") + ".py")
            try:
                consts = _module_constants(ast.parse(path.read_text(encoding="utf-8")))
            except (OSError, SyntaxError):
                consts = {}
            self._module_cache[module] = consts
        return consts.get(name, _UNRESOLVED)


def _module_constants(tree: ast.Module) -> dict[str, object]:
    """Module-level ``NAME = <literal>`` constants (any literal type)."""
    out: dict[str, object] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            value = _literal(node.value)
            if value is not _UNRESOLVED:
                out[node.targets[0].id] = value
    return out


def _resolve_settings_key(node: ast.AST, key_map: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return key_map.get(node.id, node.id)
    value = _literal(node)
    return value if isinstance(value, str) else ""


def _default(node: ast.AST, consts: _ConstResolver) -> tuple[object, bool]:
    """``(value, known)`` for a ``default=`` argument."""
    value = _literal(node)
    if value is not _UNRESOLVED:
        return value, True
    if isinstance(node, ast.Name):
        resolved = consts.resolve(node.id)
        if resolved is not _UNRESOLVED:
            return resolved, True
    return None, False


def _spec_from_call(
    call: ast.Call,
    subsystem: str,
    key_map: dict[str, str],
    consts: _ConstResolver,
) -> dict:
    """Build one record from a ``SettingSpec(...)`` call node (kwargs only)."""
    record: dict = {
        "subsystem": subsystem,
        "name": "",
        "settings_key": "",
        "value_type": "",
        "default": None,
        "default_known": False,
        "capability_required": "",
        "hint": "",
        "input_hint": "",
        "allowed_values": [],
    }
    for kw in call.keywords:
        if kw.arg is None:
            continue
        if kw.arg == "name":
            value = _literal(kw.value)
            record["name"] = value if isinstance(value, str) else ""
        elif kw.arg == "value_type":
            record["value_type"] = kw.value.id if isinstance(kw.value, ast.Name) else ""
        elif kw.arg == "default":
            record["default"], record["default_known"] = _default(kw.value, consts)
        elif kw.arg == "settings_key":
            record["settings_key"] = _resolve_settings_key(kw.value, key_map)
        elif kw.arg == "allowed_values":
            allowed = _literal(kw.value)
            record["allowed_values"] = (
                list(allowed) if isinstance(allowed, tuple) else []
            )
        elif kw.arg in _STR_FIELDS:
            value = _literal(kw.value)
            record[kw.arg] = value if isinstance(value, str) else ""
    return record


def scan_setting_specs(
    cogs_dir: Path = DEFAULT_COGS_DIR,
    keys_dir: Path = DEFAULT_KEYS_DIR,
) -> list[dict]:
    """Scan every ``cogs/*/schemas.py`` for ``SettingSpec(...)`` declarations."""
    key_map = _settings_key_map(keys_dir)
    records: list[dict] = []
    for schema_path in sorted(cogs_dir.glob("*/schemas.py")):
        subsystem = schema_path.parent.name
        try:
            tree = ast.parse(schema_path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        consts = _ConstResolver(tree)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "SettingSpec"
            ):
                records.append(_spec_from_call(node, subsystem, key_map, consts))
    records.sort(key=lambda r: (r["subsystem"], r["name"]))
    return records


def _format_summary(records: list[dict]) -> str:
    lines = [f"{len(records)} typed SettingSpec(s):\n"]
    for r in records:
        choices = f" choices={r['allowed_values']}" if r["allowed_values"] else ""
        default = repr(r["default"]) if r["default_known"] else "?"
        lines.append(
            f"  {r['subsystem']}.{r['name']:<22} {r['value_type']:<5} "
            f"default={default}{choices}",
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: print the SettingSpec catalogue (summary / JSON)."""
    parser = argparse.ArgumentParser(
        description="Scan the bot's typed SettingSpec declarations (read-only).",
    )
    parser.add_argument("--json", action="store_true", help="print raw JSON")
    args = parser.parse_args(argv)

    records = scan_setting_specs()
    if args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        print(_format_summary(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
