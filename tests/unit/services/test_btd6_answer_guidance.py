"""Crosspath answer-guidance block: focus the AI on a named upgrade."""

from __future__ import annotations

import pytest

from services import btd6_ai_knowledge_block_service as kb


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("just the stats of the top path, 400", True),
        ("4-0-0 glue gunner", True),
        ("give me the top path tier 4 stats", True),
        ("what does the dart monkey do", False),
        ("most expensive upgrade", False),
    ],
)
def test_crosspath_detector(text, expected):
    assert kb.looks_like_btd6_crosspath_question(text) is expected


@pytest.mark.asyncio
async def test_guidance_block_emitted_for_crosspath_question():
    blocks = await kb.gather_btd6_bot_knowledge_blocks(user_text="stats of 4-0-0 glue gunner")
    kinds = [b.kind for b in blocks]
    assert "bot_btd6_answer_guidance" in kinds
    guidance = next(b for b in blocks if b.kind == "bot_btd6_answer_guidance")
    assert "that specific" in guidance.text.lower()


@pytest.mark.asyncio
async def test_no_guidance_block_without_crosspath():
    blocks = await kb.gather_btd6_bot_knowledge_blocks(user_text="what is the dart monkey")
    assert "bot_btd6_answer_guidance" not in [b.kind for b in blocks]
