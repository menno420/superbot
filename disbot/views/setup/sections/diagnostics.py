"""Diagnose & repair section — inspects config and stages safe repairs.

Server-management PR12.  Surfaces the read-only
:mod:`services.setup_diagnostics` report inside the setup wizard:

* it **explains** what is broken / stale / unsafe / incomplete, grouped by
  severity so the card stays readable;
* it stages the **safe, deterministic** repairs (today: clearing a dead
  binding) as ``SetupOperation`` drafts with ``staging_kind="repair"``;
* **Final Review remains the only apply gate** — this section never calls
  ``apply_operations`` and never imports a mutation pipeline.  The
  ``test_setup_operations_invariants`` AST check and
  ``test_diagnostics_section`` both pin that.

Advisory / blocked findings (missing bindings, permission/hierarchy
blockers, stale role tiers, cleanup rows) render as read-only follow-ups
pointing at the panel that owns the fix — PR12 deliberately does **not**
open a second mutation path for them.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_diagnostics, setup_draft, setup_session
from services.setup_diagnostics import SetupDiagnosticsReport
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.diagnostics")

SLUG = "diagnostics"

# Severity → render metadata.  Order mirrors
# ``setup_diagnostics._SEVERITY_ORDER`` so the embed lists urgent first.
_SEVERITY_RENDER: tuple[tuple[str, str, str], ...] = (
    (setup_diagnostics.SEV_BLOCKER, "⛔", "Blockers"),
    (setup_diagnostics.SEV_WARNING, "⚠️", "Warnings"),
    (setup_diagnostics.SEV_ADVISORY, "💡", "Advisories"),
)

_MAX_PER_GROUP = 6  # keep each embed field well under Discord's 1024 cap


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def build_diagnostics_embed(report: SetupDiagnosticsReport) -> discord.Embed:
    """Render a grouped, severity-sorted view of ``report``.

    Healthy guilds get a short "nothing to fix" embed; otherwise findings
    are grouped by severity, each line carrying its repair label (for safe
    repairs) or its manual follow-up note (for advisory / blocked ones).
    """
    counts = report.counts
    repairable = report.repairable

    if report.is_healthy:
        embed = discord.Embed(
            title="🩺 Diagnose & repair",
            description=(
                "I inspected this server's bindings, auto-role tiers, "
                "moderator roles, and cleanup policies.\n\n"
                "🟢 **No issues detected** — nothing to repair."
            ),
            color=discord.Color.green(),
        )
        embed.set_footer(text="Re-scan any time after you change the server.")
        return embed

    embed = discord.Embed(
        title="🩺 Diagnose & repair",
        description=(
            "I inspected this server's configuration and found the items "
            "below. **Staging a repair changes nothing yet** — it's added to "
            "the draft and applied only when you run **Final review**."
        ),
        color=discord.Color.orange(),
    )
    summary = (
        f"⚠️ {counts[setup_diagnostics.SEV_WARNING]} warning(s) · "
        f"💡 {counts[setup_diagnostics.SEV_ADVISORY]} advisory · "
        f"🩹 {len(repairable)} safe repair(s) available"
    )
    if counts[setup_diagnostics.SEV_BLOCKER]:
        summary = f"⛔ {counts[setup_diagnostics.SEV_BLOCKER]} blocker(s) · " + summary
    embed.add_field(name="Summary", value=summary, inline=False)

    for severity, icon, title in _SEVERITY_RENDER:
        group = report.by_severity(severity)
        if not group:
            continue
        lines: list[str] = []
        for f in group[:_MAX_PER_GROUP]:
            if f.is_auto_repairable:
                tail = f"🩹 _{f.repair_label}_"
            elif f.repairability == setup_diagnostics.REPAIR_BLOCKED:
                tail = f"🔒 {f.advisory_note}"
            else:
                tail = f"→ {f.advisory_note}"
            lines.append(f"• {f.summary}\n  {tail}")
        if len(group) > _MAX_PER_GROUP:
            lines.append(f"_+{len(group) - _MAX_PER_GROUP} more {title.lower()}_")
        embed.add_field(name=f"{icon} {title}", value="\n".join(lines), inline=False)

    if repairable:
        embed.set_footer(
            text=(
                f"“Stage safe repairs” adds {len(repairable)} clear-binding "
                "op(s) to the draft · Final review applies them."
            ),
        )
    else:
        embed.set_footer(
            text="No automatic repairs — follow the per-item notes, then re-scan.",
        )
    return embed


# ---------------------------------------------------------------------------
# Detail view — Stage safe repairs + Re-scan
# ---------------------------------------------------------------------------


class _StageRepairsButton(discord.ui.Button):
    """Stage every auto-repairable finding's batch into the draft.

    Re-collects diagnostics on click (revalidate before staging — the
    guild may have changed since the embed was built) and appends each
    repair op with ``staging_kind="repair"`` provenance.  Never applies;
    Final Review does.
    """

    def __init__(self) -> None:
        super().__init__(
            label="Stage safe repairs",
            style=discord.ButtonStyle.success,
            emoji="🩹",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Diagnostics require a guild context.",
                ephemeral=True,
            )
            return

        try:
            report = await setup_diagnostics.collect_setup_diagnostics(guild)
        except Exception:
            logger.exception("diagnostics: collect failed on stage")
            await interaction.response.send_message(
                "Could not run diagnostics — see logs.",
                ephemeral=True,
            )
            return

        repairable = report.repairable
        if not repairable:
            await interaction.response.send_message(
                "✅ Nothing to stage — no safe automatic repairs right now.",
                ephemeral=True,
            )
            return

        staged = 0
        for finding in repairable:
            for op in finding.repair_ops:
                try:
                    await setup_draft.append(
                        op,
                        guild_id=guild.id,
                        actor_id=interaction.user.id,
                        label=finding.repair_label or f"clear {op.subsystem}",
                        section_slug=SLUG,
                        staging_kind="repair",
                    )
                    staged += 1
                except Exception:
                    logger.exception(
                        "diagnostics: setup_draft.append failed for %s",
                        finding.code,
                    )

        if staged == 0:
            await interaction.response.send_message(
                "Could not stage the repairs — see logs.",
                ephemeral=True,
            )
            return

        try:
            await setup_session.mark_in_progress(guild.id, step=SLUG)
        except Exception:
            logger.exception("diagnostics: mark_in_progress failed")

        try:
            pending = await setup_draft.count(guild.id)
        except Exception:
            logger.exception("diagnostics: setup_draft.count failed")
            pending = staged

        await interaction.response.send_message(
            f"🩹 Staged **{staged}** safe repair(s) for Final review. "
            f"Pending operations: **{pending}**. Nothing changes until you apply.",
            ephemeral=True,
        )


class _RescanButton(discord.ui.Button):
    """Re-run diagnostics and refresh the detail embed in place."""

    def __init__(self) -> None:
        super().__init__(
            label="Re-scan",
            style=discord.ButtonStyle.secondary,
            emoji="🔁",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Diagnostics require a guild context.",
                ephemeral=True,
            )
            return
        try:
            report = await setup_diagnostics.collect_setup_diagnostics(guild)
        except Exception:
            logger.exception("diagnostics: collect failed on rescan")
            await interaction.response.send_message(
                "Could not run diagnostics — see logs.",
                ephemeral=True,
            )
            return
        embed = build_diagnostics_embed(report)
        await interaction.response.edit_message(
            embed=embed,
            view=DiagnosticsSectionView(interaction.user),
        )


class DiagnosticsSectionView(BaseView):
    """Detail view — Stage safe repairs + Re-scan (row 0).

    Used both as the section card's *Customize* target and the
    wizard-native step-detail view, so it stays within rows 0–3 (row 4 is
    reserved by ``views.setup.wizard_nav.render_step_detail``).  It carries
    no live report state: both buttons re-collect on click so staging
    always validates against the current guild.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.add_item(_StageRepairsButton())
        self.add_item(_RescanButton())


# ---------------------------------------------------------------------------
# Section entry points
# ---------------------------------------------------------------------------


async def _customize_run(
    interaction: discord.Interaction,
    hub: SetupHubView | None,
) -> None:
    """Open the diagnostics detail (the card's Customize target)."""
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Diagnostics require a guild context.",
            ephemeral=True,
        )
        return
    try:
        report = await setup_diagnostics.collect_setup_diagnostics(guild)
    except Exception:
        logger.exception("diagnostics: collect failed on customize")
        await interaction.response.send_message(
            "Could not run diagnostics — see logs.",
            ephemeral=True,
        )
        return
    embed = build_diagnostics_embed(report)
    view = DiagnosticsSectionView(interaction.user)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    """Diagnostics section entry — shows the section card.

    No auto-recommended path: repairs are mutations the operator should
    stage deliberately after reading the findings, not part of a blanket
    "apply all recommended" sweep.  ``recommended_ops_builder=None`` keeps
    the hub sweep from silently clearing bindings.
    """
    from views.setup.section_card import show

    detected = (
        "Scans bindings, auto-role tiers, moderator roles, and cleanup "
        "policies for broken / stale config. Click Customize to see findings "
        "and stage the safe repairs (Final review applies them)."
    )
    await show(
        interaction,
        hub=hub,
        section=REGISTRY.get(SLUG),  # type: ignore[arg-type]
        detected_state=detected,
        on_customize=_customize_run,
        recommended_ops_builder=None,
    )


async def _build_detail_embed(
    guild: discord.Guild,
    *,
    session: object = None,
    draft_rows: object = None,
) -> discord.Embed:
    """Wizard-native detail embed for the diagnostics step."""
    del session, draft_rows
    report = await setup_diagnostics.collect_setup_diagnostics(guild)
    return build_diagnostics_embed(report)


def _build_detail_view(
    author: discord.Member | discord.User,
    *,
    section: SetupSection,
    guild: discord.Guild,
    session: object = None,
) -> DiagnosticsSectionView:
    """Wizard-native detail view for the diagnostics step."""
    del section, guild, session
    return DiagnosticsSectionView(author)


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Diagnose & repair",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="🩺",
        order=85,
        # ``clear_binding`` is shared with other binding surfaces, so leave
        # op_kinds empty and attribute progress by ``section_slug`` provenance
        # (passed to ``setup_draft.append`` above), matching the moderation
        # section's reasoning.
        op_kinds=frozenset(),
        description_if_skipped=(
            "No configuration diagnostics are run — existing bindings, role "
            "tiers, and cleanup policies keep whatever state they're in. You "
            "can re-run diagnostics later from the wizard or fix issues in "
            "their own panels."
        ),
        depths=frozenset({"standard", "advanced"}),
        recommended_ops_builder=None,
        customize=_customize_run,
        detail_embed_builder=_build_detail_embed,
        detail_view_builder=_build_detail_view,
    ),
)


__all__ = [
    "SLUG",
    "DiagnosticsSectionView",
    "build_diagnostics_embed",
    "run",
]
