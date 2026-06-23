"""AI panel in-place navigation (AI nav plan PR 1 + PR 2).

Pins the new page-swap model: the AI Platform anchor is one message, and
every chooser / scope page is reached by ``interaction.response.edit_message``
on that same anchor, with a Back button that unwinds the page stack.

* The ``views.ai._nav`` helper attaches a Back button that rebuilds its
  parent page in place.
* Each chooser carries a "↩ AI home" Back button.
* Each scope-picker page carries a "↩ AI <chooser>" Back button.
* The panel entry buttons (policy / behavior / tools) edit the anchor in
  place rather than sending a new ephemeral.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from views.ai import _nav  # noqa: E402


def _admin_interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.guild_id = 999
    interaction.guild = MagicMock()
    interaction.guild.id = 999
    interaction.response.is_done.return_value = False
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


# --- the _nav helper --------------------------------------------------------


def test_add_back_button_appends_a_button() -> None:
    view = discord.ui.View()
    before = len(view.children)
    added = _nav.add_back_button(
        view,
        label="↩ Back",
        builder=lambda: (discord.Embed(title="x"), discord.ui.View()),
    )
    assert added is True
    assert len(view.children) == before + 1
    btn = view.children[-1]
    assert isinstance(btn, discord.ui.Button)
    assert btn.label == "↩ Back"


def test_add_back_button_skips_when_at_component_cap() -> None:
    view = discord.ui.View()
    # Fill the view to the 25-component cap with disabled buttons.
    for i in range(25):
        view.add_item(discord.ui.Button(label=f"b{i}", row=i // 5))
    added = _nav.add_back_button(
        view,
        label="↩ Back",
        builder=lambda: (discord.Embed(title="x"), discord.ui.View()),
    )
    assert added is False
    assert len(view.children) == 25


async def test_back_button_edits_message_to_parent_page() -> None:
    sentinel_embed = discord.Embed(title="parent")
    sentinel_view = discord.ui.View()

    view = discord.ui.View()
    _nav.add_back_button(
        view,
        label="↩ Back",
        builder=lambda: (sentinel_embed, sentinel_view),
    )
    back = view.children[-1]
    interaction = _admin_interaction()
    await back.callback(interaction)
    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is sentinel_embed
    assert kwargs["view"] is sentinel_view


def test_ai_home_page_builds_panel_view() -> None:
    from views.ai.panel import AIPanelView

    embed, view = _nav.ai_home_page()
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, AIPanelView)


# --- choosers carry a Back-to-home button -----------------------------------


def test_policy_chooser_has_back_to_home() -> None:
    from views.ai.policy.chooser import PolicyChooserView

    view = PolicyChooserView()
    labels = {c.label for c in view.children if getattr(c, "label", None)}
    assert "↩ AI home" in labels


def test_behavior_chooser_has_back_to_home() -> None:
    from views.ai.behavior import BehaviorChooserView

    view = BehaviorChooserView()
    labels = {c.label for c in view.children if getattr(c, "label", None)}
    assert "↩ AI home" in labels


def test_tools_chooser_has_back_to_home() -> None:
    from views.ai.tools import ToolsChooserView

    view = ToolsChooserView()
    labels = {c.label for c in view.children if getattr(c, "label", None)}
    assert "↩ AI home" in labels


# --- scope pages carry a Back-to-chooser button -----------------------------


@pytest.mark.parametrize(
    ("attr", "back_label"),
    [
        ("channel_btn", "↩ AI Policy"),
        ("category_btn", "↩ AI Policy"),
        ("role_btn", "↩ AI Policy"),
    ],
)
async def test_policy_scope_pages_carry_back_button(attr, back_label) -> None:
    from views.ai.policy.chooser import PolicyChooserView

    view = PolicyChooserView()
    interaction = _admin_interaction()
    await getattr(view, attr).callback(interaction)
    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.call_args
    page_view = kwargs["view"]
    labels = {c.label for c in page_view.children if getattr(c, "label", None)}
    assert back_label in labels


async def test_tools_scope_page_carries_back_button() -> None:
    from views.ai.tools import ToolsChooserView

    view = ToolsChooserView()
    interaction = _admin_interaction()
    await view.guild_btn.callback(interaction)
    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.call_args
    labels = {c.label for c in kwargs["view"].children if getattr(c, "label", None)}
    assert "↩ AI Tools" in labels


async def test_behavior_scope_page_carries_back_button() -> None:
    from views.ai.behavior import BehaviorChooserView

    view = BehaviorChooserView()
    interaction = _admin_interaction()
    await view.channel_btn.callback(interaction)
    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.call_args
    labels = {c.label for c in kwargs["view"].children if getattr(c, "label", None)}
    assert "↩ AI Behavior" in labels


# --- panel entry buttons swap the anchor in place ---------------------------


@pytest.mark.parametrize("attr", ["policy_btn", "behavior_btn", "tools_btn"])
async def test_panel_entry_buttons_navigate_in_place(attr) -> None:
    from views.ai.panel import AIPanelView

    view = AIPanelView()
    interaction = _admin_interaction()
    # Drive the decorated button callback directly.
    await getattr(view, attr).callback(interaction)
    interaction.response.edit_message.assert_awaited_once()
    interaction.response.send_message.assert_not_awaited()
