"""views.blackjack — game views + PvP/tournament orchestration (S4.5).

Extracted from cogs/blackjack_cog.py during S4.5.

Modules:
    embeds            — _game_embed, _tourn_embed, _update_tourn_embed
    solo_view         — BlackjackView (solo + PvP hand)
    pvp_view          — _ChallengeView, _start_pvp, _resolve_pvp
    tournament_views  — _TournRegistrationView, _TournBlackjackView,
                        _start_tourn_round, _check_tourn_done

All views in this package are ephemeral (no PersistentView,
no @register) — blackjack panels are spawned by !blackjack /
!bjtournament and tied to the invocation's message lifecycle.

The cog (cogs/blackjack_cog.py) imports these names at module top so
discord.py's view registry sees them during command dispatch.  Tests
that import view classes from cogs/blackjack_cog rely on re-exports
maintained there.
"""

from __future__ import annotations

from views.blackjack.embeds import _game_embed, _tourn_embed, _update_tourn_embed
from views.blackjack.pvp_view import _ChallengeView, _resolve_pvp, _start_pvp
from views.blackjack.solo_view import BlackjackView
from views.blackjack.tournament_views import (
    _check_tourn_done,
    _start_tourn_round,
    _TournBlackjackView,
    _TournRegistrationView,
)

__all__ = [
    "BlackjackView",
    "_ChallengeView",
    "_TournBlackjackView",
    "_TournRegistrationView",
    "_check_tourn_done",
    "_game_embed",
    "_resolve_pvp",
    "_start_pvp",
    "_start_tourn_round",
    "_tourn_embed",
    "_update_tourn_embed",
]
