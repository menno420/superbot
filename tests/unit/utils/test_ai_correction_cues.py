"""Unit tests for the correction-cue heuristic (utils/ai_correction_cues.py).

Pins the conservative "is this reply a correction?" gate used by
``cogs/ai_review_cog.py`` — explicit negation / correction cues fire; ordinary
follow-ups and thanks do not.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.ai_correction_cues import looks_like_correction  # noqa: E402


@pytest.mark.parametrize(
    "text",
    [
        "no, it's actually 5",
        "No that's wrong",
        "nope",
        "nah it's the other one",
        "that's incorrect",
        "actually it costs 700",
        "you mean the dartling",
        "that should be 250 not 300",
        "wrong",
        "that isn't right",
        "that's false",
        "not quite, it's tier 5",
    ],
)
def test_positive_corrections(text: str) -> None:
    assert looks_like_correction(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "thanks!",
        "tell me more about that tower",
        "what about the next round?",
        "ok cool",
        "now I get it",  # 'now' must not trip the leading-"no" cue
        "nobody asked but interesting",  # 'nobody' must not trip it
        "",
        "   ",
        None,
    ],
)
def test_negative_non_corrections(text: str | None) -> None:
    assert looks_like_correction(text) is False
