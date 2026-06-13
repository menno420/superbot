"""Invariant — legacy Discord pointer-lane ledger (P0-3 ratchet).

Architecture lane rule: *a Discord resource pointer (channel / role / category)
must have one canonical binding owner.*  A pointer stored as a scalar
``SettingSpec`` (``input_hint="channel"`` / ``"role"``) is a pointer in the
wrong lane — it lets the generic scalar editors bypass binding target
validation / status semantics, and creates two operator-visible truths.

This invariant is the **ratchet** for that debt.  Every channel/role pointer
setting must be accounted for in exactly one of three ledgers below, each with a
known disposition (the convergence plan owns moving them):

* ``CONVERGEABLE_POINTERS`` — a binding-backfill mapping exists and its target
  ``BindingSpec`` is declared (binding-first read already in place via
  ``config_arbitration``); the scalar is pending retirement.
* ``DEFERRED_POINTERS`` — a backfill mapping exists but its target binding has
  no declared schema home yet (the reserved ``governance`` namespace).
* ``ORPHAN_POINTERS`` — a pointer stored as a scalar with no binding and no
  migration target at all.

A **new** channel/role pointer setting that is in none of these ledgers fails
the test: declare a ``BindingSpec`` and read it through
``config_arbitration`` (the right lane), or — if it must ship as a scalar for
now — add it to ``ORPHAN_POINTERS`` with the convergence plan reference, so the
debt is tracked, not silent.  (PR #775's welcome/counters channel pointers are
the recurrence this guard prevents.)

A ledger entry that is no longer a registered pointer also fails (rot): it
converged to a binding — remove it from the ledger.

Convergence plan: ``docs/planning/settings-pointer-lane-convergence-plan-2026-06-13.md``.

Provenance (Q-0105): added 2026-06-13 (P0-3 foundation PR).  The ledger was
seeded from ``scripts/settings_lane_matrix.py`` ground truth against a green
``check_quality.py --full`` run.  Load-bearing lane guard; keep.
"""

from __future__ import annotations

import importlib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_COGS_DIR = _REPO_ROOT / "disbot" / "cogs"

# ---------------------------------------------------------------------------
# The ledger — "subsystem.setting_name" keys.  Seeded 2026-06-13 from the live
# registry (scripts/settings_lane_matrix.py).  Moving an entry between buckets
# (or removing it) is a convergence step the P0-3 plan governs.
# ---------------------------------------------------------------------------

CONVERGEABLE_POINTERS: frozenset[str] = frozenset(
    {
        "economy.economy_log_channel",  # → economy.log_channel (declared)
        "xp.xp_announce_channel",  # → xp.announce_channel (declared)
    },
)

DEFERRED_POINTERS: frozenset[str] = frozenset(
    {
        "moderation.trusted_role",  # → governance.trusted_role (no home yet)
        "moderation.moderator_role",  # → governance.moderator_role (no home yet)
    },
)

ORPHAN_POINTERS: frozenset[str] = frozenset(
    {
        # welcome v1 (#775) — channel/role pointers stored as scalars.
        "welcome.channel",
        "welcome.entry_role",
        # server counters v1 (#775) — three statdock channel pointers.
        "counters.total_channel",
        "counters.humans_channel",
        "counters.bots_channel",
        # moderation public-log channel — pointer in wrong lane, no binding
        # declared (settings map "Bugs/inconsistencies" High finding).
        "moderation.public_log_channel",
    },
)

_LEDGER: frozenset[str] = CONVERGEABLE_POINTERS | DEFERRED_POINTERS | ORPHAN_POINTERS


def _pointer_settings() -> set[str]:
    """Return ``"subsystem.name"`` for every channel/role pointer setting."""
    from core.runtime.subsystem_schema import all_schemas

    for schema_path in sorted(_COGS_DIR.glob("*/schemas.py")):
        module_path = f"cogs.{schema_path.parent.name}.schemas"
        mod = importlib.import_module(module_path)
        register = getattr(mod, "register_schemas", None)
        if register is None:
            continue
        try:
            register()
        except Exception:  # noqa: BLE001 — idempotent
            pass

    pointers: set[str] = set()
    for sub, schema in all_schemas().items():
        for s in schema.settings:
            if s.input_hint in ("channel", "role"):
                pointers.add(f"{sub}.{s.name}")
    return pointers


def test_ledger_buckets_are_disjoint():
    """No pointer is filed in two buckets at once."""
    pairs = [
        ("CONVERGEABLE", "DEFERRED", CONVERGEABLE_POINTERS & DEFERRED_POINTERS),
        ("CONVERGEABLE", "ORPHAN", CONVERGEABLE_POINTERS & ORPHAN_POINTERS),
        ("DEFERRED", "ORPHAN", DEFERRED_POINTERS & ORPHAN_POINTERS),
    ]
    overlaps = [f"{a}∩{b}={sorted(s)}" for a, b, s in pairs if s]
    assert not overlaps, "ledger buckets overlap: " + ", ".join(overlaps)


def test_no_new_unledgered_pointer_setting():
    """Every channel/role pointer setting is accounted for in the ledger."""
    pointers = _pointer_settings()
    unledgered = sorted(pointers - _LEDGER)
    assert not unledgered, (
        "These channel/role pointer settings are NOT in the pointer-lane "
        "ledger.  A Discord resource pointer belongs in a BindingSpec read "
        "through config_arbitration (the right lane) — not a scalar setting.  "
        "Declare a binding, or (if it must ship as a scalar for now) add it to "
        "ORPHAN_POINTERS in this file with the convergence plan reference:\n"
        + "\n".join(f"  {p}" for p in unledgered)
    )


def test_ledger_has_no_rot():
    """Every ledger entry is still a registered channel/role pointer setting.

    A stale entry means the pointer was converged to a binding (or renamed) —
    remove it from the ledger so the ratchet stays honest.
    """
    pointers = _pointer_settings()
    stale = sorted(_LEDGER - pointers)
    assert not stale, (
        "These pointer-lane ledger entries are no longer registered channel/"
        "role pointer settings (converged or renamed?) — remove them:\n"
        + "\n".join(f"  {p}" for p in stale)
    )


def test_convergeable_and_deferred_match_backfill_registries():
    """The CONVERGEABLE / DEFERRED buckets agree with the backfill registries.

    A pointer is only ``CONVERGEABLE`` if its key is in ``MIGRATED_KEYS`` (homed)
    and only ``DEFERRED`` if its key is in ``DEFERRED_KEYS`` (un-homed).  This
    keeps the ledger's classification honest against the migration source of
    truth rather than a hand-maintained guess.
    """
    from core.runtime.subsystem_schema import all_schemas
    from services.binding_backfill import DEFERRED_KEYS, MIGRATED_KEYS

    _pointer_settings()  # ensure schemas registered
    schemas = all_schemas()

    def _key_for(pointer: str) -> str | None:
        sub, name = pointer.split(".", 1)
        schema = schemas.get(sub)
        if schema is None:
            return None
        for s in schema.settings:
            if s.name == name:
                return s.settings_key
        return None

    migrated_keys = {mk.legacy_key for mk in MIGRATED_KEYS}
    deferred_keys = {mk.legacy_key for mk in DEFERRED_KEYS}

    bad_convergeable = sorted(
        p for p in CONVERGEABLE_POINTERS if _key_for(p) not in migrated_keys
    )
    bad_deferred = sorted(
        p for p in DEFERRED_POINTERS if _key_for(p) not in deferred_keys
    )
    assert not bad_convergeable, (
        "CONVERGEABLE_POINTERS whose key is not in MIGRATED_KEYS "
        f"(homed): {bad_convergeable}"
    )
    assert not bad_deferred, (
        "DEFERRED_POINTERS whose key is not in DEFERRED_KEYS "
        f"(un-homed): {bad_deferred}"
    )
