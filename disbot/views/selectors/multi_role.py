"""Multi-select role picker — the role-typed sibling of
:class:`views.selectors.multi.MultiChannelSelector`.

Several admin flows pick a *set* of roles (exemptions, bulk assignment,
templates).  ``MultiRoleSelector`` mirrors ``MultiChannelSelector`` but
returns role ids and applies a role filter before Discord's 25-option cap,
defaulting to :func:`utils.role_feasibility.not_everyone` so every surface
agrees on what a "targetable" role is.  Pass a stricter ``role_filter``
(e.g. ``utils.role_feasibility``'s manageability partition) when the surface
may only offer roles the bot can actually mutate.

Paging beyond 25 roles is a deliberate follow-up (see
:mod:`views.selectors.channel`); the cap is enforced here so callers can pass
``guild.roles`` of any length without crashing the payload.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable

import discord

from utils.role_feasibility import RoleFilter, not_everyone
from views.selectors.multi import MultiSelect

OnSelectIds = Callable[[discord.Interaction, list[int]], Awaitable[None]]


class MultiRoleSelector(MultiSelect):
    """Multi-select guild-role picker returning every chosen role id.

    Parameters
    ----------
    roles:
        Any iterable of :class:`discord.Role`.  ``role_filter`` is applied
        before truncation to 25 entries.
    on_select:
        Awaitable invoked with ``(interaction, role_ids)``; unparseable
        values are skipped defensively.
    role_filter:
        Optional predicate.  Defaults to "not @everyone".
    """

    def __init__(
        self,
        roles: Iterable[discord.Role],
        on_select: OnSelectIds,
        *,
        role_filter: RoleFilter | None = None,
        placeholder: str = "Select one or more roles…",
        min_values: int = 0,
        max_values: int | None = None,
        custom_id: str | None = None,
        row: int | None = None,
    ) -> None:
        flt = role_filter or not_everyone
        bounded = [r for r in roles if flt(r)][:25]
        options = [
            discord.SelectOption(
                label=(str(getattr(r, "name", "")) or str(r.id))[:100],
                value=str(r.id),
            )
            for r in bounded
        ]
        super().__init__(
            options,
            self._dispatch_ids,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            custom_id=custom_id,
            row=row,
        )
        self._id_on_select = on_select

    async def _dispatch_ids(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        ids: list[int] = []
        for v in values:
            try:
                ids.append(int(v))
            except ValueError:
                continue
        await self._id_on_select(interaction, ids)
