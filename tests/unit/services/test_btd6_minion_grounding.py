"""Minion / sub-tower names ground their owning tier (answerability item 6a).

Minion stats live under the owner's ``subtowers`` — nothing keyed on the
minion's own name — so "Crushing Sentry" / "UAV" drew a blank and
"Mini Sun Avatar" mis-resolved to the Sun Avatar upgrade (the wrong tier).
The same pass's survey exposed the diacritic-split bug in the upgrade
tokenizer: "Pouākai" indexed as ``pou|kai`` and matched nothing, typed
either way.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_context_service, btd6_upgrade_service  # noqa: E402


def _minion_facts(facts) -> list[str]:
    return [f for f in facts if f.startswith("[btd6_minion]")]


@pytest.mark.asyncio
async def test_mini_sun_avatar_resolves_to_owning_tier():
    """The headline 6a case: the name used to land on Sun Avatar (3-0-0)."""
    ctx = await btd6_context_service.build("what does the mini sun avatar do")
    lines = _minion_facts(ctx.facts)
    assert any("Sun Temple" in line and "4-0-0" in line for line in lines), lines
    # The owning tier's card grounds too (it carries the minion stat lines).
    assert any(
        f.startswith("[btd6_upgrade] Sun Temple =") for f in ctx.facts
    ), ctx.facts


@pytest.mark.asyncio
async def test_typed_sentry_names_resolve():
    ctx = await btd6_context_service.build("crushing sentry stats")
    lines = _minion_facts(ctx.facts)
    assert any("Sentry Expert" in line for line in lines), lines


@pytest.mark.asyncio
async def test_hero_minion_renders_its_effect():
    """Etienne's UAV has no attack — its effect is the Camo-detection buff."""
    ctx = await btd6_context_service.build("what does etiennes uav do")
    lines = _minion_facts(ctx.facts)
    assert any(
        "Etienne" in line and "grants Camo detection" in line for line in lines
    ), lines


@pytest.mark.asyncio
async def test_generic_english_minion_names_are_stoplisted():
    ctx = await btd6_context_service.build("my plane leaves at 9")
    assert _minion_facts(ctx.facts) == []


@pytest.mark.asyncio
async def test_upgrade_owned_names_stay_with_upgrade_grounding():
    """Beast names ARE their tier's upgrade-card names since the cutover —
    the minion pass must not double-ground what Pass 3c already owns."""
    ctx = await btd6_context_service.build("what does the orca do")
    assert _minion_facts(ctx.facts) == []
    assert any(f.startswith("[btd6_upgrade] Orca =") for f in ctx.facts)


def test_minion_index_skips_colliding_names():
    index = btd6_context_service._minion_name_index()
    assert "spectre" not in index  # the Ace upgrade owns this name
    assert "orca" not in index  # beast == upgrade-card name
    assert "mini sun avatar" in index
    assert "uav" in index


# ---------------------------------------------------------------------------
# Diacritic folding in the upgrade resolver (found by the 6a survey)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("query", ["pouakai", "Pouākai", "POUAKAI stats"])
def test_pouakai_resolves_regardless_of_diacritics(query):
    res = btd6_upgrade_service.resolve_upgrade(query)
    assert res.match_type == "exact_name", (query, res.match_type)
    assert res.upgrade is not None
    assert res.upgrade.canonical == "Pouākai"


@pytest.mark.asyncio
async def test_pouakai_question_grounds_the_upgrade_card():
    ctx = await btd6_context_service.build("pouakai stats")
    assert any(f.startswith("[btd6_upgrade] Pouākai =") for f in ctx.facts)
