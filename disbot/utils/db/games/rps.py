"""rps_players + rps_matches CRUD."""

from __future__ import annotations

from utils.db import pool


async def rps_ensure_player(user_id: int, name: str, guild_id: int = 0) -> None:
    await pool.execute(
        "INSERT INTO rps_players (user_id, guild_id, name) "
        "VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
        (user_id, guild_id, name),
    )


async def rps_update_stat(user_id: int, result: str, guild_id: int = 0) -> None:
    col = {"win": "wins", "loss": "losses", "tie": "ties"}.get(result)
    if col:
        await pool.execute(
            f"UPDATE rps_players SET {col}={col}+1 WHERE user_id=$1 AND guild_id=$2",
            (user_id, guild_id),
        )


async def rps_get_leaderboard(guild_id: int = 0) -> list[dict]:
    return await pool.fetchall(
        "SELECT name, wins, losses, ties FROM rps_players "
        "WHERE guild_id=$1 ORDER BY wins DESC LIMIT 15",
        (guild_id,),
    )
