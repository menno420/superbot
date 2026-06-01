"""BTD6 admin panel — ephemeral staff-only sub-view.

Opened by the **🛠️ Admin** button on the main :class:`BTD6PanelView`.
A fresh instance per click; not persistent across bot restarts.

Layout (5 buttons per row max):

* Row 0 — fetch controls: **Fetch All**, **Fetch Selected**.
* Row 1 — diagnostics: **Source Health**, **Latest Data**, **Close**.
* Row 2 — multi-select dropdown of registered enabled source keys.

Every action is gated to ``manage_guild`` / ``administrator``.
Fetch buttons drive ``btd6_ingestion_service.refresh_source_or_dependencies``
— the same service entry point the prefix / slash ``refresh-source``
commands use, so chain expansion / audit / locks all just work.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from core.runtime.interaction_helpers import safe_defer
from services import (
    btd6_ingestion_service,
    btd6_ingestion_sources,
    btd6_source_registry,
)
from utils.discord_permissions import is_staff_member

logger = logging.getLogger("bot.views.btd6.admin")


# ---------------------------------------------------------------------------
# Initial embed
# ---------------------------------------------------------------------------


async def build_admin_embed() -> discord.Embed:
    """The static admin-panel intro embed.

    Lists the parent sources the supervisor schedules so staff know
    what 'Fetch All' will hit, and explains the multi-select.
    """
    embed = discord.Embed(
        title="🛠️ BTD6 Admin",
        description=(
            "Manual data fetches and diagnostics. Use **Fetch All** to "
            "run every parent chain in one click, or pick specific "
            "sources from the dropdown and use **Fetch Selected**."
        ),
        color=discord.Color.blurple(),
    )
    parent_keys = btd6_ingestion_sources.parent_source_keys()
    embed.add_field(
        name="Parent sources",
        value=" · ".join(f"`{key}`" for key in parent_keys),
        inline=False,
    )
    embed.set_footer(
        text="Source Health = freshness per source · Latest Data = newest fact per kind",
    )
    return embed


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------


class BTD6AdminView(discord.ui.View):
    """Ephemeral staff-only admin panel. Fresh instance per click."""

    def __init__(self, opener_user_id: int, source_keys: list[str]) -> None:
        super().__init__(timeout=600)  # 10 min
        self.opener_user_id = opener_user_id
        self._source_keys = source_keys
        # Hold the multi-select so the action buttons can read its
        # current ``values``. Stored on `self` rather than queried via
        # `self.children` so the typing stays explicit.
        self.source_select = _SourceMultiSelect(source_keys)
        self.add_item(_FetchAllButton())
        self.add_item(_FetchSelectedButton())
        self.add_item(_SourceHealthButton())
        self.add_item(_LatestDataButton())
        self.add_item(_CloseButton())
        self.add_item(self.source_select)

    @classmethod
    async def create(cls, opener_user_id: int) -> BTD6AdminView:
        """Async factory — populates the multi-select from the live registry."""
        try:
            rows = await btd6_source_registry.list_enabled_sources(limit=100)
        except Exception:  # noqa: BLE001 — degrade gracefully
            logger.exception("admin panel: failed to load source registry")
            rows = []
        keys = sorted({row["source_key"] for row in rows})
        # Discord caps `discord.ui.Select` at 25 options. Truncate
        # gracefully — if the registry ever grows past 25 enabled
        # sources, "Fetch All" still covers all parents and the
        # multi-select shows the first 25 alphabetically.
        return cls(opener_user_id, keys[:25])

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.opener_user_id:
            await interaction.response.send_message(
                "This admin panel isn't yours.",
                ephemeral=True,
            )
            return False
        if not is_staff_member(interaction.user):
            await interaction.response.send_message(
                "❌ Staff role required.",
                ephemeral=True,
            )
            return False
        return True


# ---------------------------------------------------------------------------
# Multi-select
# ---------------------------------------------------------------------------


class _SourceMultiSelect(discord.ui.Select):
    def __init__(self, source_keys: list[str]) -> None:
        options = [discord.SelectOption(label=key, value=key) for key in source_keys]
        if not options:
            # Discord requires at least one option; if the registry
            # returned nothing show a disabled placeholder.
            options = [
                discord.SelectOption(
                    label="(no enabled sources)",
                    value="__none__",
                    default=False,
                ),
            ]
        super().__init__(
            placeholder="Pick sources to fetch…",
            min_values=0,
            max_values=len(options),
            options=options,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        # The select itself is just a state holder — the action buttons
        # read `.values` when clicked. ACK without changing the view so
        # Discord doesn't show "Interaction failed". Use safe_defer so
        # the no-raw-defer invariant stays clean.
        await safe_defer(interaction, ephemeral=True)


# ---------------------------------------------------------------------------
# Action buttons
# ---------------------------------------------------------------------------


class _FetchAllButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Fetch All",
            style=discord.ButtonStyle.success,
            row=0,
            custom_id="btd6_admin:fetch_all",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await _run_fetch(
            interaction,
            list(btd6_ingestion_sources.parent_source_keys()),
            user_id=interaction.user.id,
            label="Fetch All",
        )


class _FetchSelectedButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Fetch Selected",
            style=discord.ButtonStyle.primary,
            row=0,
            custom_id="btd6_admin:fetch_selected",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: BTD6AdminView = self.view  # type: ignore[assignment]
        selected = [v for v in view.source_select.values if v != "__none__"]
        if not selected:
            await interaction.response.send_message(
                "Pick at least one source from the dropdown first.",
                ephemeral=True,
            )
            return
        await _run_fetch(
            interaction,
            selected,
            user_id=interaction.user.id,
            label="Fetch Selected",
        )


class _SourceHealthButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Source Health",
            style=discord.ButtonStyle.secondary,
            row=1,
            custom_id="btd6_admin:source_health",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from cogs.btd6._builders import build_source_health_embed

        if not await safe_defer(interaction, ephemeral=True):
            return
        embed = await build_source_health_embed(limit=25)
        await interaction.followup.send(embed=embed, ephemeral=True)


class _LatestDataButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Latest Data",
            style=discord.ButtonStyle.secondary,
            row=1,
            custom_id="btd6_admin:latest_data",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from cogs.btd6._builders import build_latest_data_embed

        if not await safe_defer(interaction, ephemeral=True):
            return
        embed = await build_latest_data_embed()
        await interaction.followup.send(embed=embed, ephemeral=True)


class _CloseButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Close",
            style=discord.ButtonStyle.danger,
            row=1,
            custom_id="btd6_admin:close",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🛠️ BTD6 Admin",
                description="Closed.",
                color=discord.Color.greyple(),
            ),
            view=None,
        )


# ---------------------------------------------------------------------------
# Fetch driver — live progress edits + final summary
# ---------------------------------------------------------------------------


async def _run_fetch(
    interaction: discord.Interaction,
    source_keys: list[str],
    *,
    user_id: int,
    label: str,
) -> None:
    """Sequentially refresh ``source_keys`` and edit the response after
    each chain completes so the operator sees live progress.

    Uses ``interaction.edit_original_response`` between chains and
    posts the combined summary embed at the end.
    """
    from cogs.btd6._builders import build_admin_refresh_summary_embed

    if not await safe_defer(interaction, ephemeral=True):
        return

    results_by_source: list[tuple[str, list[Any]]] = []
    total_facts = 0

    for idx, source_key in enumerate(source_keys, start=1):
        progress_embed = discord.Embed(
            title=f"🛠️ {label}",
            description=(
                f"Running `{source_key}` ({idx}/{len(source_keys)})…\n"
                f"Total facts written so far: **{total_facts}**"
            ),
            color=discord.Color.blurple(),
        )
        try:
            await interaction.edit_original_response(
                embed=progress_embed,
                view=None,
            )
        except discord.HTTPException:  # noqa: BLE001
            logger.debug("admin fetch progress edit failed (non-fatal)")

        try:
            results = await btd6_ingestion_service.refresh_source_or_dependencies(
                source_key,
                reason="manual",
                started_by_user_id=user_id,
            )
        except Exception:  # noqa: BLE001 — surfaced via summary embed
            logger.exception("admin fetch failed for %s", source_key)
            results = []

        results_by_source.append((source_key, results))
        total_facts += sum(r.fact_count for r in results)

    summary = build_admin_refresh_summary_embed(
        results_by_source,
        title_suffix=f" — {label}",
    )
    try:
        await interaction.edit_original_response(embed=summary, view=None)
    except discord.HTTPException:
        # Fallback: post the summary as a followup if editing failed.
        await interaction.followup.send(embed=summary, ephemeral=True)


__all__ = [
    "BTD6AdminView",
    "build_admin_embed",
]
