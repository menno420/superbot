"""Explore world hub — the federated open-world "town square" (spine PR 1).

This is the top-level hub a player walks out into. It routes them into each
registered game's own world: **Mine** opens the mining hub, **Fish** shows the
fishing entry card. The world list is discovered from
:mod:`services.world_registry`, so a future world (pets, survival) docks in by
registering a :class:`~services.world_registry.WorldEntry` at its own setup —
no edit to this hub.

Design mirrors the proven registry-driven Games hub (``views/games/hub.py``):
one button per registered entry, clicking it edits the panel in place.

Re-parenting note (plan §4): the mining ``🗺️ Explore`` button now forwards here
(it used to open a mining-local stub, ``views/mining/explore_hub.py``, retired
in this PR). The world hub's **Mine** entry walks back into the mining hub, so
existing players keep a working panel.

Plan: ``docs/planning/explore-hub-federated-world-plan-2026-06-19.md`` §4 (PR 1).
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services.world_registry import (
    WorldEntry,
    get_world_entries,
    register_world_entry,
)
from utils.ui_constants import GAME_COLOR
from views.base import HubView

logger = logging.getLogger("bot.views.explore")


# ---------------------------------------------------------------------------
# Built-in world openers (the view layer owns these — they may import views).
# Each opener runs *after* the hosting button has deferred the interaction, so
# it edits the original panel message in place via ``safe_edit``.
# ---------------------------------------------------------------------------


async def _open_mining_world(
    interaction: discord.Interaction,
    view: discord.ui.View,
) -> None:
    """Enter the mining world — swaps the panel to the mining hub."""
    from views.mining.main_panel import MiningHubView, build_overview_embed

    guild_id = interaction.guild_id
    author = interaction.user
    mining_view = MiningHubView()
    if guild_id is None:
        # Mining is guild-only; fall back to the stateless hub embed.
        await safe_edit(
            interaction,
            embed=mining_view.build_embed(),
            view=mining_view,
            attachments=[],
        )
        return
    try:
        embed = await build_overview_embed(
            author.id,
            guild_id,
            name=getattr(author, "display_name", None),
        )
    except Exception:  # noqa: BLE001 — navigation must never crash on a read
        logger.warning("explore: mining overview unavailable; using static hub embed")
        embed = mining_view.build_embed()
    await safe_edit(interaction, embed=embed, view=mining_view, attachments=[])


async def _open_fishing_world(
    interaction: discord.Interaction,
    view: discord.ui.View,
) -> None:
    """Enter the fishing world — fishing is hub-less, so show its entry card.

    Stays on the world hub (``view=view``) so the player can pick another world
    afterwards. Points at the typed ``!fish`` commands that own the loop.
    """
    embed = discord.Embed(
        title="🎣 Fishing",
        description=(
            "Cast a line, build your collection, and climb the fishing ladder.\n\n"
            "Fishing runs on typed commands for now:\n"
            "**`!fish`** — cast a line\n"
            "**`!fishlog`** — your catch collection\n"
            "**`!fishtop`** — the server's top anglers"
        ),
        color=GAME_COLOR,
    )
    embed.set_footer(text="Pick another world above, or run !fish to start.")
    await safe_edit(interaction, embed=embed, view=view, attachments=[])


# ---------------------------------------------------------------------------
# Default world registration (idempotent).
# ---------------------------------------------------------------------------

_DEFAULT_ENTRIES: tuple[WorldEntry, ...] = (
    WorldEntry(
        key="mining",
        label="Mine",
        emoji="⛏️",
        description="Dig for ores, craft gear, and grow your character.",
        opener=_open_mining_world,
        order=10,
    ),
    WorldEntry(
        key="fishing",
        label="Fish",
        emoji="🎣",
        description="Cast a line in lakes and rivers and build your collection.",
        opener=_open_fishing_world,
        order=20,
    ),
)


def ensure_default_world_entries() -> None:
    """Register the built-in worlds (Mine · Fish). Idempotent.

    Called whenever the world hub is built so the entries always exist, even
    after a test resets the registry. Subsystems added later register their own
    entries at their cog setup instead of being listed here.
    """
    for entry in _DEFAULT_ENTRIES:
        register_world_entry(entry)


# ---------------------------------------------------------------------------
# Embed + view
# ---------------------------------------------------------------------------


def build_world_hub_embed() -> discord.Embed:
    """The town-square overview — one line per registered world."""
    ensure_default_world_entries()
    embed = discord.Embed(
        title="🗺️ Explore — the open world",
        description=(
            "Walk out into the world and pick where to go. Each place is its "
            "own game — your progress in one carries its own ladder, and a "
            "shared world ties them together."
        ),
        color=GAME_COLOR,
    )
    entries = get_world_entries()
    if entries:
        lines = [f"{e.emoji} **{e.label}** — {e.description}".strip() for e in entries]
        embed.add_field(name="Where to go", value="\n".join(lines), inline=False)
    else:
        embed.add_field(
            name="No worlds yet",
            value="No worlds are registered yet — check back soon.",
            inline=False,
        )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


class _WorldButton(discord.ui.Button):
    """A direct world button on the Explore hub.

    Defers, then dispatches to the entry's opener (or a generic coming-soon
    card when an entry has no opener yet).
    """

    def __init__(self, *, entry: WorldEntry, row: int) -> None:
        super().__init__(
            label=f"{entry.emoji} {entry.label}".strip()[:80],
            style=discord.ButtonStyle.primary,
            custom_id=f"explore:open:{entry.key}",
            row=row,
        )
        self._entry = entry

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view = self.view
        if not isinstance(view, ExploreWorldHubView):
            return
        opener = self._entry.opener
        if opener is None:
            await safe_edit(
                interaction,
                embed=_coming_soon_embed(self._entry),
                view=view,
                attachments=[],
            )
            return
        await opener(interaction, view)


def _coming_soon_embed(entry: WorldEntry) -> discord.Embed:
    """Generic card for a registered world that has no opener yet."""
    embed = discord.Embed(
        title=f"{entry.emoji} {entry.label} — coming soon".strip(),
        description=(
            f"{entry.description}\n\nThis world is still being built. Pick "
            "another place above for now."
        ),
        color=GAME_COLOR,
    )
    embed.set_footer(text="Pick another world above to continue.")
    return embed


class ExploreWorldHubView(HubView):
    """The federated Explore world hub — one button per registered world.

    Registry-driven: built-in worlds are registered via
    :func:`ensure_default_world_entries`; later subsystems register their own
    :class:`~services.world_registry.WorldEntry` at setup. The view contains no
    game logic — each button forwards into that world's own panel/commands.
    """

    SUBSYSTEM = "games"

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int | None,
    ) -> None:
        super().__init__(author)
        self.guild_id = guild_id
        ensure_default_world_entries()
        # Discord allows 5 rows × 5 buttons. The curated world set is small;
        # pack 5 buttons per row so it scales to a handful of worlds without
        # the windowing the dynamic selectors need.
        for index, entry in enumerate(get_world_entries()):
            self.add_item(_WorldButton(entry=entry, row=index // 5))


__all__ = [
    "ExploreWorldHubView",
    "build_world_hub_embed",
    "ensure_default_world_entries",
]
