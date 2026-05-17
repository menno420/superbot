"""Diagnostic subsystem — shared helpers (S4.4.5 stabilization).

See ``docs/architecture.md`` §"Subsystem decomposition" for the layout
convention.  Modules in this package are pure-ish: they build embeds
and read from ``bot`` / ``db`` but do not perform Discord channel I/O
themselves (the cog commands and view callbacks handle the send/edit).

Modules:
    _helpers  — embed/page builders shared by ``cogs/diagnostic_cog.py``
                and ``views/diagnostic/*`` (S4.4.5-followup stabilization;
                resolves the panel→ctx.invoke regression where the hub
                view delegated to text commands and produced orphaned
                messages instead of editing the panel in place).
"""
