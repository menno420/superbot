"""Tests for the new ``!btd6 event <kind> <id>`` command.

Both prefix and slash invoke the same ``build_event_payload`` helper
from ``cogs/btd6/_event_helpers.py``. The empty-state path renders a
red embed with a hint pointing at ``!btd6 live <kind>``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from cogs.btd6 import _unified
from cogs.btd6_events_cog import BTD6EventsCog


def _index_row(entity_kind: str, entity_key: str, name: str | None = None) -> dict:
    body: dict = {"id": entity_key, "start_ms": 1779019200000, "end_ms": 1779105600000}
    if name is not None:
        body["name"] = name
    return {
        "id": 1,
        "source_id": 1,
        "fact_type": "btd6.races_index",
        "entity_kind": entity_kind,
        "entity_key": entity_key,
        "body_json": body,
        "game_version": "44.0",
        "fetched_at": datetime.now(tz=timezone.utc),
        "validated_at": None,
        "confidence": 1.0,
        "version": 1,
    }


def _metadata_row(towers: list[dict]) -> dict:
    return {
        "id": 2,
        "source_id": 1,
        "fact_type": "btd6.race_metadata",
        "entity_kind": "btd6_race",
        "entity_key": "Reversed_Loop",
        "body_json": {
            "race_id": "Reversed_Loop",
            "startRound": 1,
            "endRound": 60,
            "lives": 100,
            "_towers": towers,
        },
        "game_version": "44.0",
        "fetched_at": datetime.now(tz=timezone.utc),
        "validated_at": None,
        "confidence": 1.0,
        "version": 1,
    }


# ---------------------------------------------------------------------------
# Prefix command
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prefix_event_command_renders_index_only(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _fact(fact_type, entity_kind, entity_key):
        if fact_type is None:
            return _index_row(entity_kind, entity_key, name="Reversed Loop")
        return None

    monkeypatch.setattr(btd6_db, "get_latest_fact", _fact)

    cog = BTD6EventsCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()

    await cog.btd6_event.callback(cog, ctx, "race", "Reversed_Loop")

    embed = ctx.send.await_args.kwargs.get("embed")
    assert embed is not None
    assert "Reversed Loop" in (embed.title or "")
    # Status field present
    field_names = [f.name for f in embed.fields]
    assert "Window" in field_names


@pytest.mark.asyncio
async def test_prefix_event_command_renders_tower_restrictions(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _fact(fact_type, entity_kind, entity_key):
        if fact_type is None:
            return _index_row(entity_kind, entity_key, name="Reversed Loop")
        if fact_type == "btd6.race_metadata":
            return _metadata_row(
                [
                    {"tower": "BananaFarm", "max": 0, "isHero": False},
                    {"tower": "Alchemist", "max": 1, "isHero": False},
                ],
            )
        return None

    monkeypatch.setattr(btd6_db, "get_latest_fact", _fact)

    cog = BTD6EventsCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()

    await cog.btd6_event.callback(cog, ctx, "race", "Reversed_Loop")

    embed = ctx.send.await_args.kwargs.get("embed")
    field_names = [f.name for f in embed.fields]
    assert any("Banned" in n for n in field_names)
    assert any("Limited" in n for n in field_names)
    banned_field = next(f for f in embed.fields if "Banned" in (f.name or ""))
    assert "BananaFarm" in (banned_field.value or "")


@pytest.mark.asyncio
async def test_prefix_event_command_empty_state(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _fact(fact_type, entity_kind, entity_key):
        return None

    monkeypatch.setattr(btd6_db, "get_latest_fact", _fact)

    cog = BTD6EventsCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()

    await cog.btd6_event.callback(cog, ctx, "race", "nonsense")

    embed = ctx.send.await_args.kwargs.get("embed")
    assert embed.color == discord.Color.red()
    desc = embed.description or ""
    assert "No event found" in desc
    assert "!btd6 live race" in desc


# ---------------------------------------------------------------------------
# Slash command — defers before DB
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slash_event_command_defers_before_db_calls(monkeypatch):
    call_order: list[str] = []

    from cogs.btd6 import _reply as cog_mod
    from utils.db import btd6_sources as btd6_db

    async def _fact(fact_type, entity_kind, entity_key):
        call_order.append("db")
        return _index_row(entity_kind, entity_key, name="X")

    monkeypatch.setattr(btd6_db, "get_latest_fact", _fact)

    async def _defer(interaction, **kw):
        call_order.append("defer")
        return True

    async def _followup(*a, **kw):
        call_order.append("followup")
        return None

    monkeypatch.setattr(cog_mod, "safe_defer", _defer)
    monkeypatch.setattr(cog_mod, "safe_followup", _followup)

    interaction = MagicMock()
    interaction.response.is_done = lambda: False

    await _unified.events_event_slash.callback(interaction, "race", "X")

    # defer must come before any db call.
    assert call_order[0] == "defer"
    assert "db" in call_order
    assert call_order[-1] == "followup"


# ---------------------------------------------------------------------------
# Parity pin
# ---------------------------------------------------------------------------


def test_event_command_in_parity_pin():
    from tests.unit.cogs.test_btd6_boundaries import _expected_parity_names

    assert "event" in _expected_parity_names()
