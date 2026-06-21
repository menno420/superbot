from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from services import reaction_role_service
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
        embed = discord.Embed(title="💬 Reaction Roles", color=ROLE_COLOR)

        menus = await reaction_role_service.list_menus(self.ctx.guild.id)
        menu_lines = []
        for m in menus:
            posted = "📕 draft" if not m.get("message_id") else "📗 live"
            menu_lines.append(
                f"`#{m['menu_id']}` {posted} · **{m['title']}** "
                f"({m['style']}/{m['mode']})",
            )

        rows = await db.get_all_reaction_roles(self.ctx.guild.id)
        emoji_lines = []
        for r in rows:
            role = resources.resolve_role(self.ctx.guild, role_id=r["role_id"])
            role_str = role.mention if role else f"*(deleted role {r['role_id']})*"
            emoji_lines.append(
                f"Message `{r['message_id']}` · {r['emoji']} → {role_str}",
            )

        embed.add_field(
            name="🧩 Role menus (buttons / dropdowns)",
            value=(
                "\n".join(menu_lines)
                if menu_lines
                else "*None yet — press **➕ New Menu** to build one.*"
            ),
            inline=False,
        )
        embed.add_field(
            name="😀 Emoji reaction bindings",
            value=(
                "\n".join(emoji_lines)
                if emoji_lines
                else (
                    "*None.* Use `!reactroles <message_id> <emoji> <@role>` "
                    "to add a legacy emoji binding."
                )
            ),
            inline=False,
        )
        embed.set_footer(
            text="Role menus are the modern surface — one tap, no stale reactions.",
        )
        return embed

    @discord.ui.button(label="➕ New Menu", style=discord.ButtonStyle.green, row=0)
    async def new_menu_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not interaction.user.guild_permissions.manage_roles:  # type: ignore[union-attr]
            await interaction.response.send_message(
                "❌ You need **Manage Roles**.",
                ephemeral=True,
            )
            return
        from views.roles.role_menu_builder import RoleMenuBuilderView

        builder = RoleMenuBuilderView(self.ctx, parent=self)
        builder.message = self.message
        await interaction.response.edit_message(
            embed=builder.build_embed(),
            view=builder,
        )

    @discord.ui.button(label="✏️ Edit Menu", style=discord.ButtonStyle.blurple, row=0)
    async def edit_menu_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not interaction.user.guild_permissions.manage_roles:  # type: ignore[union-attr]
            await interaction.response.send_message(
                "❌ You need **Manage Roles**.",
                ephemeral=True,
            )
            return
        menus = await reaction_role_service.list_menus(self.ctx.guild.id)
        if not menus:
            await interaction.response.send_message(
                "No menus to edit yet — press **➕ New Menu**.",
                ephemeral=True,
            )
            return
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=_MenuEditPicker(self.ctx, self, menus),
        )

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.grey, row=1)
    async def refresh_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )


class _MenuEditPicker(BaseView):
    """Transient picker: choose which menu to load into the builder."""

    def __init__(
        self,
        ctx: commands.Context,
        parent: ReactionRolesPanel,
        menus: list[dict],
    ) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.parent = parent
        from views.paginated_select import attach_windowed_select

        options = [
            discord.SelectOption(
                label=f"#{m['menu_id']} {m['title']}"[:100],
                value=str(m["menu_id"]),
            )
            for m in menus
        ]
        attach_windowed_select(
            self,
            options,
            self._on_pick,
            placeholder="Pick a menu to edit…",
            select_row=0,
        )

        async def _build_parent(
            _interaction: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            return await parent.build_embed(), parent

        attach_back_button(
            self,
            label="↩ Back",
            custom_id="role:reaction:editpick:back",
            parent_builder=_build_parent,
            row=1,
        )

    def build_embed(self) -> discord.Embed:
        return discord.Embed(
            title="✏️ Edit a role menu",
            description="Pick the menu to load into the builder.",
            color=ROLE_COLOR,
        )

    async def _on_pick(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        from views.roles.role_menu_builder import RoleMenuBuilderView

        menu_id = int(values[0])
        menu = await reaction_role_service.get_menu(menu_id)
        if menu is None:
            await interaction.response.send_message(
                "That menu no longer exists.",
                ephemeral=True,
            )
            return
        options = await reaction_role_service.get_menu_options(menu_id)
        builder = RoleMenuBuilderView(
            self.ctx,
            parent=self.parent,
            menu=menu,
            options=options,
        )
        builder.message = self.parent.message
        await interaction.response.edit_message(
            embed=builder.build_embed(),
            view=builder,
        )
