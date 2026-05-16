"""Per-game DB submodules.

Each game owns its own table CRUD module here.  Note that *blackjack*
does not have a dedicated table — it uses the shared ``xp.coins`` column
via :mod:`utils.db.economy` for balance state and ``guild_settings`` for
tournament metadata.
"""
