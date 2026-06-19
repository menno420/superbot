"""Shared moderation helpers (S4.3 extraction; relocated to ``services/`` in A2).

These were top-level helpers in ``cogs/moderation_cog.py`` consumed by
the cog (panel embed + help-menu hook) and the 7 modals (interaction-
time permission check).  They now live in ``services/`` so both the cog
and ``views/moderation/*`` import them from the same allowed layer
(views may import services), clearing the tracked ``views → cogs``
layer-boundary debt without creating a circular import through
``cogs.moderation_cog``.

Names (kept identical to the pre-relocation layout so the diff stays
focused on relocation):

    _build_mod_panel_embed       — embed factory for the mod panel
    _can_act_on_interaction      — interaction-time hierarchy / owner check
    _sweepable_channel           — narrow a surface's channel for the sweep
    render_warn_outcome_lines    — operator-facing warn reply line(s)
    render_cleanup_outcome_line  — operator-facing post-action sweep line
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


def _sweepable_channel(
    channel: object,
) -> discord.TextChannel | discord.Thread | None:
    """Narrow a surface's channel to one the post-action sweep can scan.

    Only text channels and threads have meaningful message history to sweep;
    anything else (a category, a voice channel, ``None`` on a restored panel)
    yields ``None`` so ``moderation_service`` skips the optional cleanup.
    Keeping the check here means the cog and the panel modals narrow
    identically.
    """
    if isinstance(channel, (discord.TextChannel, discord.Thread)):
        return channel
    return None


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


def render_cleanup_outcome_line(
    member_mention: str,
    outcome: moderation_service.CleanupOutcome | None,
) -> str | None:
    """Render the post-action cleanup line for a kick/ban, or ``None`` to stay quiet.

    The sweep is **owned by** ``services.moderation_service`` (PR10 fourth slice)
    and only runs when the guild enables ``post_action_cleanup`` for the action;
    this just formats the returned
    :class:`~services.moderation_service.CleanupOutcome` so ``!kick`` / ``!ban``
    and the panel's kick/ban modals report it identically.  Returns ``None`` when
    no sweep was due or nothing was deleted (no line is shown).
    """
    if outcome is None or not outcome.requested:
        return None
    if outcome.blocked:
        return (
            f"🧽 Couldn't sweep {member_mention}'s recent messages here "
            "(I need Manage Messages + Read Message History)."
        )
    if outcome.deleted == 0:
        return None
    plural = "s" if outcome.deleted != 1 else ""
    suffix = f" ({outcome.failed} could not be removed)" if outcome.failed else ""
    return (
        f"🧽 Removed {outcome.deleted} recent message{plural} from "
        f"{member_mention} in this channel.{suffix}"
    )
