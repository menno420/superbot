#!/usr/bin/env python3
"""
Help-menu grouping simulation.

Finds the most *efficient logical grouping* of the bot's subsystems into Help
sections, where "efficient" means: every feature reachable in the fewest button
clicks (target: <= 3) while each section stays logically cohesive.

This is a real model of the live Help click graph, not a sketch:

  * Inventory is loaded from the LIVE registries (utils.hub_registry +
    utils.subsystem_registry) so the sim never drifts from the bot.
  * The click model mirrors cogs/help/panels.py exactly, including the
    `_PAGE_SIZE = 12` dropdown pagination that SILENTLY breaks the 3-click
    guarantee: a child past the first dropdown page costs an extra "Next >"
    click, and an un-homed ("orphan") subsystem is only reachable through the
    paginated "All Commands / Advanced" browser.
  * Click depth is computed per audience tier (a user sees ~5 sections; an
    admin sees all of them), because the crowding the owner feels is the
    admin-side view.

Candidate schemes scored:

  current       the live registry exactly (hubs + orphans -> Advanced)
  homed         live hubs, every orphan assigned to its best-fit hub (minimal,
                drift-safe change -- reuses existing hub keys only)
  consolidated  homed + the admin/ops hubs nested under one "Server & Admin"
                section, so the admin-side index shrinks to a few clear sections

An analytical `auto(k)` sweep (greedy cohesion-maximising assignment into k
sections) is printed as a reference frontier -- it shows how close the
implementable schemes get to the best possible logical cohesion.

Stdlib only. Read-only.
  Report:  python3.10 tools/sim/help_menu_grouping_sim.py
  Guard:   python3.10 tools/sim/help_menu_grouping_sim.py --check   (exit 1 on
           any orphan / >3-click / paginated-section violation; this is the
           load-bearing guard wired into CI via
           tests/unit/invariants/test_help_reachability.py).

Provenance: added 2026-06-22 for the owner-directed Help regrouping (PR #1290);
the --check reachability guard added the same day (PR #1297) once the "All
Commands / Advanced" catch-all was removed (PR #1294) and homing became
mandatory for reachability.
Verifiable: its inventory is the live registry and its click model mirrors
panels.py -- re-run after any registry change. Disposable: if the Help nav
model changes shape, delete this rather than work around it.
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from dataclasses import dataclass, field

# --- load the live registries (ground truth inventory) ---------------------
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO, "disbot"))

from utils.subsystem_registry import SUBSYSTEMS  # noqa: E402

PAGE_SIZE = 12  # mirrors cogs/help/panels.py `_PAGE_SIZE`

# Tier ranking (mirrors governance.permission_tiers ordering; hardcoded to keep
# the sim stdlib-only and import-light).
TIER_RANK = {
    "user": 0,
    "trusted": 1,
    "staff": 2,
    "moderator": 3,
    "administrator": 4,
    "owner": 5,
}

# The Help surface itself is not a navigation target inside Help.
EXCLUDE = {"help"}

LEAVES = {k: v for k, v in SUBSYSTEMS.items() if k not in EXCLUDE}


def tier_of(key: str) -> int:
    return TIER_RANK.get(LEAVES[key].get("visibility_tier", "user"), 0)


def category_of(key: str) -> str:
    return LEAVES[key].get("category", "?")


def tags_of(key: str) -> set[str]:
    return set(LEAVES[key].get("tags", []))


# ---------------------------------------------------------------------------
# Scheme model
# ---------------------------------------------------------------------------


@dataclass
class Section:
    key: str  # hub key (must map to a real subsystem for governance)
    label: str
    children: list[str] = field(default_factory=list)  # ordered, in dropdown order


@dataclass
class Scheme:
    name: str
    sections: list[Section]
    # leaves not placed in any section -> reachable only via Advanced browser
    orphans: list[str] = field(default_factory=list)

    def section_of(self, leaf: str) -> Section | None:
        for s in self.sections:
            if leaf == s.key or leaf in s.children:
                return s
        return None


# ---------------------------------------------------------------------------
# Click model (mirrors panels.py)
# ---------------------------------------------------------------------------


def visible_sections(scheme: Scheme, tier: int) -> list[Section]:
    """Index dropdown: sections whose host subsystem is visible to `tier`."""
    out = []
    for s in scheme.sections:
        if s.key in LEAVES and tier_of(s.key) <= tier:
            out.append(s)
    return out


def visible_children(section: Section, tier: int) -> list[str]:
    return [c for c in section.children if c in LEAVES and tier_of(c) <= tier]


def advanced_list(scheme: Scheme, tier: int) -> list[str]:
    """The "All Commands / Advanced" browser, mirroring panels.py: it lists
    EVERY top-level subsystem (section hosts AND un-homed orphans) -- not just
    orphans -- sorted by ui_priority and filtered by tier. So a true orphan's
    page position (hence its click cost) depends on the whole top-level list,
    which is exactly why un-homed features land on page 2 today.
    """
    children = {c for s in scheme.sections for c in s.children}
    top_level = [k for k in LEAVES if k not in children]
    top_level.sort(key=lambda k: LEAVES[k].get("ui_priority", 999))
    return [k for k in top_level if tier_of(k) <= tier]


def orphans_of(scheme: Scheme) -> list[str]:
    return [k for k in LEAVES if scheme.section_of(k) is None]


MAX_CLICKS = 3  # the reachability contract: every feature reachable in <= 3 clicks


def check_reachability() -> list[str]:
    """Return reachability-invariant violations for the LIVE help grouping.

    Empty list == healthy. This is the guard the Help menu relies on now that
    the "All Commands / Advanced" catch-all is gone (PR #1294): with no
    fallback, an un-homed subsystem is *completely unreachable*, so every
    advertisable subsystem must be homed (a hub host or a hub child) and
    reachable within ``MAX_CLICKS`` with no dropdown pagination.

    Used by ``--check`` (CLI / local) and the CI invariant
    ``tests/unit/invariants/test_help_reachability.py``.
    """
    scheme = scheme_live()
    violations: list[str] = []

    orphans = orphans_of(scheme)
    if orphans:
        violations.append(
            "un-homed subsystem(s) reachable from no hub — set parent_hub to a "
            f"registered hub (or add a hub): {', '.join(sorted(orphans))}",
        )

    admin = TIER_RANK["administrator"]
    for sec in scheme.sections:
        n = len(visible_children(sec, admin))
        if n > PAGE_SIZE:
            violations.append(
                f"section {sec.key!r} has {n} children (> {PAGE_SIZE}) — its "
                "dropdown paginates, breaking the 3-click guarantee",
            )

    for leaf in sorted(LEAVES):
        clicks = clicks_to(scheme, leaf, admin)
        if clicks is not None and clicks > MAX_CLICKS:
            violations.append(f"{leaf!r} needs {clicks} clicks (> {MAX_CLICKS})")

    return violations


def clicks_to(scheme: Scheme, leaf: str, tier: int) -> int | None:
    """Minimum button clicks from `!help` to reach `leaf`'s panel for `tier`.

    Returns None if `leaf` is invisible to the tier.
    """
    if tier_of(leaf) > tier:
        return None

    section = scheme.section_of(leaf)
    if section is not None:
        # The section host itself is reached by one index pick.
        if leaf == section.key:
            return 1
        # A child: index pick + dropdown pick, +1 per extra dropdown page.
        kids = visible_children(section, tier)
        if leaf not in kids:  # pragma: no cover - defensive
            return None
        page = kids.index(leaf) // PAGE_SIZE
        return 2 + page

    # Orphan -> Advanced browser: open Advanced (1) + page nexts + select (1).
    adv = advanced_list(scheme, tier)
    if leaf not in adv:  # pragma: no cover - defensive
        return None
    page = adv.index(leaf) // PAGE_SIZE
    return 2 + page


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@dataclass
class SchemeScore:
    name: str
    n_sections_admin: int
    n_sections_user: int
    max_clicks: int
    mean_clicks: float
    pct_within_3: float
    worst: list[tuple[str, int]]
    max_section_children: int
    n_orphans: int
    cohesion: float
    fragmentation: int

    def line(self) -> str:
        return (
            f"{self.name:<13} "
            f"sec(adm/usr)={self.n_sections_admin}/{self.n_sections_user:<2} "
            f"maxclk={self.max_clicks} "
            f"mean={self.mean_clicks:.2f} "
            f"<=3={self.pct_within_3:5.1f}% "
            f"maxkids={self.max_section_children:<2} "
            f"orph={self.n_orphans:<2} "
            f"cohesion={self.cohesion:.2f} "
            f"frag={self.fragmentation}"
        )


def cohesion(scheme: Scheme) -> float:
    """Mean dominant-category share across sections (1.0 = each section is one
    pure category). Single-host sections (no children) score 1.0.
    """
    shares = []
    for s in scheme.sections:
        members = [s.key] + s.children if s.key in LEAVES else list(s.children)
        members = [m for m in members if m in LEAVES]
        if not members:
            continue
        cats = Counter(category_of(m) for m in members)
        shares.append(cats.most_common(1)[0][1] / len(members))
    return sum(shares) / len(shares) if shares else 0.0


def fragmentation(scheme: Scheme) -> int:
    """How many categories are split across >1 section (logical fragmentation)."""
    placement: dict[str, set[str]] = {}
    for s in scheme.sections:
        members = ([s.key] if s.key in LEAVES else []) + s.children
        for m in members:
            if m in LEAVES:
                placement.setdefault(category_of(m), set()).add(s.key)
    return sum(1 for cat, secs in placement.items() if len(secs) > 1)


def score(scheme: Scheme) -> SchemeScore:
    admin = TIER_RANK["administrator"]
    user = TIER_RANK["user"]

    clicks = {}
    for leaf in LEAVES:
        c = clicks_to(scheme, leaf, admin)
        if c is not None:
            clicks[leaf] = c

    max_clicks = max(clicks.values())
    mean_clicks = sum(clicks.values()) / len(clicks)
    within = sum(1 for c in clicks.values() if c <= 3) / len(clicks) * 100
    worst = sorted(clicks.items(), key=lambda kv: -kv[1])
    worst = [(k, c) for k, c in worst if c >= 3][:8]

    max_kids = max(
        (len(visible_children(s, admin)) for s in scheme.sections),
        default=0,
    )

    return SchemeScore(
        name=scheme.name,
        n_sections_admin=len(visible_sections(scheme, admin)),
        n_sections_user=len(visible_sections(scheme, user)),
        max_clicks=max_clicks,
        mean_clicks=mean_clicks,
        pct_within_3=within,
        worst=worst,
        max_section_children=max_kids,
        n_orphans=len(orphans_of(scheme)),
        cohesion=cohesion(scheme),
        fragmentation=fragmentation(scheme),
    )


# ---------------------------------------------------------------------------
# Candidate schemes
# ---------------------------------------------------------------------------


# The pre-regrouping layout (before PR #1290), kept as a fixed historical
# snapshot so the sim shows the before/after the owner approved. 10 top-level
# hubs; 8 subsystems were orphans reachable only via the paginated Advanced
# browser. This is the "problem" state the regrouping fixed.
BASELINE_SECTIONS: dict[str, tuple[str, list[str]]] = {
    "games": (
        "Games",
        ["blackjack", "deathmatch", "rps_tournament", "mining", "counting", "chain"],
    ),
    "btd6": ("BTD6 Assistant", []),
    "economy": ("Economy", ["inventory", "leaderboard"]),
    "moderation": (
        "Moderation & Safety",
        ["automod", "image_moderation", "cleanup", "logging", "proof_channel"],
    ),
    "community": ("Community", ["xp", "community_spotlight", "role"]),
    "utility": ("Utility", ["general", "four_twenty"]),
    "admin": ("Admin / Operations", []),
    "settings": ("Settings / Configuration", []),
    "diagnostic": ("Platform / Diagnostics", []),
    "server_management": ("Server Management", []),
}


def scheme_baseline() -> Scheme:
    """The pre-regrouping layout (hardcoded historical snapshot, before PR
    #1290): 10 sections, 8 orphans falling to the paginated Advanced browser.
    """
    sections = [
        Section(key, label, [c for c in kids if c in LEAVES])
        for key, (label, kids) in BASELINE_SECTIONS.items()
    ]
    return Scheme("baseline", sections)


def scheme_live() -> Scheme:
    """The live registry exactly: hubs + their primary_children (via the
    parent_hub filter); everything else would fall to the Advanced browser.

    After PR #1290 this reads the consolidated grouping straight from the
    registry, so the sim doubles as a regression check: if a future edit
    re-orphans a subsystem or re-crowds the index, the numbers move here.
    """
    from utils.hub_registry import HUBS

    sections = []
    for hub in HUBS:
        children = [k for k, v in LEAVES.items() if v.get("parent_hub") == hub.key]
        children.sort(key=lambda k: LEAVES[k].get("ui_priority", 999))
        sections.append(Section(hub.key, hub.display_name, children))
    return Scheme("live", sections)


def scheme_auto(k: int) -> Scheme:
    """Analytical reference: greedily group leaves into k cohesive sections.

    Not directly implementable (its sections aren't hub-keyed) -- it exists to
    show the cohesion frontier the implementable schemes are measured against.
    Seeds k sections on the k most-common categories, then assigns every leaf
    to the section maximising tag overlap, respecting the PAGE_SIZE cap.
    """
    cats = [c for c, _ in Counter(category_of(x) for x in LEAVES).most_common(k)]
    sections = [Section(f"auto{i}", c, []) for i, c in enumerate(cats)]
    seed_tags = [set() for _ in sections]  # type: ignore[var-annotated]
    for i, c in enumerate(cats):
        for leaf in LEAVES:
            if category_of(leaf) == c:
                seed_tags[i] |= tags_of(leaf)

    for leaf in sorted(LEAVES, key=lambda k: LEAVES[k].get("ui_priority", 999)):
        best, best_score = None, -1.0
        lt = tags_of(leaf) | {category_of(leaf)}
        for i, sec in enumerate(sections):
            if len(sec.children) >= PAGE_SIZE:
                continue
            overlap = len(lt & (seed_tags[i] | {sec.label}))
            if overlap > best_score:
                best, best_score = i, overlap
        sections[best].children.append(leaf)
    return Scheme(f"auto(k={k})", sections)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def print_mapping(scheme: Scheme) -> None:
    print(f"\n  {scheme.name} — section map:")
    for s in scheme.sections:
        kids = ", ".join(s.children) if s.children else "(host only)"
        print(f"    {s.label:<18} [{s.key}] : {kids}")
    orphans = [k for k in LEAVES if scheme.section_of(k) is None]
    if orphans:
        print(f"    {'(Advanced)':<18} : {', '.join(orphans)}")


def main() -> None:
    print("=" * 78)
    print("HELP-MENU GROUPING SIMULATION")
    print(f"inventory: {len(LEAVES)} navigable subsystems (excluding the Help surface)")
    print(f"click model: index -> section -> child; dropdown pages at {PAGE_SIZE}")
    print("=" * 78)

    implementable = [scheme_baseline(), scheme_live()]
    reference = [scheme_auto(k) for k in (5, 6, 7, 8)]

    print("\nBASELINE (pre-PR-#1290) vs LIVE (registry) schemes:\n")
    print(
        f"  {'scheme':<13} {'sections':<14} {'maxclk':<7} {'mean':<6} "
        f"{'within3':<8} {'maxkids':<8} {'orphans':<8} {'cohesion':<9} frag",
    )
    scored = [score(s) for s in implementable]
    for sc in scored:
        print("  " + sc.line())

    print("\n  worst-reach features per scheme (>=3 clicks, admin view):")
    for sc in scored:
        if sc.worst:
            w = ", ".join(f"{k}={c}" for k, c in sc.worst)
            print(f"    {sc.name:<13}: {w}")
        else:
            print(f"    {sc.name:<13}: (all features <=2 clicks)")

    print("\nANALYTICAL reference frontier (max achievable cohesion per k):\n")
    for s in reference:
        sc = score(s)
        print("  " + sc.line())

    # --- recommendation -----------------------------------------------------
    print("\n" + "=" * 78)
    print("RECOMMENDATION")
    print("=" * 78)

    def ok(sc: SchemeScore) -> bool:
        return sc.max_clicks <= 3 and sc.max_section_children <= PAGE_SIZE

    feasible = [sc for sc in scored if ok(sc)]
    # rank: fewest admin sections, then lowest mean clicks, then highest cohesion
    feasible.sort(key=lambda sc: (sc.n_sections_admin, sc.mean_clicks, -sc.cohesion))
    if feasible:
        best = feasible[0]
        print(
            f"\n  Most efficient feasible grouping: '{best.name}'\n"
            f"    - every feature <= {best.max_clicks} clicks "
            f"({best.pct_within_3:.0f}% within 3)\n"
            f"    - {best.n_sections_admin} clear sections (admin view), "
            f"{best.n_sections_user} (user view)\n"
            f"    - logical cohesion {best.cohesion:.2f}, "
            f"category fragmentation {best.fragmentation}\n"
            f"    - no orphans, no dropdown pagination "
            f"(largest section {best.max_section_children} <= {PAGE_SIZE})",
        )
    else:
        print("\n  No implementable scheme meets the <=3-click / no-pagination bar.")

    for s in implementable:
        print_mapping(s)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Help-menu grouping simulation + reachability guard.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "exit non-zero if the LIVE help grouping violates the reachability "
            "invariant (every subsystem homed, <=3 clicks, no dropdown pagination)"
        ),
    )
    args = parser.parse_args()

    if args.check:
        problems = check_reachability()
        if problems:
            print("help reachability check FAILED:")
            for p in problems:
                print(f"  - {p}")
            sys.exit(1)
        print(
            "help reachability check OK — every subsystem homed, "
            f"<= {MAX_CLICKS} clicks, no pagination.",
        )
        sys.exit(0)

    main()
