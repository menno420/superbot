"""Regression tests for PR #1 — Economy → Inventory navigation lifecycle.

Before PR #1 the Economy Inventory button created a *detached* panel
message via ``interaction.response.send_message(view=...)``, violating
the "one active menu message that edits in place" rule and leaving the
user with two Economy-related messages on screen with no Back path.

These tests pin the post-PR-#1 contract:

* ``EconomyPanelView.inventory_btn`` defers, then edits the current
  message in place. It does NOT call ``send_message``.
* The Inventory view it opens carries a ``custom_id="economy:back"``
  button (the new ``attach_back_to_economy_button`` helper).
* The standalone ``!inventory`` command path still creates a fresh
  menu message via the cog's existing ``send_panel`` entry — it is a
  command entry point, not panel navigation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.economy.main_panel import EconomyPanelView, attach_back_to_economy_button


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = id_
    author.display_name = "tester"
    author.display_avatar = MagicMock(url="https://example/avatar.png")
    author.mention = f"<@{id_}>"
    return author


# ---------------------------------------------------------------------------
# inventory_btn edits, does not send_message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inventory_btn_does_not_send_new_message():
    """The Economy Inventory button must edit the current menu message,
    never create a detached panel via ``send_message``. This is the
    primary regression guard for Bug #1.
    """
    view = EconomyPanelView()
    btn = next(c for c in view.children if getattr(c, "custom_id", "") == "economy:inventory")

    interaction = MagicMock()
    interaction.user = _author()
    interaction.user.id = 7
    interaction.guild_id = 99
    interaction.message = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()  # If called, test should fail.
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.original_response = AsyncMock(return_value=MagicMock())

    with patch(
        "cogs.inventory_cog._build_combined_inventory",
        new_callable=AsyncMock,
        return_value={},
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

    # The bug was send_message with a view attached; assert it never happens.
    interaction.response.send_message.assert_not_called()
    # And edit must have been called with the new inventory view.
    edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_inventory_btn_attaches_back_to_economy_button():
    """The Inventory view opened from Economy must carry the
    ``custom_id="economy:back"`` button so the user can return.
    """
    view = EconomyPanelView()
    btn = next(c for c in view.children if getattr(c, "custom_id", "") == "economy:inventory")

    interaction = MagicMock()
    interaction.user = _author()
    interaction.user.id = 7
    interaction.guild_id = 99
    interaction.message = MagicMock()

    captured: dict = {}

    async def _fake_edit(_i, *, embed=None, view=None):
        captured["embed"] = embed
        captured["view"] = view
        return True

    with patch(
        "cogs.inventory_cog._build_combined_inventory",
        new_callable=AsyncMock,
        return_value={},
    ), patch(
        "views.economy.main_panel.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "views.economy.main_panel.safe_edit",
        side_effect=_fake_edit,
    ):
        await btn.callback(interaction)

    inv_view = captured["view"]
    assert inv_view is not None
    back_ids = [getattr(c, "custom_id", None) for c in inv_view.children]
    assert "economy:back" in back_ids, (
        f"Inventory-from-Economy must carry economy:back; got {back_ids}"
    )


# ---------------------------------------------------------------------------
# Standalone !inventory still creates a fresh menu
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_standalone_inventory_command_uses_send_panel():
    """``!inventory`` is a command entry point, not panel navigation.
    It must continue to create a fresh menu message via the existing
    ``send_panel`` helper — unaffected by PR #1.
    """
    from cogs.inventory_cog import InventoryCog

    bot = MagicMock()
    cog = InventoryCog(bot)

    ctx = MagicMock()
    ctx.author = _author()
    ctx.guild = MagicMock()
    ctx.guild.id = 99
    ctx.send = AsyncMock(return_value=MagicMock())

    with patch(
        "cogs.inventory_cog._build_combined_inventory",
        new_callable=AsyncMock,
        return_value={},
    ), patch(
        "cogs.inventory_cog.send_panel",
        new_callable=AsyncMock,
    ) as send_panel:
        await cog.inventory.callback(cog, ctx, None)

    send_panel.assert_awaited_once()


# ---------------------------------------------------------------------------
# attach_back_to_economy_button — helper shape
# ---------------------------------------------------------------------------


def test_attach_back_to_economy_button_adds_economy_back_id():
    """The helper must add a button with the canonical
    ``custom_id="economy:back"`` so other call sites can rely on it.
    """
    view = discord.ui.View()
    added = attach_back_to_economy_button(view, _author())
    assert added is True
    ids = [getattr(c, "custom_id", None) for c in view.children]
    assert "economy:back" in ids


def test_attach_back_to_economy_button_no_op_at_component_cap():
    """When the view already has 25 children Discord rejects more — the
    helper must no-op without raising (matches the contract of the
    sibling Games / Settings / Admin helpers).
    """
    view = discord.ui.View()
    for i in range(25):
        view.add_item(
            discord.ui.Button(
                label=f"b{i}",
                custom_id=f"x:{i}",
                row=i // 5,
            ),
        )
    added = attach_back_to_economy_button(view, _author())
    assert added is False
    assert len(view.children) == 25
