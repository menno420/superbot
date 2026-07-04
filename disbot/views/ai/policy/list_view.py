"""Paged list of current AI policy overrides (PR4A).

Aggregates the three override tables (``ai_channel_policy``,
``ai_category_policy``, ``ai_role_policy``) into one flat embed page.
Pagination handles guilds with many overrides; each page shows at most
:data:`_PER_PAGE` entries.

Read-only: this module never mutates. The reads route through the
existing :mod:`utils.db.ai` helpers, which is the canonical read path
for the typed AI tables.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import discord

logger = logging.getLogger("bot.views.ai.policy.list_view")

_VIEW_TIMEOUT_SECONDS = 300
_PER_PAGE = 10
_PANEL_COLOR = discord.Color.blurple()


@dataclass(frozen=True)
class PolicyEntry:
    """One row in the unified override list."""

    scope: str  # "channel" / "category" / "role"
    target_id: int
    summary: str


def _channel_entry_summary(row: dict[str, Any]) -> str:
    parts = [f"mode=`{row.get('mode')}`"]
    if row.get("min_level") is not None:
        parts.append(f"min_level=`{row['min_level']}`")
    if row.get("cooldown_seconds") is not None:
        parts.append(f"cooldown=`{row['cooldown_seconds']}s`")
    return " · ".join(parts)


def _category_entry_summary(row: dict[str, Any]) -> str:
    # Same shape as channel.
    return _channel_entry_summary(row)


def _role_entry_summary(row: dict[str, Any]) -> str:
    parts = [f"decision=`{row.get('decision')}`"]
    if row.get("min_level_override") is not None:
        parts.append(f"min_level_override=`{row['min_level_override']}`")
    if row.get("bypass_cooldown"):
        parts.append("bypass_cooldown=`yes`")
    return " · ".join(parts)


async def collect_entries(guild_id: int) -> list[PolicyEntry]:
    """Fetch overrides from all three typed-policy tables.

    Returns entries sorted by scope (channel → category → role) so
    pagination is stable across reloads. Within a scope, ordering
    comes from the DB read which returns by primary-key order.
    """
    from utils.db import ai as ai_db

    entries: list[PolicyEntry] = []

    channel_rows = await ai_db.list_channel_policies(guild_id)
    for row in channel_rows:
        entries.append(
            PolicyEntry(
                scope="channel",
                target_id=int(row["channel_id"]),
                summary=_channel_entry_summary(row),
            ),
        )

    category_rows = await ai_db.list_category_policies(guild_id)
    for row in category_rows:
        entries.append(
            PolicyEntry(
                scope="category",
                target_id=int(row["category_id"]),
                summary=_category_entry_summary(row),
            ),
        )

    role_rows = await ai_db.list_role_policies(guild_id)
    for row in role_rows:
        entries.append(
            PolicyEntry(
                scope="role",
                target_id=int(row["role_id"]),
                summary=_role_entry_summary(row),
            ),
        )

    return entries


def _format_target(scope: str, target_id: int) -> str:
    if scope == "channel":
        return f"<#{target_id}>"
    if scope == "category":
        return f"📁 `{target_id}`"
    if scope == "role":
        return f"<@&{target_id}>"
    return f"`{target_id}`"


def _scope_emoji(scope: str) -> str:
    return {"channel": "🔵", "category": "📁", "role": "👥"}.get(scope, "·")


def build_list_embed(
    entries: list[PolicyEntry],
    *,
    page: int,
) -> tuple[discord.Embed, int]:
    """Render one page of the override list.

    Returns ``(embed, total_pages)`` so the View can disable Prev/Next
    when the page is at an edge.
    """
    total = len(entries)
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * _PER_PAGE
    slice_ = entries[start : start + _PER_PAGE]

    embed = discord.Embed(
        title="AI policy overrides",
        description=(
            f"{total} total override(s) across this guild "
            f"(channel + category + role)."
        ),
        color=_PANEL_COLOR,
    )
    if not entries:
        embed.add_field(
            name="No overrides",
            value=(
                "The guild uses only the baseline `ai_guild_policy` row. "
                "Use the Policy chooser to add channel / category / role "
                "overrides."
            ),
            inline=False,
        )
    else:
        for entry in slice_:
            embed.add_field(
                name=f"{_scope_emoji(entry.scope)} {entry.scope}",
                value=(
                    f"{_format_target(entry.scope, entry.target_id)} · "
                    f"{entry.summary}"
                ),
                inline=False,
            )
    embed.set_footer(text=f"Page {page} / {total_pages} · administrator-only")
    return embed, total_pages


class PolicyListView(discord.ui.View):
    """Ephemeral paged view of current overrides."""

    def __init__(self, entries: list[PolicyEntry], *, page: int = 1) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.entries = entries
        self.page = page
        self._sync_button_state()

    def _sync_button_state(self) -> None:
        total_pages = max(
            1,
            (len(self.entries) + _PER_PAGE - 1) // _PER_PAGE,
        )
        self.prev_btn.disabled = self.page <= 1
        self.next_btn.disabled = self.page >= total_pages

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Canonical admin gate — honours the platform owner (Q-0212).
        from views.base import interaction_is_admin

        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.secondary, row=0)
    async def prev_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        self.page = max(1, self.page - 1)
        embed, _total = build_list_embed(self.entries, page=self.page)
        self._sync_button_state()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        total_pages = max(
            1,
            (len(self.entries) + _PER_PAGE - 1) // _PER_PAGE,
        )
        self.page = min(total_pages, self.page + 1)
        embed, _total = build_list_embed(self.entries, page=self.page)
        self._sync_button_state()
        await interaction.response.edit_message(embed=embed, view=self)


__all__ = [
    "PolicyEntry",
    "PolicyListView",
    "build_list_embed",
    "collect_entries",
]
