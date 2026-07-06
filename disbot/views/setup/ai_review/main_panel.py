"""Main AI review panel — Phase 9f / Track 5 PR 14.

Aggregate view over a :class:`SetupPlanDraft`:

* Lists counts per confidence tier (high/medium/low).
* Lists subsystems with at least one recommendation.
* Offers four buttons:
  * **Accept all high-confidence** — adds every high-confidence
    recommendation to :class:`AcceptedSet`.
  * **Review one-by-one** — transitions to
    :class:`PerRecommendationView`.
  * **Reject all AI suggestions** — clears AI recommendations from
    the draft so only deterministic ones remain.
  * **Rerun deterministic-only** — re-runs the deterministic
    advisor and replaces the draft in place.

No DB writes, no Discord resource creation. The panel only mutates
the in-memory :class:`AcceptedSet` and the in-memory
:class:`SetupPlanDraft`. The wizard hub (Track 8) consumes the
final accepted set and routes through pipelines.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import discord

from services.guild_snapshot import GuildSnapshot
from services.setup_plan import (
    DeterministicAdvisor,
    SetupPlanDraft,
    SetupRecommendation,
)
from views.base import BaseView

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.views.setup.ai_review.main_panel")

_REVIEW_HEADER = "Smart suggestions are recommendations. Review before applying."


@dataclass
class AcceptedSet:
    """Mutable container of recommendations the operator has accepted.

    Lives on the view; the wizard hub reads :attr:`recommendations`
    after the operator closes the review panel.
    """

    recommendations: list[SetupRecommendation] = field(default_factory=list)

    def add(self, rec: SetupRecommendation) -> bool:
        """Add ``rec`` if not already accepted. Returns True if added."""
        key = (rec.subsystem, rec.binding_name)
        if any((r.subsystem, r.binding_name) == key for r in self.recommendations):
            return False
        self.recommendations.append(rec)
        return True

    def add_many(
        self,
        recs: tuple[SetupRecommendation, ...] | list[SetupRecommendation],
    ) -> int:
        added = 0
        for rec in recs:
            if self.add(rec):
                added += 1
        return added

    def clear(self) -> None:
        self.recommendations.clear()

    def remove(self, subsystem: str, binding_name: str) -> bool:
        for i, rec in enumerate(self.recommendations):
            if rec.subsystem == subsystem and rec.binding_name == binding_name:
                del self.recommendations[i]
                return True
        return False

    def contains(self, rec: SetupRecommendation) -> bool:
        return any(
            (r.subsystem, r.binding_name) == (rec.subsystem, rec.binding_name)
            for r in self.recommendations
        )

    @property
    def count(self) -> int:
        return len(self.recommendations)


def build_ai_review_embed(draft: SetupPlanDraft) -> discord.Embed:
    """Render the aggregate review embed for a draft."""
    high = draft.by_confidence("high")
    medium = draft.by_confidence("medium")
    low = draft.by_confidence("low")

    description = (
        f"_{_REVIEW_HEADER}_\n\n"
        f"**High:** {len(high)} · **Medium:** {len(medium)} · "
        f"**Low:** {len(low)} · **Source:** `{draft.source}`"
    )
    color = (
        discord.Color.green()
        if high
        else discord.Color.gold()
        if medium
        else discord.Color.dark_grey()
    )
    embed = discord.Embed(
        title="🤖 Smart suggestions",
        description=description,
        color=color,
    )

    # Group by subsystem for the field section.
    by_sub: dict[str, list[SetupRecommendation]] = {}
    for rec in draft.recommendations:
        by_sub.setdefault(rec.subsystem, []).append(rec)
    for subsystem in sorted(by_sub):
        lines = []
        for rec in by_sub[subsystem]:
            icon = _CONFIDENCE_ICON[rec.confidence]
            # A "create" rec proposes making a new resource (➕); a "bind" rec
            # wires an existing one (→).
            arrow = "→ ➕ create" if getattr(rec, "mode", "bind") == "create" else "→"
            lines.append(
                f"{icon} `{rec.binding_name}` {arrow} `{rec.target_name}` — {rec.reason}",
            )
        value = "\n".join(lines)
        if len(value) > 1000:
            value = value[:997] + "..."
        embed.add_field(
            name=f"{subsystem}",
            value=value,
            inline=False,
        )

    if draft.dropped:
        dropped_value = "\n".join(f"• {d}" for d in draft.dropped[:5])
        if len(draft.dropped) > 5:
            dropped_value += f"\n_+{len(draft.dropped) - 5} more not shown_"
        embed.add_field(
            name="Dropped",
            value=dropped_value,
            inline=False,
        )

    return embed


_CONFIDENCE_ICON = {
    "high": "🟢",
    "medium": "🟡",
    "low": "⚪",
}


class AIReviewPanelView(BaseView):
    """Aggregate AI-review panel.

    Owns the active :class:`SetupPlanDraft` and the
    :class:`AcceptedSet`. Buttons mutate one or both; the wizard
    hub reads :attr:`accepted` after the operator closes the
    panel.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        draft: SetupPlanDraft,
        snapshot: GuildSnapshot | None = None,
        accepted: AcceptedSet | None = None,
        public: bool = False,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.draft = draft
        self.snapshot = snapshot
        self.accepted = accepted if accepted is not None else AcceptedSet()
        self.last_status: str | None = None  # last action label for embed

    def _refresh_embed(self) -> discord.Embed:
        embed = build_ai_review_embed(self.draft)
        if self.last_status:
            embed.set_footer(text=self.last_status)
        return embed

    async def _rerender(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.edit_message(
                embed=self._refresh_embed(),
                view=self,
            )
        except discord.HTTPException:
            logger.warning(
                "AIReviewPanelView._rerender: edit_message failed.",
            )

    @discord.ui.button(
        label="Accept all high-confidence",
        style=discord.ButtonStyle.success,
    )
    async def _accept_high(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        high = self.draft.by_confidence("high")
        added = self.accepted.add_many(high)
        self.last_status = (
            f"Accepted {added} high-confidence recommendation(s); "
            f"total accepted: {self.accepted.count}."
        )
        await self._rerender(interaction)

    @discord.ui.button(
        label="Review one-by-one",
        style=discord.ButtonStyle.primary,
    )
    async def _review_each(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not self.draft.recommendations:
            await interaction.response.send_message(
                "Nothing to review — the draft is empty.",
                ephemeral=True,
            )
            return
        from views.setup.ai_review.per_recommendation import (
            PerRecommendationView,
            build_per_recommendation_embed,
        )

        per_view = PerRecommendationView(
            self._author,
            draft=self.draft,
            accepted=self.accepted,
            index=0,
            parent_view=self,
            public=self._public,
            timeout=self.timeout,
        )
        await interaction.response.edit_message(
            embed=build_per_recommendation_embed(self.draft, 0, self.accepted),
            view=per_view,
        )

    @discord.ui.button(
        label="Reject all AI suggestions",
        style=discord.ButtonStyle.danger,
    )
    async def _reject_ai(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        surviving = tuple(r for r in self.draft.recommendations if r.source != "openai")
        removed = len(self.draft.recommendations) - len(surviving)
        self.draft = SetupPlanDraft(
            recommendations=surviving,
            dropped=self.draft.dropped,
            source="deterministic" if removed else self.draft.source,
        )
        # Also strip rejected AI items from the accepted set.
        self.accepted.recommendations = [
            r for r in self.accepted.recommendations if r.source != "openai"
        ]
        self.last_status = (
            f"Rejected {removed} AI suggestion(s); accepted set "
            f"refreshed to {self.accepted.count}."
        )
        await self._rerender(interaction)

    @discord.ui.button(
        label="Rerun deterministic-only",
        style=discord.ButtonStyle.secondary,
    )
    async def _rerun_deterministic(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if self.snapshot is None:
            await interaction.response.send_message(
                "Cannot rerun deterministic-only: no snapshot stored on this panel.",
                ephemeral=True,
            )
            return
        deterministic = DeterministicAdvisor()
        try:
            self.draft = await deterministic.suggest(self.snapshot)
        except Exception:
            logger.exception(
                "AIReviewPanelView._rerun_deterministic: advisor.suggest failed",
            )
            await interaction.response.send_message(
                "Deterministic rerun failed; the draft is unchanged.",
                ephemeral=True,
            )
            return
        # Drop any AI-sourced accepted items so the accepted set
        # stays consistent with the new deterministic-only draft.
        self.accepted.recommendations = [
            r for r in self.accepted.recommendations if r.source != "openai"
        ]
        self.last_status = (
            f"Deterministic advisor rerun: "
            f"{len(self.draft.recommendations)} recommendation(s); "
            f"accepted set: {self.accepted.count}."
        )
        await self._rerender(interaction)

    @discord.ui.button(
        label="Stage & open Final review",
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def _stage_final(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Stage the accepted recommendations into the per-guild draft and
        open the draft-driven :class:`FinalReviewView`.

        This is the single apply path: Smart Suggestions no longer dead-ends
        on an in-memory ``AcceptedSet``.  The accepted recommendations are
        adapted to :class:`SetupOperation` objects and written through
        :func:`services.setup_draft.replace_recommended_for_section` (the
        sole writer of ``staging_kind='recommended'``), so they show up in
        Final Review alongside anything staged from wizard sections and
        apply through the same audited dispatcher.
        """
        del button
        guild = interaction.guild
        guild_id = interaction.guild_id
        member = interaction.user
        if guild is None or guild_id is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return
        if not self.accepted.recommendations:
            await interaction.response.send_message(
                "Accept at least one suggestion first — use **Accept all "
                "high-confidence** or **Review one-by-one**.",
                ephemeral=True,
            )
            return

        from services import setup_access, setup_draft, setup_session
        from services.setup_operations import operations_from_recommendations

        try:
            session = await setup_session.resume_session(guild_id)
        except Exception:
            logger.exception("AIReviewPanelView._stage_final: resume failed")
            session = None
        if not setup_access.can_apply_setup(member, session):
            await interaction.response.send_message(
                "Only the server owner or a delegated setup admin can stage "
                "setup operations. Ask the owner to grant you `/setup-delegate`.",
                ephemeral=True,
            )
            return

        ops = operations_from_recommendations(list(self.accepted.recommendations))
        try:
            await setup_draft.replace_recommended_for_section(
                guild_id,
                "suggestions",
                ops,
                actor_id=member.id,
                labels={
                    idx: f"[suggestions] {op.subsystem}.{op.kind}"
                    for idx, op in enumerate(ops)
                },
            )
        except Exception:
            logger.exception("AIReviewPanelView._stage_final: staging failed")
            await interaction.response.send_message(
                "Could not stage the accepted suggestions — see logs.",
                ephemeral=True,
            )
            return

        from views.setup.final_review import (
            FinalReviewView,
            build_final_review_embed,
        )

        try:
            draft_ops = await setup_draft.list_ops(guild_id)
        except Exception:
            logger.exception("AIReviewPanelView._stage_final: list_ops failed")
            draft_ops = ops
        final = FinalReviewView(member, ops=draft_ops)
        await interaction.response.edit_message(
            embed=build_final_review_embed(final.ops),
            view=final,
        )


__all__ = [
    "AIReviewPanelView",
    "AcceptedSet",
    "build_ai_review_embed",
]
