"""Project Moon (Limbus) → AI grounding context.

The :func:`build` entry point is the projmoon analogue of
:func:`services.btd6_context_service.build`: it resolves the distinctive Limbus
entities named in a message to provenanced, length-bounded grounding fact lines
that the AI instruction stack injects as ``retrieved_facts``. Read-only over the
committed structural fixtures (:mod:`services.projmoon_data_service`); no I/O, no
DB, no live state — every fact is a patch-stable structural/lore statement.

This is **Slice A item 2** of the Project Moon knowledge-domain plan
(``docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md``, Q-0192): the
grounding path. It deliberately stays tiny. Two later lanes build on it:

* the StaticData *exact-number* ingest (Slice A item 1) appends more facts here;
* the shared ``KnowledgeDomain`` seam (Slice B) folds this + the BTD6 context
  service onto one renderer — at which point the BTD6 grounding-format helpers
  reused below (:mod:`utils.btd6.grounding_format`) move to a domain-agnostic home.

What is **not** here yet (deliberate, documented): the prose-faithfulness
*validation* guard (the plan's §6 "hardest correctness risk"). This slice injects
grounded facts; it does not yet post-verify the model's reply against them the way
``btd6_grounding_service`` does for BTD6. A Limbus reply therefore grounds on these
facts but is not refused for ungrounded prose — that guard is a follow-up slice.

Layering: ``services`` may import ``utils``; this module imports only
``services.projmoon_data_service`` and ``utils`` helpers, never core / cogs / views.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from services import projmoon_data_service
from utils.btd6.grounding_format import sanitise

# Hard upper bound on a single grounding line, before the provenance suffix is
# reserved. Limbus lore lines are richer than the BTD6 default (240), so allow a
# little more room; ``sanitise`` truncates the body so provenance always survives.
_FACT_TEXT_CAP = 400

# Cap on the number of facts a single message can pull, so a roster query (e.g.
# "list every sinner") can't drown the model context. 12 Sinners + a couple of
# named extras fit comfortably.
_MAX_FACTS = 16

# Short, honest provenance — the committed structural fixtures, not a live scrape.
_PROVENANCE = "Limbus Company structural data (committed fixture)"

# Ambiguous bare tokens that are ordinary English (or common Discord chatter) and
# must NOT match on their own — they ride along only when a distinctive longer
# alias / canonical matches (mirrors ``utils.projmoon.keywords`` curation: "don" /
# "sang" resolve via "Don Quixote" / "Yi Sang", and the E.G.O grade "HE" via
# "he grade", never the bare word).
_AMBIGUOUS_BARE_TOKENS: frozenset[str] = frozenset({"he", "don", "sang"})

# Distinctive group phrases that pull a whole entity-kind roster as grounding.
# Conservative on purpose — only clearly list-/group-shaped phrasing, never a bare
# singular (a single named entity grounds through the per-entity match instead).
_ROSTER_TRIGGERS: dict[str, tuple[str, ...]] = {
    "sinner": (
        "sinners",
        "all sinners",
        "the sinners",
        "every sinner",
        "12 sinners",
        "twelve sinners",
        "list of sinners",
    ),
    "sin": (
        "seven sins",
        "7 sins",
        "the sins",
        "all sins",
        "sin affinities",
        "sin affinity",
    ),
    "damage_type": (
        "damage types",
        "all damage types",
        "three damage types",
        "the damage types",
    ),
    "ego_grade": (
        "ego grades",
        "e.g.o grades",
        "all ego grades",
        "the ego grades",
        "ego grade list",
    ),
    "status": (
        "status effects",
        "all statuses",
        "status keywords",
    ),
    "mechanic": (
        "combat mechanics",
        "game mechanics",
        "combat system",
        "how does combat work",
        "how combat works",
        "all mechanics",
        "list of mechanics",
    ),
}


@dataclass(frozen=True)
class ProjmoonContext:
    """Retrieved Limbus facts ready for the instruction stack.

    Mirrors :class:`services.btd6_context_service.BTD6Context` so the shared
    ``KnowledgeDomain`` seam (Slice B) can fold the two onto one renderer.
    """

    facts: tuple[str, ...]
    source_summary: str = _PROVENANCE
    confidence: float = 0.6


def _normalise(text: str) -> str:
    r"""Lower-case, replace every non-word run with a single space, pad with
    spaces so whole-token containment (``f" {token} "``) is punctuation-safe.

    ``\w`` keeps Unicode letters (so accented Sinner names survive casefold).
    """
    folded = re.sub(r"[^\w]+", " ", text.casefold()).strip()
    return f" {folded} "


def _match_tokens(entry: projmoon_data_service.LimbusEntry) -> tuple[str, ...]:
    """The whole-token keys an entry may match on (canonical + aliases),
    casefolded, with the ambiguous bare tokens removed.
    """
    tokens = (entry.canonical.casefold(), *entry.aliases)
    return tuple(
        token
        for token in dict.fromkeys(tokens)
        if token and token not in _AMBIGUOUS_BARE_TOKENS
    )


def _matched_entries(text: str) -> list[projmoon_data_service.LimbusEntry]:
    """Every distinct Limbus entry named as a whole token in ``text``.

    Deterministic: returns entries in canonical dataset order (kind order, then
    file order), never message order, so a fixed message always grounds the same.
    """
    needle = _normalise(text)
    matched: list[projmoon_data_service.LimbusEntry] = []
    for entry in projmoon_data_service.all_entries():
        for token in _match_tokens(entry):
            if f" {token} " in needle:
                matched.append(entry)
                break
    return matched


def _rostered_kinds(text: str) -> list[str]:
    """Entity kinds whose whole roster a group/list phrase in ``text`` requests."""
    needle = _normalise(text)
    kinds: list[str] = []
    for kind, triggers in _ROSTER_TRIGGERS.items():
        if any(f" {_normalise(trigger).strip()} " in needle for trigger in triggers):
            kinds.append(kind)
    return kinds


def _body(entry: projmoon_data_service.LimbusEntry) -> str:
    """Compose the grounding body for one entry, enriched per kind."""
    base = f"{entry.canonical}: {entry.description}"
    if entry.entity_kind == "sinner":
        origin = entry.extra.get("literary_origin")
        if isinstance(origin, dict) and origin.get("work") and origin.get("author"):
            base = f"{base} (literary origin: {origin['work']} by {origin['author']})"
    elif entry.entity_kind == "sin":
        color = entry.extra.get("color")
        if color:
            base = f"{entry.canonical} ({color} Sin affinity): {entry.description}"
    elif entry.entity_kind == "ego_grade":
        rank = entry.extra.get("rank")
        if rank:
            base = (
                f"{entry.canonical} (E.G.O grade, rank {rank}/5): {entry.description}"
            )
    elif entry.entity_kind == "mechanic":
        category = entry.extra.get("category")
        if category:
            base = (
                f"{entry.canonical} (combat mechanic — {category}): {entry.description}"
            )
    return base


def _grounding_line(entry: projmoon_data_service.LimbusEntry) -> str:
    """``<body> (source: Limbus Company structural data ...)`` — provenance is
    reserved out of the cap so it can never be truncated away.
    """
    suffix = f" (source: {_PROVENANCE})"
    budget = max(1, _FACT_TEXT_CAP - len(suffix))
    return f"{sanitise(_body(entry), cap=budget)}{suffix}"


def build(text: str) -> ProjmoonContext:
    """Return the Limbus grounding facts for ``text``.

    Combines per-entity matches with bounded roster expansion, de-duplicates by
    entry id (preserving canonical dataset order), and caps at :data:`_MAX_FACTS`.
    Never raises: a fixture-load fault degrades to an empty context so the reply
    path proceeds unchanged (the model answers from the instruction stack alone).
    """
    try:
        entries: list[projmoon_data_service.LimbusEntry] = list(_matched_entries(text))
        roster_kinds = _rostered_kinds(text)
        if roster_kinds:
            seen_ids = {entry.id for entry in entries}
            for kind in projmoon_data_service.entity_kinds():
                if kind not in roster_kinds:
                    continue
                for entry in projmoon_data_service.get_entries(kind):
                    if entry.id not in seen_ids:
                        entries.append(entry)
                        seen_ids.add(entry.id)
    except Exception:  # noqa: BLE001 — grounding is best-effort; never break reply
        return ProjmoonContext(facts=())

    facts = tuple(_grounding_line(entry) for entry in entries[:_MAX_FACTS])
    return ProjmoonContext(facts=facts)


__all__ = ["ProjmoonContext", "build"]
