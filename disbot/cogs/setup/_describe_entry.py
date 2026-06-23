"""Entry points for ``/setup-describe`` and ``!setupdescribe`` — the
natural-language setup wedge.

Both invocations route through the same flow: collect the live guild snapshot,
ask the configured advisor for a plan *informed by the operator's free-form
description*
(:func:`services.setup_natural_language_advisor.suggest_from_description`), and
open the existing :class:`views.setup.ai_review.main_panel.AIReviewPanelView`
so the operator reviews → accepts → applies through the audited Final Review
path. Nothing is created or changed here; this surface only *proposes*.

Extracted from :mod:`cogs.setup_cog` to keep the cog file under the 800-LOC
ceiling, matching the sibling :mod:`cogs.setup._wizard_entry`.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

logger = logging.getLogger("bot.cogs.setup.describe_entry")

# Keep the free-form description bounded so an accidental paste can't bloat the
# prompt payload; the wedge only needs a sentence or two of intent.
_MAX_DESCRIPTION = 600

_EMPTY_HINT = (
    "Describe your server in a sentence or two and I'll propose how to wire it "
    "up — e.g. `a small gaming community; #mod-logs is for moderation logging "
    "and #welcome greets new members`."
)

# Shown when a description was given but the AI advisor isn't configured, so the
# plan came from deterministic name-matching and the description went unused.
_DETERMINISTIC_NOTE = (
    "ℹ️ AI isn't configured on this instance, so I matched by channel and role "
    "**names** instead — your description wasn't used. The suggestions below are "
    "still safe to review and apply."
)


async def _build_draft_and_note(
    guild: discord.Guild,
    description: str,
):  # noqa: ANN202 — returns (draft | None, snapshot | None, note)
    """Collect a snapshot and build a description-informed plan.

    Fail-safe: any snapshot/advisor error is logged and returned as
    ``(None, None, message)`` so the caller shows a friendly note instead of
    raising. Returns ``(draft, snapshot, note)`` on success, where *note* is an
    optional one-line caption for the reply.
    """
    from services import guild_snapshot
    from services.setup_natural_language_advisor import suggest_from_description

    try:
        snapshot = await guild_snapshot.collect(guild)
    except Exception:
        logger.exception("setup-describe: snapshot collect failed")
        return None, None, "I couldn't read this server's state to build a plan."

    try:
        draft = await suggest_from_description(snapshot, description)
    except Exception:
        logger.exception("setup-describe: advisor failed")
        return None, None, "The setup advisor couldn't produce a plan right now."

    note = _DETERMINISTIC_NOTE if draft.source != "openai" else None
    return draft, snapshot, note


def _clean_description(raw: str) -> str:
    return (raw or "").strip()[:_MAX_DESCRIPTION]


async def open_describe_from_slash(
    interaction: discord.Interaction,
    description: str,
) -> None:
    """Slash entry point. Ephemeral throughout."""
    guild = interaction.guild
    member = interaction.user
    if guild is None or not isinstance(member, discord.Member):
        await interaction.response.send_message(
            "Use `/setup-describe` from inside the server.",
            ephemeral=True,
        )
        return

    text = _clean_description(description)
    if not text:
        await interaction.response.send_message(_EMPTY_HINT, ephemeral=True)
        return

    # Snapshot + (possibly) an LLM round-trip can exceed the 3s ack window.
    from core.runtime.interaction_helpers import safe_defer

    if not await safe_defer(interaction, ephemeral=True, thinking=True):
        return
    draft, snapshot, note = await _build_draft_and_note(guild, text)
    if draft is None:
        await interaction.followup.send(
            note or "Couldn't build a plan.",
            ephemeral=True,
        )
        return

    from views.setup.ai_review.main_panel import (
        AIReviewPanelView,
        build_ai_review_embed,
    )

    view = AIReviewPanelView(member, draft=draft, snapshot=snapshot)
    message = await interaction.followup.send(
        content=note,
        embed=build_ai_review_embed(draft),
        view=view,
        ephemeral=True,
        wait=True,
    )
    view.message = message


async def open_describe_from_prefix(
    ctx: commands.Context,
    description: str,
) -> None:
    """Prefix entry point. Posts in the invoking channel (no ephemerals)."""
    guild = ctx.guild
    member = ctx.author
    if guild is None or not isinstance(member, discord.Member):
        await ctx.send("Run `!setupdescribe` from inside the server.")
        return

    text = _clean_description(description)
    if not text:
        await ctx.send(_EMPTY_HINT)
        return

    async with ctx.typing():
        draft, snapshot, note = await _build_draft_and_note(guild, text)
    if draft is None:
        await ctx.send(note or "Couldn't build a plan.")
        return

    from views.setup.ai_review.main_panel import (
        AIReviewPanelView,
        build_ai_review_embed,
    )

    view = AIReviewPanelView(member, draft=draft, snapshot=snapshot)
    message = await ctx.send(
        content=note,
        embed=build_ai_review_embed(draft),
        view=view,
    )
    view.message = message


__all__ = ["open_describe_from_prefix", "open_describe_from_slash"]
