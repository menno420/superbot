"""Settings mutation pipeline — S4 of the Global Settings & Customization Manager.

The canonical write path for scalar guild settings declared by
:class:`core.runtime.subsystem_schema.SettingSpec`.  Mirrors the
contract of :class:`services.binding_mutation.BindingMutationPipeline`
and :class:`services.participation_mutation.ParticipationMutationPipeline`.

Eleven-step contract per :meth:`SettingsMutationPipeline.set_value`:

  1. Resolve subsystem + ``SettingSpec``.
  2. Reject unknown subsystem / setting / unmigrateable setting.
  3. Validate actor / capability.
  4. Coerce the incoming value to the declared ``SettingSpec.value_type``.
  5. Run the ``SettingSpec.validator`` (if any).
  6. Read the previous value through :func:`services.settings_resolution.resolve_setting`.
  7. Serialise the coerced value to the legacy-KV string form.
  8. DB write + audit insert in a single asyncpg transaction.
  9. Invalidate the per-guild cache key via
     :func:`utils.guild_config_accessors.invalidate_setting_value`.
 10. Emit advisory ``"settings.changed"`` event after commit (best-effort).
 11. Return typed :class:`SettingsMutationResult`.

If event emission raises **after** a successful DB commit, the error
is logged but not re-raised; the DB state is correct.  Matches the
best-effort emission contract used by every sibling mutation pipeline.

Hard limits for S4:

  * No Settings Manager UI integration — that is S5.
  * No bindings, no resource provisioning, no access-policy writes,
    no participation writes, no list-setting writes.
  * Authority is capability-native (ADR-005 A1): the actor must hold the
    capability declared by ``SettingSpec.capability_required``, resolved via
    :func:`governance.capability.actor_holds_capability`.  ``system`` /
    ``backfill`` bypass; an empty capability resolves to the administrator floor.
  * The :data:`core.runtime.feature_flags.SETTINGS_MUTATION_PRIMARY` flag is a
    real operator kill-switch (ADR-005 F1): mutations proceed by default and are
    refused only when an operator explicitly turns it OFF (fail-open on eval error).

Cycle discipline (mirrors
:mod:`services.platform_consistency` and
:mod:`services.settings_resolution`): all cross-package imports are
function-local.  Top-level imports are stdlib only.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from services.audit_events import emit_audit_action

logger = logging.getLogger("bot.services.settings_mutation")


# ---------------------------------------------------------------------------
# Catalogued event name (registered in core/events_catalogue.py).
# ---------------------------------------------------------------------------

EVT_SETTINGS_CHANGED = "settings.changed"


# ---------------------------------------------------------------------------
# Recognized literal sets — mirror migration 029 CHECK constraints (the
# actor_type set was widened to include ``setup_delegate`` in migration 069,
# Q-0098). Alignment tests in tests/unit/invariants/ pin these to the SQL CHECK
# literals so a drift on either side fails CI.
# ---------------------------------------------------------------------------

_ALLOWED_ACTOR_TYPES: frozenset[str] = frozenset(
    {"user", "moderator", "admin", "system", "backfill", "setup_delegate"},
)
_ALLOWED_MUTATION_TYPES: frozenset[str] = frozenset({"set_value"})

# Write scopes: ``"guild"`` (per-guild, capability-gated) or ``"global"``
# (the owner's cross-server default at GLOBAL_GUILD_ID, owner-gated).
_ALLOWED_SCOPES: frozenset[str] = frozenset({"guild", "global"})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SettingsMutationError(Exception):
    """Base class for failures from :class:`SettingsMutationPipeline`."""


class UnknownSubsystemError(SettingsMutationError):
    """Raised when the mutation targets a subsystem not in SUBSYSTEMS."""


class UndeclaredSettingError(SettingsMutationError):
    """Raised when ``name`` is not declared as a ``SettingSpec`` for the
    given subsystem.
    """


class UnmigrateableSettingError(SettingsMutationError):
    """Raised when the ``SettingSpec`` has no ``settings_key``.

    The pipeline refuses to mutate settings without a canonical key
    because there is no authoritative storage location yet.  Such
    settings are surfaced by
    :data:`core.runtime.settings_registry.RegistryFindings.settings_without_settings_key`.
    """


class SettingsCoercionError(SettingsMutationError):
    """Raised when the incoming value cannot be coerced to the declared
    ``SettingSpec.value_type``.
    """


class SettingsValidationError(SettingsMutationError):
    """Raised when ``SettingSpec.validator`` rejects the coerced value."""


class UnauthorizedSettingsMutationError(SettingsMutationError):
    """Raised when the actor lacks the capability declared by
    :data:`SettingSpec.capability_required` (ADR-005 A1).
    """


class SettingsMutationDisabledError(SettingsMutationError):
    """Raised when the settings mutation pipeline is disabled via the
    :data:`core.runtime.feature_flags.SETTINGS_MUTATION_PRIMARY` operator
    kill-switch (an explicit operator OFF; ADR-005 F1).
    """


class InvalidActorTypeError(SettingsMutationError):
    """Raised when ``actor_type`` is not in :data:`_ALLOWED_ACTOR_TYPES`."""


class InvalidScopeError(SettingsMutationError):
    """Raised when ``scope`` is not in :data:`_ALLOWED_SCOPES`."""


# ---------------------------------------------------------------------------
# Typed result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SettingsMutationResult:
    """Outcome of a successful (or partially successful) mutation.

    ``event_emitted`` is ``False`` when the post-commit ``settings.changed``
    emission raised; the DB state is still correct.

    ``projection_committed`` is ``False`` only for an ``ai`` subsystem write
    whose typed-policy projection (into ``ai_guild_policy``, which the runtime
    resolver reads) failed after retries — the legacy KV write + audit still
    committed, so this flags the silent-drift window rather than swallowing it
    (Stage-2 walk bug #1). ``True`` for every non-``ai`` write and every
    successful projection.
    """

    mutation_id: str
    guild_id: int
    subsystem: str
    name: str
    settings_key: str
    old_value: Any
    new_value: Any
    old_value_raw: str | None
    new_value_raw: str
    committed_at: datetime
    event_emitted: bool
    projection_committed: bool = True


# ---------------------------------------------------------------------------
# Coercion + serialisation helpers
# ---------------------------------------------------------------------------


def _coerce_for_write(value: Any, value_type: type) -> tuple[Any, bool, str]:
    """Coerce an incoming value to ``value_type``.

    Accepts either a string (the legacy-KV shape) or an already-typed
    value.  Returns ``(coerced, ok, diagnostic)``.  When ``ok`` is
    ``False`` the caller raises :class:`SettingsCoercionError` with
    the diagnostic.
    """
    # Fast paths for already-typed values.  ``bool`` is checked before
    # ``int`` because ``True/False`` are ``int`` subclasses in Python.
    if value_type is bool and isinstance(value, bool):
        return value, True, ""
    if value_type is int and isinstance(value, int) and not isinstance(value, bool):
        return value, True, ""
    if (
        value_type is float
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
    ):
        return float(value), True, ""
    if value_type is str and isinstance(value, str):
        return value, True, ""

    # Fall back to the read-path string coercer for consistency with
    # services.settings_resolution.
    from services.settings_resolution import _coerce as _resolution_coerce

    return _resolution_coerce(str(value), value_type)


def _serialise(value: Any, value_type: type) -> str:
    """Convert a coerced typed value to its legacy-KV string form.

    Mirrors the read-path inverse — :func:`services.settings_resolution._coerce`
    reads ``"true"`` / ``"false"`` for booleans, so the writer must
    emit those exact spellings.
    """
    if value_type is bool:
        return "true" if value else "false"
    return str(value)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class SettingsMutationPipeline:
    """Centralised orchestration for scalar ``SettingSpec`` writes.

    Instances are stateless — create one per mutation request.  The
    single public method :meth:`set_value` follows the 11-step contract
    documented in the module docstring.  Callers MUST NOT touch
    :mod:`utils.db.settings_audit`'s mutation primitive directly nor
    invoke ``db.set_setting`` for keys declared by a ``SettingSpec``;
    the pipeline is the only legitimate writer.
    """

    def __init__(self) -> None:
        # No instance state.
        pass

    async def set_value(
        self,
        guild: Any,
        subsystem: str,
        name: str,
        value: Any,
        actor: Any,
        *,
        actor_type: str = "user",
        scope: str = "guild",
    ) -> SettingsMutationResult:
        """Write ``value`` to ``(subsystem, name)`` at the requested scope.

        Two scopes:

        * ``scope="guild"`` (default) — a per-guild write on ``guild``,
          authorised by ``spec.capability_required`` (a server admin).
        * ``scope="global"`` — the owner's cross-server default, stored at
          ``GLOBAL_GUILD_ID`` (``guild_id = 0``) and resolved as the
          per-guild → **global** → spec-default fallback by
          :func:`services.settings_resolution.resolve_setting`. Authorised
          **owner-only** (``config.BOT_OWNER_USER_ID``); ``guild`` may be
          ``None``.

        Args:
            guild: A ``discord.Guild`` (typed as ``Any`` so this module
                does not import ``discord``). May be ``None`` for a
                ``scope="global"`` write.
            subsystem: Subsystem name from ``SUBSYSTEMS``.
            name: ``SettingSpec.name``.
            value: Incoming value (string or already-typed).  The
                pipeline coerces and validates it.
            actor: A ``discord.Member`` representing the caller, or
                ``None`` for ``actor_type='system'`` writes.
            actor_type: One of the literals in
                :data:`_ALLOWED_ACTOR_TYPES`.
            scope: ``"guild"`` (default) or ``"global"``.

        Raises:
            UnknownSubsystemError: ``subsystem`` is not in
                ``SUBSYSTEMS``.
            UndeclaredSettingError: ``name`` is not declared as a
                ``SettingSpec`` for ``subsystem``.
            UnmigrateableSettingError: The ``SettingSpec`` has no
                ``settings_key`` — no canonical storage exists.
            SettingsCoercionError: ``value`` cannot be coerced to the
                declared type.
            SettingsValidationError: ``SettingSpec.validator`` rejected
                the coerced value.
            UnauthorizedSettingsMutationError: for ``scope="guild"``,
                ``actor`` lacks the capability declared by
                ``spec.capability_required``; for ``scope="global"``,
                ``actor`` is not the bot owner.
            SettingsMutationDisabledError: an operator has turned the
                ``SETTINGS_MUTATION_PRIMARY`` kill-switch OFF.
            InvalidActorTypeError: ``actor_type`` is not in the
                allowed set.
            InvalidScopeError: ``scope`` is not ``"guild"`` / ``"global"``.
        """
        from utils.db.settings import GLOBAL_GUILD_ID

        self._validate_scope(scope)
        is_global = scope == "global"
        effective_guild_id = GLOBAL_GUILD_ID if is_global else guild.id

        spec = self._resolve_spec(subsystem, name)
        self._validate_actor_type(actor_type)
        if is_global:
            self._validate_global_authority(actor, actor_type)
        else:
            await self._validate_authority(spec, guild, actor, actor_type)
        await self._check_mutation_enabled(effective_guild_id)

        coerced, ok, coerce_diag = _coerce_for_write(value, spec.value_type)
        if not ok:
            raise SettingsCoercionError(
                f"cannot coerce value={value!r} to {spec.value_type.__name__}: "
                f"{coerce_diag}",
            )
        if spec.validator is not None:
            try:
                spec.validator(coerced)
            except (ValueError, TypeError) as exc:
                raise SettingsValidationError(
                    f"validator rejected value={coerced!r} for "
                    f"{subsystem}.{name}: {exc}",
                ) from exc

        new_value_raw = _serialise(coerced, spec.value_type)
        old_value, old_value_raw = await self._read_previous(
            effective_guild_id,
            subsystem,
            name,
        )

        mutation_id = str(uuid.uuid4())
        actor_id = getattr(actor, "id", None) if actor is not None else None

        # Steps 8-9: DB write + audit + cache invalidate.
        try:
            from utils.db import settings_audit

            await settings_audit.set_value_with_audit(
                guild_id=effective_guild_id,
                subsystem=subsystem,
                name=name,
                settings_key=spec.settings_key,
                prev_value_raw=old_value_raw,
                new_value_raw=new_value_raw,
                actor_id=actor_id,
                actor_type=actor_type,
                mutation_id=mutation_id,
                mutation_type="set_value",
            )
        except Exception:
            logger.exception(
                "SettingsMutationPipeline.set_value: DB transaction "
                "failed for (guild=%d, subsystem=%r, name=%r); no cache "
                "invalidation, no event emission.",
                effective_guild_id,
                subsystem,
                name,
            )
            raise

        committed_at = _now_utc()
        self._invalidate_cache(effective_guild_id, spec.settings_key)

        # Post-PR-#310 hardening: AI subsystem scalars project into the
        # typed ai_guild_policy table so the runtime resolver (which
        # reads only the typed row) tracks UI mutations. The projection is a
        # *separate* write from the (already committed) legacy-KV write above;
        # the projection helper retries transient failures and returns ``None``
        # only after exhausting them. We surface that ``None`` here rather than
        # discarding it — a failed projection means the audit says "changed"
        # while the runtime policy silently didn't, so we flag it loudly on the
        # result (``projection_committed=False``) instead of swallowing the
        # drift (Stage-2 walk bug #1). Skipped for a global write — the AI
        # runtime resolver is per-guild (it reads ``ai_guild_policy`` by
        # guild_id), so a guild_id=0 projection would only create a phantom row
        # that nothing reads.
        projection_committed = True
        if subsystem == "ai" and not is_global:
            from services import ai_policy_mutation

            if spec.settings_key in ai_policy_mutation.projectable_keys():
                projection_result = (
                    await ai_policy_mutation.project_from_legacy_settings(
                        effective_guild_id,
                        actor,
                        mutation_id=mutation_id,
                    )
                )
                projection_committed = projection_result is not None
                if not projection_committed:
                    logger.error(
                        "settings_mutation: AI typed-policy projection FAILED "
                        "after retries (guild=%d, subsystem=%r, name=%r, key=%r, "
                        "mutation_id=%s); the legacy KV write + audit committed "
                        "but the runtime resolver row is now stale — DRIFT.",
                        effective_guild_id,
                        subsystem,
                        name,
                        spec.settings_key,
                        mutation_id,
                    )

        # Phase 9c.2: companion ``audit.action_recorded`` event emitted
        # via the shared publisher. Best-effort; failure is logged
        # inside the helper, not propagated.
        await emit_audit_action(
            mutation_id=mutation_id,
            subsystem=subsystem,
            mutation_type="set_value",
            target=f"setting:{subsystem}.{name}",
            scope=scope,
            guild_id=None if is_global else effective_guild_id,
            prev_value=old_value_raw,
            new_value=new_value_raw,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=committed_at,
        )

        # Step 10: best-effort event emission.
        event_emitted = await self._emit_event(
            mutation_id=mutation_id,
            guild_id=effective_guild_id,
            subsystem=subsystem,
            name=name,
            settings_key=spec.settings_key,
            old_value_raw=old_value_raw,
            new_value_raw=new_value_raw,
            committed_at=committed_at,
        )

        return SettingsMutationResult(
            mutation_id=mutation_id,
            guild_id=effective_guild_id,
            subsystem=subsystem,
            name=name,
            settings_key=spec.settings_key,
            old_value=old_value,
            new_value=coerced,
            old_value_raw=old_value_raw,
            new_value_raw=new_value_raw,
            committed_at=committed_at,
            event_emitted=event_emitted,
            projection_committed=projection_committed,
        )

    # ------------------------------------------------------------------
    # Step helpers
    # ------------------------------------------------------------------

    def _resolve_spec(self, subsystem: str, name: str) -> Any:
        """Steps 1-2: subsystem declared, setting declared, migrateable."""
        from core.runtime.subsystem_schema import get_schema
        from utils.subsystem_registry import SUBSYSTEMS

        if subsystem not in SUBSYSTEMS:
            raise UnknownSubsystemError(
                f"unknown subsystem {subsystem!r}; "
                f"not in utils.subsystem_registry.SUBSYSTEMS",
            )

        schema = get_schema(subsystem)
        if schema is None:
            raise UndeclaredSettingError(
                f"subsystem {subsystem!r} has no registered SubsystemSchema; "
                f"register one in the cog's cog_load() before mutating",
            )

        for spec in schema.settings:
            if spec.name == name:
                if not spec.settings_key:
                    raise UnmigrateableSettingError(
                        f"setting {subsystem!r}/{name!r} has no settings_key "
                        "declared; cannot be mutated until migrated to a "
                        "canonical key",
                    )
                return spec

        declared_names = [s.name for s in schema.settings]
        raise UndeclaredSettingError(
            f"setting {name!r} not declared in SubsystemSchema for "
            f"{subsystem!r}; declared settings: {declared_names}",
        )

    def _validate_actor_type(self, actor_type: str) -> None:
        if actor_type not in _ALLOWED_ACTOR_TYPES:
            raise InvalidActorTypeError(
                f"actor_type={actor_type!r} not in {sorted(_ALLOWED_ACTOR_TYPES)}",
            )

    def _validate_scope(self, scope: str) -> None:
        if scope not in _ALLOWED_SCOPES:
            raise InvalidScopeError(
                f"scope={scope!r} not in {sorted(_ALLOWED_SCOPES)}",
            )

    def _validate_global_authority(self, actor: Any, actor_type: str) -> None:
        """Step 3 (global scope): owner-only authority.

        A global write sets the owner's cross-server default, so it is
        gated to the bot owner (``config.BOT_OWNER_USER_ID``) rather than a
        per-guild capability. ``actor_type='system'`` / ``'backfill'``
        bypass (scripted ops / migrations), mirroring the per-guild path.
        """
        if actor_type in ("system", "backfill"):
            return
        from config import is_platform_owner

        actor_id = getattr(actor, "id", None) if actor is not None else None
        if not is_platform_owner(actor_id):
            raise UnauthorizedSettingsMutationError(
                "global settings scope is owner-only "
                f"(actor_id={actor_id}, requires BOT_OWNER_USER_ID)",
            )

    async def _validate_authority(
        self,
        spec: Any,
        guild: Any,
        actor: Any,
        actor_type: str,
    ) -> None:
        """Step 3: capability-native authority (ADR-005 A1).

        ``actor_type='system'`` and ``'backfill'`` bypass the check (scripted
        ops and migrations).  All other actor types must hold the capability
        declared by ``spec.capability_required``; an empty capability resolves
        to the administrator floor (see :mod:`governance.capability`).
        """
        from governance.capability import actor_holds_capability

        decision = await actor_holds_capability(
            actor,
            guild,
            spec.capability_required,
            actor_type=actor_type,
        )
        if not decision.allowed:
            raise UnauthorizedSettingsMutationError(decision.reason)

    async def _check_mutation_enabled(self, guild_id: int) -> None:
        """F1 kill-switch (ADR-005): refuse only when an operator has
        explicitly disabled the pipeline via ``SETTINGS_MUTATION_PRIMARY``.

        Defaults to ALLOW (the declared-off default is *not* a disable) and
        **fails open** — a flag-store outage must never brick settings writes.
        """
        from core.runtime import feature_flags

        try:
            disabled = await feature_flags.is_operator_disabled(
                feature_flags.SETTINGS_MUTATION_PRIMARY.name,
                guild_id,
            )
        except Exception:  # pragma: no cover - defensive; evaluator self-protects
            logger.warning(
                "settings_mutation: kill-switch flag eval raised; "
                "allowing (fail-open).",
            )
            return
        if disabled:
            raise SettingsMutationDisabledError(
                "settings mutation pipeline is disabled for "
                f"guild={guild_id} (operator turned "
                f"{feature_flags.SETTINGS_MUTATION_PRIMARY.name!r} OFF)",
            )

    async def _read_previous(
        self,
        guild_id: int,
        subsystem: str,
        name: str,
    ) -> tuple[Any, str | None]:
        """Step 6: read the previous value via the canonical resolver.

        Returns ``(typed_value, raw_string_or_None)``.  ``None`` raw
        indicates no KV row existed before this mutation; the typed
        value is the spec default in that case. ``guild_id`` is the
        **scope** id — the real guild for ``scope="guild"`` or
        ``GLOBAL_GUILD_ID`` for ``scope="global"`` — so the audit reads
        the value at the same scope it is about to write.
        """
        from services.settings_resolution import resolve_setting

        # ``include_global=False`` keeps the audit ``prev_value`` scope-local:
        # a per-guild write records the per-guild value it replaced, never an
        # inherited global default (the global tier is a read-time fallback,
        # not a value this guild ever "had"). For a global write it reads the
        # global row directly at GLOBAL_GUILD_ID.
        resolution = await resolve_setting(
            guild_id,
            subsystem,
            name,
            include_global=False,
        )
        if resolution is None:
            # Defensive — _resolve_spec already verified the spec exists.
            return None, None
        # resolution.raw is "" when the resolver served the default
        # because the KV row was absent.  Map that to None so the audit
        # row distinguishes "no row existed" from "row was empty string".
        raw = resolution.raw if resolution.raw else None
        return resolution.value, raw

    def _invalidate_cache(self, guild_id: int, settings_key: str) -> None:
        """Step 9: drop the cached KV value for this specific key.

        Routes through the typed accessor introduced in S3 so the F-1
        invariant (`test_guild_config_typed_accessors`) stays green.
        """
        from utils.guild_config_accessors import invalidate_setting_value

        invalidate_setting_value(guild_id, settings_key)

    async def _emit_event(
        self,
        *,
        mutation_id: str,
        guild_id: int,
        subsystem: str,
        name: str,
        settings_key: str,
        old_value_raw: str | None,
        new_value_raw: str,
        committed_at: datetime,
    ) -> bool:
        """Step 10: best-effort ``settings.changed`` emission.

        Returns ``True`` on success, ``False`` when emission raised.
        Emission failure after a successful DB commit is logged with
        the ``mutation_id`` and swallowed — DB state is authoritative.
        """
        from core.events import bus

        try:
            await bus.emit(
                EVT_SETTINGS_CHANGED,
                mutation_id=mutation_id,
                guild_id=guild_id,
                subsystem=subsystem,
                name=name,
                settings_key=settings_key,
                old_value_raw=old_value_raw,
                new_value_raw=new_value_raw,
                occurred_at=committed_at.isoformat(),
            )
        except Exception:
            logger.exception(
                "SettingsMutationPipeline._emit_event: emission failed for "
                "mutation_id=%s; DB state is correct, event lost.",
                mutation_id,
            )
            return False
        return True


def _now_utc() -> datetime:
    """Return a tz-aware "now" — INV-N forbids bare datetime.utcnow."""
    return datetime.now(timezone.utc)


__all__ = [
    "EVT_SETTINGS_CHANGED",
    "InvalidActorTypeError",
    "InvalidScopeError",
    "SettingsCoercionError",
    "SettingsMutationError",
    "SettingsMutationPipeline",
    "SettingsMutationResult",
    "SettingsValidationError",
    "UnauthorizedSettingsMutationError",
    "UndeclaredSettingError",
    "UnknownSubsystemError",
    "UnmigrateableSettingError",
]
