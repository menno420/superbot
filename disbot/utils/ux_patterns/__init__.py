"""UX pattern registry + pure builders for the UX Lab (zero-write workbench).

See ``docs/planning/ux-lab-interface-gallery-plan-2026-06-12.md``.
"""

from utils.ux_patterns.registry import (
    REGISTRY,
    PatternCategory,
    PatternSpec,
    PatternStatus,
    ProbeResult,
    category_counts,
    get_spec,
    register,
    specs_for,
    validate_registry,
)

__all__ = [
    "REGISTRY",
    "PatternCategory",
    "PatternSpec",
    "PatternStatus",
    "ProbeResult",
    "category_counts",
    "get_spec",
    "register",
    "specs_for",
    "validate_registry",
]
