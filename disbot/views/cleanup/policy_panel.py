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
    apply_cleanup_columns,
    collect_cleanup_diagnostics,
    preview_cleanup_change,
    preview_cleanup_columns,
    remove_cleanup_change,
)
from services.cleanup_levels import LEVELS
from services.governance_exceptions import GovernanceError
from utils.ui_constants import ADMIN_COLOR
from views.base import BaseView, HubView, interaction_is_admin

logger = logging.getLogger("bot.views.cleanup.policy_panel")

_EPHEMERAL_TIMEOUT = 180
_MAX_LISTED_ROWS = 15
_CUSTOM_VALUE = "__custom__"
_MAX_REMOVE_OPTIONS = 25  # Discord select hard limit


def _level_options() -> list[discord.SelectOption]:
    options = [
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
    options.append(
        discord.SelectOption(
            label="Custom…",
            value=_CUSTOM_VALUE,
            emoji="⚙️",
            description="Tune delete-after seconds + which commands are deleted.",
        ),
    )
    return options


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


_COMMAND_ACCESS_HINT = (
    "These levels only delete **invalid/blocked** command-style messages. "
    "To delete **any** command typed in a channel where commands aren't "
    "allowed, use **Command Access → 🗑️ Delete blocked commands** in `!settings`."
)


def _add_command_access_hint(embed: discord.Embed) -> None:
    """Clarify how cleanup levels relate to the Command Access delete toggle.

    The two systems are easily confused: a cleanup *level* only acts on
    blocked commands, while "delete on sight in a no-command channel" lives
    under Command Access.  Surfacing it here, at the point of confusion.
    """
    embed.add_field(name="ℹ️ Tip", value=_COMMAND_ACCESS_HINT, inline=False)


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
        _add_command_access_hint(embed)
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
                "legacy key the resolver never reads. **Fix:** press "
                "**🗑️ Remove a policy** to clear it, then **🔧 Set a policy** "
                "to re-set the guild default."
            ),
            inline=False,
        )
    if diag.stale_rows:
        embed.add_field(
            name="⚠️ Stale overrides",
            value=(
                f"{len(diag.stale_rows)} override(s) target a channel/category that "
                "no longer exists. Use **🗑️ Remove a policy** to clear them."
            ),
            inline=False,
        )
    _add_command_access_hint(embed)
    embed.set_footer(
        text="Read-only summary. Use the buttons below to set or remove policies.",
    )
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
            f"invalid cmds={'yes' if preview.new_delete_message else 'no'}, "
            f"failed cmds={'yes' if preview.new_delete_failed_commands else 'no'}, "
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
        if level == _CUSTOM_VALUE:
            view = _CustomLevelView(
                interaction.user,
                self._guild,
                self._scope_type,
                self._scope_id,
            )
            await interaction.response.send_message(
                content=view.summary(),
                view=view,
                ephemeral=True,
            )
            return
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


# Duration choices for the custom builder — all within the service's
# 0–MAX_DELETE_AFTER_SECONDS bound, so no typing or range-checking is needed.
_DURATION_OPTIONS: tuple[tuple[int, str], ...] = (
    (0, "Instant (0s)"),
    (2, "2 seconds"),
    (5, "5 seconds"),
    (10, "10 seconds"),
    (30, "30 seconds"),
    (60, "1 minute"),
    (120, "2 minutes"),
    (300, "5 minutes"),
)
_DURATION_LABELS: dict[int, str] = dict(_DURATION_OPTIONS)


class _DeleteAfterSelect(discord.ui.Select):
    """Pick the delete-after duration from a fixed menu (no typing)."""

    def __init__(self, current: int) -> None:
        super().__init__(
            placeholder="Delete after…",
            min_values=1,
            max_values=1,
            row=0,
            options=[
                discord.SelectOption(
                    label=label,
                    value=str(seconds),
                    default=(seconds == current),
                )
                for seconds, label in _DURATION_OPTIONS
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: _CustomLevelView = self.view  # type: ignore[assignment]
        await view.update(interaction, after=int(self.values[0]))


class _CustomYesNoSelect(discord.ui.Select):
    """A Yes/No picker for one boolean cleanup column."""

    def __init__(self, field: str, label: str, current: bool, row: int) -> None:
        self._field = field
        super().__init__(
            placeholder=label,
            min_values=1,
            max_values=1,
            row=row,
            options=[
                discord.SelectOption(label="Yes", value="yes", default=current),
                discord.SelectOption(label="No", value="no", default=not current),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: _CustomLevelView = self.view  # type: ignore[assignment]
        value = self.values[0] == "yes"
        if self._field == "invalid":
            await view.update(interaction, invalid=value)
        else:
            await view.update(interaction, failed=value)


class _CustomPreviewButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="🔎 Preview & apply",
            style=discord.ButtonStyle.primary,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: _CustomLevelView = self.view  # type: ignore[assignment]
        await view.preview(interaction)


class _CustomLevelView(BaseView):
    """Select-driven custom cleanup policy builder — no typing required.

    Three pickers (delete-after duration, delete-invalid Yes/No, delete-failed
    Yes/No) hold the choice as view state; a Preview button routes the same
    explicit columns through the shared dry-run + audited apply as the presets.
    Changing a picker rebuilds the view so each select reflects the current pick.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild: discord.Guild,
        scope_type: str,
        scope_id: int,
        *,
        after: int = 10,
        invalid: bool = True,
        failed: bool = False,
    ) -> None:
        super().__init__(author, public=False, timeout=_EPHEMERAL_TIMEOUT)
        self._guild = guild
        self._scope_type = scope_type
        self._scope_id = scope_id
        self._after = after
        self._invalid = invalid
        self._failed = failed
        self.add_item(_DeleteAfterSelect(after))
        self.add_item(
            _CustomYesNoSelect("invalid", "Delete invalid commands?", invalid, 1),
        )
        self.add_item(
            _CustomYesNoSelect("failed", "Delete failed commands?", failed, 2),
        )
        self.add_item(_CustomPreviewButton())

    def summary(self) -> str:
        return (
            "**Custom cleanup policy** — pick values, then **Preview & apply**:\n"
            f"• Delete after: **{_DURATION_LABELS.get(self._after, f'{self._after}s')}**\n"
            f"• Delete invalid commands: **{'Yes' if self._invalid else 'No'}**\n"
            f"• Delete failed commands: **{'Yes' if self._failed else 'No'}**"
        )

    async def update(
        self,
        interaction: discord.Interaction,
        *,
        after: int | None = None,
        invalid: bool | None = None,
        failed: bool | None = None,
    ) -> None:
        """Rebuild with the changed value so the selects show the new state."""
        new = _CustomLevelView(
            self._author,
            self._guild,
            self._scope_type,
            self._scope_id,
            after=self._after if after is None else after,
            invalid=self._invalid if invalid is None else invalid,
            failed=self._failed if failed is None else failed,
        )
        await interaction.response.edit_message(content=new.summary(), view=new)

    async def preview(self, interaction: discord.Interaction) -> None:
        try:
            built = await preview_cleanup_columns(
                self._guild,
                self._scope_type,
                self._scope_id,
                delete_invalid_commands=self._invalid,
                delete_failed_commands=self._failed,
                delete_after_seconds=self._after,
            )
        except Exception:  # noqa: BLE001 — preview must never crash the flow
            logger.exception("cleanup custom preview failed")
            await interaction.response.send_message(
                "Could not build the preview — see logs.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=preview_embed_from(built),
            view=_ConfirmApplyView(interaction.user, self._guild, built),
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
            await apply_cleanup_columns(
                self._guild,
                interaction.user,
                p.scope_type,
                p.scope_id,
                delete_invalid_commands=p.new_delete_message,
                delete_failed_commands=p.new_delete_failed_commands,
                delete_after_seconds=p.new_delete_after_seconds,
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
# Remove flow — clear a stored override (incl. legacy / stale rows)
# ---------------------------------------------------------------------------


def _remove_options(diag: CleanupDiagnostics) -> list[discord.SelectOption]:
    """One select option per stored row, flagging legacy / stale rows."""
    options: list[discord.SelectOption] = []
    for row in diag.rows[:_MAX_REMOVE_OPTIONS]:
        suffix = ""
        if row.is_ineffective:
            suffix = " — ⚠️ legacy/ineffective"
        elif row.is_stale:
            suffix = " — ⚠️ scope deleted"
        options.append(
            discord.SelectOption(
                label=f"{row.target_label} ({row.display_level}){suffix}"[:100],
                value=f"{row.scope_type}:{row.scope_id}",
                description=(
                    f"after={row.delete_after_seconds}s · "
                    f"invalid={'yes' if row.delete_invalid_commands else 'no'} · "
                    f"failed={'yes' if row.delete_failed_commands else 'no'}"
                )[:100],
            ),
        )
    return options


class _RemoveSelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild, diag: CleanupDiagnostics) -> None:
        super().__init__(
            placeholder="Pick a policy to remove…",
            min_values=1,
            max_values=1,
            options=_remove_options(diag),
        )
        self._guild = guild

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "You need the **Administrator** permission to change cleanup policies.",
                ephemeral=True,
            )
            return
        scope_type, _, raw_id = self.values[0].partition(":")
        try:
            scope_id = int(raw_id)
        except ValueError:
            await interaction.response.send_message(
                "Could not parse that selection — try again.",
                ephemeral=True,
            )
            return
        try:
            removed = await remove_cleanup_change(
                self._guild,
                interaction.user,
                scope_type,
                scope_id,
            )
        except GovernanceError as exc:
            await interaction.response.edit_message(
                content=f"❌ Could not remove: {exc}",
                embed=None,
                view=None,
            )
            return
        except Exception:  # noqa: BLE001 — surface a clean error, never crash
            logger.exception("cleanup remove failed")
            await interaction.response.edit_message(
                content="❌ Could not remove the policy — see logs.",
                embed=None,
                view=None,
            )
            return
        msg = (
            "✅ Removed the override — it now inherits from its parent scope. "
            "Resolution updates immediately."
            if removed
            else "ℹ️ That row was already gone — nothing to remove."
        )
        await interaction.response.edit_message(content=msg, embed=None, view=None)


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
        label="🗑️ Remove a policy",
        style=discord.ButtonStyle.danger,
        custom_id="cleanup_policy:remove",
        row=0,
    )
    async def btn_remove(
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
        diag = await collect_cleanup_diagnostics(self.guild)
        if not diag.rows:
            await interaction.response.send_message(
                "There are no stored cleanup overrides to remove — every scope "
                "already uses the inherited default.",
                ephemeral=True,
            )
            return
        view = BaseView(interaction.user, public=False, timeout=_EPHEMERAL_TIMEOUT)
        view.add_item(_RemoveSelect(self.guild, diag))
        await interaction.response.send_message(
            "Pick the override to remove (it will fall back to its parent scope):",
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
