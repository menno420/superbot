"""Unit tests for the ``!give`` / ``!pay`` peer coin-transfer command.

The command (``cogs.economy_cog.EconomyCog.give``) is the user surface over the
already-audited ``services.economy_service.transfer`` seam (S1 completion-first
deepening win — the assessment found the primitive existed but no command did).

Pins:

* The happy path forwards the right args to ``transfer`` and announces both
  balances.
* The guard rails — missing args, a bot target, self-transfer, a non-positive
  amount — short-circuit and **never** call ``transfer`` (no audit-log write for
  an invalid request).
* ``InsufficientFundsError`` degrades to a friendly message, not a traceback.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


def _member(id_: int, name: str, *, bot: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        id=id_,
        display_name=name,
        mention=f"<@{id_}>",
        bot=bot,
    )


def _ctx(author: SimpleNamespace) -> MagicMock:
    ctx = MagicMock()
    ctx.author = author
    ctx.guild = SimpleNamespace(id=99)
    ctx.send = AsyncMock()
    return ctx


def _cog() -> object:
    from cogs.economy_cog import EconomyCog

    return EconomyCog(MagicMock())


def _callback():
    from cogs.economy_cog import EconomyCog

    return EconomyCog.give.callback


@pytest.mark.asyncio
async def test_give_happy_path_forwards_to_transfer_and_reports_balances():
    cog = _cog()
    author = _member(1, "Alice")
    target = _member(2, "Bob")
    ctx = _ctx(author)

    with (
        patch(
            "services.economy_service.transfer",
            new_callable=AsyncMock,
            return_value=(40, 160),
        ) as mock_transfer,
        patch(
            "cogs.economy_cog.post_log_embed",
            new_callable=AsyncMock,
        ) as mock_log,
    ):
        await _callback()(cog, ctx, target, 60)

    mock_transfer.assert_awaited_once_with(
        99,
        1,
        2,
        60,
        reason="gift",
        actor_id=1,
    )
    # A success embed naming both balances is sent, and the audit log line fires.
    embed = ctx.send.await_args.kwargs["embed"]
    assert "40" in embed.fields[0].value
    assert "160" in embed.fields[1].value
    mock_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_give_missing_args_shows_usage_and_does_not_transfer():
    cog = _cog()
    ctx = _ctx(_member(1, "Alice"))
    with patch(
        "services.economy_service.transfer",
        new_callable=AsyncMock,
    ) as mock_transfer:
        await _callback()(cog, ctx, None, None)
    mock_transfer.assert_not_awaited()
    assert "Usage" in ctx.send.await_args.args[0]


@pytest.mark.asyncio
async def test_give_to_a_bot_is_rejected():
    cog = _cog()
    ctx = _ctx(_member(1, "Alice"))
    with patch(
        "services.economy_service.transfer",
        new_callable=AsyncMock,
    ) as mock_transfer:
        await _callback()(cog, ctx, _member(2, "BotUser", bot=True), 10)
    mock_transfer.assert_not_awaited()
    assert "bot" in ctx.send.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_give_to_self_is_rejected():
    cog = _cog()
    author = _member(1, "Alice")
    ctx = _ctx(author)
    with patch(
        "services.economy_service.transfer",
        new_callable=AsyncMock,
    ) as mock_transfer:
        await _callback()(cog, ctx, author, 10)
    mock_transfer.assert_not_awaited()
    assert "yourself" in ctx.send.await_args.args[0].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", [0, -5])
async def test_give_non_positive_amount_is_rejected(bad: int):
    cog = _cog()
    ctx = _ctx(_member(1, "Alice"))
    with patch(
        "services.economy_service.transfer",
        new_callable=AsyncMock,
    ) as mock_transfer:
        await _callback()(cog, ctx, _member(2, "Bob"), bad)
    mock_transfer.assert_not_awaited()
    assert "positive" in ctx.send.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_give_insufficient_funds_is_a_friendly_message():
    from services.economy_service import InsufficientFundsError

    cog = _cog()
    ctx = _ctx(_member(1, "Alice"))
    with (
        patch(
            "services.economy_service.transfer",
            new_callable=AsyncMock,
            side_effect=InsufficientFundsError("nope"),
        ),
        patch(
            "cogs.economy_cog.db.get_coins",
            new_callable=AsyncMock,
            return_value=25,
        ),
    ):
        await _callback()(cog, ctx, _member(2, "Bob"), 100)
    msg = ctx.send.await_args.args[0]
    assert "enough" in msg.lower()
    assert "25" in msg
