"""BTD6 damage-type & status-effect INTERACTION grounding.

Answers the "can tower X deal with bloon Y?" class of question — the single most
error-prone BTD6 topic for the model. The per-bloon ``immune_to`` lists in
``bloons.json`` are game-sourced and authoritative, but they are handed to the
model *separately* from the tower descriptions, so the model invents the
interaction rule (a live screenshot had it claim *"Lead resists glue"* — false;
glue is a status effect that ignores damage-type immunity).

This module loads the curated ``damage_types.json`` (verified against the
game-sourced ``immune_to`` data, see the cross-check test) and emits explicit
grounding facts when a message asks an interaction question: a damage type, a
status effect (glue / ice / knockback / stun), or a bloon property (Lead / Black
/ Camo / DDT / MOAB-class …) named alongside an interaction cue ("pop", "deal
with", "immune", "work on", "vs" …).

Read-only, no DB, no network. Backs a new isolated grounding pass in
:mod:`services.btd6_context_service`.
"""

from __future__ import annotations

import re
from typing import Any

from services import btd6_data_service

_DATA_FILE = "damage_types.json"
_SOURCE = "BTD6 damage-type interaction data (wiki-verified)"

# Module-level cache of the parsed data file (sibling of the dataset cache).
_CACHE: dict[str, Any] | None = None

# Most facts a single interaction question should ground — keeps a broad
# "what pops everything" question from flooding the context window.
_MAX_FACTS = 6

# An interaction-question cue (genuine VERBS only). The named entity (damage
# type / status / property) is the primary gate; this verb gate keeps lookups
# like "how much does glue gunner cost" or "what does the bomb shooter do" from
# grounding interaction facts. Deliberately excludes the entity-name words
# "glue"/"freeze" (a status effect IS named "glue", so it cannot also be the
# verb that proves an interaction question) — those fire only via the
# two-entities-named pairing below. "vs"/"against" double as the no-verb pairing
# signal ("sharp vs lead").
_INTERACTION_CUE_RE = re.compile(
    r"\b(?:pop|pops|popped|popping|deal|deals|dealt|handle|handles|counter|"
    r"counters|work|works|working|affect|affects|hit|hits|immune|immunit|"
    r"resist|resists|resistant|resistance|weak|beat|beats|stop|stops|slow|"
    r"slows|knock|able\s+to|against|vs|versus|"
    r"good\s+(?:against|vs|into)|effective|useless|bypass)\b",
    re.I,
)

# Property/bloon match tokens for the pop_guide entries (kept here, not in the
# JSON, so the data file stays a clean knowledge table). Order matters only for
# readability; matching is by whole-word alternation per entry.
_POP_GUIDE_TOKENS: dict[str, tuple[str, ...]] = {
    "lead": ("lead", "leads", "lead bloon", "lead bloons"),
    "black": ("black", "blacks", "black bloon", "black bloons"),
    "white": ("white", "whites", "white bloon", "white bloons"),
    "purple": ("purple", "purples", "purple bloon", "purple bloons"),
    "zebra": ("zebra", "zebras", "zebra bloon", "zebra bloons"),
    "camo": ("camo", "camos", "camo bloon", "camo bloons", "camouflage"),
    "frozen": ("frozen", "frozen bloon", "frozen bloons"),
    "moab_class": (
        "moab-class",
        "moab class",
        "moabclass",
        "moab",
        "moabs",
        "blimp",
        "blimps",
    ),
    "ddt": ("ddt", "ddts", "dark dirigible titan"),
}


def _load() -> dict[str, Any]:
    """Parse + cache ``damage_types.json`` (empty-safe when the file is absent)."""
    global _CACHE
    if _CACHE is None:
        raw = btd6_data_service.read_blob(_DATA_FILE)
        _CACHE = raw if isinstance(raw, dict) else {}
    return _CACHE


def reset_cache() -> None:
    """Drop the cached data (test seam / provider swap)."""
    global _CACHE
    _CACHE = None


def _word_re(token: str) -> re.Pattern[str]:
    return re.compile(rf"\b{re.escape(token)}\b", re.I)


def _alias_hit(entry: dict[str, Any], text_lower: str) -> bool:
    for alias in entry.get("aliases", ()):
        if _word_re(str(alias)).search(text_lower):
            return True
    return False


def _pop_guide_hit(entry: dict[str, Any], text_lower: str) -> bool:
    for token in _POP_GUIDE_TOKENS.get(str(entry.get("id", "")), ()):
        if _word_re(token).search(text_lower):
            return True
    return False


def _damage_type_fact(entry: dict[str, Any]) -> str:
    blocked = entry.get("blocked_by_properties") or []
    blocked_txt = (
        f"cannot pop {', '.join(blocked)}" if blocked else "pops every bloon type"
    )
    return (
        f"[btd6_damage_type] {entry['name']} damage — {entry.get('summary', '')} "
        f"({blocked_txt}.) (source: {_SOURCE})"
    )


def _status_fact(entry: dict[str, Any]) -> str:
    return (
        f"[btd6_interaction] {entry['name']} is a status effect (not damage) — "
        f"{entry.get('summary', '')} Lead: {entry.get('lead', 'n/a')}. "
        f"MOAB-class: {entry.get('moab_class', 'n/a')}. "
        f"BAD: {entry.get('bad', 'n/a')}. (source: {_SOURCE})"
    )


def _pop_guide_fact(entry: dict[str, Any]) -> str:
    label = entry.get("property", entry.get("id", ""))
    return (
        f"[btd6_interaction] To deal with {label} — needs {entry.get('needs', '')}; "
        f"{entry.get('blocked', '')}. {entry.get('note', '')} (source: {_SOURCE})"
    )


# NOTE: an auto-derived "towers that can damage a DDT" fact was grounded here
# (PR #1492) and reverted — the derivation could not tell that base Ice / Glue
# can't hit MOAB-class (a DDT is MOAB-class, and that capability is NOT in the
# stats), nor that a config is weak, so it grounded wrong recommendations. The
# correct MOAB-class subtlety is curated prose in damage_types.json instead.


def interaction_facts(message_text: str) -> list[str]:
    """Grounding facts for a damage-type / status-effect / property question.

    Fires only on a clear interaction question: a damage type, status effect, or
    bloon property is named AND (an interaction cue is present OR a damage-type +
    property are paired). Returns ``[]`` for plain lookups, cost questions, and
    anything without an interaction shape. Capped at :data:`_MAX_FACTS`.
    """
    text = (message_text or "").strip().lower()
    if not text:
        return []
    data = _load()

    matched_damage = [dt for dt in data.get("damage_types", ()) if _alias_hit(dt, text)]
    matched_status = [s for s in data.get("status_effects", ()) if _alias_hit(s, text)]
    matched_props = [p for p in data.get("pop_guide", ()) if _pop_guide_hit(p, text)]
    if not (matched_damage or matched_status or matched_props):
        return []

    cue = bool(_INTERACTION_CUE_RE.search(text))
    # A damage type + a bloon property named together is itself an interaction
    # question even without an explicit verb ("plasma purple", "sharp lead").
    # Status questions essentially always carry a verb ("does glue work on…",
    # "can ice slow…"), so a status name alone never fires — which also stops a
    # lookup like "tell me about the ice monkey" (where "ice" matches the Cold
    # damage type and "ice monkey" the status) from grounding interaction facts.
    pairing = bool(matched_damage and matched_props)
    if not (cue or pairing):
        return []

    facts: list[str] = []
    for status in matched_status:
        facts.append(_status_fact(status))
    for prop in matched_props:
        facts.append(_pop_guide_fact(prop))
    for damage in matched_damage:
        facts.append(_damage_type_fact(damage))

    # Dedup preserving order, then cap.
    seen: set[str] = set()
    deduped: list[str] = []
    for fact in facts:
        if fact not in seen:
            seen.add(fact)
            deduped.append(fact)
    return deduped[:_MAX_FACTS]


__all__ = ["interaction_facts", "reset_cache"]
