"""Paragon Calculator — ephemeral panel opened from the BTD6 hub / ``!paragon``.

Two flows share one config surface:

* **Calculate** — pick a paragon, players, difficulty, and extra-T5 count, then
  enter your numbers in a modal to get the resulting degree.
* **Requirements** — pick a strategy (balanced / least cash / tiers / pops) and a
  target degree to get a recommended build.

All compute goes through :mod:`services.paragon_service` (live API with a
labelled local fallback). Result formatting lives here as private helpers so it
is not spread across the cog, modals, and service.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services.paragon_service import (
    CALCULATOR_AUTHOR_NAME,
    CALCULATOR_PUBLIC_URL,
    ParagonRequirementResult,
    ParagonResult,
    ParagonServiceError,
    ParagonUnknownTowerError,
)
from utils.btd6.paragon_math import (
    PARAGONS,
    SolveStrategy,
    game_mode_for,
    max_extra_t5_count,
    resolve_paragon,
)
from views.base import HubView

logger = logging.getLogger("bot.views.btd6.paragon")

_DEFAULT_PARAGON = "apex_plasma_master"

_AXIS_EMOJI = {
    "pops": "💥",
    "upgrades": "⬆️",
    "cash": "💰",
    "extra_t5s": "🛡️",
    "totems": "🔱",
}
_AXIS_LABEL = {
    "pops": "Pops",
    "upgrades": "Upgrade tiers",
    "cash": "Cash",
    "extra_t5s": "Extra T5s",
    "totems": "Geraldo totems",
}
_STRATEGY_LABEL = {
    SolveStrategy.BALANCED: "Balanced (even split)",
    SolveStrategy.LEAST_CASH: "Least cash",
    SolveStrategy.LEAST_TIERS: "Least tiers",
    SolveStrategy.LEAST_POPS: "Least pops",
}
_DIFFICULTIES = (
    ("easy", "Easy (0.85x)"),
    ("medium", "Medium (1.0x)"),
    ("hard", "Hard (1.08x)"),
    ("impoppable", "Impoppable (1.2x)"),
)


def _fmt(value: int) -> str:
    return f"{value:,}"


def _add_credits_field(embed: discord.Embed) -> None:
    """Attach the web-calculator link + author credit to a paragon embed.

    Shared by every paragon embed builder so the click-through to the live
    site and the credit to its Discord author travel with each result.
    """
    embed.add_field(
        name="🔗 Web calculator & credits",
        value=(
            f"[paragon-calc.vercel.app]({CALCULATOR_PUBLIC_URL}) — "
            f"built by **{CALCULATOR_AUTHOR_NAME}**"
        ),
        inline=False,
    )


def _web_calculator_button(row: int) -> discord.ui.Button:
    """A link button to the web Paragon Calculator (no callback — URL button)."""
    return discord.ui.Button(
        label="🌐 Web calculator",
        style=discord.ButtonStyle.link,
        url=CALCULATOR_PUBLIC_URL,
        row=row,
    )


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def build_calculator_embed(view: ParagonCalculatorView) -> discord.Embed:
    paragon = resolve_paragon(view.paragon_id)
    name = paragon.name if paragon else view.paragon_id
    tower = paragon.tower if paragon else ""
    mode = game_mode_for(view.player_count)
    embed = discord.Embed(
        title=f"🔮 Paragon Calculator — {name}",
        description=(
            f"**Paragon:** {name} ({tower})\n"
            f"**Players:** {view.player_count} ({mode})\n"
            f"**Difficulty:** {view.difficulty.title()}\n"
            f"**Extra T5s:** {view.tier5_count}"
        ),
        color=discord.Color.green(),
    )
    embed.add_field(
        name="🧮 Calculate degree",
        value="Enter your pops / cash / tiers / totems to see the degree you'd get.",
        inline=False,
    )
    embed.add_field(
        name="🎯 Requirements for a degree",
        value="Pick a strategy and a target degree to get a recommended build.",
        inline=False,
    )
    embed.set_footer(
        text="Solo: 1 extra T5 (Dart only) · Co-op: up to 9 · totems are uncapped",
    )
    _add_credits_field(embed)
    return embed


def _axis_line(axis: object) -> str:
    key = axis.key  # type: ignore[attr-defined]
    power = axis.power  # type: ignore[attr-defined]
    max_power = axis.max_power  # type: ignore[attr-defined]
    if max_power is None:
        return f"{_AXIS_EMOJI[key]} **{_AXIS_LABEL[key]}:** {_fmt(power)} (uncapped)"
    fill = axis.fill_pct  # type: ignore[attr-defined]
    pct = f" ({fill:.0f}%)" if fill is not None else ""
    capped = " • **capped**" if axis.capped else ""  # type: ignore[attr-defined]
    return f"{_AXIS_EMOJI[key]} **{_AXIS_LABEL[key]}:** {_fmt(power)} / {_fmt(max_power)}{pct}{capped}"


def build_result_embed(result: ParagonResult) -> discord.Embed:
    breakdown = result.breakdown
    color = discord.Color.gold() if result.estimated else discord.Color.green()
    embed = discord.Embed(
        title=f"🔮 {result.paragon_name} — Degree {breakdown.degree}",
        color=color,
    )
    lines = [f"**Total power:** {_fmt(breakdown.total_power)}"]
    if breakdown.degree < 100:
        lines.append(
            f"**To Degree {breakdown.next_degree}:** +{_fmt(breakdown.power_for_next_degree)} power",
        )
    else:
        lines.append("**Maximum degree reached.** 🏆")
    if result.estimated:
        lines.append("\n⚠️ *Local estimate — the live calculator was unavailable.*")
    embed.description = "\n".join(lines)

    embed.add_field(
        name="Power breakdown",
        value="\n".join(_axis_line(axis) for axis in breakdown.axes),
        inline=False,
    )
    if breakdown.wasted_cash > 0:
        embed.add_field(
            name="💸 Wasted cash",
            value=f"${_fmt(breakdown.wasted_cash)} gave no benefit (cash power is capped).",
            inline=False,
        )
    notes = [w.message for w in result.warnings]
    if notes:
        embed.add_field(
            name="⚠️ Notes",
            value="\n".join(f"• {note}" for note in notes),
            inline=False,
        )
    suffix = "estimate" if result.estimated else f"API v{result.api_version}"
    embed.set_footer(
        text=(
            f"{result.tower} • {result.difficulty.title()} • {result.game_mode} • "
            f"base ${_fmt(result.base_price)} • {suffix}"
        ),
    )
    _add_credits_field(embed)
    return embed


def build_requirements_config_embed(view: ParagonRequirementsView) -> discord.Embed:
    paragon = resolve_paragon(view.paragon_id)
    name = paragon.name if paragon else view.paragon_id
    mode = game_mode_for(view.player_count)
    embed = discord.Embed(
        title=f"🎯 Requirements — {name}",
        description=(
            f"**Strategy:** {_STRATEGY_LABEL[view.strategy]}\n"
            f"**Players:** {view.player_count} ({mode})\n"
            f"**Difficulty:** {view.difficulty.title()}\n\n"
            "Choose a strategy, then **Enter target degree** to get a build."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(
        text="Least-X maxes the other inputs; totems top up only the highest degrees.",
    )
    _add_credits_field(embed)
    return embed


def build_requirement_embed(req: ParagonRequirementResult) -> discord.Embed:
    solution = req.solution
    inputs = solution.inputs
    embed = discord.Embed(
        title=f"🎯 {req.paragon_name} — reach Degree {solution.target_degree}",
        color=discord.Color.green(),
    )
    reaches = (
        req.confirmed_degree
        if req.confirmed_degree is not None
        else solution.breakdown.degree
    )
    desc = [
        f"**Strategy:** {_STRATEGY_LABEL[solution.strategy]}",
        f"**This build reaches:** Degree {reaches}",
    ]
    if req.estimated:
        desc.append("\n⚠️ *Not live-confirmed — computed locally.*")
    embed.description = "\n".join(desc)

    embed.add_field(
        name="Recommended sacrifices",
        value=(
            f"💥 **Pops:** {_fmt(inputs.pops)}\n"
            f"⬆️ **Upgrade tiers:** {inputs.upgrade_count}\n"
            f"💰 **Cash:** ${_fmt(inputs.cash_spent)}\n"
            f"🛡️ **Extra T5s:** {inputs.tier5_count}\n"
            f"🔱 **Geraldo totems:** {inputs.geraldo_totems}"
        ),
        inline=False,
    )
    if solution.requires_totems:
        embed.add_field(
            name="🔱 Totems required",
            value="Capped inputs alone can't reach this degree — Geraldo totems make up the rest.",
            inline=False,
        )
    embed.set_footer(
        text=f"{req.tower} • {inputs.difficulty.title()} • {game_mode_for(inputs.player_count)}",
    )
    _add_credits_field(embed)
    return embed


def build_error_embed(exc: ParagonServiceError) -> discord.Embed:
    embed = discord.Embed(title="🔮 Paragon Calculator", color=discord.Color.red())
    if isinstance(exc, ParagonUnknownTowerError):
        towers = ", ".join(exc.valid_towers[:8])
        embed.description = f"Couldn't match that paragon. Try one of: {towers}…"
    else:
        embed.description = f"⚠️ {exc}"
    return embed


# ---------------------------------------------------------------------------
# Calculator (landing) view
# ---------------------------------------------------------------------------


class _ParagonSelect(discord.ui.Select):
    def __init__(self, parent: ParagonCalculatorView) -> None:
        self._panel = parent
        options = [
            discord.SelectOption(
                label=p.name[:100],
                value=p.paragon_id,
                description=p.tower[:100],
                default=p.paragon_id == parent.paragon_id,
            )
            for p in PARAGONS
        ]
        super().__init__(placeholder="Choose a paragon…", options=options[:25], row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        self._panel.paragon_id = self.values[0]
        self._panel.rebuild()
        await safe_edit(
            interaction,
            embed=build_calculator_embed(self._panel),
            view=self._panel,
        )


class _PlayerCountSelect(discord.ui.Select):
    def __init__(self, parent: ParagonCalculatorView) -> None:
        self._panel = parent
        options = [
            discord.SelectOption(
                label="Solo (1 player)" if n == 1 else f"Co-op ({n} players)",
                value=str(n),
                default=n == parent.player_count,
            )
            for n in (1, 2, 3, 4)
        ]
        super().__init__(placeholder="Players…", options=options, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        self._panel.player_count = int(self.values[0])
        self._panel.rebuild()
        await safe_edit(
            interaction,
            embed=build_calculator_embed(self._panel),
            view=self._panel,
        )


class _DifficultySelect(discord.ui.Select):
    def __init__(self, parent: ParagonCalculatorView) -> None:
        self._panel = parent
        options = [
            discord.SelectOption(
                label=label,
                value=value,
                default=value == parent.difficulty,
            )
            for value, label in _DIFFICULTIES
        ]
        super().__init__(placeholder="Difficulty…", options=options, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        self._panel.difficulty = self.values[0]
        self._panel.rebuild()
        await safe_edit(
            interaction,
            embed=build_calculator_embed(self._panel),
            view=self._panel,
        )


class _Tier5Select(discord.ui.Select):
    def __init__(self, parent: ParagonCalculatorView) -> None:
        self._panel = parent
        paragon = resolve_paragon(parent.paragon_id)
        mode = game_mode_for(parent.player_count)
        limit = max_extra_t5_count(mode, is_dart=bool(paragon and paragon.is_dart))
        options = [
            discord.SelectOption(
                label=f"{n} extra T5",
                value=str(n),
                default=n == parent.tier5_count,
            )
            for n in range(0, max(limit, 0) + 1)
        ]
        disabled = limit == 0
        if disabled:
            options = [
                discord.SelectOption(
                    label="0 extra T5 (not allowed here)",
                    value="0",
                    default=True,
                ),
            ]
        super().__init__(
            placeholder="Extra T5s…",
            options=options,
            row=3,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self._panel.tier5_count = int(self.values[0])
        self._panel.rebuild()
        await safe_edit(
            interaction,
            embed=build_calculator_embed(self._panel),
            view=self._panel,
        )


class _CalculateButton(discord.ui.Button):
    def __init__(self, parent: ParagonCalculatorView) -> None:
        self._panel = parent
        super().__init__(
            label="🧮 Calculate degree",
            style=discord.ButtonStyle.primary,
            row=4,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.btd6.paragon_modals import ParagonForwardModal

        await interaction.response.send_modal(ParagonForwardModal(self._panel))


class _RequirementsButton(discord.ui.Button):
    def __init__(self, parent: ParagonCalculatorView) -> None:
        self._panel = parent
        super().__init__(
            label="🎯 Requirements",
            style=discord.ButtonStyle.success,
            row=4,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = ParagonRequirementsView(
            interaction.user,
            paragon_id=self._panel.paragon_id,
            player_count=self._panel.player_count,
            difficulty=self._panel.difficulty,
        )
        await safe_edit(
            interaction,
            embed=build_requirements_config_embed(view),
            view=view,
        )


class _StatsButton(discord.ui.Button):
    """Open the selected paragon's combat-stats view (degree picker)."""

    def __init__(self, parent: ParagonCalculatorView) -> None:
        self._panel = parent
        super().__init__(label="📊 Stats", style=discord.ButtonStyle.secondary, row=4)

    async def callback(self, interaction: discord.Interaction) -> None:
        from services import btd6_stats_service
        from views.btd6.paragon_stats_view import open_paragon_stats

        if not await safe_defer(interaction, ephemeral=True):
            return
        stats = btd6_stats_service.get_paragon_stats(self._panel.paragon_id)
        if stats is None or not stats.has_combat_stats:
            # Module-less paragon (Root of all Nature, Herald of Everfrost): the
            # wiki has no stats data page yet, so only its cost is known.
            embed = discord.Embed(
                title="📊 Paragon stats",
                description=(
                    "No combat-stats module is published for this paragon yet — "
                    "only its cost is known. Pick another paragon to see full stats."
                ),
                color=discord.Color.orange(),
            )
            await safe_edit(interaction, embed=embed, view=self._panel)
            return

        paragon_id = self._panel.paragon_id
        player_count = self._panel.player_count
        difficulty = self._panel.difficulty

        async def _rebuild_calculator(
            inter: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            view = ParagonCalculatorView(
                inter.user,
                paragon_id=paragon_id,
                player_count=player_count,
                difficulty=difficulty,
            )
            return build_calculator_embed(view), view

        await open_paragon_stats(
            interaction,
            stats,
            back_label="↩ Calculator",
            back_custom_id=f"btd6_paragon_stats:back_calc:{paragon_id}",
            back_builder=_rebuild_calculator,
        )


class _BackToBtd6Button(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="↩ BTD6", style=discord.ButtonStyle.secondary, row=4)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        from views.btd6.panel import BTD6PanelView, build_btd6_panel_embed

        await safe_edit(
            interaction,
            embed=await build_btd6_panel_embed(),
            view=BTD6PanelView(),
        )


class ParagonCalculatorView(HubView):
    """The ephemeral landing panel for the Paragon calculator."""

    def __init__(
        self,
        author: discord.User | discord.Member,
        *,
        paragon_id: str = _DEFAULT_PARAGON,
        player_count: int = 1,
        difficulty: str = "medium",
        tier5_count: int = 0,
    ) -> None:
        super().__init__(author)
        self.paragon_id = paragon_id
        self.player_count = player_count
        self.difficulty = difficulty
        self.tier5_count = tier5_count
        self.rebuild()

    def rebuild(self) -> None:
        # Keep the extra-T5 choice within the current mode/paragon's limit.
        paragon = resolve_paragon(self.paragon_id)
        limit = max_extra_t5_count(
            game_mode_for(self.player_count),
            is_dart=bool(paragon and paragon.is_dart),
        )
        self.tier5_count = min(self.tier5_count, limit)
        self.clear_items()
        self.add_item(_ParagonSelect(self))
        self.add_item(_PlayerCountSelect(self))
        self.add_item(_DifficultySelect(self))
        self.add_item(_Tier5Select(self))
        self.add_item(_CalculateButton(self))
        self.add_item(_RequirementsButton(self))
        self.add_item(_StatsButton(self))
        self.add_item(_BackToBtd6Button())
        self.add_item(_web_calculator_button(4))


# ---------------------------------------------------------------------------
# Requirements (reverse-solve) view
# ---------------------------------------------------------------------------


class _StrategySelect(discord.ui.Select):
    def __init__(self, parent: ParagonRequirementsView) -> None:
        self._panel = parent
        options = [
            discord.SelectOption(
                label=_STRATEGY_LABEL[s],
                value=s.value,
                default=s == parent.strategy,
            )
            for s in SolveStrategy
        ]
        super().__init__(placeholder="Strategy…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        self._panel.strategy = SolveStrategy(self.values[0])
        self._panel.rebuild()
        await safe_edit(
            interaction,
            embed=build_requirements_config_embed(self._panel),
            view=self._panel,
        )


class _EnterTargetButton(discord.ui.Button):
    def __init__(self, parent: ParagonRequirementsView) -> None:
        self._panel = parent
        super().__init__(
            label="🎯 Enter target degree",
            style=discord.ButtonStyle.primary,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.btd6.paragon_modals import ParagonTargetModal

        await interaction.response.send_modal(ParagonTargetModal(self._panel))


class _BackToCalculatorButton(discord.ui.Button):
    def __init__(self, parent: ParagonRequirementsView) -> None:
        self._panel = parent
        super().__init__(
            label="↩ Calculator",
            style=discord.ButtonStyle.secondary,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = ParagonCalculatorView(
            interaction.user,
            paragon_id=self._panel.paragon_id,
            player_count=self._panel.player_count,
            difficulty=self._panel.difficulty,
        )
        await safe_edit(interaction, embed=build_calculator_embed(view), view=view)


class ParagonRequirementsView(HubView):
    """Strategy + target-degree picker for the reverse solver."""

    def __init__(
        self,
        author: discord.User | discord.Member,
        *,
        paragon_id: str,
        player_count: int,
        difficulty: str,
        strategy: SolveStrategy = SolveStrategy.BALANCED,
    ) -> None:
        super().__init__(author)
        self.paragon_id = paragon_id
        self.player_count = player_count
        self.difficulty = difficulty
        self.strategy = strategy
        self.rebuild()

    def rebuild(self) -> None:
        self.clear_items()
        self.add_item(_StrategySelect(self))
        self.add_item(_EnterTargetButton(self))
        self.add_item(_BackToCalculatorButton(self))
        self.add_item(_web_calculator_button(1))


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


async def open_paragon_calculator(interaction: discord.Interaction) -> None:
    """Open the Paragon calculator as an ephemeral followup."""
    if not await safe_defer(interaction, ephemeral=True):
        return
    view = ParagonCalculatorView(interaction.user)
    await safe_followup(
        interaction,
        embed=build_calculator_embed(view),
        view=view,
        ephemeral=True,
    )


__all__ = [
    "ParagonCalculatorView",
    "ParagonRequirementsView",
    "build_calculator_embed",
    "build_error_embed",
    "build_requirement_embed",
    "build_result_embed",
    "open_paragon_calculator",
]
