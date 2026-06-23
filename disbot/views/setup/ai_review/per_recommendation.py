"""Per-recommendation review view — Phase 9f / Track 5 PR 14.

One-at-a-time walkthrough over a :class:`SetupPlanDraft`. The
operator advances index-by-index and accepts / rejects each
recommendation into the shared :class:`AcceptedSet`.

Buttons:

* **Accept** — adds the current recommendation to :class:`AcceptedSet`
  and advances to the next index.
* **Reject** — removes any existing acceptance and advances.
* **Skip** — advances without changing the accepted set.
* **Back to overview** — returns to :class:`AIReviewPanelView`.

The current index is bounded ``[0, len(recommendations))``. Once
the operator advances past the last recommendation the view
auto-returns to the overview panel.

No DB writes, no Discord resource creation — only state mutations on
the shared :class:`AcceptedSet`.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services.setup_plan import SetupPlanDraft, SetupRecommendation
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.ai_review.main_panel import AcceptedSet, AIReviewPanelView

logger = logging.getLogger("bot.views.setup.ai_review.per_recommendation")


def build_per_recommendation_embed(
    draft: SetupPlanDraft,
    index: int,
    accepted: AcceptedSet,
) -> discord.Embed:
    """Render a single recommendation."""
    total = len(draft.recommendations)
    if total == 0:
        return discord.Embed(
            title="🤖 Smart suggestions",
            description="No recommendations to review.",
            color=discord.Color.dark_grey(),
        )
    safe_index = max(0, min(index, total - 1))
    rec = draft.recommendations[safe_index]
    color = _CONFIDENCE_COLOR[rec.confidence]
    is_accepted = accepted.contains(rec)
    state_label = "✅ accepted" if is_accepted else "⬜ pending"
    # A "create" rec has no existing id — it proposes making the resource and
    # binding it; a "bind" rec wires an existing one (shown with its id).
    if getattr(rec, "mode", "bind") == "create":
        target_line = (
            f"**Create & bind:** ➕ `{rec.target_name}` (new `{rec.target_kind}`)\n"
        )
    else:
        target_line = f"**Target:** `{rec.target_name}` (id `{rec.target_id}`)\n"
    embed = discord.Embed(
        title=(f"🤖 Suggestion {safe_index + 1} / {total} · {state_label}"),
        description=(
            f"**Subsystem:** `{rec.subsystem}`\n"
            f"**Binding:** `{rec.binding_name}` (`{rec.target_kind}`)\n"
            f"{target_line}"
            f"**Confidence:** `{rec.confidence}`\n"
            f"**Source:** `{rec.source}`\n\n"
            f"_{rec.reason}_"
        ),
        color=color,
    )
    embed.set_footer(
        text=f"Accepted set: {accepted.count} · use Skip to defer, Back to return.",
    )
    return embed


_CONFIDENCE_COLOR = {
    "high": discord.Color.green(),
    "medium": discord.Color.gold(),
    "low": discord.Color.dark_grey(),
}


class PerRecommendationView(BaseView):
    """One-at-a-time walkthrough."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        draft: SetupPlanDraft,
        accepted: AcceptedSet,
        index: int = 0,
        parent_view: AIReviewPanelView | None = None,
        public: bool = False,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.draft = draft
        self.accepted = accepted
        self.index = index
        self.parent_view = parent_view

    @property
    def current(self) -> SetupRecommendation | None:
        if 0 <= self.index < len(self.draft.recommendations):
            return self.draft.recommendations[self.index]
        return None

    async def _advance_or_return(
        self,
        interaction: discord.Interaction,
    ) -> None:
        self.index += 1
        if self.index >= len(self.draft.recommendations):
            # End of list — return to overview.
            await self._return_to_overview(interaction)
            return
        await interaction.response.edit_message(
            embed=build_per_recommendation_embed(
                self.draft,
                self.index,
                self.accepted,
            ),
            view=self,
        )

    async def _return_to_overview(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if self.parent_view is None:
            await interaction.response.send_message(
                "Review complete. The accepted set is ready to apply.",
                ephemeral=True,
            )
            return
        from views.setup.ai_review.main_panel import build_ai_review_embed

        self.parent_view.last_status = (
            f"Per-recommendation review finished; "
            f"accepted set: {self.accepted.count}."
        )
        self.parent_view.draft = self.draft
        await interaction.response.edit_message(
            embed=build_ai_review_embed(self.parent_view.draft),
            view=self.parent_view,
        )

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def _accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        rec = self.current
        if rec is None:
            await self._return_to_overview(interaction)
            return
        self.accepted.add(rec)
        await self._advance_or_return(interaction)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def _reject(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        rec = self.current
        if rec is None:
            await self._return_to_overview(interaction)
            return
        self.accepted.remove(rec.subsystem, rec.binding_name)
        await self._advance_or_return(interaction)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary)
    async def _skip(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        await self._advance_or_return(interaction)

    @discord.ui.button(
        label="Back to overview",
        style=discord.ButtonStyle.secondary,
    )
    async def _back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        await self._return_to_overview(interaction)


__all__ = [
    "PerRecommendationView",
    "build_per_recommendation_embed",
]
