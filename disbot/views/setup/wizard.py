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
* The hub continues to exist; the wizard's ``Open hub`` button posts
  the hub-style embed as a transient reply so operators who prefer
  the section-list UI still get it.  ``/setup-hub`` remains as the
  explicit hub entry point.

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
from views.setup.section_card import call_recommended_ops_builder

if TYPE_CHECKING:
    from services.setup_draft import DraftOperationRow

logger = logging.getLogger("bot.views.setup.wizard")


_WIZARD_TITLE = "🛰 SuperBot setup wizard"
_FOOTER_HINT = "Nothing changes until Final Review applies the staged operations."


def _resolve_sections(session: SetupSession | None) -> list[SetupSection]:
    """Return the depth-filtered section list for ``session``."""
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
    ``Open hub``, ``Cancel``) are not gated — they only mutate
    view-local state.

    The view does not own the anchor message; the caller (typically
    :func:`open_setup_workspace`) edits the message after each
    button press to re-render the new step.
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

        customize: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Customize",
            style=discord.ButtonStyle.primary,
            custom_id="setup_wizard:customize",
            disabled=(section is None or section.customize is None),
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

        open_hub: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Open hub",
            style=discord.ButtonStyle.secondary,
            custom_id="setup_wizard:open_hub",
            row=1,
        )
        open_hub.callback = self._on_open_hub  # type: ignore[method-assign]
        self.add_item(open_hub)

        cancel: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Cancel",
            style=discord.ButtonStyle.danger,
            custom_id="setup_wizard:cancel",
            row=1,
        )
        cancel.callback = self._on_cancel  # type: ignore[method-assign]
        self.add_item(cancel)

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
        """Refresh the session + draft state and edit the anchor message.

        Used by every button callback that needs to repaint the embed
        with new step / progress data.  Edits in place so the anchor's
        id remains stable.
        """
        guild_id = interaction.guild_id
        if guild_id is not None:
            try:
                self.session = await setup_session.resume_session(guild_id)
            except Exception:
                logger.exception("wizard._refresh_and_edit: resume failed")
        # Re-resolve sections in case depth changed.
        self.sections = _resolve_sections(self.session)
        # Clamp step index in case the section list shrank.
        if self.step_index >= len(self.sections):
            self.step_index = max(0, len(self.sections) - 1)
        self._rebuild_buttons()

        draft_rows: list[DraftOperationRow] = []
        if guild_id is not None:
            try:
                draft_rows = await setup_draft.list_rows(guild_id)
            except Exception:
                logger.exception("wizard._refresh_and_edit: list_rows failed")

        section = self.current_section
        if section is None:
            embed = discord.Embed(
                title=_WIZARD_TITLE,
                description=(
                    "No setup sections are available for this depth. "
                    "Pick a different depth via `/setup-depth` or open "
                    "the hub for the full section list."
                ),
                color=discord.Color.dark_grey(),
            )
        else:
            embed = build_wizard_step_embed(
                session=self.session,
                section=section,
                step_index=self.step_index,
                total_steps=len(self.sections),
                draft_rows=draft_rows,
            )

        if interaction.response.is_done():
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=embed,
                view=self,
            )
        else:
            await interaction.response.edit_message(embed=embed, view=self)

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

    async def _on_open_hub(self, interaction: discord.Interaction) -> None:
        # Surface the existing hub-style embed as an ephemeral follow-up
        # so the operator can browse the section list without losing
        # the wizard anchor.
        from views.setup.hub import SetupHubView, build_hub_embed

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Open hub requires a guild context.",
                ephemeral=True,
            )
            return

        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use this from inside the server.",
                ephemeral=True,
            )
            return

        try:
            session = await setup_session.resume_session(guild.id)
        except Exception:
            logger.exception("wizard._on_open_hub: resume failed")
            session = self.session

        try:
            draft_rows = await setup_draft.list_rows(guild.id)
        except Exception:
            logger.exception("wizard._on_open_hub: list_rows failed")
            draft_rows = []

        hub_view = SetupHubView(member, session=session)
        embed = build_hub_embed(
            session,
            pending_ops=len(draft_rows),
            draft_ops=draft_rows,
        )
        await interaction.response.send_message(
            embed=embed,
            view=hub_view,
            ephemeral=True,
        )

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
        await interaction.response.send_message(
            f"✅ Staged **{count} recommended {noun}** for "
            f"{section.label}.{conflict_text}",
            ephemeral=True,
        )
        # Refresh the anchor to show the updated section status badge.
        # response.is_done() is True above, so _refresh_and_edit uses followup.
        try:
            await self._refresh_and_edit(interaction)
        except Exception:
            logger.exception(
                "wizard._on_apply_recommended: anchor refresh failed",
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
        if section is None or section.customize is None:
            await interaction.response.send_message(
                "This step has no detail view.",
                ephemeral=True,
            )
            return
        # Gate before opening — detail views can stage draft operations.
        if not await self._gate_apply(interaction):
            return
        try:
            # Pass None as hub; all registered customizers handle hub=None.
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
        # The section's customize callback consumed the interaction response
        # (ephemeral detail view).  Refresh the anchor to show current state.
        # For detail views that stage ops asynchronously (user picks options
        # inside the ephemeral), the anchor updates again on the next wizard
        # button press — this is intentional and documented.
        try:
            await self._refresh_and_edit(interaction)
        except Exception:
            logger.exception("wizard._on_customize: anchor refresh failed")

    async def _open_final_review(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Open Final Review as an ephemeral follow-up on the last step."""
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

        try:
            ops = await setup_draft.list_ops(guild.id)
        except Exception:
            logger.exception("wizard._open_final_review: list_ops failed")
            ops = []
        final = FinalReviewView(interaction.user, ops=ops)
        await interaction.response.send_message(
            embed=build_final_review_embed(final.ops),
            view=final,
            ephemeral=True,
        )
        # Refresh the wizard anchor so it reflects the current staged state
        # before the operator reviews.  response.is_done() is True, so
        # _refresh_and_edit uses followup.edit_message.
        try:
            await self._refresh_and_edit(interaction)
        except Exception:
            logger.exception("wizard._open_final_review: anchor refresh failed")


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
                "Pick a depth via `/setup-depth` or open the hub."
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
