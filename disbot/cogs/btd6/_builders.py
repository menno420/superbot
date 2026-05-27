"""Shared builders for BTD6 prefix + slash command parity.

PR-A introduced this module to keep prefix and slash twins reading
from a single response builder rather than reimplementing the embed
formatting twice. Every builder is pure and async-safe; none of
them write to Discord directly. The prefix command sends to
``ctx``; the slash command sends to ``interaction.response`` —
both use the same payload returned here.

Each builder returns either a single ``str`` (for line-list
commands) or a ``discord.Embed`` (for structured commands). When a
command needs to render multiple embeds (e.g. ``pending``) the
builder returns a list of ``(embed, view)`` pairs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord

from core.runtime.ai.contracts import AITask

if TYPE_CHECKING:
    from collections.abc import Sequence

    from services.btd6_ingestion_service import IngestionResult

# ---------------------------------------------------------------------------
# why-no-response
# ---------------------------------------------------------------------------


_RELEVANT_DECISIONS = ("denied", "skipped", "errored", "degraded")


async def build_why_no_response_payload(
    guild_id: int,
    *,
    limit: int = 10,
) -> discord.Embed | str:
    """Return either the audit embed or a fallback string.

    Reads ``ai_decision_audit`` filtered to ``task='btd6.answer'``
    and surfaces the policy-snapshot hash, instruction-profile ids,
    route, and reason code so operators can correlate a denial with
    the policy/profile state that produced it.

    Returns ``str`` when there are no relevant rows.
    """
    from services import ai_decision_audit_service

    safe_limit = max(1, min(50, int(limit)))
    rows = await ai_decision_audit_service.query(guild_id, limit=safe_limit)
    btd6_rows = [
        r
        for r in rows
        if r.get("task") == AITask.BTD6_ANSWER.value
        and r["decision"] in _RELEVANT_DECISIONS
    ]
    if not btd6_rows:
        return "No recent BTD6 denials or skips for this guild."

    embed = discord.Embed(
        title="🐵 BTD6 — why-no-response",
        description=(
            f"Most recent BTD6 denials / skips for this guild "
            f"(showing {min(len(btd6_rows), 10)} of {len(btd6_rows)})."
        ),
        color=discord.Color.gold(),
    )
    for row in btd6_rows[:10]:
        profile_ids = row.get("instruction_profile_ids") or []
        profile_str = ", ".join(str(pid) for pid in profile_ids) or "—"
        embed.add_field(
            name=f"`{row['decision']}` · `{row['reason_code']}`",
            value=(
                f"channel=<#{row['channel_id']}> · user=<@{row['user_id']}>\n"
                f"route=`{row.get('route') or '—'}` · "
                f"provider=`{row.get('provider') or '—'}` · "
                f"model=`{row.get('model') or '—'}`\n"
                f"policy_snapshot=`{row.get('policy_snapshot_hash') or '—'}` · "
                f"profiles=`{profile_str}`"
            ),
            inline=False,
        )
    return embed


# ---------------------------------------------------------------------------
# hero
# ---------------------------------------------------------------------------


async def build_hero_embed(name: str) -> discord.Embed:
    from cogs.btd6._embeds import response_to_embed as _response_to_embed
    from services import btd6_ai_service
    from services.btd6_resolver_service import resolve
    from services.btd6_response_builder import for_hero

    intent = resolve(name)
    if not intent.heroes:
        return _response_to_embed(btd6_ai_service.deterministic_answer(intent))
    return _response_to_embed(for_hero(intent.heroes[0]))


# ---------------------------------------------------------------------------
# sources
# ---------------------------------------------------------------------------


async def build_sources_payload() -> str:
    """Return a one-line-per-source listing (max 25 rows)."""
    from services import btd6_source_registry

    rows = await btd6_source_registry.list_all()
    if not rows:
        return "No BTD6 sources registered yet."
    lines = []
    for row in rows[:25]:
        state = "ON" if row["enabled"] else "off"
        url = row.get("full_url") or row.get("path_template") or "—"
        lines.append(
            f"`{row['source_key']:<26}` tier {row['trust_tier']} · {state} · {url}",
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# strategies
# ---------------------------------------------------------------------------


async def build_strategies_payload(guild_id: int) -> str:
    from services import btd6_strategy_service

    rows = await btd6_strategy_service.list_for_guild(guild_id, limit=10)
    if not rows:
        return "No BTD6 strategies recorded for this guild yet."
    lines = []
    for row in rows:
        tag = "📦 published" if row["visibility"] == "published" else "🛡️ guild"
        lines.append(
            f"{tag} · `{row['approval_status']}` · **{row['title']}** "
            f"— {row['summary'][:80]}",
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# pending
# ---------------------------------------------------------------------------


async def build_pending_review_payload(
    guild_id: int,
    *,
    limit: int = 5,
) -> list[tuple[discord.Embed, Any]] | str:
    """Return a list of ``(embed, view)`` pairs for staff review.

    Returns ``str`` when there is nothing pending.
    """
    from utils.db import btd6_strategies as db
    from views.btd6.strategy_review import (
        StrategyReviewView,
        build_strategy_embed,
    )

    safe_limit = max(1, min(10, int(limit)))
    rows = await db.search_strategies(
        guild_id=guild_id,
        approval_status="draft",
        limit=safe_limit,
    )
    if not rows:
        return "No pending strategies awaiting review for this guild."
    return [(build_strategy_embed(row), StrategyReviewView(row)) for row in rows]


# ---------------------------------------------------------------------------
# source-health builder
# ---------------------------------------------------------------------------


_BUCKET_BADGE = {
    "fresh": "🟢 fresh",
    "aging": "🟡 aging",
    "stale": "🔴 stale",
    "never": "⚪ never",
}


async def build_source_health_embed(
    *,
    limit: int = 25,
) -> discord.Embed:
    """Render the source-health overview (PR-D).

    Bounded by ``limit`` (default 25, hard cap inside the DB layer).
    Freshness buckets are computed in
    :mod:`services.btd6_source_registry`.
    """
    from services import btd6_source_registry

    health = await btd6_source_registry.list_health(limit=limit)
    embed = discord.Embed(
        title="🐵 BTD6 — Source Health",
        description=(
            f"Showing {len(health)} sources. Freshness buckets: "
            "🟢 fresh (≤6h) · 🟡 aging (≤2d) · 🔴 stale (>2d) · "
            "⚪ never fetched."
        ),
        color=discord.Color.gold(),
    )
    if not health:
        embed.description = "No BTD6 sources registered yet."
        return embed
    for src in health:
        state = "ON" if src.enabled else "off"
        when = (
            src.last_fetched_at.isoformat(timespec="minutes")
            if src.last_fetched_at
            else "never"
        )
        embed.add_field(
            name=f"`{src.source_key}` · tier {src.trust_tier}",
            value=(
                f"{_BUCKET_BADGE[src.bucket]} · {state} · "
                f"kind=`{src.source_kind}` · facts={src.fact_count}\n"
                f"last_fetched=`{when}`"
            ),
            inline=False,
        )
    return embed


# ---------------------------------------------------------------------------
# latest-data builder
# ---------------------------------------------------------------------------


async def build_latest_data_embed(*, limit_per_kind: int = 1) -> discord.Embed:
    """Show the newest fact envelope per source_kind.

    Reuses :func:`utils.db.btd6_sources.search_facts` to read the most
    recent rows. Pure read; the model is never invoked.

    Each fact is attributed to its ``source_key`` via a single
    ``btd6_source_registry.list_all()`` call (id→key map built once;
    missing rows render as ``—`` so the embed is robust to stale or
    deleted source rows).
    """
    from services import btd6_source_registry
    from utils.db import btd6_sources as btd6_db

    rows = await btd6_db.search_facts(limit=50)
    source_rows = await btd6_source_registry.list_all()
    id_to_key = {int(s["id"]): s["source_key"] for s in source_rows}

    by_kind: dict[str, list[dict]] = {}
    for row in rows:
        by_kind.setdefault(row["entity_kind"], []).append(row)

    embed = discord.Embed(
        title="🐵 BTD6 — Latest Data",
        description=(
            "Newest fact envelopes per entity_kind. Sourced from "
            "`btd6_facts` with no provider involvement."
        ),
        color=discord.Color.gold(),
    )
    if not by_kind:
        embed.description = "No facts recorded yet."
        return embed
    for kind in sorted(by_kind.keys()):
        latest = by_kind[kind][:limit_per_kind]
        lines = []
        for fact in latest:
            when = (
                fact["fetched_at"].isoformat(timespec="minutes")
                if fact.get("fetched_at")
                else "—"
            )
            source_key = id_to_key.get(int(fact["source_id"]), "—")
            lines.append(
                f"`{fact['entity_key']}` · source=`{source_key}` · "
                f"v{fact['version']} · fetched=`{when}`",
            )
        value = "\n".join(lines) or "—"
        if len(value) > 1024:
            kept: list[str] = []
            running = 0
            suffix_budget = 32
            for line in lines:
                if running + len(line) + 1 > 1024 - suffix_budget:
                    break
                kept.append(line)
                running += len(line) + 1
            dropped = len(lines) - len(kept)
            value = "\n".join(kept) + f"\n… ({dropped} more)"
        embed.add_field(
            name=f"`{kind}`",
            value=value,
            inline=False,
        )
    return embed


# ---------------------------------------------------------------------------
# grounding builder
# ---------------------------------------------------------------------------


async def build_grounding_embed(
    guild_id: int,
    message_id: int,
) -> discord.Embed | str:
    """Show the grounding facts that fed the AI response to a message.

    Reads the matching ``ai_decision_audit`` row plus the latest fact
    envelopes for any entities that appear in the audit row's
    metadata. Pure read — the model is never re-invoked.

    Returns ``str`` when there is no matching audit row.
    """
    from services import ai_decision_audit_service

    rows = await ai_decision_audit_service.query(guild_id, limit=200)
    target = next(
        (r for r in rows if r.get("message_id") == message_id),
        None,
    )
    if target is None:
        return (
            f"No audit row for message_id={message_id}. The bot may "
            "not have processed that message."
        )

    embed = discord.Embed(
        title=f"🐵 BTD6 — Grounding for message {message_id}",
        description=(
            f"Decision: `{target['decision']}` · "
            f"reason: `{target['reason_code']}` · "
            f"task: `{target.get('task') or '—'}`"
        ),
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="Routing",
        value=(
            f"route=`{target.get('route') or '—'}` · "
            f"provider=`{target.get('provider') or '—'}` · "
            f"model=`{target.get('model') or '—'}`"
        ),
        inline=False,
    )
    profile_ids = target.get("instruction_profile_ids") or []
    embed.add_field(
        name="Policy state",
        value=(
            f"policy_snapshot=`{target.get('policy_snapshot_hash') or '—'}` · "
            f"profiles=`{', '.join(str(p) for p in profile_ids) or '—'}`"
        ),
        inline=False,
    )
    return embed


# ---------------------------------------------------------------------------
# refresh-source result builder
# ---------------------------------------------------------------------------


_REFRESH_ERROR_STATUSES = frozenset(
    {"fetch_error", "parse_error", "store_error", "disabled", "interrupted"},
)


def _format_known_keys(keys: Sequence[str], *, max_value_chars: int = 1000) -> str:
    """Join source keys with ` · ` separators, bounded by field-value length.

    Stops before the running length exceeds ``max_value_chars`` (leaving a
    little headroom under Discord's 1024-char field-value cap) and appends
    a ``… (+N more)`` suffix when keys are dropped.
    """
    rendered: list[str] = []
    running = 0
    sep = " · "
    for key in keys:
        chunk = f"`{key}`"
        added = len(chunk) + (len(sep) if rendered else 0)
        if running + added > max_value_chars:
            break
        rendered.append(chunk)
        running += added
    body = sep.join(rendered)
    dropped = len(keys) - len(rendered)
    if dropped > 0:
        body = f"{body}{sep}… (+{dropped} more)" if body else f"… (+{dropped} more)"
    return body or "—"


def build_refresh_source_embed(
    source_key: str,
    results: list[IngestionResult],
    *,
    exception: BaseException | None = None,
    include_exception_detail: bool = False,
    known_source_keys: Sequence[str] | None = None,
) -> discord.Embed:
    """Render the result of a manual ``refresh-source`` invocation.

    Builders stay synchronous; the cog feeds in ``known_source_keys`` only
    when it has already fetched the registry (i.e. on unknown-key results)
    so this function never makes I/O calls.
    """
    if exception is not None:
        color = discord.Color.red()
    elif results and all(r.status == "ok" for r in results):
        color = discord.Color.green()
    elif results and any(r.status in _REFRESH_ERROR_STATUSES for r in results):
        color = discord.Color.red()
    elif results and all(r.status == "skipped" for r in results):
        color = discord.Color.gold()
    else:
        color = discord.Color.gold()

    embed = discord.Embed(
        title=f"🐵 BTD6 — Refresh '{source_key}'",
        color=color,
    )

    if exception is not None:
        if include_exception_detail:
            detail = str(exception)[:900]
            embed.add_field(
                name="Service error",
                value=f"Service raised `{type(exception).__name__}`: {detail}",
                inline=False,
            )
        else:
            embed.add_field(
                name="Service error",
                value=(
                    f"Service raised `{type(exception).__name__}` while "
                    "refreshing this source. Check logs for details."
                ),
                inline=False,
            )
        return embed

    if not results:
        embed.add_field(
            name="No result",
            value="No result returned by the service.",
            inline=False,
        )
        return embed

    multi = len(results) > 1
    for idx, result in enumerate(results):
        prefix = ""
        if multi:
            prefix = "parent · " if idx == 0 else "child · "
        written_preview = ""
        if result.written_entity_keys:
            head = ", ".join(f"`{k}`" for k in result.written_entity_keys[:3])
            extra = len(result.written_entity_keys) - 3
            written_preview = f" ({head}{', …' if extra > 0 else ''})"
        value = (
            f"status=`{result.status}` · facts={result.fact_count} · "
            f"duration={result.duration_ms}ms\n"
            f"run_id=`{result.run_id if result.run_id is not None else '—'}` · "
            f"error=`{result.error_code or '—'}`\n"
            f"written={len(result.written_entity_keys)}{written_preview}"
        )
        embed.add_field(
            name=f"{prefix}`{result.source_key}`",
            value=value,
            inline=False,
        )

    if (
        len(results) == 1
        and results[0].error_code == "source_not_registered"
        and known_source_keys is not None
    ):
        embed.add_field(
            name="Known source keys",
            value=_format_known_keys(known_source_keys),
            inline=False,
        )

    return embed


__all__ = [
    "build_grounding_embed",
    "build_hero_embed",
    "build_latest_data_embed",
    "build_pending_review_payload",
    "build_refresh_source_embed",
    "build_source_health_embed",
    "build_sources_payload",
    "build_strategies_payload",
    "build_why_no_response_payload",
]
