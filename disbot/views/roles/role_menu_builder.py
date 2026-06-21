"""Operator builder for the modern role menus (reaction-roles overhaul PR 2).

Reached from the Reaction Roles panel (role hub). An admin composes a menu —
title/description, the roles it offers, button-vs-dropdown style, mode, the
per-member limit, an embed **theme** preset, optionally seeded from a **starter
template** — sees a live preview, then **Posts** it to a channel. Editing an
existing menu loads it back into the same builder and **edits the live message in
place** (no repost — plan §4.6a).

Every config write goes through :mod:`services.reaction_role_service` (audited);
the view holds only draft state and renders Discord components — no DB writes, no
cog imports (``docs/architecture.md`` layer rules). Authority (``manage_roles``)
is re-checked when the builder opens and again at Post/Save time
(``.claude/rules/discord-views.md``).
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import resources
from services import reaction_role_service as rr
from utils.role_menu_logic import MODES
from utils.role_menu_presets import all_templates, all_themes, resolve_theme
from utils.ui_constants import ROLE_COLOR
from views.base import BaseView
from views.paginated_select import attach_windowed_select
from views.roles.role_menu_view import render_role_menu

logger = logging.getLogger("bot.views.role_menu_builder")

_STYLES = ("dropdown", "button")
_MODE_LABELS = {"normal": "Normal", "unique": "Unique", "verify": "Verify"}
_MAX_MENU_ROLES = 25


def _can_manage(interaction: discord.Interaction) -> bool:
    perms = getattr(interaction.user, "guild_permissions", None)
    return bool(perms and perms.manage_roles)


def _assignable_roles(guild: discord.Guild) -> list[discord.Role]:
    """Roles the bot can hand out — not @everyone/managed, below the bot's top role."""
    me = guild.me
    top = me.top_role if me else None
    out = [
        r
        for r in guild.roles
        if not r.is_default() and not r.managed and (top is None or r < top)
    ]
    out.sort(key=lambda r: r.position, reverse=True)
    return out


class RoleMenuBuilderView(BaseView):
    """Compose / edit a role menu, then post or save it in place."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        parent: BaseView | None = None,
        menu: dict | None = None,
        options: list[dict] | None = None,
    ) -> None:
        super().__init__(ctx.author, timeout=600)
        self.ctx = ctx
        self.guild = ctx.guild
        self.parent = parent

        # Draft state — seeded from an existing menu when editing.
        self.menu_id: int | None = int(menu["menu_id"]) if menu else None
        self.message_id: int | None = (
            int(menu["message_id"]) if menu and menu.get("message_id") else None
        )
        self.title: str = (menu.get("title") if menu else None) or "Pick your roles"
        self.description: str | None = menu.get("description") if menu else None
        self.style: str = (menu.get("style") if menu else None) or "dropdown"
        self.mode: str = (menu.get("mode") if menu else None) or "normal"
        self.max_roles: int = int(menu.get("max_roles") or 0) if menu else 0
        self.theme: str = (menu.get("theme") if menu else None) or "default"
        self.channel_id: int = int(menu["channel_id"]) if menu else ctx.channel.id
        self.role_ids: list[int] = (
            [int(o["role_id"]) for o in (options or [])] if menu else []
        )
        self._rebuild()

    # -- preview ---------------------------------------------------------

    def _resolve_channel(self, channel_id: int) -> discord.abc.GuildChannel | None:
        if self.guild is None:
            return None
        return resources.resolve_channel(self.guild, channel_id=channel_id)

    @property
    def editing(self) -> bool:
        return self.menu_id is not None

    def build_embed(self) -> discord.Embed:
        theme = resolve_theme(self.theme)
        channel = self._resolve_channel(self.channel_id)
        roles = ", ".join(
            r.mention
            for r in (
                resources.resolve_role(self.guild, role_id=i) for i in self.role_ids
            )
            if r is not None
        )
        limit = "unlimited" if not self.max_roles else str(self.max_roles)
        embed = discord.Embed(
            title=f"🛠️ {'Edit' if self.editing else 'New'} Role Menu",
            description=(
                f"**Title** — {self.title}\n"
                f"**Description** — {self.description or '*(none)*'}\n"
                f"**Roles** — {roles or '*none yet — pick some below*'}\n"
                f"**Style** — {self.style}   ·   **Mode** — {_MODE_LABELS[self.mode]}"
                f"   ·   **Limit** — {limit}\n"
                f"**Theme** — {theme.name}   ·   "
                f"**Channel** — {channel.mention if channel else '*unknown*'}"
            ),
            color=ROLE_COLOR,
        )
        embed.set_footer(
            text="Pick roles + tune the options, then Post. Preview matches what members see.",
        )
        return embed

    # -- (re)build components -------------------------------------------

    def _rebuild(self) -> None:
        self.clear_items()
        # Row 0/1: the role multi-select (windowed past 25).
        roles = _assignable_roles(self.guild) if self.guild else []
        selected = set(self.role_ids)
        options = [
            discord.SelectOption(
                label=r.name[:100],
                value=str(r.id),
                default=r.id in selected,
            )
            for r in roles
        ]
        if options:
            attach_windowed_select(
                self,
                options,
                self._on_roles,
                placeholder="🎭 Pick the roles this menu offers…",
                min_values=0,
                max_values=min(_MAX_MENU_ROLES, len(options)),
                select_row=0,
                nav_row=1,
            )

        # Row 2: theme picker.
        theme_options = [
            discord.SelectOption(
                label=t.name,
                value=t.key,
                default=t.key == self.theme,
            )
            for t in all_themes()
        ]
        attach_windowed_select(
            self,
            theme_options,
            self._on_theme,
            placeholder=f"🎨 Theme: {resolve_theme(self.theme).name}",
            min_values=1,
            max_values=1,
            select_row=2,
        )

        # Row 3: text / template / channel / limit.
        self._add_button("✏️ Text", self._on_text, row=3)
        self._add_button("📋 Template", self._on_template, row=3)
        self._add_button("📍 Channel", self._on_channel, row=3)
        self._add_button("🔢 Limit", self._on_limit, row=3)

        # Row 4: style / mode / post-or-save / delete / close.
        self._add_button(
            f"🔀 Style: {self.style}",
            self._on_style,
            row=4,
            style=discord.ButtonStyle.blurple,
        )
        self._add_button(
            f"🔁 Mode: {_MODE_LABELS[self.mode]}",
            self._on_mode,
            row=4,
            style=discord.ButtonStyle.blurple,
        )
        self._add_button(
            "💾 Save" if self.editing else "✅ Post",
            self._on_post,
            row=4,
            style=discord.ButtonStyle.green,
        )
        if self.editing:
            self._add_button(
                "🗑️ Delete",
                self._on_delete,
                row=4,
                style=discord.ButtonStyle.red,
            )
        self._add_button(
            "✖️ Close",
            self._on_close,
            row=4,
            style=discord.ButtonStyle.grey,
        )

    def _add_button(
        self,
        label: str,
        callback,
        *,
        row: int,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
    ) -> None:
        btn: discord.ui.Button = discord.ui.Button(label=label, row=row, style=style)
        btn.callback = callback  # type: ignore[method-assign]
        self.add_item(btn)

    async def _render(self, interaction: discord.Interaction) -> None:
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _render_message(self) -> None:
        """Re-render onto the builder's own message (after an ephemeral sub-flow)."""
        self._rebuild()
        if self.message is not None:
            await self.message.edit(embed=self.build_embed(), view=self)

    # -- callbacks -------------------------------------------------------

    async def _on_roles(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        self.role_ids = [int(v) for v in values if v.isdigit()][:_MAX_MENU_ROLES]
        await self._render(interaction)

    async def _on_theme(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        if values:
            self.theme = values[0]
        await self._render(interaction)

    async def _on_style(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        self.style = _STYLES[(_STYLES.index(self.style) + 1) % len(_STYLES)]
        await self._render(interaction)

    async def _on_mode(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
        await self._render(interaction)

    async def _on_text(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(_TextModal(self))

    async def _on_limit(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(_LimitModal(self))

    async def _on_template(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        view = _PickerView(
            self.ctx.author,
            [
                discord.SelectOption(label=t.name[:100], value=t.key)
                for t in all_templates()
            ],
            self._apply_template,
            placeholder="Pick a starter template…",
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    async def _apply_template(
        self,
        interaction: discord.Interaction,
        key: str,
    ) -> None:
        from utils.role_menu_presets import resolve_template

        tpl = resolve_template(key)
        if tpl is not None:
            self.title = tpl.title
            self.description = tpl.description or None
            self.theme = tpl.theme
        await interaction.response.edit_message(
            content="✅ Template applied.",
            view=None,
        )
        await self._render_message()

    async def _on_channel(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        view = _ChannelPickerView(self.ctx.author, self._apply_channel)
        await interaction.response.send_message(
            "Pick the channel to post this menu in:",
            view=view,
            ephemeral=True,
        )

    async def _apply_channel(
        self,
        interaction: discord.Interaction,
        channel_id: int,
    ) -> None:
        self.channel_id = channel_id
        await interaction.response.edit_message(
            content="✅ Channel set.",
            view=None,
        )
        await self._render_message()

    async def _on_post(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await interaction.response.send_message(
                "❌ You need **Manage Roles**.",
                ephemeral=True,
            )
            return
        if not self.role_ids:
            await interaction.response.send_message(
                "❌ Add at least one role first.",
                ephemeral=True,
            )
            return
        channel = self._resolve_channel(self.channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ That channel can't host a menu — pick a text channel.",
                ephemeral=True,
            )
            return

        role_options = [
            {"role_id": rid, "position": pos} for pos, rid in enumerate(self.role_ids)
        ]
        actor_id = interaction.user.id

        if self.editing and self.menu_id is not None:
            await rr.update_menu(
                self.menu_id,
                self.guild.id,
                title=self.title,
                description=self.description,
                style=self.style,
                mode=self.mode,
                max_roles=self.max_roles,
                theme=self.theme,
                role_options=role_options,
                actor_id=actor_id,
            )
            await self._refresh_live_message(channel)
            await interaction.response.edit_message(
                content="💾 Menu saved.",
                embed=None,
                view=None,
            )
            return

        menu_id = await rr.create_menu(
            self.guild.id,
            channel.id,
            title=self.title,
            description=self.description,
            style=self.style,
            mode=self.mode,
            max_roles=self.max_roles,
            theme=self.theme,
            role_options=role_options,
            actor_id=actor_id,
        )
        menu = await rr.get_menu(menu_id)
        options = await rr.get_menu_options(menu_id)
        embed, view = render_role_menu(menu, options, self.guild)
        posted = await channel.send(embed=embed, view=view)
        await rr.set_menu_message(menu_id, posted.id)
        await interaction.response.edit_message(
            content=f"✅ Posted to {channel.mention}.",
            embed=None,
            view=None,
        )

    async def _refresh_live_message(self, channel: discord.TextChannel) -> None:
        """Edit the menu's posted message in place after a save (plan §4.6a)."""
        if not self.message_id or self.menu_id is None:
            return
        menu = await rr.get_menu(self.menu_id)
        options = await rr.get_menu_options(self.menu_id)
        if menu is None:
            return
        embed, view = render_role_menu(menu, options, self.guild)
        try:
            message = await channel.fetch_message(self.message_id)
            await message.edit(embed=embed, view=view)
        except discord.HTTPException:
            logger.warning(
                "Could not edit live role-menu message %s",
                self.message_id,
            )

    async def _on_delete(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction) or self.menu_id is None:
            await interaction.response.send_message(
                "❌ You need **Manage Roles**.",
                ephemeral=True,
            )
            return
        menu = await rr.get_menu(self.menu_id)
        await rr.delete_menu(self.menu_id, self.guild.id, actor_id=interaction.user.id)
        if menu and menu.get("message_id"):
            channel = self._resolve_channel(int(menu["channel_id"]))
            if isinstance(channel, discord.TextChannel):
                try:
                    message = await channel.fetch_message(int(menu["message_id"]))
                    await message.delete()
                except discord.HTTPException:
                    pass
        await interaction.response.edit_message(
            content="🗑️ Menu deleted.",
            embed=None,
            view=None,
        )

    async def _on_close(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if self.parent is not None:
            embed = self.parent.build_embed()
            if hasattr(embed, "__await__"):  # async builder
                embed = await embed  # type: ignore[misc]
            await interaction.response.edit_message(embed=embed, view=self.parent)
        else:
            await interaction.response.edit_message(
                content="Closed.",
                embed=None,
                view=None,
            )


# ---------------------------------------------------------------------------
# Modals + ephemeral sub-pickers
# ---------------------------------------------------------------------------


class _TextModal(discord.ui.Modal, title="Menu title & description"):
    def __init__(self, builder: RoleMenuBuilderView) -> None:
        super().__init__()
        self._builder = builder
        self.title_in: discord.ui.TextInput = discord.ui.TextInput(
            label="Title",
            default=builder.title,
            max_length=100,
            required=True,
        )
        self.desc_in: discord.ui.TextInput = discord.ui.TextInput(
            label="Description",
            default=builder.description or "",
            style=discord.TextStyle.paragraph,
            max_length=2000,
            required=False,
        )
        self.add_item(self.title_in)
        self.add_item(self.desc_in)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self._builder.title = self.title_in.value.strip() or "Pick your roles"
        self._builder.description = self.desc_in.value.strip() or None
        await self._builder._render(interaction)


class _LimitModal(discord.ui.Modal, title="Per-member role limit"):
    def __init__(self, builder: RoleMenuBuilderView) -> None:
        super().__init__()
        self._builder = builder
        self.limit_in: discord.ui.TextInput = discord.ui.TextInput(
            label="Max roles a member can pick (0 = unlimited)",
            default=str(builder.max_roles),
            max_length=2,
            required=True,
        )
        self.add_item(self.limit_in)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            value = max(0, min(_MAX_MENU_ROLES, int(self.limit_in.value.strip())))
        except ValueError:
            await interaction.response.send_message(
                "❌ Enter a whole number (0 = unlimited).",
                ephemeral=True,
            )
            return
        self._builder.max_roles = value
        await self._builder._render(interaction)


class _PickerView(BaseView):
    """A small ephemeral single-select that calls back with the chosen value."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        options: list[discord.SelectOption],
        on_pick,
        *,
        placeholder: str,
    ) -> None:
        super().__init__(author, timeout=180)
        self._on_pick = on_pick

        async def _dispatch(
            interaction: discord.Interaction,
            values: list[str],
        ) -> None:
            await on_pick(interaction, values[0] if values else "")

        attach_windowed_select(
            self,
            options,
            _dispatch,
            placeholder=placeholder,
            select_row=0,
        )


class _ChannelPickerView(BaseView):
    """Ephemeral text-channel picker that calls back with the channel id."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        on_pick,
    ) -> None:
        super().__init__(author, timeout=180)
        self._on_pick = on_pick
        select: discord.ui.ChannelSelect = discord.ui.ChannelSelect(
            channel_types=[discord.ChannelType.text],
            placeholder="Pick a text channel…",
        )
        select.callback = self._selected  # type: ignore[method-assign]
        self.add_item(select)
        self._select = select

    async def _selected(self, interaction: discord.Interaction) -> None:
        values = self._select.values
        if values:
            await self._on_pick(interaction, values[0].id)


__all__ = ["RoleMenuBuilderView"]
