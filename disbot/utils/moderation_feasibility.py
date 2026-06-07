"""Pure moderation-readiness evaluation for the mod panel + diagnostics.

Answers "can the bot actually moderate in this guild?" as a structured
result rather than ad-hoc strings — which of ban / kick / timeout the bot's
permissions allow, plus its role-hierarchy ceiling (Discord only lets the bot
action members **below** its own top role).

This module is **pure**: no I/O and no service/cog/view imports (``utils`` may
import stdlib + ``discord`` only).  It mirrors :mod:`utils.role_feasibility`'s
shape so a single source of truth answers "can the bot moderate?" for the
moderation panel today and the Server-Management hub later.

It deliberately reports only what is knowable from ``guild.me`` alone — the
bot's own guild permissions and top role.  Per-target hierarchy/owner checks
(can *this* moderator act on *that* member) stay in
``cogs.moderation._helpers._can_act_on_interaction``; this is the guild-wide
"is the bot even able to act?" summary.
"""

from __future__ import annotations

from dataclasses import dataclass

import discord


@dataclass(frozen=True)
class ModerationReadiness:
    """Structured snapshot of the bot's moderation capability in one guild."""

    can_ban: bool
    can_kick: bool
    can_timeout: bool
    top_role_name: str
    # The bot's top role sits at the bottom of the hierarchy (``@everyone`` /
    # position 0) → it cannot action anyone until the role is moved up.
    top_role_is_lowest: bool

    @property
    def fully_capable(self) -> bool:
        """True when the bot holds ban + kick + timeout and can out-rank someone."""
        return (
            self.can_ban
            and self.can_kick
            and self.can_timeout
            and not self.top_role_is_lowest
        )

    def missing_permissions(self) -> tuple[str, ...]:
        """Human-readable names of the moderation permissions the bot lacks."""
        missing: list[str] = []
        if not self.can_ban:
            missing.append("Ban Members")
        if not self.can_kick:
            missing.append("Kick Members")
        if not self.can_timeout:
            missing.append("Timeout Members")
        return tuple(missing)


def evaluate_moderation_readiness(guild: discord.Guild) -> ModerationReadiness:
    """Evaluate the bot's moderation capability in *guild* from ``guild.me``.

    ``administrator`` implies every permission, so it satisfies each capability.
    """
    me = guild.me
    perms = me.guild_permissions
    admin = bool(perms.administrator)
    top_role = me.top_role
    return ModerationReadiness(
        can_ban=admin or bool(perms.ban_members),
        can_kick=admin or bool(perms.kick_members),
        can_timeout=admin or bool(perms.moderate_members),
        top_role_name=top_role.name,
        top_role_is_lowest=top_role.position == 0,
    )


def render_readiness_line(readiness: ModerationReadiness) -> str:
    """Render a short operator-facing status block for the mod panel."""
    missing = readiness.missing_permissions()
    if missing:
        lines = ["⚠️ Missing permission(s): " + ", ".join(missing) + "."]
    else:
        lines = ["🟢 I can warn, timeout, kick, and ban."]

    if readiness.top_role_is_lowest:
        lines.append(
            "⚠️ My top role is at the bottom of the list — I can't action "
            "anyone until it is moved up.",
        )
    else:
        lines.append(
            f"I can only action members below my top role "
            f"(**{readiness.top_role_name}**).",
        )
    return "\n".join(lines)


__all__ = [
    "ModerationReadiness",
    "evaluate_moderation_readiness",
    "render_readiness_line",
]
