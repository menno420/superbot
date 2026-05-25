"""Single chokepoint for BTD6 strategy writes (M4).

Every state transition (submit / refine / approve / reject /
publish / unpublish / revert / detach-submitter / anonymise) goes
through this service so the matching ``btd6_strategy_audit`` row is
written in the same transaction. The cog and view layers never call
``utils/db/btd6_strategies`` directly — the
``test_no_ai_factual_writes`` pin (and a sibling grep test) ensures
no direct DB access bypasses the audit trail.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from utils.db import btd6_strategies as db

logger = logging.getLogger("bot.services.btd6_strategy_mutation")


class BTD6StrategyMutationError(Exception):
    pass


class UnauthorizedStrategyMutationError(BTD6StrategyMutationError):
    pass


class InvalidStrategyValueError(BTD6StrategyMutationError):
    pass


_VALID_VISIBILITY = frozenset({"guild", "published"})
_VALID_APPROVAL = frozenset(
    {"draft", "pending", "approved", "rejected", "unpublished"},
)


@dataclass(frozen=True)
class StrategyMutationResult:
    mutation_id: str
    strategy_id: int
    action: str
    actor_kind: str


def _check_actor(actor: Any) -> int | None:
    if actor is None:
        raise UnauthorizedStrategyMutationError("actor is required")
    return getattr(actor, "id", None)


def _is_staff(actor: Any) -> bool:
    perms = getattr(actor, "guild_permissions", None)
    if perms is None:
        return False
    if getattr(perms, "administrator", False):
        return True
    return bool(getattr(perms, "manage_guild", False))


async def submit_strategy(
    *,
    origin_guild_id: int,
    submitter: Any,
    title: str,
    summary: str,
    map_name: str | None = None,
    mode: str | None = None,
    difficulty: str | None = None,
    hero: str | None = None,
    towers: list[Any] | None = None,
    upgrade_paths: list[Any] | None = None,
    round_range: dict[str, Any] | None = None,
    steps: list[Any] | None = None,
    common_failures: list[Any] | None = None,
    source_links: list[Any] | None = None,
    origin_metadata: dict[str, Any] | None = None,
) -> StrategyMutationResult:
    submitter_id = _check_actor(submitter)
    if not title.strip() or not summary.strip():
        raise InvalidStrategyValueError("title and summary are required")
    snapshot = getattr(submitter, "display_name", None) or getattr(
        submitter,
        "name",
        None,
    )
    strategy_id = await db.insert_strategy(
        origin_guild_id=origin_guild_id,
        current_guild_id=origin_guild_id,
        visibility="guild",
        approval_status="draft",
        title=title.strip(),
        summary=summary.strip(),
        map_name=map_name,
        mode=mode,
        difficulty=difficulty,
        hero=hero,
        towers=list(towers or []),
        upgrade_paths=list(upgrade_paths or []),
        round_range=round_range,
        steps=list(steps or []),
        common_failures=list(common_failures or []),
        source_links=list(source_links or []),
        submitted_by=submitter_id,
        submitter_display_snapshot=snapshot,
        origin_metadata=dict(origin_metadata or {}),
    )
    await db.record_strategy_audit(
        strategy_id,
        actor_kind="user",
        actor_id=submitter_id,
        action="submitted",
    )
    return StrategyMutationResult(
        mutation_id=uuid.uuid4().hex,
        strategy_id=strategy_id,
        action="submitted",
        actor_kind="user",
    )


async def ai_approve_guild(
    strategy_id: int,
    *,
    provider: str,
    model: str,
    detail: dict[str, Any] | None = None,
) -> StrategyMutationResult:
    """AI-only approval — guild-local visibility, never publishes.

    Pinned by tests: an AI-approved strategy cannot reach
    ``visibility='published'`` without a separate staff call.
    """
    before = await db.get_strategy(strategy_id)
    if before is None:
        raise InvalidStrategyValueError(f"strategy {strategy_id} not found")
    if before["visibility"] != "guild":
        raise InvalidStrategyValueError(
            "AI approval is only valid for guild-local strategies; "
            "publishing requires staff confirmation",
        )

    await db.update_strategy_state(
        strategy_id,
        approval_status="approved",
        approved_by="ai",
        approved_by_id=None,
        approval_provider=provider,
        approval_model=model,
        current_guild_id=before["current_guild_id"],
        bump_version=True,
    )
    await db.record_strategy_audit(
        strategy_id,
        actor_kind="ai",
        actor_id=None,
        action="ai_approved",
        detail={
            "provider": provider,
            "model": model,
            **(detail or {}),
        },
    )
    return StrategyMutationResult(
        mutation_id=uuid.uuid4().hex,
        strategy_id=strategy_id,
        action="ai_approved",
        actor_kind="ai",
    )


async def staff_publish(
    strategy_id: int,
    *,
    staff_actor: Any,
    detail: dict[str, Any] | None = None,
) -> StrategyMutationResult:
    """Staff promotes a guild strategy to globally published.

    Refuses if the actor lacks the staff tier check — the view +
    mutation gate provides defence in depth.
    """
    actor_id = _check_actor(staff_actor)
    if not _is_staff(staff_actor):
        raise UnauthorizedStrategyMutationError(
            "publishing requires manage_guild or administrator permission",
        )
    before = await db.get_strategy(strategy_id)
    if before is None:
        raise InvalidStrategyValueError(f"strategy {strategy_id} not found")
    if before["visibility"] == "published":
        raise InvalidStrategyValueError("strategy is already published")

    await db.update_strategy_state(
        strategy_id,
        approval_status="approved",
        visibility="published",
        approved_by="staff",
        approved_by_id=actor_id,
        current_guild_id=before["current_guild_id"],
        bump_version=True,
    )
    await db.record_strategy_audit(
        strategy_id,
        actor_kind="staff",
        actor_id=actor_id,
        action="published",
        detail=detail,
    )
    return StrategyMutationResult(
        mutation_id=uuid.uuid4().hex,
        strategy_id=strategy_id,
        action="published",
        actor_kind="staff",
    )


async def unpublish(
    strategy_id: int,
    *,
    staff_actor: Any,
    reason: str | None = None,
) -> StrategyMutationResult:
    actor_id = _check_actor(staff_actor)
    if not _is_staff(staff_actor):
        raise UnauthorizedStrategyMutationError(
            "unpublishing requires manage_guild or administrator permission",
        )
    before = await db.get_strategy(strategy_id)
    if before is None:
        raise InvalidStrategyValueError(f"strategy {strategy_id} not found")

    await db.update_strategy_state(
        strategy_id,
        approval_status="unpublished",
        visibility="guild",
        current_guild_id=before["current_guild_id"] or before["origin_guild_id"],
        bump_version=True,
    )
    await db.record_strategy_audit(
        strategy_id,
        actor_kind="staff",
        actor_id=actor_id,
        action="unpublished",
        detail={"reason": reason} if reason else None,
    )
    return StrategyMutationResult(
        mutation_id=uuid.uuid4().hex,
        strategy_id=strategy_id,
        action="unpublished",
        actor_kind="staff",
    )


async def reject(
    strategy_id: int,
    *,
    actor: Any,
    actor_kind: str = "staff",
    reason: str | None = None,
) -> StrategyMutationResult:
    actor_id = _check_actor(actor)
    await db.update_strategy_state(
        strategy_id,
        approval_status="rejected",
        bump_version=True,
        current_guild_id=None,
    )
    await db.record_strategy_audit(
        strategy_id,
        actor_kind=actor_kind,
        actor_id=actor_id,
        action="rejected",
        detail={"reason": reason} if reason else None,
    )
    return StrategyMutationResult(
        mutation_id=uuid.uuid4().hex,
        strategy_id=strategy_id,
        action="rejected",
        actor_kind=actor_kind,
    )


async def anonymise_submitter(
    strategy_id: int,
    *,
    actor: Any,
    state: str = "anonymized",
    reason: str | None = None,
) -> StrategyMutationResult:
    actor_id = _check_actor(actor)
    if state not in ("anonymized", "deleted"):
        raise InvalidStrategyValueError(
            "submitter_identity_state must be 'anonymized' or 'deleted'",
        )
    await db.anonymize_submitter(strategy_id, new_state=state)
    action = "submitter_anonymized" if state == "anonymized" else "submitter_deleted"
    await db.record_strategy_audit(
        strategy_id,
        actor_kind="system",
        actor_id=actor_id,
        action=action,
        detail={"reason": reason} if reason else None,
    )
    return StrategyMutationResult(
        mutation_id=uuid.uuid4().hex,
        strategy_id=strategy_id,
        action=action,
        actor_kind="system",
    )


__all__ = [
    "BTD6StrategyMutationError",
    "InvalidStrategyValueError",
    "StrategyMutationResult",
    "UnauthorizedStrategyMutationError",
    "ai_approve_guild",
    "anonymise_submitter",
    "reject",
    "staff_publish",
    "submit_strategy",
    "unpublish",
]
