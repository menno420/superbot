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
    reporter._session = MagicMock()  # truthy so _send proceeds past the early-return guard

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
