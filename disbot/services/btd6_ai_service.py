"""BTD6 AI orchestrator — deterministic-first.

Brings resolver, knowledge, and response-builder together. Module 4
(BTD6 Cog command MVP) only uses the deterministic path. Module 5
(optional AI augmentation) is opt-in via :func:`answer_question`'s
``augment_with_ai`` parameter and ``services.ai_gateway``.

The orchestrator never invents BTD6 facts. Deterministic services
own canonical names, costs, upgrade-path tier names, round
contents, and source labels. When AI augmentation is enabled it
adds explanatory prose only — the deterministic fields stay as-is.
"""

from __future__ import annotations

from dataclasses import replace

from services.btd6_knowledge_service import (
    hero_fact,
    map_fact,
    mode_fact,
    round_fact,
    tower_fact,
)
from services.btd6_resolver_service import ResolvedIntent, resolve
from services.btd6_response_builder import (
    BTD6Response,
    for_hero,
    for_map,
    for_mode,
    for_round,
    for_tower,
    for_unresolved,
)


def deterministic_answer(intent: ResolvedIntent) -> BTD6Response:
    """Return the deterministic-only :class:`BTD6Response` for ``intent``.

    The first recognised entity wins (towers → heroes → maps →
    modes → rounds). If nothing was resolved, returns the
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
    return for_unresolved(intent)


async def answer_question(
    text: str,
    *,
    augment_with_ai: bool = False,
) -> BTD6Response:
    """Resolve free-form ``text`` and return a typed response.

    ``augment_with_ai`` is wired in Module 5. In Module 3/4 it is
    forced to ``False`` so this service is provably deterministic.
    """
    intent = resolve(text)
    response = deterministic_answer(intent)
    if augment_with_ai:
        return await _augment_with_ai(intent, response)
    return response


async def _augment_with_ai(
    intent: ResolvedIntent,
    response: BTD6Response,
) -> BTD6Response:
    """Stub for Module 5. Returns the deterministic response unchanged.

    Module 5 will replace this with a guarded ``services.ai_gateway``
    call that adds explanatory prose to ``response.why_it_matters``
    or appends an AI-sourced ``follow_up``. Deterministic fields
    (cost, stats, sources, version label) remain unmodified.
    """
    # Module 5 hook: keep the contract stable so swapping the body
    # in does not change ``answer_question``'s call sites.
    return replace(response)
