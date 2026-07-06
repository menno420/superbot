"""Per-section recovery embed + view.

Phase 7 of the setup-wizard plan.  When a wizard section's
``Customize`` or ``Apply Recommended`` flow errors out, the
section module catches the exception, fills in a
:class:`RecoveryContext`, and mounts a :class:`SectionRecoveryView`
in place of the normal step embed.  The view carries enough
``(origin, step, section)`` context to re-invoke section paths
without losing the operator's place in the wizard.

Structured recovery embed
-------------------------

The embed surfaces four operator-facing fields:

* **What happened** — one-line human cause ("I couldn't read the
  channel list").
* **Why** — permission / feature reason ("Manage Channels missing").
* **Recommended** — one actionable suggestion ("Grant Manage Channels
  and press Retry").
* **If skipped** — the consequence ("Logging defaults stay
  unconfigured; you can revisit `/setup-skip`").

Buttons:

* **Continue** — advance to the next wizard step without retrying.
* **Retry** — re-invoke the failing section path.
* **Skip section** — write the section to ``skipped_sections`` and
  advance.
* **Customize** — open the section's detail view if it has one;
  disabled when the section is read-only.
* **Cancel** — close the recovery view and return to the wizard.

Mutating buttons (Retry / Skip) re-check
:func:`services.setup_access.can_apply_setup` against a fresh
session snapshot — same pattern as Phase 1's section card and
Phase 3's wizard.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord

from core.runtime.interaction_helpers import safe_edit
from services import setup_access, setup_draft, setup_session
from services.setup_sections import SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.views.setup.recovery")


# Origin tag: ``"wizard"`` when reached from the linear wizard
# (Phase 3 ``LinearWizardView``); ``"hub"`` when reached from the
# registry-driven hub.  Recovery views read this so ``Continue`` /
# ``Cancel`` can return the operator to the right anchor.
OriginTag = str


@dataclass(frozen=True)
class RecoveryContext:
    """Structured payload for a section-failure recovery embed.

    Recovery views carry this so the buttons know which section to
    retry / skip and where to return on Continue / Cancel.  The
    "What happened" / "Why" / "Recommended" / "If skipped" fields
    drive the rendered embed.
    """

    section: SetupSection
    origin: OriginTag
    step_index: int  # 0-based; -1 if origin is hub (no step ordinal)
    total_steps: int  # 0 if origin is hub
    what_happened: str
    why: str
    recommended: str
    if_skipped: str


# Async callback the wizard / hub registers so the recovery view can
# repaint the host on Continue / successful Retry.  Receives the
# interaction so the view can edit the anchor in place.
ResumeCallback = Callable[[discord.Interaction], Awaitable[None]]


def build_recovery_embed(context: RecoveryContext) -> discord.Embed:
    """Render the recovery embed for ``context``.

    Layout matches the Phase 7 plan: four labelled fields in a fixed
    order, gold accent so the embed is visually distinct from the
    normal step embed.
    """
    if context.step_index >= 0 and context.total_steps > 0:
        title = (
            f"⚠️ Setup issue found · Step {context.step_index + 1}/{context.total_steps}"
        )
    else:
        title = "⚠️ Setup issue found"
    embed = discord.Embed(
        title=title,
        description=(
            f"While running **{context.section.label}** the wizard hit "
            "an error.  Nothing has changed yet — pick how to proceed "
            "from the buttons below."
        ),
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="What happened",
        value=context.what_happened or "_(no detail captured)_",
        inline=False,
    )
    embed.add_field(
        name="Why",
        value=context.why or "_(no detail captured)_",
        inline=False,
    )
    embed.add_field(
        name="Recommended",
        value=context.recommended or "_(no suggestion available)_",
        inline=False,
    )
    embed.add_field(
        name="If skipped",
        value=context.if_skipped or "_(no consequence documented)_",
        inline=False,
    )
    embed.set_footer(
        text=(
            "Recovery only — Final Review still owns the apply path.  "
            "Nothing on this view stages or applies operations."
        ),
    )
    return embed


class SectionRecoveryView(BaseView):
    """Recovery view shown after a section error.

    ``resume_callback`` is called on Continue / successful Retry to
    let the host (wizard or hub) restore its normal embed in place.
    Hosts that don't need an in-place restore (e.g. the hub, where
    the recovery surfaces as a fresh ephemeral) can pass ``None`` and
    the view will simply close on Continue.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        context: RecoveryContext,
        resume_callback: ResumeCallback | None = None,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.context = context
        self._resume_callback = resume_callback
        self._populate_buttons()

    def _populate_buttons(self) -> None:
        cont: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Continue",
            style=discord.ButtonStyle.primary,
            custom_id="setup_recovery:continue",
            row=0,
        )
        cont.callback = self._on_continue  # type: ignore[method-assign]
        self.add_item(cont)

        retry: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Retry",
            style=discord.ButtonStyle.secondary,
            custom_id="setup_recovery:retry",
            row=0,
        )
        retry.callback = self._on_retry  # type: ignore[method-assign]
        self.add_item(retry)

        skip: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Skip section",
            style=discord.ButtonStyle.secondary,
            custom_id="setup_recovery:skip",
            row=0,
        )
        skip.callback = self._on_skip  # type: ignore[method-assign]
        self.add_item(skip)

        customize: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Customize",
            style=discord.ButtonStyle.secondary,
            # Customize is enabled only for sections that declare an
            # actual recommended_ops_builder OR have non-empty
            # op_kinds — read-only sections (server_scan, readiness,
            # final_review) wouldn't open a useful detail view.
            disabled=(
                self.context.section.recommended_ops_builder is None
                and not self.context.section.op_kinds
            ),
            custom_id="setup_recovery:customize",
            row=1,
        )
        customize.callback = self._on_customize  # type: ignore[method-assign]
        self.add_item(customize)

        cancel: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Cancel",
            style=discord.ButtonStyle.danger,
            custom_id="setup_recovery:cancel",
            row=1,
        )
        cancel.callback = self._on_cancel  # type: ignore[method-assign]
        self.add_item(cancel)

    async def _close_in_place(
        self,
        interaction: discord.Interaction,
        *,
        content: str | None = None,
    ) -> None:
        """Disable all children and edit the recovery message in place.

        Uses ``safe_edit`` so this works whether the upstream branch
        already consumed the interaction's response slot (resume
        callback, ``section.run`` ephemeral, ``_gate_apply`` rejection)
        or not. When the original recovery message has been deleted or
        replaced by an upstream branch, ``safe_edit`` swallows the
        resulting ``discord.NotFound`` at WARNING — the user sees the
        new state from the upstream branch and the recovery view's
        invisible state cleanup is purely belt-and-braces.
        """
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await safe_edit(interaction, content=content, view=self)

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
                logger.exception("recovery._gate_apply: resume failed")
                session = None
        if not setup_access.can_apply_setup(member, session):
            await interaction.response.send_message(
                "Only the server owner or a delegated setup admin can "
                "retry or skip a setup step.  Ask the owner to grant "
                "you `/setup-delegate`.",
                ephemeral=True,
            )
            return False
        return True

    async def _on_continue(self, interaction: discord.Interaction) -> None:
        """Advance past the failing step without retrying.

        Closes the recovery view and (when ``resume_callback`` is
        wired) hands control back to the host so it can re-paint the
        next step in place.
        """
        if self._resume_callback is not None:
            try:
                await self._resume_callback(interaction)
            except Exception:
                logger.exception("recovery._on_continue: resume failed")
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "Could not return to the wizard — see logs.",
                        ephemeral=True,
                    )
            # The resume callback usually repaints a separate host
            # anchor; the recovery message itself must still become a
            # disabled shell so its buttons don't outlive `self.stop()`.
            await self._close_in_place(interaction)
            self.stop()
            return
        # No resume callback: just close the view in place.
        await self._close_in_place(interaction)
        self.stop()

    async def _on_retry(self, interaction: discord.Interaction) -> None:
        if not await self._gate_apply(interaction):
            return
        # Re-invoke the section's run callback.  The section is
        # responsible for re-opening its own UI (section card, picker
        # view, etc.) and any subsequent failure surfaces as a fresh
        # ephemeral — the recovery view here is intentionally
        # short-lived.  Sections drive ``interaction.response.*``
        # themselves, so we let them consume the response slot before
        # closing the recovery message via ``safe_edit`` (which then
        # routes through ``followup.edit_message``).
        try:
            await self.context.section.run(interaction, None)  # type: ignore[arg-type]
        except Exception:
            logger.exception(
                "recovery._on_retry: section %s raised",
                self.context.section.slug,
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"Retry of **{self.context.section.label}** failed "
                    "again — see logs.  Use Skip section to move on.",
                    ephemeral=True,
                )
        await self._close_in_place(interaction)
        self.stop()

    async def _on_skip(self, interaction: discord.Interaction) -> None:
        if not await self._gate_apply(interaction):
            return
        guild_id = interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return
        try:
            await setup_session.mark_section_skipped(
                guild_id,
                self.context.section.slug,
            )
        except Exception:
            logger.exception(
                "recovery._on_skip: mark_section_skipped failed (section=%s)",
                self.context.section.slug,
            )
            await interaction.response.send_message(
                "Could not record the skip — see logs.",
                ephemeral=True,
            )
            return
        # Best-effort provenance delete so Final Review doesn't apply
        # ops the operator just skipped (mirrors Phase 3's wizard
        # Skip behaviour).
        try:
            existing = await setup_draft.list_by_section(
                guild_id,
                self.context.section.slug,
            )
            if existing:
                await setup_draft.delete_by_ids(
                    guild_id,
                    [row.id for row in existing],
                )
        except Exception:
            logger.exception(
                "recovery._on_skip: provenance delete failed (section=%s)",
                self.context.section.slug,
            )

        skip_msg = f"⏭ Skipped **{self.context.section.label}**."

        # Advance via the resume callback when wired.
        if self._resume_callback is not None:
            try:
                await self._resume_callback(interaction)
            except Exception:
                logger.exception("recovery._on_skip: resume failed")
            # The resume callback may repaint a separate host anchor;
            # the recovery message itself must still become a disabled
            # shell so its buttons don't outlive ``self.stop()``.
            await self._close_in_place(interaction, content=skip_msg)
            self.stop()
            return

        # Fallback: close in place with a confirmation.
        await self._close_in_place(interaction, content=skip_msg)
        self.stop()

    async def _on_customize(self, interaction: discord.Interaction) -> None:
        """Open the section's detail view directly — distinct from Retry.

        Retry re-runs the section's auto flow (``section.run``), which
        re-attempts the path that just failed.  Customize instead jumps
        straight to the section's manual detail view (``detail_embed_builder``
        + ``detail_view_builder``) on the wizard anchor, so the operator
        can configure by hand instead of re-triggering the failure.

        Sections without a wizard-native detail view have no separate
        manual UI, so for them Customize falls back to ``section.run`` —
        the same single manual entry point Retry uses.
        """
        if not await self._gate_apply(interaction):
            return
        section = self.context.section
        guild = interaction.guild
        member = interaction.user
        has_detail = (
            section.detail_embed_builder is not None
            and section.detail_view_builder is not None
        )
        if not (
            has_detail and guild is not None and isinstance(member, discord.Member)
        ):
            # No wizard-native detail view — re-enter via the section's
            # run() callback (the only manual entry it exposes).
            await self._on_retry(interaction)
            return

        from views.setup.wizard_nav import render_step_detail

        session = None
        try:
            session = await setup_session.resume_session(guild.id)
        except Exception:
            logger.exception("recovery._on_customize: resume failed")
        ok = False
        try:
            ok = await render_step_detail(
                interaction,
                guild=guild,
                member=member,
                session=session,
                section=section,
                step_index=max(self.context.step_index, 0),
            )
        except Exception:
            logger.exception("recovery._on_customize: render_step_detail failed")
            ok = False
        if not ok and not interaction.response.is_done():
            await interaction.response.send_message(
                f"Could not open the detail view for **{section.label}** — see logs.",
                ephemeral=True,
            )
        self.stop()

    async def _on_cancel(self, interaction: discord.Interaction) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content=(
                "Recovery cancelled — your wizard / hub anchor above is "
                "unchanged.  Nothing was applied or skipped."
            ),
            view=self,
        )
        self.stop()


def recovery_context_from_exception(
    *,
    section: SetupSection,
    exc: BaseException,
    origin: OriginTag = "wizard",
    step_index: int = -1,
    total_steps: int = 0,
) -> RecoveryContext:
    """Convenience helper: build a :class:`RecoveryContext` from an
    exception caught inside a section flow.

    Picks generic "What happened" / "Why" / "Recommended" / "If
    skipped" copy keyed to the section's metadata.  Section authors
    that want custom messaging build their own ``RecoveryContext``
    directly; this helper is the fall-through path for sections that
    haven't been customized yet.
    """
    exc_type = type(exc).__name__
    exc_msg = str(exc) or exc_type
    permission_hints = {
        "Forbidden": "SuperBot is missing a Discord permission for this step.",
        "HTTPException": "Discord refused the request (rate limit or API failure).",
        "TimeoutError": "The operation timed out before Discord responded.",
    }
    why = permission_hints.get(
        exc_type,
        f"{exc_type}: {exc_msg}",
    )
    return RecoveryContext(
        section=section,
        origin=origin,
        step_index=step_index,
        total_steps=total_steps,
        what_happened=(
            f"The wizard couldn't complete the **{section.label}** step "
            "without an error."
        ),
        why=why,
        recommended=(
            "Press **Retry** to try the step again, or **Skip section** "
            "to move past it and revisit later."
        ),
        if_skipped=section.description_if_skipped
        or (
            "The wizard continues with the section's current state.  "
            "You can return to it any time via the hub."
        ),
    )


__all__ = [
    "OriginTag",
    "RecoveryContext",
    "ResumeCallback",
    "SectionRecoveryView",
    "build_recovery_embed",
    "recovery_context_from_exception",
]
