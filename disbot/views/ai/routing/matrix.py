"""Operator routing matrix view (PR-G).

For a given channel + role the operator picks, run the resolver in
dry-run mode and render the resulting decision (precedence trace,
effective min_level, effective cooldown, instruction_profile_ids,
reason_code). No mutations.

The matrix consumes:

* :mod:`services.ai_natural_language_policy` for the resolver.
* :mod:`services.ai_behavior_profile_service` to translate
  instruction_profile_ids into preset keys when applicable.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from core.runtime.interaction_helpers import safe_defer, safe_followup

logger = logging.getLogger("bot.views.ai.routing.matrix")

_TIMEOUT_SECONDS = 180


def _admin(user: Any) -> bool:
    # Canonical admin gate — honours the platform owner (Q-0212).
    from views.base import member_is_admin

    return member_is_admin(user)


async def _preset_lookup() -> dict[int, str]:
    """Map preset id → key (for embed labels). Falls back to ``{}``
    if the catalog is empty / unavailable.
    """
    try:
        from services import ai_behavior_profile_service as svc

        presets = await svc.list_presets()
        return {p.preset_id: p.key for p in presets}
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.debug("routing matrix: preset catalog unavailable (%s)", exc)
        return {}


async def build_routing_matrix_embed(
    *,
    guild_id: int,
    channel_id: int,
    user_id: int,
    user_level: int = 5,
    user_role_ids: tuple[int, ...] = (),
) -> discord.Embed:
    """Run the resolver in dry-run mode and render the outcome.

    The operator picks the (channel, role) pair via the
    :class:`RoutingMatrixSelectView`; this helper does the rest.
    """
    from services import ai_natural_language_policy as nlp

    ctx = nlp.MessageContext(
        guild_id=guild_id,
        channel_id=channel_id,
        category_id=None,
        user_id=user_id,
        user_level=user_level,
        user_role_ids=user_role_ids,
        is_mention=False,
        is_fresh_user=False,
    )
    decision = await nlp.resolve(ctx, dry_run=True)
    presets = await _preset_lookup()

    color = discord.Color.green() if decision.allowed else discord.Color.red()
    embed = discord.Embed(
        title="🧭 AI Routing matrix (dry-run)",
        description=(
            f"channel=<#{channel_id}> · user=<@{user_id}> · "
            f"user_level={user_level} · roles={list(user_role_ids) or '—'}"
        ),
        color=color,
    )
    embed.add_field(
        name="Outcome",
        value=(
            "✅ allowed"
            if decision.allowed
            else f"❌ denied · `{decision.reason_code.value}`"
        ),
        inline=False,
    )
    embed.add_field(
        name="Effective min_level",
        value=str(decision.effective_min_level),
        inline=True,
    )
    embed.add_field(
        name="Effective cooldown",
        value=f"{decision.effective_cooldown}s",
        inline=True,
    )
    if decision.instruction_profile_ids:
        labels = []
        for pid in decision.instruction_profile_ids:
            key = presets.get(int(pid))
            labels.append(f"`{pid}`" + (f" ({key})" if key else ""))
        embed.add_field(
            name="Instruction profiles",
            value=", ".join(labels),
            inline=False,
        )
    if decision.precedence_trace:
        trace = "\n".join(f"• {line}" for line in decision.precedence_trace)
        if len(trace) > 1000:
            trace = trace[:999] + "…"
        embed.add_field(name="Precedence trace", value=trace, inline=False)
    embed.set_footer(
        text=(
            f"policy_snapshot=`{decision.policy_snapshot_hash or '—'}` · "
            "dry-run only · no audit / no cooldown side-effects."
        ),
    )
    return embed


class _MatrixChannelSelect(discord.ui.ChannelSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a channel to preview routing for…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            # No I/O — direct response stays inside the ack window.
            await interaction.response.send_message(
                "❌ This requires a guild context.",
                ephemeral=True,
            )
            return
        # build_routing_matrix_embed awaits the policy resolver and the
        # behavior-preset catalog (both DB-backed). Defer first so the
        # 3-second ack window never expires before the followup lands.
        if not await safe_defer(interaction, ephemeral=True, thinking=True):
            return
        picked = self.values[0]
        embed = await build_routing_matrix_embed(
            guild_id=interaction.guild.id,
            channel_id=picked.id,
            user_id=interaction.user.id,
        )
        await safe_followup(interaction, embed=embed, ephemeral=True)


class RoutingMatrixSelectView(discord.ui.View):
    """Ephemeral picker — channel select that triggers a dry-run resolve."""

    def __init__(self) -> None:
        super().__init__(timeout=_TIMEOUT_SECONDS)
        self.add_item(_MatrixChannelSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not _admin(interaction.user):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        return True


__all__ = [
    "RoutingMatrixSelectView",
    "build_routing_matrix_embed",
]
