"""Help-overlay DB primitives (HLP-3 — migration 064).

Guild-scoped presentation overrides for Help (display-hide / rename /
re-describe per hub or subsystem). **Sole writer for the ``help_overlay``
table** — every write goes through :mod:`services.help_overlay_mutation`
(the audited seam), which calls these primitives; reads go through
:mod:`services.help_overlay`'s cached read model.

Pure storage: no validation beyond the schema (the mutation service owns
catalogue-key validation, bounds, and audit), no caching (the service owns
the per-guild cache + invalidation).
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.help_overlay")


async def get_guild_rows(guild_id: int) -> list[dict[str, Any]]:
    """All overlay rows for ``guild_id`` (empty list = no deviations)."""
    rows = await pool.get().fetch(
        """
        SELECT entity_kind, entity_key, display_hidden, display_name,
               description, updated_by, updated_at
          FROM help_overlay
         WHERE guild_id = $1
        """,
        guild_id,
    )
    return [dict(r) for r in rows]


async def get_row(
    guild_id: int,
    entity_kind: str,
    entity_key: str,
) -> dict[str, Any] | None:
    """One overlay row, or ``None`` when the entity inherits defaults."""
    row = await pool.get().fetchrow(
        """
        SELECT entity_kind, entity_key, display_hidden, display_name,
               description, updated_by, updated_at
          FROM help_overlay
         WHERE guild_id = $1 AND entity_kind = $2 AND entity_key = $3
        """,
        guild_id,
        entity_kind,
        entity_key,
    )
    return dict(row) if row else None


async def upsert_row(
    guild_id: int,
    entity_kind: str,
    entity_key: str,
    *,
    display_hidden: bool | None,
    display_name: str | None,
    description: str | None,
    updated_by: int | None,
) -> None:
    """Write the full override state for one entity (NULL field = inherit).

    The caller (the mutation service) merges partial edits into the full
    field set first and never calls this with an all-NULL override — it
    calls :func:`delete_row` instead ("store only deviations").
    """
    await pool.get().execute(
        """
        INSERT INTO help_overlay
            (guild_id, entity_kind, entity_key,
             display_hidden, display_name, description, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (guild_id, entity_kind, entity_key) DO UPDATE
           SET display_hidden = EXCLUDED.display_hidden,
               display_name   = EXCLUDED.display_name,
               description    = EXCLUDED.description,
               updated_by     = EXCLUDED.updated_by,
               updated_at     = now()
        """,
        guild_id,
        entity_kind,
        entity_key,
        display_hidden,
        display_name,
        description,
        updated_by,
    )


async def delete_row(guild_id: int, entity_kind: str, entity_key: str) -> bool:
    """Remove one entity's override row. Returns ``True`` if a row existed."""
    status = await pool.get().execute(
        """
        DELETE FROM help_overlay
         WHERE guild_id = $1 AND entity_kind = $2 AND entity_key = $3
        """,
        guild_id,
        entity_kind,
        entity_key,
    )
    return status == "DELETE 1"


async def delete_guild_rows(guild_id: int) -> int:
    """Full reset: remove every overlay row for ``guild_id``. Returns count."""
    status = await pool.get().execute(
        "DELETE FROM help_overlay WHERE guild_id = $1",
        guild_id,
    )
    try:
        return int(status.rsplit(" ", 1)[-1])
    except (ValueError, AttributeError):  # pragma: no cover — asyncpg contract
        return 0


__all__ = [
    "delete_guild_rows",
    "delete_row",
    "get_guild_rows",
    "get_row",
    "upsert_row",
]
