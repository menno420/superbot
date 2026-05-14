from __future__ import annotations
import discord
from discord.ext import commands
from discord import Member
from datetime import timedelta
import logging
from utils import db

logger = logging.getLogger("bot")


class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_action(self, ctx, action: str, member, reason: str = "No reason provided"):
        await db.log_mod_action(ctx.guild.id, action, member.id, ctx.author.id, reason)
        logger.info("MOD | %s | %s | by %s | %s", action.upper(), member, ctx.author, reason)

    def _can_act_on(self, ctx, member: Member) -> str | None:
        """Returns an error message if the action is not allowed, else None."""
        if member == ctx.guild.owner:
            return "❌ You cannot perform this action on the server owner."
        if member.top_role >= ctx.author.top_role:
            return "❌ You cannot perform this action on someone with an equal or higher role."
        if member.top_role >= ctx.guild.me.top_role:
            return "❌ I cannot perform this action — that member has a higher role than me."
        return None

    # ------------------------------------------------------------------
    # Warn
    # ------------------------------------------------------------------
    @commands.command(name='warn')
    @commands.has_permissions(manage_roles=True)
    async def warn(self, ctx, member: Member, *, reason='No reason provided'):
        """Warn a user. Three warnings result in a 10-minute timeout."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return

        count = await db.add_warning(member.id, ctx.guild.id)
        await ctx.send(f"⚠️ {member.mention} warned ({count}/3). Reason: {reason}")
        await self.log_action(ctx, "warn", member, reason)

        if count >= 3:
            try:
                until = discord.utils.utcnow() + timedelta(minutes=10)
                await member.timeout(until, reason="3 warnings reached.")
                await ctx.send(f"⏳ {member.mention} timed out for 10 minutes (3 warnings).")
                await db.clear_warnings(member.id, ctx.guild.id)
            except discord.Forbidden:
                await ctx.send("⚠️ Reached 3 warnings but I lack permission to timeout this user.")

    # ------------------------------------------------------------------
    # Timeout
    # ------------------------------------------------------------------
    @commands.command(name='timeout')
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

    # ------------------------------------------------------------------
    # Kick
    # ------------------------------------------------------------------
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: Member, *, reason='No reason provided'):
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

    # ------------------------------------------------------------------
    # Ban
    # ------------------------------------------------------------------
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: Member, *, reason='No reason provided'):
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

    # ------------------------------------------------------------------
    # Unban
    # ------------------------------------------------------------------
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_name: str):
        """Unban a user by their username."""
        try:
            bans = [entry async for entry in ctx.guild.bans()]
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to view the ban list.")
            return
        for entry in bans:
            if entry.user.name == member_name:
                await ctx.guild.unban(entry.user)
                await ctx.send(f"✅ {entry.user.mention} unbanned.")
                await self.log_action(ctx, "unban", entry.user)
                return
        await ctx.send(f"❌ No banned user found with name `{member_name}`.")


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
