"""Texas Hold'em game engine — pure state machine, Discord-free.

Owns one poker *table* of seated players and drives a hand through its betting
rounds (preflop → flop → turn → river → showdown), including blinds, the
big-blind option, all-ins, and **side pots**.  It holds no Discord objects and
is fully deterministic given a deck — so the betting/pot logic is unit-tested in
isolation and the view layer is a thin renderer over it.

v1 uses **table play-chips**, not the real economy: every seat starts with an
equal stack and chips never leave the table.  Real-coin buy-ins would need
N-party escrow through ``game_wager_workflow`` (a money-safety follow-up), kept
out of v1 on purpose.

Simplification (documented, casual-play): a short all-in that raises the bet by
less than a full ``min_raise`` still reopens the action for players who already
acted.  Strict casino rule caps re-raise rights in that case; the difference
only matters in multi-way all-in re-raise spots and is acceptable for a
play-chip game.

Public API (what the view layer drives)
---------------------------------------
- :class:`PokerGame` — ``begin_hand()``, ``act(...)``, ``legal_actions()``,
  ``to_call()``, ``pot_total``, ``stage``, ``current_player``, ``results``.
- :class:`Player`, :class:`PotResult`, the ``Action`` constants, :class:`Stage`.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from utils.cards import Card, make_deck
from utils.poker.evaluate import HandRank, best_hand

__all__ = [
    "Action",
    "Player",
    "PokerError",
    "PokerGame",
    "PotResult",
    "Stage",
]


class PokerError(RuntimeError):
    """Raised on an illegal action or out-of-turn play."""


class Action(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"


class Stage(str, Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    COMPLETE = "complete"


@dataclass
class Player:
    """A seated player and their per-hand state."""

    user_id: int
    name: str
    stack: int
    hole: list[Card] = field(default_factory=list)
    committed_round: int = 0  # chips in the pot this betting round
    committed_hand: int = 0  # chips in the pot this whole hand (for side pots)
    folded: bool = False
    all_in: bool = False
    acted: bool = False  # has acted since the last aggression this round
    sitting_out: bool = False  # busted (stack 0 at hand start) — rejoins on rebuy

    @property
    def in_hand(self) -> bool:
        """Still contesting the pot (dealt in and not folded)."""
        return not self.folded and not self.sitting_out


@dataclass
class PotResult:
    """One player's winnings from a finished hand."""

    user_id: int
    amount: int
    hand_label: str | None  # the winning hand, or None if won uncontested


class PokerGame:
    """A Texas Hold'em table.  Seats persist across hands; chips move on win."""

    def __init__(
        self,
        players: list[Player],
        *,
        small_blind: int = 1,
        big_blind: int = 2,
        button: int = 0,
        rng: random.Random | None = None,
    ) -> None:
        if len(players) < 2:
            raise PokerError("poker needs at least 2 players")
        self.players = players
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.button = button % len(players)
        self._rng = rng or random.Random()

        self.deck: list[Card] = []
        self.board: list[Card] = []
        self.stage: Stage = Stage.COMPLETE
        self.current: int = -1  # index of player to act, -1 when none
        self.current_bet: int = 0
        self.min_raise: int = big_blind
        self.log: list[str] = []
        self.results: list[PotResult] = []
        self.hand_number: int = 0
        # Players forced all-in by deck (used to suppress reveal of folded hands).
        self._showdown_ranks: dict[int, HandRank] = {}

    # ------------------------------------------------------------------ helpers

    @property
    def pot_total(self) -> int:
        """Total chips in the pot (all rounds combined)."""
        return sum(p.committed_hand for p in self.players)

    @property
    def current_player(self) -> Player | None:
        if self.current < 0 or self.stage in (Stage.SHOWDOWN, Stage.COMPLETE):
            return None
        return self.players[self.current]

    @property
    def is_hand_over(self) -> bool:
        return self.stage == Stage.COMPLETE

    def _seated(self) -> list[int]:
        """Indices of players who can be dealt in (have chips, not sitting out)."""
        return [
            i for i, p in enumerate(self.players) if p.stack > 0 and not p.sitting_out
        ]

    def _next_index(self, start: int, eligible: list[int]) -> int:
        """First index in *eligible* strictly after *start*, cyclically."""
        n = len(self.players)
        for step in range(1, n + 1):
            idx = (start + step) % n
            if idx in eligible:
                return idx
        return start

    def _commit(self, player: Player, amount: int) -> int:
        """Move up to *amount* chips from a stack into the pot.  Returns actual."""
        amount = max(0, min(amount, player.stack))
        player.stack -= amount
        player.committed_round += amount
        player.committed_hand += amount
        if player.stack == 0:
            player.all_in = True
        return amount

    # ------------------------------------------------------------------ dealing

    def begin_hand(self) -> None:
        """Reset state, rotate the button, post blinds, and deal hole cards.

        Players who busted (stack 0) sit out the hand.  Raises
        :class:`PokerError` if fewer than two players can be dealt in — the
        caller should end the table.
        """
        for p in self.players:
            p.hole = []
            p.committed_round = 0
            p.committed_hand = 0
            p.folded = False
            p.all_in = False
            p.acted = False
            p.sitting_out = p.stack <= 0

        contenders = self._seated()
        if len(contenders) < 2:
            raise PokerError("need at least 2 funded players to deal a hand")

        self.hand_number += 1
        # Rotate the button to the next funded seat (skip the very first hand's
        # rotation so the caller's chosen button stands for hand 1).
        if self.hand_number > 1 or self.button not in contenders:
            self.button = self._next_index(self.button, contenders)

        self.deck = make_deck(shuffle=True, rng=self._rng)
        self.board = []
        self.stage = Stage.PREFLOP
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.log = []
        self.results = []
        self._showdown_ranks = {}

        heads_up = len(contenders) == 2
        if heads_up:
            sb_idx = self.button
            bb_idx = self._next_index(self.button, contenders)
        else:
            sb_idx = self._next_index(self.button, contenders)
            bb_idx = self._next_index(sb_idx, contenders)

        self._post_blind(sb_idx, self.small_blind, "small blind")
        self._post_blind(bb_idx, self.big_blind, "big blind")
        self.current_bet = self.big_blind
        self.min_raise = self.big_blind

        # Deal two hole cards to each contender, starting left of the button.
        order = self._deal_order(contenders)
        for _ in range(2):
            for idx in order:
                self.players[idx].hole.append(self.deck.pop())

        # First to act preflop: heads-up the small blind (button) acts first;
        # otherwise the seat left of the big blind.
        first = sb_idx if heads_up else self._next_index(bb_idx, contenders)
        self.current = first
        # The blinds were forced, not voluntary — they still owe action, so leave
        # acted=False for everyone (this is what gives the big blind its option).
        self._skip_to_actionable()

    def _deal_order(self, contenders: list[int]) -> list[int]:
        """Contender indices starting from the seat left of the button."""
        start = self.button
        order: list[int] = []
        idx = start
        for _ in range(len(self.players)):
            idx = self._next_index(idx, contenders)
            order.append(idx)
            if len(order) == len(contenders):
                break
        return order

    def _post_blind(self, idx: int, amount: int, label: str) -> None:
        player = self.players[idx]
        posted = self._commit(player, amount)
        self.log.append(f"{player.name} posts the {label} ({posted}).")

    # --------------------------------------------------------------- actionable

    def _needs_action(self, idx: int) -> bool:
        p = self.players[idx]
        if p.folded or p.all_in or p.sitting_out or p.stack == 0:
            return False
        return (not p.acted) or (p.committed_round < self.current_bet)

    def _voluntary_actors(self) -> list[int]:
        """Players who *can still choose* to act this hand (not folded/all-in)."""
        return [
            i
            for i, p in enumerate(self.players)
            if p.in_hand and not p.all_in and p.stack > 0
        ]

    def _skip_to_actionable(self) -> None:
        """Ensure ``current`` points at someone who must act, else advance state."""
        if self.players[self.current].folded or not self._needs_action(self.current):
            self._advance_to_next_actor(from_idx=self.current, inclusive=True)

    def _advance_to_next_actor(self, *, from_idx: int, inclusive: bool = False) -> None:
        n = len(self.players)
        start = 0 if inclusive else 1
        for step in range(start, n + 1):
            idx = (from_idx + step) % n
            if self._needs_action(idx):
                self.current = idx
                return
        self._end_betting_round()

    # ------------------------------------------------------------------ actions

    def to_call(self, idx: int | None = None) -> int:
        """Chips the given player (default: current) must add to call."""
        if idx is None:
            idx = self.current
        return max(0, self.current_bet - self.players[idx].committed_round)

    def min_raise_to(self) -> int:
        """Smallest legal total a raise can bring the current player to."""
        return self.current_bet + self.min_raise

    def max_raise_to(self) -> int:
        """Largest total (all-in) the current player can commit to this round."""
        p = self.players[self.current]
        return p.committed_round + p.stack

    def legal_actions(self) -> dict[str, object]:
        """Describe the legal actions for the current player (for UI buttons)."""
        if self.current_player is None:
            return {}
        p = self.players[self.current]
        to_call = self.to_call()
        actions: dict[str, object] = {"fold": True}
        if to_call == 0:
            actions["check"] = True
        else:
            actions["call"] = min(to_call, p.stack)
        # Can raise only if there are chips beyond the call.
        if p.stack > to_call:
            actions["raise"] = {
                "min": min(self.min_raise_to(), self.max_raise_to()),
                "max": self.max_raise_to(),
            }
        return actions

    def act(self, action: Action, *, raise_to: int | None = None) -> None:
        """Apply *action* for the current player and advance the game.

        ``raise_to`` is the **total** the player commits this round (their
        existing round contribution plus the new chips), required for
        :attr:`Action.RAISE`.
        """
        if self.current_player is None:
            raise PokerError("no player is to act")
        idx = self.current
        p = self.players[idx]

        if action == Action.FOLD:
            p.folded = True
            p.acted = True
            self.log.append(f"{p.name} folds.")
            # A fold can end the hand outright (one player left).
            if (
                len([i for i in range(len(self.players)) if self.players[i].in_hand])
                == 1
            ):
                self._award_uncontested()
                return
            self._advance_to_next_actor(from_idx=idx)
            return

        if action == Action.CHECK:
            if self.to_call(idx) != 0:
                raise PokerError("cannot check facing a bet")
            p.acted = True
            self.log.append(f"{p.name} checks.")
            self._advance_to_next_actor(from_idx=idx)
            return

        if action == Action.CALL:
            to_call = self.to_call(idx)
            if to_call == 0:
                raise PokerError("nothing to call — check instead")
            paid = self._commit(p, to_call)
            p.acted = True
            tag = " (all-in)" if p.all_in else ""
            self.log.append(f"{p.name} calls {paid}{tag}.")
            self._advance_to_next_actor(from_idx=idx)
            return

        if action == Action.RAISE:
            if raise_to is None:
                raise PokerError("raise requires a target amount")
            self._do_raise(idx, raise_to)
            return

        raise PokerError(f"unknown action: {action!r}")

    def _do_raise(self, idx: int, raise_to: int) -> None:
        p = self.players[idx]
        max_to = self.max_raise_to()
        min_to = min(self.min_raise_to(), max_to)
        if raise_to > max_to:
            raise PokerError("cannot raise more than your stack")
        is_all_in = raise_to == max_to
        if raise_to <= self.current_bet:
            raise PokerError("a raise must exceed the current bet")
        if raise_to < min_to and not is_all_in:
            raise PokerError(f"raise must be at least {min_to}")

        increment = raise_to - self.current_bet
        additional = raise_to - p.committed_round
        self._commit(p, additional)
        self.min_raise = max(self.min_raise, increment)
        self.current_bet = raise_to
        # Re-open the action: everyone else who is still live must respond.
        for j, other in enumerate(self.players):
            if j != idx and other.in_hand and not other.all_in:
                other.acted = False
        p.acted = True
        tag = " (all-in)" if p.all_in else ""
        verb = "bets" if increment == raise_to else "raises to"
        self.log.append(f"{p.name} {verb} {raise_to}{tag}.")
        self._advance_to_next_actor(from_idx=idx)

    # --------------------------------------------------------- round / showdown

    def _end_betting_round(self) -> None:
        self.current = -1
        # Sweep round contributions into the hand total is already tracked via
        # committed_hand; just reset the per-round bookkeeping.
        for p in self.players:
            p.committed_round = 0
            p.acted = False
        self.current_bet = 0
        self.min_raise = self.big_blind

        # If only one player remains un-folded, they win immediately.
        live = [i for i, p in enumerate(self.players) if p.in_hand]
        if len(live) == 1:
            self._award_uncontested()
            return

        # Advance the board / stage.
        if self.stage == Stage.PREFLOP:
            self._deal_board(3)
            self.stage = Stage.FLOP
        elif self.stage == Stage.FLOP:
            self._deal_board(1)
            self.stage = Stage.TURN
        elif self.stage == Stage.TURN:
            self._deal_board(1)
            self.stage = Stage.RIVER
        elif self.stage == Stage.RIVER:
            self._settle_showdown()
            return

        # If at most one player can still voluntarily act (everyone else is
        # all-in), there is no more betting — run the remaining board to showdown.
        if len(self._voluntary_actors()) <= 1:
            self._run_out_and_show()
            return

        # First to act postflop: first live seat left of the button.
        self._advance_to_next_actor(from_idx=self.button, inclusive=False)

    def _deal_board(self, count: int) -> None:
        for _ in range(count):
            self.board.append(self.deck.pop())

    def _run_out_and_show(self) -> None:
        """Deal any remaining community cards, then settle (all-in run-out)."""
        targets = {Stage.PREFLOP: 5, Stage.FLOP: 5, Stage.TURN: 5, Stage.RIVER: 5}
        need = targets.get(self.stage, 5) - len(self.board)
        if need > 0:
            self._deal_board(need)
        self.stage = Stage.RIVER
        self._settle_showdown()

    def _award_uncontested(self) -> None:
        winner_idx = next(i for i, p in enumerate(self.players) if p.in_hand)
        winner = self.players[winner_idx]
        pot = self.pot_total
        winner.stack += pot
        self.results = [PotResult(user_id=winner.user_id, amount=pot, hand_label=None)]
        self.log.append(f"{winner.name} wins {pot} (everyone else folded).")
        self.current = -1
        self.stage = Stage.COMPLETE

    def _settle_showdown(self) -> None:
        self.stage = Stage.SHOWDOWN
        self.current = -1
        contenders = [i for i, p in enumerate(self.players) if p.in_hand]
        ranks: dict[int, HandRank] = {
            i: best_hand(self.players[i].hole + self.board) for i in contenders
        }
        self._showdown_ranks = ranks

        contributions = {
            i: p.committed_hand
            for i, p in enumerate(self.players)
            if p.committed_hand > 0
        }
        winnings: dict[int, int] = defaultdict(int)
        labels: dict[int, str] = {}

        levels = sorted(set(contributions.values()))
        prev = 0
        for level in levels:
            layer = sum(level - prev for c in contributions.values() if c >= level)
            eligible = [i for i in contenders if contributions.get(i, 0) >= level]
            if eligible and layer > 0:
                best_key = max(ranks[i].key for i in eligible)
                winners = [i for i in eligible if ranks[i].key == best_key]
                share, remainder = divmod(layer, len(winners))
                # Odd chips go to the earliest winner(s) left of the button.
                ordered_winners = self._winners_in_order(winners)
                for w in ordered_winners:
                    winnings[w] += share
                    labels[w] = ranks[w].label
                for w in ordered_winners[:remainder]:
                    winnings[w] += 1
            prev = level

        for i, amt in winnings.items():
            self.players[i].stack += amt

        self.results = [
            PotResult(
                user_id=self.players[i].user_id,
                amount=amt,
                hand_label=labels.get(i),
            )
            for i, amt in sorted(winnings.items(), key=lambda kv: -kv[1])
            if amt > 0
        ]
        for res in self.results:
            name = next(p.name for p in self.players if p.user_id == res.user_id)
            self.log.append(f"{name} wins {res.amount} with {res.hand_label}.")
        self.stage = Stage.COMPLETE

    def _winners_in_order(self, winners: list[int]) -> list[int]:
        """Order winning indices starting from the first seat left of the button."""
        n = len(self.players)
        return sorted(winners, key=lambda i: (i - self.button - 1) % n)

    def showdown_rank(self, user_id: int) -> HandRank | None:
        """The evaluated hand for *user_id* at showdown (None if not shown)."""
        for i, p in enumerate(self.players):
            if p.user_id == user_id:
                return self._showdown_ranks.get(i)
        return None
