"""Passive BTD6 message stage — Module 6 of the AI/BTD6 plan.

The stage runs as part of the platform message pipeline (registered
in ``btd6_cog.cog_load`` via
``core.runtime.message_pipeline.register``). It NEVER installs a
direct ``on_message`` listener — the invariant test
``tests/unit/invariants/test_ai_btd6_boundaries.py::test_btd6_does_not_install_on_message_listener``
forbids that.

Behaviour is opt-in. Every skip is recorded with a structured
reason so ``!btd6 why-no-response`` can explain (without leaking
the original message body) why a recent message in the channel
was not handled.

Skip stack (all must pass to reply):

1. author is a bot or webhook
2. message is empty / system message
3. message starts with the bot's command prefix
4. process-level ``BTD6_PASSIVE_ENABLED`` is on
5. channel is in ``BTD6_PASSIVE_CHANNELS`` (id list)
6. earlier pipeline stage marked ``ctx.metadata["handled_by"]``
7. per-user/per-channel cooldown OK
8. resolver confidence >= ``BTD6_CONFIDENCE_THRESHOLD``

All thresholds are env-driven defaults; Module 6 deliberately does
not introduce a new persistence path (per the AI/BTD6 plan's
"existing settings infrastructure only" rule). Per-guild gating is
a follow-up once SuperBot's settings layer exposes a BTD6 schema.
"""

from __future__ import annotations

import logging
import os
import time
from collections import deque
from dataclasses import dataclass

import discord

from core.runtime.message_pipeline import MessagePipelineContext, StageResult
from services import btd6_ai_service
from services.btd6_resolver_service import resolve

logger = logging.getLogger("bot.cogs.btd6.stage")

STAGE_NAME = "btd6_assistant"
STAGE_ORDER = 80  # after cleanup/counting; before observability stages

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_DEFAULT_CONFIDENCE_THRESHOLD = 0.34  # ≥ 1 of 3 entities matched
_DEFAULT_COOLDOWN_SECONDS = 10.0
_SKIP_BUFFER_PER_CHANNEL = 8


@dataclass(frozen=True)
class SkipRecord:
    """One per-channel skip explanation, surfaced by ``!btd6 why-no-response``."""

    channel_id: int
    timestamp: float
    reason: str  # short reason code, no user content
    confidence: float  # resolver confidence (0..1) at decision time


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUTHY


def passive_enabled() -> bool:
    """Process-level flag. Default off."""
    return _env_truthy("BTD6_PASSIVE_ENABLED")


def passive_channel_ids() -> set[int]:
    """Comma-separated channel id list from ``BTD6_PASSIVE_CHANNELS``."""
    raw = os.getenv("BTD6_PASSIVE_CHANNELS", "")
    out: set[int] = set()
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        try:
            out.add(int(entry))
        except ValueError:
            continue
    return out


def confidence_threshold() -> float:
    raw = os.getenv("BTD6_CONFIDENCE_THRESHOLD", "").strip()
    try:
        return max(0.0, min(1.0, float(raw))) if raw else _DEFAULT_CONFIDENCE_THRESHOLD
    except ValueError:
        return _DEFAULT_CONFIDENCE_THRESHOLD


def cooldown_seconds() -> float:
    raw = os.getenv("BTD6_COOLDOWN_SECONDS", "").strip()
    try:
        return max(0.0, float(raw)) if raw else _DEFAULT_COOLDOWN_SECONDS
    except ValueError:
        return _DEFAULT_COOLDOWN_SECONDS


# ---------------------------------------------------------------------------
# Skip reasons — surfaced by !btd6 why-no-response. Never include message
# body or user content; reasons are short stable identifiers.
# ---------------------------------------------------------------------------

REASON_BOT_AUTHOR = "skip:bot_author"
REASON_WEBHOOK = "skip:webhook"
REASON_SYSTEM_MESSAGE = "skip:system_message"
REASON_EMPTY = "skip:empty_message"
REASON_COMMAND_PREFIX = "skip:command_prefix"
REASON_DISABLED = "skip:passive_disabled"
REASON_CHANNEL_NOT_CONFIGURED = "skip:channel_not_configured"
REASON_ALREADY_HANDLED = "skip:already_handled"
REASON_COOLDOWN = "skip:cooldown"
REASON_LOW_CONFIDENCE = "skip:low_confidence"


class BTD6AssistantMessageStage:
    """Default-off passive BTD6 assistant.

    Cooldown state and the skip-reason ring buffer live as instance
    attributes; the stage is created once when the cog loads and
    persists for the lifetime of the bot process. Tests can build a
    fresh instance to start from clean state.
    """

    name = STAGE_NAME
    order = STAGE_ORDER

    def __init__(self) -> None:
        self._cooldowns: dict[tuple[int, int], float] = {}
        self._recent_skips: dict[int, deque[SkipRecord]] = {}

    # ------------------------------------------------------------------
    # Public introspection — used by /btd6 why-no-response
    # ------------------------------------------------------------------

    def latest_skips(self, channel_id: int) -> tuple[SkipRecord, ...]:
        """Return the channel's recorded skip ring buffer (oldest → newest)."""
        return tuple(self._recent_skips.get(channel_id, ()))

    # ------------------------------------------------------------------
    # Pipeline entry
    # ------------------------------------------------------------------

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        message = ctx.message
        channel_id = message.channel.id if message.channel else 0

        # Pipeline already strips bot authors and DMs, but re-assert
        # so unit tests that bypass the pipeline still see safe behaviour.
        if message.author.bot:
            self._record_skip(channel_id, REASON_BOT_AUTHOR, confidence=0.0)
            return StageResult()
        if getattr(message, "webhook_id", None):
            self._record_skip(channel_id, REASON_WEBHOOK, confidence=0.0)
            return StageResult()
        if _is_system_message(message):
            self._record_skip(channel_id, REASON_SYSTEM_MESSAGE, confidence=0.0)
            return StageResult()
        if not message.content or not message.content.strip():
            self._record_skip(channel_id, REASON_EMPTY, confidence=0.0)
            return StageResult()

        bot = ctx.bot
        if _looks_like_command(message.content, bot):
            self._record_skip(channel_id, REASON_COMMAND_PREFIX, confidence=0.0)
            return StageResult()

        if not passive_enabled():
            self._record_skip(channel_id, REASON_DISABLED, confidence=0.0)
            return StageResult()

        configured = passive_channel_ids()
        if configured and channel_id not in configured:
            self._record_skip(
                channel_id,
                REASON_CHANNEL_NOT_CONFIGURED,
                confidence=0.0,
            )
            return StageResult()

        if ctx.metadata.get("handled_by"):
            self._record_skip(channel_id, REASON_ALREADY_HANDLED, confidence=0.0)
            return StageResult()

        if self._cooldown_active(message.author.id, channel_id):
            self._record_skip(channel_id, REASON_COOLDOWN, confidence=0.0)
            return StageResult()

        intent = resolve(message.content)
        if intent.confidence < confidence_threshold():
            self._record_skip(
                channel_id,
                REASON_LOW_CONFIDENCE,
                confidence=intent.confidence,
            )
            return StageResult()

        # Made it through every gate — deliver a deterministic answer.
        try:
            response = await btd6_ai_service.answer_question(
                message.content,
                augment_with_ai=True,
                guild_id=message.guild.id if message.guild else None,
            )
            await message.reply(
                embed=_response_to_embed(response),
                mention_author=False,
            )
            self._record_cooldown(message.author.id, channel_id)
            ctx.metadata["handled_by"] = STAGE_NAME
        except Exception:  # noqa: BLE001 — never crash the pipeline
            logger.exception(
                "btd6_stage: handling message %s raised",
                message.id,
            )

        return StageResult()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_skip(
        self,
        channel_id: int,
        reason: str,
        *,
        confidence: float,
    ) -> None:
        if channel_id <= 0:
            return
        buffer = self._recent_skips.setdefault(
            channel_id,
            deque(maxlen=_SKIP_BUFFER_PER_CHANNEL),
        )
        buffer.append(
            SkipRecord(
                channel_id=channel_id,
                timestamp=time.time(),
                reason=reason,
                confidence=confidence,
            ),
        )

    def _cooldown_active(self, user_id: int, channel_id: int) -> bool:
        cooldown = cooldown_seconds()
        if cooldown <= 0:
            return False
        last = self._cooldowns.get((user_id, channel_id))
        if last is None:
            return False
        return (time.time() - last) < cooldown

    def _record_cooldown(self, user_id: int, channel_id: int) -> None:
        self._cooldowns[(user_id, channel_id)] = time.time()


def _looks_like_command(content: str, bot: object) -> bool:
    """True if ``content`` starts with the bot's command prefix.

    Discord.py's command_prefix may be a string, a list of strings,
    or a callable. The callable form needs (bot, message), so we
    fall back to ``"!"`` (SuperBot's default) if extraction fails.
    """
    prefix_attr = getattr(bot, "command_prefix", "!")
    candidates: list[str] = []
    if isinstance(prefix_attr, str):
        candidates.append(prefix_attr)
    elif isinstance(prefix_attr, (list, tuple)):
        candidates.extend(str(p) for p in prefix_attr if isinstance(p, str))
    else:
        candidates.append("!")
    if not candidates:
        candidates.append("!")
    stripped = content.lstrip()
    return any(stripped.startswith(p) for p in candidates)


def _is_system_message(message: discord.Message) -> bool:
    """True if ``message.type`` indicates a system event (pin/join/boost/...)."""
    msg_type = getattr(message, "type", None)
    if msg_type is None:
        return False
    default_type = getattr(discord.MessageType, "default", None)
    if default_type is not None and msg_type == default_type:
        return False
    reply_type = getattr(discord.MessageType, "reply", None)
    # Anything else (pins_add, new_member, premium_guild_subscription, ...) is system.
    return not (reply_type is not None and msg_type == reply_type)


def _response_to_embed(response) -> discord.Embed:
    """Lightweight embed renderer for the passive stage.

    We deliberately do not import from ``cogs.btd6_cog`` at module
    load so this stage stays importable without touching the cog
    module. The conversion is the same shape used by the cog.
    """
    color = {
        "high": discord.Color.green(),
        "medium": discord.Color.gold(),
        "low": discord.Color.light_grey(),
    }.get(response.confidence, discord.Color.light_grey())
    embed = discord.Embed(
        title=response.title,
        description=response.short_answer,
        color=color,
    )
    if response.why_it_matters:
        embed.add_field(
            name="Why it matters",
            value=response.why_it_matters,
            inline=False,
        )
    if response.recommended_options:
        embed.add_field(
            name="Recommended options",
            value="\n".join(f"• {opt}" for opt in response.recommended_options),
            inline=False,
        )
    if response.follow_up:
        embed.add_field(name="Follow-up", value=response.follow_up, inline=False)
    if response.sources:
        embed.set_footer(text="Sources: " + " · ".join(response.sources))
    return embed
