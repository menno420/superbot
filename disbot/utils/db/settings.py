"""guild_settings KV store CRUD.

Keys are owned per :mod:`utils.settings_keys`; callers should use
constants from that module rather than raw strings to prevent typo
drift.
"""

from __future__ import annotations

from utils.db import pool


async def get_setting(guild_id: int, key: str, default: str = "") -> str:
    row = await pool.fetchone(
        "SELECT value FROM guild_settings WHERE guild_id=$1 AND key=$2",
        (guild_id, key),
    )
    return row["value"] if row else default


async def set_setting(guild_id: int, key: str, value: str) -> None:
    await pool.execute(
        """INSERT INTO guild_settings (guild_id, key, value) VALUES ($1, $2, $3)
           ON CONFLICT (guild_id, key) DO UPDATE SET value=EXCLUDED.value""",
        (guild_id, key, value),
    )
