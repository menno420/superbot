"""Tests for the gateway's per-guild policy overlay (Issue C).

Post-PR-#310 the typed ``ai_guild_policy.default_provider`` and
``default_model`` fields are written by the settings projection but
were not read at runtime — they were dead-writes. This module pins the
overlay behaviour now baked into ``AIGateway.execute``:

* When ``request.context.guild_id`` is set AND the typed row has
  non-empty provider/model, the gateway uses those values.
* When the typed row is missing, empty, or unreadable, the gateway
  falls back to the env- / hardcoded-defaults that ``routing.resolve``
  already produces.
* The overlay is never invoked when there is no guild context (e.g.
  process-level diagnostic surfaces).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponseMode,
    AIScope,
    AITask,
)
from core.runtime.ai.gateway import AIGateway, _overlay_guild_policy
from core.runtime.ai.routing import RoutingTarget


# ---------------------------------------------------------------------------
# _overlay_guild_policy — direct contract tests
# ---------------------------------------------------------------------------


def _target() -> RoutingTarget:
    return RoutingTarget(
        provider="deterministic",
        model="gpt-4o-mini",
        timeout_seconds=20.0,
    )


@pytest.mark.asyncio
async def test_overlay_uses_typed_provider_and_model(monkeypatch):
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(
            return_value={
                "default_provider": "openai",
                "default_model": "gpt-4o",
            },
        ),
    )

    result = await _overlay_guild_policy(_target(), guild_id=99)

    assert result.provider == "openai"
    assert result.model == "gpt-4o"
    assert result.timeout_seconds == 20.0


@pytest.mark.asyncio
async def test_overlay_keeps_env_default_when_typed_row_missing(monkeypatch):
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value=None),
    )

    result = await _overlay_guild_policy(_target(), guild_id=99)

    assert result == _target()


@pytest.mark.asyncio
async def test_overlay_keeps_env_default_when_typed_fields_empty(monkeypatch):
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(
            return_value={"default_provider": "", "default_model": ""},
        ),
    )

    result = await _overlay_guild_policy(_target(), guild_id=99)

    assert result == _target()


@pytest.mark.asyncio
async def test_overlay_uses_typed_provider_only(monkeypatch):
    """Provider set but model empty → typed provider, hardcoded model."""
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(
            return_value={"default_provider": "openai", "default_model": ""},
        ),
    )

    result = await _overlay_guild_policy(_target(), guild_id=99)

    assert result.provider == "openai"
    assert result.model == "gpt-4o-mini"  # fallback from routing target


@pytest.mark.asyncio
async def test_overlay_uses_typed_model_only(monkeypatch):
    """Model set but provider empty → keep routing-target provider."""
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(
            return_value={
                "default_provider": "",
                "default_model": "gpt-4o-turbo",
            },
        ),
    )

    result = await _overlay_guild_policy(_target(), guild_id=99)

    assert result.provider == "deterministic"  # from routing target
    assert result.model == "gpt-4o-turbo"


@pytest.mark.asyncio
async def test_overlay_swallows_db_failure(monkeypatch):
    """A DB read failure must NOT raise — gateway contract requires
    ``execute`` to never propagate exceptions to callers."""
    from utils.db import ai as ai_db

    async def _boom(*a, **kw):
        raise RuntimeError("connection lost")

    monkeypatch.setattr(ai_db, "get_guild_policy", _boom)

    result = await _overlay_guild_policy(_target(), guild_id=99)

    assert result == _target()


# ---------------------------------------------------------------------------
# AIGateway.execute end-to-end — the overlay is wired in
# ---------------------------------------------------------------------------


class _FakeProvider:
    """Tiny provider stub that records the model it was called with."""

    name = "openai"

    def __init__(self) -> None:
        self.received_model: str | None = None

    async def execute(self, request: AIRequest, *, model: str) -> str:
        self.received_model = model
        return "ok"


def _request(guild_id: int | None) -> AIRequest:
    return AIRequest(
        context=AIRequestContext(
            task=AITask.GENERAL_NL_ANSWER,
            scope=AIScope.USER,
            guild_id=guild_id,
            source="test",
        ),
        system_prompt="sys",
        payload={"text": "hi"},
        mode=AIResponseMode.TEXT,
    )


@pytest.fixture(autouse=True)
def _enable_ai(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")


@pytest.mark.asyncio
async def test_gateway_execute_applies_overlay_for_guild_request(monkeypatch):
    """When ``guild_id`` is set on the request, the gateway threads the
    typed-policy provider/model down to the provider call."""
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(
            return_value={
                "default_provider": "openai",
                "default_model": "gpt-4o",
            },
        ),
    )

    provider = _FakeProvider()
    gateway = AIGateway(providers={"openai": provider, "deterministic": provider})

    response = await gateway.execute(_request(guild_id=42))

    assert response.provider == "openai"
    assert response.model == "gpt-4o"
    assert provider.received_model == "gpt-4o"


@pytest.mark.asyncio
async def test_gateway_execute_skips_overlay_when_no_guild_id(monkeypatch):
    """No guild context (e.g. process-level diagnostic) → use the
    env / task-default routing target as-is."""
    from utils.db import ai as ai_db

    get_guild_policy = AsyncMock(return_value={"default_provider": "openai"})
    monkeypatch.setattr(ai_db, "get_guild_policy", get_guild_policy)

    provider = _FakeProvider()
    provider.name = "deterministic"
    gateway = AIGateway(providers={"deterministic": provider})

    response = await gateway.execute(_request(guild_id=None))

    get_guild_policy.assert_not_called()
    assert response.provider == "deterministic"
