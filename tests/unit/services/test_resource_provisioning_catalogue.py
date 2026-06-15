"""Unit tests for services.resource_provisioning_catalogue — S2.5.

Covers the builder, cross-link logic, every findings bucket, query
API, immutability, cache replacement, the diagnostics provider, and
the round-trip of suggested-name/category/permissions/description.
"""

from __future__ import annotations

import pytest

from core.runtime import subsystem_schema as schema_mod
from core.runtime.resource_specs import (
    ProvisioningHint,
    ProvisioningPriority,
    ResourceKind,
    ResourceRequirement,
)
from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SubsystemSchema,
)
from services import resource_provisioning_catalogue as rpc_mod
from services.resource_provisioning_catalogue import (
    ProvisioningCatalogue,
    ProvisioningFindings,
    ProvisioningOption,
    build_provisioning_catalogue,
    get_cached_provisioning_catalogue,
)

# ---------------------------------------------------------------------------
# Fixtures — snapshot live module state around each test to stay isolated.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_state():
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    rpc_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    rpc_mod._reset_for_tests()


def _binding(
    name: str,
    *,
    kind: BindingKind = BindingKind.CHANNEL,
    required: bool = False,
    hint: str = "",
    capability_required: str = "",
) -> BindingSpec:
    return BindingSpec(
        name=name,
        kind=kind,
        required=required,
        hint=hint,
        capability_required=capability_required,
    )


def _requirement(
    *,
    kind: ResourceKind = ResourceKind.CHANNEL,
    intent: str = "log_destination",
    priority: ProvisioningPriority = ProvisioningPriority.RECOMMENDED,
    suggested_name: str = "",
    suggested_category: str = "",
    suggested_permissions: tuple[str, ...] = (),
    binding_name: str = "",
    description: str = "",
) -> ResourceRequirement:
    return ResourceRequirement(
        kind=kind,
        intent=intent,
        provisioning=ProvisioningHint(
            priority=priority,
            suggested_name=suggested_name,
            suggested_category=suggested_category,
            suggested_permissions=suggested_permissions,
        ),
        binding_name=binding_name,
        description=description,
    )


def _register(
    subsystem: str,
    *,
    bindings: tuple[BindingSpec, ...] = (),
    resources: tuple[ResourceRequirement, ...] = (),
) -> None:
    schema_mod.register(
        SubsystemSchema(
            subsystem=subsystem,
            bindings=bindings,
            resource_requirements=resources,
        ),
    )


# ---------------------------------------------------------------------------
# Empty inputs
# ---------------------------------------------------------------------------


def test_build_returns_empty_snapshot_when_no_schemas():
    cat = build_provisioning_catalogue()
    assert isinstance(cat, ProvisioningCatalogue)
    assert cat.version == 1
    assert cat.options == ()
    assert cat.findings.total == 0


def test_get_cached_returns_none_before_first_build():
    assert get_cached_provisioning_catalogue() is None


def test_get_cached_returns_last_built():
    cat = build_provisioning_catalogue()
    assert get_cached_provisioning_catalogue() is cat


def test_build_schema_with_no_resource_requirements_yields_no_options():
    _register("xp", bindings=(_binding("announce_channel"),))
    cat = build_provisioning_catalogue()
    assert cat.options == ()
    assert cat.findings.total == 0


# ---------------------------------------------------------------------------
# Cross-link happy path
# ---------------------------------------------------------------------------


def test_requirement_with_matching_binding_produces_option():
    _register(
        "logging",
        bindings=(
            _binding(
                "mod_channel",
                kind=BindingKind.CHANNEL,
                required=True,
                hint="The mod log channel.",
                capability_required="logging.settings.configure",
            ),
        ),
        resources=(
            _requirement(
                kind=ResourceKind.CHANNEL,
                intent="mod_log",
                priority=ProvisioningPriority.RECOMMENDED,
                suggested_name="mod-logs",
                suggested_category="Staff",
                suggested_permissions=("view_channel", "send_messages"),
                binding_name="mod_channel",
                description="Operator-visible mod-action audit.",
            ),
        ),
    )
    cat = build_provisioning_catalogue()
    assert len(cat.options) == 1
    option = cat.options[0]
    assert option.subsystem == "logging"
    assert option.binding_name == "mod_channel"
    assert option.kind == "channel"
    assert option.binding_kind == "channel"
    assert option.priority == "recommended"
    assert option.suggested_name == "mod-logs"
    assert option.suggested_category == "Staff"
    assert option.suggested_permissions == ("view_channel", "send_messages")
    assert option.intent == "mod_log"
    assert option.description == "Operator-visible mod-action audit."
    assert option.capability_required == "logging.settings.configure"
    assert option.binding_required is True
    assert option.binding_hint == "The mod log channel."


def test_role_kind_cross_link():
    _register(
        "proof_channel",
        bindings=(
            _binding(
                "approval_role",
                kind=BindingKind.ROLE,
                required=False,
                capability_required="proof_channel.access.grant",
            ),
        ),
        resources=(
            _requirement(
                kind=ResourceKind.ROLE,
                intent="approval_role",
                priority=ProvisioningPriority.OPTIONAL,
                suggested_name="prize-approver",
                binding_name="approval_role",
            ),
        ),
    )
    cat = build_provisioning_catalogue()
    assert len(cat.options) == 1
    option = cat.options[0]
    assert option.kind == "role"
    assert option.binding_kind == "role"
    assert option.priority == "optional"


def test_category_kind_cross_link():
    _register(
        "cleanup",
        bindings=(_binding("staff_category", kind=BindingKind.CATEGORY),),
        resources=(
            _requirement(
                kind=ResourceKind.CATEGORY,
                intent="staff_category",
                suggested_name="Staff",
                binding_name="staff_category",
            ),
        ),
    )
    cat = build_provisioning_catalogue()
    assert cat.options[0].kind == "category"
    assert cat.options[0].binding_kind == "category"


def test_thread_kind_cross_link():
    _register(
        "moderation",
        bindings=(_binding("triage_thread", kind=BindingKind.THREAD),),
        resources=(
            _requirement(
                kind=ResourceKind.THREAD,
                intent="triage_thread",
                binding_name="triage_thread",
            ),
        ),
    )
    cat = build_provisioning_catalogue()
    assert cat.options[0].kind == "thread"
    assert cat.options[0].binding_kind == "thread"


def test_options_sorted_by_subsystem_alphabetically():
    _register(
        "xp",
        bindings=(_binding("announce_channel"),),
        resources=(_requirement(intent="announce", binding_name="announce_channel"),),
    )
    _register(
        "economy",
        bindings=(_binding("log_channel"),),
        resources=(_requirement(intent="economy_log", binding_name="log_channel"),),
    )
    _register(
        "moderation",
        bindings=(_binding("mod_log"),),
        resources=(_requirement(intent="mod_log", binding_name="mod_log"),),
    )
    cat = build_provisioning_catalogue()
    subsystems = [o.subsystem for o in cat.options]
    assert subsystems == sorted(subsystems)


# ---------------------------------------------------------------------------
# Findings: orphan_requirements
# ---------------------------------------------------------------------------


def test_requirement_without_binding_name_is_orphan():
    _register(
        "xp",
        resources=(
            _requirement(
                kind=ResourceKind.CHANNEL,
                intent="future_channel",
                # binding_name="" — orphan
            ),
        ),
    )
    cat = build_provisioning_catalogue()
    assert "xp/future_channel" in cat.findings.orphan_requirements
    # Orphans do NOT produce options.
    assert cat.options == ()


# ---------------------------------------------------------------------------
# Findings: binding_targets_unknown
# ---------------------------------------------------------------------------


def test_requirement_with_unknown_binding_name_is_flagged():
    _register(
        "xp",
        bindings=(_binding("announce_channel"),),
        resources=(
            _requirement(
                intent="ghost_intent",
                binding_name="ghost_binding",  # not in bindings
            ),
        ),
    )
    cat = build_provisioning_catalogue()
    assert "xp.ghost_binding" in cat.findings.binding_targets_unknown
    # An option IS still recorded so operators see the gap.
    assert len(cat.options) == 1
    option = cat.options[0]
    assert option.binding_kind is None
    assert option.binding_required is False
    assert option.binding_hint == ""
    assert option.capability_required == ""


# ---------------------------------------------------------------------------
# Findings: kind_mismatch
# ---------------------------------------------------------------------------


def test_kind_mismatch_between_requirement_and_binding_is_flagged():
    _register(
        "moderation",
        bindings=(_binding("mod_log", kind=BindingKind.ROLE),),  # ROLE, not CHANNEL
        resources=(
            _requirement(
                kind=ResourceKind.CHANNEL,
                intent="mod_log",
                binding_name="mod_log",
            ),
        ),
    )
    cat = build_provisioning_catalogue()
    flagged = cat.findings.kind_mismatch
    assert any("moderation.mod_log" in s for s in flagged)
    # The option is still emitted (with the mismatched binding_kind).
    assert len(cat.options) == 1
    option = cat.options[0]
    assert option.kind == "channel"
    assert option.binding_kind == "role"


# ---------------------------------------------------------------------------
# Findings: duplicate_options
# ---------------------------------------------------------------------------


def test_duplicate_subsystem_binding_pair_is_flagged():
    _register(
        "logging",
        bindings=(_binding("mod_channel"),),
        resources=(
            _requirement(intent="mod_log", binding_name="mod_channel"),
            _requirement(intent="audit_log", binding_name="mod_channel"),
        ),
    )
    cat = build_provisioning_catalogue()
    assert "logging.mod_channel" in cat.findings.duplicate_options
    # Only the first one becomes an option; the duplicate is skipped.
    assert len(cat.options) == 1
    assert cat.options[0].intent == "mod_log"


# ---------------------------------------------------------------------------
# Findings: total
# ---------------------------------------------------------------------------


def test_findings_total_sums_all_buckets():
    findings = ProvisioningFindings(
        orphan_requirements=("a",),
        binding_targets_unknown=("b", "c"),
        duplicate_options=("d",),
        kind_mismatch=("e", "f", "g"),
    )
    assert findings.total == 7


def test_findings_total_zero_on_clean_schema():
    _register(
        "logging",
        bindings=(_binding("mod_channel"),),
        resources=(_requirement(intent="mod_log", binding_name="mod_channel"),),
    )
    cat = build_provisioning_catalogue()
    assert cat.findings.total == 0


# ---------------------------------------------------------------------------
# Query API
# ---------------------------------------------------------------------------


def test_by_subsystem_returns_only_options_for_that_subsystem():
    _register(
        "logging",
        bindings=(_binding("mod_channel"), _binding("cleanup_channel")),
        resources=(
            _requirement(intent="mod_log", binding_name="mod_channel"),
            _requirement(intent="cleanup_log", binding_name="cleanup_channel"),
        ),
    )
    _register(
        "xp",
        bindings=(_binding("announce_channel"),),
        resources=(_requirement(intent="announce", binding_name="announce_channel"),),
    )
    cat = build_provisioning_catalogue()
    logging_options = cat.by_subsystem("logging")
    assert {o.binding_name for o in logging_options} == {
        "mod_channel",
        "cleanup_channel",
    }
    xp_options = cat.by_subsystem("xp")
    assert {o.binding_name for o in xp_options} == {"announce_channel"}
    assert cat.by_subsystem("no_such_subsystem") == ()


def test_find_returns_option_for_known_pair():
    _register(
        "logging",
        bindings=(_binding("mod_channel"),),
        resources=(_requirement(intent="mod_log", binding_name="mod_channel"),),
    )
    cat = build_provisioning_catalogue()
    option = cat.find("logging", "mod_channel")
    assert option is not None
    assert option.intent == "mod_log"


def test_find_returns_none_on_miss():
    _register(
        "logging",
        bindings=(_binding("mod_channel"),),
        resources=(_requirement(intent="mod_log", binding_name="mod_channel"),),
    )
    cat = build_provisioning_catalogue()
    assert cat.find("logging", "no_such") is None
    assert cat.find("no_such_subsystem", "mod_channel") is None


# ---------------------------------------------------------------------------
# Round-trip of provisioning hint fields
# ---------------------------------------------------------------------------


def test_suggested_name_category_permissions_round_trip():
    _register(
        "logging",
        bindings=(_binding("mod_channel"),),
        resources=(
            _requirement(
                intent="mod_log",
                binding_name="mod_channel",
                suggested_name="mod-logs",
                suggested_category="Staff",
                suggested_permissions=("view_channel", "send_messages", "embed_links"),
                description="Operator-visible mod-action audit channel.",
            ),
        ),
    )
    cat = build_provisioning_catalogue()
    option = cat.options[0]
    assert option.suggested_name == "mod-logs"
    assert option.suggested_category == "Staff"
    assert option.suggested_permissions == (
        "view_channel",
        "send_messages",
        "embed_links",
    )
    assert option.description == "Operator-visible mod-action audit channel."


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_provisioning_option_is_frozen():
    _register(
        "logging",
        bindings=(_binding("mod_channel"),),
        resources=(_requirement(intent="mod_log", binding_name="mod_channel"),),
    )
    cat = build_provisioning_catalogue()
    option = cat.options[0]
    with pytest.raises(Exception):
        option.subsystem = "other"  # type: ignore[misc]


def test_provisioning_findings_is_frozen():
    cat = build_provisioning_catalogue()
    with pytest.raises(Exception):
        cat.findings.orphan_requirements = ()  # type: ignore[misc]


def test_provisioning_catalogue_is_frozen():
    cat = build_provisioning_catalogue()
    with pytest.raises(Exception):
        cat.version = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


def test_rebuild_replaces_cached_snapshot():
    _register(
        "logging",
        bindings=(_binding("mod_channel"),),
        resources=(_requirement(intent="mod_log", binding_name="mod_channel"),),
    )
    first = build_provisioning_catalogue()
    schema_mod._reset_for_tests()
    _register(
        "logging",
        bindings=(_binding("mod_channel"), _binding("cleanup_channel")),
        resources=(
            _requirement(intent="mod_log", binding_name="mod_channel"),
            _requirement(intent="cleanup_log", binding_name="cleanup_channel"),
        ),
    )
    second = build_provisioning_catalogue()
    assert second is not first
    assert get_cached_provisioning_catalogue() is second
    assert len(second.options) == 2


# ---------------------------------------------------------------------------
# Diagnostics provider
# ---------------------------------------------------------------------------


def test_diagnostics_provider_returns_not_built_before_first_build():
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("resource_provisioning_catalogue")
    assert snap["status"] == "not_built"
    assert "hint" in snap


def test_diagnostics_provider_returns_counts_after_build():
    _register(
        "logging",
        bindings=(_binding("mod_channel"), _binding("cleanup_channel")),
        resources=(
            _requirement(
                kind=ResourceKind.CHANNEL,
                intent="mod_log",
                priority=ProvisioningPriority.RECOMMENDED,
                binding_name="mod_channel",
            ),
            _requirement(
                kind=ResourceKind.CHANNEL,
                intent="cleanup_log",
                priority=ProvisioningPriority.OPTIONAL,
                binding_name="cleanup_channel",
            ),
        ),
    )
    build_provisioning_catalogue()
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("resource_provisioning_catalogue")
    assert snap["status"] == "built"
    assert snap["version"] == 1
    assert snap["option_count"] == 2
    assert snap["subsystem_count"] == 1
    assert snap["by_priority"] == {"recommended": 1, "optional": 1}
    assert snap["by_kind"] == {"channel": 2}
    assert snap["by_subsystem"] == {"logging": 2}
    assert snap["findings_total"] == 0


def test_diagnostics_provider_is_registered_at_import_time():
    from services import diagnostics_service

    assert "resource_provisioning_catalogue" in diagnostics_service.registered_names()
