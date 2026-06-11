"""Conversation-carryover grounding for entity-less follow-ups (plan slice 1).

The 2026-06-10 Navarch screenshot, turn 2: "Does it make coins at the end of
round" — grounding is per-message, the pronoun names nothing, so the build
returned ZERO facts and the model answered from memory while sounding
sourced. Slice 1 of
``docs/planning/btd6-conversation-grounding-plan-2026-06-10.md``: a
zero-fact build with channel identity falls back to grounding the newest
recent conversation turn that resolves BTD6 entities, labeled
``[btd6_carryover]``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import ai_conversation_service, btd6_context_service  # noqa: E402

_GID, _CID = 9001, 9002


@pytest.fixture(autouse=True)
def _clean_buffer():
    ai_conversation_service._reset_for_tests()
    yield
    ai_conversation_service._reset_for_tests()


def _seed_navarch_exchange() -> None:
    ai_conversation_service.append(
        _GID,
        _CID,
        user_id=1,
        role="user",
        text="does the navarch of seas paragon make coins",
    )
    ai_conversation_service.append(
        _GID,
        _CID,
        user_id=2,
        role="assistant",
        text="No, Navarch of the Seas does not make coins. It is a pure combat tower.",
    )


@pytest.mark.asyncio
async def test_screenshot_turn_two_grounds_via_carryover():
    """The live failure, end-to-end: the pronoun follow-up grounds the income."""
    _seed_navarch_exchange()
    ctx = await btd6_context_service.build(
        "Does it make coins at the end of round",
        guild_id=_GID,
        channel_id=_CID,
    )
    assert ctx.facts, "carryover must ground the prior turn's entity"
    assert ctx.facts[0].startswith("[btd6_carryover]")
    assert any(
        "generates $3,200 at the end of each round" in f for f in ctx.facts
    ), ctx.facts


@pytest.mark.asyncio
async def test_topic_switch_does_not_carry_over():
    """A message that names its own entity never consults history."""
    _seed_navarch_exchange()
    ctx = await btd6_context_service.build(
        "dart monkey stats",
        guild_id=_GID,
        channel_id=_CID,
    )
    assert ctx.facts
    assert not any(f.startswith("[btd6_carryover]") for f in ctx.facts)
    assert not any("Navarch" in f for f in ctx.facts)


@pytest.mark.asyncio
async def test_without_channel_identity_behaviour_is_unchanged():
    """The Ask command / btd6_lookup tool paths pass text only — no fallback."""
    _seed_navarch_exchange()
    ctx = await btd6_context_service.build("Does it make coins at the end of round")
    assert ctx.facts == ()
    assert ctx.source_summary == btd6_context_service._FALLBACK_SOURCE_SUMMARY


@pytest.mark.asyncio
async def test_empty_buffer_yields_no_facts():
    ctx = await btd6_context_service.build(
        "Does it make coins at the end of round",
        guild_id=_GID,
        channel_id=_CID,
    )
    assert ctx.facts == ()


@pytest.mark.asyncio
async def test_newest_entity_bearing_turn_wins():
    """Two prior subjects → the more recent one is the carryover anchor."""
    ai_conversation_service.append(
        _GID, _CID, user_id=1, role="user", text="dart monkey stats"
    )
    ai_conversation_service.append(
        _GID, _CID, user_id=1, role="user", text="what about the ice monkey"
    )
    ctx = await btd6_context_service.build(
        "how much does it cost",
        guild_id=_GID,
        channel_id=_CID,
    )
    assert ctx.facts and ctx.facts[0].startswith("[btd6_carryover]")
    joined = "\n".join(ctx.facts)
    assert "Ice Monkey" in joined
    assert "Dart Monkey" not in joined


@pytest.mark.asyncio
async def test_carryover_summary_is_dataset_honest():
    """Carried fixture facts keep the item-6c dataset summary, not NK Tier 1."""
    _seed_navarch_exchange()
    ctx = await btd6_context_service.build(
        "Does it make coins at the end of round",
        guild_id=_GID,
        channel_id=_CID,
    )
    assert ctx.source_summary == btd6_context_service._DATASET_SOURCE_SUMMARY


# ---------------------------------------------------------------------------
# 2026-06-10 sweep fixes: ranking questions + bare distinctive shorthand
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ranking_questions_ground_the_rosters():
    """"best paragon" / "strongest tower" grounded ZERO facts — the model
    ranked from memory. The verified rosters pin the candidate names."""
    para = await btd6_context_service.build("best paragon")
    assert any(f.startswith("[btd6_paragon_roster]") for f in para.facts)
    tower = await btd6_context_service.build("strongest tower")
    assert any(f.startswith("[btd6_tower_roster]") for f in tower.facts)


@pytest.mark.asyncio
async def test_distinctive_bare_shorthand_grounds_without_keyword():
    ctx = await btd6_context_service.build("navarch")
    assert any("Navarch of the Seas" in f for f in ctx.facts)


@pytest.mark.asyncio
async def test_generic_alias_words_stay_behind_the_keyword_gate():
    """"boat" alone must not trigger the paragon shorthand pass (the word
    "paragon" is its gate; resolver tower aliasing is a separate, pre-existing
    path)."""
    out = btd6_context_service._paragon_name_facts("row your boat", set())
    assert out == []


@pytest.mark.asyncio
async def test_followup_flag_forces_carryover_despite_partial_grounding():
    """Live miss 2026-06-11 (first Haiku round): "which of those can damage
    lead" resolved the Lead BLOON — facts were non-empty, so the zero-fact
    carryover never fired and the reply's subject (the prior Geraldo turn)
    floored as ungrounded. With the router's conversation-cue flag the
    carryover facts are always added on top."""
    ai_conversation_service.append(
        _GID,
        _CID,
        user_id=1,
        role="user",
        text="what are geraldos items",
    )
    ai_conversation_service.append(
        _GID,
        _CID,
        user_id=2,
        role="assistant",
        text="Here are Geraldo's 16 shop items, organized by unlock level.",
    )
    ctx = await btd6_context_service.build(
        "which of those can damage lead",
        guild_id=_GID,
        channel_id=_CID,
        conversation_followup=True,
    )
    assert any("Geraldo" in f for f in ctx.facts), ctx.facts
    assert any(f.startswith("[btd6_carryover]") for f in ctx.facts), ctx.facts
    # Without the flag, today's zero-fact-only behaviour is preserved:
    # the lead-bloon resolution suppresses carryover.
    ctx_no_flag = await btd6_context_service.build(
        "which of those can damage lead",
        guild_id=_GID,
        channel_id=_CID,
    )
    if ctx_no_flag.facts:
        assert not any(
            f.startswith("[btd6_carryover]") for f in ctx_no_flag.facts
        ), "zero-fact gate should still suppress carryover when facts exist"
