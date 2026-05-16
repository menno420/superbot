"""Constants for the counting parser.

Every dict / set / regex / operator-table the parser consults lives
here as a module-level constant — there is no instance state, so the
parser is a pure-function pipeline.
"""

from __future__ import annotations

import ast
import operator as op
import re

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

# AST node type → Python operator.  Used by ``parsing.eval_expr``.
OPERATORS: dict[type, object] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.BitXor: op.pow,  # allow '^' as exponentiation
    ast.USub: op.neg,
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
