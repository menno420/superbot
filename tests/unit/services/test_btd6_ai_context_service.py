"""Unit tests for ``services.btd6_ai_context_service``.

The facade wraps the existing BTD6 query services with an AI-safe
shape: every method is read-only, defensive, and length-bounded.
These tests cover happy paths, public-safety pins, freshness mapping,
URL stripping, and the "log + return empty" defensive contract.
"""

from __future__ import annotations

import ast
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services import btd6_ai_context_service as facade
from services import btd6_knowledge_api, btd6_live_query_service, btd6_source_registry
from services.btd6_knowledge_api import FactBundle
from services.btd6_live_query_service import (
    ActiveEventHeadline,
    BroadRestriction,
    LeaderboardRow,
)
from services.btd6_source_registry import SourceHealth

# ---------------------------------------------------------------------------
# Layering / private-helper pins
# ---------------------------------------------------------------------------


_FACADE_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "services"
    / "btd6_ai_context_service.py"
).read_text()


def test_facade_does_not_import_cogs_or_views():
    """Layering pin: the AI facade must never depend on cogs or views."""
    tree = ast.parse(_FACADE_SOURCE)
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").startswith(
                ("disbot.cogs", "cogs", "disbot.views", "views"),
            ):
                bad.append(node.module or "")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(
                    ("disbot.cogs", "cogs", "disbot.views", "views"),
                ):
                    bad.append(alias.name)
    assert not bad, f"facade imports view/cog modules: {bad}"


def test_facade_does_not_reach_into_private_scan_helpers():
    """Private-helper pin: no _scan_* references in the facade source."""
    assert not re.search(
        r"\b_scan_(race|boss|odyssey|challenge)_restrictions\b",
        _FACADE_SOURCE,
    )


# ---------------------------------------------------------------------------
# get_current_events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_events_happy_path(monkeypatch):
    fetched = datetime.now(tz=timezone.utc) - timedelta(minutes=15)
    headlines = (
        ActiveEventHeadline(
            entity_kind="btd6_race",
            entity_key="race_abc",
            name="Reversed Loop",
            start_ms=1700000000000,
            end_ms=1800000000000,
            fetched_at=fetched,
        ),
        ActiveEventHeadline(
            entity_kind="btd6_boss",
            entity_key="boss_xyz",
            name="Dreadbloon",
            start_ms=None,
            end_ms=None,
            fetched_at=fetched,
        ),
    )

    async def _stub():
        return headlines

    monkeypatch.setattr(btd6_live_query_service, "get_active_events", _stub)
    out = await facade.get_current_events()
    assert len(out) == 2
    assert out[0].entity_kind == "btd6_race"
    assert out[0].name == "Reversed Loop"
    assert out[0].freshness == "fresh"
    # Render produces a single line with provenance suffix.
    line = out[0].render()
    assert "race: Reversed Loop" in line
    assert "source: data.ninjakiwi.com" in line
    assert "fetched " in line


@pytest.mark.asyncio
async def test_get_current_events_returns_empty_on_failure(monkeypatch, caplog):
    async def _boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(btd6_live_query_service, "get_active_events", _boom)
    with caplog.at_level(logging.ERROR, logger="bot.services.btd6_ai_context"):
        out = await facade.get_current_events()
    assert out == ()
    assert any("get_current_events" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# get_event_details
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_event_details_roundtrip_from_current_events(monkeypatch):
    fetched = datetime.now(tz=timezone.utc)
    headlines = (
        ActiveEventHeadline(
            entity_kind="btd6_race",
            entity_key="race_abc",
            name="R1",
            start_ms=None,
            end_ms=None,
            fetched_at=fetched,
        ),
    )

    async def _stub(kinds=None):
        return headlines

    monkeypatch.setattr(btd6_live_query_service, "get_active_events", _stub)
    current = await facade.get_current_events()
    assert current
    detail = await facade.get_event_details(
        current[0].entity_kind,
        current[0].entity_key,
    )
    assert detail is not None
    assert detail.entity_key == "race_abc"
    assert detail.name == "R1"


@pytest.mark.asyncio
async def test_get_event_details_returns_none_when_missing(monkeypatch):
    async def _stub(kinds=None):
        return ()

    monkeypatch.setattr(btd6_live_query_service, "get_active_events", _stub)
    out = await facade.get_event_details("btd6_race", "unknown")
    assert out is None


@pytest.mark.asyncio
async def test_get_event_details_logs_and_returns_none_on_failure(monkeypatch, caplog):
    async def _boom(kinds=None):
        raise RuntimeError("nope")

    monkeypatch.setattr(btd6_live_query_service, "get_active_events", _boom)
    with caplog.at_level(logging.ERROR, logger="bot.services.btd6_ai_context"):
        out = await facade.get_event_details("btd6_race", "anything")
    assert out is None
    assert any("get_event_details" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# get_tower_summary / get_hero_summary
# ---------------------------------------------------------------------------


def _bundle(
    *,
    entity_kind: str,
    entity_key: str,
    body: dict,
    fetched_at: datetime | None = None,
) -> FactBundle:
    return FactBundle(
        fact_type=entity_kind,
        entity_kind=entity_kind,
        entity_key=entity_key,
        body=body,
        source_key="nk_btd6_towers",
        source_trust_tier=1,
        source_url="https://example",
        game_version=None,
        fetched_at=fetched_at or datetime.now(tz=timezone.utc),
        validated_at=None,
        freshness_status="fresh",
        confidence=1.0,
    )


@pytest.mark.asyncio
async def test_get_tower_summary_strips_url_keys(monkeypatch):
    body_with_urls = {
        "name": "Super Monkey",
        "cost": 2500,
        "creator_url": "https://leak/creator",
        "profile_url": "https://leak/profile",
        "thumbnail_url": "https://leak/thumb",
        "metadata_url": "https://leak/meta",
    }

    async def _stub(tower_id):
        return _bundle(entity_kind="tower", entity_key=tower_id, body=body_with_urls)

    monkeypatch.setattr(btd6_knowledge_api, "get_tower", _stub)
    out = await facade.get_tower_summary("super_monkey")
    assert out is not None
    assert "creator_url" not in out.body
    assert "profile_url" not in out.body
    assert "thumbnail_url" not in out.body
    assert "metadata_url" not in out.body
    assert out.body["cost"] == 2500
    assert "Super Monkey" in out.render()


@pytest.mark.asyncio
async def test_get_tower_summary_none_when_missing(monkeypatch):
    async def _stub(tower_id):
        return None

    monkeypatch.setattr(btd6_knowledge_api, "get_tower", _stub)
    assert await facade.get_tower_summary("unknown") is None


@pytest.mark.asyncio
async def test_get_hero_summary_strips_url_keys(monkeypatch):
    body = {"name": "Quincy", "level1_ability": "Storm of Arrows", "url": "https://x"}

    async def _stub(hero_id):
        return _bundle(entity_kind="hero", entity_key=hero_id, body=body)

    monkeypatch.setattr(btd6_knowledge_api, "get_hero", _stub)
    out = await facade.get_hero_summary("quincy")
    assert out is not None
    assert "url" not in out.body
    assert "Quincy" in out.render()


@pytest.mark.asyncio
async def test_tower_summary_logs_and_returns_none_on_failure(monkeypatch, caplog):
    async def _boom(tower_id):
        raise ValueError("boom")

    monkeypatch.setattr(btd6_knowledge_api, "get_tower", _boom)
    with caplog.at_level(logging.ERROR, logger="bot.services.btd6_ai_context"):
        out = await facade.get_tower_summary("super_monkey")
    assert out is None
    assert any("get_tower_summary" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# get_active_restrictions
# ---------------------------------------------------------------------------


def _broad(
    entity_id: str,
    *,
    is_hero: bool,
    stance: str = "banned",
    sentinel: bool = False,
) -> BroadRestriction:
    return BroadRestriction(
        entity_id=entity_id,
        entity_api_key=entity_id.title().replace("_", ""),
        is_hero=is_hero,
        event_kind="btd6_race",
        event_id="race1",
        event_name="Test Race",
        end_ms=None,
        fetched_at=datetime.now(tz=timezone.utc),
        stance=stance,  # type: ignore[arg-type]
        max_count=0 if stance == "banned" else 1,
        path1_blocked=0,
        path2_blocked=0,
        path3_blocked=0,
        sentinel_all_heroes_banned=sentinel,
    )


@pytest.mark.asyncio
async def test_get_active_restrictions_scope_filtering(monkeypatch):
    rows = (
        _broad("super_monkey", is_hero=False, stance="banned"),
        _broad("quincy", is_hero=True, stance="limited"),
    )

    async def _stub(*, include_towers, include_heroes, max_rows):
        out = []
        for row in rows:
            if row.is_hero and not include_heroes:
                continue
            if not row.is_hero and not include_towers:
                continue
            out.append(row)
        return tuple(out)

    monkeypatch.setattr(btd6_live_query_service, "get_all_active_restrictions", _stub)

    all_r = await facade.get_active_restrictions("all")
    towers = await facade.get_active_restrictions("towers")
    heroes = await facade.get_active_restrictions("heroes")
    assert {r.entity_id for r in all_r} == {"super_monkey", "quincy"}
    assert [r.entity_id for r in towers] == ["super_monkey"]
    assert [r.entity_id for r in heroes] == ["quincy"]


@pytest.mark.asyncio
async def test_restriction_render_uses_event_label_and_provenance(monkeypatch):
    rows = (
        _broad("super_monkey", is_hero=False, stance="banned"),
        _broad("quincy", is_hero=True, stance="banned", sentinel=True),
    )

    async def _stub(*, include_towers, include_heroes, max_rows):
        return rows

    monkeypatch.setattr(btd6_live_query_service, "get_all_active_restrictions", _stub)
    out = await facade.get_active_restrictions("all")
    tower_line = out[0].render()
    sentinel_line = out[1].render()
    assert "super_monkey" in tower_line
    assert "race 'Test Race'" in tower_line
    assert "source: data.ninjakiwi.com" in tower_line
    assert "All heroes are banned" in sentinel_line


@pytest.mark.asyncio
async def test_active_restrictions_logs_and_returns_empty_on_failure(
    monkeypatch,
    caplog,
):
    async def _boom(*, include_towers, include_heroes, max_rows):
        raise RuntimeError("bad")

    monkeypatch.setattr(btd6_live_query_service, "get_all_active_restrictions", _boom)
    with caplog.at_level(logging.ERROR, logger="bot.services.btd6_ai_context"):
        out = await facade.get_active_restrictions("all")
    assert out == ()
    assert any("get_active_restrictions" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# get_leaderboard_summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_leaderboard_summary_race_drops_profile_url(monkeypatch):
    rows = (
        LeaderboardRow(
            rank=1,
            display_name="Alice",
            score=100,
            score_parts=None,
            submission_time_ms=None,
            profile_url="https://leak/alice",
        ),
        LeaderboardRow(
            rank=2,
            display_name="Bob",
            score=90,
            score_parts=None,
            submission_time_ms=None,
            profile_url="https://leak/bob",
        ),
    )

    async def _stub(race_id, *, limit):
        return rows[:limit]

    monkeypatch.setattr(btd6_live_query_service, "get_race_leaderboard", _stub)
    out = await facade.get_leaderboard_summary("btd6_race", "race1", limit=2)
    assert out is not None
    # LeaderboardEntry must not carry a profile_url attribute at all.
    assert not any(hasattr(e, "profile_url") for e in out.entries)
    assert [e.rank for e in out.entries] == [1, 2]
    assert [e.display_name for e in out.entries] == ["Alice", "Bob"]


@pytest.mark.asyncio
async def test_get_leaderboard_summary_unknown_kind_returns_none(monkeypatch):
    async def _boss(boss_id, *, limit):
        return ()

    monkeypatch.setattr(btd6_live_query_service, "get_boss_leaderboard", _boss)
    out = await facade.get_leaderboard_summary("btd6_odyssey", "x", limit=3)  # type: ignore[arg-type]
    assert out is None


@pytest.mark.asyncio
async def test_get_leaderboard_summary_clamps_limit(monkeypatch):
    captured: dict[str, int] = {}

    async def _stub(race_id, *, limit):
        captured["limit"] = limit
        return ()

    monkeypatch.setattr(btd6_live_query_service, "get_race_leaderboard", _stub)
    await facade.get_leaderboard_summary("btd6_race", "x", limit=999)
    assert captured["limit"] == 10


# ---------------------------------------------------------------------------
# get_source_status — PUBLIC-SAFETY PINS
# ---------------------------------------------------------------------------


def _health(
    *,
    sid: int = 1,
    key: str = "nk_btd6_races",
    name: str = "Races",
    tier: int = 1,
    enabled: bool = True,
    bucket: str = "fresh",
    fetched_at: datetime | None = None,
    fact_count: int = 12,
) -> SourceHealth:
    return SourceHealth(
        source_id=sid,
        source_key=key,
        source_name=name,
        trust_tier=tier,
        enabled=enabled,
        source_kind="official_api",
        last_fetched_at=fetched_at,
        fact_count=fact_count,
        bucket=bucket,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_get_source_status_public_safe_shape(monkeypatch):
    rows = [
        _health(
            key="nk_btd6_races",
            name="Races",
            fetched_at=datetime.now(tz=timezone.utc),
            bucket="fresh",
            fact_count=3,
        ),
        _health(
            sid=2,
            key="nk_btd6_bosses",
            name="Bosses",
            fetched_at=None,
            bucket="never",
            fact_count=0,
        ),
    ]

    async def _stub(*, limit):
        return rows[:limit]

    monkeypatch.setattr(btd6_source_registry, "list_health", _stub)
    out = await facade.get_source_status()
    assert len(out) == 2
    # Field-level pin: dataclass exposes nothing internal.
    for s in out:
        assert not hasattr(s, "source_id")
        assert not hasattr(s, "base_url")
        assert not hasattr(s, "path_template")
        assert not hasattr(s, "full_url")
        assert not hasattr(s, "raw_body_hash")
        assert not hasattr(s, "created_by")
        assert not hasattr(s, "updated_by")
    # Rendered text never leaks URLs / hashes / actor IDs.
    rendered = "\n".join(s.render() for s in out)
    assert not re.search(r"https?://", rendered)
    assert "_hash" not in rendered
    assert not re.search(r"_by\b", rendered)
    assert "path_template" not in rendered
    assert "path_params" not in rendered


@pytest.mark.asyncio
async def test_get_source_status_freshness_passthrough(monkeypatch):
    now = datetime.now(tz=timezone.utc)
    rows = [
        _health(key="a", fetched_at=now, bucket="fresh"),
        _health(key="b", fetched_at=now - timedelta(days=1), bucket="aging"),
        _health(key="c", fetched_at=now - timedelta(days=7), bucket="stale"),
        _health(key="d", fetched_at=None, bucket="never"),
    ]

    async def _stub(*, limit):
        return rows

    monkeypatch.setattr(btd6_source_registry, "list_health", _stub)
    out = await facade.get_source_status()
    assert [s.freshness for s in out] == ["fresh", "aging", "stale", "never"]


@pytest.mark.asyncio
async def test_get_source_status_logs_and_returns_empty_on_failure(monkeypatch, caplog):
    async def _boom(*, limit):
        raise RuntimeError("nope")

    monkeypatch.setattr(btd6_source_registry, "list_health", _boom)
    with caplog.at_level(logging.ERROR, logger="bot.services.btd6_ai_context"):
        out = await facade.get_source_status()
    assert out == ()
    assert any("get_source_status" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# search_btd6_facts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_btd6_facts_filters_by_query(monkeypatch):
    bundles = [
        _bundle(
            entity_kind="tower",
            entity_key="super_monkey",
            body={"name": "Super Monkey"},
        ),
        _bundle(
            entity_kind="tower",
            entity_key="dart_monkey",
            body={"name": "Dart Monkey"},
        ),
    ]

    async def _stub(*, fact_type=None, entity_kind=None, limit):
        return bundles[:limit]

    monkeypatch.setattr(btd6_knowledge_api, "search_facts", _stub)
    out = await facade.search_btd6_facts("super")
    assert len(out) == 1
    assert out[0].entity_key == "super_monkey"


@pytest.mark.asyncio
async def test_search_btd6_facts_clamps_limit(monkeypatch):
    captured: dict[str, int] = {}

    async def _stub(*, fact_type=None, entity_kind=None, limit):
        captured["limit"] = limit
        return []

    monkeypatch.setattr(btd6_knowledge_api, "search_facts", _stub)
    await facade.search_btd6_facts("anything", limit=999)
    assert captured["limit"] == 10


@pytest.mark.asyncio
async def test_search_btd6_facts_logs_and_returns_empty_on_failure(monkeypatch, caplog):
    async def _boom(*, fact_type=None, entity_kind=None, limit):
        raise RuntimeError("bad")

    monkeypatch.setattr(btd6_knowledge_api, "search_facts", _boom)
    with caplog.at_level(logging.ERROR, logger="bot.services.btd6_ai_context"):
        out = await facade.search_btd6_facts("anything")
    assert out == ()
    assert any("search_btd6_facts" in r.message for r in caplog.records)
