"""Setup wizard hub — registry-driven section host.

The hub is the owner-gated central view that the launcher's **Start
Setup** button opens.  It renders one button per registered
`SetupSection` (see `services.setup_sections`).  Section modules under
`views.setup.sections` register themselves at import time; this module
triggers that import so the hub's button layout is always derived from
the live registry.

The hub owns three responsibilities for every section:

* **Owner gating** — every section button rejects non-owners with an
  ephemeral message before the section's `run` callback fires.
* **Error isolation** — exceptions inside a section's `run` are caught,
  logged, and surfaced as an ephemeral error if the section hasn't
  already responded.  A buggy section cannot take the hub down.
* **Step tracking** — successful section runs mark the session's
  `current_step` so the launcher relabels correctly across restarts.

No DB writes from this view directly; every state change goes through
`services.setup_session` (status / step) or `services.setup_operations`
(mutations via the dispatcher).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

import discord

# Triggers section module imports → registry registration.
import views.setup.sections  # noqa: F401
from services import setup_access, setup_progress, setup_session
from services.setup_operations import SetupOperation
from services.setup_progress import SectionProgress, badge_for
from services.setup_sections import REGISTRY, SetupSection
from services.setup_session import SetupSession
from views.base import BaseView

logger = logging.getLogger("bot.views.setup.hub")


_HUB_TITLE = "🛰 SuperBot setup wizard"
_HUB_DESCRIPTION = (
    "Step through the sections to wire SuperBot up. Each section's "
    "actions go through audited mutation pipelines; nothing applies "
    "until **Final review** confirms it."
)


def _hub_sections_value(
    sections: list[SetupSection],
    progress_by_slug: dict[str, SectionProgress] | None,
) -> str:
    """Render the "Sections" field of the hub embed.

    When ``progress_by_slug`` is ``None`` (legacy callers that haven't
    computed progress yet) the field falls back to the plain numbered
    label list.  Otherwise each row is prefixed with a status glyph
    and (for sections with staged ops) a trailing "(N pending)" hint.
    """
    if not sections:
        return "_No sections registered._"
    if progress_by_slug is None:
        return "\n".join(
            f"{idx}. {section.label}" for idx, section in enumerate(sections, start=1)
        )
    lines: list[str] = []
    for idx, section in enumerate(sections, start=1):
        progress = progress_by_slug.get(section.slug)
        if progress is None:
            lines.append(f"{idx}. {section.label}")
            continue
        glyph = badge_for(progress.status)
        line = f"{glyph} {idx}. {section.label}"
        if progress.pending_ops:
            suffix = "op" if progress.pending_ops == 1 else "ops"
            line += f" · {progress.pending_ops} pending {suffix}"
        lines.append(line)
    return "\n".join(lines)


def build_hub_embed(
    session: SetupSession | None,
    *,
    pending_ops: int | None = None,
    draft_ops: Iterable[SetupOperation] | None = None,
) -> discord.Embed:
    """Build the wizard hub embed.

    ``pending_ops`` is the count of staged ``SetupOperation`` rows for
    the guild's draft.  When non-zero it surfaces in the description so
    the operator knows there is work to apply at Final Review.  When
    ``None`` the field is omitted — callers that haven't checked the
    draft store yet (or for whom it is irrelevant) keep the legacy
    layout.

    ``draft_ops`` is the iterable of staged operations for the guild.
    When supplied it drives the per-section status badges in the
    "Sections" field.  When ``None`` the field renders without
    badges, preserving the legacy layout for callers that haven't
    been migrated yet.
    """
    color = discord.Color.blurple()
    if session is not None and session.setup_status == "complete":
        color = discord.Color.green()

    description = _HUB_DESCRIPTION
    if session is not None:
        description = f"{_HUB_DESCRIPTION}\n\n**Status:** `{session.setup_status}`"
        if session.current_step:
            description += f" · current step: `{session.current_step}`"
        if session.last_readiness_score is not None:
            description += f" · readiness `{session.last_readiness_score}%`"

    if pending_ops is not None:
        prefix = (
            description + "\n\n"
            if "**Status:**" not in description
            else description + " · "
        )
        description = f"{prefix}**Pending operations:** `{pending_ops}`"

    sections = REGISTRY.all()
    progress_by_slug: dict[str, SectionProgress] | None
    if draft_ops is None:
        progress_by_slug = None
    else:
        progress_list = setup_progress.compute_all(
            sections,
            session=session,
            draft_ops=draft_ops,
        )
        progress_by_slug = {p.slug: p for p in progress_list}

    embed = discord.Embed(
        title=_HUB_TITLE,
        description=description,
        color=color,
    )
    embed.add_field(
        name="Sections",
        value=_hub_sections_value(sections, progress_by_slug),
        inline=False,
    )
    embed.set_footer(
        text="Owner-gated. No mutation runs until you confirm in Final review.",
    )
    return embed


class SetupHubView(BaseView):
    """Top-level wizard view: renders one button per registered section.

    Section layout is filtered by the session's persisted depth
    (``quick`` / ``standard`` / ``advanced``). When ``session.depth``
    is ``None`` (the legacy / pre-picker path) every registered
    section renders so the hub is never empty.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        session: SetupSession | None = None,
        public: bool = False,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.session = session
        depth = session.depth if session is not None else None
        for section in REGISTRY.for_depth(depth):
            self.add_item(self._build_section_button(section))
        self.add_item(self._build_change_depth_button())

    def _build_change_depth_button(self) -> discord.ui.Button:
        button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Change depth",
            style=discord.ButtonStyle.secondary,
            custom_id="setup_hub:change_depth",
            row=4,
        )

        async def _callback(interaction: discord.Interaction) -> None:
            if not await self._gate_owner(interaction):
                return
            from views.setup.depth_panel import (
                DepthPanelView,
                build_depth_embed,
            )

            await self._refresh_session()
            view = DepthPanelView(interaction.user, session=self.session)
            await interaction.response.edit_message(
                embed=build_depth_embed(),
                view=view,
            )

        button.callback = _callback  # type: ignore[method-assign]
        return button

    async def _refresh_session(self) -> None:
        if self.session is None:
            return
        refreshed = await setup_session.resume_session(self.session.guild_id)
        if refreshed is not None:
            self.session = refreshed

    async def _gate_owner(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use this from inside the server.",
                ephemeral=True,
            )
            return False
        if not setup_access.is_server_owner(member):
            await interaction.response.send_message(
                "Only the server owner can run the wizard.",
                ephemeral=True,
            )
            return False
        return True

    def _build_section_button(self, section: SetupSection) -> discord.ui.Button:
        button: discord.ui.Button = discord.ui.Button(
            label=section.label,
            style=section.style,
            emoji=section.emoji,
            custom_id=f"setup_section:{section.slug}",
        )

        async def _callback(
            interaction: discord.Interaction,
            *,
            sec: SetupSection = section,
        ) -> None:
            if not await self._gate_owner(interaction):
                return
            try:
                await sec.run(interaction, self)
            except Exception:
                logger.exception("setup hub section %s failed", sec.slug)
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"Section `{sec.slug}` failed. Check logs.",
                        ephemeral=True,
                    )

        button.callback = _callback  # type: ignore[assignment]
        return button


__all__ = [
    "SetupHubView",
    "build_hub_embed",
]
