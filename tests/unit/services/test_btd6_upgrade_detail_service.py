"""Structured upgrade-detail read model + grounding renderer.

Pins the deep, per-attack/minion/buff extraction that the normal-stat view
can't express — in particular the reported *"Prince of Darkness minion
pierce?"* (1, from the Reanimate attack, not the main projectile) — and the
resolve -> detail -> render grounding seam end to end.
"""

from __future__ import annotations

import pytest

from services import btd6_stats_service
from services import btd6_upgrade_detail_service as det
from services import btd6_upgrade_service as up


@pytest.fixture(autouse=True)
def _fresh():
    up.reset_cache()
    btd6_stats_service.reset_cache()
    yield
    up.reset_cache()
    btd6_stats_service.reset_cache()


def _attack(detail, name):
    return next((a for a in detail.attacks if a.name == name), None)


def test_prince_of_darkness_detail():
    d = det.get_upgrade_detail("wizard_monkey:005")
    assert d is not None
    assert d.identity.canonical == "Prince of Darkness"
    assert d.has_combat_stats
    # The headline normal view keys off the highest-DAMAGE projectile, which for
    # PoD is the reanimated BFB (100 dmg / 50 pierce) — a known quirk of that
    # distilled view, and exactly why the per-attack detail below matters.
    assert d.normal is not None
    assert d.normal.cooldown == 0.275
    assert (d.normal.damage, d.normal.pierce) == (100, 50)
    # Every named attack stays addressable, including MOAB-reanimation.
    names = {a.name for a in d.attacks}
    assert {"Attack", "Reanimate", "MOAB"} <= names
    # The actual main attack (1 dmg, 8 pierce) is not lost to the headline.
    main = _attack(d, "Attack")
    assert main.projectiles[0].damage == 1
    assert main.projectiles[0].pierce == 8


def test_prince_of_darkness_minion_pierce_is_one():
    # The marquee failure: the answer lives on Reanimate, not the main attack.
    d = det.get_upgrade_detail("wizard_monkey:005")
    reanimate = _attack(d, "Reanimate")
    assert reanimate is not None
    assert reanimate.projectiles[0].pierce == 1
    assert reanimate.projectiles[0].damage == 2


def test_prince_of_darkness_buff_and_moab_projectiles():
    d = det.get_upgrade_detail("wizard_monkey:005")
    assert any("Undead Bloon buff" in b for b in d.buffs)
    assert any("+3 damage" in b and "x1.5 lifespan" in b for b in d.buffs)
    moab = _attack(d, "MOAB")
    proj = {p.name: (p.damage, p.pierce) for p in moab.projectiles}
    assert proj["MOAB"] == (40, 20)
    assert proj["BFB"] == (100, 50)


def test_subtower_minion_is_exposed():
    # Alchemist 0-5-0 (Total Transformation) spawns Transformed Monkey.
    d = det.get_upgrade_detail("alchemist:050")
    assert d is not None
    assert any(s.name == "Transformed Monkey" for s in d.subtowers)
    assert "subtowers" in d.coverage


def test_ability_and_zone_sections():
    sup = det.get_upgrade_detail("super_monkey:050")  # The Anti-Bloon
    assert sup is not None and sup.abilities
    assert sup.abilities[0].cooldown == 30

    druid = det.get_upgrade_detail("druid:050")  # Spirit of the Forest
    assert druid is not None and druid.zones
    assert any("Thorn zone" in z for z in druid.zones)


def test_economy_upgrade_has_identity_but_no_combat():
    # Monkey-Nomics (banana farm 0-5-0): real upgrade, no combat tiers.
    d = det.get_upgrade_detail("banana_farm:050")
    assert d is not None
    assert d.identity.canonical == "Monkey-Nomics"
    assert not d.has_combat_stats
    assert d.attacks == ()


def test_unknown_id_returns_none():
    assert det.get_upgrade_detail("does_not:999") is None


def test_render_grounding_surfaces_minion_pierce():
    d = det.get_upgrade_detail("wizard_monkey:005")
    lines = det.render_upgrade_grounding(d)
    blob = "\n".join(lines)
    assert all(line.startswith("[btd6_upgrade]") for line in lines)
    # Identity line carries tower / crosspath / cost.
    assert "Prince of Darkness = Wizard Monkey 0-0-5" in blob
    assert "$26,500" in blob
    # The Reanimate line makes "minion pierce" answerable.
    reanimate_line = next(line for line in lines if "Reanimate" in line)
    assert "1 pierce" in reanimate_line
    assert "Undead Bloon buff" in blob


def test_grounding_for_query_end_to_end():
    # Natural-language query -> resolve -> detail -> grounding, no tower named.
    lines = det.grounding_for_query("Prince of Darkness minion pierce?")
    blob = "\n".join(lines)
    assert "[btd6_upgrade] Prince of Darkness" in blob
    assert "1 pierce" in blob

    pmfc = det.grounding_for_query("PMFC stats")
    assert any("Plasma Monkey Fan Club" in line for line in pmfc)

    pod = "\n".join(det.grounding_for_query("POD cooldown"))
    assert "0.275s cooldown" in pod


def test_grounding_for_query_ambiguous_and_miss():
    ambiguous = det.grounding_for_query("wizard lord phoenix vs prince of darkness")
    assert len(ambiguous) == 1
    assert "Ambiguous upgrade reference" in ambiguous[0]
    assert "Wizard Lord Phoenix" in ambiguous[0]
    assert "Prince of Darkness" in ambiguous[0]

    assert det.grounding_for_query("what is the best tower") == []
    assert det.grounding_for_query("") == []
