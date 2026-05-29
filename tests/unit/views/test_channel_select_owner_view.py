"""Regression test for the channel-panel select widgets.

discord.py 2.7+ owns ``Item._parent`` for check propagation — ``View``
dispatch calls ``item._parent._run_checks(interaction)``.  The channel
Create / Delete / Restrict select widgets used to store their parent
*view* in ``self._parent``, shadowing the library attribute; dispatch
then called ``View._run_checks`` (which does not exist) and every select
callback crashed with ``AttributeError: ... has no attribute
'_run_checks'``.  The fix renames the back-reference to ``_owner_view``.

These pin that the back-reference no longer collides with discord.py's
internal ``_parent``.
"""

from __future__ import annotations

import discord

from views.channels._helpers import _ChannelSelect
from views.channels.create_panel import _CategorySelect, _NameSelect


class _FakeOwner:
    chosen_name = None
    chosen_cat = None
    selected_channel_id = None
    selected_channel_name = None

    def build_embed(self) -> discord.Embed:
        return discord.Embed()


def _opt(label: str = "general", value: str = "1") -> discord.SelectOption:
    return discord.SelectOption(label=label, value=value)


def test_channel_select_uses_owner_view_not_parent():
    owner = _FakeOwner()
    sel = _ChannelSelect([_opt()], owner, placeholder="pick")
    assert sel._owner_view is owner
    # discord.py's own _parent must NOT be shadowed by the parent view.
    assert getattr(sel, "_parent", None) is not owner


def test_name_select_uses_owner_view_not_parent():
    owner = _FakeOwner()
    sel = _NameSelect(["alpha", "beta"], owner)
    assert sel._owner_view is owner
    assert getattr(sel, "_parent", None) is not owner


def test_category_select_uses_owner_view_not_parent():
    owner = _FakeOwner()
    sel = _CategorySelect([_opt(label="Gaming", value="Gaming")], owner)
    assert sel._owner_view is owner
    assert getattr(sel, "_parent", None) is not owner
