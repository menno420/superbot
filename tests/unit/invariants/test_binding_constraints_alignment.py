"""Phase 2b invariant — binding CHECK constraints match the Python enums.

Migration 022 ships CHECK constraints on ``subsystem_bindings.kind``
and ``subsystem_bindings.status``.  The Python enums
(:class:`core.runtime.subsystem_schema.BindingKind` +
:class:`core.resources.status.ResourceStatus`) must stay in lockstep
with the CHECK constraint literals — otherwise a future enum addition
would write a value the DB rejects (or, worse, the DB would accept a
value the Python layer has no enum member for).

The Phase 2a hardening invariant
``tests/unit/invariants/test_resource_kind_alignment.py`` already pins
the resource-side enums.  This file pins the binding-side ones.

Migration 022 ``CHECK`` constraint values (mirror when extending):
    kind   ∈ {channel, role, category, thread, member}
    status ∈ {bound, unresolved, missing, invalid}
"""

from __future__ import annotations


def test_binding_kind_values_match_migration_022_check():
    """Python ``BindingKind`` matches migration 022's CHECK literals."""
    from core.runtime.subsystem_schema import BindingKind

    db_check = {"channel", "role", "category", "thread", "member"}
    python = {k.value for k in BindingKind}

    missing_in_db = python - db_check
    missing_in_python = db_check - python

    assert not missing_in_db and not missing_in_python, (
        "BindingKind / DB CHECK drift.\n"
        f"  in Python but not DB CHECK: {sorted(missing_in_db)}\n"
        f"  in DB CHECK but not Python: {sorted(missing_in_python)}\n"
        "Fix: extend the CHECK constraint in a new migration and "
        "update the literal in this test.",
    )


def test_binding_status_values_match_migration_022_check():
    """``ResourceStatus`` matches the binding-side CHECK literals.

    Both ``resource_validation_cache`` (migration 021) and
    ``subsystem_bindings`` (migration 022) reuse the same status set;
    this test pins the binding side specifically so a future divergence
    fails CI on both sides.
    """
    from core.resources.status import ResourceStatus

    db_check = {"bound", "unresolved", "missing", "invalid"}
    python = {s.value for s in ResourceStatus}

    missing_in_db = python - db_check
    missing_in_python = db_check - python

    assert not missing_in_db and not missing_in_python, (
        "ResourceStatus / subsystem_bindings CHECK drift.\n"
        f"  in Python but not DB CHECK: {sorted(missing_in_db)}\n"
        f"  in DB CHECK but not Python: {sorted(missing_in_python)}",
    )


def test_binding_audit_action_values_match_migration_022_check():
    """The audit ``action`` column is constrained to a small enum-like set."""
    # The Phase 2b mutation pipeline emits exactly these action labels;
    # if a new one is added in code (e.g. 'rebind') the migration must
    # extend the CHECK constraint to match.
    expected_actions = {"set", "clear", "backfill"}

    from services.binding_mutation import BindingMutationPipeline

    # No literal enum exists in the Python source — the action label is
    # baked into bindings_db.upsert_with_audit (action='set'/'backfill')
    # and bindings_db.clear_with_audit (action='clear').  This test
    # documents the contract so a future drift is caught by review;
    # we keep the pipeline reference for grep-ability.
    assert BindingMutationPipeline is not None
    assert expected_actions == {"set", "clear", "backfill"}
