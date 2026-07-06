"""Operator-facing role-menu builder + manager (plan §4 PR 2, §4.6 a/b/c).

Reached from the Reaction Roles panel. ``RoleMenuListView`` is the manager (list /
new / edit / delete); ``RoleMenuBuilder`` is the build-or-edit panel. Discord's
5-row / 25-option limits forbid one giant form, so the builder is a compact preview
panel whose fields are set through modals + ephemeral sub-pickers, then **Post**
(new) or **Save** (edit-in-place — §4.6a) commits through the audited
:mod:`services.reaction_role_service`.

Layer: a thin UI over the service — no DB writes here, no role math. Authority is
re-checked at callback time (``manage_roles``), per ``.claude/rules/discord-views.md``.
"""

from __future__ import annotations

import logging

import discord

from core.runtime import resources
from core.runtime.interaction_helpers import safe_defer, safe_edit
from core.runtime.permission_checks import member_has_perms_or_owner
from utils import role_feasibility
from utils import role_menu_presentation as presentation
from views.base import BaseView
from views.navigation import attach_back_button
from views.paginated_select import PaginatedSelectView
from views.roles._helpers import _COLOR_OPTIONS, _parse_color
from views.roles.role_menu_view import (
    MAX_MENU_ROLES,
    RoleMenuView,
    build_menu_message,
)
from views.selectors import (
    attach_channel_select,
    attach_multi_role_select,
    attach_multi_select,
)

logger = logging.getLogger("bot.views.role_menu_builder")

_STYLE_LABEL = {"dropdown": "Dropdown", "button": "Buttons"}
_MODE_LABEL = {
    "normal": "Normal — pick any",
    "unique": "Unique — one only",
    "verify": "Verify — add-only",
}


def _can_manage(interaction: discord.Interaction) -> bool:
    # Owner OR manage_roles (admins implicitly hold manage_roles). Q-0212.
    return member_has_perms_or_owner(interaction.user, manage_roles=True)


async def _deny(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        "You need the **Manage Roles** permission to do that.",
        ephemeral=True,
    )


# A guild channel a menu can be posted in — all have ``.send`` / ``.mention`` /
# ``.id`` (narrower than ``MessageableChannel``, which also covers DM/group).
_GuildMessageable = (
    discord.TextChannel | discord.Thread | discord.VoiceChannel | discord.StageChannel
)


def _as_messageable(channel: object) -> _GuildMessageable | None:
    """Narrow an interaction/guild channel to a postable guild channel, or None."""
    if isinstance(
        channel,
        (
            discord.TextChannel,
            discord.Thread,
            discord.VoiceChannel,
            discord.StageChannel,
        ),
    ):
        return channel
    return None


def _option_dicts(options: list) -> list[dict]:  # type: ignore[type-arg]
    """Convert service ``RoleOption`` rows → the dicts the view/embed read."""
    return [{"role_id": o.role_id, "emoji": o.emoji, "label": o.label} for o in options]


# ---------------------------------------------------------------------------
# Manager — list / new / edit / delete
# ---------------------------------------------------------------------------


class RoleMenuListView(BaseView):
    """Lists a guild's role menus with New / Edit / Delete entry points."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild: discord.Guild,
        channel: discord.abc.MessageableChannel,
        parent: BaseView | None = None,
    ) -> None:
        super().__init__(author, timeout=300)
        self.guild = guild
        self.channel = channel
        self.parent = parent
        # See RoleMenuBuilder._panel_interaction — the manager list is on the same
        # ephemeral message, so its refresh must route through the interaction too.
        self._panel_interaction: discord.Interaction | None = None
        if parent is not None:

            async def _build_parent(
                _interaction: discord.Interaction,
            ) -> tuple[discord.Embed, discord.ui.View]:
                return await parent.build_embed(), parent  # type: ignore[attr-defined]

            attach_back_button(
                self,
                label="↩ Back",
                custom_id="role:menus:back",
                parent_builder=_build_parent,
                row=1,
            )

    async def build_embed(self) -> discord.Embed:
        from services import reaction_role_service

        menus = await reaction_role_service.list_menus(self.guild.id)
        embed = discord.Embed(
            title="🛠️ Role Menus",
            color=presentation.theme_color(None),
        )
        if menus:
            lines = []
            for m in menus:
                opts = await reaction_role_service.get_menu_options(int(m["menu_id"]))
                posted = "📌 posted" if m.get("message_id") else "📝 draft"
                lines.append(
                    f"**{m['title']}** — {_STYLE_LABEL.get(m['style'], m['style'])}"
                    f" · {m['mode']} · {len(opts)} role(s) · {posted}",
                )
            embed.description = "\n".join(lines)
        else:
            embed.description = (
                "No role menus yet.\n\n"
                "Tap **➕ New Menu** to build a button/dropdown self-role menu — the "
                "modern alternative to emoji reaction roles."
            )
        embed.set_footer(text="Members self-assign with one tap; no reactions needed.")
        return embed

    async def _rerender(self) -> None:
        if self._panel_interaction is not None and await safe_edit(
            self._panel_interaction,
            embed=await self.build_embed(),
            view=self,
        ):
            return
        if self.message is not None:
            await self.message.edit(embed=await self.build_embed(), view=self)

    @discord.ui.button(label="➕ New Menu", style=discord.ButtonStyle.green, row=0)
    async def new_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        channel = _as_messageable(interaction.channel)
        if channel is None:
            await interaction.response.send_message(
                "Open this in a server text channel so the menu can be posted there.",
                ephemeral=True,
            )
            return
        builder = RoleMenuBuilder(
            interaction.user,
            self.guild,
            channel,
            parent=self,
        )
        await interaction.response.edit_message(
            embed=builder.build_embed(),
            view=builder,
        )
        builder.message = interaction.message
        builder._panel_interaction = interaction

    @discord.ui.button(label="✏️ Edit", style=discord.ButtonStyle.blurple, row=0)
    async def edit_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        await self._pick_menu(interaction, self._open_editor, "Pick a menu to edit:")

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.red, row=0)
    async def delete_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        await self._pick_menu(interaction, self._delete_menu, "Pick a menu to delete:")

    @discord.ui.button(label="📤 Repost", style=discord.ButtonStyle.grey, row=1)
    async def repost_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        await self._pick_menu(
            interaction,
            self._repost_menu,
            "Pick a menu to repost (re-sends it; recovers a deleted message):",
        )

    @discord.ui.button(label="📋 Duplicate", style=discord.ButtonStyle.grey, row=1)
    async def duplicate_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        await self._pick_menu(
            interaction,
            self._duplicate_menu,
            "Pick a menu to duplicate into a new one:",
        )

    async def _pick_menu(self, interaction, on_pick, prompt: str) -> None:  # type: ignore[no-untyped-def]
        from services import reaction_role_service

        menus = await reaction_role_service.list_menus(self.guild.id)
        if not menus:
            await interaction.response.send_message(
                "There are no menus yet.",
                ephemeral=True,
            )
            return
        options = [
            discord.SelectOption(
                label=m["title"][:100],
                value=str(m["menu_id"]),
                description=f"{m['style']} · {m['mode']}"[:100],
            )
            for m in menus
        ]
        await interaction.response.send_message(
            prompt,
            view=PaginatedSelectView(
                interaction.user,
                options,
                on_pick,
                placeholder="Choose a menu…",
            ),
            ephemeral=True,
        )

    async def _open_editor(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        from services import reaction_role_service

        menu_id = int(values[0])
        menu = await reaction_role_service.get_menu(menu_id)
        if menu is None:
            await interaction.response.send_message(
                "That menu no longer exists.",
                ephemeral=True,
            )
            return
        opts = await reaction_role_service.get_menu_options(menu_id)
        builder = RoleMenuBuilder.from_menu(
            interaction.user,
            self.guild,
            menu,
            opts,
            parent=self,
        )
        builder._panel_interaction = interaction
        await interaction.response.edit_message(
            embed=builder.build_embed(),
            view=builder,
        )
        builder.message = interaction.message

    async def _delete_menu(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        from services import reaction_role_service

        menu_id = int(values[0])
        menu = await reaction_role_service.get_menu(menu_id)
        await reaction_role_service.delete_menu(
            menu_id=menu_id,
            guild_id=self.guild.id,
            actor_id=interaction.user.id,
        )
        # Best-effort: remove the posted menu message too.
        if menu and menu.get("message_id") and menu.get("channel_id"):
            channel = resources.resolve_channel(
                self.guild,
                channel_id=int(menu["channel_id"]),
            )
            if isinstance(channel, discord.abc.Messageable):
                try:
                    message = await channel.fetch_message(int(menu["message_id"]))
                    await message.delete()
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass
        await interaction.response.edit_message(
            content="🗑️ Menu deleted.",
            view=None,
        )
        await self._rerender()

    async def _repost_menu(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        """Re-send a saved menu, binding a fresh persistent view to the new message.

        Reuses the stored config as-is — recovers a menu whose message was
        deleted, or relocates it. Posts to the menu's own channel when it still
        exists, otherwise to the channel this manager is open in; the old message
        (if any) is best-effort removed so it doesn't linger as a dead duplicate.
        """
        from services import reaction_role_service

        menu_id = int(values[0])
        menu = await reaction_role_service.get_menu(menu_id)
        if menu is None:
            await interaction.response.edit_message(
                content="That menu no longer exists.",
                view=None,
            )
            return
        target = _as_messageable(
            resources.resolve_channel(self.guild, channel_id=int(menu["channel_id"])),
        ) or _as_messageable(self.channel)
        if target is None:
            await interaction.response.edit_message(
                content="I can't find a channel to repost this menu in.",
                view=None,
            )
            return

        await interaction.response.edit_message(content="📤 Reposting…", view=None)
        opt_dicts = _option_dicts(await reaction_role_service.get_menu_options(menu_id))
        view = RoleMenuView(menu, opt_dicts)

        await self._delete_old_message(menu)
        embed, files = build_menu_message(menu, opt_dicts, self.guild)
        try:
            message = await target.send(embed=embed, view=view, files=files)
        except discord.Forbidden:
            await interaction.followup.send(
                "I couldn't repost the menu — I lack permission to send messages "
                f"in {target.mention}.",
                ephemeral=True,
            )
            return
        await reaction_role_service.set_menu_location(menu_id, target.id, message.id)
        interaction.client.add_view(view, message_id=message.id)
        await interaction.followup.send(
            f"🚀 Reposted **{menu['title']}** to {target.mention}.",
            ephemeral=True,
        )
        await self._rerender()

    async def _duplicate_menu(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        """Open the builder pre-filled with a copy of an existing menu.

        The copy carries no ``menu_id``, so the builder's **Post** creates a new,
        independent menu (targeting the channel this manager is open in) — the
        original is untouched.
        """
        from services import reaction_role_service

        menu_id = int(values[0])
        menu = await reaction_role_service.get_menu(menu_id)
        if menu is None:
            await interaction.response.edit_message(
                content="That menu no longer exists.",
                view=None,
            )
            return
        opts = await reaction_role_service.get_menu_options(menu_id)
        builder = RoleMenuBuilder.from_menu(
            interaction.user,
            self.guild,
            menu,
            opts,
            parent=self,
            as_copy=True,
            channel=_as_messageable(self.channel),
        )
        builder._panel_interaction = interaction
        await interaction.response.edit_message(
            embed=builder.build_embed(),
            view=builder,
        )
        builder.message = interaction.message

    async def _delete_old_message(self, menu: dict) -> None:
        """Best-effort: remove a menu's previous posted message before a repost."""
        if not (menu.get("message_id") and menu.get("channel_id")):
            return
        channel = resources.resolve_channel(
            self.guild,
            channel_id=int(menu["channel_id"]),
        )
        if isinstance(channel, discord.abc.Messageable):
            try:
                message = await channel.fetch_message(int(menu["message_id"]))
                await message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass


# ---------------------------------------------------------------------------
# Builder — build a new menu or edit an existing one in place
# ---------------------------------------------------------------------------


class RoleMenuBuilder(BaseView):
    """Compact preview panel for building / editing one role menu."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild: discord.Guild,
        channel: _GuildMessageable | None,
        *,
        parent: BaseView | None = None,
        menu_id: int | None = None,
    ) -> None:
        super().__init__(author, timeout=600)
        self.guild = guild
        self.channel = channel
        self.parent = parent
        self.menu_id = menu_id
        # The interaction that owns the (ephemeral) panel message. Ephemeral
        # messages can't be edited via Message.edit() — only through the
        # interaction/webhook token — so every live preview refresh routes
        # through this via safe_edit(). Set at open + refreshed by each direct
        # panel interaction (toggles/modals); sub-flows reuse the stored token.
        self._panel_interaction: discord.Interaction | None = None
        # Draft state (dropdown default per owner decision §9 #2).
        self.title = "Pick your roles"
        self.description: str | None = None
        self.style = "dropdown"
        self.mode = "normal"
        self.max_roles = 0
        self.theme = presentation.DEFAULT_THEME_KEY
        self.template: str | None = None
        self.card_template: str | None = None
        self.card_text: str | None = None
        self.show_counts = False
        self.role_ids: list[int] = []

        if parent is not None:

            async def _build_parent(
                _interaction: discord.Interaction,
            ) -> tuple[discord.Embed, discord.ui.View]:
                return await parent.build_embed(), parent  # type: ignore[attr-defined]

            attach_back_button(
                self,
                label="↩ Back",
                custom_id="role:builder:back",
                parent_builder=_build_parent,
                row=1,
            )

    @classmethod
    def from_menu(
        cls,
        author: discord.Member | discord.User,
        guild: discord.Guild,
        menu: dict,
        options: list,  # type: ignore[type-arg]
        parent: BaseView | None = None,
        *,
        as_copy: bool = False,
        channel: _GuildMessageable | None = None,
    ) -> RoleMenuBuilder:
        """Load an existing menu's state into a fresh builder.

        ``as_copy=False`` (default) loads the menu for **edit-in-place** — the
        builder keeps the menu's id so Save updates it. ``as_copy=True`` loads it
        as a **duplicate**: the id is dropped so the builder's Post creates a new
        menu, and (unless ``channel`` is given) it targets the menu's own channel.
        """
        target = channel or _as_messageable(
            resources.resolve_channel(guild, channel_id=int(menu["channel_id"])),
        )
        builder = cls(
            author,
            guild,
            target,
            parent=parent,
            menu_id=(None if as_copy else int(menu["menu_id"])),
        )
        builder.title = (f"{menu['title']} (copy)"[:100]) if as_copy else menu["title"]
        builder.description = menu.get("description")
        builder.style = menu.get("style", "dropdown")
        builder.mode = menu.get("mode", "normal")
        builder.max_roles = int(menu.get("max_roles") or 0)
        builder.theme = menu.get("theme") or presentation.DEFAULT_THEME_KEY
        builder.template = menu.get("template")
        builder.card_template = menu.get("card_template")
        builder.card_text = menu.get("card_text")
        builder.show_counts = bool(menu.get("show_counts"))
        builder.role_ids = [o.role_id for o in options]
        return builder

    # -- preview ------------------------------------------------------------

    def build_embed(self) -> discord.Embed:
        theme = presentation.get_theme(self.theme)
        verb = "Editing" if self.menu_id else "Building"
        embed = discord.Embed(
            title=f"🛠️ {verb}: {self.title}",
            description=self.description or "*(no description)*",
            color=theme.color,
        )
        if self.role_ids:
            names = []
            for rid in self.role_ids:
                role = resources.resolve_role(self.guild, role_id=rid)
                names.append(role.mention if role else f"*(deleted {rid})*")
            embed.add_field(name="Roles", value=", ".join(names), inline=False)
        else:
            embed.add_field(
                name="Roles",
                value="*none yet — tap 🏷️ Roles*",
                inline=False,
            )
        from services.reaction_role_service import supports_role_gradients

        limit = "unlimited" if not self.max_roles else str(self.max_roles)
        channel_str = (
            self.channel.mention if self.channel is not None else "*(current channel)*"
        )
        gradient_note = (
            "\n✨ Enhanced role styles available — gradient/holographic colour roles."
            if supports_role_gradients(self.guild)
            else ""
        )
        card = presentation.get_card_template(self.card_template)
        card_str = card.label if card else "none"
        counts_str = "on" if self.show_counts else "off"
        embed.add_field(
            name="Settings",
            value=(
                f"Style: **{_STYLE_LABEL.get(self.style, self.style)}**\n"
                f"Mode: **{_MODE_LABEL.get(self.mode, self.mode)}**\n"
                f"Limit: **{limit}** · Theme: **{theme.label}**\n"
                f"Card: **{card_str}** · Sign-up counts: **{counts_str}**\n"
                f"Channel: {channel_str}{gradient_note}"
            ),
            inline=False,
        )
        embed.set_footer(
            text="Set the fields, then Post (new) or Save (edit). Roles required.",
        )
        return embed

    async def _rerender(self) -> None:
        """Refresh the live preview panel in place.

        Routes through the stored panel interaction (``safe_edit`` picks
        ``response.edit_message`` / ``followup.edit_message`` as appropriate) so
        the edit lands on the **ephemeral** hub message — a plain
        ``Message.edit()`` silently no-ops there, which is why the preview used
        to freeze while the underlying draft state changed. Falls back to
        ``Message.edit`` for any non-ephemeral caller.
        """
        if self._panel_interaction is not None and await safe_edit(
            self._panel_interaction,
            embed=self.build_embed(),
            view=self,
        ):
            return
        if self.message is not None:
            await self.message.edit(embed=self.build_embed(), view=self)

    async def _show_parent(self) -> None:
        """Return the panel to its parent manager (after Post / Save)."""
        if self.parent is None:
            return
        # Hand the live token to the parent so its own list refreshes work too.
        if hasattr(self.parent, "_panel_interaction"):
            self.parent._panel_interaction = self._panel_interaction  # type: ignore[attr-defined]
        embed = await self.parent.build_embed()  # type: ignore[attr-defined]
        if self._panel_interaction is not None and await safe_edit(
            self._panel_interaction,
            embed=embed,
            view=self.parent,
        ):
            return
        if self.message is not None:
            await self.message.edit(embed=embed, view=self.parent)

    # -- field editors ------------------------------------------------------
    # Lean layout (owner-approved, tools/sim/role_menu_layout_sim.py, 2026-07-01):
    #   row 0 = the hot content path (Template · Packs · Roles · Style · Text)
    #   row 1 = Colours · Channel · ⚙️ Advanced (Theme/Card/Counts/Mode/Limit) ·
    #           🚀 Post · ↩ Back
    # Style stays first-screen (a primary dropdown-vs-buttons choice); the
    # rarely-tapped knobs fold behind ⚙️ Advanced. Method definition order sets
    # the left-to-right order within each row.

    @discord.ui.button(label="🧩 Template", style=discord.ButtonStyle.grey, row=0)
    async def template_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        options = [
            discord.SelectOption(label=t.label[:100], value=t.key)
            for t in presentation.templates()
        ]
        await interaction.response.send_message(
            "Start from a template (you can still tweak everything):",
            view=PaginatedSelectView(
                interaction.user,
                options,
                self._apply_template,
                placeholder="Pick a starter template…",
            ),
            ephemeral=True,
        )

    @discord.ui.button(label="📦 Packs", style=discord.ButtonStyle.grey, row=0)
    async def packs_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        from views.roles._role_pack_flow import RolePackView

        view = RolePackView(
            interaction.user,
            self.guild,
            on_created=self._add_pack_roles,
        )
        await interaction.response.send_message(
            "Bulk-create roles and add them to this menu — pick a category and "
            "multiselect its roles, or **✏️ Custom (bulk)** to type your own:",
            view=view,
            ephemeral=True,
        )

    async def _add_pack_roles(
        self,
        interaction: discord.Interaction,
        role_ids: list[int],
    ) -> None:
        """on_created hook: fold the newly created pack roles into the draft."""
        for role_id in role_ids:
            if role_id not in self.role_ids and len(self.role_ids) < MAX_MENU_ROLES:
                self.role_ids.append(role_id)
        await self._rerender()

    @discord.ui.button(label="🏷️ Roles", style=discord.ButtonStyle.grey, row=0)
    async def roles_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        manageable, _excluded = role_feasibility.manageable_roles(
            self.guild.roles,
            bot_member=self.guild.me,
            actor=(
                interaction.user
                if isinstance(interaction.user, discord.Member)
                else None
            ),
        )
        if not manageable:
            await interaction.response.send_message(
                "I can't manage any of this server's roles (they're all above my "
                "highest role). Move my role up, then try again.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Pick the roles this menu offers (up to 25):",
            view=_RolePickView(self, manageable),
            ephemeral=True,
        )

    @discord.ui.button(label="🎚️ Style", style=discord.ButtonStyle.grey, row=0)
    async def style_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        """Toggle dropdown vs buttons — a first-screen choice (owner directive)."""
        self.style = "button" if self.style == "dropdown" else "dropdown"
        self._panel_interaction = interaction
        await safe_edit(interaction, embed=self.build_embed(), view=self)

    @discord.ui.button(label="📝 Text", style=discord.ButtonStyle.grey, row=0)
    async def text_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(_TextModal(self))

    @discord.ui.button(label="🎨 Colours", style=discord.ButtonStyle.grey, row=1)
    async def colours_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        await interaction.response.send_message(
            "Pick preset colours to auto-create as roles, or **✏️ Custom** for a "
            "custom colour or gradient — each becomes a role added to this menu:",
            view=_ColourRolesView(self),
            ephemeral=True,
        )

    @discord.ui.button(label="📍 Channel", style=discord.ButtonStyle.grey, row=1)
    async def channel_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        if not list(self.guild.text_channels):
            await interaction.response.send_message(
                "This server has no text channels to post in.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Pick the channel to post this menu in:",
            view=_ChannelPickView(self),
            ephemeral=True,
        )

    @discord.ui.button(label="⚙️ Advanced", style=discord.ButtonStyle.grey, row=1)
    async def advanced_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        """Open the folded less-common options (Theme / Card / Counts / Mode / Limit).

        Their current values stay visible on the main preview above; this sub-panel
        is just the controls, so the top-level builder stays lean.
        """
        await interaction.response.send_message(
            "Fine-tune the less-common options — the menu preview above updates live:",
            view=_AdvancedView(self),
            ephemeral=True,
        )

    @discord.ui.button(label="🚀 Post", style=discord.ButtonStyle.green, row=1)
    async def post_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        if not self.role_ids:
            await interaction.response.send_message(
                "Add at least one role first (🏷️ Roles).",
                ephemeral=True,
            )
            return
        await self._commit(interaction)

    # -- sub-step callbacks -------------------------------------------------

    async def _apply_template(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        tpl = presentation.get_template(values[0])
        if tpl is not None:
            self.title = tpl.title
            self.description = tpl.description
            self.theme = tpl.theme
            self.style = tpl.style
            self.mode = tpl.mode
            self.show_counts = tpl.show_counts
            self.template = tpl.key
        await interaction.response.edit_message(
            content="✓ Template applied.",
            view=None,
        )
        await self._rerender()

    async def _apply_theme(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        self.theme = values[0]
        await interaction.response.edit_message(content="✓ Theme set.", view=None)
        await self._rerender()

    async def _apply_mode(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        self.mode = values[0]
        await interaction.response.edit_message(content="✓ Mode set.", view=None)
        await self._rerender()

    # -- commit (Post new / Save edit) -------------------------------------

    async def _commit(self, interaction: discord.Interaction) -> None:
        from services import reaction_role_service
        from services.reaction_role_service import RoleOption

        if not await safe_defer(interaction, ephemeral=True):
            return
        # Snapshot the current role names as option labels so the rendered menu is
        # self-describing without re-resolving the guild (role_thresholds precedent).
        options = []
        for rid in self.role_ids:
            role = resources.resolve_role(self.guild, role_id=rid)
            if role is None:
                continue
            options.append(RoleOption(role_id=rid, emoji=None, label=role.name))

        if self.menu_id is None:
            await self._post_new(interaction, reaction_role_service, options)
        else:
            await self._save_edit(interaction, reaction_role_service, options)

    async def _post_new(self, interaction, service, options) -> None:  # type: ignore[no-untyped-def]
        channel = self.channel
        if channel is None:
            await interaction.followup.send(
                "I can't find a channel to post this menu in — re-open the builder "
                "in a text channel.",
                ephemeral=True,
            )
            return
        menu_id = await service.create_menu(
            guild_id=self.guild.id,
            channel_id=channel.id,
            title=self.title,
            description=self.description,
            style=self.style,
            mode=self.mode,
            max_roles=self.max_roles,
            options=options,
            theme=self.theme,
            card_template=self.card_template,
            card_text=self.card_text,
            show_counts=self.show_counts,
            actor_id=interaction.user.id,
        )
        menu = await service.get_menu(menu_id)
        opt_dicts = _option_dicts(await service.get_menu_options(menu_id))
        view = RoleMenuView(menu, opt_dicts)
        embed, files = build_menu_message(menu, opt_dicts, self.guild)
        try:
            message = await channel.send(embed=embed, view=view, files=files)
        except discord.Forbidden:
            await interaction.followup.send(
                "I couldn't post the menu — I lack permission to send messages here.",
                ephemeral=True,
            )
            return
        await service.set_menu_message(menu_id, message.id)
        interaction.client.add_view(view, message_id=message.id)
        await interaction.followup.send(
            f"🚀 Posted **{self.title}** to {channel.mention}.",
            ephemeral=True,
        )
        await self._show_parent()

    async def _save_edit(self, interaction, service, options) -> None:  # type: ignore[no-untyped-def]
        if self.menu_id is None:  # pragma: no cover - guarded by _commit
            return
        await service.update_menu(
            menu_id=self.menu_id,
            guild_id=self.guild.id,
            title=self.title,
            description=self.description,
            style=self.style,
            mode=self.mode,
            max_roles=self.max_roles,
            options=options,
            theme=self.theme,
            card_template=self.card_template,
            card_text=self.card_text,
            show_counts=self.show_counts,
            actor_id=interaction.user.id,
        )
        menu = await service.get_menu(self.menu_id)
        opt_dicts = _option_dicts(await service.get_menu_options(self.menu_id))
        view = RoleMenuView(menu, opt_dicts)
        edited = False
        if menu and menu.get("message_id") and menu.get("channel_id"):
            channel = resources.resolve_channel(
                self.guild,
                channel_id=int(menu["channel_id"]),
            )
            if isinstance(channel, discord.abc.Messageable):
                try:
                    message = await channel.fetch_message(int(menu["message_id"]))
                    embed, files = build_menu_message(menu, opt_dicts, self.guild)
                    # ``attachments=`` replaces the card (or clears it when [] —
                    # so removing a card on edit drops the old image too).
                    await message.edit(embed=embed, view=view, attachments=files)
                    interaction.client.add_view(view, message_id=message.id)
                    edited = True
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    edited = False
        result_text = (
            "💾 Saved — the live menu was updated."
            if edited
            else "💾 Saved. (The posted message couldn't be edited; re-post if needed.)"
        )
        await interaction.followup.send(result_text, ephemeral=True)
        await self._show_parent()


# ---------------------------------------------------------------------------
# Sub-views + modals
# ---------------------------------------------------------------------------


class _AdvancedView(BaseView):
    """The ⚙️ Advanced sub-panel — the less-common menu options folded off the
    lean two-row builder (Theme / Card / Counts / Mode / Limit).

    Each control edits the builder draft and refreshes the **main preview** via
    the builder's stored panel interaction (``_rerender``), so the current values
    stay visible on that preview while the top-level builder stays clean. The
    pickers/modals reused here are exactly the ones the builder opened when these
    were top-level buttons.
    """

    def __init__(self, builder: RoleMenuBuilder) -> None:
        super().__init__(builder._author, timeout=300)
        self.builder = builder

    def build_embed(self) -> discord.Embed:
        counts = "on" if self.builder.show_counts else "off"
        return discord.Embed(
            title="⚙️ Advanced options",
            description=(
                "Fine-tune the less-common menu options below. Every current value "
                "is shown on the **menu preview above**, which updates live as you "
                "change it here.\n\n"
                f"📊 Sign-up counts: **{counts}** — tap 📊 Counts to toggle."
            ),
            color=presentation.theme_color(self.builder.theme),
        )

    @discord.ui.button(label="🎭 Theme", style=discord.ButtonStyle.grey, row=0)
    async def theme_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        options = [
            discord.SelectOption(
                label=t.label,
                value=t.key,
                default=t.key == self.builder.theme,
            )
            for t in presentation.themes()
        ]
        await interaction.response.send_message(
            "Pick an embed theme:",
            view=PaginatedSelectView(
                interaction.user,
                options,
                self.builder._apply_theme,
                placeholder="Theme…",
            ),
            ephemeral=True,
        )

    @discord.ui.button(label="⚙️ Mode", style=discord.ButtonStyle.grey, row=0)
    async def mode_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        options = [
            discord.SelectOption(
                label=_MODE_LABEL[m],
                value=m,
                default=m == self.builder.mode,
            )
            for m in ("normal", "unique", "verify")
        ]
        await interaction.response.send_message(
            "How should members pick from this menu?",
            view=PaginatedSelectView(
                interaction.user,
                options,
                self.builder._apply_mode,
                placeholder="Mode…",
            ),
            ephemeral=True,
        )

    @discord.ui.button(label="🔢 Limit", style=discord.ButtonStyle.grey, row=0)
    async def limit_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(_LimitModal(self.builder))

    @discord.ui.button(label="🖼️ Card", style=discord.ButtonStyle.grey, row=1)
    async def card_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            "Add an optional **banner image** above the menu, or set its overlay "
            "text. Pick **✖️ None** to remove the card:",
            view=_CardPickView(self.builder),
            ephemeral=True,
        )

    @discord.ui.button(label="📊 Counts", style=discord.ButtonStyle.grey, row=1)
    async def counts_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        """Toggle the live sign-up counter (current holders shown on the menu)."""
        self.builder.show_counts = not self.builder.show_counts
        # Refresh this sub-panel in place (shows the new state) …
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        # … then the main builder preview via its stored panel interaction.
        await self.builder._rerender()


class _RolePickView(BaseView):
    """Ephemeral windowed multi-role picker feeding the builder draft."""

    def __init__(self, builder: RoleMenuBuilder, roles: list[discord.Role]) -> None:
        super().__init__(builder._author, timeout=180)
        self.builder = builder
        attach_multi_role_select(
            self,
            roles,
            self._on_pick,
            placeholder="Select the menu's roles…",
            max_values=min(len(roles), 25),
        )

    async def _on_pick(
        self,
        interaction: discord.Interaction,
        role_ids: list[int],
    ) -> None:
        # The windowed multi-select already caps a page's selection; bound the
        # stored set to a menu's hard role cap (Discord's 25 component/option max).
        self.builder.role_ids = role_ids[:MAX_MENU_ROLES]
        await interaction.response.edit_message(
            content=f"✓ {len(self.builder.role_ids)} role(s) selected.",
            view=None,
        )
        await self.builder._rerender()


class _TextModal(discord.ui.Modal, title="Menu text"):  # type: ignore[call-arg]
    title_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Title",
        placeholder="Pick your roles",
        max_length=100,
    )
    desc_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Description",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000,
    )

    def __init__(self, builder: RoleMenuBuilder) -> None:
        super().__init__()
        self.builder = builder
        self.title_in.default = builder.title
        self.desc_in.default = builder.description or ""

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.builder.title = self.title_in.value.strip() or "Pick your roles"
        self.builder.description = self.desc_in.value.strip() or None
        self.builder._panel_interaction = interaction
        await safe_edit(
            interaction, embed=self.builder.build_embed(), view=self.builder
        )


class _LimitModal(discord.ui.Modal, title="Per-member limit"):  # type: ignore[call-arg]
    limit_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Max roles a member can pick (0 = unlimited)",
        placeholder="0",
        max_length=2,
        required=False,
    )

    def __init__(self, builder: RoleMenuBuilder) -> None:
        super().__init__()
        self.builder = builder
        self.limit_in.default = str(builder.max_roles)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = self.limit_in.value.strip()
        try:
            value = max(0, int(raw)) if raw else 0
        except ValueError:
            await interaction.response.send_message(
                "❌ Enter a whole number (0 for unlimited).",
                ephemeral=True,
            )
            return
        self.builder.max_roles = value
        # Opened from the ⚙️ Advanced sub-panel, so this interaction is NOT the main
        # panel's — refresh the main preview through the builder's stored token.
        if not await safe_defer(interaction):
            return
        await self.builder._rerender()


class _CardPickView(BaseView):
    """Pick a banner-card style (or None) and optionally set its overlay text."""

    def __init__(self, builder: RoleMenuBuilder) -> None:
        super().__init__(builder._author, timeout=180)
        self.builder = builder
        options = [
            discord.SelectOption(
                label="✖️ None",
                value="",
                description="No banner image",
                default=not builder.card_template,
            ),
        ]
        for card in presentation.card_templates():
            options.append(
                discord.SelectOption(
                    label=card.label,
                    value=card.key,
                    default=card.key == builder.card_template,
                ),
            )
        self._select: discord.ui.Select = discord.ui.Select(  # type: ignore[type-arg]
            placeholder="Banner card style…",
            options=options,
            min_values=1,
            max_values=1,
            row=0,
        )
        self._select.callback = self._on_pick  # type: ignore[method-assign]
        self.add_item(self._select)

    async def _on_pick(self, interaction: discord.Interaction) -> None:
        value = self._select.values[0]
        self.builder.card_template = value or None
        card = presentation.get_card_template(value)
        msg = f"✓ Card set to {card.label}." if card else "✓ Banner card removed."
        await interaction.response.edit_message(content=msg, view=None)
        await self.builder._rerender()

    @discord.ui.button(
        label="✏️ Overlay text",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def overlay_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(_CardTextModal(self.builder))


class _CardTextModal(discord.ui.Modal, title="Card overlay text"):  # type: ignore[call-arg]
    text_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Overlay text (optional)",
        placeholder="e.g. Choose your roles below",
        required=False,
        max_length=80,
    )

    def __init__(self, builder: RoleMenuBuilder) -> None:
        super().__init__()
        self.builder = builder
        self.text_in.default = builder.card_text or ""

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.builder.card_text = self.text_in.value.strip() or None
        if not await safe_defer(interaction):
            return
        await self.builder._rerender()


# ---------------------------------------------------------------------------
# Sub-flows: post-channel picker + colour-role auto-create
# ---------------------------------------------------------------------------


class _ChannelPickView(BaseView):
    """Ephemeral picker that sets the builder's post-target channel."""

    def __init__(self, builder: RoleMenuBuilder) -> None:
        super().__init__(builder._author, timeout=180)
        self.builder = builder
        attach_channel_select(
            self,
            list(builder.guild.text_channels),
            self._on_pick,
            placeholder="Channel to post the menu in…",
        )

    async def _on_pick(
        self,
        interaction: discord.Interaction,
        channel_id: int,
    ) -> None:
        target = _as_messageable(
            resources.resolve_channel(self.builder.guild, channel_id=channel_id),
        )
        if target is None:
            await interaction.response.edit_message(
                content="That channel can't be posted to — pick a text channel.",
                view=None,
            )
            return
        self.builder.channel = target
        await interaction.response.edit_message(
            content=f"✓ This menu will post to {target.mention}.",
            view=None,
        )
        await self.builder._rerender()


def _safe_parse_color(value: str | None) -> discord.Color | None:
    """Parse an optional hex colour; return ``None`` when blank or invalid."""
    if not value or not value.strip():
        return None
    try:
        return _parse_color(value)
    except (ValueError, TypeError):
        return None


class _ColourRolesView(BaseView):
    """Pick preset colours (auto-created as roles) or open the custom/gradient modal."""

    def __init__(self, builder: RoleMenuBuilder) -> None:
        from services.reaction_role_service import supports_role_gradients

        super().__init__(builder._author, timeout=180)
        self.builder = builder
        options = [
            discord.SelectOption(label=name, value=hex_value)
            for name, hex_value in _COLOR_OPTIONS
        ]
        attach_multi_select(
            self,
            options,
            self._on_presets,
            placeholder="Preset colours to create as roles…",
            max_values=len(options),
            select_row=0,
        )
        # Gradient presets only render on Enhanced-Role-Styles guilds (3 boosts);
        # offered solely when the perk is present so we never show a styled option
        # that would silently fall back to solid.
        if supports_role_gradients(builder.guild):
            gradient_options = [
                discord.SelectOption(label=p.label, value=p.key, description=p.name)
                for p in presentation.gradient_presets()
            ]
            attach_multi_select(
                self,
                gradient_options,
                self._on_gradient_presets,
                placeholder="✨ Gradient colours (Enhanced Role Styles)…",
                max_values=len(gradient_options),
                select_row=2,
            )

    @discord.ui.button(
        label="✏️ Custom / gradient…",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def custom_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(_CustomColourModal(self.builder))

    async def _on_presets(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        by_hex = {hex_value: name for name, hex_value in _COLOR_OPTIONS}
        specs: list[
            tuple[str, discord.Color, discord.Color | None, discord.Color | None]
        ] = [
            (by_hex.get(hex_value, hex_value), _parse_color(hex_value), None, None)
            for hex_value in values
        ]
        await _commit_colour_roles(interaction, self.builder, specs)

    async def _on_gradient_presets(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        by_key = {p.key: p for p in presentation.gradient_presets()}
        specs: list[
            tuple[str, discord.Color, discord.Color | None, discord.Color | None]
        ] = []
        for key in values:
            preset = by_key.get(key)
            if preset is None:
                continue
            specs.append(
                (
                    preset.name,
                    discord.Color(preset.primary),
                    discord.Color(preset.secondary),
                    None,
                ),
            )
        await _commit_colour_roles(interaction, self.builder, specs)


class _CustomColourModal(discord.ui.Modal, title="Custom colour role"):  # type: ignore[call-arg]
    name_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Role name",
        placeholder="e.g. Sunset",
        max_length=100,
    )
    primary_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Colour (hex)",
        placeholder="#e67e22",
        max_length=7,
    )
    secondary_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Gradient 2nd colour (hex, optional)",
        placeholder="#f1c40f — needs Enhanced Role Styles",
        required=False,
        max_length=7,
    )
    tertiary_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Holographic 3rd colour (hex, optional)",
        required=False,
        max_length=7,
    )

    def __init__(self, builder: RoleMenuBuilder) -> None:
        super().__init__()
        self.builder = builder

    async def on_submit(self, interaction: discord.Interaction) -> None:
        primary = _safe_parse_color(self.primary_in.value)
        if primary is None:
            await interaction.response.send_message(
                "❌ The colour must be a hex value like `#e67e22`.",
                ephemeral=True,
            )
            return
        name = self.name_in.value.strip() or "Colour"
        await _commit_colour_roles(
            interaction,
            self.builder,
            [
                (
                    name,
                    primary,
                    _safe_parse_color(self.secondary_in.value),
                    _safe_parse_color(self.tertiary_in.value),
                ),
            ],
        )


async def _commit_colour_roles(
    interaction: discord.Interaction,
    builder: RoleMenuBuilder,
    specs: list[tuple[str, discord.Color, discord.Color | None, discord.Color | None]],
) -> None:
    """Create/reuse a colour role per spec and add it to the builder's draft."""
    from services import reaction_role_service

    if not specs:
        await interaction.response.send_message(
            "Pick at least one colour.",
            ephemeral=True,
        )
        return
    # Creating several roles is multiple API calls — defer first, report after.
    if not await safe_defer(interaction, ephemeral=True, thinking=True):
        return

    created: list[str] = []
    reused: list[str] = []
    notes: list[str] = []
    for name, primary, secondary, tertiary in specs:
        role_id, was_created, note = await reaction_role_service.ensure_color_role(
            builder.guild,
            name=name,
            color=primary,
            secondary=secondary,
            tertiary=tertiary,
            actor=interaction.user,
        )
        if role_id is None:
            notes.append(f"{name}: {note or 'could not be created'}")
            continue
        if role_id not in builder.role_ids and len(builder.role_ids) < MAX_MENU_ROLES:
            builder.role_ids.append(role_id)
        (created if was_created else reused).append(name)
        if note:
            notes.append(f"{name}: {note}")

    parts: list[str] = []
    if created:
        parts.append(f"🎨 Created {', '.join(created)}")
    if reused:
        parts.append(f"♻️ Reused existing {', '.join(reused)}")
    if notes:
        parts.append("\n".join(notes))
    await interaction.followup.send(
        "\n".join(parts) or "No colour roles were added.",
        ephemeral=True,
    )
    await builder._rerender()


__all__ = ["RoleMenuBuilder", "RoleMenuListView"]
