"""Unit tests for the counter orchestration (services.counter_service)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from services import counter_service
from services.counter_config import CounterPolicy


def _guild(*, member_count: int = 1235, members: list | None = None) -> MagicMock:
    g = MagicMock(spec=discord.Guild)
    g.id = 1
    g.member_count = member_count
    g.members = members if members is not None else []
    g.get_channel.return_value = None
    return g


def _channel(name: str = "old-name") -> MagicMock:
    ch = MagicMock(spec=discord.TextChannel)
    ch.name = name
    ch.edit = AsyncMock()
    return ch


# ---------------------------------------------------------------------------
# compute_counts
# ---------------------------------------------------------------------------


def test_compute_counts_splits_humans_and_bots():
    members = [
        MagicMock(bot=False),
        MagicMock(bot=False),
        MagicMock(bot=True),
    ]
    guild = _guild(member_count=10, members=members)
    counts = counter_service.compute_counts(guild)
    assert counts.total == 10
    assert counts.bots == 1
    assert counts.humans == 9  # total - bots
    assert counts.for_kind("total") == 10
    assert counts.for_kind("bots") == 1
    assert counts.for_kind("unknown") == 0


# ---------------------------------------------------------------------------
# sync_guild
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_disabled_is_noop(monkeypatch):
    guild = _guild()
    monkeypatch.setattr(
        counter_service.counter_config,
        "load_policy",
        AsyncMock(return_value=CounterPolicy(enabled=False, total_channel_id=100)),
    )
    renamed = await counter_service.sync_guild(guild)
    assert renamed == 0
    guild.get_channel.assert_not_called()


@pytest.mark.asyncio
async def test_sync_renames_changed_channel_and_emits(monkeypatch):
    channel = _channel(name="old")
    guild = _guild(member_count=1235)
    guild.get_channel.return_value = channel
    monkeypatch.setattr(
        counter_service.counter_config,
        "load_policy",
        AsyncMock(
            return_value=CounterPolicy(
                enabled=True,
                total_channel_id=100,
                total_template="👥 Members: {count}",
            ),
        ),
    )
    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    renamed = await counter_service.sync_guild(guild)
    assert renamed == 1
    channel.edit.assert_awaited_once()
    assert channel.edit.await_args.kwargs["name"] == "👥 Members: 1,235"
    emit.assert_awaited_once()
    assert emit.await_args.args[0] == counter_service.EVT_COUNTERS_UPDATED
    assert emit.await_args.kwargs["renamed"] == 1


@pytest.mark.asyncio
async def test_sync_skips_unchanged_name(monkeypatch):
    # Channel already has the desired name → change-detection skips the edit
    # (this is what keeps the loop under Discord's rename rate limit).
    channel = _channel(name="👥 Members: 1,235")
    guild = _guild(member_count=1235)
    guild.get_channel.return_value = channel
    monkeypatch.setattr(
        counter_service.counter_config,
        "load_policy",
        AsyncMock(
            return_value=CounterPolicy(
                enabled=True,
                total_channel_id=100,
                total_template="👥 Members: {count}",
            ),
        ),
    )
    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    renamed = await counter_service.sync_guild(guild)
    assert renamed == 0
    channel.edit.assert_not_called()
    emit.assert_not_called()


@pytest.mark.asyncio
async def test_sync_forbidden_is_swallowed(monkeypatch):
    channel = _channel(name="old")
    channel.edit = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "no perms"))
    guild = _guild()
    guild.get_channel.return_value = channel
    monkeypatch.setattr(
        counter_service.counter_config,
        "load_policy",
        AsyncMock(return_value=CounterPolicy(enabled=True, total_channel_id=100)),
    )
    renamed = await counter_service.sync_guild(guild)  # no raise
    assert renamed == 0


@pytest.mark.asyncio
async def test_sync_load_policy_fault_fails_open(monkeypatch):
    guild = _guild()
    monkeypatch.setattr(
        counter_service.counter_config,
        "load_policy",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    renamed = await counter_service.sync_guild(guild)  # no raise
    assert renamed == 0
