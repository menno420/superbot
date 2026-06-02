"""DB access for the BTD6 deterministic-data blob store (``btd6_data_blobs``).

Backs ``services.btd6_data_provider.PostgresRawProvider``: a static reference
blob store (fixtures + the per-entity stats tree) keyed by repo-relative path.
The bot already hard-depends on Postgres, so serving BTD6 reference data from
the same DB adds no new external dependency or failure mode.

Writes here are seed/refresh operations for operator-controlled reference data
(not an audited domain mutation), driven by ``scripts/seed_btd6_data.py``.
"""

from __future__ import annotations

from typing import Any

from utils.db import pool


async def fetch_all_blobs() -> list[tuple[str, Any]]:
    """Return ``(name, body)`` for every stored blob in one query.

    ``body`` is whatever the jsonb codec yields (a dict); the provider
    coerces defensively in case a row round-trips as text.
    """
    rows = await pool.get().fetch(
        "SELECT name, body FROM btd6_data_blobs ORDER BY name",
    )
    return [(row["name"], row["body"]) for row in rows]


async def fetch_blob(name: str) -> Any | None:
    """Return one blob's body, or ``None`` when absent."""
    row = await pool.get().fetchrow(
        "SELECT body FROM btd6_data_blobs WHERE name = $1",
        name,
    )
    return row["body"] if row is not None else None


async def count_blobs() -> int:
    """Number of stored blobs (0 when the table is unseeded)."""
    row = await pool.get().fetchrow("SELECT COUNT(*) AS n FROM btd6_data_blobs")
    return int(row["n"]) if row is not None else 0


async def upsert_blob(name: str, body: Any, sha256: str | None = None) -> None:
    """Insert or update one blob. ``body`` is a JSON-serialisable object."""
    await pool.get().execute(
        """
        INSERT INTO btd6_data_blobs (name, body, sha256, updated_at)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (name) DO UPDATE
           SET body = EXCLUDED.body,
               sha256 = EXCLUDED.sha256,
               updated_at = NOW()
        """,
        name,
        body,
        sha256,
    )
