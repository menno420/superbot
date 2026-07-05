"""Stage-2 walk bug #8 — proof-channel timed locks survive a restart.

A timed prize lock's unlock deadline used to live only in an in-memory
``asyncio.sleep`` task, so a restart lost the timer while the winner's channel
overwrite persisted — the channel stayed locked forever. The fix persists the
deadline and reconciles it at boot: expired → unlock now; still-pending →
reschedule; stale guild/channel → drop the row.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.proof_channel_cog import ProofChannelCog

# ruff: noqa: S101


def _cog() -> ProofChannelCog:
    return ProofChannelCog(MagicMock())


def _channel(channel_id: int = 555, guild_id: int = 42):
    ch = MagicMock(spec=discord.TextChannel)
    ch.id = channel_id
    ch.mention = "#proof"
    guild = SimpleNamespace(id=guild_id, default_role=MagicMock(), me=MagicMock())
    ch.guild = guild
    ch.edit = AsyncMock()
    return ch


@pytest.mark.asyncio
async def test_persist_timed_lock_writes_deadline():
    cog = _cog()
    with patch(
        "utils.db.proof_channel_locks.upsert_lock", new=AsyncMock(),
    ) as upsert:
        await cog._persist_timed_lock(42, 555, 99, 10)
    upsert.assert_awaited_once()
    kwargs = upsert.await_args.kwargs
    assert kwargs["guild_id"] == 42
    assert kwargs["channel_id"] == 555
    assert kwargs["winner_id"] == 99
    unlock_at = kwargs["unlock_at"]
    assert unlock_at.tzinfo is not None  # tz-aware UTC
    assert unlock_at > datetime.now(tz=timezone.utc)


@pytest.mark.asyncio
async def test_unlock_clears_persisted_row():
    cog = _cog()
    ch = _channel()
    with (
        patch("cogs.proof_channel_cog._emit_prize_audit", new=AsyncMock()),
        patch("utils.db.proof_channel_locks.delete_lock", new=AsyncMock()) as delete,
    ):
        await cog._unlock(ch, actor_id=7)
    ch.edit.assert_awaited_once()
    delete.assert_awaited_once_with(ch.guild.id, ch.id)


@pytest.mark.asyncio
async def test_reconcile_expired_unlocks_now():
    cog = _cog()
    ch = _channel()
    cog.bot.get_guild = MagicMock(return_value=SimpleNamespace(
        get_channel=MagicMock(return_value=ch),
    ))
    past = datetime.now(tz=timezone.utc) - timedelta(minutes=1)
    rows = [{"guild_id": 42, "channel_id": 555, "winner_id": 99, "unlock_at": past}]
    with (
        patch("utils.db.proof_channel_locks.all_locks", new=AsyncMock(return_value=rows)),
        patch("utils.db.proof_channel_locks.delete_lock", new=AsyncMock()),
        patch("cogs.proof_channel_cog._emit_prize_audit", new=AsyncMock()),
    ):
        await cog._reconcile_locks()
    ch.edit.assert_awaited_once()  # the expired lock was unlocked


@pytest.mark.asyncio
async def test_reconcile_active_reschedules_without_unlocking():
    cog = _cog()
    ch = _channel()
    cog.bot.get_guild = MagicMock(return_value=SimpleNamespace(
        get_channel=MagicMock(return_value=ch),
    ))
    future = datetime.now(tz=timezone.utc) + timedelta(minutes=5)
    rows = [{"guild_id": 42, "channel_id": 555, "winner_id": 99, "unlock_at": future}]

    def _fake_spawn(_name, coro):
        coro.close()  # consume the coroutine so it isn't "never awaited"
        return MagicMock()

    with (
        patch("utils.db.proof_channel_locks.all_locks", new=AsyncMock(return_value=rows)),
        patch("cogs.proof_channel_cog.tasks.spawn", side_effect=_fake_spawn) as spawn,
    ):
        await cog._reconcile_locks()
    ch.edit.assert_not_awaited()  # still pending — do NOT unlock
    spawn.assert_called_once()  # timer rescheduled
    assert 42 in cog._timed_tasks


@pytest.mark.asyncio
async def test_reconcile_stale_row_is_dropped():
    cog = _cog()
    cog.bot.get_guild = MagicMock(return_value=None)  # guild gone
    rows = [{"guild_id": 42, "channel_id": 555, "winner_id": 99,
             "unlock_at": datetime.now(tz=timezone.utc)}]
    with (
        patch("utils.db.proof_channel_locks.all_locks", new=AsyncMock(return_value=rows)),
        patch("utils.db.proof_channel_locks.delete_lock", new=AsyncMock()) as delete,
    ):
        await cog._reconcile_locks()  # must not raise
    delete.assert_awaited_once_with(42, 555)
