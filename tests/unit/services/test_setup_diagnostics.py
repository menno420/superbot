"""Tests for the setup diagnostics & repair service (server-management PR12).

Pins:

* Classification — each ``resource_health`` status maps to the right
  severity + repairability; healthy slots produce no finding.
* Repair generation — only ``stale_binding`` / ``wrong_type`` generate a
  ``clear_binding`` SetupOperation; advisory / blocked findings carry no
  ops.
* ``staged_repair_ops`` flattens only the auto-repairable batches.
* Report partitioning (counts / repairable / advisory / is_healthy).
* ``collect_setup_diagnostics`` composes the four collectors and sorts by
  severity, and is fail-safe when a detector raises.
* Each collector maps its detector's verdicts (role thresholds,
  moderation roles, cleanup) into the right advisory findings.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from core.runtime.command_access import AccessMode
from core.runtime.subsystem_schema import BindingKind
from services import resource_health, setup_diagnostics
from services.resource_health import ResourceHealthFinding


def _rh(status: str, *, kind: BindingKind = BindingKind.CHANNEL, target_id=None):
    return ResourceHealthFinding(
        subsystem="logging",
        binding_name="mod_channel",
        kind=kind,
        status=status,
        severity="error",
        message=f"msg for {status}",
        target_id=target_id,
    )


# ---------------------------------------------------------------------------
# _map_binding_finding — classification + repair generation
# ---------------------------------------------------------------------------


def test_healthy_binding_statuses_produce_no_finding():
    assert setup_diagnostics._map_binding_finding(_rh(resource_health.OK)) is None
    assert (
        setup_diagnostics._map_binding_finding(_rh(resource_health.NOT_CONFIGURED))
        is None
    )


def test_stale_binding_is_auto_repairable_clear_binding():
    finding = setup_diagnostics._map_binding_finding(
        _rh(resource_health.STALE_BINDING, target_id=999),
    )
    assert finding is not None
    assert finding.code == "stale_binding"
    assert finding.severity == setup_diagnostics.SEV_WARNING
    assert finding.repairability == setup_diagnostics.REPAIR_AUTO
    assert finding.is_auto_repairable
    assert len(finding.repair_ops) == 1
    op = finding.repair_ops[0]
    assert op.kind == "clear_binding"
    assert op.subsystem == "logging"
    assert op.binding_name == "mod_channel"
    assert op.target_kind == "channel"
    assert op.metadata["source"] == "diagnostics_repair"


def test_wrong_type_binding_is_auto_repairable():
    finding = setup_diagnostics._map_binding_finding(_rh(resource_health.WRONG_TYPE))
    assert finding is not None
    assert finding.code == "wrong_type_binding"
    assert finding.repairability == setup_diagnostics.REPAIR_AUTO
    assert finding.repair_ops[0].kind == "clear_binding"


def test_missing_required_binding_is_advisory_no_ops():
    finding = setup_diagnostics._map_binding_finding(_rh(resource_health.MISSING))
    assert finding is not None
    assert finding.code == "missing_required_binding"
    assert finding.severity == setup_diagnostics.SEV_WARNING
    assert finding.repairability == setup_diagnostics.REPAIR_ADVISORY
    assert finding.repair_ops == ()
    assert finding.section_slug == "channels"
    assert finding.advisory_note


def test_unbound_binding_is_advisory():
    finding = setup_diagnostics._map_binding_finding(_rh(resource_health.UNBOUND))
    assert finding is not None
    assert finding.code == "unbound_binding"
    assert finding.severity == setup_diagnostics.SEV_ADVISORY
    assert finding.repair_ops == ()


def test_permission_blocked_is_blocked_no_ops():
    finding = setup_diagnostics._map_binding_finding(
        _rh(resource_health.PERMISSION_BLOCKED, target_id=5),
    )
    assert finding is not None
    assert finding.repairability == setup_diagnostics.REPAIR_BLOCKED
    assert finding.repair_ops == ()
    assert not finding.is_auto_repairable


def test_hierarchy_blocked_is_blocked_no_ops():
    finding = setup_diagnostics._map_binding_finding(
        _rh(resource_health.HIERARCHY_BLOCKED, kind=BindingKind.ROLE, target_id=7),
    )
    assert finding is not None
    assert finding.code == "binding_hierarchy_blocked"
    assert finding.repairability == setup_diagnostics.REPAIR_BLOCKED
    assert finding.resource_type == "role"
    assert finding.repair_ops == ()


def test_unknown_status_is_info_advisory():
    finding = setup_diagnostics._map_binding_finding(_rh(resource_health.UNKNOWN))
    assert finding is not None
    assert finding.severity == setup_diagnostics.SEV_INFO
    assert finding.repairability == setup_diagnostics.REPAIR_ADVISORY


def test_role_binding_section_is_not_channels():
    finding = setup_diagnostics._map_binding_finding(
        _rh(resource_health.MISSING, kind=BindingKind.ROLE),
    )
    assert finding is not None
    # Role bindings have no "Channels" home — section hint stays None.
    assert finding.section_slug is None


# ---------------------------------------------------------------------------
# staged_repair_ops
# ---------------------------------------------------------------------------


def test_staged_repair_ops_flattens_only_auto_repairable():
    auto = setup_diagnostics._map_binding_finding(_rh(resource_health.STALE_BINDING))
    advisory = setup_diagnostics._map_binding_finding(_rh(resource_health.MISSING))
    blocked = setup_diagnostics._map_binding_finding(
        _rh(resource_health.PERMISSION_BLOCKED),
    )
    ops = setup_diagnostics.staged_repair_ops([auto, advisory, blocked])
    assert len(ops) == 1
    assert ops[0].kind == "clear_binding"


# ---------------------------------------------------------------------------
# Report partitioning
# ---------------------------------------------------------------------------


def _finding(code: str, severity: str, repairability: str, ops=()):
    return setup_diagnostics.SetupDiagnosticFinding(
        code=code,
        severity=severity,
        subsystem="x",
        section_slug=None,
        resource_type=None,
        resource_id=None,
        summary="s",
        detail="d",
        repairability=repairability,
        repair_ops=tuple(ops),
    )


def test_report_counts_and_partitions():
    from services.setup_operations import SetupOperation

    op = SetupOperation(kind="clear_binding", subsystem="x")
    findings = (
        _finding(
            "a", setup_diagnostics.SEV_WARNING, setup_diagnostics.REPAIR_AUTO, (op,)
        ),
        _finding(
            "b", setup_diagnostics.SEV_ADVISORY, setup_diagnostics.REPAIR_ADVISORY
        ),
        _finding("c", setup_diagnostics.SEV_INFO, setup_diagnostics.REPAIR_ADVISORY),
    )
    report = setup_diagnostics.SetupDiagnosticsReport(guild_id=1, findings=findings)
    assert report.counts[setup_diagnostics.SEV_WARNING] == 1
    assert report.counts[setup_diagnostics.SEV_ADVISORY] == 1
    assert len(report.repairable) == 1
    assert len(report.advisory) == 2
    assert report.has_findings
    assert not report.is_healthy


def test_report_is_healthy_when_only_info():
    findings = (
        _finding("c", setup_diagnostics.SEV_INFO, setup_diagnostics.REPAIR_ADVISORY),
    )
    report = setup_diagnostics.SetupDiagnosticsReport(guild_id=1, findings=findings)
    assert report.is_healthy


def test_report_empty_is_healthy():
    report = setup_diagnostics.SetupDiagnosticsReport(guild_id=1, findings=())
    assert report.is_healthy
    assert not report.has_findings


# ---------------------------------------------------------------------------
# collect_setup_diagnostics — composition + sorting + fail-safe
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_collect_composes_and_sorts_by_severity():
    guild = SimpleNamespace(id=1)
    advisory = _finding(
        "adv",
        setup_diagnostics.SEV_ADVISORY,
        setup_diagnostics.REPAIR_ADVISORY,
    )
    warning = _finding(
        "warn",
        setup_diagnostics.SEV_WARNING,
        setup_diagnostics.REPAIR_AUTO,
    )
    with (
        patch.object(
            setup_diagnostics,
            "_diagnose_bindings",
            new=AsyncMock(return_value=[advisory]),
        ),
        patch.object(
            setup_diagnostics,
            "_diagnose_role_thresholds",
            new=AsyncMock(return_value=[warning]),
        ),
        patch.object(
            setup_diagnostics,
            "_diagnose_moderation_roles",
            new=AsyncMock(return_value=[]),
        ),
        patch.object(
            setup_diagnostics,
            "_diagnose_cleanup",
            new=AsyncMock(return_value=[]),
        ),
        patch.object(
            setup_diagnostics,
            "_diagnose_routing_access_conflict",
            new=AsyncMock(return_value=[]),
        ),
    ):
        report = await setup_diagnostics.collect_setup_diagnostics(guild)
    # Warning sorts before advisory regardless of collector order.
    assert [f.code for f in report.findings] == ["warn", "adv"]


@pytest.mark.asyncio
async def test_diagnose_bindings_is_failsafe_on_detector_error():
    guild = SimpleNamespace(id=1)
    with patch.object(
        resource_health,
        "inspect",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        out = await setup_diagnostics._diagnose_bindings(guild)
    assert out == []


@pytest.mark.asyncio
async def test_diagnose_bindings_maps_inspect_verdicts():
    guild = SimpleNamespace(id=1)
    verdicts = (
        _rh(resource_health.OK),
        _rh(resource_health.STALE_BINDING),
    )
    with patch.object(resource_health, "inspect", new=AsyncMock(return_value=verdicts)):
        out = await setup_diagnostics._diagnose_bindings(guild)
    assert [f.code for f in out] == ["stale_binding"]


# ---------------------------------------------------------------------------
# Role-threshold collector
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_role_threshold_stale_when_role_unresolvable():
    guild = SimpleNamespace(id=1, me=SimpleNamespace(id=2))
    rows = [
        {"role_id": 555, "role_name": "Old", "display_name": "Old", "days_required": 7}
    ]
    with (
        patch("utils.db.roles.get_role_thresholds", new=AsyncMock(return_value=rows)),
        patch("core.runtime.guild_resources.resolve_role", return_value=None),
    ):
        out = await setup_diagnostics._diagnose_role_thresholds(guild)
    assert len(out) == 1
    assert out[0].code == "stale_role_threshold"
    assert out[0].repairability == setup_diagnostics.REPAIR_ADVISORY
    assert out[0].repair_ops == ()


@pytest.mark.asyncio
async def test_role_threshold_unassignable_when_above_bot():
    from utils.role_feasibility import ABOVE_BOT, RoleFeasibility

    guild = SimpleNamespace(id=1, me=SimpleNamespace(id=2))
    rows = [
        {"role_id": 555, "role_name": "Top", "display_name": "Top", "days_required": 7}
    ]
    role = SimpleNamespace(id=555, name="Top")
    verdict = RoleFeasibility(555, "Top", ok=False, code=ABOVE_BOT, reason="above me")
    with (
        patch("utils.db.roles.get_role_thresholds", new=AsyncMock(return_value=rows)),
        patch("core.runtime.guild_resources.resolve_role", return_value=role),
        patch("utils.role_feasibility.evaluate_role", return_value=verdict),
    ):
        out = await setup_diagnostics._diagnose_role_thresholds(guild)
    assert len(out) == 1
    assert out[0].code == "role_threshold_unassignable"
    assert out[0].repairability == setup_diagnostics.REPAIR_BLOCKED


@pytest.mark.asyncio
async def test_role_threshold_healthy_role_no_finding():
    from utils.role_feasibility import RoleFeasibility

    guild = SimpleNamespace(id=1, me=SimpleNamespace(id=2))
    rows = [
        {"role_id": 555, "role_name": "Ok", "display_name": "Ok", "days_required": 7}
    ]
    role = SimpleNamespace(id=555, name="Ok")
    verdict = RoleFeasibility(555, "Ok", ok=True, code="selectable", reason="")
    with (
        patch("utils.db.roles.get_role_thresholds", new=AsyncMock(return_value=rows)),
        patch("core.runtime.guild_resources.resolve_role", return_value=role),
        patch("utils.role_feasibility.evaluate_role", return_value=verdict),
    ):
        out = await setup_diagnostics._diagnose_role_thresholds(guild)
    assert out == []


# ---------------------------------------------------------------------------
# Moderation-role collector
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moderation_role_stale_when_deleted():
    guild = SimpleNamespace(id=1)
    with (
        patch(
            "core.runtime.config_arbitration.get_moderator_tier_role",
            new=AsyncMock(return_value=SimpleNamespace(value=123)),
        ),
        patch(
            "core.runtime.config_arbitration.get_trusted_tier_role",
            new=AsyncMock(return_value=SimpleNamespace(value=None)),
        ),
        patch("core.runtime.guild_resources.resolve_role", return_value=None),
    ):
        out = await setup_diagnostics._diagnose_moderation_roles(guild)
    assert len(out) == 1
    assert out[0].code == "stale_moderation_role"
    assert out[0].resource_id == 123
    assert out[0].repairability == setup_diagnostics.REPAIR_ADVISORY


@pytest.mark.asyncio
async def test_moderation_role_not_configured_no_finding():
    guild = SimpleNamespace(id=1)
    with (
        patch(
            "core.runtime.config_arbitration.get_moderator_tier_role",
            new=AsyncMock(return_value=SimpleNamespace(value=None)),
        ),
        patch(
            "core.runtime.config_arbitration.get_trusted_tier_role",
            new=AsyncMock(return_value=SimpleNamespace(value=None)),
        ),
    ):
        out = await setup_diagnostics._diagnose_moderation_roles(guild)
    assert out == []


# ---------------------------------------------------------------------------
# Cleanup collector
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cleanup_collector_maps_stale_and_ineffective():
    guild = SimpleNamespace(id=1)
    diag = SimpleNamespace(
        ineffective_rows=(SimpleNamespace(scope_type="guild", scope_id=0),),
        stale_rows=(SimpleNamespace(scope_type="channel", scope_id=999),),
    )
    with patch(
        "services.cleanup_diagnostics.collect_cleanup_diagnostics",
        new=AsyncMock(return_value=diag),
    ):
        out = await setup_diagnostics._diagnose_cleanup(guild)
    codes = {f.code for f in out}
    assert codes == {"ineffective_cleanup_policy", "stale_cleanup_policy"}
    assert all(f.repairability == setup_diagnostics.REPAIR_ADVISORY for f in out)


@pytest.mark.asyncio
async def test_cleanup_collector_failsafe():
    guild = SimpleNamespace(id=1)
    with patch(
        "services.cleanup_diagnostics.collect_cleanup_diagnostics",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        out = await setup_diagnostics._diagnose_cleanup(guild)
    assert out == []


# ---------------------------------------------------------------------------
# Routing ↔ command-access conflict collector (P1B)
# ---------------------------------------------------------------------------


def _access_policy(mode, allowed=frozenset()):
    return SimpleNamespace(mode=mode, allowed_channels=frozenset(allowed))


def _routing_rows(*rows):
    """Build routing rows with the list_for_guild shape."""
    out = []
    for scope_type, scope_id, cog_name, enabled in rows:
        out.append(
            {
                "scope_type": scope_type,
                "scope_id": scope_id,
                "cog_name": cog_name,
                "enabled": enabled,
            },
        )
    return out


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [None, AccessMode.ALL_CHANNELS.value])
async def test_routing_conflict_none_when_access_unrestricted(mode):
    """No command-access restriction → routing can never conflict, and the
    routing rows aren't even read.
    """
    guild = SimpleNamespace(id=1)
    list_rows = AsyncMock()
    with (
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(return_value=_access_policy(mode)),
        ),
        patch("services.command_routing.list_for_guild", new=list_rows),
    ):
        out = await setup_diagnostics._diagnose_routing_access_conflict(guild)
    assert out == []
    list_rows.assert_not_awaited()  # short-circuits before reading routing


@pytest.mark.asyncio
async def test_routing_conflict_selected_channels_flags_disallowed_channel():
    guild = SimpleNamespace(id=1)
    rows = _routing_rows(("channel", 20, "games", True))
    with (
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(
                return_value=_access_policy(
                    AccessMode.SELECTED_CHANNELS.value,
                    allowed={10},
                ),
            ),
        ),
        patch("services.command_routing.list_for_guild", new=AsyncMock(return_value=rows)),
        patch(
            "core.runtime.guild_resources.resolve_channel",
            return_value=SimpleNamespace(name="games-chat"),
        ),
    ):
        out = await setup_diagnostics._diagnose_routing_access_conflict(guild)
    assert len(out) == 1
    f = out[0]
    assert f.code == "routing_access_conflict"
    assert f.severity == setup_diagnostics.SEV_WARNING
    assert f.subsystem == "games"
    assert f.resource_id == 20
    assert f.repairability == setup_diagnostics.REPAIR_ADVISORY
    assert "#games-chat" in f.summary


@pytest.mark.asyncio
async def test_routing_conflict_no_finding_when_channel_allowed():
    guild = SimpleNamespace(id=1)
    rows = _routing_rows(("channel", 10, "games", True))
    with (
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(
                return_value=_access_policy(
                    AccessMode.SELECTED_CHANNELS.value,
                    allowed={10},
                ),
            ),
        ),
        patch("services.command_routing.list_for_guild", new=AsyncMock(return_value=rows)),
    ):
        out = await setup_diagnostics._diagnose_routing_access_conflict(guild)
    assert out == []


@pytest.mark.asyncio
async def test_routing_conflict_ignores_guild_scope_and_disabled_rows():
    """Only channel-scoped 'enabled' rows conflict — a guild-scope enable (cog on
    broadly, commands run in the allowed channels) and a disabled channel row are
    not conflicts.
    """
    guild = SimpleNamespace(id=1)
    rows = _routing_rows(
        ("guild", None, "games", True),  # broad enable — not a conflict
        ("channel", 20, "economy", False),  # disabled — intentional, not a conflict
    )
    with (
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(
                return_value=_access_policy(
                    AccessMode.SELECTED_CHANNELS.value,
                    allowed={10},
                ),
            ),
        ),
        patch("services.command_routing.list_for_guild", new=AsyncMock(return_value=rows)),
    ):
        out = await setup_diagnostics._diagnose_routing_access_conflict(guild)
    assert out == []


@pytest.mark.asyncio
async def test_routing_conflict_disabled_except_bootstrap_advisory():
    guild = SimpleNamespace(id=1)
    rows = _routing_rows(
        ("guild", None, "games", True),
        ("guild", None, "economy", True),
        ("guild", None, "moderation", False),  # disabled — not listed
    )
    with (
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(
                return_value=_access_policy(AccessMode.DISABLED_EXCEPT_BOOTSTRAP.value),
            ),
        ),
        patch("services.command_routing.list_for_guild", new=AsyncMock(return_value=rows)),
    ):
        out = await setup_diagnostics._diagnose_routing_access_conflict(guild)
    assert len(out) == 1
    f = out[0]
    assert f.code == "routing_access_conflict"
    assert f.severity == setup_diagnostics.SEV_ADVISORY
    assert f.resource_type == "guild"
    # Only the enabled cogs are named.
    assert "games" in f.detail and "economy" in f.detail
    assert "moderation" not in f.detail


@pytest.mark.asyncio
async def test_routing_conflict_disabled_except_bootstrap_no_enabled_rows():
    guild = SimpleNamespace(id=1)
    rows = _routing_rows(("guild", None, "games", False))
    with (
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(
                return_value=_access_policy(AccessMode.DISABLED_EXCEPT_BOOTSTRAP.value),
            ),
        ),
        patch("services.command_routing.list_for_guild", new=AsyncMock(return_value=rows)),
    ):
        out = await setup_diagnostics._diagnose_routing_access_conflict(guild)
    assert out == []


@pytest.mark.asyncio
async def test_routing_conflict_failsafe_on_read_error():
    guild = SimpleNamespace(id=1)
    with patch(
        "utils.guild_config_accessors.get_command_access_policy",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        out = await setup_diagnostics._diagnose_routing_access_conflict(guild)
    assert out == []
