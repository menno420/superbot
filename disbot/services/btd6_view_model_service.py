"""BTD6 view-model service — sandwich layer between query services and embeds.

The cog/view layer used to either consume query-service dataclasses
directly or read DB rows from the embed builders. This service is the
middle layer: it composes data from the existing read services
(``btd6_knowledge_service``, ``btd6_source_registry``,
``btd6_live_query_service``, ``utils.db.btd6_sources``) into typed
view-model dataclasses that the embed builders + new sub-views consume.

Three public concerns:

1. :class:`DataFreshness` — every read carries one of these. The
   ``state`` reuses :data:`services.btd6_source_registry.FreshnessBucket`
   verbatim; thresholds live in ``btd6_source_registry`` (single source
   of truth, do not duplicate).
2. :class:`ContextHandle` + :func:`make_context_handle` — the
   ``context_id`` contract a future Team Panel attaches to. Format
   ``btd6_<type>:<key>`` (single colon, regex-pinned).
3. ``build_*_view_model`` async builders — one per area.

Architecture rule (CI-enforced): this module imports only stdlib,
``services.*``, and ``utils.*``. It must NOT import ``discord``,
``views/``, or ``cogs/``. Callers unpack what they need from the
Discord interaction and pass primitives (``guild_id: int``, ``kind: str``,
etc.) — no ``discord.Interaction`` / ``Member`` / ``Guild`` reaches
this layer.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from services.btd6_source_registry import (
    FreshnessBucket,
    SourceHealth,
    bucket_freshness,
)
from utils.btd6.event_window import WindowStatus, format_window

logger = logging.getLogger("bot.services.btd6_view_model")


# ---------------------------------------------------------------------------
# Context contract
# ---------------------------------------------------------------------------


BTD6ContextType = Literal[
    "hub",
    "race",
    "boss",
    "ct",
    "ct_relic",
    "odyssey",
    "event",
    "tower",
    "hero",
    "leaderboard",
    "strategy",
    "source",
    "status",
    "diagnostics",
]


_CONTEXT_ID_RE = re.compile(r"^btd6_[a-z_]+:[A-Za-z0-9_-]+$")
_KEY_SAFE_RE = re.compile(r"[^A-Za-z0-9_-]")


@dataclass(frozen=True)
class ContextHandle:
    """Stable handle a future Team Panel attaches notes to.

    ``context_id`` always matches ``^btd6_[a-z_]+:[A-Za-z0-9_-]+$``.
    """

    context_id: str
    context_type: BTD6ContextType


def make_context_handle(
    context_type: BTD6ContextType,
    entity_key: str,
) -> ContextHandle:
    """Normalize and validate a context handle.

    ``entity_key`` is sanitized by replacing any character outside
    ``[A-Za-z0-9_-]`` with ``_`` so external IDs (URLs, names) can be
    passed straight in. Raises :class:`ValueError` if the resulting
    ``context_id`` fails the contract regex (e.g. empty key).
    """
    if not entity_key:
        raise ValueError("context entity_key cannot be empty")
    sanitized = _KEY_SAFE_RE.sub("_", entity_key)
    context_id = f"btd6_{context_type}:{sanitized}"
    if not _CONTEXT_ID_RE.match(context_id):
        raise ValueError(
            f"context_id {context_id!r} does not match the contract regex",
        )
    return ContextHandle(context_id=context_id, context_type=context_type)


# ---------------------------------------------------------------------------
# Freshness
# ---------------------------------------------------------------------------


# Threshold for "stale" surfaces to public users (24h). The bucketing
# logic in :func:`services.btd6_source_registry.bucket_freshness` uses
# ``stale`` at >2d — this VM-level threshold is finer-grained for the
# public-warning trigger. (Aging is not user-facing in PR 1.)
STALE_AFTER_SECONDS = 86_400


@dataclass(frozen=True)
class DataFreshness:
    """Per-source freshness snapshot threaded through every VM."""

    state: FreshnessBucket
    last_success_at: datetime | None
    last_attempt_at: datetime | None
    source_key: str
    stale_after_seconds: int = STALE_AFTER_SECONDS


def _freshness_from_health(source: SourceHealth) -> DataFreshness:
    """Build :class:`DataFreshness` from a :class:`SourceHealth` row."""
    return DataFreshness(
        state=source.bucket,
        last_success_at=source.last_fetched_at,
        last_attempt_at=source.last_fetched_at,
        source_key=source.source_key,
    )


def _freshness_from_fetched_at(
    fetched_at: datetime | None,
    *,
    source_key: str,
) -> DataFreshness:
    """Build :class:`DataFreshness` from a bare ``fetched_at`` timestamp."""
    return DataFreshness(
        state=bucket_freshness(fetched_at),
        last_success_at=fetched_at,
        last_attempt_at=fetched_at,
        source_key=source_key,
    )


# ---------------------------------------------------------------------------
# Hub view-model
# ---------------------------------------------------------------------------


# Each tuple is (entity_kind, emoji, short_kind, source_key) — the
# panel's "Currently active" block iterates in this order, useful-first.
_HUB_ACTIVE_KINDS: tuple[tuple[str, str, str, str], ...] = (
    ("btd6_race", "🏁", "race", "nk_btd6_races"),
    ("btd6_boss", "👑", "boss", "nk_btd6_bosses"),
    ("btd6_ct", "🗺️", "ct", "nk_btd6_ct"),
    ("btd6_odyssey", "🌊", "odyssey", "nk_btd6_odyssey"),
    ("btd6_event", "🎪", "event", "nk_btd6_events"),
)


@dataclass(frozen=True)
class HubActiveEvent:
    """One row in the Hub's 'Currently active' block."""

    entity_kind: str
    short_kind: str
    emoji: str
    name: str | None
    end_ms: int | None
    freshness: DataFreshness
    context: ContextHandle | None  # None when no fact exists for this kind


@dataclass(frozen=True)
class HubViewModel:
    """Top-level BTD6 panel view-model."""

    data_version: str
    game_version: str
    tower_count: int
    hero_count: int
    map_count: int
    mode_count: int
    round_count: int
    active_events: tuple[HubActiveEvent, ...]
    context: ContextHandle


async def build_hub_view_model() -> HubViewModel:
    """Compose the BTD6 hub view-model.

    Pulls knowledge counts from :mod:`btd6_knowledge_service`, the
    set of currently-active events from
    :func:`services.btd6_live_query_service.get_active_events`, and
    derives per-kind freshness from the latest stored fact for that
    kind so an empty "Currently active" slot still tells the operator
    whether ingestion ran recently.

    The hub uses a stricter active-window filter than the facade's
    default: only events whose ``end_ms`` is **explicitly in the future**
    surface as currently-active. Events with missing / past ``end_ms``
    are excluded (the facade's default treats missing ``end_ms`` as
    active for restriction scanning, which is too permissive for a
    user-facing "what's running right now" claim).
    """
    from datetime import datetime, timezone

    from services import btd6_knowledge_service, btd6_live_query_service
    from utils.db import btd6_sources as btd6_db

    rows = await btd6_db.latest_fact_per_entity_kind(
        [kind for kind, _, _, _ in _HUB_ACTIVE_KINDS],
    )
    headlines = await btd6_live_query_service.get_active_events(
        tuple(kind for kind, _, _, _ in _HUB_ACTIVE_KINDS),
    )
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    # Strict filter: only events with an explicit future end_ms count
    # as "currently active" on the hub.
    active_by_kind: dict[str, Any] = {}
    for headline in headlines:
        if headline.end_ms is None or headline.end_ms <= now_ms:
            continue
        # First match wins — get_active_events orders newest-fetched
        # first within each kind.
        active_by_kind.setdefault(headline.entity_kind, headline)

    active: list[HubActiveEvent] = []
    for entity_kind, emoji, short_kind, source_key in _HUB_ACTIVE_KINDS:
        live = active_by_kind.get(entity_kind)
        row = rows.get(entity_kind)
        # Freshness is derived from the latest stored fact for this
        # kind (i.e. how recently the ingestion supervisor wrote
        # anything), independently of whether a specific event is
        # currently active. That keeps the bucket badge meaningful
        # even when no event is running.
        if row is None:
            freshness = DataFreshness(
                state="never",
                last_success_at=None,
                last_attempt_at=None,
                source_key=source_key,
            )
        else:
            freshness = _freshness_from_fetched_at(
                row.get("fetched_at"),
                source_key=source_key,
            )

        if live is None:
            # Source may have data but no event is currently in its
            # active window (between rotations). Render as "—".
            active.append(
                HubActiveEvent(
                    entity_kind=entity_kind,
                    short_kind=short_kind,
                    emoji=emoji,
                    name=None,
                    end_ms=None,
                    freshness=freshness,
                    context=None,
                ),
            )
            continue

        context: ContextHandle | None = None
        if live.entity_key:
            try:
                context = make_context_handle(
                    short_kind,  # type: ignore[arg-type]
                    str(live.entity_key),
                )
            except ValueError:
                context = None
        active.append(
            HubActiveEvent(
                entity_kind=entity_kind,
                short_kind=short_kind,
                emoji=emoji,
                name=live.name or str(live.entity_key) or None,
                end_ms=live.end_ms,
                freshness=freshness,
                context=context,
            ),
        )

    return HubViewModel(
        data_version=btd6_knowledge_service.data_version(),
        game_version=btd6_knowledge_service.game_version(),
        tower_count=len(btd6_knowledge_service.list_towers()),
        hero_count=len(btd6_knowledge_service.list_heroes()),
        map_count=len(btd6_knowledge_service.list_maps()),
        mode_count=len(btd6_knowledge_service.list_modes()),
        round_count=len(btd6_knowledge_service.list_rounds()),
        active_events=tuple(active),
        context=make_context_handle("hub", "main"),
    )


# ---------------------------------------------------------------------------
# Staff diagnostics view-model (status / source-health / latest-data)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StaffDiagnosticsViewModel:
    """Aggregate for the staff status / diagnostics view.

    Carries the same data the existing ``build_status_embed`` needs:
    seed counts + per-kind fact summaries from
    ``btd6_knowledge_service.fact_summary_by_kind()``. Per-source health
    has its own VM (:class:`SourceHealthViewModel`) — the staff embed
    today only renders fact summaries, not source rows.
    """

    data_version: str
    game_version: str
    tower_count: int
    hero_count: int
    map_count: int
    mode_count: int
    round_count: int
    fact_summaries: tuple[Any, ...]  # tuple[FactKindSummary, ...]
    context: ContextHandle


async def build_staff_diagnostics_view_model(
    *,
    guild_id: int | None = None,
) -> StaffDiagnosticsViewModel:
    """Compose the staff diagnostics view-model."""
    from services import btd6_knowledge_service

    summaries = await btd6_knowledge_service.fact_summary_by_kind()
    key = str(guild_id) if guild_id is not None else "global"
    return StaffDiagnosticsViewModel(
        data_version=btd6_knowledge_service.data_version(),
        game_version=btd6_knowledge_service.game_version(),
        tower_count=len(btd6_knowledge_service.list_towers()),
        hero_count=len(btd6_knowledge_service.list_heroes()),
        map_count=len(btd6_knowledge_service.list_maps()),
        mode_count=len(btd6_knowledge_service.list_modes()),
        round_count=len(btd6_knowledge_service.list_rounds()),
        fact_summaries=tuple(summaries),
        context=make_context_handle("status", key),
    )


# ---------------------------------------------------------------------------
# Source health view-model (for source-health / Admin "Source Health" button)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceHealthRow:
    """One row in the Source Health embed."""

    health: SourceHealth
    freshness: DataFreshness
    context: ContextHandle


@dataclass(frozen=True)
class SourceHealthViewModel:
    """Per-source freshness overview."""

    rows: tuple[SourceHealthRow, ...]
    context: ContextHandle


async def build_source_health_view_model(
    *,
    limit: int = 25,
) -> SourceHealthViewModel:
    """Compose source-health rows."""
    from services import btd6_source_registry

    health = await btd6_source_registry.list_health(limit=limit)
    rows: list[SourceHealthRow] = []
    for src in health:
        freshness = _freshness_from_health(src)
        try:
            ctx = make_context_handle("source", src.source_key)
        except ValueError:
            ctx = make_context_handle("source", "unknown")
        rows.append(SourceHealthRow(health=src, freshness=freshness, context=ctx))
    return SourceHealthViewModel(
        rows=tuple(rows),
        context=make_context_handle("diagnostics", "sources"),
    )


# ---------------------------------------------------------------------------
# Event list / detail view-models
# ---------------------------------------------------------------------------


_EVENT_KIND_TO_CONTEXT_TYPE: dict[str, BTD6ContextType] = {
    "btd6_race": "race",
    "btd6_boss": "boss",
    "btd6_ct": "ct",
    "btd6_odyssey": "odyssey",
    "btd6_event": "event",
}

_EVENT_KIND_TO_SOURCE_KEY: dict[str, str] = {
    "btd6_race": "nk_btd6_races",
    "btd6_boss": "nk_btd6_bosses",
    "btd6_ct": "nk_btd6_ct",
    "btd6_odyssey": "nk_btd6_odyssey",
    "btd6_event": "nk_btd6_events",
}


@dataclass(frozen=True)
class EventListItem:
    """One row in an event-list view-model."""

    entity_kind: str
    entity_key: str
    name: str
    window: WindowStatus
    context: ContextHandle


@dataclass(frozen=True)
class EventListViewModel:
    """List of events for a given kind."""

    kind: str  # "race" / "boss" / etc. (short form)
    entity_kind: str  # "btd6_race" / "btd6_boss" / etc.
    items: tuple[EventListItem, ...]
    total_count: int  # before max_items cap
    freshness: DataFreshness
    context: ContextHandle


def _normalize_event_kind(kind: str) -> tuple[str, str]:
    """Return (entity_kind, short_kind) for a user-supplied kind string."""
    short = kind.removeprefix("btd6_") if kind.startswith("btd6_") else kind
    entity = f"btd6_{short}"
    return entity, short


async def build_event_list_view_model(
    kind: str,
    *,
    max_items: int = 25,
) -> EventListViewModel:
    """Compose an event-list view-model.

    ``kind`` may be either the long form (``"btd6_race"``) or the short
    form (``"race"``). Capped at ``max_items`` to respect Discord's
    25-option Select limit; ``total_count`` exposes the pre-cap size.
    """
    from utils.btd6.body_coerce import coerce_body
    from utils.db import btd6_sources as btd6_db

    entity_kind, short = _normalize_event_kind(kind)
    source_key = _EVENT_KIND_TO_SOURCE_KEY.get(entity_kind, "")
    context_type = _EVENT_KIND_TO_CONTEXT_TYPE.get(entity_kind, "event")

    rows = await btd6_db.search_facts(entity_kind=entity_kind, limit=max(max_items, 25))
    items: list[EventListItem] = []
    latest_fetched: datetime | None = None
    for row in rows[:max_items]:
        body = coerce_body(row.get("body_json"))
        entity_key = str(row.get("entity_key") or "")
        if not entity_key:
            continue
        try:
            ctx = make_context_handle(context_type, entity_key)
        except ValueError:
            continue
        items.append(
            EventListItem(
                entity_kind=entity_kind,
                entity_key=entity_key,
                name=str(body.get("name") or entity_key),
                window=format_window(body.get("start_ms"), body.get("end_ms")),
                context=ctx,
            ),
        )
        fetched_at = row.get("fetched_at")
        if isinstance(fetched_at, datetime):
            if latest_fetched is None or fetched_at > latest_fetched:
                latest_fetched = fetched_at

    freshness = _freshness_from_fetched_at(latest_fetched, source_key=source_key)
    return EventListViewModel(
        kind=short,
        entity_kind=entity_kind,
        items=tuple(items),
        total_count=len(rows),
        freshness=freshness,
        context=make_context_handle(context_type, "list"),
    )


@dataclass(frozen=True)
class EventDetailViewModel:
    """Detail-view payload for one event."""

    entity_kind: str
    entity_key: str
    name: str
    window: WindowStatus
    primary_body: dict[str, Any]
    metadata_body: dict[str, Any]
    fetched_at: datetime | None
    freshness: DataFreshness
    context: ContextHandle


async def build_event_detail_view_model(
    kind: str,
    entity_key: str,
) -> EventDetailViewModel | None:
    """Compose an event-detail view-model.

    Returns ``None`` when no fact exists for the requested key.
    """
    from utils.btd6.body_coerce import coerce_body
    from utils.db import btd6_sources as btd6_db

    entity_kind, _ = _normalize_event_kind(kind)
    context_type = _EVENT_KIND_TO_CONTEXT_TYPE.get(entity_kind, "event")
    source_key = _EVENT_KIND_TO_SOURCE_KEY.get(entity_kind, "")

    rows = await btd6_db.search_facts(
        entity_kind=entity_kind,
        entity_key=entity_key,
        limit=2,
    )
    primary_row = next(
        (r for r in rows if not str(r.get("fact_type", "")).endswith("_metadata")),
        rows[0] if rows else None,
    )
    metadata_row = next(
        (r for r in rows if str(r.get("fact_type", "")).endswith("_metadata")),
        None,
    )

    if primary_row is None and metadata_row is None:
        return None

    primary_body = coerce_body((primary_row or {}).get("body_json"))
    metadata_body = coerce_body((metadata_row or {}).get("body_json"))
    name = str(primary_body.get("name") or metadata_body.get("name") or entity_key)

    window_body = primary_body if primary_body.get("start_ms") else metadata_body
    window = format_window(window_body.get("start_ms"), window_body.get("end_ms"))

    fetched_at = (primary_row or {}).get("fetched_at") or (metadata_row or {}).get(
        "fetched_at",
    )
    if not isinstance(fetched_at, datetime):
        fetched_at = None

    freshness = _freshness_from_fetched_at(fetched_at, source_key=source_key)
    return EventDetailViewModel(
        entity_kind=entity_kind,
        entity_key=entity_key,
        name=name,
        window=window,
        primary_body=primary_body,
        metadata_body=metadata_body,
        fetched_at=fetched_at,
        freshness=freshness,
        context=make_context_handle(context_type, entity_key),
    )


# ---------------------------------------------------------------------------
# Tower list / detail view-models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TowerListItem:
    tower_id: str
    canonical: str
    base_cost: int
    category: str
    context: ContextHandle


@dataclass(frozen=True)
class TowerListViewModel:
    items: tuple[TowerListItem, ...]
    total_count: int
    context: ContextHandle
    page: int = 0
    total_pages: int = 1
    category_filter: str | None = None


@dataclass(frozen=True)
class TowerDetailViewModel:
    tower_id: str
    canonical: str
    fact: Any  # btd6_knowledge_service.TowerFact | None
    restrictions: tuple[Any, ...]  # tuple[TowerRestrictionContext, ...]
    context: ContextHandle


_TOWER_PAGE_SIZE = 8


async def build_tower_list_view_model(
    *,
    page: int = 0,
    category: str | None = None,
) -> TowerListViewModel:
    """Tower catalog list with optional pagination and category filter."""
    from services import btd6_knowledge_service

    all_towers = btd6_knowledge_service.list_towers()
    filtered = (
        [t for t in all_towers if t.category.lower() == category.lower()]
        if category
        else list(all_towers)
    )
    total = len(filtered)
    total_pages = max(1, (total + _TOWER_PAGE_SIZE - 1) // _TOWER_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * _TOWER_PAGE_SIZE
    page_slice = filtered[start : start + _TOWER_PAGE_SIZE]

    items: list[TowerListItem] = []
    for tower in page_slice:
        try:
            ctx = make_context_handle("tower", str(tower.id))
        except ValueError:
            continue
        items.append(
            TowerListItem(
                tower_id=str(tower.id),
                canonical=tower.canonical,
                base_cost=tower.base_cost,
                category=tower.category,
                context=ctx,
            ),
        )
    return TowerListViewModel(
        items=tuple(items),
        total_count=total,
        context=make_context_handle("tower", "list"),
        page=page,
        total_pages=total_pages,
        category_filter=category,
    )


async def build_tower_detail_view_model(
    tower_id: str,
) -> TowerDetailViewModel | None:
    """Tower detail with live restriction context."""
    from services import btd6_knowledge_service, btd6_live_query_service
    from services.btd6_resolver_service import resolve

    intent = resolve(tower_id)
    if not intent.towers:
        return None
    tower = intent.towers[0]
    fact = btd6_knowledge_service.tower_fact(tower.id)
    restrictions = (
        await btd6_live_query_service.get_active_event_restrictions_for_tower(
            str(tower.id),
        )
    )
    return TowerDetailViewModel(
        tower_id=str(tower.id),
        canonical=tower.canonical,
        fact=fact,
        restrictions=tuple(restrictions),
        context=make_context_handle("tower", str(tower.id)),
    )


# ---------------------------------------------------------------------------
# Hero list / detail view-models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HeroListItem:
    hero_id: str
    canonical: str
    base_cost: int
    description: str
    context: ContextHandle


@dataclass(frozen=True)
class HeroListViewModel:
    items: tuple[HeroListItem, ...]
    total_count: int
    context: ContextHandle
    page: int = 0
    total_pages: int = 1


@dataclass(frozen=True)
class HeroDetailViewModel:
    hero_id: str
    canonical: str
    restrictions: tuple[Any, ...]
    context: ContextHandle


_HERO_PAGE_SIZE = 8


async def build_hero_list_view_model(
    *,
    page: int = 0,
) -> HeroListViewModel:
    """Hero catalog list with optional pagination."""
    from services import btd6_knowledge_service

    all_heroes = btd6_knowledge_service.list_heroes()
    total = len(all_heroes)
    total_pages = max(1, (total + _HERO_PAGE_SIZE - 1) // _HERO_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * _HERO_PAGE_SIZE
    page_slice = all_heroes[start : start + _HERO_PAGE_SIZE]

    items: list[HeroListItem] = []
    for hero in page_slice:
        try:
            ctx = make_context_handle("hero", str(hero.id))
        except ValueError:
            continue
        items.append(
            HeroListItem(
                hero_id=str(hero.id),
                canonical=hero.canonical,
                base_cost=hero.base_cost,
                description=hero.description,
                context=ctx,
            ),
        )
    return HeroListViewModel(
        items=tuple(items),
        total_count=total,
        context=make_context_handle("hero", "list"),
        page=page,
        total_pages=total_pages,
    )


async def build_hero_detail_view_model(
    hero_id: str,
) -> HeroDetailViewModel | None:
    """Hero detail with live restriction context."""
    from services import btd6_live_query_service
    from services.btd6_resolver_service import resolve

    intent = resolve(hero_id)
    if not intent.heroes:
        return None
    hero = intent.heroes[0]
    restrictions = await btd6_live_query_service.get_active_event_restrictions_for_hero(
        str(hero.id),
    )
    return HeroDetailViewModel(
        hero_id=str(hero.id),
        canonical=hero.canonical,
        restrictions=tuple(restrictions),
        context=make_context_handle("hero", str(hero.id)),
    )


# ---------------------------------------------------------------------------
# Leaderboard view-models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LeaderboardListItem:
    """One race/boss event available to view leaderboard for."""

    event_kind: str  # "race" or "boss"
    event_id: str
    event_name: str
    window: WindowStatus
    context: ContextHandle


@dataclass(frozen=True)
class LeaderboardListViewModel:
    event_kind: str
    items: tuple[LeaderboardListItem, ...]
    total_count: int
    freshness: DataFreshness
    context: ContextHandle


@dataclass(frozen=True)
class LeaderboardDetailViewModel:
    event_kind: str
    event_id: str
    event_name: str | None
    rows: tuple[Any, ...]  # tuple[LeaderboardRow, ...]
    freshness: DataFreshness
    context: ContextHandle
    footer_hint: str = ""


async def build_leaderboard_list_view_model(
    event_kind: str,
    *,
    max_items: int = 25,
) -> LeaderboardListViewModel:
    """List recent race/boss events available for leaderboard view."""
    norm = (event_kind or "").strip().lower()
    if norm not in {"race", "boss"}:
        raise ValueError(f"event_kind must be 'race' or 'boss', got {event_kind!r}")
    entity_kind = "btd6_race" if norm == "race" else "btd6_boss"
    source_key = _EVENT_KIND_TO_SOURCE_KEY[entity_kind]
    list_vm = await build_event_list_view_model(norm, max_items=max_items)
    items: list[LeaderboardListItem] = []
    for evt in list_vm.items:
        items.append(
            LeaderboardListItem(
                event_kind=norm,
                event_id=evt.entity_key,
                event_name=evt.name,
                window=evt.window,
                context=make_context_handle(
                    "leaderboard",
                    f"{norm}_{evt.entity_key}",
                ),
            ),
        )
    return LeaderboardListViewModel(
        event_kind=norm,
        items=tuple(items),
        total_count=list_vm.total_count,
        freshness=DataFreshness(
            state=list_vm.freshness.state,
            last_success_at=list_vm.freshness.last_success_at,
            last_attempt_at=list_vm.freshness.last_attempt_at,
            source_key=source_key,
        ),
        context=make_context_handle("leaderboard", f"{norm}_list"),
    )


async def build_leaderboard_detail_view_model(
    event_kind: str,
    event_id: str,
    *,
    top_n: int = 10,
) -> LeaderboardDetailViewModel:
    """Top-N leaderboard rows for one race/boss event."""
    from services import btd6_live_query_service as live

    norm = (event_kind or "").strip().lower()
    if norm not in {"race", "boss"}:
        raise ValueError(f"event_kind must be 'race' or 'boss', got {event_kind!r}")

    if norm == "race":
        rows = await live.get_race_leaderboard(event_id, limit=top_n)
        active = await live.get_newest_active_race()
        source_key = "nk_btd6_races"
        footer = ""
    else:
        rows = await live.get_boss_leaderboard(event_id, limit=top_n)
        active = await live.get_newest_active_boss()
        source_key = "nk_btd6_bosses"
        footer = (
            "Showing standard solo leaderboard. "
            "Elite / team modes are not yet ingested."
        )

    event_name = active.name if active and active.entity_key == event_id else None
    freshness = _freshness_from_fetched_at(
        active.fetched_at if active else None,
        source_key=source_key,
    )
    return LeaderboardDetailViewModel(
        event_kind=norm,
        event_id=event_id,
        event_name=event_name,
        rows=tuple(rows),
        freshness=freshness,
        context=make_context_handle("leaderboard", f"{norm}_{event_id}"),
        footer_hint=footer,
    )


# ---------------------------------------------------------------------------
# Latest-data view-model (per-kind newest fact)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LatestDataRow:
    entity_kind: str
    entity_key: str
    source_key: str
    version: int
    fetched_at: datetime | None
    context: ContextHandle


@dataclass(frozen=True)
class LatestDataViewModel:
    rows_by_kind: dict[str, tuple[LatestDataRow, ...]] = field(default_factory=dict)
    context: ContextHandle = field(
        default_factory=lambda: make_context_handle("diagnostics", "latest_data"),
    )


async def build_latest_data_view_model(
    *,
    limit_per_kind: int = 1,
) -> LatestDataViewModel:
    """Compose the latest-data view-model."""
    from services import btd6_source_registry
    from utils.db import btd6_sources as btd6_db

    rows = await btd6_db.search_facts(limit=50)
    source_rows = await btd6_source_registry.list_all()
    id_to_key = {int(s["id"]): s["source_key"] for s in source_rows}

    grouped: dict[str, list[LatestDataRow]] = {}
    for row in rows:
        entity_kind = str(row.get("entity_kind") or "")
        if not entity_kind:
            continue
        entity_key = str(row.get("entity_key") or "")
        if not entity_key:
            continue
        source_key = id_to_key.get(int(row["source_id"]), "—")
        try:
            ctx = make_context_handle("event", entity_key)
        except ValueError:
            continue
        fetched_at = row.get("fetched_at")
        latest_row = LatestDataRow(
            entity_kind=entity_kind,
            entity_key=entity_key,
            source_key=source_key,
            version=int(row.get("version") or 0),
            fetched_at=fetched_at if isinstance(fetched_at, datetime) else None,
            context=ctx,
        )
        grouped.setdefault(entity_kind, []).append(latest_row)

    rows_by_kind = {
        kind: tuple(items[:limit_per_kind]) for kind, items in sorted(grouped.items())
    }
    return LatestDataViewModel(
        rows_by_kind=rows_by_kind,
        context=make_context_handle("diagnostics", "latest_data"),
    )


__all__ = [
    "BTD6ContextType",
    "ContextHandle",
    "DataFreshness",
    "EventDetailViewModel",
    "EventListItem",
    "EventListViewModel",
    "HeroDetailViewModel",
    "HeroListItem",
    "HeroListViewModel",
    "HubActiveEvent",
    "HubViewModel",
    "LatestDataRow",
    "LatestDataViewModel",
    "LeaderboardDetailViewModel",
    "LeaderboardListItem",
    "LeaderboardListViewModel",
    "SourceHealthRow",
    "SourceHealthViewModel",
    "STALE_AFTER_SECONDS",
    "StaffDiagnosticsViewModel",
    "TowerDetailViewModel",
    "TowerListItem",
    "TowerListViewModel",
    "build_event_detail_view_model",
    "build_event_list_view_model",
    "build_hero_detail_view_model",
    "build_hero_list_view_model",
    "build_hub_view_model",
    "build_latest_data_view_model",
    "build_leaderboard_detail_view_model",
    "build_leaderboard_list_view_model",
    "build_source_health_view_model",
    "build_staff_diagnostics_view_model",
    "build_tower_detail_view_model",
    "build_tower_list_view_model",
    "make_context_handle",
]
