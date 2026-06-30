"""Audited writes for ``ai_instruction_profile``.

Single chokepoint for instruction-profile mutations. Reads land in
:mod:`utils.db.ai`; the resolver consumes profile bodies through the
M2 instruction service. The M1 scalar
``ai.guild_instruction_profile`` is migrated into a profile row
named ``"default"`` by migration 039; subsequent UI edits write
through here so the typed row stays authoritative.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from services import ai_natural_language_policy
from utils.db import ai as ai_db

logger = logging.getLogger("bot.services.ai_instruction_mutation")


_VALID_SCOPES = frozenset(
    {"guild", "channel", "category", "feature", "system"},
)


class AIInstructionMutationError(Exception):
    pass


class UnauthorizedAIInstructionMutationError(AIInstructionMutationError):
    pass


class InvalidAIInstructionValueError(AIInstructionMutationError):
    pass


@dataclass(frozen=True)
class AIInstructionMutationResult:
    mutation_id: str
    profile_id: int
    guild_id: int | None
    scope: str
    name: str
    event_emitted: bool


def _check_admin(actor: Any) -> int | None:
    if actor is None:
        raise UnauthorizedAIInstructionMutationError("actor is required")
    # Platform-owner override: the configured bot owner configures the AI in any
    # guild, even without Discord admin there (single source: config).
    from config import is_platform_owner

    actor_id = getattr(actor, "id", None)
    if is_platform_owner(actor_id):
        return actor_id
    perms = getattr(actor, "guild_permissions", None)
    if perms is None or not getattr(perms, "administrator", False):
        raise UnauthorizedAIInstructionMutationError(
            "ai instruction mutations require administrator permission",
        )
    return actor_id


async def upsert_profile(
    *,
    guild_id: int | None,
    name: str,
    body: str,
    scope: str = "guild",
    feature_key: str | None = None,
    is_preset: bool = False,
    actor: Any,
) -> AIInstructionMutationResult:
    actor_id = _check_admin(actor)
    if scope not in _VALID_SCOPES:
        raise InvalidAIInstructionValueError(
            f"scope must be one of {sorted(_VALID_SCOPES)}, got {scope!r}",
        )
    if scope == "feature" and not feature_key:
        raise InvalidAIInstructionValueError(
            "feature_key is required when scope='feature'",
        )
    if not name.strip():
        raise InvalidAIInstructionValueError("profile name must be non-empty")
    if not isinstance(body, str):
        raise InvalidAIInstructionValueError("profile body must be a string")
    if is_preset and guild_id is not None:
        # Presets are system-wide rows seeded by migration 044. Guild
        # actors must never be able to author or impersonate them.
        raise UnauthorizedAIInstructionMutationError(
            "is_preset=True is reserved for system seeds; guild_id must be None",
        )

    # Refuse to flip an existing preset row's ``is_preset`` to FALSE
    # from a guild-scope upsert (a name collision on the same scope
    # would otherwise downgrade a seeded preset).
    if not is_preset and guild_id is None and scope == "system":
        existing = await ai_db.list_instruction_profiles(None, scope="system")
        for row in existing:
            if row.get("name") == name and row.get("is_preset"):
                raise UnauthorizedAIInstructionMutationError(
                    f"cannot overwrite preset row {name!r} with is_preset=False",
                )

    mutation_id = uuid.uuid4().hex
    profile_id = await ai_db.upsert_instruction_profile(
        guild_id=guild_id,
        name=name,
        body=body,
        scope=scope,
        feature_key=feature_key,
        created_by=actor_id,
        is_preset=is_preset,
    )
    if guild_id is not None:
        await ai_db.bump_generation(guild_id)
        ai_natural_language_policy.invalidate(guild_id)
    event_emitted = await _emit(
        "ai.instruction.profile_changed",
        guild_id,
        mutation_id,
    )
    return AIInstructionMutationResult(
        mutation_id=mutation_id,
        profile_id=profile_id,
        guild_id=guild_id,
        scope=scope,
        name=name,
        event_emitted=event_emitted,
    )


async def delete_profile(profile_id: int, *, actor: Any) -> int:
    """Remove a profile row; returns the deleted row count."""
    _check_admin(actor)
    profile = await ai_db.get_instruction_profile(profile_id)
    if profile is None:
        return 0
    deleted = await ai_db.delete_instruction_profile(profile_id)
    if profile.get("guild_id") is not None:
        await ai_db.bump_generation(int(profile["guild_id"]))
        ai_natural_language_policy.invalidate(int(profile["guild_id"]))
    return deleted


async def _emit(event: str, guild_id: int | None, mutation_id: str) -> bool:
    try:
        from core.events import bus

        await bus.emit(event, guild_id=guild_id, mutation_id=mutation_id)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("ai_instruction_mutation: event emit failed: %s", exc)
        return False


__all__ = [
    "AIInstructionMutationError",
    "AIInstructionMutationResult",
    "InvalidAIInstructionValueError",
    "UnauthorizedAIInstructionMutationError",
    "delete_profile",
    "upsert_profile",
]
