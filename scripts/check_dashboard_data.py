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
    python3.10 scripts/check_dashboard_data.py --drift    # report structural drift vs a fresh build

``--drift`` is the **non-blocking freshness reporter**: it builds a fresh export and compares only
the *structural identifier sets* (cogs, commands, env-var names, setting keys, catalogue keys,
synonym canonicals) against the committed JSON, emitting **warnings only** — never errors. It
deliberately ignores the volatile churn (timestamps, build SHA, ideas/sessions/bugs feeds, file-line
locations) so it catches a *real* surface drift (a new cog/command/env-var/setting that shipped but
was never re-exported) without the constant-red fragility of byte-equality across the many parallel
sessions that touch the file. The committed JSON drifted on ``main`` exactly this way (PR #1020/#1023
shipped new env-vars + a setting key that were never re-exported); this guard turns that into a
visible warning.

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

# Real (``is_cog``) cogs that legitimately have NO own SUBSYSTEMS registry entry
# AND no parent to map to: ``HermesCog`` (ops bridge), ``SetupCog`` (the hub-less
# wizard), ``ParagonCog`` (BTD6-adjacent but its parent is ambiguous — deferred to
# owner intent). The BTD6 sub-cogs and RPS used to be here too, but they DO belong
# to a parent subsystem, so ``scan_commands._COG_SUBSYSTEM_OVERRIDES`` now resolves
# them (``btd6`` / ``rps_tournament``) and they no longer need an exception.
# Adding a cog here is a deliberate "this cog has no registry subsystem" call — the
# point of the guard is that a *new* unresolved cog must be triaged, not silent.
_UNREGISTERED_COG_ALLOWLIST = frozenset(
    {
        "HermesCog",
        "ParagonCog",
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


# ---------------------------------------------------------------------------
# structural-drift reporter (--drift) — non-blocking freshness warning
# ---------------------------------------------------------------------------

# Each entry maps a human label -> a function returning the *set of stable
# identifiers* on that surface. Only identity is compared — never order,
# file-line locations, or the volatile feeds (ideas/sessions/bugs/timestamps),
# so a real surface drift (a shipped cog/command/env-var/setting that was never
# re-exported) is caught without byte-equality fragility.
_STRUCTURAL_SURFACES: dict[str, Callable[[dict[str, Any]], set[Any]]] = {
    "cogs": lambda d: {c.get("cog") for c in d.get("cogs", []) if c.get("is_cog")},
    "commands": lambda d: {
        (c.get("cog"), cmd.get("name"))
        for c in d.get("cogs", [])
        for cmd in c.get("commands", [])
    },
    "env vars": lambda d: {e.get("name") for e in d.get("env_usage", [])},
    "setting keys": lambda d: {
        (dom.get("domain"), k.get("key"))
        for dom in d.get("settings", [])
        for k in dom.get("keys", [])
    },
    "catalogue keys": lambda d: {e.get("key") for e in d.get("catalogue", [])},
    "synonym canonicals": lambda d: {s.get("canonical") for s in d.get("synonyms", [])},
}


def _fmt_sample(items: set[Any], limit: int = 6) -> str:
    """Render a deterministic, truncated sample of identifiers for a message."""
    ordered = sorted(items, key=repr)
    shown = ", ".join(repr(i) for i in ordered[:limit])
    extra = len(ordered) - limit
    return f"{shown}{f' (+{extra} more)' if extra > 0 else ''}"


def check_structural_drift(
    committed: dict[str, Any],
    fresh: dict[str, Any],
) -> list[Issue]:
    """Report (as **warnings only**) structural surfaces where the committed JSON
    drifts from a fresh export.

    ``added`` = identifiers a fresh build has that the committed JSON lacks (a
    source change that shipped but was never re-exported — the common case).
    ``removed`` = identifiers the committed JSON has that no longer exist in
    source (a stale entry). Never returns an ``error`` Issue: the committed
    artifact is regenerated by hand / on cadence, and many parallel sessions
    touch it, so drift is *expected* between regenerations and must not gate CI.
    """
    issues: list[Issue] = []
    for label, surface in _STRUCTURAL_SURFACES.items():
        committed_ids = surface(committed)
        fresh_ids = surface(fresh)
        added = fresh_ids - committed_ids
        removed = committed_ids - fresh_ids
        if added:
            issues.append(
                _warn(
                    "structural_drift_added",
                    f"{label}: {len(added)} present in a fresh export but missing "
                    f"from the committed dashboard.json — re-run "
                    f"export_dashboard_data.py: {_fmt_sample(added)}",
                ),
            )
        if removed:
            issues.append(
                _warn(
                    "structural_drift_removed",
                    f"{label}: {len(removed)} in the committed dashboard.json no "
                    f"longer exist in source (stale) — re-run "
                    f"export_dashboard_data.py: {_fmt_sample(removed)}",
                ),
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
    parser.add_argument(
        "--drift",
        action="store_true",
        help="report (warn-only) structural drift between the committed JSON and a fresh export",
    )
    parser.add_argument("--data", default=str(DATA_FILE), help="path to dashboard.json")
    args = parser.parse_args(argv)

    if args.fresh:
        data = _build_fresh()
    else:
        data = json.loads(Path(args.data).read_text(encoding="utf-8"))

    issues = validate(data)
    if args.drift:
        # Compare the committed artifact (never the fresh one, even under --fresh)
        # against a fresh build so the report names what the *committed* file is
        # missing. Warn-only — drift never gates the run.
        committed = json.loads(Path(args.data).read_text(encoding="utf-8"))
        issues.extend(check_structural_drift(committed, _build_fresh()))
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
