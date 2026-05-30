"""Tests for the CountingStage migration (§3.2).

Stage wrapper contract:
  - delete → short_circuit + deleted flags
  - no-delete → empty result
  - delegates to cog._process_counting_message
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.counting._stage import (
    COUNTING_STAGE_NAME,
    COUNTING_STAGE_ORDER,
    CountingStage,
)
from core.runtime.message_pipeline import MessagePipelineContext


class TestCountingStage:
    def test_metadata(self):
        stage = CountingStage(MagicMock())
        assert stage.name == COUNTING_STAGE_NAME == "counting"
        assert stage.order == COUNTING_STAGE_ORDER == 15

    @pytest.mark.asyncio
    async def test_delete_short_circuits(self):
        cog = MagicMock()
        cog._process_counting_message = AsyncMock(return_value=True)
        stage = CountingStage(cog)
        ctx = MessagePipelineContext(bot=MagicMock(), message=MagicMock())

        result = await stage.process(ctx)

        assert result.deleted is True
        assert result.short_circuit is True
        assert result.moderation_action is None

    @pytest.mark.asyncio
    async def test_no_delete_passes_through(self):
        cog = MagicMock()
        cog._process_counting_message = AsyncMock(return_value=False)
        stage = CountingStage(cog)
        ctx = MessagePipelineContext(bot=MagicMock(), message=MagicMock())

        result = await stage.process(ctx)

        assert result.deleted is False
        assert result.short_circuit is False

    @pytest.mark.asyncio
    async def test_delegates_message_to_cog(self):
        cog = MagicMock()
        cog._process_counting_message = AsyncMock(return_value=False)
        stage = CountingStage(cog)
        message = MagicMock()
        ctx = MessagePipelineContext(bot=MagicMock(), message=message)

        await stage.process(ctx)

        cog._process_counting_message.assert_awaited_once_with(message)
