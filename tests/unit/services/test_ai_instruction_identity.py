"""SuperBot identity must be asserted in the AI system prompt.

Live testing showed the bot answering "I was created by OpenAI" when
asked who/what it is. The system prompt named the bot ("You are
SuperBot") but never told the model to override its training-based
vendor attribution, so identity questions leaked the underlying model's
maker. These tests pin the explicit identity guard so the leak can't
silently return.
"""

from __future__ import annotations

import pytest

from services import ai_instruction_service


def test_bot_ai_policy_asserts_superbot_identity_over_model_vendor():
    policy = ai_instruction_service._BOT_AI_POLICY
    assert "SuperBot" in policy
    # The model must not attribute itself to its training vendor / product.
    flattened = policy.replace("\n", " ")
    assert "OpenAI" in flattened
    assert "Anthropic" in flattened
    assert "ChatGPT" in flattened or "Claude" in flattened


@pytest.mark.asyncio
async def test_assembled_system_prompt_carries_identity_guard():
    """Every turn's system prompt (built by assemble) carries the identity
    guard — assemble always includes _BOT_AI_POLICY in the system layer.
    """
    stack = await ai_instruction_service.assemble(
        guild_id=1,
        user_message="who created you?",
        profile_ids=(),
    )
    sys_prompt = stack.render_system_prompt()
    assert "SuperBot" in sys_prompt
    assert "OpenAI" in sys_prompt
    assert "Anthropic" in sys_prompt
