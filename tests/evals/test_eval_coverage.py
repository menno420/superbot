"""Eval-coverage drift guard — the versioned eval matrix can't silently fall
behind the AI surface it is meant to prove.

**"Enforce, don't exhort"** (the doc-freshness-gate principle): when a new
canonical AI tool (``services.ai_tools.all_tool_specs``) or ``AITask`` enters the
surface, the eval matrix — the golden set (``tests/evals/cases.py``) plus the
offline smoke matrix (``tests/evals/smoke.py``) — must gain a case that exercises
it, **or** it must be listed in the acknowledged-uncovered set below, with a
reason.

The acknowledged sets are a **self-cleaning ratchet, not a permanent exemption**:
they are the explicit, reviewable *pick-list of today's coverage gap* (8/34
tools, 2/16 tasks at creation, 2026-06-14). This module fails on three drift
directions, each with an actionable message:

1. a **new** tool/task that is neither referenced nor acknowledged
   → add an eval case, or acknowledge it here with a reason;
2. a **stale** acknowledgement whose tool/task no longer exists → remove it;
3. an acknowledged entry that is **now also referenced** by a case
   → remove it from the acknowledged set (coverage grew → the ledger shrinks).

Plus a **coverage floor** so coverage can only ratchet up: you cannot quiet a
deleted case by moving its tool/task into the acknowledged set.

(1) catches the forgotten-eval case; (2)+(3)+the floor stop the acknowledged
list from rotting into a rubber stamp.
"""

from __future__ import annotations

from tests.evals.cases import CASES
from tests.evals.smoke import SMOKE_CASES

from core.runtime.ai.contracts import AITask
from services import ai_tools

# --------------------------------------------------------------------------- #
# Acknowledged-uncovered TOOLS — the current gap. Pick names off these sets as
# you add live/smoke probes for them; the tests below fail if a name here is
# also covered (so the list can only shrink) or no longer exists.
# --------------------------------------------------------------------------- #

# BTD6 data + answerability lookups. Their *retrieval* is deterministically
# unit-pinned (tests/unit/services/ — btd6 context/grounding/tooling); a live
# golden probe (model selects + uses the tool) is the incremental add. The 6
# highest-value hotspot tools were lifted out into golden probes (cases.py);
# this set is the remaining pick-list — shrink it as you add more.
_ACK_BTD6_TOOLS = frozenset(
    {
        "btd6_bloon_filter",
        "btd6_ct_team_status",
        "btd6_cumulative_cost",
        "btd6_geraldo_lookup",
        "btd6_list_roster",
        "btd6_mode_lookup",
        "btd6_monkey_knowledge_lookup",
        "btd6_paragon_calculate",
        "btd6_paragon_requirements",
        "btd6_power_effect",
        "btd6_power_lookup",
        "btd6_relic_lookup",
    }
)

# Read-only guild-introspection tools (the model's "look at this server" surface).
_ACK_SERVER_TOOLS = frozenset(
    {
        "get_server_overview",
        "list_all_members",
        "list_server_channels",
        "list_server_roles",
        "lookup_member",
    }
)

# AI self-awareness tools (audience-tiered, read-only).
_ACK_AI_INTROSPECTION_TOOLS = frozenset(
    {
        "get_ai_policy_explanation",
        "get_ai_tool_catalog",
    }
)

# Operator diagnostics (platform-owner scope).
_ACK_DIAGNOSTICS_TOOLS = frozenset({"diagnostics_health_snapshot"})

_ACK_UNCOVERED_TOOLS = (
    _ACK_BTD6_TOOLS
    | _ACK_SERVER_TOOLS
    | _ACK_AI_INTROSPECTION_TOOLS
    | _ACK_DIAGNOSTICS_TOOLS
)

# --------------------------------------------------------------------------- #
# Acknowledged-uncovered TASKS. Most are exercised by their own service/cog
# tests rather than the live eval matrix; listed so a *new* task forces a
# conscious "add a case or acknowledge it" decision.
# --------------------------------------------------------------------------- #
_ACK_UNCOVERED_TASKS = frozenset(
    {
        "BTD6_STRATEGY_REVIEW",
        "CODE_CONTEXT_EXPLAIN",
        "HELP_ANSWER",
        "LOGS_TRIAGE",
        "MODERATION_ASSIST",
        "PLATFORM_EXPLAIN_CONSISTENCY",
        "PLATFORM_EXPLAIN_STATUS",
        "SETTINGS_EXPLAIN",
        "SETTINGS_PROPOSE",
        "SETUP_EXPLAIN",
        "SETUP_SUGGEST",
        "VIDEO_COMPARE",
        "VIDEO_DESCRIBE",
        "VIDEO_QA",
    }
)

# Coverage floors — the ratchet's teeth. Coverage can only go up: raise these as
# you add cases (and shrink the acknowledged sets), never lower them to quiet a
# deleted case. (8 → 14: the 6 BTD6 hotspot tool-selection probes, 2026-06-14.)
_TOOL_COVERAGE_FLOOR = 14
_TASK_COVERAGE_FLOOR = 2


# --------------------------------------------------------------------------- #
# Surface + coverage collectors.
# --------------------------------------------------------------------------- #
def _catalogue_tools() -> set[str]:
    """Every canonical tool name — flag-independent (the model-offerable surface)."""
    return set(ai_tools.all_tool_specs())


def _referenced_tools() -> set[str]:
    """Tool names offered by at least one golden or smoke case."""
    return {spec.name for case in CASES for spec in case.tools} | {
        spec.name for case in SMOKE_CASES for spec in case.tools
    }


def _all_tasks() -> set[str]:
    return {task.name for task in AITask}


def _referenced_tasks() -> set[str]:
    return {case.task.name for case in CASES} | {case.task.name for case in SMOKE_CASES}


# --------------------------------------------------------------------------- #
# Tools.
# --------------------------------------------------------------------------- #
def test_new_tool_needs_coverage_or_acknowledgement():
    new_uncovered = _catalogue_tools() - _referenced_tools() - _ACK_UNCOVERED_TOOLS
    assert not new_uncovered, (
        f"New AI tool(s) with no eval coverage: {sorted(new_uncovered)}. "
        "Add a golden/smoke case that offers the tool (tests/evals/cases.py) so "
        "the versioned matrix proves it, or add the name to _ACK_UNCOVERED_TOOLS "
        "with a reason (tests/evals/test_eval_coverage.py)."
    )


def test_no_stale_acknowledged_tools():
    stale = _ACK_UNCOVERED_TOOLS - _catalogue_tools()
    assert not stale, (
        f"_ACK_UNCOVERED_TOOLS names tool(s) no longer in the catalogue: "
        f"{sorted(stale)}. Remove the stale acknowledgement(s)."
    )


def test_acknowledged_tools_are_not_already_covered():
    now_covered = _ACK_UNCOVERED_TOOLS & _referenced_tools()
    assert not now_covered, (
        f"Tool(s) are both acknowledged-uncovered AND referenced by a case: "
        f"{sorted(now_covered)}. Coverage grew — remove them from "
        "_ACK_UNCOVERED_TOOLS so the ledger reflects reality."
    )


def test_tool_coverage_does_not_regress():
    covered = len(_referenced_tools() & _catalogue_tools())
    assert covered >= _TOOL_COVERAGE_FLOOR, (
        f"Eval tool coverage dropped to {covered} (floor {_TOOL_COVERAGE_FLOOR}). "
        "A case that referenced a tool was removed — restore it, or you are "
        "regressing the matrix. Do not lower the floor to quiet this."
    )


# --------------------------------------------------------------------------- #
# Tasks.
# --------------------------------------------------------------------------- #
def test_new_task_needs_coverage_or_acknowledgement():
    new_uncovered = _all_tasks() - _referenced_tasks() - _ACK_UNCOVERED_TASKS
    assert not new_uncovered, (
        f"New AITask(s) with no eval coverage: {sorted(new_uncovered)}. "
        "Add a case with task=AITask.<NAME>, or add the name to "
        "_ACK_UNCOVERED_TASKS with a reason."
    )


def test_no_stale_acknowledged_tasks():
    stale = _ACK_UNCOVERED_TASKS - _all_tasks()
    assert not stale, (
        f"_ACK_UNCOVERED_TASKS names task(s) that no longer exist: {sorted(stale)}. "
        "Remove the stale acknowledgement(s)."
    )


def test_acknowledged_tasks_are_not_already_covered():
    now_covered = _ACK_UNCOVERED_TASKS & _referenced_tasks()
    assert not now_covered, (
        f"Task(s) are both acknowledged-uncovered AND referenced by a case: "
        f"{sorted(now_covered)}. Remove them from _ACK_UNCOVERED_TASKS."
    )


def test_task_coverage_does_not_regress():
    covered = len(_referenced_tasks() & _all_tasks())
    assert (
        covered >= _TASK_COVERAGE_FLOOR
    ), f"Eval task coverage dropped to {covered} (floor {_TASK_COVERAGE_FLOOR})."


# --------------------------------------------------------------------------- #
# Canonical statement of the ratchet (the partition the granular tests enforce).
# --------------------------------------------------------------------------- #
def test_tool_surface_is_exactly_partitioned():
    referenced = _referenced_tools()
    assert referenced.isdisjoint(_ACK_UNCOVERED_TOOLS)
    assert referenced | _ACK_UNCOVERED_TOOLS == _catalogue_tools()


def test_task_surface_is_exactly_partitioned():
    referenced = _referenced_tasks()
    assert referenced.isdisjoint(_ACK_UNCOVERED_TASKS)
    assert referenced | _ACK_UNCOVERED_TASKS == _all_tasks()


# --------------------------------------------------------------------------- #
# Meta-tests: prove the guard actually fires (a guard that cannot fail is worse
# than none — it reads as covered). Synthetic drift must trip the predicate.
# --------------------------------------------------------------------------- #
def test_guard_fires_on_a_synthetic_new_tool(monkeypatch):
    real = ai_tools.all_tool_specs
    fake = "synthetic_uncovered_tool_zzz"
    monkeypatch.setattr(ai_tools, "all_tool_specs", lambda: {**real(), fake: object()})
    new_uncovered = _catalogue_tools() - _referenced_tools() - _ACK_UNCOVERED_TOOLS
    assert fake in new_uncovered, "guard did not detect an injected uncovered tool"


def test_guard_recognises_real_coverage():
    # A tool the golden set genuinely offers must read as covered, not flagged.
    assert "get_user_standing" in _referenced_tools()
    assert "get_user_standing" not in _ACK_UNCOVERED_TOOLS
