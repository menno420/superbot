"""Unit tests for the automod detection engine (services.automod_service).

Pure-logic coverage: the content detectors, the spam sliding window, and the
``evaluate`` orchestrator's rule ordering + exempt safety valve.  No Discord I/O
and no DB — the engine is deliberately side-effect-free.
"""

from __future__ import annotations

from types import SimpleNamespace

from services import automod_service
from services.automod_config import AutomodPolicy


def _role(rid: int) -> SimpleNamespace:
    return SimpleNamespace(id=rid)


def _msg(
    *,
    content: str = "",
    channel_id: int = 100,
    author_id: int = 200,
    guild_id: int = 1,
    role_ids: tuple[int, ...] = (),
    mentions: int = 0,
    role_mentions: int = 0,
    everyone: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        content=content,
        channel=SimpleNamespace(id=channel_id),
        author=SimpleNamespace(id=author_id, roles=[_role(r) for r in role_ids]),
        guild=SimpleNamespace(id=guild_id),
        mentions=[object()] * mentions,
        role_mentions=[object()] * role_mentions,
        mention_everyone=everyone,
    )


# ---------------------------------------------------------------------------
# Content detectors
# ---------------------------------------------------------------------------


def test_find_invite_matches_common_forms():
    assert automod_service.find_invite("join discord.gg/abc123 now")
    assert automod_service.find_invite("https://discord.com/invite/xyz")
    assert automod_service.find_invite("DISCORDAPP.COM/INVITE/Q")  # case-insensitive


def test_find_invite_ignores_plain_text():
    assert not automod_service.find_invite("I love discord and gg games")
    assert not automod_service.find_invite("")


def test_caps_ratio_counts_letters_only():
    assert automod_service.caps_ratio("ABCD") == 1.0
    assert automod_service.caps_ratio("abcd") == 0.0
    assert automod_service.caps_ratio("AB!!12") == 1.0  # non-letters ignored
    assert automod_service.caps_ratio("12345") == 0.0  # no letters → 0


def test_exceeds_caps_respects_min_length():
    # "SHORT" is all caps but below the 10-letter floor → not tripped.
    assert not automod_service.exceeds_caps("SHORT", percent=70, min_letters=10)
    assert automod_service.exceeds_caps(
        "THIS IS ALL SHOUTING", percent=70, min_letters=10
    )
    assert not automod_service.exceeds_caps(
        "this is quiet talking", percent=70, min_letters=10
    )


def test_mention_count_sums_users_roles_and_everyone():
    assert automod_service.mention_count(_msg(mentions=3, role_mentions=1)) == 4
    assert automod_service.mention_count(_msg(everyone=True)) >= 1000


# ---------------------------------------------------------------------------
# SpamTracker
# ---------------------------------------------------------------------------


def test_spam_tracker_counts_within_window():
    trk = automod_service.SpamTracker()
    counts = [
        trk.record_and_count(1, 2, 3, window_seconds=10, now=float(t)) for t in range(5)
    ]
    assert counts == [1, 2, 3, 4, 5]


def test_spam_tracker_evicts_outside_window():
    trk = automod_service.SpamTracker()
    trk.record_and_count(1, 2, 3, window_seconds=5, now=0.0)
    trk.record_and_count(1, 2, 3, window_seconds=5, now=1.0)
    # t=10 is well past the 5s window → only the new message remains.
    assert trk.record_and_count(1, 2, 3, window_seconds=5, now=10.0) == 1


def test_spam_tracker_separates_keys():
    trk = automod_service.SpamTracker()
    trk.record_and_count(1, 2, 3, window_seconds=10, now=0.0)
    # Different channel → independent window.
    assert trk.record_and_count(1, 2, 99, window_seconds=10, now=0.0) == 1


def test_spam_tracker_cross_channel_accumulates_across_channels():
    trk = automod_service.SpamTracker()
    # Same guild/user, three DIFFERENT channels — the per-channel bucket
    # would see 1 in each; the cross-channel bucket must see all three.
    counts = [
        trk.record_and_count_any_channel(1, 2, window_seconds=10, now=float(t))
        for t in range(3)
    ]
    assert counts == [1, 2, 3]


def test_spam_tracker_cross_channel_is_independent_of_per_channel_buckets():
    trk = automod_service.SpamTracker()
    # Each message records into BOTH its per-channel bucket and the
    # cross-channel bucket, mirroring how evaluate() drives the tracker.
    trk.record_and_count(1, 2, 100, window_seconds=10, now=0.0)
    trk.record_and_count_any_channel(1, 2, window_seconds=10, now=0.0)
    trk.record_and_count(1, 2, 200, window_seconds=10, now=0.0)
    trk.record_and_count_any_channel(1, 2, window_seconds=10, now=0.0)
    # The per-channel bucket for 100 only ever saw itself + this new one = 2;
    # the cross-channel bucket saw all three messages regardless of channel.
    assert trk.record_and_count(1, 2, 100, window_seconds=10, now=0.0) == 2
    assert trk.record_and_count_any_channel(1, 2, window_seconds=10, now=0.0) == 3


# ---------------------------------------------------------------------------
# DuplicateTracker
# ---------------------------------------------------------------------------


def test_duplicate_tracker_counts_matching_content():
    trk = automod_service.DuplicateTracker()
    counts = [
        trk.record_and_count(1, 2, "buy gold now", window_seconds=10, now=float(t))
        for t in range(3)
    ]
    assert counts == [1, 2, 3]


def test_duplicate_tracker_ignores_different_content():
    trk = automod_service.DuplicateTracker()
    trk.record_and_count(1, 2, "hello", window_seconds=10, now=0.0)
    # Different content in the same window → its own count of 1, not 2.
    assert trk.record_and_count(1, 2, "goodbye", window_seconds=10, now=0.0) == 1


def test_duplicate_tracker_normalizes_case_and_whitespace():
    trk = automod_service.DuplicateTracker()
    trk.record_and_count(1, 2, "Buy Gold Now", window_seconds=10, now=0.0)
    assert trk.record_and_count(1, 2, "buy   gold   now", window_seconds=10, now=0.0) == 2


def test_duplicate_tracker_ignores_empty_content():
    trk = automod_service.DuplicateTracker()
    trk.record_and_count(1, 2, "", window_seconds=10, now=0.0)
    # Blank messages never count toward a duplicate trip.
    assert trk.record_and_count(1, 2, "   ", window_seconds=10, now=0.0) == 0


def test_duplicate_tracker_evicts_outside_window():
    trk = automod_service.DuplicateTracker()
    trk.record_and_count(1, 2, "spam", window_seconds=5, now=0.0)
    trk.record_and_count(1, 2, "spam", window_seconds=5, now=1.0)
    assert trk.record_and_count(1, 2, "spam", window_seconds=5, now=10.0) == 1


# ---------------------------------------------------------------------------
# evaluate — rule ordering + exemptions
# ---------------------------------------------------------------------------


def _policy(**overrides) -> AutomodPolicy:
    base = dict(enabled=True)
    base.update(overrides)
    return AutomodPolicy(**base)


def test_evaluate_returns_none_when_nothing_enabled():
    assert automod_service.evaluate(_msg(content="hi"), _policy()) is None


def test_evaluate_invite_rule():
    v = automod_service.evaluate(
        _msg(content="discord.gg/abc"), _policy(invites_enabled=True)
    )
    assert v is not None and v.rule == "automod.invite_link"


def test_evaluate_caps_rule():
    v = automod_service.evaluate(
        _msg(content="STOP YELLING AT EVERYONE"),
        _policy(caps_enabled=True, caps_percent=70),
    )
    assert v is not None and v.rule == "automod.caps"


def test_evaluate_mass_mentions_rule():
    v = automod_service.evaluate(
        _msg(content="hi", mentions=5),
        _policy(mentions_enabled=True, mentions_count=4),
    )
    assert v is not None and v.rule == "automod.mass_mentions"


def test_evaluate_spam_rule_trips_on_burst():
    trk = automod_service.SpamTracker()
    pol = _policy(spam_enabled=True, spam_count=3, spam_window_seconds=10)
    verdicts = [
        automod_service.evaluate(_msg(content="spam"), pol, now=float(t), tracker=trk)
        for t in range(3)
    ]
    assert verdicts[0] is None and verdicts[1] is None
    assert verdicts[2] is not None and verdicts[2].rule == "automod.spam"


def test_evaluate_exempt_channel_short_circuits():
    pol = _policy(invites_enabled=True, exempt_channel_ids=frozenset({100}))
    assert automod_service.evaluate(_msg(content="discord.gg/x"), pol) is None


def test_evaluate_exempt_role_short_circuits():
    pol = _policy(invites_enabled=True, exempt_role_ids=frozenset({77}))
    msg = _msg(content="discord.gg/x", role_ids=(77,))
    assert automod_service.evaluate(msg, pol) is None


def test_evaluate_cross_channel_spam_rule_trips_across_channels():
    trk = automod_service.SpamTracker()
    pol = _policy(cross_channel_spam_enabled=True, cross_channel_spam_count=3)
    verdicts = [
        automod_service.evaluate(
            _msg(content=f"msg {t}", channel_id=100 + t),
            pol,
            now=float(t),
            tracker=trk,
        )
        for t in range(3)
    ]
    # A per-channel spam burst would never trip here — every message lands in
    # a different channel — but the cross-channel counter must still catch it.
    assert verdicts[0] is None and verdicts[1] is None
    assert verdicts[2] is not None and verdicts[2].rule == "automod.cross_channel_spam"


def test_evaluate_duplicate_rule_trips_on_repeated_content():
    dup_trk = automod_service.DuplicateTracker()
    pol = _policy(duplicate_enabled=True, duplicate_count=3)
    verdicts = [
        automod_service.evaluate(
            _msg(content="buy gold now"),
            pol,
            now=float(t),
            duplicate_tracker=dup_trk,
        )
        for t in range(3)
    ]
    assert verdicts[0] is None and verdicts[1] is None
    assert verdicts[2] is not None and verdicts[2].rule == "automod.duplicate"


def test_evaluate_duplicate_rule_does_not_trip_on_a_burst_of_different_messages():
    """The owner's exact concern: different messages, even fast, must not trip
    the duplicate rule — only repeated identical content should."""
    dup_trk = automod_service.DuplicateTracker()
    pol = _policy(duplicate_enabled=True, duplicate_count=3)
    verdicts = [
        automod_service.evaluate(
            _msg(content=f"message number {t}"),
            pol,
            now=float(t),
            duplicate_tracker=dup_trk,
        )
        for t in range(5)
    ]
    assert all(v is None for v in verdicts)


def test_evaluate_cross_channel_spam_exempt_role_short_circuits():
    pol = _policy(
        cross_channel_spam_enabled=True,
        cross_channel_spam_count=1,
        exempt_role_ids=frozenset({77}),
    )
    msg = _msg(content="hi", role_ids=(77,))
    assert automod_service.evaluate(msg, pol) is None
