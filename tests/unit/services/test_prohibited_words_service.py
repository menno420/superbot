"""Stage-2 walk bug #6 — the cleanup mutations are now audited at a service seam.

Two seams: ``prohibited_words_service`` (word add/remove + strict toggle, which
previously wrote ``utils.db`` directly from the cog / a view with no audit) and
``moderation_service.apply_channel_cleanup`` (the ``!cleanuphistory`` bulk delete,
which previously called ``apply_history_cleanup_plan`` directly, unaudited).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from services import moderation_service, prohibited_words_service

# ruff: noqa: S101


@pytest.mark.asyncio
async def test_add_prohibited_word_audits_when_added():
    with (
        patch.object(prohibited_words_service.db, "add_prohibited_word",
                     new=AsyncMock(return_value=True)),
        patch.object(prohibited_words_service, "emit_audit_action",
                     new=AsyncMock()) as emit,
    ):
        result = await prohibited_words_service.add_prohibited_word(
            42, "foo", actor_id=7,
        )
    assert result is True
    emit.assert_awaited_once()
    kwargs = emit.await_args.kwargs
    assert kwargs["subsystem"] == "cleanup"
    assert kwargs["mutation_type"] == "prohibited_word_add"
    assert kwargs["target"] == "word:foo"
    assert kwargs["guild_id"] == 42
    assert kwargs["actor_id"] == 7


@pytest.mark.asyncio
async def test_add_prohibited_word_no_audit_when_duplicate():
    with (
        patch.object(prohibited_words_service.db, "add_prohibited_word",
                     new=AsyncMock(return_value=False)),
        patch.object(prohibited_words_service, "emit_audit_action",
                     new=AsyncMock()) as emit,
    ):
        result = await prohibited_words_service.add_prohibited_word(
            42, "foo", actor_id=7,
        )
    assert result is False
    emit.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_prohibited_word_audits_when_removed():
    with (
        patch.object(prohibited_words_service.db, "remove_prohibited_word",
                     new=AsyncMock(return_value=True)),
        patch.object(prohibited_words_service, "emit_audit_action",
                     new=AsyncMock()) as emit,
    ):
        await prohibited_words_service.remove_prohibited_word(42, "foo", actor_id=7)
    assert emit.await_args.kwargs["mutation_type"] == "prohibited_word_remove"
    assert emit.await_args.kwargs["prev_value"] == "foo"


@pytest.mark.asyncio
async def test_set_wordfilter_strict_audits():
    with (
        patch.object(prohibited_words_service.db, "set_wordfilter_strict",
                     new=AsyncMock()),
        patch.object(prohibited_words_service, "emit_audit_action",
                     new=AsyncMock()) as emit,
    ):
        await prohibited_words_service.set_wordfilter_strict(42, True, actor_id=7)
    kwargs = emit.await_args.kwargs
    assert kwargs["mutation_type"] == "wordfilter_strict"
    assert kwargs["new_value"] == "True"
    assert kwargs["prev_value"] == "False"


@pytest.mark.asyncio
async def test_apply_channel_cleanup_audits_when_deleted():
    plan = SimpleNamespace(scanned=5)
    result = SimpleNamespace(deleted=2, failed=0)
    with (
        patch("services.history_cleanup.apply_history_cleanup_plan",
              new=AsyncMock(return_value=result)),
        patch.object(moderation_service, "_record_action", new=AsyncMock()) as record,
    ):
        out = await moderation_service.apply_channel_cleanup(
            plan, guild_id=42, channel_id=9, actor_id=7, mode="keyword",
        )
    assert out is result
    record.assert_awaited_once()
    kwargs = record.await_args.kwargs
    assert kwargs["action"] == "cleanup_history:keyword"
    assert kwargs["target_id"] == 9
    assert kwargs["target_kind"] == "channel"
    assert kwargs["actor_id"] == 7


@pytest.mark.asyncio
async def test_apply_channel_cleanup_no_audit_when_zero_deleted():
    plan = SimpleNamespace(scanned=5)
    result = SimpleNamespace(deleted=0, failed=0)
    with (
        patch("services.history_cleanup.apply_history_cleanup_plan",
              new=AsyncMock(return_value=result)),
        patch.object(moderation_service, "_record_action", new=AsyncMock()) as record,
    ):
        await moderation_service.apply_channel_cleanup(
            plan, guild_id=42, channel_id=9, actor_id=7, mode="keyword",
        )
    record.assert_not_awaited()
