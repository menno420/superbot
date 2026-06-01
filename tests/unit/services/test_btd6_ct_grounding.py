"""PR2: CT relic resolution precedence + AI grounding lines.

Reproduces the two Discord prompts that motivated the feature:
"where is Camo Trap in the current CT event" and "what does the SMS
relic give the team who captures it".
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_context_service as ctx  # noqa: E402
from services import btd6_resolver_service as resolver  # noqa: E402

# ---------------------------------------------------------------------------
# Resolver precedence
# ---------------------------------------------------------------------------


def test_camo_trap_resolves_relic_not_bloon():
    intent = resolver.resolve("where is Camo Trap in the current CT event")
    assert [r.id for r in intent.ct_relics] == ["camo_trap"]
    assert intent.bloons == ()  # camo bloon suppressed


def test_sms_resolves_super_monkey_storm():
    intent = resolver.resolve("what does the SMS relic give the team who captures it")
    assert [r.id for r in intent.ct_relics] == ["super_monkey_storm"]


def test_super_monkey_storm_phrase_does_not_match_super_monkey_tower():
    intent = resolver.resolve("what does super monkey storm do")
    assert [r.id for r in intent.ct_relics] == ["super_monkey_storm"]
    assert intent.towers == ()


def test_bare_super_monkey_still_matches_tower():
    intent = resolver.resolve("how good is the super monkey")
    assert intent.ct_relics == ()
    assert any(t.id == "super_monkey" for t in intent.towers)


def test_bare_camo_still_matches_bloon():
    intent = resolver.resolve("are camo bloons immune to anything")
    assert intent.ct_relics == ()
    assert intent.bloons != ()


# ---------------------------------------------------------------------------
# Grounding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_relic_effect_line_present(monkeypatch):
    from services import btd6_live_query_service as live

    async def _none(_relic):
        return ()

    monkeypatch.setattr(live, "find_relic_locations", _none)
    out = await ctx.build("what does the SMS relic give the team who captures it")
    relic_lines = [f for f in out.facts if f.startswith("[btd6_ct_relic]")]
    assert relic_lines
    assert "Super Monkey Storm (SMS)" in relic_lines[0]


@pytest.mark.asyncio
async def test_relic_tile_location_line_present(monkeypatch):
    from services import btd6_live_query_service as live
    from utils.btd6.ct_tile_geometry import decode_tile

    placement = live.CTTilePlacement(
        ct_id="mpejg5d0",
        tile_id="DEC",
        tile_type="Relic",
        game_type="Race",
        relic_name="CamoTrap",
        relic_id="camo_trap",
        relic_canonical="Camo Trap",
        fetched_at=datetime.now(tz=timezone.utc),
        position=decode_tile("DEC"),
    )

    async def _locations(relic_id):
        assert relic_id == "camo_trap"
        return (placement,)

    monkeypatch.setattr(live, "find_relic_locations", _locations)
    out = await ctx.build("where is Camo Trap in the current CT event")
    tile_lines = [f for f in out.facts if f.startswith("[btd6_ct_tile]")]
    assert tile_lines
    assert "tile DEC" in tile_lines[0]
    assert "mpejg5d0" in tile_lines[0]
