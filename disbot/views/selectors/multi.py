"""Reusable multi-select primitives.

The single-select siblings in this package (channel / role / scope /
subsystem) all hard-cap ``max_values=1``.  Several admin flows are
naturally multi-target — locking a handful of channels, granting a
policy to a set of roles — and were forced into a "pick one → confirm →
reopen" loop (repo-wide audit 2026-05-29, §5 / §9.1, finding **P1-10**).

``MultiSelect`` is the generic primitive: pass pre-built options and an
async ``on_select`` that receives the list of chosen values.
``MultiChannelSelector`` is the channel-typed convenience built on top,
mirroring :class:`channel.ChannelSelector` but returning *every*
selected id.

Discord caps Select options at 25 and ``max_values`` at the number of
options it sees; both are enforced here so callers can pass any-length
collections without crashing the payload.  An empty option list falls
back to a single placeholder entry (the same empty-guard the
``RoleSelector`` / ``SubsystemSelector`` carry) so the widget never
raises on a guild with nothing to show.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any

import discord

# Async callbacks: generic returns the chosen option ``value`` strings;
# the channel convenience returns parsed integer ids.
OnSelectValues = Callable[[discord.Interaction, list[str]], Awaitable[None]]
OnSelectIds = Callable[[discord.Interaction, list[int]], Awaitable[None]]

# Sentinel option used when the caller passes zero options.  Its value is
# the empty string so ``MultiSelect.callback`` can filter it back out and
# never hand a phantom selection to the caller.
_EMPTY_VALUE = ""
_EMPTY_OPTION = discord.SelectOption(label="— nothing available —", value=_EMPTY_VALUE)


class MultiSelect(discord.ui.Select):
    """Multi-select over caller-supplied options.

    Parameters
    ----------
    options:
        Any iterable of :class:`discord.SelectOption`.  Truncated to 25.
    on_select:
        Awaitable invoked with ``(interaction, values)`` — ``values`` is
        the list of chosen option ``value`` strings (possibly empty when
        ``min_values=0`` and the user clears the menu).  The caller must
        reply or defer.
    min_values / max_values:
        Selection bounds.  ``max_values`` defaults to "all options" (the
        whole point of a multi-select) and is clamped to the option
        count so Discord never rejects the payload.
    placeholder / custom_id / row:
        As per :class:`discord.ui.Select`.  For persistent panels pass an
        explicit ``<subsystem>:<action>`` ``custom_id``.
    """

    def __init__(
        self,
        options: Iterable[discord.SelectOption],
        on_select: OnSelectValues,
        *,
        placeholder: str = "Select one or more…",
        min_values: int = 0,
        max_values: int | None = None,
        custom_id: str | None = None,
        row: int | None = None,
    ) -> None:
        bounded = list(options)[:25]
        # Discord rejects a Select with zero options.
        effective = bounded or [_EMPTY_OPTION]
        # max_values must not exceed the number of options Discord sees;
        # default to selecting all of them.
        cap = max_values if max_values is not None else len(effective)
        cap = max(1, min(cap, len(effective)))
        # dict[str, Any] (not object) so **kwargs unpacks into Select.__init__
        # without mypy demanding str|int|list|bool per declared param.
        kwargs: dict[str, Any] = {
            "placeholder": placeholder,
            "options": effective,
            "min_values": max(0, min(min_values, cap)),
            "max_values": cap,
        }
        if custom_id is not None:
            kwargs["custom_id"] = custom_id
        if row is not None:
            kwargs["row"] = row
        super().__init__(**kwargs)
        self._on_select = on_select

    async def callback(self, interaction: discord.Interaction) -> None:
        # Drop the empty-guard sentinel so callers never see a phantom "".
        values = [v for v in self.values if v != _EMPTY_VALUE]
        await self._on_select(interaction, values)


class MultiChannelSelector(MultiSelect):
    """Multi-select text/voice-channel picker returning every chosen id.

    Mirrors :class:`channel.ChannelSelector` (which is single-select) for
    flows that act on several channels at once.  ``on_select`` receives a
    list of channel ids; unparseable values are skipped defensively.
    """

    def __init__(
        self,
        channels: Iterable[discord.abc.GuildChannel],
        on_select: OnSelectIds,
        *,
        placeholder: str = "Select one or more channels…",
        min_values: int = 1,
        max_values: int | None = None,
        custom_id: str | None = None,
        row: int | None = None,
    ) -> None:
        bounded = list(channels)[:25]
        options = [
            discord.SelectOption(label=f"#{ch.name}"[:100], value=str(ch.id))
            for ch in bounded
        ]
        super().__init__(
            options,
            self._dispatch_ids,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            custom_id=custom_id,
            row=row,
        )
        self._id_on_select = on_select

    async def _dispatch_ids(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        ids: list[int] = []
        for v in values:
            try:
                ids.append(int(v))
            except ValueError:
                continue
        await self._id_on_select(interaction, ids)
