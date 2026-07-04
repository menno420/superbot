"""Audited writes for the AI tool-orchestration profile (Phase 3).

Single chokepoint for writing ``orchestration_profile`` on ``ai_guild_policy``,
``ai_channel_policy``, and ``ai_category_policy``. Mirrors
:mod:`services.ai_policy_mutation`: authority check → value validation → DB
write → generation bump → resolver-cache invalidation → typed result + event.

Reads live in :mod:`utils.db.ai` and the
:mod:`services.ai_orchestration_policy` resolver. The Tools & Workflows UI
writes through here, never directly. Valid profile keys are validated against
:mod:`services.ai_orchestration_presets` (built-in presets only — v1 does not
accept arbitrary or guild-authored keys).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from services import ai_orchestration_policy, ai_orchestration_presets
from utils.db import ai as ai_db

logger = logging.getLogger("bot.services.ai_orchestration_mutation")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class AIOrchestrationMutationError(Exception):
    """Base class for failed orchestration-profile writes."""


class UnauthorizedAIOrchestrationMutationError(AIOrchestrationMutationError):
    """Actor lacked the administrator tier."""


class InvalidAIOrchestrationValueError(AIOrchestrationMutationError):
    """Profile key rejected by the mutation contract."""


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AIOrchestrationMutationResult:
    mutation_id: str
    table: str
    guild_id: int
    target_id: int | None
    profile_key: str | None
    generation: int | None
    event_emitted: bool


# ---------------------------------------------------------------------------
# Authority + value checks
# ---------------------------------------------------------------------------


def _check_admin(actor: Any) -> int | None:
    """Return ``actor.id`` if administrator-tier (or platform owner); raise otherwise."""
    if actor is None:
        raise UnauthorizedAIOrchestrationMutationError("actor is required")
    # Platform-owner override: the configured bot owner configures the AI in any
    # guild, even without Discord admin there (single source: config).
    from config import is_platform_owner

    actor_id = getattr(actor, "id", None)
    if is_platform_owner(actor_id):
        return actor_id
    perms = getattr(actor, "guild_permissions", None)
    if perms is None or not getattr(perms, "administrator", False):
        raise UnauthorizedAIOrchestrationMutationError(
            "ai orchestration mutations require administrator permission",
        )
    return actor_id


def _check_profile_key(profile_key: str | None) -> None:
    """Reject any key that is not a built-in preset. ``None`` clears (inherit)."""
    if profile_key is None:
        return
    if not ai_orchestration_presets.is_known(profile_key):
        valid = sorted(ai_orchestration_presets.known_profile_keys())
        raise InvalidAIOrchestrationValueError(
            f"unknown orchestration profile {profile_key!r}; "
            f"must be one of {valid} (or null to clear)",
        )


def known_profile_keys() -> frozenset[str]:
    """Expose the valid keys for the UI without reaching into presets."""
    return ai_orchestration_presets.known_profile_keys()


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


async def set_guild_orchestration(
    guild_id: int,
    *,
    profile_key: str | None,
    actor: Any,
) -> AIOrchestrationMutationResult:
    """Set (or clear, with ``None``) the guild-default orchestration profile."""
    actor_id = _check_admin(actor)
    _check_profile_key(profile_key)

    mutation_id = uuid.uuid4().hex
    generation = await ai_db.set_guild_orchestration_profile(
        guild_id,
        orchestration_profile=profile_key,
        updated_by=actor_id,
    )
    ai_orchestration_policy.invalidate(guild_id)
    event_emitted = await _emit(
        "ai.orchestration.guild_changed",
        guild_id,
        mutation_id,
    )
    return AIOrchestrationMutationResult(
        mutation_id=mutation_id,
        table="ai_guild_policy",
        guild_id=guild_id,
        target_id=None,
        profile_key=profile_key,
        generation=generation,
        event_emitted=event_emitted,
    )


async def set_channel_orchestration(
    guild_id: int,
    channel_id: int,
    *,
    profile_key: str | None,
    actor: Any,
) -> AIOrchestrationMutationResult:
    """Set (or clear) the channel-scope orchestration profile."""
    actor_id = _check_admin(actor)
    _check_profile_key(profile_key)

    mutation_id = uuid.uuid4().hex
    await ai_db.set_channel_orchestration_profile(
        guild_id,
        channel_id,
        orchestration_profile=profile_key,
        updated_by=actor_id,
    )
    generation = await ai_db.bump_generation(guild_id)
    ai_orchestration_policy.invalidate(guild_id)
    event_emitted = await _emit(
        "ai.orchestration.channel_changed",
        guild_id,
        mutation_id,
    )
    return AIOrchestrationMutationResult(
        mutation_id=mutation_id,
        table="ai_channel_policy",
        guild_id=guild_id,
        target_id=channel_id,
        profile_key=profile_key,
        generation=generation,
        event_emitted=event_emitted,
    )


async def set_category_orchestration(
    guild_id: int,
    category_id: int,
    *,
    profile_key: str | None,
    actor: Any,
) -> AIOrchestrationMutationResult:
    """Set (or clear) the category-scope orchestration profile."""
    actor_id = _check_admin(actor)
    _check_profile_key(profile_key)

    mutation_id = uuid.uuid4().hex
    await ai_db.set_category_orchestration_profile(
        guild_id,
        category_id,
        orchestration_profile=profile_key,
        updated_by=actor_id,
    )
    generation = await ai_db.bump_generation(guild_id)
    ai_orchestration_policy.invalidate(guild_id)
    event_emitted = await _emit(
        "ai.orchestration.category_changed",
        guild_id,
        mutation_id,
    )
    return AIOrchestrationMutationResult(
        mutation_id=mutation_id,
        table="ai_category_policy",
        guild_id=guild_id,
        target_id=category_id,
        profile_key=profile_key,
        generation=generation,
        event_emitted=event_emitted,
    )


# ---------------------------------------------------------------------------
# Event bus
# ---------------------------------------------------------------------------


async def _emit(event: str, guild_id: int, mutation_id: str) -> bool:
    """Best-effort emit; failures must not break the write."""
    try:
        from core.events import bus

        await bus.emit(event, guild_id=guild_id, mutation_id=mutation_id)
        return True
    except Exception as exc:  # noqa: BLE001 — never let bus drag the write down
        logger.warning("ai_orchestration_mutation: event emit failed: %s", exc)
        return False


__all__ = [
    "AIOrchestrationMutationError",
    "AIOrchestrationMutationResult",
    "InvalidAIOrchestrationValueError",
    "UnauthorizedAIOrchestrationMutationError",
    "known_profile_keys",
    "set_category_orchestration",
    "set_channel_orchestration",
    "set_guild_orchestration",
]
