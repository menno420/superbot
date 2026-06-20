"""Character sub-hub — structure, embed, and that it groups the moved actions.

Option A declutter (owner-directed, 2026-06-15;
``docs/planning/mining-hub-redesign-2026-06-15.md``): the Character sub-hub
absorbs Overview / Inventory / Stats / Skills / Vault / Home off the main hub.
Home placement here is the 2026-06-19 deviation (it personalizes the Character
card). These tests pin the sub-hub shape and the in-place rendering contract.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.mining.character_hub import (
    MiningCharacterHubView,
    build_character_hub_embed,
)

_AUTHOR = SimpleNamespace(id=1, name="Digger", display_name="Digger")


def _find_button(view: discord.ui.View, label_substr: str) -> discord.ui.Button:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and label_substr in (child.label or ""):
            return child
    raise AssertionError(f"No button with label containing {label_substr!r}")


def test_hub_embed_lists_the_character_actions():
    embed = build_character_hub_embed()
    assert "Character" in (embed.title or "")
    blob = embed.description or ""
    for token in ("Overview", "Inventory", "Stats", "Skills", "Vault", "Home"):
        assert token in blob, f"missing {token!r} from the Character hub guide"


def test_hub_has_all_six_actions_plus_back():
    view = MiningCharacterHubView(_AUTHOR, 99)
    labels = " | ".join(
        b.label or "" for b in view.children if isinstance(b, discord.ui.Button)
    )
    for token in (
        "Overview",
        "Inventory",
        "Stats",
        "Skills",
        "Vault",
        "Home",
        "Mining Hub",
    ):
        assert token in labels, f"missing {token!r} button"


def test_hub_constructor_matches_workshop_template():
    # Same (author, guild_id) shape as MiningWorkshopHubView (the template).
    view = MiningCharacterHubView(_AUTHOR, 77)
    assert view.guild_id == 77
    assert view._author is _AUTHOR


@pytest.mark.asyncio
async def test_overview_button_shows_character_embed_in_place():
    view = MiningCharacterHubView(_AUTHOR, 99)
    btn = _find_button(view, "Overview")
    interaction = MagicMock()
    interaction.user = _AUTHOR
    interaction.guild_id = 99
    with (
        patch(
            "views.mining.character_hub.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.character_panel.build_character_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(title="🧍 Digger"),
        ),
        patch(
            "views.mining.character_panel.build_character_doll",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "views.mining.character_hub.safe_edit", new_callable=AsyncMock,
        ) as safe_edit,
    ):
        await btn.callback(interaction)
    safe_edit.assert_awaited_once()
    assert safe_edit.await_args.kwargs["view"] is view  # stays on the sub-hub


@pytest.mark.asyncio
async def test_stats_button_shows_stats_in_place():
    view = MiningCharacterHubView(_AUTHOR, 99)
    btn = _find_button(view, "Stats")
    interaction = MagicMock()
    interaction.user = _AUTHOR
    interaction.guild_id = 99
    with (
        patch(
            "views.mining.character_hub.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.character_hub.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"gold": 3, "stone": 2},
        ),
        patch(
            "views.mining.character_hub.safe_edit", new_callable=AsyncMock,
        ) as safe_edit,
    ):
        await btn.callback(interaction)
    embed = safe_edit.await_args.kwargs["embed"]
    blob = " ".join(f"{f.name} {f.value}" for f in embed.fields)
    assert "5" in blob  # total items collected (3 + 2)
    assert "2" in blob  # unique items


@pytest.mark.asyncio
async def test_back_button_returns_to_main_hub():
    view = MiningCharacterHubView(_AUTHOR, 99)
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


@pytest.mark.asyncio
async def test_skills_and_vault_open_their_panels_in_place():
    view = MiningCharacterHubView(_AUTHOR, 99)
    for label, mod, view_cls, embed_fn in (
        ("Skills", "skills_panel", "MiningSkillsView", "build_skills_embed"),
        ("Vault", "vault_panel", "MiningVaultView", "build_vault_embed"),
    ):
        btn = _find_button(view, label)
        interaction = MagicMock()
        interaction.user = _AUTHOR
        interaction.guild_id = 99
        with (
            patch(
                "views.mining.character_hub.safe_defer",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                f"views.mining.{mod}.{embed_fn}",
                new_callable=AsyncMock,
                return_value=discord.Embed(title=label),
            ),
            patch(f"views.mining.{mod}.{view_cls}", return_value=MagicMock()),
            patch(
                "views.mining.character_hub.safe_edit", new_callable=AsyncMock,
            ) as safe_edit,
        ):
            await btn.callback(interaction)
        safe_edit.assert_awaited_once()
