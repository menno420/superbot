"""Constants for the counting parser.

Every dict / set / regex / operator-table the parser consults lives
here as a module-level constant — there is no instance state, so the
parser is a pure-function pipeline.
"""

from __future__ import annotations

import ast
import math
import operator as op
import re
from collections.abc import Callable
from typing import Any

# Compiled regex patterns
NUMBER_PATTERN = re.compile(r"\d+")
WORD_PATTERN = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety|hundred|thousand|million|billion|trillion|"
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
    r"eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|"
    r"seventeenth|eighteenth|nineteenth|twentieth)\b",
    re.IGNORECASE,
)

NUMBER_WORDS_SET: frozenset[str] = frozenset(
    {
        # Cardinal numbers
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
        "twenty",
        "thirty",
        "forty",
        "fifty",
        "sixty",
        "seventy",
        "eighty",
        "ninety",
        "hundred",
        "thousand",
        "million",
        "billion",
        "trillion",
        # Ordinal numbers
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "eighth",
        "ninth",
        "tenth",
        "eleventh",
        "twelfth",
        "thirteenth",
        "fourteenth",
        "fifteenth",
        "sixteenth",
        "seventeenth",
        "eighteenth",
        "nineteenth",
        "twentieth",
    },
)

PHRASE_NUMBER_MAPPING: dict[str, int] = {
    "a couple": 2,
    "a few": 3,
    "several": 7,
    "a dozen": 12,
    "half a dozen": 6,
    "a half dozen": 6,
    "a bakers dozen": 13,
    "a score": 20,
    "a gross": 144,
    "a hundred": 100,
    "a thousand": 1000,
    "a million": 1000000,
    "one million": 1000000,
    "a billion": 1000000000,
    "one billion": 1000000000,
}

ORDINAL_MAPPING: dict[str, int] = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
    "thirteenth": 13,
    "fourteenth": 14,
    "fifteenth": 15,
    "sixteenth": 16,
    "seventeenth": 17,
    "eighteenth": 18,
    "nineteenth": 19,
    "twentieth": 20,
}

ROMAN_NUMERAL_MAPPING: dict[str, int] = {
    "I": 1,
    "IV": 4,
    "V": 5,
    "IX": 9,
    "X": 10,
    "XL": 40,
    "L": 50,
    "XC": 90,
    "C": 100,
    "CD": 400,
    "D": 500,
    "CM": 900,
    "M": 1000,
}

EMOJI_NUMBER_MAPPING: dict[str, str] = {
    "0️⃣": "0",
    "1️⃣": "1",
    "2️⃣": "2",
    "3️⃣": "3",
    "4️⃣": "4",
    "5️⃣": "5",
    "6️⃣": "6",
    "7️⃣": "7",
    "8️⃣": "8",
    "9️⃣": "9",
    "🔟": "10",
}

# ---------------------------------------------------------------------------
# DoS guards.  The parser runs on the on_message hot path for every message
# in a counting channel, so a single crafted expression must never be able
# to burn CPU or RAM.  Exponentiation and factorial are the only operations
# that grow super-linearly in the size of their (small) operands, so both
# are routed through bounded wrappers.  Everything else is linear in the
# (length-capped) expression and needs no guard.
# ---------------------------------------------------------------------------
MAX_POW_EXPONENT = 1000  # reject ``a ** b`` / ``a ^ b`` when ``abs(b)`` exceeds this
MAX_FACTORIAL = 1000  # reject ``n!`` / ``factorial(n)`` when ``n`` exceeds this


def safe_pow(base: Any, exponent: Any) -> Any:
    """``base ** exponent`` with a bound on the exponent.

    Without this, ``9 ^ 9 ^ 9`` (right-associative) asks Python to build a
    ~370-million-digit integer and hangs the event loop.  Capping the
    exponent magnitude keeps every power bounded; nested towers are caught
    because each inner power is evaluated (and bounded) before it becomes the
    exponent of the next one.
    """
    if abs(exponent) > MAX_POW_EXPONENT:
        raise ValueError(f"exponent {exponent!r} exceeds limit {MAX_POW_EXPONENT}")
    return op.pow(base, exponent)


def safe_factorial(n: Any) -> int:
    """``math.factorial`` with a bound, rejecting non-integers and negatives."""
    if isinstance(n, float):
        if not n.is_integer():
            raise ValueError("factorial of a non-integer")
        n = int(n)
    if not isinstance(n, int):
        raise TypeError("factorial expects an integer")
    if n < 0 or n > MAX_FACTORIAL:
        raise ValueError(f"factorial argument {n} outside 0..{MAX_FACTORIAL}")
    return math.factorial(n)


# AST node type → Python operator.  Used by ``parsing.eval_expr``.
OPERATORS: dict[type, Callable[..., Any]] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: safe_pow,
    ast.BitXor: safe_pow,  # allow '^' as exponentiation
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

# Named constants usable in expressions, e.g. ``2 * pi`` or ``tau / 4``.
MATH_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def _signum(x: Any) -> int:
    return (x > 0) - (x < 0)


def _cbrt(x: Any) -> float:
    # ``x ** (1/3)`` returns a complex number for negative x; preserve sign.
    return math.copysign(abs(x) ** (1.0 / 3.0), x)


# Whitelisted callables.  Only alphabetic names are usable: the tokenizer
# splits a letter+digit run such as ``log2`` into ``log`` + ``2``, so any
# function with a digit in its name is unreachable from user input by design.
# Variadic builtins (min/max/sum) are wrapped so they accept positional args.
MATH_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "abs": abs,
    "round": lambda x, ndigits=0: round(x, int(ndigits)),
    "min": lambda *args: min(args),
    "max": lambda *args: max(args),
    "sum": lambda *args: sum(args),
    "sqrt": math.sqrt,
    "cbrt": _cbrt,
    "factorial": safe_factorial,
    "floor": math.floor,
    "ceil": math.ceil,
    "trunc": math.trunc,
    "sign": _signum,
    "exp": math.exp,
    "ln": math.log,
    "log": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "degrees": math.degrees,
    "radians": math.radians,
    "gcd": math.gcd,
    "lcm": math.lcm,
    "hypot": math.hypot,
    "pow": safe_pow,
    "comb": math.comb,
    "perm": math.perm,
    "fmod": math.fmod,
}

# Word/symbol → arithmetic operator replacement.
OPERATOR_MAPPING: dict[str, str] = {
    "plus": "+",
    "minus": "-",
    "times": "*",
    "multipliedby": "*",
    "multiplied": "*",
    "multiply": "*",
    "x": "*",
    "×": "*",
    "dividedby": "/",
    "divided": "/",
    "divide": "/",
    "over": "/",
    "powerof": "**",
    "tothepowerof": "**",
    "mod": "%",
    "modulo": "%",
    "equals": "=",
    "equal": "=",
    "and": "+",
}


def word_to_num(text: str) -> int | None:
    """Minimal word-to-number converter (replaces the word2number package)."""
    _ONES = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
    }
    _TENS = {
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }
    _MAGNITUDES = {
        "thousand": 1_000,
        "million": 1_000_000,
        "billion": 1_000_000_000,
        "trillion": 1_000_000_000_000,
    }
    words = text.lower().split()
    if not words:
        return None
    result = 0
    current = 0
    for word in words:
        if word == "and":
            continue
        if word in _ONES:
            current += _ONES[word]
        elif word in _TENS:
            current += _TENS[word]
        elif word == "hundred":
            current = (current or 1) * 100
        elif word in _MAGNITUDES:
            result += (current or 1) * _MAGNITUDES[word]
            current = 0
        else:
            return None
    return result + current
