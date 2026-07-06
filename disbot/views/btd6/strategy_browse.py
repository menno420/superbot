"""Strategy memory browse / mine / audit embeds (PR-F).

Read-only renderers. All writes still flow through
:mod:`services.btd6_strategy_mutation`; this module never touches
``utils.db.btd6_strategies`` directly.

Renderers:

* :func:`build_browse_embed` — published strategies catalog.
* :func:`build_mine_embed` — caller's own submissions for the guild.
* :func:`build_detail_embed` — single-strategy drill-down with
  provenance labels.
* :func:`build_audit_embed` — per-strategy audit log.
"""

from __future__ import annotations

from typing import Any

import discord

from utils.btd6.context_footer import append_context_footer

_DEFAULT_PAGE_SIZE = 10
_MAX_PAGE_SIZE = 25


def _clamp(limit: int) -> int:
    return max(1, min(int(limit), _MAX_PAGE_SIZE))


def _visibility_badge(row: dict[str, Any]) -> str:
    return "📦 published" if row.get("visibility") == "published" else "🛡️ guild"


def _approval_label(row: dict[str, Any]) -> str:
    status = row.get("approval_status", "draft")
    approved_by = row.get("approved_by")
    if approved_by == "ai":
        return f"`{status}` · approved_by=ai"
    if approved_by == "staff":
        return f"`{status}` · approved_by=staff"
    return f"`{status}`"


def _summarize_row(row: dict[str, Any]) -> str:
    badge = _visibility_badge(row)
    approval = _approval_label(row)
    title = row.get("title") or "(untitled)"
    summary = (row.get("summary") or "").strip()
    if len(summary) > 100:
        summary = summary[:99] + "…"
    return f"{badge} · {approval} · **{title}** — {summary}"


# ---------------------------------------------------------------------------
# Browse (published catalog)
# ---------------------------------------------------------------------------


async def build_browse_embed(*, limit: int = _DEFAULT_PAGE_SIZE) -> discord.Embed:
    from services import btd6_strategy_service

    rows = await btd6_strategy_service.list_published(limit=_clamp(limit))
    embed = discord.Embed(
        title="🐵 BTD6 — Published strategies",
        description=(
            f"Showing {len(rows)} published strategies (max {_MAX_PAGE_SIZE} per page)."
        ),
        color=discord.Color.green(),
    )
    if not rows:
        embed.description = "No published strategies yet."
        return append_context_footer(embed, "btd6_strategy:browse")
    for row in rows:
        embed.add_field(
            name=f"#{row['id']} · {_visibility_badge(row)}",
            value=_summarize_row(row),
            inline=False,
        )
    embed.set_footer(
        text="!btd6 strategy <id> for detail · staff-only commands gate writes.",
    )
    return append_context_footer(embed, "btd6_strategy:browse")


# ---------------------------------------------------------------------------
# Mine (caller's own submissions)
# ---------------------------------------------------------------------------


async def build_mine_embed(
    guild_id: int,
    submitter_id: int,
    *,
    limit: int = _DEFAULT_PAGE_SIZE,
) -> discord.Embed:
    from services import btd6_strategy_service

    rows = await btd6_strategy_service.list_mine(
        guild_id,
        submitter_id,
        limit=_clamp(limit),
    )
    embed = discord.Embed(
        title="🐵 BTD6 — My strategy submissions",
        description=(
            f"Showing {len(rows)} of your submissions in this guild "
            f"(max {_MAX_PAGE_SIZE})."
        ),
        color=discord.Color.green(),
    )
    if not rows:
        embed.description = "You have not submitted any strategies in this guild."
        return append_context_footer(embed, "btd6_strategy:mine")
    for row in rows:
        embed.add_field(
            name=f"#{row['id']} · {_visibility_badge(row)}",
            value=_summarize_row(row),
            inline=False,
        )
    return append_context_footer(embed, "btd6_strategy:mine")


# ---------------------------------------------------------------------------
# Detail (single drill-down)
# ---------------------------------------------------------------------------


async def build_detail_embed(
    strategy_id: int,
    *,
    viewer_guild_id: int | None = None,
) -> discord.Embed | str:
    """Render the detail for one strategy.

    Returns ``str`` when:

    * The strategy does not exist.
    * The strategy is guild-local and the viewer is in a different
      guild (cross-guild leakage prevention).
    """
    from services import btd6_strategy_service

    row = await btd6_strategy_service.get(strategy_id)
    if row is None:
        return f"Strategy #{strategy_id} not found."

    # Cross-guild visibility check: published rows are world-visible;
    # guild rows are visible only to their origin or current guild.
    visibility = row.get("visibility")
    if visibility != "published" and viewer_guild_id is not None:
        origin = row.get("origin_guild_id")
        current = row.get("current_guild_id")
        if viewer_guild_id not in {origin, current}:
            return (
                f"Strategy #{strategy_id} is guild-local; it is not "
                "visible from this guild."
            )

    embed = discord.Embed(
        title=f"🐵 BTD6 — Strategy #{row['id']}: {row.get('title') or '(untitled)'}",
        description=row.get("summary") or "(no summary)",
        color=discord.Color.green(),
    )
    embed.add_field(name="Visibility", value=_visibility_badge(row), inline=True)
    embed.add_field(name="Approval", value=_approval_label(row), inline=True)
    embed.add_field(
        name="Version",
        value=str(row.get("version") or 1),
        inline=True,
    )
    if row.get("map"):
        embed.add_field(name="Map", value=row["map"], inline=True)
    if row.get("mode"):
        embed.add_field(name="Mode", value=row["mode"], inline=True)
    if row.get("difficulty"):
        embed.add_field(name="Difficulty", value=row["difficulty"], inline=True)
    if row.get("hero"):
        embed.add_field(name="Hero", value=row["hero"], inline=True)
    if row.get("towers"):
        towers_str = ", ".join(str(t) for t in row["towers"][:10])
        embed.add_field(name="Towers", value=towers_str, inline=False)
    if row.get("steps"):
        steps_str = "\n".join(f"• {s}" for s in row["steps"][:6])
        embed.add_field(name="Steps", value=steps_str or "—", inline=False)
    embed.set_footer(
        text=(
            f"origin_guild={row.get('origin_guild_id') or '—'} · "
            f"current_guild={row.get('current_guild_id') or '—'} · "
            f"submitted_by={row.get('submitted_by') or '—'}"
        ),
    )
    return append_context_footer(embed, f"btd6_strategy:{row['id']}")


# ---------------------------------------------------------------------------
# Audit log (per-strategy)
# ---------------------------------------------------------------------------


async def build_audit_embed(strategy_id: int) -> discord.Embed:
    from services import btd6_strategy_service

    rows = await btd6_strategy_service.audit_for(strategy_id)
    embed = discord.Embed(
        title=f"🐵 BTD6 — Strategy #{strategy_id} audit",
        description=f"Showing {len(rows)} audit row(s).",
        color=discord.Color.green(),
    )
    if not rows:
        embed.description = f"No audit rows for strategy #{strategy_id}."
        return append_context_footer(embed, f"btd6_strategy:{strategy_id}")
    for r in rows[:_MAX_PAGE_SIZE]:
        when = r.get("created_at")
        when_str = when.isoformat(timespec="minutes") if when else "—"
        embed.add_field(
            name=f"`{r.get('action')}` · {r.get('actor_kind')}",
            value=(f"actor_id=`{r.get('actor_id') or '—'}` · at=`{when_str}`"),
            inline=False,
        )
    return append_context_footer(embed, f"btd6_strategy:{strategy_id}")


__all__ = [
    "build_audit_embed",
    "build_browse_embed",
    "build_detail_embed",
    "build_mine_embed",
]
