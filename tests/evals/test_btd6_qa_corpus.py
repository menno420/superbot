"""Offline BTD6 QA-accuracy corpus check — the trustworthy "test all the
questions at once" layer.

For every :data:`GROUNDING_PROBES` entry this runs the REAL production grounding
(``btd6_context_service.build``) and asserts the answer-bearing fact is grounded
(``expect``) and the known wrong claim is not (``forbid``). It needs no API keys
and runs on every PR, so it proves — deterministically — that the bot retrieves
the right stored data for each corpus question. (The live model phrasing is the
separate paid ``scripts/run_evals.py --btd6`` layer.)
"""

from __future__ import annotations

import pytest
from tests.evals.btd6_corpus import GROUNDING_PROBES

from services import btd6_context_service


@pytest.mark.parametrize("probe", GROUNDING_PROBES, ids=lambda p: p.question)
async def test_corpus_question_grounds_its_answer(probe):
    ctx = await btd6_context_service.build(probe.question)
    blob = "\n".join(ctx.facts).lower()

    for needle in probe.expect:
        assert needle.lower() in blob, (
            f"{probe.question!r}: expected grounded fact containing {needle!r}"
            f"{' — ' + probe.note if probe.note else ''}.\nGrounded:\n" + blob
        )
    for bad in probe.forbid:
        assert bad.lower() not in blob, (
            f"{probe.question!r}: grounding must NOT contain {bad!r} "
            f"(a known wrong claim)."
        )


def test_corpus_is_nontrivial():
    """Guard against the corpus being silently emptied."""
    assert len(GROUNDING_PROBES) >= 10
    # Every probe names at least one expected fact.
    assert all(p.expect for p in GROUNDING_PROBES)


async def test_live_path_wiring_runs_offline():
    """The faithful live path (router → grounding → assemble → gateway → guard)
    must run end-to-end without raising even with no DB and no API key — it just
    degrades. This guards the wiring on every PR; the paid run needs real keys.
    """
    from tests.evals.btd6_live_path import run_live

    result = await run_live("can glue strike deal with DDTs")
    # No API key in CI → a degraded, non-crashing result through the real path.
    assert result.question
    assert result.task  # the real router classified it
    assert result.handled_by in {
        "model",
        "model_regenerated",
        "refused",
        "degraded",
    } or result.handled_by.startswith("floor:")
