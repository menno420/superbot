"""Phase 9e / Track 4 PR 9 — ``cogs.setup_cog`` tests.

Pins:

* ``pick_launcher_channel`` walks the documented preference order:
  system → admin/mod/staff → bot → first sendable → None.
* ``post_launcher`` falls back to DMing the owner when no channel
  is sendable.
* ``on_guild_join`` upserts the session row via
  :mod:`services.setup_session` regardless of where the launcher
  ended up.
* Button gating refuses non-owner / non-admin members appropriately.
* The Dismiss button calls ``setup_session.dismiss`` and posts an
  ephemeral confirmation.
* Coming-soon buttons send an ephemeral message and do not touch
  any pipeline.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.setup_cog import (
    SetupLauncherView,
    pick_launcher_channel,
    post_launcher,
)
from services.setup_session import SetupSession

# ---------------------------------------------------------------------------
# Channel selection
# ---------------------------------------------------------------------------


def _perms(*, view=True, send=True, embed=True):
    return SimpleNamespace(
        view_channel=view,
        send_messages=send,
        embed_links=embed,
    )


def _channel(name: str, perms, type_=None):
    import discord

    if type_ is None:
        type_ = discord.TextChannel
    ch = MagicMock(spec=type_)
    ch.name = name
    ch.id = hash(name) & 0xFFFFFF
    ch.permissions_for = MagicMock(return_value=perms)
    return ch


def _guild(
    *,
    system: object | None = None,
    text_channels=(),
    me=None,
    owner=None,
    guild_id: int = 1,
    name: str = "Test",
    owner_id: int = 99,
):
    import discord

    g = MagicMock(spec=discord.Guild)
    g.id = guild_id
    g.name = name
    g.owner_id = owner_id
    g.system_channel = system
    g.text_channels = list(text_channels)
    g.me = me
    g.owner = owner
    return g


def test_pick_launcher_returns_system_channel_when_sendable():
    me = MagicMock()
    system = _channel("general", _perms())
    other = _channel("random", _perms())
    g = _guild(system=system, text_channels=[system, other], me=me)
    assert pick_launcher_channel(g) is system


def test_pick_launcher_skips_system_when_not_sendable():
    me = MagicMock()
    system = _channel("general", _perms(send=False))
    admin = _channel("admin-chat", _perms())
    g = _guild(system=system, text_channels=[system, admin], me=me)
    assert pick_launcher_channel(g) is admin


def test_pick_launcher_prefers_admin_over_bot_keyword():
    me = MagicMock()
    bot_ch = _channel("bot-spam", _perms())
    mod_ch = _channel("mod-log", _perms())
    g = _guild(text_channels=[bot_ch, mod_ch], me=me)
    assert pick_launcher_channel(g) is mod_ch


def test_pick_launcher_falls_back_to_bot_keyword_then_first_sendable():
    me = MagicMock()
    bot_ch = _channel("bot-spam", _perms())
    random_ch = _channel("random", _perms())
    g = _guild(text_channels=[random_ch, bot_ch], me=me)
    assert pick_launcher_channel(g) is bot_ch


def test_pick_launcher_returns_first_sendable_when_no_keyword_match():
    me = MagicMock()
    random1 = _channel("random", _perms())
    random2 = _channel("chatter", _perms())
    g = _guild(text_channels=[random1, random2], me=me)
    assert pick_launcher_channel(g) is random1


def test_pick_launcher_returns_none_when_no_sendable_channels():
    me = MagicMock()
    silent = _channel("locked", _perms(send=False))
    g = _guild(text_channels=[silent], me=me)
    assert pick_launcher_channel(g) is None


def test_pick_launcher_returns_none_when_bot_member_missing():
    g = _guild(me=None, text_channels=[_channel("general", _perms())])
    assert pick_launcher_channel(g) is None


# ---------------------------------------------------------------------------
# post_launcher
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_launcher_sends_to_picked_channel():
    me = MagicMock()
    sendable = _channel("general", _perms())
    sendable.send = AsyncMock(return_value=MagicMock(id=12345))
    g = _guild(system=sendable, text_channels=[sendable], me=me)

    channel, message = await post_launcher(g)
    assert channel is sendable
    assert message.id == 12345
    sendable.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_launcher_falls_back_to_owner_dm_when_no_channel():
    g = _guild(text_channels=[], me=MagicMock())
    g.owner = MagicMock()
    g.owner.id = 99
    g.owner.send = AsyncMock(return_value=MagicMock(id=99001))

    channel, message = await post_launcher(g)
    assert channel is None
    assert message.id == 99001
    g.owner.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_launcher_returns_none_pair_when_dm_also_fails():
    import discord

    g = _guild(text_channels=[], me=MagicMock())
    g.owner = MagicMock()
    g.owner.id = 99
    g.owner.send = AsyncMock(
        side_effect=discord.Forbidden(MagicMock(), "dms closed"),
    )

    channel, message = await post_launcher(g)
    assert channel is None
    assert message is None


@pytest.mark.asyncio
async def test_post_launcher_falls_back_to_dm_on_forbidden_in_channel():
    import discord

    me = MagicMock()
    ch = _channel("general", _perms())
    ch.send = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "no perm"))
    g = _guild(system=ch, text_channels=[ch], me=me)
    g.owner = MagicMock()
    g.owner.id = 99
    g.owner.send = AsyncMock(return_value=MagicMock(id=42))

    channel, message = await post_launcher(g)
    assert channel is None
    assert message.id == 42


# ---------------------------------------------------------------------------
# on_guild_join → setup_session.start_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_guild_join_calls_start_session_with_channel_ids():
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    me = MagicMock()
    ch = _channel("general", _perms())
    ch.id = 5555
    ch.send = AsyncMock(return_value=MagicMock(id=8888))
    g = _guild(
        system=ch,
        text_channels=[ch],
        me=me,
        owner_id=99,
        guild_id=42,
        name="My Server",
    )

    with patch(
        "cogs.setup_cog.setup_session.start_session",
        new_callable=AsyncMock,
    ) as start_mock:
        await cog._handle_join(g)

    start_mock.assert_awaited_once()
    kwargs = start_mock.await_args.kwargs
    assert kwargs["guild_id"] == 42
    assert kwargs["guild_name"] == "My Server"
    assert kwargs["owner_id"] == 99
    assert kwargs["setup_channel_id"] == 5555
    assert kwargs["setup_message_id"] == 8888


@pytest.mark.asyncio
async def test_on_guild_join_records_none_ids_when_dm_succeeds():
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    g = _guild(text_channels=[], me=MagicMock())
    g.owner = MagicMock()
    g.owner.send = AsyncMock(return_value=MagicMock(id=99001))

    with patch(
        "cogs.setup_cog.setup_session.start_session",
        new_callable=AsyncMock,
    ) as start_mock:
        await cog._handle_join(g)

    kwargs = start_mock.await_args.kwargs
    assert kwargs["setup_channel_id"] is None
    # DM message id still captured.
    assert kwargs["setup_message_id"] == 99001


@pytest.mark.asyncio
async def test_on_guild_join_swallows_handler_failure():
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    g = MagicMock()
    g.id = 1
    g.name = "x"

    with patch(
        "cogs.setup_cog.post_launcher",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    ):
        # Must not raise.
        await cog._handle_join(g)


# ---------------------------------------------------------------------------
# Button gating
# ---------------------------------------------------------------------------


def _owner_member(guild_owner_id: int = 99):
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = guild_owner_id
    m.guild = SimpleNamespace(owner_id=guild_owner_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _admin_member(guild_owner_id: int = 99, user_id: int = 42):
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=guild_owner_id)
    m.guild_permissions = SimpleNamespace(administrator=True)
    return m


def _random_member(guild_owner_id: int = 99, user_id: int = 42):
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=guild_owner_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _mock_interaction(user, guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = user
    interaction.guild_id = guild_id
    interaction.guild = MagicMock(id=guild_id)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_start_button_refuses_non_owner():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    await view._start.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert (
        "server owner"
        in interaction.response.send_message.await_args.args[0].lower()
    )


@pytest.mark.asyncio
async def test_start_button_shows_coming_soon_for_owner():
    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())

    await view._start.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "not wired up" in msg.lower()


@pytest.mark.asyncio
async def test_smart_suggestions_button_owner_only():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    await view._suggestions.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert (
        "server owner"
        in interaction.response.send_message.await_args.args[0].lower()
    )


@pytest.mark.asyncio
async def test_preset_button_owner_only():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    await view._preset.callback(interaction)

    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_readiness_button_admin_allowed():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    fake_embed = MagicMock()
    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.diagnostic._platform_embeds.build_setup_readiness_embed",
            new_callable=AsyncMock,
            return_value=fake_embed,
        ) as build_mock,
    ):
        await view._readiness.callback(interaction)

    build_mock.assert_awaited_once()
    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.await_args.kwargs["embed"] is fake_embed


@pytest.mark.asyncio
async def test_readiness_button_random_denied():
    view = SetupLauncherView()
    random = _random_member()
    interaction = _mock_interaction(random)
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="pending",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
    )

    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=session,
    ):
        await view._readiness.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "admin" in msg.lower() or "owner" in msg.lower()


@pytest.mark.asyncio
async def test_dismiss_button_owner_calls_dismiss():
    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())

    with patch(
        "cogs.setup_cog.setup_session.dismiss",
        new_callable=AsyncMock,
    ) as dismiss_mock:
        await view._dismiss.callback(interaction)

    dismiss_mock.assert_awaited_once_with(interaction.guild_id)
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_dismiss_button_refuses_non_owner():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    with patch(
        "cogs.setup_cog.setup_session.dismiss",
        new_callable=AsyncMock,
    ) as dismiss_mock:
        await view._dismiss.callback(interaction)

    dismiss_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
