"""The V-16 paper-doll compositor — manifest convention, layout, fallbacks."""

from __future__ import annotations

from utils import character_render as cr
from utils import equipment as eq

_FULL = {
    eq.TOOL: "diamond pickaxe",
    eq.LIGHT: "diamond lantern",
    eq.CHARM: "lucky charm",
    eq.WEAPON: "diamond sword",
    eq.SHIELD: "diamond shield",
    eq.HELMET: "diamond helmet",
    eq.CHESTPLATE: "diamond chestplate",
    eq.LEGGINGS: "diamond leggings",
    eq.BOOTS: "diamond boots",
}


def test_every_slot_has_an_anchor():
    assert set(cr.SLOT_ANCHORS) == set(eq.SLOTS)


def test_sprite_filenames_follow_the_owner_pack_convention():
    # Tiered set gear → "{family}_{tier}.png" (the PythonAnywhere pack names).
    assert cr.sprite_filename("diamond sword") == "sword_diamond.png"
    assert cr.sprite_filename("Bronze Boots") == "boots_bronze.png"
    assert cr.sprite_filename("iron chestplate") == "chestplate_iron.png"
    # Untiered gear → spaces become underscores.
    assert cr.sprite_filename("iron pickaxe") == "iron_pickaxe.png"
    assert cr.sprite_filename("torch") == "torch.png"
    assert cr.sprite_filename("lucky charm") == "lucky_charm.png"


def test_spec_builds_one_layer_per_equipped_item(tmp_path):
    spec = cr.build_character_spec(_FULL, asset_dir=str(tmp_path))
    assert len(spec.layers) == len(_FULL)
    assert {layer.slot for layer in spec.layers} == set(_FULL)
    # No sprites on disk → every layer is a placeholder, in the tier palette.
    assert all(layer.sprite_path is None for layer in spec.layers)
    doll_layer = next(la for la in spec.layers if la.slot == eq.WEAPON)
    assert doll_layer.color == cr.TIER_COLORS["diamond"]
    assert spec.base_sprite_path is None


def test_spec_skips_empty_slots(tmp_path):
    spec = cr.build_character_spec({eq.TOOL: "pickaxe"}, asset_dir=str(tmp_path))
    assert [layer.slot for layer in spec.layers] == [eq.TOOL]
    # Untiered gear renders in the neutral colour, not a tier colour.
    assert spec.layers[0].color not in cr.TIER_COLORS.values()


def test_spec_resolves_sprites_that_exist(tmp_path):
    (tmp_path / "sword_diamond.png").write_bytes(b"not really a png")
    (tmp_path / cr.BASE_SPRITE).write_bytes(b"also not a png")
    spec = cr.build_character_spec(
        {eq.WEAPON: "diamond sword", eq.BOOTS: "diamond boots"},
        asset_dir=str(tmp_path),
    )
    by_slot = {layer.slot: layer for layer in spec.layers}
    assert by_slot[eq.WEAPON].sprite_path is not None  # file present → used
    assert by_slot[eq.BOOTS].sprite_path is None  # file absent → placeholder
    assert spec.base_sprite_path is not None


def test_render_returns_png_bytes_with_pillow(tmp_path):
    import pytest

    pytest.importorskip("PIL")
    png = cr.render_character_for(_FULL, asset_dir=str(tmp_path))
    assert png is not None and png[:8] == b"\x89PNG\r\n\x1a\n"
    # Empty loadout renders the bare figure (still a valid card).
    bare = cr.render_character_for({}, asset_dir=str(tmp_path))
    assert bare is not None and bare[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_survives_a_corrupt_sprite_file(tmp_path):
    import pytest

    pytest.importorskip("PIL")
    (tmp_path / "sword_diamond.png").write_bytes(b"corrupt")
    (tmp_path / cr.BASE_SPRITE).write_bytes(b"corrupt")
    # A bad PNG falls back to the placeholder — the panel must never break.
    png = cr.render_character_for({eq.WEAPON: "diamond sword"}, asset_dir=str(tmp_path))
    assert png is not None and png[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_is_cached_per_spec(tmp_path):
    import pytest

    pytest.importorskip("PIL")
    spec = cr.build_character_spec(_FULL, asset_dir=str(tmp_path))
    assert cr.render_character(spec) is cr.render_character(spec)
