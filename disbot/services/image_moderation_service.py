"""Image-moderation detection logic — pure, unit-testable, no Discord/SDK I/O.

image moderation v1 (owner decision Q-0108).  This module decides **whether** a
set of OpenAI moderation category scores trips the guild's policy, and which
message attachments are images worth scanning.  It does **not** call OpenAI
(that is :mod:`core.runtime.ai.providers.openai_moderation`) and it does **not**
act (delete + warn is done by ``cogs.image_moderation.listener`` through
:mod:`services.moderation_service`, so escalation and audit stay one authority —
the same shape as :mod:`services.automod_service`).

Public surface:

    ImageModerationVerdict          — (category, score, reason) for a flagged image
    CATEGORY_BUCKETS                — owner-named bucket → raw OpenAI category keys
    image_attachment_urls(message)  — the scannable image attachment URLs
    bucket_score(scores, bucket)    — the worst raw score in a bucket
    evaluate_scores(scores, policy) -> ImageModerationVerdict | None

The four owner-named buckets (sexual · violence · harassment · hate) each map to
the raw ``omni-moderation`` category keys; a bucket's score is the **max** of its
raw categories, so the most-severe signal in the bucket drives the verdict.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

# Owner-named buckets (Q-0108: "sexual / violence / harassment / hate") → the
# raw omni-moderation category keys each one covers.  A bucket trips on the
# worst raw score it contains, so e.g. "sexual" also catches "sexual/minors".
CATEGORY_BUCKETS: dict[str, tuple[str, ...]] = {
    "sexual": ("sexual", "sexual/minors"),
    "violence": ("violence", "violence/graphic"),
    "harassment": ("harassment", "harassment/threatening"),
    "hate": ("hate", "hate/threatening"),
}

# Evaluation order — stable so the *first* tripped bucket is deterministic
# regardless of dict iteration order (matches CATEGORY_BUCKETS insertion).
_BUCKET_ORDER: tuple[str, ...] = ("sexual", "violence", "harassment", "hate")

# Filenames the bot treats as images even when Discord reports no content_type.
_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".heic", ".heif"},
)


@dataclass(frozen=True)
class ImageModerationVerdict:
    """A flagged image.

    ``category`` is the owner-named bucket id (``"sexual"``/``"violence"``/…)
    used for the ``image_moderation.flagged`` event + the ``mod_logs`` rule
    suffix; ``score`` is the worst raw score in that bucket (0..1); ``reason``
    is the human-readable attribution shown in the moderation audit.
    """

    category: str
    score: float
    reason: str

    @property
    def rule(self) -> str:
        """The machine-readable rule id for the moderation audit row."""
        return f"image_moderation.{self.category}"


def _is_image_attachment(attachment: Any) -> bool:
    """True when ``attachment`` looks like an image (content-type or extension).

    Uses ``getattr`` so it works against both ``discord.Attachment`` and
    lightweight test doubles.
    """
    content_type = getattr(attachment, "content_type", None)
    if isinstance(content_type, str) and content_type.lower().startswith("image/"):
        return True
    filename = getattr(attachment, "filename", None) or ""
    lowered = filename.lower()
    return any(lowered.endswith(ext) for ext in _IMAGE_EXTENSIONS)


def image_attachment_urls(message: Any) -> list[str]:
    """Return the URLs of every image attachment on ``message`` (order-preserving).

    Non-image attachments (text files, archives, …) are skipped, so a guild that
    enables image moderation pays the per-image API cost only on actual images.
    """
    urls: list[str] = []
    for attachment in getattr(message, "attachments", None) or []:
        if not _is_image_attachment(attachment):
            continue
        url = getattr(attachment, "url", None)
        if isinstance(url, str) and url:
            urls.append(url)
    return urls


def bucket_score(scores: Mapping[str, float], bucket: str) -> float:
    """The worst (max) raw category score within ``bucket`` (0.0 when absent)."""
    raw_keys = CATEGORY_BUCKETS.get(bucket, ())
    best = 0.0
    for key in raw_keys:
        value = scores.get(key)
        if value is not None and value > best:
            best = float(value)
    return best


def evaluate_scores(
    scores: Mapping[str, float],
    policy: Any,
) -> ImageModerationVerdict | None:
    """Return the first tripped bucket for ``scores`` under ``policy``, or None.

    The caller is responsible only for having confirmed ``policy.enabled``.  A
    bucket trips when (a) its per-bucket flag is on **and** (b) its worst raw
    score reaches ``policy.threshold_percent`` (as a fraction).  Buckets are
    tested in the fixed :data:`_BUCKET_ORDER` so the verdict is deterministic.
    """
    threshold = policy.threshold_percent / 100.0
    for bucket in _BUCKET_ORDER:
        if not _bucket_enabled(policy, bucket):
            continue
        score = bucket_score(scores, bucket)
        if score >= threshold:
            return ImageModerationVerdict(
                category=bucket,
                score=score,
                reason=(
                    f"Image flagged: {bucket} "
                    f"({score * 100:.0f}% >= {policy.threshold_percent}%)"
                ),
            )
    return None


def _bucket_enabled(policy: Any, bucket: str) -> bool:
    """Whether ``bucket``'s per-category flag is enabled on ``policy``."""
    return bool(getattr(policy, f"{bucket}_enabled", False))


__all__ = [
    "CATEGORY_BUCKETS",
    "ImageModerationVerdict",
    "bucket_score",
    "evaluate_scores",
    "image_attachment_urls",
]
