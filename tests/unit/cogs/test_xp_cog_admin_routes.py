"""Regression tests — admin XP paths route through xp_service (P0 PR-1).

Before this fix, `_GiveXpModal.on_submit` and `XpCog.givexp` called
`db.add_xp` directly, bypassing the service layer so no
`EVT_XP_AWARDED` / `EVT_LEVEL_UP` ever fired for admin grants.

These tests assert the cog code now invokes `xp_service.award` so the
service-layer event emission (covered separately by
`tests/unit/services/test_xp_service.py`) actually runs.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_interaction(
    *,
    guild_id: int = 99999,
    user_id: int = 77777,
) -> MagicMock:
    """Minimal discord.Interaction stub for modal callbacks."""
    interaction = MagicMock()
    interaction.guild_id = guild_id
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _make_member(member_id: int = 12345) -> MagicMock:
    member = MagicMock()
    member.id = member_id
    member.mention = f"<@{member_id}>"
    return member


def _make_ctx(*, guild_id: int = 99999, author_id: int = 77777) -> MagicMock:
    ctx = MagicMock()
    ctx.guild = MagicMock()
    ctx.guild.id = guild_id
    ctx.author = MagicMock()
    ctx.author.id = author_id
    ctx.send = AsyncMock()
    return ctx


def _xp_award_result(new_xp: int = 150, new_level: int = 2) -> MagicMock:
    """A stand-in for services.xp_service.XpAward."""
    result = MagicMock()
    result.new_xp = new_xp
    result.new_level = new_level
    result.leveled_up = False
    return result


@pytest.mark.asyncio
async def test_give_xp_modal_calls_xp_service_award():
    """_GiveXpModal.on_submit must route through xp_service.award."""
    from cogs.xp_cog import _GiveXpModal

    modal = _GiveXpModal(hub=MagicMock())
    modal.member_input = MagicMock()
    modal.member_input.value = "<@12345>"
    modal.amount_input = MagicMock()
    modal.amount_input.value = "50"

    interaction = _make_interaction()
    member = _make_member()

    with (
        patch("cogs.xp_cog._parse_member", return_value=member),
        patch(
            "cogs.xp_cog.xp_service.award",
            new_callable=AsyncMock,
            return_value=_xp_award_result(),
        ) as award,
    ):
        await modal.on_submit(interaction)

    award.assert_awaited_once_with(
        guild_id=interaction.guild_id,
        user_id=member.id,
        amount=50,
        source="admin:modal_grant",
    )


@pytest.mark.asyncio
async def test_givexp_command_calls_xp_service_award():
    """XpCog.givexp must route through xp_service.award."""
    from cogs.xp_cog import XpCog

    cog = XpCog(bot=MagicMock())
    ctx = _make_ctx()
    member = _make_member()

    with patch(
        "cogs.xp_cog.xp_service.award",
        new_callable=AsyncMock,
        return_value=_xp_award_result(new_xp=300, new_level=4),
    ) as award:
        await cog.givexp.callback(cog, ctx, member, 100)

    award.assert_awaited_once_with(
        guild_id=ctx.guild.id,
        user_id=member.id,
        amount=100,
        source="admin:givexp",
    )


@pytest.mark.asyncio
async def test_givexp_command_rejects_non_positive_amount():
    """Negative/zero amounts must short-circuit before the service call."""
    from cogs.xp_cog import XpCog

    cog = XpCog(bot=MagicMock())
    ctx = _make_ctx()
    member = _make_member()

    with patch(
        "cogs.xp_cog.xp_service.award",
        new_callable=AsyncMock,
    ) as award:
        await cog.givexp.callback(cog, ctx, member, 0)

    award.assert_not_awaited()
    ctx.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_reset_xp_modal_calls_xp_service_reset():
    """_ResetXpModal.on_submit must route through xp_service.reset."""
    from cogs.xp_cog import _ResetXpModal

    modal = _ResetXpModal(hub=MagicMock())
    modal.member_input = MagicMock()
    modal.member_input.value = "<@12345>"
    modal.confirm_input = MagicMock()
    modal.confirm_input.value = "CONFIRM"

    interaction = _make_interaction()
    member = _make_member()

    with (
        patch("cogs.xp_cog._parse_member", return_value=member),
        patch(
            "cogs.xp_cog.xp_service.reset",
            new_callable=AsyncMock,
        ) as reset,
    ):
        await modal.on_submit(interaction)

    reset.assert_awaited_once_with(
        guild_id=interaction.guild_id,
        user_id=member.id,
        source="admin:modal_reset",
        actor_id=interaction.user.id,
    )


@pytest.mark.asyncio
async def test_reset_xp_modal_aborts_without_confirm():
    """Without CONFIRM token the service must NOT be called."""
    from cogs.xp_cog import _ResetXpModal

    modal = _ResetXpModal(hub=MagicMock())
    modal.member_input = MagicMock()
    modal.member_input.value = "<@12345>"
    modal.confirm_input = MagicMock()
    modal.confirm_input.value = "no"

    interaction = _make_interaction()

    with patch(
        "cogs.xp_cog.xp_service.reset",
        new_callable=AsyncMock,
    ) as reset:
        await modal.on_submit(interaction)

    reset.assert_not_awaited()


@pytest.mark.asyncio
async def test_resetxp_command_calls_xp_service_reset():
    """XpCog.resetxp must route through xp_service.reset."""
    from cogs.xp_cog import XpCog

    cog = XpCog(bot=MagicMock())
    ctx = _make_ctx()
    member = _make_member()

    with patch(
        "cogs.xp_cog.xp_service.reset",
        new_callable=AsyncMock,
    ) as reset:
        await cog.resetxp.callback(cog, ctx, member)

    reset.assert_awaited_once_with(
        guild_id=ctx.guild.id,
        user_id=member.id,
        source="admin:resetxp",
        actor_id=ctx.author.id,
    )
