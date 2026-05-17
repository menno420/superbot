"""Regression tests for the channel-select widgets.

Two-part contract:

1. ``_ChannelSelect`` / ``_NameSelect`` / ``_CategorySelect`` must NOT shadow
   discord.py's ``_parent`` attribute on ``ui.Item``. Doing so makes
   ``Item._run_checks`` traverse into a View instead of an Item parent and
   raise ``AttributeError: 'View' object has no attribute '_run_checks'`` on
   every button click in the same view.

2. The select's parent view reference must still be accessible under
   ``_parent_view`` so the callbacks can mutate selection state and refresh
   the embed.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import discord
import pytest

from views.channels._helpers import _ChannelSelect
from views.channels.create_panel import _CategorySelect, _NameSelect


@pytest.fixture
def parent_view():
    view = MagicMock(spec=discord.ui.View)
    view.selected_channel_id = None
    view.selected_channel_name = None
    view.chosen_name = None
    view.chosen_cat = None
    return view


def test_channel_select_does_not_shadow_framework_parent(parent_view):
    select = _ChannelSelect(
        options=[discord.SelectOption(label="general", value="1")],
        parent_view=parent_view,
        placeholder="pick…",
    )
    # discord.py's _parent must remain None (no Item parent set), and our
    # view reference must be reachable under the non-clashing name.
    assert select._parent is None
    assert select._parent_view is parent_view


def test_name_select_does_not_shadow_framework_parent(parent_view):
    select = _NameSelect(["general", "gaming"], parent_view)
    assert select._parent is None
    assert select._parent_view is parent_view


def test_category_select_does_not_shadow_framework_parent(parent_view):
    select = _CategorySelect(
        [discord.SelectOption(label="Community", value="Community")],
        parent_view,
    )
    assert select._parent is None
    assert select._parent_view is parent_view
