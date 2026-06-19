"""Explore sub-hub — the open-world explorer STUB.

Option A declutter (owner-directed, 2026-06-15;
``docs/planning/mining-hub-redesign-2026-06-15.md``): the main hub's new
``🗺️ Explore`` button opens this open-world sub-hub. It is a *stub* — Fishing /
Roam / Quests show a "coming soon" message and are deliberately NOT wired into
any fishing module. (Distinct from the old depth-tied mining-explore event,
which folded into the Mine action.) These tests pin the stub contract.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.mining.explore_hub import (
    MiningExploreHubView,
    build_explore_hub_embed,
)

_AUTHOR = SimpleNamespace(id=1, name="Digger", display_name="Digger")


def _find_button(view: discord.ui.View, label_substr: str) -> discord.ui.Button:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and label_substr in (child.label or ""):
            return child
    raise AssertionError(f"No button with label containing {label_substr!r}")


def test_hub_embed_marks_it_as_early():
    embed = build_explore_hub_embed()
    assert "Explore" in (embed.title or "")
    desc = (embed.description or "").lower()
    assert "early" in desc or "coming soon" in desc


def test_hub_has_the_three_stub_activities_plus_back():
    view = MiningExploreHubView(_AUTHOR, 99)
    labels = " | ".join(
        b.label or "" for b in view.children if isinstance(b, discord.ui.Button)
    )
    for token in ("Fishing", "Roam", "Quests", "Mining Hub"):
        assert token in labels, f"missing {token!r} button"


def test_hub_constructor_matches_workshop_template():
    view = MiningExploreHubView(_AUTHOR, 55)
    assert view.guild_id == 55
    assert view._author is _AUTHOR


def test_stub_does_not_import_fishing_modules():
    # Pure stub: no wiring into fishing v1 or any out-of-lane module. The only
    # imports in the callbacks are the in-place helpers + the main-hub back nav.
    src = inspect.getsource(MiningExploreHubView)
    assert "from views.mining.fishing" not in src
    assert "import fishing" not in src
    assert "fishing_workflow" not in src


@pytest.mark.asyncio
async def test_each_activity_shows_coming_soon_in_place():
    view = MiningExploreHubView(_AUTHOR, 99)
    for label in ("Fishing", "Roam", "Quests"):
        btn = _find_button(view, label)
        interaction = MagicMock()
        interaction.user = _AUTHOR
        interaction.guild_id = 99
        with (
            patch(
                "views.mining.explore_hub.safe_defer",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "views.mining.explore_hub.safe_edit", new_callable=AsyncMock,
            ) as safe_edit,
        ):
            await btn.callback(interaction)
        safe_edit.assert_awaited_once()
        kwargs = safe_edit.await_args.kwargs
        assert kwargs["view"] is view  # stays on the stub hub
        embed = kwargs["embed"]
        assert "coming soon" in (embed.title or "").lower()


@pytest.mark.asyncio
async def test_back_button_returns_to_main_hub():
    view = MiningExploreHubView(_AUTHOR, 99)
    btn = _find_button(view, "Mining Hub")
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    with patch(
        "views.mining.main_panel.build_overview_embed",
        new_callable=AsyncMock,
        return_value=discord.Embed(title="⛏️ Mining Hub"),
    ):
        await btn.callback(interaction)
    interaction.response.edit_message.assert_awaited_once()
    swapped = interaction.response.edit_message.await_args.kwargs["view"]
    assert type(swapped).__name__ == "MiningHubView"
