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

import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Final

from services import ai_natural_language_policy
from utils.db import ai as ai_db

logger = logging.getLogger("bot.services.ai_policy_mutation")


# ---------------------------------------------------------------------------
# UNCHANGED sentinel (PR-C-pre)
# ---------------------------------------------------------------------------
#
# Three-state per optional column on partial updates:
#
#   * concrete value (int, bool, str)     → "set this column".
#   * ``None``                            → "clear this column" (NULL).
#   * :data:`UNCHANGED`                   → "preserve existing column".
#
# The mutation functions accept :data:`UNCHANGED` (the default for
# optional fields). Sentinel fields are listed in ``unchanged_fields``
# when handed to ``ai_db.upsert_*``; the DB layer omits them from
# the ``EXCLUDED`` SET on conflict. On an INSERT path the sentinel
# means NULL (there is nothing to preserve).
#
# Before PR-C-pre, the channel/category modals passed ``None`` for
# every field they did not own — which silently cleared
# ``instruction_profile_id`` on every save. That footgun is fixed
# here at the chokepoint so every existing and future caller is safe
# by default.


class _Unchanged:
    """Singleton sentinel — compared with ``is`` only."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debug only
        return "UNCHANGED"


UNCHANGED: Final[_Unchanged] = _Unchanged()


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
    """Return ``actor.id`` if administrator-tier (or platform owner); raise otherwise."""
    if actor is None:
        raise UnauthorizedAIPolicyMutationError("actor is required")
    # Platform-owner override: the configured bot owner configures the AI in any
    # guild, even without Discord admin there (single source: config).
    from config import is_platform_owner

    actor_id = getattr(actor, "id", None)
    if is_platform_owner(actor_id):
        return actor_id
    perms = getattr(actor, "guild_permissions", None)
    if perms is None or not getattr(perms, "administrator", False):
        raise UnauthorizedAIPolicyMutationError(
            "ai policy mutations require administrator permission",
        )
    return actor_id


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
    if default_provider not in ("deterministic", "openai", "anthropic"):
        raise InvalidAIPolicyValueError(
            "default_provider must be 'deterministic', 'openai', or "
            f"'anthropic', got {default_provider!r}",
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


def _resolve_optional(value: Any) -> tuple[Any, bool]:
    """Translate UNCHANGED into ``(None, True)``; otherwise ``(value, False)``.

    Returns ``(insert_value, is_unchanged)``. The DB layer uses
    ``insert_value`` for the binding (NULL on insert) and skips the
    column from the ``EXCLUDED`` SET when ``is_unchanged`` is True.
    """
    if value is UNCHANGED:
        return None, True
    return value, False


async def set_channel_policy(
    guild_id: int,
    channel_id: int,
    *,
    mode: str | _Unchanged = UNCHANGED,
    min_level: int | None | _Unchanged = UNCHANGED,
    cooldown_seconds: int | None | _Unchanged = UNCHANGED,
    instruction_profile_id: int | None | _Unchanged = UNCHANGED,
    actor: Any,
) -> AIPolicyMutationResult:
    actor_id = _check_admin(actor)
    if mode is UNCHANGED:
        raise InvalidAIPolicyValueError(
            "channel mode is required on upsert (UNCHANGED not supported "
            "for the mode column because the row must always carry a mode)",
        )
    if mode not in _VALID_CHANNEL_MODES:
        raise InvalidAIPolicyValueError(
            f"channel mode must be one of {sorted(_VALID_CHANNEL_MODES)}, got {mode!r}",
        )
    min_level_val, min_level_unchanged = _resolve_optional(min_level)
    cooldown_val, cooldown_unchanged = _resolve_optional(cooldown_seconds)
    profile_val, profile_unchanged = _resolve_optional(instruction_profile_id)

    unchanged_fields: set[str] = set()
    if min_level_unchanged:
        unchanged_fields.add("min_level")
    if cooldown_unchanged:
        unchanged_fields.add("cooldown_seconds")
    if profile_unchanged:
        unchanged_fields.add("instruction_profile_id")

    mutation_id = uuid.uuid4().hex
    await ai_db.upsert_channel_policy(
        guild_id,
        channel_id,
        mode=mode,
        min_level=min_level_val,
        cooldown_seconds=cooldown_val,
        instruction_profile_id=profile_val,
        updated_by=actor_id,
        unchanged_fields=unchanged_fields,
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
    mode: str | _Unchanged = UNCHANGED,
    min_level: int | None | _Unchanged = UNCHANGED,
    cooldown_seconds: int | None | _Unchanged = UNCHANGED,
    instruction_profile_id: int | None | _Unchanged = UNCHANGED,
    actor: Any,
) -> AIPolicyMutationResult:
    actor_id = _check_admin(actor)
    if mode is UNCHANGED:
        raise InvalidAIPolicyValueError(
            "category mode is required on upsert (UNCHANGED not supported "
            "for the mode column because the row must always carry a mode)",
        )
    if mode not in _VALID_CHANNEL_MODES:
        raise InvalidAIPolicyValueError(
            f"category mode must be one of {sorted(_VALID_CHANNEL_MODES)}, "
            f"got {mode!r}",
        )
    min_level_val, min_level_unchanged = _resolve_optional(min_level)
    cooldown_val, cooldown_unchanged = _resolve_optional(cooldown_seconds)
    profile_val, profile_unchanged = _resolve_optional(instruction_profile_id)

    unchanged_fields: set[str] = set()
    if min_level_unchanged:
        unchanged_fields.add("min_level")
    if cooldown_unchanged:
        unchanged_fields.add("cooldown_seconds")
    if profile_unchanged:
        unchanged_fields.add("instruction_profile_id")

    mutation_id = uuid.uuid4().hex
    await ai_db.upsert_category_policy(
        guild_id,
        category_id,
        mode=mode,
        min_level=min_level_val,
        cooldown_seconds=cooldown_val,
        instruction_profile_id=profile_val,
        updated_by=actor_id,
        unchanged_fields=unchanged_fields,
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
    decision: str | _Unchanged = UNCHANGED,
    min_level_override: int | None | _Unchanged = UNCHANGED,
    bypass_cooldown: bool | _Unchanged = UNCHANGED,
    actor: Any,
) -> AIPolicyMutationResult:
    actor_id = _check_admin(actor)
    if decision is UNCHANGED:
        raise InvalidAIPolicyValueError(
            "role decision is required on upsert (UNCHANGED not supported "
            "for the decision column because the row must always carry one)",
        )
    if decision not in _VALID_ROLE_DECISIONS:
        raise InvalidAIPolicyValueError(
            f"role decision must be one of {sorted(_VALID_ROLE_DECISIONS)}, "
            f"got {decision!r}",
        )
    min_level_val, min_level_unchanged = _resolve_optional(min_level_override)
    bypass_val, bypass_unchanged = _resolve_optional(bypass_cooldown)
    if min_level_val is not None and min_level_val < 0:
        raise InvalidAIPolicyValueError("min_level_override must be >= 0")

    unchanged_fields: set[str] = set()
    if min_level_unchanged:
        unchanged_fields.add("min_level_override")
    if bypass_unchanged:
        unchanged_fields.add("bypass_cooldown")

    mutation_id = uuid.uuid4().hex
    await ai_db.upsert_role_policy(
        guild_id,
        role_id,
        decision=decision,
        min_level_override=min_level_val,
        # NB: on INSERT path with sentinel, the column gets FALSE
        # (matching its default) rather than NULL — bypass_cooldown is
        # NOT NULL.
        bypass_cooldown=bool(bypass_val) if not bypass_unchanged else False,
        updated_by=actor_id,
        unchanged_fields=unchanged_fields,
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


# ---------------------------------------------------------------------------
# Projection from legacy AI scalar settings into the typed policy row
# ---------------------------------------------------------------------------


# Maps each canonical M1 settings_key to the ai_guild_policy column it
# projects into.  ai_guild_instruction_profile is intentionally NOT in
# this map — it stores a free-text body that needs a typed
# ai_instruction_profile row, which is a separate projection path
# (see services/ai_instruction_mutation.py) deferred to a follow-up.
_LEGACY_TO_POLICY_FIELD: dict[str, str] = {
    "ai_enabled": "enabled",
    "ai_natural_language_enabled": "natural_language_enabled",
    "ai_default_provider": "default_provider",
    "ai_default_model": "default_model",
    "ai_minimum_level_default": "minimum_level_default",
    "ai_cooldown_seconds": "cooldown_seconds",
    "ai_fresh_user_mention_allowance": "fresh_user_mention_allowance",
}


def projectable_keys() -> frozenset[str]:
    """Return the set of legacy settings_keys this module projects.

    Exposed so callers (e.g. the settings mutation pipeline) can decide
    whether a given mutation triggers projection without reaching into
    the private map.
    """
    return frozenset(_LEGACY_TO_POLICY_FIELD)


async def project_from_legacy_settings(
    guild_id: int,
    actor: Any,
    *,
    mutation_id: str,
) -> AIPolicyMutationResult | None:
    """Project the seven mapped AI scalar settings into ``ai_guild_policy``.

    Called by :class:`services.settings_mutation.SettingsMutationPipeline`
    after a successful legacy-KV write for ``subsystem='ai'`` so the
    typed policy table stays in sync with the UI.

    Best-effort: any failure is logged at WARNING with a structured
    diagnostic payload and a best-effort ``ai.policy.projection_failed``
    bus event. The raw setting value is **never** included in the log
    or the event payload because it may be a user-authored instruction
    body or other operator text.

    Returns the underlying :class:`AIPolicyMutationResult` on success,
    or ``None`` on suppressed failure.
    """
    from services import settings_resolution

    # Pull every mapped scalar from settings_resolution. The legacy KV
    # cache for the just-mutated key was invalidated by the pipeline
    # before this helper ran, so the freshly-written value is visible.
    resolved: dict[str, Any] = {}
    try:
        for legacy_key, policy_field in _LEGACY_TO_POLICY_FIELD.items():
            res = await settings_resolution.resolve_setting(
                guild_id,
                "ai",
                _legacy_key_to_spec_name(legacy_key),
            )
            # `None` only if the spec was undeclared — defensive; the
            # AI subsystem schema covers all seven.
            if res is None:
                continue
            resolved[policy_field] = res.value
    except Exception as exc:  # noqa: BLE001 — see structured log below
        await _log_projection_failure(
            guild_id=guild_id,
            settings_key=None,
            mutation_id=mutation_id,
            exc=exc,
        )
        return None

    # Read the current typed row so we keep guild_instruction_profile_id
    # (which has no scalar projection target) intact.
    current = await ai_db.get_guild_policy(guild_id)
    instruction_profile_id = (
        current.get("guild_instruction_profile_id") if current else None
    )

    # Bounded retry: the projection is a *separate* write from the (already
    # committed) legacy-KV settings write, so a transient failure here would
    # otherwise become durable silent drift — the audit says "changed" but the
    # typed ``ai_guild_policy`` row the runtime resolver reads keeps the old
    # value. Retrying self-heals the dominant failure mode (a transient DB blip);
    # a persistent failure still surfaces to the caller as a ``None`` return so
    # the settings pipeline can flag it (Stage-2 walk bug #1).
    _backoffs = (0.05, 0.2)
    for attempt in range(len(_backoffs) + 1):
        try:
            return await set_guild_policy(
                guild_id,
                enabled=bool(resolved.get("enabled", False)),
                natural_language_enabled=bool(
                    resolved.get("natural_language_enabled", False),
                ),
                default_provider=str(
                    resolved.get("default_provider", "deterministic")
                    or "deterministic",
                ),
                default_model=str(resolved.get("default_model", "") or ""),
                minimum_level_default=int(resolved.get("minimum_level_default", 2)),
                cooldown_seconds=int(resolved.get("cooldown_seconds", 30)),
                fresh_user_mention_allowance=int(
                    resolved.get("fresh_user_mention_allowance", 1),
                ),
                guild_instruction_profile_id=instruction_profile_id,
                actor=actor,
            )
        except Exception as exc:  # noqa: BLE001 — see structured log below
            if attempt >= len(_backoffs):
                await _log_projection_failure(
                    guild_id=guild_id,
                    settings_key=None,
                    mutation_id=mutation_id,
                    exc=exc,
                )
                return None
            await asyncio.sleep(_backoffs[attempt])
    return None  # pragma: no cover — loop always returns on the final attempt


def _legacy_key_to_spec_name(legacy_key: str) -> str:
    """Translate a settings_keys.ai constant into the SettingSpec name.

    M1 named the spec the same as the key (e.g.
    ``settings_key='ai_enabled'`` for ``SettingSpec(name='ai_enabled')``),
    so this is the identity function today. Kept as a named helper so
    the projection contract has a single seam if the two ever diverge.
    """
    return legacy_key


async def _log_projection_failure(
    *,
    guild_id: int,
    settings_key: str | None,
    mutation_id: str,
    exc: BaseException,
) -> None:
    """Emit the structured drift-visibility WARNING + best-effort event.

    Fields are documented in the post-PR-#310 hardening plan. The raw
    setting value is intentionally omitted because it may carry a free-
    text instruction body.
    """
    exc_type = type(exc).__name__
    exc_message = str(exc)[:200]
    logger.warning(
        "ai_policy_mutation: projection failed",
        extra={
            "guild_id": guild_id,
            "subsystem": "ai",
            "settings_key": settings_key,
            "mutation_id": mutation_id,
            "exc_type": exc_type,
            "exc_message": exc_message,
        },
    )
    try:
        from core.events import bus

        await bus.emit(
            "ai.policy.projection_failed",
            guild_id=guild_id,
            settings_key=settings_key,
            mutation_id=mutation_id,
            exc_type=exc_type,
        )
    except Exception:  # noqa: BLE001 — bus must never amplify drift
        logger.debug(
            "ai_policy_mutation: ai.policy.projection_failed emit failed",
            exc_info=True,
        )


__all__ = [
    "AIPolicyMutationError",
    "AIPolicyMutationResult",
    "InvalidAIPolicyValueError",
    "UnauthorizedAIPolicyMutationError",
    "project_from_legacy_settings",
    "projectable_keys",
    "set_category_policy",
    "set_channel_policy",
    "set_guild_policy",
    "set_role_policy",
]
