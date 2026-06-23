"""Setup plan + deterministic advisor — Phase 9f / Track 5 PR 12.

Defines the canonical recommendation shapes (``SetupRecommendation``
and ``SetupPlanDraft``) and ships the first advisor: a deterministic
name-matching engine that scans the :class:`GuildSnapshot` and
proposes binding choices based on a hand-written rule table.

The deterministic advisor never calls an LLM, never hits the
network, and never mutates anything. It exists as:

1. The fallback whenever the AI advisor is unavailable (no API key,
   provider override = ``deterministic``).
2. The verification baseline: AI suggestions are merged with
   deterministic ones, so AI must clear at least the same bar.

Public surface:

* :class:`Confidence` — literal ``"high" | "medium" | "low"``.
* :class:`SetupRecommendation` — single proposed binding.
* :class:`SetupPlanDraft` — bundle of recommendations + rejection
  diagnostics.
* :class:`DeterministicAdvisor` — wraps the matching logic.

The advisor produces a recommendation only when every output is
validated against the live :func:`subsystem_schema.all_schemas`:

* The ``subsystem`` must be a registered schema.
* The ``binding_name`` must appear in that schema's ``bindings``.
* The :class:`BindingKind` must match the proposed resource kind.

Anything that fails validation is dropped and a one-line reason is
attached to :attr:`SetupPlanDraft.dropped`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from services.guild_snapshot import GuildSnapshot

logger = logging.getLogger("bot.services.setup_plan")

Confidence = Literal["high", "medium", "low"]

CONFIDENCES: frozenset[str] = frozenset({"high", "medium", "low"})

_CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}

# A recommendation either **binds** an existing resource (the original model —
# ``target_id`` points at a live channel/role/category) or proposes **creating**
# a new one (``target_id is None``; ``target_name`` is the name to create, which
# the provisioning pipeline then binds to ``subsystem.binding_name``).
RecommendationMode = Literal["bind", "create"]

RECOMMENDATION_MODES: frozenset[str] = frozenset({"bind", "create"})

# Resource kinds the bot can create on the operator's behalf (a ``create``
# recommendation of any other kind is invalid — we never fabricate members/threads).
CREATABLE_KINDS: frozenset[str] = frozenset({"channel", "role", "category"})


@dataclass(frozen=True)
class SetupRecommendation:
    """One proposed setup action for the wizard to surface to the operator.

    ``mode`` distinguishes binding an existing resource (``"bind"`` — the
    default; ``target_id`` is the live resource) from proposing a new one
    (``"create"`` — ``target_id is None`` and ``target_name`` is the name to
    create + bind).
    """

    subsystem: str
    binding_name: str
    target_kind: str  # "channel" / "category" / "role" / "thread" / "member"
    target_name: str
    confidence: Confidence
    reason: str
    target_id: int | None = None  # required for "bind"; None for "create"
    mode: RecommendationMode = "bind"
    source: str = "deterministic"

    def __post_init__(self) -> None:
        if self.confidence not in CONFIDENCES:
            raise ValueError(
                f"confidence must be one of {sorted(CONFIDENCES)}, "
                f"got {self.confidence!r}",
            )
        if self.mode not in RECOMMENDATION_MODES:
            raise ValueError(
                f"mode must be one of {sorted(RECOMMENDATION_MODES)}, "
                f"got {self.mode!r}",
            )
        if self.mode == "bind" and self.target_id is None:
            raise ValueError("a 'bind' recommendation requires a target_id")
        if self.mode == "create" and not self.target_name:
            raise ValueError("a 'create' recommendation requires a target_name")


@dataclass(frozen=True)
class SetupPlanDraft:
    """Aggregated output of an advisor run.

    ``recommendations`` carries the surviving proposals.
    ``dropped`` carries one-line reasons for every candidate that
    was filtered out — primarily as a debug aid so the wizard /
    operator can see why the advisor stayed silent on a slot.
    """

    recommendations: tuple[SetupRecommendation, ...] = ()
    dropped: tuple[str, ...] = ()
    source: str = "deterministic"

    def by_subsystem(self, subsystem: str) -> tuple[SetupRecommendation, ...]:
        return tuple(r for r in self.recommendations if r.subsystem == subsystem)

    def by_confidence(self, confidence: Confidence) -> tuple[SetupRecommendation, ...]:
        return tuple(r for r in self.recommendations if r.confidence == confidence)


# ---------------------------------------------------------------------------
# Rule table
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Rule:
    """One row in the deterministic matching table."""

    tokens: tuple[str, ...]
    subsystem: str
    binding_name: str
    expected_kind: str


_CHANNEL_RULES: tuple[_Rule, ...] = (
    _Rule(
        tokens=("rules", "server-rules", "info"),
        subsystem="logging",
        binding_name="rules_channel",
        expected_kind="channel",
    ),
    _Rule(
        tokens=("welcome", "start-here", "lobby"),
        subsystem="onboarding",
        binding_name="welcome_channel",
        expected_kind="channel",
    ),
    _Rule(
        tokens=("general", "chat", "main"),
        subsystem="general",
        binding_name="main_channel",
        expected_kind="channel",
    ),
    _Rule(
        tokens=("bot", "commands", "bot-commands"),
        subsystem="commands",
        binding_name="bot_channel",
        expected_kind="channel",
    ),
    _Rule(
        tokens=("mod-log", "moderation-log"),
        subsystem="logging",
        binding_name="mod_channel",
        expected_kind="channel",
    ),
    _Rule(
        tokens=("cleanup-log",),
        subsystem="logging",
        binding_name="cleanup_channel",
        expected_kind="channel",
    ),
    _Rule(
        tokens=("audit-log",),
        subsystem="logging",
        binding_name="audit_channel",
        expected_kind="channel",
    ),
    _Rule(
        tokens=("counting",),
        subsystem="counting",
        binding_name="channel",
        expected_kind="channel",
    ),
    _Rule(
        tokens=("economy", "coins", "shop"),
        subsystem="economy",
        binding_name="announce_channel",
        expected_kind="channel",
    ),
)


_CATEGORY_RULES: tuple[_Rule, ...] = (
    _Rule(
        tokens=("staff", "mod-chat", "admin"),
        subsystem="moderation",
        binding_name="staff_category",
        expected_kind="category",
    ),
)


# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------


def _confidence_for(name: str, token: str) -> Confidence:
    """Score a name against a token.

    * ``high``   — exact case-insensitive equality.
    * ``medium`` — name starts or ends with the token (still a clean
                   prefix/suffix match).
    * ``low``    — token appears anywhere else in the name (substring).
    """
    n = name.lower()
    t = token.lower()
    if n == t:
        return "high"
    if n.startswith(t) or n.endswith(t):
        return "medium"
    if t in n:
        return "low"
    # Caller only invokes us when we already know there's a match.
    return "low"


def _matches(name: str, token: str) -> bool:
    return token.lower() in name.lower()


def _best_match_for_rule(
    *,
    name: str,
    rule: _Rule,
    target_id: int,
    target_label: str,
) -> SetupRecommendation | None:
    """Return the highest-confidence recommendation across a rule's tokens.

    Considers every token in ``rule.tokens`` and keeps the strongest
    match (high > medium > low). Returns ``None`` when no token
    matches.
    """
    best: tuple[Confidence, str] | None = None
    for token in rule.tokens:
        if not _matches(name, token):
            continue
        confidence = _confidence_for(name, token)
        if best is None or _CONFIDENCE_ORDER[confidence] < _CONFIDENCE_ORDER[best[0]]:
            best = (confidence, token)
    if best is None:
        return None
    confidence, token = best
    reason = f"{target_label} `{name}` matches token `{token}` ({confidence})"
    return SetupRecommendation(
        subsystem=rule.subsystem,
        binding_name=rule.binding_name,
        target_kind=rule.expected_kind,
        target_id=target_id,
        target_name=name,
        confidence=confidence,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_against_schema(
    subsystem: str,
    binding_name: str,
    expected_kind: str,
) -> str | None:
    """Return ``None`` when the (subsystem, binding, kind) exists in
    ``subsystem_schema.all_schemas``; otherwise return a one-line
    drop reason.
    """
    try:
        from core.runtime.subsystem_schema import all_schemas
    except Exception:
        logger.exception(
            "setup_plan: subsystem_schema unavailable; dropping every "
            "deterministic recommendation.",
        )
        return "subsystem_schema unavailable"
    schemas = all_schemas() or {}
    schema = schemas.get(subsystem)
    if schema is None:
        return f"subsystem {subsystem!r} not registered"
    for spec in schema.bindings:
        if spec.name == binding_name:
            if spec.kind.value != expected_kind:
                return (
                    f"binding {subsystem}.{binding_name} has kind "
                    f"{spec.kind.value}, advisor proposed {expected_kind}"
                )
            return None
    return f"binding {subsystem}.{binding_name} not declared"


# ---------------------------------------------------------------------------
# Advisor
# ---------------------------------------------------------------------------


class DeterministicAdvisor:
    """Name-matching advisor over a :class:`GuildSnapshot`.

    Stateless — instantiate once or per-call.
    """

    async def suggest(self, snapshot: GuildSnapshot) -> SetupPlanDraft:
        """Return one :class:`SetupPlanDraft` per snapshot.

        For each channel + category in the snapshot, walk the rule
        table for a match. The best confidence per (subsystem,
        binding_name) wins so we never propose two channels for the
        same slot.
        """
        candidates: dict[tuple[str, str], SetupRecommendation] = {}
        dropped: list[str] = []

        # Channels
        for channel in snapshot.channels:
            for rule in _CHANNEL_RULES:
                rec = _best_match_for_rule(
                    name=channel.name,
                    rule=rule,
                    target_id=channel.id,
                    target_label="channel name",
                )
                if rec is not None:
                    self._merge(candidates, rec)

        # Categories
        for cat in snapshot.categories:
            for rule in _CATEGORY_RULES:
                rec = _best_match_for_rule(
                    name=cat.name,
                    rule=rule,
                    target_id=cat.id,
                    target_label="category",
                )
                if rec is not None:
                    self._merge(candidates, rec)

        # Validate every survivor; drop anything not in schema.
        validated: list[SetupRecommendation] = []
        for rec in candidates.values():
            drop = _validate_against_schema(
                rec.subsystem,
                rec.binding_name,
                rec.target_kind,
            )
            if drop is not None:
                dropped.append(
                    f"{rec.subsystem}.{rec.binding_name}: {drop}",
                )
                continue
            validated.append(rec)

        validated.sort(
            key=lambda r: (
                _CONFIDENCE_ORDER[r.confidence],
                r.subsystem,
                r.binding_name,
            ),
        )

        return SetupPlanDraft(
            recommendations=tuple(validated),
            dropped=tuple(dropped),
        )

    @staticmethod
    def _merge(
        bucket: dict[tuple[str, str], SetupRecommendation],
        rec: SetupRecommendation,
    ) -> None:
        """Keep the highest-confidence recommendation per (subsystem,
        binding_name).
        """
        key = (rec.subsystem, rec.binding_name)
        existing = bucket.get(key)
        if (
            existing is None
            or _CONFIDENCE_ORDER[rec.confidence]
            < _CONFIDENCE_ORDER[existing.confidence]
        ):
            bucket[key] = rec


__all__ = [
    "CONFIDENCES",
    "Confidence",
    "DeterministicAdvisor",
    "SetupPlanDraft",
    "SetupRecommendation",
]
