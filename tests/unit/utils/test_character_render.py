"""The V-16 paper-doll compositor — manifest convention, layout, fallbacks."""

from __future__ import annotations

import os

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


def test_every_slot_has_a_default_layout():
    assert set(cr.DEFAULT_LAYOUT) == set(eq.SLOTS)


def test_sprite_filenames_follow_the_pack_convention():
    # Tiered set gear → "{family}_{tier}.png" (the seeded pack / owner names).
    assert cr.sprite_filename("diamond sword") == "sword_diamond.png"
    assert cr.sprite_filename("Bronze Boots") == "boots_bronze.png"
    assert cr.sprite_filename("iron chestplate") == "chestplate_iron.png"
    # Set starters → the family base sprite.
    assert cr.sprite_filename("sword") == "sword.png"
    assert cr.sprite_filename("shield") == "shield.png"
    # Non-set gear → spaces become underscores.
    assert cr.sprite_filename("iron pickaxe") == "iron_pickaxe.png"
    assert cr.sprite_filename("lucky charm") == "lucky_charm.png"


def test_the_seeded_repo_pack_resolves_every_set_item():
    # PR #701's pack + manifest: all 30 tiered items, both starters, and the
    # base doll must resolve to real files via the manifest.
    manifest = cr._load_manifest(cr.ASSET_DIR)
    assert manifest is not None
    names = [
        f"{tier} {family}"
        for tier in eq.TIER_ORDER
        for family in ("sword", "shield", "helmet", "chestplate", "leggings", "boots")
    ] + ["sword", "shield"]
    for name in names:
        path = os.path.join(cr.ASSET_DIR, cr.sprite_filename(name, manifest))
        assert os.path.isfile(path), path
    spec = cr.build_character_spec(_FULL)
    assert spec.base_sprite_path is not None
    by_slot = {layer.slot: layer for layer in spec.layers}
    for slot in eq.SET_SLOTS:
        assert by_slot[slot].sprite_path is not None, slot
    # Mining gear has no sprites in the seeded pack → placeholder layers.
    assert by_slot[eq.TOOL].sprite_path is None


def test_manifest_anchor_and_palette_win_over_defaults():
    manifest = cr._load_manifest(cr.ASSET_DIR)
    assert manifest is not None
    spec = cr.build_character_spec({eq.WEAPON: "diamond sword"})
    layer = spec.layers[0]
    anchor = manifest["families"]["sword"]["anchor"]
    scale = manifest["families"]["sword"]["scale"]
    side = int(256 * scale * 2)  # _RENDER_SCALE
    assert layer.box == (
        anchor[0] * 2 - side // 2,
        anchor[1] * 2 - side // 2,
        side,
        side,
    )
    assert layer.color == tuple(manifest["tier_palettes"]["diamond"])


def test_spec_in_an_empty_dir_falls_back_to_placeholders(tmp_path):
    spec = cr.build_character_spec(_FULL, asset_dir=str(tmp_path))
    assert len(spec.layers) == len(_FULL)
    assert {layer.slot for layer in spec.layers} == set(_FULL)
    assert all(layer.sprite_path is None for layer in spec.layers)
    assert spec.base_sprite_path is None
    doll_layer = next(la for la in spec.layers if la.slot == eq.WEAPON)
    assert doll_layer.color == cr.TIER_COLORS["diamond"]


def test_spec_skips_empty_slots(tmp_path):
    spec = cr.build_character_spec({eq.TOOL: "pickaxe"}, asset_dir=str(tmp_path))
    assert [layer.slot for layer in spec.layers] == [eq.TOOL]
    # Untiered gear renders in the neutral colour, not a tier colour.
    assert spec.layers[0].color not in cr.TIER_COLORS.values()


def test_render_returns_png_bytes_with_pillow():
    import pytest

    pytest.importorskip("PIL")
    png = cr.render_character_for(_FULL)  # the real seeded pack
    assert png is not None and png[:8] == b"\x89PNG\r\n\x1a\n"
    bare = cr.render_character_for({})
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


# --------------------------------------------------------------------------- #
# Home structure backdrop (mining Slice C)
# --------------------------------------------------------------------------- #


def test_home_backdrop_palette():
    # Level 0 (and unknown levels) → None → the default _BG (the additive case).
    assert cr.home_backdrop(0) is None
    assert cr.home_backdrop(99) is None
    # Built levels map to distinct, dark backdrops.
    assert cr.home_backdrop(1) == (43, 34, 28)
    assert cr.home_backdrop(2) == (40, 46, 54)
    assert cr.home_backdrop(3) == (34, 30, 58)
    assert set(cr.HOME_BACKDROPS) == {1, 2, 3}


def test_spec_backdrop_defaults_to_none():
    # The default spec carries no backdrop → byte-identical to the pre-Slice-C render.
    spec = cr.build_character_spec(_FULL)
    assert spec.backdrop is None
    # home_level=0 must produce the exact same spec as omitting it.
    assert cr.build_character_spec(_FULL, backdrop=cr.home_backdrop(0)).backdrop is None


def test_unbuilt_home_renders_byte_identical():
    import pytest

    pytest.importorskip("PIL")
    # The additive guarantee: home_level 0 == the historical render, byte for byte.
    assert cr.render_character_for(_FULL) == cr.render_character_for(
        _FULL, home_level=0
    )


def test_built_home_changes_the_render():
    import pytest

    pytest.importorskip("PIL")
    # A built Home actually changes the card (different backdrop → different bytes).
    base = cr.render_character_for(_FULL, home_level=0)
    built = cr.render_character_for(_FULL, home_level=2)
    assert base is not None and built is not None
    assert base != built
