"""Reusable paginated single/multi select — windows a long option list.

Discord caps a ``Select`` at 25 options.  A list longer than that was
historically front-truncated with ``options[:25]``, which silently dropped
every option past the 25th so the user could never pick it (the #1040
"select-option truncation" class flagged by ``scripts/check_consistency.py``).

:class:`PaginatedSelectView` windows the *full* option list into ≤25-option
pages with ◀ Prev / Next ▶ navigation, so every option stays reachable.  It
generalises the two bespoke windowing implementations that predated it —
``views/setup/sections/cog_routing.py`` ``_CogPickView`` and
``views/help/editor.py`` ``EntityPickerView`` — into one primitive.

Like :mod:`views.navigation`, this module is intentionally small: one view
class plus its two private item helpers, no framework.

Usage::

    async def _picked(interaction, values):
        await interaction.response.send_message(f"You chose {values[0]}", ephemeral=True)

    view = PaginatedSelectView(
        interaction.user,
        [discord.SelectOption(label=r.name, value=str(r.id)) for r in roles],
        _picked,
        placeholder="Pick a role…",
    )
    await interaction.response.send_message("Pick a role:", view=view, ephemeral=True)

Caveat — *multi*-select across pages: ``max_values`` is clamped to the option
count of the *current* page (Discord rejects ``max_values`` larger than the
visible option count), and a selection does not carry across a page flip.  The
primitive is therefore best for single-select "pick one from a long list"
flows; a true multi-page multi-select would need a running tally and is out of
scope here.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

import discord

from views.base import BaseView

# Async callback: receives the chosen option ``value`` strings.  Single-select
# callers read ``values[0]``; the callback must reply to or defer the interaction.
OnSelect = Callable[[discord.Interaction, list[str]], Awaitable[None]]

# Discord's hard cap on Select options / the default window size.
MAX_OPTIONS = 25

# Sentinel option shown when the caller passes zero options.  The select is
# disabled in that case so the sentinel can never be chosen.
_EMPTY_VALUE = "\x00empty"


class _WindowSelect(discord.ui.Select):
    """One page's worth of options.  Owned and re-built by the parent view."""

    def __init__(
        self,
        options: list[discord.SelectOption],
        *,
        placeholder: str,
        min_values: int,
        max_values: int,
        page: int,
        page_count: int,
    ) -> None:
        disabled = False
        if not options:
            options = [
                discord.SelectOption(label="— nothing available —", value=_EMPTY_VALUE),
            ]
            disabled = True
        if page_count > 1:
            placeholder = f"{placeholder} — page {page + 1}/{page_count}"
        # Discord rejects max_values larger than the visible option count.
        cap = max(1, min(max_values, len(options)))
        kwargs: dict[str, Any] = {
            "placeholder": placeholder[:150],
            "options": options,
            "min_values": max(0, min(min_values, cap)),
            "max_values": cap,
            "disabled": disabled,
        }
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if isinstance(view, PaginatedSelectView):
            await view._dispatch(interaction, list(self.values))


class _PageButton(discord.ui.Button):
    """◀ Prev / Next ▶ nav for the windowed select."""

    def __init__(self, *, delta: int, label: str, disabled: bool, row: int) -> None:
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label,
            disabled=disabled,
            row=row,
        )
        self._delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if isinstance(view, PaginatedSelectView):
            await view._change_page(interaction, self._delta)


class PaginatedSelectView(BaseView):
    """A windowed single/multi select over an arbitrarily long option list.

    Renders one ≤``page_size``-option select; when the list spans more than one
    page it also renders ◀ Prev / Next ▶ buttons that re-window the select in
    place.  Optional ``extra_items`` (e.g. a Back button) are preserved across
    page flips.

    Parameters
    ----------
    author:
        Passed to :class:`BaseView` for invoker restriction.
    options:
        Any-length sequence of :class:`discord.SelectOption`.
    on_select:
        Awaitable invoked with ``(interaction, values)`` once the user picks;
        ``values`` is the list of chosen option ``value`` strings.  The
        callback owns the interaction response.
    placeholder / min_values / max_values:
        As per :class:`discord.ui.Select` (``max_values`` is clamped per page —
        see the module docstring caveat).
    page_size:
        Options per page; clamped to ``1..25``.
    extra_items:
        Items re-added after the select + nav on every render (survive paging).
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        options: Sequence[discord.SelectOption],
        on_select: OnSelect,
        *,
        placeholder: str = "Select…",
        min_values: int = 1,
        max_values: int = 1,
        page_size: int = MAX_OPTIONS,
        extra_items: Sequence[discord.ui.Item[Any]] | None = None,
        public: bool = False,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self._options = list(options)
        self._on_select = on_select
        self._placeholder = placeholder
        self._min_values = min_values
        self._max_values = max_values
        self._page_size = max(1, min(page_size, MAX_OPTIONS))
        self._extra_items = list(extra_items or [])
        self._page = 0
        self._render()

    @property
    def page_count(self) -> int:
        if not self._options:
            return 1
        return -(-len(self._options) // self._page_size)  # ceil division

    def _page_options(self) -> list[discord.SelectOption]:
        start = self._page * self._page_size
        return self._options[start : start + self._page_size]

    def _render(self) -> None:
        self.clear_items()
        page_count = self.page_count
        nav_row = 1
        self.add_item(
            _WindowSelect(
                self._page_options(),
                placeholder=self._placeholder,
                min_values=self._min_values,
                max_values=self._max_values,
                page=self._page,
                page_count=page_count,
            ),
        )
        if page_count > 1:
            self.add_item(
                _PageButton(
                    delta=-1,
                    label="◀ Prev",
                    disabled=self._page == 0,
                    row=nav_row,
                ),
            )
            self.add_item(
                _PageButton(
                    delta=1,
                    label="Next ▶",
                    disabled=self._page >= page_count - 1,
                    row=nav_row,
                ),
            )
        for item in self._extra_items:
            self.add_item(item)

    async def _change_page(self, interaction: discord.Interaction, delta: int) -> None:
        self._page = max(0, min(self._page + delta, self.page_count - 1))
        self._render()
        await interaction.response.edit_message(view=self)

    async def _dispatch(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        # Defensive: the disabled empty-state sentinel can never reach here, but
        # filter it anyway so a caller never sees a phantom value.
        clean = [v for v in values if v != _EMPTY_VALUE]
        await self._on_select(interaction, clean)


__all__ = [
    "MAX_OPTIONS",
    "OnSelect",
    "PaginatedSelectView",
]
