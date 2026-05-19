"""Regression canary for the Platform/Diagnostics hook split.

Pins all four invariants in one file so any future change that tries
to collapse the two hooks back into one trips a single, named test:

1. ``DiagnosticCog.build_help_menu_view(opener)`` returns
   ``_DiagnosticsHubView``.
2. ``DiagnosticCog.build_platform_help_menu_view(opener)`` returns
   ``_PlatformHubView``.
3. Help route ``platform`` opens ``_PlatformHubView``.
4. Help route ``diagnostics`` opens ``_DiagnosticsHubView``.
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


def test_help_routes_platform_to_diagnostic_hub_key():
    """Invariant #3 (resolver half): the ``platform`` alias must
    resolve to the ``diagnostic`` hub key. ``_open_route`` then uses
    the ``_HUB_PANEL_BUILDERS`` override to call the platform builder.
    """
    route = help_cog._resolve_route("platform", bot=MagicMock())
    assert route.kind == "hub"
    assert route.target == "diagnostic"
    # Override table must point at the Platform builder, not the
    # generic ``build_help_menu_view`` hook.
    assert help_cog._HUB_PANEL_BUILDERS["diagnostic"] == "build_platform_help_menu_view"


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
