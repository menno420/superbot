"""Tests for ``scripts/btd6_patch_diff.py``.

Covers the pure parsing helpers and the file-aware ``assess`` bucketing
(CLEAN / LIKELY / STALE / NO_FILE / SCOPE) against crafted temp stat files,
so the tool's verdicts are pinned independent of the live data snapshot.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "btd6_patch_diff.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("btd6_patch_diff_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_to_number_units(mod):
    assert mod.to_number("600k") == 600000
    assert mod.to_number("$90,000") == 90000
    assert mod.to_number("8") == 8
    assert mod.to_number("1.5s") == 1.5
    assert mod.to_number("+4") == 4
    assert mod.to_number("44%") == 44
    assert mod.to_number("reworked") is None


def test_extract_transition_takes_last_pair(mod):
    assert mod.extract_transition("xx4 darts damage 8 > 6") == ("8", "6")
    # Two arrows (a boss HP line) — the real transition is the last pair.
    assert mod.extract_transition("Tail HP > 12.5% > 10%") == ("12.5%", "10%")
    assert mod.extract_transition("arrow form → uses unicode 5 → 9") == ("5", "9")
    assert mod.extract_transition("reworked, no numbers") is None


def test_parse_tier(mod):
    assert mod.parse_tier("x5x Permacharge 8 > 10") == "x5x"
    assert mod.parse_tier("(Paragon) Vinenado 6s > 18s") == "Paragon"
    assert mod.parse_tier("Lv20 ball 15 > 20") == "Lv20"
    assert mod.parse_tier("Main attack boss damage 300 > 100") is None


def test_tier_to_path(mod):
    assert mod.tier_to_path("xx5") == (3, 5)
    assert mod.tier_to_path("5xx") == (1, 5)
    assert mod.tier_to_path("x4x") == (2, 4)
    assert mod.tier_to_path("052") is None  # crosspath state, not one upgrade
    assert mod.tier_to_path(None) is None


def test_parse_notes_attaches_changes_to_subject(mod):
    index = {"bomb shooter": mod.Subject("Bomb Shooter", "tower", "bomb_shooter")}
    text = (
        "Bomb Shooter some prose about the change\n"
        "* Paragon upgrade price 600k > 650k\n"
        "* a reworked thing with no numbers\n"
    )
    changes = mod.parse_notes(text, index)
    assert len(changes) == 1
    assert changes[0].target_id == "bomb_shooter"
    assert (changes[0].old_raw, changes[0].new_raw) == ("600k", "650k")


def test_parse_notes_scopes_powers_section(mod):
    index = {"bomb shooter": mod.Subject("Bomb Shooter", "tower", "bomb_shooter")}
    text = "Powers\n* Hype Monkey Boost monkey money cost 400 > 300\n"
    changes = mod.parse_notes(text, index)
    assert len(changes) == 1
    assert changes[0].kind == "scope"


# ---------------------------------------------------------------------------
# assess() bucketing against crafted stat files
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, name: str, payload: dict) -> None:
    target = tmp_path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload), encoding="utf-8")


def test_assess_clean_cost_match(mod, tmp_path):
    _write(
        tmp_path,
        "bomb_shooter.json",
        {"game_version": "54.0", "paragon_cost": 600000, "upgrades": []},
    )
    change = mod.Change(
        subject="Bomb Shooter",
        kind="tower",
        target_id="bomb_shooter",
        tier=None,
        text="Paragon upgrade price 600k > 650k",
        old_raw="600k",
        new_raw="650k",
    )
    result = mod.assess(change, tmp_path)
    assert result.bucket == "CLEAN"
    assert result.field == "paragon_cost"


def test_assess_clean_cost_value_fallback(mod, tmp_path):
    # No "paragon" in the bullet and no tier code, but exactly one cost field
    # equals the stated old -> still resolves CLEAN.
    _write(
        tmp_path,
        "engineer_monkey.json",
        {"game_version": "52.2", "paragon_cost": 650000, "upgrades": []},
    )
    change = mod.Change(
        subject="Engineer Monkey",
        kind="tower",
        target_id="engineer_monkey",
        tier=None,
        text="Upgrade cost reduced: 650k > 600k",
        old_raw="650k",
        new_raw="600k",
    )
    result = mod.assess(change, tmp_path)
    assert result.bucket == "CLEAN"
    assert result.field == "paragon_cost"


def test_assess_stale_baseline(mod, tmp_path):
    _write(
        tmp_path,
        "wizard_monkey.json",
        {"game_version": "52.2", "upgrades": [], "node": {"dmg": 1000}},
    )
    change = mod.Change(
        subject="Wizard Monkey",
        kind="tower",
        target_id="wizard_monkey",
        tier=None,
        text="Flamethrower Boss bonus damage 1000 > 800",
        old_raw="1000",
        new_raw="800",
    )
    assert mod.assess(change, tmp_path).bucket == "STALE"


def test_assess_likely_when_old_value_present(mod, tmp_path):
    _write(
        tmp_path,
        "druid.json",
        {"game_version": "54.0", "upgrades": [], "t": {"storm": {"damage": 150}}},
    )
    change = mod.Change(
        subject="Druid",
        kind="tower",
        target_id="druid",
        tier="5xx",
        text="5xx storm damage 150 > 100",
        old_raw="150",
        new_raw="100",
    )
    assert mod.assess(change, tmp_path).bucket == "LIKELY"


def test_assess_review_when_old_absent_and_fresh(mod, tmp_path):
    _write(
        tmp_path,
        "druid.json",
        {"game_version": "54.0", "upgrades": [], "t": {"storm": {"damage": 999}}},
    )
    change = mod.Change(
        subject="Druid",
        kind="tower",
        target_id="druid",
        tier="5xx",
        text="5xx storm damage 150 > 100",
        old_raw="150",
        new_raw="100",
    )
    assert mod.assess(change, tmp_path).bucket == "REVIEW"


def test_assess_no_file_for_uncarried_hero(mod, tmp_path):
    change = mod.Change(
        subject="Pat Fusty",
        kind="hero",
        target_id="pat_fusty",
        tier="Lv1",
        text="Lv1 tower range 24 > 27",
        old_raw="24",
        new_raw="27",
    )
    assert mod.assess(change, tmp_path).bucket == "NO_FILE"


def test_assess_scope_is_out_of_scope(mod, tmp_path):
    change = mod.Change(
        subject="Powers",
        kind="scope",
        target_id=None,
        tier=None,
        text="Hype Monkey Boost monkey money cost 400 > 300",
        old_raw="400",
        new_raw="300",
    )
    assert mod.assess(change, tmp_path).bucket == "SCOPE"


def test_build_index_resolves_real_catalog(mod):
    index = mod.build_index()
    assert index["dart monkey"].target_id == "dart_monkey"
    assert index["engineer"].kind == "tower"
