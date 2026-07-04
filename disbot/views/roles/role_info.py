"""Read-only role detail card rendering for ``!roleinfo``.

Extracted from ``cogs.role_cog`` (the cog crossed the 800-LOC decomposition
threshold) — the embed builder + permission summariser are pure rendering, so
they belong in the ``views`` layer. The cog command stays a thin
resolve → render → send wrapper.
"""

from __future__ import annotations

import discord

from utils.ui_constants import ROLE_COLOR


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


# The notable permissions surfaced by !roleinfo, in display order — the staff/
# moderation-relevant ones, not the full 40-flag set.
_NOTABLE_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("manage_guild", "Manage Server"),
    ("manage_roles", "Manage Roles"),
    ("manage_channels", "Manage Channels"),
    ("manage_messages", "Manage Messages"),
    ("kick_members", "Kick Members"),
    ("ban_members", "Ban Members"),
    ("moderate_members", "Timeout Members"),
    ("mention_everyone", "Mention Everyone"),
    ("manage_webhooks", "Manage Webhooks"),
    ("manage_nicknames", "Manage Nicknames"),
)


def summarize_role_permissions(perms: discord.Permissions) -> str:
    """One-line summary of a role's notable permissions for !roleinfo.

    ``administrator`` short-circuits (it implies everything); otherwise list the
    notable staff/moderation flags the role carries, or note it has none.
    """
    if perms.administrator:
        return "Administrator (all permissions)"
    held = [label for attr, label in _NOTABLE_PERMISSIONS if getattr(perms, attr)]
    return ", ".join(held) if held else "No notable permissions"


def build_role_info_embed(
    role: discord.Role,
    *,
    requested_by: object,
) -> discord.Embed:
    """Render the read-only role detail card for ``!roleinfo``."""
    embed = discord.Embed(
        title=f"Role Info — {role.name}",
        color=role.color if role.color.value else ROLE_COLOR,
    )
    embed.add_field(name="Mention", value=role.mention, inline=True)
    embed.add_field(name="ID", value=str(role.id), inline=True)
    embed.add_field(
        name="Colour",
        value=(str(role.color) if role.color.value else "Default"),
        inline=True,
    )
    embed.add_field(name="Members", value=str(len(role.members)), inline=True)
    embed.add_field(name="Position", value=str(role.position), inline=True)
    embed.add_field(
        name="Created",
        value=role.created_at.strftime("%Y-%m-%d"),
        inline=True,
    )
    embed.add_field(name="Hoisted", value=_yes_no(role.hoist), inline=True)
    embed.add_field(name="Mentionable", value=_yes_no(role.mentionable), inline=True)
    embed.add_field(name="Managed", value=_yes_no(role.managed), inline=True)
    embed.add_field(
        name="Key Permissions",
        value=summarize_role_permissions(role.permissions),
        inline=False,
    )
    embed.set_footer(text=f"Requested by {requested_by}")
    return embed


__all__ = [
    "build_role_info_embed",
    "summarize_role_permissions",
]
