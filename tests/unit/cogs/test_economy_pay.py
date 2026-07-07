"""Cog-level tests for `!pay` / `!transfer` (peer coin transfer).

Wires the long-ready, fully-audited `economy_service.transfer()` to a user
command (FINAL-REVIEW §6.3 "ready-but-unwired"). Named `pay`/`transfer`, NOT
`give` — the `give` token is banned surface-wide after the #1541 boot
collision (Q-0211; `tests/unit/invariants/test_extension_integrity.py` pins
the ban). The service already guards positivity / self-transfer /
insufficient funds inside one transaction with two audit rows; the cog layer
adds the UX guards (missing args, bot recipient, friendly copy) and mirrors
the sibling money-command idiom (ECONOMY_COLOR embed + `post_log_embed`).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.economy_cog import EconomyCog
from services.economy_service import InsufficientFundsError


def _ctx(*, guild_id: int = 55, author_id: int = 7) -> MagicMock:
    ctx = MagicMock()
    ctx.guild = MagicMock()
    ctx.guild.id = guild_id
    ctx.author = MagicMock(spec=discord.Member)
    ctx.author.id = author_id
    ctx.author.bot = False
    ctx.author.mention = f"<@{author_id}>"
    ctx.author.display_name = "Payer"
    ctx.send = AsyncMock()
    return ctx


def _member(id_: int = 9, *, bot: bool = False) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = id_
    m.bot = bot
    m.mention = f"<@{id_}>"
    m.display_name = "Payee"
    return m


def _cog() -> EconomyCog:
    return EconomyCog(MagicMock())


async def _invoke(cog, ctx, member, amount):
    await cog.pay.callback(cog, ctx, member, amount)


@pytest.mark.asyncio
async def test_pay_happy_path_transfers_and_logs():
    cog, ctx, member = _cog(), _ctx(), _member()
    with (
        patch(
            "cogs.economy_cog.economy_service.transfer",
            new_callable=AsyncMock,
            return_value=(90, 110),
        ) as transfer,
        patch(
            "cogs.economy_cog.post_log_embed",
            new_callable=AsyncMock,
        ) as log,
    ):
        await _invoke(cog, ctx, member, 10)

    transfer.assert_awaited_once_with(
        55,
        7,
        9,
        10,
        reason="gift",
        actor_id=7,
    )
    embed = ctx.send.call_args.kwargs["embed"]
    field_values = [f.value for f in embed.fields]
    assert "**90**" in field_values[1]  # payer balance
    assert "**110**" in field_values[2]  # payee balance
    log.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("member", "amount"),
    [
        (None, 10),  # missing member
        ("payee", None),  # missing amount
        ("bot", 10),  # bot recipient
        ("self", 10),  # self-transfer
        ("payee", 0),  # non-positive
        ("payee", -5),
    ],
)
async def test_pay_guard_rails_never_reach_the_service(member, amount):
    cog, ctx = _cog(), _ctx()
    target = {
        None: None,
        "payee": _member(),
        "bot": _member(bot=True),
        "self": None,
    }.get(member, _member())
    if member == "self":
        target = _member(id_=ctx.author.id)

    with patch(
        "cogs.economy_cog.economy_service.transfer",
        new_callable=AsyncMock,
    ) as transfer:
        await _invoke(cog, ctx, target, amount)

    transfer.assert_not_awaited()
    ctx.send.assert_awaited_once()  # friendly copy, no crash


@pytest.mark.asyncio
async def test_pay_insufficient_funds_is_friendly():
    cog, ctx, member = _cog(), _ctx(), _member()
    with (
        patch(
            "cogs.economy_cog.economy_service.transfer",
            new_callable=AsyncMock,
            side_effect=InsufficientFundsError("user=7 has 3 coins, needs 10"),
        ),
        patch(
            "cogs.economy_cog.db.get_coins",
            new_callable=AsyncMock,
            return_value=3,
        ),
        patch(
            "cogs.economy_cog.post_log_embed",
            new_callable=AsyncMock,
        ) as log,
    ):
        await _invoke(cog, ctx, member, 10)

    message = ctx.send.call_args.args[0]
    assert "Not enough coins" in message
    assert "**3**" in message
    log.assert_not_awaited()


def test_pay_never_uses_the_banned_give_token():
    # Q-0211: `give` crashed the bot at boot via a top-level name collision
    # and is banned surface-wide; this command must never regrow it.
    names = {EconomyCog.pay.name, *EconomyCog.pay.aliases}
    assert "give" not in names
    assert names == {"pay", "transfer"}
