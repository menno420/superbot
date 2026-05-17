"""Mining subsystem — domain logic (S4.1).

See ``docs/architecture.md`` §"Subsystem decomposition" for the layout
convention.  Domain modules in this package are pure: no Discord,
no views.  The cog file ``cogs/mining_cog.py`` and views in
``views/mining/`` consume these helpers.

Modules:
    recipes  — JSON-driven structure recipes
    rewards  — mining loot tables + explore outcomes
"""
