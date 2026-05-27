"""Tests for the live-event read-only surfaces.

Covers the shared `build_live_events_embed` builder plus the five
`!btd6 race / boss / ct / odyssey / event` prefix commands and their
slash twins.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from cogs.btd6._builders import (
    _event_window,
    _ms_to_human,
    build_live_events_embed,
)
from cogs.btd6_cog import BTD6Cog

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fact_row(
    *,
    entity_kind: str,
    entity_key: str,
    body: dict,
    fetched_at: datetime | None = None,
) -> dict:
    return {
        "id": 1,
        "source_id": 1,
        "fact_type": "btd6.live",
        "entity_kind": entity_kind,
        "entity_key": entity_key,
        "body_json": body,
        "game_version": "47.0",
        "fetched_at": fetched_at or datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        "validated_at": None,
        "confidence": 1.0,
        "version": 1,
    }


def _slash_interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 555
    interaction.user = MagicMock()
    interaction.user.id = 7777
    interaction.response.is_done = lambda: False
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_ms_to_human_handles_missing_or_invalid_values():
    assert _ms_to_human(None) == "—"
    assert _ms_to_human("not-a-number") == "—"
    assert _ms_to_human(0) == "—"
    assert _ms_to_human(-1) == "—"


def test_ms_to_human_formats_unix_ms():
    # Format check, not exact-date check — leap-second / epoch math
    # is the stdlib's job. 1779019200000 → 2026-05-17 12:00 UTC.
    rendered = _ms_to_human(1779019200000)
    assert rendered.endswith(" UTC")
    assert rendered.startswith("2026-")


def test_event_window_renders_both_ends():
    body = {"start_ms": 1779019200000, "end_ms": 1779105600000}
    assert "→" in _event_window(body)


def test_event_window_dash_when_both_missing():
    assert _event_window({}) == "—"


# ---------------------------------------------------------------------------
# build_live_events_embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_live_events_embed_unknown_kind_returns_error_embed():
    embed = await build_live_events_embed("not_a_kind")
    assert embed.color == discord.Color.red()
    assert "Unknown" in (embed.title or "")
    assert "race" in (embed.description or "")


@pytest.mark.asyncio
async def test_build_live_events_embed_accepts_short_form(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    seen: dict = {}

    async def _fake(*, entity_kind=None, fact_type=None, limit=50):
        seen["entity_kind"] = entity_kind
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _fake)
    # ``race`` (short) should be normalised to ``btd6_race``.
    await build_live_events_embed("race")
    assert seen["entity_kind"] == "btd6_race"


@pytest.mark.asyncio
async def test_build_live_events_embed_empty_shows_hint(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _empty(*, entity_kind=None, fact_type=None, limit=50):
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _empty)
    embed = await build_live_events_embed("btd6_race")
    desc = embed.description or ""
    assert "No race facts" in desc
    assert "refresh-source nk_btd6_races" in desc


@pytest.mark.asyncio
async def test_build_live_events_embed_race_renders_fields(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _fake(*, entity_kind=None, fact_type=None, limit=50):
        assert entity_kind == "btd6_race"
        return [
            _fact_row(
                entity_kind="btd6_race",
                entity_key="reversed_loop_2026_05",
                body={
                    "id": "reversed_loop_2026_05",
                    "name": "Reversed Loop",
                    "start_ms": 1779019200000,
                    "end_ms": 1779105600000,
                    "total_scores": 9_321,
                },
            ),
        ]

    monkeypatch.setattr(btd6_db, "search_facts", _fake)

    embed = await build_live_events_embed("btd6_race", limit=1)
    assert embed.title == "🐵 BTD6 — Races"
    assert len(embed.fields) == 1
    field = embed.fields[0]
    assert field.name == "Reversed Loop"
    value = field.value or ""
    assert "`reversed_loop_2026_05`" in value
    assert "scores=9321" in value
    assert "→" in value  # window separator


@pytest.mark.asyncio
async def test_build_live_events_embed_boss_renders_standard_and_elite(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _fake(*, entity_kind=None, fact_type=None, limit=50):
        return [
            _fact_row(
                entity_kind="btd6_boss",
                entity_key="diamondback5",
                body={
                    "id": "diamondback5",
                    "name": "Diamondback Tier 5",
                    "boss_type": "diamondback",
                    "total_scores_standard": 100,
                    "total_scores_elite": 50,
                    "start_ms": 1779019200000,
                    "end_ms": 1779105600000,
                },
            ),
        ]

    monkeypatch.setattr(btd6_db, "search_facts", _fake)

    embed = await build_live_events_embed("btd6_boss", limit=1)
    value = embed.fields[0].value or ""
    assert "standard=100" in value
    assert "elite=50" in value
    assert "type=`diamondback`" in value


@pytest.mark.asyncio
async def test_build_live_events_embed_falls_back_to_entity_key_when_no_name(
    monkeypatch,
):
    from utils.db import btd6_sources as btd6_db

    async def _fake(*, entity_kind=None, fact_type=None, limit=50):
        return [
            _fact_row(
                entity_kind="btd6_ct",
                entity_key="ct_42",
                body={"start_ms": 0, "end_ms": 0},
            ),
        ]

    monkeypatch.setattr(btd6_db, "search_facts", _fake)

    embed = await build_live_events_embed("btd6_ct", limit=1)
    assert embed.fields[0].name == "ct_42"


# ---------------------------------------------------------------------------
# Prefix commands
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind_arg,entity_kind",
    [
        ("race", "btd6_race"),
        ("boss", "btd6_boss"),
        ("ct", "btd6_ct"),
        ("odyssey", "btd6_odyssey"),
        ("event", "btd6_event"),
    ],
)
async def test_live_prefix_routes_each_kind_to_entity_kind(
    monkeypatch,
    kind_arg,
    entity_kind,
):
    seen: dict = {}

    async def _fake(*, entity_kind=None, fact_type=None, limit=50):
        seen["entity_kind"] = entity_kind
        seen["limit"] = limit
        return []

    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(btd6_db, "search_facts", _fake)

    cog = BTD6Cog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()
    await cog.btd6_live.callback(cog, ctx, kind_arg, 7)

    assert seen == {"entity_kind": entity_kind, "limit": 7}
    ctx.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_live_prefix_unknown_kind_returns_error_embed(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _fake(**_kw):
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _fake)

    cog = BTD6Cog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()
    await cog.btd6_live.callback(cog, ctx, "nonsense", 5)

    embed = ctx.send.await_args.kwargs.get("embed")
    assert embed is not None
    assert "Unknown" in (embed.title or "")


# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_live_slash_defers_before_db_call(monkeypatch):
    call_order: list[str] = []

    async def _fake(*, entity_kind=None, fact_type=None, limit=50):
        call_order.append("db")
        return []

    from cogs import btd6_cog as cog_mod
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(btd6_db, "search_facts", _fake)

    async def _defer_capture(interaction, **_kw):
        call_order.append("defer")
        return True

    async def _followup_capture(*_a, **_kw):
        call_order.append("followup")
        return None

    monkeypatch.setattr(cog_mod, "safe_defer", _defer_capture)
    monkeypatch.setattr(cog_mod, "safe_followup", _followup_capture)

    cog = BTD6Cog(MagicMock())
    interaction = _slash_interaction()
    await cog.btd6_live_slash.callback(cog, interaction, "race", 3)

    assert call_order == ["defer", "db", "followup"]


@pytest.mark.asyncio
async def test_live_slash_unknown_kind_followups_with_error_embed(monkeypatch):
    from cogs import btd6_cog as cog_mod
    from utils.db import btd6_sources as btd6_db

    async def _fake(**_kw):
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _fake)

    async def _defer(*_a, **_kw):
        return True

    sent: list[dict] = []

    async def _followup(_interaction, *_a, **kwargs):
        sent.append(kwargs)

    monkeypatch.setattr(cog_mod, "safe_defer", _defer)
    monkeypatch.setattr(cog_mod, "safe_followup", _followup)

    cog = BTD6Cog(MagicMock())
    interaction = _slash_interaction()
    await cog.btd6_live_slash.callback(cog, interaction, "nonsense", 5)

    embed = sent[0].get("embed") if sent else None
    assert embed is not None
    assert "Unknown" in (embed.title or "")


# ---------------------------------------------------------------------------
# Scheduler coverage — pin the expanded source list
# ---------------------------------------------------------------------------


def test_supervisor_source_intervals_cover_live_sources():
    from services.btd6_ingestion_supervisor import _SOURCE_INTERVALS

    expected = {
        "nk_btd6_maps",
        "nk_btd6_events",
        "nk_btd6_races",
        "nk_btd6_bosses",
        "nk_btd6_odyssey",
        "nk_btd6_ct",
    }
    missing = expected - set(_SOURCE_INTERVALS)
    assert not missing, f"scheduler is missing sources: {missing}"


# ---------------------------------------------------------------------------
# Live grounding wired into !btd6 ask
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_answer_question_attaches_live_facts(monkeypatch):
    from services import btd6_ai_service, btd6_context_service

    async def _ctx(_text):
        return btd6_context_service.BTD6Context(
            facts=("Reversed Loop — type=race (source: data.ninjakiwi.com)",),
            source_summary="data.ninjakiwi.com (Tier 1)",
            confidence=0.5,
        )

    monkeypatch.setattr(btd6_context_service, "build", _ctx)

    response = await btd6_ai_service.answer_question("when is the next race?")
    assert response.live_facts == (
        "Reversed Loop — type=race (source: data.ninjakiwi.com)",
    )


@pytest.mark.asyncio
async def test_answer_question_survives_context_service_failure(monkeypatch):
    from services import btd6_ai_service, btd6_context_service

    async def _boom(_text):
        raise RuntimeError("DB down")

    monkeypatch.setattr(btd6_context_service, "build", _boom)

    response = await btd6_ai_service.answer_question("dart monkey")
    assert response.live_facts == ()  # falls back to deterministic only


def test_response_to_embed_renders_live_facts():
    from cogs.btd6._embeds import response_to_embed
    from services.btd6_response_builder import BTD6Response

    response = BTD6Response(
        title="Test",
        short_answer="Body",
        live_facts=(
            "Race #1 — type=race (source: data.ninjakiwi.com)",
            "Race #2 — type=race (source: data.ninjakiwi.com)",
        ),
    )
    embed = response_to_embed(response)
    names = [f.name for f in embed.fields]
    assert "Live data" in names
    value = next(f.value for f in embed.fields if f.name == "Live data")
    assert "Race #1" in (value or "")
    assert "Race #2" in (value or "")


def test_response_to_embed_no_live_field_when_empty():
    from cogs.btd6._embeds import response_to_embed
    from services.btd6_response_builder import BTD6Response

    response = BTD6Response(title="Test", short_answer="Body")
    embed = response_to_embed(response)
    names = [f.name for f in embed.fields]
    assert "Live data" not in names


def test_augmentation_payload_includes_live_facts():
    from services.btd6_ai_service import _augmentation_payload
    from services.btd6_resolver_service import resolve
    from services.btd6_response_builder import BTD6Response

    intent = resolve("dart monkey")
    response = BTD6Response(
        title="Test",
        short_answer="Body",
        live_facts=("Live A", "Live B"),
    )
    payload = _augmentation_payload(intent, response)
    assert payload["live_facts"] == ["Live A", "Live B"]
