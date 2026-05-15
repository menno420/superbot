from __future__ import annotations

import logging
from datetime import datetime

import discord
from discord.ext import commands, tasks
from utils import db
from utils.helpers import normalize_name
from utils.ui_constants import ROLE_COLOR
from views.roles._helpers import _ensure_defaults, _find_role_normalized, _parse_color

logger = logging.getLogger("bot")


class RoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.role_check.start()

    def cog_unload(self) -> None:
        self.role_check.cancel()

    # ------------------------------------------------------------------ background loop

    @tasks.loop(hours=24)
    async def role_check(self) -> None:
        for guild in self.bot.guilds:
            await self._assign_roles(guild)

    @role_check.before_loop
    async def before_role_check(self) -> None:
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------ core assignment logic

    async def _assign_roles(
        self, guild: discord.Guild, ctx: commands.Context = None
    ) -> int:
        """Assign time-based roles to all members. Returns count of assignments made."""
        await _ensure_defaults(guild.id)
        thresholds = await db.get_role_thresholds(guild.id)
        if not thresholds:
            return 0

        role_map = {row["role_name"]: row["days_required"] for row in thresholds}
        progression = sorted(role_map, key=lambda r: role_map[r])

        skip_role_names = [
            n.strip()
            for n in (await db.get_setting(guild.id, "skip_roles", "Admin")).split(",")
            if n.strip()
        ]
        admin_role = next(
            (
                r
                for name in skip_role_names
                for r in [_find_role_normalized(guild, name)]
                if r
            ),
            None,
        )
        assigned = 0

        for member in guild.members:
            if member.bot:
                continue
            if admin_role and admin_role in member.roles:
                continue
            if not member.joined_at:
                continue

            days = (datetime.utcnow() - member.joined_at.replace(tzinfo=None)).days

            target_name = None
            for name in progression:
                if days >= role_map[name]:
                    target_name = name

            target_role = (
                _find_role_normalized(guild, target_name) if target_name else None
            )

            current_highest: str | None = None
            for role in member.roles:
                matched = next(
                    (
                        n
                        for n in role_map
                        if normalize_name(n) == normalize_name(role.name)
                    ),
                    None,
                )
                if matched:
                    if current_highest is None or progression.index(
                        matched
                    ) > progression.index(current_highest):
                        current_highest = matched

            if (
                current_highest
                and target_name
                and progression.index(current_highest) > progression.index(target_name)
            ):
                continue

            to_remove = [
                r
                for r in member.roles
                if any(normalize_name(r.name) == normalize_name(n) for n in role_map)
                and r != target_role
            ]
            if to_remove:
                try:
                    await member.remove_roles(*to_remove)
                except (discord.Forbidden, discord.HTTPException):
                    pass

            if target_role and target_role not in member.roles:
                try:
                    await member.add_roles(target_role)
                    assigned += 1
                    logger.info(
                        "Assigned %s to %s", target_role.name, member.display_name
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

        if ctx:
            await ctx.send(f"✅ Role check complete — {assigned} assignment(s) made.")
        return assigned

    # ------------------------------------------------------------------ primary commands

    @commands.command(name="roles")
    async def roles_hub(self, ctx: commands.Context) -> None:
        """Open the role management hub."""
        from views.roles.main_panel import RoleHubView

        view = RoleHubView(ctx, self)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg

    @commands.command(name="rolesettings")
    @commands.has_permissions(administrator=True)
    async def rolesettings(self, ctx: commands.Context) -> None:
        """Open the role management hub (alias for !roles)."""
        await ctx.invoke(self.roles_hub)

    # ------------------------------------------------------------------ compatibility aliases (hidden)

    @commands.command(name="rolemenu", hidden=True)
    async def rolemenu(self, ctx: commands.Context) -> None:
        """Open the role hub (use !roles instead)."""
        await ctx.invoke(self.roles_hub)

    @commands.command(name="rolecreator", hidden=True)
    @commands.has_permissions(manage_roles=True)
    async def rolecreator(self, ctx: commands.Context) -> None:
        """Open the role hub (use !roles instead)."""
        await ctx.invoke(self.roles_hub)

    @commands.command(name="assignroles", hidden=True)
    @commands.has_permissions(administrator=True)
    async def assign_roles_cmd(self, ctx: commands.Context) -> None:
        """Manually run time-based role assignment for all members."""
        await ctx.send("🔄 Running role assignment…")
        await self._assign_roles(ctx.guild, ctx)

    @commands.command(name="createrole", hidden=True)
    @commands.has_permissions(manage_roles=True)
    async def createrole(
        self,
        ctx: commands.Context,
        name: str,
        color: str = "000000",
        hoist: str = "no",
    ) -> None:
        """Create a role (use !roles → Create instead)."""
        try:
            col = _parse_color(color)
        except (ValueError, OverflowError):
            await ctx.send(
                "❌ Invalid color — use a hex code like `#3498db`.", delete_after=10
            )
            return
        do_hoist = hoist.lower() in ("yes", "true", "1", "y")
        try:
            role = await ctx.guild.create_role(name=name, color=col, hoist=do_hoist)
            await ctx.send(f"✅ Created role **{role.name}**.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create roles.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed: {e}")

    @commands.command(name="deleterole", hidden=True)
    @commands.has_permissions(manage_roles=True)
    async def deleterole(self, ctx: commands.Context, *, role: discord.Role) -> None:
        """Delete a role by name or mention."""
        if role >= ctx.guild.me.top_role:
            await ctx.send("❌ That role is higher than or equal to my top role.")
            return
        name = role.name
        try:
            await role.delete()
            await ctx.send(f"🗑️ Deleted role **{name}**.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete that role.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed: {e}")

    @commands.command(name="setrole", hidden=True)
    @commands.has_permissions(administrator=True)
    async def setrole(
        self, ctx: commands.Context, days: int, *, role_name: str
    ) -> None:
        """Add or update a time-based role threshold."""
        if days < 0:
            await ctx.send("Days must be 0 or greater.", delete_after=5)
            return
        discord_role = _find_role_normalized(ctx.guild, role_name)
        store_name = discord_role.name if discord_role else role_name
        await db.set_role_threshold(ctx.guild.id, store_name, days)
        await ctx.send(
            f"✅ Role **{store_name}** will be assigned after **{days}** day(s)."
        )

    @commands.command(name="unsetrole", hidden=True)
    @commands.has_permissions(administrator=True)
    async def unsetrole(self, ctx: commands.Context, *, role_name: str) -> None:
        """Remove a role from time-based assignment."""
        thresholds = await db.get_role_thresholds(ctx.guild.id)
        key = normalize_name(role_name)
        match = next(
            (
                r["role_name"]
                for r in thresholds
                if normalize_name(r["role_name"]) == key
            ),
            role_name,
        )
        await db.remove_role_threshold(ctx.guild.id, match)
        await ctx.send(f"✅ Removed **{match}** from the auto-assignment system.")

    @commands.command(name="debugroles", hidden=True)
    @commands.has_permissions(administrator=True)
    async def debug_roles(self, ctx: commands.Context) -> None:
        """Print all role names for verification."""
        names = [r.name for r in ctx.guild.roles]
        await ctx.send(f"Roles: {', '.join(names)}")

    @commands.command(name="refreshmembers", hidden=True)
    @commands.has_permissions(administrator=True)
    async def refresh_members(self, ctx: commands.Context) -> None:
        """Force-fetch all members from Discord."""
        await ctx.guild.chunk()
        await ctx.send("✅ Member list refreshed.")

    # ------------------------------------------------------------------ reaction role system

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        if payload.user_id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return
        role_id = await db.get_reaction_role(
            payload.guild_id, payload.message_id, str(payload.emoji)
        )
        if role_id:
            role = guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Reaction role")
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return
        role_id = await db.get_reaction_role(
            payload.guild_id, payload.message_id, str(payload.emoji)
        )
        if role_id:
            role = guild.get_role(role_id)
            if role:
                try:
                    await member.remove_roles(role, reason="Reaction role removed")
                except discord.Forbidden:
                    pass

    @commands.command(name="reactroles", aliases=["reaktionsrollen"])
    @commands.has_permissions(manage_roles=True)
    async def setup_reaction_roles(
        self, ctx: commands.Context, message_id: int, emoji: str, role: discord.Role
    ) -> None:
        """Attach a reaction role to a message. Usage: !reactroles <message_id> <emoji> <@role>"""
        try:
            message = await ctx.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("❌ Message not found in this channel.", delete_after=8)
            return
        except discord.Forbidden:
            await ctx.send("❌ I can't read that message.", delete_after=8)
            return

        await db.add_reaction_role(ctx.guild.id, message_id, emoji, role.id)
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await ctx.send(
                "⚠️ Role saved, but I couldn't add the reaction (invalid emoji?)."
            )
            return
        await ctx.send(
            f"✅ Reaction role set: reacting with {emoji} assigns **{role.name}**.",
            delete_after=15,
        )

    @commands.command(name="removereactrole")
    @commands.has_permissions(manage_roles=True)
    async def remove_reaction_role(
        self, ctx: commands.Context, message_id: int, emoji: str
    ) -> None:
        """Remove a reaction role binding. Usage: !removereactrole <message_id> <emoji>"""
        await db.remove_reaction_role(ctx.guild.id, message_id, emoji)
        await ctx.send(
            f"✅ Reaction role for {emoji} on that message removed.", delete_after=10
        )

    @commands.command(name="listreactroles")
    @commands.has_permissions(manage_roles=True)
    async def list_reaction_roles(self, ctx: commands.Context) -> None:
        """List all active reaction roles in this server."""
        rows = await db.get_all_reaction_roles(ctx.guild.id)
        if not rows:
            await ctx.send("No reaction roles configured.", delete_after=8)
            return
        lines = []
        for r in rows:
            role = ctx.guild.get_role(r["role_id"])
            role_str = role.mention if role else f"<deleted role {r['role_id']}>"
            lines.append(f"Message `{r['message_id']}` · {r['emoji']} → {role_str}")
        embed = discord.Embed(
            title="⚙️ Reaction Roles",
            description="\n".join(lines),
            color=ROLE_COLOR,
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------ on_member_join

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return
        await _ensure_defaults(member.guild.id)
        thresholds = await db.get_role_thresholds(member.guild.id)
        zero_day = next(
            (r["role_name"] for r in thresholds if r["days_required"] == 0), None
        )
        if not zero_day:
            return
        role = _find_role_normalized(member.guild, zero_day)
        if role:
            try:
                await member.add_roles(role)
                logger.info(
                    "Assigned '%s' to %s on join.", zero_day, member.display_name
                )
            except (discord.Forbidden, discord.HTTPException):
                pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RoleCog(bot))
    logger.info("RoleCog loaded.")
