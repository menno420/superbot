"""Blackjack state — data classes, module dicts, constants.

Canonical home (fleet unit A3) for the blackjack runtime state that the
cog uses, the views import, and the persistence helpers read.  Moved out
of ``cogs/blackjack/_state.py`` so the ``views/blackjack/*`` layer imports
its game state from ``services`` (a legal dependency) instead of reaching
into the cog package — which broke the ``cogs.blackjack ↔ views.blackjack``
import cycle.

``cogs.blackjack._state`` is now a thin re-export shim of this module, so
``cogs.blackjack_cog`` and tests that ``from cogs.blackjack._state import
…`` keep resolving to the *same objects* (module dicts preserve identity
under re-import).

Imports only ``services.blackjack_engine`` (pure card primitives) and
``utils.tournaments`` (TournamentRegistration base class) — no cog imports.

The four data classes here are the natural-key carriers for blackjack
state.  The three module dicts are the runtime owners:

    _active        (user_id, guild_id) → _Game        (any mode)
    _pvp           frozenset({p1,p2})  → _PvPState    (PvP match state)
    _tournaments   guild_id            → _BjTournament (registration state)

Importing this module multiple times preserves identity of the dicts —
mutations from cog code and from views/blackjack/* both go through the
same objects.

Constants prefixed BLACKJACK_*_SUBSYSTEM / VERSION are persisted in
game_state rows (migration 015).  Bumping them requires a migration.
"""

from __future__ import annotations

import discord

from services.blackjack_engine import new_deck as _new_deck
from utils.terminal_guard import SettleOnceMixin
from utils.tournaments import TournamentRegistration

# ---------------------------------------------------------------------------
# Public constants (referenced by cog, views, persistence, and tests)
# ---------------------------------------------------------------------------

FREE_WIN_COINS = 50
TOURN_START_CHIPS = 1000
TOURN_BET_PER_ROUND = 200

BLACKJACK_SOLO_SUBSYSTEM = "blackjack_solo"
BLACKJACK_SOLO_VERSION = 1

BLACKJACK_PVP_SUBSYSTEM = "blackjack_pvp"
BLACKJACK_PVP_VERSION = 1

# P0-1 — escrow subsystem for D1 escrow-at-accept.  One ``{"bet": stake,
# "peer": other_id}`` row per player so the existing ``bet``-keyed
# recovery refunds each player their own stake.  Wagered money moves only
# through ``services.game_wager_workflow``.
BLACKJACK_PVP_ESCROW_SUBSYSTEM = "blackjack_pvp_escrow"
BLACKJACK_PVP_ESCROW_VERSION = 1

BLACKJACK_TOURNAMENT_SUBSYSTEM = "blackjack_tournament"
BLACKJACK_TOURNAMENT_VERSION = 1


# ---------------------------------------------------------------------------
# Game state classes
# ---------------------------------------------------------------------------


class _Game:
    def __init__(
        self,
        user_id: int,
        guild_id: int,
        bet: int,
        tournament_chips: int | None = None,
        *,
        channel_id: int | None = None,
    ):
        self.user_id = user_id
        self.guild_id = guild_id
        self.bet = bet
        self.doubled = False
        self.tournament_chips = tournament_chips  # None = normal game
        self.channel_id = channel_id  # PR G2 — needed for game_state persistence
        self.deck = _new_deck()
        self.player: list[str] = [self.deck.pop(), self.deck.pop()]
        self.dealer: list[str] = [self.deck.pop(), self.deck.pop()]
        # PvP linkage (set externally by _start_pvp)
        self.pvp_peer_id: int | None = None
        self.pvp_state: _PvPState | None = None

    def hit(self) -> str:
        card = self.deck.pop()
        self.player.append(card)
        return card

    def dealer_play(self):
        from services.blackjack_engine import hand_value as _hand_value

        while _hand_value(self.dealer) < 17:
            self.dealer.append(self.deck.pop())


class _PvPState(SettleOnceMixin):
    def __init__(self, p1: int, p2: int, guild_id: int, bet: int, channel_id: int):
        self.p1 = p1
        self.p2 = p2
        self.guild_id = guild_id
        self.bet = bet
        self.channel_id = channel_id
        self.results: dict[int, int] = {}  # user_id → final hand value (-1 = bust)
        self.messages: dict[int, discord.Message] = {}


class _BjTournament(TournamentRegistration, SettleOnceMixin):
    def __init__(
        self,
        host_id: int,
        guild_id: int,
        announce_id: int,
        entry_fee: int,
        rounds: int,
        duration_mins: int,
    ):
        super().__init__(host_id, guild_id, announce_id, entry_fee, duration_mins)
        self.rounds = rounds
        self.results: dict[int, int] = {}  # user_id → final chips
        self.category: discord.CategoryChannel | None = None


class _TournPlayerState:
    def __init__(
        self,
        user_id: int,
        guild_id: int,
        rounds: int,
        *,
        channel_id: int | None = None,
    ):
        self.user_id = user_id
        self.guild_id = guild_id
        self.chips = TOURN_START_CHIPS
        self.rounds_left = rounds
        self.done = False
        # PR G5 — recorded so ``_check_tourn_done`` can clear the
        # persisted entry-fee row precisely without needing a list
        # sweep at natural tournament completion.
        self.channel_id = channel_id


# ---------------------------------------------------------------------------
# Runtime state dicts (mutated by both the cog and views/blackjack/*)
# ---------------------------------------------------------------------------

_active: dict[tuple[int, int], _Game] = {}  # (user_id, guild_id) → game
_pvp: dict[frozenset, _PvPState] = {}  # frozenset({p1, p2}) → state
_tournaments: dict[int, _BjTournament] = {}  # guild_id → tournament
