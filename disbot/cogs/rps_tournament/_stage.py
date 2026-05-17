"""RPS tournament MessageStage — §3.2 migration of rps_tournament_cog.on_message.

Wraps the tournament-channel message capture (``_process_tournament_message``
on the cog) as a :class:`core.runtime.message_pipeline.MessageStage`.
The cog registers an instance in ``cog_load`` and unregisters on
``cog_unload`` for hot-reload safety.

Order: 30.  Per plan §3.2, RPS sits in the *game_input* tier — after
auto-mod (order=10) and the XP reward stage (order=20).  The stage
never deletes or short-circuits; it's pure capture of player moves
in tournament match channels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.runtime.message_pipeline import (
    MessagePipelineContext,
    StageResult,
)

if TYPE_CHECKING:
    from cogs.rps_tournament_cog import RPSTournamentCog


RPS_STAGE_NAME = "rps_tournament"
RPS_STAGE_ORDER = 30


class RpsTournamentStage:
    """Capture player moves in tournament match channels.

    Game-input tier (order=30).  No deletion, no short-circuit — just
    routes the message to the cog's tournament-state dispatch.

    Holds a cog reference because the tournament state
    (``match_channels``, ``matches``, bot-match dispatch) is
    per-instance on the cog.
    """

    name = RPS_STAGE_NAME
    order = RPS_STAGE_ORDER

    def __init__(self, cog: RPSTournamentCog):
        self.cog = cog

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        await self.cog._process_tournament_message(ctx.message)
        return StageResult()
