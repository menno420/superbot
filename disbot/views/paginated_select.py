"""Reusable paginated single/multi select — windows a long option list.

Discord caps a ``Select`` at 25 options.  A list longer than that was
historically front-truncated with ``options[:25]``, which silently dropped
every option past the 25th so the user could never pick it (the #1040
"select-option truncation" class flagged by ``scripts/check_consistency.py``).

The windowing core is :class:`SelectWindow`: a controller that owns a *band*
of items — a windowed ``Select`` plus ◀ Prev / Next ▶ nav — and re-windows
them in place.  Two ways to use it:

* :class:`PaginatedSelectView` — a self-contained :class:`BaseView` that owns a
  single ``SelectWindow`` (plus optional ``extra_items`` like a Back button).
  Best for a *standalone* "pick one from a long list" ephemeral.

* :func:`attach_windowed_select` — attaches a ``SelectWindow`` to **any host
  view** that already carries other controls.  On a page flip the window
  removes only *its own* items and re-adds the new page, so the host's other
  buttons/selects survive untouched.  This is the **embedded** path for a
  multi-control panel whose select would otherwise front-truncate.

Both share the same ``_WindowSelect`` / ``_PageButton`` items and the same page
math, so there is one windowing implementation to reason about.

Usage (standalone)::

    async def _picked(interaction, values):
        await interaction.response.send_message(f"You chose {values[0]}", ephemeral=True)

    view = PaginatedSelectView(
        interaction.user,
        [discord.SelectOption(label=r.name, value=str(r.id)) for r in roles],
        _picked,
        placeholder="Pick a role…",
    )
    await interaction.response.send_message("Pick a role:", view=view, ephemeral=True)

Usage (embedded, inside a panel that already has buttons)::

    class MyPanel(BaseView):
        def __init__(self, author, things, on_pick):
            super().__init__(author)
            attach_windowed_select(
                self,
                [discord.SelectOption(label=t.name, value=t.id) for t in things],
                on_pick,
                placeholder="Pick a thing…",
                nav_row=4,  # share the row budget with the panel's buttons
            )
            self.add_item(MyOtherButton())

Caveat — *multi*-select across pages: ``max_values`` is clamped to the option
count of the *current* page (Discord rejects ``max_values`` larger than the
visible option count), and a selection does not carry across a page flip.  The
window is therefore best for single-select "pick one from a long list" flows;
a true multi-page multi-select would need a running tally and is out of scope.
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
    """One page's worth of options.  Owned and re-built by a :class:`SelectWindow`."""

    def __init__(
        self,
        options: list[discord.SelectOption],
        window: SelectWindow,
        *,
        placeholder: str,
        min_values: int,
        max_values: int,
        page: int,
        page_count: int,
        row: int | None = None,
    ) -> None:
        self._window = window
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
        if row is not None:
            kwargs["row"] = row
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._window._dispatch(interaction, list(self.values))


class _PageButton(discord.ui.Button):
    """◀ Prev / Next ▶ nav for a :class:`SelectWindow`."""

    def __init__(
        self,
        window: SelectWindow,
        *,
        delta: int,
        label: str,
        disabled: bool,
        row: int | None,
    ) -> None:
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label,
            disabled=disabled,
            row=row,
        )
        self._window = window
        self._delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._window._change_page(interaction, self._delta)


class SelectWindow:
    """Windowing controller for an arbitrarily long option list.

    Owns a *band* of items — one ≤``page_size``-option :class:`_WindowSelect`
    plus, when the list spans more than one page, ◀ Prev / Next ▶ buttons —
    attached to a host :class:`discord.ui.View`.  On a page flip it removes
    **only its own** items from the host and re-adds the new page, leaving any
    other controls the host carries untouched.

    Use :func:`attach_windowed_select` for the common case;
    :class:`PaginatedSelectView` owns one of these internally.

    Parameters
    ----------
    options:
        Any-length sequence of :class:`discord.SelectOption`.
    on_select:
        Awaitable invoked with ``(interaction, values)`` once the user picks;
        ``values`` is the list of chosen option ``value`` strings.  The
        callback owns the interaction response.
    placeholder / min_values / max_values:
        As per :class:`discord.ui.Select` (``max_values`` is clamped per page).
    page_size:
        Options per page; clamped to ``1..25``.
    select_row / nav_row:
        Optional explicit action-rows for the select and the nav buttons, so an
        embedding host can fit them into its own row budget (Discord allows 5
        rows; a select occupies a whole row, buttons share one).
    """

    def __init__(
        self,
        options: Sequence[discord.SelectOption],
        on_select: OnSelect,
        *,
        placeholder: str = "Select…",
        min_values: int = 1,
        max_values: int = 1,
        page_size: int = MAX_OPTIONS,
        select_row: int | None = None,
        nav_row: int | None = None,
    ) -> None:
        self._options = list(options)
        self._on_select = on_select
        self._placeholder = placeholder
        self._min_values = min_values
        self._max_values = max_values
        self._page_size = max(1, min(page_size, MAX_OPTIONS))
        self._select_row = select_row
        self._nav_row = nav_row
        self._page = 0
        self._view: discord.ui.View | None = None
        self._items: list[discord.ui.Item[Any]] = []

    @property
    def page(self) -> int:
        return self._page

    @page.setter
    def page(self, value: int) -> None:
        self._page = max(0, min(value, self.page_count - 1))

    @property
    def page_count(self) -> int:
        if not self._options:
            return 1
        return -(-len(self._options) // self._page_size)  # ceil division

    def page_options(self) -> list[discord.SelectOption]:
        start = self._page * self._page_size
        return self._options[start : start + self._page_size]

    def attach(self, view: discord.ui.View) -> SelectWindow:
        """Bind to ``view`` and render the current page's band into it."""
        self._view = view
        self.render()
        return self

    def render(self) -> None:
        """(Re)build the window's item band on the bound host view in place."""
        if self._view is None:  # pragma: no cover - defensive
            raise RuntimeError("SelectWindow.render() before attach()")
        for item in self._items:
            try:
                self._view.remove_item(item)
            except ValueError:  # pragma: no cover - item already gone
                pass
        self._items = []

        page_count = self.page_count
        select = _WindowSelect(
            self.page_options(),
            self,
            placeholder=self._placeholder,
            min_values=self._min_values,
            max_values=self._max_values,
            page=self._page,
            page_count=page_count,
            row=self._select_row,
        )
        self._view.add_item(select)
        self._items.append(select)

        if page_count > 1:
            prev_btn = _PageButton(
                self,
                delta=-1,
                label="◀ Prev",
                disabled=self._page == 0,
                row=self._nav_row,
            )
            next_btn = _PageButton(
                self,
                delta=1,
                label="Next ▶",
                disabled=self._page >= page_count - 1,
                row=self._nav_row,
            )
            self._view.add_item(prev_btn)
            self._view.add_item(next_btn)
            self._items.extend((prev_btn, next_btn))

    def detach(self) -> None:
        """Remove the window's item band from its host view.

        For a host that rebuilds the option list (e.g. after a mutation): call
        ``detach()`` on the old window, then :func:`attach_windowed_select` a
        fresh one with the new options.  No-op if never attached.
        """
        if self._view is None:
            return
        for item in self._items:
            try:
                self._view.remove_item(item)
            except ValueError:  # pragma: no cover - item already gone
                pass
        self._items = []

    async def _change_page(self, interaction: discord.Interaction, delta: int) -> None:
        self.page = self._page + delta
        self.render()
        await interaction.response.edit_message(view=self._view)

    async def _dispatch(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        # Defensive: the disabled empty-state sentinel can never reach here, but
        # filter it anyway so a caller never sees a phantom value.
        clean = [v for v in values if v != _EMPTY_VALUE]
        await self._on_select(interaction, clean)


def attach_windowed_select(
    view: discord.ui.View,
    options: Sequence[discord.SelectOption],
    on_select: OnSelect,
    *,
    placeholder: str = "Select…",
    min_values: int = 1,
    max_values: int = 1,
    page_size: int = MAX_OPTIONS,
    select_row: int | None = None,
    nav_row: int | None = None,
) -> SelectWindow:
    """Attach a windowed select (+ ◀/▶ nav when needed) to ``view``.

    The embedded counterpart to :class:`PaginatedSelectView`: drop a paginated
    select into a panel that already carries other controls without the long
    option list front-truncating.  Returns the :class:`SelectWindow` (held by
    the caller only if it needs to inspect/re-render it; the band is already
    live on ``view``).
    """
    return SelectWindow(
        options,
        on_select,
        placeholder=placeholder,
        min_values=min_values,
        max_values=max_values,
        page_size=page_size,
        select_row=select_row,
        nav_row=nav_row,
    ).attach(view)


class PaginatedSelectView(BaseView):
    """A standalone windowed single/multi select over a long option list.

    Owns one :class:`SelectWindow`; optional ``extra_items`` (e.g. a Back
    button) are added once and survive page flips because the window only
    re-renders its own band.

    Parameters
    ----------
    author:
        Passed to :class:`BaseView` for invoker restriction.
    options:
        Any-length sequence of :class:`discord.SelectOption`.
    on_select:
        Awaitable invoked with ``(interaction, values)`` once the user picks.
    placeholder / min_values / max_values / page_size:
        Forwarded to :class:`SelectWindow`.
    extra_items:
        Items added after the window's band (survive paging).
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
        self._window = SelectWindow(
            options,
            on_select,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            page_size=page_size,
            select_row=0,
            nav_row=1,
        )
        self._window.attach(self)
        for item in extra_items or []:
            self.add_item(item)

    @property
    def page_count(self) -> int:
        return self._window.page_count


__all__ = [
    "MAX_OPTIONS",
    "OnSelect",
    "PaginatedSelectView",
    "SelectWindow",
    "attach_windowed_select",
]
