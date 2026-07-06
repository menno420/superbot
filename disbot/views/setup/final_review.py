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
      4. ``set_cleanup_policy`` / ``set_cog_routing`` /
         ``set_role_threshold``  (per-feature dispatcher arms — all
         wired through :mod:`services.setup_operations`)
      5. ``add_automation_rule``  (created disabled)
      6. ``enable_automation_rule`` / ``disable_automation_rule``

Failures are isolated per operation; one bad op does not abort the
rest.  Unsupported kinds appear in ``skipped`` /
``not_yet_implemented`` partitions rather than raising.

Safety invariants (Phase 0):

* ``_apply`` runs under a per-guild
  :func:`services.setup_operations.acquire_setup_apply_lock` so
  double-clicks and concurrent presses cannot run two apply batches.
* The draft is cleared and the session marked complete **only when
  every operation succeeded**.  Any ``failed`` / ``skipped`` /
  ``not_yet_implemented`` (the last folded into ``skipped`` by
  :func:`_apply_ops_in_order`) preserves the draft and mounts the
  partial-apply recovery view so the operator can retry or cancel.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import discord

from services import setup_access, setup_session
from services.setup_plan import SetupRecommendation
from views.base import BaseView

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.views.setup.final_review")


async def _gate_apply(interaction: discord.Interaction) -> bool:
    """Reject callers who don't satisfy ``can_apply_setup`` now.

    Module-level helper shared by :class:`FinalReviewView` and
    :class:`PartialApplyRecoveryView`.  The :class:`BaseView` author
    gate already restricts the panel to the user who opened it, but
    this layer re-checks the access tier against a fresh
    :class:`SetupSession` so a delegated admin who lost delegation
    between opening Final Review and pressing the button cannot
    apply.
    """
    member = interaction.user
    if not isinstance(member, discord.Member):
        await interaction.response.send_message(
            "Use this from inside the server.",
            ephemeral=True,
        )
        return False
    session = None
    guild_id = interaction.guild_id
    if guild_id is not None:
        try:
            session = await setup_session.resume_session(guild_id)
        except Exception:
            logger.exception("final_review._gate_apply: resume failed")
            session = None
    if not setup_access.can_apply_setup(member, session):
        await interaction.response.send_message(
            "Only the server owner or a delegated setup admin can apply "
            "staged setup operations. Ask the server owner to grant you "
            "`/setup-delegate`.",
            ephemeral=True,
        )
        return False
    return True


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


# Op kinds that *create* a Discord resource (vs. binding an existing one).
# Mirrors the resource-provisioning phase of :data:`_PHASE_ORDER`.
_CREATE_OP_KINDS: frozenset[str] = frozenset(
    {"create_channel", "create_role", "create_category"},
)


def _created_resource_names(accepted: list[Any] | tuple[Any, ...]) -> list[str]:
    """Names of resources a staged plan would CREATE (not just bind).

    Handles both staged shapes: a :class:`SetupOperation` (``kind`` in the
    create set → ``resource_name``) and a :class:`SetupRecommendation`
    (``mode == "create"`` → ``target_name``). Returns the display names so the
    apply screen can call out exactly what will be made before the operator
    commits — creating channels/roles is higher-impact than binding, so it
    should never be rubber-stamped.
    """
    names: list[str] = []
    for item in accepted:
        if getattr(item, "kind", None) in _CREATE_OP_KINDS:
            names.append(str(getattr(item, "resource_name", None) or "?"))
        elif getattr(item, "mode", "bind") == "create":
            names.append(str(getattr(item, "target_name", None) or "?"))
    return names


def build_final_review_embed(
    accepted: list[Any] | tuple[Any, ...],
    *,
    summary: ApplySummary | None = None,
) -> discord.Embed:
    """Render the final-review embed.

    Three states: pre-apply (lists what will happen), post-apply
    (shows ``summary`` with applied / failed / skipped counts), or
    "nothing to apply" when ``accepted`` is empty.

    Post-apply branch surfaces a distinct **partial-apply** state when
    ``summary.failed`` or ``summary.skipped`` is non-empty: title and
    description make clear that setup is NOT complete and the
    operator's draft has been preserved.

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
                "Final review — **nothing has changed yet**.  "
                f"**{len(accepted)}** {noun}(s) are staged and ready to "
                "apply.  Click **Apply staged setup** to route each "
                "through the audit pipelines."
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
        # Call out resource CREATION distinctly: creating channels/roles is
        # higher-impact + harder to undo than binding existing ones, so the
        # operator should see the count + names before committing.
        created = _created_resource_names(accepted)
        if created:
            shown = ", ".join(f"`{n}`" for n in created[:10])
            if len(created) > 10:
                shown += f" _+{len(created) - 10} more_"
            embed.add_field(
                name=f"➕ {len(created)} new resource(s) will be created",
                value=(
                    f"Applying this plan **creates** these and binds them: {shown}. "
                    "Binding an existing resource is reversible; a created "
                    "channel/role/category is new and must be deleted to undo."
                ),
                inline=False,
            )
        # No-rollback caveat (plan §D3): apply has no automatic undo.
        # Operations run through idempotent pipelines in phase order; if
        # one fails midway, the ones already applied stay applied.
        embed.add_field(
            name="⚠️ Heads-up",
            value=(
                "Apply has **no automatic rollback**. Each operation commits "
                "through its pipeline in order; if one fails partway, earlier "
                "ones stay applied and you'll be able to retry the rest."
            ),
            inline=False,
        )
        embed.set_footer(text="Owner-gated. Nothing has applied yet.")
        return embed

    partial = bool(summary.failed) or bool(summary.skipped)
    if partial:
        color = discord.Color.gold()
        title = "🛰 Final review · partially applied"
        description = (
            "**Setup partially applied.**  Some changes succeeded, but "
            "setup is **not** complete.  Your remaining draft has been "
            "preserved so you can retry or cancel.\n\n"
            f"Applied **{len(summary.applied)}**, "
            f"failed **{len(summary.failed)}**, "
            f"skipped **{len(summary.skipped)}**."
        )
    else:
        color = discord.Color.green()
        title = "🛰 Setup complete"
        description = (
            f"**Setup complete.**  Applied **{len(summary.applied)}** "
            "operation(s); nothing failed or was skipped."
        )
    embed = discord.Embed(title=title, description=description, color=color)
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
    if partial:
        embed.set_footer(
            text=(
                "Draft preserved. Retry re-runs the failed/skipped operations; "
                "Cancel leaves the draft for later. Note: Cancel does NOT undo "
                "operations that already applied."
            ),
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
                # Disable the primary Apply button when there's nothing
                # to apply.  Match by custom_id so renaming the label
                # in copy passes (Phase 7) doesn't decouple this.
                if (
                    isinstance(child, discord.ui.Button)
                    and getattr(child, "custom_id", None) == "setup_final_review:apply"
                ):
                    child.disabled = True

    @discord.ui.button(
        label="Apply staged setup",
        style=discord.ButtonStyle.success,
        custom_id="setup_final_review:apply",
    )
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
                "This can only be used in a server.",
                ephemeral=True,
            )
            return
        if not await _gate_apply(interaction):
            return
        from core.runtime.interaction_helpers import safe_defer
        from services.setup_operations import (
            SetupApplyInProgressError,
            acquire_setup_apply_lock,
        )

        # Single-flight gate.  The check + add inside
        # acquire_setup_apply_lock is atomic under asyncio, so the
        # losing interaction (second click / second user) never even
        # enters the apply block.
        try:
            async with acquire_setup_apply_lock(guild.id):
                await safe_defer(interaction, ephemeral=True)
                await self._run_apply(interaction, guild=guild)
        except SetupApplyInProgressError:
            await interaction.response.send_message(
                "Setup apply is already in progress — wait for the result "
                "message before retrying.",
                ephemeral=True,
            )
            return

    async def _run_apply(
        self,
        interaction: discord.Interaction,
        *,
        guild: Any,
    ) -> None:
        """Run the apply batch under the held single-flight lock.

        Splits out of :meth:`_apply` so the lock acquire/release is
        readable as one ``async with`` block.  Caller is responsible
        for having already deferred the interaction.
        """
        if self.ops:
            summary = await _apply_ops_in_order(
                self.ops,
                guild=guild,
                actor=interaction.user,
            )
        else:
            summary = await _apply_accepted(
                self.accepted,
                guild=guild,
                actor=interaction.user,
            )
        self.summary = summary

        # Full success only: clear draft + mark complete.  Any
        # failed / skipped (not_yet_implemented folds into skipped
        # via :func:`_apply_ops_in_order`) preserves the draft and
        # mounts the recovery view.
        full_success = not summary.failed and not summary.skipped
        if full_success and self.ops:
            try:
                from services import setup_draft as _draft

                await _draft.clear(guild.id)
            except Exception:
                logger.exception("FinalReviewView: setup_draft.clear failed")
            try:
                from services import setup_session

                await setup_session.mark_complete(guild.id)
            except Exception:
                logger.exception("FinalReviewView: mark_complete failed")
        elif full_success and self.accepted:
            # Legacy recommendation-driven path: no draft to clear,
            # but still mark the session complete on full success.
            try:
                from services import setup_session

                await setup_session.mark_complete(guild.id)
            except Exception:
                logger.exception("FinalReviewView: mark_complete failed")

        embed = build_final_review_embed(
            self.accepted if self.accepted else self.ops,
            summary=summary,
        )
        if full_success and self.ops:
            # Phase 8: full-success draft-driven branch mounts the
            # SetupCompleteView so the operator can either delete
            # the now-empty setup channel or keep it.  The legacy
            # recommendation-driven full-success path (``self.ops``
            # empty) just disables the original buttons — there's
            # no per-guild setup channel to clean up in that flow.
            view: discord.ui.View | None = SetupCompleteView(
                interaction.user,
                summary=summary,
            )
        elif full_success or not self.ops:
            for child in self.children:
                child.disabled = True  # type: ignore[attr-defined]
            view = self
        else:
            # Partial-failure draft-driven branch: replace the view
            # with the recovery surface so the operator can retry
            # or cancel.  The original Apply / Cancel buttons go
            # away — they are no longer the right next actions.
            # Partial-recovery flows NEVER offer the cleanup buttons
            # (the plan explicitly forbids that).
            view = PartialApplyRecoveryView(
                interaction.user,
                ops=self.ops,
                accepted=self.accepted,
                summary=summary,
            )
        try:
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=embed,
                view=view,
            )
        except discord.HTTPException:
            logger.warning("FinalReviewView: followup edit failed")

    @discord.ui.button(
        label="🧠 Ask AI to review",
        style=discord.ButtonStyle.secondary,
        custom_id="setup_final_review:ai_review",
    )
    async def _ai_review(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Optional, advisory-only AI review of the current setup (plan §D3).

        Reads a guild snapshot and asks the configured advisor (deterministic
        by default) for suggestions, then shows them as an **ephemeral**
        message.  It never stages, applies, or mutates anything — the staged
        draft is untouched — and it never blocks: any failure degrades to a
        friendly "couldn't run" notice via :func:`review_draft`.
        """
        del button
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return
        from core.runtime.interaction_helpers import safe_defer
        from services.setup_advisor_review import review_draft

        await safe_defer(interaction, ephemeral=True)
        review = await review_draft(guild)
        embed = discord.Embed(
            title="🧠 AI setup review",
            description=review.summary,
            color=(
                discord.Color.blurple() if review.ok else discord.Color.light_grey()
            ),
        )
        if review.lines:
            value = "\n".join(f"• {line}" for line in review.lines)
            embed.add_field(name="Suggestions", value=value[:1000], inline=False)
        embed.set_footer(
            text=(
                f"Advisory only ({review.provider}) — nothing has been staged "
                "or applied. Use the wizard to make any changes yourself."
            ),
        )
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            logger.warning("FinalReviewView: AI review followup failed")

    @discord.ui.button(
        label="Edit setup",
        style=discord.ButtonStyle.secondary,
        custom_id="setup_final_review:edit",
    )
    async def _edit(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Close the ephemeral so the operator can return to the wizard
        anchor (or hub) and re-stage / edit before applying.

        Final Review is opened as an ephemeral follow-up; the wizard /
        hub anchor message stays visible underneath.  This button just
        signals "I want to keep editing" — closing the ephemeral
        returns the operator to the anchor without any side effect.
        """
        del button
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content=(
                "Closed Final review — open the wizard or hub above to "
                "edit your staged operations.  Nothing has been applied."
            ),
            view=self,
        )
        self.stop()

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        custom_id="setup_final_review:back",
    )
    async def _back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Navigation alias for :meth:`_edit`.

        ``Back`` reads more naturally from the wizard's flow ("go back
        to the wizard") while ``Edit setup`` reads more naturally from
        the hub.  Both close the ephemeral with the same side-effect.
        """
        del button
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content=(
                "Closed Final review — your wizard / hub anchor is "
                "still open above.  Nothing has been applied."
            ),
            view=self,
        )
        self.stop()

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        custom_id="setup_final_review:cancel",
    )
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
    ("role_threshold", frozenset({"set_role_threshold"})),
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


class PartialApplyRecoveryView(BaseView):
    """View shown after a partial Final Review apply.

    The draft is preserved (Phase 0 safety guarantee).  The operator
    chooses between:

    * **Retry** — re-run the apply path.  Goes through the same
      single-flight lock and renders a fresh summary embed (which
      may itself be partial or full success).  The dispatcher's
      idempotency guarantees and the resource pipeline's reuse
      semantics (mode=use_existing on retry, where appropriate)
      ensure successful rows don't double-apply.
    * **Cancel** — close the recovery view without changes; the
      operator can re-open Final review later to retry or edit the
      draft.

    * **Finish anyway** — drop the remaining staged ops (including the
      failed / skipped ones) and mark setup complete.  This is the
      escape hatch for the partial-apply stickiness trap: an op that
      can never apply (unsupported kind, permanently missing
      permission) would otherwise keep the wizard on "partially
      applied" forever, because the draft is only cleared on a fully
      successful apply.  The already-applied ops stay applied; the
      operator can re-run ``/setup`` to revisit what was dropped.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        ops: list[Any],
        accepted: list[SetupRecommendation] | tuple[SetupRecommendation, ...],
        summary: ApplySummary,
        public: bool = False,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.ops: list[Any] = list(ops or ())
        self.accepted: list[SetupRecommendation] = list(accepted or ())
        self.summary = summary

    @discord.ui.button(label="Retry", style=discord.ButtonStyle.primary)
    async def _retry(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return
        if not await _gate_apply(interaction):
            return
        from core.runtime.interaction_helpers import safe_defer
        from services.setup_operations import (
            SetupApplyInProgressError,
            acquire_setup_apply_lock,
        )

        try:
            async with acquire_setup_apply_lock(guild.id):
                await safe_defer(interaction, ephemeral=True)
                # Rebuild a FinalReviewView so the canonical apply
                # flow runs — same lock acquisition, same draft
                # clear / mark_complete guarding, same partial
                # recovery branch on second failure.
                retry = FinalReviewView(
                    interaction.user,
                    ops=self.ops,
                    accepted=self.accepted,
                )
                await retry._run_apply(interaction, guild=guild)
                self.summary = retry.summary
        except SetupApplyInProgressError:
            await interaction.response.send_message(
                "Setup apply is already in progress — wait for the result "
                "message before retrying.",
                ephemeral=True,
            )
            return

    @discord.ui.button(label="Finish anyway", style=discord.ButtonStyle.secondary)
    async def _finish_anyway(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Drop the remaining staged ops and mark setup complete.

        Escape hatch for the partial-apply stickiness trap.  The
        already-applied ops stay applied; the failed / skipped ones are
        dropped from the draft so a single un-appliable op cannot keep
        the wizard stuck on "partially applied" forever.
        """
        del button
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return
        if not await _gate_apply(interaction):
            return
        try:
            from services import setup_draft as _draft

            await _draft.clear(guild.id)
        except Exception:
            logger.exception(
                "PartialApplyRecoveryView._finish_anyway: clear failed",
            )
        try:
            from services import setup_session as _session

            await _session.mark_complete(guild.id)
        except Exception:
            logger.exception(
                "PartialApplyRecoveryView._finish_anyway: mark_complete failed",
            )
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        dropped = len(self.summary.failed) + len(self.summary.skipped)
        noun = "operation" if dropped == 1 else "operations"
        embed = discord.Embed(
            title="🛰 Setup finished (with skips)",
            description=(
                f"Applied **{len(self.summary.applied)}** operation(s). "
                f"Dropped **{dropped}** un-appliable {noun} from the draft. "
                "Re-run `/setup` any time to revisit them."
            ),
            color=discord.Color.gold(),
        )
        await interaction.response.edit_message(embed=embed, view=self)
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
            content=(
                "Recovery cancelled — your draft is preserved. Re-open "
                "Final review when you're ready to retry."
            ),
            view=self,
        )
        self.stop()


class SetupCompleteView(BaseView):
    """Post-apply view shown when Final Review applies cleanly.

    Phase 8 of the setup-wizard plan.  Two buttons:

    * **Delete now** — calls
      :func:`services.setup_channel.cleanup_setup_channel_after_completion`.
      On success the embed flips to "Setup channel deleted" and the
      view stops; on a guard failure the operator sees an ephemeral
      with the typed reason and the buttons stay clickable.
    * **Keep setup channel** — closes the view without deletion; the
      channel stays around for the next ``/setup``.

    Both buttons re-check :func:`services.setup_access.can_apply_setup`
    against a fresh session snapshot.  The plan explicitly forbids
    showing these buttons on the partial-failure / recovery branch —
    :meth:`FinalReviewView._run_apply` only mounts this view on the
    ``full_success and self.ops`` branch.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        summary: ApplySummary,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.summary = summary
        self._populate_buttons()

    def _populate_buttons(self) -> None:
        delete_btn: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Delete now",
            style=discord.ButtonStyle.danger,
            custom_id="setup_complete:delete",
            row=0,
        )
        delete_btn.callback = self._on_delete  # type: ignore[method-assign]
        self.add_item(delete_btn)

        keep_btn: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Keep setup channel",
            style=discord.ButtonStyle.secondary,
            custom_id="setup_complete:keep",
            row=0,
        )
        keep_btn.callback = self._on_keep  # type: ignore[method-assign]
        self.add_item(keep_btn)

    async def _on_delete(self, interaction: discord.Interaction) -> None:
        if not await _gate_apply(interaction):
            return
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return

        # ACK the interaction *before* the destructive delete below.
        # ``cleanup_setup_channel_after_completion`` deletes the very
        # channel this view's message lives in.  Once that channel is
        # gone, ``response.edit_message`` 404s (message gone) AND a
        # not-yet-acknowledged ``followup`` 404s with "Unknown Webhook"
        # (10015) — the interaction was never ACKed, so its webhook is
        # invalid.  Deferring ephemerally while the channel + token are
        # still live keeps the followup webhook alive for the
        # confirmation message.  (Regression: clicking "Delete now"
        # crashed with NotFound 404 Unknown Webhook.)
        from core.runtime.interaction_helpers import safe_defer

        if not await safe_defer(interaction, ephemeral=True):
            return

        from services import setup_channel as _setup_channel
        from services import setup_session as _setup_session

        try:
            session = await _setup_session.resume_session(guild.id)
        except Exception:
            logger.exception("SetupCompleteView._on_delete: resume failed")
            await interaction.followup.send(
                "Couldn't read the setup session — see logs.",
                ephemeral=True,
            )
            return

        result = await _setup_channel.cleanup_setup_channel_after_completion(
            guild,
            session,
            actor=interaction.user,
        )
        if result.reason != "ok":
            # Channel was NOT deleted (typed guard failure).  The original
            # message + buttons survive; surface the reason ephemerally and
            # leave the buttons clickable so the operator can retry.
            await interaction.followup.send(
                f"⚠️ {result.detail}",
                ephemeral=True,
            )
            return

        # Success — the setup channel (and this view's message) is gone,
        # so there is nothing left to edit.  Confirm via an ephemeral
        # followup and stop the view.
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        try:
            await interaction.followup.send(
                "✅ Setup channel deleted.  "
                f"Applied **{len(self.summary.applied)}** operation(s); "
                "re-run `/setup` later to recreate it.",
                ephemeral=True,
            )
        except discord.HTTPException:
            logger.info(
                "SetupCompleteView._on_delete: confirmation followup failed",
            )
        self.stop()

    async def _on_keep(self, interaction: discord.Interaction) -> None:
        if not await _gate_apply(interaction):
            return
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            "✅ Setup channel kept.  Re-run `/setup` any time to revisit the wizard.",
            ephemeral=True,
        )
        self.stop()


__all__ = [
    "ApplySummary",
    "FinalReviewView",
    "PartialApplyRecoveryView",
    "SetupCompleteView",
    "_apply_ops_in_order",
    "_sort_ops_for_apply",
    "build_final_review_embed",
]
