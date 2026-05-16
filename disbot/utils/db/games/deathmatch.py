"""deathmatch_stats CRUD."""

from __future__ import annotations

from utils.db import pool


async def get_deathmatch_stats(user_id: int, guild_id: int = 0) -> dict:
    row = await pool.fetchone(
        "SELECT wins, losses FROM deathmatch_stats WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
    return row or {"wins": 0, "losses": 0}


async def update_deathmatch(
    winner_id: int,
    loser_id: int,
    guild_id: int = 0,
) -> None:
    """Atomic two-side stats update.

    Wrapped in a single transaction so a failure on the second statement
    cannot leave the winner's record updated without the loser's.
    """
    p = pool.get()
    async with p.acquire() as conn, conn.transaction():
        await conn.execute(
            """INSERT INTO deathmatch_stats (user_id, guild_id, wins)
                 VALUES ($1, $2, 1)
               ON CONFLICT (user_id, guild_id) DO UPDATE
                 SET wins=deathmatch_stats.wins+1""",
            winner_id,
            guild_id,
        )
        await conn.execute(
            """INSERT INTO deathmatch_stats (user_id, guild_id, losses)
                 VALUES ($1, $2, 1)
               ON CONFLICT (user_id, guild_id) DO UPDATE
                 SET losses=deathmatch_stats.losses+1""",
            loser_id,
            guild_id,
        )


async def get_deathmatch_leaderboard(guild_id: int = 0) -> list[dict]:
    return await pool.fetchall(
        "SELECT user_id, wins, losses FROM deathmatch_stats "
        "WHERE guild_id=$1 ORDER BY wins DESC LIMIT 15",
        (guild_id,),
    )
