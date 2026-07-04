"""AI answer review-log cog — corrections in, review feed + ``!aireview`` out.

The Discord surface for ``services/ai_review_log_service.py`` (the owner's
"react AND reply" detection + "channel AND queryable log" review surface):

* **listeners** — a 👎 reaction on, or a correction-reply to, one of the bot's
  AI answers is recorded as a correction. Both paths recover the original Q&A
  from the service's answer registry, so a correction is only ever logged
  against a message the bot actually answered with AI (no false positives on
  arbitrary bot messages).
* **poster** — subscribes to ``ai.review_logged`` and posts each entry (the
  didn't-know cases come from the natural-language stage) to the guild's
  configured review channel, fully fail-safe.
* **command** — ``!aireview`` (manage-guild) to set the channel, list recent
  entries, and mark one reviewed.

Thin layer: the service owns the DB + redaction + the registry; this cog owns
Discord I/O only (no DB writes of AI-review rows here).
"""

from __future__ import annotations

import logging
from typing import Any

import discord
from discord.ext import commands

from core.events import bus
from core.runtime import message_pipeline
from core.runtime.guild_resources import resolve_settings_channel
from core.runtime.message_pipeline import MessagePipelineContext, StageResult
from core.runtime.permission_checks import perms_or_owner
from services import ai_preset_service as presets
from services import ai_review_log_service as review
from utils.settings_keys import ai as ai_keys

logger = logging.getLogger("bot.cogs.ai_review")

_THUMBS_DOWN = "👎"
_REVIEW_COLOR = discord.Color.dark_red()
_CORRECTION_COLOR = discord.Color.orange()

AI_CORRECTION_STAGE_NAME = "ai_correction"
# Passive tier (50–69): observe-only, runs before the conversational AI stage
# (order 70) and never short-circuits. See core/runtime/message_pipeline.py.
AI_CORRECTION_STAGE_ORDER = 55


class AICorrectionStage:
    """Observe-only pipeline stage: a correction-reply to a bot AI answer.

    A reply to one of the bot's *remembered* AI answers whose text reads as a
    correction is logged as a ``correction`` review entry. The original Q&A is
    recovered from the service's answer registry, so only genuine AI answers are
    ever flagged. Never deletes, never short-circuits — the pipeline always
    continues. (The 👎-reaction half lives in ``AIReviewCog.on_raw_reaction_add``;
    a cog may not install its own ``on_message`` listener, hence this stage.)
    """

    name = AI_CORRECTION_STAGE_NAME
    order = AI_CORRECTION_STAGE_ORDER

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        # The pipeline already drops bot-authored messages + DMs, so the author
        # is a guild member and the message is not the bot's own reply.
        message = ctx.message
        ref = message.reference
        if ref is None or ref.message_id is None:
            return StageResult()
        answer = review.lookup_answer(ref.message_id)
        if answer is None:
            return StageResult()
        from utils.ai_correction_cues import looks_like_correction

        if not looks_like_correction(message.content):
            return StageResult()
        if review.already_flagged(ref.message_id, message.author.id):
            return StageResult()
        await review.record_correction(
            guild_id=answer.guild_id,
            channel_id=answer.channel_id,
            user_id=answer.user_id,
            message_id=answer.message_id,
            reply_message_id=ref.message_id,
            corrected_by=message.author.id,
            signal=review.SIGNAL_REPLY,
            question=answer.question,
            answer=answer.answer,
            correction=message.content,
            task=answer.task,
            route=answer.route,
            provider=answer.provider,
            model=answer.model,
        )
        return StageResult()


class AIReviewCog(commands.Cog):
    """Capture corrections + surface the AI answer review log."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Stable bound-method reference for bus.on/off — a fresh bound method
        # object on each attribute access would not match in bus.off (identity).
        self._review_sub = self._on_review_logged

    async def cog_load(self) -> None:
        bus.on(review.EVT_AI_REVIEW_LOGGED, self._review_sub)
        message_pipeline.register(AICorrectionStage())

    async def cog_unload(self) -> None:
        bus.off(review.EVT_AI_REVIEW_LOGGED, self._review_sub)
        message_pipeline.unregister(AI_CORRECTION_STAGE_NAME)

    # ------------------------------------------------------------- listeners

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        """A 👎 on one of the bot's AI answers → log a correction."""
        if payload.guild_id is None or str(payload.emoji) != _THUMBS_DOWN:
            return
        bot_user = self.bot.user
        if bot_user is not None and payload.user_id == bot_user.id:
            return
        ctx = review.lookup_answer(payload.message_id)
        if ctx is None or review.already_flagged(payload.message_id, payload.user_id):
            return
        await review.record_correction(
            guild_id=ctx.guild_id,
            channel_id=ctx.channel_id,
            user_id=ctx.user_id,
            message_id=ctx.message_id,
            reply_message_id=payload.message_id,
            corrected_by=payload.user_id,
            signal=review.SIGNAL_REACTION,
            question=ctx.question,
            answer=ctx.answer,
            correction=None,
            task=ctx.task,
            route=ctx.route,
            provider=ctx.provider,
            model=ctx.model,
        )

    # --------------------------------------------------------------- poster

    async def _on_review_logged(self, **payload: Any) -> None:
        """Post a review entry to the configured channel (fail-safe)."""
        try:
            guild_id = payload.get("guild_id")
            if not isinstance(guild_id, int):
                return
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                return
            channel = await resolve_settings_channel(guild, ai_keys.AI_REVIEW_CHANNEL)
            if not isinstance(channel, discord.TextChannel):
                return
            await channel.send(
                embed=_build_entry_embed(payload),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except Exception:  # noqa: BLE001 — the bus isolates handlers; stay quiet
            logger.debug("ai_review poster failed", exc_info=True)

    # -------------------------------------------------------------- command

    @commands.group(name="aireview", invoke_without_command=True)
    @perms_or_owner(manage_guild=True)
    async def aireview_group(self, ctx: commands.Context) -> None:
        """Show the AI review-log status (channel + unreviewed backlog)."""
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command needs a server context.")
            return
        chan = await resolve_settings_channel(guild, ai_keys.AI_REVIEW_CHANNEL)
        where = chan.mention if isinstance(chan, discord.TextChannel) else "*(not set)*"
        unknown_n = await review.count_unreviewed(guild.id, kind=review.KIND_UNKNOWN)
        corr_n = await review.count_unreviewed(guild.id, kind=review.KIND_CORRECTION)
        embed = discord.Embed(
            title="🔎 AI answer review log",
            description=(
                f"Review channel: {where}\n"
                f"Unreviewed — **{unknown_n}** didn't-know · **{corr_n}** corrections"
            ),
            color=_REVIEW_COLOR,
        )
        embed.set_footer(
            text=(
                "!aireview channel #chan · !aireview list [unknown|correction] · "
                "!aireview export · !aireview resolve <id> · !aireview off"
            ),
        )
        await ctx.send(embed=embed)

    @aireview_group.command(name="channel")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def aireview_channel(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Set the review channel: ``!aireview channel #chan``."""
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command needs a server context.")
            return
        if channel is None:
            await ctx.send(
                "Usage: `!aireview channel #channel` (or `!aireview off` to clear).",
            )
            return
        await review.set_review_channel(guild.id, channel.id)
        await ctx.send(
            f"✅ AI didn't-know answers + user corrections will post to "
            f"{channel.mention}. Clear with `!aireview off`.",
        )

    @aireview_group.command(name="off")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def aireview_off(self, ctx: commands.Context) -> None:
        """Clear the review channel (entries are still recorded + queryable)."""
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command needs a server context.")
            return
        await review.set_review_channel(guild.id, None)
        await ctx.send(
            "✅ Review channel cleared — entries are still recorded; query them "
            "with `!aireview list`.",
        )

    @aireview_group.command(name="list")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def aireview_list(
        self,
        ctx: commands.Context,
        kind: str | None = None,
        limit: int = 10,
    ) -> None:
        """List recent entries: ``!aireview list [unknown|correction] [n]``."""
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command needs a server context.")
            return
        filter_kind: str | None = None
        if kind:
            lowered = kind.lower()
            if lowered in ("unknown", "u", "didnt-know", "didntknow"):
                filter_kind = review.KIND_UNKNOWN
            elif lowered in ("correction", "corrections", "c"):
                filter_kind = review.KIND_CORRECTION
        rows = await review.query(
            guild.id,
            kind=filter_kind,
            limit=max(1, min(25, limit)),
        )
        if not rows:
            await ctx.send("No AI review entries recorded yet.")
            return
        embed = discord.Embed(title="🔎 AI review log — recent", color=_REVIEW_COLOR)
        for row in rows[:10]:
            embed.add_field(
                name=_entry_heading(row),
                value=_entry_summary(row),
                inline=False,
            )
        embed.set_footer(text="Mark one done with !aireview resolve <id>")
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @aireview_group.command(name="export")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def aireview_export(
        self,
        ctx: commands.Context,
        *flags: str,
    ) -> None:
        """Dump the backlog as a JSON file for triage.

        ``!aireview export`` — all unreviewed entries (both kinds).
        ``!aireview export unknown`` / ``correction`` — filter by kind.
        ``!aireview export all`` — include already-resolved entries too.

        The text is already redacted at write time, so the dump carries no
        un-scrubbed content. Feed it to ``scripts/ai_review_triage.py``.
        """
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command needs a server context.")
            return
        filter_kind, include_reviewed = _parse_export_flags(flags)
        entries = await review.export(
            guild.id,
            kind=filter_kind,
            include_reviewed=include_reviewed,
        )
        if not entries:
            scope = "any" if include_reviewed else "unreviewed"
            await ctx.send(f"No {scope} AI review entries to export.")
            return
        import io
        import json

        payload = {
            "schema": "ai_review_export",
            "version": 1,
            "guild_id": guild.id,
            "kind": filter_kind or "all",
            "include_reviewed": include_reviewed,
            "count": len(entries),
            "entries": entries,
        }
        blob = json.dumps(payload, indent=2, ensure_ascii=False)
        data = io.BytesIO(blob.encode("utf-8"))
        await ctx.send(
            content=(
                f"📤 Exported **{len(entries)}** AI review "
                f"{'entry' if len(entries) == 1 else 'entries'} "
                f"({'all' if include_reviewed else 'unreviewed'}"
                f"{', ' + filter_kind if filter_kind else ''}). "
                "Paste this file's contents back to work the backlog, or run "
                "`scripts/ai_review_triage.py` on it."
            ),
            file=discord.File(data, filename=f"ai_review_export_{guild.id}.json"),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @aireview_group.command(name="resolve")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def aireview_resolve(self, ctx: commands.Context, entry_id: int) -> None:
        """Mark one review entry reviewed: ``!aireview resolve <id>``."""
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command needs a server context.")
            return
        ok = await review.mark_reviewed(guild.id, entry_id)
        await ctx.send(
            (
                f"✅ Entry #{entry_id} marked reviewed."
                if ok
                else f"⚠️ No entry `#{entry_id}` in this server."
            ),
        )

    # ------------------------------------------------------- preset subgroup

    @aireview_group.group(  # type: ignore[arg-type]
        name="preset",
        invoke_without_command=True,
    )
    @perms_or_owner(manage_guild=True)
    async def aireview_preset(self, ctx: commands.Context) -> None:
        """Manage vetted answer presets (served with zero model call)."""
        await ctx.send(
            "Vetted answer presets — the bot serves these verbatim, no AI call:\n"
            '`!aireview preset add "<question>" <answer>` · '
            "`!aireview preset from <entry_id> <answer>` · "
            "`!aireview preset list` · `!aireview preset remove <id>`",
        )

    @aireview_preset.command(name="add")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def aireview_preset_add(
        self,
        ctx: commands.Context,
        question: str,
        *,
        answer: str,
    ) -> None:
        """Author a preset: ``!aireview preset add "<question>" <answer>``."""
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command needs a server context.")
            return
        await self._store_preset(ctx, guild.id, question, answer, source="operator")

    @aireview_preset.command(name="from")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def aireview_preset_from(
        self,
        ctx: commands.Context,
        entry_id: int,
        *,
        answer: str,
    ) -> None:
        """Author a preset from a logged question: ``!aireview preset from <id> <answer>``."""
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command needs a server context.")
            return
        entry = await review.get_entry(guild.id, entry_id)
        if entry is None:
            await ctx.send(f"⚠️ No review entry `#{entry_id}` in this server.")
            return
        question = (entry.get("question") or "").strip()
        if not question:
            await ctx.send(
                f"⚠️ Entry `#{entry_id}` has no captured question text to key a preset on.",
            )
            return
        await self._store_preset(
            ctx,
            guild.id,
            question,
            answer,
            task=entry.get("task"),
            source=f"review:{entry_id}",
        )

    async def _store_preset(
        self,
        ctx: commands.Context,
        guild_id: int,
        question: str,
        answer: str,
        *,
        task: str | None = None,
        source: str | None = None,
    ) -> None:
        """Shared add/from path — validate, store, confirm."""
        try:
            preset_id = await presets.set_preset(
                guild_id,
                question,
                answer,
                task=task,
                source=source,
                actor_id=ctx.author.id,
            )
        except ValueError as exc:
            await ctx.send(f"⚠️ Couldn't store that preset: {exc}.")
            return
        await ctx.send(
            f"✅ Preset `#{preset_id}` stored — the bot will answer "
            f"“{_clip(question, 120)}” with your vetted text (no AI call). "
            f"Remove it with `!aireview preset remove {preset_id}`.",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @aireview_preset.command(name="list")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def aireview_preset_list(
        self,
        ctx: commands.Context,
        limit: int = 10,
    ) -> None:
        """List stored presets: ``!aireview preset list [n]``."""
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command needs a server context.")
            return
        rows = await presets.list_presets(guild.id, limit=max(1, min(25, limit)))
        if not rows:
            await ctx.send(
                "No vetted presets yet. Add one with "
                '`!aireview preset add "<question>" <answer>`.',
            )
            return
        embed = discord.Embed(
            title="🧠 Vetted answer presets",
            color=discord.Color.green(),
        )
        for row in rows[:10]:
            mark = "" if row.get("enabled", True) else " *(disabled)*"
            embed.add_field(
                name=f"#{row.get('id')}{mark}",
                value=(
                    f"**Q:** {_clip(row.get('question'), 200)}\n"
                    f"**A:** {_clip(row.get('answer'), 300)}"
                ),
                inline=False,
            )
        embed.set_footer(text="Remove one with !aireview preset remove <id>")
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @aireview_preset.command(name="remove")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def aireview_preset_remove(
        self,
        ctx: commands.Context,
        preset_id: int,
    ) -> None:
        """Delete a preset: ``!aireview preset remove <id>``."""
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command needs a server context.")
            return
        ok = await presets.remove_preset(guild.id, preset_id, actor_id=ctx.author.id)
        await ctx.send(
            (
                f"✅ Preset `#{preset_id}` removed."
                if ok
                else f"⚠️ No preset `#{preset_id}` in this server."
            ),
        )


# ---------------------------------------------------------------------------
# Embed / text helpers
# ---------------------------------------------------------------------------


def _parse_export_flags(flags: tuple[str, ...]) -> tuple[str | None, bool]:
    """Parse ``!aireview export`` flags → ``(kind_filter, include_reviewed)``.

    ``all`` → include resolved entries; ``unknown``/``correction`` (or ``u``/``c``)
    → filter by kind. Pure + order-independent so it is unit-testable.
    """
    lowered = {f.lower() for f in flags}
    include_reviewed = "all" in lowered
    filter_kind: str | None = None
    if {"unknown", "u", "unknowns"} & lowered:
        filter_kind = review.KIND_UNKNOWN
    elif {"correction", "corrections", "c"} & lowered:
        filter_kind = review.KIND_CORRECTION
    return filter_kind, include_reviewed


def _clip(text: object, cap: int = 1000) -> str:
    """Stringify + trim *text* to *cap* chars; '' if empty."""
    value = ("" if text is None else str(text)).strip()
    if not value:
        return ""
    return value if len(value) <= cap else value[: cap - 1] + "…"


def _build_entry_embed(payload: dict[str, Any]) -> discord.Embed:
    """Render an ``ai.review_logged`` payload as the review-channel embed."""
    is_correction = payload.get("kind") == review.KIND_CORRECTION
    embed = discord.Embed(
        title="✏️ AI answer corrected" if is_correction else "❓ AI couldn't answer",
        color=_CORRECTION_COLOR if is_correction else _REVIEW_COLOR,
    )
    embed.add_field(
        name="Reason",
        value=f"`{payload.get('reason_code') or '?'}`",
        inline=True,
    )
    task = payload.get("task")
    if task:
        embed.add_field(name="Task", value=f"`{task}`", inline=True)
    asker = payload.get("user_id")
    if isinstance(asker, int):
        embed.add_field(name="Asked by", value=f"<@{asker}>", inline=True)
    embed.add_field(
        name="Question",
        value=_clip(payload.get("question")) or "*(not captured)*",
        inline=False,
    )
    answer = _clip(payload.get("answer"))
    if answer:
        label = "Answer the AI gave" if is_correction else "What the AI tried to say"
        embed.add_field(name=label, value=answer, inline=False)
    correction = _clip(payload.get("correction"))
    if correction:
        embed.add_field(name="User correction", value=correction, inline=False)
    corrected_by = payload.get("corrected_by")
    if isinstance(corrected_by, int):
        embed.add_field(name="Corrected by", value=f"<@{corrected_by}>", inline=True)
    entry_id = payload.get("entry_id")
    embed.set_footer(
        text=f"Entry #{entry_id} · resolve with !aireview resolve {entry_id}",
    )
    return embed


def _entry_heading(row: dict[str, Any]) -> str:
    mark = "✅" if row.get("reviewed") else "•"
    label = "correction" if row.get("kind") == review.KIND_CORRECTION else "didn't-know"
    return f"{mark} #{row.get('id')} · {label} · {row.get('reason_code') or '?'}"


def _entry_summary(row: dict[str, Any]) -> str:
    parts: list[str] = []
    question = _clip(row.get("question"), 300)
    if question:
        parts.append(f"**Q:** {question}")
    if row.get("kind") == review.KIND_CORRECTION:
        fix = _clip(row.get("correction"), 300)
        if fix:
            parts.append(f"**Fix:** {fix}")
    else:
        answer = _clip(row.get("answer"), 300)
        if answer:
            parts.append(f"**A:** {answer}")
    return "\n".join(parts) or "*(no text captured)*"


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AIReviewCog(bot))
