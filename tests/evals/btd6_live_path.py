"""Faithful "exactly live" BTD6 eval — replays the REAL production answer path.

The standard harness probes the model with a hand-built prompt. This runner
instead drives the *same components the live ``AINaturalLanguageStage`` uses*, in
the same order, so a result here is what a real Discord user would get:

1. ``ai_task_router.classify`` — the real router (so a mis-route shows up).
2. ``btd6_context_service.build`` — the real grounding facts.
3. ``ai_instruction_service.assemble`` — the real instruction stack (system
   prompt + payload), not a hand-written one.
4. ``natural_language_stage._invoke_gateway`` — the real gateway call (tools,
   orchestration policy, round-cash workflow, ledger) against the configured
   provider.
5. ``btd6_grounding_service.validate_btd6_reply`` + ``_build_grounding_constraint``
   — the real faithfulness guard with the real regenerate-once, then the real
   deterministic refusal. A hallucinated reply is rejected here exactly as live.

The ONLY things not reproduced are Discord I/O and the decision audit (neither
changes the answer text). It reuses production internals on purpose — that is
what keeps it from drifting away from live behaviour. Keep the order in
:func:`run_live` in step with ``AINaturalLanguageStage.process``.

Grading is semantic: each reply is judged by the same ``llm_judge`` the golden
set uses, against the probe's ``rubric`` (the model paraphrases, so substring
matching the grounded-fact wording gives false negatives). A refusal or a known
wrong claim is a fail.

**Known limitation — DB-backed workflow answers.** ``_invoke_gateway`` degrades
the DB-backed bits when no DB is present, so questions whose live answer depends
on the round-cash *workflow* (which only engages under a DB-resolved orchestration
profile) can't be reproduced in a DB-less CI run — they will refuse. The corpus
therefore covers interaction / immunity / damage-type questions (no DB workflow),
not "cash on round N" questions. Run with a real key + ``AI_DEFAULT_PROVIDER``
set; opt-in/paid via ``scripts/run_evals.py --btd6``.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from types import SimpleNamespace

from tests.evals.btd6_corpus import GROUNDING_PROBES, GroundingProbe

from core.runtime.ai.contracts import AIScope, AITask

# Fixed fake identity (mirrors the harness): no real guild/DB is touched.
_EVAL_GUILD_ID = 1
_EVAL_ACTOR_ID = 1
_EVAL_CHANNEL_ID = 1


@dataclass(frozen=True)
class LiveResult:
    question: str
    task: str
    reply: str
    handled_by: str  # model | model_regenerated | refused | floor:<kind> | degraded
    degraded: bool
    provider: str | None
    model: str | None


async def run_live(question: str) -> LiveResult:
    """Replay one question through the real production answer path."""
    from core.runtime.ai import natural_language_stage as nls
    from core.runtime.ai.redaction import redact_text
    from services import (
        ai_context_service,
        ai_instruction_service,
        ai_task_router,
        btd6_context_service,
        btd6_grounding_service,
    )

    routed = ai_task_router.classify(question)

    # Pre-model deterministic floors the stage serves WITHOUT the model. For the
    # interaction/knowledge corpus these rarely fire, but checking them keeps the
    # replay honest (a list/roster question is answered deterministically, live).
    for floor in (
        btd6_context_service.deterministic_btd6_list_reply,
        btd6_context_service.deterministic_bloon_roster_reply,
        btd6_context_service.deterministic_bloon_modifier_reply,
    ):
        try:
            text = floor(question)
        except Exception:  # noqa: BLE001 — a floor must never break the replay
            text = None
        if text:
            return LiveResult(
                question,
                routed.task.value,
                text,
                f"floor:{floor.__name__}",
                False,
                "deterministic",
                None,
            )

    ctx = await btd6_context_service.build(question)
    facts = tuple(ctx.facts)
    stack = await ai_instruction_service.assemble(
        guild_id=_EVAL_GUILD_ID,
        user_message=question,
        profile_ids=(),
        retrieved_facts=list(facts),
        recent_turns=[],
        bot_user_id=None,
        bot_knowledge_blocks=[],
    )
    built = ai_context_service.build(
        task=routed.task,
        guild_id=_EVAL_GUILD_ID,
        actor_id=_EVAL_ACTOR_ID,
        channel_id=_EVAL_CHANNEL_ID,
        correlation_id=uuid.uuid4().hex,
        scope=AIScope.USER,
    )
    # _invoke_gateway only reads `.message`/`.bot` off the pipeline ctx (via
    # getattr) to bind server-introspection tools; a stub with both None gives
    # the same toolset a DM-less knowledge question gets.
    stub_ctx = SimpleNamespace(message=None, bot=None)
    ledger: list[str] = []

    response = await nls._invoke_gateway(stack, built, stub_ctx, ledger=ledger)
    reply = redact_text((response.text or "").strip()).value
    handled = "model"

    # The real BTD6 faithfulness guard + regenerate-once + refusal.
    if routed.task is AITask.BTD6_ANSWER or (
        routed.task is AITask.GENERAL_NL_ANSWER
        and btd6_grounding_service.general_path_should_verify(question, reply)
    ):
        verdict = btd6_grounding_service.validate_btd6_reply(
            reply,
            facts=facts,
            tool_results=tuple(ledger),
            task=routed.task,
        )
        if not verdict.grounded:
            response = await nls._invoke_gateway(
                stack,
                built,
                stub_ctx,
                ledger=ledger,
                grounding_constraint=nls._build_grounding_constraint(verdict),
            )
            retry = redact_text((response.text or "").strip()).value
            retry_ok = (
                retry
                and btd6_grounding_service.validate_btd6_reply(
                    retry,
                    facts=facts,
                    tool_results=tuple(ledger),
                    task=routed.task,
                ).grounded
            )
            if retry_ok:
                reply, handled = retry, "model_regenerated"
            else:
                reply, handled = nls._btd6_no_data_refusal(), "refused"

    return LiveResult(
        question,
        routed.task.value,
        reply,
        handled,
        response.degraded,
        response.provider,
        response.model,
    )


@dataclass
class LiveOutcome:
    probe: GroundingProbe
    result: LiveResult
    passed: bool
    detail: str


async def _grade(probe: GroundingProbe, result: LiveResult) -> tuple[bool, str]:
    """Grade the LIVE reply: refusal/degrade → fail; a known wrong claim → fail;
    otherwise judge correctness SEMANTICALLY (the model paraphrases, so a
    substring match against the grounded-fact wording gives false negatives —
    that was the original mis-grade). Uses the same LLM-as-judge the golden set
    uses, against the probe's rubric.
    """
    if result.degraded:
        return False, f"degraded ({result.provider})"
    if result.handled_by == "refused":
        return False, "live bot REFUSED (guard rejected the model's answer)"
    low = result.reply.lower()
    bad = [s for s in probe.forbid if s.lower() in low]
    if bad:
        return False, f"stated wrong claim: {bad[0]!r}"
    if not probe.rubric:
        # No rubric → fall back to the offline-style substring check.
        missing = [s for s in probe.expect if s.lower() not in low]
        return (not missing), (
            result.handled_by if not missing else f"missing {missing[0]!r}"
        )
    from tests.evals.graders import llm_judge

    grade = await llm_judge(probe.rubric)(SimpleNamespace(text=result.reply))
    return grade.passed, (result.handled_by if grade.passed else grade.detail)


async def run_btd6_live_suite() -> list[LiveOutcome]:
    """Replay every corpus probe through the live path and grade the reply."""
    outcomes: list[LiveOutcome] = []
    for probe in GROUNDING_PROBES:
        try:
            result = await run_live(probe.question)
        except Exception as exc:  # noqa: BLE001 — one bad probe must not abort
            result = LiveResult(
                probe.question,
                "error",
                f"<error: {exc}>",
                "error",
                True,
                None,
                None,
            )
        passed, detail = await _grade(probe, result)
        outcomes.append(LiveOutcome(probe, result, passed, detail))
    return outcomes


def render_live_report(outcomes: list[LiveOutcome]) -> str:
    passed = sum(1 for o in outcomes if o.passed)
    total = len(outcomes)
    provider = next((o.result.provider for o in outcomes if o.result.provider), "?")
    lines = [
        "",
        "BTD6 live-path scorecard (real grounding + assemble + gateway + guard)",
        "=" * 68,
        f"provider: {provider}   {passed}/{total} passed "
        f"({(100.0 * passed / total) if total else 0:.0f}%)",
        "",
    ]
    for o in outcomes:
        mark = "✓" if o.passed else "✗"
        lines.append(f"  {mark} [{o.result.handled_by:>17}] {o.probe.question}")
        if not o.passed:
            lines.append(f"      → {o.detail}")
            lines.append(f"      reply: {o.result.reply[:140]}")
    return "\n".join(lines)


def live_suite_available() -> bool:
    """A real provider key must be present for the live suite to mean anything."""
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))


__all__ = [
    "LiveOutcome",
    "LiveResult",
    "render_live_report",
    "run_btd6_live_suite",
    "run_live",
    "live_suite_available",
]
