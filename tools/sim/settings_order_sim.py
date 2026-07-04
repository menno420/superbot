#!/usr/bin/env python3
"""
Settings-order simulation.

The owner recorded himself walking `!settings` → **Server Logging** → **Routes**
and asked, before I reorder anything, to "run a simulation to find out the best
order of these settings" and make it "easy and clear to change all this". This
script answers that for the *two* ordered surfaces in that walk, scoring
candidate orders against a cost model that reflects what the operator is
actually trying to do — not a sketch:

  A. The Server-Logging **routes** (the 11 per-action channel bindings:
     ``mod`` / ``cleanup`` / ``debug`` / ``info`` / ``warning`` / ``error`` /
     ``audit`` / ``events`` / ``message_log`` / ``member_log`` / ``role_log``).
     Their inventory + fallback DAG are read LIVE from
     ``services.server_logging`` so the sim never drifts from the bot. The
     operator's goal is "every event is logged *somewhere*". Because routes
     fall back along the DAG, setting a fallback **root** (``mod`` covers the
     severity/audit/cleanup tier; ``events`` covers the message/member/role
     tier) instantly satisfies everything beneath it — so the clearest order
     puts the two roots FIRST ("set these two and you're covered"), then the
     per-route overrides grouped under the root they refine. The dominant
     metric is *scroll-to-full-coverage*: how far down the list the operator
     must read before they have seen every channel they must set.

  B. The Settings-group **dropdown** (the long list the owner scrolled through
     for ~40s of the clip). It is sorted by the GLOBAL ``ui_priority`` — the
     user-facing *discovery* order (games/economy first, admin/config last).
     That is right for the Help menu, but `!settings` is an admin-only surface:
     the operator came to configure moderation / logging / security / welcome /
     roles and must scroll past ~15 fun/economy groups to reach them. The sim
     scores the admin's *find-cost* (mean dropdown index of the config groups)
     under the current order vs a settings-specific **admin-config-first**
     order, and shows the scroll saved.

Stdlib only. Read-only. Deterministic (no RNG, no clock).
  Report:  python3.10 tools/sim/settings_order_sim.py
  Guard:   python3.10 tools/sim/settings_order_sim.py --check   (exit 1 if the
           shipped `_ROUTE_DISPLAY_ORDER` has drifted from the recommended
           roots-first order; wired into CI via
           tests/unit/invariants/test_settings_order.py).

Provenance: added 2026-07-01 for the owner's screen-recording bug report (the
Routes walk). Verifiable: its route inventory + fallback DAG are the live
``services.server_logging`` tables and the routes recommendation is pinned to
the shipped ``_ROUTE_DISPLAY_ORDER`` by the --check guard — re-run after any
route-table change. Disposable: if the routes/settings ordering model changes
shape, delete this rather than work around it.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

# --- load the live tables (ground-truth inventory) -------------------------
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO, "disbot"))

from cogs.logging.routes_panel import _ROUTE_DISPLAY_ORDER  # noqa: E402
from services.server_logging import (  # noqa: E402
    _ROUTE_FALLBACK,
    _ROUTE_TO_BINDING,
)
from utils.subsystem_registry import SUBSYSTEMS  # noqa: E402

# Semantic group of each route — used only for the cohesion metric / display.
_ROUTE_GROUP: dict[str, str] = {
    "mod": "sources",
    "cleanup": "sources",
    "debug": "severity",
    "info": "severity",
    "warning": "severity",
    "error": "severity",
    "audit": "audit",
    "events": "events",
    "message_log": "events",
    "member_log": "events",
    "role_log": "events",
}


# ---------------------------------------------------------------------------
# A. Logging routes
# ---------------------------------------------------------------------------


def _root_of(kind: str) -> str:
    """Walk the fallback DAG to the terminal root a route resolves under."""
    seen: set[str] = set()
    cur = kind
    while True:
        nxt = _ROUTE_FALLBACK.get(cur)
        if nxt is None or cur in seen:
            return cur
        seen.add(cur)
        cur = nxt


def _roots() -> list[str]:
    """Fallback roots (``_ROUTE_FALLBACK[k] is None``), most-covering first."""
    roots = [k for k in _ROUTE_TO_BINDING if _ROUTE_FALLBACK.get(k) is None]
    # Descendant count = how many routes resolve under this root (self incl.).
    cover = {r: sum(1 for k in _ROUTE_TO_BINDING if _root_of(k) == r) for r in roots}
    # Most-covering root first; tie-break by first appearance in the live order.
    return sorted(roots, key=lambda r: (-cover[r], _ROUTE_DISPLAY_ORDER.index(r)))


def recommended_route_order() -> tuple[str, ...]:
    """Roots-first, then each root's overrides grouped under it.

    Deterministic and derived entirely from the live fallback table: the two
    roots lead (so the operator sees the minimum coverage set immediately),
    then every non-root route follows under its root, preserving the existing
    within-tier order for stability (cleanup → severity → audit; message →
    member → role).
    """
    order: list[str] = []
    roots = _roots()
    order.extend(roots)
    for root in roots:
        for kind in _ROUTE_DISPLAY_ORDER:
            if kind not in roots and _root_of(kind) == root:
                order.append(kind)
    # Any route not reached above (defensive — shouldn't happen) keeps its spot.
    for kind in _ROUTE_DISPLAY_ORDER:
        if kind not in order:
            order.append(kind)
    return tuple(order)


def scroll_to_full_coverage(order: tuple[str, ...] | list[str]) -> int:
    """0-based index by which every fallback root has been *seen*.

    This is the "easy and clear" metric: the operator can stop reading once
    they have seen both roots (set those two → everything is covered), so a
    lower number means less scrolling before the job is understood.
    """
    roots = [k for k in _ROUTE_TO_BINDING if _ROUTE_FALLBACK.get(k) is None]
    return max(order.index(r) for r in roots)


def fallback_inversions(order: tuple[str, ...] | list[str]) -> int:
    """Routes listed BEFORE the root they fall back to.

    A non-root route reads naturally as "overrides <root>" only if its root was
    already shown, so inversions are confusing. Lower is better (0 is ideal).
    """
    pos = {k: i for i, k in enumerate(order)}
    bad = 0
    for kind in order:
        root = _root_of(kind)
        if root != kind and pos[kind] < pos[root]:
            bad += 1
    return bad


def category_runs(order: tuple[str, ...] | list[str]) -> int:
    """Number of contiguous same-group runs (fewer = more cohesive blocks)."""
    runs = 0
    prev: str | None = None
    for kind in order:
        g = _ROUTE_GROUP.get(kind, "?")
        if g != prev:
            runs += 1
            prev = g
    return runs


@dataclass
class RouteScore:
    name: str
    order: tuple[str, ...]
    scroll: int
    inversions: int
    runs: int

    @property
    def composite(self) -> float:
        # Scroll dominates (the owner's explicit "easy and clear" goal), then
        # correctness (inversions), then cohesion (runs) as a gentle tie-break.
        return self.scroll * 10 + self.inversions * 5 + self.runs * 0.5


def _score_route_order(name: str, order: tuple[str, ...]) -> RouteScore:
    return RouteScore(
        name=name,
        order=order,
        scroll=scroll_to_full_coverage(order),
        inversions=fallback_inversions(order),
        runs=category_runs(order),
    )


def route_candidates() -> dict[str, tuple[str, ...]]:
    return {
        "current": tuple(_ROUTE_DISPLAY_ORDER),
        "alpha": tuple(sorted(_ROUTE_TO_BINDING)),
        "roots_first": recommended_route_order(),
    }


# ---------------------------------------------------------------------------
# B. Settings-group dropdown
# ---------------------------------------------------------------------------

# Categories an admin opens `!settings` to configure — the "server operations"
# groups. Everything else (games / economy / progression / fun) is discovery,
# not configuration, and belongs below in the admin surface.
_CONFIG_CATEGORIES = frozenset({"moderation", "management", "admin"})
# Community carries a mix (welcome / counters are admin-config; spotlight is
# fun) — split it by visibility tier instead of category.
_ADMIN_TIERS = frozenset({"staff", "moderator", "administrator", "owner"})


def _is_config_group(subsystem: str) -> bool:
    meta = SUBSYSTEMS.get(subsystem, {})
    if meta.get("category") in _CONFIG_CATEGORIES:
        return True
    # Admin-tier community groups (welcome, counters) are config too.
    return (
        meta.get("category") == "community"
        and meta.get("visibility_tier") in _ADMIN_TIERS
    )


def settings_sort_rank(subsystem: str) -> tuple[int, int, str]:
    """The recommended settings-dropdown sort key (admin-config-first).

    Tier 0 = server-operations groups (moderation / management / admin +
    admin-tier community), tier 1 = everything else; ``ui_priority`` then key
    order the members *within* each tier so the existing intuition is kept
    inside the block. This is settings-surface-only — the global
    ``ui_priority`` (Help / hub discovery order) is untouched.
    """
    meta = SUBSYSTEMS.get(subsystem, {})
    tier = 0 if _is_config_group(subsystem) else 1
    return (tier, int(meta.get("ui_priority", 99)), subsystem)


def _settings_candidate_members() -> list[str]:
    """Approximate the dropdown membership: every subsystem that plausibly
    exposes settings/bindings (has a parent-config signal). The ordering
    *policy* conclusion is membership-independent, but using the real registry
    keeps the find-cost numbers honest.
    """
    members = []
    for name, meta in SUBSYSTEMS.items():
        if name == "help":
            continue
        # A crude but registry-grounded proxy for "actionable in settings":
        # anything that declares config-ish capabilities or is an admin surface.
        if meta.get("category") in _CONFIG_CATEGORIES or _is_config_group(name):
            members.append(name)
            continue
        # Plus the user-facing groups the live dropdown also lists (economy /
        # games / progression) so the find-cost reflects the real scroll.
        if meta.get("category") in {"economy", "games", "progression", "community"}:
            members.append(name)
    return members


def _current_settings_order(members: list[str]) -> list[str]:
    return sorted(
        members,
        key=lambda s: (int(SUBSYSTEMS.get(s, {}).get("ui_priority", 99)), s),
    )


def _admin_first_settings_order(members: list[str]) -> list[str]:
    return sorted(members, key=settings_sort_rank)


def _config_find_cost(order: list[str]) -> float:
    """Mean 0-based dropdown index of the config groups (lower = less scroll)."""
    config = [s for s in order if _is_config_group(s)]
    if not config:
        return 0.0
    return sum(order.index(s) for s in config) / len(config)


# ---------------------------------------------------------------------------
# Guard + report
# ---------------------------------------------------------------------------


def check_orders() -> list[str]:
    """Return drift problems (empty = shipped orders match the recommendation).

    Only the routes order is hard-guarded here — it is deterministic and
    importable without registered schemas. The settings-dropdown ordering is
    guarded by ``tests/unit/views`` (where the schema registry is populated).
    """
    problems: list[str] = []
    rec = recommended_route_order()
    if tuple(_ROUTE_DISPLAY_ORDER) != rec:
        problems.append(
            "_ROUTE_DISPLAY_ORDER has drifted from the roots-first "
            f"recommendation.\n    shipped:     {list(_ROUTE_DISPLAY_ORDER)}\n"
            f"    recommended: {list(rec)}",
        )
    return problems


def _print_routes_report() -> None:
    print("=" * 72)
    print("A. Server-Logging routes — best binding order")
    print("=" * 72)
    print(
        "\nGoal: every event logged somewhere. Fallback roots "
        f"{_roots()} cover the rest, so a clear order shows them first.\n",
    )
    scored = [_score_route_order(n, o) for n, o in route_candidates().items()]
    scored.sort(key=lambda s: s.composite)
    print(f"  {'candidate':13}  {'scroll':>6}  {'inv':>4}  {'runs':>4}  score")
    print(f"  {'-' * 13}  {'-' * 6}  {'-' * 4}  {'-' * 4}  -----")
    for s in scored:
        star = "  ★ best" if s is scored[0] else ""
        print(
            f"  {s.name:13}  {s.scroll:>6}  {s.inversions:>4}  "
            f"{s.runs:>4}  {s.composite:5.1f}{star}",
        )
    best = scored[0]
    print(
        "\n  metrics: scroll = routes to read before both coverage-roots are "
        "seen\n           inv = routes shown before their fallback root · "
        "runs = category blocks",
    )
    print(f"\n  ★ recommended order ({best.name}):")
    for i, kind in enumerate(best.order):
        root = _root_of(kind)
        tag = "ROOT — covers its tier" if root == kind else f"↪ falls back to {root}"
        print(f"     {i + 1:>2}. {kind:12} ({tag})")
    cur = _score_route_order("current", tuple(_ROUTE_DISPLAY_ORDER))
    print(
        f"\n  vs current: scroll {cur.scroll} → {best.scroll} "
        f"({cur.scroll - best.scroll} fewer routes to read before full "
        "coverage is understood).",
    )
    print(
        "  shipped `_ROUTE_DISPLAY_ORDER` "
        + ("MATCHES ✓" if tuple(_ROUTE_DISPLAY_ORDER) == best.order else "DRIFTED ✗")
        + " the recommendation.",
    )


def _print_settings_report() -> None:
    print("\n" + "=" * 72)
    print("B. Settings-group dropdown — admin-config-first")
    print("=" * 72)
    members = _settings_candidate_members()
    cur = _current_settings_order(members)
    rec = _admin_first_settings_order(members)
    cur_cost = _config_find_cost(cur)
    rec_cost = _config_find_cost(rec)
    print(
        f"\n  {len(members)} candidate groups · "
        f"{sum(1 for s in members if _is_config_group(s))} are server-config.\n",
    )
    print("  find-cost (mean dropdown index of config groups, lower=better):")
    print(f"     current  (global ui_priority) : {cur_cost:5.1f}")
    print(f"     admin_first (settings-only)   : {rec_cost:5.1f}")
    print(f"     → {cur_cost - rec_cost:.1f} fewer rows of scrolling on average\n")
    print("  first 8 of each order (what the admin sees without scrolling):")
    print(f"     current    : {', '.join(cur[:8])}")
    print(f"     admin_first: {', '.join(rec[:8])}")
    print(
        "\n  recommendation: sort the Settings dropdown by "
        "`settings_sort_rank` (server-config groups first, ui_priority within\n"
        "  each tier). This is applied in "
        "`customization_catalogue.actionable_settings_groups` and touches ONLY\n"
        "  the settings surface — the global ui_priority (Help / hub discovery "
        "order) is unchanged.",
    )


def main() -> None:
    _print_routes_report()
    _print_settings_report()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Settings-order simulation + routes-order drift guard.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "exit non-zero if the shipped _ROUTE_DISPLAY_ORDER has drifted "
            "from the roots-first recommendation"
        ),
    )
    args = parser.parse_args()

    if args.check:
        issues = check_orders()
        if issues:
            print("settings-order check FAILED:")
            for p in issues:
                print(f"  - {p}")
            sys.exit(1)
        print("settings-order check OK — routes match the roots-first order.")
        sys.exit(0)

    main()
