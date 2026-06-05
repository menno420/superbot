"""Channel/category lifecycle service (server-management PR4).

The canonical owner of the channel *change* operations that
:class:`services.resource_provisioning.ResourceProvisioningPipeline` does not
own — **rename**, **move** (to/from a category), and **delete** (single or
batch).  Cogs and views authorise and render; every Discord mutation flows
through here, returning a typed :class:`services.lifecycle.LifecycleResult`
with per-channel :class:`services.lifecycle.StepResult` and a best-effort
audit companion + ``channel.lifecycle_changed`` event.

Boundaries (this PR):

* Channel *creation* stays with ``utils.channels`` / the provisioning pipeline
  (the no-silent-auto-create invariant owns that path); this service does not
  create channels.
* ``set_permissions``/overwrite changes and ``clone`` are a deliberate
  follow-up — they keep their current cog paths until routed here in a later
  PR, so the convergence invariant pins only ``.delete`` / ``.edit`` for now.

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
from dataclasses import dataclass

import discord

from services.lifecycle import contracts as lc

logger = logging.getLogger("bot.services.channel_lifecycle")

DOMAIN = "channel"
EVT_CHANNEL_LIFECYCLE = "channel.lifecycle_changed"

_OPERATIONS = ("rename", "move", "delete", "reorder")
_REVERSIBILITY = {
    "rename": lc.REVERSIBLE,
    "move": lc.COMPENSATABLE,
    "delete": lc.IRREVERSIBLE,
    "reorder": lc.COMPENSATABLE,
}


@dataclass(frozen=True)
class ChannelLifecycleRequest:
    """Typed request — one operation over one or more channels."""

    operation: str  # "rename" | "move" | "delete" | "reorder"
    channel_ids: tuple[int, ...]
    new_name: str | None = None  # rename
    category_id: int | None = None  # move (None = remove from category)
    position: str | None = None  # reorder: "top" | "bottom" (default bottom)
    reason: str | None = None


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
    "ChannelLifecycleRequest",
    "ChannelLifecycleService",
]
