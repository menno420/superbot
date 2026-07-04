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
    credit_coins,
    ensure_and_get_economy,
    get_coins,
    get_job_times,
    increment_job,
    insert_economy_audit,
    set_coins,
    set_daily_claim,
    set_last_worked,
    try_debit_coins,
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
from utils.db.games.creature_battles import (
    get_battle_record,
    record_battle_outcome,
    top_battlers,
)
from utils.db.games.creatures import (
    get_creature_collection,
    record_creature_catch,
    top_collectors,
)
from utils.db.games.deathmatch import (
    get_deathmatch_leaderboard,
    get_deathmatch_stats,
    update_deathmatch,
)
from utils.db.games.farm import (
    get_chicken_farm,
    set_chicken_farm,
    top_farmers,
)
from utils.db.games.fishing import (
    get_fishing_log,
    get_fishing_records,
    record_catch,
    top_fishers,
    top_trophies,
)
from utils.db.games.fishing_bait import (
    clear_active_bait,
    get_active_bait,
    set_active_bait,
)
from utils.db.games.fishing_energy import (
    get_fishing_energy,
    set_fishing_energy,
)
from utils.db.games.fishing_rod import (
    get_rod_tier,
    set_rod_tier,
)
from utils.db.games.fishing_venue import (
    get_fishing_venue,
    set_fishing_venue,
)
from utils.db.games.game_xp import (
    add_game_xp,
    get_game_xp,
    get_game_xp_row,
    get_total_xp,
    top_game_xp,
    top_total_xp,
)
from utils.db.games.mining import (
    apply_inventory_deltas,
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
from utils.db.games.mining_gear_wear import (
    clear_gear_wear,
    get_gear_wear,
    set_gear_wear,
)
from utils.db.games.mining_grid import (
    get_discovered_window,
    get_position,
    get_world_seed,
    mark_discovered,
    set_position,
    set_world_seed,
)
from utils.db.games.mining_loadout import (
    delete_loadout,
    get_loadout,
    list_loadouts,
    save_loadout,
)
from utils.db.games.mining_player_state import (
    get_depth,
    get_energy,
    get_equipped_title,
    get_last_broken,
    get_max_depth,
    get_vault_level,
    record_depth,
    set_depth,
    set_energy,
    set_equipped_title,
    set_last_broken,
    set_vault_level,
)
from utils.db.games.mining_structures import get_structures, set_structure_level
from utils.db.games.mining_vault import get_vault, update_vault_item
from utils.db.games.player_skills import get_skills, set_skill_points
from utils.db.games.rps import rps_ensure_player, rps_get_leaderboard, rps_update_stat
from utils.db.governance import (
    delete_cleanup_policy,
    get_all_cleanup_for_guild,
    get_all_visibility_for_guild,
    get_cleanup_policy,
    get_subsystem_visibility,
    get_visibility_override,
    set_cleanup_policy,
    set_subsystem_visibility,
    write_governance_audit,
)
from utils.db.inventory import add_item, get_inventory, has_item, try_grant_unique_item
from utils.db.karma import (
    credit_karma,
    get_karma,
    grants_given_since,
    increment_given,
    insert_karma_audit,
    karma_rank,
    recent_grant_count,
    top_karma,
)
from utils.db.moderation import (
    add_prohibited_word,
    add_warning,
    clear_warnings,
    get_mod_logs,
    get_prohibited_words,
    get_warnings,
    get_wordfilter_strict,
    log_mod_action,
    remove_prohibited_word,
    set_wordfilter_strict,
)

# ──────────────────────────────────────────────────────────────────────
# Pool lifecycle + primitives  (kept at the package root for back-compat)
# ──────────────────────────────────────────────────────────────────────
from utils.db.pool import close, execute, fetchall, fetchone, get, init, transaction
from utils.db.roles import (
    add_reaction_role,
    clear_reaction_message_mode,
    clear_role_exemption,
    clear_role_time_threshold,
    clear_role_xp_threshold,
    delete_reaction_modes_for_guild,
    get_all_reaction_roles,
    get_reaction_message_mode,
    get_reaction_message_modes,
    get_reaction_role,
    get_reaction_roles_for_message,
    get_role_exemptions,
    get_role_thresholds,
    get_xp_threshold_roles,
    remove_reaction_role,
    remove_role_threshold,
    set_reaction_message_mode,
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
from utils.db.tickets import (
    ticket_add_blacklist,
    ticket_close,
    ticket_count_open_for_user,
    ticket_create,
    ticket_get,
    ticket_get_by_channel,
    ticket_get_config,
    ticket_is_blacklisted,
    ticket_list_for_user,
    ticket_list_open,
    ticket_remove_blacklist,
    ticket_set_claim,
    ticket_upsert_config,
)
from utils.db.treasury import (
    credit_treasury,
    get_treasury,
    try_debit_treasury,
)
from utils.db.xp import (
    add_xp,
    delete_xp,
    get_guild_xp_totals,
    get_xp,
    level_progress,
    set_imported_xp,
    total_xp_for_level,
    xp_for_level,
)

__all__ = [
    # pool
    "close",
    "execute",
    "fetchall",
    "fetchone",
    "get",
    "init",
    "transaction",
    # xp
    "add_xp",
    "delete_xp",
    "get_guild_xp_totals",
    "get_xp",
    "level_progress",
    "set_imported_xp",
    "total_xp_for_level",
    "xp_for_level",
    # settings
    "get_setting",
    "set_setting",
    # roles
    "add_reaction_role",
    "clear_reaction_message_mode",
    "clear_role_exemption",
    "clear_role_time_threshold",
    "clear_role_xp_threshold",
    "delete_reaction_modes_for_guild",
    "get_all_reaction_roles",
    "get_reaction_message_mode",
    "get_reaction_message_modes",
    "get_reaction_role",
    "get_reaction_roles_for_message",
    "get_role_exemptions",
    "get_role_thresholds",
    "get_xp_threshold_roles",
    "remove_reaction_role",
    "remove_role_threshold",
    "set_reaction_message_mode",
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
    "get_wordfilter_strict",
    "log_mod_action",
    "remove_prohibited_word",
    "set_wordfilter_strict",
    # economy
    "add_coins",
    "claim_daily_if_ready",
    "credit_coins",
    "ensure_and_get_economy",
    "get_coins",
    "get_job_times",
    "increment_job",
    "insert_economy_audit",
    "set_coins",
    "set_daily_claim",
    "set_last_worked",
    "try_debit_coins",
    # treasury (guild-owned coin pool)
    "credit_treasury",
    "get_treasury",
    "try_debit_treasury",
    # tickets (support-ticket subsystem)
    "ticket_add_blacklist",
    "ticket_close",
    "ticket_count_open_for_user",
    "ticket_create",
    "ticket_get",
    "ticket_get_by_channel",
    "ticket_get_config",
    "ticket_is_blacklisted",
    "ticket_list_for_user",
    "ticket_list_open",
    "ticket_remove_blacklist",
    "ticket_set_claim",
    "ticket_upsert_config",
    # inventory
    "add_item",
    "get_inventory",
    "has_item",
    "try_grant_unique_item",
    # karma
    "credit_karma",
    "get_karma",
    "grants_given_since",
    "increment_given",
    "insert_karma_audit",
    "karma_rank",
    "recent_grant_count",
    "top_karma",
    # governance
    "delete_cleanup_policy",
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
    # game_xp (shared cross-game progression)
    "add_game_xp",
    "get_game_xp",
    "get_game_xp_row",
    "get_total_xp",
    "top_game_xp",
    "top_total_xp",
    "get_max_depth",
    "record_depth",
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
    "save_loadout",
    "get_loadout",
    "list_loadouts",
    "delete_loadout",
    "get_depth",
    "set_depth",
    "get_energy",
    "set_energy",
    "get_last_broken",
    "set_last_broken",
    "get_vault_level",
    "set_vault_level",
    "get_equipped_title",
    "set_equipped_title",
    "get_vault",
    "update_vault_item",
    "get_skills",
    "set_skill_points",
    "get_structures",
    "set_structure_level",
    "get_fishing_log",
    "get_fishing_records",
    "record_catch",
    "top_fishers",
    "top_trophies",
    "get_rod_tier",
    "set_rod_tier",
    "get_fishing_energy",
    "set_fishing_energy",
    "get_fishing_venue",
    "set_fishing_venue",
    "get_chicken_farm",
    "set_chicken_farm",
    "top_farmers",
    "get_active_bait",
    "set_active_bait",
    "clear_active_bait",
    "get_creature_collection",
    "record_creature_catch",
    "top_collectors",
    "get_battle_record",
    "record_battle_outcome",
    "top_battlers",
    "apply_inventory_deltas",
    "get_gear_wear",
    "set_gear_wear",
    "clear_gear_wear",
    # mining grid (lateral position · per-guild seed · fog of war)
    "get_position",
    "set_position",
    "get_world_seed",
    "set_world_seed",
    "mark_discovered",
    "get_discovered_window",
]
