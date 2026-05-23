"""LP-7 tests for ``WebhookReporter.on_startup_summary``.

Covers:
  * OK status → green embed.
  * DEGRADED status → gold embed with failed entries marked.
  * FAILED status → dark-red embed.
  * EMPTY (no outcomes) → greyple embed with explanation.
  * Embed renders durations and error messages per phase.
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from core.runtime import startup_outcome
from services.webhook_reporter import WebhookReporter


def _outcome(
    name: str,
    *,
    success: bool,
    error: str | None = None,
    duration_ms: float | None = None,
) -> startup_outcome.StartupOutcome:
    return startup_outcome.StartupOutcome(
        name=name,
        success=success,
        error=error,
        recorded_at=datetime.datetime.now(tz=datetime.timezone.utc),
        started_at=None,
        duration_ms=duration_ms,
        metadata={},
    )


@pytest.fixture
def _reporter_with_session() -> WebhookReporter:
    reporter = WebhookReporter("https://example.com/webhook")
    reporter._session = MagicMock()
    return reporter


async def _capture_embed(
    reporter: WebhookReporter,
    outcomes: tuple[startup_outcome.StartupOutcome, ...],
) -> discord.Embed:
    wh_mock = MagicMock()
    wh_mock.send = AsyncMock()
    with patch(
        "services.webhook_reporter.discord.Webhook.from_url",
        return_value=wh_mock,
    ):
        await reporter.on_startup_summary(outcomes)
    wh_mock.send.assert_awaited_once()
    return wh_mock.send.call_args.kwargs["embed"]


@pytest.mark.asyncio
async def test_startup_summary_ok_renders_green_embed(
    _reporter_with_session: WebhookReporter,
) -> None:
    outcomes = (
        _outcome("a", success=True, duration_ms=12.0),
        _outcome("b", success=True, duration_ms=4.0),
    )
    embed = await _capture_embed(_reporter_with_session, outcomes)
    assert "OK" in embed.title
    assert embed.color == discord.Color.green()
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Total"] == "2"
    assert fields["Succeeded"] == "2"
    assert fields["Failed"] == "0"
    # Per-phase lines include durations.
    assert "12" in (embed.description or "")


@pytest.mark.asyncio
async def test_startup_summary_degraded_renders_gold_embed(
    _reporter_with_session: WebhookReporter,
) -> None:
    outcomes = (
        _outcome("a", success=True, duration_ms=12.0),
        _outcome("b", success=False, error="RuntimeError: boom", duration_ms=8.0),
    )
    embed = await _capture_embed(_reporter_with_session, outcomes)
    assert "DEGRADED" in embed.title
    assert embed.color == discord.Color.gold()
    description = embed.description or ""
    assert "✅" in description
    assert "❌" in description
    assert "boom" in description


@pytest.mark.asyncio
async def test_startup_summary_failed_renders_dark_red_embed(
    _reporter_with_session: WebhookReporter,
) -> None:
    outcomes = (
        _outcome("a", success=False, error="RuntimeError: x"),
        _outcome("b", success=False, error="ValueError: y"),
    )
    embed = await _capture_embed(_reporter_with_session, outcomes)
    assert "FAILED" in embed.title
    assert embed.color == discord.Color.dark_red()
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Failed"] == "2"


@pytest.mark.asyncio
async def test_startup_summary_empty_renders_greyple_with_explanation(
    _reporter_with_session: WebhookReporter,
) -> None:
    embed = await _capture_embed(_reporter_with_session, ())
    assert "no outcomes" in embed.title.lower()
    assert embed.color == discord.Color.greyple()
    assert "No startup phases recorded" in (embed.description or "")
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Total"] == "0"
