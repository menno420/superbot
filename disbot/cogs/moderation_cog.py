import discord
from discord.ext import commands
from discord import Member
from datetime import timedelta
import logging
import asyncio
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/moderation.db")
LOG_PATH = os.path.join(os.path.dirname(__file__), "../data/json/mod_logs.json")

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self._setup_database()

    def _setup_database(self):
        """Create tables if they don't exist."""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS warnings (
            user_id INTEGER,
            guild_id INTEGER,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )''')
        self.conn.commit()

    async def log_action(self, ctx, action: str, member: Member, reason: str = "No reason provided"):
        """Logs actions in a JSON file."""
        log_data = {
            "guild": ctx.guild.name,
            "action": action,
            "member": member.id,
            "moderator": ctx.author.id,
            "reason": reason
        }
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as log_file:
            log_file.write(str(log_data) + "\n")

    @commands.command(name='warn')
    @commands.has_permissions(manage_roles=True)
    async def warn(self, ctx, member: Member, *, reason='No reason provided'):
        """Warn a user and track warnings in the database."""
        if member == ctx.guild.owner or member.top_role >= ctx.author.top_role:
            await ctx.send(f"❌ You cannot warn this user.")
            return

        self.cursor.execute("SELECT count FROM warnings WHERE user_id = ? AND guild_id = ?", (member.id, ctx.guild.id))
        result = self.cursor.fetchone()
        warning_count = (result[0] + 1) if result else 1

        if result:
            self.cursor.execute("UPDATE warnings SET count = ? WHERE user_id = ? AND guild_id = ?", (warning_count, member.id, ctx.guild.id))
        else:
            self.cursor.execute("INSERT INTO warnings (user_id, guild_id, count) VALUES (?, ?, ?)", (member.id, ctx.guild.id, warning_count))
        self.conn.commit()

        await ctx.send(f"⚠️ {member.mention} has been warned. Reason: {reason}. Warning count: {warning_count}")
        await self.log_action(ctx, "warn", member, reason)

        if warning_count >= 3:
            await self.timeout(ctx, member, 10)
            self.cursor.execute("DELETE FROM warnings WHERE user_id = ? AND guild_id = ?", (member.id, ctx.guild.id))
            self.conn.commit()

    @commands.command(name='timeout')
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: Member, duration: int):
        """Timeout a member for a specific duration (minutes)."""
        if member.top_role >= ctx.author.top_role:
            await ctx.send("❌ You cannot timeout this user.")
            return

        await member.timeout(discord.utils.utcnow() + timedelta(minutes=duration), reason="Timeout issued by a moderator.")
        await ctx.send(f"⏳ {member.mention} has been timed out for {duration} minutes.")
        await self.log_action(ctx, "timeout", member, f"Timed out for {duration} minutes")

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: Member, *, reason='No reason provided'):
        """Kick a member from the server."""
        if member.top_role >= ctx.author.top_role:
            await ctx.send("❌ You cannot kick this user.")
            return

        await member.kick(reason=reason)
        await ctx.send(f"👢 {member.mention} has been kicked. Reason: {reason}")
        await self.log_action(ctx, "kick", member, reason)

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: Member, *, reason='No reason provided'):
        """Ban a user."""
        if member.top_role >= ctx.author.top_role:
            await ctx.send("❌ You cannot ban this user.")
            return

        await member.ban(reason=reason)
        await ctx.send(f"🚫 {member.mention} has been banned. Reason: {reason}")
        await self.log_action(ctx, "ban", member, reason)

    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_name):
        """Unban a previously banned user."""
        banned_users = await ctx.guild.bans()
        for entry in banned_users:
            user = entry.user
            if user.name == member_name:
                await ctx.guild.unban(user)
                await ctx.send(f"✅ {user.mention} has been unbanned.")
                await self.log_action(ctx, "unban", user)
                return
        await ctx.send("❌ User not found in ban list.")

# Function to load this cog
async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
