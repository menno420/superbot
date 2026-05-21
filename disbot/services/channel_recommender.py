"""Per-intent channel recommendation scoring.

Given a :class:`services.guild_snapshot.GuildSnapshot` and a target
"intent" (e.g. ``"bot_commands"``, ``"mod_logs"``), returns a ranked
list of channels with a numeric score, a confidence bucket, and a
human-readable reason list. The wizard's channels section can use
these to:

* Pick a top match automatically (high-confidence path).
* Render runners-up under a "More options" disclosure.
* Surface the reason list so operators know *why* a channel was
  picked — directly addresses the user's "Every suggestion should
  show: reason; confidence; current permissions" requirement.

The scorer is intentionally simple and deterministic:

* +50 if the channel's name matches a classifier tag the intent
  cares about (uses :func:`views.setup.scan_panel.classify_channel_name`
  so improvements there flow into recommendations).
* +20 if the bot has view + send + embed permission.
* +10 if the bot can view but not send (still helpful for log-only
  intents that don't need write access).
* −30 if the bot can't view at all.

Confidence buckets: ``high`` (≥60), ``medium`` (≥30), ``low``
otherwise. Channels with non-positive scores are dropped.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from services.guild_snapshot import ChannelMeta, GuildSnapshot
from views.setup.scan_panel import classify_channel_name

Confidence = Literal["high", "medium", "low"]
Action = Literal["bind", "create"]


@dataclass(frozen=True)
class ChannelRecommendation:
    """One channel suggested for one binding intent."""

    channel_id: int
    channel_name: str
    intent: str
    score: int
    confidence: Confidence
    reasons: tuple[str, ...]
    action: Action  # "bind" = pick existing; "create" = create new


# ---------------------------------------------------------------------------
# Intent catalogue
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Intent:
    slug: str
    label: str
    tags: tuple[str, ...]
    requires_send: bool  # intents that need write access score perms harder
    keyword_hints: tuple[str, ...] = ()


INTENTS: dict[str, Intent] = {
    "bot_commands": Intent(
        slug="bot_commands",
        label="Bot commands / spam",
        tags=("likely_bot_cmd",),
        requires_send=True,
        keyword_hints=("bot", "commands", "cmds", "spam"),
    ),
    "logs": Intent(
        slug="logs",
        label="General log channel",
        tags=("likely_log",),
        requires_send=True,
        keyword_hints=("log", "audit"),
    ),
    "mod_logs": Intent(
        slug="mod_logs",
        label="Moderation log",
        tags=("likely_mod_log", "likely_log"),
        requires_send=True,
        keyword_hints=("mod-log", "mod_log", "moderation"),
    ),
    "welcome": Intent(
        slug="welcome",
        label="Welcome / intro",
        tags=("likely_welcome",),
        requires_send=True,
        keyword_hints=("welcome", "intro"),
    ),
    "general": Intent(
        slug="general",
        label="General chat",
        tags=("likely_general",),
        requires_send=False,
        keyword_hints=("general", "lobby", "chat"),
    ),
}


def known_intent_slugs() -> frozenset[str]:
    return frozenset(INTENTS.keys())


def get_intent(slug: str) -> Intent | None:
    return INTENTS.get(slug)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


_TAG_MATCH_BONUS = 50
_KEYWORD_HINT_BONUS = 25
_PERMS_OK_BONUS = 20
_PERMS_PARTIAL_BONUS = 10
_PERMS_NONE_PENALTY = -30


def _confidence_bucket(score: int) -> Confidence:
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _channel_score(
    channel: ChannelMeta,
    intent: Intent,
) -> tuple[int, tuple[str, ...]] | None:
    """Return ``(score, reasons)`` for ``channel`` against ``intent``,
    or ``None`` when the channel does not qualify (text channels only,
    bot must be able to view, score must be positive).
    """
    if channel.type != "text":
        return None
    # Hard exclusion: if the bot can't see the channel at all, it cannot
    # be a useful recommendation regardless of name match.
    if not channel.bot_can_view:
        return None

    name = channel.name or ""
    tags = classify_channel_name(name)
    score = 0
    reasons: list[str] = []

    tag_match = next((t for t in intent.tags if t in tags), None)
    if tag_match:
        score += _TAG_MATCH_BONUS
        reasons.append(f"Name matches `{tag_match}` pattern")
    else:
        # Fall back to a softer keyword check so channels without
        # canonical naming (e.g. "bot-shenanigans") still surface.
        lowered = name.lower()
        hit = next(
            (h for h in intent.keyword_hints if h in lowered),
            None,
        )
        if hit:
            score += _KEYWORD_HINT_BONUS
            reasons.append(f"Name contains `{hit}`")

    if score == 0:
        # Channel doesn't match the intent at all.
        return None

    # bot_can_view is guaranteed by the hard exclusion above.
    if channel.bot_can_send and channel.bot_can_embed:
        score += _PERMS_OK_BONUS
        reasons.append("Bot has view + send + embed")
    elif channel.bot_can_send:
        score += _PERMS_PARTIAL_BONUS
        reasons.append("Bot can send but not embed")
    elif not intent.requires_send:
        score += _PERMS_PARTIAL_BONUS
        reasons.append("Bot can view (intent does not require send)")
    else:
        # Can view but not send; if the intent needs send, mild penalty.
        score += -10
        reasons.append("Bot cannot send in this channel")

    if score <= 0:
        return None
    return score, tuple(reasons)


def recommend(
    intent_slug: str,
    snapshot: GuildSnapshot,
) -> list[ChannelRecommendation]:
    """Return ranked recommendations for ``intent_slug``, highest score
    first. Returns an empty list when the intent is unknown or no
    channel scores positively.
    """
    intent = INTENTS.get(intent_slug)
    if intent is None:
        return []

    matches: list[ChannelRecommendation] = []
    for ch in snapshot.channels:
        scored = _channel_score(ch, intent)
        if scored is None:
            continue
        score, reasons = scored
        matches.append(
            ChannelRecommendation(
                channel_id=ch.id,
                channel_name=ch.name,
                intent=intent.slug,
                score=score,
                confidence=_confidence_bucket(score),
                reasons=reasons,
                action="bind",
            ),
        )
    matches.sort(key=lambda r: (-r.score, r.channel_name))
    return matches


def top_pick(
    intent_slug: str,
    snapshot: GuildSnapshot,
) -> ChannelRecommendation | None:
    """Convenience: return the single top recommendation, or ``None``
    if there are no matches.
    """
    ranked = recommend(intent_slug, snapshot)
    return ranked[0] if ranked else None


def recommend_all(
    snapshot: GuildSnapshot,
    intents: Iterable[str] | None = None,
) -> dict[str, list[ChannelRecommendation]]:
    """Return ``{intent_slug: ranked_recommendations}`` for every intent
    in ``intents`` (or every documented intent when ``None``).
    """
    slugs = list(intents) if intents is not None else list(INTENTS.keys())
    return {slug: recommend(slug, snapshot) for slug in slugs}


__all__ = [
    "Action",
    "ChannelRecommendation",
    "Confidence",
    "INTENTS",
    "Intent",
    "get_intent",
    "known_intent_slugs",
    "recommend",
    "recommend_all",
    "top_pick",
]
