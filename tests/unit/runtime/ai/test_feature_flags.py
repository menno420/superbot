"""Feature-flag resolution for the AI gateway."""

from __future__ import annotations

from core.runtime.ai.contracts import AITask
from core.runtime.ai.feature_flags import (
    ai_default_provider,
    ai_enabled,
    setup_advisor_provider,
    task_enabled,
)


def test_ai_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AI_ENABLED", raising=False)
    assert ai_enabled() is False


def test_ai_enabled_via_env(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    assert ai_enabled() is True
    monkeypatch.setenv("AI_ENABLED", "true")
    assert ai_enabled() is True
    monkeypatch.setenv("AI_ENABLED", "no")
    assert ai_enabled() is False


def test_default_provider_falls_back_to_deterministic(monkeypatch):
    monkeypatch.delenv("AI_DEFAULT_PROVIDER", raising=False)
    assert ai_default_provider() == "deterministic"


def test_default_provider_respects_env(monkeypatch):
    monkeypatch.setenv("AI_DEFAULT_PROVIDER", "OPENAI")
    assert ai_default_provider() == "openai"


def test_task_disabled_when_global_off(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "0")
    assert task_enabled(AITask.SETUP_SUGGEST) is False


def test_task_enabled_default_when_global_on(monkeypatch):
    """Contract: per-task flags are a selective kill-switch, not an
    opt-in. With the global ``AI_ENABLED`` gate on and no per-task var
    set, a task defaults to enabled. Boot safety is provided by
    ``AI_ENABLED`` (default off) + the deterministic default provider,
    not by this flag — the module docstring must match this default.
    """
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.delenv("AI_TASK_SETUP_SUGGEST_ENABLED", raising=False)
    assert task_enabled(AITask.SETUP_SUGGEST) is True


def test_task_can_be_individually_disabled(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("AI_TASK_SETUP_SUGGEST_ENABLED", "0")
    assert task_enabled(AITask.SETUP_SUGGEST) is False


def test_setup_advisor_provider_honours_legacy_env(monkeypatch):
    monkeypatch.setenv("SETUP_ADVISOR_PROVIDER", "openai")
    monkeypatch.setenv("AI_DEFAULT_PROVIDER", "deterministic")
    assert setup_advisor_provider() == "openai"


def test_setup_advisor_provider_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("SETUP_ADVISOR_PROVIDER", raising=False)
    monkeypatch.setenv("AI_DEFAULT_PROVIDER", "deterministic")
    assert setup_advisor_provider() == "deterministic"
