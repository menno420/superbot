"""Dry-run analyzer for the Tools & Workflows UI.

Resolves the orchestration profile for a picked channel (``dry_run=True`` — no
provider call, no state touched) and shows the operator exactly what the model
would be offered: the resolved profile + source, the tool-choice mode and loop
budget, the precedence trace, and the per-tool offered / withheld decision with
a stable reason code ("Why is this tool unavailable?", plan §9.4).

The offered/withheld list is computed at full (``SYSTEM``) scope so it isolates
the *profile's* effect (toolset narrowing / explicit disable). Per-caller
``AIScope`` narrows the set further at request time — the footer says so.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from core.runtime.ai.contracts import AIScope

logger = logging.getLogger("bot.views.ai.tools.preview_view")

_VIEW_TIMEOUT_SECONDS = 300
_PANEL_COLOR = discord.Color.blurple()


async def build_orchestration_preview_embed(
    *,
    guild: discord.Guild,
    member: Any,
    channel: Any,
    bot: Any = None,
    snapshot: Any = None,
) -> discord.Embed:
    """Render the resolved orchestration policy + offered/withheld tools.

    Reused by the Tools & Workflows **Preview** button. Pure read: the resolver
    runs in dry-run mode and ``build_registry`` only assembles specs (no
    provider call). ``snapshot`` is the optional :class:`AIConfigSnapshot`; when
    supplied, the guild-default profile is shown in the footer.
    """
    from services import ai_orchestration_policy as orch_policy
    from services import ai_tool_catalogue, ai_tools

    category_id = getattr(channel, "category_id", None)
    if category_id is not None:
        category_id = int(category_id)

    decision = await orch_policy.resolve(
        orch_policy.OrchestrationContext(
            guild_id=int(guild.id),
            channel_id=int(channel.id),
            category_id=category_id,
        ),
        dry_run=True,
    )

    # Candidate specs at full scope = every guild-available tool, no narrowing.
    # Re-running select_tools with the profile isolates its toolset effect.
    try:
        candidates = ai_tools.build_registry(
            scope=AIScope.SYSTEM,
            guild_id=int(guild.id),
            actor_id=int(getattr(member, "id", 0) or 0),
            guild=guild,
            member=member,
            bot=bot,
        ).specs
    except Exception as exc:  # noqa: BLE001 — preview must not raise
        logger.debug("tools preview: build_registry failed (%s)", exc)
        candidates = ()

    decisions = ai_tool_catalogue.select_tools(
        candidates,
        scope=AIScope.SYSTEM,
        enabled_toolsets=decision.enabled_toolsets,
        disabled_tools=decision.disabled_tools,
    )
    offered = [d.name for d in decisions if d.included]
    withheld = [(d.name, d.reason) for d in decisions if not d.included]

    embed = discord.Embed(
        title="AI Tools & Workflows — preview",
        description=(
            f"Resolving orchestration for "
            f"{getattr(channel, 'mention', f'<#{channel.id}>')}.\n"
            "_Dry-run only — no provider call, no state touched._"
        ),
        color=_PANEL_COLOR,
    )

    toolsets = (
        "all (no narrowing)"
        if decision.enabled_toolsets is None
        else (", ".join(decision.enabled_toolsets) or "none")
    )
    budget = decision.tool_budget
    embed.add_field(
        name="Resolved profile",
        value=(
            f"profile `{decision.profile_key}` (source `{decision.source}`)\n"
            f"toolsets: {toolsets}\n"
            f"tool choice: `{decision.tool_choice.mode.value}`"
            + (
                f" · group `{decision.tool_choice.group_name}`"
                if decision.tool_choice.group_name
                else ""
            )
            + f"\nbudget: hops=`{budget.max_hops}` "
            f"calls=`{budget.max_calls if budget.max_calls is not None else '∞'}` "
            f"workflow=`{decision.workflow}`"
        ),
        inline=False,
    )

    offered_text = ", ".join(f"`{n}`" for n in offered) if offered else "_(none)_"
    embed.add_field(
        name=f"Offered tools ({len(offered)})",
        value=offered_text[:1024],
        inline=False,
    )
    if withheld:
        lines = [
            f"`{name}` — {reason.value if reason else 'withheld'}"
            for name, reason in withheld
        ]
        embed.add_field(
            name=f"Withheld by profile ({len(withheld)})",
            value="\n".join(lines)[:1024],
            inline=False,
        )

    if decision.source_trace:
        trace = "\n".join(f"· {step}" for step in decision.source_trace)
        embed.add_field(name="Precedence", value=trace[:1024], inline=False)

    guild_default = None
    if snapshot is not None:
        guild_default = getattr(
            getattr(snapshot, "orchestration", None),
            "guild_profile_key",
            None,
        )
    footer = "dry_run=True · administrator-only · tools shown at full scope"
    if guild_default:
        footer += f" · guild default: {guild_default}"
    embed.set_footer(text=footer + " (per-caller scope narrows further)")
    return embed


class _ToolsPreviewChannelSelect(discord.ui.ChannelSelect):
    """Pick a channel to dry-run the orchestration resolver against."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a channel to preview…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Preview requires a guild context.",
                ephemeral=True,
            )
            return
        picked = self.values[0]
        from core.runtime import guild_resources

        channel: Any = picked
        full = guild_resources.resolve_channel(
            interaction.guild,
            channel_id=picked.id,
            kind="text",
        )
        if full is not None:
            channel = full

        embed = await build_orchestration_preview_embed(
            guild=interaction.guild,
            member=interaction.user,
            channel=channel,
            bot=interaction.client,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ToolsPreviewChannelSelectView(discord.ui.View):
    """Ephemeral channel picker that runs the orchestration dry-run."""

    def __init__(self) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.add_item(_ToolsPreviewChannelSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Canonical admin gate — honours the platform owner (config.BOT_OWNER_USER_ID).
        from views.base import interaction_is_admin

        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        return True


__all__ = [
    "ToolsPreviewChannelSelectView",
    "build_orchestration_preview_embed",
]
