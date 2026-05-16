"""Registered-subsystem picker.

Pulls candidate options from :data:`utils.subsystem_registry.SUBSYSTEMS`
so the selector stays in sync with the registry automatically.  Sorts
by ``ui_priority`` then display name.

``visible_only=True`` filters out ``visibility_mode == 'internal'``
subsystems — appropriate for end-user-facing dialogs.  Admin tooling
that needs to act on internal subsystems passes ``visible_only=False``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import discord

from utils.subsystem_registry import all_subsystems_sorted

OnSelect = Callable[[discord.Interaction, str], Awaitable[None]]


class SubsystemSelector(discord.ui.Select):
    """Select widget listing every registered subsystem."""

    def __init__(
        self,
        on_select: OnSelect,
        *,
        visible_only: bool = True,
        placeholder: str = "Select a subsystem…",
        custom_id: str | None = None,
        row: int | None = None,
    ) -> None:
        entries = all_subsystems_sorted()
        if visible_only:
            entries = [
                (n, m) for n, m in entries if m.get("visibility_mode") != "internal"
            ]
        options = [
            discord.SelectOption(
                label=meta.get("display_name", name)[:100],
                description=str(meta.get("description", ""))[:100] or None,
                emoji=meta.get("emoji") or None,
                value=name,
            )
            for name, meta in entries[:25]
        ]
        # dict[str, Any] (not object) so **kwargs unpacks into Select.__init__
        # without mypy demanding str|int|list|bool per declared param.
        kwargs: dict[str, Any] = {
            "placeholder": placeholder,
            "options": options
            or [
                discord.SelectOption(label="— no subsystems —", value=""),
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
        name = self.values[0] if self.values else ""
        await self._on_select(interaction, name)
