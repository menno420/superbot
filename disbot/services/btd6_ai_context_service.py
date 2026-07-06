"""AI-safe read-only facade over the BTD6 data layer.

A single, narrow surface that the AI cog (and any future AI feature)
can call to fetch live BTD6 context without learning the underlying
storage schema, joining tables, or calling private helpers in other
services.

Design constraints (enforced by tests):

* **Read-only.** No DB writes, no HTTP fetches.
* **No view / cog imports.** Architecture layering rules.
* **No reach into other services' privates.** Restrictions go through
  the public :func:`services.btd6_live_query_service.get_all_active_restrictions`;
  freshness goes through :func:`services.btd6_source_registry.bucket_freshness`.
* **Public-safe by default.** :func:`get_source_status` drops every
  internal-id, URL, hash, and actor field unless ``public_safe=False``.
* **Defensive.** Every method catches exceptions, logs with the method
  name + key arg values, and returns ``()`` / ``None`` rather than
  propagating into the AI stage.

Every returned dataclass carries a ``render()`` method that produces a
single line bounded by :data:`utils.btd6.grounding_format.DEFAULT_CAP`
characters, with provenance suffix always preserved. Renderers are
sync, format-only, and never inspect DB / API objects.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from services import (
    btd6_knowledge_api,
    btd6_live_query_service,
    btd6_source_registry,
)
from services.btd6_source_registry import FreshnessBucket
from utils.btd6.grounding_format import render_grounding_line, sanitise

logger = logging.getLogger("bot.services.btd6_ai_context")


# ---------------------------------------------------------------------------
# Typed contracts
# ---------------------------------------------------------------------------


EventEntityKind = Literal[
    "btd6_race",
    "btd6_boss",
    "btd6_ct",
    "btd6_odyssey",
    "btd6_event",
    "btd6_challenge",
]


# The set of index entity_kinds that `get_active_events` exposes. We
# accept any string at the call site (the type hint is the contract);
# this set is for the round-trip pin test in PR-1.
_EVENT_ENTITY_KINDS: frozenset[str] = frozenset(
    {
        "btd6_race",
        "btd6_boss",
        "btd6_ct",
        "btd6_odyssey",
        "btd6_event",
        "btd6_challenge",
    },
)


# URL keys we strip from FactBundle bodies before composing summaries —
# bare links inside grounding lines can encourage the LLM to follow them.
_URL_BODY_KEYS: frozenset[str] = frozenset(
    {
        "creator_url",
        "profile_url",
        "metadata_url",
        "map_url",
        "boss_type_url",
        "leaderboard_url",
        "leaderboard_standard_url",
        "leaderboard_elite_url",
        "url",
    },
)

_SEARCH_LIMIT_CAP = 10


def _strip_url_keys(body: dict[str, Any]) -> dict[str, Any]:
    return {
        k: v
        for k, v in body.items()
        if k not in _URL_BODY_KEYS and not k.endswith("_url")
    }


# ---------------------------------------------------------------------------
# Summary dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActiveEventSummary:
    """One currently-active live event (PR-E live entity kinds)."""

    entity_kind: str
    entity_key: str
    name: str
    start_ms: int | None
    end_ms: int | None
    fetched_at: datetime | None
    freshness: FreshnessBucket
    source_name: str

    def render(self) -> str:
        kind_label = _EVENT_KIND_LABEL.get(self.entity_kind, "event")
        body = f"{kind_label}: {self.name or self.entity_key}"
        return render_grounding_line(
            body,
            source_name=self.source_name,
            fetched_at=self.fetched_at,
        )


@dataclass(frozen=True)
class EventDetailsSummary:
    """One event's index row, reshaped for the AI surface."""

    entity_kind: str
    entity_key: str
    name: str
    start_ms: int | None
    end_ms: int | None
    fetched_at: datetime | None
    freshness: FreshnessBucket
    source_name: str

    def render(self) -> str:
        kind_label = _EVENT_KIND_LABEL.get(self.entity_kind, "event")
        body = f"{kind_label} '{self.name or self.entity_key}'"
        return render_grounding_line(
            body,
            source_name=self.source_name,
            fetched_at=self.fetched_at,
        )


@dataclass(frozen=True)
class EntitySummary:
    """A tower / hero summary keyed by id."""

    entity_kind: str
    entity_id: str
    name: str
    body: dict[str, Any]
    source_name: str
    fetched_at: datetime | None
    freshness: str

    def render(self) -> str:
        line = f"{self.entity_kind} {self.name or self.entity_id}"
        return render_grounding_line(
            line,
            source_name=self.source_name,
            fetched_at=self.fetched_at,
        )


@dataclass(frozen=True)
class RestrictionSummary:
    """One active-event restriction on one tower or hero."""

    entity_id: str
    is_hero: bool
    event_kind: str
    event_name: str
    stance: Literal["banned", "limited", "path_blocked", "allowed"]
    max_count: int | None
    fetched_at: datetime | None
    source_name: str
    sentinel_all_heroes_banned: bool

    def render(self) -> str:
        kind_label = _EVENT_KIND_LABEL.get(self.event_kind, "event")
        target = "hero" if self.is_hero else "tower"
        name = sanitise(self.entity_id) or "(unknown)"
        event_name = sanitise(self.event_name) or "(unknown event)"
        if self.sentinel_all_heroes_banned:
            body = f"All heroes are banned in {kind_label} '{event_name}'"
        elif self.stance == "banned":
            body = f"{target} {name} is banned in {kind_label} '{event_name}'"
        elif self.stance == "limited":
            body = (
                f"{target} {name} is limited (max {self.max_count}) in "
                f"{kind_label} '{event_name}'"
            )
        elif self.stance == "path_blocked":
            body = (
                f"{target} {name} has path tiers blocked in {kind_label} '{event_name}'"
            )
        else:  # "allowed" should be filtered upstream, but render defensively.
            body = f"{target} {name} is allowed in {kind_label} '{event_name}'"
        return render_grounding_line(
            body,
            source_name=self.source_name,
            fetched_at=self.fetched_at,
        )


@dataclass(frozen=True)
class LeaderboardEntry:
    """One row on a public leaderboard summary (no profile URL)."""

    rank: int
    display_name: str
    score: int | None
    submission_time_ms: int | None


@dataclass(frozen=True)
class LeaderboardSummary:
    """Top-N leaderboard rows for one event."""

    event_kind: str
    event_id: str
    entries: tuple[LeaderboardEntry, ...]
    fetched_at: datetime | None
    source_name: str

    def render(self) -> str:
        kind_label = _EVENT_KIND_LABEL.get(self.event_kind, "event")
        head = f"{kind_label} {self.event_id} leaderboard top {len(self.entries)}"
        return render_grounding_line(
            head,
            source_name=self.source_name,
            fetched_at=self.fetched_at,
        )


@dataclass(frozen=True)
class SourceStatusSummary:
    """One BTD6 source's public-safe health snapshot.

    Public-safe by construction: no base_url, no path_template, no
    hashes, no created_by/updated_by. The facade enforces this via
    :func:`get_source_status` — there is no public-safe shape for URLs.
    """

    source_key: str
    source_name: str
    trust_tier: int
    enabled: bool
    last_fetched_at: datetime | None
    fact_count: int
    freshness: FreshnessBucket

    def render(self) -> str:
        bits = [
            self.freshness,
            f"{self.fact_count} facts",
            "enabled" if self.enabled else "disabled",
            f"source: {self.source_key}",
        ]
        body = f"{self.source_name}: " + ", ".join(bits)
        return render_grounding_line(
            body,
            source_name=self.source_key,
            fetched_at=self.last_fetched_at,
        )


@dataclass(frozen=True)
class FactSummary:
    """One row from :func:`search_btd6_facts`."""

    fact_type: str
    entity_kind: str
    entity_key: str
    body: dict[str, Any]
    source_name: str
    fetched_at: datetime | None
    freshness: str

    def render(self) -> str:
        head = self.body.get("name") or self.body.get("display_name") or self.entity_key
        body = f"{self.entity_kind}/{self.fact_type}: {head}"
        return render_grounding_line(
            body,
            source_name=self.source_name,
            fetched_at=self.fetched_at,
        )


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


_EVENT_KIND_LABEL: dict[str, str] = {
    "btd6_race": "race",
    "btd6_boss": "boss event",
    "btd6_boss_difficulty": "boss",
    "btd6_ct": "contested territory",
    "btd6_odyssey": "odyssey",
    "btd6_odyssey_difficulty": "odyssey",
    "btd6_event": "event",
    "btd6_challenge": "challenge",
}


# ---------------------------------------------------------------------------
# Public methods
# ---------------------------------------------------------------------------


async def get_current_events() -> tuple[ActiveEventSummary, ...]:
    """All currently-active events across known kinds, newest-fetched first."""
    try:
        headlines = await btd6_live_query_service.get_active_events()
    except Exception:
        logger.exception(
            "btd6_ai_context_service.get_current_events failed; "
            "returning no AI context",
            extra={"method": "get_current_events"},
        )
        return ()
    out: list[ActiveEventSummary] = []
    for h in headlines:
        out.append(
            ActiveEventSummary(
                entity_kind=h.entity_kind,
                entity_key=h.entity_key,
                name=h.name,
                start_ms=h.start_ms,
                end_ms=h.end_ms,
                fetched_at=h.fetched_at,
                freshness=btd6_source_registry.bucket_freshness(h.fetched_at),
                source_name="data.ninjakiwi.com",
            ),
        )
    return tuple(out)


async def get_event_details(
    entity_kind: EventEntityKind,
    entity_key: str,
) -> EventDetailsSummary | None:
    """Look up the index row for one specific event.

    ``entity_kind`` and ``entity_key`` are the same fields exposed by
    :class:`ActiveEventSummary`, so callers can chain
    ``get_current_events() → get_event_details(...)`` directly.
    """
    try:
        headlines = await btd6_live_query_service.get_active_events((entity_kind,))
    except Exception:
        logger.exception(
            "btd6_ai_context_service.get_event_details failed; returning no AI context",
            extra={
                "method": "get_event_details",
                "entity_kind": entity_kind,
                "entity_key": entity_key,
            },
        )
        return None
    for h in headlines:
        if h.entity_key == entity_key:
            return EventDetailsSummary(
                entity_kind=h.entity_kind,
                entity_key=h.entity_key,
                name=h.name,
                start_ms=h.start_ms,
                end_ms=h.end_ms,
                fetched_at=h.fetched_at,
                freshness=btd6_source_registry.bucket_freshness(h.fetched_at),
                source_name="data.ninjakiwi.com",
            )
    return None


async def get_tower_summary(tower_id: str) -> EntitySummary | None:
    """Tower summary (name + body, URLs stripped)."""
    try:
        bundle = await btd6_knowledge_api.get_tower(tower_id)
    except Exception:
        logger.exception(
            "btd6_ai_context_service.get_tower_summary failed; returning no AI context",
            extra={"method": "get_tower_summary", "tower_id": tower_id},
        )
        return None
    if bundle is None:
        return None
    body = _strip_url_keys(bundle.body)
    return EntitySummary(
        entity_kind="tower",
        entity_id=tower_id,
        name=str(body.get("name") or tower_id),
        body=body,
        source_name=bundle.source_key or "data.ninjakiwi.com",
        fetched_at=bundle.fetched_at,
        freshness=bundle.freshness_status,
    )


async def get_hero_summary(hero_id: str) -> EntitySummary | None:
    """Hero summary (name + body, URLs stripped)."""
    try:
        bundle = await btd6_knowledge_api.get_hero(hero_id)
    except Exception:
        logger.exception(
            "btd6_ai_context_service.get_hero_summary failed; returning no AI context",
            extra={"method": "get_hero_summary", "hero_id": hero_id},
        )
        return None
    if bundle is None:
        return None
    body = _strip_url_keys(bundle.body)
    return EntitySummary(
        entity_kind="hero",
        entity_id=hero_id,
        name=str(body.get("name") or hero_id),
        body=body,
        source_name=bundle.source_key or "data.ninjakiwi.com",
        fetched_at=bundle.fetched_at,
        freshness=bundle.freshness_status,
    )


async def get_active_restrictions(
    scope: Literal["all", "towers", "heroes"] = "all",
    *,
    max_rows: int = 24,
) -> tuple[RestrictionSummary, ...]:
    """Active-event restrictions, optionally scoped to towers or heroes."""
    include_towers = scope in ("all", "towers")
    include_heroes = scope in ("all", "heroes")
    try:
        broad = await btd6_live_query_service.get_all_active_restrictions(
            include_towers=include_towers,
            include_heroes=include_heroes,
            max_rows=max_rows,
        )
    except Exception:
        logger.exception(
            "btd6_ai_context_service.get_active_restrictions failed; "
            "returning no AI context",
            extra={"method": "get_active_restrictions", "scope": scope},
        )
        return ()
    return tuple(
        RestrictionSummary(
            entity_id=r.entity_id,
            is_hero=r.is_hero,
            event_kind=r.event_kind,
            event_name=r.event_name,
            stance=r.stance,
            max_count=r.max_count,
            fetched_at=r.fetched_at,
            source_name="data.ninjakiwi.com",
            sentinel_all_heroes_banned=r.sentinel_all_heroes_banned,
        )
        for r in broad
    )


async def get_leaderboard_summary(
    event_kind: EventEntityKind,
    event_id: str,
    *,
    limit: int = 5,
) -> LeaderboardSummary | None:
    """Top-N leaderboard rows for one race or boss. Profile URLs dropped."""
    clamped = max(1, min(10, int(limit)))
    try:
        if event_kind == "btd6_race":
            rows = await btd6_live_query_service.get_race_leaderboard(
                event_id,
                limit=clamped,
            )
        elif event_kind == "btd6_boss":
            rows = await btd6_live_query_service.get_boss_leaderboard(
                event_id,
                limit=clamped,
            )
        else:
            return None
    except Exception:
        logger.exception(
            "btd6_ai_context_service.get_leaderboard_summary failed; "
            "returning no AI context",
            extra={
                "method": "get_leaderboard_summary",
                "event_kind": event_kind,
                "event_id": event_id,
            },
        )
        return None
    if not rows:
        return None
    entries = tuple(
        LeaderboardEntry(
            rank=r.rank,
            display_name=r.display_name,
            score=r.score,
            submission_time_ms=r.submission_time_ms,
        )
        for r in rows
    )
    newest_fetched_at = None  # leaderboard rows don't expose fetched_at directly
    return LeaderboardSummary(
        event_kind=event_kind,
        event_id=event_id,
        entries=entries,
        fetched_at=newest_fetched_at,
        source_name="data.ninjakiwi.com",
    )


async def get_source_status(
    *,
    public_safe: bool = True,
    limit: int = 25,
) -> tuple[SourceStatusSummary, ...]:
    """Per-source freshness + fact-count snapshot for the AI surface.

    ``public_safe=True`` is the default and the only shape PR-1 / PR-2
    actually use. The flag is reserved so a future staff diagnostics
    caller can opt into URLs and actor fields via a sibling
    ``SourceStatusInternal`` shape — not added yet to keep the surface
    minimal.
    """
    if not public_safe:
        # Reserved for future staff use; do not return internal fields
        # until a separate dataclass exists for them.
        logger.warning(
            "btd6_ai_context_service.get_source_status called with "
            "public_safe=False; returning public-safe shape anyway",
            extra={"method": "get_source_status"},
        )
    try:
        rows = await btd6_source_registry.list_health(limit=max(1, min(100, limit)))
    except Exception:
        logger.exception(
            "btd6_ai_context_service.get_source_status failed; returning no AI context",
            extra={"method": "get_source_status", "public_safe": public_safe},
        )
        return ()
    return tuple(
        SourceStatusSummary(
            source_key=row.source_key,
            source_name=row.source_name,
            trust_tier=row.trust_tier,
            enabled=row.enabled,
            last_fetched_at=row.last_fetched_at,
            fact_count=row.fact_count,
            freshness=row.bucket,
        )
        for row in rows
    )


async def search_btd6_facts(
    query: str,
    *,
    fact_type: str | None = None,
    entity_kind: str | None = None,
    limit: int = 5,
) -> tuple[FactSummary, ...]:
    """Search facts by fact_type / entity_kind. Hard cap at 10."""
    clamped = max(1, min(_SEARCH_LIMIT_CAP, int(limit)))
    try:
        bundles = await btd6_knowledge_api.search_facts(
            fact_type=fact_type,
            entity_kind=entity_kind,
            limit=clamped,
        )
    except Exception:
        logger.exception(
            "btd6_ai_context_service.search_btd6_facts failed; returning no AI context",
            extra={
                "method": "search_btd6_facts",
                "query": query,
                "fact_type": fact_type,
                "entity_kind": entity_kind,
            },
        )
        return ()
    if not bundles:
        return ()
    lowered = (query or "").strip().lower()
    out: list[FactSummary] = []
    for bundle in bundles:
        body = _strip_url_keys(bundle.body)
        if lowered:
            hay = " ".join(
                str(v)
                for v in (
                    bundle.entity_key,
                    body.get("name"),
                    body.get("display_name"),
                )
                if v
            ).lower()
            if lowered not in hay:
                continue
        out.append(
            FactSummary(
                fact_type=bundle.fact_type,
                entity_kind=bundle.entity_kind,
                entity_key=bundle.entity_key,
                body=body,
                source_name=bundle.source_key or "data.ninjakiwi.com",
                fetched_at=bundle.fetched_at,
                freshness=bundle.freshness_status,
            ),
        )
        if len(out) >= clamped:
            break
    return tuple(out)


__all__ = [
    "ActiveEventSummary",
    "EntitySummary",
    "EventDetailsSummary",
    "EventEntityKind",
    "FactSummary",
    "LeaderboardEntry",
    "LeaderboardSummary",
    "RestrictionSummary",
    "SourceStatusSummary",
    "get_active_restrictions",
    "get_current_events",
    "get_event_details",
    "get_hero_summary",
    "get_leaderboard_summary",
    "get_source_status",
    "get_tower_summary",
    "search_btd6_facts",
]
