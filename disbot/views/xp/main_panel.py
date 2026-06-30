"""XP hub panel (S4.2-followup extraction).

``_XpHubView`` is the interactive XP panel opened by ``!xpmenu`` and
referenced by ``HelpCog`` via ``XpCog.build_help_menu_view``.  Shows
the invoking user's rank card with stat-switch and admin-action buttons.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from services.xp_helpers import _build_rank_embed, build_rank_response
from views.base import HubView, interaction_is_admin, member_is_admin


class _XpHubView(HubView):
    """Interactive XP hub — shows rank card with quick admin actions."""

    def __init__(self, ctx: commands.Context):
        super().__init__(ctx.author)
        self.ctx = ctx

    def _decorate(self, embed: discord.Embed) -> None:
        """Apply the hub's title / footer / admin-button state to ``embed``.

        Shared by every render path (``build_response`` for the direct
        ``!xpmenu`` surface *and* the ``build_help_menu_view`` help-nav hook —
        both now render the image card via the help-nav attachment seam — the
        three stat-switch buttons, and ``build_embed`` for the config-panel
        back-navigation) so the chrome stays in exactly one place.
        """
        embed.title = f"🏆 XP Panel — {self.ctx.author.display_name}"
        is_admin = member_is_admin(self.ctx.author)
        lines = ["Use the buttons below to switch stat views."]
        if is_admin:
            lines.append("Admin controls: ⚙️ Configure · 🎁 Give XP · 🔄 Reset XP")
        embed.set_footer(text=" · ".join(lines))
        # Show or hide admin buttons based on permissions
        for item in self.children:
            if hasattr(item, "_admin_only"):
                item.disabled = not is_admin

    async def build_response(
        self,
        stat: str = "both",
    ) -> tuple[discord.Embed, discord.File | None]:
        """The direct ``!xpmenu`` surface — the rank embed plus its image card.

        Reuses the fetch-once :func:`build_rank_response` (the same embed + card
        the ``!rank`` view renders, visual card engine H3); the card is ``None``
        on a Pillow-less host, where the embed stays the source of truth.
        """
        embed, card = await build_rank_response(self.ctx.author, self.ctx.guild, stat)  # type: ignore[arg-type]
        self._decorate(embed)
        return embed, card

    async def build_embed(self) -> discord.Embed:
        # Embed-only path for the config-panel back-navigation, which rebuilds
        # the parent hub embed (``XpConfigView`` → ``parent.build_embed()``). The
        # help-nav hook and the direct ``!xpmenu`` surface both render the image
        # card via ``build_response`` + the help-nav attachment seam.
        embed = await _build_rank_embed(self.ctx.author, self.ctx.guild, "both")  # type: ignore[arg-type]
        self._decorate(embed)
        return embed

    async def _switch_stat(self, interaction: discord.Interaction, stat: str) -> None:
        """Re-render the hub for ``stat`` in place, swapping the card attachment.

        Mirrors ``views.xp.rank_view._RankSelect.callback`` (the H3 toggle
        grammar): pass ``attachments`` explicitly so the new card replaces the
        old one, or clears it (``[]``) on the embed-only fallback.
        """
        embed, card = await self.build_response(stat)
        await interaction.response.edit_message(
            embed=embed,
            view=self,
            attachments=[card] if card is not None else [],
        )

    @discord.ui.button(label="📊 Both", style=discord.ButtonStyle.blurple, row=0)
    async def btn_both(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._switch_stat(interaction, "both")

    @discord.ui.button(label="🏆 XP", style=discord.ButtonStyle.blurple, row=0)
    async def btn_xp(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._switch_stat(interaction, "xp")

    @discord.ui.button(label="🪙 Coins", style=discord.ButtonStyle.blurple, row=0)
    async def btn_coins(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._switch_stat(interaction, "coins")

    @discord.ui.button(label="⚙️ Configure", style=discord.ButtonStyle.grey, row=1)
    async def btn_config(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return
        from views.xp.config_panel import XpConfigView

        config_view = XpConfigView(self.ctx, parent=self)
        config_view.message = self.message
        # The config panel has no hero image, so clear the rank card explicitly —
        # otherwise Discord keeps the prior attachment and the rank card lingers
        # as a stray image under the config panel (same contract as the stat
        # toggles in ``_switch_stat``). See bug book BUG-0025.
        await interaction.response.edit_message(
            embed=await config_view.build_embed(),
            view=config_view,
            attachments=[],
        )

    @discord.ui.button(label="🎁 Give XP", style=discord.ButtonStyle.grey, row=1)
    async def btn_givexp(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return
        from views.xp.modals import _GiveXpModal

        await interaction.response.send_modal(_GiveXpModal(self))

    @discord.ui.button(label="🔄 Reset XP", style=discord.ButtonStyle.danger, row=1)
    async def btn_resetxp(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return
        from views.xp.modals import _ResetXpModal

        await interaction.response.send_modal(_ResetXpModal(self))
