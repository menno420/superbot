from __future__ import annotations

import datetime
import logging

import discord
from discord.ext import commands

from cogs.diagnostic._helpers import (
    _fmt_snapshot_value,
    build_bot_status_embed,
    build_check_database_embed,
    build_command_list_pages,
    build_latency_embed,
    build_query_logs_embed,
    build_system_info_embed,
    build_test_notification_embed,
    build_validate_json_embed,
)
from utils import db
from views.base import send_panel
from views.diagnostic import _DiagnosticsHubView, _PaginatorView

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

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the diagnostics hub).

        The view reads ``bot`` from ``interaction.client`` inside each
        button callback, so no ctx-shim is required.  This matches the
        canonical pattern used by every other subsystem hub.
        """
        view = _DiagnosticsHubView(interaction.user)
        return view.build_embed(), view

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

        Existing (R1):
            !platform status      · !platform anchors · !platform identity

        Added in Phase S2.5 / O-1, backed by ``services.diagnostics_service``:
            !platform runtime     · !platform caches  · !platform locks [prefix]
            !platform tasks       · !platform views   · !platform sessions [subsystem]

        Added in Phase 1 (subsystem ownership protocols):
            !platform schemas              · !platform participation-schemas
            !platform resource-requirements · !platform flags
        """
        await ctx.send(
            "Usage: `!platform <status|anchors|identity|"
            "runtime|caches|locks|tasks|views|sessions|slow|"
            "schemas|participation-schemas|resource-requirements|flags>`",
            delete_after=20,
        )

    @platform_grp.command(name="status")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_status(self, ctx):
        """High-level platform status: uptime, cogs, governance, scheduler."""
        from core.runtime import tasks as runtime_tasks

        uptime_obj = getattr(self.bot, "uptime", None)
        uptime_s = (
            str(datetime.datetime.now(tz=datetime.timezone.utc) - uptime_obj)
            if uptime_obj
            else "n/a"
        )
        embed = discord.Embed(
            title="🛠 Platform status",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Uptime", value=uptime_s, inline=True)
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Cogs loaded", value=str(len(self.bot.cogs)), inline=True)
        embed.add_field(
            name="Managed tasks",
            value=str(runtime_tasks.count()),
            inline=True,
        )
        try:
            from services.governance_service import _FAILED_SUBSYSTEMS

            failed = ", ".join(sorted(_FAILED_SUBSYSTEMS)) or "none"
        except Exception:
            failed = "?"
        embed.add_field(name="Failed subsystems", value=failed, inline=False)
        await ctx.send(embed=embed)

    @platform_grp.command(name="anchors")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_anchors(self, ctx):
        """Show last restoration outcome and active anchor counts per subsystem."""
        from core.runtime import message_anchor_manager

        stats = message_anchor_manager.last_restore_stats()
        embed = discord.Embed(
            title="📌 Panel anchors",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Last restoration",
            value=(
                f"seen: **{stats['anchors_seen']}**  ·  "
                f"restored: **{stats['restored']}**  ·  "
                f"view_missing: **{stats['view_missing']}**  ·  "
                f"stale: **{stats['stale']}**"
            ),
            inline=False,
        )
        try:
            rows = await db.fetchall(
                "SELECT subsystem, COUNT(*) AS n FROM panel_anchors "
                "WHERE NOT is_stale GROUP BY subsystem ORDER BY n DESC",
                (),
            )
            if rows:
                lines = [f"`{r['subsystem']}` — {r['n']}" for r in rows]
                embed.add_field(
                    name="Active anchors by subsystem",
                    value="\n".join(lines)[:1024],
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Active anchors by subsystem",
                    value="none",
                    inline=False,
                )
        except Exception as exc:
            embed.add_field(
                name="Active anchors by subsystem",
                value=f"DB query failed: {exc}",
                inline=False,
            )
        await ctx.send(embed=embed)

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
        from utils.subsystem_registry import (
            apply_self_heal,
            summarize_findings,
            validate_identity_contract,
        )

        findings = await validate_identity_contract(self.bot)
        summary = summarize_findings(findings)
        total = summary["total"]
        fatal = summary["by_tier"]["fatal"]
        auto = summary["by_tier"]["auto_healable"]

        heal_requested = mode.strip() in ("--fix", "-f", "fix")
        heal_counts: dict[str, int] | None = None
        if heal_requested:
            heal_counts = await apply_self_heal(findings)

        if total == 0:
            color = discord.Color.green()
            desc = "All four identity surfaces agree."
        elif fatal:
            color = discord.Color.red()
            desc = (
                f"{total} finding(s) — **{fatal} fatal**, "
                f"{auto} auto-healable.  Fatal findings require operator "
                "review (likely a cog failed to load)."
            )
        else:
            color = discord.Color.orange()
            desc = f"{total} finding(s) — {auto} auto-healable."

        embed = discord.Embed(
            title="🪪 Identity contract",
            description=desc,
            color=color,
        )
        for bucket, items in findings.items():
            if not items:
                continue
            embed.add_field(
                name=f"{bucket} ({len(items)})",
                value="\n".join(items)[:1024],
                inline=False,
            )
        if heal_counts is not None:
            embed.add_field(
                name="Self-heal result",
                value=(
                    f"router prefixes unregistered: "
                    f"`{heal_counts['router_prefixes_unregistered']}` · "
                    f"views unregistered: `{heal_counts['views_unregistered']}` · "
                    f"anchors marked stale: "
                    f"`{heal_counts['anchors_marked_stale']}` · "
                    f"fatal-tier skipped: `{heal_counts['skipped_fatal']}`"
                ),
                inline=False,
            )
        await ctx.send(embed=embed)

    # ────────────────────────────────────────────────────────────────
    # !platform — Phase S2.5 / O-1: diagnostics_service-backed commands
    # ────────────────────────────────────────────────────────────────

    @platform_grp.command(name="runtime")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_runtime(self, ctx):
        """High-level runtime snapshot: every registered diagnostic provider."""
        from services import diagnostics_service

        snap = diagnostics_service.snapshot_all()
        embed = discord.Embed(
            title="🛰 Runtime snapshot",
            description=f"{len(snap)} provider(s) registered.",
            color=discord.Color.blurple(),
        )
        for name in sorted(snap):
            embed.add_field(
                name=name,
                value=_fmt_snapshot_value(snap[name]),
                inline=False,
            )
        await ctx.send(embed=embed)

    @platform_grp.command(name="caches")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_caches(self, ctx):
        """Cache state: F-1 guild_config + governance.cache."""
        from services import diagnostics_service

        embed = discord.Embed(
            title="🧠 Cache snapshot",
            color=discord.Color.blurple(),
        )
        for name in ("guild_config", "governance_cache"):
            try:
                snap = diagnostics_service.snapshot(name)
            except KeyError:
                snap = {"_error": "provider not registered"}
            embed.add_field(
                name=name,
                value=_fmt_snapshot_value(snap),
                inline=False,
            )
        await ctx.send(embed=embed)

    @platform_grp.command(name="locks")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_locks(self, ctx, prefix: str = ""):
        """scope_locks snapshot; pass a prefix to filter (e.g. `counting`)."""
        from services import diagnostics_service

        snap = diagnostics_service.snapshot("scope_locks")
        by_prefix = dict(snap.get("by_prefix", {}))
        if prefix:
            by_prefix = {k: v for k, v in by_prefix.items() if k == prefix}
        embed = discord.Embed(
            title="🔒 Scope locks",
            description=(
                f"total: **{snap.get('total', 0)}**  ·  "
                f"held: **{snap.get('held', 0)}**"
                + (f"  ·  filter: `{prefix}`" if prefix else "")
            ),
            color=discord.Color.blurple(),
        )
        if by_prefix:
            lines = [f"`{k}` — {v}" for k, v in sorted(by_prefix.items())]
            embed.add_field(
                name="By prefix",
                value="\n".join(lines)[:1024],
                inline=False,
            )
        else:
            embed.add_field(
                name="By prefix",
                value="*(no locks matching filter)*" if prefix else "*(none)*",
                inline=False,
            )
        await ctx.send(embed=embed)

    @platform_grp.command(name="tasks")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_tasks(self, ctx):
        """Managed background-task snapshot (core.runtime.tasks)."""
        from services import diagnostics_service

        snap = diagnostics_service.snapshot("tasks")
        names = list(snap.get("names", []))
        embed = discord.Embed(
            title="🔁 Managed tasks",
            description=f"{snap.get('active_count', 0)} active",
            color=discord.Color.blurple(),
        )
        if names:
            embed.add_field(
                name="Names",
                value="\n".join(f"`{n}`" for n in names)[:1024],
                inline=False,
            )
        await ctx.send(embed=embed)

    @platform_grp.command(name="views")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_views(self, ctx):
        """Registered PersistentView classes (by subsystem)."""
        from services import diagnostics_service

        snap = diagnostics_service.snapshot("persistent_views")
        subsystems = list(snap.get("subsystems", []))
        embed = discord.Embed(
            title="🖼 Persistent views",
            description=f"{snap.get('registered_count', 0)} registered",
            color=discord.Color.blurple(),
        )
        if subsystems:
            embed.add_field(
                name="Subsystems",
                value=", ".join(f"`{s}`" for s in subsystems)[:1024],
                inline=False,
            )
        await ctx.send(embed=embed)

    @platform_grp.command(name="slow")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_slow(self, ctx, limit: int = 10):
        """Show the most recent slow-path entries (S3.2 ring buffer)."""
        from core.runtime import slow_path_log

        entries = slow_path_log.snapshot()
        limit = max(1, min(limit, 25))  # Discord field-count guard
        recent = entries[-limit:]
        embed = discord.Embed(
            title="🐢 Slow path log",
            description=(
                f"**{len(entries)}** entries  ·  threshold: "
                f"`{slow_path_log.threshold_ms():.0f}ms`  ·  "
                f"capacity: `{slow_path_log.capacity()}`"
            ),
            color=discord.Color.blurple(),
        )
        if not recent:
            embed.add_field(
                name="No slow paths recorded",
                value=f"All observations under {slow_path_log.threshold_ms():.0f}ms.",
                inline=False,
            )
        else:
            embed.set_footer(text=f"Showing the {len(recent)} most recent.")
            for entry in reversed(recent):  # most recent first
                age_s = max(0.0, datetime.datetime.now().timestamp() - entry.timestamp)
                embed.add_field(
                    name=f"{entry.kind}: {entry.name}",
                    value=f"**{entry.duration_ms:.0f}ms**  ·  {age_s:.0f}s ago",
                    inline=False,
                )
        await ctx.send(embed=embed)

    @platform_grp.command(name="sessions")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_sessions(self, ctx, subsystem: str = ""):
        """Active session counts (DB-backed); optionally filtered by subsystem."""
        try:
            if subsystem:
                rows = await db.fetchall(
                    "SELECT subsystem, COUNT(*) AS n FROM runtime_sessions "
                    "WHERE subsystem=$1 GROUP BY subsystem",
                    (subsystem,),
                )
            else:
                rows = await db.fetchall(
                    "SELECT subsystem, COUNT(*) AS n FROM runtime_sessions "
                    "GROUP BY subsystem ORDER BY n DESC",
                    (),
                )
        except Exception as exc:
            await ctx.send(f"❌ DB query failed: {exc}", delete_after=15)
            return
        embed = discord.Embed(
            title="🎫 Active sessions",
            description=(f"filter: `{subsystem}`" if subsystem else "all subsystems"),
            color=discord.Color.blurple(),
        )
        if rows:
            lines = [f"`{r['subsystem']}` — {r['n']}" for r in rows]
            embed.add_field(
                name="By subsystem",
                value="\n".join(lines)[:1024],
                inline=False,
            )
        else:
            embed.add_field(name="By subsystem", value="*(none)*", inline=False)
        await ctx.send(embed=embed)

    # ────────────────────────────────────────────────────────────────
    # !platform — Phase 1: schema / participation / resource registries
    # ────────────────────────────────────────────────────────────────

    @platform_grp.command(name="schemas")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_schemas(self, ctx):
        """Registered SubsystemSchema instances (Phase 1a)."""
        from services import diagnostics_service

        snap = diagnostics_service.snapshot("schemas")
        embed = discord.Embed(
            title="📐 Subsystem schemas",
            description=(
                f"{snap['registered']} registered  ·  "
                f"bindings={snap['bindings_total']}  ·  "
                f"settings={snap['settings_total']}  ·  "
                f"resources={snap['resources_total']}"
            ),
            color=discord.Color.blurple(),
        )
        by_sub = snap.get("by_subsystem", {})
        if by_sub:
            lines = [
                f"`{name}` — b={info['bindings']} s={info['settings']} "
                f"r={info['resources']} v={info['version']}"
                for name, info in sorted(by_sub.items())
            ]
            embed.add_field(
                name="By subsystem",
                value="\n".join(lines)[:1024],
                inline=False,
            )
        else:
            embed.add_field(name="By subsystem", value="*(none)*", inline=False)
        await ctx.send(embed=embed)

    @platform_grp.command(name="participation-schemas")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_participation_schemas(self, ctx):
        """Registered ParticipationSchema instances (Phase 1b)."""
        from services import diagnostics_service

        snap = diagnostics_service.snapshot("participation_schemas")
        embed = discord.Embed(
            title="🧑‍🤝‍🧑 Participation schemas",
            description=(
                f"{snap['registered']} registered  ·  "
                f"subs={snap['subscriptions_total']}  ·  "
                f"vis={snap['visibility_intents_total']}  ·  "
                f"notif={snap['notification_intents_total']}  ·  "
                f"prefs={snap['preferences_total']}"
            ),
            color=discord.Color.blurple(),
        )
        by_sub = snap.get("by_subsystem", {})
        if by_sub:
            lines = [
                f"`{name}` — s={info['subscriptions']} "
                f"v={info['visibility_intents']} "
                f"n={info['notification_intents']} "
                f"p={info['preferences']} v{info['version']}"
                for name, info in sorted(by_sub.items())
            ]
            embed.add_field(
                name="By subsystem",
                value="\n".join(lines)[:1024],
                inline=False,
            )
        else:
            embed.add_field(name="By subsystem", value="*(none)*", inline=False)
        await ctx.send(embed=embed)

    @platform_grp.command(name="resource-requirements")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_resource_requirements(self, ctx):
        """Declared ResourceRequirement entries across subsystems (Phase 1c)."""
        from services import diagnostics_service

        snap = diagnostics_service.snapshot("resource_requirements")
        embed = discord.Embed(
            title="🧱 Resource requirements",
            description=f"{len(snap)} requirement(s) declared",
            color=discord.Color.blurple(),
        )
        if snap:
            lines = [
                f"`{r['subsystem']}` {r['kind']}/{r['intent']} "
                f"({r['priority']})"
                + (f" → `{r['suggested_name']}`" if r["suggested_name"] else "")
                for r in snap
            ]
            embed.add_field(
                name="Requirements",
                value="\n".join(lines)[:1024],
                inline=False,
            )
        else:
            embed.add_field(name="Requirements", value="*(none)*", inline=False)
        await ctx.send(embed=embed)

    @platform_grp.command(name="flags")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def platform_flags(self, ctx):
        """Declared FeatureFlag entries (Phase 1d declarations only)."""
        from services import diagnostics_service

        snap = diagnostics_service.snapshot("feature_flags")
        embed = discord.Embed(
            title="🚩 Feature flags (declared)",
            description=(
                f"{snap['declared_total']} declared  ·  "
                "Phase 2d will add runtime evaluation"
            ),
            color=discord.Color.blurple(),
        )
        by_name = snap.get("by_name", {})
        if by_name:
            lines = [
                f"`{name}` default={info['default_value']} owner=`{info['owner']}`"
                for name, info in sorted(by_name.items())
            ]
            embed.add_field(
                name="Declared",
                value="\n".join(lines)[:1024],
                inline=False,
            )
        else:
            embed.add_field(name="Declared", value="*(none)*", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DiagnosticCog(bot))
    logger.info("DiagnosticCog loaded.")
