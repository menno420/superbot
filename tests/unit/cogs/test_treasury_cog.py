"""Cog-level command tests for the Treasury cog.

Completion-first deepening (Q-0209) — clears Treasury completion-cert punch **#1**
(`docs/planning/feature-completion/units/treasury.md`): cog-level coverage of
`!treasury` (panel open), `!treasury contribute`, and `!treasury grant`, including
the `manage_guild` authority gate on disburse.  The pre-existing coverage was the
service (`test_treasury_service.py`) and the Economy-hub button
(`test_economy_treasury_button.py`); the command layer itself was untested.

Pure test coverage — no runtime change.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from cogs.treasury_cog import TreasuryCog


def _ctx(*, guild_id: int = 55, author_id: int = 7) -> MagicMock:
    ctx = MagicMock()
    ctx.guild = MagicMock()
    ctx.guild.id = guild_id
    ctx.author = MagicMock(spec=discord.Member)
    ctx.author.id = author_id
    ctx.send = AsyncMock()
    return ctx


def _result(*, success: bool = True, message: str = "ok") -> MagicMock:
    r = MagicMock()
    r.success = success
    r.message = message
    return r


def _member(**perms: bool) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = 999
    gp = MagicMock()
    gp.manage_guild = perms.get("manage_guild", False)
    m.guild_permissions = gp
    return m


def _grant_predicate():
    checks = TreasuryCog.grant.checks
    assert checks, "grant has no permission check"
    return checks[0]


# --------------------------------------------------------------------------
# treasury (panel open)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_treasury_group_opens_the_panel():
    cog = TreasuryCog(MagicMock())
    ctx = _ctx()
    embed = MagicMock()
    view = MagicMock()
    with patch(
        "cogs.treasury_cog.open_treasury_panel",
        AsyncMock(return_value=(embed, view)),
    ) as opener:
        await cog.treasury.callback(cog, ctx)
    opener.assert_awaited_once_with(ctx.author, 55)
    ctx.send.assert_awaited_once()
    # the view keeps a handle on its posted message for in-place redraws
    assert view.message is ctx.send.return_value


# --------------------------------------------------------------------------
# contribute
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_contribute_calls_service_and_reports():
    cog = TreasuryCog(MagicMock())
    ctx = _ctx()
    with patch(
        "cogs.treasury_cog.treasury_service.contribute",
        AsyncMock(return_value=_result(message="Contributed 100.")),
    ) as contribute:
        await cog.contribute.callback(cog, ctx, 100)
    contribute.assert_awaited_once_with(55, 7, 100)
    ctx.send.assert_awaited_once_with("Contributed 100.")


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", [0, -5])
async def test_contribute_rejects_non_positive_before_io(amount):
    cog = TreasuryCog(MagicMock())
    ctx = _ctx()
    with patch("cogs.treasury_cog.treasury_service.contribute") as contribute:
        await cog.contribute.callback(cog, ctx, amount)
    contribute.assert_not_called()
    ctx.send.assert_awaited_once()
    assert "positive" in ctx.send.await_args.args[0]


# --------------------------------------------------------------------------
# grant (disburse) — behaviour
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_grant_disburses_and_mentions_on_success():
    cog = TreasuryCog(MagicMock())
    ctx = _ctx()
    target = MagicMock(spec=discord.Member)
    target.id = 321
    target.mention = "@target"
    with patch(
        "cogs.treasury_cog.treasury_service.disburse",
        AsyncMock(return_value=_result(success=True, message="Sent 50.")),
    ) as disburse:
        await cog.grant.callback(cog, ctx, target, 50)
    disburse.assert_awaited_once_with(55, 7, 321, 50)
    sent = ctx.send.await_args.args[0]
    assert sent.startswith("@target — ") and "Sent 50." in sent


@pytest.mark.asyncio
async def test_grant_failure_has_no_mention_prefix():
    cog = TreasuryCog(MagicMock())
    ctx = _ctx()
    target = MagicMock(spec=discord.Member)
    target.id = 321
    target.mention = "@target"
    with patch(
        "cogs.treasury_cog.treasury_service.disburse",
        AsyncMock(return_value=_result(success=False, message="Pool underfunded.")),
    ):
        await cog.grant.callback(cog, ctx, target, 50)
    assert ctx.send.await_args.args[0] == "Pool underfunded."


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", [0, -1])
async def test_grant_rejects_non_positive_before_io(amount):
    cog = TreasuryCog(MagicMock())
    ctx = _ctx()
    target = MagicMock(spec=discord.Member)
    target.id = 321
    with patch("cogs.treasury_cog.treasury_service.disburse") as disburse:
        await cog.grant.callback(cog, ctx, target, amount)
    disburse.assert_not_called()
    ctx.send.assert_awaited_once()
    assert "positive" in ctx.send.await_args.args[0]


# --------------------------------------------------------------------------
# grant — authority (manage_guild / owner)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_grant_denies_member_without_manage_guild():
    predicate = _grant_predicate()
    ctx = MagicMock()
    ctx.author = _member(manage_guild=False)
    with pytest.raises(commands.MissingPermissions):
        await predicate(ctx)


@pytest.mark.asyncio
async def test_grant_allows_member_with_manage_guild():
    predicate = _grant_predicate()
    ctx = MagicMock()
    ctx.author = _member(manage_guild=True)
    assert await predicate(ctx) is True


@pytest.mark.asyncio
async def test_grant_allows_platform_owner():
    predicate = _grant_predicate()
    ctx = MagicMock()
    ctx.author = _member(manage_guild=False)
    with patch("core.runtime.permission_checks.is_platform_owner", return_value=True):
        assert await predicate(ctx) is True
