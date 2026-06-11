"""Single owner for BTD6 factual grounding (M4).

Two consumers ask through this module:

* The natural-language stage's answer renderer (validates AI
  output before it reaches the user).
* :mod:`services.btd6_strategy_review_service` (validates a
  proposed strategy field against retrieved facts).

Centralising the grounding check means the prompt-injection +
grounding pin tests have one place to extend, and ensures AI
output paths cannot fabricate stats by going around the validator.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any

from core.runtime.ai.contracts import AITask, PolicyDenialReason
from core.runtime.ai.safety import claims_are_grounded
from services import btd6_knowledge_api
from utils.btd6 import name_guard
from utils.btd6.keywords import has_btd6_context
from utils.btd6.paragon_math import PARAGONS

logger = logging.getLogger("bot.services.btd6_grounding")


@dataclass(frozen=True)
class GroundingResult:
    grounded: bool
    reason_code: str  # 'none' or a PolicyDenialReason value
    used_fact_keys: tuple[str, ...]
    notes: tuple[str, ...] = ()
    # Set by :func:`validate_btd6_reply` when a reply states BTD6 names or
    # numbers absent from the grounded payload — surfaced to the regenerate
    # constraint and the structured block-reply log.
    offending_names: tuple[str, ...] = ()
    offending_numbers: tuple[str, ...] = ()


async def validate_answer(
    answer_text: str,
    *,
    context_facts: list[dict[str, Any]] | None = None,
    minimum_confidence: float = 0.5,
) -> GroundingResult:
    """Verify that every numeric claim in ``answer_text`` is supported.

    ``context_facts`` is a list of :class:`btd6_knowledge_api.FactBundle`
    bodies (already retrieved) so the validator does not need to
    re-fetch. If the bundle is empty the validator returns
    ``GROUNDING_FAILED`` unless the answer is purely textual.
    """
    haystack_pieces: list[str] = []
    used_keys: list[str] = []
    if context_facts:
        for fact in context_facts:
            body = (
                fact.get("body")
                if isinstance(fact, dict)
                else getattr(
                    fact,
                    "body",
                    None,
                )
            )
            if body:
                haystack_pieces.append(str(body))
            key = (
                fact.get("entity_key")
                if isinstance(fact, dict)
                else getattr(
                    fact,
                    "entity_key",
                    None,
                )
            )
            confidence = (
                fact.get("confidence")
                if isinstance(fact, dict)
                else getattr(fact, "confidence", 1.0)
            )
            if key and (confidence is None or float(confidence) >= minimum_confidence):
                used_keys.append(str(key))

    if claims_are_grounded(answer_text, allowed_facts=haystack_pieces):
        return GroundingResult(
            grounded=True,
            reason_code=PolicyDenialReason.NONE.value,
            used_fact_keys=tuple(used_keys),
        )
    return GroundingResult(
        grounded=False,
        reason_code=PolicyDenialReason.GROUNDING_FAILED.value,
        used_fact_keys=tuple(used_keys),
        notes=("numeric_claim_unsupported",),
    )


async def validate_strategy_field(
    *,
    fact_type: str,
    entity_kind: str,
    entity_key: str,
    proposed_body: dict[str, Any],
) -> GroundingResult:
    """Verify a single strategy field against the BTD6 KnowledgeAPI."""
    bundle = (
        await btd6_knowledge_api.get_tower(entity_key)
        if entity_kind == "tower"
        else None
    )
    if entity_kind == "hero":
        bundle = await btd6_knowledge_api.get_hero(entity_key)
    elif entity_kind == "map":
        bundle = await btd6_knowledge_api.get_map(entity_key)
    elif entity_kind == "mode":
        bundle = await btd6_knowledge_api.get_mode(entity_key)
    elif entity_kind == "round":
        try:
            bundle = await btd6_knowledge_api.get_round(int(entity_key))
        except (TypeError, ValueError):
            bundle = None

    if bundle is None:
        return GroundingResult(
            grounded=False,
            reason_code=PolicyDenialReason.GROUNDING_FAILED.value,
            used_fact_keys=(),
            notes=("entity_not_in_knowledge_api",),
        )

    canonical = bundle.body if hasattr(bundle, "body") else bundle.get("body", {})
    haystack = str(canonical)
    if claims_are_grounded(str(proposed_body), allowed_facts=[haystack]):
        return GroundingResult(
            grounded=True,
            reason_code=PolicyDenialReason.NONE.value,
            used_fact_keys=(str(entity_key),),
        )
    return GroundingResult(
        grounded=False,
        reason_code=PolicyDenialReason.GROUNDING_FAILED.value,
        used_fact_keys=(str(entity_key),),
        notes=("strategy_field_unsupported_by_facts",),
    )


# ---------------------------------------------------------------------------
# Answer-path faithfulness verifier (the natural-language stage's backstop)
# ---------------------------------------------------------------------------
#
# Realises the consumer this module's docstring already names — "the
# natural-language stage's answer renderer (validates AI output before it
# reaches the user)". ``validate_answer`` above is the legacy numeric-only
# (and currently unwired) entry; ``validate_btd6_reply`` is the live one.

_index_lock = threading.Lock()
_NAME_INDEX: name_guard.NameMatchers | None = None
_NAME_INDEX_KEY: tuple[str, str, int] | None = None


def _name_index() -> name_guard.NameMatchers:
    """Memoized BTD6 proper-name matchers, rebuilt when the dataset reloads.

    Sourced entirely from :func:`btd6_data_service.get_dataset` (entities +
    ``upgrade_paths``) plus :data:`paragon_math.PARAGONS`, so the index has no
    coupling to the separate ``btd6_stats_service`` caches. Keyed on the
    dataset's ``(data_version, game_version, id())`` so a ``reset_cache()``
    (new object) forces a rebuild even when the version strings are unchanged.

    Single-word tokens are restricted to distinctive hero names + aliases
    (mirroring the router's discipline); generic single words — bloon colours
    ("Red"/"Blue"), single-word tower names — are indexed only as multi-word
    phrases or not at all, to avoid false positives on ordinary English.
    """
    global _NAME_INDEX, _NAME_INDEX_KEY
    from services import btd6_data_service

    try:
        dataset = btd6_data_service.get_dataset()
    except Exception:
        logger.warning(
            "btd6_grounding: dataset unavailable; using empty name index",
            exc_info=True,
        )
        return name_guard.NameMatchers(multi=frozenset(), single=frozenset())

    key = (dataset.data_version, dataset.game_version, id(dataset))
    if _NAME_INDEX is not None and key == _NAME_INDEX_KEY:
        return _NAME_INDEX
    with _index_lock:
        if _NAME_INDEX is not None and key == _NAME_INDEX_KEY:
            return _NAME_INDEX

        canonicals: set[str] = set()
        aliases: set[str] = set()

        # Heroes — distinctive enough for whole-word single-token matching.
        for hero in dataset.heroes:
            canonicals.add(hero.canonical)
            aliases.update(hero.aliases)

        # Boss Bloons — same discipline as heroes: every canonical
        # (Bloonarius, Lych, Vortex, …) is a distinctive word, and a BTD6
        # reply naming a boss absent from the grounded facts should offend
        # exactly like an ungrounded hero name (BUG-0002 class).
        for boss in dataset.bosses:
            canonicals.add(boss.canonical)

        # Other categories — only multi-word names (substring-safe). Single
        # words here are generic (bloon colours, "Druid") and would
        # false-positive on ordinary chat, so they are skipped.
        for entry in (
            *dataset.towers,
            *dataset.maps,
            *dataset.modes,
            *dataset.bloons,
            *dataset.ct_relics,
        ):
            if " " in entry.canonical:
                canonicals.add(entry.canonical)
            for alias in entry.aliases:
                if " " in alias:
                    aliases.add(alias)

        # All 13 paragon proper names (every one is multi-word + distinctive).
        for paragon in PARAGONS:
            canonicals.add(paragon.name)

        # Upgrade names live in the dataset (``upgrade_paths``); index the
        # multi-word ones ("Sharp Shots", "Glaive Lord") — single-word upgrade
        # names ("Juggernaut", "Crossbow") are ordinary words and skipped.
        for tower in dataset.towers:
            for path_upgrades in tower.upgrade_paths.values():
                for upgrade in path_upgrades:
                    if " " in upgrade:
                        canonicals.add(upgrade)

        index = name_guard.build_matchers(canonicals, aliases)
        _NAME_INDEX = index
        _NAME_INDEX_KEY = key
        return index


def _reset_for_tests() -> None:
    """Clear the memoized name index.

    Tests that swap BTD6 fixtures call this alongside
    ``btd6_data_service.reset_cache()`` so a stale index cannot leak across
    cases. (The index does not read ``btd6_stats_service``, so its cache is
    irrelevant here.)
    """
    global _NAME_INDEX, _NAME_INDEX_KEY
    with _index_lock:
        _NAME_INDEX = None
        _NAME_INDEX_KEY = None


def general_path_should_verify(prompt: str, answer: str) -> bool:
    """True when a ``GENERAL_NL_ANSWER`` reply should run the BTD6 name guard.

    Fires when the turn is BTD6-themed (a curated context keyword in the prompt
    or answer) OR the answer contains a distinctive **multi-word** BTD6 proper
    name (every paragon, most towers/upgrades), which never occurs in ordinary
    chat. A single common hero name on its own (e.g. "Benjamin") does NOT
    trigger — that is the false-positive guard for ordinary conversation.
    """
    try:
        if has_btd6_context(f"{prompt} {answer}"):
            return True
        return bool(name_guard.multiword_names_present(answer, _name_index()))
    except Exception:
        logger.warning(
            "btd6_grounding: general_path_should_verify raised; skipping guard",
            exc_info=True,
        )
        return False


def validate_btd6_reply(
    answer_text: str,
    *,
    facts: tuple[str, ...] = (),
    tool_results: tuple[str, ...] = (),
    task: AITask | None = None,
) -> GroundingResult:
    """Verify a model-authored reply against the grounded payload.

    Trusted haystack = ``facts ∪ tool_results`` (deterministic auto-grounding
    facts + approved BTD6 tool outputs). A reply is grounded when every indexed
    BTD6 name it states is present in the haystack and — for
    :attr:`AITask.BTD6_ANSWER` only — every numeric token is present too
    (numbers are never grounded on the general path, where ordinary numerals
    are legitimate). **Never raises**: any internal error returns a
    not-grounded result so the caller fails closed to the refusal floor.
    """
    try:
        matchers = _name_index()
        haystack = " ".join((*facts, *tool_results))

        allowed_names = name_guard.names_present(haystack, matchers)
        answer_names = name_guard.names_present(answer_text, matchers)
        offending_names = tuple(sorted(answer_names - allowed_names))

        offending_numbers: tuple[str, ...] = ()
        if task is AITask.BTD6_ANSWER:
            offending_numbers = name_guard.offending_numbers(answer_text, haystack)

        if not offending_names and not offending_numbers:
            return GroundingResult(
                grounded=True,
                reason_code=PolicyDenialReason.NONE.value,
                used_fact_keys=(),
            )

        notes: list[str] = []
        if offending_names:
            notes.append("entity_name_unsupported")
        if offending_numbers:
            notes.append("numeric_claim_unsupported")
        return GroundingResult(
            grounded=False,
            reason_code=PolicyDenialReason.GROUNDING_FAILED.value,
            used_fact_keys=(),
            notes=tuple(notes),
            offending_names=offending_names,
            offending_numbers=offending_numbers,
        )
    except Exception:
        logger.warning(
            "btd6_grounding: validate_btd6_reply raised; failing closed",
            exc_info=True,
        )
        return GroundingResult(
            grounded=False,
            reason_code=PolicyDenialReason.GROUNDING_FAILED.value,
            used_fact_keys=(),
            notes=("verifier_error",),
        )


__all__ = [
    "GroundingResult",
    "general_path_should_verify",
    "validate_answer",
    "validate_btd6_reply",
    "validate_strategy_field",
]
