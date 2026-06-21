"""Tests for utils.emoji_tokens.parse_emotes.

Pins the reaction-role Add flow's promise (owner direction, 2026-06-21): an
operator can type several emotes — spaced, jammed together, or mixed with custom
emoji — and each becomes its own bindable emote, in order, without duplicates.
"""

from __future__ import annotations

import pytest

from utils.emoji_tokens import parse_emotes

_CUSTOM = "<:custom:123456789012345678>"
_ANIM = "<a:wave:123456789012345678>"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("🎮", ["🎮"]),
        ("💀 ❤️ 😘", ["💀", "❤️", "😘"]),
        # The screenshot case: adjacent emoji with no separator must still split.
        ("💀❤️😘", ["💀", "❤️", "😘"]),
        ("  💀   ❤️  ", ["💀", "❤️"]),
        (_CUSTOM, [_CUSTOM]),
        (f"💀 {_CUSTOM} 😘", ["💀", _CUSTOM, "😘"]),
        (f"🔥🎮 {_ANIM}", ["🔥", "🎮", _ANIM]),
    ],
)
def test_parse_emotes_splits_into_ordered_list(raw: str, expected: list[str]) -> None:
    assert parse_emotes(raw) == expected


def test_parse_emotes_dedupes_preserving_order() -> None:
    assert parse_emotes("💀💀😘💀") == ["💀", "😘"]


def test_parse_emotes_keeps_zwj_sequence_whole() -> None:
    # A ZWJ family/profession emoji is one emote, never split at the joiners.
    family = "👨‍👩‍👧"
    assert parse_emotes(family) == [family]


@pytest.mark.parametrize("raw", ["", "   ", "\n\t"])
def test_parse_emotes_empty_input_is_empty_list(raw: str) -> None:
    assert parse_emotes(raw) == []


def test_parse_emotes_keeps_unrecognized_token_whole() -> None:
    # A non-emoji token is never dropped or mangled — it survives as-is so the
    # caller can surface "that isn't an emoji" instead of silently losing it.
    assert parse_emotes("hello") == ["hello"]
