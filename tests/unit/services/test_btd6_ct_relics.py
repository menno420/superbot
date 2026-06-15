"""CT relic catalog loading + lookup (services.btd6_data_service)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_data_service as d  # noqa: E402

_FIXTURES = Path(__file__).parents[3] / "tests" / "fixtures" / "ninjakiwi"


def _fixture_relic_api_names() -> set[str]:
    """Every relic_name that appears on the captured CT tile set."""
    raw = json.loads((_FIXTURES / "btd6_ct_mpejg5d0_tiles.json").read_text("utf-8"))
    body = raw.get("body", raw)
    names: set[str] = set()
    for tile in body["tiles"]:
        ttype = tile.get("type", "")
        if isinstance(ttype, str) and ttype.startswith("Relic - "):
            names.add(ttype[len("Relic - ") :].strip())
    return names


def setup_function():
    d.reset_cache()


def test_catalog_loads_and_validates():
    relics = d.list_ct_relics()
    assert len(relics) >= 24
    # Every relic carries an effect and an api_name.
    for relic in relics:
        assert relic.effect
        assert relic.api_name


def test_get_by_id_and_api_name():
    assert d.get_ct_relic("camo_trap").canonical == "Camo Trap"
    sms = d.get_ct_relic_by_api_name("SuperMonkeyStorm")
    assert sms is not None
    assert sms.id == "super_monkey_storm"
    assert sms.abbrev == "SMS"


def test_resolve_relic_by_alias_abbrev_canonical():
    assert d.resolve_relic("sms").id == "super_monkey_storm"
    assert d.resolve_relic("Super Monkey Storm").id == "super_monkey_storm"
    assert d.resolve_relic("camo trap").id == "camo_trap"
    assert d.resolve_relic("CamoTrap").id == "camo_trap"  # api name
    assert d.resolve_relic("nope-not-a-relic") is None


def test_every_fixture_relic_is_in_catalog():
    """No tile relic should be orphaned from the catalog."""
    missing = {
        name
        for name in _fixture_relic_api_names()
        if d.get_ct_relic_by_api_name(name) is None
    }
    assert not missing, f"relics on tiles but absent from catalog: {sorted(missing)}"
