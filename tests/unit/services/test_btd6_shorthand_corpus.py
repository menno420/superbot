"""Class guard: the BTD6 community-shorthand vocabulary routes to BTD6_ANSWER.

Five live-reported bugs share **one root cause** — a community-shorthand question
is not recognised by ``ai_task_router.classify`` and falls through to the
**unguarded** ``GENERAL_NL_ANSWER`` path (no grounding, no number guard), where
the model freelances from memory:

    BUG-0001  "cash by round 68" round-cash phrasing  → refused / wrong total
    BUG-0003  ``despo`` / ``impop``                   → wrong tower
    BUG-0004  ``r53`` / ``r70`` round shorthand        → wrong cumulative total
    BUG-0008  ``420 farm`` + money cue                 → invented farm income
    BUG-0015  ``d67`` (paragon degree)                 → "0-6-7 paragon doesn't exist"

Each fix shipped its *own* per-bug regression test pinning *why* that leg exists.
This file is the missing **class guard**: it pins the whole known shorthand
vocabulary as a set, so a future router refactor (or a re-ordering of the
``_looks_like_*`` ladder) can't silently regress one shorthand back onto the
unguarded path — caught today only by a *new* live user report.

Routing-only: ``classify`` is a deterministic keyword/leg scan, so these cases
need no dataset or DB. The corpus deliberately avoids the entity-alias matcher
(hero/tower *names*) — that is a separate mechanism with its own pins
(``test_ai_task_router_btd6_natural.py``); this file guards the shorthand class.
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

# The canonical community-shorthand vocabulary. Each phrasing is self-contained
# (carries its own BTD6 cue) so the route does not depend on the dataset-backed
# entity matcher. Add a new shorthand here when a new ``_looks_like_*`` leg or
# keyword lands — this is the one obvious place.
SHORTHAND_CORPUS = [
    # BUG-0001 — round-cash phrasing ("round " keyword)
    "how much cash by round 68?",
    # BUG-0003 — Desperado / Impoppable shorthand (keywords)
    "cost on impop",
    "despo on impoppable?",
    "how many despos do i need",
    # BUG-0004 — "rNN" round shorthand (two tokens, or one + money cue)
    "how much do i have on r70 if i had 26932 at the end of r53",
    "whats my cash at r53 and r70",
    # BUG-0008 — short farm alias rescued behind a money cue
    "how much money does a 420 farm make",
    # BUG-0015 — "dNN" paragon degree shorthand
    "does a d67 dart paragon exist",
    "dart paragon at degree 67 stats",
]


# Deliberate look-alikes that must STAY on the general path — the conservatism
# half of every leg above. A regression that over-routes one of these is just as
# bad as one that under-routes a real shorthand.
CONSERVATISM_NEGATIVES = [
    "r2d2 is my favorite droid",  # digit→letter is no round boundary
    "its 67 degrees outside",  # temperature "degree", no paragon
    "i have a degree in cs",  # academic "degree", no paragon
    "how do i farm coins",  # mining/harvest "farm", no money cue match
    "there r 5 of us going",  # single "r N" token, no money cue
]


@pytest.mark.parametrize("text", SHORTHAND_CORPUS)
def test_shorthand_routes_to_btd6_answer(text):
    """Every known community shorthand must reach the guarded BTD6 path."""
    decision = ai_task_router.classify(text)
    assert decision.task is AITask.BTD6_ANSWER, (
        f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER — a known "
        "shorthand regressed onto the unguarded general path"
    )


@pytest.mark.parametrize("text", CONSERVATISM_NEGATIVES)
def test_lookalikes_stay_general(text):
    """The deliberate non-BTD6 look-alikes must not over-route."""
    decision = ai_task_router.classify(text)
    assert decision.task is AITask.GENERAL_NL_ANSWER, (
        f"{text!r} over-routed to {decision.task!r} instead of GENERAL_NL_ANSWER"
    )
