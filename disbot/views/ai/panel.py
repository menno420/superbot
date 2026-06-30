"""AI Platform persistent panel — Module 2 of the AI/BTD6 plan.

Pattern B placement per ``docs/architecture.md`` §"PersistentView
placement": the view lives in ``views/ai/`` so the cog file stays
small. Importing this module triggers the ``@register`` decorator
on :class:`AIPanelView` so the persistent-view registry sees the
``ai`` subsystem before ``on_ready`` runs ``restore_anchors``.

Custom_ids use the ``ai:<action>`` prefix. ``AICog.cog_load``
registers :func:`handle_ai_interaction` with
:mod:`core.runtime.interaction_router` so the router does not log
"Unhandled interaction prefix 'ai'" warnings when a button is
clicked. The View's own ``@discord.ui.button`` callbacks remain the
primary dispatcher for ``PersistentView`` buttons; the router
handler is a safety net that bails immediately when
``interaction.response.is_done()`` is true.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from core.runtime.persistent_views import PersistentView, register
from services import ai_diagnostics_service

logger = logging.getLogger("bot.views.ai.panel")

_PANEL_COLOR = discord.Color.blurple()

AI_ROUTER_PREFIX = "ai"


def build_ai_panel_embed() -> discord.Embed:
    """Build the read-only AI Platform overview embed.

    Reads ``ai_diagnostics_service.snapshot_for_cog()`` so the
    overview reflects the latest counters without invoking any
    provider.
    """
    snap = ai_diagnostics_service.snapshot_for_cog()
    enabled = snap["enabled"]
    degraded = snap["degraded"]
    status_emoji = "✅" if enabled and not degraded else ("⚠️" if degraded else "💤")

    embed = discord.Embed(
        title=f"{status_emoji} AI Platform",
        description=(
            "Read-only diagnostics for the AI gateway. The buttons "
            "below open the matching subcommands without making a "
            "provider call."
        ),
        color=_PANEL_COLOR,
    )
    embed.add_field(name="Enabled", value="yes" if enabled else "no", inline=True)
    embed.add_field(
        name="Default provider",
        value=str(snap["default_provider"]),
        inline=True,
    )
    embed.add_field(
        name="Setup advisor provider",
        value=str(snap["setup_advisor_provider"]),
        inline=True,
    )
    embed.add_field(
        name="Active provider (last call)",
        value=str(snap["provider_active"]),
        inline=True,
    )
    embed.add_field(
        name="Requests / failures",
        value=f"{snap['requests_observed']} / {snap['failures_observed']}",
        inline=True,
    )
    embed.add_field(
        name="Redaction",
        value="on" if snap["redaction_enabled"] else "off",
        inline=True,
    )
    if degraded:
        embed.add_field(
            name="Last fallback reason",
            value=str(snap["last_fallback_reason"] or "—"),
            inline=False,
        )
    embed.set_footer(text="!ai status / !ai diagnostics / !ai providers / !ai routing")
    return embed


@register
class AIPanelView(PersistentView):
    """Persistent AI Platform panel — administrator-only.

    The panel is intentionally read-only. Every button refreshes one
    of the existing diagnostic views; no button performs a provider
    call or any state mutation.
    """

    SUBSYSTEM = "ai"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Canonical admin gate — honours the platform owner (config.BOT_OWNER_USER_ID).
        from views.base import interaction_is_admin

        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need the Administrator permission to use the AI panel.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="Refresh",
        style=discord.ButtonStyle.secondary,
        row=0,
        custom_id="ai:refresh",
    )
    async def refresh_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = _embed_for_ai_panel_action("refresh")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Diagnostics",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="ai:diagnostics",
    )
    async def diagnostics_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = _embed_for_ai_panel_action("diagnostics")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Providers",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="ai:providers",
    )
    async def providers_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = _embed_for_ai_panel_action("providers")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Routing",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="ai:routing",
    )
    async def routing_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = _embed_for_ai_panel_action("routing")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Settings",
        style=discord.ButtonStyle.success,
        row=1,
        custom_id="ai:settings",
    )
    async def settings_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # M1: open the AI subsystem settings panel in place.
        # Settings is the only action that requires an async call —
        # _embed_for_ai_panel_action handles the four sync actions; this
        # branch is special-cased here and in handle_ai_interaction below.
        from cogs.ai_cog import _build_ai_settings_panel

        embed, view = await _build_ai_settings_panel(
            interaction.user,
            interaction.guild_id,
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(
        label="Policy",
        style=discord.ButtonStyle.success,
        row=1,
        custom_id="ai:policy",
    )
    async def policy_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # In-place navigation (AI nav plan PR 1): swap the anchor message
        # to the policy chooser *page* instead of opening a new ephemeral.
        # The chooser dispatches each scope (channel / category / role /
        # list) on the same anchor; writes flow through
        # ``services.ai_policy_mutation`` from inside those scope views.
        from views.ai.policy.chooser import (
            PolicyChooserView,
            build_chooser_embed,
        )

        await interaction.response.edit_message(
            embed=build_chooser_embed(),
            view=PolicyChooserView(),
        )

    @discord.ui.button(
        label="Behavior",
        style=discord.ButtonStyle.success,
        row=1,
        custom_id="ai:behavior",
    )
    async def behavior_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # In-place navigation (AI nav plan PR 1): swap the anchor to the
        # usability-first Behavior chooser page. Bind presets without
        # learning the raw policy knobs.
        from views.ai.behavior import (
            BehaviorChooserView,
            build_behavior_embed,
        )

        await interaction.response.edit_message(
            embed=build_behavior_embed(),
            view=BehaviorChooserView(),
        )

    @discord.ui.button(
        label="Tools",
        style=discord.ButtonStyle.success,
        row=1,
        custom_id="ai:tools",
    )
    async def tools_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # In-place navigation (AI nav plan PR 1): swap the anchor to the
        # Tools & Workflows chooser page (orchestration profiles).
        # Reads the snapshot best-effort so the chooser shows the current
        # guild-default profile + override counts; writes flow through
        # services.ai_orchestration_mutation from inside the scope views.
        from views.ai.tools import ToolsChooserView, build_tools_embed

        snapshot = await _best_effort_ai_snapshot(interaction.guild_id)
        if interaction.response.is_done():
            return
        await interaction.response.edit_message(
            embed=build_tools_embed(snapshot),
            view=ToolsChooserView(),
        )


# ---------------------------------------------------------------------------
# Shared dispatch + interaction-router handler
# ---------------------------------------------------------------------------


async def _best_effort_ai_snapshot(guild_id: int | None) -> Any:
    """Build the AI config snapshot for ``guild_id``, or ``None`` on failure.

    Used to show the current orchestration profile in the Tools & Workflows
    chooser. Best-effort: the chooser renders its static intro without it.
    """
    if guild_id is None:
        return None
    try:
        from services import ai_config_projection_service

        return await ai_config_projection_service.build_snapshot(guild_id)
    except Exception:
        logger.debug(
            "ai panel: snapshot build failed for guild=%s",
            guild_id,
            exc_info=True,
        )
        return None


def _embed_for_ai_panel_action(action: str) -> discord.Embed | None:
    """Single source of truth for sync AI panel action → embed mapping.

    Returns the embed for refresh / diagnostics / providers / routing.
    Returns ``None`` for "settings" (async, special-cased by callers) and
    for unknown actions. Callers decide which ``view`` to attach (the
    View buttons reuse ``self``; the router handler creates a fresh
    ``AIPanelView()``).
    """
    if action == "refresh":
        return build_ai_panel_embed()
    # Lazy imports keep this module importable from cogs.ai_cog without
    # introducing a circular dependency at module load time.
    if action == "diagnostics":
        from cogs.ai_cog import build_diagnostics_embed

        return build_diagnostics_embed()
    if action == "providers":
        from cogs.ai_cog import build_providers_embed

        return build_providers_embed()
    if action == "routing":
        from cogs.ai_cog import build_routing_embed

        return build_routing_embed()
    return None


async def handle_ai_interaction(
    interaction: discord.Interaction,
    action: str,
    session: Any,
    request_id: str,
) -> None:
    """Interaction-router handler for prefix ``"ai"``.

    ``AIPanelView`` (PersistentView) is the primary dispatcher — its
    button callbacks run concurrently with this handler and usually win
    the race.  This handler is the post-restart fallback for when the
    view is not alive in memory.  All response calls are wrapped in
    try/except so a concurrent view response never surfaces as an ERROR.
    """
    if interaction.response.is_done():
        return

    # Canonical admin gate — honours the platform owner (config.BOT_OWNER_USER_ID).
    from views.base import interaction_is_admin

    if not interaction_is_admin(interaction):
        try:
            await interaction.response.send_message(
                "❌ You need the Administrator permission to use the AI panel.",
                ephemeral=True,
            )
        except (discord.InteractionResponded, discord.NotFound):
            pass
        except discord.HTTPException as exc:
            if exc.code != 40060:
                raise
        return

    try:
        if action == "settings":
            from cogs.ai_cog import _build_ai_settings_panel

            embed, view = await _build_ai_settings_panel(
                interaction.user,
                interaction.guild_id,
            )
            # Re-check after the async call — the view may have responded
            # while _build_ai_settings_panel was awaited.
            if interaction.response.is_done():
                return
            await interaction.response.edit_message(embed=embed, view=view)
            return

        if action == "policy":
            from views.ai.policy.chooser import (
                PolicyChooserView,
                build_chooser_embed,
            )

            # Post-restart fallback: the in-memory view is gone but the
            # anchor message persists, so navigate it in place (matching
            # the live button path) rather than spawning a new ephemeral.
            await interaction.response.edit_message(
                embed=build_chooser_embed(),
                view=PolicyChooserView(),
            )
            return

        if action == "behavior":
            from views.ai.behavior import (
                BehaviorChooserView,
                build_behavior_embed,
            )

            await interaction.response.edit_message(
                embed=build_behavior_embed(),
                view=BehaviorChooserView(),
            )
            return

        if action == "tools":
            from views.ai.tools import ToolsChooserView, build_tools_embed

            snapshot = await _best_effort_ai_snapshot(interaction.guild_id)
            if interaction.response.is_done():
                return
            await interaction.response.edit_message(
                embed=build_tools_embed(snapshot),
                view=ToolsChooserView(),
            )
            return

        embed = _embed_for_ai_panel_action(action)
        if embed is None:
            await interaction.response.send_message(
                f"❌ Unknown AI panel action: {action!r}",
                ephemeral=True,
            )
            return
        await interaction.response.edit_message(embed=embed, view=AIPanelView())

    except discord.InteractionResponded:
        pass  # View beat us to it — normal race on PersistentView buttons.
    except discord.HTTPException as exc:
        if exc.code != 40060:  # 40060 = already_acknowledged, same race
            raise


__all__ = [
    "AI_ROUTER_PREFIX",
    "AIPanelView",
    "build_ai_panel_embed",
    "handle_ai_interaction",
]
