"""Support tickets — the audited write boundary.

Every state change for the ``ticket`` subsystem flows through here: opening a
ticket (which creates its private channel), claiming, closing (transcript +
DM + channel teardown), adding / removing participants, editing config, and the
blacklist.  Each write follows the platform mutation contract
(``docs/runtime_contracts.md`` §9):

* DB writes run inside one :func:`utils.db.transaction`;
* an audited :func:`services.audit_events.emit_audit_action` companion fires
  after commit;
* a catalogued EventBus signal (``ticket.opened`` / ``ticket.closed``) is
  emitted **after** commit, never inside the transaction.

Channel *creation* is delegated to
:class:`services.channel_lifecycle_service.ChannelLifecycleService` — the one
sanctioned manual channel creator (P0-4 / Q-0100).  The private permission
overwrites and the eventual teardown are applied directly on the resolved
channel (the no-direct-channel-mutation invariant fences only the channel cog
and ``views/channels/``, not this service).

A service must not import views, so this module never posts the welcome embed
or the Claim/Close control panel itself — it emits ``ticket.opened`` and
``cogs.ticket_cog`` renders the UI.  That keeps the command, panel-button, and
AI-natural-language open paths on one UI seam.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

import discord

from core.events import bus
from core.runtime import guild_resources
from services import ticket_service
from services.audit_events import emit_audit_action
from services.channel_lifecycle_service import ChannelLifecycleService
from services.lifecycle import contracts as lc
from utils import db

logger = logging.getLogger("bot.services.ticket_mutation")

_SUBSYSTEM = "ticket"
_MAX_SUBJECT_LEN = 200
_CHANNEL_SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class TicketOpenResult:
    """Outcome of an open attempt."""

    success: bool
    ticket_id: int = 0
    channel_id: int = 0
    message: str = ""
    reason: str = ""


@dataclass(frozen=True)
class TicketActionResult:
    """Outcome of a claim / close / add / remove / config write."""

    success: bool
    message: str = ""


def _now() -> int:
    return int(time.time())


def _slug(name: str) -> str:
    """Discord-safe channel-name fragment from a display name."""
    slug = _CHANNEL_SLUG_RE.sub("-", name.lower()).strip("-")
    return slug[:24] or "user"


def _clean_subject(subject: str) -> str:
    subject = " ".join(subject.split()).strip()
    return subject[:_MAX_SUBJECT_LEN] if subject else "Support request"


# --------------------------------------------------------------------------- #
# Open
# --------------------------------------------------------------------------- #


async def open_ticket(
    guild: discord.Guild,
    opener: discord.Member,
    subject: str,
    *,
    source: str = "command",
    actor_type: str = "user",
) -> TicketOpenResult:
    """Open a ticket for ``opener``: create the private channel + the row.

    Re-checks eligibility (the per-user cap / blacklist / configured gate) so
    every caller — command, panel button, and the AI action tool — is bounded
    identically. On success, emits ``ticket.opened`` for ``cogs.ticket_cog`` to
    render the welcome + control panel.
    """
    subject = _clean_subject(subject)

    eligibility = await ticket_service.check_open_eligibility(guild.id, opener.id)
    if not eligibility.allowed:
        return TicketOpenResult(
            False,
            message=eligibility.message,
            reason=eligibility.reason,
        )

    cfg = await ticket_service.get_config(guild.id)
    if cfg is None:  # pragma: no cover — eligibility already proved configured
        return TicketOpenResult(
            False,
            message="The ticket system isn't set up on this server.",
            reason=ticket_service.REASON_NOT_CONFIGURED,
        )

    # 1. Create the channel through the audited lifecycle seam.
    channel_name = f"ticket-{_slug(opener.display_name)}"
    result = await ChannelLifecycleService().create_channels(
        guild,
        [channel_name],
        opener,
        category_id=cfg.category_id,
        category_name=cfg.category_name if cfg.category_id is None else None,
        kind="text",
        reason=f"Support ticket opened by {opener} ({source})",
        actor_type=actor_type,
    )
    if result.outcome != lc.SUCCESS or not result.applied:
        logger.warning(
            "ticket open: channel creation failed for guild=%s opener=%s: %s",
            guild.id,
            opener.id,
            result.first_error,
        )
        return TicketOpenResult(
            False,
            message=(
                "I couldn't create the ticket channel — I may be missing the "
                "**Manage Channels** permission."
            ),
            reason="channel_failed",
        )

    channel_id = result.applied[0].target_id
    channel = guild.get_channel(channel_id)

    # 2. Lock the channel down to opener + staff + bot.
    if isinstance(channel, discord.TextChannel):
        await _apply_private_overwrites(guild, channel, opener, cfg)

    # 3. Persist the ticket row.
    try:
        async with db.transaction() as conn:
            ticket_id = await db.ticket_create(
                guild.id,
                channel_id,
                opener.id,
                subject,
                source=source,
                created_at=_now(),
                conn=conn,
            )
    except Exception:
        logger.exception(
            "ticket open: row insert failed for guild=%s channel=%s; "
            "tearing the orphan channel down.",
            guild.id,
            channel_id,
        )
        if isinstance(channel, discord.TextChannel):
            try:
                await channel.delete(reason="Ticket row insert failed")
            except Exception:  # pragma: no cover — best-effort cleanup
                logger.exception("ticket open: orphan channel cleanup failed")
        return TicketOpenResult(
            False,
            message="Something went wrong saving the ticket. Please try again.",
            reason="db_failed",
        )

    # 4. Audit + advisory event (after commit).
    await _emit_audit(
        guild_id=guild.id,
        mutation_type="open",
        target=f"ticket:{ticket_id}",
        new_value=f"subject={subject!r} source={source}",
        actor_id=opener.id,
        actor_type=actor_type,
    )
    await _emit_bus(
        "ticket.opened",
        guild_id=guild.id,
        ticket_id=ticket_id,
        channel_id=channel_id,
        opener_id=opener.id,
        subject=subject,
        source=source,
    )

    mention = f"<#{channel_id}>"
    return TicketOpenResult(
        True,
        ticket_id=ticket_id,
        channel_id=channel_id,
        message=f"🎫 Opened your ticket: {mention}",
        reason=ticket_service.REASON_OK,
    )


async def _apply_private_overwrites(
    guild: discord.Guild,
    channel: discord.TextChannel,
    opener: discord.Member,
    cfg: ticket_service.TicketConfig,
) -> None:
    """Make ``channel`` visible only to the opener, staff, and the bot."""
    overwrites: dict[Any, discord.PermissionOverwrite] = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        opener: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
            read_message_history=True,
        ),
    }
    me = guild.me
    if me is not None:
        overwrites[me] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True,
            read_message_history=True,
        )
    if cfg.staff_role_id is not None:
        staff_role = guild_resources.resolve_role(guild, role_id=cfg.staff_role_id)
        if staff_role is not None:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True,
                manage_messages=True,
            )
    try:
        await channel.edit(overwrites=overwrites, reason="Ticket privacy")
    except Exception:  # pragma: no cover — defensive; ticket still usable
        logger.exception(
            "ticket open: overwrite apply failed for channel=%s",
            channel.id,
        )


# --------------------------------------------------------------------------- #
# Claim / close / participants
# --------------------------------------------------------------------------- #


async def claim_ticket(
    ticket: dict[str, Any],
    claimer: discord.Member,
) -> TicketActionResult:
    """Mark a ticket as claimed by ``claimer`` (staff)."""
    if ticket.get("status") != "open":
        return TicketActionResult(False, "This ticket is already closed.")
    if ticket.get("claimed_by"):
        who = f"<@{ticket['claimed_by']}>"
        if ticket["claimed_by"] == claimer.id:
            return TicketActionResult(False, "You've already claimed this ticket.")
        return TicketActionResult(False, f"Already claimed by {who}.")

    ticket_id = int(ticket["id"])
    async with db.transaction() as conn:
        await db.ticket_set_claim(ticket_id, claimer.id, conn=conn)
    await _emit_audit(
        guild_id=int(ticket["guild_id"]),
        mutation_type="claim",
        target=f"ticket:{ticket_id}",
        new_value=f"claimed_by={claimer.id}",
        actor_id=claimer.id,
    )
    return TicketActionResult(True, f"✋ {claimer.mention} claimed this ticket.")


async def close_ticket(
    channel: discord.TextChannel,
    ticket: dict[str, Any],
    closer: discord.Member,
    *,
    reason: str | None = None,
    delete_after: bool = True,
) -> TicketActionResult:
    """Close a ticket: persist, post + DM a transcript, then tear the channel down."""
    if ticket.get("status") != "open":
        return TicketActionResult(False, "This ticket is already closed.")

    ticket_id = int(ticket["id"])
    guild = channel.guild
    cfg = await ticket_service.get_config(guild.id)

    transcript = await ticket_service.build_transcript(channel)

    async with db.transaction() as conn:
        await db.ticket_close(
            ticket_id,
            closed_by=closer.id,
            close_reason=reason,
            closed_at=_now(),
            conn=conn,
        )

    await _emit_audit(
        guild_id=guild.id,
        mutation_type="close",
        target=f"ticket:{ticket_id}",
        new_value=f"closed_by={closer.id} reason={reason!r}",
        actor_id=closer.id,
    )
    await _emit_bus(
        "ticket.closed",
        guild_id=guild.id,
        ticket_id=ticket_id,
        channel_id=channel.id,
        opener_id=int(ticket["opener_id"]),
        closed_by=closer.id,
    )

    await _deliver_transcript(guild, cfg, ticket, transcript, closer, reason)

    if delete_after:
        try:
            await channel.delete(reason=f"Ticket #{ticket_id} closed by {closer}")
        except Exception:  # pragma: no cover — channel may already be gone
            logger.exception("ticket close: channel delete failed for %s", channel.id)

    return TicketActionResult(True, f"🔒 Ticket #{ticket_id} closed.")


async def _deliver_transcript(
    guild: discord.Guild,
    cfg: ticket_service.TicketConfig | None,
    ticket: dict[str, Any],
    transcript: str,
    closer: discord.Member,
    reason: str | None,
) -> None:
    """Post the transcript to the log channel and DM the opener (best-effort)."""
    ticket_id = int(ticket["id"])
    opener_id = int(ticket["opener_id"])
    subject = ticket.get("subject", "")

    def _file() -> discord.File:
        import io

        data = io.BytesIO(transcript.encode("utf-8"))
        return discord.File(data, filename=f"ticket-{ticket_id}-transcript.txt")

    embed = discord.Embed(
        title=f"🎫 Ticket #{ticket_id} closed",
        description=f"**Subject:** {subject}",
        color=discord.Color.dark_grey(),
    )
    embed.add_field(name="Opened by", value=f"<@{opener_id}>", inline=True)
    embed.add_field(name="Closed by", value=closer.mention, inline=True)
    if reason:
        embed.add_field(name="Reason", value=reason[:1024], inline=False)

    if cfg is not None and cfg.log_channel_id is not None:
        log_channel = guild.get_channel(cfg.log_channel_id)
        if isinstance(log_channel, discord.TextChannel):
            try:
                await log_channel.send(embed=embed, file=_file())
            except Exception:  # pragma: no cover — best-effort
                logger.exception("ticket close: log post failed")

    opener = guild_resources.resolve_member(guild, opener_id)
    if opener is not None:
        try:
            await opener.send(
                content=(
                    f"Your ticket **#{ticket_id}** in **{guild.name}** was closed. "
                    "A transcript is attached."
                ),
                file=_file(),
            )
        except Exception:  # pragma: no cover — DMs may be closed
            logger.debug("ticket close: opener DM failed (DMs closed?)")


async def add_participant(
    channel: discord.TextChannel,
    member: discord.Member,
    actor: discord.Member,
) -> TicketActionResult:
    """Grant ``member`` access to a ticket channel."""
    try:
        await channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            reason=f"Added to ticket by {actor}",
        )
    except Exception:
        logger.exception("ticket add: set_permissions failed for %s", channel.id)
        return TicketActionResult(False, "I couldn't add that member.")
    ticket = await ticket_service.get_ticket_for_channel(channel.id)
    await _emit_audit(
        guild_id=channel.guild.id,
        mutation_type="add_participant",
        target=f"ticket:{ticket['id'] if ticket else 0}",
        new_value=f"added={member.id}",
        actor_id=actor.id,
    )
    return TicketActionResult(True, f"➕ Added {member.mention} to the ticket.")


async def remove_participant(
    channel: discord.TextChannel,
    member: discord.Member,
    actor: discord.Member,
) -> TicketActionResult:
    """Revoke ``member``'s access to a ticket channel."""
    try:
        await channel.set_permissions(
            member,
            overwrite=None,
            reason=f"Removed from ticket by {actor}",
        )
    except Exception:
        logger.exception("ticket remove: set_permissions failed for %s", channel.id)
        return TicketActionResult(False, "I couldn't remove that member.")
    ticket = await ticket_service.get_ticket_for_channel(channel.id)
    await _emit_audit(
        guild_id=channel.guild.id,
        mutation_type="remove_participant",
        target=f"ticket:{ticket['id'] if ticket else 0}",
        new_value=f"removed={member.id}",
        actor_id=actor.id,
    )
    return TicketActionResult(True, f"➖ Removed {member.mention} from the ticket.")


# --------------------------------------------------------------------------- #
# Config + blacklist
# --------------------------------------------------------------------------- #


async def update_config(
    guild_id: int,
    actor_id: int,
    **fields: Any,
) -> TicketActionResult:
    """Upsert ticket config (``staff_role_id`` / ``category_id`` / … )."""
    async with db.transaction() as conn:
        await db.ticket_upsert_config(
            guild_id,
            updated_at=_now(),
            conn=conn,
            **fields,
        )
    await _emit_audit(
        guild_id=guild_id,
        mutation_type="config",
        target=f"guild:{guild_id}",
        new_value=", ".join(f"{k}={v}" for k, v in fields.items()) or "(no change)",
        actor_id=actor_id,
    )
    return TicketActionResult(True, "✅ Ticket settings updated.")


async def set_blacklist(
    guild_id: int,
    user_id: int,
    actor_id: int,
    *,
    blacklisted: bool,
    reason: str | None = None,
) -> TicketActionResult:
    """Add or remove a member from the ticket blacklist."""
    async with db.transaction() as conn:
        if blacklisted:
            await db.ticket_add_blacklist(
                guild_id,
                user_id,
                added_by=actor_id,
                reason=reason,
                added_at=_now(),
                conn=conn,
            )
        else:
            await db.ticket_remove_blacklist(guild_id, user_id, conn=conn)
    await _emit_audit(
        guild_id=guild_id,
        mutation_type="blacklist",
        target=f"user:{user_id}",
        new_value=f"blacklisted={blacklisted}",
        actor_id=actor_id,
    )
    verb = "added to" if blacklisted else "removed from"
    return TicketActionResult(True, f"<@{user_id}> {verb} the ticket blacklist.")


# --------------------------------------------------------------------------- #
# Audit / bus helpers
# --------------------------------------------------------------------------- #


async def _emit_audit(
    *,
    guild_id: int,
    mutation_type: str,
    target: str,
    new_value: str | None,
    actor_id: int | None,
    actor_type: str = "user",
) -> None:
    await emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem=_SUBSYSTEM,
        mutation_type=mutation_type,
        target=target,
        scope="guild",
        guild_id=guild_id,
        prev_value=None,
        new_value=new_value,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=lc.now_utc(),
    )


async def _emit_bus(event: str, **payload: Any) -> None:
    try:
        await bus.emit(event, **payload)
    except Exception:  # pragma: no cover — publish-accepted; never raises up
        logger.exception("ticket: %s emission failed (DB state authoritative)", event)
