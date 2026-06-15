"""Tests for the discord-aware chat-memory orchestrator."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from services import ai_conversation_service, ai_memory_service


@pytest.fixture(autouse=True)
def _reset_buffers():
    ai_conversation_service._reset_for_tests()
    yield
    ai_conversation_service._reset_for_tests()


# ---------------------------------------------------------------------------
# read_memory_settings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_memory_settings_defaults(monkeypatch):
    async def _fake(_gid, key, default=""):
        return default

    monkeypatch.setattr("services.ai_memory_service.get_setting", _fake)
    window, scan = await ai_memory_service.read_memory_settings(1)
    assert window == 0
    assert scan is False


@pytest.mark.asyncio
async def test_read_memory_settings_parses_truthy_scan(monkeypatch):
    async def _fake(_gid, key, default=""):
        if "scan_enabled" in key:
            return "True"
        if "window_minutes" in key:
            return "60"
        return default

    monkeypatch.setattr("services.ai_memory_service.get_setting", _fake)
    window, scan = await ai_memory_service.read_memory_settings(1)
    assert window == 60
    assert scan is True


@pytest.mark.asyncio
async def test_read_memory_settings_clamps_unknown_window(monkeypatch):
    async def _fake(_gid, key, default=""):
        if "window_minutes" in key:
            return "999"  # not in allowed set
        return default

    monkeypatch.setattr("services.ai_memory_service.get_setting", _fake)
    window, _scan = await ai_memory_service.read_memory_settings(1)
    assert window == 0


@pytest.mark.asyncio
async def test_read_memory_settings_handles_non_numeric_window(monkeypatch):
    async def _fake(_gid, key, default=""):
        if "window_minutes" in key:
            return "wat"
        return default

    monkeypatch.setattr("services.ai_memory_service.get_setting", _fake)
    window, _scan = await ai_memory_service.read_memory_settings(1)
    assert window == 0


# ---------------------------------------------------------------------------
# gather_recent_turns
# ---------------------------------------------------------------------------


class _FakeMessage:
    def __init__(self, *, mid: int, author_id: int, content: str):
        self.id = mid
        self.author = SimpleNamespace(id=author_id, bot=False)
        self.content = content


class _FakeChannel:
    """Async-iterable history mock modelling discord.py semantics.

    ``_messages`` is the channel's full history, oldest-first. discord.py's
    ``history`` with no before/after anchor paginates from one end:

    * ``oldest_first=True``  → forward from the channel's start: the OLDEST
      ``limit`` messages, oldest-first.
    * ``oldest_first=False`` (the default) → backward from now: the most
      RECENT ``limit`` messages, newest-first.

    The previous mock ignored ``limit`` and returned the same set either
    way, which hid the real bug — the scan pulling the channel's oldest
    messages instead of the recent ones before a restart.
    """

    def __init__(self, messages: list[_FakeMessage]):
        self._messages = messages  # oldest -> newest
        self.calls: list[dict] = []

    def history(self, *, limit: int = 100, oldest_first: bool = False):
        self.calls.append({"limit": limit, "oldest_first": oldest_first})
        if oldest_first:
            seq = self._messages[:limit]  # oldest N, oldest-first
        else:
            seq = list(reversed(self._messages[-limit:]))  # recent N, newest-first

        async def _gen():
            for m in seq:
                yield m

        return _gen()


@pytest.mark.asyncio
async def test_gather_skips_scan_when_disabled(monkeypatch):
    async def _settings(_gid):
        return (0, False)  # scan disabled

    monkeypatch.setattr(ai_memory_service, "read_memory_settings", _settings)
    channel = _FakeChannel([_FakeMessage(mid=1, author_id=9, content="x")])

    out = await ai_memory_service.gather_recent_turns(
        guild_id=1,
        channel_id=2,
        channel=channel,
    )
    assert out == []
    assert channel.calls == []  # never scanned


@pytest.mark.asyncio
async def test_gather_scans_when_enabled_and_cache_short(monkeypatch):
    async def _settings(_gid):
        return (60, True)

    monkeypatch.setattr(ai_memory_service, "read_memory_settings", _settings)

    history = [
        _FakeMessage(mid=10, author_id=100, content="first"),
        _FakeMessage(mid=11, author_id=101, content="second"),
        _FakeMessage(mid=12, author_id=100, content="third"),
    ]
    channel = _FakeChannel(history)

    out = await ai_memory_service.gather_recent_turns(
        guild_id=1,
        channel_id=2,
        channel=channel,
    )
    assert len(channel.calls) == 1
    assert {t.text for t in out} == {"first", "second", "third"}


@pytest.mark.asyncio
async def test_gather_scan_seeds_most_recent_not_oldest(monkeypatch):
    """Regression: the scan must backfill the messages from just before the
    restart (the channel tail), not the channel's oldest messages.

    discord.py ``history(limit=N, oldest_first=True)`` with no anchor returns
    the channel's OLDEST N messages — it paginates from the start. The scan
    used that, so on any channel with more than ``_SCAN_LIMIT`` messages it
    seeded ancient history and the bot's "memory" of the channel looked
    broken after every restart. It must fetch the most recent messages.
    """

    async def _settings(_gid):
        return (60, True)

    monkeypatch.setattr(ai_memory_service, "read_memory_settings", _settings)

    # Full channel history, oldest -> newest, longer than the scan limit.
    total = ai_memory_service._SCAN_LIMIT + 10
    history = [
        _FakeMessage(mid=i, author_id=100 + (i % 3), content=f"msg-{i}")
        for i in range(total)
    ]
    channel = _FakeChannel(history)

    out = await ai_memory_service.gather_recent_turns(
        guild_id=1,
        channel_id=2,
        channel=channel,
    )
    texts = {t.text for t in out}
    # The newest message is present; the oldest is NOT (it is far past the
    # most-recent _SCAN_LIMIT window).
    assert f"msg-{total - 1}" in texts
    assert "msg-0" not in texts
    # Exactly the scan-limit window of most-recent messages was seeded.
    assert len(out) == ai_memory_service._SCAN_LIMIT
    # The fetch asked for the recent tail (default newest-first), NOT the
    # oldest-first-from-start pagination that caused the bug.
    assert channel.calls == [
        {"limit": ai_memory_service._SCAN_LIMIT, "oldest_first": False},
    ]


@pytest.mark.asyncio
async def test_gather_skips_scan_when_cache_already_meets_floor(monkeypatch):
    async def _settings(_gid):
        return (60, True)

    monkeypatch.setattr(ai_memory_service, "read_memory_settings", _settings)
    # Pre-seed the cache so the floor is satisfied.
    for i in range(ai_conversation_service.MIN_FLOOR_TURNS):
        ai_conversation_service.append(
            1,
            2,
            user_id=42,
            role="user",
            text=f"cached-{i}",
        )

    channel = _FakeChannel([_FakeMessage(mid=99, author_id=9, content="ignored")])

    out = await ai_memory_service.gather_recent_turns(
        guild_id=1,
        channel_id=2,
        channel=channel,
    )
    assert channel.calls == []  # no scan
    assert len(out) == ai_conversation_service.MIN_FLOOR_TURNS


@pytest.mark.asyncio
async def test_gather_classifies_bot_messages_as_assistant(monkeypatch):
    async def _settings(_gid):
        return (60, True)

    monkeypatch.setattr(ai_memory_service, "read_memory_settings", _settings)

    history = [
        _FakeMessage(mid=1, author_id=100, content="user msg"),
        _FakeMessage(mid=2, author_id=999, content="bot reply"),
    ]
    channel = _FakeChannel(history)

    await ai_memory_service.gather_recent_turns(
        guild_id=1,
        channel_id=2,
        channel=channel,
        bot_user_id=999,
    )
    turns = ai_conversation_service.recent_turns(1, 2, window_minutes=60)
    roles = {(t.user_id, t.role) for t in turns}
    assert (100, "user") in roles
    assert (999, "assistant") in roles


@pytest.mark.asyncio
async def test_gather_skips_command_prefixed_messages(monkeypatch):
    async def _settings(_gid):
        return (60, True)

    monkeypatch.setattr(ai_memory_service, "read_memory_settings", _settings)

    history = [
        _FakeMessage(mid=1, author_id=100, content="!ai diagnostics"),
        _FakeMessage(mid=2, author_id=101, content="/btd6 status"),
        _FakeMessage(mid=3, author_id=102, content="real message"),
    ]
    channel = _FakeChannel(history)

    await ai_memory_service.gather_recent_turns(
        guild_id=1,
        channel_id=2,
        channel=channel,
    )
    turns = ai_conversation_service.recent_turns(1, 2, window_minutes=60)
    texts = {t.text for t in turns}
    assert texts == {"real message"}


@pytest.mark.asyncio
async def test_gather_swallows_history_exception(monkeypatch):
    """A history call that raises (missing perms / network) must not
    propagate — we fall back to whatever the buffer already had."""

    async def _settings(_gid):
        return (60, True)

    monkeypatch.setattr(ai_memory_service, "read_memory_settings", _settings)

    class _BrokenChannel:
        def history(self, **_kw):
            raise RuntimeError("Forbidden")

    out = await ai_memory_service.gather_recent_turns(
        guild_id=1,
        channel_id=2,
        channel=_BrokenChannel(),
    )
    assert out == []


@pytest.mark.asyncio
async def test_gather_handles_channel_without_history_attr(monkeypatch):
    async def _settings(_gid):
        return (60, True)

    monkeypatch.setattr(ai_memory_service, "read_memory_settings", _settings)

    # ``None`` simulates a thread-only / DM context.
    out = await ai_memory_service.gather_recent_turns(
        guild_id=1,
        channel_id=2,
        channel=None,
    )
    assert out == []
