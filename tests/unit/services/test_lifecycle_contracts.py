"""Tests for services.lifecycle.contracts (server-management PR3)."""

from __future__ import annotations

from services.lifecycle import contracts as lc


def test_classify_all_ok_is_success():
    steps = (lc.StepResult(1, "a", True), lc.StepResult(2, "b", True))
    assert lc.classify_outcome(steps) == lc.SUCCESS


def test_classify_some_ok_is_partial():
    steps = (lc.StepResult(1, "a", True), lc.StepResult(2, "b", False, "x"))
    assert lc.classify_outcome(steps) == lc.PARTIAL


def test_classify_none_ok_is_discord_failed():
    assert (
        lc.classify_outcome((lc.StepResult(1, "a", False, "x"),)) == lc.DISCORD_FAILED
    )


def test_classify_empty_is_discord_failed():
    assert lc.classify_outcome(()) == lc.DISCORD_FAILED


def test_result_applied_and_failed_partition():
    result = lc.LifecycleResult(
        mutation_id="m",
        guild_id=1,
        domain="channel",
        operation="delete",
        outcome=lc.PARTIAL,
        reversibility=lc.IRREVERSIBLE,
        steps=(lc.StepResult(1, "a", True), lc.StepResult(2, "b", False, "x")),
    )
    assert [s.target_id for s in result.applied] == [1]
    assert [s.target_id for s in result.failed] == [2]
