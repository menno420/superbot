"""Tests for utils.mining.world — pure depth↔biome + descent-gating model.

These pin the descent-gating decision (brainstorm §6.8 P2): depth access is
gated by the equipped-gear ``depth_access`` stat (torch → Cavern, lantern →
Deep) and is persistent, not consumed per descent.
"""

from __future__ import annotations

from utils.mining import world
from utils.mining.exploration import BIOME_ORDER, Biome
from utils.equipment import EffectiveStats


def test_max_depth_is_deepest_band_index():
    assert world.MAX_DEPTH == len(BIOME_ORDER) - 1
    assert world.MAX_DEPTH == 3  # SURFACE, CAVERN, DEEP, MAGMA


def test_clamp_depth_bounds():
    assert world.clamp_depth(-5) == 0
    assert world.clamp_depth(0) == 0
    assert world.clamp_depth(2) == 2
    assert world.clamp_depth(99) == world.MAX_DEPTH


def test_biome_for_depth_maps_each_band():
    assert world.biome_for_depth(0) == Biome.SURFACE
    assert world.biome_for_depth(1) == Biome.CAVERN
    assert world.biome_for_depth(2) == Biome.DEEP
    assert world.biome_for_depth(3) == Biome.MAGMA
    # Out-of-range depths clamp, never raise.
    assert world.biome_for_depth(-1) == Biome.SURFACE
    assert world.biome_for_depth(100) == Biome.MAGMA


def test_biome_for_depth_matches_exploration_depth_ordering():
    # The two modules must agree on the depth↔biome mapping; world derives its
    # ordering from exploration.BIOME_ORDER so they can never drift.
    for depth, biome in enumerate(BIOME_ORDER):
        assert world.biome_for_depth(depth) == biome


def test_max_accessible_depth_tracks_depth_access_stat():
    assert world.max_accessible_depth(EffectiveStats()) == 0  # no light → surface
    assert world.max_accessible_depth(EffectiveStats(depth_access=1)) == 1  # torch
    assert world.max_accessible_depth(EffectiveStats(depth_access=2)) == 2  # lantern
    # Beyond the deepest band clamps.
    assert (
        world.max_accessible_depth(EffectiveStats(depth_access=9)) == world.MAX_DEPTH
    )


def test_torch_unlocks_cavern_lantern_unlocks_deep():
    torch = EffectiveStats(depth_access=1)
    lantern = EffectiveStats(depth_access=2)
    # From the surface a torch can reach Cavern but not Deep.
    assert world.can_descend(0, torch)
    assert world.descend(0, torch) == 1
    assert not world.can_descend(1, torch)  # torch tops out at Cavern
    assert world.descend(1, torch) == 1  # blocked → unchanged
    # A lantern reaches one band deeper.
    assert world.can_descend(1, lantern)
    assert world.descend(1, lantern) == 2


def test_no_light_cannot_descend():
    assert not world.can_descend(0, EffectiveStats())
    assert world.descend(0, EffectiveStats()) == 0


def test_magma_is_unreachable_with_current_gear():
    # No shipped gear grants depth_access 3, so the Magma core stays aspirational.
    lantern = EffectiveStats(depth_access=2)
    assert not world.can_descend(2, lantern)
    assert world.descend(2, lantern) == 2


def test_ascend_always_climbs_toward_surface():
    assert world.can_ascend(2)
    assert world.ascend(2) == 1
    assert world.ascend(1) == 0
    # Already at the surface — never goes negative.
    assert not world.can_ascend(0)
    assert world.ascend(0) == 0


def test_descend_never_exceeds_accessible_or_max():
    deep_gear = EffectiveStats(depth_access=9)
    d = 0
    for _ in range(10):
        d = world.descend(d, deep_gear)
    assert d == world.MAX_DEPTH


def test_describe_position_includes_label_and_depth():
    text = world.describe_position(1)
    assert "Cavern" in text
    assert "depth 1/3" in text


def test_descend_hint_names_next_band_when_blocked():
    # Empty-handed: the hint should point at the first locked band (Cavern).
    assert "Cavern" in world.descend_hint(EffectiveStats())
    # Fully geared (hypothetically): no further band to advertise.
    maxed = EffectiveStats(depth_access=world.MAX_DEPTH)
    assert "deepest" in world.descend_hint(maxed).lower()
