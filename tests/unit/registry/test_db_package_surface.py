"""S1 regression — verify the utils.db package preserves its public surface.

The original utils/db.py was a single 1400-LOC module; S1 split it into
a package with per-feature submodules.  These tests guard the import
contract: callers that used ``from utils import db`` plus ``db.func(...)``
or ``from utils.db import func`` must continue to resolve every
historical public name.
"""

from __future__ import annotations

import pytest

# Symbols that have always been part of utils.db's public surface and
# must continue to be importable through the package root.
_EXPECTED_PUBLIC = [
    # pool lifecycle + generic primitives
    "init",
    "close",
    "get",
    "fetchone",
    "fetchall",
    "execute",
    # xp
    "xp_for_level",
    "level_progress",
    "get_xp",
    "add_xp",
    # settings
    "get_setting",
    "set_setting",
    # roles
    "get_role_thresholds",
    "set_role_threshold",
    "remove_role_threshold",
    "get_xp_threshold_roles",
    "set_role_xp_threshold",
    "add_reaction_role",
    "remove_reaction_role",
    "get_reaction_role",
    "get_all_reaction_roles",
    # moderation
    "get_warnings",
    "add_warning",
    "clear_warnings",
    "log_mod_action",
    "get_mod_logs",
    "get_prohibited_words",
    "add_prohibited_word",
    "remove_prohibited_word",
    # economy
    "get_coins",
    "add_coins",
    "set_coins",
    "get_economy",
    "claim_daily_if_ready",
    "set_daily_claim",
    "set_last_worked",
    "get_job_times",
    "increment_job",
    # inventory
    "get_inventory",
    "add_item",
    "has_item",
    # governance
    "get_subsystem_visibility",
    "get_all_visibility_for_guild",
    "get_visibility_override",
    "set_subsystem_visibility",
    "get_cleanup_policy",
    "get_all_cleanup_for_guild",
    "set_cleanup_policy",
    "write_governance_audit",
    # sessions
    "get_or_create_session",
    "touch_session",
    "get_session",
    "delete_session",
    "delete_sessions_for_guild",
    "delete_sessions_for_subsystem",
    "delete_sessions_for_scope",
    "get_session_state",
    "set_session_state",
    "set_session_state_many",
    "delete_session_state",
    "get_all_session_state",
    "delete_guild_session_state",
    "delete_expired_sessions",
    "count_active_sessions",
    # anchors
    "get_panel_anchor",
    "upsert_panel_anchor",
    "get_panel_anchor_by_message",
    "mark_anchors_stale_for_subsystem",
    "mark_panel_anchor_stale",
    "get_all_active_panel_anchors",
    "delete_stale_panel_anchors",
    "delete_guild_panel_anchors",
    "get_user_subsystem_anchors",
    # games
    "rps_ensure_player",
    "rps_update_stat",
    "rps_get_leaderboard",
    "get_counting_state",
    "set_counting_state",
    "get_chain_channel",
    "set_chain_channel",
    "delete_chain_channel",
    "set_chain_limit",
    "increment_chain_count",
    "get_all_chain_channels",
    "get_deathmatch_stats",
    "update_deathmatch",
    "get_deathmatch_leaderboard",
    "get_mining_inventory",
    "update_mining_item",
    "set_mining_inventory",
    "get_all_mining_totals",
]


@pytest.mark.parametrize("name", _EXPECTED_PUBLIC)
def test_public_symbol_reachable_via_package_root(name: str) -> None:
    """``from utils import db; db.<name>`` continues to resolve."""
    from utils import db

    assert hasattr(db, name), f"utils.db.{name} missing — back-compat broken"


@pytest.mark.parametrize("name", _EXPECTED_PUBLIC)
def test_public_symbol_reachable_via_direct_import(name: str) -> None:
    """``from utils.db import <name>`` continues to work."""
    mod = __import__("utils.db", fromlist=[name])
    assert hasattr(mod, name), f"from utils.db import {name} broken"


def test_legacy_decode_shim_still_reachable():
    """The pre-S1 private alias _maybe_decode_legacy stays reachable
    until S6 retires it.  Some tests imported it directly.
    """
    from utils import db

    assert hasattr(db, "_maybe_decode_legacy")


def test_submodule_namespaces_exist():
    """Submodules are reachable as utils.db.<subpkg> for tests that
    want to monkeypatch a specific bucket without affecting others.
    """
    import utils.db.anchors  # noqa: F401
    import utils.db.codec  # noqa: F401
    import utils.db.economy  # noqa: F401
    import utils.db.games.chain  # noqa: F401
    import utils.db.games.counting  # noqa: F401
    import utils.db.games.deathmatch  # noqa: F401
    import utils.db.games.mining  # noqa: F401
    import utils.db.games.rps  # noqa: F401
    import utils.db.governance  # noqa: F401
    import utils.db.inventory  # noqa: F401
    import utils.db.migrations  # noqa: F401
    import utils.db.moderation  # noqa: F401
    import utils.db.pool  # noqa: F401
    import utils.db.roles  # noqa: F401
    import utils.db.sessions  # noqa: F401
    import utils.db.settings  # noqa: F401
    import utils.db.xp  # noqa: F401
