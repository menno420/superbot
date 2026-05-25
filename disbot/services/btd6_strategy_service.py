"""Read-only search / filter for the BTD6 strategy memory.

PR-F surfaces the existing service to additional UX paths (browse /
detail / submit / mine / audit). The write path stays in
:mod:`services.btd6_strategy_mutation` — this module is read-only.
"""

from __future__ import annotations

from typing import Any

from utils.db import btd6_strategies as db


# Hard caps for every list query so callers cannot accidentally
# fetch the whole table.
_MAX_LIMIT = 25


def _clamp_limit(limit: int) -> int:
    return max(1, min(int(limit), _MAX_LIMIT))


async def get(strategy_id: int) -> dict[str, Any] | None:
    return await db.get_strategy(strategy_id)


async def list_for_guild(guild_id: int, *, limit: int = 25) -> list[dict[str, Any]]:
    return await db.search_strategies(
        guild_id=guild_id,
        limit=_clamp_limit(limit),
    )


async def list_published(*, limit: int = 25) -> list[dict[str, Any]]:
    return await db.search_strategies(
        visibility="published",
        limit=_clamp_limit(limit),
    )


async def list_mine(
    guild_id: int,
    submitter_id: int,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """PR-F: rows submitted by ``submitter_id`` in ``guild_id``.

    Filtered in Python (no SQL change). Bounded by ``_MAX_LIMIT``.
    """
    rows = await db.search_strategies(
        guild_id=guild_id,
        limit=_MAX_LIMIT,
    )
    mine = [r for r in rows if r.get("submitted_by") == submitter_id]
    return mine[: _clamp_limit(limit)]


async def search(
    *,
    guild_id: int | None = None,
    map_name: str | None = None,
    mode: str | None = None,
    visibility: str | None = None,
    approval_status: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    return await db.search_strategies(
        guild_id=guild_id,
        map_name=map_name,
        mode=mode,
        visibility=visibility,
        approval_status=approval_status,
        limit=_clamp_limit(limit),
    )


async def audit_for(strategy_id: int) -> list[dict[str, Any]]:
    return await db.list_strategy_audit(strategy_id)


__all__ = [
    "audit_for",
    "get",
    "list_for_guild",
    "list_mine",
    "list_published",
    "search",
]
