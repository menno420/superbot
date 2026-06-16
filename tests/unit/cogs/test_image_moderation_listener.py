"""Unit tests for the image-moderation stage orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from cogs.image_moderation import listener
from core.runtime.ai.providers.base import ProviderUnavailableError
from services.image_moderation_config import ImageModerationPolicy


def _attachment(url="http://cdn/x.png"):
    att = MagicMock()
    att.url = url
    att.content_type = "image/png"
    att.filename = "x.png"
    return att


def _message(*, with_image=True):
    msg = MagicMock()
    msg.id = 555
    msg.guild = MagicMock(id=1)
    msg.channel = MagicMock(id=100)
    msg.author = MagicMock(spec=discord.Member)
    msg.author.id = 200
    msg.author.roles = []
    msg.attachments = [_attachment()] if with_image else []
    return msg


def _enabled_policy(**overrides):
    base = dict(enabled=True, sexual_enabled=True, threshold_percent=80)
    base.update(overrides)
    return ImageModerationPolicy(**base)


@pytest.mark.asyncio
async def test_disabled_policy_is_a_noop(monkeypatch):
    monkeypatch.setattr(
        listener.image_moderation_config,
        "load_policy",
        AsyncMock(return_value=ImageModerationPolicy(enabled=False)),
    )
    classifier = AsyncMock()
    result = await listener.process_message(
        MagicMock(), _message(), classifier=classifier
    )
    assert result.deleted is False and result.short_circuit is False
    classifier.assert_not_awaited()  # never scanned when disabled


@pytest.mark.asyncio
async def test_no_image_attachment_is_a_noop(monkeypatch):
    monkeypatch.setattr(
        listener.image_moderation_config,
        "load_policy",
        AsyncMock(return_value=_enabled_policy()),
    )
    classifier = AsyncMock()
    result = await listener.process_message(
        MagicMock(), _message(with_image=False), classifier=classifier
    )
    assert result.deleted is False
    classifier.assert_not_awaited()  # no image → no external call


@pytest.mark.asyncio
async def test_exempt_channel_skips_before_any_api_call(monkeypatch):
    monkeypatch.setattr(
        listener.image_moderation_config,
        "load_policy",
        AsyncMock(return_value=_enabled_policy(exempt_channel_ids=frozenset({100}))),
    )
    classifier = AsyncMock()
    result = await listener.process_message(
        MagicMock(), _message(), classifier=classifier
    )
    assert result.deleted is False
    classifier.assert_not_awaited()  # exemption short-circuits before scanning


@pytest.mark.asyncio
async def test_provider_unavailable_fails_open(monkeypatch):
    monkeypatch.setattr(
        listener.image_moderation_config,
        "load_policy",
        AsyncMock(return_value=_enabled_policy()),
    )
    classifier = AsyncMock(side_effect=ProviderUnavailableError("no key"))
    result = await listener.process_message(
        MagicMock(), _message(), classifier=classifier
    )
    assert result.deleted is False and result.short_circuit is False


@pytest.mark.asyncio
async def test_classify_error_fails_open(monkeypatch):
    monkeypatch.setattr(
        listener.image_moderation_config,
        "load_policy",
        AsyncMock(return_value=_enabled_policy()),
    )
    classifier = AsyncMock(side_effect=RuntimeError("network"))
    result = await listener.process_message(
        MagicMock(), _message(), classifier=classifier
    )
    assert result.deleted is False


@pytest.mark.asyncio
async def test_clean_image_is_not_acted_on(monkeypatch):
    monkeypatch.setattr(
        listener.image_moderation_config,
        "load_policy",
        AsyncMock(return_value=_enabled_policy()),
    )
    auto_delete = AsyncMock()
    monkeypatch.setattr(listener.moderation_service, "auto_delete", auto_delete)
    classifier = AsyncMock(return_value={"sexual": 0.10})
    result = await listener.process_message(
        MagicMock(), _message(), classifier=classifier
    )
    assert result.deleted is False
    auto_delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_flagged_image_deletes_warns_and_emits(monkeypatch):
    monkeypatch.setattr(
        listener.image_moderation_config,
        "load_policy",
        AsyncMock(return_value=_enabled_policy()),
    )
    auto_delete = AsyncMock()
    warn = AsyncMock()
    monkeypatch.setattr(listener.moderation_service, "auto_delete", auto_delete)
    monkeypatch.setattr(listener.moderation_service, "warn", warn)

    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    classifier = AsyncMock(return_value={"sexual": 0.97})
    result = await listener.process_message(
        MagicMock(), _message(), classifier=classifier
    )

    assert result.deleted is True and result.short_circuit is True
    auto_delete.assert_awaited_once()
    assert auto_delete.await_args.kwargs["rule"] == "image_moderation.sexual"
    warn.assert_awaited_once()
    assert warn.await_args.kwargs["actor_id"] is None
    emit.assert_awaited_once()
    assert emit.await_args.args[0] == listener.EVT_IMAGE_MODERATION_FLAGGED
    assert emit.await_args.kwargs["category"] == "sexual"


@pytest.mark.asyncio
async def test_load_policy_fault_fails_open(monkeypatch):
    monkeypatch.setattr(
        listener.image_moderation_config,
        "load_policy",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    result = await listener.process_message(MagicMock(), _message())
    assert result.deleted is False and result.short_circuit is False


@pytest.mark.asyncio
async def test_dm_message_is_a_noop():
    msg = MagicMock()
    msg.guild = None
    result = await listener.process_message(MagicMock(), msg)
    assert result.deleted is False
