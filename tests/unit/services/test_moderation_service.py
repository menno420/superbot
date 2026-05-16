"""Tests for services.moderation_service (P3 PR-15)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.events_catalogue import KNOWN_EVENTS
from services import moderation_service
from services.moderation_service import EVT_MOD_ACTION


def test_event_is_catalogued():
    assert EVT_MOD_ACTION in KNOWN_EVENTS


def _make_member(member_id: int = 12345, guild_id: int = 99999) -> MagicMock:
    member = MagicMock()
    member.id = member_id
    member.guild = MagicMock()
    member.guild.id = guild_id
    member.ban = AsyncMock()
    member.kick = AsyncMock()
    member.timeout = AsyncMock()
    return member


def _make_guild(guild_id: int = 99999) -> MagicMock:
    guild = MagicMock()
    guild.id = guild_id
    guild.ban = AsyncMock()
    guild.unban = AsyncMock()
    return guild


def _make_user(user_id: int = 54321) -> MagicMock:
    u = MagicMock()
    u.id = user_id
    return u


@pytest.mark.asyncio
async def test_warn_increments_count_and_emits_event():
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=3,
        ),
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        new_count = await moderation_service.warn(
            member, reason="spam", actor_id=42,
        )

    assert new_count == 3
    log_mod.assert_awaited_once_with(
        member.guild.id, "warn", member.id, 42, "spam",
    )
    emit.assert_awaited_once()
    assert emit.await_args.args[0] == EVT_MOD_ACTION
    assert emit.await_args.kwargs["action"] == "warn"
    assert emit.await_args.kwargs["actor_id"] == 42


@pytest.mark.asyncio
async def test_timeout_calls_discord_api_and_emits_event():
    member = _make_member()
    until = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.timeout(
            member, until=until, reason="cooldown",
        )

    member.timeout.assert_awaited_once_with(until, reason="cooldown")
    emit.assert_awaited_once()
    assert emit.await_args.kwargs["action"] == "timeout"
    assert emit.await_args.kwargs["until"] == until.isoformat()


@pytest.mark.asyncio
async def test_kick_calls_discord_api_and_logs():
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.kick(member, reason="rule break")

    member.kick.assert_awaited_once_with(reason="rule break")
    log_mod.assert_awaited_once()
    assert emit.await_args.kwargs["action"] == "kick"


@pytest.mark.asyncio
async def test_ban_accepts_user_or_member():
    guild = _make_guild()
    user = _make_user()
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.ban(guild, user, reason="evade", actor_id=42)

    guild.ban.assert_awaited_once_with(user, reason="evade")
    assert emit.await_args.kwargs["action"] == "ban"
    assert emit.await_args.kwargs["target_id"] == user.id


@pytest.mark.asyncio
async def test_unban_calls_discord_api_and_logs():
    guild = _make_guild()
    user = _make_user()
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.unban(guild, user, reason="appeal accepted")

    guild.unban.assert_awaited_once_with(user, reason="appeal accepted")
    assert emit.await_args.kwargs["action"] == "unban"


@pytest.mark.asyncio
async def test_clear_warnings_deletes_and_logs():
    with (
        patch(
            "services.moderation_service.db.clear_warnings",
            new_callable=AsyncMock,
        ) as clear,
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.clear_warnings(
            guild_id=1, user_id=2, actor_id=42,
        )

    clear.assert_awaited_once_with(2, 1)
    assert emit.await_args.kwargs["action"] == "clear_warnings"


@pytest.mark.asyncio
async def test_discord_forbidden_propagates_unmodified():
    """If Discord refuses the action, the service must NOT silently swallow."""
    import discord

    member = _make_member()
    member.kick = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "nope"))

    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        with pytest.raises(discord.Forbidden):
            await moderation_service.kick(member, reason="x")

    log_mod.assert_not_awaited()
    emit.assert_not_awaited()
