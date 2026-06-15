"""Unit tests for response_renderer_registry."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import AITask  # noqa: E402
from core.runtime.ai.response_renderer_registry import (  # noqa: E402
    RenderedResponse,
    _reset_for_tests,
    register,
    render,
)


@pytest.fixture(autouse=True)
def reset_registry():
    _reset_for_tests()
    yield
    _reset_for_tests()


async def test_render_returns_none_when_no_renderer_registered():
    result = await render(AITask.GENERAL_NL_ANSWER, MagicMock(), MagicMock(), None)
    assert result is None


async def test_render_dispatches_to_registered_renderer():
    fake_embed = MagicMock()
    expected = RenderedResponse(content=None, embed=fake_embed, allowed_mentions=None)

    async def my_renderer(task, response, req, ctx):
        return expected

    register(AITask.VIDEO_DESCRIBE, my_renderer)
    result = await render(AITask.VIDEO_DESCRIBE, MagicMock(), MagicMock(), None)
    assert result is expected


async def test_register_is_idempotent_second_fn_wins():
    """Re-registering the same task silently replaces the renderer (safe for cog_load)."""
    calls: list[str] = []

    async def fn_a(task, response, req, ctx):
        calls.append("a")
        return None

    async def fn_b(task, response, req, ctx):
        calls.append("b")
        return None

    register(AITask.VIDEO_DESCRIBE, fn_a)
    register(AITask.VIDEO_DESCRIBE, fn_b)

    await render(AITask.VIDEO_DESCRIBE, MagicMock(), MagicMock(), None)

    assert calls == ["b"]


async def test_render_passes_args_to_renderer():
    received: dict = {}

    async def capturing_renderer(task, response, req, ctx):
        received["task"] = task
        received["response"] = response
        received["req"] = req
        received["ctx"] = ctx
        return None

    register(AITask.VIDEO_COMPARE, capturing_renderer)

    fake_response = MagicMock()
    fake_req = MagicMock()
    fake_ctx = object()

    await render(AITask.VIDEO_COMPARE, fake_response, fake_req, fake_ctx)

    assert received["task"] is AITask.VIDEO_COMPARE
    assert received["response"] is fake_response
    assert received["req"] is fake_req
    assert received["ctx"] is fake_ctx
