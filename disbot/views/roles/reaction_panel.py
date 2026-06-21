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
from utils.emoji_tokens import parse_emotes
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
                "Tap **➕ Add** to bind one or more emojis on a message — each to "
                "its own role — or **🛠️ Role Menus** for the modern "
                "button/dropdown surface (no reactions needed)."
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
# Sub-flow: add bindings (message-id + emoji modal → per-emote role pickers)
# ---------------------------------------------------------------------------
# One message can carry many emotes, each mapped to its OWN role (owner
# direction, 2026-06-21). The operator types one or more emotes; the flow then
# walks each emote in turn, picking its role, so 💀→A, ❤️→B, 😘→C bind in a
# single pass instead of one tediously-repeated single-emote add.


class _AddBindingModal(discord.ui.Modal, title="Add reaction role"):  # type: ignore[call-arg]
    message_id_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Message ID",
        placeholder="Right-click a message → Copy Message ID",
        max_length=25,
    )
    emoji_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Emoji(s)",
        placeholder="🎮  or  💀 ❤️ 😘  — one or more (each gets its own role)",
        max_length=200,
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
        emotes = parse_emotes(self.emoji_in.value)
        if not emotes:
            await interaction.response.send_message(
                "❌ Enter at least one emoji.",
                ephemeral=True,
            )
            return
        view = _BindEmotesView(self.panel, message_id, emotes)
        await interaction.response.send_message(
            content=view.prompt(),
            view=view,
            ephemeral=True,
        )


class _MoreEmotesModal(discord.ui.Modal, title="Add more emotes"):  # type: ignore[call-arg]
    """Bind further emotes to the SAME message without re-typing its ID."""

    emoji_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Emoji(s)",
        placeholder="💀 ❤️ 😘  — one or more (each gets its own role)",
        max_length=200,
    )

    def __init__(self, panel: ReactionRolesPanel, message_id: int) -> None:
        super().__init__()
        self.panel = panel
        self.message_id = message_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        emotes = parse_emotes(self.emoji_in.value)
        if not emotes:
            await interaction.response.send_message(
                "❌ Enter at least one emoji.",
                ephemeral=True,
            )
            return
        view = _BindEmotesView(self.panel, self.message_id, emotes)
        await interaction.response.send_message(
            content=view.prompt(),
            view=view,
            ephemeral=True,
        )


class _BindEmotesView(BaseView):
    """Walks each typed emote, picking and committing its own role binding."""

    def __init__(
        self,
        panel: ReactionRolesPanel,
        message_id: int,
        emotes: list[str],
    ) -> None:
        super().__init__(panel.ctx.author, timeout=300)
        self.panel = panel
        self.message_id = message_id
        self.emotes = emotes
        self.index = 0
        self.bound: list[tuple[str, str]] = []
        self._attach_picker()

    @property
    def _current(self) -> str:
        return self.emotes[self.index]

    def prompt(self) -> str:
        return (
            f"Pick the role for {self._current} "
            f"({self.index + 1}/{len(self.emotes)}) on message `{self.message_id}`:"
        )

    def _attach_picker(self) -> None:
        self.clear_items()
        attach_role_select(
            self,
            self.panel.ctx.guild.roles,
            self._on_pick,
            placeholder=f"Role for {self._current}…",
        )

    async def _on_pick(
        self,
        interaction: discord.Interaction,
        role_id: int,
    ) -> None:
        from services import reaction_role_service

        emote = self._current
        await reaction_role_service.bind_emoji(
            self.panel.ctx.guild.id,
            self.message_id,
            emote,
            role_id,
            actor_id=interaction.user.id,
        )
        role = resources.resolve_role(self.panel.ctx.guild, role_id=role_id)
        self.bound.append((emote, role.name if role else f"role {role_id}"))
        self.index += 1
        if self.index < len(self.emotes):
            self._attach_picker()
            await interaction.response.edit_message(content=self.prompt(), view=self)
            return
        await self._finish(interaction)

    async def _finish(self, interaction: discord.Interaction) -> None:
        pairs = ", ".join(f"{e} → **{r}**" for e, r in self.bound)
        # Respond fast (the reaction adds below are HTTP calls), then revise the
        # message only if some reaction couldn't be added.
        await interaction.response.edit_message(
            content=f"✅ Bound {pairs}.",
            view=_AfterBindView(self.panel, self.message_id),
        )
        note = await self._add_reactions(interaction)
        if note:
            await interaction.edit_original_response(
                content=f"✅ Bound {pairs}.{note}",
                view=_AfterBindView(self.panel, self.message_id),
            )
        await self.panel._rerender()

    async def _add_reactions(self, interaction: discord.Interaction) -> str:
        """Best-effort: seed each bound emote on the target message."""
        channel = interaction.channel
        if not isinstance(channel, discord.abc.Messageable):
            return ""
        try:
            message = await channel.fetch_message(self.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return (
                "\n*(I couldn't reach that message to add the reactions — add them "
                "yourself, or members can react.)*"
            )
        failed: list[str] = []
        for emote, _ in self.bound:
            try:
                await message.add_reaction(emote)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                failed.append(emote)
        if failed:
            return (
                "\n*(I couldn't add "
                + " ".join(failed)
                + " automatically — add them to the message, or members can react.)*"
            )
        return ""


class _AfterBindView(BaseView):
    """Post-bind toast offering a one-tap path to bind more emotes here."""

    def __init__(self, panel: ReactionRolesPanel, message_id: int) -> None:
        super().__init__(panel.ctx.author, timeout=300)
        self.panel = panel
        self.message_id = message_id

    @discord.ui.button(label="➕ Add more emotes", style=discord.ButtonStyle.green)
    async def more_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        await interaction.response.send_modal(
            _MoreEmotesModal(self.panel, self.message_id),
        )
