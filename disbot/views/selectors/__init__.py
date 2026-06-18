"""Reusable select primitives shared by panel cogs.

These selectors are the building blocks the user-facing "dynamic-dropdown" UX
direction calls for.  Each ``attach_*`` helper attaches a *windowed* select to
a host view: any-length collections are paginated past Discord's 25-option cap
(◀/▶ nav) instead of front-truncated, so callers can pass any-length
collections without silently dropping the tail (the #1040 class).  All are thin
wrappers over :func:`views.paginated_select.attach_windowed_select`.

Public surface:
    channel.attach_channel_select       — windowed text/voice-channel picker
    role.attach_role_select             — windowed guild-role picker
    scope.ScopeSelector                 — governance scope picker (guild/category/channel)
    subsystem.attach_subsystem_select   — registered-subsystem picker
    multi.attach_multi_select           — generic windowed multi-select
    multi.attach_multi_channel_select   — windowed multi-channel picker (returns ids)
    multi_role.attach_multi_role_select — windowed multi-role picker (returns ids)

``ScopeSelector`` stays a plain ``discord.ui.Select`` — it offers at most three
fixed options (guild / category / channel), so it never needs windowing.

Adopt these instead of building bespoke ``discord.ui.Select`` widgets in cogs.
"""

from __future__ import annotations

from views.selectors.channel import attach_channel_select
from views.selectors.multi import attach_multi_channel_select, attach_multi_select
from views.selectors.multi_role import attach_multi_role_select
from views.selectors.role import attach_role_select
from views.selectors.scope import ScopeSelector
from views.selectors.subsystem import attach_subsystem_select

__all__ = [
    "ScopeSelector",
    "attach_channel_select",
    "attach_multi_channel_select",
    "attach_multi_role_select",
    "attach_multi_select",
    "attach_role_select",
    "attach_subsystem_select",
]
