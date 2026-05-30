"""Canonical BTD6 upgrade / crosspath code logic.

A tower's upgrade state is a three-digit code ``[P1][P2][P3]`` where each digit
is that path's tier (0-5). BTD6's upgrade rule: one path may reach any tier
(0-5), a *second* path may reach at most tier 2, and the third path must stay at
0 — the classic "5-2-0" crosspath restriction.

This module is the single source of truth for validating, classifying, and
labelling those codes. The parser, the stats service, the embed renderer, the AI
grounding layer, and the Pro-view picker all defer to it so none of them
re-derive the primary path with the old "first non-zero digit" shortcut (which
is wrong for two-non-zero crosspaths such as ``2-0-2``).

Pure / stdlib-only — safe for every layer (``utils`` -> services / views /
scripts).
"""

from __future__ import annotations

from collections.abc import Iterable

# The 16 single-path codes: base + each path's five tiers, in display order.
SINGLE_PATH_CODES: tuple[str, ...] = (
    "000",
    "100", "200", "300", "400", "500",
    "010", "020", "030", "040", "050",
    "001", "002", "003", "004", "005",
)  # fmt: skip

_SINGLE_PATH_SET = frozenset(SINGLE_PATH_CODES)


def is_valid_code(code: str) -> bool:
    """True if ``code`` is three characters, each a digit 0-5."""
    return (
        isinstance(code, str) and len(code) == 3 and all(ch in "012345" for ch in code)
    )


def digits(code: str) -> tuple[int, int, int]:
    """Parse a valid code into its three integer tiers."""
    if not is_valid_code(code):
        raise ValueError(f"invalid tier code: {code!r}")
    return (int(code[0]), int(code[1]), int(code[2]))


def is_legal(code: str) -> bool:
    """True if ``code`` is a legal in-game upgrade state.

    Rule: at most two paths non-zero, and of those at most one may exceed tier 2.
    Equivalently, with tiers sorted descending ``(a, b, c)``: ``c == 0`` and
    ``b <= 2``. Rejects impossible states (``1-1-1``, ``5-3-0``) so a wiki-side
    helper/test node never becomes committed bot data.
    """
    if not is_valid_code(code):
        return False
    a, b, c = sorted(digits(code), reverse=True)
    return c == 0 and b <= 2


def nonzero_count(code: str) -> int:
    return sum(1 for d in digits(code) if d)


def is_base(code: str) -> bool:
    return code == "000"


def is_single_path(code: str) -> bool:
    """Exactly one non-zero path (one of the 16 canonical tiers, sans base)."""
    return nonzero_count(code) == 1


def is_crosspath(code: str) -> bool:
    """Two or more non-zero paths — a true crosspath."""
    return nonzero_count(code) >= 2


def primary_path(code: str) -> int | None:
    """1-based index of the 'main' path (highest tier; ties -> lowest index).

    Returns ``None`` for the base (``000``). Used to choose the upgrade *name*
    that labels a crosspath.
    """
    ds = digits(code)
    if not any(ds):
        return None
    best_idx, best_tier = 0, -1
    for idx, tier in enumerate(ds):
        if tier > best_tier:
            best_idx, best_tier = idx, tier
    return best_idx + 1


def primary_tier(code: str) -> int:
    """Tier of the primary path (0 for the base)."""
    path = primary_path(code)
    return 0 if path is None else digits(code)[path - 1]


def format_code(code: str) -> str:
    """``"202"`` -> ``"2-0-2"``."""
    return "-".join(code)


def candidate_parents(code: str) -> tuple[str, ...]:
    """Single-path parents a crosspath can be reconstructed from.

    One per non-zero path, keeping only that path's tier. A legal crosspath has
    exactly two, e.g. ``"210"`` -> ``("200", "010")``.
    """
    ds = digits(code)
    parents: list[str] = []
    for idx, tier in enumerate(ds):
        if tier:
            parent = [0, 0, 0]
            parent[idx] = tier
            parents.append("".join(str(d) for d in parent))
    return tuple(parents)


def preferred_parent(parents: Iterable[str]) -> str:
    """Deterministic canonical parent: highest tier first, then lowest path.

    e.g. ``("200", "010")`` -> ``"200"``; ``("200", "002")`` -> ``"200"``.
    """
    candidates = list(parents)
    if not candidates:
        raise ValueError("no candidate parents")
    return sorted(candidates, key=lambda p: (-primary_tier(p), primary_path(p) or 0))[0]


def ordered_codes(present: Iterable[str]) -> tuple[str, ...]:
    """Display order: the present canonical 16 first, then crosspaths sorted."""
    present_set = set(present)
    canonical = [c for c in SINGLE_PATH_CODES if c in present_set]
    extra = sorted(c for c in present_set if c not in _SINGLE_PATH_SET)
    return tuple(canonical + extra)


__all__ = [
    "SINGLE_PATH_CODES",
    "candidate_parents",
    "digits",
    "format_code",
    "is_base",
    "is_crosspath",
    "is_legal",
    "is_single_path",
    "is_valid_code",
    "nonzero_count",
    "ordered_codes",
    "preferred_parent",
    "primary_path",
    "primary_tier",
]
