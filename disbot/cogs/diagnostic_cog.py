from __future__ import annotations

import datetime
import logging
import os
import platform
import shutil

import discord
import psutil
from discord.ext import commands

from core.runtime.interaction_helpers import help_ctx_shim, safe_defer
from utils import db
from views.base import BaseView, HubView, send_panel

logger = logging.getLogger("bot")

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
)
JSON_DIR = os.path.join(DATA_DIR, "json")


class _PaginatorView(BaseView):
    """Simple prev/next paginator for multi-page embeds."""

    def __init__(
        self,
        pages: list[discord.Embed],
        author: discord.Member | discord.User,
    ):
        super().__init__(author, timeout=120)
        self.pages = pages
        self.index = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.index == 0
        self.next_btn.disabled = self.index == len(self.pages) - 1

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.index -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.index += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)


class _DiagnosticsHubView(HubView):
    """Interactive hub for all diagnostic tools."""

    def __init__(self, ctx: commands.Context, cog: DiagnosticCog):
        super().__init__(ctx.author)
        self.ctx = ctx
        self.cog = cog

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔧 Diagnostics Hub",
            description=(
                "Select a diagnostic tool below.\n"
                "All tools require Administrator permission."
            ),
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="🤖 Bot Status",
            value="Health & performance metrics",
            inline=True,
        )
        embed.add_field(name="📡 Latency", value="WebSocket ping", inline=True)
        embed.add_field(
            name="💻 System Info",
            value="OS, disk & Python version",
            inline=True,
        )
        embed.add_field(
            name="🗄️ Check Database",
            value="Verify all DB tables exist",
            inline=True,
        )
        embed.add_field(
            name="📄 Validate JSON",
            value="Check data file integrity",
            inline=True,
        )
        embed.add_field(
            name="📋 Command List",
            value="Paginated command overview",
            inline=True,
        )
        embed.add_field(
            name="🔍 Recent Errors",
            value="Last 10 error log entries",
            inline=True,
        )
        embed.add_field(
            name="🔔 Test Notify",
            value="Fire a test webhook ping",
            inline=True,
        )
        embed.set_footer(text="Diagnostics Hub  •  Admin only")
        return embed

    @discord.ui.button(label="🤖 Bot Status", style=discord.ButtonStyle.blurple, row=0)
    async def btn_status(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.diagnostic_bot_status)

    @discord.ui.button(label="📡 Latency", style=discord.ButtonStyle.blurple, row=0)
    async def btn_latency(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.latency)

    @discord.ui.button(label="💻 System Info", style=discord.ButtonStyle.blurple, row=0)
    async def btn_sysinfo(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.system_info)

    @discord.ui.button(label="🗄️ Database", style=discord.ButtonStyle.grey, row=1)
    async def btn_db(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.check_database)

    @discord.ui.button(label="📄 JSON Files", style=discord.ButtonStyle.grey, row=1)
    async def btn_json(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.validate_json_files)

    @discord.ui.button(label="📋 Commands", style=discord.ButtonStyle.grey, row=1)
    async def btn_cmds(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.list_commands_detailed)

    @discord.ui.button(
        label="🔍 Recent Errors",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def btn_errors(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.recent_errors)

    @discord.ui.button(
        label="🔔 Test Notify",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def btn_notify(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.test_notification)


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
        view = _DiagnosticsHubView(ctx, self)
        await send_panel(ctx, embed=view.build_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the diagnostics hub)."""
        view = _DiagnosticsHubView(help_ctx_shim(interaction), self)
        return view.build_embed(), view

    # ------------------------------------------------------------------
    # Command overview
    # ------------------------------------------------------------------

    @commands.command(name="list_commands_detailed", aliases=["listcmds"])
    @commands.has_permissions(administrator=True)
    async def list_commands_detailed(self, ctx):
        """List all registered commands with details, paginated by cog."""
        pages: list[discord.Embed] = []
        cogs_with_cmds = [
            (name, cog.get_commands())
            for name, cog in self.bot.cogs.items()
            if cog.get_commands()
        ]

        COGS_PER_PAGE = 4
        for i in range(0, max(len(cogs_with_cmds), 1), COGS_PER_PAGE):
            chunk = cogs_with_cmds[i : i + COGS_PER_PAGE]
            page_num = i // COGS_PER_PAGE + 1
            total_pages = (
                len(cogs_with_cmds) + COGS_PER_PAGE - 1
            ) // COGS_PER_PAGE or 1
            embed = discord.Embed(
                title=f"Command List — Page {page_num}/{total_pages}",
                color=discord.Color.blue(),
            )
            for cog_name, cmds in chunk:
                lines = []
                for cmd in cmds:
                    cd_text = "No cooldown"
                    if cmd._buckets._cooldown:
                        cd = cmd._buckets._cooldown
                        cd_text = f"{cd.rate}x per {cd.per:.0f}s"
                    aliases = ", ".join(cmd.aliases) if cmd.aliases else "—"
                    lines.append(
                        f"**`!{cmd.name}`** — {(cmd.help or 'No description')[:80]}\n"
                        f"  CD: {cd_text} | Aliases: {aliases}",
                    )
                embed.add_field(
                    name=cog_name,
                    value=("\n".join(lines) or "No commands")[:1024],
                    inline=False,
                )
            pages.append(embed)

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
        import json

        embed = discord.Embed(
            title="JSON Files Validation",
            color=discord.Color.orange(),
        )
        if not os.path.isdir(JSON_DIR):
            embed.description = f"JSON directory not found: `{JSON_DIR}`"
            await ctx.send(embed=embed)
            return

        any_issues = False
        for filename in sorted(os.listdir(JSON_DIR)):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(JSON_DIR, filename)
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, (list, dict)):
                    embed.add_field(name=filename, value="✅ Valid", inline=True)
                else:
                    embed.add_field(
                        name=filename,
                        value="⚠️ Expected list or dict",
                        inline=True,
                    )
                    any_issues = True
            except Exception as exc:
                embed.add_field(name=filename, value=f"❌ {exc}", inline=True)
                any_issues = True

        if not any_issues:
            embed.description = "All JSON files are valid."
        await ctx.send(embed=embed)

    @commands.command(name="check_database", aliases=["checkdb"])
    @commands.has_permissions(administrator=True)
    async def check_database(self, ctx):
        """Verify that all expected PostgreSQL tables exist."""
        expected = {
            "economy",
            "job_progress",
            "inventory",
            "xp",
            "warnings",
            "mod_logs",
            "role_thresholds",
            "guild_settings",
            "logs",
            "reaction_roles",
            "rps_players",
            "mining_inventory",
            "prohibited_words",
            "deathmatch_stats",
            "chain_channels",
            "counting_state",
        }
        try:
            rows = await db.fetchall(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'",
                (),
            )
            existing = {r["tablename"] for r in rows}
        except Exception as exc:
            await ctx.send(f"❌ Could not query database: {exc}", delete_after=15)
            return

        missing = expected - existing
        extra = existing - expected

        embed = discord.Embed(
            title="Database Schema Check",
            color=discord.Color.purple(),
        )
        embed.add_field(
            name="Missing Tables",
            value=", ".join(sorted(missing)) or "None",
            inline=False,
        )
        embed.add_field(
            name="Unexpected Tables",
            value=", ".join(sorted(extra)) or "None",
            inline=False,
        )
        if not missing:
            embed.description = "✅ All expected tables are present."
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Health & performance
    # ------------------------------------------------------------------

    @commands.command(name="diagnostic_bot_status", aliases=["diag_status"])
    @commands.has_permissions(administrator=True)
    async def diagnostic_bot_status(self, ctx):
        """Display bot health and performance metrics."""
        uptime_delta = datetime.datetime.now(tz=datetime.timezone.utc) - getattr(
            self.bot,
            "uptime",
            datetime.datetime.now(tz=datetime.timezone.utc),
        )
        uptime_str = str(uptime_delta).split(".")[0]

        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        embed = discord.Embed(title="Bot Status", color=discord.Color.green())
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(
            name="Members",
            value=str(sum(g.member_count for g in self.bot.guilds)),
            inline=True,
        )
        embed.add_field(name="Commands", value=str(len(self.bot.commands)), inline=True)
        embed.add_field(
            name="Latency",
            value=f"{self.bot.latency*1000:.1f} ms",
            inline=True,
        )
        embed.add_field(name="CPU", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="RAM", value=f"{memory.percent}%", inline=True)
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="latency", aliases=["ping"])
    @commands.has_permissions(administrator=True)
    async def latency(self, ctx):
        """Report the bot's WebSocket latency."""
        ms = self.bot.latency * 1000
        embed = discord.Embed(title="Bot Latency", color=discord.Color.blue())
        embed.add_field(name="Latency", value=f"{ms:.2f} ms", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="system_info", aliases=["sysinfo"])
    @commands.has_permissions(administrator=True)
    async def system_info(self, ctx):
        """Display system-level stats."""
        total, used, free = shutil.disk_usage(
            DATA_DIR if os.path.isdir(DATA_DIR) else "/",
        )
        embed = discord.Embed(title="System Information", color=discord.Color.teal())
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(
            name="OS",
            value=f"{platform.system()} {platform.release()}",
            inline=True,
        )
        embed.add_field(
            name="Disk",
            value=(
                f"Total: {total/2**30:.1f} GB  "
                f"Used: {used/2**30:.1f} GB  "
                f"Free: {free/2**30:.1f} GB"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Log queries (PostgreSQL logs table)
    # ------------------------------------------------------------------

    @commands.command(name="query_logs", aliases=["querylogs"])
    @commands.has_permissions(administrator=True)
    async def query_logs(self, ctx, event_type: str = None, limit: int = 10):
        """Query recent logs from the logs table.  !query_logs [INFO|ERROR|...] [limit]"""
        limit = max(1, min(limit, 25))
        try:
            if event_type:
                rows = await db.fetchall(
                    "SELECT timestamp, level, message FROM logs "
                    "WHERE level=$1 ORDER BY timestamp DESC LIMIT $2",
                    (event_type.upper(), limit),
                )
            else:
                rows = await db.fetchall(
                    "SELECT timestamp, level, message FROM logs "
                    "ORDER BY timestamp DESC LIMIT $1",
                    (limit,),
                )
        except Exception as exc:
            await ctx.send(f"❌ Could not query logs: {exc}", delete_after=15)
            return

        if not rows:
            await ctx.send("No logs found matching the criteria.", delete_after=10)
            return

        embed = discord.Embed(title="Recent Logs", color=discord.Color.dark_red())
        for row in rows:
            ts = str(row.get("timestamp", "?"))[:19]
            embed.add_field(
                name=f"[{ts}] {row['level']}",
                value=str(row["message"])[:256],
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(name="recent_errors", aliases=["errors"])
    @commands.has_permissions(administrator=True)
    async def recent_errors(self, ctx, limit: int = 10):
        """Retrieve the most recent ERROR-level log entries."""
        await ctx.invoke(self.query_logs, event_type="ERROR", limit=limit)

    @commands.command(name="test_notification", aliases=["testnotify"])
    @commands.has_permissions(administrator=True)
    async def test_notification(self, ctx):
        """Send a test notification via the webhook reporter."""
        reporter = getattr(self.bot, "_reporter", None)
        if not reporter:
            await ctx.send("❌ No webhook reporter is configured.", delete_after=10)
            return
        try:
            embed = discord.Embed(
                title="🧪 Test Notification",
                description="This is a test error notification from DiagnosticCog.",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )
            await reporter._send(embed, username="Diagnostic")
            await ctx.send("✅ Test notification sent.", delete_after=10)
        except Exception as exc:
            await ctx.send(f"❌ Failed: {exc}", delete_after=10)

    # ────────────────────────────────────────────────────────────────
    # !platform — runtime introspection (R1 from the hardening plan)
    # Surfaces anchor restoration state, identity-contract findings,
    # and basic runtime statistics so operators can investigate without
    # SSH access.
    # ────────────────────────────────────────────────────────────────

    @commands.group(name="platform", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def platform_grp(self, ctx):
        """Runtime introspection group. Usage: !platform <status|anchors|identity>."""
        await ctx.send(
            "Usage: `!platform status` · `!platform anchors` · "
            "`!platform identity [--fix]`",
            delete_after=15,
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


async def setup(bot):
    await bot.add_cog(DiagnosticCog(bot))
    logger.info("DiagnosticCog loaded.")
