"""Router pin: natural-language BTD6 question phrasings route to BTD6_ANSWER.

The user verified in production (PR #362 follow-up) that
``"what is the current boss?"`` was falling through to
``GENERAL_NL_ANSWER`` because the keyword list only had ``"boss bloon"``
and ``"boss event"`` — neither matched. This file pins the small set
of multi-word natural-question patterns that must route to BTD6 so
the AI block gatherer in ``btd6_ai_knowledge_block_service`` actually
fires for those messages.

Patterns deliberately stay multi-word so bare ``"boss"`` (workplace
boss, "be the boss") does not over-route.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import AITask  # noqa: E402
from services import ai_task_router  # noqa: E402


@pytest.mark.parametrize(
    "text",
    [
        "what is the current boss?",
        "what is the current race?",
        "what is the current event?",
        "what boss is on right now?",
        "what race is on right now?",
        "what odyssey is happening?",
        "is the active boss hard?",
        "any active race?",
    ],
)
def test_natural_btd6_questions_route_to_answer(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # These look BTD6-adjacent but are unambiguous non-BTD6 chatter and
    # must continue to route to the general handler.
    [
        "who is the boss of this server?",
        "what event is on the server right now?",
        "is the bot active?",
        "what's the active warn count?",
    ],
)
def test_non_btd6_lookalikes_still_route_to_general(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"


@pytest.mark.parametrize(
    "text",
    # Tower/hero names without explicit BTD6 keywords — these were falling
    # through to GENERAL_NL_ANSWER before the entity-alias fallback was added,
    # causing the AI to return no BTD6 facts.
    [
        "tell me about the bomb shooter",
        "what is bomb shooter",
        "how does bomb shooter work",
        "tell me about striker jones",
        "who is striker jones",
        "who is gwendolin",
        "how does dart monkey work",
        "what is the tack shooter",
        "who is sauda",
        "tell me about admiral brickell",
        "how does the heli pilot work",
    ],
)
def test_entity_name_questions_route_to_btd6_answer(text):
    """Tower/hero name mentions route to BTD6_ANSWER even without 'tower'/'hero'."""
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # Generic words that happen to overlap with BTD6 aliases must NOT
    # route to BTD6 — false positives degrade general chat.
    [
        "super cool idea",
        "the farm is great",
        "hello how are you",
    ],
)
def test_generic_words_do_not_over_route(text):
    """Common words that share BTD6 aliases must not trigger BTD6 routing."""
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"


@pytest.mark.parametrize(
    "text",
    # Distinctive BTD6 terms the entity-alias matcher provably MISSES, so
    # they fell through to GENERAL_NL_ANSWER (no grounding) — the AI PR2
    # grounding-gating regression. Verified against the dataset:
    #   * "obyn"      — hero "Obyn Greenfoot"; bare 4-char alias dropped by
    #                   the matcher's len(al) > 4 filter.
    #   * "desperado" — a real tower; single-word tower names are skipped.
    #   * impoppable / half cash — difficulty / mode.
    [
        "how do I use obyn",
        "is obyn good on chimps",
        "is desperado a sniper upgrade",
        "tell me about desperado",
        "impoppable tips",
        "half cash strategy",
    ],
)
def test_rewidened_btd6_terms_route_to_answer(text):
    """Re-widen #388's over-slim: these route back to BTD6_ANSWER so the
    grounding context is injected even when the model doesn't call the
    btd6_lookup tool.
    """
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # The re-widened terms must not over-route nearby general chatter.
    # "paragon" was deliberately left OUT of the keyword set precisely so
    # this legitimate English usage stays general.
    [
        "she is a paragon of virtue",
        "i only have half my cash left",  # not the exact 'half cash' phrase
    ],
)
def test_rewidened_terms_do_not_over_route_general_chat(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"


@pytest.mark.parametrize(
    "text",
    # BUG-0002 + BUG-0003 (live, 2026-06-11): boss-name and shorthand
    # questions fell through to the general path, where the model answered
    # from memory unguarded — "elite lych hp per tier" served the Standard
    # table labeled Elite; "10 041 despos … on impop" hallucinated despos =
    # Plasma Monkey Fan Club. Boss canonicals now come from the dataset;
    # "impop" / "despo" are curated keywords (substring → plurals covered).
    [
        "what is the hp of elite lych per tier",
        "how much health does bloonarius have at tier 3",
        "is dreadbloon immune to lead",
        "what does phayze do",
        "how much do 10 041 despos cost on impop",
        "despo best crosspath",
        "how much does a dart monkey cost on impop",
    ],
)
def test_boss_and_shorthand_questions_route_to_btd6_answer(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # r-shorthand rounds (live miss 2026-06-11, post-#703): "on r70 … end of
    # r53" routed general, so the model assembled tool numbers with no
    # number guard and presented cumulative(70) as the user's total. Two
    # r-round tokens — or one plus a money cue — read as BTD6 rounds talk.
    [
        "How much do I have on r70 if I had 26932 at the end of r53",
        "how much cash do i get from r40 to r80",
        "r63 and r76 are brutal",
        "how much money by r100",
    ],
)
def test_r_shorthand_round_questions_route_to_btd6_answer(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # The r-shorthand leg must not over-route ordinary chat: "r2d2" has no
    # digit boundary, and a lone "r 5" needs a money cue that these lack.
    [
        "r2d2 is my favourite droid",
        "there r 5 of us coming",
        "is r78 hard",  # single token, no money cue — stays conservative
    ],
)
def test_r_shorthand_does_not_over_route(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"


@pytest.mark.parametrize(
    "text",
    # Conversation-followup leg (live miss 2026-06-11): "does it make coins
    # at the end of the round?" — the checklist's own Tier-1.4 phrase — has
    # no BTD6 token, so the #668 carryover grounding (hosted on the BTD6
    # path) was unreachable. With the caller-observed conversation cue, a
    # pronoun follow-up question routes to BTD6 where carryover resolves it.
    [
        "does it make coins at the end of the round?",
        "does it earn money?",
        "how much do they cost",
        "is it any good against camo",
        "which of those items can damage lead",
    ],
)
def test_pronoun_followup_routes_btd6_with_conversation_cue(text):
    decision = ai_task_router.classify(text, conversation_btd6_context=True)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    [
        "does it make coins at the end of the round?",
        "does it earn money?",
    ],
)
def test_pronoun_followup_stays_general_without_cue(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"


@pytest.mark.parametrize(
    "text",
    # The cue must NOT btd6-route standalone questions with no follow-up
    # pronoun — a conversation-meta question in a BTD6-heavy channel stays
    # general ("what is the last message you can see", live 2026-06-11).
    [
        "what is the last message you can see",
        "can you tell me about the server",
        "thanks, that was great",  # pronoun "that" excluded on purpose
    ],
)
def test_conversation_cue_does_not_route_standalone_questions(text):
    decision = ai_task_router.classify(text, conversation_btd6_context=True)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"


@pytest.mark.parametrize(
    "text",
    # Short-alias + money-cue leg ("420 farm" live miss 2026-06-11): "farm"
    # is dropped from the entity matcher (≤4 chars) so the farm-economy
    # question froze the general path with unguarded freelance numbers.
    [
        "how much money does a 420 farm make",
        "how much cash does a banana farm make per round",
        "how much do farms make",
        "list all the ways you can increase your farm income",
    ],
)
def test_farm_money_questions_route_to_btd6_answer(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # The farm leg must not swallow the mining/economy chat that shares the
    # word: no money cue (cash|money|how much) → stays general.
    [
        "how do i farm coins",
        "best way to farm xp in the mine",
        "my farm is doing great",
    ],
)
def test_farm_without_money_cue_stays_general(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"


@pytest.mark.parametrize(
    "text",
    # Possessive/plural entity tokens ("what are geraldos items", live miss
    # 2026-06-11): the router's single-token set held "geraldo" but the
    # possessive token never matched, so the question froze the general path.
    # The de-s fold only applies to tokens >4 chars, keeping short ordinary
    # words out.
    [
        "what are geraldos items",
        "what are geraldo's items",
        "saudas best crosspath",
    ],
)
def test_possessive_entity_tokens_route_to_btd6_answer(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


def test_double_cash_keyword_routes():
    decision = ai_task_router.classify("does double cash affect tower prices")
    assert decision.task is AITask.BTD6_ANSWER


@pytest.mark.parametrize(
    "text",
    # BUG-0015 (live miss 2026-06-16): a paragon "degree" question carried no
    # router cue — "paragon" is excluded as English, single-word tower "dart"
    # is dropped — so it fell to the unguarded general path and the model
    # misread the "d67" shorthand as the upgrade path "0-6-7". A degree token
    # + a paragon reference (the word "paragon", or a resolving tower/paragon)
    # must route BTD6 so the per-degree stats ground.
    [
        "whats the damage of a d67 dart",  # degree shorthand + tower, no "paragon"
        "a d67 dart praragon",  # the verbatim screenshot phrasing (typo and all)
        "dart paragon at degree 67",  # spelled "degree" + the word "paragon"
        "glaive dominus d50 stats",  # a named paragon + the shorthand
        "how much damage does the ace paragon do at degree 80",
    ],
)
def test_paragon_degree_questions_route_to_btd6_answer(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # Conservatism: a degree token with NO paragon, or a paragon with NO degree
    # number, must NOT route on this leg — academic/temperature "degree" and
    # dice "d6" chatter, and conceptual paragon questions, stay general.
    [
        "i have a degree in computer science",  # degree, no paragon
        "its 67 degrees outside today",  # temperature ("degrees" after the number)
        "i rolled a d20 for initiative",  # tabletop dice, no paragon
        "what is a paragon of virtue",  # English "paragon", no degree number
        "how many degrees does a paragon have",  # paragon + "degrees" but no number
    ],
)
def test_degree_without_paragon_or_paragon_without_degree_stays_general(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"


@pytest.mark.parametrize(
    "text",
    # Live miss 2026-06-18: "which MK affects the sniper" routed GENERAL because
    # single-word tower aliases (sniper, boomerang, glue) are dropped from the
    # entity matcher, so the deterministic MK floor never ran and the model
    # grounding-refused. The "mk"/"monkey knowledge" cue + a tower alias (even a
    # short single word) must route BTD6 so the MK floor answers.
    [
        "which MK affects the sniper",
        "Which MK affects the sniper",
        "which monkey knowledge affects the boomerang",
        "what mk apply to the glue gunner",  # multi-word tower, still BTD6
        "which mk affects the dart monkey",
    ],
)
def test_mk_tower_questions_route_to_btd6_answer(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # Conservatism: the MK cue gate keeps non-BTD6 "mk"/tower-word chatter out.
    [
        "is mk11 a good game",  # "mk11" — no \bmk\b boundary, not BTD6
        "do you like the sniper rifle in cod",  # tower word, no MK cue
    ],
)
def test_mk_tower_conservatism_stays_general(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"
