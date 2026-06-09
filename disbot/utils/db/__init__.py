"""utils.db — Postgres data-access package.

The package replaces the previous 1400-LOC ``utils/db.py`` module.
Submodules host per-feature CRUD; this file re-exports every public
symbol so the historical ``from utils import db; db.func(...)`` and
``from utils.db import func`` import patterns keep working without
change.

Layout
------
    pool        — asyncpg pool lifecycle + generic CRUD primitives
    codec       — JSONB codec registration + legacy-decode shim
    migrations  — schema bootstrap + migration runner
    xp          — xp table CRUD + level math
    settings    — guild_settings KV
    roles       — role_thresholds + reaction_roles
    moderation  — warnings + mod_logs + prohibited_words
    economy     — coins + economy + job_progress
    inventory   — inventory CRUD
    governance  — subsystem_visibility + cleanup_policies + audit
    sessions    — runtime_sessions + runtime_session_state
    anchors     — panel_anchors
    games/      — per-game tables (rps, counting, chain, deathmatch, mining)

Ownership rule
--------------
Submodules import primitives via ``from utils.db import pool`` and call
``pool.get() / pool.fetchone() / pool.fetchall() / pool.execute()`` so
production callers and tests that monkeypatch ``utils.db.pool.X`` both
target the same attribute.  Direct ``from utils.db.pool import get`` is
allowed only within this package's submodules; external code should go
through ``utils.db.get`` (re-exported below) for stable identity under
monkeypatching.
"""

from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────
# Per-feature CRUD re-exports
# ──────────────────────────────────────────────────────────────────────
from utils.db.anchors import (
    delete_guild_panel_anchors,
    delete_stale_panel_anchors,
    get_all_active_panel_anchors,
    get_panel_anchor,
    get_panel_anchor_by_message,
    get_user_subsystem_anchors,
    mark_anchors_stale_for_subsystem,
    mark_panel_anchor_stale,
    upsert_panel_anchor,
)
from utils.db.economy import (
    add_coins,
    claim_daily_if_ready,
    get_coins,
    get_economy,
    get_job_times,
    increment_job,
    set_coins,
    set_daily_claim,
    set_last_worked,
)

# ──────────────────────────────────────────────────────────────────────
# Games — re-export each per-game module under the package root so
# legacy ``db.rps_update_stat`` etc. continue to resolve.
# ──────────────────────────────────────────────────────────────────────
from utils.db.games.chain import (
    delete_chain_channel,
    get_all_chain_channels,
    get_chain_channel,
    increment_chain_count,
    set_chain_channel,
    set_chain_limit,
)
from utils.db.games.counting import get_counting_state, set_counting_state
from utils.db.games.deathmatch import (
    get_deathmatch_leaderboard,
    get_deathmatch_stats,
    update_deathmatch,
)
from utils.db.games.mining import (
    get_all_mining_totals,
    get_mining_inventory,
    set_mining_inventory,
    update_mining_item,
)
from utils.db.games.mining_equipment import (
    equip_item,
    get_equipment,
    unequip_slot,
)
from utils.db.games.mining_player_state import get_depth, set_depth
from utils.db.games.rps import rps_ensure_player, rps_get_leaderboard, rps_update_stat
from utils.db.governance import (
    get_all_cleanup_for_guild,
    get_all_visibility_for_guild,
    get_cleanup_policy,
    get_subsystem_visibility,
    get_visibility_override,
    set_cleanup_policy,
    set_subsystem_visibility,
    write_governance_audit,
)
from utils.db.inventory import add_item, get_inventory, has_item
from utils.db.moderation import (
    add_prohibited_word,
    add_warning,
    clear_warnings,
    get_mod_logs,
    get_prohibited_words,
    get_warnings,
    log_mod_action,
    remove_prohibited_word,
)

# ──────────────────────────────────────────────────────────────────────
# Pool lifecycle + primitives  (kept at the package root for back-compat)
# ──────────────────────────────────────────────────────────────────────
from utils.db.pool import close, execute, fetchall, fetchone, get, init
from utils.db.roles import (
    add_reaction_role,
    clear_role_exemption,
    clear_role_time_threshold,
    clear_role_xp_threshold,
    get_all_reaction_roles,
    get_reaction_role,
    get_role_exemptions,
    get_role_thresholds,
    get_xp_threshold_roles,
    remove_reaction_role,
    remove_role_threshold,
    set_role_exemption,
    set_role_threshold,
    set_role_xp_threshold,
)
from utils.db.sessions import (
    count_active_sessions,
    delete_expired_sessions,
    delete_guild_session_state,
    delete_session,
    delete_session_state,
    delete_sessions_for_guild,
    delete_sessions_for_scope,
    delete_sessions_for_subsystem,
    get_all_session_state,
    get_or_create_session,
    get_session,
    get_session_state,
    set_session_state,
    set_session_state_many,
    touch_session,
)
from utils.db.settings import get_setting, set_setting
from utils.db.xp import add_xp, delete_xp, get_xp, level_progress, xp_for_level

__all__ = [
    # pool
    "close",
    "execute",
    "fetchall",
    "fetchone",
    "get",
    "init",
    # xp
    "add_xp",
    "delete_xp",
    "get_xp",
    "level_progress",
    "xp_for_level",
    # settings
    "get_setting",
    "set_setting",
    # roles
    "add_reaction_role",
    "clear_role_exemption",
    "clear_role_time_threshold",
    "clear_role_xp_threshold",
    "get_all_reaction_roles",
    "get_reaction_role",
    "get_role_exemptions",
    "get_role_thresholds",
    "get_xp_threshold_roles",
    "remove_reaction_role",
    "remove_role_threshold",
    "set_role_exemption",
    "set_role_threshold",
    "set_role_xp_threshold",
    # moderation
    "add_prohibited_word",
    "add_warning",
    "clear_warnings",
    "get_mod_logs",
    "get_prohibited_words",
    "get_warnings",
    "log_mod_action",
    "remove_prohibited_word",
    # economy
    "add_coins",
    "claim_daily_if_ready",
    "get_coins",
    "get_economy",
    "get_job_times",
    "increment_job",
    "set_coins",
    "set_daily_claim",
    "set_last_worked",
    # inventory
    "add_item",
    "get_inventory",
    "has_item",
    # governance
    "get_all_cleanup_for_guild",
    "get_all_visibility_for_guild",
    "get_cleanup_policy",
    "get_subsystem_visibility",
    "get_visibility_override",
    "set_cleanup_policy",
    "set_subsystem_visibility",
    "write_governance_audit",
    # sessions
    "count_active_sessions",
    "delete_expired_sessions",
    "delete_guild_session_state",
    "delete_session",
    "delete_session_state",
    "delete_sessions_for_guild",
    "delete_sessions_for_scope",
    "delete_sessions_for_subsystem",
    "get_all_session_state",
    "get_or_create_session",
    "get_session",
    "get_session_state",
    "set_session_state",
    "set_session_state_many",
    "touch_session",
    # anchors
    "delete_guild_panel_anchors",
    "delete_stale_panel_anchors",
    "get_all_active_panel_anchors",
    "get_panel_anchor",
    "get_panel_anchor_by_message",
    "get_user_subsystem_anchors",
    "mark_anchors_stale_for_subsystem",
    "mark_panel_anchor_stale",
    "upsert_panel_anchor",
    # games
    "delete_chain_channel",
    "get_all_chain_channels",
    "get_all_mining_totals",
    "get_chain_channel",
    "get_counting_state",
    "get_deathmatch_leaderboard",
    "get_deathmatch_stats",
    "get_mining_inventory",
    "increment_chain_count",
    "rps_ensure_player",
    "rps_get_leaderboard",
    "rps_update_stat",
    "set_chain_channel",
    "set_chain_limit",
    "set_counting_state",
    "set_mining_inventory",
    "update_deathmatch",
    "update_mining_item",
    "equip_item",
    "get_equipment",
    "unequip_slot",
    "get_depth",
    "set_depth",
]
