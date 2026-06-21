"""Tests for utils.duration — human duration parsing/formatting."""

from __future__ import annotations

import pytest

from utils.duration import MAX_DURATION_SECONDS, format_duration, parse_duration


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("30m", 1800),
        ("2h", 7200),
        ("2h30m", 9000),
        ("7d", 604800),
        ("1w", 604800),
        ("90s", 90),
        ("30", 1800),  # bare number = minutes
        ("  2h  ", 7200),  # whitespace tolerated
    ],
)
def test_parse_duration_valid(text: str, expected: int):
    assert parse_duration(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", "   ", "abc", "0", "0m", "soon", "-5m"],
)
def test_parse_duration_invalid_returns_none(text: str):
    assert parse_duration(text) is None


def test_parse_duration_rejects_over_cap():
    assert parse_duration("400d") is None
    # Exactly the cap (365d) is allowed.
    assert parse_duration("365d") == MAX_DURATION_SECONDS


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (5400, "1h 30m"),
        (90, "1m 30s"),
        (604800, "7d"),
        (0, "0s"),
        (3600, "1h"),
    ],
)
def test_format_duration(seconds: int, expected: str):
    assert format_duration(seconds) == expected
