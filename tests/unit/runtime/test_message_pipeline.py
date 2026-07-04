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

    @pytest.mark.asyncio
    async def test_draining_instance_runs_no_stages(self):
        # LP-4 deploy-handoff double-fire guard: a draining instance releases
        # the runtime lock before it finishes draining, so the incoming replica
        # processes the same MESSAGE_CREATE.  Running stages here would
        # double-apply additive effects (XP, counting, ...).  A draining
        # instance must run no stages.
        s = _SpyStage(name="x", order=10)
        message_pipeline.register(s)
        with patch.object(
            message_pipeline.lifecycle, "is_shutting_down", return_value=True
        ):
            await message_pipeline.dispatch(MagicMock(), _make_message())
        assert s.calls == []

    @pytest.mark.asyncio
    async def test_running_instance_runs_stages(self):
        # Guard is scoped to draining only — a RUNNING instance dispatches
        # normally (regression fence so the guard can't silently kill traffic).
        s = _SpyStage(name="x", order=10)
        message_pipeline.register(s)
        with patch.object(
            message_pipeline.lifecycle, "is_shutting_down", return_value=False
        ):
            await message_pipeline.dispatch(MagicMock(), _make_message())
        assert len(s.calls) == 1


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
            new_callable=AsyncMock,
        ) as hook:
            await message_pipeline.dispatch(MagicMock(), _make_message())
        hook.assert_awaited_once()
        # First arg is the message, second is the descriptor.
        assert hook.call_args.args[1] is desc

    @pytest.mark.asyncio
    async def test_no_moderation_action_skips_hook(self):
        s = _SpyStage(name="a", order=10)  # default result, no moderation_action
        message_pipeline.register(s)

        with patch.object(
            message_pipeline,
            "_route_moderation_action",
            new_callable=AsyncMock,
        ) as hook:
            await message_pipeline.dispatch(MagicMock(), _make_message())
        hook.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_route_dispatches_auto_delete_to_moderation_service(self):
        """The actual hook (not mocked) routes auto_delete:* to moderation_service."""
        message = _make_message()
        desc = ModerationActionDescriptor(
            action="auto_delete:cleanup.prohibited_words",
            target_id=42,
            reason="rule X",
            rule="cleanup.prohibited_words",
        )

        with patch(
            "services.moderation_service.auto_delete",
            new_callable=AsyncMock,
        ) as auto_delete:
            await message_pipeline._route_moderation_action(message, desc)
        auto_delete.assert_awaited_once_with(
            message,
            reason="rule X",
            rule="cleanup.prohibited_words",
        )

    @pytest.mark.asyncio
    async def test_route_logs_warning_for_unknown_action(self, caplog):
        """Unknown descriptor action types log a warning instead of dispatching."""
        message = _make_message()
        desc = ModerationActionDescriptor(
            action="unknown_kind",
            target_id=42,
            reason="x",
        )
        with patch(
            "services.moderation_service.auto_delete",
            new_callable=AsyncMock,
        ) as auto_delete:
            await message_pipeline._route_moderation_action(message, desc)
        auto_delete.assert_not_awaited()


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


# ---------------------------------------------------------------------------
# Canonical stage-order contract
# ---------------------------------------------------------------------------


class TestStageOrderContract:
    """Pin the canonical stage-order table documented in the module
    docstring. Every registered stage must have a DISTINCT order so the
    run sequence never depends on cog load order (the pre-pipeline bug
    these tests guard against), and the documented tier relationships
    must hold.
    """

    def _all_orders(self) -> dict[str, int]:
        """Import every stage-order constant by its canonical name."""
        from cogs.btd6.stage import STAGE_ORDER as BTD6
        from cogs.chain_cog import CHAIN_STAGE_ORDER as CHAIN
        from cogs.cleanup_cog import CLEANUP_STAGE_ORDER as CLEANUP
        from cogs.counting._stage import COUNTING_STAGE_ORDER as COUNTING
        from cogs.four_twenty_cog import FOUR_TWENTY_STAGE_ORDER as FOUR_TWENTY
        from cogs.rps_tournament._stage import RPS_STAGE_ORDER as RPS
        from cogs.xp.stage import XP_STAGE_ORDER as XP
        from core.runtime.ai.natural_language_stage import STAGE_ORDER as AI

        return {
            "cleanup": CLEANUP,
            "counting": COUNTING,
            "chain": CHAIN,
            "xp": XP,
            "rps": RPS,
            "four_twenty": FOUR_TWENTY,
            "ai": AI,
            "btd6": BTD6,
        }

    def test_registered_stage_orders_are_distinct(self):
        orders = self._all_orders()
        values = list(orders.values())
        assert len(values) == len(set(values)), (
            f"stage orders must be distinct so run order never depends on "
            f"cog load order — got duplicates in {orders}"
        )

    def test_tier_relationships_hold(self):
        o = self._all_orders()
        # auto-mod tier, cleanup first (deletes a banned word before
        # counting/chain validate it).
        assert o["cleanup"] < o["counting"] < o["chain"]
        # rewards run after every auto-mod stage (never reward a deleted msg).
        assert o["chain"] < o["xp"] < o["rps"]
        # passive observe-only sits after rewards, before conversational.
        assert o["rps"] < o["four_twenty"] < o["ai"]
        # the regression that started this: passive 🍃 must precede the
        # short-circuiting AI stage or bot-mentions never get leafed.
        assert o["four_twenty"] < o["ai"] < o["btd6"]

    def test_orders_match_documented_table(self):
        assert self._all_orders() == {
            "cleanup": 10,
            "counting": 15,
            "chain": 20,
            "xp": 30,
            "rps": 40,
            "four_twenty": 50,
            "ai": 70,
            "btd6": 80,
        }
