"""Counting MessageStage — §3.2 migration of counting_cog.on_message.

Wraps the V/M/A coordinator body (renamed to
``CountingCog._process_counting_message``) as a
:class:`core.runtime.message_pipeline.MessageStage`.  The cog
registers an instance in ``cog_load`` and unregisters on
``cog_unload`` for hot-reload safety.

Order: 10.  Per plan §3.2, counting sits in the *moderation* tier
alongside cleanup and chain.  Each can short-circuit the pipeline
on delete — once the message is gone, downstream stages (XP,
rps_tournament) skip it.

The stage holds a cog reference because the counting state
(``count_data``, the per-channel scope locks) is per-instance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.runtime.message_pipeline import (
    MessagePipelineContext,
    StageResult,
)

if TYPE_CHECKING:
    from cogs.counting_cog import CountingCog


COUNTING_STAGE_NAME = "counting"
COUNTING_STAGE_ORDER = 10


class CountingStage:
    """Validate counts in active channels; short-circuit on rule violation.

    Auto-mod tier (order=10).  Returns
    ``StageResult(deleted=True, short_circuit=True)`` when the count
    was invalid and the message was deleted, so XP/game stages skip
    a message that's gone.  Returns an empty result for valid counts
    and for messages outside any active counting channel.
    """

    name = COUNTING_STAGE_NAME
    order = COUNTING_STAGE_ORDER

    def __init__(self, cog: CountingCog):
        self.cog = cog

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        deleted = await self.cog._process_counting_message(ctx.message)
        if deleted:
            return StageResult(deleted=True, short_circuit=True)
        return StageResult()
