"""XP on_message handler (S4.2 extraction).

The pre-decomposition listener body was ~95 LOC inside
``cogs/xp_cog.py``.  Extracted here per the F-3 convention so the
cog file stays focused on commands and the handler is unit-testable
without spinning up the full XpCog instance.

Two entry points:

  handle_message(bot, message)        — drives the full cooldown +
                                         award + announce + role-grant
                                         flow.  Called from
                                         XpCog.on_message.
  announce_level_up(bot, message,     — extracted level-up bookkeeping
                    new_xp, new_level)  (announcement + log embed +
                                         role assignment).
"""

from __future__ import annotations

import logging
import random
import time

import discord
from discord.ext import commands

from core.runtime import resources
from services import xp_service
from utils import db
from utils.cooldowns import check_cooldown
from utils.guild_config_accessors import get_xp_config, get_xp_threshold_roles
from utils.helpers import post_log_embed
from utils.ui_constants import ECONOMY_COLOR

logger = logging.getLogger("bot.cogs.xp.listener")


async def _xp_participation_allowed(user_id: int, guild_id: int) -> bool:
    """Return True when the XP award should proceed for this user/guild.

    Phase 2c PR-9 gate.  Centralised here so any future XP entry path
    can call the same helper; the rule is NOT duplicated across XP
    commands.

    Resolution:

    * If ``participation.enabled`` is OFF (declared default), return
      True unconditionally — pre-PR-9 behavior is preserved exactly.
    * If ON, consult the typed ``get_participation`` accessor.  Only
      :class:`ParticipationState.OPTED_OUT` blocks the award; OPTED_IN
      and NOT_SET both allow it.
    * Any exception from the flag evaluator or the accessor is logged
      and the gate falls open (returns True).  XP is never blocked
      because of a transient runtime fault; the operator can flip the
      flag off if the gate misbehaves.
    """
    # Local imports — keep the cog/listener module light at import time
    # and out of any module-load cycles.
    from core.runtime import feature_flags
    from utils.user_config_accessors import ParticipationState, get_participation

    try:
        flag_on = await feature_flags.is_enabled(
            "participation.enabled",
            guild_id,
        )
    except Exception as exc:  # noqa: BLE001 — gate must fall open on flag error
        logger.warning(
            "xp.listener: is_enabled(participation.enabled) raised for "
            "guild=%d (%r); fall open",
            guild_id,
            exc,
        )
        return True
    if not flag_on:
        return True

    try:
        state = await get_participation(user_id, guild_id, "xp")
    except Exception as exc:  # noqa: BLE001 — gate must fall open on accessor error
        logger.warning(
            "xp.listener: get_participation raised for user=%d guild=%d (%r); "
            "fall open",
            user_id,
            guild_id,
            exc,
        )
        return True
    return state is not ParticipationState.OPTED_OUT


async def handle_message(bot: commands.Bot, message: discord.Message) -> None:
    """The XP on_message hot path.  Bot/no-guild messages are dropped early.

    Hits the F-1 cached config (S2.2) on the common cooldown-skipped
    path so most messages run with zero DB-config reads.
    """
    if message.author.bot or not message.guild:
        return

    user_id = message.author.id
    guild_id = message.guild.id
    now = int(time.time())

    cfg = await get_xp_config(guild_id)

    row = await db.get_xp(user_id, guild_id)
    on_cd, _ = check_cooldown(row["last_xp"], cfg.cooldown)
    if on_cd:
        return

    # Phase 2c PR-9 participation gate.  When ``participation.enabled``
    # is OFF (the declared default), behavior is identical to pre-PR-9
    # — every non-cooldown'd message awards XP.  When the flag is ON,
    # a user who has opted out of the ``"xp"`` subsystem skips the
    # award path entirely.  Opted-in / NOT_SET continue normally.
    #
    # Local imports preserve cycle-safety: ``core.runtime.feature_flags``
    # and ``utils.user_config_accessors`` are only touched when this
    # listener actually runs.
    if not await _xp_participation_allowed(user_id, guild_id):
        return

    amount = random.randint(cfg.xp_min, cfg.xp_max)
    result = await xp_service.award(
        guild_id=guild_id,
        user_id=user_id,
        amount=amount,
        source="chat",
        now=now,
    )

    if result.leveled_up:
        await announce_level_up(
            bot,
            message,
            new_xp=result.new_xp,
            new_level=result.new_level,
            announce_channel=cfg.announce_channel,
        )


async def announce_level_up(
    bot: commands.Bot,
    message: discord.Message,
    *,
    new_xp: int,
    new_level: int,
    announce_channel: str,
) -> None:
    """Post the level-up embed + log embed + apply XP threshold roles."""
    announce_ch: discord.TextChannel | None = None
    if announce_channel:
        announce_ch = resources.resolve_channel(  # type: ignore[assignment]
            message.guild,
            channel_id=announce_channel,
        )
    announce_ch = announce_ch or message.channel  # type: ignore[assignment]

    embed = discord.Embed(
        title="🎉 Level Up!",
        description=f"{message.author.mention} reached **Level {new_level}**!",
        color=ECONOMY_COLOR,
    )
    try:
        await announce_ch.send(embed=embed)
    except discord.Forbidden:
        pass

    log_embed = discord.Embed(
        title="🏆 Level Up",
        description=(
            f"{message.author.mention} reached **Level {new_level}**! "
            f"(Total XP: {new_xp})"
        ),
        color=ECONOMY_COLOR,
    )
    await post_log_embed(bot, message.guild.id, log_embed)

    await _apply_xp_threshold_roles(message, new_level)


async def _apply_xp_threshold_roles(
    message: discord.Message,
    new_level: int,
) -> None:
    """Grant XP-threshold roles whose level_required <= new_level.

    Hits the F-1 cached threshold-roles list (S2.2) so the role list
    is at most one DB read per (TTL × guild) instead of per-level-up.
    """
    try:
        from services import role_automation, role_exemption_service
        from services.role_automation import Assignment, summarize_failures

        guild = message.guild
        member = message.author
        member_role_ids = {r.id for r in getattr(member, "roles", ())}

        exempt = await role_exemption_service.get_exempt_role_ids(guild.id)
        if member_role_ids & exempt.xp:
            return  # member holds an XP-exempt role — grant nothing

        xp_roles = await get_xp_threshold_roles(guild.id)
        qualifying: list = []  # earned roles (level_required <= new_level)
        configured: list = []  # every configured XP role that resolves
        for role_cfg in xp_roles:
            # Id-first (PR6 migration 056), normalized-name fallback for legacy
            # rows — a renamed role keeps its XP tier.
            discord_role = resources.resolve_role(
                guild,
                role_id=role_cfg.get("role_id"),
                name=role_cfg["role_name"],
            )
            if discord_role is None:
                continue
            configured.append(discord_role)
            if role_cfg["level_required"] <= new_level:
                qualifying.append(discord_role)
        if not qualifying:
            return

        member_roles = member.roles  # type: ignore[union-attr]
        stack = await role_exemption_service.xp_roles_stack(guild.id)
        if stack:
            to_add = [r for r in qualifying if r not in member_roles]
            to_remove: list = []
        else:
            # Single-role mode: keep only the highest earned level role
            # (xp_roles is ordered by level_required ascending).
            target = qualifying[-1]
            to_add = [] if target in member_roles else [target]
            to_remove = [r for r in configured if r != target and r in member_roles]

        # Route the grant through the audited role_automation seam (one source of
        # truth for member-role mutation) rather than calling member.add_roles
        # directly — this fires `audit.action_recorded` and reuses the shared
        # manage-roles / hierarchy preflight, matching every other role grant in
        # the bot (Welcome's entry-role, the role cog). A direct add/remove here
        # was the one XP-side audit gap.
        member_display = getattr(member, "display_name", str(member.id))
        reason = f"XP level-up: reached level {new_level}"
        assignments: list[Assignment] = []
        if stack:
            # Stacking mode: one promote assignment per newly-earned role.
            for r in to_add:
                assignments.append(
                    Assignment(
                        member_id=member.id,
                        member_display=member_display,
                        add_role_id=r.id,
                        add_role_name=r.name,
                        remove_role_ids=(),
                        remove_role_names=(),
                        reason=reason,
                        days_in_guild=0,
                    ),
                )
        else:
            # Single-role mode: one assignment carries the promote + demotions.
            target = to_add[0] if to_add else None
            if target is not None or to_remove:
                assignments.append(
                    Assignment(
                        member_id=member.id,
                        member_display=member_display,
                        add_role_id=target.id if target is not None else None,
                        add_role_name=target.name if target is not None else None,
                        remove_role_ids=tuple(r.id for r in to_remove),
                        remove_role_names=tuple(r.name for r in to_remove),
                        reason=reason,
                        days_in_guild=0,
                    ),
                )

        if not assignments:
            return

        result = await role_automation.apply(guild, assignments, actor_type="system")
        if result.succeeded:
            logger.info(
                "XP roles applied for %s (level %d): %d change(s)",
                member_display,
                new_level,
                result.succeeded,
            )
        if result.failed:
            logger.warning(
                "XP role application had %d failure(s) for %s: %s",
                result.failed,
                member_display,
                summarize_failures(result),
            )
    except Exception:
        logger.error(
            "XP role assignment check failed for guild %d",
            message.guild.id,
            exc_info=True,
        )
