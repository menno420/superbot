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
from core.runtime.permission_checks import member_has_perms_or_owner
from utils.btd6.body_coerce import coerce_body as _coerce_body
from utils.btd6.coverage import (
    AREA_BOSS,
    AREA_HERO_STATS,
    AREA_LEADERBOARDS,
    AREA_ODYSSEY,
    get_coverage,
)
from utils.btd6.event_window import format_ms_human as _ms_to_human  # noqa: F401
from utils.btd6.event_window import format_window_range as _format_window_range
from utils.btd6.event_window import format_window_status as _format_window_status

if TYPE_CHECKING:
    from collections.abc import Sequence

    from services.btd6_ingestion_service import IngestionResult
    from services.btd6_ops_readiness_service import ReadinessVerdict


def _event_window(body: dict[str, Any]) -> str:
    """Render ``start_ms`` → ``end_ms`` from a fact body dict.

    Thin wrapper around :func:`utils.btd6.event_window.format_window_range`
    that preserves the legacy ``(body) -> str`` calling convention used by
    the existing embed builders.
    """
    return _format_window_range(body.get("start_ms"), body.get("end_ms"))


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
    # Live event restrictions live in their own drill-down, not on the
    # overview — keep it uncluttered (mirrors the tower-browser decision).
    from cogs.btd6._embeds import response_to_embed as _response_to_embed
    from services import btd6_ai_service
    from services.btd6_resolver_service import resolve
    from services.btd6_response_builder import for_hero
    from utils.btd6.context_footer import append_context_footer

    intent = resolve(name)
    if not intent.heroes:
        return _response_to_embed(btd6_ai_service.deterministic_answer(intent))
    hero = intent.heroes[0]
    embed = _response_to_embed(for_hero(hero))
    embed.add_field(
        name="Coverage",
        value=get_coverage(AREA_HERO_STATS).user_label,
        inline=False,
    )
    return append_context_footer(embed, f"btd6_hero:{hero.id}")


async def build_round_embed(
    number: int,
    end_round: int | None = None,
) -> discord.Embed:
    """Render the round lookup embed: danger / economy + bloon composition.

    A single round (``end_round`` omitted / equal) gets the full detail card; a
    range (``end_round`` given) gets a combined per-round values table via
    :func:`build_round_range_embed`.

    The base economy line (RBE / cash / XP) comes from the round fact; this adds
    the spawn composition and, for freeplay rounds (81+), the effective MOAB-class
    scaled RBE next to the wiki base figure (see ``btd6_data_service.round_rbe``).
    """
    if end_round is not None and end_round != number:
        return await build_round_range_embed(number, end_round)

    from cogs.btd6._embeds import response_to_embed as _response_to_embed
    from services import btd6_data_service
    from services.btd6_knowledge_service import round_fact
    from services.btd6_resolver_service import resolve
    from services.btd6_response_builder import for_round, for_unresolved

    fact = round_fact(number)
    if fact is None:
        return _response_to_embed(for_unresolved(resolve(f"round {number}")))
    embed = _response_to_embed(for_round(fact))

    rbe = btd6_data_service.round_rbe(number)
    if rbe.get("found") and rbe.get("scaled") and rbe.get("effective_rbe") is not None:
        embed.add_field(
            name="Effective RBE (freeplay-scaled)",
            value=(
                f"**{rbe['effective_rbe']:,}** — the round-{number} spawn at scaled "
                f"health (MOAB-class HP ramp + superceramics). Wiki base "
                f"(unscaled): {rbe['base_rbe']:,}."
            ),
            inline=False,
        )
    round_entry = btd6_data_service.get_round(number)
    if round_entry is not None and round_entry.groups:
        total = sum(int(g.get("count", 0)) for g in round_entry.groups)
        embed.add_field(
            name=f"Bloons this round — {total:,} spawned",
            value=_format_composition(round_entry.groups),
            inline=False,
        )
    return embed


async def build_round_range_embed(
    round_start: int,
    round_end: int,
    roundset: str = "default",
) -> discord.Embed:
    """Combined per-round values table (RBE + cash + cumulative) over a range.

    The "round values for a range" view — RBE (freeplay-scaled where it applies,
    via ``round_rbe``) and cash (via ``round_cash``) side by side, so a single
    command answers "what do rounds A-B look like?". Both totals come from the
    full range even when the per-round breakdown is elided.
    """
    from services import btd6_data_service

    lo, hi = (
        (round_start, round_end)
        if round_start <= round_end
        else (round_end, round_start)
    )
    rbe = btd6_data_service.round_rbe(lo, hi, roundset)
    if not rbe.get("found"):
        return discord.Embed(
            title="🐵 BTD6 rounds — no data",
            description=rbe.get("note") or "No round data for that range.",
            color=discord.Color.red(),
        )
    cash = btd6_data_service.round_cash(lo, hi, roundset)
    rbe_by_round = {
        r["round"]: (
            r["effective_rbe"]
            if r.get("effective_rbe") is not None
            else r.get("base_rbe")
        )
        for r in rbe.get("per_round", [])
    }
    cash_by_round = {
        r["round"]: r for r in (cash.get("per_round", []) if cash.get("found") else [])
    }
    rounds = sorted(rbe_by_round)
    shown, elided = _elide(rounds)
    body = []
    for rn in shown:
        rbe_v = rbe_by_round.get(rn)
        crow = cash_by_round.get(rn, {})
        rbe_s = f"{rbe_v:,}" if rbe_v is not None else "—"
        cash_s = f"${crow['cash']:,.0f}" if crow.get("cash") is not None else "—"
        cum_s = (
            f"${crow['cumulative_cash']:,.0f}"
            if crow.get("cumulative_cash") is not None
            else "—"
        )
        body.append(f"{'r' + str(rn):>5} │ {rbe_s:>11} │ {cash_s:>9} │ {cum_s:>11}")
    if elided:
        body.insert(len(body) - 9, f"{'⋮':>5} │ {'⋮':>11} │ {'⋮':>9} │ {'⋮':>11}")
    table = _code_table(
        f"{'round':>5} │ {'RBE':>11} │ {'cash':>9} │ {'cumulative':>11}",
        "──────┼─────────────┼───────────┼─────────────",
        body,
    )
    base_total = rbe.get("base_rbe_total")
    eff_total = rbe.get("effective_rbe_total")
    rbe_total = (
        eff_total if (rbe.get("scaled") and eff_total is not None) else base_total
    )
    head = f"**Rounds {lo}–{hi}** — total RBE **{rbe_total:,}**"
    if cash.get("found") and cash.get("range_cash") is not None:
        head += f", total cash **${cash['range_cash']:,.0f}**"
    embed = discord.Embed(
        title=f"🐵 BTD6 rounds {lo}–{hi}",
        description=f"{head}\n{table}",
        color=discord.Color.blurple(),
    )
    footer = ["Standard/Medium, no income towers"]
    if rbe.get("scaled"):
        footer.append("RBE freeplay-scaled (rounds 81+)")
    if rbe.get("truncated") or (cash.get("found") and cash.get("truncated")):
        footer.append("breakdown truncated; totals are the full range")
    embed.set_footer(text=" · ".join(footer))
    return embed


# ---------------------------------------------------------------------------
# per-round economy: income (cash) / rbe tables + composition
# ---------------------------------------------------------------------------

# Modifier tags shown next to a bloon in the composition list. Plain text (not
# emoji) so it renders identically across clients.
_MOD_TAGS = ("fortified", "regrow", "camo")


def _format_composition(groups: Sequence[dict[str, Any]]) -> str:
    """A compact ``<count>× <Bloon> — <modifiers>`` list from a round's raw spawn
    groups (``{bloon_id, count, modifiers}``), canonical names resolved. Capped at
    25 lines.
    """
    from services import btd6_data_service

    lines = []
    for g in groups[:25]:
        bloon = btd6_data_service.get_bloon(str(g.get("bloon_id")))
        name = bloon.canonical if bloon is not None else str(g.get("bloon_id"))
        mods = [m for m in _MOD_TAGS if m in (g.get("modifiers") or ())]
        suffix = f" — {', '.join(mods)}" if mods else ""
        lines.append(f"`{int(g.get('count', 0)):>5,}×` {name}{suffix}")
    if len(groups) > 25:
        lines.append(f"…and {len(groups) - 25} more groups")
    return "\n".join(lines) or "—"


def _elide(rows: list[Any], head: int = 11, tail: int = 9) -> tuple[list[Any], bool]:
    """Head+tail slice of ``rows`` for a bounded table, plus whether it elided."""
    if len(rows) <= head + tail + 1:
        return rows, False
    return rows[:head] + rows[-tail:], True


def _code_table(header: str, rule: str, body_lines: list[str]) -> str:
    """Wrap a monospace table in a fenced code block."""
    return "```\n" + "\n".join([header, rule, *body_lines]) + "\n```"


async def build_income_embed(
    round_start: int,
    round_end: int | None = None,
    roundset: str = "default",
) -> discord.Embed:
    """Per-round cash for a round or inclusive range — our verified model.

    Mirrors the familiar ``/income`` table but with SuperBot's audited cash
    (``btd6_data_service.round_cash``): Standard/Medium, no income towers. Fails
    closed with the structured reason when the range is unknown.
    """
    from services import btd6_data_service

    res = btd6_data_service.round_cash(round_start, round_end, roundset)
    if not res.get("found"):
        return discord.Embed(
            title="🐵 BTD6 income — no data",
            description=res.get("note") or "No cash data for that round range.",
            color=discord.Color.red(),
        )
    assumptions = res.get("assumptions") or "Standard/Medium, no income towers."

    if res.get("single_round"):
        cumulative = res.get("cumulative_cash")
        cum = f" (cumulative **${cumulative:,.0f}**)" if cumulative is not None else ""
        embed = discord.Embed(
            title=f"🐵 BTD6 income — round {res['round_start']}",
            description=f"Earns **${res['round_cash']:,.1f}**{cum} this round.",
            color=discord.Color.green(),
        )
        embed.set_footer(text=assumptions)
        return embed

    lo, hi = res["round_start"], res["round_end"]
    rows, elided = _elide(res.get("per_round", []))
    body = [
        f"{('r' + str(r['round'])):>5} │ {r['cash']:>9,.1f} │ {r['cumulative_cash']:>11,.0f}"
        for r in rows
    ]
    if elided:
        body.insert(len(body) - 9, f"{'⋮':>5} │ {'⋮':>9} │ {'⋮':>11}")
    table = _code_table(
        f"{'round':>5} │ {'cash':>9} │ {'cumulative':>11}",
        "──────┼───────────┼─────────────",
        body,
    )
    embed = discord.Embed(
        title=f"🐵 BTD6 income — rounds {lo}–{hi}",
        description=(
            f"You earn **${res['range_cash']:,.0f}** across rounds {lo}–{hi} "
            f"({res['rounds_counted']} rounds, both endpoints).\n{table}"
        ),
        color=discord.Color.green(),
    )
    note = assumptions
    if res.get("truncated"):
        note += " · breakdown truncated; total is the full range"
    embed.set_footer(text=note)
    return embed


async def build_rbe_embed(
    round_start: int,
    round_end: int | None = None,
    roundset: str = "default",
) -> discord.Embed:
    """Per-round RBE for a round or inclusive range.

    Shows the wiki **base** RBE and, where the freeplay rules bite (round 81+),
    the **effective** MOAB-class-scaled RBE alongside it
    (``btd6_data_service.round_rbe``). Identical columns collapse to one through
    round 80.
    """
    from services import btd6_data_service

    res = btd6_data_service.round_rbe(round_start, round_end, roundset)
    if not res.get("found"):
        return discord.Embed(
            title="🐵 BTD6 RBE — no data",
            description=res.get("note") or "No RBE data for that round range.",
            color=discord.Color.red(),
        )

    scaled = res.get("scaled")
    scaling_note = (
        "Effective RBE applies freeplay MOAB-class HP scaling + superceramic swap "
        "(our model, verified BAD r100 = 67,200); base is the wiki composition at "
        "base health. Identical through round 80."
    )

    if res.get("single_round"):
        base = res.get("base_rbe")
        eff = res.get("effective_rbe")
        if scaled and eff is not None:
            desc = (
                f"**{eff:,}** effective RBE (freeplay-scaled)\n"
                f"Wiki base (unscaled): **{base:,}**"
            )
        else:
            desc = f"**{base:,}** RBE"
        embed = discord.Embed(
            title=f"🐵 BTD6 RBE — round {res['round']}",
            description=desc,
            color=discord.Color.blue(),
        )
        if scaled:
            embed.set_footer(text=scaling_note)
        return embed

    lo, hi = res["round_start"], res["round_end"]
    rows, elided = _elide(res.get("per_round", []))
    if scaled:
        body = [
            (
                f"{('r' + str(r['round'])):>5} │ {r['base_rbe']:>12,} │ "
                f"{(r['effective_rbe'] if r['effective_rbe'] is not None else '—'):>12,}"
                if r["effective_rbe"] is not None
                else f"{('r' + str(r['round'])):>5} │ {r['base_rbe']:>12,} │ {'—':>12}"
            )
            for r in rows
        ]
        if elided:
            body.insert(len(body) - 9, f"{'⋮':>5} │ {'⋮':>12} │ {'⋮':>12}")
        table = _code_table(
            f"{'round':>5} │ {'base RBE':>12} │ {'effective':>12}",
            "──────┼──────────────┼──────────────",
            body,
        )
        eff_total = res.get("effective_rbe_total")
        totals = f"Totals — base **{res['base_rbe_total']:,}**" + (
            f", effective **{eff_total:,}**" if eff_total is not None else ""
        )
    else:
        body = [f"{('r' + str(r['round'])):>5} │ {r['base_rbe']:>12,}" for r in rows]
        if elided:
            body.insert(len(body) - 9, f"{'⋮':>5} │ {'⋮':>12}")
        table = _code_table(
            f"{'round':>5} │ {'RBE':>12}",
            "──────┼──────────────",
            body,
        )
        totals = f"Total RBE — **{res['base_rbe_total']:,}**"

    embed = discord.Embed(
        title=f"🐵 BTD6 RBE — rounds {lo}–{hi}",
        description=f"{totals} across {res['rounds_counted']} rounds.\n{table}",
        color=discord.Color.blue(),
    )
    if scaled:
        embed.set_footer(text=scaling_note)
    return embed


async def build_tower_embed(name: str) -> discord.Embed:
    """Render the tower lookup embed.

    Live event restrictions are intentionally *not* shown here — they live in
    their own ⚠️ Event-status drill-down (mirrors the tower-browser detail),
    so the overview stays uncluttered.
    """
    from cogs.btd6._embeds import response_to_embed as _response_to_embed
    from services import btd6_ai_service
    from services.btd6_knowledge_service import tower_fact
    from services.btd6_resolver_service import resolve
    from services.btd6_response_builder import for_tower
    from utils.btd6.context_footer import append_context_footer

    intent = resolve(name)
    if not intent.towers:
        return _response_to_embed(btd6_ai_service.deterministic_answer(intent))
    tower = intent.towers[0]
    fact = tower_fact(tower.id)
    if fact is None:
        return _response_to_embed(btd6_ai_service.deterministic_answer(intent))
    embed = _response_to_embed(for_tower(fact))
    return append_context_footer(embed, f"btd6_tower:{tower.id}")


# ---------------------------------------------------------------------------
# estimate (deterministic boss-fight estimator)
# ---------------------------------------------------------------------------


async def build_estimate_embed(query: str) -> discord.Embed:
    """Render the boss-fight estimate embed (deterministic HP/DPS/cost).

    ``<tower> vs <boss> [tier]`` → a single estimate; ``[counters] <boss> [tier]``
    → the most cost-efficient towers. All arithmetic is done deterministically by
    ``services.btd6_estimator_service`` so the surface estimates instead of guessing.
    """
    from services import btd6_estimator_service as est

    title = "🎯 BTD6 boss-fight estimate"
    text = (query or "").strip()
    if not text:
        body = (
            "Estimate a boss fight from grounded HP/DPS/cost:\n"
            "• `<tower> vs <boss> [tier]` — e.g. `super monkey 0-4-0 vs bloonarius t5`\n"
            "• `counters <boss> [tier]` — the most cost-efficient towers"
        )
        return discord.Embed(
            title=title,
            description=body,
            color=discord.Color.blurple(),
        )

    req = est.parse_request(text)
    if req.mode == "single":
        estimate = est.resolve_and_estimate(
            req.tower_query,
            req.boss_query,
            req.tier,
            req.map_query,
        )
        if estimate is not None:
            body = est.format_estimate_text(estimate)
        else:
            body = (
                "I couldn't resolve that — try `<tower> vs <boss> [tier]`. "
                f"(Read tower=`{req.tower_query}`, boss=`{req.boss_query}`, tier {req.tier}.)"
            )
    else:
        boss = est.find_boss(req.boss_query)
        if boss is None:
            body = (
                f"I don't have a boss matching `{req.boss_query}`. "
                "Bosses: Bloonarius, Lych, Vortex, Dreadbloon, Blastapopoulos, Phayze, Diamondback."
            )
        else:
            rows = est.cheapest_counters(boss.id, req.tier, limit=5)
            body = est.format_counters_text(rows, boss.canonical or boss.id, req.tier)
    return discord.Embed(title=title, description=body, color=discord.Color.blurple())


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


async def build_source_health_embed(
    *,
    limit: int = 25,
) -> discord.Embed:
    """Render the source-health overview (PR-D).

    Bounded by ``limit`` (default 25, hard cap inside the DB layer).
    Freshness buckets are computed in
    :mod:`services.btd6_source_registry`.
    """
    from cogs.btd6._freshness_render import BUCKET_BADGE
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
    from utils.btd6.context_footer import append_context_footer

    if not health:
        embed.description = "No BTD6 sources registered yet."
        return append_context_footer(embed, "btd6_diagnostics:sources")
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
                f"{BUCKET_BADGE[src.bucket]} · {state} · "
                f"kind=`{src.source_kind}` · facts={src.fact_count}\n"
                f"last_fetched=`{when}`"
            ),
            inline=False,
        )
    return append_context_footer(embed, "btd6_diagnostics:sources")


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
        from utils.btd6.context_footer import append_context_footer

        return append_context_footer(embed, "btd6_diagnostics:latest_data")
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
    from utils.btd6.context_footer import append_context_footer

    return append_context_footer(embed, "btd6_diagnostics:latest_data")


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
# live-event builders (race / boss / ct / odyssey / event)
# ---------------------------------------------------------------------------


_LIVE_EVENT_SPECS: dict[str, dict[str, str]] = {
    # entity_kind → display config
    "btd6_race": {
        "title": "🐵 BTD6 — Races",
        "noun": "race",
        "source_key": "nk_btd6_races",
    },
    "btd6_boss": {
        "title": "🐵 BTD6 — Bosses",
        "noun": "boss event",
        "source_key": "nk_btd6_bosses",
    },
    "btd6_ct": {
        "title": "🐵 BTD6 — Contested Territory",
        "noun": "CT event",
        "source_key": "nk_btd6_ct",
    },
    "btd6_odyssey": {
        "title": "🐵 BTD6 — Odysseys",
        "noun": "odyssey",
        "source_key": "nk_btd6_odyssey",
    },
    "btd6_event": {
        "title": "🐵 BTD6 — Events",
        "noun": "event",
        "source_key": "nk_btd6_events",
    },
}


async def build_live_events_embed(
    entity_kind: str,
    *,
    limit: int = 5,
) -> discord.Embed:
    """Render the most-recent live events for an entity_kind.

    Accepts either the full ``btd6_<kind>`` form or the short ``<kind>``
    form (race / boss / ct / odyssey / event). Unknown kinds yield a
    user-facing error embed rather than raising — surfaces just pass
    user input straight through.
    """
    if not entity_kind.startswith("btd6_"):
        entity_kind = f"btd6_{entity_kind}"
    spec = _LIVE_EVENT_SPECS.get(entity_kind)
    if spec is None:
        return discord.Embed(
            title="🐵 BTD6 — Unknown kind",
            description=(
                f"`{entity_kind}` isn't a known live-event kind. Try one of: "
                "`race`, `boss`, `ct`, `odyssey`, `event`."
            ),
            color=discord.Color.red(),
        )

    from utils.db import btd6_sources as btd6_db

    rows = await btd6_db.search_facts(entity_kind=entity_kind, limit=limit)
    embed = discord.Embed(
        title=spec["title"],
        description=(
            f"Most recent {spec['noun']} envelopes from `btd6_facts` "
            f"(source `{spec['source_key']}`). No provider involvement."
        ),
        color=discord.Color.gold(),
    )
    from utils.btd6.context_footer import append_context_footer

    short_kind = entity_kind.removeprefix("btd6_") or "event"
    context_id = f"btd6_{short_kind}:list"

    if not rows:
        embed.description = (
            f"No {spec['noun']} facts recorded yet. Try "
            f"`!btd6 refresh-source {spec['source_key']}` to fetch live data."
        )
        return append_context_footer(embed, context_id)

    for row in rows:
        body = _coerce_body(row.get("body_json"))
        name = body.get("name") or row.get("entity_key") or "—"
        window = _event_window(body)
        lines = [
            f"id=`{row['entity_key']}`",
            f"window: {window}",
        ]
        score_fragments = []
        if isinstance(body.get("total_scores"), int):
            score_fragments.append(f"scores={body['total_scores']}")
        for key, label in (
            ("total_scores_standard", "standard"),
            ("total_scores_elite", "elite"),
        ):
            value = body.get(key)
            if isinstance(value, int):
                score_fragments.append(f"{label}={value}")
        if isinstance(body.get("boss_type"), str) and body["boss_type"]:
            score_fragments.append(f"type=`{body['boss_type']}`")
        if score_fragments:
            lines.append(" · ".join(score_fragments))
        when = (
            row["fetched_at"].isoformat(timespec="minutes")
            if row.get("fetched_at")
            else "—"
        )
        lines.append(f"fetched=`{when}` · v{row['version']}")
        embed.add_field(
            name=str(name)[:256],
            value="\n".join(lines),
            inline=False,
        )
    return append_context_footer(embed, context_id)


# ---------------------------------------------------------------------------
# Contested Territory — relic detail + browser
# ---------------------------------------------------------------------------


def _relic_display_name(relic: Any) -> str:
    abbrev = getattr(relic, "abbrev", "") or ""
    canonical = getattr(relic, "canonical", "") or getattr(relic, "id", "")
    return f"{canonical} ({abbrev})" if abbrev else str(canonical)


async def build_ct_relic_embed(name: str) -> discord.Embed:
    """Relic effect + where it currently sits across active CT events.

    ``name`` is matched against the relic catalog (canonical / abbrev /
    alias / API name). Unknown relics yield a friendly error embed.
    """
    from services import btd6_data_service
    from utils.btd6.context_footer import append_context_footer

    relic = btd6_data_service.resolve_relic(name)
    if relic is None:
        names = ", ".join(
            sorted(r.canonical for r in btd6_data_service.list_ct_relics())[:8],
        )
        return discord.Embed(
            title="🗺️ BTD6 CT — Unknown relic",
            description=(
                f"`{name}` isn't a relic I know. Examples: {names}…"
                if names
                else f"`{name}` isn't a relic I know."
            ),
            color=discord.Color.red(),
        )

    embed = discord.Embed(
        title=f"🗺️ CT Relic — {_relic_display_name(relic)}",
        description=relic.effect,
        color=discord.Color.teal(),
    )
    embed.add_field(name="Category", value=relic.category, inline=True)

    from services import btd6_live_query_service as btd6_live

    placements = await btd6_live.find_relic_locations(relic.id)
    if placements:
        lines = []
        for placement in placements[:10]:
            pos = (
                placement.position.describe() if placement.position else "position n/a"
            )
            lines.append(
                f"`{placement.tile_id}` — {pos} (CT `{placement.ct_id}`)",
            )
        embed.add_field(
            name=f"On the map now ({len(placements)} tile(s))",
            value="\n".join(lines)[:1024],
            inline=False,
        )
    else:
        embed.add_field(
            name="On the map now",
            value="No active CT tile currently carries this relic (or live data isn't loaded).",
            inline=False,
        )
    embed.set_footer(text="Source: bloonswiki + data.ninjakiwi.com")
    return append_context_footer(embed, f"btd6_ct_relic:{relic.id}")


async def build_ct_browser_embed() -> discord.Embed:
    """List active Contested Territory events with their relic-tile counts."""
    from services import btd6_live_query_service as btd6_live
    from utils.btd6.context_footer import append_context_footer

    events = await btd6_live.get_active_events(("btd6_ct",))
    embed = discord.Embed(
        title="🗺️ BTD6 — Contested Territory",
        color=discord.Color.gold(),
    )
    if not events:
        embed.description = (
            "No active CT events recorded. Try "
            "`!btd6 refresh-source nk_btd6_ct` to fetch live data."
        )
        return append_context_footer(embed, "btd6_ct:browser")

    embed.description = (
        "Active CT events. Use `!btd6 relic <name>` for a relic's effect "
        "and current tile, or `!btd6 event ct <id>` for one event."
    )
    for evt in events[:8]:
        tiles = await btd6_live.get_ct_tiles(evt.entity_key, relics_only=True)
        relic_names = sorted({t.relic_canonical or t.relic_name or "?" for t in tiles})
        value = (
            f"id=`{evt.entity_key}`\n{len(tiles)} relic tile(s): "
            f"{', '.join(relic_names)[:600]}"
            if tiles
            else f"id=`{evt.entity_key}`\nno relic tiles loaded"
        )
        embed.add_field(name=str(evt.name)[:256], value=value, inline=False)
    return append_context_footer(embed, "btd6_ct:browser")


def _ct_team_notice(message: str) -> discord.Embed:
    return discord.Embed(
        title="🛡️ BTD6 — Your CT Team",
        description=message,
        color=discord.Color.gold(),
    )


async def handle_ctteam(
    ctx: Any,
    arg: str,
) -> tuple[discord.Embed, discord.ui.View | None]:
    """Drive the ``!btd6 ctteam`` command: view / guided set / clear.

    Returns ``(embed, view)`` so the cog stays a one-line delegate.
    Setting goes through the **guided flow** (Settings Phase 2, Q-0064):
    a pasted URL/id is parsed and previewed with a Confirm/Cancel step —
    never written immediately. ``clear`` stays immediate (reversible,
    nothing to preview). An empty ``arg`` shows the current team's live
    standing, plus a "Set CT team…" button for Manage Server holders.
    """
    from services import btd6_ct_team_service
    from views.btd6.ct_group_flow import (
        CTGroupConfirmView,
        CTGroupEntryView,
        build_ct_preview_embed,
    )

    guild = getattr(ctx, "guild", None)
    if guild is None:
        return _ct_team_notice("Use this in a server, not a DM."), None
    guild_id = guild.id
    action = (arg or "").strip()
    author = getattr(ctx, "author", None)
    can_manage = member_has_perms_or_owner(author, manage_guild=True)
    if action:
        if not can_manage:
            return (
                _ct_team_notice(
                    "You need the Manage Server permission to change the CT team.",
                ),
                None,
            )
        if action.lower() == "clear":
            await btd6_ct_team_service.clear_team_group_id(guild_id)
            return _ct_team_notice("Cleared this server's CT team."), None
        group_id = btd6_ct_team_service.parse_group_id(action)
        if group_id is None:
            return (
                _ct_team_notice(
                    "That doesn't look like a CT bracket id or group URL. Paste "
                    "your team's `…/leaderboard/group/<id>` link or the bare id.",
                ),
                None,
            )
        # Guided flow: parse → preview → confirm. The commit happens in the
        # Confirm callback (which re-checks Manage Server), not here.
        preview = await build_ct_preview_embed(guild_id, group_id)
        return preview, CTGroupConfirmView(author, group_id)

    embed = await build_ct_team_embed(guild_id)
    view = CTGroupEntryView(author) if can_manage else None
    return embed, view


async def build_ct_team_embed(guild_id: int) -> discord.Embed:
    """Show this server's configured CT team and its live bracket standing."""
    from services import btd6_ct_team_service
    from utils.btd6.context_footer import append_context_footer

    embed = discord.Embed(title="🛡️ BTD6 — Your CT Team", color=discord.Color.gold())
    group_id = await btd6_ct_team_service.get_team_group_id(guild_id)
    if not group_id:
        embed.description = (
            "No CT team is set for this server.\n"
            "An admin can set one with `!btd6 ctteam <bracket id or group URL>` — "
            "copy your team's `…/leaderboard/group/<id>` link from the CT team "
            "leaderboard."
        )
        return append_context_footer(embed, "btd6_ct:team")

    embed.description = f"Configured bracket id: `{group_id}`"
    result = await btd6_ct_team_service.get_ct_bracket(group_id)
    if result.ct_id is None:
        embed.add_field(
            name="Status",
            value="No Contested Territory event is active right now.",
            inline=False,
        )
        return append_context_footer(embed, "btd6_ct:team")
    if result.stale:
        embed.add_field(
            name="⚠️ Stale bracket id",
            value=(
                "This id returned no teams for the current CT event. Ninja Kiwi "
                "rotates bracket ids each event — re-paste this week's with "
                "`!btd6 ctteam <id or URL>`."
            ),
            inline=False,
        )
        return append_context_footer(embed, "btd6_ct:team")
    lines = [
        f"`#{row.rank}` **{discord.utils.escape_markdown(row.display_name)}** — "
        f"{row.score:,}"
        for row in result.rows
    ]
    embed.add_field(
        name=f"Bracket standings (CT {result.ct_id})",
        value="\n".join(lines)[:1024] or "no teams",
        inline=False,
    )
    return append_context_footer(embed, "btd6_ct:team")


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

    # Aggregate summary first — gives the operator the big picture
    # before any per-result drill-down. Always emit this so chain
    # refreshes are scannable at a glance.
    if len(results) > 1:
        status_counts: dict[str, int] = {}
        total_facts = 0
        for result in results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
            total_facts += result.fact_count
        counts_str = " · ".join(
            f"{count} {status}" for status, count in sorted(status_counts.items())
        )
        summary_value = (
            f"{len(results)} runs · {total_facts} facts written\n{counts_str}"
        )
        embed.add_field(name="Summary", value=summary_value, inline=False)

    # Discord caps embeds at 25 fields. Reserve room for the summary
    # field above (1) plus any trailing "remaining" / "Known source
    # keys" field (up to 1), so render at most 20 per-result fields.
    # Chain refreshes for nk_btd6_maps / nk_btd6_challenges currently
    # produce up to 34 results — without this cap, .add_field exceeds
    # the 25-field limit and Discord rejects the message with 400.
    max_per_result_fields = 20
    rendered_results = results[:max_per_result_fields]

    multi = len(results) > 1
    for idx, result in enumerate(rendered_results):
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

    truncated = len(results) - len(rendered_results)
    if truncated > 0:
        embed.add_field(
            name="…",
            value=(
                f"+{truncated} more child runs omitted to stay within "
                f"Discord's 25-field embed limit. Run "
                f"`!btd6 source-health` for the full per-source picture."
            ),
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


# ---------------------------------------------------------------------------
# event-detail builder
# ---------------------------------------------------------------------------


_EVENT_KIND_TITLE = {
    "btd6_race": "🏁 BTD6 Race",
    "btd6_boss": "👑 BTD6 Boss",
    "btd6_ct": "🗺️ BTD6 Contested Territory",
    "btd6_odyssey": "🌊 BTD6 Odyssey",
    "btd6_event": "🎪 BTD6 Event",
}


# Event kinds whose ingestion is intentionally partial; surfaced as a
# "Coverage" field so users/staff see the same limitation the registry
# encodes (boss = standard/teamSize 1, odyssey = easy only).
_EVENT_COVERAGE_AREA = {
    "btd6_boss": AREA_BOSS,
    "btd6_odyssey": AREA_ODYSSEY,
}


def build_event_detail_embed(
    entity_kind: str,
    entity_key: str,
    row: dict[str, Any] | None,
    *,
    metadata_row: dict[str, Any] | None = None,
) -> discord.Embed:
    """Render one specific BTD6 event from ``btd6_facts``.

    ``row`` is the index-fact (carries name + window + scores);
    ``metadata_row`` is the deeper ``*_metadata`` fact that carries
    ``_towers`` restrictions and mode flags. Either may be ``None``;
    the embed degrades gracefully.

    Builders stay synchronous — the cog does both async fetches before
    calling this function.
    """
    title = f"{_EVENT_KIND_TITLE.get(entity_kind, entity_kind)} — {entity_key}"

    if row is None and metadata_row is None:
        return discord.Embed(
            title=title,
            description=(
                f"No event found for kind=`{entity_kind}` id=`{entity_key}`. "
                f"Try `!btd6 live {entity_kind.removeprefix('btd6_')}` to "
                "list active events of this kind."
            ),
            color=discord.Color.red(),
        )

    primary = row if row is not None else metadata_row
    primary_body = _coerce_body((primary or {}).get("body_json"))

    name = primary_body.get("name") or entity_key
    embed = discord.Embed(
        title=f"{_EVENT_KIND_TITLE.get(entity_kind, entity_kind)} — {name}",
        color=discord.Color.gold(),
    )

    # Window / status from start_ms+end_ms (in either row or metadata).
    window_body = primary_body
    if not window_body.get("start_ms") and metadata_row is not None:
        window_body = _coerce_body(metadata_row.get("body_json"))
    embed.add_field(
        name="Window",
        value=_format_window_status(window_body),
        inline=False,
    )

    # Score fragments from the index row.
    score_fragments = []
    if isinstance(primary_body.get("total_scores"), int):
        score_fragments.append(f"scores={primary_body['total_scores']}")
    for key, label in (
        ("total_scores_standard", "standard"),
        ("total_scores_elite", "elite"),
    ):
        v = primary_body.get(key)
        if isinstance(v, int):
            score_fragments.append(f"{label}={v}")
    if isinstance(primary_body.get("boss_type"), str) and primary_body["boss_type"]:
        score_fragments.append(f"type=`{primary_body['boss_type']}`")
    if score_fragments:
        embed.add_field(name="Scores", value=" · ".join(score_fragments), inline=False)

    # Mode flags + round/lives from metadata (when present).
    if metadata_row is not None:
        md = _coerce_body(metadata_row.get("body_json"))
        rules_parts = []
        if isinstance(md.get("startRound"), int) and isinstance(
            md.get("endRound"),
            int,
        ):
            rules_parts.append(f"rounds {md['startRound']}–{md['endRound']}")
        if isinstance(md.get("lives"), int):
            rules_parts.append(f"lives {md['lives']}")
        if isinstance(md.get("maxLives"), int):
            rules_parts.append(f"max lives {md['maxLives']}")
        if isinstance(md.get("maxTowers"), int):
            rules_parts.append(f"max towers {md['maxTowers']}")
        if isinstance(md.get("maxParagons"), int):
            rules_parts.append(f"max paragons {md['maxParagons']}")
        if isinstance(md.get("difficulty"), str) and md["difficulty"]:
            rules_parts.append(f"difficulty `{md['difficulty']}`")
        if rules_parts:
            embed.add_field(name="Rules", value=" · ".join(rules_parts), inline=False)

        disabled_flags = []
        for k, label in (
            ("disableDoubleCash", "double cash"),
            ("disableInstas", "instas"),
            ("disableMK", "MK"),
            ("disablePowers", "powers"),
            ("disableSelling", "selling"),
        ):
            if md.get(k):
                disabled_flags.append(label)
        if disabled_flags:
            embed.add_field(
                name="Disabled",
                value=", ".join(disabled_flags),
                inline=False,
            )

        # Tower restrictions decoded from _towers.
        towers = md.get("_towers")
        if isinstance(towers, list) and towers:
            from utils.btd6.tower_restrictions import render_tower_restrictions

            restrictions = render_tower_restrictions(towers)
            for category, label in (
                ("banned", "🚫 Banned towers"),
                ("limited", "⚠️ Limited towers"),
                ("path_blocked", "🪜 Path-blocked"),
                ("heroes_banned", "🧙 Heroes banned"),
            ):
                entries = restrictions.get(category)
                if not entries:
                    continue
                value = ", ".join(entries)
                if len(value) > 1024:
                    # Truncate to fit the 1024-char field-value cap.
                    cut: list[str] = []
                    running = 0
                    for entry in entries:
                        sep = ", " if cut else ""
                        chunk = sep + entry
                        if running + len(chunk) > 990:
                            break
                        cut.append(entry)
                        running += len(chunk)
                    dropped = len(entries) - len(cut)
                    value = ", ".join(cut) + f"… (+{dropped} more)"
                embed.add_field(name=label, value=value, inline=False)

    coverage_area = _EVENT_COVERAGE_AREA.get(entity_kind)
    if coverage_area is not None:
        embed.add_field(
            name="Coverage",
            value=get_coverage(coverage_area).user_label,
            inline=False,
        )

    when = primary.get("fetched_at") if primary else None
    if when is not None:
        embed.set_footer(text=f"fetched={when.isoformat(timespec='minutes')}")
    from utils.btd6.context_footer import append_context_footer

    short_kind = entity_kind.removeprefix("btd6_") or "event"
    return append_context_footer(embed, f"btd6_{short_kind}:{entity_key}")


# ---------------------------------------------------------------------------
# admin Fetch-All / Fetch-Selected summary
# ---------------------------------------------------------------------------


def build_admin_refresh_summary_embed(
    results_by_source: list[tuple[str, list[Any]]],
    *,
    title_suffix: str = "",
) -> discord.Embed:
    """Aggregate multi-chain refresh results into one embed.

    ``results_by_source`` is a list of ``(source_key, [IngestionResult])``
    pairs — one entry per top-level chain executed. The embed summarises
    per-status counts and total facts written, then renders one line per
    chain so operators can see which ones succeeded / failed.
    """
    total_runs = 0
    total_facts = 0
    status_counts: dict[str, int] = {}
    chain_lines: list[str] = []

    for source_key, results in results_by_source:
        chain_status = "ok"
        chain_facts = 0
        chain_errors: list[str] = []
        for r in results:
            total_runs += 1
            total_facts += r.fact_count
            chain_facts += r.fact_count
            status_counts[r.status] = status_counts.get(r.status, 0) + 1
            if r.status in _REFRESH_ERROR_STATUSES:
                chain_status = "fail"
                if r.error_code:
                    # Surface error_message when present (e.g. the
                    # EnvelopeError detail from a parser) so operators
                    # don't have to grep the DB to know why
                    # parse_exception fired. Truncated to keep the
                    # field-value cap honoured.
                    detail = f"{r.source_key}={r.error_code}"
                    if r.error_message:
                        msg = r.error_message[:120]
                        detail += f" ({msg})"
                    chain_errors.append(detail)
        emoji = "✅" if chain_status == "ok" else "⚠️"
        line = f"{emoji} `{source_key}` · {chain_facts} facts · {len(results)} runs"
        if chain_errors:
            line += f"\n   errors: {', '.join(chain_errors[:3])}"
            if len(chain_errors) > 3:
                line += f" (+{len(chain_errors) - 3} more)"
        chain_lines.append(line)

    color = (
        discord.Color.green()
        if all(s == "ok" for s in status_counts)
        else discord.Color.gold() if status_counts.get("ok", 0) else discord.Color.red()
    )
    embed = discord.Embed(
        title=f"🛠️ BTD6 Admin — Refresh Summary{title_suffix}",
        color=color,
    )
    counts_str = " · ".join(f"{n} {s}" for s, n in sorted(status_counts.items()))
    embed.add_field(
        name="Aggregate",
        value=(
            f"{len(results_by_source)} chains · {total_runs} runs · "
            f"{total_facts} facts written\n{counts_str}"
        ),
        inline=False,
    )
    body = "\n".join(chain_lines)
    # Discord field-value cap.
    if len(body) > 1024:
        keep: list[str] = []
        running = 0
        for line in chain_lines:
            if running + len(line) + 1 > 990:
                break
            keep.append(line)
            running += len(line) + 1
        dropped = len(chain_lines) - len(keep)
        body = "\n".join(keep) + f"\n… (+{dropped} more chains omitted)"
    embed.add_field(name="Chains", value=body or "—", inline=False)
    return embed


# ---------------------------------------------------------------------------
# leaderboard builder
# ---------------------------------------------------------------------------


async def build_leaderboard_embed(
    kind: str,
    event_id: str | None,
    *,
    limit: int = 10,
) -> discord.Embed:
    """Render the top-N leaderboard for one race or boss event.

    ``event_id=None`` resolves to the newest active event of that kind
    via the facade's newest-active helpers. Boss leaderboards default
    to standard solo (the only combo the supervisor currently fetches).
    Empty leaderboard hints at the parent-chain refresh source, not
    the child source (children require path params).
    """
    from cogs.btd6._freshness_render import BUCKET_BADGE
    from services import btd6_live_query_service as btd6_live
    from services.btd6_source_registry import bucket_freshness

    norm = (kind or "").strip().lower()
    if norm not in {"race", "boss"}:
        return discord.Embed(
            title="🐵 BTD6 — Leaderboard",
            description=(f"Unknown kind `{kind!r}` — use `race` or `boss`."),
            color=discord.Color.red(),
        )

    refresh_source = "nk_btd6_races" if norm == "race" else "nk_btd6_bosses"
    resolved_id = event_id
    event_name: str | None = None
    if not resolved_id:
        active = (
            await btd6_live.get_newest_active_race()
            if norm == "race"
            else await btd6_live.get_newest_active_boss()
        )
        if active is None:
            return discord.Embed(
                title=f"🐵 BTD6 — {norm.title()} leaderboard",
                description=(
                    f"No active {norm} found. Try `!btd6 refresh-source "
                    f"{refresh_source}` to fetch live data."
                ),
                color=discord.Color.gold(),
            )
        resolved_id = active.entity_key
        event_name = active.name

    if norm == "race":
        rows = await btd6_live.get_race_leaderboard(resolved_id, limit=limit)
        title_suffix = "Race"
        footer_hint = ""
    else:
        rows = await btd6_live.get_boss_leaderboard(resolved_id, limit=limit)
        title_suffix = "Boss"
        footer_hint = (
            "Showing standard solo leaderboard. "
            "Elite / team modes are not yet ingested."
        )

    label = event_name or resolved_id
    embed = discord.Embed(
        title=f"🐵 BTD6 — {title_suffix} leaderboard — {label}",
        color=discord.Color.gold(),
    )
    if not rows:
        embed.description = (
            f"No leaderboard rows stored for `{resolved_id}` yet. "
            f"Try `!btd6 refresh-source {refresh_source}`."
        )
        embed.set_footer(text=footer_hint or "No rows.")
        return embed

    lines: list[str] = []
    latest_fetched = None
    for row in rows:
        score_render = ""
        if row.score is not None:
            score_render = f"score=`{row.score}`"
        elif row.score_parts:
            score_render = "score=" + "/".join(str(p) for p in row.score_parts)
        lines.append(
            f"#{row.rank} **{row.display_name or '—'}** · {score_render}".rstrip(" ·"),
        )
        # Track latest fetched_at for freshness — the facade strips
        # fetched_at off the LeaderboardRow shape, but rows are sorted
        # by rank so we'd need a separate query for that. Skip per-row
        # freshness for MVP; surface the freshness of the newest active
        # event we resolved instead via the embed footer below.

    embed.description = "\n".join(lines)

    # Freshness label via the canonical helper. We use the active-event
    # fetched_at as a proxy for "how stale is this view" — it's the same
    # signal the panel's "Currently active" block uses.
    if event_id is None:
        active_for_freshness = (
            await btd6_live.get_newest_active_race()
            if norm == "race"
            else await btd6_live.get_newest_active_boss()
        )
        if active_for_freshness is not None:
            latest_fetched = active_for_freshness.fetched_at
    parts: list[str] = []
    if footer_hint:
        parts.append(footer_hint)
    parts.append(get_coverage(AREA_LEADERBOARDS).user_label)
    if latest_fetched is not None:
        bucket = bucket_freshness(latest_fetched)
        if bucket in ("aging", "stale"):
            parts.append(f"Data: {BUCKET_BADGE[bucket]}")
    if parts:
        embed.set_footer(text=" · ".join(parts))
    from utils.btd6.context_footer import append_context_footer

    return append_context_footer(embed, f"btd6_leaderboard:{norm}_{resolved_id}")


# ---------------------------------------------------------------------------
# Operator readiness + ingestion runs (PR2)
# ---------------------------------------------------------------------------


def _yn(value: bool) -> str:
    return "✅ yes" if value else "❌ no"


_READINESS_PRESENTATION: dict[str, tuple[str, discord.Color]] = {
    "ready": ("🟢 ready", discord.Color.green()),
    "partial": ("🟡 partial", discord.Color.gold()),
    "not_ready": ("🔴 not ready", discord.Color.red()),
    "disabled": ("🚫 disabled", discord.Color.greyple()),
}

_RUN_STATUS_EMOJI = {
    "success": "🟢",
    "running": "🔵",
    "fetch_error": "🔴",
    "parse_error": "🟠",
    "store_error": "🔴",
    "interrupted": "⚪",
}


def build_readiness_embed(verdict: ReadinessVerdict) -> discord.Embed:
    """Render an operator readiness verdict.

    Pure: the cog calls ``btd6_ops_readiness_service.evaluate()`` and passes
    the verdict here. The ``"disabled"`` (env-off) status renders as its own
    distinct line, never as a generic "not ready".
    """
    title, color = _READINESS_PRESENTATION.get(
        verdict.status,
        (verdict.status, discord.Color.greyple()),
    )
    embed = discord.Embed(title=f"🐵 BTD6 ingestion readiness — {title}", color=color)

    if verdict.status == "disabled":
        embed.description = (
            "Ingestion is **switched off** (`BTD6_INGESTION_ENABLED` is not "
            "`true`). No scheduled fetches run; the sources below are "
            "configured but dormant."
        )

    embed.add_field(
        name="Ingestion",
        value=(
            f"env enabled: {_yn(verdict.ingestion_enabled)}\n"
            f"supervisor running: {_yn(verdict.supervisor_running)}"
        ),
        inline=True,
    )
    embed.add_field(
        name="Sources",
        value=(
            f"total: {verdict.sources_total}\n"
            f"enabled: {verdict.sources_enabled}\n"
            f"disabled: {verdict.sources_disabled}\n"
            f"enabled w/o base_url: {verdict.enabled_missing_base_url}"
        ),
        inline=True,
    )
    embed.add_field(
        name="Freshness (enabled)",
        value=(
            f"🟢 fresh: {verdict.fresh}\n"
            f"🟡 aging: {verdict.aging}\n"
            f"🔴 stale: {verdict.stale}\n"
            f"⚪ never: {verdict.never}"
        ),
        inline=True,
    )

    breakers = ", ".join(verdict.open_breakers) if verdict.open_breakers else "none"
    embed.add_field(name="Open circuit breakers", value=breakers, inline=False)

    last_run = (
        verdict.last_run_at.isoformat(timespec="minutes")
        if verdict.last_run_at is not None
        else "—"
    )
    embed.add_field(
        name="Recent runs",
        value=(
            f"scanned: {verdict.recent_runs_total}\n"
            f"failures: {verdict.recent_failures}\n"
            f"last run: {last_run}"
        ),
        inline=False,
    )
    return embed


def build_ingestion_runs_embed(
    runs: list[dict[str, Any]],
    *,
    source_key: str | None = None,
) -> discord.Embed:
    """Render the most-recent ingestion runs as a compact list.

    ``runs`` comes from ``utils.db.btd6_sources.list_ingestion_runs`` (newest
    first). Pure formatter — no I/O.
    """
    scope = f" — {source_key}" if source_key else ""
    embed = discord.Embed(
        title=f"🐵 BTD6 ingestion runs{scope}",
        color=discord.Color.blurple(),
    )
    if not runs:
        embed.description = (
            "No ingestion runs recorded yet."
            if source_key is None
            else f"No ingestion runs recorded for `{source_key}` yet."
        )
        return embed

    lines: list[str] = []
    for r in runs:
        status = str(r.get("status") or "?")
        emoji = _RUN_STATUS_EMOJI.get(status, "•")
        key = r.get("source_key") or "?"
        started = r.get("started_at")
        when = started.isoformat(timespec="minutes") if started is not None else "?"
        facts = r.get("fact_count")
        facts_s = f" · facts={facts}" if isinstance(facts, int) else ""
        err = r.get("error_code")
        err_s = f" · {err}" if err else ""
        lines.append(f"{emoji} `{key}` {status} · {when}{facts_s}{err_s}")

    embed.description = "\n".join(lines)
    embed.set_footer(text=f"{len(runs)} run(s), newest first")
    return embed


__all__ = [
    "build_admin_refresh_summary_embed",
    "build_event_detail_embed",
    "build_grounding_embed",
    "build_hero_embed",
    "build_ingestion_runs_embed",
    "build_latest_data_embed",
    "build_leaderboard_embed",
    "build_live_events_embed",
    "build_pending_review_payload",
    "build_readiness_embed",
    "build_refresh_source_embed",
    "build_source_health_embed",
    "build_sources_payload",
    "build_strategies_payload",
    "build_tower_embed",
    "build_why_no_response_payload",
]
