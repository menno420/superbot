"""Tests for services.server_management_hub — the PR14 hub badge composer.

The read-only model behind the Server Management hub's health badges.  Pins:

* per-manager glyph mapping (moderation / channels / roles capability),
* the cleanup + setup badges derived from the (fail-safe) diagnostics report,
* the overall config-health line,
* the fail-safe contract: a broken detector degrades one badge to ``❓`` and
  ``collect_hub_status`` never raises.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import server_management_hub as hub
from services.server_management_hub import (
    GLYPH_ATTENTION,
    GLYPH_BLOCKED,
    GLYPH_HEALTHY,
    GLYPH_UNKNOWN,
    collect_hub_status,
)
from services.setup_diagnostics import SetupDiagnosticFinding, SetupDiagnosticsReport


def _guild(
    *,
    manage_channels: bool = True,
    manage_roles: bool = True,
    ban: bool = True,
    kick: bool = True,
    timeout: bool = True,
    admin: bool = False,
    me_is_none: bool = False,
) -> MagicMock:
    guild = MagicMock()
    guild.id = 99
    if me_is_none:
        guild.me = None
        guild.roles = []
        return guild
    perms = MagicMock()
    perms.manage_channels = manage_channels
    perms.manage_roles = manage_roles
    perms.ban_members = ban
    perms.kick_members = kick
    perms.moderate_members = timeout
    perms.administrator = admin
    guild.me.guild_permissions = perms
    guild.me.top_role.position = 5
    guild.me.top_role.name = "Galaxy Bot"
    guild.roles = [MagicMock() for _ in range(6)]
    return guild


def _finding(severity: str, subsystem: str = "moderation") -> SetupDiagnosticFinding:
    return SetupDiagnosticFinding(
        code="x",
        severity=severity,
        subsystem=subsystem,
        section_slug=None,
        resource_type=None,
        resource_id=None,
        summary="s",
        detail="d",
        repairability="advisory_only",
    )


def _report(*findings: SetupDiagnosticFinding) -> SetupDiagnosticsReport:
    return SetupDiagnosticsReport(guild_id=99, findings=tuple(findings))


def _badge(status, key):
    return next(b for b in status.badges if b.key == key)


def _patch_detectors(report: SetupDiagnosticsReport | None, percentage: int | None):
    """Patch both async detectors the composer fans out to."""
    diag = (
        AsyncMock(return_value=report)
        if report is not None
        else AsyncMock(side_effect=RuntimeError("diag down"))
    )
    readiness_report = MagicMock()
    readiness_report.percentage = percentage if percentage is not None else 0
    ready = (
        AsyncMock(return_value=readiness_report)
        if percentage is not None
        else AsyncMock(side_effect=RuntimeError("readiness down"))
    )
    return patch.multiple(
        "services.setup_diagnostics",
        collect_setup_diagnostics=diag,
    ), patch("services.setup_readiness.collect", ready)


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_collect_returns_five_manager_badges():
    diag_p, ready_p = _patch_detectors(_report(), 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles",
        return_value=([MagicMock(), MagicMock()], []),
    ):
        status = await collect_hub_status(_guild())
    assert {b.key for b in status.badges} == {
        hub.MOD,
        hub.CHANNELS,
        hub.ROLES,
        hub.CLEANUP,
        hub.SETUP,
    }
    assert status.guild_id == 99


# ---------------------------------------------------------------------------
# Capability badges
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moderation_badge_healthy_when_fully_capable():
    diag_p, ready_p = _patch_detectors(_report(), 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild())
    assert _badge(status, hub.MOD).glyph == GLYPH_HEALTHY


@pytest.mark.asyncio
async def test_moderation_badge_attention_when_missing_permission():
    diag_p, ready_p = _patch_detectors(_report(), 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild(ban=False))
    badge = _badge(status, hub.MOD)
    assert badge.glyph == GLYPH_ATTENTION
    assert "Ban Members" in badge.summary


@pytest.mark.asyncio
async def test_channels_badge_blocked_without_manage_channels():
    diag_p, ready_p = _patch_detectors(_report(), 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild(manage_channels=False))
    assert _badge(status, hub.CHANNELS).glyph == GLYPH_BLOCKED


@pytest.mark.asyncio
async def test_roles_badge_blocked_without_manage_roles():
    diag_p, ready_p = _patch_detectors(_report(), 100)
    with diag_p, ready_p:
        status = await collect_hub_status(_guild(manage_roles=False))
    assert _badge(status, hub.ROLES).glyph == GLYPH_BLOCKED


@pytest.mark.asyncio
async def test_roles_badge_healthy_reports_manageable_count():
    diag_p, ready_p = _patch_detectors(_report(), 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles",
        return_value=([MagicMock(), MagicMock(), MagicMock()], [MagicMock()]),
    ):
        status = await collect_hub_status(_guild())
    badge = _badge(status, hub.ROLES)
    assert badge.glyph == GLYPH_HEALTHY
    assert "3 of 6" in badge.summary


# ---------------------------------------------------------------------------
# Cleanup + setup badges (diagnostics-derived)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cleanup_badge_attention_on_cleanup_finding():
    report = _report(_finding("warning", subsystem="cleanup"))
    diag_p, ready_p = _patch_detectors(report, 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild())
    assert _badge(status, hub.CLEANUP).glyph == GLYPH_ATTENTION


@pytest.mark.asyncio
async def test_cleanup_badge_healthy_when_no_cleanup_findings():
    report = _report(_finding("warning", subsystem="moderation"))
    diag_p, ready_p = _patch_detectors(report, 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild())
    assert _badge(status, hub.CLEANUP).glyph == GLYPH_HEALTHY


@pytest.mark.asyncio
async def test_setup_badge_blocked_when_report_has_blocker():
    report = _report(_finding("blocker", subsystem="moderation"))
    diag_p, ready_p = _patch_detectors(report, 95)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild())
    assert _badge(status, hub.SETUP).glyph == GLYPH_BLOCKED


@pytest.mark.asyncio
async def test_setup_badge_healthy_at_high_percentage():
    diag_p, ready_p = _patch_detectors(_report(), 88)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild())
    badge = _badge(status, hub.SETUP)
    assert badge.glyph == GLYPH_HEALTHY
    assert "88%" in badge.summary


@pytest.mark.asyncio
async def test_setup_badge_attention_when_unconfigured():
    diag_p, ready_p = _patch_detectors(_report(), 0)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild())
    assert _badge(status, hub.SETUP).glyph == GLYPH_ATTENTION


# ---------------------------------------------------------------------------
# Overall config-health line
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_overall_healthy_when_report_clean():
    diag_p, ready_p = _patch_detectors(_report(), 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild())
    assert status.overall_glyph == GLYPH_HEALTHY


@pytest.mark.asyncio
async def test_overall_counts_warnings_and_advisories():
    report = _report(
        _finding("warning", "moderation"),
        _finding("warning", "cleanup"),
        _finding("advisory", "roles"),
    )
    diag_p, ready_p = _patch_detectors(report, 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild())
    assert status.overall_glyph == GLYPH_ATTENTION
    assert "2 warnings" in status.overall_summary
    assert "1 advisory" in status.overall_summary


@pytest.mark.asyncio
async def test_overall_blocked_when_blocker_present():
    report = _report(_finding("blocker", "moderation"))
    diag_p, ready_p = _patch_detectors(report, 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild())
    assert status.overall_glyph == GLYPH_BLOCKED


# ---------------------------------------------------------------------------
# Fail-safe contract — never raises, degrades to unknown
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_collect_never_raises_when_diagnostics_down():
    diag_p, ready_p = _patch_detectors(None, None)  # both detectors raise
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles", return_value=([MagicMock()], [])
    ):
        status = await collect_hub_status(_guild())
    # The composer still returns a full set of badges.
    assert {b.key for b in status.badges} == {
        hub.MOD,
        hub.CHANNELS,
        hub.ROLES,
        hub.CLEANUP,
        hub.SETUP,
    }
    assert status.overall_glyph == GLYPH_UNKNOWN
    assert _badge(status, hub.CLEANUP).glyph == GLYPH_UNKNOWN
    assert _badge(status, hub.SETUP).glyph == GLYPH_UNKNOWN


@pytest.mark.asyncio
async def test_roles_badge_unknown_when_feasibility_raises():
    diag_p, ready_p = _patch_detectors(_report(), 100)
    with diag_p, ready_p, patch(
        "utils.role_feasibility.manageable_roles",
        side_effect=RuntimeError("boom"),
    ):
        status = await collect_hub_status(_guild())
    assert _badge(status, hub.ROLES).glyph == GLYPH_UNKNOWN


@pytest.mark.asyncio
async def test_collect_handles_missing_guild_me():
    diag_p, ready_p = _patch_detectors(_report(), 100)
    with diag_p, ready_p:
        status = await collect_hub_status(_guild(me_is_none=True))
    # No guild.me → moderation degrades to unknown, channels/roles blocked,
    # and nothing raises.
    assert _badge(status, hub.MOD).glyph == GLYPH_UNKNOWN
    assert _badge(status, hub.CHANNELS).glyph == GLYPH_BLOCKED
    assert _badge(status, hub.ROLES).glyph == GLYPH_BLOCKED
