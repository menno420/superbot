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
import re
import time
import uuid
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord

from core.runtime.ai.contracts import AIScope, AITask, PolicyDenialReason
from core.runtime.ai.feature_facts import FeatureFactRequest, FeatureFactsResult
from core.runtime.message_pipeline import MessagePipelineContext, StageResult
from services import (
    ai_context_service,
    ai_conversation_service,
    ai_decision_audit_service,
    ai_instruction_service,
    ai_natural_language_policy,
    ai_permission_service,
    ai_review_log_service,
    ai_task_router,
)
from services.ai_natural_language_policy import MessageContext

if TYPE_CHECKING:
    from collections.abc import Mapping

    from core.runtime.ai.contracts import AIResponse
    from core.runtime.ai.providers.base import ToolHandler
    from services import btd6_grounding_service

_VIDEO_TASKS = frozenset({AITask.VIDEO_DESCRIBE, AITask.VIDEO_COMPARE, AITask.VIDEO_QA})

logger = logging.getLogger("bot.runtime.ai.natural_language_stage")

STAGE_NAME = "ai_natural_language"
STAGE_ORDER = 70


def _accessible_channel_ids_for(
    member: object | None,
    guild: object | None,
) -> frozenset[int]:
    """Return the set of text-channel ids ``member`` can view in ``guild``.

    Used by the audit-block path so we only render references to
    channels the asker can already see. Returns an empty set on any
    exception so the calling block falls back to "channel unavailable"
    rather than leaking metadata about a channel the user lacks
    access to.
    """
    if guild is None or member is None:
        return frozenset()
    try:
        channels = list(getattr(guild, "text_channels", ()) or ())
    except Exception:  # noqa: BLE001 — defensive
        return frozenset()
    accessible: set[int] = set()
    for channel in channels:
        try:
            perms_for = channel.permissions_for(member)
        except Exception:  # noqa: BLE001, S112 — defensive per-channel
            continue
        if bool(getattr(perms_for, "view_channel", False)):
            channel_id = getattr(channel, "id", None)
            if channel_id is not None:
                try:
                    accessible.add(int(channel_id))
                except (TypeError, ValueError):
                    continue
    return frozenset(accessible)


class _NullAsyncContext:
    """Async no-op context — the fallback when a channel has no typing().

    ``contextlib.nullcontext`` only implements the *sync* protocol, so it
    cannot stand in for ``async with``; this tiny class does.
    """

    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *exc: object) -> bool:
        return False


def _maybe_typing(channel: object) -> AbstractAsyncContextManager[None]:
    """Return ``channel.typing()`` if available, else an async no-op.

    Showing the typing indicator while the (potentially multi-second)
    provider call runs makes the bot feel responsive instead of silent.
    Best-effort: a channel type without ``typing()`` (or a duck-typed
    test channel) falls back to a null context so the stage never
    depends on it.
    """
    typing = getattr(channel, "typing", None)
    if callable(typing):
        try:
            return typing()  # type: ignore[no-any-return]
        except Exception:  # noqa: BLE001 — never let UX polish break a reply
            return _NullAsyncContext()
    return _NullAsyncContext()


def _is_direct_bot_mention(
    message: discord.Message,
    bot_user: object | None,
) -> bool:
    """True only when the bot is *directly, personally* mentioned.

    discord.py's :meth:`ClientUser.mentioned_in` returns ``True`` for an
    ``@everyone``/``@here`` blast (it short-circuits on
    ``message.mention_everyone``), so a server-wide ping would read as a
    personal mention and flip the ``mention_only`` policy gate open
    (BUG-0019 #2 — the "false personal ping" class). We instead test
    membership of the bot's own id in ``message.mentions``, so only a
    literal ``<@bot_id>`` token counts — never an ``@everyone``/``@here``
    blast. Defensive: a missing bot id or a non-iterable ``mentions``
    (a duck-typed test double) yields ``False`` rather than raising.
    """
    bot_id = getattr(bot_user, "id", None)
    if bot_id is None:
        return False
    try:
        mentioned = list(getattr(message, "mentions", None) or ())
    except TypeError:
        return False
    return any(getattr(member, "id", None) == bot_id for member in mentioned)


def _strip_bot_mention(text: str, *, bot_user_id: int | None) -> str:
    """Remove all mentions of the bot from ``text``.

    Discord mentions are ``<@id>`` or ``<@!id>``. Each match plus the
    spaces/tabs hugging it collapses to a single space so an inline
    mention like ``"hey <@id> what's up"`` becomes ``"hey what's up"``
    rather than leaving a double space. Newlines are preserved so the
    layout of a multi-line question is not flattened. A bare-mention
    message still collapses to ``""`` after the surrounding strip.
    """
    if bot_user_id is None:
        return text
    return re.sub(rf"[ \t]*<@!?{bot_user_id}>[ \t]*", " ", text).strip()


def _record_user_turn_if_visible(
    message: discord.Message,
    text: str,
    *,
    guild_id: int,
    channel_id: int,
    user_id: int,
    is_mention: bool,
    record_mentions: bool,
) -> bool:
    """Append ``text`` to the conversation buffer when visibility rules allow.

    Single deterministic owner for memory writes from the stage. The
    raw ``text`` (not the mention-stripped form) is what gets stored
    so memory reflects what the user actually typed.

    ``record_mentions`` selects which message *kind* this call owns, so
    a single message is never recorded twice across the two recording
    phases in :meth:`AINaturalLanguageStage.process`:

    * ``record_mentions=False`` — the bystander pre-record. Records only
      NON-mention messages (the mention is recorded later, after the
      recent-turn buffer has been gathered, so it cannot appear in the
      context for its own reply).
    * ``record_mentions=True`` — the triggering-mention record. Records
      only mention messages; non-mentions were already captured by the
      bystander phase.

    Returns ``True`` if the turn was appended.
    """
    if getattr(message.author, "bot", False):
        return False
    if text.startswith("!") or text.startswith("/"):
        return False
    if is_mention != record_mentions:
        return False
    ai_conversation_service.append(
        guild_id,
        channel_id,
        user_id=user_id,
        role="user",
        text=text,
        display_name=getattr(message.author, "display_name", None),
    )
    return True


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
        raw_text = (message.content or "").strip()
        if not raw_text:
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
        is_mention = _is_direct_bot_mention(message, ctx.bot.user)
        bot_user_id = getattr(getattr(ctx.bot, "user", None), "id", None)

        # The model sees the message with the bot mention stripped out
        # so the ``current_user_message`` span is the user's actual
        # question — never a noisy ``<@id>`` token. Memory still
        # records the raw form below.
        user_text = _strip_bot_mention(raw_text, bot_user_id=bot_user_id)

        # Chat memory (bystander pre-record): record non-mention
        # messages the stage sees, whether or not the bot ends up
        # replying. The triggering mention is recorded later — once,
        # after ``gather_recent_turns`` has run — so it cannot appear
        # in the recent-turn context for its own response.
        _record_user_turn_if_visible(
            message,
            raw_text,
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            is_mention=is_mention,
            record_mentions=False,
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
        # The conversation cue lets an entity-less follow-up ("does IT
        # make coins…?") reach the BTD6 path where the carryover
        # grounding lives — the floor holds only the PRIOR turns here
        # (this message is recorded after gathering, below). Best-effort:
        # a cue failure must never block routing.
        conversation_btd6 = False
        try:
            from utils.btd6.keywords import has_btd6_context

            conversation_btd6 = any(
                has_btd6_context(turn.text)
                for turn in ai_conversation_service.recent_turns(
                    guild_id,
                    channel_id,
                )
            )
        except Exception:  # noqa: BLE001 — defensive: cue only
            logger.debug(
                "ai_natural_language_stage: conversation cue unavailable",
                exc_info=True,
            )
        routed = ai_task_router.classify(
            raw_text,
            conversation_btd6_context=conversation_btd6,
        )

        if not decision.allowed:
            # Record the triggering mention exactly once before the
            # denial return so future turns retain context. Non-mention
            # bystander messages were already recorded above.
            _record_user_turn_if_visible(
                message,
                raw_text,
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                is_mention=is_mention,
                record_mentions=True,
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
            _record_user_turn_if_visible(
                message,
                raw_text,
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                is_mention=is_mention,
                record_mentions=True,
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
                reason_code=PolicyDenialReason.COOLDOWN_ACTIVE,
                policy_snapshot_hash=decision.policy_snapshot_hash,
            )
            return StageResult()

        # Bare-mention guard: a message like "<@BOT_ID>" collapses to
        # empty after mention-stripping. Do not send an empty
        # current_user_message to the model. Record the mention to
        # memory and audit a clean skip.
        if not user_text:
            _record_user_turn_if_visible(
                message,
                raw_text,
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                is_mention=is_mention,
                record_mentions=True,
            )
            await ai_decision_audit_service.record(
                guild_id=guild_id,
                channel_id=channel_id,
                category_id=category_id,
                user_id=user_id,
                message_id=message.id,
                task=routed.task.value,
                route=routed.route,
                decision="skipped",
                reason_code=PolicyDenialReason.EMPTY_MESSAGE,
                policy_snapshot_hash=decision.policy_snapshot_hash,
                instruction_profile_ids=list(decision.instruction_profile_ids) or None,
            )
            return StageResult()

        # Vetted answer preset (operator-authored) — the cheapest possible
        # answer: an exact normalized-question match is served verbatim with
        # ZERO model call (the ai_review_log answer loop's preset layer,
        # services/ai_preset_service.py). Fires before feature-facts / gateway.
        # Fail-safe: a lookup miss/outage returns None and the normal model path
        # runs, so behaviour is byte-identical when no preset matches. The Q&A is
        # still remembered so a later 👎 / correction on a preset reply is logged.
        from services import ai_preset_service

        preset_answer = await ai_preset_service.lookup(guild_id, user_text)
        if preset_answer:
            preset_sent = None
            try:
                reference = message.to_reference(fail_if_not_exists=False)
                for index, chunk in enumerate(_split_for_discord(preset_answer)):
                    sent = await message.channel.send(
                        chunk,
                        allowed_mentions=discord.AllowedMentions.none(),
                        reference=reference if index == 0 else None,
                    )
                    if index == 0:
                        preset_sent = sent
            except discord.HTTPException:
                logger.warning(
                    "ai preset reply send failed for message=%s",
                    getattr(message, "id", None),
                    exc_info=True,
                )
            _record_user_turn_if_visible(
                message,
                raw_text,
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                is_mention=is_mention,
                record_mentions=True,
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
            )
            if preset_sent is not None:
                ai_review_log_service.remember_answer(
                    preset_sent.id,
                    guild_id=guild_id,
                    channel_id=channel_id,
                    user_id=user_id,
                    message_id=message.id,
                    question=raw_text,
                    answer=preset_answer,
                    task=routed.task.value,
                    route="preset",
                    provider=None,
                    model=None,
                )
            ctx.metadata["handled_by"] = STAGE_NAME
            return StageResult(short_circuit=True)

        try:
            _fact_req = FeatureFactRequest(
                task=routed.task,
                text=raw_text,
                guild_id=guild_id,
                channel_id=channel_id,
                author_id=user_id,
                message_id=message.id,
                conversation_followup=getattr(routed, "via_conversation_cue", False),
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

            # BUG-0009 ("grounded facts, wrong assembly"): answer a clear
            # deterministic list question — "which Monkey Knowledge relate to
            # <tower>?", "what does Geraldo unlock per level?" — BEFORE the
            # model. The model groups/labels these individually-grounded lists
            # incorrectly, and because every value is grounded the post-hoc
            # faithfulness floor never catches a mis-*grouping* — so the
            # deterministic layer must OWN the labelled list. The dispatcher
            # returns None for single-entity lookups / strategy / anything
            # outside an exact list shape, which fall through to the model.
            if routed.task is AITask.BTD6_ANSWER:
                list_reply: str | None = None
                try:
                    from services import btd6_context_service

                    list_reply = btd6_context_service.deterministic_btd6_list_reply(
                        raw_text,
                    )
                except Exception:  # noqa: BLE001 — never break the reply path
                    logger.warning(
                        "btd6 deterministic list floor build failed",
                        exc_info=True,
                    )
                if list_reply:
                    try:
                        reference = message.to_reference(fail_if_not_exists=False)
                        for index, chunk in enumerate(_split_for_discord(list_reply)):
                            await message.channel.send(
                                chunk,
                                allowed_mentions=discord.AllowedMentions.none(),
                                reference=reference if index == 0 else None,
                            )
                    except discord.HTTPException:
                        logger.warning(
                            "btd6 deterministic list floor send failed for message=%s",
                            getattr(message, "id", None),
                            exc_info=True,
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
                    bot_user_id=bot_user_id,
                )
            except Exception:  # noqa: BLE001 — defensive
                # Warning, not debug: the reply still proceeds without
                # recent context, but a persistent failure here silently
                # degrades every reply, so it must be visible in prod logs.
                logger.warning(
                    "ai_natural_language_stage: memory unavailable; replying "
                    "without recent context (guild=%s channel=%s)",
                    guild_id,
                    channel_id,
                    exc_info=True,
                )
                recent_turns = []

            # Record the triggering mention exactly once, AFTER the
            # gather above has captured the prior buffer. The mention
            # therefore cannot appear in its own recent-turn context.
            _record_user_turn_if_visible(
                message,
                raw_text,
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                is_mention=is_mention,
                record_mentions=True,
            )

            bot_knowledge_blocks = await _gather_bot_knowledge_blocks(
                message,
                user_text=user_text,
                task=routed.task,
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
            )

            stack = await ai_instruction_service.assemble(
                guild_id=guild_id,
                user_message=user_text,
                profile_ids=decision.instruction_profile_ids,
                retrieved_facts=list(feature.facts),
                recent_turns=recent_turns,
                bot_user_id=bot_user_id,
                bot_knowledge_blocks=bot_knowledge_blocks,
            )
            correlation_id = uuid.uuid4().hex
            built = ai_context_service.build(
                task=routed.task,
                guild_id=guild_id,
                actor_id=user_id,
                channel_id=channel_id,
                correlation_id=correlation_id,
                scope=_derive_scope(message),
            )

            # BTD6 faithfulness ledger: approved BTD6 tool results are
            # captured here so the post-generation verifier can ground the
            # reply against them (alongside the auto-grounding facts).
            ledger: list[str] = []
            # Show "Bot is typing…" while the provider call runs so a
            # multi-second reply does not look like a dropped message.
            async with _maybe_typing(message.channel):
                response = await _invoke_gateway(stack, built, ctx, ledger=ledger)
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
            await ai_review_log_service.record_unknown(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                message_id=message.id,
                task=routed.task.value,
                route=routed.route,
                reason_code="errored",
                question=raw_text,
                answer=None,
            )
            return StageResult()

        reply_text = (response.text or "").strip()
        if not reply_text:
            # Differentiate "provider degraded" (gateway/provider failure)
            # from "model returned empty text" (genuine skip) so operators
            # can tell them apart in the audit table. A *healthy* empty reply
            # to an in-domain BTD6 question is a no-data case: serve the
            # deterministic, version-stamped refusal rather than silence.
            # ``GROUNDING_FAILED`` is reserved for healthy paths — a provider
            # outage stays ``PROVIDER_UNAVAILABLE``.
            sent_refusal = False
            if response.degraded:
                audit_decision = "degraded"
                audit_reason = PolicyDenialReason.PROVIDER_UNAVAILABLE
            elif routed.task is AITask.BTD6_ANSWER:
                # Healthy but empty on an in-domain BTD6 question: serve the
                # deterministic roster for a list request, else the refusal.
                audit_decision, audit_reason = await _serve_btd6_floor(
                    message,
                    raw_text,
                )
                sent_refusal = True
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
            await ai_review_log_service.record_unknown(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                message_id=message.id,
                task=routed.task.value,
                route=routed.route,
                reason_code=getattr(audit_reason, "value", str(audit_reason)),
                question=raw_text,
                answer=None,
                provider=response.provider or None,
                model=response.model or None,
            )
            if sent_refusal:
                ctx.metadata["handled_by"] = STAGE_NAME
                return StageResult(short_circuit=True)
            return StageResult()

        # Outbound redaction: scrub Discord snowflakes and other
        # sensitive-token patterns from the model's reply before it
        # is sent to Discord OR recorded into conversation memory.
        # Placed after the empty-reply guard so empty responses still
        # take the degraded/skipped path above unchanged.
        from core.runtime.ai.redaction import redact_text

        reply_text = redact_text(reply_text).value

        # ---- BTD6 faithfulness guard ----------------------------------------
        # A BTD6 answer (or a BTD6-themed general reply that names an entity)
        # must not state names/numbers absent from the grounded payload
        # (auto-grounding facts ∪ approved BTD6 tool results in ``ledger``).
        # Reject + regenerate once with an explicit do-not-state constraint,
        # then fall to the deterministic, version-stamped refusal. Numbers are
        # only grounded on the BTD6 path; the general path runs the name guard
        # only when the turn is BTD6-themed or names a distinctive multi-word
        # entity (so "Benjamin Franklin" in ordinary chat is never refused).
        from services import btd6_grounding_service

        if routed.task is AITask.BTD6_ANSWER or (
            routed.task is AITask.GENERAL_NL_ANSWER
            and btd6_grounding_service.general_path_should_verify(raw_text, reply_text)
        ):
            # General path only: the channel's recent conversation turns are
            # legitimate quotable context — "what was the last message about?"
            # must be answerable by naming entities the conversation already
            # contains (live miss 2026-06-11: a conversation-meta question
            # floored to the BTD6 refusal because the reply quoted the prior
            # Desperado turns). Fresh entities the conversation never named
            # still floor. The BTD6 path keeps its strict facts∪tools haystack
            # — numbers there must come from grounding, never from chat.
            conversation_haystack: tuple[str, ...] = ()
            if routed.task is AITask.GENERAL_NL_ANSWER:
                conversation_haystack = tuple(
                    turn.text for turn in recent_turns if turn.text
                )
            verdict = btd6_grounding_service.validate_btd6_reply(
                reply_text,
                facts=tuple(feature.facts),
                tool_results=(*ledger, *conversation_haystack),
                task=routed.task,
            )
            if not verdict.grounded:
                async with _maybe_typing(message.channel):
                    response = await _invoke_gateway(
                        stack,
                        built,
                        ctx,
                        ledger=ledger,
                        grounding_constraint=_build_grounding_constraint(verdict),
                    )
                retry_text = redact_text((response.text or "").strip()).value
                retry_verdict = (
                    btd6_grounding_service.validate_btd6_reply(
                        retry_text,
                        facts=tuple(feature.facts),
                        tool_results=(*ledger, *conversation_haystack),
                        task=routed.task,
                    )
                    if retry_text
                    else None
                )
                if retry_text and retry_verdict is not None and retry_verdict.grounded:
                    logger.info(
                        "btd6_faithfulness: retry_rescued task=%s route=%s",
                        routed.task.value,
                        routed.route,
                    )
                    reply_text = retry_text
                else:
                    # Floor. A degraded retry is a provider outage, NOT a
                    # grounding failure — keep that audit honest. A healthy
                    # grounding failure serves the deterministic roster for a
                    # list request ("list all heroes"), else the no-data refusal.
                    logger.warning(
                        "btd6_faithfulness: blocked task=%s route=%s guard=%s "
                        "names=%s numbers=%s retry_attempted=True "
                        "retry_rescued=False degraded=%s",
                        routed.task.value,
                        routed.route,
                        ",".join(verdict.notes),
                        list(verdict.offending_names),
                        list(verdict.offending_numbers),
                        response.degraded,
                    )
                    if response.degraded:
                        await _send_btd6_refusal(message)
                        floor_decision = "degraded"
                        floor_reason = PolicyDenialReason.PROVIDER_UNAVAILABLE
                    else:
                        floor_decision, floor_reason = await _serve_btd6_floor(
                            message,
                            raw_text,
                        )
                    await ai_decision_audit_service.record(
                        guild_id=guild_id,
                        channel_id=channel_id,
                        category_id=category_id,
                        user_id=user_id,
                        message_id=message.id,
                        task=routed.task.value,
                        route=routed.route,
                        decision=floor_decision,
                        reason_code=floor_reason,
                        policy_snapshot_hash=decision.policy_snapshot_hash,
                        instruction_profile_ids=list(stack.instruction_profile_ids)
                        or None,
                        provider=response.provider or None,
                        model=response.model or None,
                    )
                    await ai_review_log_service.record_unknown(
                        guild_id=guild_id,
                        channel_id=channel_id,
                        user_id=user_id,
                        message_id=message.id,
                        task=routed.task.value,
                        route=routed.route,
                        reason_code=getattr(floor_reason, "value", str(floor_reason)),
                        question=raw_text,
                        answer=reply_text,
                        provider=response.provider or None,
                        model=response.model or None,
                    )
                    ctx.metadata["handled_by"] = STAGE_NAME
                    return StageResult(short_circuit=True)

        # ---- Project Moon (Limbus) faithfulness guard -----------------------
        # A PROJMOON_ANSWER reply must not state distinctive Limbus proper names
        # (the 12 Sinners, the E.G.O grades) absent from the grounded payload
        # injected by ``projmoon_context_service``. Reject + regenerate once with
        # a do-not-state constraint, then floor to a deterministic refusal.
        # Names-only — Limbus exact numbers aren't ingested yet (Slice A item 1).
        # Default-preserving: only PROJMOON_ANSWER replies (already Limbus-routed)
        # enter here; the BTD6 / general paths above are untouched.
        if routed.task is AITask.PROJMOON_ANSWER:
            from services import projmoon_grounding_service

            pm_verdict = projmoon_grounding_service.validate_projmoon_reply(
                reply_text,
                facts=tuple(feature.facts),
            )
            if not pm_verdict.grounded:
                async with _maybe_typing(message.channel):
                    response = await _invoke_gateway(
                        stack,
                        built,
                        ctx,
                        ledger=ledger,
                        grounding_constraint=(
                            projmoon_grounding_service.build_grounding_constraint(
                                pm_verdict,
                            )
                        ),
                    )
                pm_retry_text = redact_text((response.text or "").strip()).value
                pm_retry_verdict = (
                    projmoon_grounding_service.validate_projmoon_reply(
                        pm_retry_text,
                        facts=tuple(feature.facts),
                    )
                    if pm_retry_text
                    else None
                )
                if (
                    pm_retry_text
                    and pm_retry_verdict is not None
                    and pm_retry_verdict.grounded
                ):
                    logger.info(
                        "projmoon_faithfulness: retry_rescued route=%s",
                        routed.route,
                    )
                    reply_text = pm_retry_text
                else:
                    logger.warning(
                        "projmoon_faithfulness: blocked route=%s names=%s "
                        "retry_attempted=True retry_rescued=False degraded=%s",
                        routed.route,
                        list(pm_verdict.offending_names),
                        response.degraded,
                    )
                    await _send_projmoon_refusal(message)
                    if response.degraded:
                        pm_decision = "degraded"
                        pm_reason = PolicyDenialReason.PROVIDER_UNAVAILABLE
                    else:
                        pm_decision = "denied"
                        pm_reason = PolicyDenialReason.GROUNDING_FAILED
                    await ai_decision_audit_service.record(
                        guild_id=guild_id,
                        channel_id=channel_id,
                        category_id=category_id,
                        user_id=user_id,
                        message_id=message.id,
                        task=routed.task.value,
                        route=routed.route,
                        decision=pm_decision,
                        reason_code=pm_reason,
                        policy_snapshot_hash=decision.policy_snapshot_hash,
                        instruction_profile_ids=list(stack.instruction_profile_ids)
                        or None,
                        provider=response.provider or None,
                        model=response.model or None,
                    )
                    await ai_review_log_service.record_unknown(
                        guild_id=guild_id,
                        channel_id=channel_id,
                        user_id=user_id,
                        message_id=message.id,
                        task=routed.task.value,
                        route=routed.route,
                        reason_code=getattr(pm_reason, "value", str(pm_reason)),
                        question=raw_text,
                        answer=reply_text,
                        provider=response.provider or None,
                        model=response.model or None,
                    )
                    ctx.metadata["handled_by"] = STAGE_NAME
                    return StageResult(short_circuit=True)

        from core.runtime.ai import response_renderer_registry

        # A registered renderer may raise (bad render_context, embed
        # construction error). Fall back to the plain-text path rather
        # than discarding the model's reply: a degraded presentation
        # beats no reply at all.
        try:
            rendered = await response_renderer_registry.render(
                routed.task,
                response,
                _fact_req,
                feature.render_context,
            )
        except Exception:  # noqa: BLE001 — renderer faults degrade to plain text
            logger.warning(
                "ai_natural_language_stage: renderer for task=%s raised; "
                "falling back to plain text (guild=%s channel=%s message=%s)",
                routed.task.value,
                guild_id,
                channel_id,
                message.id,
                exc_info=True,
            )
            rendered = None

        sent_message: discord.Message | None = None
        try:
            if rendered is not None:
                sent_message = await message.channel.send(
                    content=rendered.content,
                    embed=rendered.embed,
                    allowed_mentions=rendered.allowed_mentions
                    or discord.AllowedMentions.none(),
                )
            else:
                # Reply to the triggering message on the first chunk so the
                # answer is visibly threaded to the question in a busy
                # channel. ``fail_if_not_exists=False`` degrades to a plain
                # send if the original was deleted mid-flight.
                reference = message.to_reference(fail_if_not_exists=False)
                for index, chunk in enumerate(_split_for_discord(reply_text)):
                    sent = await message.channel.send(
                        chunk,
                        allowed_mentions=discord.AllowedMentions.none(),
                        reference=reference if index == 0 else None,
                    )
                    # Remember the first chunk — the message users reply to.
                    if index == 0:
                        sent_message = sent
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
                    "video_response_send_failed"
                    if routed.task in _VIDEO_TASKS
                    else "response_send_failed"
                ),
                policy_snapshot_hash=decision.policy_snapshot_hash,
                instruction_profile_ids=list(stack.instruction_profile_ids) or None,
                provider=response.provider or None,
                model=response.model or None,
            )
            return StageResult()

        ai_permission_service.mark_reply_sent(guild_id, user_id)
        # Spend one unit of the fresh-user mention allowance only when a
        # reply was actually delivered (not per attempt), so a brand-new
        # user gets a bounded number of below-level replies before the
        # level floor applies again.
        if decision.used_fresh_allowance:
            ai_permission_service.consume_fresh_allowance(guild_id, user_id)
        # User-message recording happens earlier via
        # ``_record_user_turn_if_visible``. Here the stage records
        # only its own (sanitized) assistant reply. We omit
        # display_name — the assembler always renders bot turns as
        # ``[assistant]`` regardless of any guild nickname the bot
        # might have, so the model has one stable self-label.
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

        # Remember this answer so a later 👎 / correction-reply on it can be
        # recovered with its original question (cogs/ai_review_cog.py). Pure
        # in-memory + fail-safe; never disturbs the reply path.
        if sent_message is not None:
            ai_review_log_service.remember_answer(
                sent_message.id,
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                message_id=message.id,
                question=raw_text,
                answer=reply_text,
                task=routed.task.value,
                route=routed.route,
                provider=response.provider or None,
                model=response.model or None,
            )

        ctx.metadata["handled_by"] = STAGE_NAME
        return StageResult(short_circuit=True)


async def _gather_bot_knowledge_blocks(
    message: discord.Message,
    *,
    user_text: str,
    task: AITask,
    guild_id: int,
    channel_id: int,
    user_id: int,
) -> tuple[ai_instruction_service.BotKnowledgeBlock, ...]:
    """Collect the authoritative bot-knowledge blocks for this turn.

    Two best-effort enrichments, each isolated so a failure in one never
    suppresses the other or the reply itself:

    * Bot self-knowledge — command catalog + the asker's most recent
      non-replied audit row, gated by intent heuristics so the prompt
      only grows when the user actually asks a meta-question. Failure
      logs at warning (it silently weakens "what can you do" answers).
    * BTD6 live-state — only for BTD6-classified messages, and only when
      the message carries a BTD6 anchor term. Absence is routine, so a
      failure here stays at debug.
    """
    try:
        from services import bot_knowledge_service

        if bot_knowledge_service.looks_like_audit_question(user_text):
            accessible = _accessible_channel_ids_for(message.author, message.guild)
        else:
            accessible = frozenset()

        blocks: tuple[ai_instruction_service.BotKnowledgeBlock, ...] = (
            await bot_knowledge_service.gather(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                user_text=user_text,
                user_tier=bot_knowledge_service.resolve_user_tier(message.author),
                accessible_channel_ids=accessible,
            )
        )
    except Exception:  # noqa: BLE001 — defensive
        logger.warning(
            "ai_natural_language_stage: bot knowledge unavailable; replying "
            "without self-knowledge blocks (guild=%s channel=%s)",
            guild_id,
            channel_id,
            exc_info=True,
        )
        blocks = ()

    if task is AITask.BTD6_ANSWER:
        try:
            from services import btd6_ai_knowledge_block_service

            btd6_blocks = (
                await btd6_ai_knowledge_block_service.gather_btd6_bot_knowledge_blocks(
                    user_text=user_text,
                )
            )
            if btd6_blocks:
                blocks = blocks + btd6_blocks
        except Exception as exc:  # noqa: BLE001 — absence is routine here
            logger.debug(
                "ai_natural_language_stage: btd6 knowledge unavailable: %s",
                exc,
            )

    return blocks


async def _gather_feature_facts(req: FeatureFactRequest) -> FeatureFactsResult:
    """Hand off to the feature owner for fact retrieval.

    BTD6 routes through btd6_context_service; Project Moon (Limbus) through
    projmoon_context_service; VIDEO tasks through youtube_context_service
    (feature-flag gated).  Other tasks return empty facts and the gateway
    answers from the instruction stack alone.
    """
    if req.task is AITask.PROJMOON_ANSWER:
        # Limbus grounding is read-only over committed fixtures (sync, no I/O);
        # absence of a named entity is routine, so an empty context just lets the
        # model answer from the instruction stack (same as the GENERAL path).
        from services import projmoon_context_service

        ctx_pm = projmoon_context_service.build(req.text)
        return FeatureFactsResult(facts=tuple(ctx_pm.facts))
    if req.task is AITask.BTD6_ANSWER:
        from services import btd6_context_service

        # Channel identity enables the conversation-carryover fallback for
        # entity-less follow-ups ("does IT make coins…"); the stage grounds
        # BEFORE recording the triggering message, so the buffer holds
        # exactly the prior turns here.
        ctx = await btd6_context_service.build(
            req.text,
            guild_id=req.guild_id,
            channel_id=req.channel_id,
            conversation_followup=req.conversation_followup,
        )
        return FeatureFactsResult(facts=tuple(ctx.facts))
    if req.task in _VIDEO_TASKS:
        from services import youtube_context_service

        ctx = await youtube_context_service.build(req)
        if not ctx.facts:
            return FeatureFactsResult(
                facts=(),
                render_context=None,
                error_reason=ctx.error_reason,
            )
        return FeatureFactsResult(facts=ctx.facts, render_context=ctx)
    return FeatureFactsResult(facts=())


_DISCORD_MESSAGE_LIMIT = 2000


def _split_for_discord(text: str, *, limit: int = _DISCORD_MESSAGE_LIMIT) -> list[str]:
    """Split ``text`` into chunks no longer than ``limit`` characters.

    Discord rejects a message whose ``content`` exceeds 2000 characters, and
    this stage sends in a single call — so a long model reply (the cap is in
    tokens, ~4x characters) would otherwise fail to post entirely. Breaks on
    the last newline (then space) within the limit so words and lines are not
    cut mid-token; falls back to a hard cut for a single oversized run.
    Returns ``[text]`` unchanged when it already fits.
    """
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        window = remaining[:limit]
        cut = window.rfind("\n")
        if cut == -1:
            cut = window.rfind(" ")
        if cut <= 0:
            cut = limit
        chunks.append(remaining[:cut])
        remaining = remaining[cut:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


def _derive_scope(message: discord.Message) -> AIScope:
    """Map the message author's Discord permissions to an :class:`AIScope`.

    Used only to decide which read-only tools the model may be offered
    (see :mod:`services.ai_tools`). It does NOT influence whether the bot
    replies — the policy resolver owns that decision. Anything
    unrecognised (e.g. a missing permissions object) defaults to ``USER``.
    """
    author = getattr(message, "author", None)
    guild = getattr(message, "guild", None)
    # Platform owner — the single configured operator, recognized by verified
    # Discord user id (never message text, so it cannot be spoofed). Checked
    # FIRST so the owner outranks even guild ownership; this is what makes the
    # owner-gated diagnostics_health_snapshot tool reachable (D1). Mirrors the
    # id-gated owner seams in ai_tools.get_user_standing / bot_knowledge_service;
    # the deterministic !platform health surface uses bot.is_owner separately.
    from config import is_platform_owner

    author_id = getattr(author, "id", None)
    if is_platform_owner(author_id):
        return AIScope.PLATFORM_OWNER
    if (
        guild is not None
        and author is not None
        and getattr(guild, "owner_id", None) == getattr(author, "id", None)
    ):
        return AIScope.SERVER_OWNER
    perms = getattr(author, "guild_permissions", None)
    if perms is None:
        return AIScope.USER
    if getattr(perms, "administrator", False) or getattr(perms, "manage_guild", False):
        return AIScope.ADMIN
    if (
        getattr(perms, "manage_messages", False)
        or getattr(perms, "kick_members", False)
        or getattr(perms, "ban_members", False)
        or getattr(perms, "moderate_members", False)
    ):
        return AIScope.MODERATOR
    return AIScope.USER


def _btd6_game_version() -> str:
    """The game version the bot actually serves (e.g. "54.0"), for the stamp."""
    try:
        from services import btd6_data_service

        return btd6_data_service.get_dataset().game_version or "the current"
    except Exception:
        return "the current"


def _btd6_no_data_refusal() -> str:
    """Deterministic, version-stamped BTD6 refusal — never model prose.

    The single source for the floor string so every grounding refusal stamps
    the same version. Never raises.
    """
    return (
        "I don't have verified BTD6 data to answer that for the current game "
        f"version ({_btd6_game_version()}). I won't state names or numbers I "
        "can't ground in my data — try asking about a specific tower, hero, or "
        "paragon."
    )


def _build_grounding_constraint(verdict: btd6_grounding_service.GroundingResult) -> str:
    """A do-not-state constraint appended to the system prompt on the retry."""
    bits: list[str] = []
    if verdict.offending_names:
        bits.append("names not in the data: " + ", ".join(verdict.offending_names))
    if verdict.offending_numbers:
        bits.append("numbers not in the data: " + ", ".join(verdict.offending_numbers))
    if verdict.offending_absence_claims:
        bits.append(
            "false 'does not have' claims the data refutes: "
            + " | ".join(verdict.offending_absence_claims),
        )
    detail = "; ".join(bits) if bits else "unsupported BTD6 claims"
    correction = (
        "GROUNDING CORRECTION: your previous reply contained "
        f"{detail}. Do NOT state these. Use only BTD6 names and numbers present "
        "in the provided data and tool results. If the data does not support an "
        "answer, say you don't have that information."
    )
    if verdict.offending_absence_claims:
        correction += (
            " The provided data DOES list the thing you said is missing — state "
            "what the data shows instead of claiming it does not exist."
        )
    return correction


async def _send_btd6_refusal(message: discord.Message) -> None:
    """Send the deterministic BTD6 refusal as a reply to ``message``."""
    try:
        await message.channel.send(
            _btd6_no_data_refusal(),
            allowed_mentions=discord.AllowedMentions.none(),
            reference=message.to_reference(fail_if_not_exists=False),
        )
    except discord.HTTPException:
        logger.warning(
            "btd6_faithfulness: refusal send failed for message=%s",
            getattr(message, "id", None),
            exc_info=True,
        )


async def _send_projmoon_refusal(message: discord.Message) -> None:
    """Send the deterministic Project Moon (Limbus) refusal as a reply."""
    from services import projmoon_grounding_service

    try:
        await message.channel.send(
            projmoon_grounding_service.no_data_refusal(),
            allowed_mentions=discord.AllowedMentions.none(),
            reference=message.to_reference(fail_if_not_exists=False),
        )
    except discord.HTTPException:
        logger.warning(
            "projmoon_faithfulness: refusal send failed for message=%s",
            getattr(message, "id", None),
            exc_info=True,
        )


async def _serve_btd6_floor(
    message: discord.Message,
    raw_text: str,
) -> tuple[str, PolicyDenialReason]:
    """Floor for a healthy BTD6 answer that produced no groundable reply.

    For a clear roster-LIST request ("list all heroes", "list all towers") send
    the deterministic, code-built roster — the model cannot restate 17+ costs
    verbatim, so a single mismatch refused the whole list; the roster *is* the
    source, so it always answers. A capability/meta ask ("what do you know
    about btd6?") gets the deterministic answerability summary for the same
    reason — the model's own capability description trips the guard, so a
    healthy meta question kept ending in the no-data refusal, which is the
    wrong answer to it (live miss, 2026-06-10). Otherwise send the
    version-stamped no-data refusal. Returns the ``(decision, reason_code)``
    to audit.
    """
    floor_reply: str | None = None
    try:
        from services import btd6_context_service

        floor_reply = btd6_context_service.deterministic_roster_reply(raw_text)
        if not floor_reply:
            floor_reply = btd6_context_service.deterministic_meta_reply(raw_text)
    except Exception:
        logger.warning("btd6 deterministic floor build failed", exc_info=True)

    if floor_reply:
        try:
            reference = message.to_reference(fail_if_not_exists=False)
            for index, chunk in enumerate(_split_for_discord(floor_reply)):
                await message.channel.send(
                    chunk,
                    allowed_mentions=discord.AllowedMentions.none(),
                    reference=reference if index == 0 else None,
                )
        except discord.HTTPException:
            logger.warning(
                "btd6 floor send failed for message=%s",
                getattr(message, "id", None),
                exc_info=True,
            )
        return "replied", PolicyDenialReason.NONE

    # A question that is not itself BTD6-themed (the guard fired off the
    # REPLY's content — e.g. a conversation-meta question whose answer named
    # game entities) must not get the version-stamped BTD6 data refusal: it
    # reads as a non-sequitur (live miss 2026-06-11, "what is the last
    # message you can see"). Send an honest generic floor instead.
    try:
        from utils.btd6.keywords import has_btd6_context

        question_is_btd6 = has_btd6_context(raw_text)
    except Exception:  # noqa: BLE001 — defensive: keep the strict refusal
        question_is_btd6 = True
    if not question_is_btd6:
        try:
            await message.channel.send(
                "I drafted an answer, but it included game details I can't "
                "verify, so I held it back. Try rephrasing — or ask me about "
                "a specific tower, hero, or paragon and I'll use real data.",
                allowed_mentions=discord.AllowedMentions.none(),
                reference=message.to_reference(fail_if_not_exists=False),
            )
        except discord.HTTPException:
            logger.warning(
                "generic guard floor send failed for message=%s",
                getattr(message, "id", None),
                exc_info=True,
            )
        return "denied", PolicyDenialReason.GROUNDING_FAILED

    await _send_btd6_refusal(message)
    return "denied", PolicyDenialReason.GROUNDING_FAILED


def _wrap_handlers_for_ledger(
    handlers: Mapping[str, ToolHandler],
    allowlist: frozenset[str],
    ledger: list[str],
) -> dict[str, ToolHandler]:
    """Wrap approved BTD6 tool handlers so their results feed the ledger.

    Only handlers whose name is in ``allowlist`` are wrapped; every other
    handler is returned untouched. The captured string is the redacted,
    JSON-encoded result — the same shape the gateway feeds back into the model
    context — so the faithfulness verifier's trusted haystack contains exactly
    the deterministic BTD6 facts the model saw, and never a server member count
    or timestamp from an unrelated tool.
    """
    import json

    from core.runtime.ai.redaction import redact_text

    def _capture(handler: ToolHandler) -> ToolHandler:
        async def wrapped(arguments: dict[str, object]) -> object:
            result = await handler(arguments)
            try:
                encoded = json.dumps(result, default=str)
            except (TypeError, ValueError):
                encoded = str(result)
            ledger.append(redact_text(encoded).value)
            return result

        return wrapped

    return {
        name: (_capture(handler) if name in allowlist else handler)
        for name, handler in handlers.items()
    }


async def _invoke_gateway(
    stack: ai_instruction_service.InstructionStack,
    built: ai_context_service.BuiltContext,
    _ctx: MessagePipelineContext,
    *,
    ledger: list[str] | None = None,
    grounding_constraint: str | None = None,
) -> AIResponse:
    """Run the AI gateway and return the full :class:`AIResponse`.

    The gateway never raises (it converts every error into a degraded
    :class:`AIResponse`), so this helper has no local exception
    handling — any exception that escapes is a gateway contract
    violation and propagates to the outer handler in
    :meth:`AINaturalLanguageStage.process` which audits it as
    ``errored / PROVIDER_UNAVAILABLE``.

    When ``AI_TOOLS_ENABLED`` is on we attach the read-only tool set the
    caller's scope permits; the gateway decides whether to actually offer
    them to the model. When off, ``tools`` is empty and ``tool_handlers``
    is ``None`` — byte-for-byte identical to the no-tools path.

    ``ledger`` (BTD6 faithfulness): when supplied, approved BTD6 tool results
    are appended to it (see :func:`_wrap_handlers_for_ledger`) so the caller
    can ground the model's reply against them. ``grounding_constraint`` is
    appended to the system prompt on the regenerate-once retry to tell the
    model which names/numbers it must not restate.

    Orchestration profiles whose ``workflow`` selects it additionally run the
    deterministic round-cash plan→execute→verify workflow
    (:mod:`services.ai_round_cash_workflow`, Phase 4 MVP) before the model
    call; its evidence rides the system prompt + ledger. The default profile's
    ``direct_or_tool`` workflow never engages it.
    """
    from core.runtime.ai.contracts import (
        AIRequest,
        AIResponseMode,
        AIToolBudget,
        AIToolChoice,
        AIToolSpec,
    )
    from core.runtime.ai.feature_flags import ai_tools_enabled
    from services import ai_gateway, ai_tools

    ctx = built.request_context
    specs: tuple[AIToolSpec, ...] = ()
    handlers: Mapping[str, ToolHandler] | None = None
    # Orchestration policy (Phase 3). Defaults reproduce today's behaviour
    # byte-for-byte (AUTO choice + hop-bounded budget, no toolset narrowing);
    # the resolver only tightens them when an operator has set a non-default
    # profile for this guild / category / channel.
    tool_choice = AIToolChoice()
    tool_budget = AIToolBudget()
    workflow_block: str | None = None
    if ai_tools_enabled() and ctx.guild_id is not None and ctx.actor_id is not None:
        from services import ai_orchestration_policy, ai_round_cash_workflow

        # Pass the live guild + asking member so the server-introspection
        # tools can read roles / channels / overview. ``build_registry``
        # omits those tools when ``guild`` is None.
        message = getattr(_ctx, "message", None)
        category_id = getattr(getattr(message, "channel", None), "category_id", None)
        orchestration = await ai_orchestration_policy.resolve(
            ai_orchestration_policy.OrchestrationContext(
                guild_id=int(ctx.guild_id),
                channel_id=int(ctx.channel_id or 0),
                category_id=int(category_id) if category_id is not None else None,
            ),
        )
        registry = ai_tools.build_registry(
            scope=ctx.scope,
            guild_id=ctx.guild_id,
            actor_id=ctx.actor_id,
            guild=getattr(message, "guild", None),
            member=getattr(message, "author", None),
            bot=getattr(_ctx, "bot", None),
            # Binds get_ai_policy_explanation to the asking channel.
            channel=getattr(message, "channel", None),
            # The orchestration profile may NARROW the offered toolset; it can
            # never grant a tool above the caller's scope (select_tools enforces).
            enabled_toolsets=orchestration.enabled_toolsets,
            disabled_tools=orchestration.disabled_tools,
        )
        specs = registry.specs
        handlers = registry.handlers
        tool_choice = orchestration.tool_choice
        tool_budget = orchestration.tool_budget
        if ledger is not None:
            handlers = _wrap_handlers_for_ledger(
                handlers,
                ai_tools.BTD6_GROUNDING_TOOL_NAMES,
                ledger,
            )
        # Phase 4 MVP (Q-0046): the deterministic round-cash plan→execute→
        # verify workflow — gated on the resolved ``workflow`` label. Since
        # the 2026-06-11 BUG-0001 recurrence the compatible default and
        # balanced presets declare it too (an explicit ``direct_or_tool`` /
        # ``direct_answer`` profile still never reaches it). A recognised
        # question's evidence is appended to the system prompt (the model
        # explains the already-computed result) and to the faithfulness
        # ledger (so the restated numbers are grounded). Defensive: a
        # workflow fault must never break the reply path — it degrades to
        # the unchanged request.
        if orchestration.workflow == ai_round_cash_workflow.WORKFLOW_KEY:
            try:
                answer = ai_round_cash_workflow.run(
                    getattr(stack, "user_message", "") or "",
                )
                if answer is not None:
                    workflow_block = ai_round_cash_workflow.render_system_block(
                        answer,
                    )
                    if ledger is not None:
                        from core.runtime.ai.redaction import redact_text

                        entry = redact_text(
                            ai_round_cash_workflow.render_ledger_entry(answer),
                        ).value
                        # The regenerate-once retry reuses the same ledger;
                        # the deterministic entry must not duplicate.
                        if entry not in ledger:
                            ledger.append(entry)
            except Exception:  # noqa: BLE001 — degrade to the normal path
                logger.warning(
                    "ai_round_cash_workflow: failed; continuing without "
                    "deterministic evidence (guild=%s channel=%s)",
                    ctx.guild_id,
                    ctx.channel_id,
                    exc_info=True,
                )
                workflow_block = None

    # When no tools are offered (tools disabled, or a "no tools" orchestration
    # profile narrowed them all away) take the identical legacy single-shot
    # path: no tool_handlers, byte-for-byte the no-tools request.
    if not specs:
        handlers = None

    system_prompt = stack.render_system_prompt()
    if workflow_block:
        system_prompt = f"{system_prompt}\n\n{workflow_block}"
    if grounding_constraint:
        system_prompt = f"{system_prompt}\n\n{grounding_constraint}"

    request = AIRequest(
        context=ctx,
        system_prompt=system_prompt,
        payload={"text": stack.render_payload_text()},
        mode=AIResponseMode.TEXT,
        tools=specs,
        tool_choice=tool_choice,
        tool_budget=tool_budget,
    )
    # Pass tool_handlers only when tools are active so the no-tools path
    # matches the legacy single-argument ``execute(request)`` call.
    if handlers is None:
        return await ai_gateway.execute(request)
    return await ai_gateway.execute(request, tool_handlers=handlers)


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
