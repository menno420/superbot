"""Phase 9c.2 — cross-pipeline ``audit.action_recorded`` wiring contract.

Every production mutation pipeline must publish the canonical audit
event through the shared helper in :mod:`services.audit_events`. This
test file pins the static wiring so a future refactor that
accidentally duplicates the publisher (rather than importing it) is
caught at test time.

Per-pipeline payload-shape and DB-row correlation assertions live in
the individual pipeline test files
(``tests/unit/services/test_settings_mutation_pipeline.py``,
``tests/unit/bindings/test_binding_mutation_pipeline.py``,
``tests/unit/services/test_resource_provisioning_pipeline.py``,
``tests/unit/participation/test_participation_mutation_pipeline.py``)
where mock setup is already in place.
"""

from __future__ import annotations

import importlib

import pytest

PIPELINE_MODULES = (
    "services.settings_mutation",
    "services.binding_mutation",
    "services.resource_provisioning",
    "services.participation_mutation",
    "governance.writes",
)


@pytest.mark.parametrize("module_path", PIPELINE_MODULES)
def test_pipeline_imports_shared_audit_helper(module_path):
    """Each pipeline must import ``emit_audit_action`` so it can be
    patched at the call site from tests and so the audit publisher
    is a true shared service (not a copy)."""
    mod = importlib.import_module(module_path)
    helper = getattr(mod, "emit_audit_action", None)
    assert helper is not None, (
        f"{module_path} is missing the shared emit_audit_action import; "
        "every pipeline must route its audit emission through "
        "services.audit_events.emit_audit_action."
    )
    from services.audit_events import emit_audit_action

    assert helper is emit_audit_action, (
        f"{module_path}.emit_audit_action is shadowed by a local "
        "rebinding; the shared publisher must remain identity-equal "
        "to the canonical function."
    )


@pytest.mark.parametrize("module_path", PIPELINE_MODULES)
def test_pipeline_does_not_redefine_audit_emit(module_path):
    """No pipeline may carry a local ``_emit_audit_event`` /
    ``emit_audit_event`` helper alongside the shared import — that
    is the bug shape this refactor exists to prevent."""
    mod = importlib.import_module(module_path)
    for forbidden in ("_emit_audit_event", "emit_audit_event"):
        assert not hasattr(mod, forbidden), (
            f"{module_path} still defines {forbidden!r}; delete the "
            "local helper and route through "
            "services.audit_events.emit_audit_action instead."
        )
