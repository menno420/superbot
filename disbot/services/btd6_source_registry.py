"""Read-only access to ``btd6_source_registry`` (M3A + PR-D).

Writes flow through :mod:`services.btd6_source_mutation`. This
module exists so callers (the fetcher, the knowledge API, the
``!btd6 sources`` command, the PR-D source-health view) can ask
"is this source allowlisted?" and "is this source fresh?" without
touching the DB module directly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from utils.db import btd6_sources as btd6_db

logger = logging.getLogger("bot.services.btd6_source_registry")


# ---------------------------------------------------------------------------
# Freshness bucketing (PR-D)
# ---------------------------------------------------------------------------


FreshnessBucket = Literal["fresh", "aging", "stale", "never"]


# Buckets are deliberately coarse: the operator needs an at-a-glance
# answer, not a precise SLO. Adjust if production observation shows
# the Ninja Kiwi cadences want a different threshold.
_FRESH_THRESHOLD = timedelta(hours=6)
_AGING_THRESHOLD = timedelta(days=2)


def bucket_freshness(last_fetched_at: datetime | None) -> FreshnessBucket:
    """Public freshness bucketing helper.

    Single source of truth for the fresh/aging/stale/never buckets.
    Source-health (per source key) and the BTD6 fact summary (per
    entity_kind) both depend on this — do not duplicate thresholds
    elsewhere.

    Naive datetimes are interpreted as UTC.
    """
    if last_fetched_at is None:
        return "never"
    if last_fetched_at.tzinfo is None:
        last_fetched_at = last_fetched_at.replace(tzinfo=timezone.utc)
    age = datetime.now(tz=timezone.utc) - last_fetched_at
    if age <= _FRESH_THRESHOLD:
        return "fresh"
    if age <= _AGING_THRESHOLD:
        return "aging"
    return "stale"


# Internal alias kept for any in-module readers; new code should call
# ``bucket_freshness`` directly.
_bucket_for = bucket_freshness


@dataclass(frozen=True)
class SourceHealth:
    """One source row enriched with freshness info."""

    source_id: int
    source_key: str
    source_name: str
    trust_tier: int
    enabled: bool
    source_kind: str
    last_fetched_at: datetime | None
    fact_count: int
    bucket: FreshnessBucket


async def list_health(
    *,
    enabled: bool | None = None,
    limit: int = 25,
    offset: int = 0,
) -> list[SourceHealth]:
    """Bounded list of source-health summaries (PR-D).

    The hard cap mirrors :func:`utils.db.btd6_sources.list_sources` —
    no caller can fetch the entire registry in one call.
    """
    rows = await btd6_db.list_sources_with_freshness(
        enabled=enabled,
        limit=limit,
        offset=offset,
    )
    out: list[SourceHealth] = []
    for row in rows:
        out.append(
            SourceHealth(
                source_id=int(row["id"]),
                source_key=row["source_key"],
                source_name=row["source_name"],
                trust_tier=int(row["trust_tier"]),
                enabled=bool(row["enabled"]),
                source_kind=row["source_kind"],
                last_fetched_at=row.get("last_fetched_at"),
                fact_count=int(row.get("fact_count") or 0),
                bucket=_bucket_for(row.get("last_fetched_at")),
            ),
        )
    return out


async def get_by_key(source_key: str) -> dict[str, Any] | None:
    return await btd6_db.get_source_by_key(source_key)


async def get_by_id(source_id: int) -> dict[str, Any] | None:
    return await btd6_db.get_source(source_id)


async def list_enabled_sources(
    *,
    trust_tier: int | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return await btd6_db.list_sources(
        trust_tier=trust_tier,
        enabled=True,
        limit=limit,
    )


async def list_by_tier(trust_tier: int, *, limit: int = 100) -> list[dict[str, Any]]:
    return await btd6_db.list_sources(trust_tier=trust_tier, limit=limit)


async def list_all(*, limit: int = 100) -> list[dict[str, Any]]:
    return await btd6_db.list_sources(limit=limit)


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
    "FreshnessBucket",
    "SourceHealth",
    "bucket_freshness",
    "get_by_id",
    "get_by_key",
    "is_source_usable",
    "list_all",
    "list_by_tier",
    "list_enabled_sources",
    "list_health",
]
