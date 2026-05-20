"""Final-review view — Phase 9i / Track 8 PR 23.

The last step of the wizard. The operator sees every accepted
:class:`SetupRecommendation` in one place; clicking **Apply**
routes each through the existing mutation pipelines.

Routing:

* All recommendations go through
  :class:`services.binding_mutation.BindingMutationPipeline.set_binding`
  for binding kinds the operator picked from the AI / deterministic
  advisor. Other target kinds (set_setting, create_role, etc.) are
  routed in follow-up polish.
* Failures are isolated per recommendation: one bad binding does
  not abort the rest.
* Pipeline emission of ``audit.action_recorded`` (Track 1 PR 1)
  keeps the audit trail intact without any extra plumbing here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import discord

from services.setup_plan import SetupRecommendation
from views.base import BaseView

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.views.setup.final_review")


@dataclass
class ApplySummary:
    """Outcome of :meth:`FinalReviewView._apply` — surfaced in the
    follow-up embed and the audit log.
    """

    applied: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def build_final_review_embed(
    accepted: list[SetupRecommendation] | tuple[SetupRecommendation, ...],
    *,
    summary: ApplySummary | None = None,
) -> discord.Embed:
    """Render the final-review embed.

    Three states: pre-apply (lists what will happen), post-apply
    (shows ``summary`` with applied / failed / skipped counts), or
    "nothing to apply" when ``accepted`` is empty.
    """
    if not accepted:
        return discord.Embed(
            title="🛰 Final review",
            description=(
                "No recommendations have been accepted yet. Run "
                "**Smart suggestions** first, accept some, and come "
                "back here to apply them."
            ),
            color=discord.Color.dark_grey(),
        )

    if summary is None:
        embed = discord.Embed(
            title="🛰 Final review",
            description=(
                f"**{len(accepted)}** recommendation(s) staged. "
                "Click **Apply** to route each through the audit "
                "pipelines."
            ),
            color=discord.Color.blurple(),
        )
        lines = [
            f"• `{rec.subsystem}.{rec.binding_name}` → "
            f"`{rec.target_name}` ({rec.confidence})"
            for rec in accepted
        ]
        value = "\n".join(lines)
        if len(value) > 1000:
            value = value[:997] + "..."
        embed.add_field(name="Pending", value=value, inline=False)
        embed.set_footer(text="Owner-gated. Nothing has applied yet.")
        return embed

    color = discord.Color.green() if not summary.failed else discord.Color.gold()
    embed = discord.Embed(
        title="🛰 Final review · applied",
        description=(
            f"Applied **{len(summary.applied)}**, "
            f"failed **{len(summary.failed)}**, "
            f"skipped **{len(summary.skipped)}**."
        ),
        color=color,
    )
    if summary.applied:
        embed.add_field(
            name="Applied",
            value="\n".join(f"• {x}" for x in summary.applied[:10])
            + (
                f"\n_+{len(summary.applied) - 10} more_"
                if len(summary.applied) > 10
                else ""
            ),
            inline=False,
        )
    if summary.failed:
        embed.add_field(
            name="Failed",
            value="\n".join(f"• {x}" for x in summary.failed[:10]),
            inline=False,
        )
    if summary.skipped:
        embed.add_field(
            name="Skipped",
            value="\n".join(f"• {x}" for x in summary.skipped[:10]),
            inline=False,
        )
    return embed


class FinalReviewView(BaseView):
    """Final-review panel: apply or cancel."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        accepted: list[SetupRecommendation] | tuple[SetupRecommendation, ...],
        public: bool = False,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.accepted: list[SetupRecommendation] = list(accepted)
        self.summary: ApplySummary | None = None
        if not self.accepted:
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.label == "Apply":
                    child.disabled = True

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.success)
    async def _apply(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not self.accepted:
            await interaction.response.send_message(
                "Nothing to apply.",
                ephemeral=True,
            )
            return
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Final review requires a guild context.",
                ephemeral=True,
            )
            return
        from core.runtime.interaction_helpers import safe_defer

        await safe_defer(interaction, ephemeral=True)

        summary = await _apply_accepted(
            self.accepted,
            guild=guild,
            actor=interaction.user,
        )
        self.summary = summary
        embed = build_final_review_embed(self.accepted, summary=summary)
        try:
            from services import setup_session

            await setup_session.mark_complete(guild.id)
        except Exception:
            logger.exception("FinalReviewView: mark_complete failed")
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        try:
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=embed,
                view=self,
            )
        except discord.HTTPException:
            logger.warning("FinalReviewView: followup edit failed")

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
            content="Final review cancelled — nothing was applied.",
            view=self,
        )
        self.stop()


async def _apply_accepted(
    recs: list[SetupRecommendation],
    *,
    guild: Any,
    actor: Any,
) -> ApplySummary:
    """Route each recommendation through the right pipeline.

    All of v1 uses ``BindingMutationPipeline.set_binding`` because
    the deterministic + AI advisors only produce binding
    recommendations. Settings / role-create flows will route
    through ``SettingsMutationPipeline`` / ``role_automation`` in
    follow-up polish.
    """
    from core.runtime.subsystem_schema import BindingKind
    from services.binding_mutation import BindingMutationPipeline

    summary = ApplySummary()
    pipeline = BindingMutationPipeline()
    for rec in recs:
        try:
            kind_value = (rec.target_kind or "").lower()
            try:
                kind = BindingKind(kind_value)
            except ValueError:
                summary.skipped.append(
                    f"{rec.subsystem}.{rec.binding_name}: unsupported "
                    f"target_kind {kind_value!r}",
                )
                continue
            await pipeline.set_binding(
                guild,
                rec.subsystem,
                rec.binding_name,
                kind,
                rec.target_id,
                actor,
            )
            summary.applied.append(
                f"{rec.subsystem}.{rec.binding_name} → {rec.target_name}",
            )
        except Exception as exc:  # noqa: BLE001 — per-rec boundary
            logger.exception(
                "final_review: failed to apply %s.%s",
                rec.subsystem,
                rec.binding_name,
            )
            summary.failed.append(
                f"{rec.subsystem}.{rec.binding_name}: {type(exc).__name__}: {exc}",
            )
    return summary


__all__ = [
    "ApplySummary",
    "FinalReviewView",
    "build_final_review_embed",
]
