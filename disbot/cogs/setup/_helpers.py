"""Setup cog helpers — module-level functions extracted from setup_cog.

The cog file holds the Discord-facing surface (commands + listeners);
these helpers handle the routine resolution + embed-building work
the commands compose. Extracting them keeps the cog under the S4.6
800-LOC ceiling and lets the helpers be unit-tested without a cog
fixture.

Exports:

* :func:`resolve_hub_entry` — gate-aware resolver that picks between
  the depth picker, the hub, the readiness embed, or denial based on
  the actor and the session state. Used by ``!setup`` and ``/setup``.
* :func:`build_status_embed` — read-only status snapshot for
  ``/setup-status``. Pure embed builder, no I/O.
"""

from __future__ import annotations

import logging

import discord

from services import setup_access, setup_session
from services.setup_session import SetupSession

logger = logging.getLogger("bot.cogs.setup.helpers")


async def resolve_hub_entry(
    member: discord.Member,
    guild: discord.Guild,
) -> (
    tuple[discord.Embed, discord.ui.View, str]
    | tuple[discord.Embed, None, str]
    | tuple[None, None, str]
):
    """Resolve the hub-entry response for ``member`` in ``guild``.

    Returns one of four shapes:

    * ``(depth_embed, depth_view, "depth_picker")`` — first-time entry
      for an apply-capable member with no depth chosen yet.
    * ``(hub_embed, hub_view, "hub")`` — member can apply setup and
      has a persisted depth; full hub renders, filtered by depth.
      Caller marks the session in progress.
    * ``(readiness_embed, None, "readiness")`` — member is a setup
      admin without apply authority; render the deterministic
      readiness embed instead.
    * ``(None, None, "denied")`` — member is not a setup admin.

    The helper performs no Discord send; the calling command decides
    whether to reply ephemerally (slash) or to ``ctx.send`` (prefix).
    """
    session = await setup_session.resume_session(guild.id)

    if setup_access.can_apply_setup(member, session):
        if session is None:
            try:
                session = await setup_session.start_session(
                    guild_id=guild.id,
                    guild_name=guild.name,
                    owner_id=guild.owner_id or 0,
                )
            except Exception:
                logger.exception(
                    "resolve_hub_entry: start_session failed",
                )
                session = None

        if session is not None and session.depth is None:
            from views.setup.depth_panel import (
                DepthPanelView,
                build_depth_embed,
            )

            view = DepthPanelView(member, session=session)
            return build_depth_embed(), view, "depth_picker"

        from services import setup_draft
        from views.setup.hub import SetupHubView, build_hub_embed

        try:
            draft_ops = await setup_draft.list_ops(guild.id)
        except Exception:
            logger.exception(
                "resolve_hub_entry: setup_draft.list_ops failed",
            )
            draft_ops = []
        hub = SetupHubView(member, session=session)
        embed = build_hub_embed(
            session,
            pending_ops=len(draft_ops),
            draft_ops=draft_ops,
        )
        return embed, hub, "hub"

    if setup_access.is_setup_admin(member, session):
        from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

        embed = await build_setup_readiness_embed(guild.id, guild=guild)
        return embed, None, "readiness"

    return None, None, "denied"


_STATUS_COLOR_BY_STATUS = {
    "pending": discord.Color.blurple(),
    "in_progress": discord.Color.gold(),
    "complete": discord.Color.green(),
    "dismissed": discord.Color.dark_grey(),
}


def build_status_embed(
    session: SetupSession | None,
    *,
    pending_ops: int,
) -> discord.Embed:
    """Render a read-only status snapshot for ``/setup-status``.

    Pure helper — takes a resolved session + the pending-op count and
    returns the embed. No DB / Discord I/O. Mirrors the data points
    the hub embed surfaces (status, depth, current step, readiness
    score, pending ops, skipped sections) but with no buttons.
    """
    status = session.setup_status if session is not None else "no session"
    color = _STATUS_COLOR_BY_STATUS.get(status, discord.Color.blurple())
    embed = discord.Embed(
        title="🛰 Setup status",
        description=f"**Status:** `{status}`",
        color=color,
    )
    if session is None:
        embed.add_field(
            name="No session row",
            value=(
                "The bot has not recorded any setup session for this guild. "
                "Run `!setup` or `/setup` to start."
            ),
            inline=False,
        )
        return embed

    if session.depth:
        embed.add_field(name="Depth", value=f"`{session.depth}`", inline=True)
    if session.current_step:
        embed.add_field(
            name="Current step",
            value=f"`{session.current_step}`",
            inline=True,
        )
    if session.last_readiness_score is not None:
        embed.add_field(
            name="Readiness",
            value=f"`{session.last_readiness_score}%`",
            inline=True,
        )
    embed.add_field(
        name="Pending operations",
        value=f"`{pending_ops}`",
        inline=True,
    )
    if session.skipped_sections:
        embed.add_field(
            name="Skipped sections",
            value=", ".join(f"`{s}`" for s in sorted(session.skipped_sections)),
            inline=False,
        )
    if session.delegated_admins:
        embed.add_field(
            name="Delegated admins",
            value=", ".join(f"<@{uid}>" for uid in session.delegated_admins),
            inline=False,
        )
    if session.setup_channel_id is not None:
        embed.add_field(
            name="Setup channel",
            value=f"<#{session.setup_channel_id}>",
            inline=True,
        )
    embed.set_footer(text="Read-only. Run `!setup` / `/setup` to make changes.")
    return embed


__all__ = [
    "build_status_embed",
    "resolve_hub_entry",
]
