"""Tests for the async ``build_status_embed`` Live facts block."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import discord
import pytest

from cogs.btd6._embeds import build_status_embed


@pytest.mark.asyncio
async def test_status_embed_has_seed_and_live_blocks(monkeypatch):
    from services import btd6_knowledge_service

    now = datetime.now(tz=timezone.utc)

    async def _summary():
        return (
            btd6_knowledge_service.FactKindSummary(
                entity_kind="btd6_event",
                fact_count=14,
                last_fetched_at=now - timedelta(minutes=45),
                bucket="fresh",
            ),
            btd6_knowledge_service.FactKindSummary(
                entity_kind="btd6_map",
                fact_count=78,
                last_fetched_at=now - timedelta(hours=2),
                bucket="fresh",
            ),
        )

    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        _summary,
    )

    embed = await build_status_embed()
    assert isinstance(embed, discord.Embed)
    names = [f.name for f in embed.fields]
    assert any("📚" in n for n in names), "expected a seed block"
    assert any("📊" in n for n in names), "expected a live-facts block"


@pytest.mark.asyncio
async def test_status_embed_empty_db_renders_placeholder(monkeypatch):
    from services import btd6_knowledge_service

    async def _empty():
        return ()

    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        _empty,
    )

    embed = await build_status_embed()
    live_field = next(f for f in embed.fields if "📊" in (f.name or ""))
    value = live_field.value or ""
    assert "No facts ingested yet" in value
    assert "refresh-source" in value


@pytest.mark.asyncio
async def test_status_embed_uses_useful_first_order(monkeypatch):
    """event → map → boss → race → challenge → odyssey → ct."""
    from services import btd6_knowledge_service

    now = datetime.now(tz=timezone.utc)

    # Intentionally pass them in reverse alphabetical / random order;
    # the builder must re-sort by useful-first.
    async def _summary():
        return tuple(
            btd6_knowledge_service.FactKindSummary(
                entity_kind=kind,
                fact_count=1,
                last_fetched_at=now,
                bucket="fresh",
            )
            for kind in (
                "btd6_ct",
                "btd6_odyssey",
                "btd6_challenge",
                "btd6_race",
                "btd6_boss",
                "btd6_map",
                "btd6_event",
            )
        )

    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        _summary,
    )

    embed = await build_status_embed()
    live_field = next(f for f in embed.fields if "📊" in (f.name or ""))
    value = live_field.value or ""

    # Each kind appears on its own line. Walk lines in display order and
    # assert event < map < boss < race < challenge < odyssey < ct.
    indices = {}
    for i, line in enumerate(value.splitlines()):
        for kind in (
            "event",
            "map",
            "boss",
            "race",
            "challenge",
            "odyssey",
            "ct",
        ):
            if f"`{kind:<10}`" in line:
                indices[kind] = i
    assert indices["event"] < indices["map"] < indices["boss"]
    assert indices["boss"] < indices["race"] < indices["challenge"]
    assert indices["challenge"] < indices["odyssey"] < indices["ct"]


@pytest.mark.asyncio
async def test_status_embed_uses_newest_fact_wording_not_source_health(monkeypatch):
    """Labels must distinguish entity-kind freshness from source-key health."""
    from services import btd6_knowledge_service

    async def _summary():
        return (
            btd6_knowledge_service.FactKindSummary(
                entity_kind="btd6_map",
                fact_count=10,
                last_fetched_at=datetime.now(tz=timezone.utc),
                bucket="fresh",
            ),
        )

    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        _summary,
    )

    embed = await build_status_embed()
    live_field = next(f for f in embed.fields if "📊" in (f.name or ""))
    value = (live_field.value or "").lower()
    assert "newest fact" in value, "expected 'newest fact X ago' wording"
    assert "source-health" not in value
    assert "source health" not in value


@pytest.mark.asyncio
async def test_status_embed_caps_rows_for_many_kinds(monkeypatch):
    """Many entity_kinds must stay within Discord's field-value limit."""
    from services import btd6_knowledge_service

    now = datetime.now(tz=timezone.utc)

    async def _summary():
        return tuple(
            btd6_knowledge_service.FactKindSummary(
                entity_kind=f"btd6_kind_{i:02d}",
                fact_count=1,
                last_fetched_at=now,
                bucket="fresh",
            )
            for i in range(25)
        )

    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        _summary,
    )

    embed = await build_status_embed()
    live_field = next(f for f in embed.fields if "📊" in (f.name or ""))
    value = live_field.value or ""
    # Stays under Discord's 1024-char field-value cap.
    assert len(value) <= 1024
    # And tells the user something was elided.
    assert "more)" in value


@pytest.mark.asyncio
async def test_status_embed_renders_never_bucket(monkeypatch):
    """A kind that has never been fetched renders with the ⚪ emoji."""
    from services import btd6_knowledge_service

    async def _summary():
        return (
            btd6_knowledge_service.FactKindSummary(
                entity_kind="btd6_race",
                fact_count=0,
                last_fetched_at=None,
                bucket="never",
            ),
        )

    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        _summary,
    )

    embed = await build_status_embed()
    live_field = next(f for f in embed.fields if "📊" in (f.name or ""))
    value = live_field.value or ""
    assert "⚪" in value
    assert "never fetched" in value
