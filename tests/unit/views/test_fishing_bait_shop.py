"""fishing bait shop — the buy + craft panel, incl. the pearl craft path (#1518).

Pins that ``build_bait_embed`` surfaces the three earn paths (buy with coins,
craft from fish, craft the premium bait from pearls) and that the panel wires a
select for each. Discord I/O is not exercised here — these are pure-render/wiring
assertions.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from utils.fishing import bait as bait_mod
from views.fishing.bait_shop import (
    BaitShopView,
    _BaitCraftSelect,
    _BaitSelect,
    _PearlCraftSelect,
    build_bait_embed,
)

_FEAST = bait_mod.bait_by_key("feast")
_FEAST_PEARLS = bait_mod.pearl_recipe("feast")


def _author(user_id: int = 1):
    class _A:
        id = user_id

    return _A()


def test_embed_shows_the_pearl_recipe_and_count():
    embed = build_bait_embed(None, 0, balance=500, pearls=7)
    blob = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    # the premium bait's pearl cost is advertised, with the player's pearl count
    assert bait_mod.pearl_recipe_text(_FEAST_PEARLS) in blob
    assert "you have 7" in blob.lower()
    assert _FEAST.name in blob


def test_embed_defaults_to_zero_pearls():
    embed = build_bait_embed(None, 0, balance=0)
    blob = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "you have 0" in blob.lower()


def test_pearl_craft_select_lists_only_pearl_recipes():
    select = _PearlCraftSelect()
    values = {opt.value for opt in select.options}
    assert values == set(bait_mod.PEARL_CRAFTABLE_KEYS)
    # the premium combo (no fish recipe) is the pearl path; never a fish-craftable one
    assert values.isdisjoint(bait_mod.CRAFTABLE_KEYS)


def test_panel_wires_buy_fish_craft_and_pearl_craft_selects():
    view = BaitShopView(_author(), guild_id=1)
    kinds = {type(item) for item in view.children}
    assert {_BaitSelect, _BaitCraftSelect, _PearlCraftSelect} <= kinds


def test_embed_is_a_discord_embed():
    assert isinstance(build_bait_embed(None, 0, 0, pearls=1), discord.Embed)


@pytest.mark.asyncio
async def test_back_button_returns_to_the_fishing_menu():
    # The menu self.stop()s when it opens the shop, so the back button must mint
    # a fresh, fully-navigable FishingMenuView (punch-list #1, the trapped-view fix).
    from views.fishing.menu import FishingMenuView

    author = MagicMock()
    author.id = 7
    view = BaitShopView(author, guild_id=99)
    interaction = MagicMock()
    interaction.message = MagicMock()
    interaction.response.edit_message = AsyncMock()
    with (
        patch(
            "views.fishing.menu.fishing_workflow.get_energy",
            AsyncMock(return_value=5),
        ),
        patch(
            "views.fishing.menu.fishing_workflow.get_venue",
            AsyncMock(return_value=None),
        ),
    ):
        await type(view).back_btn(view, interaction, MagicMock())

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], FishingMenuView)
    assert view.is_finished()
