"""Reusable UI component primitives for the SuperBot platform.

These functions produce Discord embed and view building blocks that cogs
compose into panels.  They are the canonical vocabulary for all SuperBot UIs.

Public surface:
    stats_block(title, fields, color, ...)        → discord.Embed
    progress_bar(current, maximum, width)         → str
    paginated_list(items, page, page_size)        → tuple[list[str], int]
    ActionDef                                     — button descriptor dataclass
    resolve_action_states(interaction, actions)   → list[ActionDef]
    add_actions_to_view(view, actions, callbacks) → None
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import discord


@dataclass
class ActionDef:
    """Descriptor for one action button in an action grid.

    Set capability to a governance capability string to enable automatic
    governance gating — resolve_action_states() will mark the button disabled
    if the user lacks that capability.  None means always enabled.
    """

    label: str
    custom_id: str
    style: discord.ButtonStyle = discord.ButtonStyle.secondary
    emoji: str | None = None
    capability: str | None = None
    row: int = 0
    disabled: bool = False


def stats_block(
    title: str,
    fields: list[tuple[str, str, bool]],
    color: int,
    *,
    description: str | None = None,
    footer: str | None = None,
    thumbnail_url: str | None = None,
) -> discord.Embed:
    """Build a labeled key-value embed.

    Args:
        title: Embed title.
        fields: List of (name, value, inline) tuples.
        color: Integer color value.
        description: Optional embed description.
        footer: Optional footer text.
        thumbnail_url: Optional thumbnail image URL.
    """
    embed = discord.Embed(title=title, color=color, description=description)
    for name, value, inline in fields:
        embed.add_field(name=name, value=value or "​", inline=inline)
    if footer:
        embed.set_footer(text=footer)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    return embed


def progress_bar(
    current: int | float,
    maximum: int | float,
    width: int = 10,
    *,
    fill: str = "█",
    empty: str = "░",
) -> str:
    """Return a Unicode block progress bar, e.g. ``█████░░░░░ 50%``."""
    if maximum <= 0:
        return empty * width + " 0%"
    ratio = min(1.0, current / maximum)
    filled = round(ratio * width)
    bar = fill * filled + empty * (width - filled)
    return f"{bar} {ratio:.0%}"


def paginated_list(
    items: list[str],
    page: int,
    page_size: int = 10,
) -> tuple[list[str], int]:
    """Return ``(items_on_page, total_pages)`` for the requested page.

    Page index is 0-based.  Out-of-range pages are clamped to valid bounds.
    An empty ``items`` list returns ``([], 1)`` so callers always have a page count.
    """
    if not items:
        return [], 1
    total = max(1, math.ceil(len(items) / page_size))
    page = max(0, min(page, total - 1))
    start = page * page_size
    return items[start : start + page_size], total


async def resolve_action_states(
    interaction: discord.Interaction,
    actions: list[ActionDef],
) -> list[ActionDef]:
    """Return copies of *actions* with ``.disabled`` set via governance checks.

    Actions whose ``capability`` is ``None`` are passed through unchanged.
    Actions whose ``disabled`` is already ``True`` are not re-checked.
    """
    from core.runtime import ui_permissions

    result: list[ActionDef] = []
    for action in actions:
        disabled = action.disabled
        if not disabled and action.capability:
            allowed = await ui_permissions.can_execute(interaction, action.capability)
            disabled = not allowed
        result.append(
            ActionDef(
                label=action.label,
                custom_id=action.custom_id,
                style=action.style,
                emoji=action.emoji,
                capability=action.capability,
                row=action.row,
                disabled=disabled,
            ),
        )
    return result


def add_actions_to_view(
    view: discord.ui.View,
    actions: list[ActionDef],
    callbacks: dict[str, Callable[..., Any]],
) -> None:
    """Add button items to *view*, wiring callbacks by ``custom_id``.

    Buttons whose ``custom_id`` has no matching callback are added as
    inert display buttons (useful for disabled / label-only slots).
    """
    for action in actions:
        btn: discord.ui.Button = discord.ui.Button(
            label=action.label,
            custom_id=action.custom_id,
            style=action.style,
            emoji=action.emoji,
            disabled=action.disabled,
            row=action.row,
        )
        cb = callbacks.get(action.custom_id)
        if cb is not None:
            btn.callback = cb  # type: ignore[method-assign]
        view.add_item(btn)
