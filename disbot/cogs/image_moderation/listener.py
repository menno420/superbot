"""Image-moderation message-pipeline stage body (scan → delete + warn).

Kept out of the cog (the F-3 thin-cog convention) so the orchestration is
unit-testable without spinning up the full cog or hitting the network:
:func:`process_message` takes a message + the bot and returns a
:class:`StageResult`, classifying each image attachment through the injectable
``classifier`` and routing any action through :mod:`services.moderation_service`
so escalation and audit stay one authority (the same shape as
``cogs.automod.listener``).

Privacy + cost discipline (family-plan §3): only image attachments are scanned,
and only the image **URL** is sent externally — never message text, never the
author.  Exempt channels/members short-circuit *before* any API call, so an
operator can keep an art/NSFW-gated channel out of the external pipeline.

Fail-open discipline (family-plan §3 rule 4): any fault — config read, a missing
OpenAI key/SDK (``ProviderUnavailableError``), a network error, a malformed
response — lets the image through (logged).  Image moderation never blocks a
legitimate upload because of a transient error.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping

import discord

from core.runtime.ai.providers.base import ProviderUnavailableError
from core.runtime.message_pipeline import StageResult
from services import (
    image_moderation_config,
    image_moderation_service,
    moderation_service,
)

logger = logging.getLogger("bot.cogs.image_moderation.listener")

EVT_IMAGE_MODERATION_FLAGGED = "image_moderation.flagged"

#: A classifier returns OpenAI's per-category scores for an image URL.
Classifier = Callable[[str], Awaitable[Mapping[str, float]]]


def _default_classifier() -> Classifier:
    """The process-wide OpenAI moderation classifier (lazy, SDK-gated)."""
    from core.runtime.ai.providers.openai_moderation import default_provider

    return default_provider().classify_image


async def process_message(
    bot: object,
    message: discord.Message,
    *,
    classifier: Classifier | None = None,
) -> StageResult:
    """Scan a message's image attachments and act on the first flagged one.

    Returns ``StageResult(deleted=True, short_circuit=True)`` when an image
    tripped a category (so downstream reward/conversational stages skip the
    removed message), or an empty ``StageResult()`` otherwise.
    """
    guild = getattr(message, "guild", None)
    if guild is None:
        # The pipeline pre-filters DMs; defensive for direct test calls.
        return StageResult()

    try:
        policy = await image_moderation_config.load_policy(guild.id)
    except Exception:  # noqa: BLE001 — fail open on any config-read fault
        logger.exception(
            "image_moderation: load_policy failed for guild=%s",
            guild.id,
        )
        return StageResult()

    if not policy.enabled or not policy.any_category_enabled:
        return StageResult()

    if _is_exempt(message, policy):
        return StageResult()

    urls = image_moderation_service.image_attachment_urls(message)
    if not urls:
        return StageResult()

    classify = classifier if classifier is not None else _default_classifier()

    for url in urls:
        try:
            scores = await classify(url)
        except ProviderUnavailableError as exc:
            # No key / SDK — image moderation is simply unavailable; fail open.
            logger.warning("image_moderation: provider unavailable: %s", exc)
            return StageResult()
        except Exception:  # noqa: BLE001 — fail open on any classify fault
            logger.exception(
                "image_moderation: classify failed for message=%s",
                getattr(message, "id", "?"),
            )
            continue

        verdict = image_moderation_service.evaluate_scores(scores, policy)
        if verdict is not None:
            await _act(message, verdict)
            return StageResult(deleted=True, short_circuit=True)

    return StageResult()


def _is_exempt(
    message: discord.Message,
    policy: image_moderation_config.ImageModerationPolicy,
) -> bool:
    """True when the message's channel or author role is on the exempt list."""
    channel_id = getattr(getattr(message, "channel", None), "id", None)
    if policy.is_exempt_channel(channel_id):
        return True
    author = getattr(message, "author", None)
    role_ids = {
        rid
        for role in (getattr(author, "roles", None) or [])
        if (rid := getattr(role, "id", None)) is not None
    }
    return policy.is_exempt_member(role_ids)


async def _act(
    message: discord.Message,
    verdict: image_moderation_service.ImageModerationVerdict,
) -> None:
    """Delete the message + warn the member, then emit the domain event.

    Deletion and discipline both route through ``moderation_service`` (no
    parallel audit path); the warn carries moderation's own warn→timeout
    escalation ladder, so image moderation adds no second ladder.
    """
    member = getattr(message, "author", None)

    try:
        await moderation_service.auto_delete(
            message,
            reason=verdict.reason,
            rule=verdict.rule,
        )
    except discord.HTTPException as exc:
        logger.warning(
            "image_moderation: auto_delete failed (%s): %s",
            verdict.rule,
            exc,
        )

    if isinstance(member, discord.Member):
        try:
            await moderation_service.warn(
                member,
                reason=f"Image moderation: {verdict.reason}",
                actor_id=None,
            )
        except discord.Forbidden:
            # Missing perms / hierarchy — the deletion already happened; the
            # escalation is reported on the WarnOutcome, never raised.
            pass
        except Exception:  # noqa: BLE001 — a warn fault must not crash the stage
            logger.exception(
                "image_moderation: warn failed for member=%s",
                member.id,
            )

    await _emit(message, verdict)


async def _emit(
    message: discord.Message,
    verdict: image_moderation_service.ImageModerationVerdict,
) -> None:
    """Emit the advisory ``image_moderation.flagged`` event (best-effort)."""
    from core.events import bus

    member = getattr(message, "author", None)
    guild = getattr(message, "guild", None)
    channel = getattr(message, "channel", None)
    try:
        await bus.emit(
            EVT_IMAGE_MODERATION_FLAGGED,
            guild_id=getattr(guild, "id", None),
            user_id=getattr(member, "id", None),
            category=verdict.category,
            channel_id=getattr(channel, "id", None),
        )
    except Exception:  # noqa: BLE001 — advisory event; never fail the stage
        logger.exception("image_moderation: flagged emit failed")
