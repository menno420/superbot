"""Tests for the obfuscation-resistant word matcher (utils.text_obfuscation).

The pure module carries the bulk of the feature's value, so it is tested
exhaustively here: every evasion class it is meant to defeat, the
false-positive boundaries it must NOT cross (Scunthorpe-safety), and the
invisible-character layer specifically.
"""

from __future__ import annotations

import pytest

from utils.text_obfuscation import deobfuscate, find_obfuscated_match

WORDS = ["bad", "spam", "ass"]


# ---------------------------------------------------------------------------
# deobfuscate — normalization primitives
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("bad", "bad"),
        ("BAD", "bad"),
        ("ＢＡＤ", "bad"),  # fullwidth
        ("𝐛𝐚𝐝", "bad"),  # mathematical bold
        ("ｂａｄ", "bad"),  # fullwidth lower
        ("bád", "bad"),  # precomposed accent
        ("bád", "bad"),  # combining accent (zalgo-style)
        ("b4d", "bad"),  # leet inside a letter-token
        ("a$$", "ass"),  # leet symbols inside a letter-token
        ("455", "455"),  # bare number — NOT folded to a word
        ("2026", "2026"),  # year stays a year
    ],
)
def test_deobfuscate(raw: str, expected: str) -> None:
    assert deobfuscate(raw) == expected


def test_deobfuscate_strips_zero_width() -> None:
    assert deobfuscate("b​a​d") == "bad"


def test_deobfuscate_strips_invisible_letters() -> None:
    # Hangul filler (Lo) + braille blank (So) — invisible but NOT format chars.
    assert deobfuscate("bㅤa⠀d") == "bad"


# ---------------------------------------------------------------------------
# find_obfuscated_match — catches (the point of the feature)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "content",
    [
        "bad",  # plain
        "BAD",  # caps
        "b4d",  # leet
        "b a d",  # spaced
        "b.a.d",  # dot-separated
        "b-a-d",  # dash-separated
        "b_a_d",  # underscore-separated
        "ＢＡＤ",  # fullwidth
        "𝐛𝐚𝐝",  # mathematical
        "this is b4d stuff",  # embedded
        "a 5 5",  # spaced leet (combined evasion)
    ],
)
def test_match_catches_obfuscation(content: str) -> None:
    assert find_obfuscated_match(content, WORDS) is not None


@pytest.mark.parametrize(
    "sep",
    [
        "​",  # zero width space
        "‌",  # zero width non-joiner
        "‍",  # zero width joiner
        "⁠",  # word joiner
        "﻿",  # BOM / zero width no-break space
        "ㅤ",  # HANGUL FILLER (the "passes advanced bots" one)
        "ᅟ",  # HANGUL CHOSEONG FILLER
        "⠀",  # BRAILLE PATTERN BLANK
        "ﾠ",  # HALFWIDTH HANGUL FILLER
        "­",  # SOFT HYPHEN
    ],
)
def test_match_catches_invisible_insertion(sep: str) -> None:
    """A banned word broken up by invisible characters is still caught."""
    payload = sep.join("bad")  # b<inv>a<inv>d
    assert find_obfuscated_match(payload, WORDS) == "bad"


def test_match_catches_unicode_confusables() -> None:
    # Cyrillic а (U+0430), Greek о would not apply; build "bad" from look-alikes.
    assert find_obfuscated_match("bаd", WORDS) == "bad"  # Cyrillic a


def test_match_returns_original_word() -> None:
    # The configured term is returned (for the audit reason), not its
    # normalized form.
    assert find_obfuscated_match("SP4M!!", ["spam"]) == "spam"


# ---------------------------------------------------------------------------
# find_obfuscated_match — false-positive boundaries (must NOT match)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "content",
    [
        "hello world",  # unrelated
        "therapist",  # contains "rapist" — must NOT trip a banned "rapist"
        "class",  # contains "ass"
        "grass",  # contains "ass"
        "455",  # bare number — must NOT become "ass"
        "the bassist played",  # "bassist" contains "ass"
    ],
)
def test_match_avoids_false_positives(content: str) -> None:
    assert find_obfuscated_match(content, ["bad", "ass", "rapist"]) is None


def test_therapist_not_flagged_as_rapist() -> None:
    # The headline Scunthorpe case: separator collapse never crosses a real
    # word boundary, so normal prose with no spacing is safe.
    assert find_obfuscated_match("my therapist is great", ["rapist"]) is None


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("content", "words"),
    [
        ("", ["bad"]),
        ("anything", []),
        ("anything", [""]),
    ],
)
def test_match_edge_cases_return_none(content: str, words: list[str]) -> None:
    assert find_obfuscated_match(content, words) is None


def test_deobfuscate_empty() -> None:
    assert deobfuscate("") == ""
