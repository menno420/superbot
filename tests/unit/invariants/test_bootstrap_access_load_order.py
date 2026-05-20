"""Invariant: ``cogs.bootstrap_access_cog`` must load before any other cog.

The bootstrap cog replaces the legacy ``_channel_guard`` from
``bot1.py`` with a fresh-guild-aware guard.  If any other cog were to
load first, its commands could still be blocked by the legacy guard
before the replacement runs, stranding operators in a new guild.

The order is enforced via ``config.INITIAL_EXTENSIONS``.  These tests
pin that order so reorders during refactors are caught at CI time.
"""

from __future__ import annotations

import config


def test_bootstrap_access_cog_is_in_initial_extensions() -> None:
    assert "cogs.bootstrap_access_cog" in config.INITIAL_EXTENSIONS, (
        "cogs.bootstrap_access_cog must be present in config.INITIAL_EXTENSIONS "
        "so the fresh-guild channel guard replaces the legacy one at boot."
    )


def test_bootstrap_access_cog_loads_first() -> None:
    assert config.INITIAL_EXTENSIONS[0] == "cogs.bootstrap_access_cog", (
        "cogs.bootstrap_access_cog must be the FIRST entry in "
        "config.INITIAL_EXTENSIONS so its setup() runs before any other cog's "
        "commands could be blocked by the legacy _channel_guard."
    )


def test_bootstrap_access_cog_precedes_admin_cog() -> None:
    bootstrap_index = config.INITIAL_EXTENSIONS.index("cogs.bootstrap_access_cog")
    admin_index = config.INITIAL_EXTENSIONS.index("cogs.admin_cog")
    assert bootstrap_index < admin_index, (
        "cogs.bootstrap_access_cog must load before cogs.admin_cog so the "
        "fresh-guild guard is installed before admin entry points are "
        "registered (PR #220)."
    )


def test_bootstrap_access_cog_listed_once() -> None:
    occurrences = [
        ext for ext in config.INITIAL_EXTENSIONS if ext == "cogs.bootstrap_access_cog"
    ]
    assert len(occurrences) == 1, (
        "cogs.bootstrap_access_cog must appear exactly once in "
        "config.INITIAL_EXTENSIONS; duplicate entries would cause the "
        "fresh-guild guard installer to run twice and double-remove."
    )
