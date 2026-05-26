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

from typing import Any

import discord

from core.runtime.ai.contracts import AITask

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
    """
    from utils.db import btd6_sources as btd6_db

    rows = await btd6_db.search_facts(limit=50)
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
            lines.append(
                f"`{fact['entity_key']}` · v{fact['version']} · fetched=`{when}`",
            )
        embed.add_field(
            name=f"`{kind}`",
            value="\n".join(lines) or "—",
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


__all__ = [
    "build_grounding_embed",
    "build_hero_embed",
    "build_latest_data_embed",
    "build_pending_review_payload",
    "build_source_health_embed",
    "build_sources_payload",
    "build_strategies_payload",
    "build_why_no_response_payload",
]
