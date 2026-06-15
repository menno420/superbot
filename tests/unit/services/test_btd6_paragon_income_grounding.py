"""Paragon income + effects reach every surface (the Navarch "no coins" miss).

Live failure (2026-06-10): "@SuperBot does the navarch of seas paragon make
coins" → the bot answered a confident NO. The committed data was right all
along (``cashPerRound: 3200`` + the Trade Empire buff, decoded at the v55.1
cutover) — the failure was routing, in three layers:

1. "navarch of seas" (article dropped) failed ``_paragon_name_facts``'s exact
   substring match → ZERO grounding facts → the model freelanced.
2. The curated description's income sentence is the LAST sentence and the
   240-char fact cap truncates it.
3. The paragon grounding rendered only the primary-attack headline — no
   income line, no buff/zone effect lines (towers surface income via
   specials, heroes via [btd6_hero_buff]; paragons had no leg).

These tests pin the repaired routing end-to-end.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_context_service, btd6_stats_service  # noqa: E402
from utils.btd6.effect_lines import buff_text  # noqa: E402

# ---------------------------------------------------------------------------
# Data accessor
# ---------------------------------------------------------------------------


def test_navarch_income_per_round_property():
    stats = btd6_stats_service.get_paragon_stats("navarch_of_the_seas")
    assert stats is not None
    assert stats.income_per_round == 3200


def test_combat_only_paragon_has_no_income():
    stats = btd6_stats_service.get_paragon_stats("apex_plasma_master")
    assert stats is not None
    assert stats.income_per_round is None


# ---------------------------------------------------------------------------
# AI grounding — the exact live miss
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_typoed_navarch_question_grounds_income():
    """The screenshot's exact text (article dropped) must ground the income."""
    ctx = await btd6_context_service.build(
        "does the navarch of seas paragon make coins",
    )
    income_lines = [f for f in ctx.facts if "income" in f.lower()]
    assert any(
        "generates $3,200 at the end of each round" in line for line in income_lines
    ), f"no income grounding line in: {ctx.facts!r}"


@pytest.mark.asyncio
async def test_navarch_grounding_includes_buff_effect_lines():
    ctx = await btd6_context_service.build("navarch of the seas paragon")
    effects = [f for f in ctx.facts if f.startswith("[btd6_paragon_stats effect]")]
    joined = "\n".join(effects)
    assert "+$10/round per Merchantman" in joined
    assert "+$20/round per Favored Trades" in joined
    assert "(affects paragons only)" in joined  # the structural Flagship split


@pytest.mark.asyncio
async def test_paragon_shorthand_grounds_when_paragon_keyword_present():
    """ "boat paragon" reaches the Navarch via the canonical shorthand
    resolver; the word "paragon" gates the loosened matching."""
    ctx = await btd6_context_service.build("boat paragon income?")
    assert any("Navarch of the Seas income" in f for f in ctx.facts)


@pytest.mark.asyncio
async def test_combat_only_paragon_gets_no_income_line():
    ctx = await btd6_context_service.build("apex plasma master paragon")
    assert not any(
        "income" in f.lower() and "Apex" in f for f in ctx.facts
    ), "Apex must not gain a fabricated income line"


def test_squash_matching_does_not_loosen_to_fuzzy():
    """A non-paragon sentence without the keyword grounds nothing here."""
    out = btd6_context_service._paragon_name_facts(
        "the seas were rough this morning",
        set(),
    )
    assert out == []


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def test_buff_text_marks_paragon_scoped_aura():
    rendered = buff_text(
        {
            "kind": "FlagshipAttackSpeedIncrease",
            "name": "Flagship buff",
            "rateMultiplier": 0.85,
            "isGlobal": True,
            "onlyAffectParagon": True,
        },
    )
    assert rendered == "Flagship buff: x0.85 attack cooldown (affects paragons only)"


def test_stat_node_embeds_render_income():
    from utils.btd6 import stats_embed

    paragon = btd6_stats_service.get_paragon_stats("navarch_of_the_seas")
    embed = stats_embed.build_paragon_base_embed(paragon)
    assert "Income $3,200/round" in (embed.description or "")

    tower = btd6_stats_service.get_tower_stats("monkey_buccaneer")
    tier_embed = stats_embed.build_pro_tier_embed(tower, "005")
    assert "Income $800/round" in (tier_embed.description or "")

    hero = btd6_stats_service.get_hero_stats("benjamin")
    level_embed = stats_embed.build_pro_hero_level_embed(hero, "10")
    assert "Income $250/round" in (level_embed.description or "")


def test_stat_node_embed_without_income_stays_clean():
    from utils.btd6 import stats_embed

    paragon = btd6_stats_service.get_paragon_stats("apex_plasma_master")
    embed = stats_embed.build_paragon_base_embed(paragon)
    assert "Income" not in (embed.description or "")


# ---------------------------------------------------------------------------
# AI tool result
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_paragon_stats_tool_carries_income():
    from services.ai_tools import _btd6_paragon_stats_at_degree

    result = await _btd6_paragon_stats_at_degree({"paragon": "navarch", "degree": 50})
    assert result["found"] is True
    assert result["income_per_round"] == 3200
    assert "end of each round" in result["income_note"]


@pytest.mark.asyncio
async def test_paragon_stats_tool_omits_income_when_absent():
    from services.ai_tools import _btd6_paragon_stats_at_degree

    result = await _btd6_paragon_stats_at_degree({"paragon": "apex"})
    assert result["found"] is True
    assert "income_per_round" not in result


# ---------------------------------------------------------------------------
# Source-label faithfulness (answerability items 6b + 6c)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fixture_facts_carry_dataset_label_not_repo_path():
    """Item 6b: users saw the repo path-ism ``fixture/btd6_data`` verbatim."""
    ctx = await btd6_context_service.build("dart monkey")
    labelled = [f for f in ctx.facts if "(source: BTD6 dataset, game v" in f]
    assert labelled, f"no dataset-labelled facts in: {ctx.facts[:4]!r}"
    assert not any("fixture/btd6_data" in f for f in ctx.facts)


@pytest.mark.asyncio
async def test_fixture_only_answer_does_not_claim_nk_api():
    """Item 6c: a dataset-only answer must not be summarised as the NK API."""
    ctx = await btd6_context_service.build("dart monkey")
    assert ctx.facts  # fixture grounding fired
    assert ctx.source_summary == btd6_context_service._DATASET_SOURCE_SUMMARY
    assert "ninjakiwi" not in ctx.source_summary
