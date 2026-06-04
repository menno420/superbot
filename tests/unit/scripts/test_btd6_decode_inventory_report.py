"""Tests for ``scripts/btd6_decode_inventory_report.py`` — the SHA-pinned
decode inventory report generator.

Hermetic: the novel logic (the effect-model ``$type`` tail scan and the two
effect-work columns — *decodable-number?* / *has-curated-name?*) is exercised
on a tiny synthetic ``Towers/`` tree on ``tmp_path``. The full ``build_report``
integration needs the real committed stats + catalogs and is covered by the
deterministic real-dump run + the CI-mirror suite, not here. No vendored clone.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "btd6_decode_inventory_report.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("btd6_decode_inventory_report_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _t(cls: str) -> str:
    return f"Il2CppAssets.Scripts.Models.Towers.Behaviors.{cls}, Assembly-CSharp"


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def towers_dump(tmp_path: Path) -> Path:
    root = tmp_path / "dump"
    # A tower whose behaviors carry: a zone with an effect multiplier (decodable
    # + named), a zone with only aura geometry (geometry-only), a support with a
    # pierce number and a buffLocsName, and a name/flag-only buff.
    _write(
        root / "Towers" / "Druid" / "Druid-000.json",
        {
            "$type": _t("TowerModel"),
            "name": "Druid",
            "behaviors": [
                {
                    "$type": _t("BonusCashZoneModel"),
                    "name": "Bonus Cash",
                    "multiplier": 1.5,
                    "range": 40,
                },
                {
                    "$type": _t("ActivateRateSupportZoneModel"),
                    "buffLocsName": "Storm",
                    "range": 50,
                    "lifespan": 3.0,
                },
                {
                    "$type": _t("PierceSupportModel"),
                    "buffLocsName": "Sharpen",
                    "pierce": 4,
                },
                {
                    "$type": _t("VisibilitySupportModel"),
                    "buffLocsName": "Spotter",
                },
                # noise: not an effect model, must be ignored
                {"$type": _t("AttackModel"), "range": 35},
            ],
        },
    )
    return root


def test_decodable_distinguishes_effect_from_geometry(mod):
    assert mod._decodable({"multiplier"}).startswith("yes")
    assert mod._decodable({"pierce", "range"}).startswith("yes")  # effect wins over geometry
    assert mod._decodable({"range", "lifespan"}) == "geometry-only"
    assert mod._decodable({"someFlag"}) == "no (name/flag only)"
    assert mod._decodable(set()) == "no (name/flag only)"


def test_has_name_prefers_direct_then_falls_back(mod):
    assert mod._has_name({"buffLocsName"}).startswith("yes")
    assert mod._has_name({"name"}) == "yes (model name)"
    assert mod._has_name(set()) == "via owning upgrade"
    # a bare model name is weaker than a localized buff name but still curated
    assert "model name" in mod._has_name({"name"})


def test_scan_effect_tail_buckets_zones_and_buffs(mod, towers_dump):
    tail = mod._scan_effect_tail(towers_dump)
    zone_types = {row[0] for row in tail["zone"]}
    buff_types = {row[0] for row in tail["buff"]}
    assert zone_types == {"BonusCashZoneModel", "ActivateRateSupportZoneModel"}
    assert buff_types == {"PierceSupportModel", "VisibilitySupportModel"}
    # the AttackModel noise is in neither bucket
    assert "AttackModel" not in zone_types | buff_types


def test_scan_effect_tail_captures_numeric_and_name_signals(mod, towers_dump):
    tail = mod._scan_effect_tail(towers_dump)
    by_type = {row[0]: row for row in tail["zone"] + tail["buff"]}

    # BonusCash: effect multiplier present + a model name → fully decodable.
    _, count, nums, names = by_type["BonusCashZoneModel"]
    assert count == 1
    assert mod._decodable(nums).startswith("yes")
    assert mod._has_name(names).startswith("yes")

    # ActivateRateSupportZone: only aura geometry on the node itself.
    _, _, nums, names = by_type["ActivateRateSupportZoneModel"]
    assert mod._decodable(nums) == "geometry-only"

    # PierceSupport: decodable pierce + buffLocsName.
    _, _, nums, names = by_type["PierceSupportModel"]
    assert "pierce" in mod._decodable(nums)
    assert "buffLocsName" in mod._has_name(names)

    # VisibilitySupport: name only, no effect number → description fallback.
    _, _, nums, names = by_type["VisibilitySupportModel"]
    assert mod._decodable(nums) == "no (name/flag only)"
    assert mod._has_name(names).startswith("yes")


def test_md_table_shapes_header_and_rows(mod):
    out = mod._md_table(["A", "B"], [["1", "2"], ["3", "4"]])
    assert out[0] == "| A | B |"
    assert out[1] == "|---|---|"
    assert out[2] == "| 1 | 2 |"
    assert len(out) == 4


def test_dump_sha_unknown_outside_git(mod, tmp_path):
    # A non-git directory yields the documented sentinel, never a crash.
    assert mod._dump_sha(tmp_path) == "unknown"


def test_decode_class_registry_is_classification_only(mod):
    # Slice-2 scaffolding: the registry classifies but writes no numbers.
    c = mod._DECODE_CLASS
    assert c["PierceSupportModel"] == "SAFE_WRITE"
    assert c["RateSupportModel"] == "SAFE_WRITE"
    assert c["ProjectileSpeedSupportModel"] == "SCHEMA_FIRST"
    assert c["RangeSupportModel"] == "DEFER"  # ambiguous multiplier
    assert set(c.values()) <= {"SAFE_WRITE", "SCHEMA_FIRST", "DEFER", "DESCRIPTION_ONLY"}
