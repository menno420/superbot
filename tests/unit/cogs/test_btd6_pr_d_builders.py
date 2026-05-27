"""PR-D embed builder tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import discord
import pytest

from cogs.btd6._builders import (
    build_grounding_embed,
    build_latest_data_embed,
    build_source_health_embed,
)
from services import btd6_source_registry as health_svc


def _now():
    return datetime.now(tz=timezone.utc)


@pytest.mark.asyncio
async def test_source_health_embed_renders_each_source(monkeypatch):
    now = _now()

    async def _fake(*, limit=25):
        return [
            health_svc.SourceHealth(
                source_id=1,
                source_key="nk_btd6_races",
                source_name="Races",
                trust_tier=1,
                enabled=True,
                source_kind="official_api",
                last_fetched_at=now - timedelta(hours=1),
                fact_count=12,
                bucket="fresh",
            ),
            health_svc.SourceHealth(
                source_id=2,
                source_key="nk_btd6_bosses",
                source_name="Bosses",
                trust_tier=1,
                enabled=False,
                source_kind="official_api",
                last_fetched_at=None,
                fact_count=0,
                bucket="never",
            ),
        ]

    monkeypatch.setattr(health_svc, "list_health", _fake)

    embed = await build_source_health_embed()
    assert isinstance(embed, discord.Embed)
    blob = "\n".join(f.name + " " + f.value for f in embed.fields)
    assert "nk_btd6_races" in blob
    assert "nk_btd6_bosses" in blob
    assert "🟢 fresh" in blob
    assert "⚪ never" in blob
    assert "facts=12" in blob


@pytest.mark.asyncio
async def test_source_health_embed_handles_empty(monkeypatch):
    async def _fake(*, limit=25):
        return []

    monkeypatch.setattr(health_svc, "list_health", _fake)

    embed = await build_source_health_embed()
    assert "No BTD6 sources" in (embed.description or "")


@pytest.mark.asyncio
async def test_latest_data_embed_groups_by_entity_kind(monkeypatch):
    from services import btd6_source_registry
    from utils.db import btd6_sources as btd6_db

    now = _now()

    async def _fake(*, limit=50, **_kw):
        return [
            {
                "id": 1,
                "source_id": 1,
                "fact_type": "race_metadata",
                "entity_kind": "race",
                "entity_key": "Reversed_Loop",
                "body_json": {},
                "game_version": "44.0",
                "fetched_at": now,
                "validated_at": now,
                "confidence": 1.0,
                "version": 1,
            },
            {
                "id": 2,
                "source_id": 2,
                "fact_type": "boss_metadata",
                "entity_kind": "boss",
                "entity_key": "Diamondback5",
                "body_json": {},
                "game_version": "44.0",
                "fetched_at": now - timedelta(hours=2),
                "validated_at": now,
                "confidence": 1.0,
                "version": 1,
            },
        ]

    async def _list_all(*, limit=100):
        return [
            {"id": 1, "source_key": "nk_btd6_races"},
            {"id": 2, "source_key": "nk_btd6_bosses"},
        ]

    monkeypatch.setattr(btd6_db, "search_facts", _fake)
    monkeypatch.setattr(btd6_source_registry, "list_all", _list_all)

    embed = await build_latest_data_embed()
    names = {f.name for f in embed.fields}
    assert "`race`" in names
    assert "`boss`" in names


@pytest.mark.asyncio
async def test_grounding_embed_returns_string_when_no_match(monkeypatch):
    from services import ai_decision_audit_service

    async def _fake_q(_guild_id, **_kw):
        return [{"message_id": 1, "decision": "allowed", "reason_code": "none"}]

    monkeypatch.setattr(ai_decision_audit_service, "query", _fake_q)

    out = await build_grounding_embed(guild_id=1, message_id=999)
    assert isinstance(out, str)
    assert "999" in out


@pytest.mark.asyncio
async def test_grounding_embed_renders_audit_fields(monkeypatch):
    from services import ai_decision_audit_service

    async def _fake_q(_guild_id, **_kw):
        return [
            {
                "message_id": 42,
                "decision": "replied",
                "reason_code": "none",
                "task": "btd6.answer",
                "route": "btd6.answer",
                "provider": "openai",
                "model": "gpt-4",
                "policy_snapshot_hash": "ff",
                "instruction_profile_ids": [5, 6],
            },
        ]

    monkeypatch.setattr(ai_decision_audit_service, "query", _fake_q)

    embed = await build_grounding_embed(guild_id=1, message_id=42)
    assert isinstance(embed, discord.Embed)
    blob = (embed.description or "") + "\n".join(
        f.name + " " + f.value for f in embed.fields
    )
    assert "replied" in blob
    assert "openai" in blob
    assert "gpt-4" in blob
    assert "ff" in blob
    assert "5" in blob and "6" in blob
