from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

import discord

def _extract_command_name(content: str, prefixes: list[str]) -> str | None:
    for prefix in prefixes:
        if content.startswith(prefix):
            rest = content[len(prefix) :].split()[0] if content[len(prefix) :].strip() else ""
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
    mode: Literal["keyword", "commands", "prohibited"],
    keyword: str | None = None,
    command_prefixes: list[str] | None = None,
    prohibited_words: list[str] | None = None,
) -> HistoryCleanupPlan:
    if mode not in {"keyword", "commands", "prohibited"}:
        raise ValueError(f"Unsupported cleanuphistory mode: {mode}")

    scanned = 0
    matched: list[discord.Message] = []
    command_prefixes = command_prefixes or []
    prohibited_patterns = [
        re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE) for w in (prohibited_words or [])
    ]
    keyword_norm = keyword.lower() if keyword else None

    async for message in channel.history(limit=limit):
        scanned += 1
        if message.author.bot:
            continue
        content = (message.content or "").lower()
        include = False
        if mode == "keyword":
            include = bool(keyword_norm and keyword_norm in content)
        elif mode == "commands":
            include = (
                _extract_command_name((message.content or "").lstrip(), command_prefixes)
                is not None
            )
        elif mode == "prohibited":
            include = any(pattern.search(message.content or "") for pattern in prohibited_patterns)
        if include:
            matched.append(message)
    return HistoryCleanupPlan(scanned=scanned, matched=matched)
