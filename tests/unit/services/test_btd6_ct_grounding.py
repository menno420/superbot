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
async def test_general_ct_question_lists_relic_tiles(monkeypatch):
    """A question that names no specific relic still gets the active CT's
    relic→tile breakdown (the gap behind 'I don't have per-tile details')."""
    from services import btd6_live_query_service as live
    from utils.btd6.ct_tile_geometry import decode_tile

    def _tile(tid, rid, canon, api):
        return live.CTTilePlacement(
            ct_id="mpejg5d0",
            tile_id=tid,
            tile_type="Relic",
            game_type="Race",
            relic_name=api,
            relic_id=rid,
            relic_canonical=canon,
            fetched_at=datetime.now(tz=timezone.utc),
            position=decode_tile(tid),
        )

    async def _active(kinds=None):
        return (
            live.ActiveEventHeadline(
                "btd6_ct",
                "mpejg5d0",
                "mpejg5d0",
                None,
                None,
                datetime.now(tz=timezone.utc),
            ),
        )

    async def _tiles(ct_id, *, relic=None, relics_only=False):
        return (
            _tile("DEC", "camo_trap", "Camo Trap", "CamoTrap"),
            _tile(
                "AAA", "super_monkey_storm", "Super Monkey Storm", "SuperMonkeyStorm"
            ),
        )

    monkeypatch.setattr(live, "get_active_events", _active)
    monkeypatch.setattr(live, "get_ct_tiles", _tiles)
    out = await ctx.build("Do you have specific information about the tiles and relics")
    tile_lines = [f for f in out.facts if f.startswith("[btd6_ct_tile]")]
    relic_lines = [f for f in out.facts if f.startswith("[btd6_ct_relic]")]
    assert any("tile DEC" in ln and "Camo Trap" in ln for ln in tile_lines)
    assert any("tile AAA" in ln and "Super Monkey Storm" in ln for ln in tile_lines)
    # distinct relic effects are appended too
    assert relic_lines


@pytest.mark.asyncio
async def test_btd6_lookup_tool_returns_ct_relics_without_db():
    """The live AI path is the btd6_lookup tool → build(). A general CT relic
    question must come back found=True with verified relic effects even when
    no live tile data is loaded (static-catalog fallback)."""
    from services import ai_tools

    res = await ai_tools._btd6_lookup({"query": "tell me about the CT relics"})
    assert res["found"] is True
    relic_lines = [f for f in res["facts"] if f.startswith("[btd6_ct_relic]")]
    assert relic_lines, "btd6_lookup returned no CT relic effects"


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


@pytest.mark.asyncio
async def test_general_ct_question_lists_all_relics_without_14_cap(monkeypatch):
    """Regression: a full CT map must surface ALL its relic tiles in grounding.

    The API can return 24 active relics, but ``_ct_active_tile_lines`` used to
    hard-cap the broad listing at 14 — so the model only ever saw 14 of 24.
    Build one tile per catalog relic and assert every one survives into facts
    (tiles AND distinct relic effects, the latter previously capped at 8).
    """
    from services import btd6_data_service
    from services import btd6_live_query_service as live

    relics = btd6_data_service.list_ct_relics()
    n = len(relics)
    assert n > 14, "relic catalog must exceed the old cap for this test to bite"

    async def _active(kinds=None):
        return (
            live.ActiveEventHeadline(
                "btd6_ct",
                "mpejg5d0",
                "mpejg5d0",
                None,
                None,
                datetime.now(tz=timezone.utc),
            ),
        )

    async def _tiles(ct_id, *, relic=None, relics_only=False):
        return tuple(
            live.CTTilePlacement(
                ct_id="mpejg5d0",
                tile_id=f"T{i:02d}",
                tile_type="Relic",
                game_type="Race",
                relic_name=getattr(r, "canonical", None) or str(getattr(r, "id", "")),
                relic_id=str(getattr(r, "id", "")),
                relic_canonical=getattr(r, "canonical", None),
                fetched_at=datetime.now(tz=timezone.utc),
                position=None,
            )
            for i, r in enumerate(relics)
        )

    monkeypatch.setattr(live, "get_active_events", _active)
    monkeypatch.setattr(live, "get_ct_tiles", _tiles)
    out = await ctx.build("Do you have specific information about the tiles and relics")
    tile_lines = [f for f in out.facts if f.startswith("[btd6_ct_tile]")]
    relic_lines = [f for f in out.facts if f.startswith("[btd6_ct_relic]")]
    # Every relic tile surfaces — not just the first 14.
    assert len(tile_lines) == n, (len(tile_lines), n)
    # Distinct relic effects are no longer capped at 8 either.
    assert len(relic_lines) > 8, len(relic_lines)


@pytest.mark.asyncio
async def test_btd6_lookup_tool_lists_all_relics_despite_live_preamble(monkeypatch):
    """Regression: the btd6_lookup TOOL must surface every relic tile.

    ``build()`` emits all 24 tile lines (the grounding test above proves it),
    but the live AI path consumes them through the ``btd6_lookup`` tool, which
    caps the returned facts. In production the live DB is populated, so Pass-2
    live-event rows are emitted *before* the CT tile lines and eat into that
    cap — which dropped a 24-relic listing to 19 (the model lists exactly what
    the tool returns). The grounding-only test never exercised the capped tool
    path, so it stayed green while the user saw 19. Reproduce a populated live
    DB + a full 24-relic map and assert all 24 tiles reach the model.
    """
    from services import ai_tools, btd6_data_service
    from services import btd6_live_query_service as live

    relics = btd6_data_service.list_ct_relics()
    n = len(relics)
    assert n > 14, "relic catalog must exceed the old cap for this test to bite"

    async def _active(kinds=None):
        return (
            live.ActiveEventHeadline(
                "btd6_ct",
                "mpejg5d0",
                "mpejg5d0",
                None,
                None,
                datetime.now(tz=timezone.utc),
            ),
        )

    async def _tiles(ct_id, *, relic=None, relics_only=False):
        return tuple(
            live.CTTilePlacement(
                ct_id="mpejg5d0",
                tile_id=f"T{i:02d}",
                tile_type="Relic",
                game_type="Race",
                relic_name=getattr(r, "canonical", None) or str(getattr(r, "id", "")),
                relic_id=str(getattr(r, "id", "")),
                relic_canonical=getattr(r, "canonical", None),
                fetched_at=datetime.now(tz=timezone.utc),
                position=None,
            )
            for i, r in enumerate(relics)
        )

    # Production has a populated live DB: several active-event rows render
    # before the CT tiles and so eat into the tool's fact cap.
    async def _preamble(_intent):
        return [
            {
                "fact_type": "btd6.event",
                "entity_kind": "btd6_ct",
                "entity_key": f"live_event_{i}",
                "body_json": {"name": f"Live event {i}"},
                "fetched_at": datetime.now(tz=timezone.utc),
            }
            for i in range(6)
        ]

    monkeypatch.setattr(live, "get_active_events", _active)
    monkeypatch.setattr(live, "get_ct_tiles", _tiles)
    monkeypatch.setattr(ctx, "_fetch_live_entity_rows", _preamble)

    res = await ai_tools._btd6_lookup(
        {"query": "list all active relics in the current ct event"},
    )
    tile_lines = [f for f in res["facts"] if f.startswith("[btd6_ct_tile]")]
    preamble = [
        f
        for f in res["facts"]
        if not f.startswith("[btd6_ct_tile]") and not f.startswith("[btd6_ct_relic]")
    ]
    # The preamble must actually render, or this test exerts no cap pressure
    # and would pass even under a too-small cap (the original blind spot).
    assert preamble, "live-event preamble did not render; test is toothless"
    # Every relic tile reaches the model through the capped tool path.
    assert len(tile_lines) == n, (len(tile_lines), n)


# ---------------------------------------------------------------------------
# Full tile inventory (all 169 tiles, not just the 24 relic tiles)
# ---------------------------------------------------------------------------


def _ct_placements_from_fixture() -> list:
    """Build CTTilePlacement objects from the committed 169-tile CT fixture."""
    import json

    from services import btd6_data_service
    from services import btd6_live_query_service as live
    from utils.btd6.ct_tile_geometry import decode_tile

    path = (
        Path(__file__).parents[3]
        / "tests/fixtures/ninjakiwi/btd6_ct_mpejg5d0_tiles.json"
    )
    payload = json.loads(path.read_text())

    def _find_tiles(obj):
        if isinstance(obj, dict):
            if isinstance(obj.get("tiles"), list):
                return obj["tiles"]
            for value in obj.values():
                found = _find_tiles(value)
                if found is not None:
                    return found
        return None

    placements = []
    for tile in _find_tiles(payload) or []:
        raw_type = str(tile.get("type", ""))
        relic_api = None
        tile_type = raw_type
        if raw_type.startswith("Relic - "):
            tile_type = "Relic"
            relic_api = raw_type[len("Relic - ") :].strip()
        relic_id = relic_canon = None
        if relic_api:
            entry = btd6_data_service.get_ct_relic_by_api_name(relic_api)
            if entry is not None:
                relic_id, relic_canon = entry.id, entry.canonical
            else:
                relic_canon = relic_api
        placements.append(
            live.CTTilePlacement(
                ct_id="mpejg5d0",
                tile_id=tile["id"],
                tile_type=tile_type,
                game_type=tile.get("gameType"),
                relic_name=relic_api,
                relic_id=relic_id,
                relic_canonical=relic_canon,
                fetched_at=datetime.now(tz=timezone.utc),
                position=decode_tile(tile["id"]),
            ),
        )
    return placements


def _patch_full_map(monkeypatch, placements):
    """Point the live layer at ``placements`` for one active CT event."""
    from services import btd6_live_query_service as live

    async def _active(kinds=None):
        return (
            live.ActiveEventHeadline(
                "btd6_ct",
                "mpejg5d0",
                "mpejg5d0",
                None,
                None,
                datetime.now(tz=timezone.utc),
            ),
        )

    async def _tiles(ct_id, *, relic=None, relics_only=False):
        return tuple(
            p for p in placements if (p.relic_name is not None or not relics_only)
        )

    monkeypatch.setattr(live, "get_active_events", _active)
    monkeypatch.setattr(live, "get_ct_tiles", _tiles)


def test_humanize_label_splits_camelcase():
    assert ctx._humanize_label("LeastCash") == "Least Cash"
    assert ctx._humanize_label("TeamFirstCapture") == "Team First Capture"
    assert ctx._humanize_label("Relic") == "Relic"


def test_tile_codes_in_text_uppercases_three_letter_tokens():
    codes = ctx._tile_codes_in_text("what's on tile dcb and DAG, not tiles overall")
    assert {"DCB", "DAG"} <= codes
    # 4+ letter words ("what", "tile", "tiles", "overall") are never codes.
    assert "TILE" not in codes and "WHAT" not in codes


@pytest.mark.asyncio
async def test_general_ct_question_grounds_full_tile_inventory(monkeypatch):
    """'list all tiles' grounds the TRUE 169-tile total + per-type / per-mode
    breakdown (so the model stops claiming the lookup is truncating), alongside
    the full 24-relic list. The other ~145 tiles are summarised, not enumerated.
    """
    _patch_full_map(monkeypatch, _ct_placements_from_fixture())
    out = await ctx.build("list all tiles you can see")

    map_lines = [f for f in out.facts if f.startswith("[btd6_ct_map]")]
    tile_lines = [f for f in out.facts if f.startswith("[btd6_ct_tile]")]
    assert map_lines, "no [btd6_ct_map] inventory line"
    total_line = map_lines[0]
    assert "169 tiles total" in total_line
    assert "97 Regular" in total_line and "24 Relic" in total_line
    # A battle-mode breakdown line is present too.
    assert any("battle modes" in ln for ln in map_lines)
    # All 24 relic tiles are still listed in full; the 145 plain tiles are NOT
    # enumerated (so the relic tiles are the only per-tile lines for a broad
    # listing — no false specific lines from words like "all"/"you"/"see").
    assert len(tile_lines) == 24, len(tile_lines)


@pytest.mark.asyncio
async def test_specific_tile_lookup_grounds_any_type(monkeypatch):
    """A tile named by its code grounds a detailed line for ANY tile type —
    the EDN-style gap where non-relic tiles were invisible."""
    _patch_full_map(monkeypatch, _ct_placements_from_fixture())

    # DAG is a Banner tile (no relic) — previously unreachable.
    out = await ctx.build("what is on tile DAG")
    dag = [f for f in out.facts if "tile DAG" in f]
    assert dag, "non-relic tile DAG was not grounded"
    assert any("Banner" in ln for ln in dag)

    # DCB is a relic tile — its detailed line names the relic it carries.
    out2 = await ctx.build("what's on tile DCB")
    dcb = [f for f in out2.facts if "tile DCB (" in f and "—" in f]
    assert dcb and any("Air and Sea" in ln for ln in dcb), dcb


@pytest.mark.asyncio
async def test_unknown_tile_code_grounds_no_phantom_tile(monkeypatch):
    """A code that isn't a real tile in the event grounds no tile line, so the
    model can say it's absent instead of inventing it (e.g. 'EDN')."""
    _patch_full_map(monkeypatch, _ct_placements_from_fixture())
    out = await ctx.build("is there anything on tile ZZZ in the current ct")
    assert not [f for f in out.facts if "tile ZZZ" in f]
