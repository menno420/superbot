#!/usr/bin/env python3
"""
Casino / card-games design simulation.

The owner asked, before building, to "research which games would be playable in
Discord, how they will work, what the interaction style would be, maybe run a
simulator to find out which games would be appealing". This script answers both
halves:

1. A **design scorecard** for casino game candidates against the constraints
   that actually decide whether a game works *on Discord specifically*:

     * group_fit       -- can ≥3 people meaningfully play one table at once?
     * private_info    -- does each player need a private hand only they see?
                          (this is the whole reason for per-player EPHEMERAL
                          auto-updating messages — the feature the owner wants)
     * simultaneity    -- can players act at the same time, or is it strict
                          turn-by-turn? (Discord rewards parallel action)
     * latency_safe    -- is it free of sub-second reflex windows? (Discord's
                          edit→render→click→receive round-trip makes twitch
                          games unfair — see fishing_minigame_sim.py)
     * depth           -- is there skill / decision depth, or is it a pure dice
                          roll? (roll-only games get boring fast)
     * impl_cost       -- how much correct logic must we get right (hand
                          evaluation, side pots, wheel math, ...)?

   The scorecard is the reasoning behind picking **Texas Hold'em** as the first
   table game: it is the rare game that is high on *every* Discord-favouring
   axis (group, private info, betting-driven near-simultaneous action, no reflex
   windows, deep) — so it justifies the per-player ephemeral table framework,
   which then makes roulette / other games cheap to add on top.

2. A **Monte-Carlo validation** of the actual shipped poker engine
   (`utils.poker.engine`): play thousands of random hands and check the
   invariants a real money(ish) game must hold — chips are conserved every hand,
   pots are always awarded, side pots resolve — and report the hand-category
   frequencies so they can be eye-checked against known poker odds (e.g. a flush
   shows up ~3% of 7-card showdowns, a pair is the plurality, etc.). If the
   engine were wrong, this is where it shows.

Run:  python3.10 tools/sim/casino_games_sim.py
      python3.10 tools/sim/casino_games_sim.py --hands 20000 --seed 1

Pure stdlib + the repo's own pure poker domain. No Discord, no DB, no network.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from collections import Counter
from dataclasses import dataclass

# Allow running as a plain script: add disbot/ to the path so `utils.*` resolves.
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO, "disbot"))

from utils.poker.engine import Action, Player, PokerGame  # noqa: E402
from utils.poker.evaluate import HandCategory, best_hand  # noqa: E402

# --------------------------------------------------------------------------- #
# Part 1 — design scorecard
# --------------------------------------------------------------------------- #


@dataclass
class GameCandidate:
    name: str
    group_fit: int  # 0..5
    private_info: int  # 0..5 (how much it benefits from per-player ephemerals)
    simultaneity: int  # 0..5
    latency_safe: int  # 0..5
    depth: int  # 0..5
    impl_cost: int  # 0..5 (5 = expensive — penalised)
    note: str

    @property
    def score(self) -> int:
        # impl_cost is a cost, so it subtracts. The other five are all
        # Discord-favouring virtues.
        return (
            self.group_fit
            + self.private_info
            + self.simultaneity
            + self.latency_safe
            + self.depth
            - self.impl_cost
        )


CANDIDATES = [
    GameCandidate(
        "Texas Hold'em poker",
        5,
        5,
        4,
        5,
        5,
        4,
        "Marquee. Private hole cards => per-player ephemeral. Betting drives "
        "fast, near-simultaneous reads. Cost is hand-eval + side pots (both pure "
        "+ testable). The framework it needs makes every other game cheap.",
    ),
    GameCandidate(
        "Blackjack (multiplayer table)",
        4,
        3,
        5,
        5,
        3,
        2,
        "Everyone vs the dealer, all decide at once => great simultaneity. Already "
        "have a solo blackjack engine to reuse. Good *second* table game.",
    ),
    GameCandidate(
        "Roulette",
        5,
        1,
        5,
        5,
        2,
        1,
        "Pure simultaneous betting on a shared wheel — no private info, so a "
        "shared public board works; cheapest add once the table framework exists.",
    ),
    GameCandidate(
        "Five-card draw poker",
        4,
        5,
        3,
        5,
        4,
        4,
        "Also private-hand + betting, but the draw/exchange step adds turns and "
        "UI for less payoff than Hold'em. Defer.",
    ),
    GameCandidate(
        "Baccarat",
        4,
        0,
        5,
        5,
        1,
        1,
        "Public hands, fixed draw rules => almost no decisions. Roll-ish; low "
        "depth. Cheap filler at best.",
    ),
    GameCandidate(
        "War / high-card",
        3,
        1,
        5,
        5,
        0,
        1,
        "Zero decisions — pure variance. Fun for 30s. Not worth a slot.",
    ),
    GameCandidate(
        "Liar's dice / poker dice",
        4,
        4,
        3,
        5,
        4,
        3,
        "Private dice + bluffing maps well to ephemerals, but turn-based bidding "
        "and a niche ruleset. A possible later surprise.",
    ),
]


def print_scorecard() -> None:
    print("=" * 78)
    print("CASINO GAME DESIGN SCORECARD — fit for Discord group play")
    print("=" * 78)
    print(
        f"{'game':28} {'grp':>3} {'priv':>4} {'sim':>3} {'lat':>3} "
        f"{'dep':>3} {'cost':>4} {'=':>5}",
    )
    print("-" * 78)
    for c in sorted(CANDIDATES, key=lambda c: c.score, reverse=True):
        print(
            f"{c.name:28} {c.group_fit:>3} {c.private_info:>4} {c.simultaneity:>3} "
            f"{c.latency_safe:>3} {c.depth:>3} {c.impl_cost:>4} {c.score:>5}",
        )
    print("-" * 78)
    print(
        "Legend: grp=group fit  priv=benefit from private ephemerals  sim=simultaneity",
    )
    print("        lat=latency-safe  dep=decision depth  cost=impl cost (subtracted)")
    print()
    top = max(CANDIDATES, key=lambda c: c.score)
    print(f"WINNER → {top.name}  (score {top.score})")
    print(f"  {top.note}")
    print()
    print("Notes on the rest:")
    for c in sorted(CANDIDATES, key=lambda c: c.score, reverse=True)[1:]:
        print(f"  • {c.name}: {c.note}")
    print()


# --------------------------------------------------------------------------- #
# Part 2 — Monte-Carlo validation of the real poker engine
# --------------------------------------------------------------------------- #


def _auto_act(game: PokerGame, rng: random.Random) -> None:
    """A simple bot policy: mostly call/check, sometimes raise, rarely fold."""
    actions = game.legal_actions()
    if not actions:
        return
    roll = rng.random()
    if "raise" in actions and roll < 0.20 and isinstance(actions["raise"], dict):
        spec = actions["raise"]
        lo, hi = int(spec["min"]), int(spec["max"])
        game.act(Action.RAISE, raise_to=rng.randint(lo, hi))
    elif "check" in actions:
        # Occasionally fold even when free, to exercise fold paths.
        if roll > 0.97:
            game.act(Action.FOLD)
        else:
            game.act(Action.CHECK)
    elif "call" in actions:
        if roll > 0.85:
            game.act(Action.FOLD)
        else:
            game.act(Action.CALL)
    else:
        game.act(Action.FOLD)


def simulate(hands: int, seed: int) -> None:
    rng = random.Random(seed)
    n_players = 4
    start_stack = 200
    showdowns = 0
    uncontested = 0
    pot_total = 0
    cat_counter: Counter[HandCategory] = Counter()
    conservation_failures = 0
    total_hands_played = 0

    for _ in range(hands):
        players = [
            Player(user_id=i + 1, name=f"P{i + 1}", stack=start_stack)
            for i in range(n_players)
        ]
        game = PokerGame(players, small_blind=1, big_blind=2, button=0, rng=rng)
        # Total chips in the system = stacks + pot. Measure before the deal (pot
        # is 0), then after (pot fully distributed back into stacks) — they must
        # match exactly, every hand.
        chips_before = sum(p.stack for p in game.players)
        # Fresh full stacks every loop, so begin_hand always has enough funded
        # players — no guard needed.
        game.begin_hand()

        guard = 0
        while not game.is_hand_over and guard < 200:
            guard += 1
            _auto_act(game, rng)

        if not game.is_hand_over:
            conservation_failures += 1  # stuck hand == a bug
            continue

        total_hands_played += 1
        chips_after = sum(p.stack for p in game.players)
        if chips_after != chips_before:
            conservation_failures += 1

        pot_total += sum(r.amount for r in game.results)
        if any(r.hand_label for r in game.results):
            showdowns += 1
        else:
            uncontested += 1

        # Sample showdown hand categories (everyone who saw the river).
        if len(game.board) == 5:
            for p in game.players:
                if p.in_hand:
                    cat_counter[best_hand(p.hole + game.board).category] += 1

    print("=" * 78)
    print(f"POKER ENGINE MONTE-CARLO  ({total_hands_played} hands, {n_players}-handed)")
    print("=" * 78)
    print(
        f"  chip-conservation failures : {conservation_failures}  "
        f"({'PASS ✅' if conservation_failures == 0 else 'FAIL ❌'})",
    )
    print(f"  showdowns                  : {showdowns}")
    print(f"  won uncontested (folds)    : {uncontested}")
    if total_hands_played:
        print(
            f"  avg pot                    : {pot_total / total_hands_played:.1f} chips",
        )
    print()
    if cat_counter:
        total_cats = sum(cat_counter.values())
        print("  Showdown hand frequencies (eye-check vs known 7-card poker odds):")
        for cat in sorted(HandCategory, key=int, reverse=True):
            n = cat_counter.get(cat, 0)
            pct = 100 * n / total_cats
            print(f"    {cat.label:18} {pct:6.2f}%")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hands", type=int, default=5000, help="hands to simulate")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print_scorecard()
    simulate(args.hands, args.seed)


if __name__ == "__main__":
    main()
