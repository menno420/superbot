"""chain_channels CRUD."""

from __future__ import annotations

from utils.db import pool


async def get_chain_channel(channel_id: int) -> dict | None:
    return await pool.fetchone(
        "SELECT word, word_limit, chain_count FROM chain_channels WHERE channel_id=$1",
        (channel_id,),
    )


async def set_chain_channel(
    channel_id: int,
    guild_id: int,
    word: str,
    limit: int = 0,
) -> None:
    await pool.execute(
        """INSERT INTO chain_channels
               (channel_id, guild_id, word, word_limit, chain_count)
           VALUES ($1, $2, $3, $4, 0)
           ON CONFLICT (channel_id) DO UPDATE
             SET word=EXCLUDED.word, word_limit=EXCLUDED.word_limit""",
        (channel_id, guild_id, word, limit),
    )


async def delete_chain_channel(channel_id: int) -> None:
    await pool.execute(
        "DELETE FROM chain_channels WHERE channel_id=$1",
        (channel_id,),
    )


async def set_chain_limit(channel_id: int, limit: int) -> None:
    await pool.execute(
        "UPDATE chain_channels SET word_limit=$1 WHERE channel_id=$2",
        (limit, channel_id),
    )


async def increment_chain_count(channel_id: int) -> int:
    row = await pool.fetchone(
        "UPDATE chain_channels SET chain_count=chain_count+1 "
        "WHERE channel_id=$1 RETURNING chain_count",
        (channel_id,),
    )
    return row["chain_count"] if row else 0


async def get_all_chain_channels(guild_id: int) -> list[dict]:
    return await pool.fetchall(
        "SELECT channel_id, word, word_limit, chain_count "
        "FROM chain_channels WHERE guild_id=$1",
        (guild_id,),
    )
