"""Unit tests for the automod stage orchestration (cogs.automod.listener)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from cogs.automod import listener
from services.automod_config import AutomodPolicy
from services.automod_service import AutomodVerdict


def _message() -> MagicMock:
    msg = MagicMock()
    msg.id = 555
    msg.guild = MagicMock(id=1)
    msg.channel = MagicMock(id=100)
    # A real-spec Member so the isinstance(discord.Member) gate in _act passes.
    msg.author = MagicMock(spec=discord.Member)
    msg.author.id = 200
    return msg


@pytest.mark.asyncio
async def test_disabled_policy_is_a_noop(monkeypatch):
    monkeypatch.setattr(
        listener.automod_config,
        "load_policy",
        AsyncMock(return_value=AutomodPolicy(enabled=False)),
    )
    evaluate = MagicMock()
    monkeypatch.setattr(listener.automod_service, "evaluate", evaluate)

    result = await listener.process_message(MagicMock(), _message())
    assert result.deleted is False and result.short_circuit is False
    evaluate.assert_not_called()  # never even evaluated when disabled


@pytest.mark.asyncio
async def test_no_verdict_does_not_act(monkeypatch):
    monkeypatch.setattr(
        listener.automod_config,
        "load_policy",
        AsyncMock(return_value=AutomodPolicy(enabled=True, invites_enabled=True)),
    )
    monkeypatch.setattr(
        listener.automod_service, "evaluate", MagicMock(return_value=None)
    )
    auto_delete = AsyncMock()
    monkeypatch.setattr(listener.moderation_service, "auto_delete", auto_delete)

    result = await listener.process_message(MagicMock(), _message())
    assert result.deleted is False
    auto_delete.assert_not_called()


@pytest.mark.asyncio
async def test_verdict_deletes_warns_and_emits(monkeypatch):
    verdict = AutomodVerdict(rule="automod.invite_link", reason="invite")
    monkeypatch.setattr(
        listener.automod_config,
        "load_policy",
        AsyncMock(return_value=AutomodPolicy(enabled=True, invites_enabled=True)),
    )
    monkeypatch.setattr(
        listener.automod_service, "evaluate", MagicMock(return_value=verdict)
    )
    auto_delete = AsyncMock()
    warn = AsyncMock()
    monkeypatch.setattr(listener.moderation_service, "auto_delete", auto_delete)
    monkeypatch.setattr(listener.moderation_service, "warn", warn)

    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    msg = _message()
    result = await listener.process_message(MagicMock(), msg)

    assert result.deleted is True and result.short_circuit is True
    auto_delete.assert_awaited_once()
    assert auto_delete.await_args.kwargs["rule"] == "automod.invite_link"
    warn.assert_awaited_once()
    assert warn.await_args.kwargs["actor_id"] is None
    emit.assert_awaited_once()
    assert emit.await_args.args[0] == listener.EVT_AUTOMOD_RULE_TRIGGERED
    assert emit.await_args.kwargs["rule"] == "automod.invite_link"


@pytest.mark.asyncio
async def test_load_policy_fault_fails_open(monkeypatch):
    monkeypatch.setattr(
        listener.automod_config,
        "load_policy",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    result = await listener.process_message(MagicMock(), _message())
    assert result.deleted is False and result.short_circuit is False


@pytest.mark.asyncio
async def test_dm_message_is_a_noop():
    msg = MagicMock()
    msg.guild = None
    result = await listener.process_message(MagicMock(), msg)
    assert result.deleted is False
