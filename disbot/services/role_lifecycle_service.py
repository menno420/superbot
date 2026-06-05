"""Role lifecycle service (server-management PR5).

The canonical owner of operator-driven role *lifecycle* mutations —
**create**, **edit** (rename / recolour / hoist / mentionable), and **delete** —
that :class:`services.resource_provisioning.ResourceProvisioningPipeline` does
not own.  It is the role-domain sibling of
:class:`services.channel_lifecycle_service.ChannelLifecycleService`: cogs and
views authorise and render; every Discord role mutation flows through here,
returning a typed :class:`services.lifecycle.LifecycleResult` with a per-role
:class:`services.lifecycle.StepResult` plus a best-effort audit companion and a
``role.lifecycle_changed`` event.

Boundaries (this PR):

* **Member assignment** (``member.add_roles`` / ``remove_roles`` for reaction
  roles and time/XP automation) keeps its current paths — the automation apply
  path in :mod:`services.role_automation` is already audited.  This service owns
  only the role *object* lifecycle.
* **Subsystem-declared** role provisioning (create-or-reuse + bind) stays with
  ``ResourceProvisioningPipeline`` / ``guild_resources.ensure_role``.  This
  service is the audited creator for *manual* operator roles, so it is the one
  legitimate ``guild.create_role`` caller on the
  ``test_no_silent_auto_create.py`` allowlist outside the helper layer.

Authorisation mirrors ``moderation_service`` / ``channel_lifecycle_service``:
the bot's ``manage_roles`` permission and the per-role manageability verdict
(via :mod:`utils.role_feasibility`) are checked here; the *actor's* authority
stays at the cog/view layer (the role commands are already admin-gated).

Reversibility: create → compensatable (the new id makes recreation not a
rollback), edit → reversible (prior name/colour can be restored), delete →
irreversible (the role and its member assignments are gone; delete requires
``confirmed=True``).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

import discord

from services.lifecycle import contracts as lc
from utils import role_feasibility

logger = logging.getLogger("bot.services.role_lifecycle")

DOMAIN = "role"
EVT_ROLE_LIFECYCLE = "role.lifecycle_changed"

_OPERATIONS = ("create", "edit", "delete")
_REVERSIBILITY = {
    "create": lc.COMPENSATABLE,
    "edit": lc.REVERSIBLE,
    "delete": lc.IRREVERSIBLE,
}


@dataclass(frozen=True)
class RoleLifecycleRequest:
    """Typed request — one operation over one role."""

    operation: str  # "create" | "edit" | "delete"
    role_id: int | None = None  # edit / delete target
    name: str | None = None  # create (required) / edit (rename)
    color: discord.Color | None = None  # create / edit
    hoist: bool | None = None  # create / edit
    mentionable: bool | None = None  # create / edit
    reason: str | None = None


class RoleLifecycleService:
    """Stateless coordinator — one instance per request is fine."""

    async def preview(
        self,
        guild: discord.Guild,
        request: RoleLifecycleRequest,
    ) -> lc.LifecyclePreview:
        """Describe what :meth:`apply` would do, with no side effects."""
        operation = request.operation
        if operation not in _OPERATIONS:
            return lc.LifecyclePreview(
                allowed=False,
                operation=operation,
                summary="",
                reversibility="",
                warnings=(f"unknown operation {operation!r}",),
            )
        reversibility = _REVERSIBILITY[operation]
        if not self._bot_can_manage(guild):
            return lc.LifecyclePreview(
                allowed=False,
                operation=operation,
                summary="",
                reversibility=reversibility,
                warnings=("bot lacks the Manage Roles permission",),
            )
        warnings: list[str] = []
        role: discord.Role | None = None
        if operation in ("edit", "delete"):
            role = self._resolve(guild, request.role_id)
            if role is None:
                return lc.LifecyclePreview(
                    allowed=False,
                    operation=operation,
                    summary="",
                    reversibility=reversibility,
                    warnings=("role no longer exists",),
                )
            verdict = role_feasibility.evaluate_role(
                role,
                bot_member=getattr(guild, "me", None),
            )
            if not verdict.ok:
                return lc.LifecyclePreview(
                    allowed=False,
                    operation=operation,
                    summary=self._summary(request, role=role),
                    reversibility=reversibility,
                    warnings=(verdict.reason,),
                )
        if operation == "delete":
            warnings.append(
                "deletion is irreversible — the role and its assignments are lost",
            )
        return lc.LifecyclePreview(
            allowed=True,
            operation=operation,
            summary=self._summary(request, role=role),
            reversibility=reversibility,
            warnings=tuple(warnings),
        )

    async def apply(
        self,
        guild: discord.Guild,
        request: RoleLifecycleRequest,
        actor: object | None,
        *,
        confirmed: bool = False,
        actor_type: str = "user",
    ) -> lc.LifecycleResult:
        """Execute *request*; return a typed, audited result.

        Irreversible operations (delete) require ``confirmed=True``.  Discord
        failures are captured as a failed step rather than raised, so the result
        records the actual final state.
        """
        operation = request.operation
        if operation not in _OPERATIONS:
            raise ValueError(f"unknown role lifecycle operation {operation!r}")
        reversibility = _REVERSIBILITY[operation]
        mutation_id = str(uuid.uuid4())
        actor_id = getattr(actor, "id", None) if actor is not None else None

        if not self._bot_can_manage(guild):
            return self._terminal(
                mutation_id,
                guild.id,
                operation,
                reversibility,
                lc.BLOCKED,
                "bot lacks the Manage Roles permission",
            )

        role: discord.Role | None = None
        if operation in ("edit", "delete"):
            role = self._resolve(guild, request.role_id)
            if role is None:
                return self._terminal(
                    mutation_id,
                    guild.id,
                    operation,
                    reversibility,
                    lc.BLOCKED,
                    "role not found",
                )
            verdict = role_feasibility.evaluate_role(
                role,
                bot_member=getattr(guild, "me", None),
            )
            if not verdict.ok:
                return self._terminal(
                    mutation_id,
                    guild.id,
                    operation,
                    reversibility,
                    lc.BLOCKED,
                    verdict.reason,
                )

        if reversibility == lc.IRREVERSIBLE and not confirmed:
            return self._terminal(
                mutation_id,
                guild.id,
                operation,
                reversibility,
                lc.DECLINED,
                "irreversible operation requires confirmation",
            )

        fallback_id = request.role_id or 0
        fallback_name = (role.name if role else request.name) or str(fallback_id)
        try:
            applied = await self._apply_one(guild, operation, role, request)
            steps: tuple[lc.StepResult, ...] = (
                lc.StepResult(applied.id, applied.name, True),
            )
        except discord.Forbidden:
            steps = (
                lc.StepResult(fallback_id, fallback_name, False, "missing permission"),
            )
        except discord.HTTPException as exc:
            steps = (
                lc.StepResult(fallback_id, fallback_name, False, f"Discord: {exc}"),
            )

        outcome = lc.classify_outcome(steps)
        committed_at = lc.now_utc()
        summary = self._summary(request, role=role, steps=steps)
        audit_emitted = await lc.emit_lifecycle_audit(
            mutation_id=mutation_id,
            domain=DOMAIN,
            operation=operation,
            guild_id=guild.id,
            target=self._target(request, steps),
            summary=summary,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=committed_at,
        )
        event_emitted = await self._emit_event(
            mutation_id=mutation_id,
            guild_id=guild.id,
            operation=operation,
            outcome=outcome,
            steps=steps,
            committed_at=committed_at,
        )
        return lc.LifecycleResult(
            mutation_id=mutation_id,
            guild_id=guild.id,
            domain=DOMAIN,
            operation=operation,
            outcome=outcome,
            reversibility=reversibility,
            steps=steps,
            committed_at=committed_at,
            audit_emitted=audit_emitted,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _bot_can_manage(self, guild: discord.Guild) -> bool:
        me = getattr(guild, "me", None)
        perms = getattr(me, "guild_permissions", None)
        return bool(getattr(perms, "manage_roles", False))

    def _resolve(
        self,
        guild: discord.Guild,
        role_id: int | None,
    ) -> discord.Role | None:
        if role_id is None:
            return None
        # Route through the canonical resolver (raw guild.get_role is pinned out
        # by tests/unit/runtime/test_guild_resources_invariant.py).
        from core.runtime import guild_resources

        return guild_resources.resolve_role(guild, role_id=role_id)

    async def _apply_one(
        self,
        guild: discord.Guild,
        operation: str,
        role: discord.Role | None,
        request: RoleLifecycleRequest,
    ) -> discord.Role:
        reason = request.reason
        if operation == "create":
            return await guild.create_role(
                name=request.name or "new-role",
                color=(
                    request.color
                    if request.color is not None
                    else discord.Color.default()
                ),
                hoist=bool(request.hoist),
                mentionable=bool(request.mentionable),
                reason=reason,
            )
        if role is None:  # apply() resolves edit/delete targets before dispatch
            raise ValueError(f"{operation} requires a resolved role")
        if operation == "edit":
            await role.edit(reason=reason, **self._edit_kwargs(request))
            return role
        await role.delete(reason=reason)
        return role

    def _edit_kwargs(self, request: RoleLifecycleRequest) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if request.name is not None:
            kwargs["name"] = request.name
        if request.color is not None:
            kwargs["color"] = request.color
        if request.hoist is not None:
            kwargs["hoist"] = request.hoist
        if request.mentionable is not None:
            kwargs["mentionable"] = request.mentionable
        return kwargs

    def _target(
        self,
        request: RoleLifecycleRequest,
        steps: tuple[lc.StepResult, ...],
    ) -> str:
        if steps and steps[0].target_id:
            return f"role:{steps[0].target_id}"
        if request.role_id:
            return f"role:{request.role_id}"
        return "role:new"

    def _summary(
        self,
        request: RoleLifecycleRequest,
        *,
        role: discord.Role | None = None,
        steps: tuple[lc.StepResult, ...] | None = None,
    ) -> str:
        name = (
            (steps[0].target_name if steps else None)
            or (role.name if role else None)
            or request.name
            or (str(request.role_id) if request.role_id else "?")
        )
        if request.operation == "create":
            return f"create role {request.name!r}"
        if request.operation == "edit":
            return f"edit role {name!r}"
        return f"delete role {name!r}"

    def _terminal(
        self,
        mutation_id: str,
        guild_id: int,
        operation: str,
        reversibility: str,
        outcome: str,
        reason: str,
    ) -> lc.LifecycleResult:
        return lc.LifecycleResult(
            mutation_id=mutation_id,
            guild_id=guild_id,
            domain=DOMAIN,
            operation=operation,
            outcome=outcome,
            reversibility=reversibility,
            steps=(lc.StepResult(0, "", False, reason),),
            committed_at=lc.now_utc(),
        )

    async def _emit_event(
        self,
        *,
        mutation_id: str,
        guild_id: int,
        operation: str,
        outcome: str,
        steps: tuple[lc.StepResult, ...],
        committed_at: object,
    ) -> bool:
        from core.events import bus

        try:
            await bus.emit(
                EVT_ROLE_LIFECYCLE,
                mutation_id=mutation_id,
                guild_id=guild_id,
                operation=operation,
                outcome=outcome,
                applied=[s.target_id for s in steps if s.ok],
                failed=[s.target_id for s in steps if not s.ok],
                occurred_at=getattr(committed_at, "isoformat", lambda: None)(),
            )
        except Exception:
            logger.exception(
                "RoleLifecycleService._emit_event: emission failed for "
                "mutation_id=%s; Discord state is correct, event lost.",
                mutation_id,
            )
            return False
        return True


__all__ = [
    "EVT_ROLE_LIFECYCLE",
    "RoleLifecycleRequest",
    "RoleLifecycleService",
]
