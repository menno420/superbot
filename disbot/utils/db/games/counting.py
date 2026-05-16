"""counting_state JSONB blob CRUD (one row per guild)."""

from __future__ import annotations

from utils.db import pool


async def get_counting_state(guild_id: int) -> dict:
    row = await pool.fetchone(
        "SELECT state FROM counting_state WHERE guild_id=$1",
        (guild_id,),
    )
    return row["state"] if row else {}


async def set_counting_state(guild_id: int, state: dict) -> None:
    await pool.execute(
        """INSERT INTO counting_state (guild_id, state) VALUES ($1, $2::jsonb)
           ON CONFLICT (guild_id) DO UPDATE SET state=EXCLUDED.state""",
        (guild_id, state),
    )
