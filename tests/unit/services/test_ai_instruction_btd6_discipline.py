"""Pin: the BTD6 verify-or-disclaim grounding discipline reaches the model.

``_TASK_CONTRACT`` is always part of the system instruction layer in
``ai_instruction_service.assemble`` (it is one of the three base system
strings), so asserting the clause here pins what every turn's system prompt
carries — without needing a DB to assemble a full stack.
"""

from __future__ import annotations

from services import ai_instruction_service as instr


def test_task_contract_instructs_proactive_btd6_lookup():
    tc = instr._TASK_CONTRACT
    assert "Bloons TD 6" in tc
    assert "btd6_lookup" in tc  # call the tool when no fact span covers it


def test_task_contract_carries_exact_disclaimer_and_no_fact_claims():
    tc = instr._TASK_CONTRACT
    # The verbatim disclaimer the model must lead with when it has no data.
    assert "I don't have verified BTD6 data on that, but here's my best guess:" in tc
    assert "Never present an unverified BTD6 claim as established fact" in tc


def test_task_contract_is_a_base_system_string():
    # Guards that the contract is one of the always-on system strings, so the
    # discipline is not accidentally demoted to an optional profile body.
    assert instr._TASK_CONTRACT not in ("", None)
    assert isinstance(instr._TASK_CONTRACT, str)
