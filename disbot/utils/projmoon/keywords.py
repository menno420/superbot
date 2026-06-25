"""Curated Project Moon (Limbus) context keywords.

The detector :func:`has_limbus_context` answers "does this message look like it's
about Limbus Company?" — used by the browse surface today and, in a later PR, by
the AI task router + the answer-faithfulness guard (the BTD6 ``has_btd6_context``
pattern). Kept in ``utils`` (stdlib only) so every layer can read **one** list
with no drift, exactly like :mod:`utils.btd6.keywords`.

Curated to avoid over-routing: the bare Sin words ``pride`` / ``sloth`` /
``gluttony`` / ``envy`` / ``wrath`` / ``lust`` / ``gloom`` are deliberately
**absent** (ordinary English), as are ambiguous status words (``burn``,
``charge``, ``haste``, ``poise``, ``bleed``). Routing on those would over-trigger;
a real Limbus question almost always also carries a distinctive token (``limbus``,
``sinner``, ``e.g.o``, a Sephirah grade, a distinctive Sinner name) or names a
resolvable entity, which the entity resolver covers.
"""

from __future__ import annotations

import re

# Distinctive, low-false-positive tokens. Each is matched on word boundaries.
LIMBUS_CONTEXT_KEYWORDS: tuple[str, ...] = (
    "limbus",
    "sinner",
    "sinners",
    "e.g.o",
    "ego grade",
    "mirror dungeon",
    "intervallo",
    # E.G.O / risk grades (Sephirah names) — distinctive in this context.
    "zayin",
    "teth",
    "waw",
    "aleph",
    # Distinctive Sinner proper names (the ambiguous "faust"/"don" rely on the
    # resolver + a co-occurring token, not this bare list).
    "yi sang",
    "ryoshu",
    "ryōshū",
    "meursault",
    "hong lu",
    "heathcliff",
    "ishmael",
    "rodion",
    "sinclair",
    "outis",
    "gregor",
    "don quixote",
)

_KEYWORD_RE = re.compile(
    r"(?<![\w.])(?:"
    + "|".join(re.escape(k) for k in LIMBUS_CONTEXT_KEYWORDS)
    + r")(?![\w])",
    re.IGNORECASE,
)


def has_limbus_context(text: str) -> bool:
    """True when ``text`` carries a distinctive Limbus Company token."""
    if not text:
        return False
    return _KEYWORD_RE.search(text) is not None
