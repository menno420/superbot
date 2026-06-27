"""BTD6 damage-type / status-effect interaction grounding.

Covers ``services.btd6_interaction_service`` and the curated ``damage_types.json``
it grounds. The headline guard is :func:`test_damage_table_matches_game_sourced_immunities`
— it cross-checks the curated damage-type → property table against the
game-sourced ``immune_to`` fields in ``bloons.json`` (per Q-0120: a curated
table that fights the authoritative data is a bug in the *table*). The rest pin
the fire/suppress gate and the specific corrections for the live screenshot
misses (glue does NOT resist Lead; base ice IS cold-blocked by Lead).
"""

from __future__ import annotations

import pytest

from services import btd6_data_service, btd6_interaction_service

# Representative single-property bloons whose game-sourced immune_to list is the
# authoritative truth for "which damage types does <property> block". (Status-only
# "Frozen"/"Camo" have no bloon row, so they are excluded from the cross-check.)
_PROPERTY_BLOON = {
    "Lead": "lead",
    "Black": "black",
    "White": "white",
    "Purple": "purple",
}


@pytest.fixture(autouse=True)
def _fresh_cache():
    btd6_interaction_service.reset_cache()
    yield
    btd6_interaction_service.reset_cache()


def _damage_types() -> list[dict]:
    raw = btd6_data_service.read_blob("damage_types.json")
    assert raw is not None, "damage_types.json must be present"
    return raw["damage_types"]


def test_damage_table_matches_game_sourced_immunities():
    """Each property's curated blockers == its bloon's game-sourced immune_to.

    Bidirectional: every damage type the curated table says is blocked by a
    property must appear in that property's representative bloon's immune_to,
    and vice-versa. A curated typo OR a future game-data re-seed that changes an
    immunity fails here.
    """
    dataset = btd6_data_service.get_dataset()
    by_id = {b.id: b for b in dataset.bloons}
    damage_types = _damage_types()

    for prop, bloon_id in _PROPERTY_BLOON.items():
        bloon = by_id[bloon_id]
        curated = {
            dt["name"]
            for dt in damage_types
            if prop in dt.get("blocked_by_properties", [])
        }
        game_sourced = set(bloon.immune_to or ())
        assert curated == game_sourced, (
            f"{prop}: curated damage table {sorted(curated)} disagrees with "
            f"game-sourced {bloon.canonical}.immune_to {sorted(game_sourced)}"
        )


def test_every_damage_type_is_complete():
    for dt in _damage_types():
        assert dt["id"] and dt["name"], dt
        assert dt.get("aliases"), f"{dt['id']} needs aliases"
        assert dt.get("summary"), f"{dt['id']} needs a summary"
        assert "blocked_by_properties" in dt, dt["id"]


def test_glue_correction_lead_is_not_resisted():
    """The exact live screenshot error: the bot said 'Lead resists glue'.

    The grounded glue fact must state the opposite — glue is a status effect
    that ignores damage-type immunity and works on Lead — and must route
    MOAB-class through MOAB Glue.
    """
    facts = btd6_interaction_service.interaction_facts(
        "can glue strike deal with lead bloons and DDTs",
    )
    blob = " ".join(facts).lower()
    assert "lead does not resist glue" in blob
    assert "status effect" in blob
    assert "moab glue" in blob
    # It must NOT imply Lead resists glue.
    assert "lead resists glue" not in blob


def test_ice_is_cold_blocked_by_lead():
    """Base ice is cold-based and blocked by Lead — and the Cold Snap crosspath
    is the fix (the point the owner raised: ice has a crosspath to hit lead)."""
    facts = btd6_interaction_service.interaction_facts("can ice monkey slow DDTs")
    blob = " ".join(facts).lower()
    assert "cold" in blob and "lead" in blob
    assert "cold snap" in blob


def test_ddt_grounds_verified_counter_towers():
    """'how do I deal with a DDT' must ground a VERIFIED tower list so the model
    names real towers (and the faithfulness guard does not refuse the answer).
    This is the over-refusal fix: the towers are derived from the dump, not
    freelanced."""
    facts = btd6_interaction_service.interaction_facts("how do I deal with a DDT")
    counter = [f for f in facts if "towers whose attack can damage a ddt" in f.lower()]
    assert counter, "expected a grounded DDT counter-tower fact"
    blob = counter[0].lower()
    # Real, verified damage-dealers must be named.
    assert "super monkey" in blob
    assert "spike factory" in blob
    # It must be framed as a capability list, not freelanced advice.
    assert "verified from game data" in blob


def test_ddt_pop_guide_lists_correct_damage():
    facts = btd6_interaction_service.interaction_facts(
        "how do I deal with a DDT",
    )
    blob = " ".join(facts).lower()
    assert "camo detection" in blob
    # The five blocked types must be named as blocked, fire/plasma as the answer.
    for blocked in ("sharp", "cold", "energy", "explosion"):
        assert blocked in blob
    assert "fire" in blob or "plasma" in blob


def test_lead_pop_guide_does_not_offer_sharp():
    facts = btd6_interaction_service.interaction_facts("what pops lead bloons")
    # The 'needs' clause must not tell the user Sharp pops Lead.
    assert facts
    needs = facts[0].split("needs", 1)[1].split(";", 1)[0].lower()
    assert "sharp" not in needs
    assert "explosion" in needs


@pytest.mark.parametrize(
    "message",
    [
        "how much does glue gunner cost",
        "what is a ddt",
        "tell me about the ice monkey",
        "what are the dartling gunner upgrades",
    ],
)
def test_lookups_do_not_fire_interaction(message):
    """Cost / definition / upgrade-listing lookups ground no interaction facts —
    the verb-gate + two-entities rule keeps the layer to interaction questions."""
    assert btd6_interaction_service.interaction_facts(message) == []


@pytest.mark.parametrize(
    "message",
    [
        "can you pop purple with plasma",
        "does sharp damage pop lead",
        "can glue deal with ddts",
        "what slows a moab",
        "is bomb shooter good against black bloons",
    ],
)
def test_interaction_questions_fire(message):
    assert btd6_interaction_service.interaction_facts(message), message


def test_empty_message_is_safe():
    assert btd6_interaction_service.interaction_facts("") == []
    assert btd6_interaction_service.interaction_facts("   ") == []


async def test_build_wires_interaction_facts_for_screenshot_question():
    """End-to-end: the new pass 3g in build() emits the interaction facts for
    the exact live screenshot question, so the model gets the glue+DDT correction."""
    from services import btd6_context_service

    ctx = await btd6_context_service.build("can glue strike and avenger deal with DDTs")
    interaction = [f for f in ctx.facts if f.startswith("[btd6_interaction]")]
    blob = " ".join(interaction).lower()
    assert interaction, "build() must ground interaction facts for this question"
    assert "lead does not resist glue" in blob
    assert "moab glue" in blob
