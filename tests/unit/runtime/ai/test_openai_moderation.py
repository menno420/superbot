"""OpenAIModerationProvider unit tests.

The provider is one of the only modules that imports the OpenAI SDK directly
(the image-moderation chokepoint).  These tests inject a duck-typed client
shaped like ``AsyncOpenAI`` and verify the score extraction + the
fail-open ``ProviderUnavailableError`` when no client/key is available — no
network call is ever made.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.runtime.ai.providers.base import ProviderUnavailableError
from core.runtime.ai.providers.openai_moderation import (
    OpenAIModerationProvider,
    _extract_category_scores,
)


class _PydanticishScores:
    """Mimics the SDK's category_scores model (has ``model_dump``)."""

    def __init__(self, mapping):
        self._mapping = mapping

    def model_dump(self):
        return dict(self._mapping)


def test_extract_scores_from_plain_dict():
    response = {"results": [{"category_scores": {"sexual": 0.9, "hate": 0.1}}]}
    assert _extract_category_scores(response) == {"sexual": 0.9, "hate": 0.1}


def test_extract_scores_from_model_dump():
    result = MagicMock()
    result.category_scores = _PydanticishScores({"violence": 0.5})
    response = MagicMock()
    response.results = [result]
    assert _extract_category_scores(response) == {"violence": 0.5}


def test_extract_scores_empty_on_unexpected_shape():
    assert _extract_category_scores({}) == {}
    assert _extract_category_scores({"results": []}) == {}
    assert _extract_category_scores(object()) == {}


def test_extract_scores_coerces_and_skips_non_numeric():
    response = {"results": [{"category_scores": {"sexual": "0.8", "hate": None}}]}
    assert _extract_category_scores(response) == {"sexual": 0.8}


@pytest.mark.asyncio
async def test_classify_image_with_injected_client():
    create = AsyncMock(
        return_value={"results": [{"category_scores": {"sexual": 0.95}}]},
    )
    client = MagicMock()
    client.moderations.create = create

    provider = OpenAIModerationProvider(client=client)
    scores = await provider.classify_image("http://cdn/x.png")

    assert scores == {"sexual": 0.95}
    create.assert_awaited_once()
    kwargs = create.await_args.kwargs
    assert kwargs["model"] == "omni-moderation-latest"
    # Only the URL is sent — no message text, no author.
    assert kwargs["input"] == [
        {"type": "image_url", "image_url": {"url": "http://cdn/x.png"}},
    ]


@pytest.mark.asyncio
async def test_no_key_raises_provider_unavailable(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = OpenAIModerationProvider()  # no client, no key
    with pytest.raises(ProviderUnavailableError):
        await provider.classify_image("http://cdn/x.png")
