"""RC-7 — feature cleanup provider registry + game_state provider.

``session_gc`` used to import ``economy_service`` / ``game_state_service`` and
inline the stale-``game_state`` refund-then-delete sweep.  That ownership moved
to ``services.game_state_cleanup`` behind ``core.runtime.cleanup_registry``;
``session_gc`` now only schedules and aggregates.

These tests cover the registry mechanics, the migrated refund behaviour (so the
ADR-002 refund contract is preserved), and the invariant that ``session_gc`` no
longer imports the feature services at module level.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from core.runtime import cleanup_registry
from core.runtime.cleanup_registry import CleanupResult


@pytest.fixture(autouse=True)
def _clean_registry():
    cleanup_registry._reset_for_tests()
    yield
    cleanup_registry._reset_for_tests()


# ---------------------------------------------------------------------------
# Registry mechanics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_all_aggregates_provider_results():
    async def a() -> CleanupResult:
        return CleanupResult(removed=2, refunded=1)

    async def b() -> CleanupResult:
        return CleanupResult(removed=3, refunded=0)

    cleanup_registry.register("a", a)
    cleanup_registry.register("b", b)
    result = await cleanup_registry.run_all()
    assert result == CleanupResult(removed=5, refunded=1)


@pytest.mark.asyncio
async def test_run_all_empty_is_zero():
    assert await cleanup_registry.run_all() == CleanupResult(0, 0)


@pytest.mark.asyncio
async def test_run_all_isolates_a_failing_provider():
    async def good() -> CleanupResult:
        return CleanupResult(removed=1, refunded=1)

    async def bad() -> CleanupResult:
        raise RuntimeError("provider blew up")

    cleanup_registry.register("good", good)
    cleanup_registry.register("bad", bad)
    # The bad provider is logged + skipped; the good one still counts.
    assert await cleanup_registry.run_all() == CleanupResult(removed=1, refunded=1)


def test_register_unregister_and_names():
    async def p() -> CleanupResult:
        return CleanupResult()

    cleanup_registry.register("x", p)
    assert "x" in cleanup_registry.registered_names()
    cleanup_registry.unregister("x")
    assert "x" not in cleanup_registry.registered_names()


def test_cleanup_result_unpacks_like_a_tuple():
    removed, refunded = CleanupResult(removed=4, refunded=2)
    assert (removed, refunded) == (4, 2)


# ---------------------------------------------------------------------------
# game_state provider — migrated from the old session_gc sweep tests so the
# ADR-002 refund-then-delete behaviour stays covered.
# ---------------------------------------------------------------------------


class TestGameStateCleanupProvider:
    @pytest.mark.asyncio
    async def test_no_stale_rows_is_noop(self):
        from services import game_state_cleanup

        with patch(
            "services.game_state_service.list_stale",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await game_state_cleanup.sweep_stale_game_state()
        assert result == CleanupResult(removed=0, refunded=0)

    @pytest.mark.asyncio
    async def test_stale_row_with_bet_triggers_refund(self):
        from services import game_state_cleanup

        stale = [
            {
                "id": 7,
                "guild_id": 111,
                "user_id": 222,
                "channel_id": 333,
                "subsystem": "blackjack_solo",
                "state": {"bet": 50, "hand": []},
                "version": 1,
                "updated_at": "2025-01-01",
            },
        ]
        with (
            patch(
                "services.game_state_service.list_stale",
                new_callable=AsyncMock,
                return_value=stale,
            ),
            patch(
                "services.game_state_service.clear_by_id",
                new_callable=AsyncMock,
            ) as mock_clear,
            patch(
                "services.economy_service.refund",
                new_callable=AsyncMock,
                return_value=50,
            ) as mock_refund,
        ):
            result = await game_state_cleanup.sweep_stale_game_state()
        assert result.removed == 1
        assert result.refunded == 1
        mock_refund.assert_awaited_once()
        kwargs = mock_refund.await_args.kwargs
        assert kwargs["guild_id"] == 111
        assert kwargs["user_id"] == 222
        assert kwargs["amount"] == 50
        assert "game_state:gc:blackjack_solo" in kwargs["reason"]
        # Delete uses the synthetic id, not the natural key.
        mock_clear.assert_awaited_once_with(7)

    @pytest.mark.asyncio
    async def test_stale_row_without_bet_deletes_without_refund(self):
        from services import game_state_cleanup

        stale = [
            {
                "id": 8,
                "guild_id": 111,
                "user_id": 222,
                "channel_id": 333,
                "subsystem": "counting",
                "state": {"current_count": 42},  # no "bet" key
                "version": 1,
                "updated_at": "2025-01-01",
            },
        ]
        with (
            patch(
                "services.game_state_service.list_stale",
                new_callable=AsyncMock,
                return_value=stale,
            ),
            patch(
                "services.game_state_service.clear_by_id",
                new_callable=AsyncMock,
            ) as mock_clear,
            patch(
                "services.economy_service.refund",
                new_callable=AsyncMock,
            ) as mock_refund,
        ):
            result = await game_state_cleanup.sweep_stale_game_state()
        assert result.removed == 1
        assert result.refunded == 0
        mock_refund.assert_not_called()
        mock_clear.assert_awaited_once_with(8)

    @pytest.mark.asyncio
    async def test_refund_failure_does_not_block_delete(self):
        """A permanently-failing refund must not loop forever — the row is still
        deleted so the next sweep moves on."""
        from services import game_state_cleanup

        stale = [
            {
                "id": 9,
                "guild_id": 111,
                "user_id": 222,
                "channel_id": 333,
                "subsystem": "blackjack_solo",
                "state": {"bet": 100},
                "version": 1,
                "updated_at": "2025-01-01",
            },
        ]
        with (
            patch(
                "services.game_state_service.list_stale",
                new_callable=AsyncMock,
                return_value=stale,
            ),
            patch(
                "services.game_state_service.clear_by_id",
                new_callable=AsyncMock,
            ) as mock_clear,
            patch(
                "services.economy_service.refund",
                new_callable=AsyncMock,
                side_effect=RuntimeError("refund DB hiccup"),
            ),
        ):
            result = await game_state_cleanup.sweep_stale_game_state()
        assert result.refunded == 0  # refund failed → not counted
        assert result.removed == 1  # delete still ran → counted
        mock_clear.assert_awaited_once_with(9)

    @pytest.mark.asyncio
    async def test_list_stale_failure_is_logged_not_raised(self):
        from services import game_state_cleanup

        with patch(
            "services.game_state_service.list_stale",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB down"),
        ):
            result = await game_state_cleanup.sweep_stale_game_state()
        assert result == CleanupResult(removed=0, refunded=0)


# ---------------------------------------------------------------------------
# install() wiring + the RC-7 boundary invariant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_install_registers_provider_and_run_all_invokes_it():
    from services import game_state_cleanup

    game_state_cleanup.install()
    assert game_state_cleanup.PROVIDER_NAME in cleanup_registry.registered_names()
    with patch(
        "services.game_state_service.list_stale",
        new_callable=AsyncMock,
        return_value=[],
    ):
        # Goes through the registry, exercising the session_gc → run_all path.
        assert await cleanup_registry.run_all() == CleanupResult(0, 0)


def test_session_gc_does_not_import_economy_or_game_state_at_module_level():
    """RC-7: the GC scheduler must not statically depend on the feature services
    whose cleanup it now delegates (only services.metrics remains)."""
    from core.runtime import session_gc

    tree = ast.parse(Path(session_gc.__file__).read_text(encoding="utf-8"))
    forbidden = {"economy_service", "game_state_service"}
    offenders: list[str] = []
    # Top-level statements only (function-body lazy imports would be a separate,
    # weaker concern; RC-7 targets the module-import graph).
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = {a.name for a in node.names}
            if mod == "services" and (forbidden & names):
                offenders.append(
                    f"from services import {', '.join(sorted(forbidden & names))}"
                )
            if any(mod.startswith(f"services.{f}") for f in forbidden):
                offenders.append(f"from {mod} import ...")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(f"services.{f}") for f in forbidden):
                    offenders.append(f"import {alias.name}")
    assert (
        not offenders
    ), f"session_gc must not import {forbidden} at module level: {offenders}"
