"""Tests for ``cogs.admin_cog`` restart command — LP-3.

Pins the contract that ``!restart`` records intent through
:mod:`core.runtime.lifecycle` and never touches process control
(``os.execv`` / ``os._exit``) directly. The watchdog in ``bot1.py``
turns the intent into ``bot.close()`` with a bounded timeout.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.admin_cog import AdminCog
from core.runtime import lifecycle

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ADMIN_COG = _REPO_ROOT / "disbot" / "cogs" / "admin_cog.py"


@pytest.fixture(autouse=True)
def _reset_lifecycle_state() -> None:
    lifecycle.reset_for_tests()
    yield
    lifecycle.reset_for_tests()


def _src() -> str:
    return _ADMIN_COG.read_text()


def test_admin_cog_source_does_not_touch_process_control() -> None:
    """LP-3: cog must not call ``os.execv`` / ``os._exit`` / ``sys.exit``
    / ``bot.close()``. Process control belongs to ``bot1.py``."""
    src = _src()
    assert "os.execv" not in src, (
        "admin_cog must not call os.execv — restart is routed through "
        "lifecycle.request_restart, executed by the bot1 watchdog (LP-3)."
    )
    assert "os._exit" not in src, "admin_cog must not call os._exit (LP-3)."
    assert "sys.exit" not in src, "admin_cog must not call sys.exit (LP-3)."
    assert ".bot.close(" not in src and "self.bot.close(" not in src, (
        "admin_cog must not call bot.close() directly — the close is "
        "driven by the bot1 restart watchdog so the timeout fallback "
        "applies uniformly (LP-3)."
    )


def test_admin_cog_restart_command_calls_lifecycle_request_restart() -> None:
    """AST-level: restart command body contains a
    ``lifecycle.request_restart`` call."""
    src = _src()
    tree = ast.parse(src)
    restart_fn: ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AsyncFunctionDef)
            and node.name == "reload_main_script"
        ):
            restart_fn = node
            break
    assert restart_fn is not None, (
        "admin_cog must define an async reload_main_script handler"
    )
    body_src = ast.unparse(restart_fn)
    assert re.search(
        r"lifecycle\.request_restart\(",
        body_src,
    ), "restart command must call lifecycle.request_restart (LP-3)"


@pytest.mark.asyncio
async def test_restart_command_records_intent_and_replies_to_user() -> None:
    """Behavioural: invoking the command records the intent in
    lifecycle and sends an acknowledgement to the user. The cog never
    closes the bot itself."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)

    bot = MagicMock()
    bot.close = AsyncMock()
    cog = AdminCog(bot)

    author = SimpleNamespace()
    author.__str__ = lambda self: "alice#0001"  # type: ignore[method-assign]
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.author = "alice#0001"  # str() on this is the literal

    await cog.reload_main_script.callback(cog, ctx)

    pending = lifecycle.get_pending()
    assert pending is not None
    assert pending.kind == "restart"
    assert pending.reason == "!restart"
    assert pending.actor == "alice#0001"
    ctx.send.assert_awaited_once()
    sent = ctx.send.await_args.args[0]
    assert "restart" in sent.lower()
    bot.close.assert_not_called()


@pytest.mark.asyncio
async def test_repeated_restart_command_coalesces_with_user_message() -> None:
    """A second ``!restart`` while one is already pending must coalesce
    and give the user explicit feedback rather than silently double-firing."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)

    bot = MagicMock()
    bot.close = AsyncMock()
    cog = AdminCog(bot)

    ctx1 = MagicMock()
    ctx1.send = AsyncMock()
    ctx1.author = "alice#0001"

    ctx2 = MagicMock()
    ctx2.send = AsyncMock()
    ctx2.author = "bob#0002"

    await cog.reload_main_script.callback(cog, ctx1)
    await cog.reload_main_script.callback(cog, ctx2)

    # Only the first request is recorded; the second coalesces.
    pending = lifecycle.get_pending()
    assert pending is not None
    assert pending.actor == "alice#0001"

    # Both users get feedback; the second message must clearly say
    # "already in progress" / "coalesced".
    first_msg = ctx1.send.await_args.args[0]
    second_msg = ctx2.send.await_args.args[0]
    assert "restart" in first_msg.lower()
    second_lower = second_msg.lower()
    assert "progress" in second_lower or "coalesced" in second_lower
    bot.close.assert_not_called()
