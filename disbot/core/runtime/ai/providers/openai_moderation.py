"""OpenAI moderation adapter — the image-moderation chokepoint for the SDK.

image moderation v1 (owner decision Q-0108): scan uploaded images against
OpenAI's free ``omni-moderation-latest`` endpoint.  Like
:mod:`core.runtime.ai.providers.openai_provider`, this is one of the only
modules permitted to import the ``openai`` SDK — the invariant test
``tests/unit/invariants/test_ai_btd6_boundaries.py::test_provider_sdk_imports_only_in_providers``
fails if any module outside ``core/runtime/ai/providers/`` imports it.  The
service + cog layers stay SDK-free and call through here.

The adapter is deliberately tiny: it constructs the client (lazily, sharing the
``OPENAI_API_KEY`` the AI cog already uses) and returns the moderation
**category scores** as a provider-neutral ``dict[str, float]``.  All threshold /
verdict logic lives in the pure :mod:`services.image_moderation_service` so it is
unit-testable without a network call or the SDK.

Privacy (Q-0108): only the image **URL** is sent to OpenAI — never message text,
never the author.  Operators are told this in the setting hint and
``docs/ownership.md``.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from core.runtime.ai.providers.base import ProviderUnavailableError

logger = logging.getLogger("bot.runtime.ai.openai_moderation")

#: The only model owner-approved for image moderation (Q-0108): free, covers
#: sexual / violence / harassment / hate, accepts image inputs.
DEFAULT_MODERATION_MODEL = "omni-moderation-latest"


class OpenAIModerationProvider:
    """Async OpenAI moderation adapter for image inputs.

    Constructed once and shared (see :func:`default_provider`).  A test can
    inject a duck-typed ``client`` (a ``MagicMock`` shaped like ``AsyncOpenAI``)
    without importing the SDK.  ``classify_image`` raises
    :class:`ProviderUnavailableError` when no client/key is available so the
    caller can **fail open** (let the image through) — the v1 discipline.
    """

    def __init__(
        self,
        *,
        client: Any = None,
        api_key: str | None = None,
        model: str = DEFAULT_MODERATION_MODEL,
    ) -> None:
        self._client = client
        self._api_key = api_key
        self._model = model

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - SDK present in CI
            raise ProviderUnavailableError(
                "openai package is not installed; image moderation is "
                "unavailable until ``openai>=1.40.0`` is installed.",
            ) from exc
        api_key = self._api_key or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ProviderUnavailableError(
                "OPENAI_API_KEY is not set; cannot run image moderation.",
            )
        self._client = AsyncOpenAI(api_key=api_key)
        return self._client

    async def classify_image(self, image_url: str) -> dict[str, float]:
        """Return OpenAI's per-category scores (0..1) for ``image_url``.

        Raises :class:`ProviderUnavailableError` when the SDK/key is missing.
        Any other fault (network, malformed response) propagates to the caller,
        which logs + fails open.  Only the URL is transmitted.
        """
        client = self._ensure_client()
        response = await client.moderations.create(
            model=self._model,
            input=[{"type": "image_url", "image_url": {"url": image_url}}],
        )
        return _extract_category_scores(response)


def _extract_category_scores(response: Any) -> dict[str, float]:
    """Pull ``results[0].category_scores`` out of a moderation response.

    Tolerant of both the SDK's pydantic model (``.model_dump()`` / attribute
    access) and a plain-dict test double; returns ``{}`` when the shape is
    unexpected so the caller fails open rather than crashing the stage.
    """
    results = getattr(response, "results", None)
    if results is None and isinstance(response, dict):
        results = response.get("results")
    if not results:
        return {}
    first = results[0]
    scores = getattr(first, "category_scores", None)
    if scores is None and isinstance(first, dict):
        scores = first.get("category_scores")
    if scores is None:
        return {}
    # The SDK exposes category_scores as a pydantic model; ``model_dump`` gives
    # the {category: float} mapping with the raw "sexual/minors" keys intact.
    dump = getattr(scores, "model_dump", None)
    if callable(dump):
        scores = dump()
    if not isinstance(scores, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in scores.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return out


# Process-wide default provider — one client per process, shared by the stage.
_DEFAULT_PROVIDER = OpenAIModerationProvider()


def default_provider() -> OpenAIModerationProvider:
    """Return the process-wide default :class:`OpenAIModerationProvider`."""
    return _DEFAULT_PROVIDER
