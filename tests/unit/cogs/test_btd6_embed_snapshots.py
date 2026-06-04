"""Byte-identical pins for BTD6 embed output (PR 1).

The PR 1 acceptance bar is that every existing user-facing embed
renders byte-identically after the duplicate-helper consolidation —
except the panel's "Currently active" block, which now leads each row
with a per-kind freshness badge. These tests pin the relevant
invariants.

Snapshot tests for embed text are intentionally light: we assert
title, description, field count, key fragments, and footer rather than
storing serialized snapshots. That keeps the tests resilient to
formatter / dependency churn while still catching layout regressions.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import discord
import pytest

# ---------------------------------------------------------------------------
# source-health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_source_health_embed_uses_consolidated_badge(monkeypatch) -> None:
    from cogs.btd6._builders import build_source_health_embed
    from services import btd6_source_registry
    from services.btd6_source_registry import SourceHealth

    now = datetime.now(tz=timezone.utc)
    fake = SourceHealth(
        source_id=1,
        source_key="nk_btd6_races",
        source_name="Races",
        trust_tier=1,
        enabled=True,
        source_kind="api",
        last_fetched_at=now - timedelta(hours=2),
        fact_count=42,
        bucket="fresh",
    )
    monkeypatch.setattr(
        btd6_source_registry,
        "list_health",
        AsyncMock(return_value=[fake]),
    )

    embed = await build_source_health_embed(limit=25)
    assert isinstance(embed, discord.Embed)
    assert embed.title == "🐵 BTD6 — Source Health"
    field_value = embed.fields[0].value or ""
    # Bucket badge format pinned by _freshness_render.BUCKET_BADGE.
    assert "🟢 fresh" in field_value
    assert "facts=42" in field_value


# ---------------------------------------------------------------------------
# latest-data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_latest_data_embed_renders_header(monkeypatch) -> None:
    from cogs.btd6._builders import build_latest_data_embed
    from services import btd6_source_registry
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        btd6_source_registry,
        "list_all",
        AsyncMock(return_value=[]),
    )

    embed = await build_latest_data_embed()
    assert embed.title == "🐵 BTD6 — Latest Data"
    assert "No facts recorded yet." in (embed.description or "")


# ---------------------------------------------------------------------------
# live-events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_live_events_embed_unknown_kind_red(monkeypatch) -> None:
    from cogs.btd6._builders import build_live_events_embed

    embed = await build_live_events_embed("not-a-kind")
    assert embed.color == discord.Color.red()
    assert "isn't a known live-event kind" in (embed.description or "")


# ---------------------------------------------------------------------------
# event-detail
# ---------------------------------------------------------------------------


def test_event_detail_unknown_renders_red() -> None:
    from cogs.btd6._builders import build_event_detail_embed

    embed = build_event_detail_embed("btd6_race", "missing", row=None)
    assert embed.color == discord.Color.red()
    assert "No event found" in (embed.description or "")


def test_event_detail_window_field_present() -> None:
    from cogs.btd6._builders import build_event_detail_embed

    now = datetime.now(tz=timezone.utc)
    row = {
        "entity_kind": "btd6_race",
        "entity_key": "R42",
        "body_json": {
            "name": "Reversed Loop",
            "start_ms": int((now - timedelta(hours=1)).timestamp() * 1000),
            "end_ms": int((now + timedelta(hours=2)).timestamp() * 1000),
        },
        "fetched_at": now,
    }
    embed = build_event_detail_embed("btd6_race", "R42", row=row)
    names = [f.name for f in embed.fields]
    assert "Window" in names
    window_field = next(f for f in embed.fields if f.name == "Window")
    # `format_window_status` byte-identity is verified in
    # tests/unit/utils/test_btd6_event_window.py; here we only assert
    # the field renders the canonical "status: ..." prefix.
    assert "status:" in (window_field.value or "")


def test_event_detail_boss_shows_coverage_field() -> None:
    from cogs.btd6._builders import build_event_detail_embed
    from utils.btd6.coverage import AREA_BOSS, get_coverage

    row = {
        "entity_kind": "btd6_boss",
        "entity_key": "B7",
        "body_json": {"name": "Phayze"},
    }
    embed = build_event_detail_embed("btd6_boss", "B7", row=row)
    coverage_fields = [f for f in embed.fields if f.name == "Coverage"]
    assert coverage_fields, "boss event detail must surface a Coverage field"
    assert coverage_fields[0].value == get_coverage(AREA_BOSS).user_label


def test_event_detail_odyssey_shows_coverage_field() -> None:
    from cogs.btd6._builders import build_event_detail_embed
    from utils.btd6.coverage import AREA_ODYSSEY, get_coverage

    row = {
        "entity_kind": "btd6_odyssey",
        "entity_key": "O3",
        "body_json": {"name": "Tidal Surge"},
    }
    embed = build_event_detail_embed("btd6_odyssey", "O3", row=row)
    coverage_fields = [f for f in embed.fields if f.name == "Coverage"]
    assert coverage_fields, "odyssey event detail must surface a Coverage field"
    assert coverage_fields[0].value == get_coverage(AREA_ODYSSEY).user_label


def test_event_detail_race_has_no_coverage_field() -> None:
    # Races are not in the partial-coverage map, so no Coverage field on the
    # event-detail embed (leaderboard page-1 coverage is surfaced separately).
    from cogs.btd6._builders import build_event_detail_embed

    row = {
        "entity_kind": "btd6_race",
        "entity_key": "R1",
        "body_json": {"name": "Loop"},
    }
    embed = build_event_detail_embed("btd6_race", "R1", row=row)
    assert not [f for f in embed.fields if f.name == "Coverage"]


# ---------------------------------------------------------------------------
# status (build_status_embed uses _BUCKET_EMOJI via _freshness_render)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_status_embed_live_facts_use_consolidated_emoji(monkeypatch) -> None:
    from cogs.btd6._embeds import build_status_embed
    from services import btd6_knowledge_service
    from services.btd6_knowledge_service import FactKindSummary

    monkeypatch.setattr(btd6_knowledge_service, "data_version", lambda: "1.0")
    monkeypatch.setattr(btd6_knowledge_service, "game_version", lambda: "42.0")
    monkeypatch.setattr(btd6_knowledge_service, "list_towers", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_heroes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_maps", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_modes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_rounds", lambda: [])
    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        AsyncMock(
            return_value=(
                FactKindSummary(
                    entity_kind="btd6_race",
                    fact_count=5,
                    last_fetched_at=datetime.now(tz=timezone.utc),
                    bucket="fresh",
                ),
            ),
        ),
    )

    embed = await build_status_embed()
    # Live facts field should render the bucket emoji from the
    # consolidated _freshness_render.BUCKET_EMOJI mapping.
    live_field = next(f for f in embed.fields if "Live facts" in (f.name or ""))
    assert "🟢" in (live_field.value or "")


# ---------------------------------------------------------------------------
# tower / hero embeds — basic shape
# ---------------------------------------------------------------------------


def test_towers_embed_title() -> None:
    from cogs.btd6._embeds import build_towers_embed

    embed = build_towers_embed()
    assert embed.title == "🐵 BTD6 — Towers"


def test_heroes_embed_title() -> None:
    from cogs.btd6._embeds import build_heroes_embed

    embed = build_heroes_embed()
    assert embed.title == "🐵 BTD6 — Heroes"


def test_modes_embed_title() -> None:
    from cogs.btd6._embeds import build_modes_embed

    embed = build_modes_embed()
    assert embed.title == "🐵 BTD6 — Difficulties & Modes"
