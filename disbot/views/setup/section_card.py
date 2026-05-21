"""Setup wizard section card — shared entry panel for setup sections.

Every section that supports the new staged-navigation pattern uses this
module's :func:`show` helper as its registered ``run`` callback. The
card surfaces, in one place:

* step number + total
* section purpose (the registered label)
* detected current state (section-specific text)
* "if you skip this" description (from ``SetupSection.description_if_skipped``)
* pending op count + status badge (from ``services.setup_progress``)
* a button row: **Apply Recommended** · **Customize** · **Skip** · **Hub**

Buttons:

* **Apply Recommended** — calls the section's ``recommended_ops_builder``
  (passed in by the section module) and stages each returned
  :class:`SetupOperation` via :func:`services.setup_draft.append` with
  metadata ``source="setup_ux:recommended"``. Disabled when no
  builder was supplied.
* **Customize** — calls the section-supplied ``on_customize`` callback,
  which typically opens the section's existing detail view. Disabled
  when no callback was supplied.
* **Skip** — calls :func:`services.setup_session.mark_section_skipped`
  and closes the card.
* **Hub** — closes the card; the hub message remains the operator's
  anchor.

Constraints preserved:

* No DB writes from the view — only via the canonical
  ``setup_draft.append`` and ``setup_session.mark_section_skipped``.
* No SetupOperation kinds invented here — recommended builders return
  the same kinds the section already supports.
* Final Review remains the only apply gate. Apply Recommended **stages**;
  nothing executes until Final Review confirms.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

import discord

from services import setup_draft, setup_progress, setup_session
from services.setup_operations import SetupOperation
from services.setup_progress import SectionProgress, badge_for
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.section_card")


CustomizeCallback = Callable[
    [discord.Interaction, "SetupHubView | None"],
    Awaitable[None],
]

RecommendedOpsBuilder = Callable[[discord.Guild], list[SetupOperation]]


_STATUS_LABELS = {
    "not_started": "Not started",
    "recommended": "Recommended selected",
    "customized": "Customized",
    "skipped": "Skipped",
    "needs_attention": "Needs attention",
    "applied": "Applied",
}


def _step_index(section: SetupSection, sections: list[SetupSection]) -> int:
    """Return the 1-based position of ``section`` in ``sections``."""
    for idx, s in enumerate(sections, start=1):
        if s.slug == section.slug:
            return idx
    return 0


def build_section_card(
    *,
    section: SetupSection,
    progress: SectionProgress,
    detected_state: str,
    has_recommended: bool,
    has_customize: bool,
) -> discord.Embed:
    """Build the section card embed.

    The card is the single source of section-level UX: every field an
    operator might want when standing on a stage panel is rendered
    here. Section modules supply ``detected_state`` (what's currently
    configured) and the booleans flag whether the corresponding action
    will be enabled in the button row.
    """
    sections = REGISTRY.all()
    total = len(sections)
    step = _step_index(section, sections)
    glyph = badge_for(progress.status)
    status_label = _STATUS_LABELS.get(progress.status.value, progress.status.value)

    title_emoji = section.emoji or "🛰"
    title = f"{title_emoji} {section.label}"

    color = discord.Color.blurple()
    if progress.status.value in ("recommended", "applied"):
        color = discord.Color.green()
    elif progress.status.value == "skipped":
        color = discord.Color.dark_grey()
    elif progress.status.value == "needs_attention":
        color = discord.Color.gold()

    embed = discord.Embed(
        title=title,
        description=(
            f"**Step {step} of {total}** · {glyph} *{status_label}*"
            if step
            else f"{glyph} *{status_label}*"
        ),
        color=color,
    )
    embed.add_field(
        name="Detected",
        value=detected_state or "_(no state detected)_",
        inline=False,
    )
    recommended_value = (
        "Click **Apply Recommended** to stage the section's safe defaults."
        if has_recommended
        else "_(this section has no recommended defaults — use Customize.)_"
    )
    embed.add_field(name="Recommended action", value=recommended_value, inline=False)
    if section.description_if_skipped:
        embed.add_field(
            name="If you skip this",
            value=section.description_if_skipped,
            inline=False,
        )
    if progress.pending_ops:
        suffix = "operation" if progress.pending_ops == 1 else "operations"
        embed.add_field(
            name="Pending",
            value=f"{progress.pending_ops} {suffix} staged for Final review.",
            inline=False,
        )
    footer_bits = []
    if has_customize:
        footer_bits.append("Customize to open the detailed picker")
    footer_bits.append("Final Review applies all staged ops")
    embed.set_footer(text=" · ".join(footer_bits))
    return embed


class SectionCardView(BaseView):
    """Card view that owns the four-button section panel."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        section: SetupSection,
        hub: SetupHubView | None,
        on_customize: CustomizeCallback | None,
        recommended_ops_builder: RecommendedOpsBuilder | None,
    ) -> None:
        super().__init__(author, timeout=180)
        self._section = section
        self._hub = hub
        self._on_customize = on_customize
        self._recommended_ops_builder = recommended_ops_builder

        self._apply_button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Apply Recommended",
            style=discord.ButtonStyle.success,
            custom_id=f"setup_card:{section.slug}:apply_recommended",
            disabled=recommended_ops_builder is None,
        )
        self._apply_button.callback = self._apply_recommended  # type: ignore[method-assign]
        self.add_item(self._apply_button)

        self._customize_button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Customize",
            style=discord.ButtonStyle.primary,
            custom_id=f"setup_card:{section.slug}:customize",
            disabled=on_customize is None,
        )
        self._customize_button.callback = self._customize  # type: ignore[method-assign]
        self.add_item(self._customize_button)

        self._skip_button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Skip",
            style=discord.ButtonStyle.secondary,
            custom_id=f"setup_card:{section.slug}:skip",
        )
        self._skip_button.callback = self._skip  # type: ignore[method-assign]
        self.add_item(self._skip_button)

        self._hub_button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="↩ Hub",
            style=discord.ButtonStyle.secondary,
            custom_id=f"setup_card:{section.slug}:hub",
        )
        self._hub_button.callback = self._return_to_hub  # type: ignore[method-assign]
        self.add_item(self._hub_button)

    async def _apply_recommended(self, interaction: discord.Interaction) -> None:
        if self._recommended_ops_builder is None:
            await interaction.response.send_message(
                "This section has no recommended defaults.",
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
            ops = self._recommended_ops_builder(guild)
        except Exception:
            logger.exception(
                "section_card._apply_recommended: builder failed (section=%s)",
                self._section.slug,
            )
            await interaction.response.send_message(
                "Could not build the recommended defaults. See logs.",
                ephemeral=True,
            )
            return
        if not ops:
            await interaction.response.send_message(
                "No recommended operations were generated for this section.",
                ephemeral=True,
            )
            return

        for op in ops:
            try:
                await setup_draft.append(
                    op,
                    guild_id=interaction.guild_id,
                    actor_id=interaction.user.id,
                    label=f"[Recommended] {op.kind}",
                    metadata={"source": "setup_ux:recommended"},
                )
            except Exception:
                logger.exception(
                    "section_card._apply_recommended: append failed",
                )

        try:
            await setup_session.unmark_section_skipped(
                interaction.guild_id,
                self._section.slug,
            )
        except Exception:
            logger.exception("section_card: unmark skip failed")

        word = "operation" if len(ops) == 1 else "operations"
        await interaction.response.send_message(
            f"Staged **{len(ops)} recommended {word}** for {self._section.label}. "
            "Open Final review to apply.",
            ephemeral=True,
        )

    async def _customize(self, interaction: discord.Interaction) -> None:
        if self._on_customize is None:
            await interaction.response.send_message(
                "This section has no detail view yet.",
                ephemeral=True,
            )
            return
        try:
            await self._on_customize(interaction, self._hub)
        except Exception:
            logger.exception(
                "section_card._customize: handler failed (section=%s)",
                self._section.slug,
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Could not open the detail view. See logs.",
                    ephemeral=True,
                )

    async def _skip(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "Skip requires a guild context.",
                ephemeral=True,
            )
            return
        try:
            await setup_session.mark_section_skipped(
                interaction.guild_id,
                self._section.slug,
            )
        except Exception:
            logger.exception(
                "section_card._skip: mark_section_skipped failed (section=%s)",
                self._section.slug,
            )
            await interaction.response.send_message(
                "Could not record the skip. See logs.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"Marked **{self._section.label}** as skipped. "
            f"Reopen the section any time to change your mind.",
            ephemeral=True,
        )

    async def _return_to_hub(self, interaction: discord.Interaction) -> None:
        # Closing the ephemeral card returns the operator to the hub
        # message that was already open above it.
        await interaction.response.send_message(
            "Returning to the setup hub above.",
            ephemeral=True,
        )


async def show(
    interaction: discord.Interaction,
    *,
    hub: SetupHubView | None,
    section: SetupSection,
    detected_state: str = "",
    on_customize: CustomizeCallback | None = None,
    recommended_ops_builder: RecommendedOpsBuilder | None = None,
) -> None:
    """Render the section card for ``section`` and post it ephemerally.

    Builds the embed from live session + draft state so the card
    reflects today's progress. The card view captures the supplied
    callbacks so each section can plug in its own detail view and
    recommended-ops builder.
    """
    guild = interaction.guild
    member = interaction.user
    if guild is None or interaction.guild_id is None:
        await interaction.response.send_message(
            "Setup sections must be opened inside the server.",
            ephemeral=True,
        )
        return

    try:
        session = await setup_session.resume_session(interaction.guild_id)
    except Exception:
        logger.exception("section_card.show: resume_session failed")
        session = None

    try:
        draft_ops = await setup_draft.list_ops(interaction.guild_id)
    except Exception:
        logger.exception("section_card.show: list_ops failed")
        draft_ops = []

    progress = setup_progress.compute_section_status(
        section,
        session=session,
        draft_ops=draft_ops,
    )

    embed = build_section_card(
        section=section,
        progress=progress,
        detected_state=detected_state,
        has_recommended=recommended_ops_builder is not None,
        has_customize=on_customize is not None,
    )
    view = SectionCardView(
        member,
        section=section,
        hub=hub,
        on_customize=on_customize,
        recommended_ops_builder=recommended_ops_builder,
    )
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
    )

    try:
        await setup_session.mark_in_progress(
            interaction.guild_id,
            step=section.session_step,
        )
    except Exception:
        logger.exception("section_card.show: mark_in_progress failed")


__all__ = [
    "CustomizeCallback",
    "RecommendedOpsBuilder",
    "SectionCardView",
    "build_section_card",
    "show",
]
