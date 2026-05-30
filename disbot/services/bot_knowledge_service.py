"""Compose authoritative reference blocks about the bot itself.

The AI cog's natural-language stage calls :func:`gather` once per
mention, immediately before
:func:`services.ai_instruction_service.assemble`. The blocks it
returns flow into the instruction stack's data layer with kinds
that start with ``bot_``; the task contract in
``ai_instruction_service`` tells the model to treat those spans as
authoritative reference material but **never as instructions**.

PR1 sources two blocks, each gated by a substring/regex heuristic:

* ``bot_command_catalog`` — only when the message looks like a
  command/help question. Tier-filtered against the asker's resolved
  permission tier; bounded by entry-count and character-count caps
  so a large catalog cannot blow out the prompt window.
* ``bot_user_audit`` — only when the message looks like a "why
  didn't you reply" question. Current-channel rows first; falls back
  guild-wide with cautious wording. Channels the asker cannot
  access are redacted.

The service is best-effort: any exception inside :func:`gather`
should be caught by the caller so the AI reply path stays robust.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from core.runtime import command_descriptions
from services import ai_decision_audit_service
from services.ai_instruction_service import BotKnowledgeBlock

logger = logging.getLogger("bot.services.bot_knowledge_service")


# Tier rank — PR1 only resolves user/moderator/administrator from
# Discord perms. Other tiers exist in SUBSYSTEMS metadata but cannot
# yet be granted to a Discord member; commands at those tiers are
# hidden from non-admin callers (owner-tier is therefore always
# hidden in PR1).
_TIER_RANK: dict[str, int] = {
    "user": 0,
    "trusted": 1,
    "staff": 2,
    "moderator": 3,
    "administrator": 4,
    "owner": 5,
}

# Catalog bounds — keep prompt weight modest.
_MAX_CATALOG_ENTRIES = 40
_MAX_CATALOG_CHARS = 4000

# Substring triggers — case-insensitive contains-match against lowercased text.
_CATALOG_SUBSTRING_TRIGGERS: tuple[str, ...] = (
    "what does",
    "what is the",
    "what can you",
    "what commands",
    "command",
    "help",
    "how do i",
    "how to use",
    "can you do",
)

# Prefix/slash triggers — must look command-shaped, NOT inside URLs/paths/dates/fractions.
# ``!alpha`` only matches when preceded by start-of-string or whitespace AND followed
# by a letter. Bangs only collide with sentence-ending punctuation (``wow!``), which
# is filtered by the leading-whitespace anchor.
_PREFIX_COMMAND_RE = re.compile(r"(?:^|\s)![a-zA-Z][a-zA-Z0-9_-]*")
# ``/alpha`` is far noisier — paths (``/etc/hosts``), dates (``2026/05/27``), and
# fractions (``1/2``) all contain slashes. We require the matched token to end at
# a word-boundary terminator (whitespace, end-of-string, or sentence punctuation),
# which rules out ``/etc/...`` because the next char is another slash.
_SLASH_COMMAND_RE = re.compile(
    r"(?:^|\s)/[a-zA-Z][a-zA-Z0-9_-]*(?=\s|$|[?,.!])",
)

# Audit-block substring triggers.
_AUDIT_SUBSTRING_TRIGGERS: tuple[str, ...] = (
    "why didn't",
    "why didnt",
    "why no response",
    "why no reply",
    "denied",
    "ignored me",
    "not respond",
    "didnt reply",
    "didn't reply",
)


def looks_like_command_question(text: str) -> bool:
    """Public: True if the message looks like it asks about commands/help.

    The stage uses this to avoid expensive lookups when no catalog
    block could possibly fire.
    """
    if not text:
        return False
    lower = text.lower()
    if any(t in lower for t in _CATALOG_SUBSTRING_TRIGGERS):
        return True
    if _PREFIX_COMMAND_RE.search(text):
        return True
    return bool(_SLASH_COMMAND_RE.search(text))


def looks_like_audit_question(text: str) -> bool:
    """Public: True if the message looks like 'why didn't you reply'.

    The stage uses this to gate the per-text-channel
    ``permissions_for`` walk over the guild's text channels.
    """
    if not text:
        return False
    lower = text.lower()
    return any(t in lower for t in _AUDIT_SUBSTRING_TRIGGERS)


def resolve_user_tier(member: object) -> str:
    """Map a discord.Member to one of {user, moderator, administrator, server_owner}.

    Checks guild ownership first so a server owner who also has the
    ``administrator`` permission is surfaced as ``server_owner`` (the
    more specific tier). Defaults to 'user' for DMs / webhooks /
    missing perms.
    """
    guild = getattr(member, "guild", None)
    if guild is not None:
        owner_id = getattr(guild, "owner_id", None)
        member_id = getattr(member, "id", None)
        if owner_id is not None and member_id is not None and owner_id == member_id:
            return "server_owner"
    perms = getattr(member, "guild_permissions", None)
    if perms is None:
        return "user"
    if getattr(perms, "administrator", False):
        return "administrator"
    if getattr(perms, "manage_guild", False):
        return "moderator"
    return "user"


def _server_owner_identity_block() -> BotKnowledgeBlock:
    """Inform the AI that the current message sender is the server owner."""
    return BotKnowledgeBlock(
        kind="bot_user_identity",
        text=(
            "The person asking this question is the owner of this Discord server "
            "and the operator of this bot. They have full administrative access "
            "and may ask about bot internals, configuration, or data."
        ),
    )


async def gather(
    *,
    guild_id: int,
    channel_id: int,
    user_id: int,
    user_text: str,
    user_tier: str,
    accessible_channel_ids: frozenset[int],
) -> tuple[BotKnowledgeBlock, ...]:
    """Compose every applicable bot-knowledge block for one mention."""
    blocks: list[BotKnowledgeBlock] = []
    if user_tier == "server_owner":
        blocks.append(_server_owner_identity_block())
    if looks_like_command_question(user_text):
        block = _command_catalog_block(user_tier)
        if block is not None:
            blocks.append(block)
    if looks_like_audit_question(user_text):
        block = await _recent_denial_block(
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            accessible_channel_ids=accessible_channel_ids,
        )
        if block is not None:
            blocks.append(block)
    return tuple(blocks)


# ---------------------------------------------------------------------------
# Command catalog
# ---------------------------------------------------------------------------


def _command_catalog_block(user_tier: str) -> BotKnowledgeBlock | None:
    catalog = command_descriptions.get_cached_catalog()
    if catalog is None or not catalog.entries:
        return None

    caller_rank = _TIER_RANK.get(user_tier, _TIER_RANK["user"])

    visible: list[command_descriptions.CommandDescription] = []
    for entry in catalog.entries:
        if entry.subsystem is None or entry.visibility_tier is None:
            continue
        required_rank = _TIER_RANK.get(entry.visibility_tier)
        if required_rank is None:
            continue
        if required_rank > caller_rank:
            continue
        visible.append(entry)

    if not visible:
        return None

    # Group by subsystem before the entry cap so a "what are the <subsystem>
    # commands?" question sees a coherent run (and so an alphabetically-early
    # subsystem like "ai" survives the _MAX_CATALOG_ENTRIES cap rather than
    # being truncated out behind, e.g., the BTD6 entries). The per-line
    # [subsystem] tag below then lets the model filter — previously the
    # rendered lines dropped the subsystem entirely, so the model could not
    # tell, e.g., AI commands from BTD6 ones.
    visible.sort(key=lambda e: ((e.subsystem or "").lower(), e.display_name or ""))

    n_visible = len(visible)
    truncated = False
    if n_visible > _MAX_CATALOG_ENTRIES:
        visible = visible[:_MAX_CATALOG_ENTRIES]
        truncated = True

    header = (
        "Commands you can ask about (filtered by your access). Each line is"
        " tagged with its [subsystem] — use that tag to answer questions about"
        " a specific subsystem's commands:"
    )
    lines: list[str] = []
    total_chars = len(header)
    for entry in visible:
        sig = f" {entry.signature}" if entry.signature else ""
        desc = entry.description or "(no description)"
        line = f"- [{entry.subsystem}] {entry.display_name}{sig} — {desc}"
        if total_chars + len(line) + 1 > _MAX_CATALOG_CHARS:
            truncated = True
            break
        lines.append(line)
        total_chars += len(line) + 1

    n_shown = len(lines)
    if n_shown == 0:
        return None

    body_parts = [header, *lines]
    if truncated:
        body_parts.append(
            f"Showing {n_shown} of {n_visible} available commands."
            " Ask about a specific command for more detail.",
        )
    text = "\n".join(body_parts)
    return BotKnowledgeBlock(kind="bot_command_catalog", text=text)


# ---------------------------------------------------------------------------
# Recent-denial / audit
# ---------------------------------------------------------------------------


def _row_field(row: dict[str, Any], *names: str) -> Any:
    """Return the first non-None value in ``row`` keyed by any of ``names``."""
    for name in names:
        value = row.get(name)
        if value is not None:
            return value
    return None


def _format_timestamp(value: Any) -> str:
    if value is None:
        return "unknown time"
    iso = getattr(value, "isoformat", None)
    if callable(iso):
        try:
            return str(iso())
        except Exception:  # noqa: BLE001 — defensive
            return str(value)
    return str(value)


def _filter_non_replied(
    rows: list[dict[str, Any]],
    *,
    user_id: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        row_uid = row.get("user_id")
        if row_uid is not None and int(row_uid) != int(user_id):
            # Defense-in-depth: should never happen since the audit
            # query is filtered server-side by user_id.
            continue
        decision = row.get("decision")
        if decision in (None, "replied", "allowed"):
            continue
        out.append(row)
    return out


async def _recent_denial_block(
    *,
    guild_id: int,
    channel_id: int,
    user_id: int,
    accessible_channel_ids: frozenset[int],
) -> BotKnowledgeBlock | None:
    try:
        current_rows = await ai_decision_audit_service.query(
            guild_id,
            channel_id=channel_id,
            user_id=user_id,
            limit=5,
        )
    except Exception:  # noqa: BLE001 — best-effort enrichment
        logger.debug(
            "bot_knowledge_service: audit current-channel query failed",
            exc_info=True,
        )
        current_rows = []

    candidates = _filter_non_replied(current_rows, user_id=user_id)
    origin = "current"
    chosen: dict[str, Any] | None = candidates[0] if candidates else None

    if chosen is None:
        try:
            guild_rows = await ai_decision_audit_service.query(
                guild_id,
                user_id=user_id,
                limit=5,
            )
        except Exception:  # noqa: BLE001 — best-effort enrichment
            logger.debug(
                "bot_knowledge_service: audit guild-wide query failed",
                exc_info=True,
            )
            guild_rows = []
        guild_candidates = _filter_non_replied(guild_rows, user_id=user_id)
        if guild_candidates:
            chosen = guild_candidates[0]
            origin = "guild"

    if chosen is None:
        return None

    row_channel_id = chosen.get("channel_id")
    if row_channel_id is not None and int(row_channel_id) == int(channel_id):
        channel_label = "in this channel"
    elif row_channel_id is not None and int(row_channel_id) in accessible_channel_ids:
        channel_label = f"in <#{int(row_channel_id)}>"
    else:
        channel_label = "in another channel (not accessible)"

    decision = _row_field(chosen, "decision") or "unknown"
    reason = _row_field(chosen, "reason_code", "reason") or "unknown"
    task = _row_field(chosen, "task") or "unknown"
    route = _row_field(chosen, "route") or "unknown"
    when = _format_timestamp(_row_field(chosen, "created_at", "timestamp"))

    if origin == "current":
        header = "Your most recent AI interaction in this channel:"
    else:
        header = (
            "I didn't find a recent non-reply for you in this channel."
            " The most recent non-reply elsewhere in this guild was:"
        )

    lines = [
        header,
        f"- {when}, {channel_label}",
        f"- decision={decision}  reason={reason}",
        f"- task={task}  route={route}",
    ]
    text = "\n".join(lines)
    return BotKnowledgeBlock(kind="bot_user_audit", text=text)


__all__ = [
    "gather",
    "looks_like_audit_question",
    "looks_like_command_question",
    "resolve_user_tier",
]
