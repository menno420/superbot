"""Pin: the BTD6 grounding discipline reaches the model — and is *scoped*.

``_TASK_CONTRACT`` is always part of the system instruction layer in
``ai_instruction_service.assemble`` (one of the three base system strings), so
asserting the clause here pins what every turn's system prompt carries without
needing a DB.

The discipline is deliberately scoped: answer general/conceptual BTD6 questions
normally (no blanket disclaimer — that regression made the bot look broken on
"what are paragons"); ground only SPECIFIC stats via the lookup tools.
"""

from __future__ import annotations

from services import ai_instruction_service as instr


def test_task_contract_names_the_btd6_lookup_tools():
    tc = instr._TASK_CONTRACT
    assert "Bloons TD 6" in tc
    assert "btd6_lookup" in tc  # named entity / topic
    assert "btd6_capability_lookup" in tc  # 'which tower …'
    assert "btd6_superlative_lookup" in tc  # 'most/least expensive …'
    assert "btd6_difficulty_cost" in tc  # Easy/Hard/Impoppable conversion


def test_task_contract_teaches_difficulty_scaling_and_faithful_lists():
    tc = instr._TASK_CONTRACT
    # Costs vary by difficulty — the bot must not claim they're uniform.
    assert "scale with difficulty" in tc
    assert "across difficulties" in tc
    # Don't invent list entries (the hallucinated "Dart Monkey Paragon").
    assert "use only the entries it returned" in tc


def test_task_contract_scopes_grounding_to_specific_stats():
    tc = instr._TASK_CONTRACT
    # General/conceptual questions must NOT be prefaced with a disclaimer.
    assert "do NOT preface these with a disclaimer" in tc
    # Grounding is required only for specific stats.
    assert "SPECIFIC stat" in tc
    # No fabricated precise numbers.
    assert "never state an invented precise stat as fact" in tc


def test_task_contract_dropped_the_blanket_disclaimer():
    # The old all-or-nothing disclaimer is gone (it fired on general questions).
    tc = instr._TASK_CONTRACT
    assert "but here's my best guess:" not in tc


def test_task_contract_is_a_base_system_string():
    assert instr._TASK_CONTRACT not in ("", None)
    assert isinstance(instr._TASK_CONTRACT, str)


def test_task_contract_requires_calling_lookup_before_claiming_missing():
    # The bot was refusing to call the tool — asserting from a stale prior turn
    # that the lookup "isn't exposing" abilities instead of just trying.
    tc = instr._TASK_CONTRACT
    assert "ALWAYS run the lookup before telling the user you lack" in tc
    # Don't infer tool contents from earlier turns; data changes between messages.
    assert "can change between messages" in tc
    assert "found=false" in tc  # only report missing AFTER an actual call


def test_task_contract_routes_upgrades_and_paragon_abilities_to_lookup():
    tc = instr._TASK_CONTRACT
    # The routing line must name the entity kinds added this cycle, so the model
    # knows btd6_lookup covers them (not just towers/heroes/bloons).
    assert "an upgrade by name or abbreviation" in tc
    assert "paragon ability" in tc


def test_task_contract_routes_per_degree_paragon_stats_and_forbids_interpolation():
    tc = instr._TASK_CONTRACT
    assert "btd6_paragon_stats_at_degree" in tc
    assert "NON-linear" in tc
    assert "square-root" in tc
    assert "interpolate" in tc  # the model must not linearly interpolate degrees
