"""Read-only search / filter for the BTD6 strategy memory (M4)."""

from __future__ import annotations

from typing import Any

from utils.db import btd6_strategies as db


async def get(strategy_id: int) -> dict[str, Any] | None:
    return await db.get_strategy(strategy_id)


async def list_for_guild(guild_id: int, *, limit: int = 25) -> list[dict[str, Any]]:
    return await db.search_strategies(guild_id=guild_id, limit=limit)


async def list_published(*, limit: int = 25) -> list[dict[str, Any]]:
    return await db.search_strategies(visibility="published", limit=limit)


async def search(
    *,
    guild_id: int | None = None,
    map: str | None = None,
    mode: str | None = None,
    visibility: str | None = None,
    approval_status: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    return await db.search_strategies(
        guild_id=guild_id, map=map, mode=mode,
        visibility=visibility, approval_status=approval_status,
        limit=limit,
    )


async def audit_for(strategy_id: int) -> list[dict[str, Any]]:
    return await db.list_strategy_audit(strategy_id)


__all__ = ["audit_for", "get", "list_for_guild", "list_published", "search"]
