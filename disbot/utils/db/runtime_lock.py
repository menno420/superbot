"""Runtime instance lock — DB primitives.

Owns the read/write surface for the ``bot_runtime_lock`` table created
by migration 034. Higher-level callers (``services.runtime`` and
``bot1.main``) wrap these primitives; nothing outside this module + the
service issues raw SQL against ``bot_runtime_lock``.

Ownership model
---------------
The ``bot_runtime_lock`` row is the authoritative ownership signal.
A live holder bumps ``heartbeat_at`` every 30 s via :func:`heartbeat`;
a row whose ``heartbeat_at`` is older than ``stale_after_seconds``
(default 90 s) is treated as orphaned and can be reclaimed by the next
boot.

``pg_try_advisory_lock`` is used ONLY as a brief mutex around the
check-then-upsert window inside :func:`try_acquire`, so two replicas
that race during boot cannot both decide a stale row is theirs. The
advisory lock is released before the call returns; long-lived ownership
is entirely in the row.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.runtime_lock")

# Stable 64-bit key for pg_advisory_lock — distinct from the migration
# lock key at ``utils.db.migrations._MIGRATION_ADVISORY_LOCK`` (which is
# 0x73757065_72626F74 = "superbot" ASCII).
# Encodes the ASCII "RUNLOCK\0" interpreted as int64.
_RUNTIME_ADVISORY_LOCK_KEY: int = 0x52554E4C_4F434B00

DEFAULT_LOCK_NAME: str = "discord_bot"
DEFAULT_STALE_AFTER_SECONDS: int = 90


@dataclass(frozen=True)
class AcquireResult:
    """Outcome of :func:`try_acquire`."""

    acquired: bool
    holder_boot_id: uuid.UUID | None
    holder_heartbeat_at: Any | None
    reason: str


async def get_holder(lock_name: str = DEFAULT_LOCK_NAME) -> dict[str, Any] | None:
    """Return the current ``bot_runtime_lock`` row, or ``None`` if absent."""
    row = await pool.get().fetchrow(
        """
        SELECT lock_name, boot_id, acquired_at, heartbeat_at
        FROM bot_runtime_lock
        WHERE lock_name = $1
        """,
        lock_name,
    )
    if row is None:
        return None
    return dict(row)


async def try_acquire(
    boot_id: uuid.UUID,
    *,
    lock_name: str = DEFAULT_LOCK_NAME,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> AcquireResult:
    """Attempt to claim the runtime lock for ``boot_id``.

    Sequence (all inside one asyncpg connection so the advisory lock
    scope is the same as the check + upsert):

      1. ``pg_advisory_lock`` — blocking; brief contention window only.
      2. Read the current ``bot_runtime_lock`` row.
      3. If a fresh row exists (``heartbeat_at`` within
         ``stale_after_seconds``) and belongs to a different boot,
         return ``acquired=False`` so the caller can log who holds it
         and exit cleanly.
      4. Otherwise UPSERT the row with the new ``boot_id`` and return
         ``acquired=True``.
      5. ``pg_advisory_unlock`` (always, even on the early-return
         path).
    """
    p = pool.get()
    async with p.acquire() as conn:
        # Brief mutex — blocking acquire so concurrent boots line up.
        await conn.execute(
            "SELECT pg_advisory_lock($1)",
            _RUNTIME_ADVISORY_LOCK_KEY,
        )
        try:
            existing = await conn.fetchrow(
                """
                SELECT boot_id, heartbeat_at,
                       EXTRACT(EPOCH FROM (NOW() - heartbeat_at)) AS age_seconds
                FROM bot_runtime_lock
                WHERE lock_name = $1
                """,
                lock_name,
            )
            if existing is not None:
                age = existing["age_seconds"]
                existing_boot = existing["boot_id"]
                if (
                    existing_boot != boot_id
                    and age is not None
                    and age < stale_after_seconds
                ):
                    return AcquireResult(
                        acquired=False,
                        holder_boot_id=existing_boot,
                        holder_heartbeat_at=existing["heartbeat_at"],
                        reason="row_fresh",
                    )

            await conn.execute(
                """
                INSERT INTO bot_runtime_lock (
                    lock_name, boot_id, acquired_at, heartbeat_at
                )
                VALUES ($1, $2, NOW(), NOW())
                ON CONFLICT (lock_name) DO UPDATE SET
                    boot_id      = EXCLUDED.boot_id,
                    acquired_at  = NOW(),
                    heartbeat_at = NOW()
                """,
                lock_name,
                boot_id,
            )
            return AcquireResult(
                acquired=True,
                holder_boot_id=boot_id,
                holder_heartbeat_at=None,
                reason="acquired",
            )
        finally:
            await conn.execute(
                "SELECT pg_advisory_unlock($1)",
                _RUNTIME_ADVISORY_LOCK_KEY,
            )


async def heartbeat(
    boot_id: uuid.UUID,
    *,
    lock_name: str = DEFAULT_LOCK_NAME,
) -> bool:
    """Refresh ``heartbeat_at`` for the row owned by ``boot_id``.

    Returns ``True`` when one row was updated, ``False`` otherwise.
    ``False`` means the lock was stolen / cleared — the caller should
    treat that as fatal for the current process.
    """
    result = await pool.get().execute(
        """
        UPDATE bot_runtime_lock
           SET heartbeat_at = NOW()
         WHERE lock_name = $1
           AND boot_id   = $2
        """,
        lock_name,
        boot_id,
    )
    # asyncpg returns the tag string e.g. "UPDATE 1"; parse the count.
    try:
        count = int(result.rsplit(" ", 1)[-1])
    except (ValueError, AttributeError):
        count = 0
    return count == 1


async def release(
    boot_id: uuid.UUID,
    *,
    lock_name: str = DEFAULT_LOCK_NAME,
) -> None:
    """Release the lock owned by ``boot_id`` (best effort).

    Clears the ``bot_runtime_lock`` row only when ``boot_id`` still owns
    it — never clobbers another holder's row.
    """
    await pool.get().execute(
        """
        DELETE FROM bot_runtime_lock
         WHERE lock_name = $1
           AND boot_id   = $2
        """,
        lock_name,
        boot_id,
    )


__all__ = [
    "DEFAULT_LOCK_NAME",
    "DEFAULT_STALE_AFTER_SECONDS",
    "AcquireResult",
    "get_holder",
    "heartbeat",
    "release",
    "try_acquire",
]
