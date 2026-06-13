#!/usr/bin/env python3
"""Settings / bindings / provisioning lane matrix — offline inventory.

Walks the live ``SubsystemSchema`` registry (every ``cogs/*/schemas.py``
``register_schemas()``) plus the ``binding_backfill`` migration registry and
the ``config_arbitration`` binding-first read accessors, and emits one
machine-readable matrix of:

* every declared ``SettingSpec`` (key, type, capability, input_hint),
* every declared ``BindingSpec`` (kind, capability),
* every provisionable ``ResourceRequirement`` (intent → binding),
* the backfill mappings (``MIGRATED_KEYS`` active vs ``DEFERRED_KEYS``),
* the arbitration read seams (which (subsystem, binding) a typed accessor
  resolves through the binding→legacy ladder),
* a **pointer-lane analysis**: every legacy Discord pointer setting
  (``input_hint`` channel/role) classified as binding-backed (convergeable),
  binding-backed-deferred (schema home TBD), or an orphan pointer (no binding).

    python3.10 scripts/settings_lane_matrix.py             # human table
    python3.10 scripts/settings_lane_matrix.py --json      # JSON
    python3.10 scripts/settings_lane_matrix.py --pointers  # just the pointer lane

This is the machine-readable matrix the settings production-readiness map
(`docs/planning/production-readiness/settings-bindings-provisioning-...`)
asks for as recommendation #1, and the data source the P0-3 pointer-lane
convergence plan + parity invariants are built from.

Provenance / reliability (Q-0105): added 2026-06-13 for the P0-3 settings
lane. **Unverified** — confirm its inventory against
``scripts/check_quality.py``-green source a few times across sessions before
trusting its counts. It is read-only (no Discord / Postgres). If it proves
unreliable or unused over multiple sessions, delete it — it is a convenience
inventory, not load-bearing runtime.

Read-only; no Discord / database dependency; safe in CI.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
_DISBOT = REPO_ROOT / "disbot"

# config.py validates env at import time; mirror tests/conftest.py.
os.environ.setdefault("DISCORD_BOT_TOKEN_PRODUCTION", "TEST_TOKEN_PLACEHOLDER")
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


# ---------------------------------------------------------------------------
# Schema discovery — register every cog schema offline.
# ---------------------------------------------------------------------------


def _load_all_schemas() -> None:
    """Import every ``cogs/*/schemas.py`` and call ``register_schemas``.

    Cogs register their schema in ``cog_load`` at boot; this offline tool
    does not load cogs, so it triggers registration directly.  Discovery is
    glob-based (not a hardcoded list) so a new subsystem schema is picked up
    automatically.
    """
    cogs_dir = _DISBOT / "cogs"
    for schema_path in sorted(cogs_dir.glob("*/schemas.py")):
        module_path = f"cogs.{schema_path.parent.name}.schemas"
        try:
            mod = importlib.import_module(module_path)
        except Exception as exc:  # noqa: BLE001 — tolerate an un-importable cog
            print(
                f"# skipped {module_path}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            continue
        register = getattr(mod, "register_schemas", None)
        if register is None:
            continue
        try:
            register()
        except Exception:  # noqa: BLE001 — idempotent re-register is fine
            pass


# ---------------------------------------------------------------------------
# Arbitration read seams — the closed set of binding-first typed accessors in
# core.runtime.config_arbitration.  Declared here (a closed, documented set)
# rather than AST-scraped: each names the (subsystem, binding, legacy_key)
# triple it resolves through the binding→legacy ladder.
# ---------------------------------------------------------------------------

_ARBITRATION_READS: tuple[tuple[str, str, str, str], ...] = (
    # Each row pairs an accessor with its subsystem, binding_name, legacy_key.
    ("get_xp_announce_channel", "xp", "announce_channel", "xp_announce_channel"),
    ("get_economy_log_channel", "economy", "log_channel", "economy_log_channel"),
    ("get_trusted_tier_role", "governance", "trusted_role", "trusted_tier_role_id"),
    (
        "get_moderator_tier_role",
        "governance",
        "moderator_role",
        "moderator_tier_role_id",
    ),
)


# ---------------------------------------------------------------------------
# Result shapes
# ---------------------------------------------------------------------------


@dataclass
class PointerRow:
    """One legacy Discord pointer setting and its convergence disposition."""

    subsystem: str
    setting_name: str
    settings_key: str
    input_hint: str  # "channel" | "role"
    backfill_lane: str  # "migrated" | "deferred" | "none"
    target_subsystem: str | None
    target_binding: str | None
    target_binding_declared: bool
    disposition: str  # see _classify_pointer


@dataclass
class Matrix:
    settings: list[dict[str, Any]] = field(default_factory=list)
    bindings: list[dict[str, Any]] = field(default_factory=list)
    resources: list[dict[str, Any]] = field(default_factory=list)
    backfill_migrated: list[dict[str, Any]] = field(default_factory=list)
    backfill_deferred: list[dict[str, Any]] = field(default_factory=list)
    arbitration_reads: list[dict[str, Any]] = field(default_factory=list)
    pointers: list[PointerRow] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_matrix() -> Matrix:
    _load_all_schemas()

    from core.runtime.subsystem_schema import all_schemas
    from services import binding_backfill

    schemas = all_schemas()

    # Set of declared (subsystem, binding_name) — the canonical binding homes.
    declared_bindings: set[tuple[str, str]] = set()
    for sub, schema in schemas.items():
        for b in schema.bindings:
            declared_bindings.add((sub, b.name))

    m = Matrix()

    for sub in sorted(schemas):
        schema = schemas[sub]
        for s in schema.settings:
            m.settings.append(
                {
                    "subsystem": sub,
                    "name": s.name,
                    "settings_key": s.settings_key,
                    "value_type": getattr(s.value_type, "__name__", str(s.value_type)),
                    "capability_required": s.capability_required,
                    "input_hint": s.input_hint,
                },
            )
        for b in schema.bindings:
            m.bindings.append(
                {
                    "subsystem": sub,
                    "name": b.name,
                    "kind": b.kind.value,
                    "required": b.required,
                    "capability_required": b.capability_required,
                },
            )
        for r in schema.resource_requirements:
            m.resources.append(
                {
                    "subsystem": sub,
                    "intent": r.intent,
                    "kind": r.kind.value,
                    "binding_name": getattr(r, "binding_name", None),
                },
            )

    # Backfill registries (DEFERRED_KEYS may not exist on older revisions).
    def _mk_row(mk: Any) -> dict[str, Any]:
        return {
            "legacy_key": mk.legacy_key,
            "subsystem": mk.subsystem,
            "binding_name": mk.binding_name,
            "kind": mk.kind.value,
            "target_declared": (mk.subsystem, mk.binding_name) in declared_bindings,
        }

    for mk in getattr(binding_backfill, "MIGRATED_KEYS", ()):
        m.backfill_migrated.append(_mk_row(mk))
    for mk in getattr(binding_backfill, "DEFERRED_KEYS", ()):
        m.backfill_deferred.append(_mk_row(mk))

    for accessor, sub, binding_name, legacy_key in _ARBITRATION_READS:
        m.arbitration_reads.append(
            {
                "accessor": accessor,
                "subsystem": sub,
                "binding_name": binding_name,
                "legacy_key": legacy_key,
                "target_declared": (sub, binding_name) in declared_bindings,
            },
        )

    # Pointer-lane analysis: every channel/role pointer setting.
    backfill_by_key: dict[str, tuple[str, dict[str, Any]]] = {}
    for row in m.backfill_migrated:
        backfill_by_key[row["legacy_key"]] = ("migrated", row)
    for row in m.backfill_deferred:
        backfill_by_key[row["legacy_key"]] = ("deferred", row)

    for s in m.settings:
        if s["input_hint"] not in ("channel", "role"):
            continue
        lane, row = backfill_by_key.get(s["settings_key"], ("none", None))
        target_sub = row["subsystem"] if row else None
        target_binding = row["binding_name"] if row else None
        declared = bool(row and row["target_declared"])
        m.pointers.append(
            PointerRow(
                subsystem=s["subsystem"],
                setting_name=s["name"],
                settings_key=s["settings_key"],
                input_hint=s["input_hint"],
                backfill_lane=lane,
                target_subsystem=target_sub,
                target_binding=target_binding,
                target_binding_declared=declared,
                disposition=_classify_pointer(lane, declared),
            ),
        )

    m.counts = {
        "subsystems": len(schemas),
        "settings": len(m.settings),
        "bindings": len(m.bindings),
        "resources": len(m.resources),
        "backfill_migrated": len(m.backfill_migrated),
        "backfill_deferred": len(m.backfill_deferred),
        "pointer_settings": len(m.pointers),
        "pointer_convergeable": sum(
            1 for p in m.pointers if p.disposition == "binding_backed_convergeable"
        ),
        "pointer_deferred": sum(
            1 for p in m.pointers if p.disposition == "binding_backed_deferred"
        ),
        "pointer_orphan": sum(
            1 for p in m.pointers if p.disposition == "orphan_no_binding"
        ),
    }
    return m


def _classify_pointer(lane: str, target_declared: bool) -> str:
    """Disposition of a legacy channel/role pointer setting.

    * ``binding_backed_convergeable`` — a backfill mapping exists and its
      target ``BindingSpec`` is declared: this pointer can converge today
      (binding-first read already in place).
    * ``binding_backed_deferred`` — a backfill mapping exists but its target
      binding has **no declared schema home yet** (e.g. the reserved
      ``governance`` namespace): convergence is gated on a schema-home
      decision (P0-3 plan).
    * ``orphan_no_binding`` — no backfill mapping at all: a pointer in the
      wrong lane with no migration target (e.g. ``moderation.public_log_channel``).
    """
    if lane == "migrated" and target_declared:
        return "binding_backed_convergeable"
    if lane == "deferred" or (lane == "migrated" and not target_declared):
        return "binding_backed_deferred"
    return "orphan_no_binding"


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def _render_table(m: Matrix) -> str:
    out: list[str] = []
    c = m.counts
    out.append("Settings / bindings / provisioning lane matrix")
    out.append("=" * 60)
    out.append(
        f"subsystems={c['subsystems']}  settings={c['settings']}  "
        f"bindings={c['bindings']}  resources={c['resources']}",
    )
    out.append(
        f"backfill: migrated={c['backfill_migrated']} deferred={c['backfill_deferred']}",
    )
    out.append("")
    out.append("Pointer lane (legacy channel/role settings)")
    out.append("-" * 60)
    out.append(
        f"  convergeable={c['pointer_convergeable']}  "
        f"deferred={c['pointer_deferred']}  orphan={c['pointer_orphan']}",
    )
    for p in m.pointers:
        target = (
            f"{p.target_subsystem}.{p.target_binding}"
            if p.target_subsystem
            else "(no binding)"
        )
        flag = (
            ""
            if p.target_binding_declared or p.backfill_lane == "none"
            else " [UNDECLARED]"
        )
        out.append(
            f"  {p.subsystem}.{p.setting_name} ({p.input_hint}) "
            f"→ {target}{flag}  [{p.disposition}]",
        )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--pointers",
        action="store_true",
        help="emit only the pointer-lane analysis",
    )
    args = parser.parse_args(argv)

    m = build_matrix()

    if args.json:
        payload: dict[str, Any] = {
            "counts": m.counts,
            "settings": m.settings,
            "bindings": m.bindings,
            "resources": m.resources,
            "backfill_migrated": m.backfill_migrated,
            "backfill_deferred": m.backfill_deferred,
            "arbitration_reads": m.arbitration_reads,
            "pointers": [asdict(p) for p in m.pointers],
        }
        if args.pointers:
            payload = {"counts": m.counts, "pointers": payload["pointers"]}
        print(json.dumps(payload, indent=2))
        return 0

    if args.pointers:
        print(_render_table(m))
        return 0

    print(_render_table(m))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
