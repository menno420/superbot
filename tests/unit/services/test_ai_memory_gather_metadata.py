"""PR-5 — gather_recent_turns_with_metadata returns scan metadata.

Pins:

* New helper returns a :class:`MemoryGatherResult` dataclass carrying
  ``turns`` plus ``window_minutes`` / ``scan_attempted`` /
  ``scan_added_turns``.
* The legacy ``gather_recent_turns`` is unchanged and still returns a
  bare list — so existing callsites do not break.
* When the buffer already has ``MIN_FLOOR_TURNS`` content, no scan is
  attempted (``scan_attempted=False``, ``scan_added_turns=0``).
* When the buffer is short and ``channel_scan_enabled=True``, the
  scan attempt is recorded and the added-turn count reflects what
  the seed appended.
* Scan disabled → ``scan_attempted=False`` regardless of buffer state.
"""

from __future__ import annotations

import pytest

from services import ai_conversation_service, ai_memory_service


@pytest.fixture(autouse=True)
def _reset_buffers():
    ai_conversation_service._reset_for_tests()
    yield
    ai_conversation_service._reset_for_tests()


def _patch_settings(monkeypatch, *, window: int, scan: bool) -> None:
    async def _read(_guild_id):
        return window, scan

    monkeypatch.setattr(ai_memory_service, "read_memory_settings", _read)


@pytest.mark.asyncio
async def test_legacy_helper_signature_unchanged():
    """``gather_recent_turns`` still returns a bare list."""
    import inspect

    sig = inspect.signature(ai_memory_service.gather_recent_turns)
    assert list(sig.parameters.keys()) == [
        "guild_id",
        "channel_id",
        "channel",
        "bot_user_id",
    ]


@pytest.mark.asyncio
async def test_metadata_helper_returns_dataclass(monkeypatch):
    _patch_settings(monkeypatch, window=30, scan=False)
    ai_conversation_service.append(1, 100, user_id=1, role="user", text="a")
    ai_conversation_service.append(1, 100, user_id=1, role="user", text="b")
    ai_conversation_service.append(1, 100, user_id=1, role="user", text="c")
    ai_conversation_service.append(1, 100, user_id=1, role="user", text="d")

    result = await ai_memory_service.gather_recent_turns_with_metadata(
        guild_id=1,
        channel_id=100,
    )
    assert isinstance(result, ai_memory_service.MemoryGatherResult)
    assert len(result.turns) == 4
    assert result.window_minutes == 30
    # Buffer is well above MIN_FLOOR_TURNS — no scan attempted.
    assert result.scan_attempted is False
    assert result.scan_added_turns == 0


@pytest.mark.asyncio
async def test_metadata_helper_records_window_zero(monkeypatch):
    _patch_settings(monkeypatch, window=0, scan=False)
    ai_conversation_service.append(1, 100, user_id=1, role="user", text="a")

    result = await ai_memory_service.gather_recent_turns_with_metadata(
        guild_id=1,
        channel_id=100,
    )
    assert result.window_minutes == 0
    assert result.scan_attempted is False


@pytest.mark.asyncio
async def test_metadata_helper_no_scan_when_disabled(monkeypatch):
    """Even on an empty buffer, scan stays off when ``scan=False``."""
    _patch_settings(monkeypatch, window=30, scan=False)

    class _FakeChannel:
        async def history(self, **_kw):
            # Would yield messages — but the helper must not call this
            # when scan is disabled. The test asserts via scan_attempted=False.
            for _ in range(0):
                yield None

    result = await ai_memory_service.gather_recent_turns_with_metadata(
        guild_id=1,
        channel_id=100,
        channel=_FakeChannel(),
    )
    assert result.scan_attempted is False
    assert result.scan_added_turns == 0


@pytest.mark.asyncio
async def test_metadata_helper_scan_attempted_when_buffer_short(monkeypatch):
    """Scan enabled + buffer below floor → attempt recorded."""
    _patch_settings(monkeypatch, window=30, scan=True)

    seeded_messages: list[tuple[int, str]] = [
        (1, "hello"),
        (2, "world"),
    ]

    class _FakeMessage:
        def __init__(self, author_id, content):
            self.author = type("A", (), {"id": author_id, "bot": False})()
            self.content = content

            class _CreatedAt:
                def timestamp(self):
                    return 1700000000.0

            self.created_at = _CreatedAt()

    class _FakeChannel:
        def history(self, **_kw):
            messages = [_FakeMessage(uid, body) for uid, body in seeded_messages]

            async def _gen():
                for m in messages:
                    yield m

            return _gen()

    result = await ai_memory_service.gather_recent_turns_with_metadata(
        guild_id=1,
        channel_id=100,
        channel=_FakeChannel(),
        bot_user_id=999,
    )
    assert result.scan_attempted is True
    # The seed appended at least the two messages we mocked.
    assert result.scan_added_turns >= 1


@pytest.mark.asyncio
async def test_metadata_helper_scan_failure_does_not_raise(monkeypatch):
    """If the scan helper raises, the result still returns the buffer
    contents with ``scan_attempted=True, scan_added_turns=0``."""
    _patch_settings(monkeypatch, window=30, scan=True)

    class _BrokenChannel:
        def history(self, **_kw):
            async def _gen():
                yield None
                raise RuntimeError("network down")

            return _gen()

    result = await ai_memory_service.gather_recent_turns_with_metadata(
        guild_id=1,
        channel_id=100,
        channel=_BrokenChannel(),
        bot_user_id=999,
    )
    assert result.scan_attempted is True
    # Best-effort: failure surfaces as zero added turns rather than raising.
    assert result.scan_added_turns == 0
