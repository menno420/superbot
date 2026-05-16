"""views.rps — Rock-Paper-Scissors panel hierarchy.

Five view classes extracted from cogs/rps_tournament_cog during D4:

    solo_play       _RpsView (single-player game)
    registration    _RpsRegistrationView (tournament join button)
    pvp_challenge   _RpsPvpChallengeView (accept/decline)
    pvp_play        _RpsPvpPlayView (both players pick → resolve)
    move_picker     _RpsMovePickerView (ephemeral per-player picker)

Shared constants + the pending-match registry live in :mod:`_helpers`.

The cog re-exports every view (and the constants) so existing
``from cogs.rps_tournament_cog import …`` imports continue to resolve.
"""

from __future__ import annotations

from views.rps._helpers import _FREE_WIN, _RPS_EMOJI, _RPS_WINS, _rps_pvp_pending
from views.rps.move_picker import _RpsMovePickerView
from views.rps.pvp_challenge import _RpsPvpChallengeView
from views.rps.pvp_play import _RpsPvpPlayView
from views.rps.registration import _RpsRegistrationView
from views.rps.solo_play import _RpsView

__all__ = [
    "_FREE_WIN",
    "_RPS_EMOJI",
    "_RPS_WINS",
    "_RpsMovePickerView",
    "_RpsPvpChallengeView",
    "_RpsPvpPlayView",
    "_RpsRegistrationView",
    "_RpsView",
    "_rps_pvp_pending",
]
