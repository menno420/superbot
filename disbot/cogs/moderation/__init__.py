"""Moderation subsystem — domain helpers (S4.3).

See ``docs/architecture.md`` §"Subsystem decomposition" for the layout
convention.  Modules in this package are pure-ish: they take a
``discord.Interaction`` or values derived from it and never perform
Discord-API I/O themselves.

Modules:
    _helpers  — mod-panel embed builder + interaction-time permission check
                (shared by ``cogs/moderation_cog.py`` and ``views/moderation/*``)
"""
