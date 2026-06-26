"""Cross-domain AI-routing disjointness guard (the over-route harness).

`services.ai_task_router.classify` checks knowledge domains in a fixed priority
order — BTD6 first, then Project Moon (Limbus) — on the bare premise, stated only
in a code comment, that *"BTD6 keywords never collide with the distinctive Limbus
tokens"*. That premise was **asserted but never tested**, and the two detectors do
not even share match semantics: :func:`utils.btd6.keywords.has_btd6_context` is a
**substring** scan, while :func:`utils.projmoon.keywords.has_limbus_context` is a
**word-boundary** regex. A future keyword-set edit could therefore silently make a
Limbus question route to BTD6 (starving the projmoon grounding path) or a BTD6
phrase trip the Limbus detector — with no test to catch it.

This module is the **registry-driven over-route harness** flagged by two consecutive
Project Moon dispatch runs' session ideas (PR #1453 / PR #1469 logs). It pins three
properties of the multi-domain router so the next reference domain (Library of Ruina,
Lobotomy Corporation, …) is a one-line :data:`DOMAINS` registration, not a
re-derivation from source:

1. **Routing** — each domain's clean, single-domain sample questions route to exactly
   that domain's :class:`AITask`.
2. **Detector disjointness (the root guard)** — no domain's distinctive tokens trip
   any *other* domain's context detector, in **both** directions and across **all**
   domain pairs. This is the structural form of the router's comment.
3. **Priority is a total order** — when more than one domain could claim a phrase, the
   earlier domain in the documented priority order wins (BTD6 over Limbus), so adding a
   domain can never silently reorder an existing route.

Adding a domain: append a :class:`DomainRoute` to :data:`DOMAINS` (detector, the task a
clean question routes to, the bare distinctive tokens the detector keys on, and a few
single-domain sample questions). All three guards then cover it automatically.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import AITask  # noqa: E402
from services import ai_task_router  # noqa: E402
from utils.btd6.keywords import BTD6_CONTEXT_KEYWORDS, has_btd6_context  # noqa: E402
from utils.projmoon.keywords import (  # noqa: E402
    LIMBUS_CONTEXT_KEYWORDS,
    has_limbus_context,
)


@dataclass(frozen=True)
class DomainRoute:
    """One knowledge domain's routing contract, as the harness sees it.

    ``name`` — display name (test ids).
    ``detector`` — the curated ``has_<domain>_context`` predicate.
    ``expected_task`` — the task a clean single-domain question routes to.
    ``distinctive_tokens`` — the bare tokens the detector keys on (its keyword list);
      every one must be inert to every *other* domain's detector.
    ``sample_questions`` — clean, single-domain phrasings (no foreign-domain token).
    """

    name: str
    detector: Callable[[str], bool]
    expected_task: AITask
    distinctive_tokens: tuple[str, ...]
    sample_questions: tuple[str, ...]


# Priority order MATTERS: it mirrors the order `ai_task_router.classify` checks the
# domains (BTD6 first, then Limbus). The priority test below relies on this order.
DOMAINS: tuple[DomainRoute, ...] = (
    DomainRoute(
        name="btd6",
        detector=has_btd6_context,
        expected_task=AITask.BTD6_ANSWER,
        distinctive_tokens=BTD6_CONTEXT_KEYWORDS,
        sample_questions=(
            "how much does a dart monkey cost",
            "what is the best hero in btd6",
            "explain the moab class bloons",
            "how much cash do i get on round 40",
            "is obyn good for chimps",
            "what does a banana farm earn",
        ),
    ),
    DomainRoute(
        name="limbus",
        detector=has_limbus_context,
        expected_task=AITask.PROJMOON_ANSWER,
        distinctive_tokens=LIMBUS_CONTEXT_KEYWORDS,
        sample_questions=(
            "tell me about Limbus Company",
            "who is Heathcliff",
            "what does the ZAYIN grade mean",
            "list every sinner",
            "explain E.G.O grades",
            "what is a mirror dungeon",
        ),
    ),
)

# Ordinary chatter that must stay general — claimed by no domain detector.
_NEUTRAL_CHATTER: tuple[str, ...] = (
    "what time is the event tonight",
    "can you help me set up the server",
    "i sang a song at karaoke yesterday",
    "pride comes before a fall",
    "he is the new moderator here",
    "what's the weather like",
)


def _domain_id(domain: DomainRoute) -> str:
    return domain.name


@pytest.mark.parametrize("domain", DOMAINS, ids=_domain_id)
def test_sample_questions_route_to_their_domain(domain: DomainRoute) -> None:
    """Every clean single-domain question routes to that domain's task."""
    for question in domain.sample_questions:
        routed = ai_task_router.classify(question)
        assert routed.task is domain.expected_task, (
            f"{domain.name!r} sample {question!r} routed to "
            f"{routed.task.value!r}, expected {domain.expected_task.value!r}"
        )


@pytest.mark.parametrize("domain", DOMAINS, ids=_domain_id)
def test_sample_questions_are_claimed_only_by_their_own_detector(
    domain: DomainRoute,
) -> None:
    """A clean single-domain phrasing trips at most its own context detector.

    The literal "at most one domain claims each phrase" property — a sample that
    other detectors also claim is an over-route waiting to happen.
    """
    for question in domain.sample_questions:
        claimants = [d.name for d in DOMAINS if d.detector(question)]
        assert claimants in ([domain.name], []), (
            f"{domain.name!r} sample {question!r} is claimed by {claimants} — "
            "a clean single-domain phrasing must trip at most its own detector"
        )


def test_distinctive_tokens_do_not_trip_another_domains_detector() -> None:
    """The root guard: each domain's tokens are inert to every other detector.

    This is the structural form of the router's comment ("BTD6 keywords never
    collide with the distinctive Limbus tokens"), generalised to every ordered
    domain pair and both match semantics (BTD6 substring vs Limbus word-boundary).
    A future keyword-set edit that introduces a collision fails here.
    """
    collisions: list[str] = []
    for source in DOMAINS:
        for other in DOMAINS:
            if other is source:
                continue
            for token in source.distinctive_tokens:
                if other.detector(token):
                    collisions.append(
                        f"{source.name} token {token!r} trips the {other.name} detector"
                    )
    assert not collisions, "cross-domain detector collisions:\n  " + "\n  ".join(
        collisions
    )


@pytest.mark.parametrize("text", _NEUTRAL_CHATTER)
def test_neutral_chatter_is_claimed_by_no_domain(text: str) -> None:
    """Ordinary chatter trips no domain detector and routes general."""
    claimants = [d.name for d in DOMAINS if d.detector(text)]
    assert not claimants, f"neutral {text!r} wrongly claimed by {claimants}"
    routed = ai_task_router.classify(text)
    assert routed.task is AITask.GENERAL_NL_ANSWER


def test_priority_is_a_total_order_earlier_domain_wins() -> None:
    """When a phrase carries tokens from two domains, the earlier domain wins.

    Pins the documented tie-break (BTD6 is checked before Limbus) so adding a
    domain can never silently reorder an existing route. The phrase names a BTD6
    entity AND a Limbus token; it must route BTD6 by priority, not projmoon.
    """
    routed = ai_task_router.classify("compare the dart monkey to a limbus sinner")
    assert routed.task is AITask.BTD6_ANSWER
    # Both detectors genuinely fire on this phrase — i.e. the test exercises the
    # tie-break, not a case where only one detector matched.
    assert has_btd6_context("compare the dart monkey to a limbus sinner")
    assert has_limbus_context("compare the dart monkey to a limbus sinner")
