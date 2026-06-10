"""chain_service — the canonical audited owner of chain_channels (RS07).

Pins the mutation contract the Batch 3 pattern requires: old-value read
before write, ``audit.action_recorded`` with the real ``prev_value``,
typed results, and **no write / no audit** on the rejection paths the
cog + modals used to duplicate locally.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import chain_service


def _patches(existing: dict | None):
    """Patch the chain DB primitives + the audit emitter in one place."""
    return (
        patch(
            "services.chain_service.db.get_chain_channel",
            AsyncMock(return_value=existing),
        ),
        patch("services.chain_service.db.set_chain_channel", AsyncMock()),
        patch("services.chain_service.db.delete_chain_channel", AsyncMock()),
        patch("services.chain_service.db.set_chain_limit", AsyncMock()),
        patch(
            "services.chain_service.emit_audit_action",
            AsyncMock(return_value=True),
        ),
    )


# ---------------------------------------------------------------------------
# create_chain
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_chain_writes_normalized_word_and_audits():
    get, set_, delete, limit, emit = _patches(existing=None)
    with get, set_ as set_mock, delete, limit, emit as emit_mock:
        result = await chain_service.create_chain(
            guild_id=99,
            channel_id=5,
            word="  HeLLo ",
            actor_id=1,
        )

    assert result.applied and result.status == "applied"
    assert result.new_value == "hello"
    set_mock.assert_awaited_once_with(5, 99, "hello", limit=0)
    kwargs = emit_mock.await_args.kwargs
    assert kwargs["subsystem"] == "chain"
    assert kwargs["mutation_type"] == "create_chain"
    assert kwargs["target"] == "channel:5"
    assert kwargs["prev_value"] is None
    assert kwargs["new_value"] == "word=hello"
    assert kwargs["actor_id"] == 1
    assert result.audit_emitted is True and result.mutation_id


@pytest.mark.asyncio
async def test_create_chain_rejects_existing_word_without_write():
    existing = {"word": "good", "word_limit": 0}
    get, set_, delete, limit, emit = _patches(existing)
    with get, set_ as set_mock, delete, limit, emit as emit_mock:
        result = await chain_service.create_chain(
            guild_id=99,
            channel_id=5,
            word="other",
            actor_id=1,
        )

    assert result.status == "already_exists" and not result.applied
    set_mock.assert_not_awaited()
    emit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_chain_rejects_empty_word():
    get, set_, delete, limit, emit = _patches(existing=None)
    with get, set_ as set_mock, delete, limit, emit as emit_mock:
        result = await chain_service.create_chain(
            guild_id=99,
            channel_id=5,
            word="   ",
            actor_id=1,
        )

    assert result.status == "invalid"
    set_mock.assert_not_awaited()
    emit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_chain_preserves_existing_limit():
    """A limit-only row keeps its word_limit when a chain word is created
    on top (the old direct upsert silently reset it to 0)."""
    existing = {"word": None, "word_limit": 7}
    get, set_, delete, limit, emit = _patches(existing)
    with get, set_ as set_mock, delete, limit, emit:
        result = await chain_service.create_chain(
            guild_id=99,
            channel_id=5,
            word="go",
            actor_id=1,
        )

    assert result.applied
    set_mock.assert_awaited_once_with(5, 99, "go", limit=7)
    assert result.old_value == "limit=7"


# ---------------------------------------------------------------------------
# delete_chain
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_chain_audits_with_real_prev_value():
    existing = {"word": "good", "word_limit": 3}
    get, set_, delete, limit, emit = _patches(existing)
    with get, set_, delete as delete_mock, limit, emit as emit_mock:
        result = await chain_service.delete_chain(
            guild_id=99,
            channel_id=5,
            actor_id=2,
        )

    assert result.applied
    delete_mock.assert_awaited_once_with(5)
    kwargs = emit_mock.await_args.kwargs
    assert kwargs["mutation_type"] == "delete_chain"
    assert kwargs["prev_value"] == "word=good limit=3"
    assert kwargs["new_value"] is None


@pytest.mark.asyncio
async def test_delete_chain_not_found_skips_write_and_audit():
    get, set_, delete, limit, emit = _patches(existing=None)
    with get, set_, delete as delete_mock, limit, emit as emit_mock:
        result = await chain_service.delete_chain(
            guild_id=99,
            channel_id=5,
            actor_id=2,
        )

    assert result.status == "not_found"
    delete_mock.assert_not_awaited()
    emit_mock.assert_not_awaited()


# ---------------------------------------------------------------------------
# set_word_limit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_word_limit_writes_and_audits_old_new():
    existing = {"word": "good", "word_limit": 2}
    get, set_, delete, limit, emit = _patches(existing)
    with get, set_, delete, limit as limit_mock, emit as emit_mock:
        result = await chain_service.set_word_limit(
            guild_id=99,
            channel_id=5,
            limit=10,
            actor_id=3,
        )

    assert result.applied
    limit_mock.assert_awaited_once_with(5, 10)
    kwargs = emit_mock.await_args.kwargs
    assert kwargs["mutation_type"] == "set_chain_limit"
    assert kwargs["prev_value"] == "2"
    assert kwargs["new_value"] == "10"


@pytest.mark.asyncio
async def test_set_word_limit_requires_existing_row():
    get, set_, delete, limit, emit = _patches(existing=None)
    with get, set_, delete, limit as limit_mock, emit as emit_mock:
        result = await chain_service.set_word_limit(
            guild_id=99,
            channel_id=5,
            limit=10,
            actor_id=3,
        )

    assert result.status == "not_found"
    limit_mock.assert_not_awaited()
    emit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_word_limit_no_change_skips_write_and_audit():
    existing = {"word": "good", "word_limit": 0}
    get, set_, delete, limit, emit = _patches(existing)
    with get, set_, delete, limit as limit_mock, emit as emit_mock:
        result = await chain_service.set_word_limit(
            guild_id=99,
            channel_id=5,
            limit=0,
            actor_id=3,
        )

    assert result.status == "no_change"
    limit_mock.assert_not_awaited()
    emit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_word_limit_rejects_negative():
    get, set_, delete, limit, emit = _patches(existing={"word": "good"})
    with get, set_, delete, limit as limit_mock, emit:
        result = await chain_service.set_word_limit(
            guild_id=99,
            channel_id=5,
            limit=-1,
            actor_id=3,
        )

    assert result.status == "invalid"
    limit_mock.assert_not_awaited()


# ---------------------------------------------------------------------------
# record_chain_progress (game-state lane — unaudited passthrough)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_chain_progress_increments_without_audit():
    with (
        patch(
            "services.chain_service.db.increment_chain_count",
            AsyncMock(return_value=4),
        ) as inc,
        patch(
            "services.chain_service.emit_audit_action",
            AsyncMock(),
        ) as emit_mock,
    ):
        count = await chain_service.record_chain_progress(5)

    assert count == 4
    inc.assert_awaited_once_with(5)
    emit_mock.assert_not_awaited()
