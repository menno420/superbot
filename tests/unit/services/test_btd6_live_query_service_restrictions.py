"""Restriction scanning against real Ninja Kiwi fixtures.

Uses the bundled Reversed Loop race-metadata fixture (43-entry
_towers array) to verify per-tower / per-hero stance decoding, and a
synthetic boss-metadata payload to assert the parent-fallback rule
uses ``body_json["boss_id"]`` rather than ``entity_key.split("_")[0]``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from services import btd6_live_query_service as live
from services.btd6_live_query_service import TowerRestrictionContext

_FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "ninjakiwi"


def _race_metadata_body() -> dict[str, Any]:
    with (
        _FIXTURE_ROOT / "btd6_races_Reversed_Loop_mpbd7tcu_metadata.json"
    ).open() as fh:
        return json.load(fh)["body"]


def _race_index_row(entity_key: str, name: str) -> dict[str, Any]:
    return {
        "entity_kind": "btd6_race",
        "entity_key": entity_key,
        "fact_type": "btd6.races_index",
        "body_json": {"name": name},
        "fetched_at": datetime.now(tz=timezone.utc),
    }


@pytest.mark.asyncio
async def test_wizard_monkey_banned_in_reversed_loop(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    # NOTE: ``wizard_monkey`` is not in the current static seed
    # (data/btd6/towers.json), so the facade's lookup map doesn't know
    # the API key. We override the map for this test to verify the
    # scanner path; the production scanner would skip unknown ids.
    monkeypatch.setitem(live._TOWER_ID_TO_API_KEY, "wizard_monkey", "WizardMonkey")

    body = _race_metadata_body()

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        if entity_kind == "btd6_race":
            return [_race_index_row("mpbd7tcu", "Reversed Loop")]
        return []

    async def _get_latest_fact(fact_type, entity_kind, entity_key):
        if fact_type == "btd6.race_metadata" and entity_kind == "btd6_race":
            return {
                "entity_kind": "btd6_race",
                "entity_key": entity_key,
                "fact_type": "btd6.race_metadata",
                "body_json": body,
                "fetched_at": datetime.now(tz=timezone.utc),
            }
        return None

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)

    out = await live.get_active_event_restrictions_for_tower("wizard_monkey")
    assert out, "expected a restriction for WizardMonkey in the Reversed Loop fixture"
    # WizardMonkey has max=0 in the fixture → banned.
    assert any(ctx.stance == "banned" for ctx in out)


@pytest.mark.asyncio
async def test_dart_monkey_in_reversed_loop_is_classified(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    body = _race_metadata_body()

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        if entity_kind == "btd6_race":
            return [_race_index_row("mpbd7tcu", "Reversed Loop")]
        return []

    async def _get_latest_fact(fact_type, entity_kind, entity_key):
        if fact_type == "btd6.race_metadata":
            return {
                "entity_kind": "btd6_race",
                "entity_key": entity_key,
                "fact_type": "btd6.race_metadata",
                "body_json": body,
                "fetched_at": datetime.now(tz=timezone.utc),
            }
        return None

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)

    out = await live.get_active_event_restrictions_for_tower("dart_monkey")
    # The fixture lists DartMonkey — could be allowed, limited, or
    # path-blocked. Either way the facade must classify it without
    # raising; we assert the call returned (empty tuple if allowed).
    assert isinstance(out, tuple)


@pytest.mark.asyncio
async def test_chosen_primary_hero_sentinel_emitted(monkeypatch):
    """When ChosenPrimaryHero is max=0, hero queries get a sentinel row."""
    from utils.db import btd6_sources as btd6_db

    body = _race_metadata_body()
    # ChosenPrimaryHero IS max=0 in the Reversed Loop fixture.

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        if entity_kind == "btd6_race":
            return [_race_index_row("mpbd7tcu", "Reversed Loop")]
        return []

    async def _get_latest_fact(fact_type, entity_kind, entity_key):
        if fact_type == "btd6.race_metadata":
            return {
                "entity_kind": "btd6_race",
                "entity_key": entity_key,
                "fact_type": "btd6.race_metadata",
                "body_json": body,
                "fetched_at": datetime.now(tz=timezone.utc),
            }
        return None

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)

    out = await live.get_active_event_restrictions_for_hero("quincy")
    assert any(ctx.sentinel_all_heroes_banned for ctx in out), (
        "Expected ChosenPrimaryHero sentinel to surface as a separate "
        "TowerRestrictionContext with sentinel_all_heroes_banned=True"
    )


@pytest.mark.asyncio
async def test_missing_towers_array_returns_empty(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        if entity_kind == "btd6_race":
            return [_race_index_row("X", "Empty Race")]
        return []

    async def _get_latest_fact(fact_type, entity_kind, entity_key):
        return {
            "entity_kind": "btd6_race",
            "entity_key": entity_key,
            "fact_type": "btd6.race_metadata",
            "body_json": {"name": "Empty Race"},  # no _towers
            "fetched_at": datetime.now(tz=timezone.utc),
        }

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)

    out = await live.get_active_event_restrictions_for_tower("dart_monkey")
    assert out == ()


@pytest.mark.asyncio
async def test_missing_window_does_not_break_scan(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        if entity_kind == "btd6_race":
            return [_race_index_row("X", "Windowless")]  # no end_ms
        return []

    async def _get_latest_fact(fact_type, entity_kind, entity_key):
        return {
            "entity_kind": "btd6_race",
            "entity_key": entity_key,
            "fact_type": "btd6.race_metadata",
            "body_json": {
                "_towers": [{"tower": "DartMonkey", "max": 0, "isHero": False}],
            },
            "fetched_at": datetime.now(tz=timezone.utc),
        }

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)

    out = await live.get_active_event_restrictions_for_tower("dart_monkey")
    assert out
    assert out[0].stance == "banned"
    assert out[0].end_ms is None


@pytest.mark.asyncio
async def test_boss_metadata_parent_resolution_uses_body_field(monkeypatch):
    """Regression: boss IDs can contain underscores. Parent resolution
    must read ``body_json["boss_id"]`` rather than split the entity_key.
    """
    from utils.db import btd6_sources as btd6_db

    boss_id_with_underscore = "Diamond_back_5"
    metadata_entity_key = f"{boss_id_with_underscore}_standard"

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        if entity_kind == "btd6_boss":
            return [
                {
                    "entity_kind": "btd6_boss",
                    "entity_key": boss_id_with_underscore,
                    "fact_type": "btd6.bosses_index",
                    "body_json": {"name": "Diamondback V"},
                    "fetched_at": datetime.now(tz=timezone.utc),
                },
            ]
        return []

    async def _get_latest_fact(fact_type, entity_kind, entity_key):
        if fact_type == "btd6.boss_metadata":
            # Crucially: body_json has the explicit boss_id.
            return {
                "entity_kind": "btd6_boss_difficulty",
                "entity_key": entity_key,
                "fact_type": "btd6.boss_metadata",
                "body_json": {
                    "boss_id": boss_id_with_underscore,
                    "difficulty": "standard",
                    "_towers": [
                        {"tower": "DartMonkey", "max": 0, "isHero": False},
                    ],
                },
                "fetched_at": datetime.now(tz=timezone.utc),
            }
        return None

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)

    out = await live.get_active_event_restrictions_for_tower("dart_monkey")
    assert out
    boss_restriction = next(
        (ctx for ctx in out if ctx.event_kind == "btd6_boss_difficulty"),
        None,
    )
    assert boss_restriction is not None
    # event_id is the full composed key, and event_name comes from the
    # parent index — proving body_json["boss_id"] was consulted (not a
    # left-split that would have produced "Diamond").
    assert boss_restriction.event_id == metadata_entity_key
    assert boss_restriction.event_name == "Diamondback V"


@pytest.mark.asyncio
async def test_jsonb_double_encoded_body_is_decoded(monkeypatch):
    """Legacy double-encoded rows round-trip as JSON strings; the scanner
    must decode them via _coerce_body instead of failing silently.
    """
    from utils.db import btd6_sources as btd6_db

    async def _search(*, fact_type=None, entity_kind=None, limit=50):
        if entity_kind == "btd6_race":
            return [_race_index_row("X", "Legacy Race")]
        return []

    async def _get_latest_fact(fact_type, entity_kind, entity_key):
        return {
            "entity_kind": "btd6_race",
            "entity_key": entity_key,
            "fact_type": "btd6.race_metadata",
            # Double-encoded as a JSON string instead of a dict.
            "body_json": json.dumps(
                {
                    "_towers": [{"tower": "DartMonkey", "max": 0, "isHero": False}],
                }
            ),
            "fetched_at": datetime.now(tz=timezone.utc),
        }

    monkeypatch.setattr(btd6_db, "search_facts", _search)
    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)

    out = await live.get_active_event_restrictions_for_tower("dart_monkey")
    assert out
    assert out[0].stance == "banned"


def test_restriction_dataclass_is_immutable():
    ctx = TowerRestrictionContext(
        event_kind="btd6_race",
        event_id="r",
        event_name="r",
        end_ms=None,
        fetched_at=None,
        stance="banned",
        max_count=0,
        path1_blocked=0,
        path2_blocked=0,
        path3_blocked=0,
        is_hero=False,
    )
    with pytest.raises(Exception):  # frozen dataclass raises FrozenInstanceError
        ctx.stance = "allowed"  # type: ignore[misc]
