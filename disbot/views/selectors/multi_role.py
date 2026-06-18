"""Multi-select role picker — the role-typed sibling of
:func:`views.selectors.multi.attach_multi_channel_select`.

Several admin flows pick a *set* of roles (exemptions, bulk assignment,
templates).  :func:`attach_multi_role_select` mirrors
:func:`~views.selectors.multi.attach_multi_channel_select` but returns role ids
and applies a role filter before pagination, defaulting to
:func:`utils.role_feasibility.not_everyone` so every surface agrees on what a
"targetable" role is.  Pass a stricter ``role_filter`` (e.g.
``utils.role_feasibility``'s manageability partition) when the surface may only
offer roles the bot can actually mutate.

The full filtered list is windowed (◀/▶ nav past 25) instead of front-truncated
(the #1040 class), so callers can pass ``guild.roles`` of any length.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable

import discord

from utils.role_feasibility import RoleFilter, not_everyone
from views.paginated_select import SelectWindow
from views.selectors.multi import attach_multi_select

OnSelectIds = Callable[[discord.Interaction, list[int]], Awaitable[None]]


def attach_multi_role_select(
    view: discord.ui.View,
    roles: Iterable[discord.Role],
    on_select: OnSelectIds,
    *,
    role_filter: RoleFilter | None = None,
    placeholder: str = "Select one or more roles…",
    min_values: int = 0,
    max_values: int | None = None,
    select_row: int | None = None,
    nav_row: int | None = None,
) -> SelectWindow:
    """Attach a windowed multi-role picker returning every chosen id to ``view``.

    Parameters
    ----------
    roles:
        Any iterable of :class:`discord.Role`.  ``role_filter`` is applied
        before pagination; the full filtered list is windowed (never truncated).
    on_select:
        Awaitable invoked with ``(interaction, role_ids)``; unparseable values
        are skipped defensively.
    role_filter:
        Optional predicate.  Defaults to "not @everyone".
    select_row / nav_row:
        Optional explicit action-rows for the embedding host's row budget.
    """
    flt = role_filter or not_everyone
    options = [
        discord.SelectOption(
            label=(str(getattr(r, "name", "")) or str(r.id))[:100],
            value=str(r.id),
        )
        for r in roles
        if flt(r)
    ]

    async def _dispatch_ids(
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        ids: list[int] = []
        for v in values:
            try:
                ids.append(int(v))
            except ValueError:
                continue
        await on_select(interaction, ids)

    return attach_multi_select(
        view,
        options,
        _dispatch_ids,
        placeholder=placeholder,
        min_values=min_values,
        max_values=max_values,
        select_row=select_row,
        nav_row=nav_row,
    )
