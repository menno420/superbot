"""The member-facing role menu — a restart-durable button/dropdown self-role panel.

This is the modern surface Carl-bot lacks at its core (plan §4 PR 2 / Surface B):
a public message anyone can click to self-assign roles, with **server-side** mode
enforcement (``unique`` / ``verify`` / ``max_roles``) and an **ephemeral**
confirmation — no stale reactions, no "un-react to remove" confusion.

It is a :class:`PersistentView` so it survives restarts: every component carries a
static ``role_menu:{menu_id}:…`` custom_id, and :func:`reattach_role_menus` re-binds
a fresh view to each posted menu message at boot. The view holds only the menu's
*immutable config* (menu id + the option list), never per-user state — every click
acts on ``interaction.user`` and the authoritative menu row is re-read inside the
audited service.

All assignment goes through :mod:`services.reaction_role_service`; this module is a
thin UI over that seam (no DB writes, no role math here).
"""

from __future__ import annotations

import io
import logging

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.persistent_views import PersistentView
from utils import role_menu_presentation as presentation
from utils import role_menu_render
from views.base import handle_view_error
from views.roles import role_menu_counter

logger = logging.getLogger("bot.views.role_menu")

# Discord caps a select at 25 options and a view at 25 components (5×5 buttons),
# so a menu offers at most this many roles (the builder enforces it too).
MAX_MENU_ROLES = 25

# The attachment filename a banner card is sent under (the embed image references
# ``attachment://`` this name); kept stable so an edit replaces the same slot.
_CARD_FILENAME = "role_menu_card.png"


def build_menu_embed(
    menu: dict,
    options: list[dict],
    guild: discord.Guild,
) -> discord.Embed:
    """Render a menu row + its options into its themed embed."""
    theme = presentation.get_theme(menu.get("theme"))
    embed = discord.Embed(
        title=menu.get("title") or "Pick your roles",
        description=menu.get("description") or None,
        color=theme.color,
    )

    # Live sign-up counter (opt-in, migration 103): current holders per role +
    # the distinct total, computed in one pass and rendered inline + in the footer.
    show_counts = bool(menu.get("show_counts"))
    counts: dict[int, int] = {}
    total = 0
    if show_counts:
        counts, total = role_menu_counter.collect_counts(
            guild,
            [int(opt["role_id"]) for opt in options],
        )

    lines: list[str] = []
    for opt in options:
        role = resources.resolve_role(guild, role_id=int(opt["role_id"]))
        if role is None:
            continue
        emoji = opt.get("emoji")
        prefix = f"{emoji} " if emoji else ""
        label = opt.get("label") or role.name
        line = (
            f"{prefix}{role.mention} — {label}"
            if opt.get("label")
            else f"{prefix}{role.mention}"
        )
        if show_counts:
            line += f" · {role_menu_counter.format_count(counts.get(int(opt['role_id']), 0))}"
        lines.append(line)
    if lines:
        embed.add_field(name="Roles", value="\n".join(lines), inline=False)

    mode = menu.get("mode", "normal")
    max_roles = int(menu.get("max_roles") or 0)
    hint = {
        "unique": "Pick one — choosing another swaps it.",
        "verify": "Tap to claim — this menu only ever adds a role.",
    }.get(mode)
    if not hint and max_roles:
        hint = f"You can hold up to {max_roles} of these roles."
    footer = hint or theme.footer or "Pick the roles you want."
    if show_counts:
        footer = f"{footer}  ·  {role_menu_counter.format_total(total)}"
    embed.set_footer(text=footer)
    return embed


def render_menu_card(menu: dict) -> bytes | None:
    """Render a menu's optional banner card → PNG bytes, or ``None`` (no card / no PIL).

    Returns ``None`` when the menu carries no ``card_template``, the template key is
    unknown, or Pillow is unavailable — so every caller degrades to embed-only. The
    card's accent is the menu theme's colour so the banner matches the embed.
    """
    card = presentation.get_card_template(menu.get("card_template"))
    if card is None:
        return None
    theme = presentation.get_theme(menu.get("theme"))
    return role_menu_render.render_role_menu_card(
        style=card.style,
        title=menu.get("title") or "Pick your roles",
        overlay=(menu.get("card_text") or None),
        accent=theme.color.to_rgb(),
    )


def build_menu_message(
    menu: dict,
    options: list[dict],
    guild: discord.Guild,
) -> tuple[discord.Embed, list[discord.File]]:
    """Compose a menu's message body: the themed embed + an optional banner card.

    When the menu has a banner card (and Pillow is available) the embed's image is
    set to the attached card; otherwise the file list is empty and the embed is
    image-free. Callers send with ``files=`` (post/repost) or edit with
    ``attachments=`` (edit-in-place) — passing ``[]`` removes a prior card cleanly.
    """
    embed = build_menu_embed(menu, options, guild)
    card_bytes = render_menu_card(menu)
    if card_bytes is None:
        return embed, []
    embed.set_image(url=f"attachment://{_CARD_FILENAME}")
    return embed, [discord.File(io.BytesIO(card_bytes), filename=_CARD_FILENAME)]


def _select_bounds(mode: str, max_roles: int, option_count: int) -> tuple[int, int]:
    """Return ``(min_values, max_values)`` for a dropdown given the menu's mode."""
    if mode == "unique":
        max_values = 1
    elif max_roles:
        max_values = min(max_roles, option_count)
    else:
        max_values = option_count
    return 0, max(1, min(max_values, MAX_MENU_ROLES))


class _RoleButton(discord.ui.Button):
    """One role-per-button toggle (the ``style='button'`` surface)."""

    def __init__(
        self,
        menu_id: int,
        role_id: int,
        label: str,
        emoji: str | None,
    ) -> None:
        super().__init__(
            label=label[:80],
            emoji=emoji or None,
            style=discord.ButtonStyle.secondary,
            custom_id=f"role_menu:{menu_id}:role:{role_id}",
        )
        self._menu_id = menu_id
        self._role_id = role_id

    async def callback(self, interaction: discord.Interaction) -> None:
        await _handle_toggle(
            interaction,
            self._menu_id,
            self._role_id,
            show_counts=_view_shows_counts(self.view),
        )


class _RoleSelect(discord.ui.Select):
    """The multi-select dropdown surface (the default)."""

    def __init__(
        self,
        menu_id: int,
        options: list[discord.SelectOption],
        *,
        min_values: int,
        max_values: int,
    ) -> None:
        super().__init__(
            custom_id=f"role_menu:{menu_id}:select",
            placeholder="Pick your roles…",
            min_values=min_values,
            max_values=max_values,
            options=options or [discord.SelectOption(label="— no roles —", value="0")],
            disabled=not options,
        )
        self._menu_id = menu_id

    async def callback(self, interaction: discord.Interaction) -> None:
        selected = [int(v) for v in self.values if v != "0"]
        await _handle_selection(
            interaction,
            self._menu_id,
            selected,
            show_counts=_view_shows_counts(self.view),
        )


class _RosterButton(discord.ui.Button):
    """An ephemeral "who picked each option" roster (counted menus only).

    Read-only: it lists current holders (``role.members``), the same opt-in public
    membership the counter already surfaces — so it adds no privacy surface over
    what Discord's member list already shows.
    """

    def __init__(self, menu_id: int) -> None:
        super().__init__(
            label="Who's in?",
            emoji="👥",
            style=discord.ButtonStyle.primary,
            custom_id=f"role_menu:{menu_id}:roster",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await _handle_roster(interaction, self.view)


class RoleMenuView(PersistentView):
    """A restart-durable self-role menu rendered from a ``role_menus`` row.

    Construct with the menu row + its option rows. The no-argument form yields an
    empty view; real instances come from :func:`reattach_role_menus` and the
    builder's Post.

    NOT registered in the persistent-view anchor registry (no ``register()``):
    a role menu is a **public, data-driven message** (one persistent view per
    ``role_menus`` row), re-bound at boot by :func:`reattach_role_menus` keyed on
    the table — unlike the per-user, anchor-owned hub panels the registry's
    ``restore_anchors`` path is for (``RoleHubPanelView`` owns ``SUBSYSTEM='role'``
    there). Registering it would both collide with that key and trip the
    identity-contract ``SUBSYSTEMS`` parity check. Persistence still works: each
    component carries a static ``role_menu:{menu_id}:*`` custom_id and the view is
    bound with ``bot.add_view(..., message_id=...)``.
    """

    # The menu is a public, shared message — any member self-assigns — so the
    # anchor-ownership check in PersistentView does not apply (overridden below).

    def __init__(
        self,
        menu: dict | None = None,
        options: list[dict] | None = None,
    ) -> None:
        super().__init__()
        self.menu = menu
        self.options = options or []
        if menu is None:
            return
        menu_id = int(menu["menu_id"])
        style = menu.get("style", "dropdown")
        if style == "button":
            self._build_buttons(menu_id)
        else:
            self._build_select(menu_id)
        # The "Who's in?" roster rides the same opt-in as the counter, and only
        # when there's component room (Discord caps a view at 25 components — a
        # full 25-role button menu has none; RSVPs are small, so this never bites).
        if menu.get("show_counts") and len(self.children) < 25:
            self.add_item(_RosterButton(menu_id))

    def _build_buttons(self, menu_id: int) -> None:
        for opt in self.options[:MAX_MENU_ROLES]:
            label = opt.get("label") or f"Role {opt['role_id']}"
            self.add_item(
                _RoleButton(menu_id, int(opt["role_id"]), label, opt.get("emoji")),
            )

    def _build_select(self, menu_id: int) -> None:
        if self.menu is None:  # pragma: no cover - guarded by __init__
            return
        select_options: list[discord.SelectOption] = []
        for opt in self.options[:MAX_MENU_ROLES]:
            select_options.append(
                discord.SelectOption(
                    label=(opt.get("label") or f"Role {opt['role_id']}")[:100],
                    value=str(opt["role_id"]),
                    emoji=opt.get("emoji") or None,
                ),
            )
        min_values, max_values = _select_bounds(
            self.menu.get("mode", "normal"),
            int(self.menu.get("max_roles") or 0),
            len(select_options),
        )
        self.add_item(
            _RoleSelect(
                menu_id,
                select_options,
                min_values=min_values,
                max_values=max_values,
            ),
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Public menu — any guild member may self-assign (no ownership gate)."""
        return interaction.guild is not None and isinstance(
            interaction.user,
            discord.Member,
        )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        await handle_view_error(self, interaction, error, item)


# ---------------------------------------------------------------------------
# Interaction handlers (shared by both surfaces) — thin over the audited service
# ---------------------------------------------------------------------------


def _view_shows_counts(view: discord.ui.View | None) -> bool:
    """Whether the menu behind a component has the live counter on (cheap read)."""
    menu = getattr(view, "menu", None)
    return bool(menu and menu.get("show_counts"))


async def _handle_toggle(
    interaction: discord.Interaction,
    menu_id: int,
    role_id: int,
    *,
    show_counts: bool = False,
) -> None:
    from services import reaction_role_service

    member, guild = _require_member(interaction)
    if member is None or guild is None:
        return
    outcome = await reaction_role_service.toggle_role(
        menu_id=menu_id,
        member=member,
        guild=guild,
        clicked_role_id=role_id,
    )
    await interaction.response.send_message(
        _format_outcome(guild, outcome),
        ephemeral=True,
    )
    if show_counts and outcome.changed:
        role_menu_counter.schedule_count_refresh(interaction.message, menu_id)


async def _handle_selection(
    interaction: discord.Interaction,
    menu_id: int,
    selected_ids: list[int],
    *,
    show_counts: bool = False,
) -> None:
    from services import reaction_role_service

    member, guild = _require_member(interaction)
    if member is None or guild is None:
        return
    outcome = await reaction_role_service.apply_selection(
        menu_id=menu_id,
        member=member,
        guild=guild,
        selected_ids=selected_ids,
    )
    await interaction.response.send_message(
        _format_outcome(guild, outcome),
        ephemeral=True,
    )
    if show_counts and outcome.changed:
        role_menu_counter.schedule_count_refresh(interaction.message, menu_id)


async def _handle_roster(
    interaction: discord.Interaction,
    view: discord.ui.View | None,
) -> None:
    """Post the ephemeral "who's in" roster for the menu behind the button.

    Reads the menu's immutable config (title + options) off the view and the live
    holders off the guild — no DB round-trip, no per-user storage.
    """
    if interaction.guild is None:
        return
    menu = getattr(view, "menu", None)
    options = getattr(view, "options", None) or []
    embed = role_menu_counter.build_roster_embed(menu, options, interaction.guild)
    await interaction.response.send_message(embed=embed, ephemeral=True)


def _require_member(
    interaction: discord.Interaction,
) -> tuple[discord.Member | None, discord.Guild | None]:
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        return None, None
    return interaction.user, interaction.guild


def _format_outcome(guild: discord.Guild, outcome) -> str:  # type: ignore[no-untyped-def]
    """Turn a service ``RoleMenuOutcome`` into an ephemeral confirmation string."""

    def names(ids: tuple[int, ...]) -> str:
        out = []
        for rid in ids:
            role = resources.resolve_role(guild, role_id=rid)
            out.append(f"**{role.name}**" if role else f"role {rid}")
        return ", ".join(out)

    parts: list[str] = []
    if outcome.added:
        parts.append(f"✅ Added {names(outcome.added)}")
    if outcome.removed:
        parts.append(f"➖ Removed {names(outcome.removed)}")
    if outcome.note:
        parts.append(f"⚠️ {outcome.note}")
    if not parts:
        return "No changes."
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Restart recovery — re-bind a fresh view to every posted menu message at boot
# ---------------------------------------------------------------------------

_REATTACHED_ONCE = False


def reset_reattach_state() -> None:
    """Clear the once-guard so the next :func:`reattach_role_menus` runs (tests)."""
    global _REATTACHED_ONCE
    _REATTACHED_ONCE = False


async def reattach_role_menus(bot: commands.Bot) -> int:
    """Re-bind a :class:`RoleMenuView` to every posted menu so clicks survive a restart.

    Mirrors ``message_anchor_manager.restore_anchors`` but keyed on the
    ``role_menus`` rows (each menu is a public, data-driven message rather than a
    per-user anchor). Idempotent: a no-op after the first call so an ``on_ready``
    re-fire on gateway reconnect doesn't double-bind.
    """
    global _REATTACHED_ONCE
    if _REATTACHED_ONCE:
        return 0
    _REATTACHED_ONCE = True

    from services import reaction_role_service

    menus = await reaction_role_service.list_posted_menus()
    restored = 0
    for menu in menus:
        message_id = menu.get("message_id")
        if not message_id:
            continue
        try:
            opts = await reaction_role_service.get_menu_options(int(menu["menu_id"]))
            options = [
                {"role_id": o.role_id, "emoji": o.emoji, "label": o.label} for o in opts
            ]
            bot.add_view(RoleMenuView(menu, options), message_id=int(message_id))
            restored += 1
        except Exception as exc:
            logger.warning(
                "reattach_role_menus: could not re-bind menu %s (msg=%s): %s",
                menu.get("menu_id"),
                message_id,
                exc,
            )
    if restored:
        logger.info("reattach_role_menus: re-bound %d role menu(s)", restored)
    return restored


__all__ = [
    "MAX_MENU_ROLES",
    "RoleMenuView",
    "build_menu_embed",
    "build_menu_message",
    "reattach_role_menus",
    "render_menu_card",
    "reset_reattach_state",
]
