"""Message → integer parser for the counting game.

Every function in this module is a pure function: no instance state,
no Discord types.  Tests can call them directly without spinning up a
cog.

The pipeline ``parse_message(content)`` accepts any user-typed string
and returns either an integer count or ``None`` (unrecognised input).
It tolerates word numbers ("twenty-one"), phrases ("a dozen"), Roman
numerals, emojis, and arithmetic expressions ("3 + 4 = 7").

Adopted from the previous CountingCog instance methods of the same
names.  Behaviour is preserved exactly; only ``self`` was removed.
"""

from __future__ import annotations

import ast
import difflib
import logging
import re

from cogs.counting._constants import (
    EMOJI_NUMBER_MAPPING,
    NUMBER_WORDS_SET,
    OPERATOR_MAPPING,
    OPERATORS,
    ORDINAL_MAPPING,
    PHRASE_NUMBER_MAPPING,
    ROMAN_NUMERAL_MAPPING,
    word_to_num,
)

logger = logging.getLogger("CountingCog.parsing")


def parse_message(content: str) -> int | None:
    """Parse user-typed text and return the embedded number, or None."""
    content = content.strip().lower()

    # Replace phrases with their numeric equivalents
    for phrase, num in PHRASE_NUMBER_MAPPING.items():
        pattern = r"\b" + re.escape(phrase) + r"\b"
        content = re.sub(pattern, str(num), content)

    # Replace number emotes with their numeric equivalents
    for emote, num_str in EMOJI_NUMBER_MAPPING.items():
        content = content.replace(emote, num_str)

    # Replace hyphens within words (e.g. "twenty-one") with spaces
    # but keep hyphens used as operators intact.
    content = re.sub(r"(?<=[a-zA-Z])-(?=[a-zA-Z])", " ", content)

    # Split concatenated number words
    content = split_concatenated_numbers(content)

    # Define all operator symbols, including '×' and 'x'
    operator_symbols = "+-*/^()=.×x"

    # Tokenize the content into numbers, words, and operators
    tokens = re.findall(r"\d+|[^\W\d_]+|[^\w\s]", content, re.UNICODE)

    processed_tokens: list[str] = []
    number_word_tokens: list[str] = []
    prev_token_type: str | None = None

    for token in tokens:
        lower_token = token.lower()

        if lower_token in OPERATOR_MAPPING or token in operator_symbols:
            if number_word_tokens:
                number_word_str = " ".join(number_word_tokens)
                number = parse_number_word(number_word_str)
                if number is None:
                    return None
                processed_tokens.append(str(number))
                number_word_tokens = []
                prev_token_type = "number"
            if lower_token in OPERATOR_MAPPING:
                processed_tokens.append(OPERATOR_MAPPING[lower_token])
            else:
                processed_tokens.append(token)
            prev_token_type = "operator"
        elif lower_token.isdigit() or token.isdigit():
            if number_word_tokens:
                number_word_str = " ".join(number_word_tokens)
                number = parse_number_word(number_word_str)
                if number is None:
                    return None
                processed_tokens.append(str(number))
                number_word_tokens = []
            if prev_token_type == "number":
                processed_tokens.append("+")
            processed_tokens.append(token)
            prev_token_type = "number"
        elif lower_token in NUMBER_WORDS_SET:
            number_word_tokens.append(lower_token)
            prev_token_type = "number_word"
        else:
            # Try fuzzy matching for misspellings
            close_matches = difflib.get_close_matches(
                lower_token,
                NUMBER_WORDS_SET,
                n=1,
                cutoff=0.8,
            )
            if close_matches:
                number_word_tokens.append(close_matches[0])
                prev_token_type = "number_word"
            else:
                roman_value = roman_to_int(lower_token.upper())
                if roman_value is not None:
                    if prev_token_type == "number":
                        processed_tokens.append("+")
                    processed_tokens.append(str(roman_value))
                    prev_token_type = "number"
                else:
                    return None

    if number_word_tokens:
        number_word_str = " ".join(number_word_tokens)
        number = parse_number_word(number_word_str)
        if number is None:
            return None
        processed_tokens.append(str(number))

    expr = "".join(processed_tokens)
    result = eval_expr(expr)
    if result is not None:
        return int(result)
    return None


def parse_number_word(text: str) -> int | None:
    """Resolve a number word or ordinal to its integer value."""
    lower = text.lower()
    if lower in ORDINAL_MAPPING:
        return ORDINAL_MAPPING[lower]
    return word_to_num(lower)


def split_concatenated_numbers(text: str) -> str:
    """Insert spaces between concatenated number words (e.g. ``twentyone``)."""
    text_lower = text.lower()
    result = ""
    i = 0
    while i < len(text_lower):
        match_found = False
        for j in range(len(text_lower), i, -1):
            substr = text_lower[i:j]
            if substr in NUMBER_WORDS_SET:
                result += substr + " "
                i = j - 1
                match_found = True
                break
        if not match_found:
            result += text_lower[i]
        i += 1
    return result


def roman_to_int(s: str) -> int | None:
    """Convert a Roman numeral string to integer, or None if invalid."""
    i = 0
    num = 0
    while i < len(s):
        if i + 1 < len(s) and s[i : i + 2] in ROMAN_NUMERAL_MAPPING:
            num += ROMAN_NUMERAL_MAPPING[s[i : i + 2]]
            i += 2
        elif s[i] in ROMAN_NUMERAL_MAPPING:
            num += ROMAN_NUMERAL_MAPPING[s[i]]
            i += 1
        else:
            return None
    return num


def eval_expr(expr: str) -> int | None:
    """Safely evaluate a basic arithmetic expression.  Returns int or None."""
    try:
        expr = expr.replace(" ", "")
        if not re.match(r"^[0-9+\-*/^().=]+$", expr):
            return None
        if len(expr) > 50:
            return None
        if "=" in expr:
            left_expr, right_expr = expr.split("=", 1)
            left_val = safe_eval(left_expr)
            right_val = safe_eval(right_expr)
            if left_val == right_val:
                return right_val
            return None
        return safe_eval(expr)
    except Exception as exc:
        logger.error("Error evaluating expression %r: %s", expr, exc)
        return None


def safe_eval(expr: str) -> int | None:
    """Parse + evaluate ``expr`` via the AST whitelist in OPERATORS."""
    try:
        node = ast.parse(expr, mode="eval").body
        return _eval_ast(node)
    except Exception as exc:
        logger.error("Error in safe_eval with expression %r: %s", expr, exc)
        return None


def _eval_ast(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Num):  # Python < 3.8 compat
        return node.n
    if isinstance(node, ast.BinOp):
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        operator = OPERATORS.get(type(node.op))
        if operator is None:
            raise TypeError(f"Unsupported operator: {node.op}")
        return operator(left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _eval_ast(node.operand)
        operator = OPERATORS.get(type(node.op))
        if operator is None:
            raise TypeError(f"Unsupported operator: {node.op}")
        return operator(operand)
    raise TypeError(f"Unsupported expression: {node}")
