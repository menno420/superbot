"""fishing menu — the interactive hub panel (owner-reported "no buttons" fix).

Pins that the fishing menu reached via the Help hub is a real buttoned panel: the
Cast button launches the minigame in place, Rod swaps to the rod shop, and Fishdex
renders the collection while keeping the menu. Discord I/O is mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import fishing_workflow
from utils.fishing.fish import Catch, FishSpecies
from views.fishing import FishingMenuView, build_fishlog_embed, build_menu_embed
from views.fishing.cast_view import FishingCastView
from views.fishing.rod_shop import RodShopView

_CAST = fishing_workflow.Cast(
    catch=Catch(species=FishSpecies("minnow", 2, "🐟")),
    level_before=7,
)


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
    interaction.response.send_message = AsyncMock()
    return interaction


def _click(view: FishingMenuView, name: str, interaction: MagicMock):
    return getattr(type(view), name)(view, interaction, MagicMock())


def _menu() -> FishingMenuView:
    return FishingMenuView(_author(), guild_id=99)


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def test_menu_embed_advertises_the_actions():
    text = build_menu_embed().description
    assert "Cast" in text and "Rod" in text and "Fishdex" in text


def test_menu_embed_shows_todays_forecast():
    # The daily weather is surfaced as a field so the menu is a reason to fish today.
    field_names = [f.name for f in build_menu_embed().fields]
    assert any("forecast" in n.lower() for n in field_names)


def test_fishlog_embed_counts_only_known_species():
    log = {"minnow": 3, "golden koi": 99}  # the koi is a legacy/unknown row
    embed = build_fishlog_embed("Anya", log, level=7)
    # 1 of the 32-species catalogue (21 shore + 11 deepwater) discovered, 3 total
    # — the legacy koi is ignored, no impossible progress.
    assert "1/32" in embed.description
    assert "**3** total" in embed.description
    # Both venue sections render (the Q-0175 §5 split).
    field_names = [f.name for f in embed.fields]
    assert any("Shore" in n for n in field_names)
    assert any("Deepwater" in n for n in field_names)


def test_fishlog_embed_shows_the_personal_best_weight():
    log = {"minnow": 5}
    records = {"minnow": 2.4}
    embed = build_fishlog_embed("Anya", log, level=7, records=records)
    body = "\n".join(f.value for f in embed.fields)
    assert "2.4kg" in body  # the trophy record renders beside the tally


def test_fishlog_embed_omits_the_trophy_when_no_record():
    log = {"minnow": 5}
    embed = build_fishlog_embed("Anya", log, level=7)  # no records given
    body = "\n".join(f.value for f in embed.fields)
    assert "kg" not in body  # a caught species with no recorded best shows no trophy


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cast_button_launches_the_minigame_in_place():
    view = _menu()
    interaction = _interaction()
    with (
        patch(
            "views.fishing.menu.prepare_cast",
            AsyncMock(return_value=(MagicMock(), MagicMock(spec=FishingCastView))),
        ) as prep,
    ):
        embed, cast_view = prep.return_value
        await _click(view, "cast_btn", interaction)

    prep.assert_awaited_once_with(1, 99)
    interaction.response.edit_message.assert_awaited_once()  # took over the panel
    cast_view.start.assert_called_once()  # the bite task was spawned


@pytest.mark.asyncio
async def test_cast_button_surfaces_the_busy_message_ephemerally():
    view = _menu()
    interaction = _interaction()
    with patch(
        "views.fishing.menu.prepare_cast",
        AsyncMock(return_value="🎣 You've already got a line in the water…"),
    ):
        await _click(view, "cast_btn", interaction)

    # a string result → an ephemeral nudge, no panel takeover
    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.await_args.kwargs.get("ephemeral") is True
    interaction.response.edit_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_sail_button_toggles_the_venue_and_keeps_the_menu():
    from utils.fishing import venue as venue_mod

    view = _menu()
    interaction = _interaction()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    change = fishing_workflow.VenueChange(
        venue="deepwater",
        message="⛵ You set sail for deepwater.",
    )
    with (
        patch(
            "views.fishing.menu.fishing_workflow.toggle_venue",
            AsyncMock(return_value=change),
        ) as toggle,
        patch(
            "views.fishing.menu.fishing_workflow.get_energy",
            AsyncMock(return_value=42),
        ),
    ):
        await _click(view, "sail_btn", interaction)

    toggle.assert_awaited_once_with(1, 99)
    # The panel stays (re-rendered with the new venue) — same view object back.
    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert kwargs["view"] is view
    assert venue_mod.DEEPWATER_PROFILE.name in kwargs["embed"].fields[0].value
    # ...and the player gets an ephemeral confirmation of the toggle.
    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.await_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_rod_button_swaps_to_the_rod_shop():
    view = _menu()
    interaction = _interaction()
    with (
        patch("views.fishing.menu.db.get_rod_tier", AsyncMock(return_value=1)),
        patch("views.fishing.menu.db.get_coins", AsyncMock(return_value=500)),
    ):
        await _click(view, "rod_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], RodShopView)  # the panel became the rod shop


@pytest.mark.asyncio
async def test_fishdex_button_renders_the_collection_and_keeps_the_menu():
    view = _menu()
    interaction = _interaction()
    with (
        patch("views.fishing.menu.db.get_fishing_log", AsyncMock(return_value={})),
        patch("views.fishing.menu.db.get_fishing_records", AsyncMock(return_value={})),
        patch("views.fishing.menu.db.get_game_xp", AsyncMock(return_value={})),
    ):
        await _click(view, "fishdex_btn", interaction)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert kwargs["view"] is view  # the menu stays so you can act again


def test_menu_declares_the_fishing_subsystem_for_standard_nav():
    # SUBSYSTEM = "fishing" makes attach_standard_nav add 📚 Help + ↩ Games so the
    # menu is never a dead-end (the 2026-06-23 never-stranded directive).
    assert FishingMenuView.SUBSYSTEM == "fishing"
    view = _menu()
    labels = [getattr(c, "label", "") or "" for c in view.children]
    assert any("Help" in lbl for lbl in labels)
    assert any("Games" in lbl for lbl in labels)


@pytest.mark.asyncio
async def test_rules_button_sends_an_ephemeral_how_to_card():
    view = _menu()
    interaction = _interaction()
    await _click(view, "rules_btn", interaction)
    interaction.response.send_message.assert_awaited_once()
    _, kwargs = interaction.response.send_message.await_args
    assert kwargs.get("ephemeral") is True
    assert "How to fish" in kwargs["embed"].title


@pytest.mark.asyncio
async def test_open_fishing_menu_rebuilds_a_navigable_menu():
    from views.fishing.menu import open_fishing_menu

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
        await open_fishing_menu(interaction, _author(), guild_id=99)

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], FishingMenuView)
