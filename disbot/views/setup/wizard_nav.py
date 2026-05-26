"""Setup-wizard anchor navigation helpers.

Single owner of two operations on the durable workspace anchor:

* :func:`render_wizard_step` — rebuild the wizard embed + view at a
  given step (or at ``session.current_step``) and edit the clicked
  interaction's anchor in place.
* :func:`render_step_detail` — swap the wizard anchor into a section's
  detail mode by calling the section's ``detail_embed_builder`` and
  ``detail_view_builder`` and injecting an ``↩ Back to step`` button
  that re-runs :func:`render_wizard_step` at the originating step.

Both functions go through
:func:`core.runtime.interaction_helpers.safe_edit` so the anchor
message id is preserved. The durable-anchor first-post and the
persisted ``setup_message_id`` row are owned by
:func:`views.setup.wizard.open_setup_workspace`; nothing in this
module clears or rewrites the session row's anchor id.

Callgraph note: detail builders are stored as attributes on a frozen
``SetupSection`` dataclass and invoked via
``await section.detail_embed_builder(...)``. CodeGraph cannot see
these as edges from this module to e.g.
``views.setup.sections.channels.build_channels_embed``. When
reviewing dead-code claims for section builder helpers, grep-verify.

Row layout: ``render_step_detail`` injects the Back button on
``row=4``. Section ``detail_view_builder`` implementations must keep
rows 0–3 free for their own components (selects, buttons).
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import setup_draft, setup_session
from services.setup_sections import SetupSection
from services.setup_session import SetupSession

logger = logging.getLogger("bot.views.setup.wizard_nav")


async def render_wizard_step(
    interaction: discord.Interaction,
    *,
    guild: discord.Guild,
    member: discord.Member,
    session: SetupSession | None,
    step_index: int | None = None,
) -> bool:
    """Rebuild the wizard anchor at ``step_index`` and edit it in place.

    When ``step_index`` is ``None`` the step is resolved from
    ``session.current_step`` via the wizard's existing
    ``_step_index_for`` helper. The session is refreshed from the DB
    so depth changes and skipped/acknowledged updates are reflected.

    Returns ``True`` on a successful anchor edit.
    """
    from views.setup.wizard import (
        _WIZARD_TITLE,
        LinearWizardView,
        _resolve_sections,
        _step_index_for,
        build_wizard_step_embed,
    )

    try:
        refreshed = await setup_session.resume_session(guild.id)
        if refreshed is not None:
            session = refreshed
    except Exception:
        logger.exception("wizard_nav.render_wizard_step: resume failed")

    sections = _resolve_sections(session)
    if step_index is None:
        step_index = _step_index_for(session, sections)
    if sections:
        if step_index < 0:
            step_index = 0
        elif step_index >= len(sections):
            step_index = len(sections) - 1
    else:
        step_index = 0

    try:
        draft_rows = await setup_draft.list_rows(guild.id)
    except Exception:
        logger.exception("wizard_nav.render_wizard_step: list_rows failed")
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
                "Pick a different depth via `/setup-depth`."
            ),
            color=discord.Color.dark_grey(),
        )

    view = LinearWizardView(
        member,
        session=session,
        sections=sections,
        step_index=step_index,
    )

    return await safe_edit(interaction, embed=embed, view=view)


async def render_step_detail(
    interaction: discord.Interaction,
    *,
    guild: discord.Guild,
    member: discord.Member,
    session: SetupSession | None,
    section: SetupSection,
    step_index: int,
) -> bool:
    """Swap the wizard anchor to ``section``'s detail embed + view.

    Calls ``section.detail_embed_builder`` and
    ``section.detail_view_builder`` (both required for wizard-native
    Customize), injects an ``↩ Back to step`` button on row 4, then
    edits the anchor in place. The Back button restores the wizard
    view at ``step_index``.

    Returns ``True`` when the anchor was edited successfully.
    """
    if section.detail_embed_builder is None or section.detail_view_builder is None:
        logger.error(
            "wizard_nav.render_step_detail: section %s missing detail builders",
            section.slug,
        )
        return False

    if not await safe_defer(interaction):
        return False

    try:
        draft_rows = await setup_draft.list_rows(guild.id)
    except Exception:
        logger.exception("wizard_nav.render_step_detail: list_rows failed")
        draft_rows = []

    try:
        embed = await section.detail_embed_builder(
            guild,
            session=session,
            draft_rows=draft_rows,
        )
    except Exception:
        logger.exception(
            "wizard_nav.render_step_detail: detail_embed_builder failed (slug=%s)",
            section.slug,
        )
        return False

    try:
        view = section.detail_view_builder(
            member,
            section=section,
            guild=guild,
            session=session,
        )
    except Exception:
        logger.exception(
            "wizard_nav.render_step_detail: detail_view_builder failed (slug=%s)",
            section.slug,
        )
        return False

    back_button = _build_back_to_step_button(step_index=step_index)
    try:
        view.add_item(back_button)
    except Exception:
        logger.exception(
            "wizard_nav.render_step_detail: add_item(back_button) failed (slug=%s)",
            section.slug,
        )
        return False

    try:
        await setup_session.mark_in_progress(guild.id, step=section.session_step)
    except Exception:
        logger.exception(
            "wizard_nav.render_step_detail: mark_in_progress failed",
        )

    return await safe_edit(interaction, embed=embed, view=view)


def _build_back_to_step_button(*, step_index: int) -> discord.ui.Button:
    """Build the row-4 Back button injected into every step-detail view."""
    button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
        label="↩ Back to step",
        style=discord.ButtonStyle.secondary,
        custom_id=f"setup_wizard:back_to_step:{step_index}",
        row=4,
    )

    async def _callback(interaction: discord.Interaction) -> None:
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use this from inside the server.",
                ephemeral=True,
            )
            return
        session: SetupSession | None = None
        try:
            session = await setup_session.resume_session(guild.id)
        except Exception:
            logger.exception(
                "wizard_nav.back_to_step: resume failed",
            )
        ok = await render_wizard_step(
            interaction,
            guild=guild,
            member=member,
            session=session,
            step_index=step_index,
        )
        if not ok and not interaction.response.is_done():
            await interaction.response.send_message(
                "Could not restore the wizard view — see logs.",
                ephemeral=True,
            )

    button.callback = _callback  # type: ignore[method-assign]
    return button


__all__ = [
    "render_step_detail",
    "render_wizard_step",
]
