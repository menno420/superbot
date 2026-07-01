from __future__ import annotations

import logging

import discord
from discord.ext import commands, tasks

from core.runtime import panel_manager, resources
from core.runtime.component_registry import stats_block
from core.runtime.permission_checks import (
    admin_or_owner,
    member_has_perms_or_owner,
    perms_or_owner,
)
from core.runtime.persistent_views import PersistentView, register
from services import reaction_role_service, role_automation
from services.lifecycle import SUCCESS
from services.role_lifecycle_service import RoleLifecycleRequest, RoleLifecycleService
from utils import db
from utils.guild_config_accessors import invalidate_xp_threshold_roles
from utils.helpers import normalize_name
from utils.ui_constants import ROLE_COLOR
from views.roles._helpers import _find_role_normalized, _parse_color

logger = logging.getLogger("bot")


def _format_role_check_result(result: role_automation.ApplyResult) -> str:
    """Operator-facing summary of a time-role reconciliation run.

    Surfaces failures (with their classified cause) instead of the old
    success-only line that reported "0 assignment(s) made" while every member
    silently 403'd — the signal that hid the role-automation degradation.
    """
    if not result.failed:
        return f"✅ Role check complete — {result.succeeded} assignment(s) made."
    return (
        f"⚠️ Role check complete — {result.succeeded} made, "
        f"{result.failed} failed ({role_automation.summarize_failures(result)}).\n"
        "Open **!roles → 🔧 Diagnostics** to see what's blocking role automation."
    )


def _build_role_hub_embed() -> discord.Embed:
    return stats_block(
        "🎭 Role Hub",
        [
            ("📝 Create", "Create a new server role", True),
            ("🗂️ Manage", "View, edit, or delete roles", True),
            ("⏱️ Time Roles", "Days-in-server auto-assignment", True),
            ("⚡ XP Roles", "Level-based auto-assignment", True),
            ("💬 Reaction Roles", "Emoji reaction role bindings", True),
            ("🔧 Diagnostics", "System status & debug tools", True),
            ("🚫 Exemptions", "Exempt roles from XP/time automation", True),
        ],
        ROLE_COLOR,
    )


class _CtxAdapter:
    """Duck-type adapter exposing the ctx fields that role sub-panels need.

    Role sub-panels were written against commands.Context and access
    ctx.guild, ctx.author, and ctx.bot.  This adapter lets them work
    from an interaction without requiring a full sub-panel rewrite.
    """

    def __init__(self, interaction: discord.Interaction) -> None:
        self.guild = interaction.guild
        self.author = interaction.user
        self.bot = interaction.client


@register
class RoleHubPanelView(PersistentView):
    """Persistent role management hub — one panel per user per channel."""

    SUBSYSTEM = "role"
    # RC-3 / ADR-004: owner-scoped mutating panel (role management) — fail closed
    # when the anchor (ownership) cannot be verified, rather than allow any user.
    FAIL_CLOSED_ON_MISSING_ANCHOR = True

    def build_embed(self) -> discord.Embed:
        return _build_role_hub_embed()

    @discord.ui.button(
        label="📝 Create",
        style=discord.ButtonStyle.green,
        row=0,
        custom_id="role:create",
    )
    async def create_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not member_has_perms_or_owner(interaction.user, manage_roles=True):
            await interaction.response.send_message(
                "❌ You need **Manage Roles** permission.",
                ephemeral=True,
            )
            return
        from views.roles.creation_panel import RoleCreatePanel

        panel = RoleCreatePanel(_CtxAdapter(interaction))
        await interaction.response.send_message(
            embed=panel.build_embed(),
            view=panel,
            ephemeral=True,
        )

    @discord.ui.button(
        label="🗂️ Manage",
        style=discord.ButtonStyle.blurple,
        row=0,
        custom_id="role:manage",
    )
    async def manage_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not member_has_perms_or_owner(interaction.user, manage_roles=True):
            await interaction.response.send_message(
                "❌ You need **Manage Roles** permission.",
                ephemeral=True,
            )
            return
        from views.roles.management_panel import ManagementPanel

        self.message = interaction.message
        panel = ManagementPanel(_CtxAdapter(interaction), parent=self)
        panel.message = interaction.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )

    @discord.ui.button(
        label="⏱️ Time Roles",
        style=discord.ButtonStyle.blurple,
        row=0,
        custom_id="role:time",
    )
    async def time_roles_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not member_has_perms_or_owner(interaction.user, administrator=True):
            await interaction.response.send_message(
                "❌ You need **Administrator** permission.",
                ephemeral=True,
            )
            return
        from views.roles.time_roles_panel import TimeRolesPanel

        self.message = interaction.message
        panel = TimeRolesPanel(_CtxAdapter(interaction), parent=self)
        panel.message = interaction.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )

    @discord.ui.button(
        label="⚡ XP Roles",
        style=discord.ButtonStyle.blurple,
        row=1,
        custom_id="role:xp",
    )
    async def xp_roles_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not member_has_perms_or_owner(interaction.user, administrator=True):
            await interaction.response.send_message(
                "❌ You need **Administrator** permission.",
                ephemeral=True,
            )
            return
        from views.roles.xp_roles_panel import XpRolesPanel

        self.message = interaction.message
        panel = XpRolesPanel(_CtxAdapter(interaction), parent=self)
        panel.message = interaction.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )

    @discord.ui.button(
        label="💬 Reaction Roles",
        style=discord.ButtonStyle.blurple,
        row=1,
        custom_id="role:reaction",
    )
    async def reaction_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.roles.reaction_panel import ReactionRolesPanel

        self.message = interaction.message
        panel = ReactionRolesPanel(_CtxAdapter(interaction), parent=self)
        panel.message = interaction.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )

    @discord.ui.button(
        label="🔧 Diagnostics",
        style=discord.ButtonStyle.grey,
        row=1,
        custom_id="role:diagnostics",
    )
    async def diagnostics_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not member_has_perms_or_owner(interaction.user, administrator=True):
            await interaction.response.send_message(
                "❌ You need **Administrator** permission.",
                ephemeral=True,
            )
            return
        from views.roles.diagnostics_panel import DiagnosticsPanel

        self.message = interaction.message
        panel = DiagnosticsPanel(_CtxAdapter(interaction), parent=self)
        panel.message = interaction.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )

    @discord.ui.button(
        label="🚫 Exemptions",
        style=discord.ButtonStyle.grey,
        row=2,
        custom_id="role:exemptions",
    )
    async def exemptions_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not member_has_perms_or_owner(interaction.user, administrator=True):
            await interaction.response.send_message(
                "❌ You need **Administrator** permission.",
                ephemeral=True,
            )
            return
        from views.roles.exemptions_panel import RoleExemptionsPanel

        self.message = interaction.message
        panel = RoleExemptionsPanel(_CtxAdapter(interaction), parent=self)
        panel.message = interaction.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )


class RoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.role_check.start()

    async def cog_load(self) -> None:
        from cogs.role.schemas import register_schemas

        register_schemas()  # role-automation stacking toggles (Settings hub).

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
        self,
        guild: discord.Guild,
        ctx: commands.Context = None,
    ) -> int:
        """Assign time-based roles to all members.

        Returns the count of successful assignments. Delegates the
        decision + mutation to
        :mod:`services.role_automation` so that audit events
        (``audit.action_recorded``) are emitted for every change and
        the guild-wide batch shares logic with
        :meth:`on_member_join`.
        """
        thresholds = await db.get_role_thresholds(guild.id)
        if not thresholds:
            if ctx:
                await ctx.send("✅ Role check complete — 0 assignment(s) made.")
            return 0

        from services import role_exemption_service

        exempt = await role_exemption_service.get_exempt_role_ids(guild.id)
        keep_previous = await role_exemption_service.time_roles_stack(guild.id)

        threshold_objs = tuple(
            role_automation.RoleThreshold(
                role_name=row["role_name"],
                days_required=row["days_required"],
                role_id=row.get("role_id"),
            )
            for row in thresholds
            # XP reward roles (xp_auto_assign) are granted by the XP listener
            # at a level threshold — they are NOT time-based. Excluding them
            # stops the time-based reconciliation from stripping a level-earned
            # role from members who haven't met a days_required threshold (the
            # "lost testrole on restart" regression).
            if not row.get("xp_auto_assign") and row.get("days_required") is not None
        )

        assignments = role_automation.compute_assignments(
            guild,
            threshold_objs,
            exempt_role_ids=exempt.time,
            keep_previous_tier=keep_previous,
        )
        result = await role_automation.apply(
            guild,
            assignments,
            actor_id=None,
            actor_type="system",
        )

        if ctx:
            await ctx.send(_format_role_check_result(result))
        return result.succeeded

    # ------------------------------------------------------------------ primary commands

    @commands.command(name="roles")
    async def roles_hub(self, ctx: commands.Context) -> None:
        """Open the role management hub."""
        view = RoleHubPanelView()
        embed = _build_role_hub_embed()
        msg = await panel_manager.get_or_render_panel(ctx, "role", embed, view)
        view.message = msg

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the role management hub)."""
        return _build_role_hub_embed(), RoleHubPanelView()

    @commands.command(name="rolesettings")
    @admin_or_owner()
    async def rolesettings(self, ctx: commands.Context) -> None:
        """Open the role management hub (alias for !roles)."""
        await ctx.invoke(self.roles_hub)

    @commands.command(
        name="roleinfo",
        aliases=["ri"],
        help="Show a role's details. Usage: !roleinfo <@role|name|id>",
    )
    @commands.guild_only()
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role) -> None:
        """Read-only role detail card — the role sibling of !channelinfo / !info user.

        Member-tier and read-only (no mutation, so no audited seam): anyone can
        look up a role's colour, member count, position, flags, and notable
        permissions. Closes the assessment punch-list's "utility roleinfo" gap.
        The rendering lives in ``views.roles.role_info`` (the cog stays a thin
        resolve → render → send wrapper).
        """
        from views.roles.role_info import build_role_info_embed

        embed = build_role_info_embed(role, requested_by=ctx.author)
        await ctx.send(embed=embed)

    @roleinfo.error
    async def roleinfo_error(self, ctx: commands.Context, error: Exception) -> None:
        """Friendly message when the role argument is missing or unresolved."""
        if isinstance(
            error,
            (
                commands.RoleNotFound,
                commands.MissingRequiredArgument,
                commands.BadArgument,
            ),
        ):
            await ctx.send(
                "Usage: `!roleinfo <@role|name|id>` — I couldn't find that role.",
            )
            return
        raise error

    # ------------------------------------------------------------------ compatibility aliases (hidden)

    @commands.command(
        name="rolemenu",
        hidden=True,
        extras={"classification": "legacy_duplicate"},
    )
    async def rolemenu(self, ctx: commands.Context) -> None:
        """Open the role hub (use !roles instead)."""
        await ctx.invoke(self.roles_hub)

    @commands.command(
        name="rolecreator",
        hidden=True,
        extras={"classification": "legacy_duplicate"},
    )
    @perms_or_owner(manage_roles=True)
    async def rolecreator(self, ctx: commands.Context) -> None:
        """Open the role hub (use !roles instead)."""
        await ctx.invoke(self.roles_hub)

    @commands.command(
        name="assignroles",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @admin_or_owner()
    async def assign_roles_cmd(self, ctx: commands.Context) -> None:
        """Manually run time-based role assignment for all members."""
        await ctx.send("🔄 Running role assignment…")
        await self._assign_roles(ctx.guild, ctx)

    @commands.command(
        name="createrole",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @perms_or_owner(manage_roles=True)
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
                "❌ Invalid color — use a hex code like `#3498db`.",
                delete_after=10,
            )
            return
        do_hoist = hoist.lower() in ("yes", "true", "1", "y")
        result = await RoleLifecycleService().apply(
            ctx.guild,
            RoleLifecycleRequest(
                operation="create",
                name=name,
                color=col,
                hoist=do_hoist,
            ),
            ctx.author,
            actor_type="admin",
        )
        if result.outcome == SUCCESS:
            await ctx.send(f"✅ Created role **{result.steps[0].target_name}**.")
        else:
            await ctx.send(f"❌ Could not create role: {result.first_error}")

    @commands.command(
        name="deleterole",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @perms_or_owner(manage_roles=True)
    async def deleterole(self, ctx: commands.Context, *, role: discord.Role) -> None:
        """Delete a role by name or mention."""
        name = role.name
        result = await RoleLifecycleService().apply(
            ctx.guild,
            RoleLifecycleRequest(operation="delete", role_id=role.id),
            ctx.author,
            confirmed=True,
            actor_type="admin",
        )
        if result.outcome == SUCCESS:
            await ctx.send(f"🗑️ Deleted role **{name}**.")
        else:
            await ctx.send(f"❌ Could not delete **{name}**: {result.first_error}")

    @commands.command(
        name="setrole",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @admin_or_owner()
    async def setrole(
        self,
        ctx: commands.Context,
        days: int,
        *,
        role_name: str,
    ) -> None:
        """Add or update a time-based role threshold."""
        if days < 0:
            await ctx.send("Days must be 0 or greater.", delete_after=5)
            return
        discord_role = _find_role_normalized(ctx.guild, role_name)
        store_name = discord_role.name if discord_role else role_name
        # Audited seam (P0C): route through role_automation so the change is
        # audited. role_id is captured when the named role resolves (rename-safe);
        # the legacy free-text path keeps a name-only write (role_id=None).
        await role_automation.set_time_threshold(
            guild_id=ctx.guild.id,
            role_id=discord_role.id if discord_role else None,
            role_name=store_name,
            days=days,
            actor_id=ctx.author.id,
        )
        await ctx.send(
            f"✅ Role **{store_name}** will be assigned after **{days}** day(s).",
        )

    @commands.command(
        name="unsetrole",
        hidden=True,
        extras={"classification": "panel_action"},
    )
    @admin_or_owner()
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
        # Audited seam: the field-specific clear (preserves any XP config on the
        # row; drops it only when no automation remains) + audit emit live in
        # role_automation. The cache invalidate also runs there; this local call
        # keeps the cog's invalidator wiring pinned by test_xp_cog_caching.
        await role_automation.clear_time_threshold(
            guild_id=ctx.guild.id,
            role_name=match,
            actor_id=ctx.author.id,
        )
        invalidate_xp_threshold_roles(ctx.guild.id)
        await ctx.send(f"✅ Removed **{match}** from time-based assignment.")

    @commands.command(
        name="debugroles",
        hidden=True,
        extras={"classification": "internal_admin"},
    )
    @admin_or_owner()
    async def debug_roles(self, ctx: commands.Context) -> None:
        """Print all role names for verification."""
        names = [r.name for r in ctx.guild.roles]
        await ctx.send(f"Roles: {', '.join(names)}")

    @commands.command(
        name="refreshmembers",
        hidden=True,
        extras={"classification": "internal_admin"},
    )
    @admin_or_owner()
    async def refresh_members(self, ctx: commands.Context) -> None:
        """Force-fetch all members from Discord."""
        await ctx.guild.chunk()
        await ctx.send("✅ Member list refreshed.")

    # ------------------------------------------------------------------ reaction role system

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        if payload.user_id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = resources.resolve_member(guild, payload.user_id)
        if not member or member.bot:
            return
        # The audited service owns mode enforcement (normal/unique/verify) and
        # the per-guild reaction_roles_enabled gate; the cog only strips the
        # reaction afterward for verify mode (so the message stays clean).
        _outcome, strip_reaction = await reaction_role_service.handle_reaction_add(
            guild,
            member,
            payload.message_id,
            str(payload.emoji),
        )
        if strip_reaction:
            await self._strip_reaction(payload, member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = resources.resolve_member(guild, payload.user_id)
        if not member or member.bot:
            return
        await reaction_role_service.handle_reaction_remove(
            guild,
            member,
            payload.message_id,
            str(payload.emoji),
        )

    async def _strip_reaction(
        self,
        payload: discord.RawReactionActionEvent,
        member: discord.Member,
    ) -> None:
        """Remove a member's reaction (verify mode keeps the message clean)."""
        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            return
        try:
            await channel.get_partial_message(payload.message_id).remove_reaction(
                payload.emoji,
                member,
            )
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

    @commands.command(name="reactroles", aliases=["reaktionsrollen"])
    @perms_or_owner(manage_roles=True)
    async def setup_reaction_roles(
        self,
        ctx: commands.Context,
        message_id: int,
        emoji: str,
        role: discord.Role,
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

        await reaction_role_service.bind_emoji(
            ctx.guild.id,
            message_id,
            emoji,
            role.id,
            actor_id=ctx.author.id,
        )
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await ctx.send(
                "⚠️ Role saved, but I couldn't add the reaction (invalid emoji?).",
            )
            return
        await ctx.send(
            f"✅ Reaction role set: reacting with {emoji} assigns **{role.name}**.",
            delete_after=15,
        )

    @commands.command(name="removereactrole")
    @perms_or_owner(manage_roles=True)
    async def remove_reaction_role(
        self,
        ctx: commands.Context,
        message_id: int,
        emoji: str,
    ) -> None:
        """Remove a reaction role binding. Usage: !removereactrole <message_id> <emoji>"""
        await reaction_role_service.unbind_emoji(
            ctx.guild.id,
            message_id,
            emoji,
            actor_id=ctx.author.id,
        )
        await ctx.send(
            f"✅ Reaction role for {emoji} on that message removed.",
            delete_after=10,
        )

    @commands.command(name="listreactroles")
    @perms_or_owner(manage_roles=True)
    async def list_reaction_roles(self, ctx: commands.Context) -> None:
        """List all active reaction roles in this server."""
        rows = await reaction_role_service.list_bindings(ctx.guild.id)
        if not rows:
            await ctx.send("No reaction roles configured.", delete_after=8)
            return
        lines = []
        for r in rows:
            role = resources.resolve_role(ctx.guild, role_id=r["role_id"])
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
        thresholds = await db.get_role_thresholds(member.guild.id)
        if not thresholds:
            return

        threshold_objs = tuple(
            role_automation.RoleThreshold(
                role_name=row["role_name"],
                days_required=row["days_required"],
                role_id=row.get("role_id"),
            )
            for row in thresholds
            # XP reward roles (xp_auto_assign) are granted by the XP listener
            # at a level threshold — they are NOT time-based. Excluding them
            # stops the time-based reconciliation from stripping a level-earned
            # role from members who haven't met a days_required threshold (the
            # "lost testrole on restart" regression).
            if not row.get("xp_auto_assign") and row.get("days_required") is not None
        )
        from services import role_exemption_service

        exempt = await role_exemption_service.get_exempt_role_ids(member.guild.id)
        keep_previous = await role_exemption_service.time_roles_stack(member.guild.id)
        plan = role_automation.explain_assignment_for(
            member.guild,
            member,
            threshold_objs,
            exempt_role_ids=exempt.time,
            keep_previous_tier=keep_previous,
        )
        if plan is None:
            return
        result = await role_automation.apply(
            member.guild,
            (plan,),
            actor_id=None,
            actor_type="system",
        )
        if result.failed:
            # Don't swallow a join-time failure: log it (WARNING — a single
            # member, not a flood) with the classified cause so an operator
            # isn't left guessing why a new member never got their role.
            logger.warning(
                "on_member_join: role assignment failed for member=%s in "
                "guild=%s — %s",
                member.id,
                member.guild.id,
                role_automation.summarize_failures(result),
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RoleCog(bot))
    logger.info("RoleCog loaded.")
