from __future__ import annotations

from datetime import timedelta

import discord
from discord import Member, app_commands
from discord.ext import commands

from cogs.moderation._helpers import _build_mod_panel_embed
from core.runtime import panel_manager
from services import moderation_service
from utils import db
from utils.ui_constants import MOD_COLOR

# Pattern B re-export: importing this triggers @register on ModPanelView
# so the persistent-view registry is populated before on_ready runs
# restore_anchors.  See docs/architecture.md §"PersistentView placement".
from views.moderation import ModPanelView  # noqa: F401 — re-exported


class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self) -> None:
        from cogs.moderation.schemas import register_schemas

        register_schemas()

    def _can_act_on(self, ctx, member: Member) -> str | None:
        if member == ctx.guild.owner:
            return "❌ You cannot perform this action on the server owner."
        if member.top_role >= ctx.author.top_role:
            return "❌ You cannot perform this action on someone with an equal or higher role."
        if member.top_role >= ctx.guild.me.top_role:
            return "❌ I cannot perform this action — that member has a higher role than me."
        return None

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

    @app_commands.command(
        name="moderation",
        description="Open the Moderation hub (moderator only).",
    )
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def moderation_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for the Moderation hub — ephemeral, mod-only.

        PR E2 — privileged slash. Gated by ``moderate_members`` to
        mirror the ``!modmenu`` prefix command's permission check.
        Reuses :meth:`build_help_menu_view` so the embed + view are
        identical to the prefix / help routes.
        """
        embed, view = await self.build_help_menu_view(interaction)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # Traditional text commands (kept for direct use)
    #
    # Every mutating action routes through ``services.moderation_service``
    # (the single audited writer); this cog only authorizes, parses, and
    # renders.  Pinned by
    # ``tests/unit/invariants/test_no_direct_moderation_writes.py``.
    # ------------------------------------------------------------------

    @commands.command(name="warn", hidden=True)
    @commands.has_permissions(manage_roles=True)
    async def warn(self, ctx, member: Member, *, reason="No reason provided"):
        """Warn a user. Auto-timeouts at the configured threshold (default: 3)."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        # Read through the canonical scalar resolver so coercion +
        # validation are centralised; a malformed stored value falls
        # back to the SettingSpec default instead of raising.
        from services.settings_resolution import resolve_value

        threshold = await resolve_value(
            ctx.guild.id,
            "moderation",
            "warn_threshold",
            3,
        )
        timeout_minutes = await resolve_value(
            ctx.guild.id,
            "moderation",
            "warn_timeout_minutes",
            10,
        )
        count = await moderation_service.warn(
            member,
            reason=reason,
            actor_id=ctx.author.id,
        )
        await ctx.send(
            f"⚠️ {member.mention} warned ({count}/{threshold}). Reason: {reason}",
        )
        if count >= threshold:
            try:
                until = discord.utils.utcnow() + timedelta(minutes=timeout_minutes)
                await moderation_service.timeout(
                    member,
                    until=until,
                    reason=f"{threshold} warnings reached.",
                    actor_id=ctx.author.id,
                )
                await ctx.send(
                    f"⏳ {member.mention} timed out for {timeout_minutes} minutes "
                    f"({threshold} warnings).",
                )
                await moderation_service.clear_warnings(
                    ctx.guild.id,
                    member.id,
                    actor_id=ctx.author.id,
                )
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
            await moderation_service.timeout(
                member,
                until=until,
                reason=f"{duration} minutes",
                actor_id=ctx.author.id,
            )
            await ctx.send(f"⏳ {member.mention} timed out for {duration} minute(s).")
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
            await moderation_service.kick(
                member,
                reason=reason,
                actor_id=ctx.author.id,
            )
            await ctx.send(f"👢 {member.mention} kicked. Reason: {reason}")
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
            await moderation_service.ban(
                ctx.guild,
                member,
                reason=reason,
                actor_id=ctx.author.id,
            )
            await ctx.send(f"🚫 {member.mention} banned. Reason: {reason}")
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
            await moderation_service.unban(
                ctx.guild,
                user,
                reason="No reason provided",
                actor_id=ctx.author.id,
            )
            await ctx.send(f"✅ {user.mention} unbanned.")
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
        await moderation_service.clear_warnings(
            ctx.guild.id,
            member.id,
            actor_id=ctx.author.id,
        )
        await ctx.send(f"✅ Warnings cleared for {member.mention}.")

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
