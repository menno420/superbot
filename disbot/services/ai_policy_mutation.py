"""Audited writes for the M2 AI policy tables.

Single chokepoint for writes to ``ai_guild_policy``,
``ai_channel_policy``, ``ai_category_policy``, and
``ai_role_policy``. Mirrors the shape of
:class:`services.settings_mutation.SettingsMutationPipeline`:
authority check → DB write → cache invalidation → typed result.

Reads live in :mod:`utils.db.ai` and the
:mod:`services.ai_natural_language_policy` resolver. The settings
UI writes through here, never directly.

The AI audit channel binding is NOT mutated through this service —
it stays in ``subsystem_bindings`` under the M1 BindingSpec.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from services import ai_natural_language_policy
from utils.db import ai as ai_db

logger = logging.getLogger("bot.services.ai_policy_mutation")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class AIPolicyMutationError(Exception):
    """Base class for failed policy writes."""


class UnauthorizedAIPolicyMutationError(AIPolicyMutationError):
    """Actor lacked the administrator tier."""


class InvalidAIPolicyValueError(AIPolicyMutationError):
    """Value rejected by the mutation contract."""


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AIPolicyMutationResult:
    mutation_id: str
    table: str
    guild_id: int
    target_id: int | None
    generation: int | None
    event_emitted: bool


# ---------------------------------------------------------------------------
# Authority check
# ---------------------------------------------------------------------------


_VALID_CHANNEL_MODES = frozenset(
    {"inherit", "always_reply", "mention_only", "disabled"},
)
_VALID_ROLE_DECISIONS = frozenset({"allow", "deny", "inherit"})


def _check_admin(actor: Any) -> int | None:
    """Return ``actor.id`` if administrator-tier; raise otherwise."""
    if actor is None:
        raise UnauthorizedAIPolicyMutationError("actor is required")
    perms = getattr(actor, "guild_permissions", None)
    if perms is None or not getattr(perms, "administrator", False):
        raise UnauthorizedAIPolicyMutationError(
            "ai policy mutations require administrator permission",
        )
    return getattr(actor, "id", None)


# ---------------------------------------------------------------------------
# Guild policy
# ---------------------------------------------------------------------------


async def set_guild_policy(
    guild_id: int,
    *,
    enabled: bool,
    natural_language_enabled: bool,
    default_provider: str,
    default_model: str,
    minimum_level_default: int,
    cooldown_seconds: int,
    fresh_user_mention_allowance: int,
    guild_instruction_profile_id: int | None,
    actor: Any,
) -> AIPolicyMutationResult:
    actor_id = _check_admin(actor)
    if default_provider not in ("deterministic", "openai"):
        raise InvalidAIPolicyValueError(
            f"default_provider must be 'deterministic' or 'openai', got "
            f"{default_provider!r}",
        )
    if minimum_level_default < 0:
        raise InvalidAIPolicyValueError("minimum_level_default must be >= 0")
    if cooldown_seconds < 0:
        raise InvalidAIPolicyValueError("cooldown_seconds must be >= 0")
    if fresh_user_mention_allowance < 0:
        raise InvalidAIPolicyValueError("fresh_user_mention_allowance must be >= 0")

    mutation_id = uuid.uuid4().hex
    generation = await ai_db.upsert_guild_policy(
        guild_id,
        enabled=enabled,
        natural_language_enabled=natural_language_enabled,
        default_provider=default_provider,
        default_model=default_model,
        minimum_level_default=minimum_level_default,
        cooldown_seconds=cooldown_seconds,
        fresh_user_mention_allowance=fresh_user_mention_allowance,
        guild_instruction_profile_id=guild_instruction_profile_id,
        updated_by=actor_id,
    )
    ai_natural_language_policy.invalidate(guild_id)
    event_emitted = await _emit("ai.policy.guild_changed", guild_id, mutation_id)

    return AIPolicyMutationResult(
        mutation_id=mutation_id,
        table="ai_guild_policy",
        guild_id=guild_id,
        target_id=None,
        generation=generation,
        event_emitted=event_emitted,
    )


# ---------------------------------------------------------------------------
# Channel / category / role policies
# ---------------------------------------------------------------------------


async def set_channel_policy(
    guild_id: int,
    channel_id: int,
    *,
    mode: str,
    min_level: int | None,
    cooldown_seconds: int | None,
    instruction_profile_id: int | None,
    actor: Any,
) -> AIPolicyMutationResult:
    actor_id = _check_admin(actor)
    if mode not in _VALID_CHANNEL_MODES:
        raise InvalidAIPolicyValueError(
            f"channel mode must be one of {sorted(_VALID_CHANNEL_MODES)}, "
            f"got {mode!r}",
        )
    mutation_id = uuid.uuid4().hex
    await ai_db.upsert_channel_policy(
        guild_id,
        channel_id,
        mode=mode,
        min_level=min_level,
        cooldown_seconds=cooldown_seconds,
        instruction_profile_id=instruction_profile_id,
        updated_by=actor_id,
    )
    generation = await ai_db.bump_generation(guild_id)
    ai_natural_language_policy.invalidate(guild_id)
    event_emitted = await _emit("ai.policy.channel_changed", guild_id, mutation_id)
    return AIPolicyMutationResult(
        mutation_id=mutation_id,
        table="ai_channel_policy",
        guild_id=guild_id,
        target_id=channel_id,
        generation=generation,
        event_emitted=event_emitted,
    )


async def set_category_policy(
    guild_id: int,
    category_id: int,
    *,
    mode: str,
    min_level: int | None,
    cooldown_seconds: int | None,
    instruction_profile_id: int | None,
    actor: Any,
) -> AIPolicyMutationResult:
    actor_id = _check_admin(actor)
    if mode not in _VALID_CHANNEL_MODES:
        raise InvalidAIPolicyValueError(
            f"category mode must be one of {sorted(_VALID_CHANNEL_MODES)}, "
            f"got {mode!r}",
        )
    mutation_id = uuid.uuid4().hex
    await ai_db.upsert_category_policy(
        guild_id,
        category_id,
        mode=mode,
        min_level=min_level,
        cooldown_seconds=cooldown_seconds,
        instruction_profile_id=instruction_profile_id,
        updated_by=actor_id,
    )
    generation = await ai_db.bump_generation(guild_id)
    ai_natural_language_policy.invalidate(guild_id)
    event_emitted = await _emit("ai.policy.category_changed", guild_id, mutation_id)
    return AIPolicyMutationResult(
        mutation_id=mutation_id,
        table="ai_category_policy",
        guild_id=guild_id,
        target_id=category_id,
        generation=generation,
        event_emitted=event_emitted,
    )


async def set_role_policy(
    guild_id: int,
    role_id: int,
    *,
    decision: str,
    min_level_override: int | None,
    bypass_cooldown: bool,
    actor: Any,
) -> AIPolicyMutationResult:
    actor_id = _check_admin(actor)
    if decision not in _VALID_ROLE_DECISIONS:
        raise InvalidAIPolicyValueError(
            f"role decision must be one of {sorted(_VALID_ROLE_DECISIONS)}, "
            f"got {decision!r}",
        )
    if min_level_override is not None and min_level_override < 0:
        raise InvalidAIPolicyValueError("min_level_override must be >= 0")
    mutation_id = uuid.uuid4().hex
    await ai_db.upsert_role_policy(
        guild_id,
        role_id,
        decision=decision,
        min_level_override=min_level_override,
        bypass_cooldown=bypass_cooldown,
        updated_by=actor_id,
    )
    generation = await ai_db.bump_generation(guild_id)
    ai_natural_language_policy.invalidate(guild_id)
    event_emitted = await _emit("ai.policy.role_changed", guild_id, mutation_id)
    return AIPolicyMutationResult(
        mutation_id=mutation_id,
        table="ai_role_policy",
        guild_id=guild_id,
        target_id=role_id,
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
        logger.warning("ai_policy_mutation: event emit failed: %s", exc)
        return False


__all__ = [
    "AIPolicyMutationError",
    "AIPolicyMutationResult",
    "InvalidAIPolicyValueError",
    "UnauthorizedAIPolicyMutationError",
    "set_category_policy",
    "set_channel_policy",
    "set_guild_policy",
    "set_role_policy",
]
