"""Typed accessors for the ``core.runtime.guild_config`` cache.

Every consumer of ``guild_config`` MUST import its accessor from this
module rather than calling ``guild_config.get(...)`` with a bare string
key.  Enforced by the AST invariant at
``tests/unit/invariants/test_guild_config_typed_accessors.py``.

The discipline:

    Cogs / views / services
        ↓
    utils.guild_config_accessors          ← canonical key strings live here
        ↓
    core.runtime.guild_config             ← the primitive

Each accessor owns:

  * a single canonical key string,
  * the typed return shape (dataclass / NamedTuple),
  * the loader callable that fetches from authoritative state on miss,
  * and the invalidation entry point its admin write paths call into.

This module is intentionally empty in Phase S1.1 — it scaffolds the
discipline so the first migration in Phase S2.2 (XP listener) has an
obvious home for ``get_xp_config`` + ``invalidate_xp_config``.  Future
cogs add their accessors here as they migrate off ``db.get_setting``
hot-path calls.
"""

from __future__ import annotations

__all__: list[str] = []
