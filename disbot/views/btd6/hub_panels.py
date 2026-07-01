"""BTD6 hub category sub-panels (menu Layout B).

The persistent :class:`views.btd6.panel.BTD6PanelView` shows one button per
**subdivision**; each opens one of these ephemeral :class:`BaseView` sub-panels,
which wire the already-shipped browsers + embed builders (and a couple of input
modals for the round/economy lookups that had no panel entry point before). The
design study is ``docs/btd6/btd6-menu-layout-design-2026-07-01.md``; the shape
was chosen with ``tools/btd6/menu_layout_simulator.html`` (owner picked Layout B).

Ephemeral + short-lived, so ``BaseView`` (invoker-locked, auto-timeout) is the
right base — not ``PersistentView``. Sub-panel buttons carry no ``custom_id``:
discord.py generates them for a non-persistent view, and nothing needs to match
these across a restart. Each leaf action opens its own follow-up ephemeral (or a
modal), reusing the exact functions the ``/btd6`` slash commands call, so the
hub adds discoverability without duplicating any logic.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import discord

from core.runtime.interaction_helpers import safe_defer, safe_followup
from views.base import BaseView

_Handler = Callable[[discord.Interaction], Awaitable[None]]
_HUB_COLOR = discord.Color.green()


# ---------------------------------------------------------------------------
# Leaf actions — each reuses the existing browser / builder the slash uses.
# ---------------------------------------------------------------------------


async def _open_towers(interaction: discord.Interaction) -> None:
    from views.btd6.tower_browser_view import open_tower_browser

    await open_tower_browser(interaction)


async def _open_heroes(interaction: discord.Interaction) -> None:
    from views.btd6.hero_browser_view import open_hero_browser

    await open_hero_browser(interaction)


async def _open_paragon(interaction: discord.Interaction) -> None:
    from views.btd6.paragon_view import open_paragon_calculator

    await open_paragon_calculator(interaction)


async def _open_live_events(interaction: discord.Interaction) -> None:
    from views.btd6.live_events_view import open_live_events_browser

    await open_live_events_browser(interaction)


async def _open_leaderboards(interaction: discord.Interaction) -> None:
    from views.btd6.leaderboard_browser_view import open_leaderboard_browser

    await open_leaderboard_browser(interaction)


async def _open_ct(interaction: discord.Interaction) -> None:
    # Contested Territory browser + rendered hex map (mirrors the old btd6:ct button).
    from cogs.btd6._builders import build_ct_browser_embed
    from views.btd6.ct_map_view import build_ct_map_file

    if not await safe_defer(interaction, ephemeral=True):
        return
    embed = await build_ct_browser_embed()
    map_file, _ = await build_ct_map_file()
    if map_file is not None:
        embed.set_image(url="attachment://ct_map.png")
    await safe_followup(interaction, embed=embed, file=map_file, ephemeral=True)


async def _show_maps(interaction: discord.Interaction) -> None:
    from cogs.btd6._embeds import build_maps_embed

    if not await safe_defer(interaction, ephemeral=True):
        return
    await safe_followup(interaction, embed=build_maps_embed(), ephemeral=True)


async def _show_modes(interaction: discord.Interaction) -> None:
    from cogs.btd6._embeds import build_modes_embed

    if not await safe_defer(interaction, ephemeral=True):
        return
    await safe_followup(interaction, embed=build_modes_embed(), ephemeral=True)


async def _show_status(interaction: discord.Interaction) -> None:
    from cogs.btd6._embeds import build_status_embed

    if not await safe_defer(interaction, ephemeral=True):
        return
    await safe_followup(interaction, embed=await build_status_embed(), ephemeral=True)


async def _show_strategy(interaction: discord.Interaction) -> None:
    from views.btd6 import strategy_browse

    if not await safe_defer(interaction, ephemeral=True):
        return
    await safe_followup(
        interaction,
        embed=await strategy_browse.build_browse_embed(limit=10),
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# Input modals — the round/economy + bloon lookups that had no panel entry.
# ---------------------------------------------------------------------------


def _parse_round(raw: str | None) -> int | None:
    """A round number in 1..140, or ``None`` when blank / out of range."""
    text = (raw or "").strip().lstrip("rR")
    if not text.isdigit():
        return None
    value = int(text)
    return value if 1 <= value <= 140 else None


_ROUND_TITLES = {
    "round": "Round lookup",
    "rbe": "RBE lookup",
    "income": "Income lookup",
}


class _RoundModal(discord.ui.Modal):
    """One round, or an inclusive range, for the round / RBE / income builders."""

    def __init__(self, kind: str) -> None:
        super().__init__(title=_ROUND_TITLES.get(kind, "Round lookup"))
        self._kind = kind
        self.start_round: discord.ui.TextInput = discord.ui.TextInput(
            label="Round (or first round of a range)",
            placeholder="e.g. 63",
            required=True,
            max_length=3,
        )
        self.end_round: discord.ui.TextInput = discord.ui.TextInput(
            label="Last round (optional — for a range)",
            placeholder="e.g. 100",
            required=False,
            max_length=3,
        )
        self.add_item(self.start_round)
        self.add_item(self.end_round)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        start = _parse_round(str(self.start_round.value))
        raw_end = str(self.end_round.value).strip()
        end = _parse_round(raw_end) if raw_end else None
        if start is None or (raw_end and end is None):
            await interaction.response.send_message(
                "Enter a round number between 1 and 140.",
                ephemeral=True,
            )
            return
        if not await safe_defer(interaction, ephemeral=True):
            return
        from cogs.btd6._builders import (
            build_income_embed,
            build_rbe_embed,
            build_round_embed,
        )

        if self._kind == "rbe":
            embed = await build_rbe_embed(start, end)
        elif self._kind == "income":
            embed = await build_income_embed(start, end)
        else:
            embed = await build_round_embed(start, end)
        await safe_followup(interaction, embed=embed, ephemeral=True)


class _BloonModal(discord.ui.Modal, title="Bloon lookup"):
    """A bloon name → the deterministic bloon answer (stats, immunities, children)."""

    name: discord.ui.TextInput = discord.ui.TextInput(
        label="Bloon name",
        placeholder="e.g. ceramic, MOAB, lead, BAD",
        required=True,
        max_length=40,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from cogs.btd6._embeds import response_to_embed
        from services import btd6_ai_service

        if not await safe_defer(interaction, ephemeral=True):
            return
        response = await btd6_ai_service.answer_question(str(self.name.value))
        await safe_followup(
            interaction,
            embed=response_to_embed(response),
            ephemeral=True,
        )


def _round_modal_opener(kind: str) -> _Handler:
    async def _open(interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(_RoundModal(kind))

    return _open


async def _open_bloon_modal(interaction: discord.Interaction) -> None:
    await interaction.response.send_modal(_BloonModal())


# ---------------------------------------------------------------------------
# Category registry — one entry list per subdivision.
# ---------------------------------------------------------------------------

_P = discord.ButtonStyle.primary
_S = discord.ButtonStyle.secondary

# id -> (emoji, label, blurb, [(emoji, label, style, handler), ...])
_CATEGORIES: dict[
    str,
    tuple[str, str, str, list[tuple[str, str, discord.ButtonStyle, _Handler]]],
] = {
    "units": (
        "🗼",
        "Units",
        "Towers, heroes & paragons — stats, upgrades, crosspaths.",
        [
            ("🗼", "Towers", _P, _open_towers),
            ("🦸", "Heroes", _P, _open_heroes),
            ("🔮", "Paragons", _P, _open_paragon),
        ],
    ),
    "events": (
        "🎯",
        "Live Events",
        "Race / boss / CT / odyssey, leaderboards, relics.",
        [
            ("🎯", "Live events", _P, _open_live_events),
            ("🏆", "Leaderboards", _P, _open_leaderboards),
            ("🗺️", "CT + map", _S, _open_ct),
        ],
    ),
    "rounds": (
        "🎲",
        "Rounds & Economy",
        "Round detail, RBE & income (single round or a range), bloon lookup.",
        [
            ("🎲", "Round / range", _P, _round_modal_opener("round")),
            ("💥", "RBE", _S, _round_modal_opener("rbe")),
            ("💰", "Income", _S, _round_modal_opener("income")),
            ("🎈", "Bloon lookup", _S, _open_bloon_modal),
        ],
    ),
    "maps": (
        "🗺️",
        "Maps & Modes",
        "Maps by difficulty (with water) + mode rules.",
        [
            ("🗺️", "Maps", _S, _show_maps),
            ("🎛️", "Modes", _S, _show_modes),
        ],
    ),
    "strategy": (
        "📋",
        "Strategy",
        "Community strategy memory — published strategies.",
        [
            ("📋", "Browse strategies", _S, _show_strategy),
        ],
    ),
    "status": (
        "📊",
        "Status",
        "Assistant status & dataset health.",
        [
            ("📊", "Status", _S, _show_status),
        ],
    ),
}


class BTD6CategoryView(BaseView):
    """Ephemeral sub-panel: one button per function in a subdivision.

    Invoker-locked (``BaseView``), no standard nav (``SUBSYSTEM`` unset), 5-min
    timeout. Each button's callback is one of the leaf handlers above.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        entries: list[tuple[str, str, discord.ButtonStyle, _Handler]],
    ) -> None:
        super().__init__(author, timeout=300)
        for emoji, label, style, handler in entries:
            button: discord.ui.Button = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=style,
            )
            # Dynamically-added items are invoked as ``await item.callback(interaction)``;
            # our leaf handlers have exactly that shape. (discord.py types callback as
            # a generic-Client coroutine, hence the assignment ignore.)
            button.callback = handler  # type: ignore[assignment]
            self.add_item(button)


async def open_category(interaction: discord.Interaction, category_id: str) -> None:
    """Open the ephemeral sub-panel for ``category_id`` as a follow-up.

    Unknown ids fail closed to a short notice rather than raising — the caller is
    a persistent button whose custom_id could outlive a category rename.
    """
    entry = _CATEGORIES.get(category_id)
    if entry is None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        await safe_followup(
            interaction,
            content="That section is unavailable — re-open the BTD6 panel.",
            ephemeral=True,
        )
        return
    emoji, label, blurb, entries = entry
    if not await safe_defer(interaction, ephemeral=True):
        return
    embed = discord.Embed(
        title=f"{emoji} {label}",
        description=blurb,
        color=_HUB_COLOR,
    )
    await safe_followup(
        interaction,
        embed=embed,
        view=BTD6CategoryView(interaction.user, entries),
        ephemeral=True,
    )


__all__ = ["BTD6CategoryView", "open_category"]
