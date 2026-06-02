"""Tests for btd6_capability_service against the real committed stats.

These pin the cross-entity "which tower has property X" answers that the
entity resolver cannot produce — derived live from the per-tier stats.
"""

from __future__ import annotations

import pytest

from services import btd6_capability_service as cap
from services import btd6_stats_service as ss


@pytest.fixture(autouse=True)
def _fresh():
    ss.reset_cache()
    yield
    ss.reset_cache()


def _ids(hits) -> set[str]:
    return {h.tower_id for h in hits}


def test_camo_detection_unupgraded_is_ninja_only():
    hits = cap.towers_with_capability(cap.CAMO_DETECTION, unupgraded=True)
    ids = _ids(hits)
    assert "ninja_monkey" in ids
    assert "dart_monkey" not in ids
    # Detail explains where it comes from.
    ninja = next(h for h in hits if h.tower_id == "ninja_monkey")
    assert "0-0-0" in ninja.detail


def test_lead_popping_unupgraded_includes_explosive_and_acid_towers():
    ids = _ids(cap.towers_with_capability(cap.LEAD_POPPING, unupgraded=True))
    # Explosive / acid towers pop Lead at base; sharp ones do not.
    assert {"bomb_shooter", "mortar_monkey", "alchemist"} <= ids
    assert "dart_monkey" not in ids
    assert "boomerang_monkey" not in ids


def test_unupgraded_false_includes_upgrade_granted_camo():
    base_only = _ids(cap.towers_with_capability(cap.CAMO_DETECTION, unupgraded=True))
    with_upgrades = _ids(
        cap.towers_with_capability(cap.CAMO_DETECTION, unupgraded=False),
    )
    # Dart Monkey gains camo via an upgrade, so it appears only in the wider set.
    assert "dart_monkey" in with_upgrades
    assert "dart_monkey" not in base_only
    assert base_only <= with_upgrades


def test_unknown_capability_returns_empty():
    assert cap.towers_with_capability("flying") == []
    assert cap.towers_with_capability("") == []


def test_black_popping_unupgraded_excludes_explosion_towers():
    ids = _ids(cap.towers_with_capability(cap.BLACK_POPPING, unupgraded=True))
    # Black bloons are immune to explosions: bomb/mortar can't pop them at
    # base, but sharp towers can.
    assert "dart_monkey" in ids
    assert {"bomb_shooter", "mortar_monkey"}.isdisjoint(ids)


def test_white_popping_unupgraded_excludes_cold_towers():
    ids = _ids(cap.towers_with_capability(cap.WHITE_POPPING, unupgraded=True))
    # White bloons are immune to cold: the Ice Monkey can't pop them.
    assert "dart_monkey" in ids
    assert "ice_monkey" not in ids


def test_purple_popping_unupgraded_excludes_magic_towers():
    ids = _ids(cap.towers_with_capability(cap.PURPLE_POPPING, unupgraded=True))
    # Purple bloons are immune to magic: the Wizard Monkey can't pop them at base.
    assert "dart_monkey" in ids
    assert "wizard_monkey" not in ids


def test_capabilities_constant_is_the_supported_set():
    assert set(cap.CAPABILITIES) == {
        cap.CAMO_DETECTION,
        cap.LEAD_POPPING,
        cap.BLACK_POPPING,
        cap.WHITE_POPPING,
        cap.PURPLE_POPPING,
    }


def test_paragon_camo_covers_all_13_and_splits_correctly():
    hits = cap.paragons_with_capability(cap.CAMO_DETECTION)
    # Exactly the 13 tower paragons, no heroes.
    assert len(hits) == len(ss.list_paragon_ids()) == 13
    can = {h.paragon for h in hits if h.has_capability}
    cannot = {h.paragon for h in hits if not h.has_capability}
    # The five without innate camo (curated from bloonswiki + stats).
    assert cannot == {
        "Ballistic Obliteration Missile Bunker",
        "Crucible of Steel and Flame",
        "Mega Massive Munitions Factory",
        "Herald of Everfrost",
        "Root of all Nature",
    }
    # Spot-check the resolved-from-wiki cases.
    assert "Glaive Dominus" in can  # "innate camo detection"
    assert "Ascended Shadow" in can  # grants global camo detection
    assert "Herald of Everfrost" not in can  # only receives camo buffs


def test_paragon_camo_curation_keys_match_real_paragons():
    # Every curated key must be a real paragon id (no typos / stale ids).
    assert set(cap._PARAGON_CAMO) == set(ss.list_paragon_ids())


def test_paragons_with_capability_only_supports_camo():
    assert cap.paragons_with_capability(cap.LEAD_POPPING) == []
    assert cap.paragons_with_capability("nonsense") == []
