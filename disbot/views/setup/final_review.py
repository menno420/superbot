"""Final-review view — the wizard's sole apply gate.

The operator sees every staged operation in one place; clicking
**Apply** routes each through :mod:`services.setup_operations`
(the canonical setup/preset/repair operation dispatcher).

Two construction modes:

* ``FinalReviewView(author, accepted=...)`` — legacy
  recommendation-driven path used by the AI / suggestions panel.
  Recommendations are adapted via
  ``operations_from_recommendations`` and applied.
* ``FinalReviewView(author, ops=...)`` — draft-driven path used
  by the setup wizard's hub Final review section.  Operations come
  from :mod:`services.setup_draft` and apply in canonical phase order:

      1. ``create_*``      (resource provisioning)
      2. ``bind_*`` / ``clear_binding``  (binding mutation)
      3. ``set_setting``   (settings mutation)
      4. ``set_cleanup_policy`` / ``set_cog_routing``  (per-feature
         dispatcher arms; PR 11 wires set_cleanup_policy and
         set_cog_routing remains a follow-up)
      5. ``add_automation_rule``  (created disabled)
      6. ``enable_automation_rule`` / ``disable_automation_rule``

Failures are isolated per operation; one bad op does not abort the
rest.  Unsupported kinds appear in ``skipped`` /
``not_yet_implemented`` partitions rather than raising.
On full success the wizard's draft is cleared and the session is
marked complete.
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


def _is_setup_operation(item: Any) -> bool:
    """Return True if ``item`` looks like a :class:`SetupOperation`."""
    return hasattr(item, "kind") and hasattr(item, "metadata")


def _render_pending_line(item: Any) -> str:
    """Single-line summary of one item — handles both SetupRecommendation
    and SetupOperation shapes.
    """
    if _is_setup_operation(item):
        # Defer to the canonical renderer in views.setup.draft_render so
        # the styling matches everywhere drafts appear.
        from views.setup.draft_render import render_op_line

        return render_op_line(item, getattr(item, "metadata", None) or {})
    # SetupRecommendation
    return (
        f"`{item.subsystem}.{item.binding_name}` → "
        f"`{item.target_name}` ({item.confidence})"
    )


def build_final_review_embed(
    accepted: list[Any] | tuple[Any, ...],
    *,
    summary: ApplySummary | None = None,
) -> discord.Embed:
    """Render the final-review embed.

    Three states: pre-apply (lists what will happen), post-apply
    (shows ``summary`` with applied / failed / skipped counts), or
    "nothing to apply" when ``accepted`` is empty.

    ``accepted`` may be a list of :class:`SetupRecommendation` (legacy
    AI / suggestions flow) or a list of :class:`SetupOperation` (the
    draft-driven flow from the setup wizard hub).  Both render with
    one line per item.
    """
    if not accepted:
        return discord.Embed(
            title="🛰 Final review",
            description=(
                "No staged work yet. Visit a wizard section to stage "
                "the first change, then come back here to apply."
            ),
            color=discord.Color.dark_grey(),
        )

    if summary is None:
        is_ops = bool(accepted) and _is_setup_operation(accepted[0])
        noun = "operation" if is_ops else "recommendation"
        embed = discord.Embed(
            title="🛰 Final review",
            description=(
                f"**{len(accepted)}** {noun}(s) staged. "
                "Click **Apply** to route each through the audit "
                "pipelines."
            ),
            color=discord.Color.blurple(),
        )
        lines = [f"• {_render_pending_line(item)}" for item in accepted[:10]]
        if len(accepted) > 10:
            lines.append(f"_+{len(accepted) - 10} more_")
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
    """Final-review panel: apply or cancel.

    Construct in one of two modes:

    * ``accepted=<list[SetupRecommendation]>`` — recommendation-driven
      apply path (existing AI / Smart suggestions flow).
    * ``ops=<list[SetupOperation]>`` — draft-driven apply path (the
      wizard's hub Final review section reads
      :mod:`services.setup_draft` and passes the list here).
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        accepted: (
            list[SetupRecommendation] | tuple[SetupRecommendation, ...] | None
        ) = None,
        ops: list[Any] | None = None,
        public: bool = False,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.accepted: list[SetupRecommendation] = list(accepted or ())
        self.ops: list[Any] = list(ops or ())
        self.summary: ApplySummary | None = None
        if not self.accepted and not self.ops:
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
        if not self.accepted and not self.ops:
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

        if self.ops:
            summary = await _apply_ops_in_order(
                self.ops,
                guild=guild,
                actor=interaction.user,
            )
            # Clear the draft only when the apply ran end-to-end —
            # mark_complete (below) also calls setup_draft.clear, but
            # we drop the rows defensively here too.
            try:
                from services import setup_draft as _draft

                await _draft.clear(guild.id)
            except Exception:
                logger.exception("FinalReviewView: setup_draft.clear failed")
        else:
            summary = await _apply_accepted(
                self.accepted,
                guild=guild,
                actor=interaction.user,
            )
        self.summary = summary
        embed = build_final_review_embed(
            self.accepted if self.accepted else self.ops,
            summary=summary,
        )
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


# Canonical apply order (matches the wizard's per-feature contract).
# Phases run sequentially; per-op isolation inside each phase remains
# the responsibility of :func:`services.setup_operations.apply_operations`.
_PHASE_ORDER: tuple[tuple[str, frozenset[str]], ...] = (
    (
        "resource_provisioning",
        frozenset({"create_channel", "create_role", "create_category"}),
    ),
    (
        "binding_mutation",
        frozenset(
            {
                "bind_channel",
                "bind_role",
                "bind_category",
                "bind_thread",
                "bind_member",
                "clear_binding",
            },
        ),
    ),
    ("settings_mutation", frozenset({"set_setting"})),
    ("cleanup_policy", frozenset({"set_cleanup_policy"})),
    ("cog_routing", frozenset({"set_cog_routing"})),
    ("automation_add", frozenset({"add_automation_rule"})),
    (
        "automation_toggle",
        frozenset({"enable_automation_rule", "disable_automation_rule"}),
    ),
)


def _sort_ops_for_apply(ops: list[Any]) -> list[Any]:
    """Return ``ops`` partitioned by the canonical phase order.

    The dispatcher is happy to take any order, but Final Review applies
    in phase order so resource creation can complete before the
    binding ops that point at the new resources.  Unknown kinds end up
    in a final "other" bucket and surface as ``not_yet_implemented``.
    """
    buckets: dict[int, list[Any]] = {i: [] for i in range(len(_PHASE_ORDER) + 1)}
    for op in ops:
        kind = getattr(op, "kind", "")
        placed = False
        for idx, (_, kinds) in enumerate(_PHASE_ORDER):
            if kind in kinds:
                buckets[idx].append(op)
                placed = True
                break
        if not placed:
            buckets[len(_PHASE_ORDER)].append(op)
    return [op for idx in sorted(buckets) for op in buckets[idx]]


async def _apply_ops_in_order(
    ops: list[Any],
    *,
    guild: Any,
    actor: Any,
) -> ApplySummary:
    """Apply a draft of :class:`SetupOperation` records in canonical
    phase order.  Returns an :class:`ApplySummary` partitioned the
    same way :func:`_apply_accepted` does.

    Per-op isolation is delegated to
    :func:`services.setup_operations.apply_operations`; per-phase
    isolation comes from applying each phase as its own batch so an
    upstream failure does not abort downstream phases (the operator
    can re-run with the same draft to retry the failed phase only).
    """
    from services.setup_operations import apply_operations

    ordered = _sort_ops_for_apply(ops)

    summary = ApplySummary()
    for op in ordered:
        # Single-op batch keeps each phase boundary visible in the
        # audit + event streams; the dispatcher's per-op isolation
        # logic still applies.
        batch = await apply_operations([op], guild=guild, actor=actor)
        for r in batch.applied:
            summary.applied.append(r.label)
        for r in batch.failed:
            summary.failed.append(
                f"{r.label}: {r.error}" if r.error else r.label,
            )
        for r in batch.skipped:
            summary.skipped.append(r.label)
        for r in batch.not_yet_implemented:
            summary.skipped.append(
                (
                    f"{r.label} (not yet implemented)"
                    if not r.error
                    else f"{r.label}: {r.error}"
                ),
            )
    return summary


async def _apply_accepted(
    recs: list[SetupRecommendation],
    *,
    guild: Any,
    actor: Any,
) -> ApplySummary:
    """Route each recommendation through :mod:`services.setup_operations`.

    Converts recommendations to :class:`~services.setup_operations.SetupOperation`
    objects, delegates to :func:`~services.setup_operations.apply_operations`,
    then maps the :class:`~services.setup_operations.SetupOperationBatchResult`
    back to :class:`ApplySummary` for rendering.

    Failures are isolated per recommendation.  Unsupported or unrecognised
    operation kinds appear in ``skipped`` rather than raising.
    """
    from services.setup_operations import (
        apply_operations,
        operations_from_recommendations,
    )

    ops = operations_from_recommendations(recs)
    batch = await apply_operations(ops, guild=guild, actor=actor)

    summary = ApplySummary()
    for result in batch.applied:
        summary.applied.append(result.label)
    for result in batch.failed:
        summary.failed.append(
            f"{result.label}: {result.error}" if result.error else result.label,
        )
    for result in batch.skipped:
        summary.skipped.append(result.label)
    for result in batch.not_yet_implemented:
        summary.skipped.append(
            (
                f"{result.label} (not yet implemented)"
                if not result.error
                else f"{result.label}: {result.error}"
            ),
        )
    return summary


__all__ = [
    "ApplySummary",
    "FinalReviewView",
    "_apply_ops_in_order",
    "_sort_ops_for_apply",
    "build_final_review_embed",
]
