"""Read facade over ``utils.db.btd6_sources`` for BTD6 live data.

Single typed surface for UI / AI consumers that want fetched
Ninja-Kiwi facts (active events, per-tower restrictions, leaderboards)
without learning the raw fact-store schema. Architecture-clean:

* imports only stdlib, ``utils.db.btd6_sources``,
  ``services.btd6_source_registry``, ``services.btd6_ingestion_sources``,
  and ``utils.btd6.tower_restrictions``;
* no view / cog imports;
* read-only — never mutates.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from utils.btd6.body_coerce import coerce_body as _coerce_body
from utils.btd6.ct_tile_geometry import CTTilePosition, decode_tile

logger = logging.getLogger("bot.services.btd6_live_query")


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActiveEventHeadline:
    """One currently-active live event."""

    entity_kind: str
    entity_key: str
    name: str
    start_ms: int | None
    end_ms: int | None
    fetched_at: datetime | None


@dataclass(frozen=True)
class TowerRestrictionContext:
    """One active event's stance on one tower or hero."""

    event_kind: str
    event_id: str
    event_name: str
    end_ms: int | None
    fetched_at: datetime | None
    stance: Literal["banned", "limited", "path_blocked", "allowed"]
    max_count: int | None
    path1_blocked: int
    path2_blocked: int
    path3_blocked: int
    is_hero: bool
    sentinel_all_heroes_banned: bool = False


@dataclass(frozen=True)
class LeaderboardRow:
    """One rank on a race or boss leaderboard."""

    rank: int
    display_name: str
    score: int | None
    score_parts: list[Any] | None
    submission_time_ms: int | None
    profile_url: str | None


# ---------------------------------------------------------------------------
# Mapping: static seed id (snake_case) → Ninja Kiwi API key (CamelCase)
# ---------------------------------------------------------------------------

# Hard-coded so new entries to data/btd6/towers.json or heroes.json must
# also gain an explicit mapping (enforced by the mapping-coverage test).
# Snake-to-CamelCase covers current entries; the explicit form is a
# self-documenting safety net for irregular future keys (e.g. ``Psi``,
# ``HeliPilot``, ``BombShooter``).
_TOWER_ID_TO_API_KEY: dict[str, str] = {
    # Primary
    "dart_monkey": "DartMonkey",
    "boomerang_monkey": "BoomerangMonkey",
    "bomb_shooter": "BombShooter",
    "tack_shooter": "TackShooter",
    "ice_monkey": "IceMonkey",
    "glue_gunner": "GlueGunner",
    "desperado": "Desperado",
    # Military
    "sniper_monkey": "SniperMonkey",
    "monkey_sub": "MonkeySub",
    "monkey_buccaneer": "MonkeyBuccaneer",
    "monkey_ace": "MonkeyAce",
    "heli_pilot": "HeliPilot",
    "mortar_monkey": "MortarMonkey",
    "dartling_gunner": "DartlingGunner",
    # Magic
    "wizard_monkey": "WizardMonkey",
    "super_monkey": "SuperMonkey",
    "ninja_monkey": "NinjaMonkey",
    "alchemist": "Alchemist",
    "druid": "Druid",
    "mermonkey": "Mermonkey",
    # Support
    "banana_farm": "BananaFarm",
    "spike_factory": "SpikeFactory",
    "monkey_village": "MonkeyVillage",
    "engineer_monkey": "EngineerMonkey",
    "beast_handler": "BeastHandler",
}

_HERO_ID_TO_API_KEY: dict[str, str] = {
    "quincy": "Quincy",
    "gwendolin": "Gwendolin",
    "striker_jones": "StrikerJones",
    "obyn_greenfoot": "ObynGreenfoot",
    "captain_churchill": "CaptainChurchill",
    "benjamin": "Benjamin",
    "ezili": "Ezili",
    "pat_fusty": "PatFusty",
    "adora": "Adora",
    "admiral_brickell": "AdmiralBrickell",
    "etienne": "Etienne",
    "sauda": "Sauda",
    "psi": "Psi",
    "geraldo": "Geraldo",
    "corvus": "Corvus",
    "rosalia": "Rosalia",
    "silas": "Silas",
}

_CHOSEN_PRIMARY_HERO_KEY = "ChosenPrimaryHero"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_active_window(body: dict[str, Any]) -> bool:
    """Return True unless the event's ``end_ms`` is clearly in the past.

    Defensive: ``latest_fact_per_entity_kind`` / ``search_facts`` return
    whatever was fetched most recently regardless of window status. If
    ``end_ms`` is present and < now, treat the event as ended.
    """
    end_ms = body.get("end_ms")
    if not isinstance(end_ms, (int, float)) or end_ms <= 0:
        return True
    now_ms = datetime.now(tz=timezone.utc).timestamp() * 1000
    return end_ms >= now_ms


def _stance_from_entry(
    entry: dict[str, Any],
) -> tuple[
    Literal["banned", "limited", "path_blocked", "allowed"],
    int | None,
    int,
    int,
    int,
]:
    """Classify one ``_towers`` entry. Returns (stance, max, p1, p2, p3)."""
    max_val = entry.get("max")
    max_int = max_val if isinstance(max_val, int) else None
    p1 = entry.get("path1NumBlockedTiers") or 0
    p2 = entry.get("path2NumBlockedTiers") or 0
    p3 = entry.get("path3NumBlockedTiers") or 0
    p1 = p1 if isinstance(p1, int) else 0
    p2 = p2 if isinstance(p2, int) else 0
    p3 = p3 if isinstance(p3, int) else 0
    if max_int == 0:
        return "banned", 0, p1, p2, p3
    if max_int is not None and max_int >= 1:
        return "limited", max_int, p1, p2, p3
    if p1 > 0 or p2 > 0 or p3 > 0:
        return "path_blocked", max_int, p1, p2, p3
    return "allowed", max_int, p1, p2, p3


def _build_restriction(
    *,
    event_kind: str,
    event_id: str,
    event_name: str,
    end_ms: int | None,
    fetched_at: datetime | None,
    entry: dict[str, Any],
    sentinel: bool = False,
) -> TowerRestrictionContext:
    stance, max_count, p1, p2, p3 = _stance_from_entry(entry)
    if sentinel:
        stance = "banned"
        max_count = 0
    return TowerRestrictionContext(
        event_kind=event_kind,
        event_id=event_id,
        event_name=event_name,
        end_ms=end_ms,
        fetched_at=fetched_at,
        stance=stance,
        max_count=max_count,
        path1_blocked=p1,
        path2_blocked=p2,
        path3_blocked=p3,
        is_hero=bool(entry.get("isHero", False)) or sentinel,
        sentinel_all_heroes_banned=sentinel,
    )


def _find_entry(towers: list[Any], api_key: str) -> dict[str, Any] | None:
    """Locate the first ``_towers`` entry matching ``api_key``."""
    for entry in towers:
        if isinstance(entry, dict) and entry.get("tower") == api_key:
            return entry
    return None


# ---------------------------------------------------------------------------
# Sync surface — pure config passthrough
# ---------------------------------------------------------------------------


def list_scheduled_parent_sources() -> tuple[str, ...]:
    """Re-export of the canonical parent-source order.

    Sync because this is pure config — see ``btd6_ingestion_sources``.
    """
    from services import btd6_ingestion_sources

    return btd6_ingestion_sources.parent_source_keys()


# ---------------------------------------------------------------------------
# Active events
# ---------------------------------------------------------------------------


_DEFAULT_ACTIVE_KINDS: tuple[str, ...] = (
    "btd6_race",
    "btd6_boss",
    "btd6_ct",
    "btd6_odyssey",
    "btd6_event",
    "btd6_challenge",
)

# Fact-type that carries the index entry for each live-event kind.
# Restriction scans use a different fact-type (the ``*_metadata`` row).
_INDEX_FACT_TYPE: dict[str, str] = {
    "btd6_race": "btd6.races_index",
    "btd6_boss": "btd6.bosses_index",
    "btd6_ct": "btd6.ct_index",
    "btd6_odyssey": "btd6.odyssey_index",
    "btd6_event": "btd6.events_index",
    "btd6_challenge": "btd6.challenge_list",
}


async def get_active_events(
    kinds: Sequence[str] | None = None,
) -> tuple[ActiveEventHeadline, ...]:
    """Return active-event headlines across the requested kinds.

    ``kinds=None`` covers race / boss / CT / odyssey / event / challenge.
    Within each kind, rows are ordered newest-fetched first; the result
    is the concatenation across kinds in input order. Events whose
    ``end_ms`` is clearly past are excluded.
    """
    from utils.db import btd6_sources as btd6_db

    selected = tuple(kinds) if kinds else _DEFAULT_ACTIVE_KINDS
    out: list[ActiveEventHeadline] = []
    for kind in selected:
        fact_type = _INDEX_FACT_TYPE.get(kind)
        rows = await btd6_db.search_facts(
            fact_type=fact_type,
            entity_kind=kind,
            limit=25,
        )
        for row in rows:
            body = _coerce_body(row.get("body_json"))
            if not _is_active_window(body):
                continue
            start_ms = (
                body.get("start_ms") if isinstance(body.get("start_ms"), int) else None
            )
            end_ms = body.get("end_ms") if isinstance(body.get("end_ms"), int) else None
            out.append(
                ActiveEventHeadline(
                    entity_kind=kind,
                    entity_key=str(row.get("entity_key") or ""),
                    name=str(body.get("name") or row.get("entity_key") or ""),
                    start_ms=start_ms,
                    end_ms=end_ms,
                    fetched_at=row.get("fetched_at"),
                ),
            )
    return tuple(out)


async def get_newest_active_race() -> ActiveEventHeadline | None:
    """Newest active race, or None when nothing is stored."""
    for evt in await get_active_events(("btd6_race",)):
        return evt
    return None


async def get_newest_active_boss() -> ActiveEventHeadline | None:
    """Newest active boss, or None when nothing is stored."""
    for evt in await get_active_events(("btd6_boss",)):
        return evt
    return None


async def list_active_race_ids() -> tuple[str, ...]:
    """Active race entity_keys ordered by newest-fetched first."""
    return tuple(evt.entity_key for evt in await get_active_events(("btd6_race",)))


async def list_active_boss_ids() -> tuple[str, ...]:
    """Active boss entity_keys ordered by newest-fetched first."""
    return tuple(evt.entity_key for evt in await get_active_events(("btd6_boss",)))


# ---------------------------------------------------------------------------
# Restriction scanning
# ---------------------------------------------------------------------------


async def _scan_race_restrictions(
    api_key: str,
    *,
    sentinel_check: bool,
) -> list[TowerRestrictionContext]:
    """Race metadata: stored under ``btd6_race`` / ``btd6.race_metadata``.

    Active races are read from the index; their metadata is keyed by
    the same ``raceID`` so the lookup is a direct
    ``get_latest_fact("btd6.race_metadata", "btd6_race", race_id)``.
    """
    from utils.db import btd6_sources as btd6_db

    out: list[TowerRestrictionContext] = []
    for race in await get_active_events(("btd6_race",)):
        md = await btd6_db.get_latest_fact(
            "btd6.race_metadata",
            "btd6_race",
            race.entity_key,
        )
        if md is None:
            continue
        body = _coerce_body(md.get("body_json"))
        towers = body.get("_towers")
        if not isinstance(towers, list) or not towers:
            continue
        if sentinel_check:
            sentinel_entry = _find_entry(towers, _CHOSEN_PRIMARY_HERO_KEY)
            if sentinel_entry is not None and sentinel_entry.get("max") == 0:
                out.append(
                    _build_restriction(
                        event_kind="btd6_race",
                        event_id=race.entity_key,
                        event_name=race.name,
                        end_ms=race.end_ms,
                        fetched_at=md.get("fetched_at"),
                        entry=sentinel_entry,
                        sentinel=True,
                    ),
                )
        entry = _find_entry(towers, api_key)
        if entry is not None:
            stance, *_ = _stance_from_entry(entry)
            if stance != "allowed":
                out.append(
                    _build_restriction(
                        event_kind="btd6_race",
                        event_id=race.entity_key,
                        event_name=race.name,
                        end_ms=race.end_ms,
                        fetched_at=md.get("fetched_at"),
                        entry=entry,
                    ),
                )
    return out


async def _scan_boss_restrictions(
    api_key: str,
    *,
    sentinel_check: bool,
) -> list[TowerRestrictionContext]:
    """Boss metadata: stored under ``btd6_boss_difficulty`` keyed as
    ``{bossID}_{difficulty}``. The parser preserves ``boss_id`` and
    ``difficulty`` as explicit body fields — read those directly
    instead of splitting the entity_key (boss ids can contain
    underscores).
    """
    from utils.db import btd6_sources as btd6_db

    out: list[TowerRestrictionContext] = []
    for boss in await get_active_events(("btd6_boss",)):
        # Standard / current difficulty fan-out is "standard" (see
        # ``btd6_ingestion_service._DEPENDENCY_CHAINS``). Must match the
        # path-param the ingestion supervisor uses, otherwise lookups
        # find nothing.
        metadata_key = f"{boss.entity_key}_standard"
        md = await btd6_db.get_latest_fact(
            "btd6.boss_metadata",
            "btd6_boss_difficulty",
            metadata_key,
        )
        if md is None:
            continue
        body = _coerce_body(md.get("body_json"))
        # Resolve parent boss via preserved body fields — never split entity_key.
        parent_id = body.get("boss_id") or boss.entity_key
        towers = body.get("_towers")
        if not isinstance(towers, list) or not towers:
            continue
        if sentinel_check:
            sentinel_entry = _find_entry(towers, _CHOSEN_PRIMARY_HERO_KEY)
            if sentinel_entry is not None and sentinel_entry.get("max") == 0:
                out.append(
                    _build_restriction(
                        event_kind="btd6_boss_difficulty",
                        event_id=metadata_key,
                        event_name=boss.name or str(parent_id),
                        end_ms=boss.end_ms,
                        fetched_at=md.get("fetched_at"),
                        entry=sentinel_entry,
                        sentinel=True,
                    ),
                )
        entry = _find_entry(towers, api_key)
        if entry is not None:
            stance, *_ = _stance_from_entry(entry)
            if stance != "allowed":
                out.append(
                    _build_restriction(
                        event_kind="btd6_boss_difficulty",
                        event_id=metadata_key,
                        event_name=boss.name or str(parent_id),
                        end_ms=boss.end_ms,
                        fetched_at=md.get("fetched_at"),
                        entry=entry,
                    ),
                )
    return out


async def _scan_odyssey_restrictions(
    api_key: str,
    *,
    sentinel_check: bool,
) -> list[TowerRestrictionContext]:
    """Odyssey metadata: ``btd6_odyssey_difficulty`` keyed as
    ``{odysseyID}_{difficulty}``. Parser preserves ``odyssey_id`` and
    ``difficulty`` in the body. Default difficulty fan-out is ``easy``.
    """
    from utils.db import btd6_sources as btd6_db

    out: list[TowerRestrictionContext] = []
    for ody in await get_active_events(("btd6_odyssey",)):
        metadata_key = f"{ody.entity_key}_easy"
        md = await btd6_db.get_latest_fact(
            "btd6.odyssey_metadata",
            "btd6_odyssey_difficulty",
            metadata_key,
        )
        if md is None:
            continue
        body = _coerce_body(md.get("body_json"))
        parent_id = body.get("odyssey_id") or ody.entity_key
        # Odyssey carries both _towers and _availableTowers; scan _towers
        # first (race/boss-shape), fall back to _availableTowers if absent.
        towers = body.get("_towers")
        if not isinstance(towers, list) or not towers:
            towers = body.get("_availableTowers")
        if not isinstance(towers, list) or not towers:
            continue
        if sentinel_check:
            sentinel_entry = _find_entry(towers, _CHOSEN_PRIMARY_HERO_KEY)
            if sentinel_entry is not None and sentinel_entry.get("max") == 0:
                out.append(
                    _build_restriction(
                        event_kind="btd6_odyssey_difficulty",
                        event_id=metadata_key,
                        event_name=ody.name or str(parent_id),
                        end_ms=ody.end_ms,
                        fetched_at=md.get("fetched_at"),
                        entry=sentinel_entry,
                        sentinel=True,
                    ),
                )
        entry = _find_entry(towers, api_key)
        if entry is not None:
            stance, *_ = _stance_from_entry(entry)
            if stance != "allowed":
                out.append(
                    _build_restriction(
                        event_kind="btd6_odyssey_difficulty",
                        event_id=metadata_key,
                        event_name=ody.name or str(parent_id),
                        end_ms=ody.end_ms,
                        fetched_at=md.get("fetched_at"),
                        entry=entry,
                    ),
                )
    return out


async def _scan_challenge_restrictions(
    api_key: str,
    *,
    sentinel_check: bool,
) -> list[TowerRestrictionContext]:
    """Challenge metadata: ``btd6_challenge`` / ``btd6.challenge_metadata``.

    Challenges use the same entity_key for index and metadata, so the
    lookup mirrors the race shape.
    """
    from utils.db import btd6_sources as btd6_db

    out: list[TowerRestrictionContext] = []
    for ch in await get_active_events(("btd6_challenge",)):
        md = await btd6_db.get_latest_fact(
            "btd6.challenge_metadata",
            "btd6_challenge",
            ch.entity_key,
        )
        if md is None:
            continue
        body = _coerce_body(md.get("body_json"))
        towers = body.get("_towers")
        if not isinstance(towers, list) or not towers:
            continue
        if sentinel_check:
            sentinel_entry = _find_entry(towers, _CHOSEN_PRIMARY_HERO_KEY)
            if sentinel_entry is not None and sentinel_entry.get("max") == 0:
                out.append(
                    _build_restriction(
                        event_kind="btd6_challenge",
                        event_id=ch.entity_key,
                        event_name=ch.name,
                        end_ms=ch.end_ms,
                        fetched_at=md.get("fetched_at"),
                        entry=sentinel_entry,
                        sentinel=True,
                    ),
                )
        entry = _find_entry(towers, api_key)
        if entry is not None:
            stance, *_ = _stance_from_entry(entry)
            if stance != "allowed":
                out.append(
                    _build_restriction(
                        event_kind="btd6_challenge",
                        event_id=ch.entity_key,
                        event_name=ch.name,
                        end_ms=ch.end_ms,
                        fetched_at=md.get("fetched_at"),
                        entry=entry,
                    ),
                )
    return out


async def get_active_event_restrictions_for_tower(
    tower_id: str,
) -> tuple[TowerRestrictionContext, ...]:
    """Scan active race / boss / odyssey / challenge metadata for
    restrictions targeting ``tower_id``.

    Returns an empty tuple when the tower id is unknown, no metadata is
    stored, or the tower is unrestricted across all active events.
    """
    api_key = _TOWER_ID_TO_API_KEY.get(tower_id)
    if api_key is None:
        return ()
    try:
        race = await _scan_race_restrictions(api_key, sentinel_check=False)
        boss = await _scan_boss_restrictions(api_key, sentinel_check=False)
        ody = await _scan_odyssey_restrictions(api_key, sentinel_check=False)
        ch = await _scan_challenge_restrictions(api_key, sentinel_check=False)
    except Exception:  # noqa: BLE001 — degrade gracefully
        logger.exception("restriction scan failed for tower=%s", tower_id)
        return ()
    return tuple(race + boss + ody + ch)


async def get_active_event_restrictions_for_hero(
    hero_id: str,
) -> tuple[TowerRestrictionContext, ...]:
    """Scan active events for restrictions on ``hero_id``.

    Also checks the ``ChosenPrimaryHero`` sentinel — when set to
    ``max=0`` in an event, ALL heroes are banned regardless of which
    specific hero the caller is asking about. The sentinel is emitted
    as a separate ``TowerRestrictionContext`` with
    ``sentinel_all_heroes_banned=True`` so UI layers can phrase the
    "all heroes banned" wording appropriately. The hero-specific entry
    (if present) is still emitted separately.
    """
    api_key = _HERO_ID_TO_API_KEY.get(hero_id)
    if api_key is None:
        return ()
    try:
        race = await _scan_race_restrictions(api_key, sentinel_check=True)
        boss = await _scan_boss_restrictions(api_key, sentinel_check=True)
        ody = await _scan_odyssey_restrictions(api_key, sentinel_check=True)
        ch = await _scan_challenge_restrictions(api_key, sentinel_check=True)
    except Exception:  # noqa: BLE001 — degrade gracefully
        logger.exception("restriction scan failed for hero=%s", hero_id)
        return ()
    return tuple(race + boss + ody + ch)


@dataclass(frozen=True)
class BroadRestriction:
    """One restriction emitted by :func:`get_all_active_restrictions`.

    Carries the entity it applies to (id + api key + is_hero), the
    event context, and the stance bundle. Unlike
    :class:`TowerRestrictionContext`, this struct is keyed by entity
    rather than by event, so a single restriction row identifies both
    "what is restricted" and "where".
    """

    entity_id: str
    entity_api_key: str
    is_hero: bool
    event_kind: str
    event_id: str
    event_name: str
    end_ms: int | None
    fetched_at: datetime | None
    stance: Literal["banned", "limited", "path_blocked", "allowed"]
    max_count: int | None
    path1_blocked: int
    path2_blocked: int
    path3_blocked: int
    sentinel_all_heroes_banned: bool = False


async def get_all_active_restrictions(
    *,
    include_towers: bool = True,
    include_heroes: bool = True,
    max_rows: int = 64,
) -> tuple[BroadRestriction, ...]:
    """Public broad scan: every restriction across every active event.

    Iterates the known tower / hero id maps and composes the per-entity
    restriction scans. Deduplicates so the ``ChosenPrimaryHero`` sentinel
    only appears once per event even when multiple heroes are scanned.

    Bounded by ``max_rows`` (hard cap 256) so a misbehaving fetch can
    never blow out the AI prompt window. Returns ``()`` on any internal
    failure rather than raising.
    """
    bound = max(1, min(256, int(max_rows)))
    out: list[BroadRestriction] = []
    seen_sentinels: set[str] = set()
    try:
        if include_towers:
            for tower_id, api_key in _TOWER_ID_TO_API_KEY.items():
                for ctx in await get_active_event_restrictions_for_tower(tower_id):
                    if ctx.stance == "allowed":
                        continue
                    out.append(
                        BroadRestriction(
                            entity_id=tower_id,
                            entity_api_key=api_key,
                            is_hero=False,
                            event_kind=ctx.event_kind,
                            event_id=ctx.event_id,
                            event_name=ctx.event_name,
                            end_ms=ctx.end_ms,
                            fetched_at=ctx.fetched_at,
                            stance=ctx.stance,
                            max_count=ctx.max_count,
                            path1_blocked=ctx.path1_blocked,
                            path2_blocked=ctx.path2_blocked,
                            path3_blocked=ctx.path3_blocked,
                            sentinel_all_heroes_banned=False,
                        ),
                    )
                    if len(out) >= bound:
                        return tuple(out)
        if include_heroes:
            for hero_id, api_key in _HERO_ID_TO_API_KEY.items():
                for ctx in await get_active_event_restrictions_for_hero(hero_id):
                    if ctx.sentinel_all_heroes_banned:
                        sentinel_key = f"{ctx.event_kind}:{ctx.event_id}"
                        if sentinel_key in seen_sentinels:
                            continue
                        seen_sentinels.add(sentinel_key)
                    if ctx.stance == "allowed":
                        continue
                    out.append(
                        BroadRestriction(
                            entity_id=hero_id,
                            entity_api_key=api_key,
                            is_hero=True,
                            event_kind=ctx.event_kind,
                            event_id=ctx.event_id,
                            event_name=ctx.event_name,
                            end_ms=ctx.end_ms,
                            fetched_at=ctx.fetched_at,
                            stance=ctx.stance,
                            max_count=ctx.max_count,
                            path1_blocked=ctx.path1_blocked,
                            path2_blocked=ctx.path2_blocked,
                            path3_blocked=ctx.path3_blocked,
                            sentinel_all_heroes_banned=ctx.sentinel_all_heroes_banned,
                        ),
                    )
                    if len(out) >= bound:
                        return tuple(out)
    except Exception:  # noqa: BLE001 — degrade gracefully
        logger.exception("broad active-restriction scan failed")
        return ()
    return tuple(out)


# ---------------------------------------------------------------------------
# Leaderboards
# ---------------------------------------------------------------------------


_LEADERBOARD_LIMIT_CAP = 25


def _clamp_limit(limit: int) -> int:
    return max(1, min(_LEADERBOARD_LIMIT_CAP, int(limit)))


def _row_to_leaderboard(body: dict[str, Any]) -> LeaderboardRow | None:
    rank = body.get("rank")
    if not isinstance(rank, int) or rank < 1:
        return None
    score_parts = body.get("score_parts")
    score_parts_out = score_parts if isinstance(score_parts, list) else None
    return LeaderboardRow(
        rank=rank,
        display_name=str(body.get("display_name") or ""),
        score=body.get("score") if isinstance(body.get("score"), int) else None,
        score_parts=score_parts_out,
        submission_time_ms=(
            body.get("submission_time_ms")
            if isinstance(body.get("submission_time_ms"), int)
            else None
        ),
        profile_url=(
            body.get("profile_url")
            if isinstance(body.get("profile_url"), str)
            else None
        ),
    )


async def get_race_leaderboard(
    race_id: str,
    *,
    limit: int = 10,
) -> tuple[LeaderboardRow, ...]:
    """Top-N rows for one race, ordered by rank ASC.

    ``search_facts`` returns the newest rows first regardless of rank;
    this function filters by the ``raceID_rank_*`` entity_key prefix,
    sorts by rank, and clamps the limit at ``_LEADERBOARD_LIMIT_CAP``.
    """
    from utils.db import btd6_sources as btd6_db

    clamped = _clamp_limit(limit)
    prefix = f"{race_id}_rank_"
    raw = await btd6_db.search_facts(
        entity_kind="btd6_race_leaderboard_row",
        limit=200,
    )
    rows: list[LeaderboardRow] = []
    for row in raw:
        key = str(row.get("entity_key") or "")
        if not key.startswith(prefix):
            continue
        body = _coerce_body(row.get("body_json"))
        lb = _row_to_leaderboard(body)
        if lb is None:
            continue
        rows.append(lb)
    rows.sort(key=lambda r: r.rank)
    return tuple(rows[:clamped])


async def get_boss_leaderboard(
    boss_id: str,
    *,
    score_type: Literal["standard", "elite"] = "standard",
    team_size: int = 1,
    limit: int = 10,
) -> tuple[LeaderboardRow, ...]:
    """Top-N rows for one boss / score_type / team_size combo.

    Boss leaderboard entity_keys are composed as
    ``{bossID}_{score_type}_{teamSize}_rank_{n}``. Filter by that
    prefix, sort by rank ASC, clamp.
    """
    from utils.db import btd6_sources as btd6_db

    clamped = _clamp_limit(limit)
    prefix = f"{boss_id}_{score_type}_{team_size}_rank_"
    raw = await btd6_db.search_facts(
        entity_kind="btd6_boss_leaderboard_row",
        limit=200,
    )
    rows: list[LeaderboardRow] = []
    for row in raw:
        key = str(row.get("entity_key") or "")
        if not key.startswith(prefix):
            continue
        body = _coerce_body(row.get("body_json"))
        lb = _row_to_leaderboard(body)
        if lb is None:
            continue
        rows.append(lb)
    rows.sort(key=lambda r: r.rank)
    return tuple(rows[:clamped])


# ---------------------------------------------------------------------------
# Contested Territory tiles
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CTTilePlacement:
    """One CT tile, with its relic (if any) and decoded map position.

    ``relic_name`` is the raw Ninja Kiwi token; ``relic_id`` /
    ``relic_canonical`` are the matched catalog entry (``None`` when the
    relic isn't in the catalog or the tile carries no relic).
    ``position`` is the decoded hex location (``None`` for unparseable
    codes).
    """

    ct_id: str
    tile_id: str
    tile_type: str | None
    game_type: str | None
    relic_name: str | None
    relic_id: str | None
    relic_canonical: str | None
    fetched_at: datetime | None
    position: CTTilePosition | None


def _row_to_ct_placement(row: dict[str, Any]) -> CTTilePlacement | None:
    body = _coerce_body(row.get("body_json"))
    tile_id = body.get("tile_id")
    if not isinstance(tile_id, str) or not tile_id:
        return None
    raw_relic = body.get("relic_name")
    relic_name = raw_relic if isinstance(raw_relic, str) and raw_relic else None
    relic_id: str | None = None
    relic_canonical: str | None = None
    if relic_name is not None:
        from services import btd6_data_service

        entry = btd6_data_service.get_ct_relic_by_api_name(relic_name)
        if entry is not None:
            relic_id = entry.id
            relic_canonical = entry.canonical
    ct_id = body.get("ct_id")
    tile_type = body.get("type")
    game_type = body.get("game_type")
    return CTTilePlacement(
        ct_id=ct_id if isinstance(ct_id, str) else "",
        tile_id=tile_id,
        tile_type=tile_type if isinstance(tile_type, str) else None,
        game_type=game_type if isinstance(game_type, str) else None,
        relic_name=relic_name,
        relic_id=relic_id,
        relic_canonical=relic_canonical,
        fetched_at=row.get("fetched_at"),
        position=decode_tile(tile_id),
    )


async def get_ct_tiles(
    ct_id: str,
    *,
    relic: str | None = None,
    relics_only: bool = False,
) -> tuple[CTTilePlacement, ...]:
    """All tiles for one CT event, newest version per tile.

    ``relic`` filters to tiles carrying that relic (matched by catalog
    id / API name / canonical / alias, or raw ``relic_name`` as a
    fallback). ``relics_only`` drops non-relic tiles (Banner / Regular /
    TeamStart …).
    """
    from utils.db import btd6_sources as btd6_db

    target_id: str | None = None
    needle: str | None = None
    if relic is not None:
        from services import btd6_data_service

        entry = btd6_data_service.resolve_relic(relic)
        target_id = entry.id if entry is not None else None
        needle = relic.strip().lower()

    rows = await btd6_db.list_ct_tiles_for_event(ct_id)
    out: list[CTTilePlacement] = []
    for row in rows:
        placement = _row_to_ct_placement(row)
        if placement is None:
            continue
        if (relics_only or relic is not None) and placement.relic_name is None:
            continue
        if relic is not None and not _placement_matches_relic(
            placement,
            target_id,
            needle,
        ):
            continue
        out.append(placement)
    out.sort(key=lambda p: (p.position.ring if p.position else 99, p.tile_id))
    return tuple(out)


def _placement_matches_relic(
    placement: CTTilePlacement,
    target_id: str | None,
    needle: str | None,
) -> bool:
    if target_id is not None and placement.relic_id == target_id:
        return True
    if needle:
        for value in (
            placement.relic_name,
            placement.relic_id,
            placement.relic_canonical,
        ):
            if value and value.lower() == needle:
                return True
    return False


async def find_relic_locations(relic: str) -> tuple[CTTilePlacement, ...]:
    """Every active-CT tile carrying ``relic``, across all active events.

    ``relic`` accepts a catalog id, API name, canonical name, abbrev or
    alias. Returns an empty tuple when nothing active carries it.
    """
    out: list[CTTilePlacement] = []
    try:
        for evt in await get_active_events(("btd6_ct",)):
            out.extend(await get_ct_tiles(evt.entity_key, relic=relic))
    except Exception:  # noqa: BLE001 — degrade gracefully
        logger.exception("ct relic-location scan failed for relic=%s", relic)
        return ()
    return tuple(out)


__all__ = [
    "ActiveEventHeadline",
    "BroadRestriction",
    "CTTilePlacement",
    "LeaderboardRow",
    "TowerRestrictionContext",
    "find_relic_locations",
    "get_active_event_restrictions_for_hero",
    "get_active_event_restrictions_for_tower",
    "get_active_events",
    "get_ct_tiles",
    "get_all_active_restrictions",
    "get_boss_leaderboard",
    "get_newest_active_boss",
    "get_newest_active_race",
    "get_race_leaderboard",
    "list_active_boss_ids",
    "list_active_race_ids",
    "list_scheduled_parent_sources",
]
