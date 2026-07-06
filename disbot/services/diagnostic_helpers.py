"""Shared diagnostic helpers (S4.4.5-followup stabilization).

Each helper is a pure embed/page builder consumed by BOTH the
``DiagnosticCog`` text command (which does ``ctx.send(embed=...)``)
AND the matching button on ``_DiagnosticsHubView`` (which does
``safe_edit(interaction, embed=..., view=self)``).

Splitting embed construction from the channel I/O is what lets the
hub view update its panel in place — matching the canonical panel
pattern used by ``views/economy/main_panel.py``,
``views/moderation/main_panel.py``, and the xp/mining/role hubs.

Two-consumer rule (§A2.1) satisfied for every helper.  No
abstractions beyond plain functions per §A11.6.
"""

from __future__ import annotations

import datetime
import json
import os
import platform
import shutil

import discord
from discord.ext import commands

# ---------------------------------------------------------------------------
# Data directories (mirror the cog's pre-stabilization layout exactly)
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
)
JSON_DIR = os.path.join(DATA_DIR, "json")


# ---------------------------------------------------------------------------
# Hub overview embed (no dependencies)
# ---------------------------------------------------------------------------


def build_hub_overview_embed() -> discord.Embed:
    """The static overview embed shown when the diagnostics hub opens.

    Listing the 8 tools matches the button layout on _DiagnosticsHubView.
    """
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


# ---------------------------------------------------------------------------
# Health & performance
# ---------------------------------------------------------------------------


def build_bot_status_embed(bot: commands.Bot) -> discord.Embed:
    """Bot health and performance metrics."""
    import psutil

    uptime_delta = datetime.datetime.now(tz=datetime.timezone.utc) - getattr(
        bot,
        "uptime",
        datetime.datetime.now(tz=datetime.timezone.utc),
    )
    uptime_str = str(uptime_delta).split(".")[0]

    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()

    embed = discord.Embed(title="Bot Status", color=discord.Color.green())
    embed.add_field(name="Guilds", value=str(len(bot.guilds)), inline=True)
    embed.add_field(
        name="Members",
        value=str(sum(g.member_count for g in bot.guilds)),
        inline=True,
    )
    embed.add_field(name="Commands", value=str(len(bot.commands)), inline=True)
    embed.add_field(
        name="Latency",
        value=f"{bot.latency * 1000:.1f} ms",
        inline=True,
    )
    embed.add_field(name="CPU", value=f"{cpu_usage}%", inline=True)
    embed.add_field(name="RAM", value=f"{memory.percent}%", inline=True)
    embed.add_field(name="Uptime", value=uptime_str, inline=True)
    return embed


def build_latency_embed(bot: commands.Bot) -> discord.Embed:
    """Report the bot's WebSocket latency."""
    ms = bot.latency * 1000
    embed = discord.Embed(title="Bot Latency", color=discord.Color.blue())
    embed.add_field(name="Latency", value=f"{ms:.2f} ms", inline=True)
    return embed


def build_system_info_embed() -> discord.Embed:
    """System-level stats: Python version, OS, disk usage."""
    total, used, free = shutil.disk_usage(DATA_DIR if os.path.isdir(DATA_DIR) else "/")
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
            f"Total: {total / 2**30:.1f} GB  "
            f"Used: {used / 2**30:.1f} GB  "
            f"Free: {free / 2**30:.1f} GB"
        ),
        inline=False,
    )
    return embed


# ---------------------------------------------------------------------------
# Data integrity
# ---------------------------------------------------------------------------


def _format_table_set(names: set[str], *, limit: int = 1024) -> str:
    """Render a set of table names as a comma list that fits one embed
    field.

    Discord caps embed field values at 1024 chars; a raw
    ``", ".join(...)`` of every table overflowed once the schema grew
    past ~50 tables and made Discord reject the whole embed (the panel
    edit then silently failed).  This trims to as many names as fit and
    appends a ``+N more`` marker.
    """
    if not names:
        return "None"
    ordered = sorted(names)
    joined = ", ".join(ordered)
    if len(joined) <= limit:
        return joined
    kept = list(ordered)
    while kept:
        suffix = f", … (+{len(ordered) - len(kept)} more)"
        candidate = ", ".join(kept)
        if len(candidate) + len(suffix) <= limit:
            return candidate + suffix
        kept.pop()
    return f"(+{len(ordered)} more)"


async def build_check_database_embed() -> discord.Embed:
    """Report schema health: base tables present + every migration applied.

    The DB is migration-managed, so the authoritative signals are (a) the
    pre-migration base tables exist and (b) every ``NNN_*.sql`` migration has
    been recorded in ``schema_migrations`` — not a hand-maintained "expected
    tables" list.  That list went stale and flagged all ~52 migration-added
    tables as "unexpected"; several tables are also created by runtime code
    (e.g. ``bot_runtime_lock``), so no static list can stay correct.
    """
    base = {
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
    from utils.db.migrations import (
        applied_migration_versions,
        list_public_tables,
        migration_versions_on_disk,
    )

    try:
        existing = await list_public_tables()
        applied = await applied_migration_versions()
    except Exception as exc:
        return discord.Embed(
            title="Database Schema Check",
            description=f"❌ Could not query database: {exc}",
            color=discord.Color.red(),
        )

    on_disk = migration_versions_on_disk()
    pending = on_disk - applied
    missing_base = base - existing
    healthy = not missing_base and not pending

    embed = discord.Embed(
        title="Database Schema Check",
        color=discord.Color.green() if healthy else discord.Color.orange(),
        description=(
            "✅ Schema healthy — all base tables present and every migration applied."
            if healthy
            else "⚠️ Schema needs attention (details below)."
        ),
    )
    embed.add_field(
        name="Base tables",
        value=(
            f"✅ {len(base)}/{len(base)} present"
            if not missing_base
            else f"❌ missing {len(missing_base)}: {_format_table_set(missing_base)}"
        ),
        inline=False,
    )
    embed.add_field(
        name="Migrations applied",
        value=(
            f"✅ {len(on_disk) - len(pending)}/{len(on_disk)}"
            if not pending
            else f"⚠️ {len(on_disk) - len(pending)}/{len(on_disk)} — pending: "
            + ", ".join(f"{v:03d}" for v in sorted(pending))
        ),
        inline=False,
    )
    embed.add_field(name="Tables present", value=str(len(existing)), inline=False)
    return embed


def build_validate_json_embed() -> discord.Embed:
    """Validate the structure of all JSON files in the data directory."""
    embed = discord.Embed(title="JSON Files Validation", color=discord.Color.orange())
    if not os.path.isdir(JSON_DIR):
        embed.description = f"JSON directory not found: `{JSON_DIR}`"
        return embed

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

    if not any_issues and embed.fields:
        embed.description = "All JSON files are valid."
    return embed


# ---------------------------------------------------------------------------
# Command overview (paginated)
# ---------------------------------------------------------------------------


def build_command_list_pages(bot: commands.Bot) -> list[discord.Embed]:
    """Build the multi-embed page list for the paginated command overview."""
    pages: list[discord.Embed] = []
    cogs_with_cmds = [
        (name, cog.get_commands())
        for name, cog in bot.cogs.items()
        if cog.get_commands()
    ]

    cogs_per_page = 4
    for i in range(0, max(len(cogs_with_cmds), 1), cogs_per_page):
        chunk = cogs_with_cmds[i : i + cogs_per_page]
        page_num = i // cogs_per_page + 1
        total_pages = (len(cogs_with_cmds) + cogs_per_page - 1) // cogs_per_page or 1
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
    return pages


# ---------------------------------------------------------------------------
# Log queries
# ---------------------------------------------------------------------------


async def build_query_logs_embed(
    event_type: str | None = None,
    limit: int = 10,
) -> discord.Embed:
    """Show recent in-process log records (optionally filtered by level).

    Reads the in-memory ring buffer installed by ``DiagnosticCog.setup()``.
    The legacy ``logs`` DB table was never written to (the bot logs to
    ``bot.log`` + stdout), so the DB-backed version always returned
    "No logs found matching the criteria".
    """
    from cogs.diagnostic._log_buffer import recent

    limit = max(1, min(limit, 25))
    rows = recent(level=event_type, limit=limit)

    embed = discord.Embed(title="Recent Logs", color=discord.Color.dark_red())
    if not rows:
        embed.description = "No logs found matching the criteria."
        return embed
    for row in rows:
        ts = str(row.get("timestamp", "?"))[:19]
        embed.add_field(
            name=f"[{ts}] {row['level']}",
            value=str(row["message"])[:256],
            inline=False,
        )
    return embed


# ---------------------------------------------------------------------------
# Test webhook notification
# ---------------------------------------------------------------------------


async def build_test_notification_embed(bot: commands.Bot) -> discord.Embed:
    """Fire a test webhook notification and return the status embed."""
    reporter = getattr(bot, "_reporter", None)
    if not reporter:
        return discord.Embed(
            title="🔔 Test Notification",
            description="❌ No webhook reporter is configured.",
            color=discord.Color.red(),
        )
    try:
        test_embed = discord.Embed(
            title="🧪 Test Notification",
            description="This is a test error notification from DiagnosticCog.",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        await reporter._send(test_embed, username="Diagnostic")
    except Exception as exc:
        return discord.Embed(
            title="🔔 Test Notification",
            description=f"❌ Failed: {exc}",
            color=discord.Color.red(),
        )
    return discord.Embed(
        title="🔔 Test Notification",
        description="✅ Test notification sent.",
        color=discord.Color.green(),
    )


# ---------------------------------------------------------------------------
# Snapshot value formatter (used by !platform commands; relocated from cog)
# ---------------------------------------------------------------------------


def _fmt_snapshot_value(value: object) -> str:
    """Format a diagnostics provider's snapshot for embed display."""
    if isinstance(value, dict):
        if not value:
            return "*(empty)*"
        lines = []
        for k, v in value.items():
            if isinstance(v, (list, tuple)):
                v_str = ", ".join(map(str, v[:8]))
                if len(v) > 8:
                    v_str += f", … (+{len(v) - 8} more)"
                lines.append(f"**{k}**: {v_str or '*(none)*'}")
            elif isinstance(v, dict):
                lines.append(
                    f"**{k}**: " + ", ".join(f"{kk}={vv}" for kk, vv in v.items()),
                )
            else:
                lines.append(f"**{k}**: {v}")
        return "\n".join(lines)[:1024]
    return str(value)[:1024]
