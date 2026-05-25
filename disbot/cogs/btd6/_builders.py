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
    from cogs.btd6_cog import _response_to_embed
    from services import btd6_ai_service
    from services.btd6_resolver_service import resolve
    from services.btd6_response_builder import for_hero, for_unresolved

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
            f"`{row['source_key']:<26}` tier {row['trust_tier']} · "
            f"{state} · {url}",
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


__all__ = [
    "build_hero_embed",
    "build_pending_review_payload",
    "build_sources_payload",
    "build_strategies_payload",
    "build_why_no_response_payload",
]
