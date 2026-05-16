"""Multi-server governance template system (ISSUE-034).

Templates store a named set of visibility overrides that can be:
  - Exported from one guild via export_template()
  - Applied to another guild via apply_template()
  - Stored in the DB for reuse via save_template()

Public surface:
    export_template(guild_id, name="", description="") → GovernanceTemplate
    apply_template(ctx, template) → int (overrides applied via pipeline)
    save_template(template, created_by_guild_id=None) → int (template_id)
    load_template(template_id) → GovernanceTemplate | None

apply_template() routes every override through GovernanceMutationPipeline so
authority validation, transactional audit writes, and event emission happen
per entry — see INV-003.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from governance.models import GovernanceContext
from governance.writes import GovernanceMutationPipeline
from utils import db

logger = logging.getLogger("bot.governance.templates")


@dataclass
class GovernanceTemplate:
    """Serializable governance configuration snapshot for one guild.

    ``visibility_overrides`` is a list of dicts matching the
    ``subsystem_visibility`` table schema (without guild_id/id columns).
    ``cleanup_overrides`` mirrors ``cleanup_policies`` similarly.
    """

    name: str = ""
    description: str = ""
    visibility_overrides: list[dict] = field(default_factory=list)
    cleanup_overrides: list[dict] = field(default_factory=list)
    source_guild_id: int | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "source_guild_id": self.source_guild_id,
            "visibility_overrides": self.visibility_overrides,
            "cleanup_overrides": self.cleanup_overrides,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GovernanceTemplate:
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            visibility_overrides=data.get("visibility_overrides", []),
            cleanup_overrides=data.get("cleanup_overrides", []),
            source_guild_id=data.get("source_guild_id"),
        )


async def export_template(
    guild_id: int,
    name: str = "",
    description: str = "",
) -> GovernanceTemplate:
    """Export the current governance overrides for a guild as a template."""
    vis_rows = await db.get_all_visibility_for_guild(guild_id)
    cleanup_rows = await db.get_all_cleanup_for_guild(guild_id)

    visibility_overrides = [
        {
            "scope_type": r["scope_type"],
            "scope_id": r["scope_id"],
            "subsystem": r["subsystem"],
            "enabled": r["enabled"],
        }
        for r in vis_rows
    ]
    cleanup_overrides = [
        {
            "scope_type": r["scope_type"],
            "scope_id": r["scope_id"],
            "delete_invalid_commands": r["delete_invalid_commands"],
            "delete_failed_commands": r.get("delete_failed_commands", True),
            "delete_after_seconds": r["delete_after_seconds"],
        }
        for r in cleanup_rows
    ]

    template = GovernanceTemplate(
        name=name or f"Guild {guild_id} export",
        description=description,
        visibility_overrides=visibility_overrides,
        cleanup_overrides=cleanup_overrides,
        source_guild_id=guild_id,
    )
    logger.info(
        "Exported governance template from guild=%d: %d vis, %d cleanup overrides",
        guild_id,
        len(visibility_overrides),
        len(cleanup_overrides),
    )
    return template


async def apply_template(ctx: GovernanceContext, template: GovernanceTemplate) -> int:
    """Apply a template's overrides to a guild via GovernanceMutationPipeline.

    INV-003: every mutation routes through the pipeline.  This guarantees
    per-override authority validation (SEC-001), transactional DB+audit writes,
    deterministic cache invalidation, and EVT_VISIBILITY_CHANGED /
    EVT_CLEANUP_CHANGED / EVT_CACHE_INVALIDATED event emission for each entry.
    A template apply with N entries produces N audit rows, one per mutation.

    Returns the number of records successfully written.  Individual entries
    that fail validation (unknown scope, unknown subsystem, insufficient
    authority) raise the relevant GovernanceError without rolling back earlier
    successful writes — callers wanting all-or-nothing semantics should wrap
    this call in their own transaction boundary.
    """
    pipeline = GovernanceMutationPipeline()
    count = 0
    for override in template.visibility_overrides:
        await pipeline.set_visibility(
            ctx,
            override["scope_type"],
            override["scope_id"],
            override["subsystem"],
            override["enabled"],
        )
        count += 1

    for policy in template.cleanup_overrides:
        await pipeline.set_cleanup_policy(
            ctx,
            policy["scope_type"],
            policy["scope_id"],
            delete_invalid_commands=policy.get("delete_invalid_commands", True),
            delete_failed_commands=policy.get("delete_failed_commands", True),
            delete_after_seconds=policy.get("delete_after_seconds", 5),
        )
        count += 1

    logger.info(
        "Applied governance template %r to guild=%d: %d overrides via pipeline",
        template.name,
        ctx.guild_id,
        count,
    )
    return count


async def save_template(
    template: GovernanceTemplate,
    *,
    created_by_guild_id: int | None = None,
) -> int:
    """Persist a template to the DB. Returns the new template_id."""
    payload = json.dumps(template.to_dict())
    row = await db.get().fetchrow(
        """INSERT INTO governance_templates
               (name, description, created_by_guild_id, payload)
           VALUES ($1, $2, $3, $4::jsonb)
           RETURNING template_id""",
        template.name,
        template.description,
        created_by_guild_id,
        payload,
    )
    template_id: int = row["template_id"]
    logger.info("Saved governance template %r as id=%d", template.name, template_id)
    return template_id


async def load_template(template_id: int) -> GovernanceTemplate | None:
    """Load a template from the DB by ID. Returns None if not found."""
    row = await db.get().fetchrow(
        "SELECT payload FROM governance_templates WHERE template_id = $1",
        template_id,
    )
    if row is None:
        return None
    data = json.loads(row["payload"])
    return GovernanceTemplate.from_dict(data)
