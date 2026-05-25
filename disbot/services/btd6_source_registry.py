"""Read-only access to ``btd6_source_registry`` (M3A).

Writes flow through :mod:`services.btd6_source_mutation`. This
module exists so callers (the fetcher, the knowledge API, the
``!btd6 sources`` command) can ask "is this source allowlisted?"
without touching the DB module directly.
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import btd6_sources as btd6_db

logger = logging.getLogger("bot.services.btd6_source_registry")


async def get_by_key(source_key: str) -> dict[str, Any] | None:
    return await btd6_db.get_source_by_key(source_key)


async def get_by_id(source_id: int) -> dict[str, Any] | None:
    return await btd6_db.get_source(source_id)


async def list_enabled_sources(
    *,
    trust_tier: int | None = None,
) -> list[dict[str, Any]]:
    return await btd6_db.list_sources(trust_tier=trust_tier, enabled=True)


async def list_by_tier(trust_tier: int) -> list[dict[str, Any]]:
    return await btd6_db.list_sources(trust_tier=trust_tier)


async def list_all() -> list[dict[str, Any]]:
    return await btd6_db.list_sources()


async def is_source_usable(source_key: str) -> tuple[bool, str]:
    """Return ``(usable, reason)`` for a source key.

    A source is usable when the row exists, has ``enabled=TRUE``, and
    has a non-null ``base_url``. The reason string is stable enough
    to feed into the audit row when a fetcher refuses a request.
    """
    row = await btd6_db.get_source_by_key(source_key)
    if row is None:
        return False, "source_not_registered"
    if not row.get("enabled"):
        return False, "source_disabled"
    if not row.get("base_url"):
        return False, "source_missing_base_url"
    return True, "ok"


__all__ = [
    "get_by_id",
    "get_by_key",
    "is_source_usable",
    "list_all",
    "list_by_tier",
    "list_enabled_sources",
]
