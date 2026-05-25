"""AI Platform cog — Module 2 of the AI/BTD6 plan.

Provides read-only diagnostics for the AI gateway. Owns no provider
logic; all source-of-truth lives under :mod:`core.runtime.ai` and
:mod:`services.ai_gateway`. Commands consume
:mod:`services.ai_diagnostics_service` and surface the gateway's
state without ever invoking a provider.

The cog matches the standard SuperBot admin-tier shape: a prefix
``@commands.command`` family gated by ``has_permissions(administrator=True)``
and a parallel ``app_commands`` family with the same gating. The
``aimenu`` entry point opens the persistent panel (see
:mod:`views.ai.panel`).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from types import SimpleNamespace

import discord
from discord import app_commands
from discord.ext import commands

from core.runtime.ai.contracts import AITask
from services import ai_diagnostics_service
from views.ai.panel import AIPanelView, build_ai_panel_embed

logger = logging.getLogger("bot")


def _relative_time(ts: datetime, *, now: datetime | None = None) -> str:
    """Format ``ts`` as a relative-time string like ``"2m ago"``.

    Returns ``"in the future"`` if ``ts`` is later than ``now``; the
    audit table writes ``created_at`` server-side so this should not
    happen in practice, but the renderer must not raise on clock skew.
    """
    reference = now or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    delta = (reference - ts).total_seconds()
    if delta < 0:
        return "in the future"
    if delta < 60:
        return f"{int(delta)}s ago"
    if delta < 3600:
        return f"{int(delta // 60)}m ago"
    if delta < 86400:
        return f"{int(delta // 3600)}h ago"
    return f"{int(delta // 86400)}d ago"


def _format_audit_row(row: dict) -> str:
    """Format one ``ai_decision_audit`` row for the why-no-response embed.

    Includes relative timestamp, decision, reason_code, task, route,
    channel link, user mention, provider, model. No raw message content
    is rendered (the audit table does not store any).
    """
    created_at = row.get("created_at")
    when = _relative_time(created_at) if isinstance(created_at, datetime) else "—"
    return (
        f"`{when:<8}` · `{row['decision']:<8}` · `{row['reason_code']}` · "
        f"task={row.get('task') or '—'} · route={row.get('route') or '—'} · "
        f"<#{row['channel_id']}> · <@{row['user_id']}> · "
        f"provider={row.get('provider') or '—'} model={row.get('model') or '—'}"
    )


async def _build_ai_settings_panel(
    author: discord.abc.User,
    guild_id: int | None,
) -> tuple[discord.Embed, discord.ui.View]:
    """Build the (embed, view) pair for the AI Platform settings panel.

    Reuses :func:`views.settings.subsystem_view.build_subsystem_embed`
    and :class:`SubsystemSettingsView` so the dedicated ``!ai settings``
    entry point renders identically to opening AI via the global
    ``!settings`` hub.
    """
    from views.settings.subsystem_view import (
        SubsystemSettingsView,
        build_subsystem_embed,
    )

    # build_subsystem_embed only reads .guild_id from its first arg.
    shim = SimpleNamespace(guild_id=guild_id)
    embed = await build_subsystem_embed(shim, "ai")  # type: ignore[arg-type]
    view = SubsystemSettingsView(author, "ai")
    return embed, view


# ---------------------------------------------------------------------------
# Embed builders — used by both the slash/prefix commands and the panel
# buttons. Centralised here so the panel and the explicit commands always
# render the same data.
# ---------------------------------------------------------------------------


def build_status_embed() -> discord.Embed:
    """Compact status: enabled / default provider / last call outcome."""
    snap = ai_diagnostics_service.snapshot_for_cog()
    embed = discord.Embed(
        title="AI Gateway — Status",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Enabled", value="yes" if snap["enabled"] else "no")
    embed.add_field(name="Default provider", value=str(snap["default_provider"]))
    embed.add_field(
        name="Setup advisor provider",
        value=str(snap["setup_advisor_provider"]),
    )
    embed.add_field(name="Active provider", value=str(snap["provider_active"]))
    embed.add_field(name="Requests", value=str(snap["requests_observed"]))
    embed.add_field(name="Failures", value=str(snap["failures_observed"]))
    return embed


def build_diagnostics_embed() -> discord.Embed:
    """Full diagnostics snapshot — every counter the gateway exposes."""
    snap = ai_diagnostics_service.snapshot_for_cog()
    embed = discord.Embed(
        title="AI Gateway — Diagnostics",
        color=discord.Color.blurple(),
    )
    for key, value in snap.items():
        embed.add_field(name=key.replace("_", " "), value=str(value), inline=True)
    return embed


def build_providers_embed() -> discord.Embed:
    """List of configured providers and which is active right now."""
    snap = ai_diagnostics_service.snapshot_for_cog()
    embed = discord.Embed(
        title="AI Gateway — Providers",
        description=(
            "Configured providers. The active provider is the one the "
            "gateway selected for the most recent request; the default "
            "provider is the env-driven choice for new requests."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Default", value=str(snap["default_provider"]))
    embed.add_field(name="Active (last call)", value=str(snap["provider_active"]))
    embed.add_field(name="Setup advisor", value=str(snap["setup_advisor_provider"]))
    return embed


def build_routing_embed(task_name: str | None = None) -> discord.Embed:
    """Per-task routing table. With ``task_name``, narrows to one row."""
    rows = ai_diagnostics_service.list_task_routing()
    if task_name:
        rows = [r for r in rows if r["task"] == task_name]
    embed = discord.Embed(
        title="AI Gateway — Routing",
        description=(
            "Resolved provider/model/timeout for each AI task. This view "
            "does not invoke any provider."
        ),
        color=discord.Color.blurple(),
    )
    if not rows:
        embed.add_field(
            name="No matching task",
            value=f"Known tasks: {', '.join(t.value for t in AITask)}",
            inline=False,
        )
        return embed
    for row in rows:
        embed.add_field(
            name=str(row["task"]),
            value=(
                f"provider: `{row['provider']}`\n"
                f"model: `{row['model']}`\n"
                f"timeout: `{row['timeout_seconds']}s`\n"
                f"enabled: `{row['enabled']}`"
            ),
            inline=True,
        )
    embed.set_footer(
        text=(
            "Per-guild overrides from ai_guild_policy.default_provider / "
            "default_model take precedence at gateway time when set. "
            "Run !ai policy in a guild to see its typed overrides."
        ),
    )
    return embed


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class AICog(commands.Cog):
    """AI Platform surface — diagnostics (Module 2) + M1 settings host."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        # Register the AI SubsystemSchema so the auto-dispatched
        # settings UI renders the AI section for free. Idempotent —
        # the underlying registry replaces on re-registration with a
        # DEBUG log entry.
        from cogs.ai.schemas import register_schemas

        register_schemas()

        # M2: install the central natural-language stage at order 70
        # so it runs before the legacy BTD6 stage (order 80) and
        # before any future passive responder. Registering through
        # message_pipeline.register dedupes by name, so reloading
        # the cog stays clean.
        from core.runtime import message_pipeline
        from core.runtime.ai.natural_language_stage import get_stage

        message_pipeline.register(get_stage())

        # Claim the "ai" prefix on the interaction router so button
        # clicks from views.ai.panel.AIPanelView don't emit
        # "Unhandled interaction prefix 'ai'" warnings. The View's own
        # @discord.ui.button callbacks remain the primary dispatcher;
        # the router handler is a safety net that bails when
        # interaction.response.is_done() is true.
        #
        # interaction_router has no unregister() API; registrations are
        # process-lifetime. The guard below makes cog_load idempotent so
        # repeated reloads do not trigger spurious overwrite WARNINGs
        # and do not silently replace a handler set by another path.
        from core.runtime import interaction_router
        from views.ai.panel import AI_ROUTER_PREFIX, handle_ai_interaction

        existing = interaction_router._handlers.get(AI_ROUTER_PREFIX)
        if existing is handle_ai_interaction:
            pass  # already registered to the correct handler; skip
        elif existing is not None:
            logger.warning(
                "AICog.cog_load: replacing unexpected handler for "
                "interaction-router prefix %r",
                AI_ROUTER_PREFIX,
            )
            interaction_router.register(AI_ROUTER_PREFIX, handle_ai_interaction)
        else:
            interaction_router.register(AI_ROUTER_PREFIX, handle_ai_interaction)

    async def cog_unload(self) -> None:
        from core.runtime import message_pipeline
        from core.runtime.ai.natural_language_stage import STAGE_NAME

        message_pipeline.unregister(STAGE_NAME)

        # interaction_router exposes no unregister() API — the module-level
        # _handlers dict holds registrations for the lifetime of the
        # process by design. We cannot remove the "ai" prefix here. The
        # handler reference remains valid because it dispatches to
        # module-level build_* functions that stay importable. On reload,
        # cog_load's idempotency guard detects that the handler is already
        # handle_ai_interaction and skips re-registration.

    # ------------------------------------------------------------------
    # Prefix commands — `!ai`, `!ai status`, `!ai diagnostics`, ...
    # ------------------------------------------------------------------

    @commands.group(name="ai", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def ai_group(self, ctx: commands.Context) -> None:
        """Open the AI Platform panel."""
        await ctx.send(embed=build_ai_panel_embed(), view=AIPanelView())

    @ai_group.command(name="status")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def ai_status(self, ctx: commands.Context) -> None:
        await ctx.send(embed=build_status_embed())

    @ai_group.command(name="settings")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def ai_settings(self, ctx: commands.Context) -> None:
        """Open the AI Platform settings panel directly."""
        guild_id = ctx.guild.id if ctx.guild else None
        embed, view = await _build_ai_settings_panel(ctx.author, guild_id)
        await ctx.send(embed=embed, view=view)

    @ai_group.command(name="why-no-response")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def ai_why_no_response(
        self,
        ctx: commands.Context,
        limit: int = 10,
    ) -> None:
        """Show the most recent denials / skips for this guild."""
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return
        from services import ai_decision_audit_service

        rows = await ai_decision_audit_service.query(
            ctx.guild.id,
            limit=max(1, min(50, int(limit))),
        )
        denials = [
            r
            for r in rows
            if r["decision"] in ("denied", "skipped", "errored", "degraded")
        ][:25]
        if not denials:
            await ctx.send("No recent denials or skips for this guild.")
            return
        lines = [_format_audit_row(r) for r in denials]
        embed = discord.Embed(
            title="AI — why no response",
            description="\n".join(lines),
            color=discord.Color.orange(),
        )
        oldest = denials[-1].get("created_at")
        if isinstance(oldest, datetime):
            embed.set_footer(
                text=(
                    f"Showing {len(denials)} most recent · "
                    f"oldest: {oldest.isoformat()}"
                ),
            )
        else:
            embed.set_footer(text=f"Showing {len(denials)} most recent")
        await ctx.send(embed=embed)

    @ai_group.command(name="policy")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def ai_policy(self, ctx: commands.Context) -> None:
        """Show the typed policy row for this guild."""
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return
        from utils.db import ai as ai_db

        policy = await ai_db.get_guild_policy(ctx.guild.id)
        if not policy:
            await ctx.send(
                "No typed AI policy row yet — set `ai.enabled` via `!settings`"
                " to create one.",
            )
            return
        lines = [
            f"**enabled** = `{policy['enabled']}`",
            f"**natural_language_enabled** = `{policy['natural_language_enabled']}`",
            f"**default_provider** = `{policy['default_provider']}`",
            f"**default_model** = `{policy['default_model'] or '—'}`",
            f"**minimum_level_default** = `{policy['minimum_level_default']}`",
            f"**cooldown_seconds** = `{policy['cooldown_seconds']}`",
            f"**fresh_user_mention_allowance** ="
            f" `{policy['fresh_user_mention_allowance']}`",
            f"**generation** = `{policy['generation']}`",
        ]
        await ctx.send("\n".join(lines))

    @ai_group.command(name="diagnostics")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def ai_diagnostics(self, ctx: commands.Context) -> None:
        await ctx.send(embed=build_diagnostics_embed())

    @ai_group.command(name="providers")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def ai_providers(self, ctx: commands.Context) -> None:
        await ctx.send(embed=build_providers_embed())

    @ai_group.command(name="routing")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def ai_routing(
        self,
        ctx: commands.Context,
        task: str | None = None,
    ) -> None:
        await ctx.send(embed=build_routing_embed(task))

    @commands.command(name="aimenu")
    @commands.has_permissions(administrator=True)
    async def aimenu(self, ctx: commands.Context) -> None:
        """Open the AI Platform panel (alias for ``!ai``)."""
        await ctx.send(embed=build_ai_panel_embed(), view=AIPanelView())

    @ai_group.command(name="support-report")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def ai_support_report(self, ctx: commands.Context) -> None:
        """Render a copy-pasteable support report from recent audit (PR-H).

        No outbound delivery — the operator copies the rendered code
        block into whatever support channel they use.
        """
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return
        from views.ai.support_report import build_support_report_embed

        bot_user_id = getattr(self.bot.user, "id", None) if self.bot.user else None
        embed = await build_support_report_embed(
            guild_id=ctx.guild.id,
            bot_user_id=bot_user_id,
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # App commands (slash). Mirror the prefix group, admin-gated.
    # ------------------------------------------------------------------

    ai_app_group = app_commands.Group(
        name="ai",
        description="AI Platform diagnostics (administrator only).",
        default_permissions=discord.Permissions(administrator=True),
    )

    @ai_app_group.command(name="status", description="AI gateway status summary.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ai_status_slash(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=build_status_embed(),
            ephemeral=True,
        )

    @ai_app_group.command(
        name="diagnostics",
        description="Full AI gateway diagnostics snapshot.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ai_diagnostics_slash(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=build_diagnostics_embed(),
            ephemeral=True,
        )

    @ai_app_group.command(
        name="providers",
        description="List configured AI providers.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ai_providers_slash(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=build_providers_embed(),
            ephemeral=True,
        )

    @ai_app_group.command(
        name="routing",
        description="Show the routing table for AI tasks.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ai_routing_slash(
        self,
        interaction: discord.Interaction,
        task: str | None = None,
    ) -> None:
        await interaction.response.send_message(
            embed=build_routing_embed(task),
            ephemeral=True,
        )

    @ai_app_group.command(
        name="support-report",
        description="Render a copy-paste AI support report (no delivery).",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ai_support_report_slash(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return
        from views.ai.support_report import build_support_report_embed

        bot_user_id = (
            getattr(self.bot.user, "id", None) if self.bot.user else None
        )
        embed = await build_support_report_embed(
            guild_id=interaction.guild.id,
            bot_user_id=bot_user_id,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ai_app_group.command(
        name="settings",
        description="Open the AI Platform settings panel.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ai_settings_slash(self, interaction: discord.Interaction) -> None:
        embed, view = await _build_ai_settings_panel(
            interaction.user,
            interaction.guild_id,
        )
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )

    @app_commands.command(
        name="aimenu",
        description="Open the AI Platform panel (administrator only).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def aimenu_slash(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=build_ai_panel_embed(),
            view=AIPanelView(),
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # Help-menu hook (the standard SuperBot pattern).
    # ------------------------------------------------------------------

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Direct-navigation hook used by ``help_cog.route``."""
        return build_ai_panel_embed(), AIPanelView()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AICog(bot))
