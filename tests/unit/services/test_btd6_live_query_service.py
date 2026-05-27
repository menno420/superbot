"""Facade behavior for ``services.btd6_live_query_service``.

Tests the boring shape: tuple return for active events, sync source
list, leaderboard rank ordering, limit clamping. Restriction-scanning
and integration with fixtures live in a separate file.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone

import pytest

from services import btd6_live_query_service as live

# ---------------------------------------------------------------------------
# Sync surface
# ---------------------------------------------------------------------------


def test_list_scheduled_parent_sources_is_sync():
    assert not inspect.iscoroutinefunction(live.list_scheduled_parent_sources)


def test_list_scheduled_parent_sources_matches_canonical():
    from services import btd6_ingestion_sources

    assert (
        live.list_scheduled_parent_sources()
        == btd6_ingestion_sources.parent_source_keys()
    )


# ---------------------------------------------------------------------------
# get_active_events — tuple shape preserves multiple events per kind
# ---------------------------------------------------------------------------


def _race_index_row(entity_key, name, end_ms=None):
    body = {"name": name}
    if end_ms is not None:
        body["end_ms"] = end_ms
    return {
        "entity_kind": "btd6_race",
        "entity_key": entity_key,
        "fact_type": "btd6.races_index",
        "body_json": body,
        "fetched_at": datetime.now(tz=timezone.utc),
    }


@pytest.mark.asyncio
async def test_get_active_events_returns_tuple(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    rows = [
        _race_index_row("RaceA_abc", "Race A"),
        _race_index_row("RaceB_def", "Race B"),
    ]

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        if entity_kind == "btd6_race":
            return rows
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    out = await live.get_active_events(("btd6_race",))
    assert isinstance(out, tuple)
    assert len(out) == 2
    assert out[0].entity_key == "RaceA_abc"
    assert out[0].name == "Race A"
    assert out[1].entity_key == "RaceB_def"


@pytest.mark.asyncio
async def test_get_active_events_excludes_ended(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    past = int(datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    future = int(datetime(2100, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    rows = [
        _race_index_row("Ended", "Ended", end_ms=past),
        _race_index_row("Active", "Active", end_ms=future),
    ]

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        return rows

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    out = await live.get_active_events(("btd6_race",))
    keys = [evt.entity_key for evt in out]
    assert "Ended" not in keys
    assert "Active" in keys


@pytest.mark.asyncio
async def test_get_newest_active_race(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        if entity_kind == "btd6_race":
            return [_race_index_row("FirstRace", "First")]
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    race = await live.get_newest_active_race()
    assert race is not None
    assert race.entity_key == "FirstRace"


@pytest.mark.asyncio
async def test_get_newest_active_boss_none_when_empty(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    assert await live.get_newest_active_boss() is None


# ---------------------------------------------------------------------------
# Leaderboards — rank ASC, clamping, invalid-rank exclusion
# ---------------------------------------------------------------------------


def _race_lb_row(race_id, rank, score=100):
    return {
        "entity_kind": "btd6_race_leaderboard_row",
        "entity_key": f"{race_id}_rank_{rank}",
        "body_json": {
            "race_id": race_id,
            "rank": rank,
            "display_name": f"player{rank}",
            "score": score,
            "submission_time_ms": 1700000000000,
            "profile_url": "https://example.invalid",
        },
        "fetched_at": datetime.now(tz=timezone.utc),
    }


@pytest.mark.asyncio
async def test_race_leaderboard_sorts_rank_ascending(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    # Return rows out of order to confirm in-facade sort.
    raw = [
        _race_lb_row("R1", 3),
        _race_lb_row("R1", 1),
        _race_lb_row("R1", 2),
    ]

    async def _search(*, fact_type=None, entity_kind=None, limit=200):
        return raw

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    out = await live.get_race_leaderboard("R1")
    ranks = [r.rank for r in out]
    assert ranks == [1, 2, 3]


@pytest.mark.asyncio
async def test_race_leaderboard_filters_by_race_id(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    raw = [
        _race_lb_row("R1", 1),
        _race_lb_row("R2", 1),
    ]

    async def _search(*, fact_type=None, entity_kind=None, limit=200):
        return raw

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    out = await live.get_race_leaderboard("R1")
    assert len(out) == 1
    assert out[0].display_name == "player1"


@pytest.mark.asyncio
async def test_race_leaderboard_excludes_invalid_rank(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    bad = {
        "entity_kind": "btd6_race_leaderboard_row",
        "entity_key": "R1_rank_NaN",
        "body_json": {"rank": "not-a-number", "display_name": "x"},
        "fetched_at": datetime.now(tz=timezone.utc),
    }
    good = _race_lb_row("R1", 1)

    async def _search(*, fact_type=None, entity_kind=None, limit=200):
        return [bad, good]

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    out = await live.get_race_leaderboard("R1")
    assert len(out) == 1
    assert out[0].rank == 1


@pytest.mark.asyncio
async def test_race_leaderboard_clamps_limit(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    raw = [_race_lb_row("R1", i) for i in range(1, 30)]

    async def _search(*, fact_type=None, entity_kind=None, limit=200):
        return raw

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    out_high = await live.get_race_leaderboard("R1", limit=100)
    assert len(out_high) == 25  # cap
    out_low = await live.get_race_leaderboard("R1", limit=0)
    assert len(out_low) == 1  # floor


@pytest.mark.asyncio
async def test_boss_leaderboard_filters_by_score_type_and_team_size(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    raw = [
        {
            "entity_kind": "btd6_boss_leaderboard_row",
            "entity_key": "Boss1_standard_1_rank_1",
            "body_json": {"rank": 1, "display_name": "alice"},
            "fetched_at": datetime.now(tz=timezone.utc),
        },
        {
            "entity_kind": "btd6_boss_leaderboard_row",
            "entity_key": "Boss1_elite_1_rank_1",
            "body_json": {"rank": 1, "display_name": "bob"},
            "fetched_at": datetime.now(tz=timezone.utc),
        },
        {
            "entity_kind": "btd6_boss_leaderboard_row",
            "entity_key": "Boss1_standard_4_rank_1",
            "body_json": {"rank": 1, "display_name": "carol"},
            "fetched_at": datetime.now(tz=timezone.utc),
        },
    ]

    async def _search(*, fact_type=None, entity_kind=None, limit=200):
        return raw

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    out = await live.get_boss_leaderboard("Boss1")
    assert len(out) == 1
    assert out[0].display_name == "alice"  # standard solo by default

    elite = await live.get_boss_leaderboard("Boss1", score_type="elite")
    assert len(elite) == 1
    assert elite[0].display_name == "bob"


@pytest.mark.asyncio
async def test_unknown_tower_returns_empty():
    out = await live.get_active_event_restrictions_for_tower("not_a_real_tower")
    assert out == ()


@pytest.mark.asyncio
async def test_unknown_hero_returns_empty():
    out = await live.get_active_event_restrictions_for_hero("not_a_real_hero")
    assert out == ()
