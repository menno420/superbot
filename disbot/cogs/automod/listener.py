"""Automod message-pipeline stage body (delete + warn orchestration).

Kept out of the cog (the F-3 thin-cog convention) so the orchestration is
unit-testable without spinning up the full cog: :func:`process_message` takes a
message + the bot and returns a :class:`StageResult`, calling
:mod:`services.moderation_service` for the actual action so escalation and audit
stay one authority.

Fail-open discipline (family-plan §3 rule 4): any fault in the config read or
the detector lets the message through — automod never blocks legitimate
activity because of a transient error.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.message_pipeline import StageResult
from services import automod_config, automod_service, moderation_service

logger = logging.getLogger("bot.cogs.automod.listener")

EVT_AUTOMOD_RULE_TRIGGERED = "automod.rule_triggered"


async def process_message(
    bot: object,
    message: discord.Message,
) -> StageResult:
    """Evaluate one message against the guild's automod policy and act.

    Returns ``StageResult(deleted=True, short_circuit=True)`` when a rule
    tripped (so downstream reward/conversational stages skip a removed
    message), or an empty ``StageResult()`` otherwise.
    """
    guild = getattr(message, "guild", None)
    if guild is None:
        # The pipeline pre-filters DMs; defensive for direct test calls.
        return StageResult()

    try:
        policy = await automod_config.load_policy(guild.id)
    except Exception:  # noqa: BLE001 — fail open on any config-read fault
        logger.exception("automod: load_policy failed for guild=%s", guild.id)
        return StageResult()

    if not policy.enabled or not policy.any_rule_enabled:
        return StageResult()

    try:
        verdict = automod_service.evaluate(message, policy)
    except Exception:  # noqa: BLE001 — fail open on a detector fault
        logger.exception("automod: evaluate failed for message=%s", message.id)
        return StageResult()

    if verdict is None:
        return StageResult()

    await _act(message, verdict)
    return StageResult(deleted=True, short_circuit=True)


async def _act(
    message: discord.Message,
    verdict: automod_service.AutomodVerdict,
) -> None:
    """Delete the message + warn the member, then emit the domain event.

    Deletion and discipline both route through ``moderation_service`` (no
    parallel audit path); the warn carries moderation's own warn→timeout
    escalation ladder, so automod adds no second ladder.
    """
    member = getattr(message, "author", None)

    try:
        await moderation_service.auto_delete(
            message,
            reason=verdict.reason,
            rule=verdict.rule,
        )
    except discord.HTTPException as exc:
        logger.warning("automod: auto_delete failed (%s): %s", verdict.rule, exc)

    if isinstance(member, discord.Member):
        try:
            await moderation_service.warn(
                member,
                reason=f"Automod: {verdict.reason}",
                actor_id=None,
            )
        except discord.Forbidden:
            # Missing perms / hierarchy — the deletion already happened; the
            # escalation is reported on the WarnOutcome, never raised.
            pass
        except Exception:  # noqa: BLE001 — a warn fault must not crash the stage
            logger.exception("automod: warn failed for member=%s", member.id)

    await _emit(message, verdict)


async def _emit(
    message: discord.Message,
    verdict: automod_service.AutomodVerdict,
) -> None:
    """Emit the advisory ``automod.rule_triggered`` event (best-effort)."""
    from core.events import bus

    member = getattr(message, "author", None)
    guild = getattr(message, "guild", None)
    channel = getattr(message, "channel", None)
    try:
        await bus.emit(
            EVT_AUTOMOD_RULE_TRIGGERED,
            guild_id=getattr(guild, "id", None),
            user_id=getattr(member, "id", None),
            rule=verdict.rule,
            channel_id=getattr(channel, "id", None),
        )
    except Exception:  # noqa: BLE001 — advisory event; never fail the stage
        logger.exception("automod: rule_triggered emit failed")
