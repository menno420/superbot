"""Tests for ``scripts/btd6_gamedata_inventory.py`` — the dump discovery tool.

Hermetic: a tiny synthetic dump on ``tmp_path`` mirroring the real layout
(domains of ``$type``-tagged model files + a ``textTable.json``). No vendored
clone.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "btd6_gamedata_inventory.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("btd6_gamedata_inventory_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _t(cls: str) -> str:
    return f"Il2CppAssets.Scripts.Models.{cls}, Assembly-CSharp"


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def dump(tmp_path: Path) -> Path:
    root = tmp_path / "dump"
    # two bloons, each a BloonModel with some scalar stats + a noisy SpriteReference
    for name, hp in (("Red", 1), ("Bloonarius1", 20000)):
        _write(
            root / "Bloons" / f"{name}.json",
            {
                "$type": _t("Bloons.BloonModel"),
                "id": name,
                "maxHealth": hp,
                "speed": 1.25,
                "icon": {"$type": _t("SpriteReference"), "guidRef": "abc"},
            },
        )
    # an upgrade carrying a LocsKey into textTable
    _write(
        root / "Upgrades" / "Sharp Shots.json",
        {
            "$type": _t("Upgrades.UpgradeModel"),
            "name": "Sharp Shots",
            "cost": 140,
            "LocsKey": "Sharp Shots",
        },
    )
    _write(
        root / "textTable.json",
        {
            "Sharp Shots": "Sharp Shots",
            "Sharp Shots Description": "Darts pop +1 layer.",
        },
    )
    (root / ".git").mkdir()  # must be ignored as a domain
    return root


def test_short_type_extraction(mod):
    assert mod._short_type({"$type": _t("Bloons.BloonModel")}) == "BloonModel"
    assert mod._short_type({"no": "type"}) == ""
    assert mod._short_type("not a dict") == ""


def test_walk_types_counts_nested(mod):
    counter: mod.Counter = mod.Counter()
    node = {
        "$type": _t("Towers.TowerModel"),
        "kids": [
            {"$type": _t("Behaviors.AttackModel")},
            {"$type": _t("X.AttackModel")},
        ],
    }
    mod._walk_types(node, counter)
    assert counter["TowerModel"] == 1
    assert counter["AttackModel"] == 2


def test_list_domains_skips_dotfiles(mod, dump):
    domains = mod.list_domains(dump)
    assert domains == ["Bloons", "Upgrades"]
    assert ".git" not in domains


def test_domain_summary_counts_files_and_types(mod, dump):
    files, counter = mod.domain_summary(dump, "Bloons")
    assert files == 2
    assert counter["BloonModel"] == 2
    assert counter["SpriteReference"] == 2


def test_field_catalog_collects_scalars(mod, dump):
    cat = mod.field_catalog(dump, "Bloons", "BloonModel")
    assert cat["maxHealth"] == 2
    assert cat["id"] == 2
    # nested sprite ref's fields are not attributed to BloonModel
    assert "guidRef" not in cat


def test_render_domain_targets_root_model_not_noise(mod, dump):
    # SpriteReference also appears once per file; the root BloonModel must win.
    out = mod.render_domain(dump, "Bloons")
    assert "scalar fields on BloonModel:" in out
    assert "maxHealth" in out


def test_text_link_report(mod, dump):
    lines = "\n".join(mod.text_link_report(dump))
    assert "textTable: 2 keys" in lines
    # the one upgrade resolves both a name and a description
    assert "Upgrades: 1/1 have a name string, 1/1 have a '<name> Description'" in lines


def test_render_overview_lists_domains_and_loose_files(mod, dump):
    out = mod.render_overview(dump)
    assert "Bloons" in out and "Upgrades" in out
    assert "textTable.json" in out


def test_full_map_renders_domains_fields_and_fetch_status(mod, dump):
    md = mod.render_full_map(dump)
    # provenance header + the regenerable warning
    assert "auto-generated" in md
    assert "## Domains" in md and "## Per-domain detail" in md
    # every domain table row + a fetch-status glyph column
    assert "`Bloons/`" in md and "`Upgrades/`" in md
    assert "Fetch" in md  # the status column header
    # per-domain detail surfaces the root model's scalar fields
    assert "`BloonModel`" in md and "`maxHealth`" in md
    # loose-file structure is enumerated
    assert "## Loose-file structure" in md and "textTable.json" in md


def test_full_map_primary_override_picks_named_root(mod, dump, monkeypatch):
    # When the heuristic would misfire, an override names the real root model.
    monkeypatch.setitem(mod._PRIMARY_OVERRIDE, "Bloons", "BloonModel")
    files, counter = mod.domain_summary(dump, "Bloons")
    assert mod._primary_model("Bloons", counter, files) == "BloonModel"


def test_loose_structure_reports_keys(mod, dump):
    lines = mod._loose_structure(dump, "textTable.json")
    assert "2 top-level keys" in lines[0]
    assert mod._loose_structure(dump, "nope.json") == ["(missing)"]
