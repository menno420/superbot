"""Mining image cards render in place, not as stacking ephemeral follow-ups.

Owner report (2026-06-15, screenshots): every Inventory / Gear click sent the
PIL card as a separate ``followup.send(file=..., ephemeral=True)`` message that
piled up below the panel. These tests pin the fix: the card rides the panel's
**own** anchor message (one self-replacing message) and clears when you
navigate away, so nothing stacks.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.mining import main_panel
from views.mining.gear_panel import MiningGearView, render_gear_doll
from views.mining.main_panel import MiningHubView

_AUTHOR = SimpleNamespace(id=1, name="Digger", display_name="Digger")


def _button(view: discord.ui.View, *, custom_id=None, label=None):
    for child in view.children:
        if custom_id is not None and getattr(child, "custom_id", None) == custom_id:
            return child
        if label is not None and getattr(child, "label", None) == label:
            return child
    raise AssertionError(f"button not found (custom_id={custom_id!r} label={label!r})")


# --------------------------------------------------------------- render helpers


@pytest.mark.asyncio
async def test_render_gear_doll_attaches_in_place_when_pillow_available():
    embed = discord.Embed(title="Gear")
    with (
        patch(
            "views.mining.gear_panel.db.get_equipment",
            new_callable=AsyncMock,
            return_value={"weapon": "diamond sword"},
        ),
        patch("utils.character_render.render_character_for", return_value=b"PNGBYTES"),
    ):
        file = await render_gear_doll(embed, 1, 99)
    assert isinstance(file, discord.File)
    assert file.filename == "character_doll.png"
    assert embed.image.url == "attachment://character_doll.png"


@pytest.mark.asyncio
async def test_render_gear_doll_is_additive_without_pillow():
    # No Pillow → no file and no broken attachment:// reference on the embed.
    embed = discord.Embed(title="Gear")
    with (
        patch(
            "views.mining.gear_panel.db.get_equipment",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch("utils.character_render.render_character_for", return_value=None),
    ):
        file = await render_gear_doll(embed, 1, 99)
    assert file is None
    assert embed.image.url is None


def test_render_inventory_file_attaches_in_place():
    embed = discord.Embed(title="Inventory")
    with patch("utils.mining_render.render_inventory_card", return_value=b"PNG"):
        file = main_panel._render_inventory_file("Digger", {"gold": 4}, embed)
    assert isinstance(file, discord.File)
    assert file.filename == "inventory.png"
    assert embed.image.url == "attachment://inventory.png"


def test_render_inventory_file_is_additive_without_pillow():
    embed = discord.Embed(title="Inventory")
    with patch("utils.mining_render.render_inventory_card", return_value=None):
        file = main_panel._render_inventory_file("Digger", {"gold": 4}, embed)
    assert file is None
    assert embed.image.url is None


# ------------------------------------------------------- in-place edit semantics


@pytest.mark.asyncio
async def test_edit_in_place_sets_the_image():
    f = MagicMock(spec=discord.File)
    with patch(
        "views.mining.main_panel.safe_edit", new_callable=AsyncMock
    ) as safe_edit:
        await main_panel._edit_in_place(
            MagicMock(), embed=discord.Embed(), view=MagicMock(), image=f
        )
    assert safe_edit.await_args.kwargs["attachments"] == [f]


@pytest.mark.asyncio
async def test_edit_in_place_clears_the_image_by_default():
    # Every non-image action clears, so a prior card never lingers.
    with patch(
        "views.mining.main_panel.safe_edit", new_callable=AsyncMock
    ) as safe_edit:
        await main_panel._edit_in_place(
            MagicMock(), embed=discord.Embed(), view=MagicMock()
        )
    assert safe_edit.await_args.kwargs["attachments"] == []


# ------------------------------------------------------- hub button regressions


@pytest.mark.asyncio
async def test_inventory_button_renders_card_in_place_no_ephemeral_followup():
    view = MiningHubView()
    interaction = MagicMock()
    interaction.user = _AUTHOR
    interaction.guild_id = 99
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    btn = _button(view, custom_id="mining:inventory")
    with (
        patch(
            "views.mining.main_panel.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.main_panel.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"gold": 4},
        ),
        patch(
            "views.mining.main_panel._render_inventory_file",
            return_value=MagicMock(spec=discord.File),
        ),
        patch(
            "views.mining.main_panel.safe_edit", new_callable=AsyncMock
        ) as safe_edit,
    ):
        await btn.callback(interaction)
    # The card rides the in-place edit; NO separate ephemeral image message.
    interaction.followup.send.assert_not_awaited()
    assert safe_edit.await_args.kwargs["attachments"]  # the inventory card


@pytest.mark.asyncio
async def test_gear_button_renders_doll_in_place_no_ephemeral_followup():
    view = MiningHubView()
    interaction = MagicMock()
    interaction.user = _AUTHOR
    interaction.guild_id = 99
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    btn = _button(view, custom_id="mining:gear")
    with (
        patch(
            "views.mining.main_panel.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.gear_panel.build_gear_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(title="Gear"),
        ),
        patch(
            "views.mining.gear_panel.MiningGearView.create",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ),
        patch(
            "views.mining.gear_panel.render_gear_doll",
            new_callable=AsyncMock,
            return_value=MagicMock(spec=discord.File),
        ),
        patch(
            "views.mining.main_panel.safe_edit", new_callable=AsyncMock
        ) as safe_edit,
    ):
        await btn.callback(interaction)
    interaction.followup.send.assert_not_awaited()
    assert safe_edit.await_args.kwargs["attachments"]  # the paper-doll


@pytest.mark.asyncio
async def test_gear_back_button_clears_the_doll_attachment():
    view = MiningGearView(_AUTHOR, 99)
    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    btn = _button(view, label="↩ Mining Hub")
    with (
        patch(
            "views.mining.main_panel.build_overview_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(),
        ),
        patch("views.mining.main_panel.MiningHubView", return_value=MagicMock()),
    ):
        await btn.callback(interaction)
    # Returning to the hub explicitly clears the gear screen's doll.
    assert interaction.response.edit_message.await_args.kwargs["attachments"] == []
