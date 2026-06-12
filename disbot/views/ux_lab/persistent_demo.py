"""UX Lab — the restart-survival exhibit (a real, registered PersistentView).

Posted by the buttons wing's ``persistent_panel`` exhibit. This is the
canonical persistence mechanism, not a simulation: ``@register`` + a
boot-time ``bot.add_view`` (anchor-free, the ``SetupLauncherView``
precedent) + static custom_ids. Press the button, restart the bot, press it
again — it still answers, because discord.py re-matches the custom_id to
the registered class.

Stateless on purpose (the PersistentView contract): the only data shown is
carried by the message itself or the click-time interaction.
"""

from __future__ import annotations

import discord

from core.runtime.persistent_views import PersistentView, register
from views.base import interaction_is_admin


@register
class UxLabPersistentDemo(PersistentView):
    """Two buttons that keep working across bot restarts."""

    SUBSYSTEM = "ux_lab"

    @discord.ui.button(
        label="Press me (survives restarts)",
        style=discord.ButtonStyle.primary,
        emoji="♻️",
        custom_id="ux_lab:persist:ping",
    )
    async def ping(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        posted = (
            discord.utils.format_dt(interaction.message.created_at, style="R")
            if interaction.message
            else "?"
        )
        await interaction.response.send_message(
            f"♻️ Alive. This panel was posted {posted} — if the bot restarted "
            "since, this click was matched by **custom_id** to the registered "
            "view class (`timeout=None` + static ids). That is the whole "
            "PersistentView mechanism.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Remove this demo",
        style=discord.ButtonStyle.secondary,
        emoji="🗑️",
        custom_id="ux_lab:persist:remove",
    )
    async def remove(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        # Persistent panels outlive author-lock context — re-check authority
        # at callback time (the capability-authority panel rule).
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "Only an administrator can remove the demo panel.",
                ephemeral=True,
            )
            return
        if interaction.message:
            await interaction.message.delete()


def build_persistent_demo_embed() -> discord.Embed:
    return discord.Embed(
        title="♻️ Persistent panel demo",
        description=(
            "This panel uses the **canonical PersistentView mechanism** "
            "(`timeout=None`, static custom_ids, boot-time registration).\n\n"
            "**The test:** press the button now, restart the bot, press it "
            "again. It keeps answering — unlike every other lab panel, which "
            "greys out at timeout.\n\n"
            "-# 🗑️ removes the panel (admin only) so demos don't accumulate."
        ),
        color=discord.Color.green(),
    )
