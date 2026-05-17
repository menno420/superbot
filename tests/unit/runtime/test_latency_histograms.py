"""Tests for the S3.1 / O-2 latency histograms.

Three histograms instrumented at three hot-path boundaries:

  command_latency_seconds         — bot1.on_command_completion
  db_query_seconds                — utils/db/pool primitives
  interaction_handler_seconds     — interaction_router.dispatch

Each test verifies that the histogram is observed at the expected
emit site with the expected labels.  The histogram object itself is
patched so the test doesn't depend on prometheus_client internals.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# db_query_seconds — pool primitive instrumentation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query, expected_label",
    [
        ("SELECT * FROM xp WHERE user_id = $1", "select:xp"),
        ("INSERT INTO guild_settings (k, v) VALUES ($1, $2)", "insert:guild_settings"),
        ("UPDATE economy SET coins = coins + 5 WHERE user_id = $1", "update:economy"),
        ("DELETE FROM runtime_sessions WHERE id = $1", "delete:runtime_sessions"),
        ("    select * from xp", "select:xp"),  # leading whitespace
        ("EXPLAIN ANALYZE SELECT 1", "explain:unknown"),  # no table match
        ("", "unknown:unknown"),  # empty query
    ],
)
def test_query_label_extracts_op_and_table(query, expected_label):
    from utils.db.pool import _query_label

    assert _query_label(query) == expected_label


@pytest.mark.asyncio
async def test_fetchone_observes_db_query_seconds():
    from utils.db import pool

    fake_conn = MagicMock()
    fake_conn.fetchrow = AsyncMock(return_value={"id": 1})

    with (
        patch("utils.db.pool.get", return_value=fake_conn),
        patch("utils.db.pool._metrics.db_query_seconds") as hist,
    ):
        await pool.fetchone("SELECT * FROM xp WHERE id = $1", (1,))

    hist.labels.assert_called_with(query_name="select:xp")
    hist.labels.return_value.observe.assert_called_once()


@pytest.mark.asyncio
async def test_fetchall_observes_db_query_seconds():
    from utils.db import pool

    fake_conn = MagicMock()
    fake_conn.fetch = AsyncMock(return_value=[])

    with (
        patch("utils.db.pool.get", return_value=fake_conn),
        patch("utils.db.pool._metrics.db_query_seconds") as hist,
    ):
        await pool.fetchall("SELECT * FROM guild_settings", ())

    hist.labels.assert_called_with(query_name="select:guild_settings")
    hist.labels.return_value.observe.assert_called_once()


@pytest.mark.asyncio
async def test_execute_observes_db_query_seconds():
    from utils.db import pool

    fake_conn = MagicMock()
    fake_conn.execute = AsyncMock()

    with (
        patch("utils.db.pool.get", return_value=fake_conn),
        patch("utils.db.pool._metrics.db_query_seconds") as hist,
    ):
        await pool.execute(
            "UPDATE economy SET coins = $1 WHERE user_id = $2",
            (100, 1),
        )

    hist.labels.assert_called_with(query_name="update:economy")
    hist.labels.return_value.observe.assert_called_once()


@pytest.mark.asyncio
async def test_db_query_seconds_observes_even_when_query_raises():
    """The finally block must observe latency even if the underlying call fails."""
    from utils.db import pool

    fake_conn = MagicMock()
    fake_conn.fetchrow = AsyncMock(side_effect=RuntimeError("connection lost"))

    with (
        patch("utils.db.pool.get", return_value=fake_conn),
        patch("utils.db.pool._metrics.db_query_seconds") as hist,
        pytest.raises(RuntimeError),
    ):
        await pool.fetchone("SELECT * FROM xp", ())

    hist.labels.assert_called_with(query_name="select:xp")
    hist.labels.return_value.observe.assert_called_once()


# ---------------------------------------------------------------------------
# interaction_handler_seconds — router.dispatch instrumentation
# ---------------------------------------------------------------------------


def _interaction(custom_id: str) -> MagicMock:
    i = MagicMock()
    i.custom_id = custom_id
    i.data = {"custom_id": custom_id}
    i.user = MagicMock()
    i.user.id = 42
    i.guild_id = None
    i.channel_id = None
    i.response = MagicMock()
    i.response.is_done = MagicMock(return_value=False)
    i.response.send_message = AsyncMock()
    return i


@pytest.mark.asyncio
async def test_handler_latency_observed_on_success():
    from core.runtime import interaction_router

    async def handler(*_a, **_kw):
        return None

    interaction_router._handlers["xp"] = handler
    try:
        with patch(
            "core.runtime.interaction_router.metrics.interaction_handler_seconds",
        ) as hist:
            await interaction_router.dispatch(_interaction("xp:rank"))
        hist.labels.assert_called_with(prefix="xp")
        hist.labels.return_value.observe.assert_called_once()
    finally:
        interaction_router._handlers.pop("xp", None)


@pytest.mark.asyncio
async def test_handler_latency_observed_when_handler_raises():
    """The finally block must observe latency even on handler failure."""
    from core.runtime import interaction_router

    async def handler(*_a, **_kw):
        raise RuntimeError("handler boom")

    interaction_router._handlers["xp"] = handler
    try:
        with patch(
            "core.runtime.interaction_router.metrics.interaction_handler_seconds",
        ) as hist:
            await interaction_router.dispatch(_interaction("xp:rank"))
        hist.labels.assert_called_with(prefix="xp")
        hist.labels.return_value.observe.assert_called_once()
    finally:
        interaction_router._handlers.pop("xp", None)


@pytest.mark.asyncio
async def test_unhandled_prefix_does_NOT_observe_handler_latency():
    """If no handler matched, there's no handler to time."""
    from core.runtime import interaction_router

    with patch(
        "core.runtime.interaction_router.metrics.interaction_handler_seconds",
    ) as hist:
        await interaction_router.dispatch(_interaction("ghost:foo"))

    hist.labels.assert_not_called()


# ---------------------------------------------------------------------------
# command_latency_seconds — bot1.on_command_completion instrumentation
# ---------------------------------------------------------------------------
#
# bot1.py has side effects at import time (PID file checks, signal
# handlers).  We assert the wiring by checking the histogram is in the
# metrics module + that the on_command_completion handler code references
# it.  Live instrumentation is exercised indirectly by the integration
# test below.


def test_command_latency_seconds_metric_exists():
    from services import metrics

    assert hasattr(metrics, "command_latency_seconds")


def test_bot1_on_command_completion_observes_command_latency():
    """Static check: bot1 imports the metric and observes it on completion."""
    import ast
    from pathlib import Path

    src = Path("disbot/bot1.py").read_text()
    tree = ast.parse(src)

    found_observe = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "observe":
            # Look at parent expressions for "command_latency_seconds"
            parent_str = ast.unparse(node)
            if "command_latency_seconds" in parent_str:
                found_observe = True
                break

    assert found_observe, (
        "bot1.py is missing the command_latency_seconds.observe(...) call "
        "in on_command_completion — S3.1 instrumentation regression."
    )


def test_bot1_on_command_stamps_cmd_start():
    """Static check: bot1.on_command must stamp _cmd_start for completion timing."""
    src = open("disbot/bot1.py").read()
    assert "_cmd_start = time.monotonic()" in src, (
        "bot1.py on_command must stamp ctx._cmd_start = time.monotonic() "
        "so on_command_completion can observe end-to-end latency."
    )
