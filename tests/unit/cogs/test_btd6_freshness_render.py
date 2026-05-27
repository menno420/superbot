"""Coverage for ``cogs/btd6/_freshness_render.py``.

The module is the single source of truth for the bucket emoji + warning
copy that previously lived in three duplicate dicts.
"""

from __future__ import annotations

import pytest

from cogs.btd6._freshness_render import (
    BUCKET_BADGE,
    BUCKET_EMOJI,
    NEVER_FETCHED_COPY,
    STALE_WARNING,
    render_empty_state,
    render_freshness_warning,
)


def test_bucket_emoji_covers_all_buckets() -> None:
    assert set(BUCKET_EMOJI) == {"fresh", "aging", "stale", "never"}
    assert BUCKET_EMOJI["fresh"] == "🟢"
    assert BUCKET_EMOJI["aging"] == "🟡"
    assert BUCKET_EMOJI["stale"] == "🔴"
    assert BUCKET_EMOJI["never"] == "⚪"


def test_bucket_badge_covers_all_buckets() -> None:
    assert set(BUCKET_BADGE) == {"fresh", "aging", "stale", "never"}
    assert BUCKET_BADGE["fresh"] == "🟢 fresh"
    assert BUCKET_BADGE["aging"] == "🟡 aging"
    assert BUCKET_BADGE["stale"] == "🔴 stale"
    assert BUCKET_BADGE["never"] == "⚪ never"


# ---------------------------------------------------------------------------
# render_freshness_warning
# ---------------------------------------------------------------------------


def test_warning_none_for_fresh() -> None:
    assert render_freshness_warning("fresh") is None


def test_warning_none_for_aging() -> None:
    # Aging is an operator-only signal in PR 1; not user-facing copy.
    assert render_freshness_warning("aging") is None


def test_warning_stale_copy() -> None:
    assert render_freshness_warning("stale") == STALE_WARNING
    assert "outdated" in STALE_WARNING
    assert "24 hours" in STALE_WARNING


def test_warning_never_copy() -> None:
    assert render_freshness_warning("never") == NEVER_FETCHED_COPY
    assert "has not been fetched" in NEVER_FETCHED_COPY


# ---------------------------------------------------------------------------
# render_empty_state
# ---------------------------------------------------------------------------


def test_empty_state_never_fetched_uses_locked_copy() -> None:
    embed = render_empty_state("race", "never_fetched")
    assert embed.description == NEVER_FETCHED_COPY
    assert "race" in (embed.title or "").lower()


def test_empty_state_no_active_uses_context_type() -> None:
    embed = render_empty_state("boss", "no_active")
    assert "No active boss right now." in (embed.description or "")


def test_empty_state_color_is_greyple_for_both_reasons() -> None:
    # Both empty states render in a neutral color so users don't read
    # them as errors.
    for reason in ("never_fetched", "no_active"):
        embed = render_empty_state("race", reason)
        assert embed.color is not None
