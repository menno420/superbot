"""Phase 1a unit tests — SubsystemSchema registry contract.

Verifies the registration / lookup / re-registration semantics of the
:mod:`core.runtime.subsystem_schema` registry and the integration with
:mod:`services.diagnostics_service`.
"""

from __future__ import annotations

import pytest

from core.runtime.resource_specs import (
    ProvisioningHint,
    ProvisioningPriority,
    ResourceKind,
    ResourceRequirement,
)
from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SettingSpec,
    SubsystemSchema,
    all_schemas,
    get_schema,
    register,
    registered_subsystems,
)
from core.runtime.subsystem_schema import _reset_for_tests as _reset_schemas


@pytest.fixture
def _clean_schemas():
    _reset_schemas()
    try:
        yield
    finally:
        _reset_schemas()


def _build_schema(name: str = "alpha") -> SubsystemSchema:
    return SubsystemSchema(
        subsystem=name,
        bindings=(
            BindingSpec(
                name="log_channel",
                kind=BindingKind.CHANNEL,
                required=False,
                hint="Test",
                capability_required="alpha.settings.configure",
            ),
        ),
        settings=(
            SettingSpec(
                name="threshold",
                value_type=int,
                default=3,
                settings_key="alpha_threshold",
                capability_required="alpha.settings.configure",
                hint="Test",
            ),
        ),
        resource_requirements=(
            ResourceRequirement(
                kind=ResourceKind.CHANNEL,
                intent="log",
                provisioning=ProvisioningHint(
                    priority=ProvisioningPriority.OPTIONAL,
                    suggested_name="alpha-log",
                ),
                binding_name="log_channel",
            ),
        ),
        version=1,
    )


def test_register_and_lookup_round_trips(_clean_schemas):
    schema = _build_schema("alpha")
    register(schema)
    assert get_schema("alpha") is schema
    assert get_schema("missing") is None
    assert all_schemas() == {"alpha": schema}
    assert registered_subsystems() == ["alpha"]


def test_re_registration_replaces(_clean_schemas):
    a = _build_schema("alpha")
    b = SubsystemSchema(subsystem="alpha", version=2)
    register(a)
    register(b)
    assert get_schema("alpha") is b
    assert get_schema("alpha").version == 2


def test_registered_subsystems_is_sorted(_clean_schemas):
    register(_build_schema("zulu"))
    register(_build_schema("alpha"))
    register(_build_schema("mike"))
    assert registered_subsystems() == ["alpha", "mike", "zulu"]


def test_immutable_schema_field_tuples(_clean_schemas):
    schema = _build_schema("alpha")
    assert isinstance(schema.bindings, tuple)
    assert isinstance(schema.settings, tuple)
    assert isinstance(schema.resource_requirements, tuple)


def test_diagnostics_provider_registered(_clean_schemas):
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("schemas")
    assert "registered" in snap
    assert "by_subsystem" in snap
    register(_build_schema("alpha"))
    snap = diagnostics_service.snapshot("schemas")
    assert snap["registered"] == 1
    assert "alpha" in snap["by_subsystem"]


def test_resource_requirements_provider(_clean_schemas):
    from services import diagnostics_service

    register(_build_schema("alpha"))
    snap = diagnostics_service.snapshot("resource_requirements")
    assert len(snap) == 1
    assert snap[0]["subsystem"] == "alpha"
    assert snap[0]["kind"] == "channel"
    assert snap[0]["intent"] == "log"
