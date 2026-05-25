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
from types import SimpleNamespace

import discord
from discord import app_commands
from discord.ext import commands

from core.runtime.ai.contracts import AITask
from services import ai_diagnostics_service
from views.ai.panel import AIPanelView, build_ai_panel_embed

logger = logging.getLogger("bot")


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
