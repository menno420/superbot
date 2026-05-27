"""Required mapping coverage for tower / hero ↔ Ninja Kiwi API keys.

If a new tower / hero is added to ``data/btd6/towers.json`` /
``heroes.json`` without a matching entry in
``_TOWER_ID_TO_API_KEY`` / ``_HERO_ID_TO_API_KEY``, ``/btd6 tower``
and ``/btd6 hero`` will silently return no active-event restrictions
for that entity. This test fails loudly when the maps drift.
"""

from __future__ import annotations

import json
from pathlib import Path

from services import btd6_live_query_service as live

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BTD6_DATA = _REPO_ROOT / "disbot" / "data" / "btd6"


def _load_ids(filename: str, key: str) -> list[str]:
    with (_BTD6_DATA / filename).open(encoding="utf-8") as fh:
        data = json.load(fh)
    return [entry["id"] for entry in data.get(key, [])]


def test_every_tower_has_explicit_api_mapping():
    seed_ids = _load_ids("towers.json", "towers")
    missing = [tid for tid in seed_ids if tid not in live._TOWER_ID_TO_API_KEY]
    assert not missing, (
        f"Towers missing from _TOWER_ID_TO_API_KEY: {missing}. "
        "Add explicit entries — the canonical NK key is the CamelCase form "
        "(e.g. 'dart_monkey' → 'DartMonkey')."
    )


def test_every_hero_has_explicit_api_mapping():
    seed_ids = _load_ids("heroes.json", "heroes")
    missing = [hid for hid in seed_ids if hid not in live._HERO_ID_TO_API_KEY]
    assert not missing, (
        f"Heroes missing from _HERO_ID_TO_API_KEY: {missing}. "
        "Add explicit entries — the canonical NK key is the CamelCase form "
        "(e.g. 'quincy' → 'Quincy')."
    )


def test_tower_mapping_has_no_empty_values():
    for key, value in live._TOWER_ID_TO_API_KEY.items():
        assert value, f"empty API key for tower id {key!r}"


def test_hero_mapping_has_no_empty_values():
    for key, value in live._HERO_ID_TO_API_KEY.items():
        assert value, f"empty API key for hero id {key!r}"


def test_tower_mapping_has_no_duplicate_values():
    values = list(live._TOWER_ID_TO_API_KEY.values())
    assert len(values) == len(
        set(values)
    ), f"Duplicate API keys in _TOWER_ID_TO_API_KEY: {values}"


def test_hero_mapping_has_no_duplicate_values():
    values = list(live._HERO_ID_TO_API_KEY.values())
    assert len(values) == len(
        set(values)
    ), f"Duplicate API keys in _HERO_ID_TO_API_KEY: {values}"


def test_chosen_primary_hero_is_sentinel_only():
    seed_ids = _load_ids("heroes.json", "heroes")
    assert "ChosenPrimaryHero" not in seed_ids
    assert "ChosenPrimaryHero" not in live._HERO_ID_TO_API_KEY
    assert "ChosenPrimaryHero" not in live._HERO_ID_TO_API_KEY.values()
    # Sentinel constant must be defined so the scan code can reference it.
    assert live._CHOSEN_PRIMARY_HERO_KEY == "ChosenPrimaryHero"
