"""CT map view: tile classification + discord.File assembly."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.btd6.ct_tile_geometry import decode_tile  # noqa: E402
from views.btd6 import ct_map_view  # noqa: E402

_NOW = datetime.now(tz=timezone.utc)


def _placement(
    tile_id, tile_type, relic_name=None, relic_id=None, relic_canonical=None
):
    from services import btd6_live_query_service as live

    return live.CTTilePlacement(
        ct_id="mpejg5d0",
        tile_id=tile_id,
        tile_type=tile_type,
        game_type="Race",
        relic_name=relic_name,
        relic_id=relic_id,
        relic_canonical=relic_canonical,
        fetched_at=_NOW,
        position=decode_tile(tile_id),
    )


def test_tile_classification_and_label():
    relic = _placement(
        "DEC", "Relic", "SuperMonkeyStorm", "super_monkey_storm", "Super Monkey Storm"
    )
    tile = ct_map_view._placement_to_tile(relic)
    assert tile is not None
    assert tile.kind == "relic"
    assert tile.label == "SMS"  # catalog abbreviation
    banner = ct_map_view._placement_to_tile(_placement("AAA", "Banner"))
    assert banner.kind == "banner"
    assert banner.label == ""
    assert (
        ct_map_view._placement_to_tile(_placement("MRX", "Regular")).is_center is True
    )


@pytest.mark.asyncio
async def test_build_ct_map_file_none_when_no_active_event(monkeypatch):
    from services import btd6_live_query_service as live

    async def _none(kinds=None):
        return ()

    monkeypatch.setattr(live, "get_active_events", _none)
    file, event_id = await ct_map_view.build_ct_map_file()
    assert file is None
    assert event_id is None


@pytest.mark.asyncio
async def test_build_ct_map_file_renders_when_data_present(monkeypatch):
    from services import btd6_live_query_service as live
    from utils.btd6.ct_map_render import pillow_available

    async def _active(kinds=None):
        return (
            live.ActiveEventHeadline(
                "btd6_ct", "mpejg5d0", "mpejg5d0", None, None, _NOW
            ),
        )

    async def _tiles(ct_id, *, relic=None, relics_only=False):
        return (
            _placement("DEC", "Relic", "CamoTrap", "camo_trap", "Camo Trap"),
            _placement("AAA", "Banner"),
            _placement("ABA", "Regular"),
        )

    monkeypatch.setattr(live, "get_active_events", _active)
    monkeypatch.setattr(live, "get_ct_tiles", _tiles)
    file, event_id = await ct_map_view.build_ct_map_file()
    assert event_id == "mpejg5d0"
    if pillow_available():
        import discord

        assert isinstance(file, discord.File)
        assert file.filename == "ct_map.png"
    else:  # pragma: no cover - depends on env
        assert file is None
