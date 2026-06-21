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
    # The headline no longer reports the reanimated BFB (100/50): _main_projectile
    # skips MOAB-class reanimated minions, so the highest *own-attack* projectile
    # wins — here the Reanimate hit (2 dmg / 1 pierce), not the blimp's.
    assert d.normal is not None
    assert d.normal.cooldown == 0.275
    assert (d.normal.damage, d.normal.pierce) == (2, 1)
    # Every named attack stays addressable, including MOAB-reanimation (game
    # names since the v55.1 cutover: the wiki's "Reanimate"/"MOAB" attacks are
    # the game's "Attack Necromancer", whose projectiles carry the minions).
    names = {a.name for a in d.attacks}
    assert {"Attack", "Attack Necromancer", "Attack Shimmer"} <= names
    # The reanimated MOAB/BFB minions are still readable in the detail, just no
    # longer masquerading as the tower's headline damage.
    necro = _attack(d, "Attack Necromancer")
    assert {p.name: p.damage for p in necro.projectiles} == {
        "Projectile": 2,
        "ProjectileMoab": 40,
        "ProjectileBfb": 100,
    }


def test_prince_of_darkness_minion_pierce_is_one():
    # The marquee failure: the answer lives on the Necromancer attack (the
    # wiki-era "Reanimate"), not the main attack.
    d = det.get_upgrade_detail("wizard_monkey:005")
    reanimate = _attack(d, "Attack Necromancer")
    assert reanimate is not None
    assert reanimate.projectiles[0].pierce == 1
    assert reanimate.projectiles[0].damage == 2


def test_prince_of_darkness_buff_and_moab_projectiles():
    d = det.get_upgrade_detail("wizard_monkey:005")
    assert any("Undead Bloon buff" in b for b in d.buffs)
    assert any("+3 damage" in b and "x1.5 lifespan" in b for b in d.buffs)
    necro = _attack(d, "Attack Necromancer")
    proj = {p.name: (p.damage, p.pierce) for p in necro.projectiles}
    assert proj["ProjectileMoab"] == (40, 20)
    assert proj["ProjectileBfb"] == (100, 50)


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


def test_economy_upgrade_has_attacks_suppressed_but_ability():
    # Monkey-Nomics (banana farm 0-5-0): since the Q-0067 cutover the Farm has
    # full game-native tiers — the nominal banana "attack" is suppressed, but
    # the ability is real data.
    d = det.get_upgrade_detail("banana_farm:050")
    assert d is not None
    assert d.identity.canonical == "Monkey-Nomics"
    assert d.attacks == ()
    assert d.abilities and d.abilities[0].name == "Monkey-Nomics"
    assert d.abilities[0].cooldown == 60


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
    # The Reanimate *attack* line makes "minion pierce" answerable. (Match the
    # attack line specifically — the textTable description line also says
    # "Reanimate", so key off the per-attack "pierce" stat, not the word alone.)
    reanimate_line = next(
        line for line in lines if "Attack Necromancer" in line and "pierce" in line
    )
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


# --- game-authored textTable descriptions (step 4) --------------------------


def test_upgrade_detail_carries_game_description():
    # The committed stats now carry the upgrade's textTable prose, joined by
    # (path, tier); get_upgrade_detail surfaces it.
    d = det.get_upgrade_detail("wizard_monkey:005")
    assert d is not None
    assert "Reanimate" in d.description and "Necromancer" in d.description


def test_description_grounds_with_in_game_source_label():
    lines = det.grounding_for_query("Spike-o-pult")
    desc = [ln for ln in lines if "in-game description" in ln]
    assert len(desc) == 1
    assert "Spike-o-pult" in desc[0]
    assert "spiked ball" in desc[0].lower()
    assert "(source: BTD6 in-game description)" in desc[0]
    # The description grounds as its own line, distinct from the identity line.
    assert lines[0].startswith("[btd6_upgrade] Spike-o-pult =")


def test_description_line_present_even_with_combat_stats():
    # Order contract: the prose line lands right after identity, before stats.
    lines = det.grounding_for_query("Prince of Darkness")
    assert "in-game description" in lines[1]


def test_under_emitted_card_description_filled_via_texttable_fallback():
    # The 2 cards the mapper under-emits (Ace "Operation: Dart Storm", Wizard
    # "Necromancer: Unpopped Army") now get their description from the textTable
    # "<curated name> Description" fallback — 375/375 cards carry prose.
    lines = det.grounding_for_query("Operation Dart Storm")
    desc = [ln for ln in lines if "in-game description" in ln]
    assert len(desc) == 1
    assert "16 darts" in desc[0]
    assert any("main attack" in ln for ln in lines)


# --- damage modifiers in grounding (bonus vs bloon class) -------------------


def test_projectile_carries_damage_modifiers():
    # Juggernaut (4-0-0) gets +3 vs Ceramic, +2 vs Fortified — the curated
    # damageModifierFor* numbers must reach the read model, not just MOAB bonus.
    d = det.get_upgrade_detail("dart_monkey:400")  # Juggernaut = top path tier 4
    assert d is not None
    main = _attack(d, "Attack")
    assert main is not None
    mods = dict(main.projectiles[0].modifiers)
    assert mods.get("Ceramic") == 3
    assert mods.get("Fortified") == 2


def test_grounding_surfaces_bonus_vs_bloon_class():
    # The retrieval-gap regression: the bot could recite the prose ("crushes
    # Ceramic/Fortified") but not the numbers. Now the numbers ground.
    blob = "\n".join(det.grounding_for_query("Juggernaut"))
    assert "+3 damage vs Ceramic" in blob
    assert "+2 damage vs Fortified" in blob


def test_grounding_surfaces_lead_bonus_on_ultra_juggernaut():
    # "Ultra-Juggernaut" resolves ambiguous by name (Juggernaut substring), so
    # render the id (0-0-5 top path = "500") directly.
    blob = "\n".join(
        det.render_upgrade_grounding(det.get_upgrade_detail("dart_monkey:500")),
    )
    assert "+20 damage vs Lead" in blob
    assert "+8 damage vs Ceramic" in blob


def test_modifiers_empty_when_none_present():
    # The base dart (tier-1 top) has no damage modifiers — no phantom bonus lines.
    d = det.get_upgrade_detail("dart_monkey:100")
    assert d is not None
    main = _attack(d, "Attack")
    assert main is not None
    assert main.projectiles[0].modifiers == ()


# --- buff percentage rendering (fraction -> percent) ------------------------


def test_buff_percentage_fields_render_as_percent_not_fraction():
    # Regression: committed percentage buffs store fractions (0.15 = 15%, faithful
    # to the dump's *PercentIncrease), but the render read them as a literal "%",
    # so Poplust showed "+0.15% pierce" (wrong) instead of "+15%".
    text = det._buff_text(
        {"name": "Poplust buff", "ratePercentage": 0.15, "piercePercentage": 0.15},
    )
    assert "+15% pierce" in text
    assert "15% attack speed" in text
    assert "0.15%" not in text


def test_buff_additive_and_multiplier_fields_unscaled():
    # Only *Percentage fields scale; additive/multiplier stay verbatim.
    text = det._buff_text(
        {"name": "Undead Bloon buff", "damageAdditive": 3, "lifespanMultiplier": 1.5},
    )
    assert text == "Undead Bloon buff: +3 damage, x1.5 lifespan"


def test_buff_range_percentage_renders_whole_percent():
    assert "+10% range" in det._buff_text({"name": "X", "rangePercentage": 0.1})


def test_buff_cash_per_round_fields_render_with_dollar():
    # Trade Empire's income was decoded into committed data but DROPPED by the
    # renderer (no _BUFF_FIELDS entry), so "what does Trade Empire do" surfaced
    # only the +1 damage and lost the headline cash effect (extracted, but not
    # answerable). Both per-round fields now render.
    text = det._buff_text(
        {
            "name": "Trade Empire buff",
            "cashPerRoundPerMechantship": 10,
            "cashPerRoundPerFavouredTrades": 20,
        },
    )
    assert "+$10/round per Merchantman" in text
    assert "+$20/round per Favored Trades" in text


def test_buff_sellback_multiplier_renders_whole_percent():
    # cashbackZoneMultiplier scales x100 like the other percent-as-fraction fields.
    assert "+4% sellback value" in det._buff_text(
        {"name": "Sellback rate buff", "cashbackZoneMultiplier": 0.04},
    )


def test_buff_projectile_radius_fields_render():
    # Striker Jones L7's committed radiusMultiplier rendered as a bare "buff"
    # before these fields landed (extracted-but-not-answerable).
    text = det._buff_text(
        {"name": "Projectile radius buff", "radiusMultiplier": 1.1},
    )
    assert "x1.1 projectile radius" in text
    assert "+15% projectile radius" in det._buff_text(
        {"name": "X", "radiusPercentage": 0.15},
    )
    assert "6 projectile radius" in det._buff_text(
        {"name": "X", "projectileRadius": 6},
    )


def test_buff_projectile_speed_percentage_renders_whole_percent():
    # Q-0069: fraction in data, percent on screen.
    assert "+25% projectile speed" in det._buff_text(
        {"name": "Primary Training", "projectileSpeedPercentage": 0.25},
    )


def test_buff_bank_income_percentage_renders_whole_percent():
    # Benjamin's Bank Hack: fraction in data (0.05 / 0.12), percent on screen.
    assert "+5% income" in det._buff_text(
        {"name": "Bank Hack", "incomePercentage": 0.05},
    )
    assert "+12% income" in det._buff_text(
        {"name": "Bank Hack", "incomePercentage": 0.12},
    )


def test_trade_empire_detail_surfaces_income_end_to_end():
    # The real committed Buccaneer 0-0-5 data: the income buff now reaches the
    # rendered detail (and thus AI grounding), not just the damage bonus.
    d = det.get_upgrade_detail("monkey_buccaneer:005")
    blob = " | ".join(d.buffs)
    assert "+$10/round per Merchantman" in blob
    assert "+$20/round per Favored Trades" in blob
    assert "+4% sellback value" in blob


def test_buff_hero_xp_multiplier_renders():
    # Sub Energizer's global buff: abilityCooldownMultiplier already rendered, but
    # heroXpMultiplier was dropped (the +50% hero XP was invisible).
    text = det._buff_text(
        {
            "name": "Ability cooldown buff (global)",
            "abilityCooldownMultiplier": 1.2,
            "heroXpMultiplier": 1.5,
        },
    )
    assert "x1.5 hero XP" in text


# --- buff stack cap (maxStacks / maxStackSize) ------------------------------


def test_buff_stack_cap_renders_when_positive():
    # Trade Empire stacks per Merchantman in range, up to 20 — a real cap a
    # player asks about. It sat in committed data (maxStacks) but never
    # surfaced; only a code comment hardcoded "up to 20".
    text = det._buff_text(
        {
            "name": "Trade Empire buff",
            "cashPerRoundPerMechantship": 10,
            "maxStacks": 20,
        },
    )
    assert "+$10/round per Merchantman" in text
    assert "(stacks up to 20)" in text


def test_buff_stack_cap_zero_means_no_clause():
    # maxStacks == 0 is "applies once, does not stack" (a global aura), NOT an
    # unlimited cap — so we render no stack clause for it.
    text = det._buff_text(
        {"name": "Flagship buff", "rateMultiplier": 0.8, "maxStacks": 0},
    )
    assert "stacks up to" not in text
    assert text == "Flagship buff: x0.8 attack cooldown"


def test_buff_stack_cap_reads_max_stack_size_alias():
    # Sniper encodes the same concept under the other field name (maxStackSize);
    # a positive value still surfaces a cap, 0 still renders nothing.
    assert "(stacks up to 4)" in det._buff_text(
        {"name": "X", "rateMultiplier": 0.75, "maxStackSize": 4},
    )
    assert "stacks up to" not in det._buff_text(
        {"name": "Attack speed buff", "rateMultiplier": 0.75, "maxStackSize": 0},
    )


def test_sellback_stack_cap_surfaces_end_to_end():
    # Real committed Buccaneer 0-0-4: +4% sellback, stacks up to 3 (= +12%).
    d = det.get_upgrade_detail("monkey_buccaneer:004")
    blob = " | ".join(d.buffs)
    assert "+4% sellback value" in blob
    assert "(stacks up to 3)" in blob


# --- triggered-buff window + cash-on-leak (trigger fixes the duration unit) --


def test_buff_lives_lost_trigger_renders_seconds_and_cash_on_leak():
    # on_life_lost: the window/cooldown are SECONDS, the condition is stated, and
    # the cash-on-leak is a separate permanent clause (not inside the timed bit).
    text = det._buff_text(
        {
            "name": "Nomad buff",
            "trigger": "on_life_lost",
            "rateMultiplier": 0.6,
            "rangeAdditive": 16,
            "cashOnLeakMultiplier": 2,
            "lifespan": 15,
            "cooldown": 60,
        },
    )
    assert "for 15s when a life is lost (60s cooldown)" in text
    assert "leaked bloons give 2x their value as cash" in text


def test_buff_start_of_round_trigger_renders_each_round_not_seconds():
    # start_of_round re-applies every round, so we state the condition and never
    # a fixed duration — duration_rounds must NOT surface as "3s".
    text = det._buff_text(
        {
            "name": "Start-of-round buff",
            "trigger": "start_of_round",
            "rateMultiplier": 0.25,
            "duration_rounds": 3,
        },
    )
    assert (
        text == "Start-of-round buff: x0.25 attack cooldown at the start of each round"
    )
    assert "3s" not in text and "3 round" not in text


def test_lives_lost_buff_surfaces_end_to_end():
    # Real committed Desperado Enforcer (0-0-3): event-driven buff, seconds, ×2
    # cash-on-leak — all reaching the rendered detail / AI grounding.
    d = det.get_upgrade_detail("desperado:003")
    blob = " | ".join(d.buffs)
    assert "+16 range for 15s when a life is lost (60s cooldown)" in blob
    assert "leaked bloons give 2x their value as cash" in blob


def test_start_of_round_buff_surfaces_end_to_end():
    # Real committed Spike Factory Perma-Spike (0-0-5): round-start speed buff.
    d = det.get_upgrade_detail("spike_factory:005")
    blob = " | ".join(d.buffs)
    assert "at the start of each round" in blob
    assert "lifespan" not in blob


def test_zone_slow_multiplier_renders_as_speed():
    # Ice Monkey's Arctic Wind: 'multiplier' is a speed multiplier (0.6 = 60%
    # speed). It was dropped, so Ice's signature slow was unstated. MOABs slow
    # less via multiplierForMoabs.
    text = det._zone_text(
        {"name": "Arctic Wind", "multiplier": 0.6, "multiplierForMoabs": 0.7},
    )
    assert "slows bloons to x0.6 speed" in text
    assert "MOABs to x0.7 speed" in text


def test_zone_ceramic_moab_bonus_damage_renders():
    text = det._zone_text(
        {"name": "Thorn zone", "damage": 2, "damageModifierForCeramicOrMoabs": 8},
    )
    assert "+8 damage vs Ceramic/MOAB" in text


def test_zone_moab_shove_renders_signed_per_blimp_caps():
    # Heli Pilot "MOAB Shove" (Comanche Defense 0-1-4): negative cap = shoved
    # backward (maintainer-confirmed), positive = slowed forward, 0 = halt. Values
    # are the committed data, verified exact vs the dump's *PushSpeedScaleCap.
    text = det._zone_text(
        {
            "name": "MOAB Shove",
            "radius": 42,
            "multiplierForMoab": -0.51,
            "multiplierForBfb": -0.11,
            "multiplierForZomg": 0.09,
            "multiplierForDdt": 0.09,
        },
    )
    assert "MOAB-class shoved backward at x-0.51 speed" in text
    assert "BFB shoved backward at x-0.11 speed" in text
    assert "ZOMG slowed to x0.09 speed" in text
    assert "DDT slowed to x0.09 speed" in text


def test_zone_moab_shove_zero_cap_is_a_halt():
    text = det._zone_text(
        {"name": "MOAB Shove", "multiplierForMoab": -0.4, "multiplierForBfb": 0},
    )
    assert "BFB slowed to a halt" in text


def test_zone_moab_shove_marker_does_not_fire_on_ice_slow():
    # Ice uses multiplierForMoabs (plural); the shove path keys on the singular
    # multiplierForMoab, so an Ice zone must not pick up shove phrasing.
    text = det._zone_text({"name": "Arctic Wind", "multiplierForMoabs": 0.7})
    assert "shoved" not in text and "halt" not in text


def test_ice_slow_and_thorn_bonus_surface_end_to_end():
    # Real committed data: the slow and the thorn bonus now reach the rendered
    # detail (and thus AI grounding).
    ice = " | ".join(det.get_upgrade_detail("ice_monkey:030").zones)
    assert "slows bloons to x0.6 speed" in ice
    druid = " | ".join(det.get_upgrade_detail("druid:050").zones)
    assert "damage vs Ceramic/MOAB" in druid


def test_vine_instant_pop_sentinel_renders_as_infinity_not_raw_number():
    # Live SOTF bug: the grounding showed "9,999,999 dmg" for the vine's instant-
    # pop collidable (vs the deliberate ∞ convention in the tower-stats path), and
    # the model then reported it as the MAIN attack's damage. The grounding now
    # renders ∞ for the sentinel while the real main attack stays 6 dmg.
    from utils.btd6.grounding_format import is_infinite

    assert is_infinite(9_999_999) and not is_infinite(6)
    assert not is_infinite(True) and not is_infinite(None)

    lines = det.render_upgrade_grounding(det.get_upgrade_detail("druid:050"))
    blob = "\n".join(lines)
    assert "9,999,999" not in blob and "9999999" not in blob
    assert "∞ dmg" in blob and "∞ pierce" in blob  # the vine collidable
    assert "main attack: 6 dmg" in blob  # real main attack unaffected


def test_power_effect_grounds_monkey_boost_on_a_real_upgrade():
    # Crossbow Master (dart 0-0-5) on a Monkey Boost: rate_scale 0.5 halves the
    # cooldown, so the boosted attack rate is exactly double the base rate. The
    # tool returns the grounded numbers so the model never multiplies them itself.
    res = det.power_effect("Monkey Boost", "Crossbow Master")
    assert res["found"] is True
    assert res["target"] == "Crossbow Master"
    assert res["rate_scale"] == 0.5
    assert res["duration_seconds"] == 15
    assert res["boosted_cooldown_seconds"] == round(
        res["base_cooldown_seconds"] * 0.5,
        4,
    )
    # Independent rounding of base vs boosted leaves a sub-0.01 gap.
    gap = abs(res["boosted_attacks_per_second"] - 2 * res["base_attacks_per_second"])
    assert gap < 0.01
    assert "Monkey Boost" in res["note"]


def test_power_effect_accepts_a_bare_tower_as_its_base_tier():
    res = det.power_effect("Monkey Boost", "Dart Monkey")
    assert res["found"] is True
    assert res["tier_code"] == "000"
    assert res["target"] == "Dart Monkey"


def test_power_effect_refuses_non_attack_powers_without_a_number():
    # Thrive (cash) / Camo Trap (bloons) must not produce an attack-speed number;
    # they fail closed with a pointer to the lookup tool.
    for power in ("Thrive", "Camo Trap"):
        res = det.power_effect(power, "Crossbow Master")
        assert res["found"] is False
        assert "btd6_power_lookup" in res["note"]
        assert "attacks_per_second" not in res


def test_power_effect_reports_no_attack_stat_for_economy_towers():
    # Banana Farm has no committed attack tiers — say so, don't invent a rate.
    res = det.power_effect("Monkey Boost", "Banana Farm")
    assert res["found"] is False
    assert "no attack-speed stat" in res["note"]


def test_power_effect_handles_unknown_power_and_unknown_tower():
    assert det.power_effect("Bogus", "Dart Monkey")["found"] is False
    assert det.power_effect("Monkey Boost", "not a tower")["found"] is False


# --- buff_uptime -------------------------------------------------------------
# Until parse_gamedata decodes the buff window onto the live data, these inject
# the decoded fields (buff_duration / buff_attack_cap) the same way the parser
# will — so the math + limiter logic is pinned independent of the data refresh.


def _inject_buff_window(monkeypatch, *, duration=None, cap=None, permanent=False):
    """Patch the buff-attack lookup so the Alchemist tier reports a decoded
    window (mirrors what parse_gamedata._buff_window will attach).
    """
    real = det._alch_buff_attack

    def fake(tower_id, code):
        node = real(tower_id, code)
        if node is None:
            return None
        node = dict(node)
        if duration is not None:
            node["buff_duration"] = duration
        if cap is not None:
            node["buff_attack_cap"] = cap
        if permanent:
            node["buff_permanent"] = True
        return node

    monkeypatch.setattr(det, "_alch_buff_attack", fake)


def test_buff_uptime_attack_capped_on_a_fast_tower(monkeypatch):
    # Stronger Stimulant = 12s OR 40 attacks. A 5-0-0 Ninja (0.217s) burns 40
    # attacks in ~8.7s — BEFORE the 12s timer — so it is attack-cap-limited, and
    # since the alch re-throws every 8s the buff is continuous (100% uptime). This
    # is the owner's live-test question.
    _inject_buff_window(monkeypatch, duration=12.0, cap=40)
    res = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0")
    assert res["found"] is True
    assert res["buff"] == "Berserker Brew"
    assert res["limiter"] == "attacks"
    assert res["attacks_under_buff"] == 40
    assert res["effective_window_seconds"] == pytest.approx(8.68, abs=0.05)
    assert res["throw_cadence_seconds"] == 8.0
    assert res["uptime_percent"] == 100.0


def test_buff_uptime_time_limited_on_a_slow_tower(monkeypatch):
    # A slow tower can't reach the 40-attack cap within 12s, so the TIME limit
    # binds instead — the dual-limit logic must pick the other limiter.
    _inject_buff_window(monkeypatch, duration=12.0, cap=40)
    res = det.buff_uptime("Stronger Stimulant", "Dart Monkey")
    assert res["found"] is True
    assert res["limiter"] == "time"
    assert res["effective_window_seconds"] == 12.0
    assert res["attacks_under_buff"] < 40


def test_buff_uptime_permanent_brew_is_full_uptime(monkeypatch):
    _inject_buff_window(monkeypatch, permanent=True)
    res = det.buff_uptime("Permanent Brew", "ninja 5-0-0")
    assert res["found"] is True
    assert res["limiter"] == "permanent"
    assert res["uptime"] == 1.0


def test_buff_uptime_honest_when_window_not_decoded(monkeypatch):
    # Defensive: if a buff attack ever lacks a decoded window (cadence known, but
    # no duration/cap/permanent), don't fabricate — say what IS known (throw
    # cadence + target attack speed) and never emit an uptime.
    real = det._alch_buff_attack

    def windowless(tower_id, code):
        node = real(tower_id, code)
        if node is None:
            return None
        node = dict(node)
        for k in ("buff_duration", "buff_attack_cap", "buff_permanent"):
            node.pop(k, None)
        return node

    monkeypatch.setattr(det, "_alch_buff_attack", windowless)
    res = det.buff_uptime("Stronger Stimulant", "Grandmaster Ninja")
    assert res["found"] is False
    assert res["buff"] == "Berserker Brew"
    assert "8.0s" in res["note"]  # throw cadence still surfaced
    assert "0.217" in res["note"]  # target attack speed still surfaced
    assert "uptime" not in res


def test_buff_uptime_rejects_non_alchemist_source():
    res = det.buff_uptime("Crossbow Master", "Dart Monkey")
    assert res["found"] is False
    assert "Alchemist" in res["note"]


def test_buff_uptime_reports_no_attack_stat_for_economy_target(monkeypatch):
    _inject_buff_window(monkeypatch, duration=12.0, cap=40)
    res = det.buff_uptime("alchemist 4-0-0", "Banana Farm")
    assert res["found"] is False
    assert "no attack-speed stat" in res["note"]


def test_buff_uptime_tier_without_a_buff_throw_is_honest():
    # Base Alchemist (0-0-0) has neither Berserker Brew nor Acidic Mixture Dip.
    res = det.buff_uptime("Alchemist", "Dart Monkey")
    assert res["found"] is False
    assert "no buff throw" in res["note"]


# --- buff_uptime on the REAL committed data (no injection) -------------------
# The buff window (duration + attack cap) is now decoded into stats/alchemist.json
# from the game-data dump, so these resolve end to end without monkeypatching.


def test_buff_uptime_real_data_stronger_stimulant_on_ninja():
    # The owner's live-test question, fully grounded: 4-0-0 = 12s / 40 attacks; a
    # 5-0-0 Ninja (0.217s) burns the cap in ~8.7s → attack-cap-limited, 100%.
    res = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0")
    assert res["found"] is True
    assert res["buff"] == "Berserker Brew"
    assert res["buff_duration_seconds"] == 12.0
    assert res["buff_attack_cap"] == 40
    assert res["limiter"] == "attacks"
    assert res["uptime_percent"] == 100.0


def test_buff_uptime_real_data_base_brew_is_time_limited_on_ninja():
    # Base Berserker Brew (3-0-0) = 5s / 25: a Ninja makes only ~23 attacks in 5s,
    # so TIME binds (not the cap), and thrown every 8s it is NOT continuous.
    res = det.buff_uptime("alchemist 3-0-0", "ninja 5-0-0")
    assert res["found"] is True
    assert res["buff_duration_seconds"] == 5.0
    assert res["limiter"] == "time"
    assert res["uptime_percent"] < 100.0


def test_buff_uptime_real_data_permanent_brew():
    res = det.buff_uptime("Permanent Brew", "ninja 5-0-0")
    assert res["found"] is True
    assert res["limiter"] == "permanent"
    assert res["uptime"] == 1.0


def test_buff_uptime_real_data_lead_buff_is_cap_limited():
    # Acidic Mixture Dip = 10 shots, no time limit → cap-limited on any tower.
    res = det.buff_uptime("Acidic Mixture Dip", "ninja 5-0-0")
    assert res["found"] is True
    assert res["buff"] == "Acidic Mixture Dip"
    assert res["buff_attack_cap"] == 10
    assert res["limiter"] == "attacks"
    assert "buff_duration_seconds" not in res  # lead buff has no time window


def test_buff_uptime_real_data_surfaces_rebuff_block():
    # rebuffBlockTime is decoded from the dump (5s @ 4-0-0).
    res = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0")
    assert res["rebuff_block_seconds"] == 5.0
    assert res["targets"] == 1


def test_buff_uptime_multi_target_drops_per_tower_uptime():
    # One alch buffing N towers round-robins its throws, so per-tower uptime falls
    # ~1/N: 4-0-0 on a 5-0-0 Ninja is 100% on one tower but ~54% split across two.
    one = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0", targets=1)
    two = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0", targets=2)
    assert one["uptime_percent"] == 100.0
    assert two["targets"] == 2
    assert two["rebuff_interval_seconds"] == 16.0  # max(2 × 8s, 5s floor)
    assert 50.0 <= two["uptime_percent"] <= 60.0
    assert two["uptime_percent"] < one["uptime_percent"]
    assert "2 towers" in two["note"]


def test_buff_uptime_targets_floor_is_at_least_one():
    # A nonsensical targets=0 is clamped to 1 (no divide-by-zero, no 0-target math).
    res = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0", targets=0)
    assert res["targets"] == 1
    assert res["uptime_percent"] == 100.0


# --- alch_speed (attack-speed buffs ON the Alchemist) -----------------------


def test_buff_uptime_monkey_boost_resolves_via_power():
    # Monkey Boost (a Power, rate_scale 0.5) speeds the brew throw 8s → 4s.
    res = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0", alch_speed="Monkey Boost")
    assert res["found"] is True
    assert res["alch_speed_source"] == "Monkey Boost"
    assert res["alch_speed_multiplier"] == 0.5
    assert res["effective_throw_cadence_seconds"] == 4.0


def test_buff_uptime_speed_buff_lets_alch_hold_more_towers():
    # Unboosted, a 4-0-0 alch holds ~1 Ninja at 100% but only ~54% on two.
    # Monkey Boost (×0.5 throw) lets it hold BOTH at 100%.
    plain = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0", targets=2)
    boosted = det.buff_uptime(
        "alchemist 4-0-0",
        "ninja 5-0-0",
        targets=2,
        alch_speed="Monkey Boost",
    )
    assert plain["uptime_percent"] < 100.0
    assert boosted["uptime_percent"] == 100.0
    assert boosted["uptime_percent"] > plain["uptime_percent"]


def test_buff_uptime_rebuff_floor_binds_under_fast_throwing():
    # Monkey Boost makes the throw 4s, below the 5s rebuff_block floor → the
    # floor binds (a tower can't be re-buffed faster than 5s, however fast the
    # alch throws). This is the case rebuffBlockTime exists for.
    res = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0", alch_speed="Monkey Boost")
    assert res["effective_throw_cadence_seconds"] == 4.0
    assert res["rebuff_interval_seconds"] == 5.0  # floored at rebuff_block, not 4s
    assert res["rebuff_floor_binds"] is True


def test_buff_uptime_jungle_drums_resolves_via_upgrade_rate_buff():
    # Jungle Drums (Monkey Village 2-0-0, RateSupport ×0.85) resolves through the
    # upgrade → tier rate-buff path and improves multi-target uptime.
    plain = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0", targets=2)
    jd = det.buff_uptime(
        "alchemist 4-0-0",
        "ninja 5-0-0",
        targets=2,
        alch_speed="Jungle Drums",
    )
    assert jd["found"] is True
    assert jd["alch_speed_source"] == "Jungle Drums"
    assert jd["alch_speed_multiplier"] == 0.85
    assert jd["uptime_percent"] > plain["uptime_percent"]


def test_buff_uptime_unknown_alch_speed_is_honest():
    res = det.buff_uptime("alchemist 4-0-0", "ninja 5-0-0", alch_speed="Banana")
    assert res["found"] is False
    assert "couldn't resolve" in res["note"]
    assert "Monkey Boost" in res["note"]  # names the supported kinds
