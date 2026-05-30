"""views.channels — channel-management panel hierarchy.

The cog at ``cogs/channel_cog.py`` is a thin dispatcher; every panel
view lives here.  Modules:

  main_panel        — ChannelManagerView (top-level hub)
  create_panel      — CreateSubView, NameSelect, CategorySelect, CustomNameModal
  delete_panel      — DeleteSubView, DeleteConfirmView
  restrict_panel    — RestrictSubView
  visibility_panel  — VisibilitySubView, SubsystemToggleView
  _helpers          — _NAME_PRESETS, _CATEGORY_PRESETS,
                      _build_channel_options, _ChannelSelect

Test imports may still reach into these underscore-prefixed names —
they're kept stable so the existing ``test_view_error_handling.py``
test against ``_SubsystemToggleView`` continues to resolve.
"""

from __future__ import annotations

from views.channels._helpers import (
    _CATEGORY_PRESETS,
    _NAME_PRESETS,
    _build_channel_options,
    _ChannelSelect,
)
from views.channels.create_panel import (
    _CategorySelect,
    _CreateSubView,
    _CustomNameModal,
)
from views.channels.delete_panel import _DeleteConfirmView, _DeleteSubView
from views.channels.main_panel import _ChannelManagerView
from views.channels.restrict_panel import _RestrictSubView
from views.channels.visibility_panel import (
    _SubsystemToggleView,
    _VisibilitySubView,
)

__all__ = [
    "_CATEGORY_PRESETS",
    "_NAME_PRESETS",
    "_CategorySelect",
    "_ChannelManagerView",
    "_ChannelSelect",
    "_CreateSubView",
    "_CustomNameModal",
    "_DeleteConfirmView",
    "_DeleteSubView",
    "_RestrictSubView",
    "_SubsystemToggleView",
    "_VisibilitySubView",
    "_build_channel_options",
]
