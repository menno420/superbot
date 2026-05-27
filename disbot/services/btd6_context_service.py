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


def _coerce_body(value: Any) -> dict[str, Any]:
    """Normalise ``body_json`` to a dict.

    Legacy ``btd6_facts`` rows were written via a double-encoded
    ``json.dumps`` path (fixed in utils.db.btd6_sources) and so
    round-trip as JSON strings. We decode on read so the grounding
    bundle keeps working for those rows until they're rewritten.
    """
    import json

    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (ValueError, TypeError):
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}


def _render_fact(row: dict[str, Any]) -> str:
    """Turn one fact row into a single labeled context string.

    URL fields (``creator_url``, ``profile_url``, ``metadata_url``,
    ``map_url``, ``boss_type_url``, ``leaderboard_*_url`` etc.) are
    intentionally NOT included; the parser preserves them in the
    body, but bare links in a context string can encourage the LLM
    to follow them.
    """
    body = _coerce_body(row.get("body_json"))
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
    """Map a :class:`ResolvedIntent` to grounding queries (static kinds).

    Each typed entity with a known key (tower / hero / map / mode)
    becomes one :class:`BTD6FactQuery` with ``fact_type=None`` so any
    registered fact about the entity surfaces. PR-E added live
    entities (race / boss / CT / odyssey / challenge / event /
    leaderboard) — those don't have a known key from the resolver
    and are handled by :func:`_fetch_live_entity_rows` instead.
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


async def _fetch_live_entity_rows(
    intent: Any,
    *,
    per_kind_limit: int = 3,
) -> list[dict[str, Any]]:
    """Resolve PR-E live entities into the newest facts per kind.

    The resolver yields ``LiveEntityMatch`` records that only carry
    the parser-produced ``entity_kind``. The fact store's
    ``search_facts`` already returns the newest envelopes per kind,
    ordered by ``fetched_at DESC``. We cap each kind so one chatty
    leaderboard cannot drown out other kinds in the same context.
    """
    matches = getattr(intent, "live_entities", ()) or ()
    if not matches:
        return []
    from utils.db import btd6_sources as btd6_db

    seen_kinds: set[str] = set()
    rows: list[dict[str, Any]] = []
    for match in matches:
        kind = getattr(match, "entity_kind", None)
        if not kind or kind in seen_kinds:
            continue
        seen_kinds.add(kind)
        batch = await btd6_db.search_facts(
            entity_kind=kind,
            limit=per_kind_limit,
        )
        rows.extend(batch)
    return rows


def _render_restriction_for_grounding(entity_name: str, ctx: Any) -> str:
    """Render one tower/hero restriction context as a grounding line.

    Bounded by ``_FACT_TEXT_CAP``; provenance label always present.
    """
    name = _sanitise(entity_name) or "(unknown)"
    event_name = _sanitise(getattr(ctx, "event_name", "")) or "(unknown event)"
    kind = getattr(ctx, "event_kind", "")
    kind_label = {
        "btd6_race": "race",
        "btd6_boss_difficulty": "boss",
        "btd6_odyssey_difficulty": "odyssey",
        "btd6_challenge": "challenge",
    }.get(kind, kind or "event")
    stance = getattr(ctx, "stance", "allowed")
    if getattr(ctx, "sentinel_all_heroes_banned", False):
        body = f"All heroes are banned in {kind_label} '{event_name}'"
    elif stance == "banned":
        body = f"{name} is banned in {kind_label} '{event_name}'"
    elif stance == "limited":
        body = (
            f"{name} is limited (max {ctx.max_count}) in "
            f"{kind_label} '{event_name}'"
        )
    elif stance == "path_blocked":
        body = f"{name} has path tiers blocked in {kind_label} '{event_name}'"
    else:
        return ""
    rel = _relative_time(getattr(ctx, "fetched_at", None))
    full = f"{body} (source: data.ninjakiwi.com, fetched {rel})"
    if len(full) > _FACT_TEXT_CAP:
        full = full[: _FACT_TEXT_CAP - 1] + "…"
    return full


async def _restriction_lines_for_intent(intent: Any) -> list[str]:
    """Pull active-event restriction strings for towers/heroes in ``intent``.

    Returns an empty list when nothing matches; bounded at 8 lines so a
    chatty event can't drown the LLM context window.
    """
    from services import btd6_live_query_service as btd6_live

    out: list[str] = []
    for tower in getattr(intent, "towers", ()) or ():
        if not getattr(tower, "id", None):
            continue
        for ctx in await btd6_live.get_active_event_restrictions_for_tower(
            str(tower.id),
        ):
            line = _render_restriction_for_grounding(
                getattr(tower, "canonical", "") or str(tower.id),
                ctx,
            )
            if line:
                out.append(line)
    for hero in getattr(intent, "heroes", ()) or ():
        if not getattr(hero, "id", None):
            continue
        for ctx in await btd6_live.get_active_event_restrictions_for_hero(
            str(hero.id),
        ):
            line = _render_restriction_for_grounding(
                getattr(hero, "canonical", "") or str(hero.id),
                ctx,
            )
            if line:
                out.append(line)
    return out[:8]


async def build(message_text: str) -> BTD6Context:
    """Build a BTD6 context bundle for ``message_text``.

    The flow is: resolver → queries → fact_store.fetch_for_intent +
    PR-E live entity lookup → tower/hero active-event restrictions →
    sanitised rendering with provenance. The instruction service wraps
    the resulting tuple as untrusted data, so adversarial body text
    reaches the LLM only inside the data envelope.
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
        # PR-E: also surface live-entity facts (race / boss / CT /
        # odyssey / challenge / event / leaderboard).
        live_rows = await _fetch_live_entity_rows(intent)
        rows = rows + live_rows
        for row in rows:
            facts.append(_render_fact(row))
        # PR 2: tower/hero-specific active-event restriction lines.
        facts.extend(await _restriction_lines_for_intent(intent))
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
