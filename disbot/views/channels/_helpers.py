"""Shared helpers for the channel-management panel views.

Hosts the name/category presets and the cross-panel ``_ChannelSelect``
widget (used by both delete and restrict flows).

The generic ``_build_channel_options`` factory now lives in
``views.selectors._resource_helpers`` so it can be consumed by code that
does not belong to the channel-management subsystem (Phase 0 of the
platform roadmap).  This module re-exports it for back-compat.

Kept underscore-prefixed because these are implementation details of
the channel subsystem — production code should depend on the public
``views.channels`` re-exports instead.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer
from views.selectors._resource_helpers import _build_channel_options

__all__ = [
    "_CATEGORY_PRESETS",
    "_ChannelSelect",
    "_NAME_PRESETS",
    "_build_channel_options",
]

# Keyword presets shown in the dropdown menus
_NAME_PRESETS = [
    "general",
    "gaming",
    "announcements",
    "events",
    "tournament",
    "support",
    "bot-commands",
    "vc-lounge",
]
_CATEGORY_PRESETS = [
    "Gaming",
    "Community",
    "Events",
    "Tournaments",
    "Staff",
]


class _ChannelSelect(discord.ui.Select):
    """Generic channel select used by Delete and Restrict sub-panels.

    The parent view must define ``selected_channel_id`` and
    ``selected_channel_name`` attributes plus a ``build_embed()``
    method — the callback writes both fields and refreshes the
    embed.
    """

    def __init__(
        self,
        options: list[discord.SelectOption],
        parent_view,
        *,
        placeholder: str,
    ):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )
        # NB: must NOT be ``self._parent`` — discord.py 2.7+ owns that
        # attribute for check propagation (``item._parent._run_checks(...)``).
        # Shadowing it with the parent view crashed every select callback
        # with ``AttributeError: ... has no attribute '_run_checks'``.
        self._owner_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self._owner_view.selected_channel_id = int(self.values[0])  # type: ignore[attr-defined]
        # Resolve the display name from the options list
        chosen_opt = next((o for o in self.options if o.value == self.values[0]), None)
        self._owner_view.selected_channel_name = (  # type: ignore[attr-defined]
            chosen_opt.label if chosen_opt else self.values[0]
        )
        try:
            await interaction.response.edit_message(
                embed=self._owner_view.build_embed(),  # type: ignore[attr-defined]
                view=self._owner_view,  # type: ignore[attr-defined, arg-type]
            )
        except discord.HTTPException:
            await safe_defer(interaction)
