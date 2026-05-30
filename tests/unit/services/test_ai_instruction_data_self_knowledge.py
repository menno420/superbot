"""The bot must describe its own data/sources truthfully.

Live testing: when a user asked SuperBot "did you confirm that in the
files?" after a BTD6 list, it replied "I don't have access to any
internal files or data" — false, since it has a verified BTD6 data set,
lookup tools, and authoritative bot_* reference spans. The task contract
now carries an explicit data-self-knowledge clause: acknowledge the real
data, stay honest per-answer (grounded vs. open-ended recall), and never
flatly deny having any data/files. These tests pin that clause so the
denial can't silently return.
"""

from __future__ import annotations

from services import ai_instruction_service as instr


def test_task_contract_asserts_real_data_access():
    tc = instr._TASK_CONTRACT
    assert "verified reference data" in tc
    assert "verified BTD6 data" in tc
    # The exact false claim the bot made must be forbidden.
    assert "no data or files" in tc


def test_task_contract_keeps_verify_or_disclaim_for_recall():
    """It must not let the bot present unverified recall as confirmed data."""
    tc = instr._TASK_CONTRACT
    assert "never present unverified recall as confirmed data" in tc


def test_task_contract_does_not_overclaim_attachment_access():
    """It must not claim it can read arbitrary uploads / full history."""
    tc = instr._TASK_CONTRACT
    assert "cannot read uploaded attachments" in tc
