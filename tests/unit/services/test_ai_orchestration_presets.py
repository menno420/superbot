"""Built-in orchestration presets — compatibility + drift guards (Phase 3)."""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import (  # noqa: E402
    AIToolBudget,
    ToolRequirementMode,
)
from services import ai_orchestration_presets as presets  # noqa: E402
from services import ai_tool_catalogue as catalogue  # noqa: E402


def test_default_is_compatible_byte_identical() -> None:
    """The default preset must reproduce today's behaviour exactly."""
    default = presets.default()
    assert default.key == presets.DEFAULT_PROFILE_KEY
    # No toolset narrowing, no explicit disables.
    assert default.enabled_toolsets is None
    assert default.disabled_tools == ()
    # Automatic tool choice (the historical default).
    assert default.tool_choice.mode is ToolRequirementMode.AUTO
    # The default budget is the historical hop-bounded one with no other caps.
    assert default.tool_budget == AIToolBudget()


def test_default_and_balanced_engage_round_cash_workflow() -> None:
    """BUG-0001 recurred live (2026-06-11) on a default-profile channel: the
    deterministic round-cash workflow is the ONLY path that can answer
    round-cash arithmetic (the faithfulness guard rightly blocks model
    sums), so the default + balanced presets must declare it. ``no_tools``
    stays conversational by explicit operator choice."""
    assert presets.default().workflow == "analyze_execute_verify"
    assert presets.get("balanced_helper").workflow == "analyze_execute_verify"
    assert presets.get("btd6_grounded").workflow == "analyze_execute_verify"
    assert presets.get("no_tools").workflow == "direct_answer"


def test_all_presets_default_first() -> None:
    allp = presets.all_presets()
    assert allp[0].key == presets.DEFAULT_PROFILE_KEY
    # Stable + unique keys.
    keys = [p.key for p in allp]
    assert len(keys) == len(set(keys))
    assert set(keys) == set(presets.known_profile_keys())


def test_is_known_and_get_and_resolve_or_default() -> None:
    assert presets.is_known(presets.DEFAULT_PROFILE_KEY)
    assert presets.is_known("no_tools")
    assert not presets.is_known("bogus")
    assert not presets.is_known(None)
    assert presets.get("bogus") is None
    assert presets.get(None) is None
    # A stale/unknown key degrades to the default rather than raising.
    assert presets.resolve_or_default("bogus").key == presets.DEFAULT_PROFILE_KEY
    assert presets.resolve_or_default(None).key == presets.DEFAULT_PROFILE_KEY


def test_no_tools_offers_nothing() -> None:
    p = presets.get("no_tools")
    assert p is not None
    # Empty (not None) enabled set means "narrow everything away".
    assert p.enabled_toolsets == ()
    assert p.tool_choice.mode is ToolRequirementMode.NONE


def test_strict_grounded_requires_group() -> None:
    p = presets.get("btd6_grounded_strict")
    assert p is not None
    assert p.tool_choice.mode is ToolRequirementMode.REQUIRED_GROUP
    assert p.tool_choice.group_name == "btd6_grounding"
    assert p.enabled_toolsets  # narrowed to the BTD6 factual toolsets


def test_every_preset_references_real_toolsets() -> None:
    """Drift guard: a preset toolset must be a known catalogue toolset.

    Self-maintaining — the catalogue is the source of truth, so a renamed /
    removed toolset surfaces here rather than silently offering nothing.
    """
    bad = presets.unknown_toolset_references(
        known_toolsets=catalogue.known_toolsets(),
    )
    assert bad == {}, f"presets reference unknown toolsets: {bad}"
