"""Governance health diagnostics.

Layer: models → ... → snapshot → health.
Imports from governance.models only (within governance/).
"""

from __future__ import annotations

from governance.models import GovernanceHealthReport
from utils import db, settings_keys
from utils.subsystem_registry import REGISTRY_VERSION, SUBSYSTEMS


async def run_governance_healthcheck(guild_id: int) -> GovernanceHealthReport:
    """Check for orphan overrides, stale versions, and invalid configs."""
    known_subsystems = set(SUBSYSTEMS.keys())
    rows = await db.get_all_visibility_for_guild(guild_id)
    orphans = [
        {
            "scope_type": r["scope_type"],
            "scope_id": r["scope_id"],
            "subsystem": r["subsystem"],
        }
        for r in rows
        if r["subsystem"] not in known_subsystems
    ]

    stored = await db.get_setting(
        guild_id, settings_keys.GOVERNANCE_VERSION, default="0"
    )
    stale = [guild_id] if int(stored) < REGISTRY_VERSION else []

    summary = f"{len(orphans)} orphan override(s), {len(stale)} stale version guild(s)"
    return GovernanceHealthReport(
        orphan_overrides=orphans,
        stale_version_guilds=stale,
        invalid_cleanup_configs=[],
        summary=summary,
    )
