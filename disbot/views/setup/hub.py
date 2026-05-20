"""Setup wizard hub — Phase 9i / Track 8 PR 23.

The owner-gated central view the launcher's **Start Setup** button
opens. Lists the wizard sections and lets the operator step
through them. Section state is persisted in
``setup_session.current_step`` so the wizard survives bot
restarts.

Sections (this PR ships the minimum-viable orchestration; the
section-specific views can fill in their detail panels in
follow-up PRs):

* **Readiness** — drop into ``build_setup_readiness_embed``
  rendered ephemerally.
* **Smart suggestions** — open ``AIReviewPanelView`` against the
  current ``GuildSnapshot``.
* **Final review** — open ``FinalReviewView`` to apply the
  ``AcceptedSet`` through the existing mutation pipelines.

No DB writes from this view directly; every state change goes
through ``services.setup_session`` (status / step tracking) or
the mutation pipelines (via :class:`FinalReviewView`).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_access, setup_session
from services.setup_session import SetupSession
from views.base import BaseView

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.views.setup.hub")


def _build_suggestions_embed(draft) -> discord.Embed:
    """Render the deterministic advisor's draft as a compact list.

    The full AI-review interactive panel ships in a follow-up; v1
    of the wizard renders the draft inline so the operator can
    eyeball the recommendations and reach for **Final review** for
    apply.
    """
    if not getattr(draft, "recommendations", ()):
        return discord.Embed(
            title="🤖 Smart suggestions",
            description=(
                "The deterministic advisor produced no recommendations "
                "for this guild. Either every binding is already "
                "configured or the channel/category names did not "
                "match the rule table."
            ),
            color=discord.Color.dark_grey(),
        )
    embed = discord.Embed(
        title="🤖 Smart suggestions",
        description=(
            f"_{_REVIEW_HEADER}_\n\n"
            f"**{len(draft.recommendations)}** recommendation(s) — "
            "open **Final review** to apply the high-confidence ones."
        ),
        color=discord.Color.blurple(),
    )
    lines = [
        f"• `{rec.subsystem}.{rec.binding_name}` → "
        f"`{rec.target_name}` ({rec.confidence})"
        for rec in draft.recommendations
    ]
    value = "\n".join(lines)
    if len(value) > 1000:
        value = value[:997] + "..."
    embed.add_field(name="Recommendations", value=value, inline=False)
    return embed


_REVIEW_HEADER = "Smart suggestions are recommendations. Review before applying."


_HUB_TITLE = "🛰 SuperBot setup wizard"
_HUB_DESCRIPTION = (
    "Step through the sections to wire SuperBot up. Each section's "
    "actions go through audited mutation pipelines; nothing applies "
    "until **Final review** confirms it."
)


def build_hub_embed(session: SetupSession | None) -> discord.Embed:
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

    embed = discord.Embed(
        title=_HUB_TITLE,
        description=description,
        color=color,
    )
    embed.add_field(
        name="Sections",
        value=(
            "1. Run readiness scan\n"
            "2. Smart suggestions (review + accept)\n"
            "3. Final review (apply accepted plan)"
        ),
        inline=False,
    )
    embed.set_footer(
        text=("Owner-gated. No mutation runs until you confirm in Final review."),
    )
    return embed


class SetupHubView(BaseView):
    """Top-level wizard view: lists sections + drives transitions."""

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

    @discord.ui.button(
        label="Run readiness scan",
        style=discord.ButtonStyle.primary,
    )
    async def _readiness(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not await self._gate_owner(interaction):
            return
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Readiness requires a guild context.",
                ephemeral=True,
            )
            return
        from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

        embed = await build_setup_readiness_embed(guild.id, guild=guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Persist the readiness step so the launcher relabels correctly.
        try:
            await setup_session.mark_in_progress(guild.id, step="readiness")
        except Exception:
            logger.exception("setup hub: mark_in_progress failed")

    @discord.ui.button(
        label="Smart suggestions",
        style=discord.ButtonStyle.success,
    )
    async def _suggestions(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not await self._gate_owner(interaction):
            return
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Smart suggestions require a guild context.",
                ephemeral=True,
            )
            return
        from services.guild_snapshot import collect as collect_snapshot
        from services.setup_plan import DeterministicAdvisor

        try:
            snapshot = await collect_snapshot(guild)
            draft = await DeterministicAdvisor().suggest(snapshot)
        except Exception:
            logger.exception("setup hub: advisor flow failed")
            await interaction.response.send_message(
                "Advisor failed. Try again later or run readiness for "
                "a deterministic baseline.",
                ephemeral=True,
            )
            return

        embed = _build_suggestions_embed(draft)
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )
        try:
            await setup_session.mark_in_progress(
                guild.id,
                step="suggestions",
            )
        except Exception:
            logger.exception("setup hub: mark_in_progress failed")

    @discord.ui.button(
        label="Final review",
        style=discord.ButtonStyle.secondary,
    )
    async def _final_review(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not await self._gate_owner(interaction):
            return
        from views.setup.final_review import FinalReviewView, build_final_review_embed

        # In v1 the operator drives Smart suggestions → accept set first.
        # Without an accepted set in this view's state we just open an
        # empty FinalReview so the operator sees the "nothing to apply" copy.
        final = FinalReviewView(interaction.user, accepted=[])
        await interaction.response.send_message(
            embed=build_final_review_embed(final.accepted),
            view=final,
            ephemeral=True,
        )


__all__ = [
    "SetupHubView",
    "build_hub_embed",
]
