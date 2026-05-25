"""PR-F tests for the strategy submission modal."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from services import btd6_strategy_mutation
from views.btd6.strategy_submit import StrategySubmitModal


def _set_inputs(modal, **fields):
    """Set ``TextInput._value`` so .value reads back our test data."""
    for k, v in fields.items():
        getattr(modal, f"{k}_input")._value = v


def _interaction(guild_id: int = 100):
    interaction = MagicMock()
    interaction.guild = SimpleNamespace(id=guild_id) if guild_id else None
    interaction.user = SimpleNamespace(id=555, display_name="alice", name="alice")
    interaction.response.send_message = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_submit_calls_chokepoint(monkeypatch):
    captured = {}

    async def _submit(**kwargs):
        captured.update(kwargs)
        return MagicMock(strategy_id=42, action="submitted")

    monkeypatch.setattr(btd6_strategy_mutation, "submit_strategy", _submit)

    modal = StrategySubmitModal()
    _set_inputs(
        modal,
        title="Bloody CHIMPS",
        summary="Works in 30 minutes",
        map="Bloody Puddles",
        mode="CHIMPS",
        hero="Geraldo",
    )
    interaction = _interaction()
    await modal.on_submit(interaction)

    assert captured["origin_guild_id"] == 100
    assert captured["title"] == "Bloody CHIMPS"
    assert captured["summary"] == "Works in 30 minutes"
    assert captured["map_name"] == "Bloody Puddles"
    assert captured["mode"] == "CHIMPS"
    assert captured["hero"] == "Geraldo"
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "#42" in msg


@pytest.mark.asyncio
async def test_submit_requires_guild_context():
    modal = StrategySubmitModal()
    _set_inputs(modal, title="x", summary="y", map="", mode="", hero="")
    interaction = _interaction(guild_id=0)
    interaction.guild = None
    await modal.on_submit(interaction)
    msg = interaction.response.send_message.await_args.args[0]
    assert "guild context" in msg


@pytest.mark.asyncio
async def test_submit_surfaces_validation_error(monkeypatch):
    async def _submit(**_kw):
        raise btd6_strategy_mutation.InvalidStrategyValueError("missing field")

    monkeypatch.setattr(btd6_strategy_mutation, "submit_strategy", _submit)

    modal = StrategySubmitModal()
    _set_inputs(modal, title="", summary="", map="", mode="", hero="")
    interaction = _interaction()
    await modal.on_submit(interaction)
    msg = interaction.response.send_message.await_args.args[0]
    assert "missing field" in msg
