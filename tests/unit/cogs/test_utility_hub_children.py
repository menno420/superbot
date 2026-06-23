"""Utility hub surfaces its child subsystems (discoverability-audit Session 1).

Regression guard for the owner-reported bug: *"the general cog is completely
unfindable from the help menu."*  Root cause — the Utility hub panel
(``_UtilityPanelView``) is a hybrid surface (its own action buttons **plus** a
parent hub for ``general`` / ``four_twenty``), but it rendered only its own
actions, so the ``general`` subsystem (and ``!joke`` / ``!fact`` / …) had no
click-through path from ``!help``.  The fix surfaces the ``parent_hub="utility"``
children as forwarding buttons, the same way the Games / Community hubs do.

These tests pin that behaviour so the path can't silently regress:

- ``discover_utility_children`` is metadata-driven (``parent_hub == "utility"``),
  never a hardcoded list.
- the panel has a forwarding button per child (stable ``utility:open:<sub>`` id).
- the embed names the children so they're discoverable in text too.
- the child button rechecks governance at click time and forwards to the target
  cog's ``build_help_menu_view`` hook.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from cogs.utility_cog import (
    _UtilityChildButton,
    _UtilityPanelView,
    discover_utility_children,
)
from governance.models import VisibilityResult
from utils.subsystem_registry import SUBSYSTEMS


def _ctx(author_id: int = 1) -> MagicMock:
    ctx = MagicMock()
    author = MagicMock(spec=discord.Member)
    author.id = author_id
    ctx.author = author
    return ctx


def _interaction() -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.id = 1
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


@contextmanager
def _all_visible():
    vis_result = VisibilityResult(
        visible_subsystems=set(SUBSYSTEMS),
        member_tier="user",
        resolved_from={},
        traces={},
    )
    with patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ):
        yield


# ---------------------------------------------------------------------------
# discover_utility_children — metadata-driven discovery
# ---------------------------------------------------------------------------


def test_discover_children_come_from_parent_hub_metadata():
    """Children must equal the SUBSYSTEMS entries with ``parent_hub == "utility"`` —
    never a hardcoded view-local list."""
    keys = {name for name, _meta in discover_utility_children()}
    expected = {
        name for name, meta in SUBSYSTEMS.items() if meta.get("parent_hub") == "utility"
    }
    assert keys == expected
    # The reported subsystem must be among them.
    assert "general" in keys


def test_discover_children_sorted_deterministically():
    children = discover_utility_children()
    order = [(meta.get("ui_priority", 99), name) for name, meta in children]
    assert order == sorted(order)


# ---------------------------------------------------------------------------
# View shape — a forwarding button per child
# ---------------------------------------------------------------------------


def test_panel_has_a_button_for_every_child():
    view = _UtilityPanelView(_ctx())
    surfaced = {
        btn._subsystem  # type: ignore[attr-defined]
        for btn in view.children
        if isinstance(btn, _UtilityChildButton)
    }
    assert surfaced == {name for name, _ in discover_utility_children()}
    assert "general" in surfaced


def test_child_buttons_have_stable_custom_ids():
    view = _UtilityPanelView(_ctx())
    ids = {
        btn.custom_id for btn in view.children if isinstance(btn, _UtilityChildButton)
    }
    assert "utility:open:general" in ids


def test_child_buttons_leave_row_four_for_back_button():
    """Children sit on row 3 so the help layer's row-4 Back button never collides."""
    view = _UtilityPanelView(_ctx())
    for btn in view.children:
        if isinstance(btn, _UtilityChildButton):
            assert btn.row == 3
    # Well under Discord's 25-component cap, with row 4 free.
    assert len(view.children) < 25


def test_embed_names_the_children():
    view = _UtilityPanelView(_ctx())
    embed = view.build_embed()
    blob = (embed.description or "") + " ".join(
        f"{f.name} {f.value}" for f in embed.fields
    )
    assert SUBSYSTEMS["general"]["display_name"] in blob


# ---------------------------------------------------------------------------
# Child-button callback — governance recheck + forward
# ---------------------------------------------------------------------------


async def test_child_button_blocks_invisible_subsystem():
    """A child hidden since render fails closed (ephemeral), never opens."""
    button = _UtilityChildButton(subsystem="general", label="💬 General", row=3)
    interaction = _interaction()
    vis_result = VisibilityResult(
        visible_subsystems=set(),  # general no longer visible
        member_tier="user",
        resolved_from={},
        traces={},
    )
    with patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ):
        await button.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.await_args.kwargs.get("ephemeral") is True
    interaction.response.edit_message.assert_not_called()


async def test_child_button_forwards_to_target_panel():
    """When visible, the button opens the target cog's ``build_help_menu_view`` in place."""
    button = _UtilityChildButton(subsystem="general", label="💬 General", row=3)
    interaction = _interaction()

    sub_embed = discord.Embed(title="💬 General")
    sub_view = discord.ui.View()
    target_cog = MagicMock()
    target_cog.build_help_menu_view = AsyncMock(return_value=(sub_embed, sub_view))

    # The button reads its parent view for a back-target; give it a bare view.
    button._view = MagicMock()
    button._view._back_target = None

    with (
        _all_visible(),
        patch(
            "cogs.help_cog._cog_for_subsystem",
            return_value=target_cog,
        ),
    ):
        await button.callback(interaction)

    target_cog.build_help_menu_view.assert_awaited_once_with(interaction)
    interaction.response.edit_message.assert_awaited_once()
    assert interaction.response.edit_message.await_args.kwargs["embed"] is sub_embed
