"""Central natural-language message stage (M2).

One pipeline owns "should the bot reply?" for every product
handler. Registered at ``order=70``. M5 retired the transitional
``AI_BTD6_VIA_ROUTER`` env var; the legacy BTD6 passive stage
stays unregistered so this stage is the only passive responder.

Flow per message:

    1. resolver:  ai_natural_language_policy.resolve()
    2. router:    ai_task_router.classify()
    3. feature:   for BTD6 → btd6_context_service.build()
    4. stack:     ai_instruction_service.assemble()
    5. gateway:   services.ai_gateway.execute()  (never raises; returns
                  a degraded :class:`AIResponse` when the provider path
                  fails — audit row records degraded vs skipped).
    6. audit:     ai_decision_audit_service.record()

Every code path through this stage produces exactly one
``ai_decision_audit`` row — denial, skip, reply, degrade, error.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord

from core.runtime.ai.contracts import AITask, PolicyDenialReason
from core.runtime.ai.feature_facts import FeatureFactRequest, FeatureFactsResult
from core.runtime.message_pipeline import MessagePipelineContext, StageResult

_VIDEO_TASKS = frozenset({AITask.VIDEO_DESCRIBE, AITask.VIDEO_COMPARE, AITask.VIDEO_QA})

if TYPE_CHECKING:
    from core.runtime.ai.contracts import AIResponse
from services import (
    ai_context_service,
    ai_conversation_service,
    ai_decision_audit_service,
    ai_instruction_service,
    ai_natural_language_policy,
    ai_permission_service,
    ai_task_router,
)
from services.ai_natural_language_policy import MessageContext

logger = logging.getLogger("bot.runtime.ai.natural_language_stage")

STAGE_NAME = "ai_natural_language"
STAGE_ORDER = 70


@dataclass
class AINaturalLanguageStage:
    """Single passive natural-language responder.

    The class is a simple registration target for
    :func:`core.runtime.message_pipeline.register`; the heavy
    lifting lives in the service modules so each piece is unit-
    testable in isolation.
    """

    name: str = STAGE_NAME
    order: int = STAGE_ORDER

    async def process(
        self,
        ctx: MessagePipelineContext,
    ) -> StageResult:
        message: discord.Message = ctx.message

        # Cheap pre-filter: only flow through when there is text.
        text = (message.content or "").strip()
        if not text:
            return StageResult()

        # Earlier stages may already have handled this message.
        if ctx.metadata.get("handled_by"):
            return StageResult()

        if message.guild is None:
            return StageResult()

        guild_id = message.guild.id
        channel_id = message.channel.id if message.channel else 0
        category_id = (
            getattr(message.channel, "category_id", None) if message.channel else None
        )
        user_id = message.author.id
        is_mention = ctx.bot.user is not None and ctx.bot.user.mentioned_in(message)

        # Chat memory: record every human message the stage sees,
        # whether or not the bot ends up replying. Skip command
        # prefixes so operator typos don't pollute the conversational
        # context. Bot messages are skipped by the earlier
        # ``handled_by`` short-circuit + the pipeline's own filtering;
        # we also guard against ``author.bot`` defensively here.
        if (
            not getattr(message.author, "bot", False)
            and not text.startswith("!")
            and not text.startswith("/")
        ):
            ai_conversation_service.append(
                guild_id,
                channel_id,
                user_id=user_id,
                role="user",
                text=text,
            )

        snap = await ai_permission_service.snapshot(guild_id, user_id)

        msg_ctx = MessageContext(
            guild_id=guild_id,
            channel_id=channel_id,
            category_id=category_id,
            user_id=user_id,
            user_level=snap.level,
            user_role_ids=tuple(
                role.id for role in getattr(message.author, "roles", ())
            ),
            is_mention=is_mention,
            is_fresh_user=snap.is_fresh_user,
        )
        decision = await ai_natural_language_policy.resolve(msg_ctx)

        # Route classification first so the audit row records both
        # the routed task and the resolver decision even when denied.
        routed = ai_task_router.classify(text)

        if not decision.allowed:
            await ai_decision_audit_service.record(
                guild_id=guild_id,
                channel_id=channel_id,
                category_id=category_id,
                user_id=user_id,
                message_id=message.id,
                task=routed.task.value,
                route=routed.route,
                decision="denied",
                reason_code=decision.reason_code,
                policy_snapshot_hash=decision.policy_snapshot_hash,
                instruction_profile_ids=list(decision.instruction_profile_ids) or None,
            )
            return StageResult()

        # Cooldown — checked after policy resolved so we can record
        # the rejection with the right reason code.
        if ai_permission_service.is_on_cooldown(
            guild_id,
            user_id,
            decision.effective_cooldown,
        ):
            await ai_decision_audit_service.record(
                guild_id=guild_id,
                channel_id=channel_id,
                category_id=category_id,
                user_id=user_id,
                message_id=message.id,
                task=routed.task.value,
                route=routed.route,
                decision="denied",
                reason_code=PolicyDenialReason.COOLDOWN_ACTIVE,
                policy_snapshot_hash=decision.policy_snapshot_hash,
            )
            return StageResult()

        try:
            _fact_req = FeatureFactRequest(
                task=routed.task,
                text=text,
                guild_id=guild_id,
                channel_id=channel_id,
                author_id=user_id,
                message_id=message.id,
            )
            feature = await _gather_feature_facts(_fact_req)

            # Video tasks: short-circuit when no grounding facts are available.
            # Must not call the AI provider with empty video context.
            if routed.task in _VIDEO_TASKS and not feature.facts:
                try:
                    await message.channel.send(
                        "I couldn't retrieve video information for that link.",
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                    await ai_decision_audit_service.record(
                        guild_id=guild_id,
                        channel_id=channel_id,
                        category_id=category_id,
                        user_id=user_id,
                        message_id=message.id,
                        task=routed.task.value,
                        route=routed.route,
                        decision="denied",
                        reason_code=feature.error_reason or "video_grounding_failed",
                        policy_snapshot_hash=decision.policy_snapshot_hash,
                    )
                except discord.HTTPException:
                    await ai_decision_audit_service.record(
                        guild_id=guild_id,
                        channel_id=channel_id,
                        category_id=category_id,
                        user_id=user_id,
                        message_id=message.id,
                        task=routed.task.value,
                        route=routed.route,
                        decision="errored",
                        reason_code="video_unavailable_reply_send_failed",
                        policy_snapshot_hash=decision.policy_snapshot_hash,
                    )
                ctx.metadata["handled_by"] = STAGE_NAME
                return StageResult(short_circuit=True)

            # Chat memory: gather recent channel turns (with optional
            # Discord history fallback). Best-effort — failure returns
            # an empty list and the stack assembles without recent
            # turns, preserving the prior behaviour.
            try:
                from services import ai_memory_service

                recent_turns = await ai_memory_service.gather_recent_turns(
                    guild_id=guild_id,
                    channel_id=channel_id,
                    channel=getattr(message, "channel", None),
                    bot_user_id=getattr(
                        getattr(ctx, "bot_user", None),
                        "id",
                        None,
                    ),
                )
            except Exception as exc:  # noqa: BLE001 — defensive
                logger.debug(
                    "ai_natural_language_stage: memory unavailable: %s",
                    exc,
                )
                recent_turns = []
            stack = await ai_instruction_service.assemble(
                guild_id=guild_id,
                user_message=text,
                profile_ids=decision.instruction_profile_ids,
                retrieved_facts=list(feature.facts),
                recent_turns=recent_turns,
            )
            correlation_id = uuid.uuid4().hex
            built = ai_context_service.build(
                task=routed.task,
                guild_id=guild_id,
                actor_id=user_id,
                channel_id=channel_id,
                correlation_id=correlation_id,
            )

            response = await _invoke_gateway(stack, built, ctx)
        except Exception:
            logger.exception(
                "ai_natural_language_stage: feature pipeline raised "
                "for guild=%s channel=%s message=%s",
                guild_id,
                channel_id,
                message.id,
            )
            await ai_decision_audit_service.record(
                guild_id=guild_id,
                channel_id=channel_id,
                category_id=category_id,
                user_id=user_id,
                message_id=message.id,
                task=routed.task.value,
                route=routed.route,
                decision="errored",
                reason_code=PolicyDenialReason.PROVIDER_UNAVAILABLE,
                policy_snapshot_hash=decision.policy_snapshot_hash,
                instruction_profile_ids=(
                    list(stack.instruction_profile_ids) if "stack" in locals() else None
                ),
            )
            return StageResult()

        reply_text = (response.text or "").strip()
        if not reply_text:
            # Differentiate "provider degraded" (gateway/provider failure)
            # from "model returned empty text" (genuine skip) so operators
            # can tell them apart in the audit table.
            if response.degraded:
                audit_decision = "degraded"
                audit_reason = PolicyDenialReason.PROVIDER_UNAVAILABLE
            else:
                audit_decision = "skipped"
                audit_reason = PolicyDenialReason.NO_ROUTE_MATCHED
            await ai_decision_audit_service.record(
                guild_id=guild_id,
                channel_id=channel_id,
                category_id=category_id,
                user_id=user_id,
                message_id=message.id,
                task=routed.task.value,
                route=routed.route,
                decision=audit_decision,
                reason_code=audit_reason,
                policy_snapshot_hash=decision.policy_snapshot_hash,
                instruction_profile_ids=list(stack.instruction_profile_ids) or None,
                provider=response.provider or None,
                model=response.model or None,
            )
            return StageResult()

        from core.runtime.ai import response_renderer_registry

        rendered = await response_renderer_registry.render(
            routed.task, response, _fact_req, feature.render_context
        )

        try:
            if rendered is not None:
                await message.channel.send(
                    content=rendered.content,
                    embed=rendered.embed,
                    allowed_mentions=rendered.allowed_mentions or discord.AllowedMentions.none(),
                )
            else:
                await message.channel.send(
                    reply_text,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
        except discord.HTTPException:
            logger.exception(
                "ai_natural_language_stage: send failed for guild=%s "
                "channel=%s message=%s",
                guild_id,
                channel_id,
                message.id,
            )
            await ai_decision_audit_service.record(
                guild_id=guild_id,
                channel_id=channel_id,
                category_id=category_id,
                user_id=user_id,
                message_id=message.id,
                task=routed.task.value,
                route=routed.route,
                decision="errored",
                reason_code=(
                    "video_response_send_failed" if routed.task in _VIDEO_TASKS
                    else "response_send_failed"
                ),
                policy_snapshot_hash=decision.policy_snapshot_hash,
                instruction_profile_ids=list(stack.instruction_profile_ids) or None,
                provider=response.provider or None,
                model=response.model or None,
            )
            return StageResult()

        ai_permission_service.mark_reply_sent(guild_id, user_id)
        # The AI cog's on_message listener owns user-message recording
        # so chat memory captures bystander messages too. The stage
        # only records its own assistant reply.
        ai_conversation_service.append(
            guild_id,
            channel_id,
            user_id=user_id,
            role="assistant",
            text=reply_text,
        )

        await ai_decision_audit_service.record(
            guild_id=guild_id,
            channel_id=channel_id,
            category_id=category_id,
            user_id=user_id,
            message_id=message.id,
            task=routed.task.value,
            route=routed.route,
            decision="replied",
            reason_code=PolicyDenialReason.NONE,
            policy_snapshot_hash=decision.policy_snapshot_hash,
            instruction_profile_ids=list(stack.instruction_profile_ids) or None,
            provider=response.provider or None,
            model=response.model or None,
        )

        ctx.metadata["handled_by"] = STAGE_NAME
        return StageResult(short_circuit=True)


async def _gather_feature_facts(req: FeatureFactRequest) -> FeatureFactsResult:
    """Hand off to the feature owner for fact retrieval.

    BTD6 routes through btd6_context_service; VIDEO tasks through
    youtube_context_service (feature-flag gated).  Other tasks return
    empty facts and the gateway answers from the instruction stack alone.
    """
    if req.task is AITask.BTD6_ANSWER:
        from services import btd6_context_service

        ctx = await btd6_context_service.build(req.text)
        return FeatureFactsResult(facts=tuple(ctx.facts))
    if req.task in _VIDEO_TASKS:
        from services import youtube_context_service

        ctx = await youtube_context_service.build(req)
        if not ctx.facts:
            return FeatureFactsResult(facts=(), render_context=None, error_reason=ctx.error_reason)
        return FeatureFactsResult(facts=ctx.facts, render_context=ctx)
    return FeatureFactsResult(facts=())


async def _invoke_gateway(
    stack: ai_instruction_service.InstructionStack,
    built: ai_context_service.BuiltContext,
    _ctx: MessagePipelineContext,
) -> AIResponse:
    """Run the AI gateway and return the full :class:`AIResponse`.

    The gateway never raises (it converts every error into a degraded
    :class:`AIResponse`), so this helper has no local exception
    handling — any exception that escapes is a gateway contract
    violation and propagates to the outer handler in
    :meth:`AINaturalLanguageStage.process` which audits it as
    ``errored / PROVIDER_UNAVAILABLE``.
    """
    from core.runtime.ai.contracts import AIRequest, AIResponseMode
    from services import ai_gateway

    request = AIRequest(
        context=built.request_context,
        system_prompt=stack.render_system_prompt(),
        payload={"text": stack.render_payload_text()},
        mode=AIResponseMode.TEXT,
    )
    return await ai_gateway.execute(request)


# Convenience export used by AICog.cog_load when wiring the stage in.
def get_stage() -> AINaturalLanguageStage:
    return AINaturalLanguageStage()


__all__ = [
    "AINaturalLanguageStage",
    "STAGE_NAME",
    "STAGE_ORDER",
    "get_stage",
]


# Compile-time timestamp for diagnostics; placed last so import-time
# errors elsewhere don't depend on this value.
_BUILD_TIMESTAMP = int(time.time())
