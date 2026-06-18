"""Reusable multi-select primitives.

The single-select siblings in this package (channel / role / scope /
subsystem) all hard-cap selection at one.  Several admin flows are naturally
multi-target — locking a handful of channels, granting a policy to a set of
roles — and were forced into a "pick one → confirm → reopen" loop (repo-wide
audit 2026-05-29, §5 / §9.1, finding **P1-10**).

:func:`attach_multi_select` is the generic primitive: attach a *windowed*
multi-select over caller-supplied options to a host view, with an async
``on_select`` that receives the list of chosen values.
:func:`attach_multi_channel_select` is the channel-typed convenience built on
top, mirroring :func:`views.selectors.channel.attach_channel_select` but
returning *every* selected id.

Both paginate past Discord's 25-option cap (◀/▶ nav) instead of front-truncating
(the #1040 class), so callers can pass any-length collections.

Caveat — *multi*-select across pages: ``max_values`` is clamped to the current
page's option count and a selection does not carry across a page flip (see
:mod:`views.paginated_select`).  For ≤25 options this is a single page and
behaves exactly like a plain multi-select; for longer lists the user pages to
reach every option and acts per page.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable

import discord

from views.paginated_select import MAX_OPTIONS, SelectWindow, attach_windowed_select

# Async callbacks: generic returns the chosen option ``value`` strings;
# the channel convenience returns parsed integer ids.
OnSelectValues = Callable[[discord.Interaction, list[str]], Awaitable[None]]
OnSelectIds = Callable[[discord.Interaction, list[int]], Awaitable[None]]


def attach_multi_select(
    view: discord.ui.View,
    options: Iterable[discord.SelectOption],
    on_select: OnSelectValues,
    *,
    placeholder: str = "Select one or more…",
    min_values: int = 0,
    max_values: int | None = None,
    select_row: int | None = None,
    nav_row: int | None = None,
) -> SelectWindow:
    """Attach a windowed multi-select over caller options to ``view``.

    Parameters
    ----------
    options:
        Any iterable of :class:`discord.SelectOption`; paginated past 25.
    on_select:
        Awaitable invoked with ``(interaction, values)`` — ``values`` is the
        list of chosen option ``value`` strings (the windowing layer filters
        its empty-state sentinel).  The caller must reply or defer.
    min_values / max_values:
        Selection bounds.  ``max_values=None`` (default) selects "all on the
        current page"; the windowing layer clamps it to the page option count.
    select_row / nav_row:
        Optional explicit action-rows for the embedding host's row budget.
    """
    cap = MAX_OPTIONS if max_values is None else max_values
    return attach_windowed_select(
        view,
        list(options),
        on_select,
        placeholder=placeholder,
        min_values=min_values,
        max_values=cap,
        select_row=select_row,
        nav_row=nav_row,
    )


def attach_multi_channel_select(
    view: discord.ui.View,
    channels: Iterable[discord.abc.GuildChannel],
    on_select: OnSelectIds,
    *,
    placeholder: str = "Select one or more channels…",
    min_values: int = 1,
    max_values: int | None = None,
    select_row: int | None = None,
    nav_row: int | None = None,
) -> SelectWindow:
    """Attach a windowed multi-channel picker returning every chosen id.

    Mirrors :func:`views.selectors.channel.attach_channel_select` (single) for
    flows that act on several channels at once.  ``on_select`` receives a list
    of channel ids; unparseable values are skipped defensively.
    """
    options = [
        discord.SelectOption(label=f"#{ch.name}"[:100], value=str(ch.id))
        for ch in channels
    ]

    async def _dispatch_ids(
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        ids: list[int] = []
        for v in values:
            try:
                ids.append(int(v))
            except ValueError:
                continue
        await on_select(interaction, ids)

    return attach_multi_select(
        view,
        options,
        _dispatch_ids,
        placeholder=placeholder,
        min_values=min_values,
        max_values=max_values,
        select_row=select_row,
        nav_row=nav_row,
    )
