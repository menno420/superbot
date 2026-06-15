"""Unit tests for the welcome orchestration (services.welcome_service)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from services import welcome_service
from services.welcome_config import WelcomePolicy


def _guild() -> MagicMock:
    g = MagicMock(spec=discord.Guild)
    g.id = 1
    g.name = "Demo"
    g.member_count = 1235
    g.get_channel.return_value = None
    g.get_role.return_value = None
    return g


def _member(guild: MagicMock | None = None) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = 200
    m.bot = False
    m.mention = "<@200>"
    m.display_name = "Astro"
    m.roles = []
    avatar = MagicMock()
    avatar.url = "https://cdn.example/avatar.png"
    m.display_avatar = avatar
    m.guild = guild if guild is not None else _guild()
    return m


def _text_channel() -> MagicMock:
    ch = MagicMock(spec=discord.TextChannel)
    ch.send = AsyncMock()
    return ch


# ---------------------------------------------------------------------------
# Embed builders
# ---------------------------------------------------------------------------


def test_join_embed_uses_mention_and_count():
    member = _member()
    policy = WelcomePolicy(join_message="Hi {user} — #{count} in {server}")
    embed = welcome_service.format_join_embed(member, policy, 1235)
    assert embed.description == "Hi <@200> — #1,235 in Demo"
    assert embed.color == discord.Color.green()


def test_leave_embed_uses_plain_name():
    member = _member()
    policy = WelcomePolicy(leave_message="{user} left {server}")
    embed = welcome_service.format_leave_embed(member, policy, 42)
    # A departed member is named, not mentioned.
    assert embed.description == "Astro left Demo"


# ---------------------------------------------------------------------------
# handle_member_join
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_join_disabled_is_noop(monkeypatch):
    member = _member()
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(return_value=WelcomePolicy(enabled=False)),
    )
    apply = AsyncMock()
    monkeypatch.setattr("services.role_automation.apply", apply)

    await welcome_service.handle_member_join(member)
    apply.assert_not_called()
    member.guild.get_channel.assert_not_called()


@pytest.mark.asyncio
async def test_join_posts_greeting_and_emits(monkeypatch):
    channel = _text_channel()
    member = _member()
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True,
                join_enabled=True,
                channel_id=100,
            ),
        ),
    )
    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    await welcome_service.handle_member_join(member)

    channel.send.assert_awaited_once()
    assert "embed" in channel.send.await_args.kwargs
    emit.assert_awaited_once()
    assert emit.await_args.args[0] == welcome_service.EVT_WELCOME_MEMBER_GREETED
    assert emit.await_args.kwargs["user_id"] == 200


@pytest.mark.asyncio
async def test_join_grants_entry_role(monkeypatch):
    role = MagicMock()
    role.id = 777
    role.name = "Member"
    member = _member()
    member.guild.get_role.return_value = role
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True, join_enabled=False, entry_role_id=777
            ),
        ),
    )
    apply = AsyncMock()
    monkeypatch.setattr("services.role_automation.apply", apply)

    await welcome_service.handle_member_join(member)

    apply.assert_awaited_once()
    # The grant goes through the audited seam as a system actor.
    assert apply.await_args.kwargs["actor_type"] == "system"
    assignment = apply.await_args.args[1][0]
    assert assignment.add_role_id == 777


@pytest.mark.asyncio
async def test_join_skips_role_already_held(monkeypatch):
    role = MagicMock()
    role.id = 777
    member = _member()
    member.roles = [role]  # already has the entry role
    member.guild.get_role.return_value = role
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(return_value=WelcomePolicy(enabled=True, entry_role_id=777)),
    )
    apply = AsyncMock()
    monkeypatch.setattr("services.role_automation.apply", apply)

    await welcome_service.handle_member_join(member)
    apply.assert_not_called()


@pytest.mark.asyncio
async def test_join_missing_channel_does_not_send(monkeypatch):
    member = _member()
    member.guild.get_channel.return_value = None  # configured id no longer resolves
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(enabled=True, join_enabled=True, channel_id=100),
        ),
    )
    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    await welcome_service.handle_member_join(member)
    emit.assert_not_called()  # no greeting posted → no greeted event


@pytest.mark.asyncio
async def test_join_load_policy_fault_fails_open(monkeypatch):
    member = _member()
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    # Must not raise.
    await welcome_service.handle_member_join(member)


@pytest.mark.asyncio
async def test_join_send_forbidden_is_swallowed(monkeypatch):
    channel = _text_channel()
    channel.send = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "no perms"))
    member = _member()
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(enabled=True, join_enabled=True, channel_id=100),
        ),
    )
    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    await welcome_service.handle_member_join(member)  # no raise
    emit.assert_not_called()  # failed post → no greeted event


# ---------------------------------------------------------------------------
# Welcome card (phase 2)
# ---------------------------------------------------------------------------


def _card_policy() -> WelcomePolicy:
    return WelcomePolicy(
        enabled=True,
        join_enabled=True,
        channel_id=100,
        card_enabled=True,
    )


@pytest.mark.asyncio
async def test_join_attaches_card_when_enabled(monkeypatch):
    channel = _text_channel()
    member = _member()
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(return_value=_card_policy()),
    )
    render = MagicMock(return_value=b"\x89PNG-bytes")
    monkeypatch.setattr("utils.welcome_render.render_welcome_card", render)

    await welcome_service.handle_member_join(member)

    channel.send.assert_awaited_once()
    kwargs = channel.send.await_args.kwargs
    assert "embed" in kwargs
    assert isinstance(kwargs.get("file"), discord.File)
    # The card is rendered from the member's display name + the live count.
    assert render.call_args.kwargs["member_name"] == "Astro"
    assert render.call_args.kwargs["member_number"] == 1235


@pytest.mark.asyncio
async def test_join_no_card_when_disabled(monkeypatch):
    channel = _text_channel()
    member = _member()
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(enabled=True, join_enabled=True, channel_id=100),
        ),
    )
    render = MagicMock(return_value=b"unused")
    monkeypatch.setattr("utils.welcome_render.render_welcome_card", render)

    await welcome_service.handle_member_join(member)

    channel.send.assert_awaited_once()
    assert "file" not in channel.send.await_args.kwargs
    render.assert_not_called()  # card disabled -> renderer never invoked


@pytest.mark.asyncio
async def test_join_card_render_none_still_posts(monkeypatch):
    """Pillow unavailable (render -> None): greeting posts without an attachment."""
    channel = _text_channel()
    member = _member()
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(return_value=_card_policy()),
    )
    monkeypatch.setattr(
        "utils.welcome_render.render_welcome_card",
        MagicMock(return_value=None),
    )
    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    await welcome_service.handle_member_join(member)

    channel.send.assert_awaited_once()
    assert "file" not in channel.send.await_args.kwargs
    emit.assert_awaited_once()  # the greeting still posted


@pytest.mark.asyncio
async def test_join_card_render_fault_still_posts(monkeypatch):
    """A render exception is swallowed: greeting posts without an attachment."""
    channel = _text_channel()
    member = _member()
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(return_value=_card_policy()),
    )
    monkeypatch.setattr(
        "utils.welcome_render.render_welcome_card",
        MagicMock(side_effect=RuntimeError("boom")),
    )

    await welcome_service.handle_member_join(member)  # no raise

    channel.send.assert_awaited_once()
    assert "file" not in channel.send.await_args.kwargs


def test_accent_for_default_role_is_none():
    member = _member()
    member.top_role = MagicMock()
    member.top_role.color = discord.Color(0)  # Discord default colour
    assert welcome_service._accent_for(member) is None


def test_accent_for_uses_top_role_colour():
    member = _member()
    member.top_role = MagicMock()
    member.top_role.color = discord.Color(0x5865F2)  # blurple
    assert welcome_service._accent_for(member) == (0x58, 0x65, 0xF2)


# ---------------------------------------------------------------------------
# handle_member_leave
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_leave_posts_farewell(monkeypatch):
    channel = _text_channel()
    member = _member()
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True,
                leave_enabled=True,
                channel_id=100,
            ),
        ),
    )
    await welcome_service.handle_member_leave(member)
    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_leave_disabled_is_noop(monkeypatch):
    channel = _text_channel()
    member = _member()
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True,
                leave_enabled=False,
                channel_id=100,
            ),
        ),
    )
    await welcome_service.handle_member_leave(member)
    channel.send.assert_not_called()
