from __future__ import annotations

import datetime as dt
import logging
import re
from dataclasses import dataclass
from typing import Literal

import discord

logger = logging.getLogger("bot.history_cleanup")


def _extract_command_name(content: str, prefixes: list[str]) -> str | None:
    for prefix in prefixes:
        if content.startswith(prefix):
            rest = (
                content[len(prefix) :].split()[0]
                if content[len(prefix) :].strip()
                else ""
            )
            return rest.lower() if rest else None
    return None


@dataclass
class HistoryCleanupPlan:
    scanned: int
    matched: list[discord.Message]


async def build_history_cleanup_plan(
    channel,
    *,
    limit: int,
    mode: Literal["keyword", "commands", "prohibited", "spam"],
    keyword: str | None = None,
    command_prefixes: list[str] | None = None,
    prohibited_words: list[str] | None = None,
    exclude_message_ids: set[int] | None = None,
    spam_duplicate_window_seconds: int = 15,
) -> HistoryCleanupPlan:
    if mode not in {"keyword", "commands", "prohibited", "spam"}:
        raise ValueError(f"Unsupported cleanuphistory mode: {mode}")

    scanned = 0
    matched: list[discord.Message] = []
    scanned_messages: list[discord.Message] = []
    exclude_message_ids = exclude_message_ids or set()
    command_prefixes = command_prefixes or []
    prohibited_patterns = [
        re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE)
        for w in (prohibited_words or [])
    ]
    keyword_norm = keyword.lower() if keyword else None
    spam_last_seen: dict[str, dt.datetime] = {}

    async for message in channel.history(limit=limit):
        scanned += 1
        scanned_messages.append(message)
        if message.id in exclude_message_ids:
            continue
        if message.author.bot:
            continue
        content = (message.content or "").lower()
        include = False
        if mode == "keyword":
            include = bool(keyword_norm and keyword_norm in content)
        elif mode == "commands":
            include = (
                _extract_command_name(
                    (message.content or "").lstrip(),
                    command_prefixes,
                )
                is not None
            )
        elif mode == "prohibited":
            include = any(
                pattern.search(message.content or "") for pattern in prohibited_patterns
            )
        elif mode == "spam":
            # processed in a second pass oldest→newest (history API is newest→oldest)
            continue
        if include:
            matched.append(message)
    if mode == "spam":
        for message in reversed(scanned_messages):
            if message.id in exclude_message_ids or message.author.bot:
                continue
            normalized = " ".join((message.content or "").lower().split())
            if not normalized:
                continue
            created_at = message.created_at
            previous = spam_last_seen.get(normalized)
            if previous is None:
                spam_last_seen[normalized] = created_at
                continue
            delta = (created_at - previous).total_seconds()
            if delta <= spam_duplicate_window_seconds:
                matched.append(message)
            else:
                spam_last_seen[normalized] = created_at
    return HistoryCleanupPlan(scanned=scanned, matched=matched)


async def build_author_cleanup_plan(
    channel,
    *,
    author_id: int,
    limit: int,
    exclude_message_ids: set[int] | None = None,
) -> HistoryCleanupPlan:
    """Plan a post-moderation sweep of one member's recent messages.

    Scans up to *limit* recent messages in *channel* and matches those whose
    author is ``author_id`` — the target of a kick/ban whose leftover messages
    a guild has opted to clear (server-management PR10).  Returns the same
    :class:`HistoryCleanupPlan` the keyword/command/prohibited/spam modes
    produce, so :func:`apply_history_cleanup_plan` applies all of them
    identically.  This is a *plan* only — no message is deleted here.
    """
    exclude = exclude_message_ids or set()
    scanned = 0
    matched: list[discord.Message] = []
    async for message in channel.history(limit=limit):
        scanned += 1
        if message.id in exclude:
            continue
        author = message.author
        if author is not None and author.id == author_id:
            matched.append(message)
    return HistoryCleanupPlan(scanned=scanned, matched=matched)


@dataclass(frozen=True)
class CleanupApplyResult:
    """Outcome of applying a :class:`HistoryCleanupPlan` — counts only."""

    deleted: int
    failed: int


async def apply_history_cleanup_plan(plan: HistoryCleanupPlan) -> CleanupApplyResult:
    """Delete every message a plan matched, one at a time (best-effort).

    The single canonical apply path shared by the ``!cleanuphistory`` command
    and the moderation post-action sweep, so the deletion mechanics live in one
    place (the cleanup subsystem) rather than being re-implemented per caller.
    Messages are deleted individually — Discord's bulk delete refuses messages
    older than 14 days and gives no per-message failure isolation.  A
    per-message ``Forbidden`` / ``HTTPException`` (including an already-deleted
    ``NotFound``) is counted as a failure and never raised; the caller decides
    how to surface the counts.
    """
    deleted = 0
    failed = 0
    for message in plan.matched:
        try:
            await message.delete()
            deleted += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1
    if failed:
        logger.warning(
            "apply_history_cleanup_plan: %d of %d message(s) could not be deleted",
            failed,
            len(plan.matched),
        )
    return CleanupApplyResult(deleted=deleted, failed=failed)
