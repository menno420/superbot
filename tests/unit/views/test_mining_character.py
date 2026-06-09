"""Read-only Character overview aggregates position, gear, coins, net worth."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from views.mining.character_panel import build_character_embed
from views.mining.main_panel import MiningHubView


def test_hub_has_character_button():
    ids = {getattr(c, "custom_id", None) for c in MiningHubView().children}
    assert "mining:character" in ids


@pytest.mark.asyncio
async def test_build_character_embed_aggregates_every_owner():
    with patch(
        "views.mining.character_panel.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"diamond": 2},
    ), patch(
        "views.mining.character_panel.db.get_equipment",
        new_callable=AsyncMock,
        return_value={"tool": "iron pickaxe", "weapon": "iron sword"},
    ), patch(
        "views.mining.character_panel.db.get_gear_wear",
        new_callable=AsyncMock,
        return_value={"iron pickaxe": 42},
    ), patch(
        "views.mining.character_panel.db.get_depth",
        new_callable=AsyncMock,
        return_value=2,
    ), patch(
        "views.mining.character_panel.db.get_coins",
        new_callable=AsyncMock,
        return_value=150,
    ):
        embed = await build_character_embed(123, 7, name="Digger")

    blob = embed.title + " " + " ".join(f"{f.name} {f.value}" for f in embed.fields)
    assert "Digger" in embed.title
    assert "Deep" in blob  # depth 2 → the Deep (world.describe_position)
    assert "Iron Pickaxe" in blob  # equipped tool
    assert "Iron Sword" in blob  # equipped weapon
    assert "+4" in blob  # iron pickaxe mining_power
    assert "+6" in blob  # iron sword damage
    assert "150" in blob  # coins
    assert "24" in blob  # net worth = diamond value (12) × 2
