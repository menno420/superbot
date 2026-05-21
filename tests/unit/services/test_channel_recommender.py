"""Tests for ``services.channel_recommender`` — intent → ranked channels."""

from __future__ import annotations

import pytest

from services.channel_recommender import (
    INTENTS,
    ChannelRecommendation,
    get_intent,
    known_intent_slugs,
    recommend,
    recommend_all,
    top_pick,
)
from services.guild_snapshot import ChannelMeta, GuildSnapshot


def _channel(
    name: str,
    *,
    channel_id: int = 1,
    type_: str = "text",
    can_view: bool = True,
    can_send: bool = True,
    can_embed: bool = True,
    topic: str | None = None,
    parent_category: str | None = None,
    position: int = 0,
) -> ChannelMeta:
    return ChannelMeta(
        id=channel_id,
        name=name,
        type=type_,
        topic=topic,
        parent_category=parent_category,
        position=position,
        bot_can_view=can_view,
        bot_can_send=can_send,
        bot_can_embed=can_embed,
    )


def _snapshot(*channels: ChannelMeta) -> GuildSnapshot:
    return GuildSnapshot(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        channels=tuple(channels),
        categories=(),
        roles=(),
        settings_snapshot={},
        bindings_snapshot={},
        readiness_findings=(),
    )


# ---------------------------------------------------------------------------
# Intent catalogue
# ---------------------------------------------------------------------------


def test_known_intents_cover_documented_set():
    assert known_intent_slugs() == {
        "bot_commands",
        "logs",
        "mod_logs",
        "welcome",
        "general",
    }


@pytest.mark.parametrize("slug", sorted(known_intent_slugs()))
def test_get_intent_returns_match(slug):
    intent = get_intent(slug)
    assert intent is not None
    assert intent.slug == slug
    assert intent.label


def test_get_intent_returns_none_for_unknown():
    assert get_intent("does-not-exist") is None


# ---------------------------------------------------------------------------
# recommend — score / ranking / confidence
# ---------------------------------------------------------------------------


def test_recommend_returns_empty_for_unknown_intent():
    snap = _snapshot(_channel("general"))
    assert recommend("does-not-exist", snap) == []


def test_recommend_picks_tag_matching_channel_high_confidence():
    """A channel whose name matches the canonical tag pattern AND has
    full permissions should score "high"."""
    snap = _snapshot(_channel("bot-commands", channel_id=42))
    ranked = recommend("bot_commands", snap)
    assert len(ranked) == 1
    rec = ranked[0]
    assert rec.channel_id == 42
    assert rec.confidence == "high"
    assert rec.intent == "bot_commands"
    assert rec.action == "bind"
    assert any("pattern" in r.lower() for r in rec.reasons)


def test_recommend_keyword_hint_match_is_medium():
    """A non-canonical name that contains an intent keyword still
    surfaces but with lower confidence than a tag match."""
    snap = _snapshot(_channel("the-bot-zone", channel_id=42))
    ranked = recommend("bot_commands", snap)
    assert len(ranked) == 1
    assert ranked[0].confidence in ("medium", "low")


def test_recommend_drops_channels_with_no_signal():
    """A channel with neither a tag match nor a keyword hint should
    not appear in the ranked output at all."""
    snap = _snapshot(_channel("random-chatter"))
    assert recommend("bot_commands", snap) == []


def test_recommend_drops_channels_bot_cannot_view():
    """A channel matching the intent but invisible to the bot scores
    negatively and is excluded."""
    snap = _snapshot(_channel("bot-commands", can_view=False, can_send=False))
    assert recommend("bot_commands", snap) == []


def test_recommend_ranks_higher_score_first():
    """Tag match (+50) ranks above keyword hint (+25), all else equal."""
    snap = _snapshot(
        _channel("the-bot-zone", channel_id=1),
        _channel("bot-cmds", channel_id=2),
    )
    ranked = recommend("bot_commands", snap)
    assert [r.channel_id for r in ranked] == [2, 1]


def test_recommend_sorts_alphabetically_on_score_tie():
    """When two channels score identically the alphabetical name
    breaks the tie deterministically."""
    snap = _snapshot(
        _channel("zeta-commands", channel_id=1),
        _channel("alpha-commands", channel_id=2),
    )
    ranked = recommend("bot_commands", snap)
    assert ranked[0].channel_name == "alpha-commands"


def test_recommend_text_only():
    """Voice / category / forum channels never appear in the ranked
    list even if their name matches."""
    snap = _snapshot(
        _channel("bot-commands", channel_id=1, type_="voice"),
    )
    assert recommend("bot_commands", snap) == []


def test_recommend_general_intent_does_not_require_send():
    """The ``general`` intent is read-mostly; bot can score positively
    when it can view but cannot send."""
    snap = _snapshot(_channel("general", can_send=False))
    ranked = recommend("general", snap)
    assert ranked  # not empty


# ---------------------------------------------------------------------------
# top_pick / recommend_all
# ---------------------------------------------------------------------------


def test_top_pick_returns_first_recommendation():
    snap = _snapshot(
        _channel("the-bot-zone", channel_id=1),
        _channel("bot-cmds", channel_id=2),
    )
    pick = top_pick("bot_commands", snap)
    assert pick is not None
    assert pick.channel_id == 2


def test_top_pick_returns_none_when_no_matches():
    snap = _snapshot(_channel("random-chatter"))
    assert top_pick("bot_commands", snap) is None


def test_recommend_all_covers_every_intent_by_default():
    snap = _snapshot(
        _channel("mod-log", channel_id=1),
        _channel("welcome", channel_id=2),
    )
    results = recommend_all(snap)
    assert set(results.keys()) == set(INTENTS.keys())
    assert results["mod_logs"]
    assert results["welcome"]


def test_recommend_all_honours_explicit_intent_list():
    snap = _snapshot(_channel("general"))
    results = recommend_all(snap, intents=["general"])
    assert set(results.keys()) == {"general"}


# ---------------------------------------------------------------------------
# Reasons / metadata surface
# ---------------------------------------------------------------------------


def test_every_recommendation_carries_at_least_one_reason():
    snap = _snapshot(_channel("bot-commands"))
    rec = recommend("bot_commands", snap)[0]
    assert rec.reasons
    assert all(isinstance(r, str) and r for r in rec.reasons)


def test_recommendation_action_is_bind():
    """The recommender ranks EXISTING channels — every result is a
    'bind this' suggestion. Creating new channels is a separate path."""
    snap = _snapshot(_channel("bot-commands"))
    rec = recommend("bot_commands", snap)[0]
    assert rec.action == "bind"


def test_recommendation_immutable():
    """ChannelRecommendation is frozen so callers can stash refs."""
    snap = _snapshot(_channel("bot-commands"))
    rec = recommend("bot_commands", snap)[0]
    with pytest.raises(Exception):
        rec.score = 0  # type: ignore[misc]
