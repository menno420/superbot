"""Phase 2a hardening — ResourceKind enum drift protection.

Two enums spell out the resource taxonomy:

* :class:`core.runtime.resource_specs.ResourceKind` — the *declaration*
  side.  Phase 1c subsystem schemas use it to declare what kinds of
  resources they need.
* :class:`core.resources.types.ResourceKind` — the *snapshot* side.
  Phase 2a's discovery layer produces snapshots tagged with this enum.

The two layers are independent (a snapshot may exist for a kind a
schema hasn't declared yet — an orphan; a schema may declare a kind
before any guild has that resource), so they live in separate modules.
That independence creates a drift risk: if someone adds ``FORUM`` to
one enum and not the other, Phase 2b's binding pipeline would either
reject a valid declaration or accept a snapshot whose kind it doesn't
understand.

This invariant test pins the two enums to the same ``.value`` set so
the drift fails fast at CI time rather than silently in production.
The migration-021 CHECK constraints + this Python invariant together
prevent drift in either direction (Python vs Python; Python vs DB).
"""

from __future__ import annotations


def test_resource_kind_enum_values_match():
    """Snapshot-side and declaration-side ResourceKind agree on members."""
    from core.resources.types import ResourceKind as SnapshotKind
    from core.runtime.resource_specs import ResourceKind as DeclKind

    snap_values = {k.value for k in SnapshotKind}
    decl_values = {k.value for k in DeclKind}

    extra_in_snap = snap_values - decl_values
    extra_in_decl = decl_values - snap_values

    assert not extra_in_snap and not extra_in_decl, (
        "ResourceKind drift detected — Phase 2a snapshot enum and Phase "
        "1c declaration enum must agree on member values.\n"
        f"  in snapshot but not declaration: {sorted(extra_in_snap)}\n"
        f"  in declaration but not snapshot: {sorted(extra_in_decl)}\n"
        "Fix: update both enums in lockstep; Phase 2b's binding "
        "pipeline routes by kind and cannot tolerate a one-sided "
        "addition.",
    )


def test_resource_kind_values_match_migration_021_check():
    """Python enum values match the DB-level CHECK constraint in migration 021.

    If a new kind is added to the Python enum, this test fails until
    migration 02X is added that extends the CHECK constraint.  That is
    the desired forcing function — DB and Python stay aligned.
    """
    from core.resources.types import ResourceKind

    # Mirror of migration 021's CHECK constraint value list.  Update
    # *both* when adding a new kind: this list and the migration.
    db_check_values = {"channel", "role", "category", "thread"}

    python_values = {k.value for k in ResourceKind}
    missing_in_db = python_values - db_check_values
    missing_in_python = db_check_values - python_values

    assert not missing_in_db and not missing_in_python, (
        "ResourceKind / DB CHECK-constraint drift detected.\n"
        f"  in Python but not DB CHECK: {sorted(missing_in_db)}\n"
        f"  in DB CHECK but not Python: {sorted(missing_in_python)}\n"
        "Fix: ship a new migration that ALTERs the CHECK constraint, "
        "and update the literal in this test.",
    )


def test_resource_status_values_match_migration_021_check():
    """Python ResourceStatus enum matches the DB CHECK constraint values."""
    from core.resources.status import ResourceStatus

    db_check_values = {"bound", "unresolved", "missing", "invalid"}
    python_values = {s.value for s in ResourceStatus}

    missing_in_db = python_values - db_check_values
    missing_in_python = db_check_values - python_values

    assert not missing_in_db and not missing_in_python, (
        "ResourceStatus / DB CHECK-constraint drift detected.\n"
        f"  in Python but not DB CHECK: {sorted(missing_in_db)}\n"
        f"  in DB CHECK but not Python: {sorted(missing_in_python)}",
    )
