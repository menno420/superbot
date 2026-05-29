"""Linear setup wizard — step-by-step section walkthrough.

Phase 3 of the setup-wizard plan.  Replaces the registry-driven hub
as the default ``/setup`` / ``!setup`` entry point with a guided
linear UX: one section per step, navigation buttons, "nothing
changes until Final Review" reassurance, and a final step that opens
:class:`views.setup.final_review.FinalReviewView`.

Architecture
------------

* :class:`LinearWizardView` is the short-lived per-interaction view.
  It does NOT persist across bot restarts; on a stale interaction
  after restart, the launcher cog falls back to "this setup message
  has expired — run ``/setup`` again" and the next ``/setup``
  edits the existing anchor message in place.
* The wizard is the **view layer only** — it stages draft operations
  through :func:`services.setup_draft.replace_recommended_for_section`
  (Phase 0 / Phase 2 helper), reads progress via
  :mod:`services.setup_progress`, and gates every mutating button
  through :func:`services.setup_access.can_apply_setup`.
* The hub continues to exist as an expert / advanced entry point
  reached via ``/setup-hub``.  The wizard no longer carries a button
  to it — the hub's own ``↩ Back to wizard`` button is the return
  path for operators who chose to open the hub explicitly.

Lifecycle
---------

1. ``/setup`` / ``!setup`` resolves the session, ensures
   ``#superbot-setup`` exists, and routes through
   :func:`open_setup_workspace`.
2. :func:`open_setup_workspace` posts (or edits in place) one
   anchor message in ``#superbot-setup`` and writes its id back to
   the session via :func:`services.setup_session.set_setup_message_id`.
3. The invoking channel receives an ephemeral / transient pointer
   reply with a jump link to the anchor.
4. Button presses on the anchor update :attr:`LinearWizardView.step`
   in place; the helpers re-render the embed without changing the
   anchor's id.

Skip semantics (Phase 3)
------------------------

``Skip`` writes the section's slug to
:attr:`SetupSession.skipped_sections` via
:func:`services.setup_session.mark_section_skipped`.  When the
section has Phase-0 provenance (rows with ``section_slug`` set),
those rows are also deleted from the draft so Final Review never
applies an op the operator chose to skip.  Without provenance the
delete is best-effort and a confirmation message warns the operator
that stale rows may remain (Phase 4+ removes that gap).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import (
    setup_access,
    setup_channel,
    setup_draft,
    setup_progress,
    setup_session,
)
from services.setup_sections import REGISTRY, SetupSection
from services.setup_session import SetupSession
from views.base import BaseView
from views.setup._anchor import push_setup_notice
from views.setup.section_card import call_recommended_ops_builder

if TYPE_CHECKING:
    from services.setup_draft import DraftOperationRow

logger = logging.getLogger("bot.views.setup.wizard")


_WIZARD_TITLE = "🛰 SuperBot setup wizard"
_FOOTER_HINT = "Nothing changes until Final Review applies the staged operations."


def _resolve_sections(session: SetupSession | None) -> list[SetupSection]:
    """Return the depth-filtered section list for ``session``.

    Imports the sections package for its registration side effect first.
    The registry is populated when ``views.setup.sections`` is imported,
    and the wizard entry path (``/setup`` / ``!setup``) does not otherwise
    import it — historically only the hub did. Without this, a process
    that opens the wizard before ever touching the hub sees an empty
    registry and renders "No setup sections available for this depth".
    The import is idempotent and cached after the first call.
    """
    import views.setup.sections  # noqa: F401 — populate REGISTRY

    depth = session.depth if session is not None else None
    return REGISTRY.for_depth(depth)


def _step_index_for(
    session: SetupSession | None,
    sections: list[SetupSection],
) -> int:
    """Return the index of ``session.current_step`` in ``sections``.

    Falls back to 0 (first step) when the session is missing, has no
    ``current_step``, or the recorded step no longer exists in the
    depth-filtered registry (e.g. operator switched depth between runs).
    """
    if session is None or not session.current_step:
        return 0
    for idx, section in enumerate(sections):
        if section.slug == session.current_step:
            return idx
    return 0


def _short_state_for(
    section: SetupSection,
    draft_rows: list[DraftOperationRow],
) -> str:
    """Return a one-line summary of the section's current staged state.

    Reads provenance-matched rows from ``draft_rows`` (the typed
    wrapper) and returns ``"N op(s) staged"`` plus a hint when the
    rows are recommended-staged.  Empty for sections with no matching
    rows so the embed stays compact.
    """
    matching = [
        row
        for row in draft_rows
        if (row.section_slug == section.slug)
        or (row.section_slug is None and row.op.kind in section.op_kinds)
    ]
    if not matching:
        return ""
    count = len(matching)
    noun = "operation" if count == 1 else "operations"
    if all(row.staging_kind == "recommended" for row in matching):
        return f"{count} recommended {noun} staged"
    if all((row.staging_kind or "manual") != "recommended" for row in matching):
        return f"{count} customised {noun} staged"
    return f"{count} {noun} staged ({count} mixed)"


def build_wizard_step_embed(
    *,
    session: SetupSession | None,
    section: SetupSection,
    step_index: int,
    total_steps: int,
    draft_rows: list[DraftOperationRow],
) -> discord.Embed:
    """Build the embed shown at wizard step ``step_index``.

    Fields:

    * **Detected** — one-line summary of the section's current staged
      state, derived from ``draft_rows``.
    * **Recommended action** — copy that describes what
      ``Apply Recommended`` will do for this section.  Empty when the
      section has no ``recommended_ops_builder``.
    * **If you skip this** — pulled from
      :attr:`SetupSection.description_if_skipped`.  Empty when the
      section author hasn't supplied skip-impact text yet.
    """
    glyph_status = setup_progress.compute_section_status(
        section,
        session=session,
        draft_ops=draft_rows,
    )
    glyph = setup_progress.badge_for(glyph_status.status)
    skipped = session is not None and section.slug in session.skipped_sections
    completed = session is not None and section.slug in session.acknowledged_sections

    title = f"{_WIZARD_TITLE} · Step {step_index + 1}/{total_steps}"
    if skipped:
        accent = discord.Color.dark_grey()
    elif completed or glyph_status.status.value == "recommended":
        accent = discord.Color.green()
    elif glyph_status.status.value == "customized":
        accent = discord.Color.gold()
    else:
        accent = discord.Color.blurple()
    embed = discord.Embed(
        title=title,
        description=(
            f"{glyph} **{section.label}** "
            f"({glyph_status.status.value.replace('_', ' ')})"
        ),
        color=accent,
    )

    detected = _short_state_for(section, draft_rows)
    embed.add_field(
        name="Current state",
        value=detected or "_(nothing staged for this step yet)_",
        inline=False,
    )

    if section.recommended_ops_builder is not None:
        embed.add_field(
            name="Recommended action",
            value=(
                "Click **Apply Recommended** to stage this section's safe "
                "defaults.  Nothing applies until **Final Review** confirms."
            ),
            inline=False,
        )
    else:
        embed.add_field(
            name="Recommended action",
            value=(
                "_(no recommended defaults — use Customize to open the "
                "section's detail view.)_"
            ),
            inline=False,
        )

    if section.description_if_skipped:
        embed.add_field(
            name="If you skip this",
            value=section.description_if_skipped,
            inline=False,
        )

    embed.set_footer(text=_FOOTER_HINT)
    return embed


class LinearWizardView(BaseView):
    """One-step-at-a-time wizard view.

    Mutating buttons (``Apply Recommended``, ``Skip``) re-check
    :func:`services.setup_access.can_apply_setup` against a fresh
    session snapshot, mirroring the section card's per-button gate
    from Phase 1.  Navigation buttons (``Back``, ``Continue``,
    ``Cancel``) are not gated — they only mutate view-local state.

    The view does not own the anchor message; the caller (typically
    :func:`open_setup_workspace`) edits the message after each
    button press to re-render the new step. Anchor rebuilds go
    through :func:`views.setup.wizard_nav.render_wizard_step`.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        session: SetupSession | None,
        sections: list[SetupSection],
        step_index: int,
        timeout: int = 600,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.session = session
        self.sections = sections
        self.step_index = step_index
        self._rebuild_buttons()

    @property
    def current_section(self) -> SetupSection | None:
        if not self.sections:
            return None
        if self.step_index < 0 or self.step_index >= len(self.sections):
            return None
        return self.sections[self.step_index]

    def _rebuild_buttons(self) -> None:
        """Repopulate the button row based on the current step.

        Called at construction and after every navigation step so the
        button enabled/disabled state and the conditional last-step
        ``Final review`` button reflect the operator's position.
        """
        self.clear_items()
        section = self.current_section

        back: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="◀ Back",
            style=discord.ButtonStyle.secondary,
            custom_id="setup_wizard:back",
            disabled=self.step_index <= 0,
            row=0,
        )
        back.callback = self._on_back  # type: ignore[method-assign]
        self.add_item(back)

        apply_recommended: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Apply Recommended",
            style=discord.ButtonStyle.success,
            custom_id="setup_wizard:apply_recommended",
            disabled=(section is None or section.recommended_ops_builder is None),
            row=0,
        )
        apply_recommended.callback = self._on_apply_recommended  # type: ignore[method-assign]
        self.add_item(apply_recommended)

        customize_disabled = section is None or (
            section.customize is None
            and (
                section.detail_embed_builder is None
                or section.detail_view_builder is None
            )
        )
        customize: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Customize",
            style=discord.ButtonStyle.primary,
            custom_id="setup_wizard:customize",
            disabled=customize_disabled,
            row=0,
        )
        customize.callback = self._on_customize  # type: ignore[method-assign]
        self.add_item(customize)

        skip: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Skip",
            style=discord.ButtonStyle.secondary,
            custom_id="setup_wizard:skip",
            disabled=(section is None),
            row=0,
        )
        skip.callback = self._on_skip  # type: ignore[method-assign]
        self.add_item(skip)

        is_last_step = self.step_index >= len(self.sections) - 1
        continue_btn: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Continue ▶" if not is_last_step else "Final Review",
            style=(
                discord.ButtonStyle.primary
                if is_last_step
                else discord.ButtonStyle.secondary
            ),
            custom_id="setup_wizard:continue",
            disabled=False,
            row=1,
        )
        continue_btn.callback = self._on_continue  # type: ignore[method-assign]
        self.add_item(continue_btn)

        cancel: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Cancel",
            style=discord.ButtonStyle.danger,
            custom_id="setup_wizard:cancel",
            row=1,
        )
        cancel.callback = self._on_cancel  # type: ignore[method-assign]
        self.add_item(cancel)

        jump = self._build_jump_select()
        if jump is not None:
            self.add_item(jump)

        apply_all = self._build_apply_all_button()
        if apply_all is not None:
            self.add_item(apply_all)

    def _build_apply_all_button(self) -> discord.ui.Button | None:
        """Build the row-3 "Apply all recommended" button.

        Stages every depth-filtered section's recommended ops in one
        click — the one-click path that used to live on the hub.
        Returns ``None`` when no section in the current depth has a
        recommended builder, so the button never renders as a no-op.
        """
        if not any(s.recommended_ops_builder is not None for s in self.sections):
            return None
        button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Apply all recommended",
            style=discord.ButtonStyle.success,
            custom_id="setup_wizard:apply_all_recommended",
            row=3,
        )
        button.callback = self._on_apply_all_recommended  # type: ignore[method-assign]
        return button

    def _build_jump_select(self) -> discord.ui.Select | None:
        """Build the row-2 "Jump to section" select.

        This is the section-jump that folds the standalone hub's
        navigation role into the wizard anchor: every depth-filtered
        section is reachable directly from the wizard, so operators no
        longer need a parallel hub view to skip ahead.  Returns ``None``
        when there are no sections for the current depth.
        """
        if not self.sections:
            return None
        return _JumpToSectionSelect(self)

    async def _gate_apply(self, interaction: discord.Interaction) -> bool:
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
                logger.exception("wizard._gate_apply: resume failed")
                session = None
        if not setup_access.can_apply_setup(member, session):
            await interaction.response.send_message(
                "Only the server owner or a delegated setup admin can stage "
                "or skip setup operations. Ask the server owner to grant "
                "you `/setup-delegate`.",
                ephemeral=True,
            )
            return False
        return True

    async def _mount_recovery_view(
        self,
        interaction: discord.Interaction,
        *,
        section: SetupSection,
        exc: BaseException,
    ) -> None:
        """Edit the wizard anchor to show the recovery embed + view.

        Called when ``_on_apply_recommended`` (and, eventually, other
        section-flow callbacks) catches a section-side exception.  The
        recovery view's ``Continue`` button re-paints this step via
        :meth:`_refresh_and_edit` so the operator returns cleanly to
        the wizard flow.
        """
        from views.setup.recovery import (
            SectionRecoveryView,
            build_recovery_embed,
            recovery_context_from_exception,
        )

        context = recovery_context_from_exception(
            section=section,
            exc=exc,
            origin="wizard",
            step_index=self.step_index,
            total_steps=len(self.sections),
        )
        embed = build_recovery_embed(context)
        recovery_view = SectionRecoveryView(
            interaction.user,
            context=context,
            resume_callback=self._refresh_and_edit,
        )
        try:
            if interaction.response.is_done():
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    embed=embed,
                    view=recovery_view,
                )
            else:
                await interaction.response.edit_message(
                    embed=embed,
                    view=recovery_view,
                )
        except discord.HTTPException:
            logger.exception(
                "wizard._mount_recovery_view: edit failed",
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"Could not show the recovery view for "
                    f"**{section.label}** — see logs.",
                    ephemeral=True,
                )

    async def _refresh_and_edit(self, interaction: discord.Interaction) -> None:
        """Refresh state and edit the anchor message at ``self.step_index``.

        Thin delegate over :func:`views.setup.wizard_nav.render_wizard_step`
        so every wizard callback uses the same anchor-rebuild path
        (also used by the hub's ↩ Back to wizard button).
        """
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            # Without a Member context we can't construct a new wizard
            # view; fall back to the same ephemeral hint the apply gate
            # uses.
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Use this from inside the server.",
                    ephemeral=True,
                )
            return

        from views.setup.wizard_nav import render_wizard_step

        await render_wizard_step(
            interaction,
            guild=guild,
            member=member,
            session=self.session,
            step_index=self.step_index,
        )

    async def _on_back(self, interaction: discord.Interaction) -> None:
        if self.step_index > 0:
            self.step_index -= 1
        await self._refresh_and_edit(interaction)

    async def _on_continue(self, interaction: discord.Interaction) -> None:
        if self.step_index < len(self.sections) - 1:
            self.step_index += 1
            await self._refresh_and_edit(interaction)
            return
        # Last step → open Final Review as a transient ephemeral.
        await self._open_final_review(interaction)

    async def _on_cancel(self, interaction: discord.Interaction) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        embed = discord.Embed(
            title=_WIZARD_TITLE,
            description=(
                "Wizard closed.  Re-open with `/setup` or `!setup`; your "
                "draft is preserved."
            ),
            color=discord.Color.dark_grey(),
        )
        if interaction.response.is_done():
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=embed,
                view=self,
            )
        else:
            await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def _on_apply_recommended(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if not await self._gate_apply(interaction):
            return
        section = self.current_section
        if section is None:
            await interaction.response.send_message(
                "No section selected.",
                ephemeral=True,
            )
            return
        builder = section.recommended_ops_builder
        if builder is None:
            await interaction.response.send_message(
                "This step has no recommended defaults — use Customize "
                "to open the detail view.",
                ephemeral=True,
            )
            return
        guild = interaction.guild
        if guild is None or interaction.guild_id is None:
            await interaction.response.send_message(
                "Apply Recommended requires a guild context.",
                ephemeral=True,
            )
            return
        try:
            session = await setup_session.resume_session(interaction.guild_id)
        except Exception:
            logger.exception("wizard._on_apply_recommended: resume failed")
            session = self.session
        try:
            ops = await call_recommended_ops_builder(
                builder,
                guild=guild,
                session=session,
                purpose=session.purpose if session is not None else None,
                depth=session.depth if session is not None else None,
                section_slug=section.slug,
            )
        except Exception as exc:
            logger.exception(
                "wizard._on_apply_recommended: builder failed (%s)",
                section.slug,
            )
            await self._mount_recovery_view(interaction, section=section, exc=exc)
            return
        if not ops:
            await interaction.response.send_message(
                "No recommended operations were generated for this step.",
                ephemeral=True,
            )
            return
        try:
            result = await setup_draft.replace_recommended_for_section(
                interaction.guild_id,
                section.slug,
                ops,
                actor_id=interaction.user.id,
                labels={
                    idx: f"[wizard] {section.slug}.{op.kind}"
                    for idx, op in enumerate(ops)
                },
            )
        except Exception as exc:
            logger.exception(
                "wizard._on_apply_recommended: replace_recommended failed",
            )
            await self._mount_recovery_view(interaction, section=section, exc=exc)
            return
        try:
            await setup_session.unmark_section_skipped(
                interaction.guild_id,
                section.slug,
            )
        except Exception:
            logger.exception("wizard._on_apply_recommended: unmark skip failed")

        count = len(result.inserted_seqs)
        noun = "operation" if count == 1 else "operations"
        conflict_text = ""
        if result.conflicts:
            cn = len(result.conflicts)
            conflict_word = "row" if cn == 1 else "rows"
            conflict_text = (
                f"\n\n⚠️ Preserved **{cn} custom / preset {conflict_word}** "
                "at conflicting slot(s); no overwrite."
            )
        # Aggressive ephemeral policy: post the apply-recommended record
        # as a durable workspace notice (event log) and let the anchor
        # refresh reflect the new state. defer() is the interaction ack.
        await safe_defer(interaction)
        notice_embed = discord.Embed(
            title=f"✅ Recommended staged · {section.label}",
            description=f"Staged **{count} {noun}**.{conflict_text}",
            color=discord.Color.green(),
        )
        try:
            await push_setup_notice(guild, embed=notice_embed)
        except Exception:
            logger.exception(
                "wizard._on_apply_recommended: push_setup_notice failed",
            )
        # Refresh the anchor to show the updated section status badge.
        try:
            await self._refresh_and_edit(interaction)
        except Exception:
            logger.exception(
                "wizard._on_apply_recommended: anchor refresh failed",
            )

    async def _on_apply_all_recommended(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Stage recommended ops for every depth-filtered builder section.

        The one-click path: iterate the current depth's sections with a
        ``recommended_ops_builder`` and stage each through the shared
        :func:`views.setup.section_card.stage_all_recommended` helper.
        Posts a durable workspace notice, gives the operator an immediate
        ephemeral confirmation (click-level feedback), and refreshes the
        anchor so the per-section badges update.
        """
        if not await self._gate_apply(interaction):
            return
        guild = interaction.guild
        guild_id = interaction.guild_id
        if guild is None or guild_id is None:
            await interaction.response.send_message(
                "Apply all recommended requires a guild context.",
                ephemeral=True,
            )
            return
        try:
            session = await setup_session.resume_session(guild_id)
        except Exception:
            logger.exception("wizard._on_apply_all_recommended: resume failed")
            session = self.session
        sections = [
            s
            for s in _resolve_sections(session)
            if s.recommended_ops_builder is not None
        ]
        if not sections:
            await interaction.response.send_message(
                "No section in the current depth has a recommended default — "
                "use **Customize** on individual steps instead.",
                ephemeral=True,
            )
            return

        if not await safe_defer(interaction):
            return
        from views.setup.section_card import stage_all_recommended

        try:
            section_totals, conflicts_total = await stage_all_recommended(
                guild=guild,
                guild_id=guild_id,
                session=session,
                sections=sections,
                actor_id=interaction.user.id,
            )
        except Exception:
            logger.exception("wizard._on_apply_all_recommended: staging failed")
            await interaction.followup.send(
                "Could not stage recommended operations — see logs.",
                ephemeral=True,
            )
            return

        total = sum(section_totals.values())
        word = "operation" if total == 1 else "operations"
        if not total and not conflicts_total:
            await interaction.followup.send(
                "No recommended operations were generated — the guild may "
                "already cover these, or no channels matched the rules.",
                ephemeral=True,
            )
            return

        lines = "\n".join(
            f"• `{slug}`: **{count}** op(s)" for slug, count in section_totals.items()
        )
        description = (
            f"Staged **{total} {word}** across {len(section_totals)} "
            "section(s). Continue to **Final Review** to apply."
        )
        if lines:
            description += f"\n\n{lines}"
        if conflicts_total:
            conflict_word = "row" if conflicts_total == 1 else "rows"
            description += (
                f"\n\n⚠️ Preserved **{conflicts_total} custom / preset "
                f"{conflict_word}** at conflicting slot(s); no overwrite."
            )
        notice_embed = discord.Embed(
            title=f"✅ Apply all recommended — {total} {word}",
            description=description,
            color=discord.Color.green(),
        )
        try:
            await push_setup_notice(guild, embed=notice_embed)
        except Exception:
            logger.exception(
                "wizard._on_apply_all_recommended: push_setup_notice failed",
            )
        # Immediate click-level feedback so the operator does not have to
        # hunt the workspace channel to confirm the press did something.
        try:
            await interaction.followup.send(
                f"✅ Staged **{total} {word}** across "
                f"{len(section_totals)} section(s).",
                ephemeral=True,
            )
        except Exception:
            logger.exception(
                "wizard._on_apply_all_recommended: followup confirm failed",
            )
        try:
            await self._refresh_and_edit(interaction)
        except Exception:
            logger.exception(
                "wizard._on_apply_all_recommended: anchor refresh failed",
            )

    async def _on_skip(self, interaction: discord.Interaction) -> None:
        if not await self._gate_apply(interaction):
            return
        section = self.current_section
        if section is None or interaction.guild_id is None:
            await interaction.response.send_message(
                "No step to skip.",
                ephemeral=True,
            )
            return
        try:
            await setup_session.mark_section_skipped(
                interaction.guild_id,
                section.slug,
            )
        except Exception:
            logger.exception(
                "wizard._on_skip: mark_section_skipped failed (%s)",
                section.slug,
            )
            await interaction.response.send_message(
                "Could not record the skip — see logs.",
                ephemeral=True,
            )
            return

        # Provenance-aware delete: drop any rows the section owns so
        # Final Review never applies an op the operator skipped.
        deleted_count = 0
        try:
            existing_rows = await setup_draft.list_by_section(
                interaction.guild_id,
                section.slug,
            )
            if existing_rows:
                deleted_count = await setup_draft.delete_by_ids(
                    interaction.guild_id,
                    [row.id for row in existing_rows],
                )
        except Exception:
            logger.exception(
                "wizard._on_skip: provenance delete failed (%s)",
                section.slug,
            )

        # Advance to the next step.
        if self.step_index < len(self.sections) - 1:
            self.step_index += 1

        followup = (
            f"\n\nRemoved {deleted_count} staged op(s) for this section."
            if deleted_count
            else ""
        )
        # Ephemeral reply first; then refresh the anchor in a follow-up.
        await interaction.response.send_message(
            f"⏭ Skipped **{section.label}**.{followup}",
            ephemeral=True,
        )
        # Refresh the anchor message in place.
        try:
            await self._refresh_anchor_after_skip(interaction)
        except Exception:
            logger.exception("wizard._on_skip: anchor refresh failed")

    async def _refresh_anchor_after_skip(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Re-render the wizard anchor message after a Skip.

        Skip's first response is the ephemeral confirmation; the anchor
        edit happens via ``interaction.followup.edit_message`` so the
        operator sees both the confirmation and the updated step.
        """
        guild_id = interaction.guild_id
        if guild_id is not None:
            try:
                self.session = await setup_session.resume_session(guild_id)
            except Exception:
                logger.exception("wizard.skip-refresh: resume failed")
        self.sections = _resolve_sections(self.session)
        if self.step_index >= len(self.sections):
            self.step_index = max(0, len(self.sections) - 1)
        self._rebuild_buttons()
        draft_rows: list[DraftOperationRow] = []
        if guild_id is not None:
            try:
                draft_rows = await setup_draft.list_rows(guild_id)
            except Exception:
                logger.exception("wizard.skip-refresh: list_rows failed")
        section = self.current_section
        if section is None:
            return
        embed = build_wizard_step_embed(
            session=self.session,
            section=section,
            step_index=self.step_index,
            total_steps=len(self.sections),
            draft_rows=draft_rows,
        )
        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            embed=embed,
            view=self,
        )

    async def _on_customize(self, interaction: discord.Interaction) -> None:
        section = self.current_section
        if section is None:
            await interaction.response.send_message(
                "This step has no detail view.",
                ephemeral=True,
            )
            return
        has_detail = (
            section.detail_embed_builder is not None
            and section.detail_view_builder is not None
        )
        if not has_detail and section.customize is None:
            await interaction.response.send_message(
                "This step has no detail view.",
                ephemeral=True,
            )
            return
        # Gate before opening — detail views can stage draft operations.
        if not await self._gate_apply(interaction):
            return

        if has_detail:
            # Wizard-native path: swap the anchor into detail mode with
            # an injected ↩ Back to step button.  No ephemeral side
            # panel, no stranding.
            guild = interaction.guild
            member = interaction.user
            if guild is None or not isinstance(member, discord.Member):
                await interaction.response.send_message(
                    "Use this from inside the server.",
                    ephemeral=True,
                )
                return
            from views.setup.wizard_nav import render_step_detail

            try:
                ok = await render_step_detail(
                    interaction,
                    guild=guild,
                    member=member,
                    session=self.session,
                    section=section,
                    step_index=self.step_index,
                )
            except Exception:
                logger.exception(
                    "wizard._on_customize: render_step_detail failed (%s)",
                    section.slug,
                )
                ok = False
            if not ok and not interaction.response.is_done():
                await interaction.response.send_message(
                    "Could not open the detail view — see logs.",
                    ephemeral=True,
                )
            return

        # Legacy fallback: section provides only the ephemeral customize
        # callback.  After it consumes the interaction we refresh the
        # anchor so the operator sees any newly staged state.
        try:
            await section.customize(interaction, None)
        except Exception:
            logger.exception(
                "wizard._on_customize: section handler failed (%s)",
                section.slug,
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Could not open the detail view — see logs.",
                    ephemeral=True,
                )
            return
        try:
            await self._refresh_and_edit(interaction)
        except Exception:
            logger.exception("wizard._on_customize: anchor refresh failed")

    async def _open_final_review(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Swap the wizard anchor to the Final Review embed + view.

        Aggressive ephemeral policy: Final Review is canonical setup
        state — admins need to revisit it, share it, and delete it
        from the source-of-truth workspace channel rather than from
        a private ephemeral that's tied to one operator.
        """
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Final Review requires a guild context.",
                ephemeral=True,
            )
            return
        from views.setup.final_review import (
            FinalReviewView,
            build_final_review_embed,
        )

        if not await safe_defer(interaction):
            return

        try:
            ops = await setup_draft.list_ops(guild.id)
        except Exception:
            logger.exception("wizard._open_final_review: list_ops failed")
            ops = []
        final = FinalReviewView(interaction.user, ops=ops)
        await safe_edit(
            interaction,
            embed=build_final_review_embed(final.ops),
            view=final,
        )


class _JumpToSectionSelect(discord.ui.Select):
    """Row-2 "Jump to section" select for :class:`LinearWizardView`.

    Lets a power user jump straight to any depth-filtered section's step
    in the wizard anchor — the section-jump role that used to require a
    separate hub view.  On select it re-renders the anchor at the chosen
    step via the wizard's shared ``_refresh_and_edit`` path.
    """

    def __init__(self, wizard: LinearWizardView) -> None:
        self._wizard = wizard
        current = wizard.current_section
        options = [
            discord.SelectOption(
                label=section.label[:100],
                value=str(idx),
                default=(current is not None and section.slug == current.slug),
            )
            for idx, section in enumerate(wizard.sections[:25])
        ]
        super().__init__(
            placeholder="Jump to section…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="setup_wizard:jump",
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        wizard = self._wizard
        try:
            target = int(self.values[0])
        except (ValueError, IndexError):
            target = wizard.step_index
        wizard.step_index = max(0, min(target, len(wizard.sections) - 1))
        await wizard._refresh_and_edit(interaction)


# ---------------------------------------------------------------------------
# Workspace anchor — /setup and !setup route through this helper.
# ---------------------------------------------------------------------------


async def open_setup_workspace(
    guild: discord.Guild,
    *,
    member: discord.Member,
    session: SetupSession | None,
) -> tuple[discord.TextChannel | None, discord.Message | None, str]:
    """Ensure ``#superbot-setup`` exists and (re)post the wizard anchor.

    Returns ``(channel, message, reason)``:

    * On success — ``(channel, message, "ok")``.  ``message`` is the
      anchor that was either edited in place (when ``setup_message_id``
      pointed to a still-fetchable message) or newly posted.
    * On missing perms — ``(None, None, "no_channel")``.  Caller
      surfaces the privacy / permissions hint in its invoking-channel
      reply.
    * On Discord HTTP failure during post / edit — ``(channel, None,
      "post_failed")``.  Channel was resolved but the message couldn't
      be posted; caller surfaces an error.

    Side effects:

    * Persists the new message id via
      :func:`services.setup_session.set_setup_message_id` whenever
      a fresh message is posted.
    * Records ``current_step="wizard"`` via
      :func:`services.setup_session.mark_in_progress` so the launcher
      surfaces the right label across restarts.
    """
    channel, _was_created = await setup_channel.ensure_setup_channel(
        guild,
        existing_channel_id=(session.setup_channel_id if session is not None else None),
        session=session,
    )
    if channel is None:
        return None, None, "no_channel"

    # Persist the resolved channel id when it differs from the session's
    # stored value (covers stale pointer and first-run cases).
    if session is None or session.setup_channel_id != channel.id:
        try:
            await setup_session.set_setup_channel_id(guild.id, channel.id)
        except Exception:
            logger.exception("open_setup_workspace: set_setup_channel_id failed")

    sections = _resolve_sections(session)
    step_index = _step_index_for(session, sections)

    try:
        draft_rows = await setup_draft.list_rows(guild.id)
    except Exception:
        logger.exception("open_setup_workspace: list_rows failed")
        draft_rows = []

    if sections:
        embed = build_wizard_step_embed(
            session=session,
            section=sections[step_index],
            step_index=step_index,
            total_steps=len(sections),
            draft_rows=draft_rows,
        )
    else:
        embed = discord.Embed(
            title=_WIZARD_TITLE,
            description=(
                "No setup sections are available for this depth. "
                "Pick a depth via `/setup-depth` to populate the wizard."
            ),
            color=discord.Color.dark_grey(),
        )

    view = LinearWizardView(
        member,
        session=session,
        sections=sections,
        step_index=step_index,
    )

    message: discord.Message | None = None
    existing_id = session.setup_message_id if session is not None else None
    if existing_id is not None:
        # Best-effort edit-in-place.  When the message has been
        # deleted (or the bot lost access to the channel), fall
        # through to the post path.
        try:
            existing_msg = await channel.fetch_message(existing_id)
            message = await existing_msg.edit(embed=embed, view=view)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            logger.info(
                "open_setup_workspace: anchor %s no longer fetchable; "
                "reposting in guild %d",
                existing_id,
                guild.id,
            )
            message = None
            try:
                await setup_session.set_setup_message_id(guild.id, None)
            except Exception:
                logger.exception(
                    "open_setup_workspace: clearing stale message_id failed",
                )

    if message is None:
        try:
            message = await channel.send(embed=embed, view=view)
        except discord.HTTPException:
            logger.exception(
                "open_setup_workspace: failed to post anchor in guild %d",
                guild.id,
            )
            return channel, None, "post_failed"
        try:
            await setup_session.set_setup_message_id(guild.id, message.id)
        except Exception:
            logger.exception(
                "open_setup_workspace: persist message id failed",
            )

    try:
        await setup_session.mark_in_progress(guild.id, step="wizard")
    except Exception:
        logger.exception(
            "open_setup_workspace: mark_in_progress failed",
        )

    return channel, message, "ok"


def jump_link(message: discord.Message) -> str:
    """Return a Discord jump URL for ``message`` (markdown link wrap)."""
    return f"[Open setup workspace]({message.jump_url})"


__all__ = [
    "LinearWizardView",
    "build_wizard_step_embed",
    "jump_link",
    "open_setup_workspace",
]
