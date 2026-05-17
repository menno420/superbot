"""SuperBot cog package — subsystem entry points.

Each ``<name>_cog.py`` in this directory is a discord.py extension
loaded by ``bot1._load_cogs``.  Cogs are **thin dispatchers**: they
host commands, listeners, and (optionally) a ``PersistentView``
entry point.

When a cog grows past ~400 LOC it MUST be decomposed per the
convention in ``docs/architecture.md`` §"Subsystem decomposition":

    cogs/<name>_cog.py    entry-point: commands, listeners, persistent panel
    cogs/<name>/          domain logic (pure, no Discord, no views)
    views/<name>/         UI components (panels, modals, selectors)
    services/<name>_*     cross-subsystem audited mutation (only when needed)

The reference implementation is ``role_cog.py`` + ``views/roles/*``.
Partial decomposition reference: ``counting_cog.py`` +
``cogs/counting/``.

Related architecture sections:

* §"Where to add a new subsystem"     — onboarding checklist
* §"Subsystem decomposition"          — splitting checklist + ownership rules
* §"PersistentView placement"         — Pattern A vs Pattern B
* §"Realtime / event-driven systems"  — mandatory V/M/A pattern for
  cogs whose ``on_message`` or callbacks mutate shared in-process state
* §"State classification"             — which state class a value belongs to
"""
