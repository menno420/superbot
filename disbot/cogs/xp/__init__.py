"""XP subsystem — domain logic (S4.2).

See ``docs/architecture.md`` §"Subsystem decomposition" for the layout
convention.  Modules in this package are pure-ish: they call DB +
service primitives but no Discord-API I/O outside of the on_message
listener body itself.

Modules:
    listener  — on_message handler + level-up announcement + role assignment
"""
