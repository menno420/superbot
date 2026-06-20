"""Unit tests for the federated Explore world hub (spine PR 1).

Pins:
* the hub embed lists the registered worlds,
* the view renders one button per registered entry (registry-driven),
* the Mine button forwards into the mining hub,
* the Fish button shows the fishing entry card and stays on the world hub,
* an opener-less entry renders a generic coming-soon card.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.world_registry import (
    WorldEntry,
    clear_world_entries,
    get_world_entries,
    register_world_entry,
)
from views.explore.world_hub import (
    ExploreWorldHubView,
    build_world_hub_embed,
    ensure_default_world_entries,
)

_AUTHOR = SimpleNamespace(id=7, name="Wanderer", display_name="Wanderer")


@pytest.fixture(autouse=True)
def _clean_registry():
    clear_world_entries()
    yield
    clear_world_entries()


def _find_button(view: discord.ui.View, label_substr: str) -> discord.ui.Button:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and label_substr in (child.label or ""):
            return child
    raise AssertionError(f"No button with label containing {label_substr!r}")


def test_default_entries_register_mine_and_fish():
    ensure_default_world_entries()
    keys = {e.key for e in get_world_entries()}
    assert {"mining", "fishing"} <= keys


def test_embed_lists_registered_worlds():
    embed = build_world_hub_embed()
    blob = " ".join(f.value for f in embed.fields)
    assert "Mine" in blob
    assert "Fish" in blob
    assert "Explore" in (embed.title or "")


def test_view_renders_a_button_per_entry():
    view = ExploreWorldHubView(_AUTHOR, 99)
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    # Mine + Fish from the default registration.
    labels = " | ".join(b.label or "" for b in buttons)
    assert "Mine" in labels
    assert "Fish" in labels
    assert view.guild_id == 99
    assert view._author is _AUTHOR


def test_view_is_registry_driven():
    """A newly-registered world appears as a button without editing the view."""
    register_world_entry(
        WorldEntry(key="pets", label="Adopt", emoji="🐾", description="pets", order=30),
    )
    view = ExploreWorldHubView(_AUTHOR, 99)
    labels = " | ".join(
        b.label or "" for b in view.children if isinstance(b, discord.ui.Button)
    )
    assert "Adopt" in labels


@pytest.mark.asyncio
async def test_mine_button_forwards_to_mining_hub():
    view = ExploreWorldHubView(_AUTHOR, 99)
    btn = _find_button(view, "Mine")
    interaction = MagicMock()
    interaction.user = _AUTHOR
    interaction.guild_id = 99
    with (
        patch(
            "views.explore.world_hub.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.explore.world_hub.safe_edit",
            new_callable=AsyncMock,
        ) as safe_edit,
        patch(
            "views.mining.main_panel.build_overview_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(title="⛏️ Mining Hub"),
        ),
    ):
        await btn.callback(interaction)
    safe_edit.assert_awaited_once()
    swapped = safe_edit.await_args.kwargs["view"]
    assert type(swapped).__name__ == "MiningHubView"


@pytest.mark.asyncio
async def test_fish_button_shows_card_and_stays_on_hub():
    view = ExploreWorldHubView(_AUTHOR, 99)
    btn = _find_button(view, "Fish")
    interaction = MagicMock()
    interaction.user = _AUTHOR
    interaction.guild_id = 99
    with (
        patch(
            "views.explore.world_hub.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.explore.world_hub.safe_edit",
            new_callable=AsyncMock,
        ) as safe_edit,
    ):
        await btn.callback(interaction)
    safe_edit.assert_awaited_once()
    kwargs = safe_edit.await_args.kwargs
    assert kwargs["view"] is view  # stays on the town square
    assert "!fish" in (kwargs["embed"].description or "")


@pytest.mark.asyncio
async def test_world_card_button_opens_card_and_stays_on_hub():
    view = ExploreWorldHubView(_AUTHOR, 99)
    btn = _find_button(view, "World Card")
    interaction = MagicMock()
    interaction.user = _AUTHOR
    interaction.guild_id = 99
    with (
        patch(
            "views.explore.world_hub.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.explore.world_hub.safe_edit",
            new_callable=AsyncMock,
        ) as safe_edit,
        patch(
            "views.explore.world_card.build_world_card_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(title="🪪 world card"),
        ) as build_card,
    ):
        await btn.callback(interaction)
    build_card.assert_awaited_once_with(_AUTHOR, 99)
    safe_edit.assert_awaited_once()
    assert safe_edit.await_args.kwargs["view"] is view  # stays on the town square


@pytest.mark.asyncio
async def test_mining_explore_button_attaches_back_to_mining():
    """Mining hub → 🗺️ Explore opens the world hub WITH a "↩ Mining Hub" back
    button so the player isn't stranded. The !world root open (GamesCog) omits
    it — back is attached externally by the opener, mirroring Help/Games.
    """
    from views.mining.main_panel import MiningHubView

    hub = MiningHubView()
    btn = _find_button(hub, "Explore")
    interaction = MagicMock()
    interaction.user = _AUTHOR
    interaction.guild_id = 99
    with (
        patch(
            "views.mining.main_panel.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.main_panel.safe_edit",
            new_callable=AsyncMock,
        ) as safe_edit,
    ):
        await btn.callback(interaction)
    safe_edit.assert_awaited_once()
    world_view = safe_edit.await_args.kwargs["view"]
    back_ids = {
        c.custom_id
        for c in world_view.children
        if isinstance(c, discord.ui.Button)
    }
    assert "explore:back_mining" in back_ids, (
        "Explore opened from the mining hub must carry a back-to-mining button"
    )


def test_world_command_root_open_has_no_back_button():
    """The !world root entry builds the hub directly (no opener attaches a back
    button) — a root panel has no parent to return to, matching !games/!community.
    """
    view = ExploreWorldHubView(_AUTHOR, 99)
    back_ids = {
        c.custom_id
        for c in view.children
        if isinstance(c, discord.ui.Button) and "back" in (c.custom_id or "")
    }
    assert back_ids == set()


@pytest.mark.asyncio
async def test_openerless_entry_shows_coming_soon():
    clear_world_entries()
    register_world_entry(
        WorldEntry(key="roam", label="Roam", emoji="🧭", description="wander", order=5),
    )
    view = ExploreWorldHubView(_AUTHOR, 99)
    btn = _find_button(view, "Roam")
    interaction = MagicMock()
    interaction.user = _AUTHOR
    interaction.guild_id = 99
    with (
        patch(
            "views.explore.world_hub.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.explore.world_hub.safe_edit",
            new_callable=AsyncMock,
        ) as safe_edit,
    ):
        await btn.callback(interaction)
    safe_edit.assert_awaited_once()
    kwargs = safe_edit.await_args.kwargs
    assert kwargs["view"] is view
    assert "coming soon" in (kwargs["embed"].title or "").lower()
