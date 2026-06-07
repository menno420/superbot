"""Shared moderation helpers (S4.3 extraction).

These were top-level helpers in ``cogs/moderation_cog.py`` consumed by
the cog (panel embed + help-menu hook) and the 7 modals (interaction-
time permission check).  Lifted here per the F-3 convention so they
live alongside future moderation domain modules and are importable by
both the cog and ``views/moderation/*`` without creating a circular
import through ``cogs.moderation_cog``.

Names (kept identical to the pre-extraction layout so the diff stays
focused on relocation):

    _build_mod_panel_embed       — embed factory for the mod panel
    _can_act_on_interaction      — interaction-time hierarchy / owner check
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import Member

from core.runtime import resources
from core.runtime.component_registry import stats_block
from utils.ui_constants import MOD_COLOR

if TYPE_CHECKING:
    from services import moderation_service


def _build_mod_panel_embed(guild: discord.Guild | None = None) -> discord.Embed:
    """Build the moderation panel embed.

    When *guild* is supplied (the live ``!modmenu`` / slash / help routes), a
    read-only **Bot readiness** field reports whether the bot actually holds
    Ban / Kick / Timeout and where its role sits in the hierarchy — so an
    operator can see *before* clicking why an action might fail (PR10).
    Restored persistent panels keep their original embed (no guild at restore
    time), so the field simply isn't shown there until the panel is reopened.
    """
    embed = stats_block(
        "🔨 Moderation Panel",
        [
            ("⚠️ Warn", "Issue a warning (auto-timeout at 3)", True),
            ("⏳ Timeout", "Temporarily mute for N minutes", True),
            ("👢 Kick", "Remove from server", True),
            ("🚫 Ban", "Permanently ban", True),
            ("✅ Unban", "Lift a ban by user ID", True),
            ("📋 Mod Logs", "View moderation history", True),
            ("⬛ Clear Warnings", "Reset warning count", True),
        ],
        MOD_COLOR,
        description=(
            "Click a button to take a moderation action.\n"
            "You'll be prompted to enter the user and reason."
        ),
        footer="Any staff member with Moderate Members permission may use this panel.",
    )
    if guild is not None:
        from utils.moderation_feasibility import (
            evaluate_moderation_readiness,
            render_readiness_line,
        )

        readiness = evaluate_moderation_readiness(guild)
        embed.add_field(
            name="🤖 Bot readiness",
            value=render_readiness_line(readiness),
            inline=False,
        )
    return embed


def _can_act_on_interaction(
    interaction: discord.Interaction,
    member: Member,
) -> str | None:
    """Return an error string if the actor cannot moderate *member*, else None."""
    if member == interaction.guild.owner:
        return "❌ You cannot perform this action on the server owner."
    actor = resources.resolve_member(interaction.guild, interaction.user.id)
    if actor and member.top_role >= actor.top_role:
        return (
            "❌ You cannot perform this action on someone with an equal or higher role."
        )
    if member.top_role >= interaction.guild.me.top_role:
        return (
            "❌ I cannot perform this action — that member has a higher role than me."
        )
    return None


def render_warn_outcome_lines(
    member_mention: str,
    reason: str,
    outcome: moderation_service.WarnOutcome,
) -> list[str]:
    """Render the operator-facing reply line(s) for a warn + any escalation.

    Shared by ``!warn`` and the panel's ``_WarnModal`` so both surfaces render
    one consistent message.  The escalation itself is **owned by**
    ``services.moderation_service.warn`` (PR10 third slice) — this only formats
    the :class:`~services.moderation_service.WarnOutcome` it returns.  The first
    line is always the warning confirmation; a second line reports the
    escalation (or the soft "I lack permission" notice when Discord refused it).
    """
    lines = [
        f"⚠️ {member_mention} warned ({outcome.count}/{outcome.threshold}). "
        f"Reason: {reason or 'No reason provided'}",
    ]
    action = outcome.escalation_action
    if outcome.escalation_blocked and action:
        lines.append(
            f"⚠️ Reached {outcome.threshold} warnings but I lack permission "
            f"to {action} this user.",
        )
    elif outcome.escalated and action == "timeout":
        lines.append(
            f"⏳ {member_mention} timed out for {outcome.timeout_minutes} "
            f"minutes ({outcome.threshold} warnings).",
        )
    elif outcome.escalated and action == "kick":
        lines.append(f"👢 {member_mention} kicked ({outcome.threshold} warnings).")
    elif outcome.escalated and action == "ban":
        lines.append(f"🚫 {member_mention} banned ({outcome.threshold} warnings).")
    return lines
