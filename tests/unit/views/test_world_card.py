"""Unit tests for the cross-game world card (Explore spine PR 3).

Pins:
* the card renders the global level + per-game standings from ``world_identity``,
* a player with no game XP gets an honest empty state (not a wall of zeros),
* a DM (no guild) says progress is per-server rather than rendering blank,
* the card is read-only — it imports no mutation surface (the PR-A profile-card
  property, applied to the federated identity card).
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from services.game_xp_service import GameStanding, WorldIdentity
from views.explore.world_card import _progress_bar, build_world_card_embed

_USER = SimpleNamespace(
    id=7,
    display_name="Wanderer",
    display_avatar=SimpleNamespace(url="http://avatar"),
)


def test_progress_bar_clamps_and_guards_zero_denominator():
    assert _progress_bar(0, 100) == "░" * 10
    assert _progress_bar(50, 100) == "█" * 5 + "░" * 5
    assert _progress_bar(100, 100) == "█" * 10
    assert _progress_bar(999, 100) == "█" * 10  # clamps, never overflows
    assert _progress_bar(5, 0) == "█" * 10  # full when nothing more is needed


@pytest.mark.asyncio
async def test_card_renders_global_and_per_game():
    identity = WorldIdentity(
        global_level=2,
        global_into=40,
        global_needed=160,
        global_total=300,
        per_game=(
            GameStanding(game="mining", level=2, xp=250),
            GameStanding(game="fishing", level=0, xp=50),
        ),
    )
    with patch(
        "views.explore.world_card.game_xp_service.world_identity",
        new_callable=AsyncMock,
        return_value=identity,
    ):
        embed = await build_world_card_embed(_USER, 99)
    blob = (embed.title or "") + " ".join(f"{f.name} {f.value}" for f in embed.fields)
    assert "World level — 2" in blob
    assert "300" in blob  # total XP
    assert "Mining" in blob and "Fishing" in blob
    assert "250" in blob  # mining's own xp


@pytest.mark.asyncio
async def test_card_empty_state_when_no_progress():
    identity = WorldIdentity(
        global_level=0,
        global_into=0,
        global_needed=100,
        global_total=0,
        per_game=(),
    )
    with patch(
        "views.explore.world_card.game_xp_service.world_identity",
        new_callable=AsyncMock,
        return_value=identity,
    ):
        embed = await build_world_card_embed(_USER, 99)
    blob = " ".join(f.value for f in embed.fields)
    assert "not earned any game XP" in blob
    assert "!world" in blob


@pytest.mark.asyncio
async def test_card_in_dm_says_per_server():
    # No world_identity call at all when guild_id is None (no scope to read).
    with patch(
        "views.explore.world_card.game_xp_service.world_identity",
        new_callable=AsyncMock,
    ) as identity:
        embed = await build_world_card_embed(_USER, None)
    identity.assert_not_awaited()
    blob = " ".join(f.value for f in embed.fields)
    assert "per server" in blob


def test_world_card_module_is_read_only():
    """No mutation/pipeline/economy import — the card only reads (Q-0080)."""
    src = Path("disbot/views/explore/world_card.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
    banned = ("mutation", "_pipeline", "economy_service")
    offenders = [m for m in imported if any(b in m for b in banned)]
    assert not offenders, f"world card must stay read-only; found {offenders}"
