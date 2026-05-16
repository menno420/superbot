"""Reusable role picker.

Same 25-option truncation as :class:`channel.ChannelSelector`.  By
default ``@everyone`` is filtered out, since it's almost never the
useful pick.  Callers may pass a ``role_filter`` to restrict further
(e.g. "assignable to bots", "below caller's top role").
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable

import discord

OnSelect = Callable[[discord.Interaction, int], Awaitable[None]]
RoleFilter = Callable[[discord.Role], bool]


def _default_filter(role: discord.Role) -> bool:
    return not role.is_default()


class RoleSelector(discord.ui.Select):
    """Select widget listing up to 25 roles.

    Parameters
    ----------
    roles:
        Any iterable of ``discord.Role``.  ``role_filter`` is applied
        before truncation to 25 entries.
    on_select:
        ``(interaction, role_id)`` awaitable.
    role_filter:
        Optional predicate.  Defaults to "not @everyone".
    """

    def __init__(
        self,
        roles: Iterable[discord.Role],
        on_select: OnSelect,
        *,
        role_filter: RoleFilter | None = None,
        placeholder: str = "Select a role…",
        custom_id: str | None = None,
        row: int | None = None,
    ) -> None:
        flt = role_filter or _default_filter
        bounded = [r for r in roles if flt(r)][:25]
        options = [
            discord.SelectOption(label=r.name[:100], value=str(r.id)) for r in bounded
        ]
        kwargs: dict[str, object] = {
            "placeholder": placeholder,
            "options": options
            or [
                discord.SelectOption(label="— no roles available —", value="0"),
            ],
            "min_values": 1,
            "max_values": 1,
        }
        if custom_id is not None:
            kwargs["custom_id"] = custom_id
        if row is not None:
            kwargs["row"] = row
        super().__init__(**kwargs)
        self._on_select = on_select

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            role_id = int(self.values[0])
        except (IndexError, ValueError):
            role_id = 0
        await self._on_select(interaction, role_id)
