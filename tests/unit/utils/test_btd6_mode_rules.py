"""utils.btd6.mode_rules — the shared mode-rules clause formatter.

Both surfaces (the ``btd6_mode_lookup`` AI payload's consumers and the menu's
modes embed) render the cutover's structured ``rules`` block through this one
formatter, so the wording is pinned here once.
"""

from __future__ import annotations

from utils.btd6.mode_rules import summarize_mode_rules


def test_empty_rules_yield_no_clauses():
    assert summarize_mode_rules({}) == []


def test_chimps_shaped_rules_render_every_clause():
    clauses = summarize_mode_rules(
        {
            "starting_lives": 1,
            "start_round": 6,
            "end_round": 100,
            "locked_towers": ["BananaFarm"],
            "no_continues": True,
            "no_selling": True,
            "no_monkey_knowledge": True,
        },
    )
    assert clauses == [
        "1 life",
        "rounds 6–100",
        "Banana Farm locked",
        "no continues",
        "no selling",
        "no Monkey Knowledge",
    ]


def test_deflation_no_income_suppresses_zero_multiplier():
    # Deflation carries BOTH income_multiplier 0 and the no_income flag —
    # one clause, not a redundant "income ×0" pair.
    clauses = summarize_mode_rules(
        {"starting_cash": 20000, "income_multiplier": 0, "no_income": True},
    )
    assert clauses == ["$20,000 starting cash", "no income from pops"]


def test_multipliers_and_roundset_clauses():
    clauses = summarize_mode_rules(
        {
            "cost_multiplier": 1.2,
            "speed_multiplier": 1.25,
            "moabs_health_multiplier": 2,
            "income_multiplier": 0.5,
            "round_set": "AlternateRoundSet",
            "reverse": True,
        },
    )
    assert clauses == [
        "Alternate Bloons Rounds",
        "reversed track",
        "prices ×1.2",
        "bloon speed ×1.25",
        "MOAB-class health ×2",
        "income ×0.5",
    ]


def test_locked_tower_classes_clause():
    clauses = summarize_mode_rules(
        {"locked_tower_classes": ["magic", "military", "support"]},
    )
    assert clauses == ["magic/military/support towers locked"]


def test_single_bound_rounds_and_unknown_key_stay_visible():
    # A future dump key must render (unpolished) rather than go dark.
    clauses = summarize_mode_rules({"start_round": 31, "new_dump_key": 7})
    assert clauses == ["starts at round 31", "new_dump_key=7"]
    assert summarize_mode_rules({"end_round": 60}) == ["ends at round 60"]
