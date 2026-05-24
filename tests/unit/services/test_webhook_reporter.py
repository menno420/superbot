"""Tests for ``services.webhook_reporter`` — embed redaction wiring (LP-1).

Covers the `_redact_embed` helper directly and an end-to-end path
through ``WebhookReporter._send`` and ``on_command_error`` to prove
secret-looking substrings never reach ``discord.Webhook.send``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.webhook_reporter import WebhookReporter, _redact_embed


class _Stringy:
    """Tiny stand-in for objects whose ``__str__`` is interpolated into
    embed fields (``ctx.author``, ``ctx.guild`` etc.)."""

    def __init__(self, s: str, id_: int | None = None) -> None:
        self._s = s
        if id_ is not None:
            self.id = id_

    def __str__(self) -> str:
        return self._s


def test_redact_embed_scrubs_every_textual_surface() -> None:
    embed = discord.Embed(
        title="ok",  # benign title
        description="connection string: postgres://u:secret@host/db failed",
    )
    embed.add_field(name="key", value="sk_live_abcdef123456", inline=False)
    embed.set_footer(text="contact alice@example.com")
    embed.set_author(name="Bearer abc.def-123")

    counts = _redact_embed(embed)

    assert "[database_url:redacted]" in (embed.description or "")
    assert "[api_key_like:redacted]" in embed.fields[0].value
    assert "[email:redacted]" in (embed.footer.text or "")
    assert "[bearer_token:redacted]" in (embed.author.name or "")
    assert counts.get("database_url") == 1
    assert counts.get("api_key_like") == 1
    assert counts.get("email") == 1
    assert counts.get("bearer_token") == 1


def test_redact_embed_no_secrets_means_no_changes() -> None:
    embed = discord.Embed(title="ok", description="all good")
    embed.add_field(name="x", value="123", inline=True)

    counts = _redact_embed(embed)

    assert embed.title == "ok"
    assert embed.description == "all good"
    assert embed.fields[0].value == "123"
    assert not counts


@pytest.mark.asyncio
async def test_send_scrubs_embed_before_dispatch_to_webhook() -> None:
    reporter = WebhookReporter("https://discord.com/api/webhooks/123/abc")
    reporter._session = (
        MagicMock()
    )  # truthy so _send proceeds past the early-return guard

    embed = discord.Embed(
        title="Crash",
        description="Traceback ... postgres://u:p@h/db ... raise",
    )

    wh_mock = MagicMock()
    wh_mock.send = AsyncMock()

    with patch(
        "services.webhook_reporter.discord.Webhook.from_url",
        return_value=wh_mock,
    ):
        await reporter._send(embed)

    wh_mock.send.assert_awaited_once()
    sent_embed = wh_mock.send.call_args.kwargs["embed"]
    assert "[database_url:redacted]" in (sent_embed.description or "")
    assert "postgres://" not in (sent_embed.description or "")


@pytest.mark.asyncio
async def test_send_no_session_returns_early_without_redaction_or_dispatch() -> None:
    reporter = WebhookReporter("https://discord.com/api/webhooks/123/abc")
    # _session left as None — _send should bail before redacting or sending.

    embed = discord.Embed(description="postgres://u:p@h/db")

    with patch(
        "services.webhook_reporter.discord.Webhook.from_url",
    ) as from_url:
        await reporter._send(embed)

    from_url.assert_not_called()
    # Embed not mutated because we never reached the redaction step.
    assert embed.description == "postgres://u:p@h/db"


def _webhook_dispatch_counter(outcome: str) -> float:
    from services import metrics as _metrics

    return _metrics.webhook_dispatch_total.labels(outcome=outcome)._value.get()


@pytest.mark.asyncio
async def test_send_records_success_outcome_in_metric() -> None:
    """Successful dispatch increments ``webhook_dispatch_total{outcome=success}``
    so operators can graph healthy posts."""
    reporter = WebhookReporter("https://discord.com/api/webhooks/123/abc")
    reporter._session = MagicMock()

    before = _webhook_dispatch_counter("success")

    wh_mock = MagicMock()
    wh_mock.send = AsyncMock()
    with patch(
        "services.webhook_reporter.discord.Webhook.from_url",
        return_value=wh_mock,
    ):
        await reporter._send(discord.Embed(title="ok"))

    assert _webhook_dispatch_counter("success") == before + 1


@pytest.mark.asyncio
async def test_send_records_error_outcome_when_send_raises() -> None:
    """A network failure / 4xx / 5xx raises out of ``wh.send`` and is
    caught + logged at DEBUG.  Without this metric, webhook outages
    were silent — only visible as the absence of expected embeds.
    Now operators can alert on
    ``rate(webhook_dispatch_total{outcome="error"}[5m]) > 0``."""
    reporter = WebhookReporter("https://discord.com/api/webhooks/123/abc")
    reporter._session = MagicMock()

    before = _webhook_dispatch_counter("error")

    wh_mock = MagicMock()
    wh_mock.send = AsyncMock(side_effect=RuntimeError("network down"))
    with patch(
        "services.webhook_reporter.discord.Webhook.from_url",
        return_value=wh_mock,
    ):
        # _send swallows the exception (best-effort observability).
        await reporter._send(discord.Embed(title="ok"))

    assert _webhook_dispatch_counter("error") == before + 1


def _dispatch_seconds_count_and_sum() -> tuple[float, float]:
    """Return (count, sum) for webhook_dispatch_seconds."""
    from services import metrics as _metrics

    samples = next(iter(_metrics.webhook_dispatch_seconds.collect())).samples
    count = next(s.value for s in samples if s.name.endswith("_count"))
    total = next(s.value for s in samples if s.name.endswith("_sum"))
    return count, total


@pytest.mark.asyncio
async def test_send_observes_dispatch_duration_on_success() -> None:
    """Healthy posts observe their duration in the histogram so
    operators can graph p50/p95 dispatch latency."""
    reporter = WebhookReporter("https://discord.com/api/webhooks/123/abc")
    reporter._session = MagicMock()

    before_count, before_sum = _dispatch_seconds_count_and_sum()

    wh_mock = MagicMock()
    wh_mock.send = AsyncMock()
    with patch(
        "services.webhook_reporter.discord.Webhook.from_url",
        return_value=wh_mock,
    ):
        await reporter._send(discord.Embed(title="ok"))

    after_count, after_sum = _dispatch_seconds_count_and_sum()
    assert after_count == before_count + 1
    # AsyncMock returns instantly so the observation is near-zero but
    # non-negative.
    assert (after_sum - before_sum) >= 0


@pytest.mark.asyncio
async def test_send_observes_dispatch_duration_on_error_too() -> None:
    """Exception path STILL observes — the time spent in a failing
    send is itself a useful signal (a slow connection-pool timeout
    looks different from an instant network error)."""
    reporter = WebhookReporter("https://discord.com/api/webhooks/123/abc")
    reporter._session = MagicMock()

    before_count, _ = _dispatch_seconds_count_and_sum()

    wh_mock = MagicMock()
    wh_mock.send = AsyncMock(side_effect=RuntimeError("network down"))
    with patch(
        "services.webhook_reporter.discord.Webhook.from_url",
        return_value=wh_mock,
    ):
        await reporter._send(discord.Embed(title="ok"))

    after_count, _ = _dispatch_seconds_count_and_sum()
    assert after_count == before_count + 1


@pytest.mark.asyncio
async def test_send_no_dispatch_outcome_when_session_missing() -> None:
    """The early-return guard (no URL or no session) must NOT increment
    either outcome — those are "no attempt made" not "attempt
    succeeded/failed"."""
    reporter = WebhookReporter("https://discord.com/api/webhooks/123/abc")
    # No _session set — _send bails before reaching dispatch.

    before_success = _webhook_dispatch_counter("success")
    before_error = _webhook_dispatch_counter("error")

    await reporter._send(discord.Embed(title="ok"))

    assert _webhook_dispatch_counter("success") == before_success
    assert _webhook_dispatch_counter("error") == before_error


@pytest.mark.asyncio
async def test_on_command_error_redacts_traceback_secret_end_to_end() -> None:
    """Construct a real exception whose message contains a Postgres URL,
    route through ``on_command_error``, and verify the embed that reached
    ``discord.Webhook.send`` no longer carries the raw URL.
    """
    reporter = WebhookReporter("https://example.com/webhook")
    reporter._session = MagicMock()

    ctx = MagicMock()
    ctx.message.content = "!leak"
    ctx.author = _Stringy("alice#0001", id_=12345)
    ctx.guild = _Stringy("Test Guild")
    ctx.channel = _Stringy("general")
    ctx.command = _Stringy("leak")
    ctx.cog = None

    try:
        raise RuntimeError("connection failed for postgres://u:p@host:5432/db")
    except RuntimeError as exc:
        err = exc

    wh_mock = MagicMock()
    wh_mock.send = AsyncMock()

    with patch(
        "services.webhook_reporter.discord.Webhook.from_url",
        return_value=wh_mock,
    ):
        await reporter.on_command_error(ctx, err)

    wh_mock.send.assert_awaited_once()
    sent_embed = wh_mock.send.call_args.kwargs["embed"]
    body = (sent_embed.description or "") + "".join(
        (f.value or "") for f in sent_embed.fields
    )
    assert "postgres://u:p@host" not in body
    assert "[database_url:redacted]" in body


# ---------------------------------------------------------------------------
# on_lifecycle_close_completed — companion to on_lifecycle_close_beginning,
# posted from main()'s finalizer right before reporter.close().
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_lifecycle_close_completed_renders_shutdown_embed():
    """Shutdown intent → red embed titled 'Shutdown Complete' with
    kind/reason/actor fields populated from the pending request."""
    from core.runtime.lifecycle import PendingShutdown

    reporter = WebhookReporter(url="https://example/wh")
    reporter._send = AsyncMock()  # type: ignore[method-assign]
    pending = PendingShutdown(
        kind="shutdown",
        reason="sigterm",
        actor="signal_handler",
        requested_at=0.0,
        grace_seconds=None,
    )

    await reporter.on_lifecycle_close_completed(pending, duration_seconds=1.42)

    reporter._send.assert_awaited_once()
    embed = reporter._send.await_args.args[0]
    assert "Shutdown Complete" in embed.title
    assert embed.color == discord.Color.dark_red()
    field_names = {f.name for f in embed.fields}
    assert {"Kind", "Reason", "Actor", "Close duration"} <= field_names
    duration_field = next(f for f in embed.fields if f.name == "Close duration")
    assert duration_field.value == "1.42s"


@pytest.mark.asyncio
async def test_on_lifecycle_close_completed_renders_restart_embed_without_duration():
    """Restart intent → gold embed titled 'Restart Complete'.  When the
    caller cannot compute duration (e.g. no close_executing event found),
    the Close duration field is omitted rather than rendered as 'None'."""
    from core.runtime.lifecycle import PendingShutdown

    reporter = WebhookReporter(url="https://example/wh")
    reporter._send = AsyncMock()  # type: ignore[method-assign]
    pending = PendingShutdown(
        kind="restart",
        reason="!restart",
        actor="operator#0001",
        requested_at=0.0,
        grace_seconds=None,
    )

    await reporter.on_lifecycle_close_completed(pending, duration_seconds=None)

    embed = reporter._send.await_args.args[0]
    assert "Restart Complete" in embed.title
    assert embed.color == discord.Color.gold()
    field_names = {f.name for f in embed.fields}
    assert "Close duration" not in field_names


# ---------------------------------------------------------------------------
# on_lifecycle_close_timeout — posted in the wedged-close branch before
# os._exit(1) so operators see why the container respawned.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_lifecycle_close_timeout_renders_dark_red_embed_with_timeout():
    """Timeout intent → dark-red embed titled 'Bot Close Timeout' with
    kind, reason, actor, and the configured timeout populated.  The
    title and color make wedge events unambiguous in the operator
    channel vs the gold 'Restart Complete' / dark-red 'Shutdown
    Complete' embeds."""
    from core.runtime.lifecycle import PendingShutdown

    reporter = WebhookReporter(url="https://example/wh")
    reporter._send = AsyncMock()  # type: ignore[method-assign]
    pending = PendingShutdown(
        kind="shutdown",
        reason="sigterm",
        actor="signal_handler",
        requested_at=0.0,
        grace_seconds=None,
    )

    await reporter.on_lifecycle_close_timeout(pending, timeout_seconds=20.0)

    reporter._send.assert_awaited_once()
    embed = reporter._send.await_args.args[0]
    assert "Close Timeout" in embed.title
    assert embed.color == discord.Color.dark_red()
    field_map = {f.name: f.value for f in embed.fields}
    assert field_map["Kind"] == "shutdown"
    assert field_map["Reason"] == "sigterm"
    assert field_map["Actor"] == "signal_handler"
    assert field_map["Timeout"] == "20.00s"


@pytest.mark.asyncio
async def test_on_lifecycle_close_timeout_falls_back_for_missing_actor_reason():
    """Missing actor / reason on the pending request must not blow up
    embed construction — they fall back to ``<unknown>`` consistently
    with the beginning / completed embeds."""
    from core.runtime.lifecycle import PendingShutdown

    reporter = WebhookReporter(url="https://example/wh")
    reporter._send = AsyncMock()  # type: ignore[method-assign]
    pending = PendingShutdown(
        kind="restart",
        reason="",
        actor=None,
        requested_at=0.0,
        grace_seconds=None,
    )

    await reporter.on_lifecycle_close_timeout(pending, timeout_seconds=5.5)

    embed = reporter._send.await_args.args[0]
    field_map = {f.name: f.value for f in embed.fields}
    assert field_map["Actor"] == "<unknown>"
    assert field_map["Reason"] == "<unknown>"
    assert field_map["Kind"] == "restart"
    assert field_map["Timeout"] == "5.50s"
