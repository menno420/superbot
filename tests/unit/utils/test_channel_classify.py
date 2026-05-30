"""Tests for the canonical channel-name classifier (``utils.channel_classify``).

The classifier moved here from ``views.setup.scan_panel`` to remove the
zero-tolerance ``services/ → views/`` import (arch-fix-1).  These tests
pin the canonical home directly and assert the legacy re-export still
resolves to the *same* object, so a regression that re-copies the
function back into ``views/`` is caught.
"""

from __future__ import annotations

import pytest

from utils.channel_classify import classify_channel_name


@pytest.mark.parametrize(
    ("name", "expected_tag"),
    [
        ("mod-log", "likely_log"),
        ("mod-log", "likely_mod_log"),
        ("audit-log", "likely_log"),
        ("bot-logs", "likely_log"),
        ("bot-commands", "likely_bot_cmd"),
        ("bot-cmd", "likely_bot_cmd"),
        ("bot-spam", "likely_bot_cmd"),
        ("admin-only", "likely_admin"),
        ("owner", "likely_admin"),
        ("staff", "likely_mod"),
        ("moderation", "likely_mod"),
        ("counting", "likely_counting"),
        ("mining", "likely_mining"),
        ("games", "likely_game"),
        ("casino", "likely_game"),
        ("blackjack", "likely_game"),
        ("general", "likely_general"),
        ("lobby", "likely_general"),
        ("welcome", "likely_welcome"),
        ("proofs", "likely_proof"),
    ],
)
def test_classifier_matches_documented_patterns(name: str, expected_tag: str):
    assert expected_tag in classify_channel_name(name)


@pytest.mark.parametrize(
    "name",
    ["off-topic", "introductions", "random", "deals", "art"],
)
def test_classifier_returns_empty_for_unmatched_names(name: str):
    assert classify_channel_name(name) == ()


def test_classifier_returns_empty_for_empty_name():
    assert classify_channel_name("") == ()


def test_classifier_is_case_insensitive():
    assert "likely_log" in classify_channel_name("MOD-LOG")
    assert "likely_general" in classify_channel_name("General")


def test_classifier_returns_tags_sorted():
    """Sort guarantees deterministic embed output."""
    tags = classify_channel_name("mod-log")
    assert list(tags) == sorted(tags)


def test_legacy_scan_panel_reexport_is_same_object():
    """The setup scan panel re-exports the canonical function, not a copy.

    Guards against re-introducing the ``services/ → views/`` breach by
    copying the classifier back into ``views/``.
    """
    from views.setup import scan_panel

    assert scan_panel.classify_channel_name is classify_channel_name


def test_consumers_import_from_utils_not_views():
    """The three services use the canonical ``utils`` home directly."""
    from services import (
        channel_recommender,
        cleanup_profiles,
        cog_routing_profiles,
    )

    assert channel_recommender.classify_channel_name is classify_channel_name
    assert cleanup_profiles.classify_channel_name is classify_channel_name
    assert cog_routing_profiles.classify_channel_name is classify_channel_name
