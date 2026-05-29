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


def test_task_contract_names_all_three_btd6_lookup_tools():
    tc = instr._TASK_CONTRACT
    assert "Bloons TD 6" in tc
    assert "btd6_lookup" in tc  # named entity / topic
    assert "btd6_capability_lookup" in tc  # 'which tower …'
    assert "btd6_superlative_lookup" in tc  # 'most/least expensive …'


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
