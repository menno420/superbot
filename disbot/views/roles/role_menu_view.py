"""The public, restart-durable role menu (reaction-roles overhaul PR 2).

The headline Surface-B feature: a bot-posted message any member clicks to
self-assign roles — a dropdown (the owner-locked default, plan §9) or a row of
buttons — with an **ephemeral confirmation** and **server-side mode enforcement**
(``unique`` / ``verify`` / ``max_roles``). Strictly nicer than Carl-bot's
emoji-reaction core: clicks are stateless, so there is no stale-reaction problem
and no add-reaction permission needed.

**Restart durability via** :class:`discord.ui.DynamicItem`. The menu is a *public*
message (every member interacts), so the anchor-owned :class:`PersistentView`
recovery (single-owner) does not fit. Instead each component encodes its
``menu_id`` (and, for buttons, ``role_id``) in a templated ``custom_id``; the item
*classes* are registered once at startup (:func:`register_dynamic_items`) and
discord.py reconstructs the handler from the ``custom_id`` on every interaction —
no per-message registration, no DB scan on boot, works for unlimited menus.

Layer note: this view reads through :mod:`services.reaction_role_service` and
mutates only Discord roles (``member.add_roles`` / ``remove_roles``); it performs
no DB writes, honouring the views→(no cogs) / no-direct-DB rules.
"""

from __future__ import annotations

import logging
import re

import discord

from core.runtime import resources
from services import reaction_role_service as rr
from utils.role_menu_logic import RoleDelta, reconcile_select, toggle_button
from utils.role_menu_presets import resolve_theme

logger = logging.getLogger("bot.views.role_menu")

_BTN_TEMPLATE = r"rmenu:btn:(?P<menu_id>[0-9]+):(?P<role_id>[0-9]+)"
_SEL_TEMPLATE = r"rmenu:sel:(?P<menu_id>[0-9]+)"

_BUTTON_STYLE = discord.ButtonStyle.secondary
_MAX_BUTTONS = 25  # 5 action rows × 5 buttons
_MAX_OPTIONS = 25  # Discord select cap


# ---------------------------------------------------------------------------
# Dynamic components (custom_id-routed, restart-durable)
# ---------------------------------------------------------------------------


class RoleMenuToggleButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=_BTN_TEMPLATE,
):
    """One button on a role menu — toggles a single role on click."""

    def __init__(
        self,
        menu_id: int,
        role_id: int,
        *,
        label: str = "role",
        emoji: str | None = None,
        style: discord.ButtonStyle = _BUTTON_STYLE,
    ) -> None:
        self.menu_id = menu_id
        self.role_id = role_id
        super().__init__(
            discord.ui.Button(
                label=(label or "role")[:80],
                emoji=_coerce_emoji(emoji),
                style=style,
                custom_id=f"rmenu:btn:{menu_id}:{role_id}",
            ),
        )

    @classmethod
    async def from_custom_id(  # type: ignore[override]
        cls,
        _interaction: discord.Interaction,
        _item: discord.ui.Button,
        match: re.Match[str],
    ) -> RoleMenuToggleButton:
        return cls(int(match["menu_id"]), int(match["role_id"]))

    async def callback(self, interaction: discord.Interaction) -> None:
        await _handle_button(interaction, self.menu_id, self.role_id)


class RoleMenuSelect(
    discord.ui.DynamicItem[discord.ui.Select],
    template=_SEL_TEMPLATE,
):
    """The dropdown on a role menu — submits the member's desired role set."""

    def __init__(
        self,
        menu_id: int,
        *,
        options: list[discord.SelectOption] | None = None,
        placeholder: str = "Pick your roles…",
        min_values: int = 0,
        max_values: int = 1,
    ) -> None:
        self.menu_id = menu_id
        super().__init__(
            discord.ui.Select(
                custom_id=f"rmenu:sel:{menu_id}",
                placeholder=placeholder,
                min_values=min_values,
                max_values=max_values,
                options=options or [discord.SelectOption(label="—", value="0")],
            ),
        )

    @classmethod
    async def from_custom_id(  # type: ignore[override]
        cls,
        _interaction: discord.Interaction,
        _item: discord.ui.Select,
        match: re.Match[str],
    ) -> RoleMenuSelect:
        return cls(int(match["menu_id"]))

    async def callback(self, interaction: discord.Interaction) -> None:
        # Read selected values straight from the payload so the handler does not
        # depend on the reconstructed component's option list.
        raw: list[str] = []
        if isinstance(interaction.data, dict):
            raw = list(interaction.data.get("values", []))  # type: ignore[arg-type]
        picked = {int(v) for v in raw if v.isdigit()}
        await _handle_select(interaction, self.menu_id, picked)


def register_dynamic_items(bot: discord.Client) -> None:
    """Register the role-menu dynamic items so interactions route after restart."""
    bot.add_dynamic_items(RoleMenuToggleButton, RoleMenuSelect)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_role_menu(
    menu: dict,
    options: list[dict],
    guild: discord.Guild,
) -> tuple[discord.Embed, discord.ui.View]:
    """Build the (embed, view) for a posted role menu from its row + options."""
    theme = resolve_theme(menu.get("theme"))
    embed = discord.Embed(
        title=menu.get("title") or "Pick your roles",
        description=_menu_body(menu, options, guild),
        color=theme.color,
    )
    if theme.footer:
        embed.set_footer(text=theme.footer)

    view = discord.ui.View(timeout=None)
    if menu.get("style") == "button":
        for opt in options[:_MAX_BUTTONS]:
            role = resources.resolve_role(guild, role_id=int(opt["role_id"]))
            view.add_item(
                RoleMenuToggleButton(
                    int(menu["menu_id"]),
                    int(opt["role_id"]),
                    label=_option_label(opt, role),
                    emoji=opt.get("emoji"),
                ),
            )
    else:  # dropdown (default) / unknown style → dropdown
        view.add_item(
            RoleMenuSelect(
                int(menu["menu_id"]),
                options=_select_options(options, guild),
                min_values=0,
                max_values=_select_max_values(menu, len(options)),
            ),
        )
    return embed, view


def _menu_body(menu: dict, options: list[dict], guild: discord.Guild) -> str:
    lines: list[str] = []
    if menu.get("description"):
        lines.append(str(menu["description"]))
        lines.append("")
    for opt in options:
        role = resources.resolve_role(guild, role_id=int(opt["role_id"]))
        mention = role.mention if role else f"*(deleted role {opt['role_id']})*"
        emoji = f"{opt['emoji']} " if opt.get("emoji") else ""
        lines.append(f"{emoji}{mention}")
    if not options:
        lines.append("*No roles configured yet.*")
    note = _mode_note(menu)
    if note:
        lines.append("")
        lines.append(note)
    return "\n".join(lines)


def _mode_note(menu: dict) -> str | None:
    mode = menu.get("mode")
    cap = int(menu.get("max_roles") or 0)
    if mode == "unique":
        return "_You can hold one role from this menu at a time._"
    if mode == "verify":
        return "_Roles here can only be added._"
    if cap:
        return f"_Pick up to {cap} role(s) from this menu._"
    return None


def _select_options(
    options: list[dict],
    guild: discord.Guild,
) -> list[discord.SelectOption]:
    out: list[discord.SelectOption] = []
    for opt in options[:_MAX_OPTIONS]:
        role = resources.resolve_role(guild, role_id=int(opt["role_id"]))
        out.append(
            discord.SelectOption(
                label=_option_label(opt, role)[:100],
                value=str(opt["role_id"]),
                emoji=_coerce_emoji(opt.get("emoji")),
            ),
        )
    return out or [discord.SelectOption(label="—", value="0")]


def _select_max_values(menu: dict, option_count: int) -> int:
    if menu.get("mode") == "unique":
        return 1
    cap = int(menu.get("max_roles") or 0)
    usable = max(1, min(option_count, _MAX_OPTIONS))
    return min(cap, usable) if cap else usable


def _option_label(opt: dict, role: discord.Role | None) -> str:
    if opt.get("label"):
        return str(opt["label"])
    if role is not None:
        return role.name
    return f"role {opt['role_id']}"


def _coerce_emoji(emoji: str | None) -> str | discord.PartialEmoji | None:
    if not emoji:
        return None
    try:
        return discord.PartialEmoji.from_str(emoji)
    except Exception:  # pragma: no cover — defensive, malformed stored emoji
        return None


# ---------------------------------------------------------------------------
# Interaction handlers
# ---------------------------------------------------------------------------


async def _handle_select(
    interaction: discord.Interaction,
    menu_id: int,
    picked: set[int],
) -> None:
    menu, options = await _load(interaction, menu_id)
    if menu is None:
        return
    menu_role_ids = [int(o["role_id"]) for o in options]
    member = interaction.user
    delta = reconcile_select(
        member_role_ids={r.id for r in getattr(member, "roles", [])},
        menu_role_ids=menu_role_ids,
        picked_role_ids=picked,
        mode=str(menu.get("mode") or "normal"),
        max_roles=int(menu.get("max_roles") or 0),
    )
    await _apply_and_confirm(interaction, delta)


async def _handle_button(
    interaction: discord.Interaction,
    menu_id: int,
    role_id: int,
) -> None:
    menu, options = await _load(interaction, menu_id)
    if menu is None:
        return
    menu_role_ids = [int(o["role_id"]) for o in options]
    member = interaction.user
    delta = toggle_button(
        member_role_ids={r.id for r in getattr(member, "roles", [])},
        menu_role_ids=menu_role_ids,
        clicked_role_id=role_id,
        mode=str(menu.get("mode") or "normal"),
        max_roles=int(menu.get("max_roles") or 0),
    )
    await _apply_and_confirm(interaction, delta)


async def _load(
    interaction: discord.Interaction,
    menu_id: int,
) -> tuple[dict | None, list[dict]]:
    menu = await rr.get_menu(menu_id)
    if menu is None or interaction.guild is None:
        await interaction.response.send_message(
            "This role menu no longer exists.",
            ephemeral=True,
        )
        return None, []
    options = await rr.get_menu_options(menu_id)
    return menu, options


async def _apply_and_confirm(
    interaction: discord.Interaction,
    delta: RoleDelta,
) -> None:
    guild = interaction.guild
    member = interaction.user
    if guild is None or not isinstance(member, discord.Member):
        # Role menus only live in guilds; nothing to do off-guild.
        return

    add = [
        r
        for r in (resources.resolve_role(guild, role_id=i) for i in delta.to_add)
        if r is not None
    ]
    remove = [
        r
        for r in (resources.resolve_role(guild, role_id=i) for i in delta.to_remove)
        if r is not None
    ]

    try:
        if add:
            await member.add_roles(*add, reason="Role menu self-assign")
        if remove:
            await member.remove_roles(*remove, reason="Role menu self-assign")
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I can't manage one of those roles — my role must sit **above** them"
            " and I need **Manage Roles**.",
            ephemeral=True,
        )
        return
    except discord.HTTPException:
        logger.exception("Role menu assignment failed for %s", member.id)
        await interaction.response.send_message(
            "❌ Something went wrong updating your roles. Try again in a moment.",
            ephemeral=True,
        )
        return

    parts: list[str] = []
    if add:
        parts.append("✅ Added " + ", ".join(r.mention for r in add))
    if remove:
        parts.append("➖ Removed " + ", ".join(r.mention for r in remove))
    if delta.rejected:
        parts.append("⚠️ " + delta.rejected)
    if not parts:
        parts.append("No changes — you're all set.")
    await interaction.response.send_message("\n".join(parts), ephemeral=True)


__all__ = [
    "RoleMenuSelect",
    "RoleMenuToggleButton",
    "register_dynamic_items",
    "render_role_menu",
]
