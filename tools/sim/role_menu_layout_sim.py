#!/usr/bin/env python3
"""
Role-menu builder button-layout simulation.

Finds the button arrangement (and function set) for the reaction-role **menu
builder** (``disbot/views/roles/role_menu_builder.py`` ``RoleMenuBuilder``) that
minimises real interaction cost across the tasks operators actually do — the
owner asked "find the most optimal button placements and functions" after a live
test where the 14-button, 3-row builder felt dense and a couple of taps deep.

It is a model, not a sketch, but "optimal" is only as good as the model, so every
assumption is spelled out and tunable:

  * INVENTORY — the 14 builder buttons + their groups are the live set (kept in
    sync with the button decorators in role_menu_builder.py; a drift guard in
    tests/unit/tools/test_role_menu_layout_sim.py pins the names).
  * JOURNEYS — weighted operator tasks (build an RSVP, colour roles, game roles,
    notifications, verify gate, a fully-custom menu, edit-a-field). Weights lead
    with the RSVP/self-role cases the owner cares about; templates short-circuit
    config, so most journeys start at "Template" and never touch Mode/Limit/etc.
  * COST — for a layout, each journey pays: prominence (a button's top-left
    reading index — top-left is found fastest), travel (eye/thumb move between
    consecutive taps, row jumps costlier than column), and a submenu-open penalty
    when a pressed function is folded behind a grouping button. Layout-level terms
    reward keeping a group's buttons contiguous and putting Post/Back in their
    conventional submit/back corners.
  * SEARCH — seeded simulated annealing with restarts (deterministic; no live
    RNG), over both the arrangement AND a few function-set variants (fold rarely
    used cosmetic/rule buttons behind one grouping button).

The output ranks the variants, prints the winning grid, and lists the per-journey
tap cost vs. the CURRENT layout so the recommendation is concrete and auditable.

Stdlib only. Read-only. Deterministic (seeded).
  Report:  python3.10 tools/sim/role_menu_layout_sim.py
           python3.10 tools/sim/role_menu_layout_sim.py --seed 7 --iters 40000

FINDINGS (seed 1, stable across seeds 1/2/7; re-run to confirm)
---------------------------------------------------------------
The CURRENT 14-button / 3-row builder scores ~40. It leads with rarely-tapped
knobs (Theme/Mode/Limit on the top two rows) and scatters the hot content
buttons, so the common RSVP/self-role tasks pay for buttons they never press.

Style is PINNED first-screen (owner directive, 2026-07-01: dropdown-vs-buttons is
a primary choice), so every recommendation keeps it visible on row 0.

Two improvements, both re-order the hot content buttons onto row 0 with Style, and
drop Post to the bottom-right (submit convention):

  * LOW-RISK — keep all 14 buttons, only re-order:               ~ -42% cost.
  * BEST — "lean_advanced": fold the five rarely-tapped knobs
    (Theme/Card/Counts/Mode/Limit) behind one ⚙️ Advanced button
    (Style stays visible) → a 10-button / 2-row builder:          ~ -52% cost.
        row 0: [🧩 Template] [📦 Packs] [🏷️ Roles] [🎚️ Style] [📝 Text]
        row 1: [↩ Back] [🎨 Colours] [📍 Channel] [⚙️ Advanced] [🚀 Post]

The lean layout is a product call (it hides five functions behind Advanced — the
RSVP template already sets Counts/Mode, so the common path never needs them); the
re-order is a safe, mechanical win. Adopting either is a follow-up — this file
only *finds* the layout; it doesn't change the builder.

Provenance: added 2026-07-01 for the owner-directed builder-layout question
(follow-on to the reaction-roles counter/roster/preview-fix arc, #1570/#1571/#1608).
Verifiable: the inventory mirrors the live button decorators (drift-guarded) and
the cost model is transparent + tunable — re-run after any builder button change.
Disposable: advisory tooling; if the builder's surface changes shape, delete this
rather than work around it.
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Grid + tuning constants (Discord: <=5 buttons per row, <=5 rows)
# ---------------------------------------------------------------------------
COLS = 5
MAX_ROWS = 5

# Cost weights — documented judgment, tunable. See module docstring.
P_W = 1.0  # prominence per reading-index unit (top-left = cheapest to find)
T_W = 1.0  # travel weight
ROW_W = 3.0  # a row jump is a bigger eye/thumb move than a column step
COL_W = 1.0
OPEN_COST = 6.0  # opening a grouping submenu ~ crossing 6 index units of friction
LAMBDA_GROUP = 0.6  # keep a function group's buttons contiguous
LAMBDA_CONV = 1.6  # Post -> bottom-right (submit), Back -> bottom-left (convention)
LAMBDA_PIN = 3.0  # a first-screen-pinned button (Style) belongs on row 0


# ---------------------------------------------------------------------------
# Inventory — the live builder buttons (grounded in role_menu_builder.py)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Button:
    key: str
    label: str
    group: str


BUTTONS: list[Button] = [
    # content — what the menu offers / says
    Button("template", "🧩 Template", "content"),
    Button("roles", "🏷️ Roles", "content"),
    Button("packs", "📦 Packs", "content"),
    Button("colours", "🎨 Colours", "content"),
    Button("text", "📝 Text", "content"),
    # appearance — how it looks
    Button("theme", "🎭 Theme", "appearance"),
    Button("style", "🎚️ Style", "appearance"),
    Button("card", "🖼️ Card", "appearance"),
    Button("counts", "📊 Counts", "appearance"),
    # behaviour — assignment rules
    Button("mode", "⚙️ Mode", "behaviour"),
    Button("limit", "🔢 Limit", "behaviour"),
    # placement
    Button("channel", "📍 Channel", "placement"),
    # actions
    Button("post", "🚀 Post", "action"),
    Button("back", "↩ Back", "action"),
]
BY_KEY = {b.key: b for b in BUTTONS}

# Buttons the owner wants VISIBLE ON THE FIRST SCREEN — never folded behind a
# grouping button, and pulled to row 0. Style (dropdown vs buttons) is a primary,
# up-front choice about the menu's whole shape, so it stays first-screen even
# though the RSVP template pre-sets it (owner directive, 2026-07-01).
PINNED_FIRST_SCREEN: set[str] = {"style"}

# The CURRENT live layout (row-by-row, mirrors the decorators' row= values).
CURRENT_LAYOUT: list[list[str]] = [
    ["text", "roles", "colours", "packs", "template"],  # row 0
    ["theme", "mode", "style", "limit", "channel"],  # row 1
    ["card", "counts", "post", "back"],  # row 2
]


# ---------------------------------------------------------------------------
# Journeys — weighted operator tasks (ordered fine-grained button presses)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Journey:
    name: str
    weight: float
    presses: tuple[str, ...]


JOURNEYS: list[Journey] = [
    # The owner's headline case: an RSVP poll. The Event RSVP template pre-sets
    # style=buttons, mode=unique, counts=on, so those are NOT tapped here.
    Journey("rsvp_event", 0.24, ("template", "packs", "channel", "post")),
    Journey("rsvp_quick", 0.06, ("template", "packs", "post")),
    # Non-RSVP self-role menus: dropdown-vs-buttons is a real up-front choice, so
    # Style IS tapped here (owner: Style belongs on the first screen, 2026-07-01).
    Journey("colour_roles", 0.15, ("template", "colours", "style", "post")),
    Journey("game_roles", 0.14, ("template", "roles", "style", "text", "post")),
    Journey("notification_roles", 0.12, ("template", "packs", "post")),
    Journey("verify_gate", 0.06, ("template", "roles", "post")),
    # The rare power-user path that actually touches every knob.
    Journey(
        "custom_advanced",
        0.09,
        ("text", "roles", "style", "mode", "limit", "theme", "channel", "post"),
    ),
    # Edit an existing menu: reopen, tweak the roles (the common edit), Save(=post).
    Journey("edit_tweak", 0.14, ("roles", "post")),
]
if abs(sum(j.weight for j in JOURNEYS) - 1.0) >= 1e-9:  # pragma: no cover - guard
    raise ValueError("journey weights must sum to 1")


# ---------------------------------------------------------------------------
# Function-set variants — fold rarely-used buttons behind one grouping button.
# fold maps a fine-grained key -> the top-level button actually on the grid.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Variant:
    name: str
    buttons: tuple[str, ...]  # top-level keys placed on the grid
    fold: dict[str, str] = field(default_factory=dict)  # pressed key -> grid key
    labels: dict[str, str] = field(default_factory=dict)  # grid key -> label

    def grid_key(self, pressed: str) -> str:
        return self.fold.get(pressed, pressed)

    def label_of(self, key: str) -> str:
        if key in self.labels:
            return self.labels[key]
        return BY_KEY[key].label

    def group_of(self, key: str) -> str:
        if key in BY_KEY:
            return BY_KEY[key].group
        return "grouped"


def _base_variant() -> Variant:
    return Variant("base(14)", tuple(b.key for b in BUTTONS))


def _folded_variant(name: str, folds: dict[str, tuple[str, str, list[str]]]) -> Variant:
    """Build a variant that folds groups of fine buttons behind grouping buttons.

    folds: new_key -> (label, group, [member fine keys folded into it]).
    """
    fold_map: dict[str, str] = {}
    labels: dict[str, str] = {}
    folded_members = set()
    for new_key, (label, _group, members) in folds.items():
        labels[new_key] = label
        for m in members:
            if m in PINNED_FIRST_SCREEN:
                continue  # a first-screen-pinned button is never folded
            fold_map[m] = new_key
            folded_members.add(m)
    top = [b.key for b in BUTTONS if b.key not in folded_members]
    top += list(folds.keys())
    return Variant(name, tuple(top), fold_map, labels)


VARIANTS: list[Variant] = [
    _base_variant(),
    # Fold the two cosmetic buttons hardly anyone taps (Card, Theme) behind "Look".
    _folded_variant(
        "fold_look",
        {"look": ("🎨 Look", "appearance", ["theme", "card"])},
    ),
    # Fold the two assignment-rule buttons behind "Rules".
    _folded_variant(
        "fold_rules",
        {"rules": ("⚙️ Rules", "behaviour", ["mode", "limit"])},
    ),
    # Both of the above.
    _folded_variant(
        "fold_look_rules",
        {
            "look": ("🎨 Look", "appearance", ["theme", "card"]),
            "rules": ("⚙️ Rules", "behaviour", ["mode", "limit"]),
        },
    ),
    # Aggressive: one "Advanced" button hides the rarely-tapped knobs so the top
    # level is the hot path only. Style is PINNED first-screen, so it is NOT folded
    # here even though it is listed (the fold-builder skips pinned members).
    _folded_variant(
        "lean_advanced",
        {
            "advanced": (
                "⚙️ Advanced",
                "appearance",
                ["theme", "card", "counts", "style", "mode", "limit"],
            ),
        },
    ),
]


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------
def positions(layout: list[list[str]]) -> dict[str, tuple[int, int]]:
    pos: dict[str, tuple[int, int]] = {}
    for r, row in enumerate(layout):
        for c, key in enumerate(row):
            pos[key] = (r, c)
    return pos


def reading_index(pos: tuple[int, int]) -> int:
    return pos[0] * COLS + pos[1]


def valid(layout: list[list[str]]) -> bool:
    return len(layout) <= MAX_ROWS and all(len(r) <= COLS for r in layout)


def _submenu_grid_sequence(
    journey: Journey,
    variant: Variant,
) -> list[tuple[str, bool]]:
    """Collapse a journey to the sequence of GRID taps, marking submenu opens.

    A pressed key folded behind a grouping button becomes a tap on that grouping
    button (is_submenu=True); consecutive presses that stay inside the same
    submenu don't re-open it.
    """
    seq: list[tuple[str, bool]] = []
    for pressed in journey.presses:
        gk = variant.grid_key(pressed)
        is_sub = gk != pressed
        if is_sub and seq and seq[-1][0] == gk:
            continue  # already inside that submenu
        seq.append((gk, is_sub))
    return seq


def journey_cost(
    journey: Journey,
    variant: Variant,
    pos: dict[str, tuple[int, int]],
) -> float:
    seq = _submenu_grid_sequence(journey, variant)
    cost = 0.0
    prev = (0, 0)  # eye starts at the top-left of the button block
    for gk, is_sub in seq:
        p = pos[gk]
        # Post/Back are colour-coded anchors (green = submit) the operator learns
        # once, so they don't pay find-from-scratch prominence — the convention
        # penalty places them in their submit/back corners instead. Everything
        # else pays prominence by reading index (top-left = found fastest).
        if variant.group_of(gk) != "action":
            cost += P_W * reading_index(p)
        cost += T_W * (ROW_W * abs(p[0] - prev[0]) + COL_W * abs(p[1] - prev[1]))
        if is_sub:
            cost += OPEN_COST
        prev = p
    return cost


def group_penalty(variant: Variant, pos: dict[str, tuple[int, int]]) -> float:
    """Penalise a function group whose buttons are scattered (non-contiguous)."""
    groups: dict[str, list[int]] = {}
    for key in variant.buttons:
        groups.setdefault(variant.group_of(key), []).append(reading_index(pos[key]))
    pen = 0.0
    for _g, idxs in groups.items():
        if len(idxs) <= 1:
            continue
        span = max(idxs) - min(idxs)
        pen += span - (len(idxs) - 1)  # 0 when perfectly contiguous
    return pen


def pin_penalty(pos: dict[str, tuple[int, int]]) -> float:
    """First-screen-pinned buttons (Style) belong on row 0 (owner directive)."""
    return float(sum(pos[k][0] for k in PINNED_FIRST_SCREEN if k in pos))


def convention_penalty(
    variant: Variant,
    layout: list[list[str]],
    pos: dict[str, tuple[int, int]],
) -> float:
    """Post belongs bottom-right (submit); Back bottom-left (convention)."""
    pen = 0.0
    last_row = len(layout) - 1
    if "post" in pos:
        r, c = pos["post"]
        pen += (last_row - r) + (COLS - 1 - c)
    if "back" in pos:
        r, c = pos["back"]
        pen += (last_row - r) + c
    return pen


def total_cost(variant: Variant, layout: list[list[str]]) -> float:
    pos = positions(layout)
    cost = sum(j.weight * journey_cost(j, variant, pos) for j in JOURNEYS)
    cost += LAMBDA_GROUP * group_penalty(variant, pos)
    cost += LAMBDA_CONV * convention_penalty(variant, layout, pos)
    cost += LAMBDA_PIN * pin_penalty(pos)
    return cost


def mean_taps(variant: Variant) -> float:
    """Weighted mean number of GRID taps per journey (a plain, model-free stat)."""
    return sum(j.weight * len(_submenu_grid_sequence(j, variant)) for j in JOURNEYS)


# ---------------------------------------------------------------------------
# Search — seeded simulated annealing over row layouts
# ---------------------------------------------------------------------------
def _rows_for(n: int) -> int:
    return min(MAX_ROWS, math.ceil(n / COLS))


def _random_layout(keys: list[str], rng: random.Random) -> list[list[str]]:
    ks = keys[:]
    rng.shuffle(ks)
    rows = _rows_for(len(ks))
    layout: list[list[str]] = [[] for _ in range(rows)]
    for i, k in enumerate(ks):
        layout[i % rows].append(k)  # round-robin keeps rows balanced + <=COLS
    return [r for r in layout if r]


def _neighbour(layout: list[list[str]], rng: random.Random) -> list[list[str]]:
    new = [row[:] for row in layout]
    flat = [(r, c) for r, row in enumerate(new) for c in range(len(row))]
    move = rng.random()
    if move < 0.6 and len(flat) >= 2:
        (r1, c1), (r2, c2) = rng.sample(flat, 2)
        new[r1][c1], new[r2][c2] = new[r2][c2], new[r1][c1]
    else:
        r1, c1 = rng.choice(flat)
        key = new[r1].pop(c1)
        tgt = rng.randrange(len(new))
        if len(new[tgt]) >= COLS:
            tgt = r1
        new[tgt].insert(rng.randint(0, len(new[tgt])), key)
        new = [r for r in new if r]
    return new if valid(new) else layout


def optimise(variant: Variant, seed: int, iters: int) -> tuple[list[list[str]], float]:
    rng = random.Random(seed)
    best_layout: list[list[str]] | None = None
    best_cost = math.inf
    keys = list(variant.buttons)
    for restart in range(4):
        cur = _random_layout(keys, random.Random(seed + restart * 101))
        cur_cost = total_cost(variant, cur)
        t = 3.0
        for i in range(iters):
            t = 3.0 * (1.0 - i / iters) + 0.01
            cand = _neighbour(cur, rng)
            cc = total_cost(variant, cand)
            if cc < cur_cost or rng.random() < math.exp((cur_cost - cc) / max(t, 1e-6)):
                cur, cur_cost = cand, cc
            if cur_cost < best_cost:
                best_layout, best_cost = [r[:] for r in cur], cur_cost
    if best_layout is None:  # pragma: no cover - always set on the first iteration
        raise RuntimeError("optimise: no layout found")
    return best_layout, best_cost


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render(variant: Variant, layout: list[list[str]]) -> str:
    lines = []
    for r, row in enumerate(layout):
        cells = " ".join(f"[{variant.label_of(k)}]" for k in row)
        lines.append(f"    row {r}: {cells}")
    return "\n".join(lines)


def journey_table(
    variant: Variant,
    layout: list[list[str]],
) -> list[tuple[str, float, int, float]]:
    pos = positions(layout)
    rows = []
    for j in JOURNEYS:
        rows.append(
            (
                j.name,
                j.weight,
                len(_submenu_grid_sequence(j, variant)),
                journey_cost(j, variant, pos),
            ),
        )
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Role-menu builder layout simulation.")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--iters", type=int, default=12000)
    args = parser.parse_args()

    print("=" * 78)
    print("ROLE-MENU BUILDER — BUTTON-LAYOUT SIMULATION")
    print(f"inventory: {len(BUTTONS)} buttons · {len(JOURNEYS)} weighted journeys")
    print(
        f"grid: <={COLS}/row, <={MAX_ROWS} rows · seed={args.seed} iters={args.iters}",
    )
    print("=" * 78)

    base = VARIANTS[0]
    cur_cost = total_cost(base, CURRENT_LAYOUT)
    print("\nCURRENT live layout:")
    print(render(base, CURRENT_LAYOUT))
    print(f"    cost = {cur_cost:.2f}   mean grid-taps/journey = {mean_taps(base):.2f}")

    print("\nOptimising each function-set variant (lower cost = better):\n")
    print(
        f"  {'variant':<16} {'top-btns':<9} {'best cost':<11} {'vs current':<11} mean-taps",
    )
    results = []
    for v in VARIANTS:
        layout, cost = optimise(v, args.seed, args.iters)
        results.append((v, layout, cost))
        delta = (cost - cur_cost) / cur_cost * 100.0
        print(
            f"  {v.name:<16} {len(v.buttons):<9} {cost:<11.2f} "
            f"{delta:+6.1f}%     {mean_taps(v):.2f}",
        )

    results.sort(key=lambda t: t[2])
    win_v, win_layout, win_cost = results[0]

    print("\n" + "=" * 78)
    print("RECOMMENDATION")
    print("=" * 78)
    improve = (cur_cost - win_cost) / cur_cost * 100.0
    print(
        f"\n  Best: '{win_v.name}'  —  cost {win_cost:.2f} "
        f"({improve:+.1f}% vs current {cur_cost:.2f})\n",
    )
    print(render(win_v, win_layout))
    print("\n  per-journey cost (winner vs current base layout):\n")
    print(f"    {'journey':<20} {'weight':<7} {'taps':<5} {'winner':<9} current")
    cur_pos_v = base
    cur_rows = journey_table(cur_pos_v, CURRENT_LAYOUT)
    win_rows = journey_table(win_v, win_layout)
    cur_by = {r[0]: r for r in cur_rows}
    for name, w, taps, wc in win_rows:
        cc = cur_by.get(name, (name, w, taps, float("nan")))[3]
        print(f"    {name:<20} {w:<7.2f} {taps:<5} {wc:<9.2f} {cc:.2f}")

    # Also surface the best pure-placement result (base function set) — the
    # low-risk change (just reorder), separate from any function folding.
    base_layout, base_cost = optimise(base, args.seed, args.iters)
    print("\n  Low-risk option (keep all 14 buttons, only re-order):")
    print(
        f"    cost {base_cost:.2f} ({(cur_cost - base_cost) / cur_cost * 100:+.1f}% vs current)",
    )
    print(render(base, base_layout))

    print(
        "\n  NOTE: 'optimal' reflects the journey weights + cost model above "
        "(documented,\n  tunable). Re-run with --seed/--iters to confirm the "
        "winner is stable.",
    )


if __name__ == "__main__":
    main()
