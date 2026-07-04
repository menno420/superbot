"""Unit tests for utils/ai_text_normalize.normalize_question.

Pins the conservative-equality contract the triage dedup + the preset lookup both
depend on: same question (modulo case / whitespace / edge punctuation / Unicode
fold) → same key; genuinely different wording → different keys.
"""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

import pytest  # noqa: E402

from utils.ai_text_normalize import normalize_question  # noqa: E402


@pytest.mark.parametrize("empty", [None, "", "   ", "?!", "...", "  ??  "])
def test_empty_and_punct_only_normalize_to_blank(empty) -> None:
    assert normalize_question(empty) == ""


def test_case_whitespace_and_edge_punct_fold_together() -> None:
    keys = {
        normalize_question("Can glue deal with a DDT?"),
        normalize_question("can glue deal with a ddt"),
        normalize_question("  CAN   glue deal with a DDT???  "),
        normalize_question("\tcan glue deal with a ddt!\n"),
    }
    assert len(keys) == 1
    assert keys.pop() == "can glue deal with a ddt"


def test_inner_punctuation_is_preserved() -> None:
    # crosspath codes / contractions must survive — only EDGE punctuation is trimmed.
    assert normalize_question("what's a 0-4-1?") == "what's a 0-4-1"


def test_different_questions_keep_distinct_keys() -> None:
    a = normalize_question("how much cash on round 10")
    b = normalize_question("how much cash on round 20")
    assert a != b


def test_unicode_fold_is_stable() -> None:
    # NFKC fold: a full-width digit and its ASCII form collapse.
    assert normalize_question("round １０") == normalize_question("round 10")


def test_discord_mentions_are_stripped_for_key_consistency() -> None:
    # The stored review-log question keeps the bot mention; the runtime sees it
    # stripped. Both must produce the same preset key.
    with_mention = normalize_question("<@123456789> how much cash on round 10")
    stripped = normalize_question("how much cash on round 10")
    assert with_mention == stripped == "how much cash on round 10"


def test_role_channel_and_emoji_tokens_stripped() -> None:
    assert (
        normalize_question("<@!42> <#99> <:smile:1> who wins <@&7>")
        == "who wins"
    )
