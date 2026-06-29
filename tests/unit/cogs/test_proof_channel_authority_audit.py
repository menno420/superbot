"""Proof-channel completion-deepening (Q-0209 punch #1 + #2).

Pins the two maturation gaps the completion certificate named:

* **Punch #2 — audit trail:** every ``_lock_for_winner`` / ``_unlock``
  permission change emits ``audit.action_recorded`` (subsystem
  ``proof_channel``), so an exclusive prize-access grant/revoke leaves a
  trail like every other access surface. The timer-driven auto-unlock is a
  ``system`` actor.
* **Punch #1 — modal/panel authority re-check:** opening the prize panel does
  not authorize later button/modal callbacks; each mutation entry point
  re-verifies the actor still holds ``manage_channels``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.proof_channel_cog import (
    ProofChannelCog,
    _PrizeManagerView,
    _PrizeWinnerModal,
    _reject_without_manage_channels,
    _TimedPrizeModal,
)


def _channel(channel_id: int = 555, guild_id: int = 42) -> MagicMock:
    ch = MagicMock(spec=discord.TextChannel)
    ch.id = channel_id
    ch.mention = "#proof"
    guild = MagicMock()
    guild.id = guild_id
    guild.default_role = MagicMock()
    guild.me = MagicMock()
    ch.guild = guild
    ch.edit = AsyncMock()
    return ch


def _interaction(*, manage_channels: bool, user_id: int = 7, guild_id: int = 42):
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.user.guild_permissions = MagicMock()
    interaction.user.guild_permissions.manage_channels = manage_channels
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.guild_id = guild_id
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Punch #2 — audit trail on lock / unlock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lock_emits_grant_audit_event():
    cog = ProofChannelCog(MagicMock())
    ch = _channel()
    winner = MagicMock()
    winner.id = 99
    winner.display_name = "Winner"

    with patch(
        "services.audit_events.emit_audit_action", new=AsyncMock()
    ) as emit:
        await cog._lock_for_winner(ch, winner, actor_id=7)

    ch.edit.assert_awaited_once()
    emit.assert_awaited_once()
    kw = emit.await_args.kwargs
    assert kw["subsystem"] == "proof_channel"
    assert kw["mutation_type"] == "prize_access_grant"
    assert kw["target"] == "channel:555"
    assert kw["new_value"] == "winner:99"
    assert kw["guild_id"] == 42
    assert kw["actor_id"] == 7
    assert kw["actor_type"] == "admin"


@pytest.mark.asyncio
async def test_unlock_emits_revoke_audit_event():
    cog = ProofChannelCog(MagicMock())
    ch = _channel()

    with patch(
        "services.audit_events.emit_audit_action", new=AsyncMock()
    ) as emit:
        await cog._unlock(ch, actor_id=7)

    ch.edit.assert_awaited_once()
    emit.assert_awaited_once()
    kw = emit.await_args.kwargs
    assert kw["mutation_type"] == "prize_access_revoke"
    assert kw["target"] == "channel:555"
    assert kw["actor_id"] == 7
    assert kw["actor_type"] == "admin"


@pytest.mark.asyncio
async def test_timer_unlock_is_a_system_actor():
    cog = ProofChannelCog(MagicMock())
    ch = _channel()

    with patch(
        "services.audit_events.emit_audit_action", new=AsyncMock()
    ) as emit:
        await cog._unlock(ch, actor_id=None, actor_type="system")

    kw = emit.await_args.kwargs
    assert kw["actor_id"] is None
    assert kw["actor_type"] == "system"


@pytest.mark.asyncio
async def test_audit_bus_failure_does_not_block_the_unlock():
    """A best-effort audit emit must never strand a winner locked out."""
    cog = ProofChannelCog(MagicMock())
    ch = _channel()

    with patch(
        "services.audit_events.emit_audit_action",
        new=AsyncMock(side_effect=RuntimeError("bus down")),
    ):
        # Must NOT raise — audit is best-effort, the access change is authoritative.
        await cog._unlock(ch, actor_id=7)
    ch.edit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Punch #1 — authority re-check at the callback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_helper_allows_manager_denies_others():
    ok = _interaction(manage_channels=True)
    assert await _reject_without_manage_channels(ok) is True
    ok.response.send_message.assert_not_awaited()

    denied = _interaction(manage_channels=False)
    assert await _reject_without_manage_channels(denied) is False
    denied.response.send_message.assert_awaited_once()
    assert "Manage Channels" in denied.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_grant_modal_denies_actor_without_manage_channels():
    cog = ProofChannelCog(MagicMock())
    cog._lock_for_winner = AsyncMock()  # type: ignore[method-assign]
    modal = _PrizeWinnerModal(cog, timed=False)
    modal.winner_input = MagicMock()
    modal.winner_input.value = "<@99>"
    interaction = _interaction(manage_channels=False)

    await modal.on_submit(interaction)

    cog._lock_for_winner.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_timed_modal_denies_actor_without_manage_channels():
    cog = ProofChannelCog(MagicMock())
    cog._lock_for_winner = AsyncMock()  # type: ignore[method-assign]
    winner = MagicMock()
    modal = _TimedPrizeModal(cog, winner)
    modal.duration_input = MagicMock()
    modal.duration_input.value = "10"
    interaction = _interaction(manage_channels=False)

    await modal.on_submit(interaction)

    cog._lock_for_winner.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_panel_end_session_denies_actor_without_manage_channels():
    cog = ProofChannelCog(MagicMock())
    cog._unlock = AsyncMock()  # type: ignore[method-assign]
    cog.get_proof_channel = AsyncMock(return_value=_channel())  # type: ignore[method-assign]
    ctx = MagicMock()
    ctx.author = MagicMock()
    view = _PrizeManagerView(ctx, cog)
    interaction = _interaction(manage_channels=False)

    await view.btn_end.callback(interaction)  # type: ignore[union-attr,misc]

    cog._unlock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_panel_grant_button_denies_actor_without_manage_channels():
    cog = ProofChannelCog(MagicMock())
    ctx = MagicMock()
    view = _PrizeManagerView(ctx, cog)
    interaction = _interaction(manage_channels=False)

    await view.btn_grant.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_modal.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
