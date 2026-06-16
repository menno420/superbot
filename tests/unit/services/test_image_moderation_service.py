"""Unit tests for the pure image-moderation detection logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from services.image_moderation_config import ImageModerationPolicy
from services.image_moderation_service import (
    CATEGORY_BUCKETS,
    ImageModerationVerdict,
    bucket_score,
    evaluate_scores,
    image_attachment_urls,
)


def _attachment(*, url="http://cdn/x.png", content_type="image/png", filename="x.png"):
    att = MagicMock()
    att.url = url
    att.content_type = content_type
    att.filename = filename
    return att


# ---------------------------------------------------------------------------
# image_attachment_urls
# ---------------------------------------------------------------------------


def test_image_attachments_filtered_by_content_type():
    msg = MagicMock()
    msg.attachments = [
        _attachment(url="http://cdn/a.png", content_type="image/png"),
        _attachment(url="http://cdn/b.txt", content_type="text/plain", filename="b.txt"),
    ]
    assert image_attachment_urls(msg) == ["http://cdn/a.png"]


def test_image_attachments_detected_by_extension_when_content_type_missing():
    msg = MagicMock()
    msg.attachments = [
        _attachment(url="http://cdn/c.JPG", content_type=None, filename="c.JPG"),
        _attachment(url="http://cdn/d.zip", content_type=None, filename="d.zip"),
    ]
    assert image_attachment_urls(msg) == ["http://cdn/c.JPG"]


def test_no_attachments_returns_empty():
    msg = MagicMock()
    msg.attachments = []
    assert image_attachment_urls(msg) == []


# ---------------------------------------------------------------------------
# bucket_score
# ---------------------------------------------------------------------------


def test_bucket_score_takes_max_across_raw_categories():
    # "sexual" bucket covers both "sexual" and "sexual/minors" — worst wins.
    scores = {"sexual": 0.3, "sexual/minors": 0.91}
    assert bucket_score(scores, "sexual") == 0.91


def test_bucket_score_missing_category_is_zero():
    assert bucket_score({}, "hate") == 0.0


def test_every_bucket_has_raw_keys():
    for bucket, raw in CATEGORY_BUCKETS.items():
        assert raw, bucket


# ---------------------------------------------------------------------------
# evaluate_scores
# ---------------------------------------------------------------------------


def test_flags_when_enabled_category_exceeds_threshold():
    policy = ImageModerationPolicy(
        enabled=True,
        sexual_enabled=True,
        threshold_percent=80,
    )
    verdict = evaluate_scores({"sexual": 0.95}, policy)
    assert isinstance(verdict, ImageModerationVerdict)
    assert verdict.category == "sexual"
    assert verdict.rule == "image_moderation.sexual"
    assert verdict.score == 0.95


def test_no_flag_below_threshold():
    policy = ImageModerationPolicy(
        enabled=True,
        sexual_enabled=True,
        threshold_percent=80,
    )
    assert evaluate_scores({"sexual": 0.79}, policy) is None


def test_threshold_is_inclusive():
    policy = ImageModerationPolicy(
        enabled=True,
        violence_enabled=True,
        threshold_percent=80,
    )
    assert evaluate_scores({"violence": 0.80}, policy) is not None


def test_disabled_category_is_not_flagged_even_above_threshold():
    # hate score is high, but only the sexual category is enabled.
    policy = ImageModerationPolicy(
        enabled=True,
        sexual_enabled=True,
        hate_enabled=False,
        threshold_percent=80,
    )
    assert evaluate_scores({"hate": 0.99}, policy) is None


def test_first_bucket_in_order_wins():
    # Both sexual and violence trip; sexual is first in _BUCKET_ORDER.
    policy = ImageModerationPolicy(
        enabled=True,
        sexual_enabled=True,
        violence_enabled=True,
        threshold_percent=80,
    )
    verdict = evaluate_scores({"sexual": 0.90, "violence": 0.99}, policy)
    assert verdict is not None and verdict.category == "sexual"
