"""XP MessageStage — §3.2 migration of xp_cog.on_message.

Wraps the existing ``cogs.xp.listener.handle_message`` body as a
:class:`core.runtime.message_pipeline.MessageStage`.  The cog
registers an instance of this class in ``cog_load`` and unregisters
on ``cog_unload`` so hot reloads remain clean.

Order: 30.  XP runs in the *rewards* tier, after the auto-mod tier
(cleanup=10, counting=15, chain=20), so XP never rewards a message that
an upstream stage deleted in the same dispatch.  See the canonical
stage-order table in ``core/runtime/message_pipeline.py``.
"""

from __future__ import annotations

from core.runtime.message_pipeline import (
    MessagePipelineContext,
    StageResult,
)

XP_STAGE_NAME = "xp"
XP_STAGE_ORDER = 30


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
