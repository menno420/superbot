"""BTD6 context owner for the central AI stage.

The BTD6 cog's intent-resolution / confidence-threshold logic lives
here so it can be invoked by the central natural-language stage when
the task router classifies a message as
:attr:`AITask.BTD6_ANSWER`.

PR3 wires real grounding: the resolver's typed entities become
:class:`BTD6FactQuery` rows, and :func:`btd6_fact_store.fetch_for_intent`
returns matching ``btd6_facts`` rows joined to the source registry.
Each row is sanitised (control chars stripped, capped at 240 chars)
and rendered with a provenance label before reaching the instruction
stack — which itself wraps the whole bundle as untrusted data, so
adversarial text inside body_json never reaches the system prompt
unwrapped.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("bot.services.btd6_context")

# Control characters that could otherwise break out of the
# untrusted-data envelope or confuse the LLM tokenizer.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Maximum chars per rendered fact string. The instruction service
# treats facts as data, but bounded length keeps total context
# predictable and prevents one fact from filling the window.
_FACT_TEXT_CAP = 240

_DEFAULT_SOURCE_SUMMARY = "data.ninjakiwi.com (Tier 1)"
_FALLBACK_SOURCE_SUMMARY = "no btd6_facts rows for intent"


@dataclass(frozen=True)
class BTD6Context:
    """Retrieved facts ready for the instruction stack."""

    facts: tuple[str, ...]
    source_summary: str
    confidence: float


def _sanitise(value: object) -> str:
    """Strip control chars, collapse whitespace, cap at 240 chars.

    Non-strings return an empty string. Used on every value that
    would otherwise reach the LLM via the untrusted-data envelope.
    """
    if not isinstance(value, str):
        return ""
    cleaned = _CONTROL_CHARS.sub("", value)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > _FACT_TEXT_CAP:
        cleaned = cleaned[: _FACT_TEXT_CAP - 1] + "…"
    return cleaned


def _relative_time(fetched_at: datetime | None) -> str:
    """Render a fetched_at timestamp as ``Ns/Nm/Nh/Nd ago``."""
    if not isinstance(fetched_at, datetime):
        return "unknown"
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - fetched_at
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


# Body keys (in priority order) we try as the human-readable headline.
_HEADLINE_KEYS = ("name", "display_name", "id", "tile_id")

# Body keys we surface as "k=v" extras when present and scalar.
_EXTRA_KEYS = (
    ("map", "map"),
    ("mode", "mode"),
    ("difficulty", "difficulty"),
    ("rank", "rank"),
    ("score", "score"),
    ("type", "type"),
    ("game_type", "game_type"),
)


def _render_fact(row: dict[str, Any]) -> str:
    """Turn one fact row into a single labeled context string.

    URL fields (``creator_url``, ``profile_url``, ``metadata_url``,
    ``map_url``, ``boss_type_url``, ``leaderboard_*_url`` etc.) are
    intentionally NOT included; the parser preserves them in the
    body, but bare links in a context string can encourage the LLM
    to follow them.
    """
    body = row.get("body_json") if isinstance(row.get("body_json"), dict) else {}
    headline = ""
    for key in _HEADLINE_KEYS:
        value = body.get(key)
        if isinstance(value, str) and value and value != "n/a":
            headline = _sanitise(value)
            break
    extras: list[str] = []
    for body_key, label in _EXTRA_KEYS:
        value = body.get(body_key)
        if value is None or isinstance(value, (dict, list)):
            continue
        extras.append(f"{label}={_sanitise(str(value))}")
    parts: list[str] = []
    if headline:
        parts.append(headline)
    if extras:
        parts.append(", ".join(extras))
    summary = " — ".join(parts) if parts else "(no summary)"
    source_name = _sanitise(row.get("source_name") or "data.ninjakiwi.com")
    rel = _relative_time(row.get("fetched_at"))
    version = row.get("version")
    version_label = f", v{version}" if isinstance(version, int) and version > 1 else ""
    full = f"{summary} (source: {source_name}{version_label}, fetched {rel})"
    if len(full) > _FACT_TEXT_CAP:
        full = full[: _FACT_TEXT_CAP - 1] + "…"
    return full


def _intent_to_queries(intent: Any) -> list[Any]:
    """Map a :class:`ResolvedIntent` to grounding queries.

    Each typed entity (tower / hero / map / mode) becomes one
    :class:`BTD6FactQuery` with ``fact_type=None`` so any registered
    fact about the entity surfaces. New entity kinds (events, races,
    bosses) will land here once the resolver recognises them.
    """
    from services.btd6_fact_store import BTD6FactQuery

    queries: list[BTD6FactQuery] = []
    for tower in getattr(intent, "towers", ()):
        if getattr(tower, "id", None):
            queries.append(BTD6FactQuery(None, "btd6_tower", str(tower.id)))
    for hero in getattr(intent, "heroes", ()):
        if getattr(hero, "id", None):
            queries.append(BTD6FactQuery(None, "btd6_hero", str(hero.id)))
    for game_map in getattr(intent, "maps", ()):
        if getattr(game_map, "id", None):
            queries.append(BTD6FactQuery(None, "btd6_map", str(game_map.id)))
    for mode in getattr(intent, "modes", ()):
        if getattr(mode, "id", None):
            queries.append(BTD6FactQuery(None, "btd6_mode", str(mode.id)))
    return queries


async def build(message_text: str) -> BTD6Context:
    """Build a BTD6 context bundle for ``message_text``.

    The flow is: resolver → queries → fact_store.fetch_for_intent →
    sanitised rendering with provenance. The instruction service
    wraps the resulting tuple as untrusted data, so adversarial body
    text reaches the LLM only inside the data envelope.
    """
    facts: list[str] = []
    confidence = 0.0
    source_summary = _FALLBACK_SOURCE_SUMMARY
    try:
        from services import btd6_fact_store, btd6_resolver_service

        intent = btd6_resolver_service.resolve(message_text)
        confidence = float(getattr(intent, "confidence", 0.0) or 0.0)
        queries = _intent_to_queries(intent)
        rows = await btd6_fact_store.fetch_for_intent(queries) if queries else []
        for row in rows:
            facts.append(_render_fact(row))
        if facts:
            source_summary = _DEFAULT_SOURCE_SUMMARY
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.debug("btd6_context_service: grounding unavailable (%s)", exc)
    return BTD6Context(
        facts=tuple(facts),
        source_summary=source_summary,
        confidence=confidence,
    )


__all__ = ["BTD6Context", "build"]
