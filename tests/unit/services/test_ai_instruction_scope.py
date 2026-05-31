"""SuperBot must accept general requests, not just BTD6 / server ones.

Live testing showed the bot refusing everyday requests ("make me a cake
recipe") with "I'm not a general-purpose bot ... that's outside my
scope." The base system prompt framed SuperBot exclusively around BTD6
and server management, so the model inferred everything else was off
limits and declined — the same look-broken failure mode as the old
blanket BTD6 disclaimer.

The prompt now states the breadth explicitly: BTD6 and this server are
the *specialty*, but SuperBot is also a general-purpose assistant that
answers everyday requests directly. These tests pin that breadth clause
(in both the persona policy and the per-request task contract) so the
over-refusal can't silently return.
"""

from __future__ import annotations

import pytest

from services import ai_instruction_service as instr


def test_bot_ai_policy_declares_general_assistant_scope():
    policy = instr._BOT_AI_POLICY
    # Specialty framing is kept ...
    assert "specialty" in policy
    assert "Bloons TD 6" in policy
    # ... but the bot is explicitly also a general-purpose assistant.
    assert "general-purpose assistant" in policy
    assert "recipes" in policy


def test_bot_ai_policy_forbids_off_topic_refusal():
    """The exact refusal phrasings from live testing must be forbidden."""
    policy = instr._BOT_AI_POLICY
    assert "not a general-purpose bot" in policy
    assert "outside your scope" in policy
    # The instruction must tell the model NOT to refuse for being off-topic.
    flattened = policy.replace("\n", " ")
    assert "Do NOT refuse" in flattened
    assert "off-topic" in flattened


def test_task_contract_permits_general_requests():
    tc = instr._TASK_CONTRACT
    assert "general assistant too" in tc
    # The everyday-request examples reach the model in the per-turn contract.
    assert "recipes" in tc
    assert "Never refuse or deflect a request" in tc


@pytest.mark.asyncio
async def test_assembled_system_prompt_carries_scope_breadth():
    """Every turn's system prompt (built by assemble) carries the breadth
    clause — assemble always includes _BOT_AI_POLICY and _TASK_CONTRACT in
    the system layer, with no DB or guild profile required.
    """
    stack = await instr.assemble(
        guild_id=1,
        user_message="make me a cake recipe",
        profile_ids=(),
    )
    sys_prompt = stack.render_system_prompt()
    assert "general-purpose assistant" in sys_prompt
    assert "general assistant too" in sys_prompt
