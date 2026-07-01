from __future__ import annotations

from datetime import timedelta

import discord
from discord import Member, app_commands
from discord.ext import commands

from core.runtime import panel_manager
from core.runtime.permission_checks import app_perms_or_owner
from core.runtime.ui_permissions import can_execute_ctx
from services import moderation_service
from services.moderation_helpers import (
    _build_mod_panel_embed,
    _sweepable_channel,
    render_cleanup_outcome_line,
    render_warn_outcome_lines,
)
from services.moderation_service import ReasonRequiredError
from utils import db
from utils.ui_constants import MOD_COLOR

# Pattern B re-export: importing this triggers @register on ModPanelView
# so the persistent-view registry is populated before on_ready runs
# restore_anchors.  See docs/architecture.md §"PersistentView placement".
from views.moderation import ModPanelView  # noqa: F401 — re-exported


def _require_mod(capability: str, perm_attr: str):
    """Command check: allow if the invoker holds the Discord permission
    *perm_attr* **or** the governance *capability* (e.g. via a configured
    moderator role — ADR-008, capability-native authority).

    Behaviour-preserving: the Discord-permission path is evaluated first and is
    unchanged, so no one who can moderate today loses access — the capability
    path only *adds* the configured-role grant.  On denial it raises
    :class:`discord.ext.commands.MissingPermissions` so the existing
    ``on_command_error`` handler shows the standard "no permission" message
    (a bare ``CheckFailure`` would be silent).
    """

    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        perms = getattr(ctx.author, "guild_permissions", None)
        if perms is not None and getattr(perms, perm_attr, False):
            return True
        if await can_execute_ctx(ctx, capability):
            return True
        raise commands.MissingPermissions([perm_attr])

    return commands.check(predicate)


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
    @_require_mod("moderation.warn.apply", "moderate_members")
    async def mod_menu(self, ctx):
        """Show the interactive moderation action panel."""
        embed = _build_mod_panel_embed(ctx.guild)
        view = ModPanelView()
        await panel_manager.get_or_render_panel(ctx, "moderation", embed, view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the moderation panel)."""
        return _build_mod_panel_embed(interaction.guild), ModPanelView()

    @app_commands.command(
        name="moderation",
        description="Open the Moderation hub (moderator only).",
    )
    @app_commands.default_permissions(moderate_members=True)
    @app_perms_or_owner(moderate_members=True)
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

    @commands.command(
        name="warn",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @_require_mod("moderation.warn.apply", "manage_roles")
    async def warn(self, ctx, member: Member, *, reason=""):
        """Warn a user. Escalates at the configured threshold (default: timeout)."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        # The raw reason is passed through; the service enforces require_reason,
        # owns the escalation ladder (threshold → configured action, reset on
        # success), and returns a WarnOutcome the surface just renders.
        try:
            outcome = await moderation_service.warn(
                member,
                reason=reason,
                actor_id=ctx.author.id,
            )
        except ReasonRequiredError as exc:
            await ctx.send(f"❌ {exc}")
            return
        for line in render_warn_outcome_lines(member.mention, reason, outcome):
            await ctx.send(line)

    @commands.command(
        name="timeout",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @_require_mod("moderation.timeout.apply", "moderate_members")
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

    @commands.command(
        name="kick",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @_require_mod("moderation.kick.apply", "kick_members")
    async def kick(self, ctx, member: Member, *, reason=""):
        """Kick a member from the server."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        try:
            outcome = await moderation_service.kick(
                member,
                reason=reason,
                actor_id=ctx.author.id,
                channel=_sweepable_channel(ctx.channel),
            )
            await ctx.send(
                f"👢 {member.mention} kicked. Reason: {reason or 'No reason provided'}",
            )
            cleanup_line = render_cleanup_outcome_line(member.mention, outcome)
            if cleanup_line:
                await ctx.send(cleanup_line)
        except ReasonRequiredError as exc:
            await ctx.send(f"❌ {exc}")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick that user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to kick: {e}")

    @commands.command(
        name="ban",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @_require_mod("moderation.ban.apply", "ban_members")
    async def ban(self, ctx, member: Member, *, reason=""):
        """Ban a member from the server."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        try:
            outcome = await moderation_service.ban(
                ctx.guild,
                member,
                reason=reason,
                actor_id=ctx.author.id,
                channel=_sweepable_channel(ctx.channel),
            )
            await ctx.send(
                f"🚫 {member.mention} banned. Reason: {reason or 'No reason provided'}",
            )
            cleanup_line = render_cleanup_outcome_line(member.mention, outcome)
            if cleanup_line:
                await ctx.send(cleanup_line)
        except ReasonRequiredError as exc:
            await ctx.send(f"❌ {exc}")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban that user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to ban: {e}")

    @commands.command(
        name="unban",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @_require_mod("moderation.ban.remove", "ban_members")
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

    @commands.command(
        name="clearwarnings",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @_require_mod("moderation.warn.apply", "manage_roles")
    async def clearwarnings(self, ctx, member: Member):
        """Clear all warnings for a member."""
        await moderation_service.clear_warnings(
            ctx.guild.id,
            member.id,
            actor_id=ctx.author.id,
        )
        await ctx.send(f"✅ Warnings cleared for {member.mention}.")

    @commands.command(
        name="modlogs",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @_require_mod("moderation.log.view", "manage_roles")
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
