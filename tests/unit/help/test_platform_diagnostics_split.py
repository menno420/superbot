"""Regression canary for the Platform/Diagnostics hook split.

The DiagnosticCog keeps BOTH hooks so both surfaces survive the help-menu
regrouping (PR #1290), which made Diagnostics an ``admin`` child rather than a
top-level hub:

1. ``DiagnosticCog.build_help_menu_view(opener)`` returns
   ``_DiagnosticsHubView`` (reached via ``!help diagnostic[s]`` and the
   Server & Admin panel's Diagnostics button).
2. ``DiagnosticCog.build_platform_help_menu_view(opener)`` returns
   ``_PlatformHubView`` (reached via the Server & Admin panel's Platform
   button).
3. Help route ``platform`` resolves to the consolidated ``admin`` hub.
4. Help route ``diagnostics`` opens the Diagnostics subsystem panel.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cogs import help_cog
from cogs.diagnostic_cog import DiagnosticCog
from views.diagnostic import _DiagnosticsHubView, _PlatformHubView


def _interaction() -> MagicMock:
    interaction = MagicMock()
    user = MagicMock()
    user.id = 1
    interaction.user = user
    interaction.guild = None
    interaction.guild_id = None
    interaction.client = MagicMock()
    interaction.channel = MagicMock()
    return interaction


def _opener() -> help_cog.HelpOpener:
    user = MagicMock()
    user.id = 1
    return help_cog.HelpOpener(
        user=user,
        guild=None,
        guild_id=None,
        client=MagicMock(),
        channel=MagicMock(),
    )


@pytest.mark.asyncio
async def test_build_help_menu_view_returns_diagnostics_hub():
    """Invariant #1: the generic hook stays pointed at Diagnostics so
    Admin → Diagnostics keeps working.
    """
    cog = DiagnosticCog(bot=MagicMock())
    interaction = _interaction()
    _embed, view = await cog.build_help_menu_view(interaction)
    assert isinstance(view, _DiagnosticsHubView)


@pytest.mark.asyncio
async def test_build_platform_help_menu_view_returns_platform_hub():
    """Invariant #2: the new sibling hook returns the Platform Hub."""
    cog = DiagnosticCog(bot=MagicMock())
    interaction = _interaction()
    _embed, view = await cog.build_platform_help_menu_view(interaction)
    assert isinstance(view, _PlatformHubView)


def test_help_routes_platform_to_server_admin_hub():
    """Invariant #3 (resolver half): after the help-menu regrouping (PR #1290)
    the ``platform`` alias resolves to the consolidated ``admin`` hub, where the
    Platform view lives (reached via the Server & Admin panel's Platform
    button). The Platform builder itself still exists on the cog (invariant #2),
    so the surface is intact — it is just no longer its own top-level hub.
    """
    route = help_cog._resolve_route("platform", bot=MagicMock())
    assert route.kind == "hub"
    assert route.target == "admin"
    # The legacy override is gone: Diagnostics/Platform is no longer a hub.
    assert "diagnostic" not in help_cog._HUB_PANEL_BUILDERS


def test_help_routes_diagnostics_to_diagnostic_subsystem():
    """Invariant #4 (resolver half): the ``diagnostics`` alias must
    resolve to the ``diagnostic`` subsystem so it opens via
    ``build_help_menu_view`` (Diagnostics Hub), not the Platform Hub
    builder.
    """
    route = help_cog._resolve_route("diagnostics", bot=MagicMock())
    assert route.kind == "subsystem"
    assert route.target == "diagnostic"


def test_help_routes_diag_short_alias_to_diagnostic_subsystem():
    """The short ``diag`` alias mirrors the ``diagnostics`` route."""
    route = help_cog._resolve_route("diag", bot=MagicMock())
    assert route.kind == "subsystem"
    assert route.target == "diagnostic"
