from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from utils import db
from utils.ui_constants import ROLE_COLOR
from views.base import BaseView
from views.navigation import attach_back_button


class ReactionRolesPanel(BaseView):
    """Displays all reaction role bindings for the guild."""

    def __init__(self, ctx: commands.Context, parent: BaseView | None = None) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.parent = parent

        if parent is not None:

            async def _build_parent(
                _interaction: discord.Interaction,
            ) -> tuple[discord.Embed, discord.ui.View]:
                return parent.build_embed(), parent

            attach_back_button(
                self,
                label="↩ Back",
                custom_id="role:reaction:back",
                parent_builder=_build_parent,
                row=0,
            )

    async def build_embed(self) -> discord.Embed:
        rows = await db.get_all_reaction_roles(self.ctx.guild.id)
        embed = discord.Embed(title="💬 Reaction Roles", color=ROLE_COLOR)
        if rows:
            lines = []
            for r in rows:
                role = resources.resolve_role(self.ctx.guild, role_id=r["role_id"])
                role_str = role.mention if role else f"*(deleted role {r['role_id']})*"
                lines.append(f"Message `{r['message_id']}` · {r['emoji']} → {role_str}")
            embed.description = "\n".join(lines)
        else:
            embed.description = (
                "No reaction roles configured.\n\n"
                "Use `!reactroles <message_id> <emoji> <@role>` to add one.\n"
                "Use `!removereactrole <message_id> <emoji>` to remove one."
            )
        embed.set_footer(text="Members react to earn their role automatically.")
        return embed

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.grey, row=0)
    async def refresh_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )
