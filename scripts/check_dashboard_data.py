#!/usr/bin/env python3.10
"""Validate the developer dashboard's exported ``dashboard.json`` (stdlib only).

The dashboard (``dashboard/``) is the bot's main website; it renders
``dashboard/data/dashboard.json``, produced by ``scripts/export_dashboard_data.py``
from the repo's structured sources and extended by many parallel sessions. Nothing
validated that payload, so a drift silently degraded a page until someone eyeballed
it (PR #988 hit exactly this: acronym cogs whose ``subsystem`` didn't resolve to the
registry rendered with a generic icon + no routing key). This guard turns the common
drift classes into a failed check instead.

Checks:

* **cog->subsystem resolution** — every real (``is_cog``) cog's ``subsystem`` resolves
  to a registry subsystem key (a catalogue entry), minus a curated allow-list of
  cogs that legitimately have no own registry entry, and modules/mixins
  (``is_cog == False``). A *new* unregistered cog or a broken join is an error.
* **count integrity** — ``meta.counts.*`` match the actual array lengths (the #973
  command-count-drift class).
* **required fields** — every command has a name + valid ``type``; every cog has a
  ``file``; every catalogue entry has a ``key``.

Pure stdlib so it runs in CI with no extra dependencies (the dashboard's web deps
never enter the bot's ``requirements.txt``). Run::

    python3.10 scripts/check_dashboard_data.py            # validate committed JSON
    python3.10 scripts/check_dashboard_data.py --fresh    # regenerate first, then validate

Reliability (Q-0105): **unverified** — confirm its verdicts against the live sources
a few times across sessions before trusting it, and delete this guard if it proves
unreliable. It is a convenience guard, not load-bearing runtime code.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "dashboard" / "data" / "dashboard.json"

# Real (``is_cog``) cogs that legitimately have NO own SUBSYSTEMS registry entry:
# the BTD6 sub-cogs belong to the ``btd6`` subsystem; Hermes/Paragon/Setup are
# ops/internal cogs; RPS's class name differs from its ``rps_tournament`` key.
# Adding a cog here is a deliberate "this cog has no registry subsystem" call — the
# point of the guard is that a *new* unresolved cog must be triaged, not silent.
_UNREGISTERED_COG_ALLOWLIST = frozenset(
    {
        "BTD6EventsCog",
        "BTD6OpsCog",
        "BTD6ReferenceCog",
        "BTD6StrategyCog",
        "HermesCog",
        "ParagonCog",
        "RockPaperScissorsCog",
        "SetupCog",
    },
)

_VALID_COMMAND_TYPES = frozenset({"prefix", "slash", "both"})


@dataclass(frozen=True)
class Issue:
    """One validation finding. ``severity`` is ``"error"`` or ``"warning"``."""

    severity: str
    code: str
    message: str


def _err(code: str, message: str) -> Issue:
    return Issue("error", code, message)


def _warn(code: str, message: str) -> Issue:
    return Issue("warning", code, message)


def check_cog_subsystem_resolution(data: dict[str, Any]) -> list[Issue]:
    """Every real cog's ``subsystem`` must resolve to a registered subsystem."""
    issues: list[Issue] = []
    catalogue_keys = {e.get("key") for e in data.get("catalogue", [])}
    for cog in data.get("cogs", []):
        if not cog.get("is_cog"):
            continue  # modules / mixins need no registry entry
        name = cog.get("cog", "?")
        subsystem = cog.get("subsystem", "")
        if subsystem in catalogue_keys or name in _UNREGISTERED_COG_ALLOWLIST:
            continue
        issues.append(
            _err(
                "cog_subsystem_unresolved",
                f"cog {name!r} (subsystem {subsystem!r}) does not resolve to a "
                f"registered subsystem — register it, fix the cog->subsystem join "
                f"in scan_commands._cog_to_subsystem, or add it to "
                f"_UNREGISTERED_COG_ALLOWLIST in check_dashboard_data.py",
            ),
        )
    return issues


def check_count_integrity(data: dict[str, Any]) -> list[Issue]:
    """``meta.counts.*`` must equal the actual lengths they summarise."""
    issues: list[Issue] = []
    counts = data.get("meta", {}).get("counts", {})
    cogs = data.get("cogs", [])
    settings = data.get("settings", [])
    expected = {
        "cogs": sum(1 for c in cogs if c.get("is_cog")),
        "commands": sum(len(c.get("commands", [])) for c in cogs),
        "synonyms": sum(len(s.get("synonyms", [])) for s in data.get("synonyms", [])),
        "ideas": len(data.get("ideas", [])),
        "bugs": len(data.get("bugs", [])),
        "env_vars": len(data.get("env_usage", [])),
        "setting_domains": len(settings),
        "setting_keys": sum(len(d.get("keys", [])) for d in settings),
        "visible_subsystems": data.get("access", {}).get("total_visible", 0),
    }
    for key, exp in expected.items():
        if key not in counts:
            issues.append(_warn("count_missing", f"meta.counts.{key} is missing"))
        elif counts[key] != exp:
            issues.append(
                _err(
                    "count_mismatch",
                    f"meta.counts.{key}={counts[key]} but the data has {exp}",
                ),
            )
    return issues


def check_required_fields(data: dict[str, Any]) -> list[Issue]:
    """Every command/cog/catalogue entry must carry its load-bearing fields."""
    issues: list[Issue] = []
    for cog in data.get("cogs", []):
        cog_name = cog.get("cog")
        if not cog_name:
            issues.append(
                _err(
                    "cog_missing_name",
                    f"a cog entry has no 'cog' ({cog.get('file')})",
                ),
            )
        if not cog.get("file"):
            issues.append(_err("cog_missing_file", f"cog {cog_name!r} has no 'file'"))
        for cmd in cog.get("commands", []):
            if not cmd.get("name"):
                issues.append(
                    _err(
                        "command_missing_name",
                        f"a command in {cog_name!r} has no name",
                    ),
                )
            if cmd.get("type") not in _VALID_COMMAND_TYPES:
                issues.append(
                    _err(
                        "command_bad_type",
                        f"command {cmd.get('name')!r} in {cog_name!r} has invalid "
                        f"type {cmd.get('type')!r}",
                    ),
                )
    for entry in data.get("catalogue", []):
        if not entry.get("key"):
            issues.append(
                _err("catalogue_missing_key", "a catalogue entry has no 'key'"),
            )
    return issues


_CHECKS: tuple[Callable[[dict[str, Any]], list[Issue]], ...] = (
    check_cog_subsystem_resolution,
    check_count_integrity,
    check_required_fields,
)


def validate(data: dict[str, Any]) -> list[Issue]:
    """Run every check over ``data`` and return the combined findings."""
    issues: list[Issue] = []
    for check in _CHECKS:
        issues.extend(check(data))
    return issues


def _build_fresh() -> dict[str, Any]:
    """Regenerate the payload from live sources (sibling import — scripts/ isn't a package)."""
    script = Path(__file__).resolve().parent / "export_dashboard_data.py"
    spec = importlib.util.spec_from_file_location("_export_dashboard_seam", script)
    if spec is None or spec.loader is None:  # pragma: no cover - import wiring
        raise ImportError("cannot load export_dashboard_data.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_data()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: validate the export, print findings, exit non-zero on error."""
    parser = argparse.ArgumentParser(description="Validate the dashboard data export.")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="regenerate the payload from live sources before validating",
    )
    parser.add_argument("--data", default=str(DATA_FILE), help="path to dashboard.json")
    args = parser.parse_args(argv)

    if args.fresh:
        data = _build_fresh()
    else:
        data = json.loads(Path(args.data).read_text(encoding="utf-8"))

    issues = validate(data)
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    for issue in issues:
        marker = "✗" if issue.severity == "error" else "⚠"
        print(f"{marker} [{issue.code}] {issue.message}")

    if errors:
        print(
            f"\ncheck_dashboard_data: {len(errors)} error(s), {len(warnings)} warning(s)",
        )
        return 1
    print(
        f"check_dashboard_data: OK ✓ "
        f"({len(warnings)} warning(s); {len(data.get('cogs', []))} cogs validated)",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
