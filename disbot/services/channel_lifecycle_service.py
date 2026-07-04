"""Channel/category lifecycle service (server-management PR4).

The canonical owner of the channel *change* operations that
:class:`services.resource_provisioning.ResourceProvisioningPipeline` does not
own — **rename**, **move** (to/from a category), **reorder**, **delete**
(single or batch), **set_overwrite** (permission overwrites: lock/unlock/grant/
deny), **clone**, **set_slowmode** (per-user delay), and **set_topic**.  Cogs
and views authorise and render; every Discord
mutation flows through here, returning a typed
:class:`services.lifecycle.LifecycleResult` with per-channel
:class:`services.lifecycle.StepResult` and a best-effort audit companion +
``channel.lifecycle_changed`` event.

Boundaries (P0-4 convergence, Q-0100):

* **Subsystem-bound** channel/category creation (a channel that becomes a
  declared ``(subsystem, binding_name)`` binding) stays with
  :class:`services.resource_provisioning.ResourceProvisioningPipeline` — it is
  catalogue-driven and writes the binding row.
* **Ad-hoc operator** channel creation (``!create`` / ``!evt`` / ``!bulkcreate``
  / the create panel) has *no* declared binding, so it does not fit that
  pipeline; it is now owned **here** via :meth:`create_channels` (P0-4 PR 2),
  the channel-domain sibling of
  :class:`services.role_lifecycle_service.RoleLifecycleService` (the audited
  manual-role creator).  ``set_permissions``/overwrite and ``clone`` were the
  earlier follow-up and are also **owned here** (P0-4 PR 1).  The convergence
  invariant pins ``.delete`` / ``.edit`` / ``.set_permissions`` / ``.clone`` and
  the operator ``create_*`` calls in the cog + channel views; this service is
  the one sanctioned manual ``guild.create_*`` caller (no-silent-auto-create
  allowlist).

Authorisation: the bot's Discord permission (``manage_channels``) is checked
here; the *actor's* authority stays at the cog/view layer (the channel
commands are already gated by ``is_admin_or_owner``), mirroring
``services.moderation_service``.

Reversibility: rename → reversible, move → compensatable, delete →
irreversible (delete requires ``confirmed=True``; the typed command invocation
is the operator's confirmation, exactly as provisioning treats an explicit
selection).
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

import discord

from services.lifecycle import contracts as lc

logger = logging.getLogger("bot.services.channel_lifecycle")

DOMAIN = "channel"
EVT_CHANNEL_LIFECYCLE = "channel.lifecycle_changed"

_OPERATIONS = (
    "rename",
    "move",
    "delete",
    "reorder",
    "set_overwrite",
    "clone",
    "set_slowmode",
    "set_topic",
)
_REVERSIBILITY = {
    "rename": lc.REVERSIBLE,
    "move": lc.COMPENSATABLE,
    "delete": lc.IRREVERSIBLE,
    "reorder": lc.COMPENSATABLE,
    # An overwrite can be flipped back; a clone can be compensated by deleting
    # the copy.  Neither is irreversible, so neither demands ``confirmed=True``
    # (preserving the existing lock/unlock/clone command UX).
    "set_overwrite": lc.REVERSIBLE,
    "clone": lc.COMPENSATABLE,
    # Slowmode and topic are plain scalar channel edits — fully reversible by
    # setting the old value back (the operator's typed command is the change).
    "set_slowmode": lc.REVERSIBLE,
    "set_topic": lc.REVERSIBLE,
}

# Discord's hard cap on a text channel's per-user slowmode delay (6 hours).
MAX_SLOWMODE_SECONDS = 21600
# Discord's hard cap on a channel topic.
MAX_TOPIC_LENGTH = 1024


@dataclass(frozen=True)
class ChannelLifecycleRequest:
    """Typed request — one operation over one or more channels."""

    operation: str  # one of _OPERATIONS
    channel_ids: tuple[int, ...]
    new_name: str | None = None  # rename
    category_id: int | None = None  # move (None = remove from category)
    position: str | None = None  # reorder: "top" | "bottom" (default bottom)
    reason: str | None = None
    # set_overwrite: who the overwrite is for + the permission deltas.
    overwrite_target_id: int | None = None
    overwrite_target_type: str | None = None  # "role" (default) | "member"
    overwrites: dict[str, bool | None] | None = None  # permission name → allow/deny
    # clone: the new channel's name.
    clone_name: str | None = None
    # set_slowmode: per-user delay in seconds (0 disables).
    slowmode_seconds: int | None = None
    # set_topic: the new topic text (None / "" clears it).
    topic: str | None = None


class ChannelLifecycleService:
    """Stateless coordinator — one instance per request is fine."""

    async def preview(
        self,
        guild: discord.Guild,
        request: ChannelLifecycleRequest,
    ) -> lc.LifecyclePreview:
        """Describe what :meth:`apply` would do, with no side effects."""
        if request.operation not in _OPERATIONS:
            return lc.LifecyclePreview(
                allowed=False,
                operation=request.operation,
                summary="",
                reversibility="",
                warnings=(f"unknown operation {request.operation!r}",),
            )
        reversibility = _REVERSIBILITY[request.operation]
        warnings: list[str] = []
        if not self._bot_can_manage(guild):
            return lc.LifecyclePreview(
                allowed=False,
                operation=request.operation,
                summary="",
                reversibility=reversibility,
                warnings=("bot lacks the Manage Channels permission",),
            )
        resolved = [guild.get_channel(cid) for cid in request.channel_ids]
        missing = [
            cid
            for cid, ch in zip(request.channel_ids, resolved, strict=True)
            if ch is None
        ]
        if missing:
            warnings.append(f"{len(missing)} channel(s) no longer exist")
        if request.operation == "delete":
            warnings.append("deletion is irreversible — message history is lost")
        summary = self._summary(request, tuple(s for s in resolved if s is not None))
        return lc.LifecyclePreview(
            allowed=any(ch is not None for ch in resolved),
            operation=request.operation,
            summary=summary,
            reversibility=reversibility,
            warnings=tuple(warnings),
        )

    async def apply(
        self,
        guild: discord.Guild,
        request: ChannelLifecycleRequest,
        actor: object | None,
        *,
        confirmed: bool = False,
        actor_type: str = "user",
    ) -> lc.LifecycleResult:
        """Execute *request*; return a typed, audited result.

        Irreversible operations (delete) require ``confirmed=True``.  Per-channel
        Discord failures are captured as failed steps rather than raised, so a
        batch records its actual final state.
        """
        operation = request.operation
        if operation not in _OPERATIONS:
            raise ValueError(f"unknown channel lifecycle operation {operation!r}")
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
                "bot lacks the Manage Channels permission",
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

        steps: list[lc.StepResult] = []
        for cid in request.channel_ids:
            channel = guild.get_channel(cid)
            if channel is None:
                steps.append(lc.StepResult(cid, str(cid), False, "channel not found"))
                continue
            try:
                await self._apply_one(guild, operation, channel, request)
                steps.append(lc.StepResult(cid, channel.name, True))
            except discord.Forbidden:
                steps.append(
                    lc.StepResult(cid, channel.name, False, "missing permission"),
                )
            except discord.HTTPException as exc:
                steps.append(lc.StepResult(cid, channel.name, False, f"Discord: {exc}"))
            except LookupError as exc:
                # e.g. a set_overwrite whose target role/member no longer exists.
                steps.append(lc.StepResult(cid, channel.name, False, str(exc)))

        steps_t = tuple(steps)
        outcome = lc.classify_outcome(steps_t)
        committed_at = lc.now_utc()
        summary = self._summary(
            request,
            tuple(s for s in (guild.get_channel(c) for c in request.channel_ids) if s),
            steps=steps_t,
        )
        audit_emitted = await lc.emit_lifecycle_audit(
            mutation_id=mutation_id,
            domain=DOMAIN,
            operation=operation,
            guild_id=guild.id,
            target=self._target(request),
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
            steps=steps_t,
            committed_at=committed_at,
        )
        return lc.LifecycleResult(
            mutation_id=mutation_id,
            guild_id=guild.id,
            domain=DOMAIN,
            operation=operation,
            outcome=outcome,
            reversibility=reversibility,
            steps=steps_t,
            committed_at=committed_at,
            audit_emitted=audit_emitted,
            event_emitted=event_emitted,
        )

    async def create_channels(
        self,
        guild: discord.Guild,
        names: Sequence[str],
        actor: object | None,
        *,
        category_id: int | None = None,
        category_name: str | None = None,
        kind: str = "text",
        reason: str | None = None,
        actor_type: str = "user",
    ) -> lc.LifecycleResult:
        """Create one or more channels through the audited lifecycle seam.

        This is the audited *manual* channel creator — the channel-domain sibling
        of :class:`services.role_lifecycle_service.RoleLifecycleService` (Q-0100,
        P0-4).  Ad-hoc operator channels (``!create`` / ``!evt`` / ``!bulkcreate``
        / the create panel) have **no declared subsystem binding**, so they do not
        fit the catalogue-driven
        :class:`services.resource_provisioning.ResourceProvisioningPipeline`
        (which resolves a ``(subsystem, binding_name)`` option and always writes a
        binding row); routing them here gives them the same audit companion +
        ``channel.lifecycle_changed`` event as every other operator channel
        mutation, without minting a fake binding.

        Channels are created with safe (auto-incremented) names.  An optional
        category is resolved by id (``category_id``) or get-or-created by name
        (``category_name``); a category failure aborts the whole batch (every
        channel would otherwise land in the wrong place).  ``StepResult.target_id``
        carries each new channel's id (``0`` on failure) so callers can re-resolve
        the created channel (e.g. to apply a follow-up overwrite).
        """
        operation = "create"
        reversibility = lc.COMPENSATABLE
        mutation_id = str(uuid.uuid4())
        actor_id = getattr(actor, "id", None) if actor is not None else None

        if not self._bot_can_manage(guild):
            return self._terminal(
                mutation_id,
                guild.id,
                operation,
                reversibility,
                lc.BLOCKED,
                "bot lacks the Manage Channels permission",
            )

        category, cat_error = await self._resolve_create_category(
            guild,
            category_id,
            category_name,
        )
        if cat_error is not None:
            return self._terminal(
                mutation_id,
                guild.id,
                operation,
                reversibility,
                lc.BLOCKED,
                cat_error,
            )

        steps: list[lc.StepResult] = []
        for requested in names:
            try:
                channel = await self._create_one(
                    guild,
                    kind,
                    requested,
                    category,
                    reason,
                )
            except discord.Forbidden:
                steps.append(lc.StepResult(0, requested, False, "missing permission"))
            except discord.HTTPException as exc:
                steps.append(lc.StepResult(0, requested, False, f"Discord: {exc}"))
            else:
                steps.append(lc.StepResult(int(channel.id), requested, True))

        steps_t = tuple(steps)
        outcome = lc.classify_outcome(steps_t)
        committed_at = lc.now_utc()
        summary = self._create_summary(names, category, kind, steps_t)
        audit_emitted = await lc.emit_lifecycle_audit(
            mutation_id=mutation_id,
            domain=DOMAIN,
            operation=operation,
            guild_id=guild.id,
            target=f"channels:{len(names)}",
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
            steps=steps_t,
            committed_at=committed_at,
        )
        return lc.LifecycleResult(
            mutation_id=mutation_id,
            guild_id=guild.id,
            domain=DOMAIN,
            operation=operation,
            outcome=outcome,
            reversibility=reversibility,
            steps=steps_t,
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
        return bool(getattr(perms, "manage_channels", False))

    async def _apply_one(
        self,
        guild: discord.Guild,
        operation: str,
        channel: discord.abc.GuildChannel,
        request: ChannelLifecycleRequest,
    ) -> None:
        reason = request.reason
        if operation == "rename":
            # .edit lives on the concrete channel subclasses, not the abc.
            await channel.edit(name=request.new_name, reason=reason)  # type: ignore[attr-defined]
        elif operation == "move":
            from core.runtime import guild_resources

            category = (
                guild_resources.resolve_category(guild, category_id=request.category_id)
                if request.category_id is not None
                else None
            )
            await channel.edit(category=category, reason=reason)  # type: ignore[attr-defined]
        elif operation == "reorder":
            # .move lives on the abc; beginning/end repositions the channel
            # within its category (or the guild). Discord reorder is not atomic
            # — a partial batch records its actual final state via the steps.
            if request.position == "top":
                await channel.move(beginning=True, reason=reason)
            else:
                await channel.move(end=True, reason=reason)
        elif operation == "delete":
            await channel.delete(reason=reason)
        elif operation == "set_overwrite":
            target = self._resolve_overwrite_target(guild, request)
            if target is None:
                raise LookupError(
                    f"overwrite target {request.overwrite_target_type or 'role'} "
                    f"{request.overwrite_target_id} not found",
                )
            # **permissions replaces the whole overwrite for *target* (discord.py
            # semantics) — identical to the prior direct cog/view calls.
            await channel.set_permissions(  # type: ignore[attr-defined]
                target,
                reason=reason,
                **(request.overwrites or {}),
            )
        elif operation == "clone":
            await channel.clone(name=request.clone_name, reason=reason)  # type: ignore[attr-defined]
        elif operation == "set_slowmode":
            # .edit's slowmode_delay lives on text/forum channels, not the abc.
            seconds = max(0, min(request.slowmode_seconds or 0, MAX_SLOWMODE_SECONDS))
            await channel.edit(slowmode_delay=seconds, reason=reason)  # type: ignore[attr-defined]
        elif operation == "set_topic":
            # An empty string / None clears the topic; cap at Discord's limit.
            topic = (request.topic or "")[:MAX_TOPIC_LENGTH]
            await channel.edit(topic=topic or None, reason=reason)  # type: ignore[attr-defined]

    async def _resolve_create_category(
        self,
        guild: discord.Guild,
        category_id: int | None,
        category_name: str | None,
    ) -> tuple[discord.CategoryChannel | None, str | None]:
        """Resolve the target category for a create batch.

        ``category_id`` resolves an existing category (error if it is gone);
        ``category_name`` get-or-creates one by name (the long-standing
        ``!evt`` / create-panel behaviour); neither given → no category.
        Returns ``(category, error)`` — ``error`` is non-None on failure and the
        caller aborts the whole batch.
        """
        if category_id is not None:
            from core.runtime import guild_resources

            cat = guild_resources.resolve_category(guild, category_id=category_id)
            if cat is None:
                return None, f"category {category_id} not found"
            return cat, None
        if category_name:
            from utils.channels import get_or_create_category

            try:
                cat = await get_or_create_category(guild, category_name)
            except discord.Forbidden:
                return None, "missing permission to create the category"
            except discord.HTTPException as exc:
                return None, f"Discord: {exc}"
            return cat, None
        return None, None

    async def _create_one(
        self,
        guild: discord.Guild,
        kind: str,
        requested_name: str,
        category: discord.CategoryChannel | None,
        reason: str | None,
    ) -> discord.abc.GuildChannel:
        """Create a single channel with a collision-safe name.

        This is the one sanctioned ``guild.create_*`` call for *manual* operator
        channels (allowlisted in ``test_no_silent_auto_create.py`` as the channel
        sibling of ``role_lifecycle_service``).
        """
        from utils.channels import safe_channel_name

        safe = await safe_channel_name(guild, requested_name)
        if kind == "voice":
            return await guild.create_voice_channel(
                safe,
                category=category,
                reason=reason,
            )
        return await guild.create_text_channel(safe, category=category, reason=reason)

    def _create_summary(
        self,
        names: Sequence[str],
        category: discord.CategoryChannel | None,
        kind: str,
        steps: tuple[lc.StepResult, ...],
    ) -> str:
        applied = sum(1 for s in steps if s.ok)
        where = f" in category {category.name!r}" if category is not None else ""
        return (
            f"create {len(names)} {kind} channel(s){where} "
            f"({applied}/{len(steps)} applied)"
        )

    def _resolve_overwrite_target(
        self,
        guild: discord.Guild,
        request: ChannelLifecycleRequest,
    ) -> discord.Role | discord.Member | None:
        """Resolve the overwrite subject by id (defaults to a role lookup, which
        also covers ``guild.default_role`` for @everyone lock/unlock).
        """
        from core.runtime import guild_resources

        if request.overwrite_target_id is None:
            return None
        if request.overwrite_target_type == "member":
            return guild_resources.resolve_member(guild, request.overwrite_target_id)
        return guild_resources.resolve_role(
            guild,
            role_id=request.overwrite_target_id,
        )

    def _target(self, request: ChannelLifecycleRequest) -> str:
        if len(request.channel_ids) == 1:
            return f"channel:{request.channel_ids[0]}"
        return f"channels:{len(request.channel_ids)}"

    def _summary(
        self,
        request: ChannelLifecycleRequest,
        channels: tuple[discord.abc.GuildChannel, ...],
        *,
        steps: tuple[lc.StepResult, ...] | None = None,
    ) -> str:
        n = len(request.channel_ids)
        if steps is not None:
            applied = sum(1 for s in steps if s.ok)
            suffix = f" ({applied}/{len(steps)} applied)"
        else:
            suffix = ""
        if request.operation == "rename":
            name = getattr(channels[0], "name", "?") if channels else "?"
            return f"rename channel {name!r} → {request.new_name!r}{suffix}"
        if request.operation == "move":
            return f"move {n} channel(s) to category {request.category_id}{suffix}"
        if request.operation == "reorder":
            return f"send {n} channel(s) to {request.position or 'bottom'}{suffix}"
        if request.operation == "set_overwrite":
            keys = ", ".join(sorted((request.overwrites or {}).keys())) or "(none)"
            who = f"{request.overwrite_target_type or 'role'} {request.overwrite_target_id}"
            return f"set overwrite [{keys}] on {n} channel(s) for {who}{suffix}"
        if request.operation == "clone":
            name = getattr(channels[0], "name", "?") if channels else "?"
            return f"clone channel {name!r} → {request.clone_name!r}{suffix}"
        if request.operation == "set_slowmode":
            seconds = max(0, min(request.slowmode_seconds or 0, MAX_SLOWMODE_SECONDS))
            name = getattr(channels[0], "name", "?") if channels else "?"
            return f"set slowmode {seconds}s on channel {name!r}{suffix}"
        if request.operation == "set_topic":
            name = getattr(channels[0], "name", "?") if channels else "?"
            verb = (
                "clear topic of"
                if not (request.topic or "").strip()
                else "set topic of"
            )
            return f"{verb} channel {name!r}{suffix}"
        return f"delete {n} channel(s){suffix}"

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
                EVT_CHANNEL_LIFECYCLE,
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
                "ChannelLifecycleService._emit_event: emission failed for "
                "mutation_id=%s; DB/Discord state is correct, event lost.",
                mutation_id,
            )
            return False
        return True


__all__ = [
    "EVT_CHANNEL_LIFECYCLE",
    "MAX_SLOWMODE_SECONDS",
    "MAX_TOPIC_LENGTH",
    "ChannelLifecycleRequest",
    "ChannelLifecycleService",
]
