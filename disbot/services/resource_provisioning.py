"""Resource provisioning pipeline — S4.5 of the Global Settings & Customization Manager.

The canonical creator/binder of Discord resources (channels, roles,
categories) for subsystem use.  Wraps:

* :mod:`core.runtime.guild_resources` — pure infrastructure helpers
  ``ensure_channel`` / ``ensure_role`` / ``ensure_category`` that
  perform the actual Discord API calls.  No policy lives there.
* :mod:`services.binding_mutation` — writes the binding row at step
  8 of the contract.  This pipeline is the only legitimate creator;
  it composes ``BindingMutationPipeline.set_binding`` rather than
  replacing it.
* :mod:`services.resource_provisioning_catalogue` — read-only
  cross-link snapshot of every ``ResourceRequirement`` with its
  ``BindingSpec``.  The pipeline reads this catalogue to resolve
  the request shape.
* :mod:`utils.db.resource_provisioning_audit` — append-only audit
  log for every provisioning attempt (success, decline, or failure).

Eleven-step contract per :meth:`ResourceProvisioningPipeline.provision`:

  1. Resolve ``ResourceRequirement`` + ``BindingSpec`` from
     :class:`services.resource_provisioning_catalogue.ProvisioningCatalogue`.
     Raise :class:`UndeclaredResourceError` if no option matches.
  2. Validate actor / capability (ADR-005 A1): the actor must hold the
     option's ``capability_required`` (resolved via
     :func:`governance.capability.actor_holds_capability`; empty resolves to
     the administrator floor).
  3. Validate bot Discord permissions for the requested kind
     (``manage_channels`` for CHANNEL/CATEGORY, ``manage_roles`` for
     ROLE).  Insufficient perms → :class:`UnauthorizedProvisioningError`
     and audited as ``permission_blocked``.
  4. Preview creation/reuse result via :meth:`preview` (already-bound?
     name collision? category exists?).  Records ``warnings``
     non-fatally.
  5. Require explicit confirmation: ``mode='create'`` requires
     ``confirmed=True``, otherwise raise
     :class:`ProvisioningConfirmationRequired`.
  6. Create or reuse the resource.
     - ``mode='create'``: dispatch via :mod:`core.runtime.guild_resources`
       (``ensure_channel`` / ``ensure_role`` / ``ensure_category``).
       Discord failure → :class:`DiscordProvisioningFailedError` and
       audited as ``discord_failed``.
     - ``mode='use_existing'``: re-resolve ``existing_id`` on the
       guild and verify ``kind`` matches.
  7. Validate created resource — re-resolve by ID, confirm ``kind``
     match.  Mismatches log a warning but do not abort.
  8. Bind the resource through
     :meth:`services.binding_mutation.BindingMutationPipeline.set_binding`.
     Binding failure does NOT roll back the created Discord resource —
     it is audited as ``binding_failed`` so the operator can manually
     re-bind or clean up.
  9. Audit one row in ``resource_provisioning_audit`` (migration 030).
 10. Emit advisory ``"resource.provisioned"`` event after commit
     (best-effort; subscriber failure logged + swallowed).
 11. Return typed :class:`ProvisioningResult`.

Hard limits for S4.5:

* Pipeline is adopted (RC-13 correction; this bullet previously read
  "zero production callers").  ``provision()`` is invoked by
  ``services.readiness_repair``, ``services.automation_executor``, and
  ``services.setup_operations`` (the ``create_*`` op route).
* The :data:`core.runtime.feature_flags.RESOURCE_PROVISIONING_PRIMARY` flag is a
  real operator kill-switch (ADR-005 F1): provisioning proceeds by default and
  is refused only on an explicit operator OFF (fail-open on eval error), matching
  SETTINGS_MUTATION_PRIMARY.
* No silent auto-create.  ``mode='create'`` always requires
  ``confirmed=True``; standing operator settings (e.g.
  ``logging.auto_create_channels=true``) are the only legitimate
  source of an "implicit confirmation" and are wired by S7's
  logging consumer, not by this pipeline.
* No direct ``guild.create_*`` calls in this module — every
  resource-creation goes through the ``ensure_*`` helpers in
  :mod:`core.runtime.guild_resources`.  Pinned by
  ``tests/unit/invariants/test_no_silent_auto_create.py``.

Cycle discipline (mirrors :mod:`services.platform_consistency`,
:mod:`services.settings_mutation`): all cross-package imports are
function-local.  Top-level imports are stdlib only.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from services.audit_events import emit_audit_action

logger = logging.getLogger("bot.services.resource_provisioning")


# ---------------------------------------------------------------------------
# Catalogued event name (registered in core/events_catalogue.py).
# ---------------------------------------------------------------------------

EVT_RESOURCE_PROVISIONED = "resource.provisioned"


# ---------------------------------------------------------------------------
# Recognized literal sets — mirror migration 030 CHECK constraints (the
# actor_type set was widened to include ``setup_delegate`` in migration 069,
# Q-0098).
# Pinned by tests/unit/invariants/test_resource_provisioning_audit_alignment.py.
# ---------------------------------------------------------------------------

_ALLOWED_ACTOR_TYPES: frozenset[str] = frozenset(
    {"user", "moderator", "admin", "system", "backfill", "setup_delegate"},
)
_ALLOWED_MUTATION_TYPES: frozenset[str] = frozenset({"provision"})
_ALLOWED_MODES: frozenset[str] = frozenset({"use_existing", "create"})
_ALLOWED_KINDS: frozenset[str] = frozenset(
    {"channel", "role", "category", "thread"},
)
_ALLOWED_OUTCOMES: frozenset[str] = frozenset(
    {"success", "permission_blocked", "discord_failed", "binding_failed", "declined"},
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ResourceProvisioningError(Exception):
    """Base class for failures from :class:`ResourceProvisioningPipeline`."""


class UndeclaredResourceError(ResourceProvisioningError):
    """Raised when ``(subsystem, binding_name)`` is not in the catalogue."""


class UnauthorizedProvisioningError(ResourceProvisioningError):
    """Raised when actor or bot lacks the required permissions."""


class ResourceProvisioningDisabledError(ResourceProvisioningError):
    """Raised when the provisioning pipeline is disabled via the
    :data:`core.runtime.feature_flags.RESOURCE_PROVISIONING_PRIMARY` operator
    kill-switch (an explicit operator OFF; ADR-005 F1).
    """


class ProvisioningConfirmationRequired(  # noqa: N818 — name pinned by the roadmap spec
    ResourceProvisioningError,
):
    """Raised when ``mode='create'`` is invoked without ``confirmed=True``.

    The pipeline rejects creates that have not seen an explicit
    confirmation gate.  UI callers must call :meth:`preview` first,
    show the operator the planned action, then call
    :meth:`provision(..., confirmed=True)`.
    """


class DiscordProvisioningFailedError(ResourceProvisioningError):
    """Raised when the Discord API call itself fails (HTTPException etc.)."""


class InvalidActorTypeError(ResourceProvisioningError):
    """Raised when ``actor_type`` is not in :data:`_ALLOWED_ACTOR_TYPES`."""


class KindMismatchError(ResourceProvisioningError):
    """Raised when ``mode='use_existing'`` resolves a resource whose kind
    does not match the requested :class:`ResourceKind`.
    """


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


_ProvisioningMode = Literal["use_existing", "create"]
_ProvisioningAction = Literal["reuse_existing", "create_new", "blocked"]
_ProvisioningOutcome = Literal[
    "success",
    "permission_blocked",
    "discord_failed",
    "binding_failed",
    "declined",
]


@dataclass(frozen=True)
class ProvisioningRequest:
    """Typed request shape passed into :meth:`provision` / :meth:`preview`.

    The pipeline never mutates the request; UI callers build one
    request per provisioning attempt.
    """

    subsystem: str
    binding_name: str
    mode: _ProvisioningMode
    existing_id: int | None = None
    custom_name: str | None = None
    category_id: int | None = None
    permission_template: str | None = None


@dataclass(frozen=True)
class ProvisioningPreview:
    """What :meth:`provision` would do without performing side effects."""

    allowed: bool
    action: _ProvisioningAction
    target_name: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProvisioningResult:
    """Outcome of a (successful or partially successful) provisioning attempt."""

    mutation_id: str
    guild_id: int
    subsystem: str
    binding_name: str
    kind: str
    mode: str
    outcome: _ProvisioningOutcome
    created: bool
    resource_id: int | None
    binding_written: bool
    audit_id: int | None
    committed_at: datetime
    event_emitted: bool


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class ResourceProvisioningPipeline:
    """Centralised orchestration for Discord resource provisioning.

    Instances are stateless — create one per provisioning request.
    Public methods :meth:`preview` (side-effect-free) and
    :meth:`provision` (audited write path).  Callers MUST NOT touch
    :mod:`utils.db.resource_provisioning_audit`'s insert primitive
    directly, nor invoke ``guild.create_*`` outside this pipeline +
    the grandfathered legacy allowlist enforced by
    ``tests/unit/invariants/test_no_silent_auto_create.py``.
    """

    def __init__(self) -> None:
        pass

    async def preview(
        self,
        guild: Any,
        request: ProvisioningRequest,
    ) -> ProvisioningPreview:
        """Return what :meth:`provision` would do, without side effects.

        Resolves the catalogue option, checks bot permissions, and
        notes any warnings (already-bound slot, name collision,
        category mismatch).  Does NOT raise; an error condition is
        reflected as ``allowed=False`` and ``action='blocked'`` with
        the reason in ``warnings``.
        """
        from services import resource_provisioning_catalogue as rpc

        catalogue = rpc.get_cached_provisioning_catalogue()
        if catalogue is None:
            return ProvisioningPreview(
                allowed=False,
                action="blocked",
                target_name="",
                warnings=("resource_provisioning_catalogue not built yet",),
            )

        option = catalogue.find(request.subsystem, request.binding_name)
        if option is None:
            return ProvisioningPreview(
                allowed=False,
                action="blocked",
                target_name="",
                warnings=(
                    f"no provisioning option for "
                    f"{request.subsystem!r}/{request.binding_name!r}",
                ),
            )

        warnings: list[str] = []

        # Bot permission check.
        ok, perm_msg = self._bot_can_provision(guild, option.kind, request.mode)
        if not ok:
            return ProvisioningPreview(
                allowed=False,
                action="blocked",
                target_name=option.suggested_name,
                warnings=(perm_msg,),
            )

        target_name = request.custom_name or option.suggested_name

        if request.mode == "use_existing":
            if request.existing_id is None:
                return ProvisioningPreview(
                    allowed=False,
                    action="blocked",
                    target_name=target_name,
                    warnings=("mode='use_existing' requires existing_id",),
                )
            resolved = self._resolve_existing(guild, option.kind, request.existing_id)
            if resolved is None:
                return ProvisioningPreview(
                    allowed=False,
                    action="blocked",
                    target_name=target_name,
                    warnings=(
                        f"existing_id={request.existing_id} did not resolve to a "
                        f"{option.kind} on this guild",
                    ),
                )
            return ProvisioningPreview(
                allowed=True,
                action="reuse_existing",
                target_name=getattr(resolved, "name", str(request.existing_id)),
                warnings=tuple(warnings),
            )

        # request.mode is "create" past this point.
        if not target_name:
            return ProvisioningPreview(
                allowed=False,
                action="blocked",
                target_name="",
                warnings=("no target name supplied and option has no suggested_name",),
            )
        # Surface a soft warning if a same-named resource already exists.
        if self._existing_by_name(guild, option.kind, target_name) is not None:
            warnings.append(
                f"a {option.kind} named {target_name!r} already exists; "
                "ensure_* will reuse it",
            )
        return ProvisioningPreview(
            allowed=True,
            action="create_new",
            target_name=target_name,
            warnings=tuple(warnings),
        )

    async def provision(
        self,
        guild: Any,
        request: ProvisioningRequest,
        actor: Any,
        *,
        confirmed: bool = False,
        actor_type: str = "user",
    ) -> ProvisioningResult:
        """Execute the 11-step contract.

        ``confirmed=True`` is required when ``request.mode == 'create'``;
        UI callers obtain confirmation by showing the operator a
        :class:`ProvisioningPreview` first.  ``mode='use_existing'``
        does not require ``confirmed=True`` because the operator's
        selection of an existing resource is itself the confirmation.

        Raises (with audit row written before the raise where
        applicable):

          * UndeclaredResourceError
          * UnauthorizedProvisioningError
          * ResourceProvisioningDisabledError
          * ProvisioningConfirmationRequired
          * DiscordProvisioningFailedError
          * KindMismatchError
          * InvalidActorTypeError
        """
        from services import resource_provisioning_catalogue as rpc

        self._validate_actor_type(actor_type)
        self._validate_mode(request.mode)

        # Resolve the catalogue option first so authority can be checked against
        # the option's declared capability (ADR-005 A1).  Catalogue resolution
        # has no side effects, so doing it before the authority check is safe.
        catalogue = rpc.get_cached_provisioning_catalogue()
        if catalogue is None:
            raise UndeclaredResourceError(
                "resource_provisioning_catalogue not built yet — "
                "call build_provisioning_catalogue() first",
            )
        option = catalogue.find(request.subsystem, request.binding_name)
        if option is None:
            raise UndeclaredResourceError(
                f"no provisioning option for "
                f"{request.subsystem!r}/{request.binding_name!r}",
            )

        await self._validate_actor_authority(
            option.capability_required,
            guild,
            actor,
            actor_type,
        )
        await self._check_provisioning_enabled(guild.id)

        if request.mode == "create" and not confirmed:
            raise ProvisioningConfirmationRequired(
                f"mode='create' for {request.subsystem!r}/"
                f"{request.binding_name!r} requires confirmed=True; "
                "call .preview(...) first",
            )

        mutation_id = str(uuid.uuid4())
        actor_id = getattr(actor, "id", None) if actor is not None else None
        target_name = request.custom_name or option.suggested_name

        # Step 3: bot permission check.
        bot_ok, bot_msg = self._bot_can_provision(guild, option.kind, request.mode)
        if not bot_ok:
            await self._write_audit(
                mutation_id=mutation_id,
                guild_id=guild.id,
                option=option,
                request=request,
                outcome="permission_blocked",
                created=False,
                resource_id=None,
                actor_id=actor_id,
                actor_type=actor_type,
                error_message=bot_msg,
            )
            raise UnauthorizedProvisioningError(bot_msg)

        # Step 6: create or reuse.
        try:
            if request.mode == "use_existing":
                if request.existing_id is None:
                    await self._write_audit(
                        mutation_id=mutation_id,
                        guild_id=guild.id,
                        option=option,
                        request=request,
                        outcome="declined",
                        created=False,
                        resource_id=None,
                        actor_id=actor_id,
                        actor_type=actor_type,
                        error_message="missing existing_id",
                    )
                    raise UndeclaredResourceError(
                        "mode='use_existing' requires existing_id",
                    )
                resource = self._resolve_existing(
                    guild,
                    option.kind,
                    request.existing_id,
                )
                if resource is None:
                    await self._write_audit(
                        mutation_id=mutation_id,
                        guild_id=guild.id,
                        option=option,
                        request=request,
                        outcome="declined",
                        created=False,
                        resource_id=request.existing_id,
                        actor_id=actor_id,
                        actor_type=actor_type,
                        error_message="existing_id did not resolve",
                    )
                    raise KindMismatchError(
                        f"existing_id={request.existing_id} did not resolve "
                        f"to a {option.kind} on guild {guild.id}",
                    )
                created = False
            else:
                resource = await self._create_resource(
                    guild,
                    option.kind,
                    target_name,
                    request,
                )
                created = True
        except DiscordProvisioningFailedError as exc:
            await self._write_audit(
                mutation_id=mutation_id,
                guild_id=guild.id,
                option=option,
                request=request,
                outcome="discord_failed",
                created=False,
                resource_id=None,
                actor_id=actor_id,
                actor_type=actor_type,
                error_message=str(exc),
            )
            raise

        # Step 7: validate created resource (kind match is enforced by
        # the create helpers; we just confirm an id exists).
        resource_id = int(getattr(resource, "id", 0)) or None
        if resource_id is None:
            await self._write_audit(
                mutation_id=mutation_id,
                guild_id=guild.id,
                option=option,
                request=request,
                outcome="discord_failed",
                created=created,
                resource_id=None,
                actor_id=actor_id,
                actor_type=actor_type,
                error_message="resource has no .id attribute",
            )
            raise DiscordProvisioningFailedError(
                f"created {option.kind!r} has no .id attribute",
            )

        # Step 8: bind through BindingMutationPipeline (compose, don't replace).
        binding_written = False
        try:
            await self._bind_resource(
                guild=guild,
                option=option,
                resource_id=resource_id,
                actor=actor,
            )
            binding_written = True
        except Exception as exc:  # noqa: BLE001 — audit the bind failure
            audit_id = await self._write_audit(
                mutation_id=mutation_id,
                guild_id=guild.id,
                option=option,
                request=request,
                outcome="binding_failed",
                created=created,
                resource_id=resource_id,
                actor_id=actor_id,
                actor_type=actor_type,
                error_message=f"{type(exc).__name__}: {exc}",
            )
            logger.exception(
                "ResourceProvisioningPipeline.provision: binding write "
                "failed for mutation_id=%s after %s (guild=%d, %s/%s, "
                "resource_id=%d).  Resource is NOT rolled back — operator "
                "must manually re-bind or clean up.",
                mutation_id,
                "create" if created else "reuse",
                guild.id,
                request.subsystem,
                request.binding_name,
                resource_id,
            )
            return ProvisioningResult(
                mutation_id=mutation_id,
                guild_id=guild.id,
                subsystem=request.subsystem,
                binding_name=request.binding_name,
                kind=option.kind,
                mode=request.mode,
                outcome="binding_failed",
                created=created,
                resource_id=resource_id,
                binding_written=False,
                audit_id=audit_id,
                committed_at=_now_utc(),
                event_emitted=False,
            )

        # Step 9: audit success.
        audit_id = await self._write_audit(
            mutation_id=mutation_id,
            guild_id=guild.id,
            option=option,
            request=request,
            outcome="success",
            created=created,
            resource_id=resource_id,
            actor_id=actor_id,
            actor_type=actor_type,
            error_message=None,
        )

        committed_at = _now_utc()
        # Phase 9c.2: companion ``audit.action_recorded`` event via the
        # shared publisher. Best-effort; failure is logged inside the
        # helper, not propagated.
        await emit_audit_action(
            mutation_id=mutation_id,
            subsystem=request.subsystem,
            mutation_type="provision_resource",
            target=f"binding:{request.subsystem}.{request.binding_name}",
            scope="guild",
            guild_id=guild.id,
            prev_value=None,
            new_value=f"{option.kind}:{resource_id}",
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=committed_at,
        )
        # Step 10: best-effort event emission.
        event_emitted = await self._emit_event(
            mutation_id=mutation_id,
            guild_id=guild.id,
            subsystem=request.subsystem,
            binding_name=request.binding_name,
            kind=option.kind,
            mode=request.mode,
            created=created,
            resource_id=resource_id,
            committed_at=committed_at,
        )

        return ProvisioningResult(
            mutation_id=mutation_id,
            guild_id=guild.id,
            subsystem=request.subsystem,
            binding_name=request.binding_name,
            kind=option.kind,
            mode=request.mode,
            outcome="success",
            created=created,
            resource_id=resource_id,
            binding_written=binding_written,
            audit_id=audit_id,
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # Step helpers
    # ------------------------------------------------------------------

    def _validate_actor_type(self, actor_type: str) -> None:
        if actor_type not in _ALLOWED_ACTOR_TYPES:
            raise InvalidActorTypeError(
                f"actor_type={actor_type!r} not in {sorted(_ALLOWED_ACTOR_TYPES)}",
            )

    def _validate_mode(self, mode: str) -> None:
        if mode not in _ALLOWED_MODES:
            raise UndeclaredResourceError(
                f"mode={mode!r} not in {sorted(_ALLOWED_MODES)}",
            )

    async def _validate_actor_authority(
        self,
        capability: str,
        guild: Any,
        actor: Any,
        actor_type: str,
    ) -> None:
        """Step 2: capability-native authority (ADR-005 A1).

        ``actor_type='system'`` / ``'backfill'`` bypass the check.  All other
        types must hold ``capability`` (the option's ``capability_required``);
        an empty capability resolves to the administrator floor.  See
        :func:`governance.capability.actor_holds_capability`.
        """
        from governance.capability import actor_holds_capability

        decision = await actor_holds_capability(
            actor,
            guild,
            capability,
            actor_type=actor_type,
        )
        if not decision.allowed:
            raise UnauthorizedProvisioningError(decision.reason)

    async def _check_provisioning_enabled(self, guild_id: int) -> None:
        """F1 kill-switch (ADR-005): refuse only when an operator has explicitly
        disabled provisioning via ``RESOURCE_PROVISIONING_PRIMARY``.

        Defaults to ALLOW and **fails open** — a flag-store outage must not block
        provisioning.  Raised before any audit row or Discord call.
        """
        from core.runtime import feature_flags

        try:
            disabled = await feature_flags.is_operator_disabled(
                feature_flags.RESOURCE_PROVISIONING_PRIMARY.name,
                guild_id,
            )
        except Exception:  # pragma: no cover - defensive; evaluator self-protects
            logger.warning(
                "resource_provisioning: kill-switch flag eval raised; "
                "allowing (fail-open).",
            )
            return
        if disabled:
            raise ResourceProvisioningDisabledError(
                "resource provisioning pipeline is disabled for "
                f"guild={guild_id} (operator turned "
                f"{feature_flags.RESOURCE_PROVISIONING_PRIMARY.name!r} OFF)",
            )

    def _bot_can_provision(
        self,
        guild: Any,
        kind: str,
        mode: str,
    ) -> tuple[bool, str]:
        """Check the bot's Discord-side permissions for the requested kind.

        Returns ``(ok, reason)``.  ``reason`` is empty on success.
        ``mode='use_existing'`` does not need create permissions —
        only the bind step needs guild visibility, which is implicit
        in being a guild member.
        """
        if mode == "use_existing":
            return True, ""
        me = getattr(guild, "me", None)
        if me is None:
            return False, "bot has no member representation on this guild"
        perms = getattr(me, "guild_permissions", None)
        if perms is None:
            return False, "bot guild_permissions unavailable"
        if kind in ("channel", "category", "thread"):
            if not getattr(perms, "manage_channels", False):
                return False, f"bot lacks manage_channels for {kind!r} create"
        elif kind == "role":
            if not getattr(perms, "manage_roles", False):
                return False, "bot lacks manage_roles for role create"
        return True, ""

    def _resolve_existing(self, guild: Any, kind: str, existing_id: int) -> Any:
        """Re-resolve ``existing_id`` on ``guild`` and verify kind matches."""
        from core.runtime import guild_resources

        if kind == "channel":
            ch = guild.get_channel(existing_id)
            return ch if ch is not None and ch.type.value in (0, 2, 5) else None
        if kind == "category":
            return guild_resources.resolve_category(guild, category_id=existing_id)
        if kind == "role":
            return guild_resources.resolve_role(guild, role_id=existing_id)
        if kind == "thread":
            return (
                guild.get_thread(existing_id) if hasattr(guild, "get_thread") else None
            )
        return None

    def _existing_by_name(self, guild: Any, kind: str, name: str) -> Any:
        from core.runtime import guild_resources

        if kind == "channel":
            return guild_resources.resolve_channel(guild, name=name)
        if kind == "category":
            return guild_resources.resolve_category(guild, name=name)
        if kind == "role":
            return guild_resources.resolve_role(guild, name=name)
        return None

    async def _create_resource(
        self,
        guild: Any,
        kind: str,
        target_name: str,
        request: ProvisioningRequest,
    ) -> Any:
        """Dispatch to the appropriate ``ensure_*`` helper."""
        from core.runtime import guild_resources

        try:
            if kind == "channel":
                category = None
                if request.category_id is not None:
                    category = guild_resources.resolve_category(
                        guild,
                        category_id=request.category_id,
                    )
                return await guild_resources.ensure_channel(
                    guild,
                    target_name,
                    category=category,
                )
            if kind == "category":
                return await guild_resources.ensure_category(guild, target_name)
            if kind == "role":
                return await guild_resources.ensure_role(guild, target_name)
        except Exception as exc:
            raise DiscordProvisioningFailedError(
                f"Discord API failed creating {kind!r} {target_name!r}: "
                f"{type(exc).__name__}: {exc}",
            ) from exc
        raise DiscordProvisioningFailedError(
            f"kind={kind!r} is not supported by the create path "
            "(thread provisioning is reserved for a future PR)",
        )

    async def _bind_resource(
        self,
        *,
        guild: Any,
        option: Any,  # services.resource_provisioning_catalogue.ProvisioningOption
        resource_id: int,
        actor: Any,
    ) -> None:
        """Step 8: hand off to BindingMutationPipeline.set_binding."""
        from core.runtime.subsystem_schema import BindingKind
        from services.binding_mutation import BindingMutationPipeline

        kind_enum = BindingKind(option.binding_kind or option.kind)
        await BindingMutationPipeline().set_binding(
            guild=guild,
            subsystem=option.subsystem,
            binding_name=option.binding_name,
            kind=kind_enum,
            target_id=resource_id,
            actor=actor,
        )

    async def _write_audit(
        self,
        *,
        mutation_id: str,
        guild_id: int,
        option: Any,
        request: ProvisioningRequest,
        outcome: _ProvisioningOutcome,
        created: bool,
        resource_id: int | None,
        actor_id: int | None,
        actor_type: str,
        error_message: str | None,
    ) -> int:
        from utils.db import resource_provisioning_audit as audit_db

        return await audit_db.insert_audit(
            mutation_id=mutation_id,
            guild_id=guild_id,
            subsystem=option.subsystem,
            binding_name=option.binding_name,
            kind=option.kind,
            mode=request.mode,
            outcome=outcome,
            created=created,
            resource_id=resource_id,
            suggested_name=option.suggested_name or None,
            custom_name=request.custom_name,
            actor_id=actor_id,
            actor_type=actor_type,
            mutation_type="provision",
            error_message=error_message,
        )

    async def _emit_event(
        self,
        *,
        mutation_id: str,
        guild_id: int,
        subsystem: str,
        binding_name: str,
        kind: str,
        mode: str,
        created: bool,
        resource_id: int,
        committed_at: datetime,
    ) -> bool:
        from core.events import bus

        try:
            await bus.emit(
                EVT_RESOURCE_PROVISIONED,
                mutation_id=mutation_id,
                guild_id=guild_id,
                subsystem=subsystem,
                binding_name=binding_name,
                kind=kind,
                mode=mode,
                created=created,
                resource_id=resource_id,
                occurred_at=committed_at.isoformat(),
            )
        except Exception:
            logger.exception(
                "ResourceProvisioningPipeline._emit_event: emission failed "
                "for mutation_id=%s; DB state is correct, event lost.",
                mutation_id,
            )
            return False
        return True


def _now_utc() -> datetime:
    """Return a tz-aware "now" — INV-N forbids bare datetime.utcnow."""
    return datetime.now(timezone.utc)


__all__ = [
    "EVT_RESOURCE_PROVISIONED",
    "DiscordProvisioningFailedError",
    "InvalidActorTypeError",
    "KindMismatchError",
    "ProvisioningConfirmationRequired",
    "ProvisioningPreview",
    "ProvisioningRequest",
    "ProvisioningResult",
    "ResourceProvisioningError",
    "ResourceProvisioningPipeline",
    "UnauthorizedProvisioningError",
    "UndeclaredResourceError",
]
