"""Cleanup-policy operator panel — diagnostics + presets builder (PR9).

Reached from the Cleanup hub (``cogs/cleanup/panel.py``).  Two surfaces over the
:mod:`services.cleanup_diagnostics` backend:

* **Diagnostics** (read-only): every stored policy named by level, with the
  inheritance reminder, stale-scope flags, and ineffective-row flags.
* **Builder** (presets-only): pick scope → pick level → **dry-run preview**
  (resolved effect + inherited source + diff) → **confirm** → audited apply via
  the governance pipeline.  No custom dimensions, no side-path writes.

Authority: the hub command is admin-gated and ``BaseView(public=False)`` already
restricts every step to the invoker; the apply button re-checks
``interaction_is_admin`` at the mutation point (capability-authority.md), with the
pipeline's ``_validate_authority`` as the infrastructure backstop.
"""

from __future__ import annotations

import logging

import discord

from services.cleanup_diagnostics import (
    CleanupDiagnostics,
    CleanupPolicyPreview,
    apply_cleanup_change,
    collect_cleanup_diagnostics,
    preview_cleanup_change,
)
from services.cleanup_levels import LEVELS
from services.governance_exceptions import GovernanceError
from utils.ui_constants import ADMIN_COLOR
from views.base import BaseView, HubView, interaction_is_admin

logger = logging.getLogger("bot.views.cleanup.policy_panel")

_EPHEMERAL_TIMEOUT = 180
_MAX_LISTED_ROWS = 15


def _level_options() -> list[discord.SelectOption]:
    return [
        discord.SelectOption(
            label=name,
            value=name,
            description=(
                f"after={cols['delete_after_seconds']}s · "
                f"invalid={'yes' if cols['delete_invalid_commands'] else 'no'} · "
                f"failed={'yes' if cols['delete_failed_commands'] else 'no'}"
            ),
        )
        for name, cols in LEVELS.items()
    ]


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def _format_row(row) -> str:
    flags = ""
    if row.is_ineffective:
        flags = " ⚠️ *legacy key — not applied; re-set to fix*"
    elif row.is_stale:
        flags = " ⚠️ *scope deleted*"
    return f"• **{row.target_label}** → `{row.display_level}` ({row.delete_after_seconds}s){flags}"


def diagnostics_embed_from(diag: CleanupDiagnostics) -> discord.Embed:
    """Build the diagnostics embed from an already-collected report (testable)."""
    embed = discord.Embed(
        title="🧹 Cleanup Policies — Diagnostics",
        description=(
            "Resolution walks **channel → category → guild → default**; the most "
            "specific override wins. Threads inherit from their parent channel."
        ),
        color=ADMIN_COLOR,
    )
    if not diag.rows:
        embed.add_field(
            name="Configured policies",
            value="_None — every scope uses the fallback default (delete after 5s)._",
            inline=False,
        )
        embed.set_footer(text="Use “Set a policy” to add one.")
        return embed

    counts = ", ".join(f"{name}×{n}" for name, n in sorted(diag.level_counts.items()))
    embed.add_field(
        name=f"Configured policies ({diag.total})",
        value=counts or "_none_",
        inline=False,
    )

    listed = diag.rows[:_MAX_LISTED_ROWS]
    body = "\n".join(_format_row(r) for r in listed)
    if diag.total > _MAX_LISTED_ROWS:
        body += f"\n… and {diag.total - _MAX_LISTED_ROWS} more."
    embed.add_field(name="Overrides", value=body, inline=False)

    if diag.ineffective_rows:
        embed.add_field(
            name="⚠️ Ineffective rows",
            value=(
                f"{len(diag.ineffective_rows)} guild row(s) are stored under a "
                "legacy key the resolver never reads. Re-set the guild default to fix."
            ),
            inline=False,
        )
    if diag.stale_rows:
        embed.add_field(
            name="⚠️ Stale overrides",
            value=(
                f"{len(diag.stale_rows)} override(s) target a channel/category that "
                "no longer exists."
            ),
            inline=False,
        )
    embed.set_footer(text="Read-only summary. Use “Set a policy” to make changes.")
    return embed


async def build_cleanup_diagnostics_embed(guild: discord.Guild) -> discord.Embed:
    """Collect + render the cleanup diagnostics for ``guild``."""
    diag = await collect_cleanup_diagnostics(guild)
    return diagnostics_embed_from(diag)


def preview_embed_from(preview: CleanupPolicyPreview) -> discord.Embed:
    """Render a dry-run preview (no side effects already guaranteed by service)."""
    cur = preview.current
    color = discord.Color.orange() if preview.will_change else discord.Color.greyple()
    embed = discord.Embed(
        title="🔎 Dry run — review before applying",
        description=f"Set **{preview.target_label}** to `{preview.level}`?",
        color=color,
    )
    embed.add_field(
        name="Currently resolves to",
        value=(
            f"delete={'yes' if cur.delete_message else 'no'}, "
            f"after={cur.delete_after_seconds}s\n"
            f"_source: {cur.resolved_from.value}_"
        ),
        inline=True,
    )
    embed.add_field(
        name="After applying",
        value=(
            f"delete={'yes' if preview.new_delete_message else 'no'}, "
            f"after={preview.new_delete_after_seconds}s\n"
            f"_source: {preview.scope_type} override_"
        ),
        inline=True,
    )
    if not preview.will_change:
        embed.add_field(
            name="No change",
            value="This scope already resolves exactly this way.",
            inline=False,
        )
    for warning in preview.warnings:
        embed.add_field(name="⚠️ Note", value=warning, inline=False)
    embed.set_footer(text="Nothing has been written yet.")
    return embed


# ---------------------------------------------------------------------------
# Builder flow — selects
# ---------------------------------------------------------------------------

_SCOPE_OPTIONS = [
    discord.SelectOption(
        label="Guild default",
        value="guild",
        emoji="🌐",
        description="Baseline level for every channel without an override.",
    ),
    discord.SelectOption(
        label="Category override",
        value="category",
        emoji="📁",
        description="Override one category (its channels inherit unless overridden).",
    ),
    discord.SelectOption(
        label="Channel override",
        value="channel",
        emoji="📡",
        description="Override one specific channel.",
    ),
]


class _ScopeSelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild) -> None:
        super().__init__(
            placeholder="Pick a scope to set cleanup for…",
            min_values=1,
            max_values=1,
            options=list(_SCOPE_OPTIONS),
        )
        self._guild = guild

    async def callback(self, interaction: discord.Interaction) -> None:
        scope = self.values[0]
        view = BaseView(interaction.user, public=False, timeout=_EPHEMERAL_TIMEOUT)
        if scope == "guild":
            view.add_item(
                _LevelSelect(self._guild, "guild", self._guild.id, "Guild default"),
            )
            await interaction.response.send_message(
                "Pick the guild-default cleanup level:",
                view=view,
                ephemeral=True,
            )
        elif scope == "category":
            view.add_item(_CategoryPickSelect(self._guild))
            await interaction.response.send_message(
                "Pick a category to override:",
                view=view,
                ephemeral=True,
            )
        else:
            view.add_item(_ChannelPickSelect(self._guild))
            await interaction.response.send_message(
                "Pick a channel to override:",
                view=view,
                ephemeral=True,
            )


class _CategoryPickSelect(discord.ui.ChannelSelect):
    def __init__(self, guild: discord.Guild) -> None:
        super().__init__(
            placeholder="Pick a category…",
            channel_types=[discord.ChannelType.category],
            min_values=1,
            max_values=1,
        )
        self._guild = guild

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        view = BaseView(interaction.user, public=False, timeout=_EPHEMERAL_TIMEOUT)
        view.add_item(
            _LevelSelect(self._guild, "category", picked.id, f"Category {picked.name}"),
        )
        await interaction.response.send_message(
            f"Pick the cleanup level for category **{picked.name}**:",
            view=view,
            ephemeral=True,
        )


class _ChannelPickSelect(discord.ui.ChannelSelect):
    def __init__(self, guild: discord.Guild) -> None:
        super().__init__(
            placeholder="Pick a channel…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
        )
        self._guild = guild

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        view = BaseView(interaction.user, public=False, timeout=_EPHEMERAL_TIMEOUT)
        view.add_item(
            _LevelSelect(self._guild, "channel", picked.id, f"#{picked.name}"),
        )
        await interaction.response.send_message(
            f"Pick the cleanup level for #{picked.name}:",
            view=view,
            ephemeral=True,
        )


class _LevelSelect(discord.ui.Select):
    def __init__(
        self,
        guild: discord.Guild,
        scope_type: str,
        scope_id: int,
        label: str,
    ) -> None:
        super().__init__(
            placeholder=f"Level for {label}…",
            min_values=1,
            max_values=1,
            options=_level_options(),
        )
        self._guild = guild
        self._scope_type = scope_type
        self._scope_id = scope_id

    async def callback(self, interaction: discord.Interaction) -> None:
        level = self.values[0]
        try:
            preview = await preview_cleanup_change(
                self._guild,
                self._scope_type,
                self._scope_id,
                level,
            )
        except Exception:  # noqa: BLE001 — preview must never crash the flow
            logger.exception("cleanup preview failed")
            await interaction.response.send_message(
                "Could not build the preview — see logs.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=preview_embed_from(preview),
            view=_ConfirmApplyView(interaction.user, self._guild, preview),
            ephemeral=True,
        )


# ---------------------------------------------------------------------------
# Confirm + apply
# ---------------------------------------------------------------------------


class _ConfirmApplyView(BaseView):
    def __init__(
        self,
        author: discord.Member | discord.User,
        guild: discord.Guild,
        preview: CleanupPolicyPreview,
    ) -> None:
        super().__init__(author, public=False, timeout=_EPHEMERAL_TIMEOUT)
        self._guild = guild
        self._preview = preview

    @discord.ui.button(label="✅ Apply", style=discord.ButtonStyle.success)
    async def btn_apply(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "You need the **Administrator** permission to change cleanup policies.",
                ephemeral=True,
            )
            return
        p = self._preview
        try:
            await apply_cleanup_change(
                self._guild,
                interaction.user,
                p.scope_type,
                p.scope_id,
                p.level,
            )
        except GovernanceError as exc:
            await interaction.response.edit_message(
                content=f"❌ Could not apply: {exc}",
                embed=None,
                view=None,
            )
            return
        except Exception:  # noqa: BLE001 — surface a clean error, never crash
            logger.exception("cleanup apply failed")
            await interaction.response.edit_message(
                content="❌ Could not apply the policy — see logs.",
                embed=None,
                view=None,
            )
            return
        await interaction.response.edit_message(
            content=(
                f"✅ Applied `{p.level}` to **{p.target_label}**. "
                "Resolution updates immediately."
            ),
            embed=None,
            view=None,
        )

    @discord.ui.button(label="✖ Cancel", style=discord.ButtonStyle.secondary)
    async def btn_cancel(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            content="Cancelled — nothing was written.",
            embed=None,
            view=None,
        )


# ---------------------------------------------------------------------------
# Top-level diagnostics panel
# ---------------------------------------------------------------------------


class CleanupPolicyPanelView(HubView):
    """Diagnostics view + entry to the presets builder."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild: discord.Guild,
    ) -> None:
        super().__init__(author)
        self.guild = guild

    @discord.ui.button(
        label="🔧 Set a policy",
        style=discord.ButtonStyle.success,
        custom_id="cleanup_policy:build",
        row=0,
    )
    async def btn_build(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "You need the **Administrator** permission to change cleanup policies.",
                ephemeral=True,
            )
            return
        view = BaseView(interaction.user, public=False, timeout=_EPHEMERAL_TIMEOUT)
        view.add_item(_ScopeSelect(self.guild))
        await interaction.response.send_message(
            "Choose what to set cleanup for:",
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(
        label="🔄 Refresh",
        style=discord.ButtonStyle.secondary,
        custom_id="cleanup_policy:refresh",
        row=0,
    )
    async def btn_refresh(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        embed = await build_cleanup_diagnostics_embed(self.guild)
        await interaction.response.edit_message(embed=embed, view=self)
