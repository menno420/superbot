"""Canonical BTD6 bloon identifiers and name normalisation.

The same bloon is named differently across sources: the ``btd6_bloons`` Cargo
table ("Moab", "DynamiteBloon"), the wiki link text in a parent's children list
("[[Ceramic Bloon (BTD6)|Ceramic Bloon]]"), and (PR3) the round module's spawn
keys. This module maps them all onto one stable id set so bloon children and
round composition join cleanly — PR3 must not invent a second naming scheme.

Pure / stdlib-only — safe for every layer (utils -> services / scripts).
"""

from __future__ import annotations

import re

# Modifier prefixes that decorate a bloon rather than name a distinct one.
MODIFIER_TOKENS: tuple[str, ...] = ("camo", "regrow", "fortified")

# The five basic (coloured) bloons — used to classify a bloon's category.
BASIC_IDS: tuple[str, ...] = ("red", "blue", "green", "yellow", "pink")

# MOAB-class blimp ids.
MOAB_IDS: tuple[str, ...] = ("moab", "bfb", "zomg", "ddt", "bad")

_DISAMBIG_RE = re.compile(r"\(\s*btd\s*6\s*\)", re.I)
# [[target|Display]] -> Display
_LINK_PIPED_RE = re.compile(r"\[\[[^\]|]*\|([^\]]+)\]\]")
# [[Display]] -> Display
_LINK_BARE_RE = re.compile(r"\[\[([^\]]+)\]\]")


def strip_links(text: str) -> str:
    """Reduce wiki link markup to its display text."""
    return _LINK_BARE_RE.sub(r"\1", _LINK_PIPED_RE.sub(r"\1", text))


def normalize_bloon_name(name: str) -> str:
    """Map a wiki bloon name / link text / Cargo id to a canonical id.

    e.g. ``"Black Bloon"``, ``"[[Black Bloon (BTD6)|Black Bloon]]"`` and
    ``"Black"`` all map to ``"black"``; ``"ZOMG"`` -> ``"zomg"``;
    ``"DynamiteBloon"`` -> ``"dynamite"``.
    """
    s = strip_links(str(name))
    s = _DISAMBIG_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    if s.endswith(" bloon"):
        s = s[: -len(" bloon")]
    elif s.endswith("bloon") and s != "bloon":
        s = s[: -len("bloon")]
    return s.strip()


# Modifier suffixes as they appear (CamelCase) in round-module spawn keys.
_ROUND_MODIFIER_SUFFIXES = ("Camo", "Regrow", "Fortified")


def parse_round_bloon_key(key: str) -> tuple[str, list[str]]:
    """Split a round-module spawn key into (canonical id, modifiers).

    e.g. ``"LeadFortifiedCamo"`` -> ``("lead", ["fortified", "camo"])``;
    ``"CeramicRegrowFortifiedCamo"`` -> ``("ceramic", ["regrow", "fortified", "camo"])``.
    """
    remaining = str(key)
    modifiers: list[str] = []
    changed = True
    while changed:
        changed = False
        for suffix in _ROUND_MODIFIER_SUFFIXES:
            if remaining.endswith(suffix) and len(remaining) > len(suffix):
                modifiers.append(suffix.lower())
                remaining = remaining[: -len(suffix)]
                changed = True
    modifiers.reverse()  # stripped from the end -> restore source order
    return normalize_bloon_name(remaining), modifiers


__all__ = [
    "BASIC_IDS",
    "MOAB_IDS",
    "MODIFIER_TOKENS",
    "normalize_bloon_name",
    "parse_round_bloon_key",
    "strip_links",
]
