"""Message → integer parser for the counting game.

Every function in this module is a pure function: no instance state,
no Discord types.  Tests can call them directly without spinning up a
cog.

The pipeline ``parse_message(content)`` accepts any user-typed string
and returns either an integer count or ``None`` (unrecognised input).
It tolerates word numbers ("twenty-one"), phrases ("a dozen"), Roman
numerals, emojis, and arithmetic expressions ("3 + 4 = 7").

Expressions go well beyond the four basic operators: alongside
``+ - * /`` it understands integer/float division (``//``), modulo
(``%``), exponentiation (``**`` / ``^``), postfix factorial (``5!``),
named constants (``pi``, ``e``, ``tau``), and a whitelist of math
functions (``sqrt``, ``floor``, ``gcd``, ``comb``, ``min``/``max``, …
— see ``_constants.MATH_FUNCTIONS``).  Evaluation walks a hardened AST
(never ``eval``); exponentiation and factorial are bounded so a crafted
message cannot stall the on_message hot path.

Originally adopted from the previous CountingCog instance methods of
the same names (only ``self`` was removed); later extended with the
function / constant / factorial support described above.
"""

from __future__ import annotations

import ast
import difflib
import logging
import re
from typing import Any

from cogs.counting._constants import (
    EMOJI_NUMBER_MAPPING,
    MATH_CONSTANTS,
    MATH_FUNCTIONS,
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

    # Define all operator symbols, including '×' and 'x'.  ',' separates
    # function arguments, '%' is modulo, and '!' is postfix factorial.
    operator_symbols = "+-*/^()=.×x,%!"

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
        elif lower_token in MATH_FUNCTIONS:
            # A function name (``sqrt``, ``gcd``, …).  Flush any pending
            # number words, then emit the name so the AST sees an ast.Call.
            if number_word_tokens:
                number_word_str = " ".join(number_word_tokens)
                number = parse_number_word(number_word_str)
                if number is None:
                    return None
                processed_tokens.append(str(number))
                number_word_tokens = []
                prev_token_type = "number"
            if prev_token_type == "number":
                processed_tokens.append("+")
            processed_tokens.append(lower_token)
            prev_token_type = "function"
        elif lower_token in MATH_CONSTANTS:
            # A named constant (``pi``, ``e``, ``tau``) — behaves like a number.
            if number_word_tokens:
                number_word_str = " ".join(number_word_tokens)
                number = parse_number_word(number_word_str)
                if number is None:
                    return None
                processed_tokens.append(str(number))
                number_word_tokens = []
            if prev_token_type == "number":
                processed_tokens.append("+")
            processed_tokens.append(lower_token)
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


def eval_expr(expr: str) -> int | float | None:
    """Safely evaluate an arithmetic expression.  Returns a number or None.

    Supports ``+ - * / // % ** ^``, parentheses, postfix factorial (``5!``),
    named constants (``pi``, ``e``, ``tau``), and the whitelisted callables in
    ``MATH_FUNCTIONS`` (``sqrt``, ``gcd``, ``comb``, …).  Evaluation is done
    over a hardened AST walk — never ``eval`` — and exponentiation / factorial
    are bounded so a crafted message cannot stall the event loop.
    """
    try:
        expr = expr.replace(" ", "")
        # Coarse gate: lowercase letters (function/constant names) plus the
        # arithmetic symbols.  The AST walk below is the real safety boundary.
        if not re.match(r"^[0-9a-z+\-*/^%!().,=]+$", expr):
            return None
        if len(expr) > 120:
            return None
        if "=" in expr:
            left_expr, right_expr = expr.split("=", 1)
            left_val = safe_eval(left_expr)
            right_val = safe_eval(right_expr)
            if left_val is not None and left_val == right_val:
                return right_val
            return None
        return safe_eval(expr)
    except Exception as exc:
        logger.error("Error evaluating expression %r: %s", expr, exc)
        return None


def safe_eval(expr: str) -> int | float | None:
    """Parse + evaluate ``expr`` via the AST whitelist in OPERATORS."""
    try:
        expr = _expand_factorials(expr)
        node = ast.parse(expr, mode="eval").body
        return _eval_ast(node)
    except Exception as exc:
        logger.error("Error in safe_eval with expression %r: %s", expr, exc)
        return None


def _expand_factorials(expr: str) -> str:
    """Rewrite postfix factorial (``5!``, ``(2+3)!``) into ``factorial(...)``.

    Python's grammar has no ``!`` operator, so the postfix form is desugared
    to a call before ``ast.parse`` sees it.  The factorial binds to the
    immediately preceding number or parenthesised group; ``5!!`` becomes
    ``factorial(factorial(5))``.
    """
    while "!" in expr:
        idx = expr.index("!")
        end = idx  # operand is expr[start:end]
        if end == 0:
            raise ValueError("'!' has no operand")
        if expr[end - 1] == ")":
            # Walk back over the balanced parenthesised group.
            depth = 0
            k = end - 1
            while k >= 0:
                if expr[k] == ")":
                    depth += 1
                elif expr[k] == "(":
                    depth -= 1
                    if depth == 0:
                        break
                k -= 1
            if depth != 0:
                raise ValueError("unbalanced parentheses before '!'")
            start = k
        else:
            # Walk back over a run of digits / decimal point.
            k = end - 1
            while k >= 0 and (expr[k].isdigit() or expr[k] == "."):
                k -= 1
            start = k + 1
            if start == end:
                raise ValueError("'!' has no numeric operand")
        operand = expr[start:end]
        expr = f"{expr[:start]}factorial({operand}){expr[idx + 1 :]}"
    return expr


def _eval_ast(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Num):  # Python < 3.8 compat
        return node.n
    if isinstance(node, ast.Name):
        if node.id in MATH_CONSTANTS:
            return MATH_CONSTANTS[node.id]
        raise NameError(f"Unknown name: {node.id}")
    if isinstance(node, ast.Call):
        if node.keywords or not isinstance(node.func, ast.Name):
            raise TypeError("Unsupported call")
        func = MATH_FUNCTIONS.get(node.func.id)
        if func is None:
            raise NameError(f"Unknown function: {node.func.id}")
        args = [_eval_ast(arg) for arg in node.args]
        return func(*args)
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
