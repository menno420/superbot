"""PR3: CT relic / browser embed builders."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from cogs.btd6 import _builders  # noqa: E402

_NOW = datetime.now(tz=timezone.utc)


def _placement(tile_id, relic_id, relic_canonical, ct_id="mpejg5d0"):
    from services import btd6_live_query_service as live
    from utils.btd6.ct_tile_geometry import decode_tile

    return live.CTTilePlacement(
        ct_id=ct_id,
        tile_id=tile_id,
        tile_type="Relic",
        game_type="Race",
        relic_name="CamoTrap",
        relic_id=relic_id,
        relic_canonical=relic_canonical,
        fetched_at=_NOW,
        position=decode_tile(tile_id),
    )


@pytest.mark.asyncio
async def test_relic_embed_shows_effect_and_location(monkeypatch):
    from services import btd6_live_query_service as live

    async def _locations(relic_id):
        assert relic_id == "camo_trap"
        return (_placement("DEC", "camo_trap", "Camo Trap"),)

    monkeypatch.setattr(live, "find_relic_locations", _locations)
    embed = await _builders.build_ct_relic_embed("camo trap")
    assert "Camo Trap" in embed.title
    assert embed.description  # the effect text
    joined = " ".join(f.value for f in embed.fields)
    assert "DEC" in joined
    # context footer carries the new ct_relic handle.
    assert "btd6_ct_relic:camo_trap" in (embed.footer.text or "")


@pytest.mark.asyncio
async def test_relic_embed_unknown_name():
    embed = await _builders.build_ct_relic_embed("not-a-relic-xyz")
    assert "Unknown relic" in embed.title


@pytest.mark.asyncio
async def test_ct_browser_lists_events(monkeypatch):
    from services import btd6_live_query_service as live

    async def _active(kinds=None):
        return (
            live.ActiveEventHeadline("btd6_ct", "evt1", "CT One", None, None, _NOW),
        )

    async def _tiles(ct_id, *, relic=None, relics_only=False):
        return (_placement("DEC", "camo_trap", "Camo Trap", ct_id=ct_id),)

    monkeypatch.setattr(live, "get_active_events", _active)
    monkeypatch.setattr(live, "get_ct_tiles", _tiles)
    embed = await _builders.build_ct_browser_embed()
    assert "Contested Territory" in embed.title
    joined = " ".join(f.value for f in embed.fields)
    assert "evt1" in joined
    assert "Camo Trap" in joined
    assert "btd6_ct:browser" in (embed.footer.text or "")
