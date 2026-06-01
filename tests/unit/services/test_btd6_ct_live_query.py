"""CT tile / relic-location queries in services.btd6_live_query_service."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_live_query_service as live  # noqa: E402

_NOW = datetime.now(tz=timezone.utc)


def _tile_row(ct_id: str, tile_id: str, tile_type: str, relic_name=None):
    return {
        "entity_kind": "btd6_ct_tile",
        "entity_key": f"{ct_id}_tile_{tile_id}",
        "fact_type": "btd6.ct_tiles",
        "body_json": {
            "ct_id": ct_id,
            "tile_id": tile_id,
            "type": tile_type,
            "relic_name": relic_name,
            "game_type": "Race",
        },
        "fetched_at": _NOW,
    }


def _patch_tiles(monkeypatch, rows):
    from utils.db import btd6_sources as btd6_db

    async def _list(ct_id, *, limit=256):
        return [r for r in rows if r["entity_key"].startswith(f"{ct_id}_tile_")]

    monkeypatch.setattr(btd6_db, "list_ct_tiles_for_event", _list)


@pytest.mark.asyncio
async def test_get_ct_tiles_attaches_relic_and_position(monkeypatch):
    rows = [
        _tile_row("evt1", "DEC", "Relic", "CamoTrap"),
        _tile_row("evt1", "DAG", "Banner"),
    ]
    _patch_tiles(monkeypatch, rows)

    tiles = await live.get_ct_tiles("evt1")
    assert len(tiles) == 2
    camo = next(t for t in tiles if t.tile_id == "DEC")
    assert camo.relic_id == "camo_trap"
    assert camo.relic_canonical == "Camo Trap"
    assert camo.position is not None
    assert camo.position.ring == 3


@pytest.mark.asyncio
async def test_get_ct_tiles_relic_filter(monkeypatch):
    rows = [
        _tile_row("evt1", "DEC", "Relic", "CamoTrap"),
        _tile_row("evt1", "AAA", "Relic", "SuperMonkeyStorm"),
        _tile_row("evt1", "DAG", "Banner"),
    ]
    _patch_tiles(monkeypatch, rows)

    # By abbrev -> resolves to SuperMonkeyStorm.
    sms = await live.get_ct_tiles("evt1", relic="sms")
    assert [t.tile_id for t in sms] == ["AAA"]
    # relics_only drops the banner.
    relics = await live.get_ct_tiles("evt1", relics_only=True)
    assert {t.tile_id for t in relics} == {"DEC", "AAA"}


@pytest.mark.asyncio
async def test_find_relic_locations_across_active_events(monkeypatch):
    rows = [
        _tile_row("evt1", "DEC", "Relic", "CamoTrap"),
        _tile_row("evt2", "BCD", "Relic", "CamoTrap"),
        _tile_row("evt2", "AAA", "Relic", "Restoration"),
    ]
    _patch_tiles(monkeypatch, rows)

    async def _active(kinds=None):
        return (
            live.ActiveEventHeadline("btd6_ct", "evt1", "evt1", None, None, _NOW),
            live.ActiveEventHeadline("btd6_ct", "evt2", "evt2", None, None, _NOW),
        )

    monkeypatch.setattr(live, "get_active_events", _active)

    hits = await live.find_relic_locations("camo trap")
    assert {(t.ct_id, t.tile_id) for t in hits} == {("evt1", "DEC"), ("evt2", "BCD")}
