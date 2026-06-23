#!/usr/bin/env python3
"""Settings-reachability guard for SuperBot.

The *settings* analog of ``scripts/check_command_reachability.py`` (the
per-command help guard).  Where that one guards that every member command is
reachable by clicking through ``!help``, this one guards the consolidation
audit's §3.4 goal — **every cog's configurable settings are reachable from the
``!settings`` hub** — and makes it un-regressable.

A subsystem's config surfaces in ``!settings`` via
``services.customization_catalogue.actionable_settings_groups()``, which
includes a subsystem iff it is **non-internal** and declares a
``SubsystemSchema`` with at least one actionable surface (an editable setting,
binding, resource requirement, or domain panel).  So a subsystem's config is
*centralized + reachable* exactly when it declares a schema and is non-internal.

The check is static (no live bot, no Postgres).  For every registered subsystem
that **declares config** — it has a ``cogs/<sub>/schemas.py`` ``SubsystemSchema``
*or* a ``*.configure`` / ``*.settings.*`` capability — it classifies the
subsystem as:

  * **reachable** — declares a schema and is non-internal → it appears in the
    Settings hub;
  * **exempt** — an ``internal`` subsystem (never in the hub by design), or
    allowlisted in ``architecture_rules/settings_reachability_exceptions.yml``
    with a documented reason (the intentional domain-panel cases: per-channel
    game setup like counting/chain, or a ``*.configure`` capability that is an
    admin *action* rather than stored config);
  * **gap** — declares config (a ``*.configure`` capability, or a schema) but is
    NOT reachable from ``!settings`` and is not allowlisted.  This is the
    actionable finding: add a ``SubsystemSchema`` (centralize the config) or
    allowlist it with a reason.

It is **warn-first and disposable** (Q-0105): every finding is a warning,
nothing fails CI in ``--mode report``.  The invariant test
(``tests/unit/invariants/test_settings_reachability.py``) ratchets against a
recorded baseline so *new* gaps fail while any pre-existing ones are tolerated.
The guard graduates to ``--mode strict`` (exit 1 on any gap) once the baseline
is empty and it has run clean across a few sessions.

Provenance / reliability (Q-0105):
  - Added 2026-06-23 for the consolidation/discoverability audit (settings half):
    `docs/planning/consolidation-discoverability-audit-brief-2026-06-23.md` §3.4.
  - **Unverified:** the static schema scan keys off ``cogs/<sub>/schemas.py``
    declaring ``SubsystemSchema(subsystem="…")``; it mirrors the live
    ``actionable_settings_groups()`` rule but cannot exercise the bot-dependent
    catalogue signals.  Confirm a flagged subsystem really lacks a Settings-hub
    surface in a live guild before centralizing it, and keep the rule warn-only
    until proven quiet.
  - **Delete this guard if it proves unreliable over multiple sessions** — it is
    a convenience ratchet, not load-bearing runtime code.

Usage:
    python3.10 scripts/check_settings_reachability.py              # report
    python3.10 scripts/check_settings_reachability.py --json       # machine-readable
    python3.10 scripts/check_settings_reachability.py --mode strict # exit 1 on a gap
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DISBOT_ROOT = REPO_ROOT / "disbot"
COGS_DIR = DISBOT_ROOT / "cogs"
RULES_DIR = REPO_ROOT / "architecture_rules"
_EXCEPTIONS_FILE = "settings_reachability_exceptions.yml"

if str(DISBOT_ROOT) not in sys.path:
    sys.path.insert(0, str(DISBOT_ROOT))

from utils.subsystem_registry import SUBSYSTEMS  # noqa: E402

# A capability whose action implies configurable state lives in one of these
# namespaces — ``{sub}.settings.configure`` / ``{sub}.settings.view`` or a
# ``{sub}.{resource}.configure`` operation.
_CONFIG_CAP_MARKERS = (".configure", ".settings.")


@dataclass(frozen=True)
class Finding:
    """One subsystem's settings-reachability classification."""

    subsystem: str
    status: str  # "reachable" | "exempt" | "gap"
    reason: str

    @property
    def key(self) -> str:
        """Stable identity used by the baseline ratchet."""
        return self.subsystem

    def display(self) -> str:
        tag = {"reachable": "ok", "exempt": "exempt", "gap": "GAP"}[self.status]
        return f"  [{tag}] {self.subsystem}  —  {self.reason}"


def _load_exceptions() -> dict:
    path = RULES_DIR / _EXCEPTIONS_FILE
    if not path.exists():
        return {}
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


def _allowlisted(subsystem: str, exceptions: dict) -> str | None:
    """Return the documented reason if ``subsystem`` is allowlisted, else None."""
    for exc in exceptions.get("exceptions", []):
        if exc.get("subsystem") == subsystem:
            return str(exc.get("reason", "(no reason given)"))
    return None


def _schema_subsystems() -> set[str]:
    """Subsystems that declare a ``SubsystemSchema`` in ``cogs/<sub>/schemas.py``.

    Static AST scan for a ``SubsystemSchema(subsystem="X", …)`` call — the
    declaration the cog registers into the customization catalogue at load.
    """
    found: set[str] = set()
    for schema_file in COGS_DIR.glob("*/schemas.py"):
        try:
            tree = ast.parse(schema_file.read_text(), filename=str(schema_file))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else getattr(func, "id", "")
            )
            if name != "SubsystemSchema":
                continue
            for kw in node.keywords:
                if (
                    kw.arg == "subsystem"
                    and isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, str)
                ):
                    found.add(kw.value.value)
    return found


def _config_capabilities(meta: dict) -> list[str]:
    return [
        cap
        for cap in meta.get("capabilities", ())
        if any(marker in cap for marker in _CONFIG_CAP_MARKERS)
    ]


def collect_findings() -> list[Finding]:
    """Classify every config-declaring subsystem's Settings-hub reachability."""
    schema_subs = _schema_subsystems()
    exceptions = _load_exceptions()
    findings: list[Finding] = []

    for name in sorted(SUBSYSTEMS):
        meta = SUBSYSTEMS[name]
        has_schema = name in schema_subs
        config_caps = _config_capabilities(meta)
        if not (has_schema or config_caps):
            continue  # no configurable surface → nothing to centralize

        internal = meta.get("visibility_mode") == "internal"
        # Reachable from !settings == declares a schema (the actionable surface
        # actionable_settings_groups() requires) AND is non-internal.
        if has_schema and not internal:
            findings.append(
                Finding(
                    name,
                    "reachable",
                    "schema declared; surfaces in the !settings hub",
                ),
            )
            continue

        allow_reason = _allowlisted(name, exceptions)
        if allow_reason is not None:
            findings.append(Finding(name, "exempt", f"allowlisted — {allow_reason}"))
            continue
        if internal and not config_caps and has_schema:
            # An internal subsystem with a schema: hidden from the hub by design.
            findings.append(
                Finding(
                    name,
                    "exempt",
                    "internal subsystem (not in the Settings hub by design)",
                ),
            )
            continue

        if config_caps and not has_schema:
            reason = (
                f"declares config capability {config_caps} but no SubsystemSchema — "
                "its settings are not reachable from the !settings hub "
                "(add a schema to centralize, or allowlist with a reason)"
            )
        else:  # has_schema and internal
            reason = (
                "declares a SubsystemSchema but is visibility_mode=internal, so "
                "actionable_settings_groups() hides it from the !settings hub"
            )
        findings.append(Finding(name, "gap", reason))

    return findings


def gaps(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.status == "gap"]


def _print_report(findings: list[Finding]) -> None:
    reachable = [f for f in findings if f.status == "reachable"]
    exempt = [f for f in findings if f.status == "exempt"]
    g = gaps(findings)
    print(
        f"check_settings_reachability — {len(reachable)} reachable · "
        f"{len(exempt)} exempt · {len(g)} GAP\n",
    )
    if not g:
        print("  every config-declaring subsystem is reachable from !settings ✓")
    else:
        print("  GAPS — configurable subsystems not reachable from the !settings hub:")
        for f in g:
            print(f.display())
    if exempt:
        print("\n  exempt (allowlisted / internal):")
        for f in exempt:
            print(f.display())


def _print_json(findings: list[Finding]) -> None:
    print(
        json.dumps(
            {
                "reachable": [f.subsystem for f in findings if f.status == "reachable"],
                "exempt": [f.subsystem for f in findings if f.status == "exempt"],
                "gaps": [
                    {"subsystem": f.subsystem, "reason": f.reason}
                    for f in gaps(findings)
                ],
            },
            indent=2,
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["report", "strict"], default="report")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    findings = collect_findings()
    if args.json:
        _print_json(findings)
    else:
        _print_report(findings)

    if args.mode == "strict" and gaps(findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
