"""XP MessageStage — §3.2 migration of xp_cog.on_message.

Wraps the existing ``cogs.xp.listener.handle_message`` body as a
:class:`core.runtime.message_pipeline.MessageStage`.  The cog
registers an instance of this class in ``cog_load`` and unregisters
on ``cog_unload`` so hot reloads remain clean.

Order: 20.  Per the plan §3.2, XP runs in the *rewards* tier (after
*moderation* at order=10).  This means once auto-mod stages migrate,
XP will no longer reward a message that was deleted by an upstream
stage in the same dispatch — that's the intended behavior shift.

In this PR only XP has migrated, so order=20 has no other neighbors;
the value is set per the plan so future migrations slot in without
re-numbering.
"""

from __future__ import annotations

from core.runtime.message_pipeline import (
    MessagePipelineContext,
    StageResult,
)

XP_STAGE_NAME = "xp"
XP_STAGE_ORDER = 20


class XpStage:
    """Awards XP for non-bot guild messages.

    No deletion, no short-circuit, no moderation_action — XP is a
    pure reward stage.
    """

    name = XP_STAGE_NAME
    order = XP_STAGE_ORDER

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        from cogs.xp.listener import handle_message

        await handle_message(ctx.bot, ctx.message)
        return StageResult()
