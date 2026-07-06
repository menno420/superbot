"""BTD6 boss-fight estimator — deterministic kill-time / cost / DPS estimates.

The bot has every ingredient to *estimate* a boss fight — boss HP + speed
(``bosses.json``), per-crosspath combat stats (:mod:`services.btd6_stats_service`),
and tower costs — yet without a compute seam the model either refuses the question
or confabulates a wrong tower list (the failure seen in the review-log export). This
service does the arithmetic **deterministically** so the answer path can state a
grounded estimate *with explicit assumptions* instead of guessing.

**Scope (v1): single-target base DPS.** Deliberately approximate and labelled as
such — it excludes MOAB/boss bonus damage, abilities, buffs, targeting, pierce, AoE,
uptime, and boss damage-resistance phases. The owner explicitly accepts a stated
estimate over a refusal; :attr:`KillEstimate.assumptions` carries the caveats so the
reply can show them. Pure data + arithmetic — no Discord, no network.
"""

from __future__ import annotations

from dataclasses import dataclass

from services import btd6_stats_service
from utils.btd6 import tier_codes

# Base single-target DPS understates abilities/bonuses, so the caveat ships with
# every estimate (the reply states it; the owner wants honesty over false precision).
_ASSUMPTIONS: tuple[str, ...] = (
    "base single-target DPS (excludes MOAB/boss bonus damage, abilities, buffs)",
    "ignores targeting, pierce, AoE, uptime, and boss damage-resistance phases",
    "one tower, no support (Alchemist/Village) buffs",
)


@dataclass(frozen=True)
class KillEstimate:
    """A deterministic single-tower vs single-boss-tier estimate."""

    tower_id: str
    tower_canonical: str
    crosspath: str  # display form, e.g. "0-2-4"
    cost: int
    dps: float
    damage_type: str | None
    sees_camo: bool
    boss_id: str
    boss_canonical: str
    boss_tier: int
    boss_hp: int
    boss_speed: float
    time_to_kill_s: float | None  # None when dps is 0 / immunity-blocked
    blocked_by_immunity: bool
    boss_immune_to: tuple[str, ...]
    # Track context (populated only when a known map is named):
    map_canonical: str | None = None
    track_rbs: float | None = None  # red-bloon seconds to cross the main track
    boss_cross_s: float | None = None  # est. seconds for THIS boss to cross
    kills_before_exit: bool | None = None  # ttk < boss_cross_s (one unobstructed pass)
    assumptions: tuple[str, ...] = _ASSUMPTIONS


@dataclass(frozen=True)
class EstimateRequest:
    """A parsed ``!btd6estimate`` query."""

    mode: str  # "single" (tower vs boss) | "counters" (rank towers vs boss)
    tower_query: str
    boss_query: str
    tier: int
    map_query: str = ""


@dataclass(frozen=True)
class CounterRow:
    """One tower's best cost-efficiency option against a boss (ranking entry)."""

    tower_id: str
    tower_canonical: str
    crosspath: str
    cost: int
    dps: float
    dps_per_dollar: float
    time_to_kill_s: float | None


# ---------------------------------------------------------------------------
# Cost + DPS primitives
# ---------------------------------------------------------------------------


def cost_for_code(stats: btd6_stats_service.TowerStats, code: str) -> int | None:
    """Total cash to reach crosspath ``code``: base + every upgrade on the way.

    None if the code is malformed or an upgrade cost is missing from the data.
    """
    if not tier_codes.is_valid_code(code):
        return None
    digits = tier_codes.digits(code)
    by_path_tier: dict[tuple[int, int], int] = {}
    for upg in stats.upgrades:
        path, tier = upg.get("path"), upg.get("tier")
        cost = upg.get("cost")
        if isinstance(path, int) and isinstance(tier, int) and isinstance(cost, int):
            by_path_tier[(path, tier)] = cost
    total = stats.base_cost or 0
    for path_idx, top_tier in enumerate(digits, start=1):
        for tier in range(1, top_tier + 1):
            cost = by_path_tier.get((path_idx, tier))
            if cost is None:
                return None
            total += cost
    return total


# Per-hit damage at/above this is an instakill / sentinel value (e.g. Druid's
# 9,999,999 Vine, an instant-kill marker the stats service renders as "∞"), not
# sustained DPS — excluded so a single sentinel can't dominate the estimate.
_INSTAKILL_DAMAGE_CAP = 100_000.0


def dps_for_code(stats: btd6_stats_service.TowerStats, code: str) -> float | None:
    """Base single-target DPS at crosspath ``code`` (None if no damaging attack).

    Sums per-attack ``Σ projectile damage ÷ cooldown`` over the tier's attacks,
    excluding instakill sentinel projectiles (see :data:`_INSTAKILL_DAMAGE_CAP`).
    Like :func:`services.btd6_stats_service.rough_attack_dps` this ignores
    targeting / pierce / AoE / count (single-target approximation).
    """
    tier = stats.tier(code)
    if not tier:
        return None
    breakdown = btd6_stats_service.attack_breakdown(tier.get("attacks") or [])
    if not breakdown:
        return None
    total = 0.0
    for atk in breakdown:
        if not atk.cooldown:
            continue
        damage = sum(
            dmg
            for (_name, dmg, _pierce) in atk.projectiles
            if 0 < dmg < _INSTAKILL_DAMAGE_CAP
        )
        total += damage / atk.cooldown
    return round(total, 1)


# ---------------------------------------------------------------------------
# Boss lookup
# ---------------------------------------------------------------------------


def find_boss(query: str):  # -> BossEntry | None
    """Resolve a free-form boss name to its dataset entry (substring/alias match)."""
    from services import btd6_data_service

    text = (query or "").strip().lower()
    if not text:
        return None
    for boss in btd6_data_service.get_dataset().bosses:
        if boss.id.lower() in text or (
            boss.canonical and boss.canonical.lower() in text
        ):
            return boss
    # token containment the other way (e.g. "bloonarius t5" -> "bloonarius")
    for boss in btd6_data_service.get_dataset().bosses:
        if boss.canonical and any(
            tok == boss.canonical.lower() for tok in text.split()
        ):
            return boss
    return None


def _boss_tier_row(boss, tier: int) -> dict | None:
    for row in boss.tiers:
        if row.get("tier") == tier:
            return row
    return None


# ---------------------------------------------------------------------------
# Track length (Red Bloon Seconds) — map_track_lengths.json
# ---------------------------------------------------------------------------

# (map_id, canonical, rbs), longest-canonical-first for greedy substring match.
_TRACK_INDEX: tuple[tuple[str, str, float], ...] | None = None


def _track_index() -> tuple[tuple[str, str, float], ...]:
    """Load + cache the wiki-sourced Red Bloon Seconds per map (longest name first)."""
    global _TRACK_INDEX
    if _TRACK_INDEX is None:
        from services import btd6_data_service

        blob = btd6_data_service.read_blob("map_track_lengths.json") or {}
        rows: list[tuple[str, str, float]] = []
        for t in blob.get("tracks", ()):
            map_id, name, rbs = t.get("map_id"), t.get("map"), t.get("rbs")
            if map_id and name and isinstance(rbs, (int, float)):
                rows.append((str(map_id), str(name), float(rbs)))
        rows.sort(key=lambda r: len(r[1]), reverse=True)
        _TRACK_INDEX = tuple(rows)
    return _TRACK_INDEX


def find_map_track(query: str) -> tuple[str, float] | None:
    """Resolve a map named in ``query`` to ``(canonical, rbs)`` — longest match wins.

    Greedy substring match on the map's display name so "monkey meadow" resolves
    even inside a longer sentence; None when no known map is named. ``rbs`` is the
    Red Bloon Seconds (red bloon, the speed-1.0 baseline) to cross the main track.
    """
    low = (query or "").lower()
    if not low:
        return None
    for _map_id, name, rbs in _track_index():
        if name.lower() in low:
            return name, rbs
    return None


def reset_cache_for_tests() -> None:
    """Drop the cached track index (test seam)."""
    global _TRACK_INDEX
    _TRACK_INDEX = None


# ---------------------------------------------------------------------------
# Estimate
# ---------------------------------------------------------------------------


def estimate(
    tower_id: str,
    code: str,
    boss_id: str,
    tier: int,
    map_query: str = "",
) -> KillEstimate | None:
    """Estimate one tower (at crosspath ``code``) vs one boss tier.

    None when the tower has no stats, the code has no DPS, or the boss/tier is
    unknown. ``time_to_kill_s`` is None when the boss is immune to the tower's
    damage type (or DPS is 0). When ``map_query`` names a known map, the track
    fields (red-bloon RBS, est. boss-crossing time, escape verdict) are filled.
    """
    from services import btd6_data_service

    stats = btd6_stats_service.get_tower_stats(tower_id)
    if stats is None:
        return None
    tier_stats = stats.tier(code)
    if not tier_stats:
        return None
    boss = next(
        (b for b in btd6_data_service.get_dataset().bosses if b.id == boss_id),
        None,
    )
    if boss is None:
        return None
    row = _boss_tier_row(boss, tier)
    if row is None:
        return None

    dps = dps_for_code(stats, code) or 0.0
    cost = cost_for_code(stats, code)
    normal = btd6_stats_service.normal_stats(tier_stats)
    hp = int(row.get("health") or 0)
    blocked = bool(normal.damage_type and normal.damage_type in boss.immune_to)
    time_to_kill = (hp / dps) if (dps > 0 and not blocked) else None
    boss_speed = float(row.get("speed") or 0.0)

    # Track context (only when a known map is named). A red bloon crosses in
    # `rbs` s; the boss moves at `boss_speed`× the base bloon speed, so it crosses
    # in ~`rbs / boss_speed` s (one unobstructed pass — an estimate, since boss
    # fights actually pause at skull phases).
    map_canonical: str | None = None
    track_rbs: float | None = None
    boss_cross_s: float | None = None
    kills_before_exit: bool | None = None
    track = find_map_track(map_query) if map_query else None
    if track is not None:
        map_canonical, track_rbs = track
        if boss_speed > 0:
            boss_cross_s = round(track_rbs / boss_speed, 1)
            if time_to_kill is not None:
                kills_before_exit = time_to_kill <= boss_cross_s

    return KillEstimate(
        tower_id=tower_id,
        tower_canonical=stats.canonical or tower_id,
        crosspath=tier_codes.format_code(code),
        cost=cost if cost is not None else (stats.base_cost or 0),
        dps=round(dps, 1),
        damage_type=normal.damage_type,
        sees_camo=normal.can_see_camo,
        boss_id=boss.id,
        boss_canonical=boss.canonical or boss.id,
        boss_tier=tier,
        boss_hp=hp,
        boss_speed=boss_speed,
        time_to_kill_s=round(time_to_kill, 1) if time_to_kill is not None else None,
        blocked_by_immunity=blocked,
        boss_immune_to=tuple(boss.immune_to),
        map_canonical=map_canonical,
        track_rbs=track_rbs,
        boss_cross_s=boss_cross_s,
        kills_before_exit=kills_before_exit,
    )


def resolve_tower(query: str) -> tuple[str, str] | None:
    """Resolve free-form text to ``(tower_id, crosspath_code)``.

    Picks the first resolved tower and a crosspath code if the text names one
    (e.g. "super monkey 0-2-4"); defaults to the base ``000``.
    """
    from services import btd6_resolver_service

    intent = btd6_resolver_service.resolve(query)
    if not intent.towers:
        return None
    tower_id = intent.towers[0].id
    code = _extract_code(query)
    return tower_id, code


def _extract_code(text: str) -> str:
    """Pull a crosspath code like ``0-2-4`` / ``024`` from free text, else ``000``."""
    import re

    m = re.search(r"\b([0-5])\s*-\s*([0-5])\s*-\s*([0-5])\b", text)
    if m:
        code = "".join(m.groups())
        if tier_codes.is_valid_code(code):
            return code
    m = re.search(r"\b([0-5])([0-5])([0-5])\b", text)
    if m and tier_codes.is_valid_code(m.group(0)):
        return m.group(0)
    return "000"


def resolve_and_estimate(
    tower_query: str,
    boss_query: str,
    tier: int,
    map_query: str = "",
) -> KillEstimate | None:
    """Resolve free-form tower + boss names and estimate the fight."""
    resolved = resolve_tower(tower_query)
    boss = find_boss(boss_query)
    if resolved is None or boss is None:
        return None
    tower_id, code = resolved
    return estimate(tower_id, code, boss.id, tier, map_query)


# ---------------------------------------------------------------------------
# Cheapest-counter ranking (most DPS per dollar)
# ---------------------------------------------------------------------------


def parse_request(text: str) -> EstimateRequest:
    """Parse a free-form estimate query into structured intent.

    ``"super monkey 0-4-0 vs bloonarius t5"`` → single estimate (tier 5).
    ``"counters for bloonarius tier 3"`` / ``"bloonarius"`` → counters ranking.
    Tier defaults to **5** (the hardest tier, most-asked) when none is named.
    """
    import re

    raw = (text or "").strip()
    tier = 5
    m = re.search(r"\b(?:tier\s*|t)([1-5])\b", raw, re.IGNORECASE)
    if m:
        tier = int(m.group(1))
        raw = (raw[: m.start()] + " " + raw[m.end() :]).strip()

    # Pull a known map name out of the text ("… on monkey meadow") so it doesn't
    # pollute boss resolution; record it for the track / escape-margin estimate.
    map_query = ""
    track = find_map_track(raw)
    if track is not None:
        map_query = track[0]
        raw = re.sub(
            rf"\s*\bon\b\s*{re.escape(map_query)}|\s*{re.escape(map_query)}",
            " ",
            raw,
            count=1,
            flags=re.IGNORECASE,
        ).strip()

    low = raw.lower()
    for sep in (" vs ", " versus "):
        if sep in low:
            idx = low.index(sep)
            return EstimateRequest(
                mode="single",
                tower_query=raw[:idx].strip(),
                boss_query=raw[idx + len(sep) :].strip(),
                tier=tier,
                map_query=map_query,
            )
    boss_q = re.sub(
        r"^(counters?|cheapest|best)\s+(for\s+|to\s+|vs\s+)?",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip()
    return EstimateRequest(
        mode="counters",
        tower_query="",
        boss_query=boss_q,
        tier=tier,
        map_query=map_query,
    )


def cheapest_counters(
    boss_id: str,
    tier: int,
    *,
    limit: int = 5,
) -> list[CounterRow]:
    """Rank towers by best DPS-per-dollar against a boss tier (v1 cost-efficiency).

    For each tower, scans its present legal crosspaths, computes base DPS + cost,
    and keeps the highest DPS-per-dollar option (skipping options blocked by the
    boss's damage-type immunity). Returns the top ``limit``, most-efficient first.
    This is the "cheapest single tower" proxy until the track-time gate lands.
    """
    from services import btd6_data_service

    dataset = btd6_data_service.get_dataset()
    boss = next((b for b in dataset.bosses if b.id == boss_id), None)
    if boss is None:
        return []
    row = _boss_tier_row(boss, tier)
    if row is None:
        return []
    hp = int(row.get("health") or 0)
    immune = set(boss.immune_to)

    rows: list[CounterRow] = []
    for tower in dataset.towers:
        stats = btd6_stats_service.get_tower_stats(tower.id)
        if stats is None or not stats.has_combat_stats:
            continue
        best: CounterRow | None = None
        for code in stats.tiers:
            if not tier_codes.is_valid_code(code) or not tier_codes.is_legal(code):
                continue
            tier_stats = stats.tier(code)
            if not tier_stats:
                continue
            normal = btd6_stats_service.normal_stats(tier_stats)
            if normal.damage_type and normal.damage_type in immune:
                continue
            dps = dps_for_code(stats, code) or 0.0
            cost = cost_for_code(stats, code)
            if dps <= 0 or not cost:
                continue
            value = dps / cost
            if best is None or value > best.dps_per_dollar:
                best = CounterRow(
                    tower_id=tower.id,
                    tower_canonical=stats.canonical or tower.id,
                    crosspath=tier_codes.format_code(code),
                    cost=cost,
                    dps=round(dps, 1),
                    dps_per_dollar=round(value, 4),
                    time_to_kill_s=round(hp / dps, 1) if dps > 0 else None,
                )
        if best is not None:
            rows.append(best)
    rows.sort(key=lambda r: r.dps_per_dollar, reverse=True)
    return rows[: max(1, limit)]


# ---------------------------------------------------------------------------
# Text formatting (reused by the command + the AI answer path)
# ---------------------------------------------------------------------------


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 90:
        return f"~{seconds:.0f}s"
    minutes = seconds / 60.0
    if minutes < 90:
        return f"~{minutes:.1f} min"
    return f"~{minutes / 60.0:.1f} hr"


def format_estimate_text(est: KillEstimate) -> str:
    """A grounded, assumption-stated estimate as plain text (no Discord types)."""
    lines = [
        f"**{est.tower_canonical} ({est.crosspath})** vs "
        f"**{est.boss_canonical} Tier {est.boss_tier}**",
        f"• Boss HP: **{est.boss_hp:,}** (speed {est.boss_speed})",
        f"• Tower: ~**{est.dps:,.0f} DPS** ({est.damage_type or 'unknown'} damage), "
        f"cost **${est.cost:,}**" + ("" if est.sees_camo else " — ⚠️ no camo detection"),
    ]
    if est.blocked_by_immunity:
        lines.append(
            f"• ⛔ This boss is immune to **{est.damage_type}** — that tower can't "
            f"damage it. (Immune to: {', '.join(est.boss_immune_to) or 'n/a'}.)",
        )
    else:
        lines.append(
            f"• Estimated solo kill time: **{_fmt_duration(est.time_to_kill_s)}** "
            f"({est.boss_hp:,} HP ÷ {est.dps:,.0f} DPS)",
        )
    if est.map_canonical and est.track_rbs is not None:
        track_line = (
            f"• **{est.map_canonical}** track: ~{est.track_rbs:.0f}s for a red bloon"
        )
        if est.boss_cross_s is not None:
            track_line += f"; this boss crosses in ~{est.boss_cross_s:.0f}s"
        lines.append(track_line)
        if est.kills_before_exit is True:
            lines.append(
                f"• ✅ Kills it in {_fmt_duration(est.time_to_kill_s)} — **before** one "
                f"unobstructed pass (~{est.boss_cross_s:.0f}s).",
            )
        elif est.kills_before_exit is False:
            lines.append(
                f"• ⚠️ Solo kill ({_fmt_duration(est.time_to_kill_s)}) is **slower** than "
                f"one pass (~{est.boss_cross_s:.0f}s) — you'd need more DPS or stalling "
                "(bosses do pause at skull phases, so you usually get longer).",
            )
    lines.append("_Estimate — " + "; ".join(est.assumptions) + "._")
    return "\n".join(lines)


def format_counters_text(
    rows: list[CounterRow],
    boss_canonical: str,
    tier: int,
) -> str:
    """Rank text for the most cost-efficient towers vs a boss tier."""
    if not rows:
        return f"No tower estimates available for {boss_canonical} Tier {tier}."
    out = [
        f"**Most DPS-per-dollar vs {boss_canonical} Tier {tier}** (base DPS, single tower):",
    ]
    for i, r in enumerate(rows, start=1):
        out.append(
            f"{i}. **{r.tower_canonical} {r.crosspath}** — ~{r.dps:,.0f} DPS, "
            f"${r.cost:,} (solo kill {_fmt_duration(r.time_to_kill_s)})",
        )
    out.append("_Estimate — base single-target DPS; excludes abilities/buffs/bonuses._")
    return "\n".join(out)


__all__ = [
    "CounterRow",
    "EstimateRequest",
    "KillEstimate",
    "cheapest_counters",
    "format_counters_text",
    "format_estimate_text",
    "parse_request",
    "cost_for_code",
    "dps_for_code",
    "estimate",
    "find_boss",
    "find_map_track",
    "resolve_and_estimate",
    "resolve_tower",
]
