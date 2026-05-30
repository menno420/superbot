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
    ai_task_router,
)
from services.ai_natural_language_policy import MessageContext

if TYPE_CHECKING:
    from core.runtime.ai.contracts import AIResponse

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


def _strip_bot_mention(text: str, *, bot_user_id: int | None) -> str:
    """Remove all mentions of the bot from ``text``.

    Discord mentions are ``<@id>`` or ``<@!id>``. ``re.sub`` replaces
    every match. The returned string is stripped of surrounding
    whitespace so a bare-mention message collapses to ``""``.
    """
    if bot_user_id is None:
        return text
    return re.sub(rf"<@!?{bot_user_id}>", "", text).strip()


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
        is_mention = ctx.bot.user is not None and ctx.bot.user.mentioned_in(message)
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
        routed = ai_task_router.classify(raw_text)

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

        try:
            _fact_req = FeatureFactRequest(
                task=routed.task,
                text=raw_text,
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

            # Bot self-knowledge enrichment: catalog of known commands +
            # the asker's most recent non-replied audit row. Gated by
            # intent heuristics so the prompt only grows when the user
            # actually asks a meta-question. Best-effort — failure
            # collapses to no bot-knowledge blocks.
            try:
                from services import bot_knowledge_service

                if bot_knowledge_service.looks_like_audit_question(user_text):
                    accessible = _accessible_channel_ids_for(
                        message.author,
                        message.guild,
                    )
                else:
                    accessible = frozenset()

                bot_knowledge_blocks = await bot_knowledge_service.gather(
                    guild_id=guild_id,
                    channel_id=channel_id,
                    user_id=user_id,
                    user_text=user_text,
                    user_tier=bot_knowledge_service.resolve_user_tier(
                        message.author,
                    ),
                    accessible_channel_ids=accessible,
                )
            except Exception:  # noqa: BLE001 — defensive
                # Warning, not debug: a failure here means meta-questions
                # ("what can you do", "why didn't you reply") silently lose
                # their grounding blocks and get a vaguer answer.
                logger.warning(
                    "ai_natural_language_stage: bot knowledge unavailable; "
                    "replying without self-knowledge blocks (guild=%s channel=%s)",
                    guild_id,
                    channel_id,
                    exc_info=True,
                )
                bot_knowledge_blocks = ()

            # BTD6 live-state / source-status enrichment: only fires for
            # BTD6-classified messages so general-channel chatter doesn't
            # pay the lookup cost. Heuristics live in
            # services.btd6_ai_knowledge_block_service and require a
            # BTD6 anchor term, so bare "what event is on" cannot route
            # here even when the task router lets the message through.
            if routed.task is AITask.BTD6_ANSWER:
                try:
                    from services import btd6_ai_knowledge_block_service

                    btd6_blocks = await btd6_ai_knowledge_block_service.gather_btd6_bot_knowledge_blocks(
                        user_text=user_text,
                    )
                    if btd6_blocks:
                        bot_knowledge_blocks = bot_knowledge_blocks + btd6_blocks
                except Exception as exc:  # noqa: BLE001 — defensive
                    logger.debug(
                        "ai_natural_language_stage: btd6 knowledge unavailable: %s",
                        exc,
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

            # Show "Bot is typing…" while the provider call runs so a
            # multi-second reply does not look like a dropped message.
            async with _maybe_typing(message.channel):
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

        # Outbound redaction: scrub Discord snowflakes and other
        # sensitive-token patterns from the model's reply before it
        # is sent to Discord OR recorded into conversation memory.
        # Placed after the empty-reply guard so empty responses still
        # take the degraded/skipped path above unchanged.
        from core.runtime.ai.redaction import redact_text

        reply_text = redact_text(reply_text).value

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

        try:
            if rendered is not None:
                await message.channel.send(
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
                    await message.channel.send(
                        chunk,
                        allowed_mentions=discord.AllowedMentions.none(),
                        reference=reference if index == 0 else None,
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

    When ``AI_TOOLS_ENABLED`` is on we attach the read-only tool set the
    caller's scope permits; the gateway decides whether to actually offer
    them to the model. When off, ``tools`` is empty and ``tool_handlers``
    is ``None`` — byte-for-byte identical to the no-tools path.
    """
    from collections.abc import Mapping

    from core.runtime.ai.contracts import AIRequest, AIResponseMode, AIToolSpec
    from core.runtime.ai.feature_flags import ai_tools_enabled
    from core.runtime.ai.providers.base import ToolHandler
    from services import ai_gateway, ai_tools

    ctx = built.request_context
    specs: tuple[AIToolSpec, ...] = ()
    handlers: Mapping[str, ToolHandler] | None = None
    if ai_tools_enabled() and ctx.guild_id is not None and ctx.actor_id is not None:
        # Pass the live guild + asking member so the server-introspection
        # tools can read roles / channels / overview. ``build_registry``
        # omits those tools when ``guild`` is None.
        message = getattr(_ctx, "message", None)
        registry = ai_tools.build_registry(
            scope=ctx.scope,
            guild_id=ctx.guild_id,
            actor_id=ctx.actor_id,
            guild=getattr(message, "guild", None),
            member=getattr(message, "author", None),
        )
        specs = registry.specs
        handlers = registry.handlers

    request = AIRequest(
        context=ctx,
        system_prompt=stack.render_system_prompt(),
        payload={"text": stack.render_payload_text()},
        mode=AIResponseMode.TEXT,
        tools=specs,
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
