"""Pure grid-Mine model — seed determinism, movement, loot folding, render.

The grid Mine world (hub-redesign PR 3, Q-0173) is a pure function of the world
seed + ``(x, y, z)``, so every property here is checkable without Discord or a DB.
"""

from __future__ import annotations

from utils.mining import grid
from utils.mining.grid import Cell, CellFeature
from utils.mining.rewards import ore_weights_for_depth

# ---------------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------------


def test_step_moves_one_cell_per_compass_direction():
    assert grid.step(0, 0, grid.NORTH) == (0, 1)
    assert grid.step(0, 0, grid.SOUTH) == (0, -1)
    assert grid.step(0, 0, grid.EAST) == (1, 0)
    assert grid.step(0, 0, grid.WEST) == (-1, 0)


def test_step_leaves_position_unchanged_for_vertical_or_unknown():
    # Up/Down change the depth band (z), handled by the caller — not step().
    assert grid.step(3, 4, grid.UP) == (3, 4)
    assert grid.step(3, 4, grid.DOWN) == (3, 4)
    assert grid.step(3, 4, "elsewhere") == (3, 4)


def test_lateral_and_vertical_token_sets_are_disjoint_and_complete():
    assert grid.LATERAL == {grid.NORTH, grid.SOUTH, grid.EAST, grid.WEST}
    assert grid.VERTICAL == {grid.UP, grid.DOWN}
    assert grid.LATERAL.isdisjoint(grid.VERTICAL)
    assert grid.DIRECTIONS == grid.LATERAL | grid.VERTICAL


def test_move_phrase_is_human_readable():
    assert grid.move_phrase(grid.NORTH) == "north"
    assert grid.move_phrase(grid.DOWN) == "deeper"


# ---------------------------------------------------------------------------
# Cell content — seed-deterministic
# ---------------------------------------------------------------------------


def test_cell_at_is_deterministic_for_the_same_inputs():
    a = grid.cell_at(12345, 3, -7, 2)
    b = grid.cell_at(12345, 3, -7, 2)
    assert a == b


def test_cell_at_invariants_hold_for_any_output():
    valid_ores = set(ore_weights_for_depth(0))
    for x in range(-3, 4):
        for y in range(-3, 4):
            cell = grid.cell_at(999, x, y, 1)
            assert cell.feature in CellFeature
            assert cell.featured_resource in valid_ores
            assert cell.richness == grid._RICHNESS[cell.feature]
            assert cell.x == x and cell.y == y and cell.z == 1


def test_cell_at_varies_across_coordinates():
    """A flat/constant world would be a hashing bug — assert variety."""
    features = {
        grid.cell_at(42, x, y, 0).feature for x in range(-5, 6) for y in range(-5, 6)
    }
    assert len(features) > 1


def test_cell_at_seed_changes_the_world():
    """Different seeds give different worlds (Q-0173 shareable seeds)."""
    world_a = [grid.cell_at(1, x, 0, 0).feature for x in range(20)]
    world_b = [grid.cell_at(2, x, 0, 0).feature for x in range(20)]
    assert world_a != world_b


def test_deeper_cells_favor_richer_featured_ore():
    """z = depth band carries 'deeper = richer' (reuses ore_weights_for_depth)."""
    surface = [grid.cell_at(7, x, 0, 0).featured_resource for x in range(200)]
    deep = [grid.cell_at(7, x, 0, 3).featured_resource for x in range(200)]
    assert deep.count("diamond") > surface.count("diamond")


# ---------------------------------------------------------------------------
# Loot folding
# ---------------------------------------------------------------------------


def _cell(feature: CellFeature, ore: str = "gold") -> Cell:
    return Cell(0, 0, 0, feature, ore, grid._RICHNESS[feature])


def test_rich_cell_yields_its_featured_ore_and_scales_amount():
    found, amount, note = grid.apply_cell_to_loot(
        _cell(CellFeature.RICH, "iron"), "stone", 3
    )
    assert found == "iron"  # the lucky strike overrides the base roll
    assert amount == 6  # 3 × richness 2.0
    assert note and "rich" in note.lower()


def test_treasure_cell_doubles_and_features_its_ore():
    found, amount, note = grid.apply_cell_to_loot(
        _cell(CellFeature.TREASURE, "diamond"),
        "stone",
        2,
    )
    assert found == "diamond"
    assert amount == 4  # 2 × 2.0 (treasure richness trimmed ×3 → ×2, 2026-06-22)
    assert note is not None


def test_barren_cell_keeps_the_base_ore_but_never_zero():
    found, amount, note = grid.apply_cell_to_loot(_cell(CellFeature.BARREN), "stone", 1)
    assert found == "stone"  # barren does NOT override the base roll
    assert amount == 1  # max(1, round(1 × 0.5)) — never nothing
    assert note and "barren" in note.lower()


def test_normal_cell_is_a_passthrough_with_no_note():
    found, amount, note = grid.apply_cell_to_loot(_cell(CellFeature.NORMAL), "gold", 4)
    assert (found, amount, note) == ("gold", 4, None)


# ---------------------------------------------------------------------------
# Map render (fog of war)
# ---------------------------------------------------------------------------


def test_render_places_player_at_centre():
    body = grid.render_local_map(1, 0, 0, 0, discovered=set(), radius=1)
    rows = body.split("\n")
    assert len(rows) == 3  # (2·radius + 1) rows
    centre = rows[1].split(" ")
    assert centre[1] == grid.PLAYER_GLYPH


def test_unvisited_cells_render_as_fog():
    body = grid.render_local_map(1, 0, 0, 0, discovered=set(), radius=1)
    # Every non-player glyph is fog when nothing has been discovered.
    glyphs = set(body.replace("\n", " ").split(" "))
    assert glyphs == {grid.PLAYER_GLYPH, grid.FOG_GLYPH}


def test_discovered_cells_show_their_feature_glyph():
    # Reveal one neighbour; it must no longer render as fog.
    body = grid.render_local_map(1, 0, 0, 0, discovered={(1, 0)}, radius=1)
    glyphs = set(body.replace("\n", " ").split(" "))
    assert glyphs - {
        grid.PLAYER_GLYPH,
        grid.FOG_GLYPH,
    }, "a revealed cell should show a feature glyph"


def test_describe_cell_mentions_ore_only_for_notable_cells():
    assert "rich vein" in grid.describe_cell(_cell(CellFeature.RICH, "gold"))
    assert "gold" in grid.describe_cell(_cell(CellFeature.RICH, "gold"))
    # NORMAL cells don't name an ore (nothing notable underfoot).
    assert "(" not in grid.describe_cell(_cell(CellFeature.NORMAL))
