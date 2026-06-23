"""Per-recommendation review view — Phase 9f / Track 5 PR 14.

One-at-a-time walkthrough over a :class:`SetupPlanDraft`. The operator advances
index-by-index, deciding each AI suggestion with the **Accept · Deny · Edit**
controls (the Q-0048 finalize) into the shared :class:`AcceptedSet`.

Buttons:

* **Accept** — adds the current recommendation to :class:`AcceptedSet`
  and advances to the next index.
* **Deny** — removes any existing acceptance and advances.
* **Edit** — for a ``create`` suggestion, opens a modal to rename the resource
  the bot will create, then accepts the edited version and advances. A ``bind``
  suggestion (an existing resource) can't be renamed — Edit explains that.
* **Skip** — advances without changing the accepted set.
* **Back to overview** — returns to :class:`AIReviewPanelView`.

The current index is bounded ``[0, len(recommendations))``. Once the operator
advances past the last recommendation the view auto-returns to the overview.

No DB writes, no Discord resource creation — only state mutations on the shared
:class:`AcceptedSet` and the in-memory draft. The accepted (possibly edited)
operations apply only later, through the gated Final Review.
"""

from __future__ import annotations

import dataclasses
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
    edit_hint = (
        " · Edit to rename before accepting"
        if getattr(rec, "mode", "bind") == "create"
        else ""
    )
    embed.set_footer(
        text=(
            f"Accepted set: {accepted.count} · Accept / Deny / Edit"
            f"{edit_hint} · Skip to defer, Back to return."
        ),
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

    def apply_edit(
        self,
        old: SetupRecommendation,
        new_name: str,
    ) -> SetupRecommendation:
        """Rewrite the current ``create`` recommendation's target name in place.

        Swaps the edited copy into both this view's draft and the parent
        overview's draft (so the change survives the return), then accepts the
        edited recommendation. Pure in-memory state mutation — no DB write, no
        Discord resource creation (the edited op still applies only through the
        gated Final Review). Returns the edited recommendation.
        """
        edited = dataclasses.replace(old, target_name=new_name)
        recs = list(self.draft.recommendations)
        if 0 <= self.index < len(recs):
            recs[self.index] = edited
        self.draft = dataclasses.replace(self.draft, recommendations=tuple(recs))
        if self.parent_view is not None:
            self.parent_view.draft = self.draft
        # Reflect the edit in the accepted set: drop any prior acceptance of this
        # binding, then accept the edited version.
        self.accepted.remove(old.subsystem, old.binding_name)
        self.accepted.add(edited)
        return edited

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, row=0)
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

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, row=0)
    async def _deny(
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

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary, row=0)
    async def _edit(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        rec = self.current
        if rec is None:
            await self._return_to_overview(interaction)
            return
        # Edit rewrites the name of a resource the bot will CREATE. A "bind"
        # suggestion points at an existing resource — we never rename those, so
        # editing it would mislabel; tell the operator to Deny + rebind instead.
        if getattr(rec, "mode", "bind") != "create":
            await interaction.response.send_message(
                f"**Edit** only changes the name of a `{rec.target_kind}` the bot "
                f"will create. This suggestion binds an existing `{rec.target_kind}` "
                f"(`{rec.target_name}`) — **Deny** it and bind a different one if "
                "it isn't right.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(_EditRecommendationModal(self, rec))

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, row=1)
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
        row=1,
    )
    async def _back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        await self._return_to_overview(interaction)


class _EditRecommendationModal(discord.ui.Modal, title="Edit suggestion"):
    """Edit the name of a ``create`` suggestion before accepting it.

    A single text field pre-filled with the AI-proposed name. On submit it
    rewrites the recommendation (via :meth:`PerRecommendationView.apply_edit`),
    accepts the edited version, and advances the walkthrough. No DB / Discord
    writes — the edit only changes what the gated Final Review will create.
    """

    def __init__(
        self,
        view: PerRecommendationView,
        rec: SetupRecommendation,
    ) -> None:
        super().__init__()
        self._view = view
        self._rec = rec
        self.name_input: discord.ui.TextInput = discord.ui.TextInput(
            label=f"{rec.target_kind.title()} name to create",
            default=rec.target_name,
            min_length=1,
            max_length=100,
            required=True,
        )
        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        new_name = self.name_input.value.strip()
        if not new_name:
            await interaction.response.send_message(
                "The name can't be empty — nothing was changed.",
                ephemeral=True,
            )
            return
        self._view.apply_edit(self._rec, new_name)
        await self._view._advance_or_return(interaction)


__all__ = [
    "PerRecommendationView",
    "build_per_recommendation_embed",
]
