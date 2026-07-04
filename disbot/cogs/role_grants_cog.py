"""Free temporary roles — the grant command + the periodic expiry sweep (PR 4).

Mirrors the ``MediaMaintenanceCog`` / ``HealthMaintenanceCog`` pattern: a
``discord.ext.tasks`` loop, started on ``cog_load`` and cancelled on
``cog_unload``, that scans each guild for lapsed ``role_grants`` and removes the
roles through the audited :mod:`services.role_grants_service`. The cog is a thin
shell — all role math + audit lives in the service.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands, tasks

from core.runtime.permission_checks import member_has_perms_or_owner, perms_or_owner
from services import role_grants_service
from utils import role_feasibility
from utils.duration import format_duration, parse_duration

logger = logging.getLogger("bot.cogs.role_grants")

# Cadence: expiry is approximate to within one tick. 5 min keeps the sweep cheap
# while feeling prompt — matches the media/health maintenance loops.
_SWEEP_MINUTES = 5


class RoleGrantsCog(commands.Cog):
    """Grant temporary roles and sweep them away once they expire."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self._sweep_loop.start()

    def cog_unload(self) -> None:
        self._sweep_loop.cancel()

    # ------------------------------------------------------------------ sweep
    @tasks.loop(minutes=_SWEEP_MINUTES)
    async def _sweep_loop(self) -> None:
        try:
            for guild in list(self.bot.guilds):
                resolved = await role_grants_service.sweep_expired(guild)
                if resolved:
                    logger.info(
                        "role_grants: resolved %d expired grant(s) in guild=%d",
                        resolved,
                        guild.id,
                    )
        except (
            Exception
        ):  # noqa: BLE001 — a transient DB/Discord blip must not kill the loop
            logger.exception("role_grants: expiry sweep failed")

    @_sweep_loop.before_loop
    async def _before_sweep(self) -> None:
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------ command
    @commands.command(name="temprole")
    @perms_or_owner(manage_roles=True)
    async def temprole(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        role: discord.Role,
    ) -> None:
        """Give a member a role for a limited time. Usage: !temprole @member 2h @role"""
        seconds = parse_duration(duration)
        if not seconds:
            await ctx.send(
                "❌ Invalid duration — try `30m`, `2h`, or `7d` (max 1 year).",
                delete_after=10,
            )
            return
        if not role_feasibility.evaluate_role(role, bot_member=ctx.guild.me).ok:
            await ctx.send(
                "❌ I can't manage that role — it's above my highest role.",
                delete_after=10,
            )
            return
        try:
            expires = await role_grants_service.grant_temp_role(
                ctx.guild,
                member,
                role,
                seconds=seconds,
                actor_id=ctx.author.id,
            )
        except discord.Forbidden:
            await ctx.send(
                "❌ I couldn't assign that role (missing permission).",
                delete_after=10,
            )
            return
        await ctx.send(
            f"✅ Gave {member.mention} **{role.name}** for {format_duration(seconds)} "
            f"— expires <t:{int(expires.timestamp())}:R>.",
        )

    @commands.command(name="temproles")
    @commands.guild_only()
    async def temproles(
        self,
        ctx: commands.Context,
        member: discord.Member | None = None,
    ) -> None:
        """List active temporary roles. Usage: !temproles (yours) or !temproles @member (staff)."""
        author = ctx.author
        target = member or author
        is_self = target.id == author.id
        author_is_staff = member_has_perms_or_owner(author, manage_roles=True)
        if not is_self and not author_is_staff:
            await ctx.send(
                "❌ You can only view your own temp roles — viewing another "
                "member's needs Manage Roles.",
                delete_after=10,
            )
            return

        grants = await role_grants_service.list_active_grants(ctx.guild, target.id)
        whose = "You have" if is_self else f"**{target.display_name}** has"
        if not grants:
            await ctx.send(f"📭 {whose} no active temp roles.")
            return

        lines = [
            f"• {role.mention} — expires <t:{int(expires.timestamp())}:R>"
            for role, expires in grants
        ]
        header = f"⏳ {whose} {len(grants)} active temp role(s):"
        await ctx.send(header + "\n" + "\n".join(lines))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RoleGrantsCog(bot))
    logger.info("RoleGrantsCog loaded.")
