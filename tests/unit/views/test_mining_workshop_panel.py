"""Workshop panel + hub live-overview — structure and composition tests."""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord
import pytest

from views.mining.main_panel import MiningHubView, build_overview_embed
from views.mining.workshop_panel import MiningWorkshopView, build_workshop_embed


def test_hub_has_workshop_button_with_dm_guard():
    by_id = {
        getattr(c, "custom_id", None): c
        for c in MiningHubView().children
        if isinstance(c, discord.ui.Button)
    }
    assert "mining:workshop" in by_id
    assert by_id["mining:workshop"].row == 1
    src = inspect.getsource(MiningHubView.workshop_btn)
    assert "interaction.guild_id is None" in src


def _db_patches(**overrides):
    """Patch every owner the workshop/overview builders read, with defaults."""
    values = {
        "get_mining_inventory": {"wood": 4, "pickaxe": 1},
        "get_equipment": {"tool": "pickaxe"},
        "get_gear_wear": {"pickaxe": 10},
        "get_depth": 1,
        "get_last_broken": "torch",
        "get_coins": 55,
    }
    values.update(overrides)
    return [
        patch(
            f"views.mining.workshop_panel.db.{name}",
            new_callable=AsyncMock,
            return_value=value,
        )
        for name, value in values.items()
    ]


@pytest.mark.asyncio
async def test_workshop_embed_shows_condition_repair_and_craftables():
    patches = _db_patches()
    for p in patches:
        p.start()
    try:
        embed = await build_workshop_embed(1, 7)
    finally:
        for p in patches:
            p.stop()
    blob = " ".join(f"{f.name} {f.value}" for f in embed.fields)
    assert "Pickaxe" in blob
    assert "10/60" in blob  # worn durability bar
    assert "repair" in blob.lower()
    assert "Torch" in blob  # last broken banner
    assert "55" in (embed.footer.text or "")  # balance


@pytest.mark.asyncio
async def test_workshop_view_builds_selects_and_quick_craft_state():
    patches = _db_patches()
    for p in patches:
        p.start()
    try:
        view = await MiningWorkshopView.create(SimpleNamespace(id=1), 7)
    finally:
        for p in patches:
            p.stop()
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 2  # repair (worn pickaxe) + craft (gear recipes)
    quick = next(
        b
        for b in view.children
        if isinstance(b, discord.ui.Button) and "Quick-craft" in (b.label or "")
    )
    assert quick.disabled is False  # last_broken set → enabled


@pytest.mark.asyncio
async def test_workshop_view_disables_quick_craft_without_marker():
    patches = _db_patches(get_last_broken=None, get_gear_wear={})
    for p in patches:
        p.start()
    try:
        view = await MiningWorkshopView.create(SimpleNamespace(id=1), 7)
    finally:
        for p in patches:
            p.stop()
    quick = next(
        b
        for b in view.children
        if isinstance(b, discord.ui.Button) and "Quick-craft" in (b.label or "")
    )
    assert quick.disabled is True
    # No worn gear → no repair select.
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1


@pytest.mark.asyncio
async def test_overview_embed_composes_location_gear_and_wealth():
    values = {
        "get_mining_inventory": {"diamond": 2},
        "get_equipment": {"tool": "pickaxe", "light": "torch"},
        "get_gear_wear": {"pickaxe": 30},
        "get_depth": 1,
        "get_last_broken": "lantern",
    }
    patches = [
        patch(
            f"views.mining.main_panel.db.{name}",
            new_callable=AsyncMock,
            return_value=value,
        )
        for name, value in values.items()
    ]
    for p in patches:
        p.start()
    try:
        embed = await build_overview_embed(1, 7, name="Digger")
    finally:
        for p in patches:
            p.stop()
    assert "Digger" in (embed.title or "")
    blob = " ".join(f"{f.name} {f.value}" for f in embed.fields)
    assert "Cavern" in blob  # depth 1
    assert "30/60" in blob  # tool durability
    assert "40/40" in blob  # unworn torch at full durability
    assert "24" in blob  # net worth (diamond 12 × 2)
    assert "lantern" in blob  # broken-gear hint
    # The action guide stays in the description (the hub still routes).
    assert "Workshop" in (embed.description or "")
