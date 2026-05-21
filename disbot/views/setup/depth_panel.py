"""Setup-wizard depth picker — first menu the operator sees.

When the operator opens the wizard for the first time the bot does
not yet know how much help they want. The depth picker offers three
buckets:

* **Quick** — only the essentials (server scan → preset → final review).
* **Standard** — quick + channels & log routing + cleanup.
* **Advanced** — every registered section (smart suggestions, cog
  routing, identity, etc.).

The chosen depth is persisted on
:attr:`services.setup_session.SetupSession.depth` via
:func:`services.setup_session.set_depth` and used by the hub
(:class:`views.setup.hub.SetupHubView`) to filter which sections
render as buttons. The picker can be re-entered later from the hub's
**Change depth** button to widen or narrow the scope mid-run.

Constraint preservation:

* No DB writes from the buttons except through ``set_depth``.
* No SetupOperations staged here.
* The picker swaps the panel in place via ``edit_message`` — the
  wizard's single anchored message stays the operator's working
  surface.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_session
from services.setup_session import SetupSession
from views.base import BaseView

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.views.setup.depth_panel")


_DEPTH_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "quick": (
        "⚡ Quick",
        "3 steps — server scan, choose a preset, apply. Best for small "
        "servers that just want safe defaults.",
    ),
    "standard": (
        "🛠 Standard",
        "5–6 steps — scan, channels & logging, cleanup, optional preset, "
        "review. Best for most communities.",
    ),
    "advanced": (
        "🔬 Advanced",
        "Every section — identity, smart suggestions, cog routing, "
        "cleanup, channels, presets. Best for owners who want control.",
    ),
}


def build_depth_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛰 Choose your setup depth",
        description=(
            "How detailed do you want the wizard to be? You can change "
            "this later from the hub. Your selection only filters which "
            "sections appear — nothing applies until **Final review**."
        ),
        color=discord.Color.blurple(),
    )
    for label, description in _DEPTH_DESCRIPTIONS.values():
        embed.add_field(name=label, value=description, inline=False)
    embed.set_footer(text="Recommended: Standard.")
    return embed


class DepthPanelView(BaseView):
    """Three-button depth picker. Each button persists the selection
    and swaps the panel to the setup hub in place.

    Constructor takes the live session so we can show the operator
    which depth (if any) is currently chosen — the corresponding
    button is styled in success colour as a visual cue.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        session: SetupSession | None = None,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, timeout=timeout)
        current = session.depth if session is not None else None
        for slug in ("quick", "standard", "advanced"):
            label, _ = _DEPTH_DESCRIPTIONS[slug]
            style = (
                discord.ButtonStyle.success
                if slug == current
                else discord.ButtonStyle.secondary
            )
            button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
                label=label,
                style=style,
                custom_id=f"setup_depth:{slug}",
            )

            async def _callback(
                interaction: discord.Interaction,
                *,
                chosen: str = slug,
            ) -> None:
                await self._select(interaction, chosen)

            button.callback = _callback  # type: ignore[method-assign]
            self.add_item(button)

    async def _select(
        self,
        interaction: discord.Interaction,
        depth: str,
    ) -> None:
        guild = interaction.guild
        if guild is None or interaction.guild_id is None:
            await interaction.response.send_message(
                "Depth picker requires a guild context.",
                ephemeral=True,
            )
            return
        try:
            await setup_session.set_depth(interaction.guild_id, depth)
        except Exception:
            logger.exception(
                "depth_panel._select: set_depth failed (depth=%s)",
                depth,
            )
            await interaction.response.send_message(
                "Could not save your depth choice. See logs.",
                ephemeral=True,
            )
            return

        # Open the hub at the selected depth.
        from services import setup_draft
        from views.setup.hub import SetupHubView, build_hub_embed

        try:
            session = await setup_session.resume_session(interaction.guild_id)
        except Exception:
            logger.exception("depth_panel._select: resume_session failed")
            session = None
        try:
            draft_ops = await setup_draft.list_ops(interaction.guild_id)
        except Exception:
            logger.exception("depth_panel._select: list_ops failed")
            draft_ops = []

        hub = SetupHubView(interaction.user, session=session)
        embed = build_hub_embed(
            session,
            pending_ops=len(draft_ops),
            draft_ops=draft_ops,
        )
        await interaction.response.edit_message(embed=embed, view=hub)
        self.stop()


__all__ = [
    "DepthPanelView",
    "build_depth_embed",
]
