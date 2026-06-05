from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.diagnostic._helpers import (
    build_bot_status_embed,
    build_check_database_embed,
    build_command_list_pages,
    build_latency_embed,
    build_query_logs_embed,
    build_system_info_embed,
    build_test_notification_embed,
    build_validate_json_embed,
)
from cogs.diagnostic._platform_embeds import (
    build_anchors_embed,
    build_bindings_embed,
    build_caches_embed,
    build_consistency_embed,
    build_customization_embed,
    build_flags_embed,
    build_identity_embed,
    build_lifecycle_embed,
    build_locks_embed,
    build_migrations_embed,
    build_participation_schemas_embed,
    build_provisioning_embed,
    build_resource_requirements_embed,
    build_resources_embed,
    build_runtime_embed,
    build_schemas_embed,
    build_sessions_embed,
    build_setting_detail_embed,
    build_settings_registry_embed,
    build_slow_embed,
    build_status_embed,
    build_tasks_embed,
    build_views_embed,
)
from views.base import send_panel
from views.diagnostic import (
    _DiagnosticsHubView,
    _PaginatorView,
    _PlatformHubView,
    build_platform_hub_embed,
)

logger = logging.getLogger("bot")


class DiagnosticCog(commands.Cog):
    """Advanced diagnostics and monitoring tools."""

    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # Diagnostics hub
    # ------------------------------------------------------------------

    @commands.cooldown(rate=2, per=15, type=commands.BucketType.user)
    @commands.command(name="diagnostics", aliases=["diag"])
    @commands.has_permissions(administrator=True)
    async def diagnostics_hub(self, ctx):
        """Open the interactive diagnostics hub panel."""
        view = _DiagnosticsHubView(ctx.author)
        await send_panel(ctx, embed=view.build_embed(), view=view)

    @commands.command(name="lifecycle", aliases=["lc"])
    @commands.has_permissions(administrator=True)
    async def lifecycle_shortcut(self, ctx):
        """Lifecycle state (phase, pending request, recent events).

        Shortcut for ``!platform lifecycle`` — operators don't need to
        remember the ``platform`` prefix during an incident.  Mirrors
        the existing ``!diag`` → ``!diagnostics`` shortcut pattern.
        """
        await ctx.send(embed=build_lifecycle_embed())

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the diagnostics hub).

        The view reads ``bot`` from ``interaction.client`` inside each
        button callback, so no ctx-shim is required.  This matches the
        canonical pattern used by every other subsystem hub.

        This hook stays pointed at the Diagnostics Hub so Admin →
        Diagnostics and ``!help diagnostics`` / ``!help diag`` continue
        to open the diagnostics surface. The Help "Platform /
        Diagnostics" entry uses :meth:`build_platform_help_menu_view`
        instead — see the ``_HUB_PANEL_BUILDERS`` override in
        ``help_cog``.
        """
        view = _DiagnosticsHubView(interaction.user)
        return view.build_embed(), view

    async def build_platform_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook for the Platform hub.

        Routed to by Help's ``_HUB_PANEL_BUILDERS`` override for the
        ``diagnostic`` hub key (display name "Platform / Diagnostics").
        ``DiagnosticCog`` owns both surfaces; this sibling hook keeps
        :meth:`build_help_menu_view` free for the Diagnostics callers
        that already depend on it.

        Reads only ``interaction.user`` — the ``HelpOpener`` adapter is
        a safe drop-in here.
        """
        view = _PlatformHubView(interaction.user)
        return build_platform_hub_embed(), view

    @app_commands.command(
        name="platform",
        description="Open the Platform / Diagnostics hub (administrator only).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def platform_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for the Platform hub — ephemeral, admin-only.

        PR E2 — privileged slash. Mirrors ``!platform`` (gated by
        ``administrator=True``). Reuses
        :meth:`build_platform_help_menu_view` so the slash entry
        opens the same Platform hub as Help → Platform/Diagnostics.
        """
        embed, view = await self.build_platform_help_menu_view(interaction)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # Command overview
    # ------------------------------------------------------------------

    @commands.command(name="list_commands_detailed", aliases=["listcmds"])
    @commands.has_permissions(administrator=True)
    async def list_commands_detailed(self, ctx):
        """List all registered commands with details, paginated by cog."""
        pages = build_command_list_pages(self.bot)
        if not pages:
            await ctx.send("No cogs with commands found.", delete_after=10)
            return
        view = _PaginatorView(pages, ctx.author)
        view.message = await ctx.send(embed=pages[0], view=view)

    @commands.command(name="find_command", aliases=["findcmd"])
    @commands.has_permissions(administrator=True)
    async def find_command_cmd(self, ctx, keyword: str):
        """Search for commands by keyword in their name or description."""
        embed = discord.Embed(
            title=f"Search Results for '{keyword}'",
            color=discord.Color.green(),
        )
        found = False
        for cog_name, cog_obj in self.bot.cogs.items():
            for cmd in cog_obj.get_commands():
                if keyword.lower() in cmd.name.lower() or (
                    cmd.help and keyword.lower() in cmd.help.lower()
                ):
                    found = True
                    cd_text = "No cooldown"
                    if cmd._buckets._cooldown:
                        cd = cmd._buckets._cooldown
                        cd_text = f"{cd.rate} use(s) per {cd.per}s"
                    embed.add_field(
                        name=f"!{cmd.name} ({cog_name})",
                        value=(
                            f"{cmd.help or 'No description'}\n"
                            f"Cooldown: {cd_text} | Aliases: {', '.join(cmd.aliases) or 'None'}"
                        ),
                        inline=False,
                    )
        if not found:
            embed.description = "No commands found matching the keyword."
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Data integrity
    # ------------------------------------------------------------------

    @commands.command(name="validate_json_files", aliases=["validatejson"])
    @commands.has_permissions(administrator=True)
    async def validate_json_files(self, ctx):
        """Validate the structure of all JSON files in the data directory."""
        embed = build_validate_json_embed()
        await ctx.send(embed=embed)

    @commands.command(name="check_database", aliases=["checkdb"])
    @commands.has_permissions(administrator=True)
    async def check_database(self, ctx):
        """Verify that all expected PostgreSQL tables exist."""
        embed = await build_check_database_embed()
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Health & performance
    # ------------------------------------------------------------------

    @commands.command(name="diagnostic_bot_status", aliases=["diag_status"])
    @commands.has_permissions(administrator=True)
    async def diagnostic_bot_status(self, ctx):
        """Display bot health and performance metrics."""
        embed = build_bot_status_embed(self.bot)
        await ctx.send(embed=embed)

    @commands.command(name="latency", aliases=["ping"])
    @commands.has_permissions(administrator=True)
    async def latency(self, ctx):
        """Report the bot's WebSocket latency."""
        embed = build_latency_embed(self.bot)
        await ctx.send(embed=embed)

    @commands.command(name="system_info", aliases=["sysinfo"])
    @commands.has_permissions(administrator=True)
    async def system_info(self, ctx):
        """Display system-level stats."""
        embed = build_system_info_embed()
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Log queries (PostgreSQL logs table)
    # ------------------------------------------------------------------

    @commands.command(name="query_logs", aliases=["querylogs"])
    @commands.has_permissions(administrator=True)
    async def query_logs(self, ctx, event_type: str = None, limit: int = 10):
        """Query recent logs from the logs table.  !query_logs [INFO|ERROR|...] [limit]"""
        embed = await build_query_logs_embed(event_type=event_type, limit=limit)
        await ctx.send(embed=embed)

    @commands.command(name="recent_errors", aliases=["errors"])
    @commands.has_permissions(administrator=True)
    async def recent_errors(self, ctx, limit: int = 10):
        """Retrieve the most recent ERROR-level log entries."""
        embed = await build_query_logs_embed(event_type="ERROR", limit=limit)
        await ctx.send(embed=embed)

    @commands.command(name="test_notification", aliases=["testnotify"])
    @commands.has_permissions(administrator=True)
    async def test_notification(self, ctx):
        """Send a test notification via the webhook reporter."""
        embed = await build_test_notification_embed(self.bot)
        await ctx.send(embed=embed)

    # ────────────────────────────────────────────────────────────────
    # !platform — runtime introspection (R1 from the hardening plan)
    # Surfaces anchor restoration state, identity-contract findings,
    # and basic runtime statistics so operators can investigate without
    # SSH access.
    # ────────────────────────────────────────────────────────────────

    @commands.group(name="platform", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def platform_grp(self, ctx):
        """Runtime introspection group.

        With no subcommand the interactive ``_PlatformHubView`` opens —
        every existing typed ``!platform <subcommand>`` is preserved and
        continues to work exactly as before.

        Existing surfaces (read-only):
            status · anchors · identity · runtime · caches ·
            locks [prefix] · tasks · views · sessions [subsystem] ·
            slow [limit] · schemas · settings-registry · customization ·
            provisioning · participation-schemas · resource-requirements ·
            resources · bindings · flags · migrations · consistency
        """
        view = _PlatformHubView(ctx.author)
        await send_panel(ctx, embed=build_platform_hub_embed(), view=view)

    @platform_grp.command(name="status")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_status(self, ctx):
        """High-level platform status: uptime, cogs, governance, scheduler."""
        await ctx.send(embed=build_status_embed(self.bot))

    @platform_grp.command(name="setup-readiness", aliases=["readiness", "ready"])  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_setup_readiness(self, ctx):
        """Per-guild setup-readiness inventory (PR H).

        Walks ``core.runtime.subsystem_schema.all_schemas`` and joins
        each subsystem's declared bindings + settings against this
        guild's stored values to compute how much of the configurable
        surface has been populated.

        Read-only — does not mutate anything. The output is the
        substrate for a future setup wizard; for now operators use it
        to spot subsystems that need attention.
        """
        from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

        embed = await build_setup_readiness_embed(ctx.guild.id, guild=ctx.guild)
        await ctx.send(embed=embed)

    @platform_grp.command(name="anchors")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_anchors(self, ctx):
        """Show last restoration outcome and active anchor counts per subsystem."""
        await ctx.send(embed=await build_anchors_embed())

    @platform_grp.command(name="identity")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_identity(self, ctx, mode: str = ""):
        """Run the identity-contract validator and show findings.

        Usage:
            !platform identity          run validator, show findings
            !platform identity --fix    also remediate auto_healable
                                        findings (fatal-tier are never
                                        auto-fixed; cog reload required).
        """
        await ctx.send(embed=await build_identity_embed(self.bot, mode))

    # ────────────────────────────────────────────────────────────────
    # !platform — Phase S2.5 / O-1: diagnostics_service-backed commands
    # ────────────────────────────────────────────────────────────────

    @platform_grp.command(name="runtime")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_runtime(self, ctx):
        """High-level runtime snapshot: every registered diagnostic provider."""
        await ctx.send(embed=build_runtime_embed())

    @platform_grp.command(name="lifecycle")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_lifecycle(self, ctx):
        """Lifecycle state: phase, pending request, recent events."""
        await ctx.send(embed=build_lifecycle_embed())

    @platform_grp.command(name="caches")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_caches(self, ctx):
        """Cache state: F-1 guild_config + governance.cache."""
        await ctx.send(embed=build_caches_embed())

    @platform_grp.command(name="locks")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_locks(self, ctx, prefix: str = ""):
        """scope_locks snapshot; pass a prefix to filter (e.g. `counting`)."""
        await ctx.send(embed=build_locks_embed(prefix))

    @platform_grp.command(name="tasks")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_tasks(self, ctx):
        """Managed background-task snapshot (core.runtime.tasks)."""
        await ctx.send(embed=build_tasks_embed())

    @platform_grp.command(name="views")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_views(self, ctx):
        """Registered PersistentView classes (by subsystem)."""
        await ctx.send(embed=build_views_embed())

    @platform_grp.command(name="slow")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_slow(self, ctx, limit: int = 10):
        """Show the most recent slow-path entries (S3.2 ring buffer)."""
        await ctx.send(embed=build_slow_embed(limit))

    @platform_grp.command(name="automation")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_automation(self, ctx):
        """Open the automation management + diagnostics panel.

        Renders the ``automation_scheduler`` snapshot alongside the
        per-guild rule list and lets administrators enable / disable /
        delete individual rules through the audited
        :class:`AutomationMutationPipeline`.
        """
        from views.diagnostic.automation_panel import open_panel

        embed, view = await open_panel(ctx)
        await send_panel(ctx, embed=embed, view=view)

    @platform_grp.command(name="sessions")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_sessions(self, ctx, subsystem: str = ""):
        """Active session counts (DB-backed); optionally filtered by subsystem."""
        embed, error = await build_sessions_embed(subsystem)
        if error is not None:
            await ctx.send(error, delete_after=15)
            return
        await ctx.send(embed=embed)

    # ────────────────────────────────────────────────────────────────
    # !platform — Phase 1: schema / participation / resource registries
    # ────────────────────────────────────────────────────────────────

    @platform_grp.command(name="schemas")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_schemas(self, ctx):
        """Registered SubsystemSchema instances (Phase 1a)."""
        await ctx.send(embed=build_schemas_embed())

    @platform_grp.command(name="settings-registry")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_settings_registry(self, ctx):
        """Declared SettingSpec catalogue + this guild's current values (S1)."""
        await ctx.send(embed=await build_settings_registry_embed(ctx.guild))

    @platform_grp.command(name="setting")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_setting(self, ctx, subsystem: str, name: str):
        """Explain one scalar setting for this guild.

        Shows the resolved value, its provenance (default vs legacy_kv),
        the declared default, validity, the raw stored string, and any
        resolver diagnostics — the "why is this value?" answer that
        feature flags already have via ``!platform flag``.
        """
        await ctx.send(
            embed=await build_setting_detail_embed(ctx.guild, subsystem, name),
        )

    @platform_grp.command(name="customization")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_customization(self, ctx):
        """Customization catalogue across subsystems (S2)."""
        await ctx.send(embed=build_customization_embed())

    @platform_grp.command(name="provisioning")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_provisioning(self, ctx):
        """Cross-linked ResourceRequirement × BindingSpec catalogue (S2.5)."""
        await ctx.send(embed=build_provisioning_embed())

    @platform_grp.command(name="participation-schemas")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_participation_schemas(self, ctx):
        """Registered ParticipationSchema instances (Phase 1b)."""
        await ctx.send(embed=build_participation_schemas_embed())

    @platform_grp.command(name="resource-requirements")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_resource_requirements(self, ctx):
        """Declared ResourceRequirement entries across subsystems (Phase 1c)."""
        await ctx.send(embed=build_resource_requirements_embed())

    @platform_grp.command(name="bindings")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_bindings(self, ctx):
        """Subsystem bindings (Phase 2b) — taxonomy + per-guild histograms."""
        await ctx.send(embed=await build_bindings_embed(ctx.guild))

    @platform_grp.command(name="resources")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_resources(self, ctx):
        """Resource runtime (Phase 2a) — taxonomy + cached status histogram."""
        await ctx.send(embed=await build_resources_embed(ctx.guild))

    @platform_grp.command(name="flags")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_flags(self, ctx):
        """Feature flags: declarations + Phase 2d evaluator state per flag."""
        await ctx.send(embed=await build_flags_embed(ctx.guild))

    @platform_grp.command(name="flag")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_flag_manager(self, ctx):
        """Open the editable per-guild flag manager (Phase 6.5a).

        Every mutation routes through
        :class:`services.rollout_mutation.RolloutMutationPipeline`
        (validates, writes audit, invalidates cache, emits event).
        """
        from views.base import send_panel
        from views.diagnostic.flag_manager import (
            FlagManagerView,
            build_flag_manager_overview_embed,
        )

        guild_id = ctx.guild.id if ctx.guild else None
        view = FlagManagerView(ctx.author, guild_id=guild_id)
        await send_panel(
            ctx,
            embed=build_flag_manager_overview_embed(),
            view=view,
        )

    @platform_grp.command(name="migrations")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_migrations(self, ctx):
        """Platform migration checkpoints (Phase 2 PR-5) — status + summary."""
        await ctx.send(embed=await build_migrations_embed(ctx.guild))

    @platform_grp.command(name="consistency")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_consistency(self, ctx):
        """Unified platform readiness diagnostic — read-only (Phase 2 PR-10)."""
        from services.platform_consistency import collect_report

        report = await collect_report(bot=self.bot, guild=ctx.guild)
        await ctx.send(embed=build_consistency_embed(report))

    @platform_grp.command(  # type: ignore[arg-type]
        name="command-access",
        aliases=["commandaccess"],
    )
    @commands.has_permissions(administrator=True)
    async def platform_command_access(
        self,
        ctx,
        channel: discord.TextChannel | None = None,
    ):
        """Show the live command-access decision for a channel.

        Defaults to the invoking channel.  Output covers every input
        the resolver consumed to make its decision so operators can
        see at a glance why ``!bj`` (or ``/blackjack``) succeeded or
        denied here — closes the "command vanished" debugging loop
        the command-access onboarding fix was written to eliminate.
        """
        from cogs.diagnostic._platform_embeds import (
            build_command_access_diagnostic_embed,
        )

        target = channel or ctx.channel
        embed = await build_command_access_diagnostic_embed(
            ctx=ctx,
            target_channel=target,
        )
        await ctx.send(embed=embed)

    @platform_grp.command(name="access", aliases=["whyhere"])  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_access(
        self,
        ctx,
        target: discord.TextChannel | discord.Thread | None = None,
    ):
        """Explain which subsystems you can use in a channel/thread (IL-1).

        Resolves the governance snapshot for the selected location (thread-aware,
        validates RC-2) and lists visible/denied subsystems + where each decision
        resolved from.  Read-only.
        """
        from cogs.diagnostic._platform_embeds import build_access_explainer_embed
        from governance.snapshot import build_governance_snapshot

        where = target or ctx.channel
        gctx = _governance_context_for(ctx, where)
        snapshot = await build_governance_snapshot(gctx)
        await ctx.send(embed=build_access_explainer_embed(where.mention, snapshot))

    @platform_grp.command(  # type: ignore[arg-type]
        name="cleanup-preview",
        aliases=["cleanuppreview", "cleanup-policy"],
    )
    @commands.has_permissions(administrator=True)
    async def platform_cleanup_preview(
        self,
        ctx,
        target: discord.TextChannel | discord.Thread | None = None,
    ):
        """Dry-run preview of the cleanup policy resolved for a location (IL-2).

        Reuses the read-only resolver; shows the resolved policy + which scope
        types a cleanup write accepts.  Makes no changes.
        """
        from cogs.diagnostic._platform_embeds import build_cleanup_preview_embed
        from governance.cleanup import resolve_cleanup_policy
        from governance.scopes import VALID_CLEANUP_SCOPE_TYPES

        where = target or ctx.channel
        gctx = _governance_context_for(ctx, where)
        policy = await resolve_cleanup_policy(gctx)
        await ctx.send(
            embed=build_cleanup_preview_embed(
                where.mention,
                policy,
                is_thread=isinstance(where, discord.Thread),
                valid_cleanup_scopes=VALID_CLEANUP_SCOPE_TYPES,
            ),
        )

    @platform_grp.command(  # type: ignore[arg-type]
        name="counting-health",
        aliases=["countinghealth"],
    )
    @commands.has_permissions(administrator=True)
    async def platform_counting_health(self, ctx):
        """Surface counting persistence health from task_outcome_total (IL-3).

        Reads the existing managed-task metric (RC-15) — not a new monitor.
        """
        from cogs.diagnostic._platform_embeds import (
            build_counting_health_embed,
            read_counting_save_outcomes,
        )

        guild_id = ctx.guild.id
        await ctx.send(
            embed=build_counting_health_embed(
                guild_id,
                read_counting_save_outcomes(guild_id),
                read_counting_save_outcomes(),
            ),
        )


def _governance_context_for(ctx, target):
    """Build a GovernanceContext for an arbitrary channel/thread (IL-1/IL-2).

    Mirrors ``GovernanceContext.from_ctx`` but for a user-selected ``target``
    instead of ``ctx.channel``, keeping the invoker's member/roles so the
    explainer answers "can *I* use this here?".
    """
    from governance.models import GovernanceContext

    if isinstance(target, discord.Thread):
        thread_id = target.id
        channel_id = target.parent_id
        category_id = getattr(target.parent, "category_id", None)
    else:
        thread_id = None
        channel_id = getattr(target, "id", None)
        category_id = getattr(target, "category_id", None)
    member = ctx.author
    return GovernanceContext(
        guild_id=ctx.guild.id,
        channel_id=channel_id,
        category_id=category_id,
        thread_id=thread_id,
        member=member if isinstance(member, discord.Member) else None,
        role_ids={r.id for r in getattr(member, "roles", [])},
    )


async def setup(bot):
    from cogs.diagnostic._log_buffer import install as install_log_buffer

    install_log_buffer()
    await bot.add_cog(DiagnosticCog(bot))
    logger.info("DiagnosticCog loaded.")
