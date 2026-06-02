"""Tests for ``scripts/import_btd6_data_from_csv.py``.

Covers happy path, every validation failure mode, alias-collision
detection, and that the produced JSON round-trips through the same
loader the runtime uses (``services.btd6_data_service``).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "import_btd6_data_from_csv.py"


@pytest.fixture(scope="module")
def importer():
    """Load the import script as a module under a unique name."""
    spec = importlib.util.spec_from_file_location(
        "import_btd6_data_from_csv_under_test",
        _SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_TOWER_HEADER = (
    "id,canonical,category,aliases,base_cost,description,"
    "top_1,top_2,top_3,top_4,top_5,"
    "mid_1,mid_2,mid_3,mid_4,mid_5,"
    "bot_1,bot_2,bot_3,bot_4,bot_5,"
    "wiki_url\n"
)
_HERO_HEADER = (
    "id,canonical,aliases,base_cost,description,"
    "ability_3_name,ability_3_summary,"
    "ability_10_name,ability_10_summary,wiki_url\n"
)


def _valid_tower_row(
    *,
    tower_id: str = "dart_monkey",
    canonical: str = "Dart Monkey",
    category: str = "primary",
    aliases: str = "dart,darts",
    base_cost: str = "200",
    description: str = "Throws a dart.",
    wiki_url: str = "https://example.invalid/Dart_Monkey",
) -> str:
    tiers = ",".join([f"u{i}" for i in range(1, 16)])
    return (
        f'{tower_id},{canonical},{category},"{aliases}",'
        f"{base_cost},{description},{tiers},{wiki_url}\n"
    )


def _valid_hero_row(
    *,
    hero_id: str = "quincy",
    canonical: str = "Quincy",
    aliases: str = "q",
    base_cost: str = "540",
    description: str = "Starter hero.",
    ability_3_name: str = "Rapid Shot",
    ability_3_summary: str = "Briefly fast.",
    ability_10_name: str = "Storm of Arrows",
    ability_10_summary: str = "Massive AoE.",
    wiki_url: str = "https://example.invalid/Quincy",
) -> str:
    return (
        f'{hero_id},{canonical},"{aliases}",'
        f"{base_cost},{description},"
        f"{ability_3_name},{ability_3_summary},"
        f"{ability_10_name},{ability_10_summary},{wiki_url}\n"
    )


def _write_csvs(
    tmp_path: Path,
    *,
    tower_rows: list[str],
    hero_rows: list[str],
) -> tuple[Path, Path]:
    towers_csv = tmp_path / "towers.csv"
    heroes_csv = tmp_path / "heroes.csv"
    towers_csv.write_text(_TOWER_HEADER + "".join(tower_rows), encoding="utf-8")
    heroes_csv.write_text(_HERO_HEADER + "".join(hero_rows), encoding="utf-8")
    return towers_csv, heroes_csv


def _run(
    importer,
    tmp_path: Path,
    *,
    tower_rows: list[str],
    hero_rows: list[str],
    check_only: bool = False,
    game_version: str | None = "test-1.0",
) -> tuple[int, Path, Path]:
    towers_csv, heroes_csv = _write_csvs(
        tmp_path,
        tower_rows=tower_rows,
        hero_rows=hero_rows,
    )
    towers_json = tmp_path / "towers.json"
    heroes_json = tmp_path / "heroes.json"
    rc = importer.convert(
        towers_csv=towers_csv,
        heroes_csv=heroes_csv,
        towers_json=towers_json,
        heroes_json=heroes_json,
        game_version=game_version,
        check_only=check_only,
    )
    return rc, towers_json, heroes_json


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_writes_valid_json(importer, tmp_path, capsys):
    rc, towers_json, heroes_json = _run(
        importer,
        tmp_path,
        tower_rows=[_valid_tower_row()],
        hero_rows=[_valid_hero_row()],
    )
    assert rc == 0
    assert towers_json.exists() and heroes_json.exists()

    towers = json.loads(towers_json.read_text())
    heroes = json.loads(heroes_json.read_text())
    assert towers["data_version"] == "1.0"
    assert towers["game_version"] == "test-1.0"
    assert len(towers["towers"]) == 1
    tower = towers["towers"][0]
    assert tower["id"] == "dart_monkey"
    assert tower["category"] == "primary"
    assert tower["base_cost"] == 200
    assert tower["upgrade_paths"]["top"] == ["u1", "u2", "u3", "u4", "u5"]
    assert tower["upgrade_paths"]["mid"] == ["u6", "u7", "u8", "u9", "u10"]
    assert tower["upgrade_paths"]["bot"] == ["u11", "u12", "u13", "u14", "u15"]
    assert tower["aliases"] == ["dart", "darts"]

    assert len(heroes["heroes"]) == 1
    hero = heroes["heroes"][0]
    assert hero["id"] == "quincy"
    assert hero["base_cost"] == 540
    assert hero["abilities"] == [
        {"level": 3, "name": "Rapid Shot", "summary": "Briefly fast."},
        {"level": 10, "name": "Storm of Arrows", "summary": "Massive AoE."},
    ]


def test_happy_path_round_trips_through_runtime_loader(importer, tmp_path, monkeypatch):
    """JSON the script produces must load cleanly via btd6_data_service."""
    rc, towers_json, heroes_json = _run(
        importer,
        tmp_path,
        tower_rows=[_valid_tower_row()],
        hero_rows=[_valid_hero_row()],
    )
    assert rc == 0

    # Stage the JSON into a fresh data root, plus the other fixtures we don't
    # touch (maps / modes / rounds) from the repo.
    fake_root = tmp_path / "data_root"
    fake_root.mkdir()
    real_data = _REPO_ROOT / "disbot" / "data" / "btd6"
    (fake_root / "towers.json").write_text(towers_json.read_text())
    (fake_root / "heroes.json").write_text(heroes_json.read_text())
    for filename in ("maps.json", "modes.json", "rounds.json"):
        (fake_root / filename).write_text((real_data / filename).read_text())

    from services import btd6_data_service
    from services.btd6_data_provider import FileRawProvider

    # Reads funnel through the swappable provider; point it at the staged root.
    monkeypatch.setattr(btd6_data_service, "_PROVIDER", FileRawProvider(fake_root))
    btd6_data_service.reset_cache()
    try:
        dataset = btd6_data_service.get_dataset()
        assert len(dataset.towers) == 1
        assert dataset.towers[0].id == "dart_monkey"
        assert dataset.towers[0].category == "primary"
        assert dataset.heroes[0].id == "quincy"
    finally:
        btd6_data_service.reset_cache()


def test_check_mode_validates_without_writing(importer, tmp_path):
    rc, towers_json, heroes_json = _run(
        importer,
        tmp_path,
        tower_rows=[_valid_tower_row()],
        hero_rows=[_valid_hero_row()],
        check_only=True,
    )
    assert rc == 0
    assert not towers_json.exists()
    assert not heroes_json.exists()


# ---------------------------------------------------------------------------
# Per-field validation failures
# ---------------------------------------------------------------------------


def test_empty_required_field_fails(importer, tmp_path, capsys):
    rc, towers_json, _ = _run(
        importer,
        tmp_path,
        tower_rows=[_valid_tower_row(description="")],
        hero_rows=[_valid_hero_row()],
    )
    assert rc == 1
    assert not towers_json.exists()
    output = capsys.readouterr().out
    assert "description" in output


def test_invalid_category_fails(importer, tmp_path, capsys):
    rc, _, _ = _run(
        importer,
        tmp_path,
        tower_rows=[_valid_tower_row(category="primay")],
        hero_rows=[_valid_hero_row()],
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "category" in out
    assert "primay" in out


def test_zero_base_cost_fails(importer, tmp_path, capsys):
    rc, _, _ = _run(
        importer,
        tmp_path,
        tower_rows=[_valid_tower_row(base_cost="0")],
        hero_rows=[_valid_hero_row()],
    )
    assert rc == 1
    assert "base_cost" in capsys.readouterr().out


def test_non_integer_base_cost_fails(importer, tmp_path, capsys):
    rc, _, _ = _run(
        importer,
        tmp_path,
        tower_rows=[_valid_tower_row(base_cost="not-a-number")],
        hero_rows=[_valid_hero_row()],
    )
    assert rc == 1
    assert "base_cost" in capsys.readouterr().out


def test_empty_upgrade_tier_fails(importer, tmp_path, capsys):
    bad_row = (
        'dart_monkey,Dart Monkey,primary,"d",200,Desc.,'
        ",t2,t3,t4,t5,m1,m2,m3,m4,m5,b1,b2,b3,b4,b5,"
        "https://example.invalid/d\n"
    )
    rc, _, _ = _run(
        importer,
        tmp_path,
        tower_rows=[bad_row],
        hero_rows=[_valid_hero_row()],
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "top_1" in out


# ---------------------------------------------------------------------------
# Cross-row validation
# ---------------------------------------------------------------------------


def test_duplicate_tower_id_fails(importer, tmp_path, capsys):
    rc, _, _ = _run(
        importer,
        tmp_path,
        tower_rows=[
            _valid_tower_row(tower_id="dart_monkey", canonical="Dart Monkey"),
            _valid_tower_row(tower_id="dart_monkey", canonical="Dart Monkey 2"),
        ],
        hero_rows=[_valid_hero_row()],
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "duplicate" in out.lower()
    assert "dart_monkey" in out


def test_tower_hero_alias_collision_fails(importer, tmp_path, capsys):
    rc, _, _ = _run(
        importer,
        tmp_path,
        tower_rows=[_valid_tower_row(aliases="shared")],
        hero_rows=[_valid_hero_row(aliases="shared")],
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "alias collision" in out.lower()
    assert "shared" in out


def test_aliases_split_and_dedup(importer, tmp_path):
    rc, towers_json, _ = _run(
        importer,
        tmp_path,
        tower_rows=[_valid_tower_row(aliases="A, b , B,  c")],
        hero_rows=[_valid_hero_row()],
    )
    assert rc == 0
    aliases = json.loads(towers_json.read_text())["towers"][0]["aliases"]
    # Dedup is case-insensitive, preserves first-seen casing.
    assert aliases == ["A", "b", "c"]


# ---------------------------------------------------------------------------
# Header / file errors
# ---------------------------------------------------------------------------


def test_missing_column_fails(importer, tmp_path, capsys):
    # Drop the `category` column from header.
    towers_csv = tmp_path / "towers.csv"
    heroes_csv = tmp_path / "heroes.csv"
    towers_csv.write_text("id,canonical\n", encoding="utf-8")
    heroes_csv.write_text(_HERO_HEADER + _valid_hero_row(), encoding="utf-8")
    rc = importer.convert(
        towers_csv=towers_csv,
        heroes_csv=heroes_csv,
        towers_json=tmp_path / "towers.json",
        heroes_json=tmp_path / "heroes.json",
        game_version="x",
        check_only=False,
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "missing columns" in out


def test_missing_file_fails(importer, tmp_path, capsys):
    rc = importer.convert(
        towers_csv=tmp_path / "no-such.csv",
        heroes_csv=tmp_path / "no-such-2.csv",
        towers_json=tmp_path / "towers.json",
        heroes_json=tmp_path / "heroes.json",
        game_version="x",
        check_only=False,
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "not found" in out


# ---------------------------------------------------------------------------
# Scaffold integrity — the prefilled CSVs must parse without crashing
# ---------------------------------------------------------------------------


def test_scaffold_csvs_are_well_formed(importer):
    """The committed scaffold CSVs should validate cleanly at the header
    level even though content cells are blank — every row should still
    parse and emit per-field errors rather than crashing.
    """
    towers_csv = _REPO_ROOT / "data" / "btd6" / "towers.csv"
    heroes_csv = _REPO_ROOT / "data" / "btd6" / "heroes.csv"
    assert towers_csv.exists()
    assert heroes_csv.exists()
    tower_rows, errors = importer._read_csv(towers_csv, importer._TOWER_COLUMNS)
    assert errors == [], f"unexpected header errors: {errors}"
    assert len(tower_rows) >= 20, "scaffold should list the full roster"
    hero_rows, errors = importer._read_csv(heroes_csv, importer._HERO_COLUMNS)
    assert errors == []
    assert len(hero_rows) >= 10


def test_scaffold_roster_matches_api_key_mappings(importer):
    """Every tower / hero in the CSV must already have an API-key mapping —
    otherwise the live-query coverage test will fail once the import runs.
    """
    from services import btd6_live_query_service as live

    towers_csv = _REPO_ROOT / "data" / "btd6" / "towers.csv"
    heroes_csv = _REPO_ROOT / "data" / "btd6" / "heroes.csv"
    tower_rows, _ = importer._read_csv(towers_csv, importer._TOWER_COLUMNS)
    hero_rows, _ = importer._read_csv(heroes_csv, importer._HERO_COLUMNS)

    missing_towers = [
        row["id"] for row in tower_rows if row["id"] not in live._TOWER_ID_TO_API_KEY
    ]
    missing_heroes = [
        row["id"] for row in hero_rows if row["id"] not in live._HERO_ID_TO_API_KEY
    ]
    assert not missing_towers, missing_towers
    assert not missing_heroes, missing_heroes
