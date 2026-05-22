from __future__ import annotations

from dataclasses import dataclass

def _extract_command_name(content: str, prefixes: list[str]) -> str | None:
    for prefix in prefixes:
        if content.startswith(prefix):
            rest = content[len(prefix) :].split()[0] if content[len(prefix) :].strip() else ""
            return rest.lower() if rest else None
    return None


@dataclass
class HistoryCleanupPlan:
    scanned: int
    matched: list


async def build_history_cleanup_plan(
    channel,
    *,
    limit: int,
    mode: str,
    keyword: str | None = None,
    command_prefixes: list[str] | None = None,
    prohibited_words: list[str] | None = None,
) -> HistoryCleanupPlan:
    scanned = 0
    matched: list = []
    command_prefixes = command_prefixes or []
    prohibited_words = [w.lower() for w in (prohibited_words or [])]
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
            include = _extract_command_name(message.content.strip(), command_prefixes) is not None
        elif mode == "prohibited":
            include = any(word in content for word in prohibited_words)
        if include:
            matched.append(message)
    return HistoryCleanupPlan(scanned=scanned, matched=matched)
