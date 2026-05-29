"""Tests for the pure (non-network) logic in ``scripts/fetch_bloonswiki.py``."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "fetch_bloonswiki.py"

_HEADER = (
    ["id", "canonical", "category", "aliases", "base_cost", "description"]
    + [f"{p}_{t}" for p in ("top", "mid", "bot") for t in range(1, 6)]
    + [f"{p}_{t}_cost" for p in ("top", "mid", "bot") for t in range(1, 6)]
    + ["wiki_url"]
)


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("fetch_bloonswiki_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _full_tower(mod, tower_id="bomb_shooter"):
    td = mod.TowerData(tower_id=tower_id, canonical="Bomb Shooter")
    td.base_cost = 375
    td.category = "primary"
    td.game_version = "54.0"
    for path in (1, 2, 3):
        for tier in range(1, 6):
            td.upgrades.append(
                {
                    "path": path,
                    "tier": tier,
                    "name": f"U{path}{tier}",
                    "cost": path * 100 + tier,
                    "xp": 10,
                },
            )
    return td


def test_int_parsing(mod):
    assert mod._int("1,100") == 1100
    assert mod._int("250") == 250
    assert mod._int(None) is None
    assert mod._int("n/a") is None


def test_validate_clean_tower_has_no_warnings(mod):
    td = _full_tower(mod)
    td.warnings.clear()
    mod._validate(td)
    assert td.warnings == []


def test_validate_flags_short_path_and_missing_base(mod):
    td = mod.TowerData(tower_id="x", canonical="X")
    td.upgrades = [{"path": 1, "tier": 1, "name": "a", "cost": 100, "xp": 1}]
    mod._validate(td)
    assert any("missing base cost" in w for w in td.warnings)
    assert any("path 1 has 1" in w for w in td.warnings)


def test_apply_costs_to_row_maps_paths_to_columns(mod):
    td = _full_tower(mod)
    row = dict.fromkeys(_HEADER, "")
    mod.apply_costs_to_row(row, td)
    assert row["base_cost"] == "375"
    assert row["top_1_cost"] == "101"  # path1 tier1
    assert row["mid_3_cost"] == "203"  # path2 tier3
    assert row["bot_5_cost"] == "305"  # path3 tier5


def test_stats_document_shape(mod):
    td = _full_tower(mod)
    doc = mod.stats_document(td)
    assert doc["tower_id"] == "bomb_shooter"
    assert doc["base_cost"] == 375
    assert doc["game_version"] == "54.0"
    assert len(doc["upgrades"]) == 15
    assert "CC BY-NC-SA" in doc["source"]


def test_hero_writable_requires_levels(mod):
    with_levels = mod.HeroData(hero_id="quincy", canonical="Quincy", base_cost=540)
    with_levels.levels = {"1": {"level": 1}}
    cost_only = mod.HeroData(hero_id="obyn", canonical="Obyn Greenfoot", base_cost=650)
    assert mod._hero_writable(with_levels) is True
    assert mod._hero_writable(cost_only) is False  # prose-only hero — no file


def test_hero_stats_document_shape(mod):
    hd = mod.HeroData(
        hero_id="quincy",
        canonical="Quincy",
        base_cost=540,
        cost_chimps=540,
        game_version="46.3",
    )
    hd.levels = {str(n): {"level": n} for n in range(1, 21)}
    doc = mod.hero_stats_document(hd)
    assert doc["hero_id"] == "quincy"
    assert doc["base_cost"] == 540
    assert len(doc["levels"]) == 20
    assert "CC BY-NC-SA" in doc["source"]


def test_update_csv_only_touches_matched_rows(mod, tmp_path):
    csv_path = tmp_path / "towers.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_HEADER)
        writer.writeheader()
        bomb = dict.fromkeys(_HEADER, "")
        bomb.update(
            {"id": "bomb_shooter", "canonical": "Bomb Shooter", "top_1_cost": "999"}
        )
        other = dict.fromkeys(_HEADER, "")
        other.update(
            {"id": "dart_monkey", "canonical": "Dart Monkey", "top_1_cost": "42"}
        )
        writer.writerows([bomb, other])

    mod.update_csv(csv_path, {"bomb_shooter": _full_tower(mod)})

    with csv_path.open(encoding="utf-8", newline="") as fh:
        rows = {r["id"]: r for r in csv.DictReader(fh)}
    assert rows["bomb_shooter"]["top_1_cost"] == "101"  # corrected
    assert rows["dart_monkey"]["top_1_cost"] == "42"  # untouched
