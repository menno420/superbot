"""Tests for the RpsTournamentStage migration (§3.2).

The stage is a thin wrapper: it delegates to the cog's
``_process_tournament_message`` and never short-circuits or returns
a moderation_action.  Tests focus on the wrapper contract; the
underlying tournament-state logic is exercised by the existing
rps_tournament integration tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.rps_tournament._stage import (
    RPS_STAGE_NAME,
    RPS_STAGE_ORDER,
    RpsTournamentStage,
)
from core.runtime.message_pipeline import MessagePipelineContext


class TestRpsTournamentStage:
    def test_metadata(self):
        cog = MagicMock()
        stage = RpsTournamentStage(cog)
        assert stage.name == RPS_STAGE_NAME == "rps_tournament"
        assert stage.order == RPS_STAGE_ORDER == 30

    @pytest.mark.asyncio
    async def test_process_delegates_to_cog(self):
        cog = MagicMock()
        cog._process_tournament_message = AsyncMock()
        stage = RpsTournamentStage(cog)
        message = MagicMock()
        ctx = MessagePipelineContext(bot=MagicMock(), message=message)

        result = await stage.process(ctx)

        cog._process_tournament_message.assert_awaited_once_with(message)
        # Stage never short-circuits or marks deletion — game-input tier.
        assert result.deleted is False
        assert result.short_circuit is False
        assert result.moderation_action is None
