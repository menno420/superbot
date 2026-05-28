"""Pin the new 'Currently active' field on the BTD6 panel embed.

The plan is to make ``build_btd6_panel_embed`` async and add a field
that lists the latest race / boss / CT / odyssey / event by name with
a ``ends Xh/Xd`` hint.
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
        "body_json": body,
        "fetched_at": datetime.now(tz=timezone.utc),
    }


@pytest.mark.asyncio
async def test_panel_embed_includes_currently_active_field(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _rows(kinds):
        return {
            "btd6_race": _fact_row(
                entity_kind="btd6_race",
                entity_key="Reversed_Loop",
                name="Reversed Loop",
                end_ms=_now_ms(48),
            ),
            "btd6_boss": _fact_row(
                entity_kind="btd6_boss",
                entity_key="Diamondback5",
                name="Diamondback v5",
                end_ms=_now_ms(5),
            ),
        }

    monkeypatch.setattr(btd6_db, "latest_fact_per_entity_kind", _rows)

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
    from utils.db import btd6_sources as btd6_db

    async def _empty(kinds):
        return {}

    monkeypatch.setattr(btd6_db, "latest_fact_per_entity_kind", _empty)

    embed = await build_btd6_panel_embed()
    active_field = next(f for f in embed.fields if "Currently active" in (f.name or ""))
    value = active_field.value or ""
    # All 5 kinds render '—' when no facts exist.
    assert value.count("—") >= 5


@pytest.mark.asyncio
async def test_panel_embed_falls_back_to_entity_key_when_no_name(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _rows(kinds):
        return {
            "btd6_ct": _fact_row(entity_kind="btd6_ct", entity_key="ct_abc123"),
        }

    monkeypatch.setattr(btd6_db, "latest_fact_per_entity_kind", _rows)

    embed = await build_btd6_panel_embed()
    active_field = next(f for f in embed.fields if "Currently active" in (f.name or ""))
    value = active_field.value or ""
    assert "ct_abc123" in value


@pytest.mark.asyncio
async def test_panel_embed_keeps_seed_reference_block(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _empty(kinds):
        return {}

    monkeypatch.setattr(btd6_db, "latest_fact_per_entity_kind", _empty)

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
    from utils.db import btd6_sources as btd6_db

    async def _empty(kinds):
        return {}

    monkeypatch.setattr(btd6_db, "latest_fact_per_entity_kind", _empty)

    embed = await build_btd6_panel_embed()
    active_field = next(f for f in embed.fields if "Currently active" in (f.name or ""))
    value = active_field.value or ""
    # All 5 kinds render with ⚪ since none have facts.
    assert value.count("⚪") == 5


@pytest.mark.asyncio
async def test_panel_embed_renders_fresh_badge_for_recent_fact(monkeypatch):
    """A recently-fetched row leads with 🟢."""
    from utils.db import btd6_sources as btd6_db

    async def _rows(kinds):
        return {
            "btd6_race": _fact_row(
                entity_kind="btd6_race",
                entity_key="Reversed_Loop",
                name="Reversed Loop",
                end_ms=_now_ms(48),
            ),
        }

    monkeypatch.setattr(btd6_db, "latest_fact_per_entity_kind", _rows)

    embed = await build_btd6_panel_embed()
    active_field = next(f for f in embed.fields if "Currently active" in (f.name or ""))
    value = active_field.value or ""
    # Race kind has a recent fetch → 🟢. Other four kinds → ⚪.
    assert "🟢" in value
    assert value.count("⚪") == 4
    # Existing layout invariants still hold.
    assert "Reversed Loop" in value
