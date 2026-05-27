"""PR-F + Blocker PR-1 tests for the strategy submission modal.

The modal now defers before the DB insert and delivers every result
through ``safe_followup`` to avoid 3-second token expiry. Only the
synchronous guild-context check still uses
``interaction.response.send_message`` (pre-defer, no I/O).
"""

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
    """Build an interaction mock that flips ``response.is_done``
    after ``defer()`` so the safe_* helpers route correctly.
    """
    interaction = MagicMock()
    interaction.guild = SimpleNamespace(id=guild_id) if guild_id else None
    interaction.user = SimpleNamespace(id=555, display_name="alice", name="alice")

    deferred = {"done": False}
    interaction.response.is_done = lambda: deferred["done"]

    async def _defer(**_kw):
        deferred["done"] = True

    interaction.response.defer = AsyncMock(side_effect=_defer)
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.original_response = AsyncMock()
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
    # Post-defer: success message arrives via safe_followup (content
    # passed as kwarg because safe_followup unpacks via **kwargs).
    interaction.response.defer.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()
    msg = interaction.followup.send.await_args.kwargs["content"]
    assert "#42" in msg


@pytest.mark.asyncio
async def test_submit_requires_guild_context():
    """The guild-context check is synchronous and runs BEFORE defer,
    so it still uses interaction.response.send_message."""
    modal = StrategySubmitModal()
    _set_inputs(modal, title="x", summary="y", map="", mode="", hero="")
    interaction = _interaction(guild_id=0)
    interaction.guild = None
    await modal.on_submit(interaction)
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "guild context" in msg
    # No defer happened — the validation refused before any I/O.
    interaction.response.defer.assert_not_awaited()
    interaction.followup.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_submit_surfaces_validation_error(monkeypatch):
    """Validation errors come out via safe_followup (post-defer),
    surfacing the typed exc message but not the class name."""

    async def _submit(**_kw):
        raise btd6_strategy_mutation.InvalidStrategyValueError("missing field")

    monkeypatch.setattr(btd6_strategy_mutation, "submit_strategy", _submit)

    modal = StrategySubmitModal()
    _set_inputs(modal, title="", summary="", map="", mode="", hero="")
    interaction = _interaction()
    await modal.on_submit(interaction)
    interaction.followup.send.assert_awaited_once()
    msg = interaction.followup.send.await_args.kwargs["content"]
    assert "missing field" in msg
    assert "InvalidStrategyValueError" not in msg


@pytest.mark.asyncio
async def test_modal_defers_before_submit_strategy(monkeypatch):
    """defer() must be awaited BEFORE submit_strategy runs so the
    3-second token doesn't expire under DB load.
    """
    call_order: list[str] = []

    async def _submit(**_kw):
        call_order.append("submit")
        return MagicMock(strategy_id=42, action="submitted")

    monkeypatch.setattr(btd6_strategy_mutation, "submit_strategy", _submit)

    modal = StrategySubmitModal()
    _set_inputs(modal, title="t", summary="s", map="", mode="", hero="")
    interaction = _interaction()

    deferred = {"done": False}

    async def _defer(**_kw):
        call_order.append("defer")
        deferred["done"] = True
        interaction.response.is_done = lambda: True

    interaction.response.defer.side_effect = _defer

    await modal.on_submit(interaction)
    assert call_order[:2] == ["defer", "submit"]


@pytest.mark.asyncio
async def test_modal_unexpected_error_uses_safe_followup(monkeypatch):
    """Unexpected exceptions are surfaced via safe_followup with a
    generic user-facing message — no class name leakage.
    """

    async def _submit(**_kw):
        raise RuntimeError("database connection died")

    monkeypatch.setattr(btd6_strategy_mutation, "submit_strategy", _submit)

    modal = StrategySubmitModal()
    _set_inputs(modal, title="t", summary="s", map="", mode="", hero="")
    interaction = _interaction()
    # Must not raise.
    await modal.on_submit(interaction)

    interaction.followup.send.assert_awaited_once()
    msg = interaction.followup.send.await_args.kwargs["content"]
    assert "Unexpected error" in msg
    assert "RuntimeError" not in msg
    assert "database connection died" not in msg
