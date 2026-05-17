"""Tests for core.runtime.message_pipeline (§3.2).

Covers the orchestrator contract:

  - register / unregister / clear (de-dup by name, sort by order)
  - pre-filter (bot author, no-guild) short-circuits before stages run
  - stages run sequentially in `order` (smaller first)
  - short_circuit stops the pipeline
  - exception in a stage is logged + isolated (downstream stages run)
  - moderation_action triggers the routing hook
  - latency metric is observed per (stage, message) regardless of outcome
  - setup(bot) is idempotent
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime import message_pipeline
from core.runtime.message_pipeline import (
    MessagePipelineContext,
    ModerationActionDescriptor,
    StageResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_message(*, is_bot: bool = False, has_guild: bool = True):
    msg = SimpleNamespace()
    msg.id = 12345
    msg.author = SimpleNamespace(bot=is_bot)
    msg.guild = SimpleNamespace(id=1) if has_guild else None
    return msg


@dataclass
class _SpyStage:
    """Hand-rolled stage that records calls + returns a configurable result."""

    name: str
    order: int
    result: StageResult = field(default_factory=StageResult)
    raises: BaseException | None = None
    calls: list[MessagePipelineContext] = field(default_factory=list)

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        self.calls.append(ctx)
        if self.raises is not None:
            raise self.raises
        return self.result


@pytest.fixture(autouse=True)
def _reset_pipeline_state():
    """Reset module-level state between every test."""
    message_pipeline.clear()
    # Also reset the setup() idempotency flag so tests can rebind freely.
    message_pipeline._PLATFORM_LISTENER_INSTALLED = False
    yield
    message_pipeline.clear()
    message_pipeline._PLATFORM_LISTENER_INSTALLED = False


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_register_appends(self):
        s = _SpyStage(name="a", order=10)
        message_pipeline.register(s)
        assert message_pipeline.stages_snapshot() == [s]

    def test_register_dedupes_by_name(self):
        s1 = _SpyStage(name="a", order=10)
        s2 = _SpyStage(name="a", order=20)  # same name, new instance
        message_pipeline.register(s1)
        message_pipeline.register(s2)
        assert message_pipeline.stages_snapshot() == [s2]

    def test_register_sorts_by_order(self):
        s30 = _SpyStage(name="rps", order=30)
        s10 = _SpyStage(name="mod", order=10)
        s20 = _SpyStage(name="xp", order=20)
        message_pipeline.register(s30)
        message_pipeline.register(s10)
        message_pipeline.register(s20)
        assert [s.name for s in message_pipeline.stages_snapshot()] == [
            "mod",
            "xp",
            "rps",
        ]

    def test_unregister_removes(self):
        s = _SpyStage(name="a", order=10)
        message_pipeline.register(s)
        message_pipeline.unregister("a")
        assert message_pipeline.stages_snapshot() == []

    def test_unregister_missing_is_noop(self):
        message_pipeline.unregister("does-not-exist")  # no raise

    def test_clear_drops_all(self):
        message_pipeline.register(_SpyStage(name="a", order=10))
        message_pipeline.register(_SpyStage(name="b", order=20))
        message_pipeline.clear()
        assert message_pipeline.stages_snapshot() == []


# ---------------------------------------------------------------------------
# Pre-filter
# ---------------------------------------------------------------------------


class TestPreFilter:
    @pytest.mark.asyncio
    async def test_bot_author_short_circuits(self):
        s = _SpyStage(name="x", order=10)
        message_pipeline.register(s)
        await message_pipeline.dispatch(MagicMock(), _make_message(is_bot=True))
        assert s.calls == []

    @pytest.mark.asyncio
    async def test_no_guild_short_circuits(self):
        s = _SpyStage(name="x", order=10)
        message_pipeline.register(s)
        await message_pipeline.dispatch(MagicMock(), _make_message(has_guild=False))
        assert s.calls == []


# ---------------------------------------------------------------------------
# Stage iteration
# ---------------------------------------------------------------------------


class TestDispatchOrdering:
    @pytest.mark.asyncio
    async def test_stages_run_in_order_smaller_first(self):
        order_log: list[str] = []

        @dataclass
        class _Recorder:
            name: str
            order: int

            async def process(self, ctx):
                order_log.append(self.name)
                return StageResult()

        message_pipeline.register(_Recorder("c", 30))
        message_pipeline.register(_Recorder("a", 10))
        message_pipeline.register(_Recorder("b", 20))

        await message_pipeline.dispatch(MagicMock(), _make_message())
        assert order_log == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_short_circuit_stops_downstream(self):
        s10 = _SpyStage(name="a", order=10, result=StageResult(short_circuit=True))
        s20 = _SpyStage(name="b", order=20)
        message_pipeline.register(s10)
        message_pipeline.register(s20)

        await message_pipeline.dispatch(MagicMock(), _make_message())
        assert len(s10.calls) == 1
        assert s20.calls == []

    @pytest.mark.asyncio
    async def test_exception_is_isolated(self):
        s10 = _SpyStage(name="a", order=10, raises=RuntimeError("boom"))
        s20 = _SpyStage(name="b", order=20)
        message_pipeline.register(s10)
        message_pipeline.register(s20)

        await message_pipeline.dispatch(MagicMock(), _make_message())
        # Downstream stage still ran despite upstream raising.
        assert len(s20.calls) == 1

    @pytest.mark.asyncio
    async def test_context_is_shared_across_stages(self):
        seen_metadata: list[dict] = []

        @dataclass
        class _A:
            name: str = "a"
            order: int = 10

            async def process(self, ctx):
                ctx.metadata["from_a"] = "hello"
                return StageResult()

        @dataclass
        class _B:
            name: str = "b"
            order: int = 20

            async def process(self, ctx):
                seen_metadata.append(dict(ctx.metadata))
                return StageResult()

        message_pipeline.register(_A())
        message_pipeline.register(_B())
        await message_pipeline.dispatch(MagicMock(), _make_message())
        assert seen_metadata == [{"from_a": "hello"}]


# ---------------------------------------------------------------------------
# Moderation routing
# ---------------------------------------------------------------------------


class TestModerationRouting:
    @pytest.mark.asyncio
    async def test_moderation_action_triggers_hook(self):
        desc = ModerationActionDescriptor(
            action="auto_delete:test",
            target_id=42,
            reason="rule X",
        )
        s = _SpyStage(name="a", order=10, result=StageResult(moderation_action=desc))
        message_pipeline.register(s)

        with patch.object(
            message_pipeline,
            "_route_moderation_action",
        ) as hook:
            await message_pipeline.dispatch(MagicMock(), _make_message())
        hook.assert_called_once()
        # First arg is the message, second is the descriptor.
        assert hook.call_args.args[1] is desc

    @pytest.mark.asyncio
    async def test_no_moderation_action_skips_hook(self):
        s = _SpyStage(name="a", order=10)  # default result, no moderation_action
        message_pipeline.register(s)

        with patch.object(
            message_pipeline,
            "_route_moderation_action",
        ) as hook:
            await message_pipeline.dispatch(MagicMock(), _make_message())
        hook.assert_not_called()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class TestMetrics:
    @pytest.mark.asyncio
    async def test_latency_observed_per_stage(self):
        s = _SpyStage(name="my_stage", order=10)
        message_pipeline.register(s)

        with patch(
            "core.runtime.message_pipeline.metrics.message_pipeline_stage_seconds",
        ) as hist:
            await message_pipeline.dispatch(MagicMock(), _make_message())
        hist.labels.assert_called_once_with(stage="my_stage")
        hist.labels.return_value.observe.assert_called_once()

    @pytest.mark.asyncio
    async def test_latency_observed_even_on_exception(self):
        s = _SpyStage(name="my_stage", order=10, raises=RuntimeError("x"))
        message_pipeline.register(s)

        with patch(
            "core.runtime.message_pipeline.metrics.message_pipeline_stage_seconds",
        ) as hist:
            await message_pipeline.dispatch(MagicMock(), _make_message())
        hist.labels.return_value.observe.assert_called_once()


# ---------------------------------------------------------------------------
# setup(bot)
# ---------------------------------------------------------------------------


class TestSetup:
    def test_registers_listener(self):
        bot = MagicMock()
        bot.listen.return_value = lambda fn: fn  # decorator passthrough
        message_pipeline.setup(bot)
        bot.listen.assert_called_once_with("on_message")

    def test_idempotent(self):
        bot = MagicMock()
        bot.listen.return_value = lambda fn: fn
        message_pipeline.setup(bot)
        message_pipeline.setup(bot)
        # Second call should be a no-op — listener registered only once.
        assert bot.listen.call_count == 1
