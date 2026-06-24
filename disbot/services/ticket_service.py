"""Support tickets — the read model + eligibility checks (read-only).

The query/decision half of the ``ticket`` subsystem.  Everything here is
side-effect-free: it reads :mod:`utils.db.tickets` (config, counts, blacklist)
and Discord state and returns typed values.  The audited *writes* live in
:mod:`services.ticket_mutation`.

Both the command surface (``cogs.ticket_cog``) and the AI action tool
(``services.ai_tools.open_support_ticket``) call :func:`check_open_eligibility`
before opening, so the per-user cap + blacklist + "is this guild even set up?"
rules have exactly one home.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from utils import db

logger = logging.getLogger("bot.services.ticket")

# Eligibility reason codes — stable strings so the AI tool / command surface
# can map them to copy without re-deriving the rule.
REASON_OK = "ok"
REASON_DISABLED = "disabled"  # subsystem off, or never configured
REASON_NOT_CONFIGURED = "not_configured"  # no staff role set yet
REASON_BLACKLISTED = "blacklisted"
REASON_LIMIT_REACHED = "limit_reached"

_DEFAULT_CATEGORY_NAME = "Tickets"


@dataclass(frozen=True)
class TicketConfig:
    """Typed view of a guild's ``ticket_config`` row."""

    guild_id: int
    enabled: bool
    staff_role_id: int | None
    category_id: int | None
    log_channel_id: int | None
    panel_channel_id: int | None
    panel_message_id: int | None
    max_open_per_user: int
    ping_staff_on_open: bool

    @property
    def category_name(self) -> str:
        """Name used to get-or-create the ticket category when no id is set."""
        return _DEFAULT_CATEGORY_NAME

    @property
    def is_set_up(self) -> bool:
        """True when the guild has done the minimum setup (a staff role)."""
        return self.enabled and self.staff_role_id is not None


@dataclass(frozen=True)
class OpenEligibility:
    """Whether a member may open a ticket right now, with a reason code."""

    allowed: bool
    reason: str
    open_count: int = 0
    max_open: int = 0

    @property
    def message(self) -> str:
        """A short human-facing explanation for the reason code."""
        if self.allowed:
            return "You can open a ticket."
        return {
            REASON_DISABLED: "The ticket system isn't enabled on this server.",
            REASON_NOT_CONFIGURED: (
                "The ticket system isn't set up yet — an admin needs to run "
                "`!ticketsetup` and choose a staff role first."
            ),
            REASON_BLACKLISTED: "You can't open tickets on this server.",
            REASON_LIMIT_REACHED: (
                f"You already have {self.open_count} open ticket(s) "
                f"(limit {self.max_open}). Close one before opening another."
            ),
        }.get(self.reason, "You can't open a ticket right now.")


def _to_config(row: dict[str, Any] | None) -> TicketConfig | None:
    if row is None:
        return None
    return TicketConfig(
        guild_id=int(row["guild_id"]),
        enabled=bool(row["enabled"]),
        staff_role_id=row["staff_role_id"],
        category_id=row["category_id"],
        log_channel_id=row["log_channel_id"],
        panel_channel_id=row["panel_channel_id"],
        panel_message_id=row["panel_message_id"],
        max_open_per_user=int(row["max_open_per_user"]),
        ping_staff_on_open=bool(row["ping_staff_on_open"]),
    )


async def get_config(guild_id: int) -> TicketConfig | None:
    """Return the guild's ticket config, or ``None`` if never configured."""
    return _to_config(await db.ticket_get_config(guild_id))


async def check_open_eligibility(guild_id: int, user_id: int) -> OpenEligibility:
    """Decide whether ``user_id`` may open a new ticket in ``guild_id``.

    The single source of truth for the open gate — enabled, configured, not
    blacklisted, and under the per-user open cap. Called by every open path.
    """
    cfg = await get_config(guild_id)
    if cfg is None or not cfg.enabled:
        return OpenEligibility(False, REASON_DISABLED)
    if not cfg.is_set_up:
        return OpenEligibility(False, REASON_NOT_CONFIGURED)
    if await db.ticket_is_blacklisted(guild_id, user_id):
        return OpenEligibility(False, REASON_BLACKLISTED)
    open_count = await db.ticket_count_open_for_user(guild_id, user_id)
    if open_count >= cfg.max_open_per_user:
        return OpenEligibility(
            False,
            REASON_LIMIT_REACHED,
            open_count=open_count,
            max_open=cfg.max_open_per_user,
        )
    return OpenEligibility(
        True,
        REASON_OK,
        open_count=open_count,
        max_open=cfg.max_open_per_user,
    )


async def list_user_open(guild_id: int, user_id: int) -> list[dict[str, Any]]:
    """A member's open tickets in the guild, newest first."""
    return await db.ticket_list_for_user(guild_id, user_id)


async def list_open(guild_id: int, *, limit: int = 25) -> list[dict[str, Any]]:
    """All open tickets in the guild, newest first (staff listing)."""
    return await db.ticket_list_open(guild_id, limit=limit)


async def get_ticket_for_channel(channel_id: int) -> dict[str, Any] | None:
    """The ticket bound to ``channel_id`` (for in-channel control buttons)."""
    return await db.ticket_get_by_channel(channel_id)


async def build_transcript(channel: Any, *, max_messages: int = 500) -> str:
    """Render a plain-text transcript of a ticket channel, oldest first.

    Best-effort: reads up to ``max_messages`` from history. Returns a header +
    one ``[time] author: content`` line per message (attachments noted). Used
    on close to preserve the conversation for the log channel + the opener DM.
    """
    lines: list[str] = []
    try:
        async for msg in channel.history(limit=max_messages, oldest_first=True):
            stamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
            author = getattr(msg.author, "display_name", str(msg.author))
            content = msg.content or ""
            if msg.attachments:
                names = ", ".join(a.filename for a in msg.attachments)
                content = f"{content} [attachments: {names}]".strip()
            if not content and msg.embeds:
                content = "[embed]"
            lines.append(f"[{stamp}] {author}: {content}")
    except Exception:  # pragma: no cover — defensive; transcript is best-effort
        logger.exception(
            "ticket transcript: history read failed for channel %s",
            getattr(channel, "id", "?"),
        )
        if not lines:
            return "Transcript unavailable (could not read channel history)."
    header = f"Transcript — #{getattr(channel, 'name', 'ticket')} "
    header += f"({len(lines)} message(s))"
    return header + "\n" + ("\n".join(lines) if lines else "(no messages)")
