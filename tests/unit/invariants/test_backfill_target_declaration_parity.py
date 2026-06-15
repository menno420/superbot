"""Invariant — binding-backfill target declaration parity (P0-3).

The settings production-readiness map's "Required before production-ready" #2:
a backfill mapping that targets an **undeclared** ``BindingSpec`` is broken
migration machinery — ``_schema_declares()`` rejects it, so every guild gets a
permanent ``BLOCKED_NO_SCHEMA`` finding for that key.  Before this invariant the
``governance.trusted_role`` mapping sat in ``MIGRATED_KEYS`` exactly that way.

This pins the contract that resolves it:

* Every :data:`~services.binding_backfill.MIGRATED_KEYS` target
  ``(subsystem, binding_name)`` **is** a declared ``BindingSpec`` — and its
  declared kind matches the mapping's kind.  A key may only sit in
  ``MIGRATED_KEYS`` when it can actually be migrated today.
* Every :data:`~services.binding_backfill.DEFERRED_KEYS` target is **not** yet
  a declared ``BindingSpec``.  If a deferred key's binding home gets declared,
  it must graduate to ``MIGRATED_KEYS`` (and this test fails until it does), so
  a homed-but-still-deferred key can't silently rot.
* No legacy key appears in both registries.

When the P0-3 plan
(``docs/planning/settings-pointer-lane-convergence-plan-2026-06-13.md``)
decides the governance role-pointer binding home and declares the
``BindingSpec``, move those keys from ``DEFERRED_KEYS`` to ``MIGRATED_KEYS`` in
the same commit and this invariant enforces correctness.

Provenance (Q-0105): added 2026-06-13 (P0-3 foundation PR).  Verified against a
green ``check_quality.py --full`` run.  Load-bearing parity guard; keep.
"""

from __future__ import annotations

import importlib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_COGS_DIR = _REPO_ROOT / "disbot" / "cogs"


def _declared_bindings() -> set[tuple[str, str]]:
    """Return every declared ``(subsystem, binding_name)`` after registering schemas.

    Cogs register their schema at boot; the test runner does not load cogs, so
    we trigger registration directly (glob-discovered, so a new subsystem
    schema is picked up automatically).  Registration is idempotent.
    """
    from core.runtime.subsystem_schema import all_schemas

    for schema_path in sorted(_COGS_DIR.glob("*/schemas.py")):
        module_path = f"cogs.{schema_path.parent.name}.schemas"
        mod = importlib.import_module(module_path)
        register = getattr(mod, "register_schemas", None)
        if register is None:
            continue
        try:
            register()
        except Exception:  # noqa: BLE001 — idempotent re-register is fine
            pass

    return {
        (sub, b.name) for sub, schema in all_schemas().items() for b in schema.bindings
    }


def _binding_kind(subsystem: str, binding_name: str) -> str | None:
    from core.runtime.subsystem_schema import all_schemas

    schema = all_schemas().get(subsystem)
    if schema is None:
        return None
    for b in schema.bindings:
        if b.name == binding_name:
            return b.kind.value
    return None


def test_every_migrated_key_target_is_declared():
    """Every ``MIGRATED_KEYS`` target resolves to a declared ``BindingSpec``."""
    from services.binding_backfill import MIGRATED_KEYS

    declared = _declared_bindings()
    missing = [
        f"{mk.legacy_key} → {mk.subsystem}.{mk.binding_name}"
        for mk in MIGRATED_KEYS
        if (mk.subsystem, mk.binding_name) not in declared
    ]
    assert not missing, (
        "These MIGRATED_KEYS target a binding that is NOT a declared "
        "BindingSpec — the backfill would return BLOCKED_NO_SCHEMA for every "
        "guild.  Declare the BindingSpec, or move the key to DEFERRED_KEYS "
        "with the schema-home decision routed to the P0-3 plan:\n"
        + "\n".join(f"  {m}" for m in missing)
    )


def test_migrated_key_kind_matches_declared_binding():
    """A mapping's ``kind`` matches its declared ``BindingSpec.kind``."""
    from services.binding_backfill import MIGRATED_KEYS

    _declared_bindings()  # ensure schemas registered
    mismatches = []
    for mk in MIGRATED_KEYS:
        declared_kind = _binding_kind(mk.subsystem, mk.binding_name)
        if declared_kind is not None and declared_kind != mk.kind.value:
            mismatches.append(
                f"{mk.legacy_key}: mapping kind={mk.kind.value!r} but "
                f"{mk.subsystem}.{mk.binding_name} BindingSpec kind={declared_kind!r}",
            )
    assert not mismatches, "Backfill kind drift:\n" + "\n".join(
        f"  {m}" for m in mismatches
    )


def test_every_deferred_key_target_is_undeclared():
    """A ``DEFERRED_KEYS`` target must NOT be a declared ``BindingSpec``.

    If its binding home has been declared, the key is migratable and belongs in
    ``MIGRATED_KEYS`` — leaving it deferred would silently strand a ready
    migration.
    """
    from services.binding_backfill import DEFERRED_KEYS

    declared = _declared_bindings()
    graduated = [
        f"{mk.legacy_key} → {mk.subsystem}.{mk.binding_name}"
        for mk in DEFERRED_KEYS
        if (mk.subsystem, mk.binding_name) in declared
    ]
    assert not graduated, (
        "These DEFERRED_KEYS now have a declared BindingSpec home — move them "
        "to MIGRATED_KEYS in the same commit that declares the binding:\n"
        + "\n".join(f"  {m}" for m in graduated)
    )


def test_no_key_in_both_registries():
    """A legacy key is migratable or deferred, never both."""
    from services.binding_backfill import DEFERRED_KEYS, MIGRATED_KEYS

    migrated = {mk.legacy_key for mk in MIGRATED_KEYS}
    deferred = {mk.legacy_key for mk in DEFERRED_KEYS}
    overlap = migrated & deferred
    assert (
        not overlap
    ), f"keys in both MIGRATED_KEYS and DEFERRED_KEYS: {sorted(overlap)}"
