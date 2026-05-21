"""Setup-summary view — Phase 9i / Track 8 PR 24.

The launcher swaps to **Re-run Setup** + **View summary** once
``setup_status='complete'``. The View summary button opens this
panel: a digest of what the wizard applied (subsystems + binding
names + audit IDs when available) and a drift line that flags any
deviation from the accepted plan based on the current readiness
scan.

No DB writes from this view. The drift detection runs against a
fresh :func:`services.setup_readiness.collect` and the cached
``last_readiness_score`` already on the
:class:`SetupSession`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import discord

from services.setup_session import DriftReport, detect_drift
from views.base import BaseView

if TYPE_CHECKING:
    from services.setup_session import SetupSession

logger = logging.getLogger("bot.views.setup.summary")


@dataclass(frozen=True)
class AppliedRecord:
    """One line item the wizard applied during Final review."""

    subsystem: str
    binding_name: str
    target_name: str
    mutation_id: str | None = None
    audit_id: int | None = None


@dataclass(frozen=True)
class SummarySnapshot:
    """Aggregate of every applied operation + drift verdict."""

    applied: tuple[AppliedRecord, ...] = ()
    drift: DriftReport | None = None
    extra_notes: tuple[str, ...] = field(default_factory=tuple)


def build_summary_embed(snapshot: SummarySnapshot) -> discord.Embed:
    """Render the summary embed.

    Three states:

    * No applied operations — operator finished setup with no
      changes (e.g. accepted nothing). The embed surfaces drift
      only.
    * Applied + clean — green embed listing every applied
      ``subsystem.binding`` → target name + audit id.
    * Applied + drift — yellow embed; drift line callouts on top
      of the applied list.
    """
    drift = snapshot.drift
    has_drift = drift is not None and drift.has_drift

    if not snapshot.applied:
        color = discord.Color.gold() if has_drift else discord.Color.dark_grey()
        embed = discord.Embed(
            title="🛰 Setup summary",
            description=(
                "Setup finished without recording any applied changes. "
                "Run **Smart suggestions** → **Final review** to apply "
                "recommendations."
            ),
            color=color,
        )
        if drift is not None:
            embed.add_field(
                name="Drift",
                value=drift.summary,
                inline=False,
            )
        return embed

    color = discord.Color.gold() if has_drift else discord.Color.green()
    embed = discord.Embed(
        title="🛰 Setup summary",
        description=(
            f"**{len(snapshot.applied)}** recommendation(s) applied during "
            "the wizard run."
        ),
        color=color,
    )
    lines = []
    for rec in snapshot.applied:
        parts = [
            f"• `{rec.subsystem}.{rec.binding_name}` → `{rec.target_name}`",
        ]
        if rec.mutation_id:
            parts.append(f"_(mutation `{rec.mutation_id[:8]}`)_")
        if rec.audit_id is not None:
            parts.append(f"_(audit `{rec.audit_id}`)_")
        lines.append(" ".join(parts))
    value = "\n".join(lines)
    if len(value) > 1000:
        value = value[:997] + "..."
    embed.add_field(name="Applied", value=value, inline=False)

    if drift is not None:
        embed.add_field(
            name="Drift",
            value=drift.summary,
            inline=False,
        )

    if snapshot.extra_notes:
        embed.add_field(
            name="Notes",
            value="\n".join(f"• {n}" for n in snapshot.extra_notes),
            inline=False,
        )
    return embed


def _build_delete_channel_button() -> discord.ui.Button:
    """Construct the row-1 "Delete setup channel" button.

    Click handler opens a confirmation view ephemerally — the
    deletion only fires after the operator explicitly confirms.
    """
    button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
        label="Delete setup channel",
        style=discord.ButtonStyle.danger,
        custom_id="setup_summary:delete_channel",
        row=1,
    )

    async def _callback(interaction: discord.Interaction) -> None:
        view = _DeleteSetupChannelConfirmView(interaction.user)
        await interaction.response.send_message(
            "⚠️ Delete the private `#superbot-setup` channel?\n"
            "This cannot be undone. Setup state stays in the database — "
            "you can rerun setup via `!setup` or `/setup` at any time.",
            view=view,
            ephemeral=True,
        )

    button.callback = _callback  # type: ignore[method-assign]
    return button


class _DeleteSetupChannelConfirmView(BaseView):
    """Two-button confirmation view: Confirm delete vs. Cancel."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        timeout: int = 60,
    ) -> None:
        super().__init__(author, timeout=timeout)

    @discord.ui.button(label="Confirm delete", style=discord.ButtonStyle.danger)
    async def _confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        guild = interaction.guild
        if guild is None or interaction.guild_id is None:
            await interaction.response.send_message(
                "Delete requires a guild context.",
                ephemeral=True,
            )
            return
        from services import setup_session as session_service
        from services.setup_channel import delete_setup_channel

        try:
            session = await session_service.resume_session(interaction.guild_id)
        except Exception:
            logger.exception(
                "summary._confirm: resume_session failed (guild=%d)",
                interaction.guild_id,
            )
            session = None

        if session is None or session.setup_channel_id is None:
            await interaction.response.send_message(
                "No setup channel is tracked on this server.",
                ephemeral=True,
            )
            self.stop()
            return

        ok = await delete_setup_channel(guild, session.setup_channel_id)
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        if ok:
            await interaction.response.edit_message(
                content=(
                    "✅ Setup channel deleted. Run `!setup` or `/setup` "
                    "any time to revisit setup."
                ),
                view=self,
            )
        else:
            await interaction.response.edit_message(
                content=(
                    "⚠️ Could not delete the channel — it may have been "
                    "renamed, the bot may lack Manage Channels, or "
                    "Discord refused the request. See logs."
                ),
                view=self,
            )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def _cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content="Cancelled. The setup channel is unchanged.",
            view=self,
        )
        self.stop()


class SummaryView(BaseView):
    """Owner-facing summary panel.

    The constructor accepts a pre-built :class:`SummarySnapshot` so
    the launcher / wizard can build it from whatever state they
    have (the wizard hub passes through the last ``FinalReview``
    result; the launcher passes through the cached
    ``last_readiness_score`` plus a fresh drift detection).

    When ``session`` is supplied AND the session tracks a bot-managed
    setup channel (``setup_channel_id`` set), a "Delete setup
    channel" button surfaces so the operator can clean up the
    private workspace after Final Review completes.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        snapshot: SummarySnapshot,
        session: SetupSession | None = None,
        public: bool = False,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.snapshot = snapshot
        self.session = session
        if session is not None and session.setup_channel_id is not None:
            self.add_item(_build_delete_channel_button())

    @discord.ui.button(
        label="Open Settings Manager",
        style=discord.ButtonStyle.success,
    )
    async def _open_settings(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Swap the current summary message to the Settings Manager hub.

        Uses ``edit_message`` to keep the wizard's single anchored
        message — the operator does not get yet another ephemeral.
        """
        del button
        try:
            from views.settings.hub import SettingsHubView
        except Exception:
            logger.exception(
                "summary._open_settings: SettingsHubView import failed",
            )
            await interaction.response.send_message(
                "Settings Manager is unavailable right now. Run `!settings` "
                "to open it directly.",
                ephemeral=True,
            )
            return

        try:
            embed = SettingsHubView.build_embed()
            view = SettingsHubView(interaction.user)
        except Exception:
            logger.exception(
                "summary._open_settings: SettingsHubView build failed",
            )
            await interaction.response.send_message(
                "Could not open the Settings Manager. Run `!settings` instead.",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()

    @discord.ui.button(label="Close", style=discord.ButtonStyle.secondary)
    async def _close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(view=self)
        self.stop()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def build_summary_snapshot(
    *,
    session: SetupSession,
    applied: tuple[AppliedRecord, ...] = (),
    guild: object | None = None,
) -> SummarySnapshot:
    """Convenience helper: combine the persisted applied records
    with a fresh drift scan.

    The fresh scan calls ``services.setup_readiness.collect`` if a
    ``guild`` is passed in; otherwise the drift report uses the
    persisted ``last_readiness_score`` against ``None`` for the
    current score (which the drift detector then surfaces as "no
    score").
    """
    current_score: int | None = None
    current_summary: dict[str, int] = {}
    new_findings: tuple[object, ...] = ()
    if guild is not None:
        try:
            from services import setup_readiness

            report = await setup_readiness.collect(
                session.guild_id,
                guild=guild,
            )
        except Exception:
            logger.exception(
                "summary: setup_readiness.collect failed for guild=%d",
                session.guild_id,
            )
            report = None
        if report is not None:
            current_score = report.percentage
            current_summary = dict(report.health_summary)
            new_findings = tuple(
                f for f in report.health_findings if f.severity in ("error", "warn")
            )

    drift = detect_drift(
        previous_score=session.last_readiness_score,
        current_score=current_score,
        current_health_summary=current_summary,
        new_findings=new_findings,
    )

    return SummarySnapshot(applied=applied, drift=drift)


__all__ = [
    "AppliedRecord",
    "SummarySnapshot",
    "SummaryView",
    "build_summary_embed",
    "build_summary_snapshot",
]
