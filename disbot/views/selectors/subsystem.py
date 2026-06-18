"""Registered-subsystem picker.

:func:`attach_subsystem_select` attaches a *windowed* subsystem picker to a
host view, pulling candidate options from
:data:`utils.subsystem_registry.SUBSYSTEMS` so it stays in sync with the
registry automatically (sorted by ``ui_priority`` then display name) and
paginating past Discord's 25-option cap instead of front-truncating (the #1040
class).

``visible_only=True`` filters out ``visibility_mode == 'internal'``
subsystems — appropriate for end-user-facing dialogs.  Admin tooling that needs
to act on internal subsystems passes ``visible_only=False``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import discord

from utils.subsystem_registry import all_subsystems_sorted
from views.paginated_select import SelectWindow, attach_windowed_select

OnSelect = Callable[[discord.Interaction, str], Awaitable[None]]


def attach_subsystem_select(
    view: discord.ui.View,
    on_select: OnSelect,
    *,
    visible_only: bool = True,
    placeholder: str = "Select a subsystem…",
    select_row: int | None = None,
    nav_row: int | None = None,
) -> SelectWindow:
    """Attach a windowed picker listing every registered subsystem to ``view``.

    Parameters
    ----------
    on_select:
        ``(interaction, subsystem_name)`` awaitable.
    visible_only:
        When ``True`` (default), omit ``internal``-mode subsystems.
    select_row / nav_row:
        Optional explicit action-rows for the embedding host's row budget.
    """
    entries = all_subsystems_sorted()
    if visible_only:
        entries = [(n, m) for n, m in entries if m.get("visibility_mode") != "internal"]
    options = [
        discord.SelectOption(
            label=meta.get("display_name", name)[:100],
            description=str(meta.get("description", ""))[:100] or None,
            emoji=meta.get("emoji") or None,
            value=name,
        )
        for name, meta in entries
    ]

    async def _dispatch(interaction: discord.Interaction, values: list[str]) -> None:
        await on_select(interaction, values[0] if values else "")

    return attach_windowed_select(
        view,
        options,
        _dispatch,
        placeholder=placeholder,
        min_values=1,
        max_values=1,
        select_row=select_row,
        nav_row=nav_row,
    )
