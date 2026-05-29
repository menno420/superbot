"""AI provider adapters.

The ``providers/`` subpackage is the only place in the codebase that
imports external LLM SDKs (``openai``, ``anthropic`` later). The
gateway in :mod:`core.runtime.ai.gateway` holds typed
:class:`Provider` instances and never touches an SDK directly. The
invariant test
``tests/unit/invariants/test_ai_btd6_boundaries.py::test_provider_sdk_imports_only_in_providers``
enforces this rule.
"""

from __future__ import annotations

from core.runtime.ai.providers.anthropic_provider import AnthropicProvider
from core.runtime.ai.providers.base import Provider, ProviderUnavailableError
from core.runtime.ai.providers.deterministic_provider import (
    DeterministicFallbackError,
    DeterministicProvider,
)
from core.runtime.ai.providers.openai_provider import OpenAIProvider

__all__ = [
    "AnthropicProvider",
    "DeterministicFallbackError",
    "DeterministicProvider",
    "OpenAIProvider",
    "Provider",
    "ProviderUnavailableError",
]
