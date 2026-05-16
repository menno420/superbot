"""rps_players + rps_matches CRUD.

PR R1 (mining-shape sibling fix): every public function now requires
``guild_id``.  Two production bugs are closed here:

  * ``rps_update_stat`` previously had ``guild_id: int = 0`` and the
    single production caller in ``cogs/rps_tournament_cog.py`` never
    passed it — every guild's stats merged at ``(user_id, 0)`` despite
    migration 005 widening the PK to ``(user_id, guild_id)``.
  * ``rps_update_stat`` interpolated a column name into raw SQL via
    f-string.  Whitelisted today, structurally unsafe; replaced by an
    explicit ``match`` over three prepared statements.

``rps_ensure_player`` and ``rps_get_leaderboard`` shared the same
default-guild-0 bug and are tightened in this PR for parity.
"""

from __future__ import annotations

from utils.db import pool


async def rps_ensure_player(user_id: int, guild_id: int, name: str) -> None:
    await pool.execute(
        "INSERT INTO rps_players (user_id, guild_id, name) "
        "VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
        (user_id, guild_id, name),
    )


async def rps_update_stat(user_id: int, guild_id: int, result: str) -> None:
    """Increment a stat column for (user_id, guild_id).

    ``result`` is one of ``"win"``, ``"loss"``, ``"tie"``.  Any other
    value is silently a no-op so callers that hand in normalised inputs
    elsewhere don't need to re-validate.

    The three-arm ``match`` is deliberate: asyncpg caches each query
    independently and there is no dynamic identifier interpolation.
    """
    match result:
        case "win":
            query = (
                "UPDATE rps_players SET wins=wins+1 "
                "WHERE user_id=$1 AND guild_id=$2"
            )
        case "loss":
            query = (
                "UPDATE rps_players SET losses=losses+1 "
                "WHERE user_id=$1 AND guild_id=$2"
            )
        case "tie":
            query = (
                "UPDATE rps_players SET ties=ties+1 "
                "WHERE user_id=$1 AND guild_id=$2"
            )
        case _:
            return
    await pool.execute(query, (user_id, guild_id))


async def rps_get_leaderboard(guild_id: int) -> list[dict]:
    return await pool.fetchall(
        "SELECT name, wins, losses, ties FROM rps_players "
        "WHERE guild_id=$1 ORDER BY wins DESC LIMIT 15",
        (guild_id,),
    )
