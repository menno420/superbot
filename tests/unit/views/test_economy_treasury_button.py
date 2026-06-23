"""Economy → Treasury button: panel-link + back-nav guards.

The treasury subsystem shipped (#1334) registered as an Economy `primary_child`
with a `build_help_menu_view` hook, but the Economy hub panel hardcodes its
buttons (it does not render `primary_children` dynamically like the Games hub),
so treasury had no clickable entry — reachable only by typing `!treasury` /
`!help treasury`. This adds the `economy:treasury` button; these tests pin that
it (a) edits in place rather than spawning a detached panel, and (b) opens a
treasury view carrying the `economy:back` control so the user can return.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.economy.main_panel import EconomyPanelView


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = id_
    author.display_name = "tester"
    author.display_avatar = MagicMock(url="https://example/avatar.png")
    author.mention = f"<@{id_}>"
    return author


def _treasury_btn(view: EconomyPanelView):
    return next(
        c for c in view.children if getattr(c, "custom_id", "") == "economy:treasury"
    )


@pytest.mark.asyncio
async def test_economy_panel_has_treasury_button():
    """Regression: the Economy panel must expose a clickable Treasury button."""
    ids = [getattr(c, "custom_id", None) for c in EconomyPanelView().children]
    assert "economy:treasury" in ids, f"no treasury button on Economy panel; got {ids}"


@pytest.mark.asyncio
async def test_treasury_btn_edits_in_place_not_new_message():
    """The Treasury button edits the current message — never a detached panel."""
    btn = _treasury_btn(EconomyPanelView())

    interaction = MagicMock()
    interaction.user = _author(7)
    interaction.guild_id = 99
    interaction.message = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()  # must NOT be called

    with patch(
        "services.treasury_service.get_balance",
        new_callable=AsyncMock,
        return_value=500,
    ), patch(
        "utils.db.get_coins",
        new_callable=AsyncMock,
        return_value=300,
    ), patch(
        "views.economy.main_panel.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "views.economy.main_panel.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)

    interaction.response.send_message.assert_not_called()
    edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_treasury_btn_attaches_back_to_economy_button():
    """The treasury view opened from Economy must carry `economy:back`."""
    btn = _treasury_btn(EconomyPanelView())

    interaction = MagicMock()
    interaction.user = _author(7)
    interaction.guild_id = 99
    interaction.message = MagicMock()

    captured: dict = {}

    async def _fake_edit(_i, *, embed=None, view=None):
        captured["view"] = view
        return True

    with patch(
        "services.treasury_service.get_balance",
        new_callable=AsyncMock,
        return_value=500,
    ), patch(
        "utils.db.get_coins",
        new_callable=AsyncMock,
        return_value=300,
    ), patch(
        "views.economy.main_panel.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "views.economy.main_panel.safe_edit",
        side_effect=_fake_edit,
    ):
        await btn.callback(interaction)

    treasury_view = captured["view"]
    assert treasury_view is not None
    back_ids = [getattr(c, "custom_id", None) for c in treasury_view.children]
    assert "economy:back" in back_ids, (
        f"Treasury-from-Economy must carry economy:back; got {back_ids}"
    )
