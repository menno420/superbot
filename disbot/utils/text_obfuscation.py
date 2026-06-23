r"""Obfuscation-resistant text matching for the prohibited-words filter.

Pure, stdlib-only, no Discord I/O — so it is exhaustively unit-testable and can
be shared by the cog, a service, or a future API surface (``utils/`` may import
stdlib only).

The problem
-----------
A naive word filter compiles ``re.compile(rf"\\b{word}\\b", IGNORECASE)`` and
matches it against the raw message.  Every mainstream bot (Sapphire, Carl, MEE6,
Dyno) does exactly this, and it is trivially evaded:

* **leetspeak** — ``b4d``, ``a$$``, ``f@ck``
* **unicode confusables** — ``bаd`` (Cyrillic а), ``fμ¢k`` (Greek mu, cent sign)
* **compatibility glyphs** — ``ｂａｄ`` (fullwidth), ``𝐛𝐚𝐝`` (mathematical bold)
* **separator insertion** — ``b a d``, ``b.a.d``, ``b-a-d``
* **invisible-character insertion** — a zero-width space / joiner *between* the
  letters so the word reads normally to a human but no substring matches.

The invisible-character class is the interesting one.  A bot that strips "all
format characters" (Unicode category ``Cf``) catches ``U+200B`` ZERO WIDTH SPACE
and friends — but **misses** the characters that render blank yet are *not*
format characters: HANGUL FILLER ``U+3164`` and the choseong/jungseong fillers
(category ``Lo`` — *letters*), the BRAILLE PATTERN BLANK ``U+2800`` (``So`` — a
*symbol*), HALFWIDTH HANGUL FILLER ``U+FFA0``.  Those slip past category-based
strippers, which is exactly how "passes some advanced bots but not all" works.
We defend with **both** layers: strip the ``Cf``/``Mn``/``Me`` categories *and*
an explicit set of the invisible-but-not-format characters.

The approach
------------
:func:`deobfuscate` normalizes a string to *what a human actually reads* — fold
compatibility glyphs, drop invisibles and combining marks, map confusables, fold
leetspeak (only inside tokens that contain a letter, so a bare number like
``455`` is never turned into ``ass``).  Matching then happens with word
boundaries preserved, so normal prose keeps a low false-positive rate — notably
``therapist`` never matches a banned ``rapist`` because no separator collapse
crosses a real word.  :func:`find_obfuscated_match` returns the first banned word
a message trips, or ``None``.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

# ---------------------------------------------------------------------------
# Invisible / zero-width / combining handling
# ---------------------------------------------------------------------------

# Unicode general categories that are always safe to strip: combining marks
# (accents, zalgo stacks) and format characters (zero-width space/joiner, the
# invisible Unicode tag block U+E0000-E007F, most variation selectors).
_STRIP_CATEGORIES = frozenset({"Mn", "Me", "Cf"})

# Characters that render invisible/blank but are NOT in the categories above —
# a category-only stripper misses these, so we list them explicitly.  This is
# the layer that catches the "passes advanced bots" evasion.
_INVISIBLE = frozenset(
    {
        0x00AD,  # SOFT HYPHEN
        0x115F,  # HANGUL CHOSEONG FILLER          (Lo — a "letter")
        0x1160,  # HANGUL JUNGSEONG FILLER         (Lo)
        0x17B4,  # KHMER VOWEL INHERENT AQ
        0x17B5,  # KHMER VOWEL INHERENT AA
        0x180E,  # MONGOLIAN VOWEL SEPARATOR
        0x200B,  # ZERO WIDTH SPACE
        0x200C,  # ZERO WIDTH NON-JOINER
        0x200D,  # ZERO WIDTH JOINER
        0x2060,  # WORD JOINER
        0x2061,  # FUNCTION APPLICATION  (invisible)
        0x2062,  # INVISIBLE TIMES
        0x2063,  # INVISIBLE SEPARATOR
        0x2064,  # INVISIBLE PLUS
        0x2800,  # BRAILLE PATTERN BLANK            (So — a "symbol")
        0x3164,  # HANGUL FILLER                    (Lo)
        0xFEFF,  # ZERO WIDTH NO-BREAK SPACE / BOM
        0xFFA0,  # HALFWIDTH HANGUL FILLER          (Lo)
    },
)

# Exotic spaces normalized to a plain ASCII space so they read as ordinary
# separators (handled by word boundaries / the spaced-run collapse below).
_UNICODE_SPACES = frozenset(
    {
        0x00A0,  # NO-BREAK SPACE
        0x1680,  # OGHAM SPACE MARK
        0x2000,  # EN QUAD
        0x2001,  # EM QUAD
        0x2002,  # EN SPACE
        0x2003,  # EM SPACE
        0x2004,  # THREE-PER-EM SPACE
        0x2005,  # FOUR-PER-EM SPACE
        0x2006,  # SIX-PER-EM SPACE
        0x2007,  # FIGURE SPACE
        0x2008,  # PUNCTUATION SPACE
        0x2009,  # THIN SPACE
        0x200A,  # HAIR SPACE
        0x202F,  # NARROW NO-BREAK SPACE
        0x205F,  # MEDIUM MATHEMATICAL SPACE
        0x3000,  # IDEOGRAPHIC SPACE
    },
)

# ---------------------------------------------------------------------------
# Confusables (curated Latin look-alikes) and leetspeak
# ---------------------------------------------------------------------------

# Curated homoglyph map — Cyrillic / Greek / symbol look-alikes → Latin.  Keys
# are lower-case (we casefold before mapping, so upper-case look-alikes fold in
# too).  Intentionally conservative: only unambiguous look-alikes, so we do not
# mangle legitimate non-Latin text more than necessary.
_CONFUSABLES: dict[str, str] = {
    # Cyrillic
    "а": "a",
    "е": "e",
    "о": "o",
    "р": "p",
    "с": "c",
    "х": "x",
    "у": "y",
    "ѕ": "s",
    "і": "i",
    "ј": "j",
    "ԁ": "d",
    "һ": "h",
    "к": "k",
    "м": "m",
    "т": "t",
    "ь": "b",
    "ԛ": "q",
    "ԝ": "w",
    "г": "r",
    "п": "n",
    # Greek
    "α": "a",
    "ο": "o",
    "ρ": "p",
    "ν": "v",
    "ι": "i",
    "κ": "k",
    "ε": "e",
    "τ": "t",
    "υ": "u",
    "χ": "x",
    "γ": "y",
    "β": "b",
    "ϲ": "c",
    "μ": "u",
    # Symbol look-alikes
    "¢": "c",
    "€": "e",
    "₤": "l",
    "ø": "o",
    "đ": "d",
    "ł": "l",
}
_CONFUSABLE_TABLE = {ord(k): v for k, v in _CONFUSABLES.items()}

# Leetspeak digit/symbol → letter.  Applied ONLY inside tokens that already
# contain a letter (see :func:`_leet_fold`), so standalone numbers ("455",
# "2026", a price "$5") are never folded into words.
_LEET: dict[str, str] = {
    "4": "a",
    "@": "a",
    "3": "e",
    "1": "i",
    "0": "o",
    "5": "s",
    "$": "s",
    "7": "t",
    "+": "t",
    "8": "b",
    "9": "g",
    "6": "g",
    "2": "z",
}

_NON_WHITESPACE_RUN = re.compile(r"\S+")


def _leet_fold(text: str) -> str:
    """Fold leetspeak, but only within whitespace-delimited tokens that contain
    at least one ASCII letter.

    ``"a55"`` → ``"ass"`` (token has a letter), but ``"455"`` and ``"4 to 3"``
    are left untouched (no letter in those tokens), so a bare number is never
    turned into a word.
    """

    def fold(match: re.Match[str]) -> str:
        run = match.group(0)
        if not any(ch.isalpha() for ch in run):
            return run
        return "".join(_LEET.get(ch, ch) for ch in run)

    return _NON_WHITESPACE_RUN.sub(fold, text)


def deobfuscate(text: str) -> str:
    """Normalize ``text`` to what a human reads — defeating glyph/invisible
    obfuscation while preserving word structure.

    Steps: NFKD compatibility fold (fullwidth/mathematical/ligatures) → drop
    combining marks, format characters, and the explicit invisible set → map
    exotic spaces to a plain space → casefold → map confusables → leet-fold
    (letter-bounded).  Pure and idempotent on already-clean ASCII.
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)

    out: list[str] = []
    for ch in text:
        cp = ord(ch)
        if cp in _INVISIBLE:
            continue
        if unicodedata.category(ch) in _STRIP_CATEGORIES:
            continue
        if cp in _UNICODE_SPACES:
            out.append(" ")
            continue
        out.append(ch)
    text = "".join(out)

    text = text.casefold()
    text = text.translate(_CONFUSABLE_TABLE)
    return _leet_fold(text)


# A run of >= 3 single characters each separated by one-or-more non-word
# characters: "b a d", "b.a.d", "b-a-d".  Bounded to single-char elements (the
# inner ``\w`` are length 1) so normal multi-letter prose ("the rapist") is
# never collapsed — only deliberately spaced-out letters are.
_SPACED_RUN = re.compile(r"\w(?:[\W_]+\w){2,}")


def _collapse_spaced(text: str) -> str:
    """Collapse spaced-out single-character runs so ``"b a d"`` → ``"bad"``."""

    def collapse(match: re.Match[str]) -> str:
        return re.sub(r"[\W_]+", "", match.group(0))

    return _SPACED_RUN.sub(collapse, text)


def find_obfuscated_match(content: str, words: Iterable[str]) -> str | None:
    """Return the first word in ``words`` that ``content`` trips after
    de-obfuscation, or ``None``.

    Each word is matched with word boundaries against two views of the
    de-obfuscated message: the de-obfuscated text itself (catches leet,
    confusables, compatibility glyphs, invisibles) and a spaced-run-collapsed
    copy (catches separator insertion).  The returned value is the *original*
    word from ``words`` (so the caller logs the configured term, not its
    normalized form).
    """
    if not content:
        return None

    norm = deobfuscate(content)
    if not norm:
        return None
    # Collapsing spaced-out runs can form new tokens ("a 5 5" -> "a55"), so
    # re-fold leetspeak on the collapsed view to catch combined evasion.
    collapsed = _collapse_spaced(norm)
    haystacks = (norm, _leet_fold(collapsed)) if collapsed != norm else (norm,)

    for word in words:
        normalized = deobfuscate(word)
        if not normalized:
            continue
        pattern = re.compile(rf"\b{re.escape(normalized)}\b")
        if any(pattern.search(h) for h in haystacks):
            return word
    return None


__all__ = ["deobfuscate", "find_obfuscated_match"]
