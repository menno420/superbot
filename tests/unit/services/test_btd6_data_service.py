"""Validation tests for the BTD6 deterministic dataset."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from services.btd6_data_provider import FileRawProvider
from services.btd6_data_service import (
    DATA_ROOT,
    BTD6DataValidationError,
    find_geraldo_item,
    get_dataset,
    get_geraldo_item,
    get_monkey_knowledge,
    get_power,
    get_provider,
    reset_cache,
    set_provider,
)


@pytest.fixture(autouse=True)
def _reset_dataset_cache():
    """Each test starts from a fresh dataset load."""
    reset_cache()
    yield
    reset_cache()


@contextmanager
def _use_root(root: Path):
    """Point the dataset loader at a staged fixture root via the provider seam.

    Replaces the historical ``data_service.DATA_ROOT = bad_root`` patching —
    reads now funnel through the swappable ``FileRawProvider``, so staging a
    fixture set means installing a provider rooted at the temp dir and
    restoring the previous one afterwards.
    """
    original = get_provider()
    set_provider(FileRawProvider(root))
    reset_cache()
    try:
        yield
    finally:
        set_provider(original)
        reset_cache()


def test_dataset_loads_with_metadata():
    dataset = get_dataset()
    assert dataset.data_version
    assert dataset.game_version
    for category in ("towers", "heroes", "maps", "modes", "rounds"):
        assert category in dataset.sources, f"missing source for {category}"


def test_dataset_has_representative_entries():
    dataset = get_dataset()
    assert len(dataset.towers) >= 4
    assert len(dataset.heroes) >= 2
    assert len(dataset.maps) >= 3
    assert len(dataset.modes) >= 2
    assert len(dataset.rounds) >= 5


def test_powers_and_monkey_knowledge_load_and_resolve():
    dataset = get_dataset()
    assert len(dataset.powers) >= 20
    assert len(dataset.monkey_knowledge) >= 100
    # Power resolves by catalog id and by game-native power_id.
    boost = get_power("monkey_boost")
    assert boost is not None and boost.canonical == "Monkey Boost"
    assert get_power("MonkeyBoost") is boost
    assert boost.monkey_money_cost == 100
    # The structured headline effect (2x speed / 15s) is decoded, and the prose
    # has no unfilled placeholder.
    assert boost.effect == {"rate_scale": 0.5, "duration_seconds": 15}
    assert "{0}" not in boost.description
    # Monkey knowledge carries its in-game category + costs.
    mk = get_monkey_knowledge("aviation_grade_glue")
    assert mk is not None
    assert mk.category in {"Primary", "Military", "Magic", "Support", "Heroes", "Powers"}
    assert mk.monkey_money_cost >= 0 and mk.investment_required >= 0
    # Every MK category folder is represented.
    cats = {k.category for k in dataset.monkey_knowledge}
    assert {"Primary", "Military", "Magic", "Support", "Heroes", "Powers"} <= cats


def test_geraldo_items_load_and_resolve():
    dataset = get_dataset()
    # All 16 of Geraldo's shop items are ingested.
    assert len(dataset.geraldo_items) == 16
    # Resolves by catalog id and (fuzzily) by canonical name / partial.
    totem = get_geraldo_item("paragon_power_totem")
    assert totem is not None and totem.canonical == "Paragon Power Totem"
    assert totem.cost == 26000 and totem.unlock_level == 20
    assert find_geraldo_item("Genie Bottle") is get_geraldo_item("genie_bottle")
    assert find_geraldo_item("pickle").canonical == "Jar of Pickles"
    # Every item carries a game-authored name + description and a sane cost.
    for item in dataset.geraldo_items:
        assert item.canonical and item.description
        assert item.cost > 0 and item.unlock_level >= 0
        assert item.max_quantity >= item.starting_quantity >= 0
    # Unknown / ambiguous lookups fail closed rather than guessing.
    assert get_geraldo_item("nope") is None
    assert find_geraldo_item("") is None


def test_map_removables_curated_for_known_maps_only():
    # Removable obstacles are bloonswiki-curated (not in the dump). They must
    # land on the maps we have data for, and stay blank (= "no data", not
    # "none") everywhere else — so the bot never implies a map has no removables.
    by_id = {m.id: m for m in get_dataset().maps}
    assert "trucks" in by_id["cargo"].removables.lower()
    assert "round 39" in by_id["cargo"].removables  # the unlock condition survives
    assert by_id["cornfield"].removables  # Advanced map with curated removables
    # A map with no curated data carries an empty string, never a fabricated note.
    assert by_id["tree_stump"].removables == ""


def test_map_grounding_surfaces_removables():
    # The map fact the model sees (via btd6_response_builder.for_map) must carry
    # removables alongside line-of-sight — answering "what removables on X".
    from services import btd6_response_builder as rb

    by_id = {m.id: m for m in get_dataset().maps}
    why = rb.for_map(by_id["cargo"]).why_it_matters
    assert "Removable obstacles:" in why and "trucks" in why.lower()
    # No removables data → no removables clause (not "has none").
    assert "Removable obstacles" not in rb.for_map(by_id["tree_stump"]).why_it_matters


def test_tower_upgrade_paths_have_five_tiers():
    dataset = get_dataset()
    for tower in dataset.towers:
        for path_name, tiers in tower.upgrade_paths.items():
            assert (
                len(tiers) == 5
            ), f"{tower.id}.{path_name} should have 5 tiers, got {len(tiers)}"


def test_chimps_mode_has_no_income_restriction():
    dataset = get_dataset()
    chimps = next((m for m in dataset.modes if m.id == "chimps"), None)
    assert chimps is not None, "CHIMPS mode must be in the fixture"
    assert any(
        "income" in r.lower() or "farm" in r.lower() for r in chimps.restrictions
    )


def test_alias_collision_fails_loudly(tmp_path):
    """A duplicate alias across categories must abort dataset loading."""
    bad_root = tmp_path / "btd6"
    bad_root.mkdir()
    for filename in ("towers", "heroes", "maps", "modes", "rounds"):
        source = DATA_ROOT / f"{filename}.json"
        target = bad_root / f"{filename}.json"
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    # Inject a colliding alias: make a hero alias collide with a tower alias.
    heroes_path = bad_root / "heroes.json"
    heroes = json.loads(heroes_path.read_text(encoding="utf-8"))
    heroes["heroes"][0]["aliases"].append("dart")  # collides with Dart Monkey
    heroes_path.write_text(json.dumps(heroes), encoding="utf-8")

    # Point the loader at the broken copy via the provider seam.
    with _use_root(bad_root):
        with pytest.raises(BTD6DataValidationError, match="alias collision"):
            get_dataset()


def test_duplicate_canonical_name_fails_loudly(tmp_path):
    """Two towers with the same canonical name must fail validation."""
    bad_root = tmp_path / "btd6"
    bad_root.mkdir()
    for filename in ("towers", "heroes", "maps", "modes", "rounds"):
        source = DATA_ROOT / f"{filename}.json"
        target = bad_root / f"{filename}.json"
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    towers_path = bad_root / "towers.json"
    towers = json.loads(towers_path.read_text(encoding="utf-8"))
    # Duplicate canonical name with a different id.
    clone = dict(towers["towers"][0])
    clone["id"] = "dart_monkey_copy"
    clone["aliases"] = ["dart-monkey-copy-alias"]
    towers["towers"].append(clone)
    towers_path.write_text(json.dumps(towers), encoding="utf-8")

    with _use_root(bad_root):
        with pytest.raises(BTD6DataValidationError, match="duplicate"):
            get_dataset()


def test_missing_required_field_fails_loudly(tmp_path):
    """A tower entry missing required fields must fail validation."""
    bad_root = tmp_path / "btd6"
    bad_root.mkdir()
    for filename in ("towers", "heroes", "maps", "modes", "rounds"):
        source = DATA_ROOT / f"{filename}.json"
        target = bad_root / f"{filename}.json"
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    towers_path = bad_root / "towers.json"
    towers = json.loads(towers_path.read_text(encoding="utf-8"))
    del towers["towers"][0]["base_cost"]
    towers_path.write_text(json.dumps(towers), encoding="utf-8")

    with _use_root(bad_root):
        with pytest.raises(BTD6DataValidationError, match="missing required"):
            get_dataset()


# ---------------------------------------------------------------------------
# Extended validation: category, base_cost, upgrade-path shape
# ---------------------------------------------------------------------------


def _stage_data(tmp_path: Path) -> Path:
    """Copy every fixture into a fresh root so tests can mutate one safely."""
    root = tmp_path / "btd6"
    root.mkdir()
    for filename in ("towers", "heroes", "maps", "modes", "rounds"):
        source = DATA_ROOT / f"{filename}.json"
        (root / f"{filename}.json").write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    return root


def _expect_validation_error(
    bad_root: Path,
    *,
    match: str,
) -> None:
    with _use_root(bad_root):
        with pytest.raises(BTD6DataValidationError, match=match):
            get_dataset()


def test_invalid_tower_category_fails(tmp_path):
    bad_root = _stage_data(tmp_path)
    towers_path = bad_root / "towers.json"
    towers = json.loads(towers_path.read_text(encoding="utf-8"))
    towers["towers"][0]["category"] = "primay"  # deliberate typo
    towers_path.write_text(json.dumps(towers), encoding="utf-8")
    _expect_validation_error(bad_root, match="category 'primay'")


def test_zero_tower_base_cost_fails(tmp_path):
    bad_root = _stage_data(tmp_path)
    towers_path = bad_root / "towers.json"
    towers = json.loads(towers_path.read_text(encoding="utf-8"))
    towers["towers"][0]["base_cost"] = 0
    towers_path.write_text(json.dumps(towers), encoding="utf-8")
    _expect_validation_error(bad_root, match="base_cost must be > 0")


def test_negative_hero_base_cost_fails(tmp_path):
    bad_root = _stage_data(tmp_path)
    heroes_path = bad_root / "heroes.json"
    heroes = json.loads(heroes_path.read_text(encoding="utf-8"))
    heroes["heroes"][0]["base_cost"] = -100
    heroes_path.write_text(json.dumps(heroes), encoding="utf-8")
    _expect_validation_error(bad_root, match="base_cost must be > 0")


def test_missing_upgrade_path_key_fails(tmp_path):
    bad_root = _stage_data(tmp_path)
    towers_path = bad_root / "towers.json"
    towers = json.loads(towers_path.read_text(encoding="utf-8"))
    del towers["towers"][0]["upgrade_paths"]["bot"]
    towers_path.write_text(json.dumps(towers), encoding="utf-8")
    _expect_validation_error(bad_root, match="upgrade_paths missing keys")


def test_extra_upgrade_path_key_fails(tmp_path):
    bad_root = _stage_data(tmp_path)
    towers_path = bad_root / "towers.json"
    towers = json.loads(towers_path.read_text(encoding="utf-8"))
    towers["towers"][0]["upgrade_paths"]["extra"] = ["x"] * 5
    towers_path.write_text(json.dumps(towers), encoding="utf-8")
    _expect_validation_error(bad_root, match="unexpected keys")


def test_wrong_tier_count_fails(tmp_path):
    bad_root = _stage_data(tmp_path)
    towers_path = bad_root / "towers.json"
    towers = json.loads(towers_path.read_text(encoding="utf-8"))
    towers["towers"][0]["upgrade_paths"]["top"] = ["a", "b", "c"]
    towers_path.write_text(json.dumps(towers), encoding="utf-8")
    _expect_validation_error(bad_root, match="must have exactly 5 tiers")


def test_empty_upgrade_tier_name_fails(tmp_path):
    bad_root = _stage_data(tmp_path)
    towers_path = bad_root / "towers.json"
    towers = json.loads(towers_path.read_text(encoding="utf-8"))
    tiers = towers["towers"][0]["upgrade_paths"]["top"]
    tiers[2] = "   "
    towers["towers"][0]["upgrade_paths"]["top"] = tiers
    towers_path.write_text(json.dumps(towers), encoding="utf-8")
    _expect_validation_error(bad_root, match="tier 3 is empty")


# ---------------------------------------------------------------------------
# Bloons (optional fixture added after the original five)
# ---------------------------------------------------------------------------


def test_bloons_load_with_immunities():
    dataset = get_dataset()
    assert len(dataset.bloons) >= 10
    assert "bloons" in dataset.sources
    lead = next((b for b in dataset.bloons if b.id == "lead"), None)
    assert lead is not None, "Lead Bloon must be in the fixture"
    # Lead resists Sharp damage — the fact that answers "can a dart pop lead?".
    assert "Sharp" in lead.immune_to
    assert lead.children  # pops into something


def test_get_bloon_accessor():
    from services.btd6_data_service import get_bloon

    assert get_bloon("ceramic") is not None
    assert get_bloon("ddt").category == "moab_class"
    assert get_bloon("does_not_exist") is None


def test_bloons_include_basics_and_rbe():
    from services.btd6_data_service import get_bloon

    ids = {b.id for b in get_dataset().bloons}
    # The basics the old hand-curated file lacked are now present...
    assert {"red", "blue", "green", "yellow", "pink"} <= ids
    # ...and the wiki's test bloons are filtered out.
    assert not any(b.id.startswith("test") for b in get_dataset().bloons)
    ceramic = get_bloon("ceramic")
    assert ceramic.rbe and ceramic.rbe > 0
    assert ceramic.speed and ceramic.speed > 0
    moab = get_bloon("moab")
    # RBE is children-inclusive: a MOAB = its 200 layers + four full Ceramics.
    assert moab.rbe == moab.health + 4 * ceramic.rbe
    assert moab.health_fortified and moab.health_fortified > moab.health


def test_bloon_children_list_is_structured():
    from services.btd6_data_service import get_bloon

    assert get_bloon("lead").children_list == (
        {"bloon_id": "black", "count": 2, "modifiers": []},
    )
    # children/immunity are now game-data-sourced (the --bloons cutover). The
    # dump tags DDT's four Ceramic children as Regrow only — not Camo, which the
    # wiki had asserted — so the curated modifier here was corrected to the game's.
    ddt_child = get_bloon("ddt").children_list[0]
    assert ddt_child["bloon_id"] == "ceramic" and ddt_child["count"] == 4
    assert ddt_child["modifiers"] == ["regrow"]


def test_bloon_children_and_immunity_are_game_data_sourced():
    # The --bloons cutover sources children + immunity from the dump. Two
    # curated values the wiki had wrong are now the game's:
    from services.btd6_data_service import get_bloon

    # BAD spawns *camo* DDTs (the wiki dropped the camo tag).
    bad_ddt = next(c for c in get_bloon("bad").children_list if c["bloon_id"] == "ddt")
    assert bad_ddt["modifiers"] == ["camo"]
    assert "Camo DDTs" in get_bloon("bad").children
    # Immunity derived from the bloonProperties bitflag still matches the curated
    # set exactly (the inverter verified 23/23 against the wiki on v55).
    assert set(get_bloon("zebra").immune_to) == {
        "Explosion",
        "Glacier",
        "Cold",
        "Frigid",
    }


def test_curated_aliases_and_modifier_entries_preserved():
    from services.btd6_data_service import get_bloon

    # A curated alias survived the regen (resolver lookups must not regress)...
    assert "cerb" in get_bloon("ceramic").aliases
    # ...and the synthesised modifier entries (absent from Cargo) are kept.
    assert get_bloon("camo") is not None
    assert get_bloon("fortified") is not None


def test_invalid_bloon_rbe_fails(tmp_path):
    staged = _stage_data(tmp_path)
    (staged / "bloons.json").write_text(
        json.dumps(
            {
                "data_version": "1.0",
                "game_version": "54.0",
                "source": "test",
                "bloons": [
                    {
                        "id": "x",
                        "canonical": "X",
                        "aliases": ["xbloon"],
                        "category": "special",
                        "description": "d",
                        "rbe": 0,
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    _expect_validation_error(staged, match="rbe must be > 0")


# ---------------------------------------------------------------------------
# Rounds (full composition from Module:BTD6_rounds)
# ---------------------------------------------------------------------------


def test_rounds_full_composition_loads():
    from services.btd6_data_service import get_round

    assert len(get_dataset().rounds) == 140
    r63 = get_round(63)
    assert r63.rbe and r63.rbe > 0
    assert any(g["bloon_id"] == "ceramic" for g in r63.groups)
    assert r63.roundset == "default"
    assert get_round(100).groups[0]["bloon_id"] == "bad"


def test_round_cash_populated_for_all_140_rounds():
    from services.btd6_data_service import get_round

    # Per-round cash is derived from composition for every round (the recompute
    # is pinned by test_btd6_round_cash.py); income decay (rounds 51+) yields
    # fractional values, hence float.
    assert get_round(1).cash == 121 and get_round(1).cumulative_cash == 771
    assert get_round(80).cash == 1400.2 and get_round(80).cumulative_cash == 98253.6
    assert all(get_round(n).cash is not None for n in range(1, 141))
    # Cumulative is monotonic non-decreasing across all 140 rounds.
    cumulatives = [get_round(n).cumulative_cash for n in range(1, 141)]
    assert all(a <= b for a, b in zip(cumulatives, cumulatives[1:], strict=False))


def test_invalid_round_rbe_fails(tmp_path):
    staged = _stage_data(tmp_path)
    (staged / "rounds.json").write_text(
        json.dumps(
            {
                "data_version": "1.0",
                "game_version": "54.0",
                "source": "test",
                "rounds": [
                    {
                        "round": 1,
                        "summary": "s",
                        "danger": "low",
                        "common_threats": [],
                        "rbe": -5,
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    _expect_validation_error(staged, match="rbe must be >= 0")


def test_every_bloon_category_is_valid():
    from services.btd6_data_service import _BLOON_CATEGORIES

    for bloon in get_dataset().bloons:
        assert bloon.category in _BLOON_CATEGORIES


def test_dataset_loads_when_bloons_fixture_absent(tmp_path):
    """A missing bloons.json must degrade to an empty category, not abort."""
    # _stage_data copies only the original five files (no bloons.json).
    staged = _stage_data(tmp_path)
    assert not (staged / "bloons.json").exists()

    with _use_root(staged):
        dataset = get_dataset()  # must not raise
        assert dataset.bloons == ()
        assert "bloons" not in dataset.sources


def test_invalid_bloon_category_fails(tmp_path):
    staged = _stage_data(tmp_path)
    (staged / "bloons.json").write_text(
        json.dumps(
            {
                "data_version": "1.0",
                "game_version": "54.0",
                "source": "test",
                "bloons": [
                    {
                        "id": "x",
                        "canonical": "X",
                        "aliases": ["xbloon"],
                        "category": "not_a_category",
                        "description": "d",
                        "wiki_url": "u",
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    _expect_validation_error(staged, match="category 'not_a_category'")
