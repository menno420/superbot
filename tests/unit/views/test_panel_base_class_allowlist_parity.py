"""Cross-allowlist drift guard: the `panel_base_class` consistency-linter
allowlist must agree with the `baseview_inheritance` arch conformance frozenset.

The same documented direct-``discord.ui.View`` exceptions are enumerated **twice**,
by hand, in two files:

* ``tests/unit/views/test_view_base_class_conformance.py`` —
  ``_KNOWN_DIRECT_VIEW_SUBCLASSES``, the *hard* ratchet that pins the arch
  checker's ``baseview_inheritance`` warnings (may shrink, never grow without
  review).
* ``architecture_rules/consistency_exceptions.yml`` ▶ ``panel_base_class`` —
  the per-entry-reasoned allowlist that scopes the warn-only consistency rule 3
  (`scripts/check_consistency.py`) off the *same* set, so it does not re-flag
  arch-decided exceptions (Q-0120).

They serve different purposes (one is the ratchet, the other carries the
human-readable reasons + scopes the linter), so neither subsumes the other —
but they MUST list exactly the same ``(path, class)`` pairs. The yml's own
comment already instructs "when the conformance frozenset shrinks, drop the
matching entry here too"; this test makes that instruction enforced instead of
hoped-for. When one is ratcheted down and the other is not, they silently
diverge (the "two sources of truth" smell that motivated this guard) — this
test catches that the moment it happens.

This is the cross-allowlist drift guard captured as the
``2026-06-20-arch-ratchet-cog-layer.md`` Q-0089 session idea (built 2026-06-20).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from tests.unit.views.test_view_base_class_conformance import (
    _KNOWN_DIRECT_VIEW_SUBCLASSES,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXCEPTIONS_YML = _REPO_ROOT / "architecture_rules" / "consistency_exceptions.yml"


def _panel_base_class_allowlist() -> set[tuple[str, str]]:
    """The ``panel_base_class`` exceptions as ``(path, class)`` pairs.

    Each yml ``pattern`` is the ``path::Class`` form the consistency linter
    matches on; split it into the same tuple shape the conformance frozenset
    uses so the two can be compared directly.
    """
    data = yaml.safe_load(_EXCEPTIONS_YML.read_text(encoding="utf-8"))
    rule = data.get("panel_base_class")
    assert rule is not None, (
        f"`panel_base_class` rule missing from {_EXCEPTIONS_YML.name} — the "
        "consistency linter's rule-3 allowlist; without it the warn-only rule "
        "re-flags every arch-decided direct-View exception."
    )

    pairs: set[tuple[str, str]] = set()
    for entry in rule.get("exceptions", []):
        pattern = entry["pattern"]
        assert "::" in pattern, (
            f"`panel_base_class` exception pattern {pattern!r} is not in the "
            "expected `path::Class` form."
        )
        path, cls = pattern.split("::", 1)
        pairs.add((path, cls))
    return pairs


def test_panel_base_class_allowlist_matches_conformance_frozenset() -> None:
    yml_allowlist = _panel_base_class_allowlist()

    only_in_frozenset = _KNOWN_DIRECT_VIEW_SUBCLASSES - yml_allowlist
    only_in_yml = yml_allowlist - _KNOWN_DIRECT_VIEW_SUBCLASSES

    assert not only_in_frozenset, (
        "Direct-View exception(s) pinned in the arch conformance frozenset "
        "(tests/unit/views/test_view_base_class_conformance.py) but MISSING from "
        "the `panel_base_class` allowlist in "
        "architecture_rules/consistency_exceptions.yml — the warn-only "
        "consistency rule will re-flag them as findings. Add a matching entry "
        f"(with a reason): {sorted(only_in_frozenset)}"
    )
    assert not only_in_yml, (
        "Direct-View exception(s) listed in the `panel_base_class` allowlist "
        "(architecture_rules/consistency_exceptions.yml) but NOT in the arch "
        "conformance frozenset (tests/unit/views/test_view_base_class_conformance.py)"
        " — they ratcheted down on one side only. Drop the stale yml entry (the "
        "yml comment instructs exactly this when the frozenset shrinks): "
        f"{sorted(only_in_yml)}"
    )
