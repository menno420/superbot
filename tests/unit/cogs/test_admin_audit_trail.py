"""Stage-2 walk bug #3 — high-privilege admin mutations now emit an audit event.

Cog load/unload/reload and the restart / log-level paths previously performed
their runtime mutation with zero ``emit_audit_action`` call. They now emit a
best-effort audit (cog-layer seam, like ``proof_channel_cog._emit_prize_audit``):
on success only, and an audit failure never blocks the operation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.admin.cog_manager import _do_load, _do_reload, _do_unload
from cogs.admin_cog import _emit_admin_runtime_audit

# ruff: noqa: S101


def _bot():
    bot = MagicMock()
    bot.load_extension = AsyncMock()
    bot.unload_extension = AsyncMock()
    bot.reload_extension = AsyncMock()
    return bot


@pytest.mark.parametrize(
    ("fn", "mtype"),
    [(_do_load, "cog_load"), (_do_unload, "cog_unload"), (_do_reload, "cog_reload")],
)
@pytest.mark.asyncio
async def test_cog_action_emits_audit(fn, mtype):
    with patch("services.audit_events.emit_audit_action", new=AsyncMock()) as emit:
        await fn(_bot(), "cogs.general_cog", actor_id=7)
    emit.assert_awaited_once()
    kwargs = emit.await_args.kwargs
    assert kwargs["subsystem"] == "admin"
    assert kwargs["mutation_type"] == mtype
    assert kwargs["target"] == "cog:cogs.general_cog"
    assert kwargs["scope"] == "global"
    assert kwargs["guild_id"] is None
    assert kwargs["actor_id"] == 7
    assert kwargs["actor_type"] == "admin"


@pytest.mark.asyncio
async def test_failed_load_does_not_emit_audit():
    bot = _bot()
    bot.load_extension = AsyncMock(side_effect=RuntimeError("boom"))
    with patch("services.audit_events.emit_audit_action", new=AsyncMock()) as emit:
        status = await _do_load(bot, "cogs.general_cog", actor_id=7)
    emit.assert_not_awaited()  # audit only on success
    assert "Error loading" in status


@pytest.mark.asyncio
async def test_audit_failure_does_not_block_the_load():
    with patch(
        "services.audit_events.emit_audit_action",
        new=AsyncMock(side_effect=RuntimeError("bus down")),
    ):
        status = await _do_load(_bot(), "cogs.general_cog", actor_id=7)
    assert "loaded" in status  # the op succeeded despite the audit failure


@pytest.mark.asyncio
async def test_runtime_audit_helper_emits_expected_fields():
    with patch("services.audit_events.emit_audit_action", new=AsyncMock()) as emit:
        await _emit_admin_runtime_audit("restart", "runtime:process", None, "!restart", 7)
    kwargs = emit.await_args.kwargs
    assert kwargs["subsystem"] == "admin"
    assert kwargs["mutation_type"] == "restart"
    assert kwargs["target"] == "runtime:process"
    assert kwargs["new_value"] == "!restart"
    assert kwargs["actor_id"] == 7


@pytest.mark.asyncio
async def test_runtime_audit_helper_swallows_failure():
    with patch(
        "services.audit_events.emit_audit_action",
        new=AsyncMock(side_effect=RuntimeError("bus down")),
    ):
        # must not raise
        await _emit_admin_runtime_audit("set_log_level", "logging:root", "INFO", "DEBUG", 7)
