"""Interactive reaction-role panel (overhaul PR 3).

Converts the old read-only ``ReactionRolesPanel`` (display + refresh only) into a
full add / remove / mode editor for the **legacy emoji** surface, closing the
``ui-view-adoption-audit`` P1 "hand-rolled, display-only" finding. Every write
routes through the audited :mod:`services.reaction_role_service` (no DB writes in
views, per ``docs/architecture.md``); authority (``manage_roles``) is re-checked at
callback time (``.claude/rules/discord-views.md``).

The modern button/dropdown **role menus** keep their own builder (the 🛠️ Role
Menus entry → ``role_menu_builder``); this panel owns the emoji bindings + Carl's
per-message modes (normal / unique / verify).
"""

from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from utils.ui_constants import ROLE_COLOR
from views.base import BaseView
from views.navigation import attach_back_button
from views.paginated_select import PaginatedSelectView
from views.selectors import attach_role_select

_MODE_LABEL = {
    "normal": "Normal — react adds, un-react removes",
    "unique": "Unique — one role per message (swaps)",
    "verify": "Verify — add-only, reaction removed",
}


def _can_manage(interaction: discord.Interaction) -> bool:
    perms = getattr(interaction.user, "guild_permissions", None)
    return bool(perms is not None and (perms.manage_roles or perms.administrator))


async def _deny(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        "You need the **Manage Roles** permission to do that.",
        ephemeral=True,
    )


class ReactionRolesPanel(BaseView):
    """Add / remove / mode editor for a guild's emoji reaction-role bindings."""

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
                row=2,
            )

    # -- presentation -------------------------------------------------------

    async def build_embed(self) -> discord.Embed:
        from services import reaction_role_service

        rows = await reaction_role_service.list_bindings(self.ctx.guild.id)
        modes = await reaction_role_service.list_message_modes(self.ctx.guild.id)
        menus = await reaction_role_service.list_menus(self.ctx.guild.id)

        embed = discord.Embed(title="💬 Reaction Roles", color=ROLE_COLOR)
        if rows:
            lines = []
            for r in rows:
                role = resources.resolve_role(self.ctx.guild, role_id=r["role_id"])
                role_str = role.mention if role else f"*(deleted role {r['role_id']})*"
                lines.append(f"`{r['message_id']}` · {r['emoji']} → {role_str}")
            embed.description = "\n".join(lines)[:4096]
        else:
            embed.description = (
                "No emoji reaction roles yet.\n\n"
                "Tap **➕ Add** to bind an emoji on a message to a role — or "
                "**🛠️ Role Menus** for the modern button/dropdown surface (no "
                "reactions needed)."
            )
        if modes:
            embed.add_field(
                name="⚙️ Message modes",
                value="\n".join(f"`{mid}` → **{mode}**" for mid, mode in modes.items())[
                    :1024
                ],
                inline=False,
            )
        embed.add_field(
            name="🛠️ Role menus",
            value=(
                f"{len(menus)} button/dropdown menu(s) configured."
                if menus
                else "None yet — tap **🛠️ Role Menus** to build one."
            ),
            inline=False,
        )
        embed.set_footer(text="One tap to self-assign; modes mirror Carl-bot.")
        return embed

    async def _rerender(self) -> None:
        if self.message:
            await self.message.edit(embed=await self.build_embed(), view=self)

    # -- add / remove emoji bindings ---------------------------------------

    @discord.ui.button(label="➕ Add", style=discord.ButtonStyle.green, row=0)
    async def add_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        await interaction.response.send_modal(_AddBindingModal(self))

    @discord.ui.button(label="🗑️ Remove", style=discord.ButtonStyle.red, row=0)
    async def remove_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        from services import reaction_role_service

        rows = await reaction_role_service.list_bindings(self.ctx.guild.id)
        if not rows:
            await interaction.response.send_message(
                "There are no bindings to remove.",
                ephemeral=True,
            )
            return
        options = []
        for r in rows:
            role = resources.resolve_role(self.ctx.guild, role_id=r["role_id"])
            rname = role.name if role else f"role {r['role_id']}"
            options.append(
                discord.SelectOption(
                    label=f"{r['emoji']} → {rname}"[:100],
                    value=f"{r['message_id']}:{r['emoji']}",
                    description=f"message {r['message_id']}"[:100],
                ),
            )
        await interaction.response.send_message(
            "Pick a binding to remove:",
            view=PaginatedSelectView(
                interaction.user,
                options,
                self._do_remove,
                placeholder="Choose a binding…",
            ),
            ephemeral=True,
        )

    async def _do_remove(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        from services import reaction_role_service

        message_id_str, emoji = values[0].split(":", 1)
        await reaction_role_service.unbind_emoji(
            self.ctx.guild.id,
            int(message_id_str),
            emoji,
            actor_id=interaction.user.id,
        )
        await interaction.response.edit_message(
            content="🗑️ Binding removed.",
            view=None,
        )
        await self._rerender()

    # -- per-message mode (normal / unique / verify) -----------------------

    @discord.ui.button(label="⚙️ Mode", style=discord.ButtonStyle.blurple, row=0)
    async def mode_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        from services import reaction_role_service

        rows = await reaction_role_service.list_bindings(self.ctx.guild.id)
        message_ids = sorted({int(r["message_id"]) for r in rows})
        if not message_ids:
            await interaction.response.send_message(
                "Add a binding first — modes apply to a message with reaction roles.",
                ephemeral=True,
            )
            return
        modes = await reaction_role_service.list_message_modes(self.ctx.guild.id)
        options = [
            discord.SelectOption(
                label=f"message {mid}"[:100],
                value=str(mid),
                description=f"current: {modes.get(mid, 'normal')}"[:100],
            )
            for mid in message_ids
        ]
        await interaction.response.send_message(
            "Pick a message to set its mode:",
            view=PaginatedSelectView(
                interaction.user,
                options,
                self._pick_mode,
                placeholder="Choose a message…",
            ),
            ephemeral=True,
        )

    async def _pick_mode(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        message_id = int(values[0])
        options = [
            discord.SelectOption(label=_MODE_LABEL[m], value=f"{message_id}:{m}")
            for m in ("normal", "unique", "verify")
        ]
        await interaction.response.edit_message(
            content=f"How should reactions behave on message `{message_id}`?",
            view=PaginatedSelectView(
                interaction.user,
                options,
                self._apply_mode,
                placeholder="Mode…",
            ),
        )

    async def _apply_mode(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        from services import reaction_role_service

        message_id_str, mode = values[0].split(":", 1)
        await reaction_role_service.set_message_mode(
            guild_id=self.ctx.guild.id,
            message_id=int(message_id_str),
            mode=mode,
            actor_id=interaction.user.id,
        )
        await interaction.response.edit_message(
            content=f"⚙️ Mode set to **{mode}**.",
            view=None,
        )
        await self._rerender()

    # -- modern menus + refresh --------------------------------------------

    @discord.ui.button(label="🛠️ Role Menus", style=discord.ButtonStyle.grey, row=1)
    async def menus_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.roles.role_menu_builder import RoleMenuListView

        view = RoleMenuListView(
            interaction.user,
            interaction.guild,
            interaction.channel,
            parent=self,
        )
        await interaction.response.edit_message(
            embed=await view.build_embed(),
            view=view,
        )
        view.message = interaction.message

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


# ---------------------------------------------------------------------------
# Sub-flow: add a binding (message-id + emoji modal → role picker)
# ---------------------------------------------------------------------------


class _AddBindingModal(discord.ui.Modal, title="Add reaction role"):  # type: ignore[call-arg]
    message_id_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Message ID",
        placeholder="Right-click a message → Copy Message ID",
        max_length=25,
    )
    emoji_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Emoji",
        placeholder="🎮 (or a custom emoji)",
        max_length=64,
    )

    def __init__(self, panel: ReactionRolesPanel) -> None:
        super().__init__()
        self.panel = panel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = self.message_id_in.value.strip()
        try:
            message_id = int(raw)
        except ValueError:
            await interaction.response.send_message(
                "❌ The message ID must be a number.",
                ephemeral=True,
            )
            return
        emoji = self.emoji_in.value.strip()
        await interaction.response.send_message(
            f"Pick the role to assign for {emoji} on message `{message_id}`:",
            view=_BindRolePickView(self.panel, message_id, emoji),
            ephemeral=True,
        )


class _BindRolePickView(BaseView):
    """Ephemeral single-role picker that commits a new emoji binding."""

    def __init__(
        self,
        panel: ReactionRolesPanel,
        message_id: int,
        emoji: str,
    ) -> None:
        super().__init__(panel.ctx.author, timeout=180)
        self.panel = panel
        self.message_id = message_id
        self.emoji = emoji
        attach_role_select(self, panel.ctx.guild.roles, self._on_pick)

    async def _on_pick(
        self,
        interaction: discord.Interaction,
        role_id: int,
    ) -> None:
        from services import reaction_role_service

        await reaction_role_service.bind_emoji(
            self.panel.ctx.guild.id,
            self.message_id,
            self.emoji,
            role_id,
            actor_id=interaction.user.id,
        )
        # Best-effort: add the emoji to the target message so members have
        # something to click. The message is usually in the current channel; if
        # it isn't reachable, the binding still stands.
        note = ""
        channel = interaction.channel
        if isinstance(channel, discord.abc.Messageable):
            try:
                message = await channel.fetch_message(self.message_id)
                await message.add_reaction(self.emoji)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                note = (
                    "\n*(I couldn't add the reaction automatically — add "
                    f"{self.emoji} to the message, or members can react themselves.)*"
                )
        role = resources.resolve_role(self.panel.ctx.guild, role_id=role_id)
        rname = role.name if role else f"role {role_id}"
        await interaction.response.edit_message(
            content=f"✅ Bound {self.emoji} → **{rname}**.{note}",
            view=None,
        )
        await self.panel._rerender()
