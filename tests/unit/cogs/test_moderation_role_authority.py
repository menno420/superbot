"""Authority tests for the moderation surfaces' OR-gate (ADR-008).

The moderation cog's prefix commands and the moderation panel admit a member on
``Discord permission`` **OR** the governance moderation capability (the latter is
how a configured moderator role grants access).  These tests pin:

* the permission path still admits (no regression);
* the capability path admits a permission-less member (the role grant);
* neither path → denial, raised as ``MissingPermissions`` so the existing
  ``on_command_error`` UX (a visible "no permission" message) is preserved.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from discord.ext import commands


def _ctx(*, guild=object(), **perm_kwargs):
    """A fake prefix Context whose author has the given guild_permissions."""
    return SimpleNamespace(
        guild=guild,
        author=SimpleNamespace(
            id=1,
            guild_permissions=SimpleNamespace(**perm_kwargs),
        ),
    )


def _predicate(capability: str, perm_attr: str):
    """The predicate inside the _require_mod check decorator."""
    from cogs.moderation_cog import _require_mod

    return _require_mod(capability, perm_attr).predicate


# ---------------------------------------------------------------------------
# Prefix command OR-gate (_require_mod)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_permission_path_admits(monkeypatch):
    import cogs.moderation_cog as cog_mod

    # can_execute_ctx must NOT even be consulted when the perm is present.
    spy = AsyncMock(return_value=False)
    monkeypatch.setattr(cog_mod, "can_execute_ctx", spy)

    predicate = _predicate("moderation.ban.apply", "ban_members")
    assert await predicate(_ctx(ban_members=True)) is True
    spy.assert_not_awaited()


@pytest.mark.asyncio
async def test_capability_path_admits_without_permission(monkeypatch):
    import cogs.moderation_cog as cog_mod

    monkeypatch.setattr(cog_mod, "can_execute_ctx", AsyncMock(return_value=True))

    predicate = _predicate("moderation.ban.apply", "ban_members")
    # No ban_members permission, but the capability (role grant) allows it.
    assert await predicate(_ctx(ban_members=False)) is True


@pytest.mark.asyncio
async def test_neither_path_raises_missing_permissions(monkeypatch):
    import cogs.moderation_cog as cog_mod

    monkeypatch.setattr(cog_mod, "can_execute_ctx", AsyncMock(return_value=False))

    predicate = _predicate("moderation.ban.apply", "ban_members")
    with pytest.raises(commands.MissingPermissions):
        await predicate(_ctx(ban_members=False))


@pytest.mark.asyncio
async def test_outside_guild_raises_no_private_message(monkeypatch):
    import cogs.moderation_cog as cog_mod

    monkeypatch.setattr(cog_mod, "can_execute_ctx", AsyncMock(return_value=True))

    predicate = _predicate("moderation.ban.apply", "ban_members")
    with pytest.raises(commands.NoPrivateMessage):
        await predicate(_ctx(guild=None, ban_members=True))


# ---------------------------------------------------------------------------
# Panel interaction_check OR-gate
# ---------------------------------------------------------------------------


def _interaction(*, moderate_members: bool):
    return SimpleNamespace(
        user=SimpleNamespace(
            id=1,
            guild_permissions=SimpleNamespace(moderate_members=moderate_members),
        ),
        response=SimpleNamespace(send_message=AsyncMock()),
    )


@pytest.mark.asyncio
async def test_panel_admits_moderate_members_permission(monkeypatch):
    from views.moderation import main_panel

    spy = AsyncMock(return_value=False)
    monkeypatch.setattr(main_panel, "can_execute", spy)

    view = main_panel.ModPanelView()
    interaction = _interaction(moderate_members=True)
    assert await view.interaction_check(interaction) is True
    spy.assert_not_awaited()  # perm path short-circuits
    interaction.response.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_panel_admits_via_capability(monkeypatch):
    from views.moderation import main_panel

    monkeypatch.setattr(main_panel, "can_execute", AsyncMock(return_value=True))

    view = main_panel.ModPanelView()
    interaction = _interaction(moderate_members=False)
    assert await view.interaction_check(interaction) is True
    interaction.response.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_panel_denies_without_permission_or_capability(monkeypatch):
    from views.moderation import main_panel

    monkeypatch.setattr(main_panel, "can_execute", AsyncMock(return_value=False))

    view = main_panel.ModPanelView()
    interaction = _interaction(moderate_members=False)
    assert await view.interaction_check(interaction) is False
    interaction.response.send_message.assert_awaited_once()
