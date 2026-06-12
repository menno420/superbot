"""UX pattern registry — the durable metadata behind every UX Lab exhibit.

Each exhibit in the UX Lab (``views/ux_lab/``) registers a :class:`PatternSpec`
here. The registry is the source of the lab's spec cards, the Home panel's
coverage counts, and (plan PR C) the generated ``docs/ux/pattern-library.md``
export. Pattern ids are the shared design vocabulary future plans reference
("use ``danger_confirm_then_result``").

Layer rules: this package imports stdlib + discord only (``utils/`` contract).
It owns no state besides the in-process registry dict and performs no I/O.

Design reference: ``docs/planning/ux-lab-interface-gallery-plan-2026-06-12.md``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

_PATTERN_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


class PatternCategory(str, Enum):
    """The UX Lab wing a pattern belongs to."""

    BUTTONS = "buttons"
    SELECTS = "selects"
    MODALS = "modals"
    EMBEDS = "embeds"
    LAYOUT_V2 = "layout_v2"
    IMAGE = "image"
    MOCKUP = "mockup"
    PROBE = "probe"


class PatternStatus(str, Enum):
    """Adoption status — drives the spec-card colour and the library export."""

    STABLE = "stable"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


@dataclass(frozen=True)
class PatternSpec:
    """Metadata for one reusable UX pattern.

    ``pattern_id`` is the durable vocabulary token. ``adopted_by`` grows as
    real views adopt the pattern (updated by the session that adopts it).
    """

    pattern_id: str
    title: str
    category: PatternCategory
    status: PatternStatus
    recommended_for: tuple[str, ...]
    limits: tuple[str, ...]
    anti_patterns: tuple[str, ...] = ()
    adopted_by: tuple[str, ...] = ()
    uses_components_v2: bool = False
    requires_pil: bool = False
    requires_modal: bool = False
    notes: str = ""


REGISTRY: dict[str, PatternSpec] = {}


def register(spec: PatternSpec) -> PatternSpec:
    """Add *spec* to the registry; raise on duplicate or malformed ids."""
    if not _PATTERN_ID_RE.match(spec.pattern_id):
        raise ValueError(
            f"pattern_id {spec.pattern_id!r} is not snake_case "
            "(^[a-z][a-z0-9_]{2,63}$)",
        )
    if spec.pattern_id in REGISTRY:
        raise ValueError(f"duplicate pattern_id {spec.pattern_id!r}")
    REGISTRY[spec.pattern_id] = spec
    return spec


def get_spec(pattern_id: str) -> PatternSpec:
    """Return the registered spec; raise ``KeyError`` with a helpful message."""
    try:
        return REGISTRY[pattern_id]
    except KeyError:
        raise KeyError(
            f"unknown pattern_id {pattern_id!r} — register it in the wing module",
        ) from None


def specs_for(category: PatternCategory) -> tuple[PatternSpec, ...]:
    """All specs in *category*, in registration order."""
    return tuple(s for s in REGISTRY.values() if s.category is category)


def category_counts() -> dict[PatternCategory, int]:
    """Registered-pattern count per category (the Home coverage line)."""
    counts: dict[PatternCategory, int] = {c: 0 for c in PatternCategory}
    for spec in REGISTRY.values():
        counts[spec.category] += 1
    return counts


def validate_registry() -> list[str]:
    """Return completeness problems (empty = healthy). Pinned by unit test."""
    problems: list[str] = []
    for spec in REGISTRY.values():
        if not spec.title.strip():
            problems.append(f"{spec.pattern_id}: empty title")
        if not spec.recommended_for:
            problems.append(f"{spec.pattern_id}: recommended_for is empty")
        if not spec.limits:
            problems.append(f"{spec.pattern_id}: limits is empty")
    return problems


@dataclass(frozen=True)
class ProbeResult:
    """Outcome of one platform-limit probe (rendered by the probe bench)."""

    probe_id: str
    title: str
    ok: bool
    detail: str
    extras: tuple[str, ...] = ()
