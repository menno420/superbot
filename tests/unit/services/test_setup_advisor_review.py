"""Tests for services.setup_advisor_review — setup-wizard PR3.

The advisor review path must be advisory-only and fail-safe: every error
mode degrades to ``ok=False`` with a friendly message instead of raising,
so AI latency / outage can never block Final Review.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import setup_advisor_review
from services.setup_advisor_review import AdvisorReview, review_draft


def _rec(subsystem="xp", binding_name="announce_channel", rationale="because"):
    return SimpleNamespace(
        subsystem=subsystem,
        binding_name=binding_name,
        rationale=rationale,
        confidence="high",
    )


@pytest.mark.asyncio
async def test_returns_recommendations_as_advisory_text():
    draft = SimpleNamespace(
        recommendations=(_rec(), _rec(subsystem="economy", binding_name="log")),
        notes="",
    )
    advisor = MagicMock()
    advisor.suggest = AsyncMock(return_value=draft)
    with (
        patch(
            "services.guild_snapshot.collect",
            new=AsyncMock(return_value=object()),
        ),
        patch(
            "services.setup_ai_advisor.build_advisor",
            return_value=advisor,
        ),
    ):
        result = await review_draft(MagicMock())
    assert result.ok is True
    assert len(result.lines) == 2
    assert any("xp.announce_channel" in line for line in result.lines)


@pytest.mark.asyncio
async def test_no_recommendations_is_positive_ok():
    draft = SimpleNamespace(recommendations=(), notes="")
    advisor = MagicMock()
    advisor.suggest = AsyncMock(return_value=draft)
    with (
        patch("services.guild_snapshot.collect", new=AsyncMock(return_value=object())),
        patch("services.setup_ai_advisor.build_advisor", return_value=advisor),
    ):
        result = await review_draft(MagicMock())
    assert result.ok is True
    assert result.lines == ()
    assert "looks good" in result.summary.lower()


@pytest.mark.asyncio
async def test_snapshot_failure_degrades_gracefully():
    with patch(
        "services.guild_snapshot.collect",
        new=AsyncMock(side_effect=RuntimeError("discord down")),
    ):
        result = await review_draft(MagicMock())
    assert result.ok is False
    assert isinstance(result, AdvisorReview)
    # Friendly message, no exception propagated.
    assert result.summary


@pytest.mark.asyncio
async def test_advisor_suggest_failure_degrades_gracefully():
    advisor = MagicMock()
    advisor.suggest = AsyncMock(side_effect=TimeoutError("model timeout"))
    with (
        patch("services.guild_snapshot.collect", new=AsyncMock(return_value=object())),
        patch("services.setup_ai_advisor.build_advisor", return_value=advisor),
    ):
        result = await review_draft(MagicMock())
    assert result.ok is False
    assert result.summary


@pytest.mark.asyncio
async def test_review_never_raises_even_on_import_error():
    # Simulate the advisor import blowing up entirely.
    with patch.dict("sys.modules", {"services.setup_ai_advisor": None}):
        result = await review_draft(MagicMock())
    assert result.ok is False


@pytest.mark.asyncio
async def test_truncates_to_max_lines():
    draft = SimpleNamespace(
        recommendations=tuple(_rec(binding_name=f"b{i}") for i in range(15)),
        notes="",
    )
    advisor = MagicMock()
    advisor.suggest = AsyncMock(return_value=draft)
    with (
        patch("services.guild_snapshot.collect", new=AsyncMock(return_value=object())),
        patch("services.setup_ai_advisor.build_advisor", return_value=advisor),
    ):
        result = await review_draft(MagicMock())
    # 10 rendered + 1 "more" line.
    assert len(result.lines) == setup_advisor_review._MAX_LINES + 1
    assert "more" in result.lines[-1]
