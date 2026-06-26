"""Seam pin: PROJMOON_ANSWER routes feature-fact gathering to projmoon grounding.

Project Moon knowledge-domain PR 2 (Slice A item 2). ``_gather_feature_facts``
must hand a ``PROJMOON_ANSWER`` turn to ``projmoon_context_service`` and return
its grounded facts, so they flow into the instruction stack's ``retrieved_facts``.
A non-Limbus general turn must still gather nothing (default-preserving).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai import natural_language_stage as stage  # noqa: E402
from core.runtime.ai.contracts import AITask  # noqa: E402
from core.runtime.ai.feature_facts import FeatureFactRequest  # noqa: E402


def _req(task: AITask, text: str) -> FeatureFactRequest:
    return FeatureFactRequest(
        task=task,
        text=text,
        guild_id=1,
        channel_id=2,
        author_id=3,
        message_id=4,
    )


@pytest.mark.asyncio
async def test_projmoon_task_gathers_limbus_grounding_facts() -> None:
    result = await stage._gather_feature_facts(
        _req(AITask.PROJMOON_ANSWER, "tell me about Faust in limbus"),
    )
    assert result.facts
    assert any(f.startswith("Faust:") for f in result.facts)


@pytest.mark.asyncio
async def test_general_task_still_gathers_no_facts() -> None:
    result = await stage._gather_feature_facts(
        _req(AITask.GENERAL_NL_ANSWER, "tell me about Faust in limbus"),
    )
    assert result.facts == ()
