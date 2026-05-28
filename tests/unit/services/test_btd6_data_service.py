"""Validation tests for the BTD6 deterministic dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.btd6_data_service import (
    DATA_ROOT,
    BTD6DataValidationError,
    get_dataset,
    reset_cache,
)


@pytest.fixture(autouse=True)
def _reset_dataset_cache():
    """Each test starts from a fresh dataset load."""
    reset_cache()
    yield
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

    # Point the loader at the broken copy by patching DATA_ROOT.
    import services.btd6_data_service as data_service

    original = data_service.DATA_ROOT
    data_service.DATA_ROOT = bad_root
    try:
        reset_cache()
        with pytest.raises(BTD6DataValidationError, match="alias collision"):
            get_dataset()
    finally:
        data_service.DATA_ROOT = original
        reset_cache()


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

    import services.btd6_data_service as data_service

    original = data_service.DATA_ROOT
    data_service.DATA_ROOT = bad_root
    try:
        reset_cache()
        with pytest.raises(BTD6DataValidationError, match="duplicate"):
            get_dataset()
    finally:
        data_service.DATA_ROOT = original
        reset_cache()


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

    import services.btd6_data_service as data_service

    original = data_service.DATA_ROOT
    data_service.DATA_ROOT = bad_root
    try:
        reset_cache()
        with pytest.raises(BTD6DataValidationError, match="missing required"):
            get_dataset()
    finally:
        data_service.DATA_ROOT = original
        reset_cache()


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
    import services.btd6_data_service as data_service

    original = data_service.DATA_ROOT
    data_service.DATA_ROOT = bad_root
    try:
        reset_cache()
        with pytest.raises(BTD6DataValidationError, match=match):
            get_dataset()
    finally:
        data_service.DATA_ROOT = original
        reset_cache()


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
