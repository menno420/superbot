"""Pin the 'Currently active' field on the BTD6 panel embed.

PR 1 made ``build_btd6_panel_embed`` async and added a field that
lists the latest race / boss / CT / odyssey / event by name with a
freshness badge. The follow-up fix switched the source-of-truth to
``btd6_live_query_service.get_active_events`` with a stricter "has an
explicit future end_ms" filter so ended events stop showing as
currently-active.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import discord
import pytest

from views.btd6.panel import build_btd6_panel_embed


def _now_ms(delta_hours: int = 0) -> int:
    when = datetime.now(tz=timezone.utc) + timedelta(hours=delta_hours)
    return int(when.timestamp() * 1000)


def _fact_row(
    *,
    entity_kind: str,
    entity_key: str,
    name: str | None = None,
    end_ms: int | None = None,
) -> dict:
    body: dict = {}
    if name is not None:
        body["name"] = name
    if end_ms is not None:
        body["end_ms"] = end_ms
    return {
        "entity_kind": entity_kind,
        "entity_key": entity_key,
        # fact_type must match what get_active_events looks for per kind.
        "fact_type": f"btd6.{entity_kind.removeprefix('btd6_')}s_index"
        if entity_kind not in ("btd6_ct", "btd6_odyssey", "btd6_event")
        else {
            "btd6_ct": "btd6.ct_index",
            "btd6_odyssey": "btd6.odyssey_index",
            "btd6_event": "btd6.events_index",
        }[entity_kind],
        "body_json": body,
        "fetched_at": datetime.now(tz=timezone.utc),
    }


def _patch_db(monkeypatch, *, latest_rows: dict, search_rows_by_kind: dict | None = None):
    """Mock both DB paths the hub VM now uses."""
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(
        btd6_db, "latest_fact_per_entity_kind", AsyncMock(return_value=latest_rows),
    )
    sources = search_rows_by_kind or {}

    async def _search_facts(*, fact_type=None, entity_kind=None, limit=50):
        return sources.get(entity_kind, [])

    monkeypatch.setattr(btd6_db, "search_facts", _search_facts)


@pytest.mark.asyncio
async def test_panel_embed_includes_currently_active_field(monkeypatch):
    race = _fact_row(
        entity_kind="btd6_race",
        entity_key="Reversed_Loop",
        name="Reversed Loop",
        end_ms=_now_ms(48),
    )
    boss = _fact_row(
        entity_kind="btd6_boss",
        entity_key="Diamondback5",
        name="Diamondback v5",
        end_ms=_now_ms(5),
    )
    _patch_db(
        monkeypatch,
        latest_rows={"btd6_race": race, "btd6_boss": boss},
        search_rows_by_kind={"btd6_race": [race], "btd6_boss": [boss]},
    )

    embed = await build_btd6_panel_embed()
    assert isinstance(embed, discord.Embed)
    names = [f.name for f in embed.fields]
    assert any("Currently active" in (n or "") for n in names)

    active_field = next(f for f in embed.fields if "Currently active" in (f.name or ""))
    value = active_field.value or ""
    assert "Reversed Loop" in value
    assert "Diamondback v5" in value
    # End-time hint renders for present kinds.
    assert "ends" in value


@pytest.mark.asyncio
async def test_panel_embed_renders_dash_for_missing_kinds(monkeypatch):
    _patch_db(monkeypatch, latest_rows={}, search_rows_by_kind={})

    embed = await build_btd6_panel_embed()
    active_field = next(f for f in embed.fields if "Currently active" in (f.name or ""))
    value = active_field.value or ""
    # All 5 kinds render '—' when no facts exist.
    assert value.count("—") >= 5


@pytest.mark.asyncio
async def test_panel_embed_falls_back_to_entity_key_when_no_name(monkeypatch):
    ct = _fact_row(
        entity_kind="btd6_ct",
        entity_key="ct_abc123",
        end_ms=_now_ms(48),
    )
    _patch_db(
        monkeypatch,
        latest_rows={"btd6_ct": ct},
        search_rows_by_kind={"btd6_ct": [ct]},
    )

    embed = await build_btd6_panel_embed()
    active_field = next(f for f in embed.fields if "Currently active" in (f.name or ""))
    value = active_field.value or ""
    assert "ct_abc123" in value


@pytest.mark.asyncio
async def test_panel_embed_keeps_seed_reference_block(monkeypatch):
    _patch_db(monkeypatch, latest_rows={}, search_rows_by_kind={})

    embed = await build_btd6_panel_embed()
    names = [f.name for f in embed.fields]
    assert any("Reference" in (n or "") for n in names)
    ref_field = next(f for f in embed.fields if "Reference" in (f.name or ""))
    value = ref_field.value or ""
    assert "towers" in value.lower()
    assert "heroes" in value.lower()


# ---------------------------------------------------------------------------
# PR 1 — per-kind freshness badges in 'Currently active'
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_panel_embed_renders_white_circle_for_never_kinds(monkeypatch):
    """Every missing kind leads with ⚪ (never fetched)."""
    _patch_db(monkeypatch, latest_rows={}, search_rows_by_kind={})

    embed = await build_btd6_panel_embed()
    active_field = next(f for f in embed.fields if "Currently active" in (f.name or ""))
    value = active_field.value or ""
    # All 5 kinds render with ⚪ since none have facts.
    assert value.count("⚪") == 5


@pytest.mark.asyncio
async def test_panel_embed_renders_fresh_badge_for_recent_fact(monkeypatch):
    """A recently-fetched row leads with 🟢."""
    race = _fact_row(
        entity_kind="btd6_race",
        entity_key="Reversed_Loop",
        name="Reversed Loop",
        end_ms=_now_ms(48),
    )
    _patch_db(
        monkeypatch,
        latest_rows={"btd6_race": race},
        search_rows_by_kind={"btd6_race": [race]},
    )

    embed = await build_btd6_panel_embed()
    active_field = next(f for f in embed.fields if "Currently active" in (f.name or ""))
    value = active_field.value or ""
    # Race kind has a recent fetch → 🟢. Other four kinds → ⚪.
    assert "🟢" in value
    assert value.count("⚪") == 4
    # Existing layout invariants still hold.
    assert "Reversed Loop" in value


@pytest.mark.asyncio
async def test_panel_embed_hides_ended_race_from_currently_active(monkeypatch):
    """Regression: an ended race must NOT appear in 'Currently active'.

    Pre-fix, ``latest_fact_per_entity_kind`` picked an arbitrary tied-
    fetched_at race fact and rendered it without filtering by end_ms.
    A race that ended a month ago surfaced as the current race because
    the renderer relied on ``_format_ends_relative`` to slap on a
    "· ended" suffix — which never fired when end_ms was missing or
    when the race was simply the wrong choice.
    """
    ended = _fact_row(
        entity_kind="btd6_race",
        entity_key="Enjoying_the_Hotsprings_mois29mi",
        name="Enjoying the Hotsprings",
        end_ms=_now_ms(-24 * 30),  # 30 days in the past
    )
    _patch_db(
        monkeypatch,
        latest_rows={"btd6_race": ended},
        search_rows_by_kind={"btd6_race": [ended]},
    )

    embed = await build_btd6_panel_embed()
    active_field = next(f for f in embed.fields if "Currently active" in (f.name or ""))
    value = active_field.value or ""
    # Ended race name is NOT in the field.
    assert "Enjoying the Hotsprings" not in value
    # Race slot renders as "—".
    assert "race" in value  # row label still present
    # Freshness still reflects the underlying data being recent (🟢)
    # even though no race is currently active.
    assert "🟢" in value
