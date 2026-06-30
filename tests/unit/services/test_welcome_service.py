"""Unit tests for the welcome orchestration (services.welcome_service)."""

from __future__ import annotations

import datetime as dt
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


def test_join_embed_picks_a_random_variant():
    import random

    member = _member()
    policy = WelcomePolicy(
        join_message="Hi {user}\n---\nWelcome {user}\n---\nHey {user}"
    )
    # Every render is one of the variants, placeholders expanded…
    rendered = {
        welcome_service.format_join_embed(
            member, policy, 1, rng=random.Random(s)
        ).description
        for s in range(20)
    }
    assert rendered <= {"Hi <@200>", "Welcome <@200>", "Hey <@200>"}
    # …and it genuinely varies across seeds.
    assert len(rendered) > 1


def test_leave_embed_picks_a_random_variant():
    import random

    member = _member()
    policy = WelcomePolicy(leave_message="Bye {user}\n---\nFarewell {user}")
    rendered = {
        welcome_service.format_leave_embed(
            member, policy, 1, rng=random.Random(s)
        ).description
        for s in range(20)
    }
    assert rendered <= {"Bye Astro", "Farewell Astro"}
    assert len(rendered) > 1


def test_dm_embed_renders_dm_message_with_mention():
    member = _member()
    policy = WelcomePolicy(dm_message="Welcome {user} to {server} (#{count})")
    embed = welcome_service.format_dm_embed(member, policy, 7)
    assert embed.description == "Welcome <@200> to Demo (#7)"
    assert embed.color == discord.Color.green()


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
async def test_join_sends_dm_greeting(monkeypatch):
    member = _member()
    member.send = AsyncMock()
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True,
                join_enabled=False,  # no channel greeting
                dm_enabled=True,
                dm_message="Hey {user}!",
            ),
        ),
    )

    await welcome_service.handle_member_join(member)

    member.send.assert_awaited_once()
    embed = member.send.await_args.kwargs["embed"]
    assert embed.description == "Hey <@200>!"
    # No channel was configured → no channel post attempted.
    member.guild.get_channel.assert_not_called()


@pytest.mark.asyncio
async def test_join_dm_closed_is_swallowed(monkeypatch):
    member = _member()
    member.send = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "closed"))
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True, join_enabled=False, dm_enabled=True
            ),
        ),
    )

    # A member with DMs closed must not raise — the join dispatch completes.
    await welcome_service.handle_member_join(member)
    member.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_join_channel_greeting_and_dm_are_independent(monkeypatch):
    channel = _text_channel()
    member = _member()
    member.send = AsyncMock()
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True,
                join_enabled=True,
                channel_id=100,
                dm_enabled=True,
            ),
        ),
    )
    import core.events

    monkeypatch.setattr(core.events.bus, "emit", AsyncMock())

    await welcome_service.handle_member_join(member)

    # Both the channel greeting and the DM fire.
    channel.send.assert_awaited_once()
    member.send.assert_awaited_once()


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
# Welcome phase 2 — the greeting card
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_join_attaches_card_when_enabled(monkeypatch):
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
                card_enabled=True,
            ),
        ),
    )
    sentinel_file = MagicMock(spec=discord.File)
    monkeypatch.setattr(
        welcome_service,
        "render_join_card",
        MagicMock(return_value=sentinel_file),
    )
    import core.events

    monkeypatch.setattr(core.events.bus, "emit", AsyncMock())

    await welcome_service.handle_member_join(member)

    channel.send.assert_awaited_once()
    kwargs = channel.send.await_args.kwargs
    assert kwargs["file"] is sentinel_file
    # The embed points its in-place image at the attachment.
    assert kwargs["embed"].image.url == "attachment://welcome.jpg"


@pytest.mark.asyncio
async def test_join_card_disabled_sends_embed_only(monkeypatch):
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
                card_enabled=False,
            ),
        ),
    )
    render = MagicMock()
    monkeypatch.setattr(welcome_service, "render_join_card", render)
    import core.events

    monkeypatch.setattr(core.events.bus, "emit", AsyncMock())

    await welcome_service.handle_member_join(member)

    render.assert_not_called()  # not rendered when the toggle is off
    assert "file" not in channel.send.await_args.kwargs


@pytest.mark.asyncio
async def test_join_card_unavailable_falls_back_to_embed(monkeypatch):
    """Pillow absent (renderer → None) ⇒ embed-only greeting, still posted."""
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
                card_enabled=True,
            ),
        ),
    )
    monkeypatch.setattr(
        welcome_service,
        "render_join_card",
        MagicMock(return_value=None),
    )
    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    await welcome_service.handle_member_join(member)

    channel.send.assert_awaited_once()
    assert "file" not in channel.send.await_args.kwargs
    # No image set on the embed when the card could not render.
    assert not channel.send.await_args.kwargs["embed"].image.url
    emit.assert_awaited_once()  # greeting still posted


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


# ---------------------------------------------------------------------------
# Join-delay age-gating (anti-raid)
# ---------------------------------------------------------------------------


def _aged_member(days_old: float, guild: MagicMock | None = None) -> MagicMock:
    """A member whose account was created ``days_old`` days ago (tz-aware UTC)."""
    member = _member(guild)
    member.created_at = discord.utils.utcnow() - dt.timedelta(days=days_old)
    return member


@pytest.mark.asyncio
async def test_join_too_young_account_is_skipped_entirely(monkeypatch):
    """A below-threshold account gets no greeting, no DM, and no entry role."""
    channel = _text_channel()
    member = _aged_member(days_old=1)  # 1 day old, gate is 7 days
    member.send = AsyncMock()
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True,
                join_enabled=True,
                dm_enabled=True,
                channel_id=100,
                entry_role_id=500,
                min_account_age_days=7,
            ),
        ),
    )
    apply = AsyncMock()
    monkeypatch.setattr("services.role_automation.apply", apply)

    await welcome_service.handle_member_join(member)

    channel.send.assert_not_called()
    member.send.assert_not_called()
    apply.assert_not_called()


@pytest.mark.asyncio
async def test_join_old_enough_account_is_greeted(monkeypatch):
    """An account at/above the threshold is greeted normally."""
    channel = _text_channel()
    member = _aged_member(days_old=30)  # 30 days old, gate is 7
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True,
                join_enabled=True,
                channel_id=100,
                min_account_age_days=7,
            ),
        ),
    )
    await welcome_service.handle_member_join(member)
    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_join_gate_off_does_not_consult_account_age(monkeypatch):
    """With the gate at 0 a brand-new account is still greeted (default behaviour)."""
    channel = _text_channel()
    member = _aged_member(days_old=0)  # created seconds ago
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True,
                join_enabled=True,
                channel_id=100,
                min_account_age_days=0,
            ),
        ),
    )
    await welcome_service.handle_member_join(member)
    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_join_unknown_account_age_fails_open(monkeypatch):
    """A missing created_at (unknown age) greets rather than silently dropping."""
    channel = _text_channel()
    member = _member()
    member.created_at = None
    member.guild.get_channel.return_value = channel
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True,
                join_enabled=True,
                channel_id=100,
                min_account_age_days=7,
            ),
        ),
    )
    await welcome_service.handle_member_join(member)
    channel.send.assert_awaited_once()


# ---------------------------------------------------------------------------
# Ping-then-delete (auto-delete the channel greeting/farewell)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_join_greeting_passes_delete_after(monkeypatch):
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
                delete_after_seconds=30,
            ),
        ),
    )
    await welcome_service.handle_member_join(member)
    channel.send.assert_awaited_once()
    assert channel.send.await_args.kwargs["delete_after"] == 30.0


@pytest.mark.asyncio
async def test_join_greeting_delete_after_off_is_none(monkeypatch):
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
    await welcome_service.handle_member_join(member)
    assert channel.send.await_args.kwargs["delete_after"] is None


@pytest.mark.asyncio
async def test_leave_farewell_passes_delete_after(monkeypatch):
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
                delete_after_seconds=45,
            ),
        ),
    )
    await welcome_service.handle_member_leave(member)
    assert channel.send.await_args.kwargs["delete_after"] == 45.0


@pytest.mark.asyncio
async def test_dm_greeting_is_never_deleted(monkeypatch):
    """delete_after applies to the channel post, never to the DM send."""
    member = _member()
    member.send = AsyncMock()
    monkeypatch.setattr(
        welcome_service.welcome_config,
        "load_policy",
        AsyncMock(
            return_value=WelcomePolicy(
                enabled=True,
                dm_enabled=True,
                delete_after_seconds=30,
            ),
        ),
    )
    await welcome_service.handle_member_join(member)
    member.send.assert_awaited_once()
    assert "delete_after" not in member.send.await_args.kwargs
