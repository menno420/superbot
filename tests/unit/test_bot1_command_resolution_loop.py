"""Regression tests for the BUG-0014 command-resolution loop.

A user typing ``!coglist`` made ``bot1.on_command_error`` re-dispatch an AUTO
typo-correction (``coglist``) that was not a registered command, which
``CommandNotFound``-ed again and re-resolved to the same phantom — an infinite
"↩️ Ran ``!coglist`` — assumed from ``!coglist``" spam loop that only stopped on
restart.

The fix is the loop-breaker in ``on_command_error``: an AUTO correction is only
re-dispatched when it is a *registered* command *different* from the raw token.
These tests drive the handler directly with a stubbed resolver and assert the
re-dispatch (``bot.process_commands``) only fires on a safe correction.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from discord.ext import commands

import bot1
from utils.command_resolution import Outcome, Resolution


def _make_ctx(raw: str, content: str) -> SimpleNamespace:
    """Minimal Context stand-in exposing only what on_command_error reads."""
    return SimpleNamespace(
        command=None,
        cog=None,
        invoked_with=raw,
        prefix="!",
        message=SimpleNamespace(content=content),
        send=AsyncMock(),
        channel=SimpleNamespace(id=1),
        author="tester",
        guild=None,
    )


def _sent_texts(ctx: SimpleNamespace) -> list[str]:
    return [c.args[0] for c in ctx.send.await_args_list if c.args]


@pytest.mark.asyncio
async def test_phantom_auto_correction_does_not_redispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An AUTO correction to an UNREGISTERED command (the BUG-0014 phantom) must
    NOT be re-dispatched — that is the infinite loop. The user gets a single
    terminal not-found reply instead."""
    monkeypatch.setattr(bot1, "reporter", None)
    monkeypatch.setattr(
        bot1.command_resolution,
        "classify",
        lambda *a, **k: Resolution(Outcome.AUTO, "coglist"),
    )
    monkeypatch.setattr(bot1.bot, "get_command", lambda name: None)  # unregistered
    proc = AsyncMock()
    monkeypatch.setattr(bot1.bot, "process_commands", proc)

    ctx = _make_ctx("coglist", "!coglist")
    await bot1.on_command_error(ctx, commands.CommandNotFound())

    proc.assert_not_called()
    texts = _sent_texts(ctx)
    assert len(texts) == 1 and "not found" in texts[0].lower(), texts
    # The misleading "assumed from" note must NOT have been sent.
    assert not any("assumed from" in t for t in texts), texts


@pytest.mark.asyncio
async def test_identity_auto_correction_does_not_redispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Even if the correction were 'registered', a correction equal to the raw
    token must not re-dispatch — it can only re-enter CommandNotFound."""
    monkeypatch.setattr(bot1, "reporter", None)
    monkeypatch.setattr(
        bot1.command_resolution,
        "classify",
        lambda *a, **k: Resolution(Outcome.AUTO, "coglist"),
    )
    monkeypatch.setattr(bot1.bot, "get_command", lambda name: object())  # pretend real
    proc = AsyncMock()
    monkeypatch.setattr(bot1.bot, "process_commands", proc)

    ctx = _make_ctx("coglist", "!coglist")  # corrected == raw
    await bot1.on_command_error(ctx, commands.CommandNotFound())

    proc.assert_not_called()


@pytest.mark.asyncio
async def test_valid_auto_correction_still_redispatches_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A genuine typo correction (registered command, different token) must
    still auto-run exactly once — the loop-breaker must not regress the feature."""
    monkeypatch.setattr(bot1, "reporter", None)
    monkeypatch.setattr(
        bot1.command_resolution,
        "classify",
        lambda *a, **k: Resolution(Outcome.AUTO, "serverstats"),
    )
    monkeypatch.setattr(bot1.bot, "get_command", lambda name: object())  # registered
    proc = AsyncMock()
    monkeypatch.setattr(bot1.bot, "process_commands", proc)

    ctx = _make_ctx("serverstas", "!serverstas")
    await bot1.on_command_error(ctx, commands.CommandNotFound())

    proc.assert_awaited_once()
    assert ctx.message.content == "!serverstats"
    assert any("assumed from" in t for t in _sent_texts(ctx))
