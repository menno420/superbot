"""Pure, common-word-safe BTD6 name and number matching for the answer guard.

stdlib only — unit-testable in isolation. Mirrors the canonical/alias
discipline the task router already uses in
``ai_task_router._get_entity_aliases``: canonical proper names are matched
whole-word (single tokens) or as substrings (multi-word phrases), while
generic aliases are length-filtered and stop-listed so ordinary English words
(``ice``, ``dart``, ``ace``) are never treated as BTD6 proper-name evidence.

The caller (the grounding service) is responsible for passing a *safe* set of
names — e.g. it does not pass single-word bloon colours ("Red", "Blue") as
single tokens. This module only performs the mechanical split + matching.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

# Short alias/token forms that collide with ordinary English or chat. Even
# when they survive the length filter they must never count as proper-name
# evidence. Kept small and explicit.
_ALIAS_STOPLIST: frozenset[str] = frozenset(
    {
        "ace",
        "ice",
        "dart",
        "bomb",
        "tack",
        "glue",
        "boat",
        "sub",
        "gun",
        "hero",
        "tower",
        "round",
        "boss",
        "race",
        "event",
        "camo",
        "lead",
        "pink",
        "blue",
        "black",
        "white",
        "green",
        "purple",
        "yellow",
    },
)

_WORD_RE = re.compile(r"[a-z0-9]+")
_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


@dataclass(frozen=True)
class NameMatchers:
    """Compiled matchers: multi-word phrases (substring) + single tokens."""

    multi: frozenset[str]
    single: frozenset[str]


def build_matchers(
    canonicals: Iterable[str],
    aliases: Iterable[str],
) -> NameMatchers:
    """Split names into multi-word (substring) and single-token matchers.

    * Canonicals are proper nouns: single-word forms are kept at length >= 3
      (so distinctive short hero names like ``Psi`` / ``Adora`` survive),
      multi-word forms become substring phrases.
    * Aliases are generic: single-word forms are kept only at length > 4 and
      when not stop-listed (mirrors the router's ``len(al) > 4`` rule).

    Stop-listed tokens are removed from the single set unconditionally, even if
    they arrived as a (short) canonical.
    """
    multi: set[str] = set()
    single: set[str] = set()

    for raw in canonicals:
        name = (raw or "").strip().lower()
        if not name:
            continue
        if " " in name:
            multi.add(name)
        elif len(name) >= 3:
            single.add(name)

    for raw in aliases:
        alias = (raw or "").strip().lower()
        if not alias:
            continue
        if " " in alias:
            multi.add(alias)
        elif len(alias) > 4 and alias not in _ALIAS_STOPLIST:
            single.add(alias)

    single -= _ALIAS_STOPLIST
    return NameMatchers(multi=frozenset(multi), single=frozenset(single))


def names_present(text: str, matchers: NameMatchers) -> set[str]:
    """All indexed names that appear in ``text`` (whole-word + substring)."""
    lowered = (text or "").lower()
    found: set[str] = {phrase for phrase in matchers.multi if phrase in lowered}
    if matchers.single:
        tokens = set(_WORD_RE.findall(lowered))
        found |= tokens & matchers.single
    return found


def multiword_names_present(text: str, matchers: NameMatchers) -> set[str]:
    """Only the multi-word indexed names present in ``text``.

    Multi-word BTD6 proper names (every paragon, most towers) are distinctive
    enough to trigger the general-path guard on their own, without a separate
    BTD6 context keyword.
    """
    lowered = (text or "").lower()
    return {phrase for phrase in matchers.multi if phrase in lowered}


def normalize_numbers(text: str) -> set[str]:
    """Canonical numeric tokens in ``text``, thousands-separators stripped.

    ``"48,210"`` and ``"48210"`` normalize to the same token so a grounded
    comma-formatted value matches an answer that drops the comma (or vice
    versa). Decimals are preserved.
    """
    return {match.replace(",", "") for match in _NUMBER_RE.findall(text or "")}


def offending_numbers(answer: str, haystack: str) -> tuple[str, ...]:
    """Numeric tokens in ``answer`` not present in ``haystack``.

    Comma-normalized on both sides (so a grounded ``48,210`` covers an answer's
    ``48210``). Uses a **substring** test, not exact-token membership — this
    deliberately mirrors the leniency of
    :func:`core.runtime.ai.safety.claims_are_grounded` so list markers and short
    integers that appear inside a larger grounded number (``"5000"`` inside
    ``"150000"``) do not false-positive. The trade is a known residual: a
    fabricated number that is a substring of a real one passes.
    """
    hay = (haystack or "").replace(",", "")
    out: list[str] = []
    for raw in _NUMBER_RE.findall(answer or ""):
        token = raw.replace(",", "")
        if token and token not in hay:
            out.append(token)
    return tuple(out)


__all__ = [
    "NameMatchers",
    "build_matchers",
    "names_present",
    "multiword_names_present",
    "normalize_numbers",
    "offending_numbers",
]
