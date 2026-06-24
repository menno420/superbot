"""Paragon degree scaling reproduces the wiki's own ``parse_paragon_table``.

Every formula here is pinned to a value read directly off a bloonswiki paragon
page's "Degree-dependent stats" table, so a drift in the math fails loudly. The
worked example (cooldown 0.5s, pierce 210, damage 25 at degree 1) is the canonical
one shown on the Glaive Dominus / Apex-style pages.
"""

from __future__ import annotations

from utils.btd6 import paragon_degrees as pd

# The wiki's hardcoded `degree_requirements` table (Module:BTD6 stats), the
# authoritative oracle for the Power column. Index 0 == degree 1.
_WIKI_POWER = [
    0, 2000, 2324, 2666, 3027, 3408, 3808, 4228, 4669, 5131,
    5615, 6121, 6650, 7203, 7779, 8379, 9004, 9654, 10330, 11032,
    11761, 12518, 13302, 14114, 14955, 15825, 16725, 17655, 18616, 19609,
    20633, 21689, 22778, 23900, 25056, 26246, 27471, 28732, 30028, 31360,
    32729, 34135, 35579, 37061, 38582, 40143, 41743, 43383, 45064, 46786,
    48550, 50356, 52205, 54098, 56034, 58014, 60039, 62109, 64225, 66387,
    68596, 70853, 73157, 75509, 77910, 80360, 82860, 85410, 88011, 90664,
    93368, 96124, 98933, 101795, 104711, 107681, 110706, 113787, 116923, 120115,
    123364, 126670, 130034, 133456, 136937, 140478, 144078, 147738, 151459, 155241,
    159085, 162991, 166960, 170993, 175089, 179249, 183474, 187764, 192120, 200000,
]  # fmt: skip


def test_power_column_matches_wiki_table_for_all_100_degrees():
    for degree in range(1, 101):
        assert pd.power_for_degree(degree) == _WIKI_POWER[degree - 1], degree


def test_cooldown_scaling_matches_page():
    f = pd.format_value
    assert f(pd.scale_cooldown(0.5, 1)) == "0.5"
    assert f(pd.scale_cooldown(0.5, 2)) == "0.467"
    assert f(pd.scale_cooldown(0.5, 3)) == "0.4545"
    assert f(pd.scale_cooldown(0.5, 20)) == "0.3822"
    assert f(pd.scale_cooldown(0.5, 21)) == "0.3799"


def test_pierce_scaling_matches_page():
    f = pd.format_value
    assert f(pd.scale_pierce(210, 1)) == "210"
    assert f(pd.scale_pierce(210, 2)) == "212.1"
    assert f(pd.scale_pierce(210, 10)) == "228.9"
    assert f(pd.scale_pierce(210, 11)) == "232"  # the +1 per-ten step kicks in
    assert f(pd.scale_pierce(210, 20)) == "250.9"
    assert f(pd.scale_pierce(210, 21)) == "254"


def test_damage_scaling_matches_page():
    f = pd.format_value
    assert f(pd.scale_damage(25, 1)) == "25"
    assert f(pd.scale_damage(25, 2)) == "25.25"
    assert f(pd.scale_damage(25, 11)) == "28.5"  # +1 step at degree 11
    assert f(pd.scale_damage(25, 20)) == "30.75"
    assert f(pd.scale_damage(25, 21)) == "32"


def test_damage_modifier_scaling():
    f = pd.format_value
    assert f(pd.scale_damage_modifier(60, 1)) == "60"
    assert f(pd.scale_damage_modifier(60, 2)) == "60.6"
    # No per-ten step for modifiers (pure +1%/degree).
    assert pd.scale_damage_modifier(60, 11) == 60 * 1.10


def test_degree_100_specials_are_double_plus_ten():
    assert pd.scale_damage(25, 100) == 25 * 2 + 10
    assert pd.scale_pierce(210, 100) == 210 * 2 + 10
    assert pd.scale_damage_modifier(60, 100) == 60 * 2 + 10


def test_boss_multiplier_ladder():
    assert pd.boss_multiplier(1) == 1.0
    assert pd.boss_multiplier(19) == 1.0
    assert pd.boss_multiplier(20) == 1.25
    assert pd.boss_multiplier(39) == 1.25
    assert pd.boss_multiplier(40) == 1.5
    assert pd.boss_multiplier(60) == 1.75
    assert pd.boss_multiplier(80) == 2.0
    assert pd.boss_multiplier(99) == 2.0
    assert pd.boss_multiplier(100) == 2.25


def test_elite_boss_multiplier_is_boss_times_two_at_every_degree():
    # Paragons deal DOUBLE their boss damage to Elite Bosses — a flat x2 that
    # applies at all degrees (Fandom "Extra Damage to Boss"/"Paragons": "the extra
    # damage from Paragons is doubled ... even at degree 1"; cross-checked vs hemi's
    # paragon bot ed=2x bd). It is NOT in the dump (verified: no Elite tag on the
    # Dart/Ice paragon models, no elite field in paragonDegreeData) — a curated
    # runtime constant. So elite == boss x ELITE_BOSS_DAMAGE_MULTIPLIER for all d.
    assert pd.ELITE_BOSS_DAMAGE_MULTIPLIER == 2.0
    for d in (1, 19, 20, 35, 60, 80, 99, 100):
        assert pd.elite_boss_multiplier(d) == pd.boss_multiplier(d) * 2.0
    # Anchors: Degree 1 -> x2.0, Degree 35 -> x2.5 (the owner screenshot), 100 -> x4.5
    assert pd.elite_boss_multiplier(1) == 2.0
    assert pd.elite_boss_multiplier(35) == 2.5
    assert pd.elite_boss_multiplier(100) == 4.5


def test_degree_row_carries_elite_boss_multiplier():
    row = pd.degree_row({}, 35)
    assert row.elite_boss_multiplier == 2.5
    assert row.elite_boss_multiplier == row.boss_multiplier * 2.0


# A cleaned paragon node mirroring the page worked example: one attack with a
# cooldown and two projectiles carrying boss + ceramic damage modifiers.
_NODE = {
    "range": 85,
    "attacks": [
        {
            "name": "Attack",
            "rate": 0.5,
            "projectiles": [
                {
                    "name": "Projectile",
                    "pierce": 210,
                    "maxPierce": 0,
                    "damage": 25,
                    "damageModifierForBoss": 60,
                    "damageModifierForCeramic": 75,
                },
                {
                    "name": "Mini-projectile",
                    "pierce": 200,
                    "maxPierce": 0,
                    "damage": 25,
                },
            ],
        },
    ],
}


def _cell(row, group, label):
    return next(s for s in row.stats if s.group == group and s.label == label)


def test_degree_row_degree_1_equals_base():
    row = pd.degree_row(_NODE, 1)
    assert row.degree == 1
    assert row.power == 0
    assert row.boss_multiplier == 1.0
    assert _cell(row, "Attack", "Cooldown").value == 0.5
    assert _cell(row, "Projectile", "Pierce").value == 210
    assert _cell(row, "Projectile", "Damage").value == 25
    assert _cell(row, "Projectile", "Damage to bosses").value == 60
    assert _cell(row, "Projectile", "Damage to Ceramic").value == 75


def test_degree_row_scales_every_cell():
    row = pd.degree_row(_NODE, 2)
    assert pd.format_value(_cell(row, "Attack", "Cooldown").value) == "0.467"
    assert pd.format_value(_cell(row, "Projectile", "Pierce").value) == "212.1"
    assert pd.format_value(_cell(row, "Projectile", "Damage").value) == "25.25"
    assert _cell(row, "Projectile", "Damage to bosses").value == 60 * 1.01
    assert _cell(row, "Mini-projectile", "Pierce").value == 202.1


def test_modifier_emit_order_matches_wiki():
    # boss BEFORE ceramic, exactly as parse_paragon_table emits them.
    row = pd.degree_row(_NODE, 1)
    labels = [s.label for s in row.stats if s.group == "Projectile"]
    assert labels == ["Pierce", "Damage", "Damage to bosses", "Damage to Ceramic"]


def test_cooldown_and_modifier_flags():
    row = pd.degree_row(_NODE, 5)
    assert _cell(row, "Attack", "Cooldown").is_cooldown is True
    assert _cell(row, "Projectile", "Damage to bosses").is_modifier is True
    assert _cell(row, "Projectile", "Pierce").is_modifier is False


def test_degree_groups_are_ordered_and_distinct():
    assert pd.degree_stat_groups(_NODE) == ("Attack", "Projectile", "Mini-projectile")


def test_degree_is_clamped():
    assert pd.degree_row(_NODE, 0).degree == 1
    assert pd.degree_row(_NODE, 250).degree == 100


def test_infinite_pierce_and_sentinel_rate_are_omitted():
    node = {
        "attacks": [
            {
                "name": "Spin",
                "rate": 99999,  # sentinel: no real cooldown
                "projectiles": [
                    {"name": "P", "pierce": 9999999, "maxPierce": 0, "damage": 10},
                ],
            },
        ],
    }
    row = pd.degree_row(node, 50)
    assert all(s.label != "Cooldown" for s in row.stats)
    assert all(s.label != "Pierce" for s in row.stats)
    # Damage still scales.
    assert any(s.label == "Damage" for s in row.stats)
