"""Chat-memory tests for the extended ai_conversation_service."""

from __future__ import annotations

import time

import pytest

from services import ai_conversation_service as svc


@pytest.fixture(autouse=True)
def _reset_buffers():
    svc._reset_for_tests()
    yield
    svc._reset_for_tests()


# ---------------------------------------------------------------------------
# Append + read
# ---------------------------------------------------------------------------


def test_append_records_basic_turn():
    svc.append(1, 2, user_id=99, role="user", text="hello")
    out = svc.recent_turns(1, 2)
    assert len(out) == 1
    assert out[0].user_id == 99
    assert out[0].role == "user"
    assert out[0].text == "hello"


def test_append_skips_empty_text():
    svc.append(1, 2, user_id=99, role="user", text="")
    svc.append(1, 2, user_id=99, role="user", text="   ")
    assert svc.recent_turns(1, 2) == []


def test_append_skips_non_string_text():
    svc.append(1, 2, user_id=99, role="user", text=None)  # type: ignore[arg-type]
    svc.append(1, 2, user_id=99, role="user", text=42)  # type: ignore[arg-type]
    assert svc.recent_turns(1, 2) == []


# ---------------------------------------------------------------------------
# Floor (always-on minimum)
# ---------------------------------------------------------------------------


def test_window_zero_returns_at_most_floor():
    for i in range(10):
        svc.append(1, 2, user_id=i, role="user", text=f"msg-{i}")
    out = svc.recent_turns(1, 2, window_minutes=0)
    assert len(out) == svc.MIN_FLOOR_TURNS
    # Floor returns the most-recent N.
    assert [t.text for t in out] == ["msg-7", "msg-8", "msg-9"]


def test_window_short_returns_at_least_floor():
    """Even on a quiet channel a short window must return the floor."""
    # Two turns older than the window.
    old_ts = time.time() - 3600
    svc.append(1, 2, user_id=1, role="user", text="old-a", ts=old_ts)
    svc.append(1, 2, user_id=2, role="user", text="old-b", ts=old_ts)
    svc.append(1, 2, user_id=3, role="user", text="fresh", ts=time.time())

    out = svc.recent_turns(1, 2, window_minutes=15)
    # Floor=3 keeps all three even though only "fresh" is in window.
    assert {t.text for t in out} == {"old-a", "old-b", "fresh"}


# ---------------------------------------------------------------------------
# Window pruning
# ---------------------------------------------------------------------------


def test_window_drops_turns_older_than_cutoff():
    old_ts = time.time() - 7200  # 2h ago
    svc.append(1, 2, user_id=1, role="user", text="very-old", ts=old_ts)
    # Five fresh ones inside the 30-min window.
    for i in range(5):
        svc.append(1, 2, user_id=i + 2, role="user", text=f"fresh-{i}")

    out = svc.recent_turns(1, 2, window_minutes=30)
    # Five within window > floor (3), so the very-old turn is pruned.
    assert "very-old" not in {t.text for t in out}
    assert len(out) == 5


def test_window_two_hours_includes_recent_history():
    one_hour = time.time() - 3600
    svc.append(1, 2, user_id=1, role="user", text="hour-old", ts=one_hour)
    svc.append(1, 2, user_id=2, role="user", text="now")

    out = svc.recent_turns(1, 2, window_minutes=120)
    assert {t.text for t in out} == {"hour-old", "now"}


def test_limit_caps_window_output():
    for i in range(20):
        svc.append(1, 2, user_id=i, role="user", text=f"m-{i}")
    out = svc.recent_turns(1, 2, window_minutes=120, limit=5)
    assert len(out) == 5


# ---------------------------------------------------------------------------
# Forget
# ---------------------------------------------------------------------------


def test_forget_channel_drops_only_the_target():
    svc.append(1, 2, user_id=1, role="user", text="keep-a")
    svc.append(1, 3, user_id=1, role="user", text="drop-this")
    svc.append(99, 3, user_id=1, role="user", text="keep-b")

    dropped = svc.forget_channel(1, 3)
    assert dropped == 1
    assert svc.recent_turns(1, 2)
    assert svc.recent_turns(99, 3)
    assert svc.recent_turns(1, 3) == []


def test_forget_channel_no_op_for_missing_key():
    assert svc.forget_channel(404, 404) == 0


def test_forget_guild_drops_every_channel_for_guild():
    svc.append(1, 2, user_id=1, role="user", text="a")
    svc.append(1, 3, user_id=1, role="user", text="b")
    svc.append(99, 3, user_id=1, role="user", text="c")

    dropped = svc.forget_guild(1)
    assert dropped == 2
    assert svc.recent_turns(1, 2) == []
    assert svc.recent_turns(1, 3) == []
    assert svc.recent_turns(99, 3)


# ---------------------------------------------------------------------------
# LRU + caps
# ---------------------------------------------------------------------------


def test_per_channel_cap_enforced():
    for i in range(svc._PER_CHANNEL_CAP + 50):
        svc.append(1, 2, user_id=i, role="user", text=f"m-{i}")
    # The deque caps at _PER_CHANNEL_CAP; we don't exceed it.
    out = svc.recent_turns(1, 2, window_minutes=120, limit=500)
    assert len(out) == svc._PER_CHANNEL_CAP


def test_channel_lru_evicts_least_recently_used():
    # Fill exactly to the cap with N distinct channels.
    cap = svc._CHANNEL_LRU_CAP
    for c in range(cap):
        svc.append(1, c, user_id=1, role="user", text=f"channel-{c}")

    # One more channel — the oldest (channel 0) should be evicted.
    svc.append(1, cap, user_id=1, role="user", text="new-channel")
    assert svc.recent_turns(1, 0) == []
    assert svc.recent_turns(1, cap)


def test_recent_turns_touches_lru_order():
    # If a channel is READ from, it should be considered "used" so a
    # subsequent insertion evicts something else instead.
    cap = svc._CHANNEL_LRU_CAP
    for c in range(cap):
        svc.append(1, c, user_id=1, role="user", text=f"c-{c}")
    # Touch channel 0 via a read.
    svc.recent_turns(1, 0)
    # Add a new channel — channel 1 should now be the LRU victim, not 0.
    svc.append(1, cap + 100, user_id=1, role="user", text="hello")
    assert svc.recent_turns(1, 0)
    assert svc.recent_turns(1, 1) == []


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def test_stats_returns_counts_only():
    secret_body = "ZZZ_secret_message_body_should_not_leak_ZZZ"
    svc.append(1, 2, user_id=1, role="user", text=secret_body)
    svc.append(1, 2, user_id=1, role="user", text=secret_body)
    svc.append(1, 3, user_id=1, role="user", text=secret_body)
    snap = svc.stats()
    assert snap.channel_count == 2
    assert snap.total_turns == 3
    # Bodies must not leak through stats.
    assert "secret_message_body" not in repr(snap)


def test_channel_stats_per_guild():
    svc.append(1, 2, user_id=1, role="user", text="x")
    svc.append(1, 3, user_id=1, role="user", text="y")
    svc.append(99, 4, user_id=1, role="user", text="z")
    out = svc.channel_stats(1)
    assert out == {2: 1, 3: 1}
