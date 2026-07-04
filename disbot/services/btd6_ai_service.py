"""BTD6 AI orchestrator — deterministic-first.

Brings resolver, knowledge, and response-builder together.

* Module 3+4 use deterministic-only mode.
* Module 5 (this module) adds optional AI augmentation through
  ``services.ai_gateway``. AI receives structured deterministic
  context, NEVER a raw user prompt, and only contributes
  explanation prose. Deterministic facts (cost, stats, sources,
  version label) remain owned by deterministic services.

Gate stack (all must be true to call the gateway):

1. Caller passes ``augment_with_ai=True``.
2. The AI platform itself is enabled (``AI_ENABLED``) and the
   ``HELP_ANSWER`` task is allowed.

The legacy ``BTD6_AI_ENABLED`` env var was retired in M5;
``btd6_ai_enabled()`` is now a ``return True`` shim and the task /
``ai_natural_language_policy`` layer is the real runtime gate.

Any failure mode — gateway disabled, provider unavailable, timeout,
invalid output, exception — yields the deterministic baseline
without raising. The orchestrator is provably safe to call from
the cog regardless of provider state.
"""

from __future__ import annotations

import logging
from dataclasses import replace

from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponseMode,
    AIScope,
    AITask,
)
from core.runtime.ai.feature_flags import task_enabled
from services import ai_gateway
from services.btd6_knowledge_service import (
    hero_fact,
    map_fact,
    mode_fact,
    round_fact,
    tower_fact,
)
from services.btd6_resolver_service import ResolvedIntent, resolve
from services.btd6_response_builder import (
    UNRESOLVED_TITLE,
    BTD6Response,
    for_bloon,
    for_hero,
    for_list_reply,
    for_map,
    for_mode,
    for_reference_facts,
    for_round,
    for_tower,
    for_unresolved,
)

logger = logging.getLogger("bot.services.btd6_ai_service")

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def btd6_ai_enabled() -> bool:
    """Return True if BTD6 AI augmentation is currently allowed.

    M5 of the BTD6-top-level + AI-central-policy initiative retires
    the legacy ``BTD6_AI_ENABLED`` env var. AI Platform task policy
    + ``ai_natural_language_policy`` resolution are the runtime
    gates now; this function stays as a thin shim returning True so
    the legacy ``answer_question(augment_with_ai=True)`` caller path
    continues to work end-to-end (the policy/task layer is checked
    immediately after).
    """
    return True


_AUGMENT_SYSTEM_PROMPT = (
    "You are a Bloons Tower Defense 6 assistant. The user has asked a "
    "question and a deterministic SuperBot service has already produced "
    "a factually-grounded answer from validated game data. Your job is "
    "to add a SHORT explanatory paragraph (under 80 words) that helps "
    "the player understand WHY the deterministic answer is correct or "
    "what to look out for. Never invent stats, costs, or tier names — "
    "rely only on the deterministic fields supplied in the payload. "
    "Reply with strict JSON of the form "
    '{"explanation": "<your paragraph>"}.'
)

_AUGMENT_SCHEMA: dict = {
    "name": "BTD6Augmentation",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "explanation": {"type": "string"},
        },
        "required": ["explanation"],
    },
    "strict": True,
}


def deterministic_answer(intent: ResolvedIntent) -> BTD6Response:
    """Return the deterministic-only :class:`BTD6Response` for ``intent``.

    The first recognised entity wins (towers → heroes → maps →
    modes → rounds → bloons). If nothing was resolved, returns the
    "unresolved" response so the cog can surface a helpful hint.
    """
    if intent.towers:
        fact = tower_fact(intent.towers[0].id)
        if fact is not None:
            return for_tower(fact)
    if intent.heroes:
        hero = hero_fact(intent.heroes[0].id)
        if hero is not None:
            return for_hero(hero)
    if intent.maps:
        game_map = map_fact(intent.maps[0].id)
        if game_map is not None:
            return for_map(game_map)
    if intent.modes:
        mode = mode_fact(intent.modes[0].id)
        if mode is not None:
            return for_mode(mode)
    if intent.rounds:
        fact = round_fact(intent.rounds[0].round_number)
        if fact is not None:
            return for_round(fact)
    # Bloons resolve last so "ceramic rush on round 63" stays a round answer;
    # the resolver matched bloons all along — this branch was the missing
    # consumer (#655 answerability item 5).
    if intent.bloons:
        return for_bloon(intent.bloons[0])
    return for_unresolved(intent)


def _deterministic_list_floor(text: str) -> BTD6Response | None:
    """The BUG-0009 / round-range list floor, wrapped for the Ask surfaces.

    Returns a :class:`BTD6Response` when ``btd6_context_service`` owns a labelled
    list/range answer for ``text`` (the same floor the conversational stage serves
    as raw text), else ``None`` so the caller keeps its normal entity path.
    Best-effort — a floor build failure never breaks the reply.
    """
    try:
        from services import btd6_context_service

        reply = btd6_context_service.deterministic_btd6_list_reply(text)
    except Exception:  # noqa: BLE001 — never block on the floor
        logger.debug("btd6_ai_service: list floor unavailable", exc_info=True)
        return None
    return for_list_reply(reply) if reply else None


async def answer_question(
    text: str,
    *,
    augment_with_ai: bool = False,
    guild_id: int | None = None,
) -> BTD6Response:
    """Resolve free-form ``text`` and return a typed response.

    Augmentation is opt-in AND gated by AI Platform task policy:
    after M5 the only gate is :func:`task_enabled(AITask.HELP_ANSWER)`
    (and, in production, the central ``ai_natural_language_policy``
    resolver via the M2 stage). The deterministic baseline is always
    produced first; ``btd6_ai_enabled`` is a no-op shim kept for
    backwards-compatible callers.

    Live grounding from ``btd6_context_service`` is best-effort: any
    failure leaves the deterministic response unchanged. The bundle is
    already sanitised + provenance-labelled before reaching this layer.
    """
    intent = resolve(text)
    # Deterministic list/range floor FIRST: it owns labelled list answers the
    # entity resolver can't assemble — notably a round RANGE, which the resolver
    # only sees as two endpoint round numbers ("list all the bloons from r29 till
    # r63" grounded just rounds 29 + 63). Serving it here gives the Ask modal /
    # `!btd6 ask` the same authoritative floor the conversational stage already
    # uses; best-effort, never blocks the normal entity path.
    floor = _deterministic_list_floor(text)
    if floor is not None:
        return floor
    response = deterministic_answer(intent)
    response = await _attach_live_grounding(text, response)
    if response.title == UNRESOLVED_TITLE and response.live_facts:
        # No entity intent matched, but the shared grounding pipeline answered
        # anyway (powers / Monkey Knowledge / bosses / Geraldo / relics…) —
        # lead with the facts instead of a "couldn't find anything" headline.
        # The AI tool path reads the same facts directly; this gives the
        # deterministic menu Ask the same reach (#655 item 5).
        response = for_reference_facts(response.live_facts)
    if augment_with_ai and btd6_ai_enabled() and task_enabled(AITask.HELP_ANSWER):
        return await _augment_with_ai(intent, response, guild_id=guild_id)
    return response


async def _attach_live_grounding(text: str, response: BTD6Response) -> BTD6Response:
    """Populate ``response.live_facts`` from ``btd6_context_service``.

    Best-effort: any exception (DB unavailable, context build failure)
    falls back to the unchanged ``response``. The same service backs
    the AI Platform natural-language stage so the two surfaces share
    one grounding pipeline rather than each maintaining its own.
    """
    try:
        from services import btd6_context_service

        ctx = await btd6_context_service.build(text)
    except Exception:  # noqa: BLE001 — never block on grounding
        logger.debug("btd6_ai_service: live grounding unavailable", exc_info=True)
        return response
    if not ctx.facts:
        return response
    return replace(response, live_facts=ctx.facts)


def _augmentation_payload(
    intent: ResolvedIntent,
    response: BTD6Response,
) -> dict[str, object]:
    """Structured deterministic context for the LLM.

    The provider never sees raw user prose. It receives the resolved
    intent (canonical entity ids only) and the deterministic response
    fields. This guarantees AI output cannot drift outside the
    grounded set.
    """
    return {
        "query_summary": {
            "resolved_towers": [t.id for t in intent.towers],
            "resolved_heroes": [h.id for h in intent.heroes],
            "resolved_maps": [m.id for m in intent.maps],
            "resolved_modes": [m.id for m in intent.modes],
            "resolved_rounds": list(intent.candidate_round_numbers),
            "resolved_bloons": [b.id for b in intent.bloons],
            "resolver_confidence": intent.confidence,
        },
        "deterministic_answer": {
            "title": response.title,
            "short_answer": response.short_answer,
            "why_it_matters": response.why_it_matters,
            "recommended_options": list(response.recommended_options),
            "common_mistakes": list(response.common_mistakes),
            "version_sensitivity": response.version_sensitivity,
            "confidence": response.confidence,
        },
        # Already-sanitised live grounding strings. The provider sees
        # these only as untrusted data; deterministic fields above stay
        # authoritative.
        "live_facts": list(response.live_facts),
    }


async def _augment_with_ai(
    intent: ResolvedIntent,
    response: BTD6Response,
    *,
    guild_id: int | None,
) -> BTD6Response:
    """Try to add an AI-authored explanation paragraph.

    Returns the deterministic ``response`` unchanged on any failure:
    gateway degraded, invalid JSON, missing ``explanation`` key,
    empty explanation, or exception. Deterministic fields are never
    mutated; only ``follow_up`` is appended (if it would otherwise
    be empty) or replaced with the AI prose.
    """
    request = AIRequest(
        context=AIRequestContext(
            task=AITask.HELP_ANSWER,
            scope=AIScope.USER,
            guild_id=guild_id,
            source="btd6_ai_service",
        ),
        system_prompt=_AUGMENT_SYSTEM_PROMPT,
        payload=_augmentation_payload(intent, response),
        mode=AIResponseMode.JSON,
        response_schema=_AUGMENT_SCHEMA,
    )
    try:
        ai_response = await ai_gateway.execute(request)
    except Exception:  # noqa: BLE001 — defensive boundary
        logger.exception("btd6_ai_service: gateway raised; using deterministic")
        return replace(response)

    if ai_response.degraded or not ai_response.data:
        return replace(response)

    explanation = ai_response.data.get("explanation") if ai_response.data else None
    if not isinstance(explanation, str) or not explanation.strip():
        return replace(response)

    # Compose: append the AI prose into follow_up. The deterministic
    # follow_up (if any) wins over AI prose to preserve operator-
    # authored navigation hints.
    new_follow_up = response.follow_up if response.follow_up else explanation.strip()
    if response.follow_up:
        # Append AI prose after the deterministic hint so callers see both.
        new_follow_up = f"{response.follow_up}\n\n{explanation.strip()}"

    return replace(response, follow_up=new_follow_up)
