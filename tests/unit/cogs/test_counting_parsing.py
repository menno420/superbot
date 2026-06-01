"""Tests for the counting expression parser (``cogs.counting.parsing``).

Covers the original behaviour (word numbers, Roman numerals, basic
arithmetic, equality checks) plus the extended "complicated formula"
support: whitelisted math functions, named constants, modulo / floor
division, and postfix factorial — and the DoS guards that keep a crafted
message from stalling the on_message hot path.
"""

from __future__ import annotations

import time

import pytest

from cogs.counting import _constants
from cogs.counting.parsing import parse_message


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # --- pre-existing behaviour (regression) ---
        ("5", 5),
        ("twenty three", 23),
        ("5 + 3", 8),
        ("2 ** 3", 8),
        ("2 ^ 3", 8),
        ("(4 + 2) * 3", 18),
        ("ten times five", 50),
        ("5 + 3 = 8", 8),
        ("-5", -5),
        ("IV", 4),
        ("a dozen", 12),
    ],
)
def test_basic_and_word_numbers(text: str, expected: int) -> None:
    assert parse_message(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # --- new: math functions ---
        ("sqrt(16)", 4),
        ("factorial(5)", 120),
        ("gcd(12, 8)", 4),
        ("lcm(4, 6)", 12),
        ("comb(5, 2)", 10),
        ("perm(5, 2)", 20),
        ("abs(-7)", 7),
        ("max(3, 9, 5)", 9),
        ("min(3, 9, 5)", 3),
        ("floor(7 / 2)", 3),
        ("ceil(7 / 2)", 4),
        ("round(sqrt(50))", 7),
        ("hypot(3, 4)", 5),
        ("cbrt(27)", 3),
        # --- new: modulo / floor division ---
        ("10 % 3", 1),
        ("17 // 5", 3),
        ("10 mod 3", 1),
        # --- new: postfix factorial ---
        ("5!", 120),
        ("(2 + 3)!", 120),
        ("3! + 4!", 30),
        # --- new: named constants ---
        ("floor(2 * pi)", 6),
        ("floor(tau)", 6),
        # --- nested / "complicated" combinations ---
        ("2 ** 10 + factorial(4)", 1048),
        ("sqrt(144) + 5!", 132),
        ("gcd(comb(6, 2), 9)", 3),
    ],
)
def test_complicated_formulas(text: str, expected: int) -> None:
    assert parse_message(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "not a number",
        "sqrt(16",  # unbalanced
        "!5",  # factorial without operand
        "frobnicate(5)",  # unknown function
        "[1, 2, 3]",  # disallowed syntax
    ],
)
def test_invalid_input_returns_none(text: str) -> None:
    assert parse_message(text) is None


@pytest.mark.parametrize(
    "text",
    [
        "2 ** 999999999",  # exponent blows past the cap
        "factorial(999999)",  # factorial argument past the cap
        "9 ** 9 ** 9",  # nested power tower (right-associative)
    ],
)
def test_dos_guards_reject_without_hanging(text: str) -> None:
    """Crafted blow-up expressions must return None quickly, not hang."""
    start = time.monotonic()
    assert parse_message(text) is None
    assert time.monotonic() - start < 1.0


def test_pow_cap_boundary() -> None:
    # Exactly at the limit is allowed; one past it is rejected.
    assert parse_message(f"2 ** {_constants.MAX_POW_EXPONENT}") is not None
    assert parse_message(f"2 ** {_constants.MAX_POW_EXPONENT + 1}") is None


def test_factorial_cap_boundary() -> None:
    assert parse_message(f"factorial({_constants.MAX_FACTORIAL})") is not None
    assert parse_message(f"factorial({_constants.MAX_FACTORIAL + 1})") is None
