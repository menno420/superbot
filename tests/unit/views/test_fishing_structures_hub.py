"""Fishing structures sub-hub — the 🏗 Structures child of the fishing menu.

Pins that the two coral structures (🪸 Tide Pool + ⚓ Dock) are reached through one
sub-hub button (so the menu stays lean), that the sub-hub routes into each panel,
and that the panels' ↩ back button returns to the sub-hub — a clean menu →
structures → panel hierarchy. Discord I/O is mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.mining import structures as struct
from views.fishing import (
    FishingMenuView,
    StructuresView,
    build_structures_embed,
)
from views.fishing.boathouse import BoathouseView
from views.fishing.dock import DockView
from views.fishing.fishery import FisheryView
from views.fishing.structures_hub import open_structures_hub
from views.fishing.tide_pool import TidePoolView


def _author(user_id: int = 1) -> MagicMock:
    author = MagicMock()
    author.id = user_id
    author.display_name = "Anya"
    return author


def _interaction(user_id: int = 1) -> MagicMock:
    interaction = MagicMock()
    interaction.user = _author(user_id)
    interaction.message = MagicMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


def _click(view, name: str, interaction: MagicMock):
    return getattr(type(view), name)(view, interaction, MagicMock())


def _hub() -> StructuresView:
    return StructuresView(_author(), guild_id=99)


# ---------------------------------------------------------------------------
# The menu now routes to the sub-hub with one button, not two
# ---------------------------------------------------------------------------


def test_menu_replaces_the_two_structure_buttons_with_one_structures_button():
    view = FishingMenuView(_author(), guild_id=99)
    labels = [getattr(c, "label", "") or "" for c in view.children]
    assert "Structures" in labels
    # The individual structure buttons no longer clutter the menu.
    assert "Tide Pool" not in labels
    assert "Dock" not in labels


def test_menu_embed_advertises_the_structures_child():
    from views.fishing.menu import build_menu_embed

    assert "Structures" in build_menu_embed().description


@pytest.mark.asyncio
async def test_menu_structures_button_opens_the_sub_hub():
    view = FishingMenuView(_author(), guild_id=99)
    interaction = _interaction()
    with patch(
        "views.fishing.structures_hub.db.get_structures",
        AsyncMock(return_value={}),
    ):
        await _click(view, "structures_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], StructuresView)


# ---------------------------------------------------------------------------
# The sub-hub embed + routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_structures_embed_shows_both_structures_at_a_glance():
    with patch(
        "views.fishing.structures_hub.db.get_structures",
        AsyncMock(return_value={struct.TIDE_POOL: 1}),
    ):
        embed = await build_structures_embed(1, 99)
    field_names = [f.name for f in embed.fields]
    assert any("Tide Pool" in n for n in field_names)
    assert any("Dock" in n for n in field_names)
    assert any("Boathouse" in n for n in field_names)
    assert any("Fishery" in n for n in field_names)
    # A built Tide Pool shows its live bonus; an unbuilt Dock/Boathouse read
    # "not built yet".
    body = "\n".join(f.value for f in embed.fields)
    assert "pull toward rarer fish" in body
    assert "not built yet" in body


@pytest.mark.asyncio
async def test_structures_embed_shows_the_boathouse_regen_bonus_when_built():
    with patch(
        "views.fishing.structures_hub.db.get_structures",
        AsyncMock(return_value={struct.BOATHOUSE: 2}),
    ):
        embed = await build_structures_embed(1, 99)
    body = "\n".join(f.value for f in embed.fields)
    assert "faster energy regen" in body


@pytest.mark.asyncio
async def test_structures_embed_shows_the_fishery_double_catch_bonus_when_built():
    with patch(
        "views.fishing.structures_hub.db.get_structures",
        AsyncMock(return_value={struct.FISHERY: 2}),
    ):
        embed = await build_structures_embed(1, 99)
    body = "\n".join(f.value for f in embed.fields)
    assert "double-catch chance" in body


@pytest.mark.asyncio
async def test_sub_hub_tide_pool_button_opens_the_tide_pool_panel():
    view = _hub()
    interaction = _interaction()
    with patch(
        "views.fishing.tide_pool.db.get_structures",
        AsyncMock(return_value={}),
    ):
        await _click(view, "tide_pool_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], TidePoolView)


@pytest.mark.asyncio
async def test_sub_hub_dock_button_opens_the_dock_panel():
    view = _hub()
    interaction = _interaction()
    with patch(
        "views.fishing.dock.db.get_structures",
        AsyncMock(return_value={}),
    ):
        await _click(view, "dock_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], DockView)


@pytest.mark.asyncio
async def test_sub_hub_boathouse_button_opens_the_boathouse_panel():
    view = _hub()
    interaction = _interaction()
    with patch(
        "views.fishing.boathouse.db.get_structures",
        AsyncMock(return_value={}),
    ):
        await _click(view, "boathouse_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], BoathouseView)


@pytest.mark.asyncio
async def test_sub_hub_fishery_button_opens_the_fishery_panel():
    view = _hub()
    interaction = _interaction()
    with patch(
        "views.fishing.fishery.db.get_structures",
        AsyncMock(return_value={}),
    ):
        await _click(view, "fishery_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], FisheryView)


@pytest.mark.asyncio
async def test_sub_hub_back_button_rebuilds_the_fishing_menu():
    view = _hub()
    interaction = _interaction()
    with (
        patch(
            "views.fishing.menu.fishing_workflow.get_energy",
            AsyncMock(return_value=9),
        ),
        patch(
            "views.fishing.menu.fishing_workflow.get_venue",
            AsyncMock(return_value=None),
        ),
    ):
        await _click(view, "back_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], FishingMenuView)


def test_sub_hub_declares_the_fishing_subsystem_for_standard_nav():
    # SUBSYSTEM = "fishing" makes attach_standard_nav add 📚 Help + ↩ Games so the
    # sub-hub is never a dead-end (the 2026-06-23 never-stranded directive).
    assert StructuresView.SUBSYSTEM == "fishing"
    view = _hub()
    labels = [getattr(c, "label", "") or "" for c in view.children]
    assert any("Help" in lbl for lbl in labels)
    assert any("Games" in lbl for lbl in labels)


# ---------------------------------------------------------------------------
# The structure panels' back button now returns to the sub-hub, not the menu
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tide_pool_back_button_returns_to_the_structures_sub_hub():
    view = TidePoolView(_author(), guild_id=99)
    interaction = _interaction()
    with patch(
        "views.fishing.structures_hub.db.get_structures",
        AsyncMock(return_value={}),
    ):
        await _click(view, "back_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], StructuresView)


@pytest.mark.asyncio
async def test_dock_back_button_returns_to_the_structures_sub_hub():
    view = DockView(_author(), guild_id=99)
    interaction = _interaction()
    with patch(
        "views.fishing.structures_hub.db.get_structures",
        AsyncMock(return_value={}),
    ):
        await _click(view, "back_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], StructuresView)


@pytest.mark.asyncio
async def test_boathouse_back_button_returns_to_the_structures_sub_hub():
    view = BoathouseView(_author(), guild_id=99)
    interaction = _interaction()
    with patch(
        "views.fishing.structures_hub.db.get_structures",
        AsyncMock(return_value={}),
    ):
        await _click(view, "back_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], StructuresView)


@pytest.mark.asyncio
async def test_fishery_back_button_returns_to_the_structures_sub_hub():
    view = FisheryView(_author(), guild_id=99)
    interaction = _interaction()
    with patch(
        "views.fishing.structures_hub.db.get_structures",
        AsyncMock(return_value={}),
    ):
        await _click(view, "back_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], StructuresView)


@pytest.mark.asyncio
async def test_open_structures_hub_rebuilds_a_navigable_sub_hub():
    interaction = _interaction()
    with patch(
        "views.fishing.structures_hub.db.get_structures",
        AsyncMock(return_value={}),
    ):
        await open_structures_hub(interaction, _author(), guild_id=99)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], StructuresView)
