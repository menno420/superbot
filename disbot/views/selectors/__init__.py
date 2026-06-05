"""Reusable ``discord.ui.Select`` primitives shared by panel cogs.

These selectors are the building blocks the user-facing
"dynamic-dropdown" UX direction calls for.  Each accepts an async
``on_select`` callback and handles Discord's 25-option cap so callers
can pass any-length collections without thinking about pagination.

Public surface:
    channel.ChannelSelector     — text-channel picker
    role.RoleSelector           — guild-role picker
    scope.ScopeSelector         — governance scope picker (guild/category/channel)
    subsystem.SubsystemSelector — registered-subsystem picker
    multi.MultiSelect           — generic multi-select over caller options
    multi.MultiChannelSelector  — multi-select channel picker (returns ids)
    multi_role.MultiRoleSelector — multi-select role picker (returns ids)

Adopt these instead of building bespoke ``discord.ui.Select`` widgets
in cogs.  Adoption is mechanical: replace the local Select subclass
with a configured selector that calls back into the cog's handler.
"""

from __future__ import annotations

from views.selectors.channel import ChannelSelector
from views.selectors.multi import MultiChannelSelector, MultiSelect
from views.selectors.multi_role import MultiRoleSelector
from views.selectors.role import RoleSelector
from views.selectors.scope import ScopeSelector
from views.selectors.subsystem import SubsystemSelector

__all__ = [
    "ChannelSelector",
    "MultiChannelSelector",
    "MultiRoleSelector",
    "MultiSelect",
    "RoleSelector",
    "ScopeSelector",
    "SubsystemSelector",
]
