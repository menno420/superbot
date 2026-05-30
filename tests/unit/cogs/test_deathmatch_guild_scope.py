"""Audit P0-2 — deathmatch stats must be scoped to the originating guild.

The ``deathmatch_stats`` table has a composite primary key
``(user_id, guild_id)`` and the leaderboard query filters
``WHERE guild_id=$1`` — per-guild stats were the schema's design
intent.  The cog's write path historically omitted ``guild_id``, so
every result landed under the global ``guild_id=0`` bucket (cross-guild
leakage).  These tests pin that the duel flow now threads the
originating guild id through to ``db.update_deathmatch``.
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


def _player(id_: int, name: str = "P") -> SimpleNamespace:
    return SimpleNamespace(
        id=id_,
        display_name=name,
        mention=f"<@{id_}>",
        bot=False,
    )


@pytest.mark.asyncio
async def test_update_leaderboard_forwards_guild_id_to_db():
    """The write seam forwards its ``guild_id`` to ``db.update_deathmatch``."""
    from cogs.deathmatch_cog import Deathmatch

    cog = Deathmatch(MagicMock())
    with patch(
        "cogs.deathmatch_cog.db.update_deathmatch",
        new_callable=AsyncMock,
    ) as mock_db:
        await cog.update_leaderboard(winner_id=1, loser_id=2, guild_id=99)
    mock_db.assert_awaited_once_with(1, 2, 99)


@pytest.mark.asyncio
async def test_duel_timeout_records_result_under_originating_guild():
    """A real duel timeout threads ``ctx.guild.id`` into the write path."""
    from cogs.deathmatch_cog import Deathmatch, _Duel, _DuelView

    cog = Deathmatch(MagicMock())
    p1, p2 = _player(100, "One"), _player(200, "Two")
    duel = _Duel(p1, p2)  # type: ignore[arg-type]
    duel_key = tuple(sorted([p1.id, p2.id]))
    cog.active_duels[duel_key] = duel

    ctx = MagicMock()
    ctx.guild.id = 777
    view = _DuelView(cog, duel, duel_key, ctx)

    with patch(
        "cogs.deathmatch_cog.Deathmatch.update_leaderboard",
        new_callable=AsyncMock,
    ) as mock_update:
        # turn == player1, so on timeout player1 loses to player2.
        await view.on_timeout()

    mock_update.assert_awaited_once_with(
        winner_id=p2.id,
        loser_id=p1.id,
        guild_id=777,
    )
