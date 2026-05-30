"""Env-driven feature flags for the AI platform.

The gateway consults these on every call. Defaults are designed for
boot safety: AI is disabled unless an operator opts in, and the
default provider is ``deterministic`` so no external call is ever
made by accident.

Recognised env vars:

* ``AI_ENABLED``                 — ``"1"``/``"true"`` to enable the
  platform globally. Default off.
* ``AI_DEFAULT_PROVIDER``        — provider name; one of
  ``deterministic`` / ``openai``. Default ``deterministic``.
* ``AI_TASK_<NAME>_ENABLED``     — per-:class:`AITask` override. The
  ``<NAME>`` portion is the uppercase enum name (e.g.
  ``AI_TASK_SETUP_SUGGEST_ENABLED``). Once the global ``AI_ENABLED``
  gate is on, each task defaults to **enabled**; set this var to a
  falsey value to selectively *disable* a single task. The per-task
  flags are a kill-switch, not the opt-in gate — boot safety comes
  from the two layers above (``AI_ENABLED`` defaults off, and the
  default provider is ``deterministic`` so no external call is made
  by accident even when the platform is enabled).
* ``AI_TOOLS_ENABLED``           — ``"1"``/``"true"`` to let the
  gateway offer read-only tools to the model (function calling).
  Layers under :func:`ai_enabled`; default off, so tool calling is
  inert until an operator opts in.

Compatibility note: ``SETUP_ADVISOR_PROVIDER`` remains the
authoritative env var for the setup advisor's provider choice. The
new flags are additive; existing operators see no behavior change.
"""

from __future__ import annotations

import os

from core.runtime.ai.contracts import AITask

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _bool_env(name: str, *, default: bool = False) -> bool:
    raw = os.getenv(name, "")
    if not raw:
        return default
    return raw.strip().lower() in _TRUTHY


def ai_enabled() -> bool:
    """True if the AI platform is globally enabled.

    When false, the gateway returns degraded responses without
    invoking any provider. The setup advisor's deterministic
    fallback path is preserved separately via
    :func:`setup_advisor_provider`.
    """
    return _bool_env("AI_ENABLED", default=False)


def ai_default_provider() -> str:
    """Return the configured default provider name."""
    value = os.getenv("AI_DEFAULT_PROVIDER", "").strip().lower()
    if value:
        return value
    return "deterministic"


def task_enabled(task: AITask) -> bool:
    """True if a specific :class:`AITask` is allowed to call a provider.

    Per-task gating layers on top of :func:`ai_enabled`: the global
    flag must also be on. When ``ai_enabled()`` is false this
    function returns false regardless of the task flag.

    Once the global gate is on, individual tasks default to *enabled*
    (the per-task flag is a selective kill-switch, not an opt-in gate
    — see the module docstring for the boot-safety model).
    """
    if not ai_enabled():
        return False
    env_name = f"AI_TASK_{task.name}_ENABLED"
    # default=True is intentional: the opt-in gate is ai_enabled() above
    # (plus the deterministic default provider). Pinned by
    # tests/unit/runtime/ai/test_feature_flags.py::test_task_enabled_default_when_global_on
    # — do NOT flip to False without updating that contract and the
    # gateway's expectations (gateway.py:196 gates calls on this).
    return _bool_env(env_name, default=True)


def ai_tools_enabled() -> bool:
    """True if the gateway may offer read-only tools to the model.

    Layers on top of :func:`ai_enabled`: the global flag must also be
    on. When false (the default), the gateway never passes a tool
    dispatch to the provider, so behaviour is identical to the
    no-tools path regardless of what tools a caller supplies.
    """
    if not ai_enabled():
        return False
    return _bool_env("AI_TOOLS_ENABLED", default=False)


def setup_advisor_provider() -> str:
    """Authoritative provider choice for the setup advisor.

    Honours the legacy ``SETUP_ADVISOR_PROVIDER`` env var so existing
    operators see no behavior change. Falls back to
    :func:`ai_default_provider` when unset.
    """
    legacy = os.getenv("SETUP_ADVISOR_PROVIDER", "").strip().lower()
    if legacy:
        return legacy
    return ai_default_provider()
