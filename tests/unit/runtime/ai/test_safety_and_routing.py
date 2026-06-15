"""Safety prechecks and routing resolution."""

from __future__ import annotations

import pytest

from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponseMode,
    AIScope,
    AITask,
)
from core.runtime.ai.routing import (
    RoutingTarget,
    clear_overrides,
    override,
    resolve,
)
from core.runtime.ai.safety import MAX_PAYLOAD_BYTES, precheck


def _req(payload: dict, *, system: str = "system") -> AIRequest:
    return AIRequest(
        context=AIRequestContext(
            task=AITask.SETUP_SUGGEST,
            scope=AIScope.ADMIN,
            source="test",
        ),
        system_prompt=system,
        payload=payload,
        mode=AIResponseMode.JSON,
    )


# ----- safety -----------------------------------------------------------


def test_safety_rejects_empty_system_prompt():
    assert precheck(_req({"ok": 1}, system="")) is not None
    assert precheck(_req({"ok": 1}, system="   ")) is not None


def test_safety_rejects_empty_payload():
    assert precheck(_req({})) is not None


def test_safety_rejects_oversized_payload():
    big = {"data": "x" * (MAX_PAYLOAD_BYTES + 1024)}
    result = precheck(_req(big))
    assert result is not None
    assert "exceeds" in result


def test_safety_allows_normal_payload():
    assert precheck(_req({"channels": [1, 2, 3]})) is None


# ----- routing ----------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_overrides_after_test():
    yield
    clear_overrides()


def test_routing_default_uses_deterministic(monkeypatch):
    monkeypatch.delenv("AI_DEFAULT_PROVIDER", raising=False)
    monkeypatch.delenv("AI_ROUTING_SETUP_SUGGEST", raising=False)
    target = resolve(AITask.SETUP_SUGGEST)
    assert target.provider == "deterministic"
    assert target.model
    assert target.timeout_seconds > 0


def test_routing_env_var_overrides_default(monkeypatch):
    monkeypatch.setenv("AI_ROUTING_SETUP_SUGGEST", "openai:gpt-4o")
    target = resolve(AITask.SETUP_SUGGEST)
    assert target.provider == "openai"
    assert target.model == "gpt-4o"


def test_routing_override_takes_precedence(monkeypatch):
    monkeypatch.setenv("AI_DEFAULT_PROVIDER", "openai")
    override(
        AITask.SETUP_SUGGEST,
        RoutingTarget(provider="fake", model="fake-1", timeout_seconds=1.0),
    )
    target = resolve(AITask.SETUP_SUGGEST)
    assert target.provider == "fake"
    assert target.model == "fake-1"
