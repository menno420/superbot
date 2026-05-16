"""Governance-scope picker.

Renders the three currently-resolvable scope types (guild, category,
channel) as a single Select.  ``role`` is omitted because role-scoped
overrides are schema-only (ISSUE-007 from the audit) — the governance
resolver does not currently walk them.

The selector returns ``(scope_type, scope_id)`` via the on_select
callback; callers feed that directly into
``GovernanceMutationPipeline.set_visibility`` / ``set_cleanup_policy``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import discord

OnSelect = Callable[[discord.Interaction, str, int], Awaitable[None]]


class ScopeSelector(discord.ui.Select):
    """Three-option scope picker for governance dialogs."""

    def __init__(
        self,
        guild_id: int,
        category_id: int | None,
        channel_id: int | None,
        on_select: OnSelect,
        *,
        placeholder: str = "Choose governance scope…",
        custom_id: str | None = None,
        row: int | None = None,
    ) -> None:
        options: list[discord.SelectOption] = []
        # Channel scope appears first — most specific override.
        if channel_id is not None:
            options.append(
                discord.SelectOption(
                    label="Channel",
                    description="Override applies only to this channel.",
                    value=f"channel:{channel_id}",
                    emoji="#️⃣",
                ),
            )
        if category_id is not None:
            options.append(
                discord.SelectOption(
                    label="Category",
                    description="Override applies to every channel in the category.",
                    value=f"category:{category_id}",
                    emoji="📂",
                ),
            )
        options.append(
            discord.SelectOption(
                label="Guild (server-wide)",
                description="Override applies to the entire server.",
                value=f"guild:{guild_id}",
                emoji="🌐",
            ),
        )
        # dict[str, Any] (not object) so **kwargs unpacks into Select.__init__
        # without mypy demanding str|int|list|bool per declared param.
        kwargs: dict[str, Any] = {
            "placeholder": placeholder,
            "options": options,
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
            scope_type, scope_id_str = self.values[0].split(":", 1)
            scope_id = int(scope_id_str)
        except (IndexError, ValueError):
            await interaction.response.send_message(
                "Invalid scope.",
                ephemeral=True,
            )
            return
        await self._on_select(interaction, scope_type, scope_id)
