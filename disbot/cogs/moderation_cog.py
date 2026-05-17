from __future__ import annotations

import logging
from datetime import timedelta

import discord
from discord import Member
from discord.ext import commands

from cogs.moderation._helpers import _build_mod_panel_embed
from core.runtime import panel_manager
from utils import db
from utils.settings_keys import WARN_THRESHOLD, WARN_TIMEOUT_MINS
from utils.ui_constants import MOD_COLOR

# Pattern B re-export: importing this triggers @register on ModPanelView
# so the persistent-view registry is populated before on_ready runs
# restore_anchors.  See docs/architecture.md §"PersistentView placement".
from views.moderation import ModPanelView  # noqa: F401 — re-exported

logger = logging.getLogger("bot")


class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _can_act_on(self, ctx, member: Member) -> str | None:
        if member == ctx.guild.owner:
            return "❌ You cannot perform this action on the server owner."
        if member.top_role >= ctx.author.top_role:
            return "❌ You cannot perform this action on someone with an equal or higher role."
        if member.top_role >= ctx.guild.me.top_role:
            return "❌ I cannot perform this action — that member has a higher role than me."
        return None

    async def log_action(
        self,
        ctx,
        action: str,
        member,
        reason: str = "No reason provided",
    ):
        await db.log_mod_action(ctx.guild.id, action, member.id, ctx.author.id, reason)
        logger.info(
            "MOD | %s | %s | by %s | %s",
            action.upper(),
            member,
            ctx.author,
            reason,
        )

    # ------------------------------------------------------------------
    # Moderation panel (action-first interactive UI)
    # ------------------------------------------------------------------

    @commands.command(name="modmenu")
    @commands.has_permissions(moderate_members=True)
    async def mod_menu(self, ctx):
        """Show the interactive moderation action panel."""
        embed = _build_mod_panel_embed()
        view = ModPanelView()
        await panel_manager.get_or_render_panel(ctx, "moderation", embed, view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the moderation panel)."""
        return _build_mod_panel_embed(), ModPanelView()

    # ------------------------------------------------------------------
    # Traditional text commands (kept for direct use)
    # ------------------------------------------------------------------

    @commands.command(name="warn", hidden=True)
    @commands.has_permissions(manage_roles=True)
    async def warn(self, ctx, member: Member, *, reason="No reason provided"):
        """Warn a user. Auto-timeouts at the configured threshold (default: 3)."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        threshold = int(await db.get_setting(ctx.guild.id, WARN_THRESHOLD, "3"))
        timeout_minutes = int(
            await db.get_setting(ctx.guild.id, WARN_TIMEOUT_MINS, "10"),
        )
        count = await db.add_warning(member.id, ctx.guild.id)
        await ctx.send(
            f"⚠️ {member.mention} warned ({count}/{threshold}). Reason: {reason}",
        )
        await self.log_action(ctx, "warn", member, reason)
        if count >= threshold:
            try:
                until = discord.utils.utcnow() + timedelta(minutes=timeout_minutes)
                await member.timeout(until, reason=f"{threshold} warnings reached.")
                await ctx.send(
                    f"⏳ {member.mention} timed out for {timeout_minutes} minutes "
                    f"({threshold} warnings).",
                )
                await db.clear_warnings(member.id, ctx.guild.id)
            except discord.Forbidden:
                await ctx.send(
                    f"⚠️ Reached {threshold} warnings but I lack permission to timeout this user.",
                )

    @commands.command(name="timeout", hidden=True)
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: Member, duration: int):
        """Timeout a member for a given number of minutes."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        try:
            until = discord.utils.utcnow() + timedelta(minutes=duration)
            await member.timeout(until, reason=f"Timeout by {ctx.author}")
            await ctx.send(f"⏳ {member.mention} timed out for {duration} minute(s).")
            await self.log_action(ctx, "timeout", member, f"{duration} minutes")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to timeout that user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to timeout: {e}")

    @commands.command(name="kick", hidden=True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: Member, *, reason="No reason provided"):
        """Kick a member from the server."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        try:
            await member.kick(reason=reason)
            await ctx.send(f"👢 {member.mention} kicked. Reason: {reason}")
            await self.log_action(ctx, "kick", member, reason)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick that user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to kick: {e}")

    @commands.command(name="ban", hidden=True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: Member, *, reason="No reason provided"):
        """Ban a member from the server."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        try:
            await member.ban(reason=reason)
            await ctx.send(f"🚫 {member.mention} banned. Reason: {reason}")
            await self.log_action(ctx, "ban", member, reason)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban that user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to ban: {e}")

    @commands.command(name="unban", hidden=True)
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """Unban a user by their Discord user ID."""
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            await ctx.send(f"❌ No user found with ID `{user_id}`.")
            return
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to fetch user: {e}")
            return
        try:
            await ctx.guild.unban(user)
            await ctx.send(f"✅ {user.mention} unbanned.")
            await self.log_action(ctx, "unban", user)
        except discord.NotFound:
            await ctx.send(f"❌ User `{user_id}` is not banned.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unban.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to unban: {e}")

    @commands.command(name="clearwarnings", hidden=True)
    @commands.has_permissions(manage_roles=True)
    async def clearwarnings(self, ctx, member: Member):
        """Clear all warnings for a member."""
        await db.clear_warnings(member.id, ctx.guild.id)
        await ctx.send(f"✅ Warnings cleared for {member.mention}.")
        await self.log_action(ctx, "clearwarnings", member)

    @commands.command(name="modlogs", hidden=True)
    @commands.has_permissions(manage_roles=True)
    async def modlogs(self, ctx, member: Member):
        """Show moderation log history for a member."""
        logs = await db.get_mod_logs(member.id, ctx.guild.id, limit=10)
        embed = discord.Embed(
            title=f"📋 Mod Logs — {member.display_name}",
            color=MOD_COLOR,
        )
        if not logs:
            embed.description = "No moderation history found."
        else:
            for entry in logs:
                embed.add_field(
                    name=f"{entry['action'].upper()} — {entry['timestamp']}",
                    value=f"By <@{entry['moderator_id']}> | {entry['reason']}",
                    inline=False,
                )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
