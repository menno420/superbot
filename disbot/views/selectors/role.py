"""Reusable role picker.

:func:`attach_role_select` attaches a *windowed* role picker to a host view —
any-length role iterable is paginated (◀/▶ nav past 25) instead of
front-truncated (the #1040 class).  By default ``@everyone`` is filtered out,
since it's almost never the useful pick.  Callers may pass a ``role_filter`` to
restrict further (e.g. "assignable to bots", "below caller's top role").
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable

import discord

from views.paginated_select import SelectWindow, attach_windowed_select

OnSelect = Callable[[discord.Interaction, int], Awaitable[None]]
RoleFilter = Callable[[discord.Role], bool]


def _default_filter(role: discord.Role) -> bool:
    return not role.is_default()


def attach_role_select(
    view: discord.ui.View,
    roles: Iterable[discord.Role],
    on_select: OnSelect,
    *,
    role_filter: RoleFilter | None = None,
    placeholder: str = "Select a role…",
    select_row: int | None = None,
    nav_row: int | None = None,
) -> SelectWindow:
    """Attach a windowed single-role picker to ``view``.

    Parameters
    ----------
    roles:
        Any iterable of ``discord.Role``.  ``role_filter`` is applied before
        pagination; the full filtered list is windowed (never truncated).
    on_select:
        ``(interaction, role_id)`` awaitable.
    role_filter:
        Optional predicate.  Defaults to "not @everyone".
    select_row / nav_row:
        Optional explicit action-rows for the embedding host's row budget.
    """
    flt = role_filter or _default_filter
    options = [
        discord.SelectOption(label=r.name[:100], value=str(r.id))
        for r in roles
        if flt(r)
    ]

    async def _dispatch(interaction: discord.Interaction, values: list[str]) -> None:
        try:
            role_id = int(values[0])
        except (IndexError, ValueError):
            role_id = 0
        await on_select(interaction, role_id)

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
