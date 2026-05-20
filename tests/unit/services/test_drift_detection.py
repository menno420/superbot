"""Phase 9i / Track 8 PR 24 — drift detection tests.

Pins:

* ``detect_drift`` returns ``has_drift=False`` when the score is
  unchanged and there are no new findings.
* Score deltas at or above the threshold (5%) mark drift.
* New error / warn findings mark drift even when the score didn't
  move.
* Outstanding health-error counts (from ``current_health_summary``)
  mark drift.
* The summary string is human-readable and surfaces the drift
  cause.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from services.setup_session import DriftReport, detect_drift


def _finding(*, severity: str, subsystem: str = "logging", name: str = "mod_channel"):
    return SimpleNamespace(
        severity=severity,
        subsystem=subsystem,
        binding_name=name,
    )


def test_no_score_no_drift_no_findings():
    report = detect_drift(previous_score=None, current_score=None)
    assert isinstance(report, DriftReport)
    assert report.has_drift is False
    assert "No drift" in report.summary


def test_identical_scores_no_drift():
    report = detect_drift(previous_score=85, current_score=85)
    assert report.has_drift is False
    assert report.score_delta == 0


def test_small_score_change_below_threshold_does_not_drift():
    report = detect_drift(previous_score=85, current_score=88)  # +3
    assert report.has_drift is False


def test_score_regression_at_threshold_marks_drift():
    report = detect_drift(previous_score=90, current_score=85)  # -5
    assert report.has_drift is True
    assert "regressed" in report.summary
    assert "5" in report.summary


def test_score_improvement_at_threshold_marks_drift():
    report = detect_drift(previous_score=80, current_score=90)  # +10
    assert report.has_drift is True
    assert "improved" in report.summary
    assert "10" in report.summary


def test_new_error_findings_mark_drift_even_when_score_unchanged():
    report = detect_drift(
        previous_score=85,
        current_score=85,
        new_findings=(_finding(severity="error"),),
    )
    assert report.has_drift is True
    assert "1 new error finding" in report.summary
    assert report.new_error_findings == ("logging.mod_channel",)


def test_new_warn_findings_mark_drift_even_when_score_unchanged():
    report = detect_drift(
        previous_score=85,
        current_score=85,
        new_findings=(_finding(severity="warn", name="audit_channel"),),
    )
    assert report.has_drift is True
    assert "1 new warning finding" in report.summary


def test_outstanding_health_errors_mark_drift():
    report = detect_drift(
        previous_score=85,
        current_score=85,
        current_health_summary={"error": 2, "warn": 0, "info": 0},
    )
    assert report.has_drift is True


def test_report_carries_score_delta():
    report = detect_drift(previous_score=80, current_score=90)
    assert report.score_delta == 10
    assert report.prev_score == 80
    assert report.current_score == 90


@pytest.mark.parametrize(
    ("prev", "curr"),
    [(None, 90), (None, None), (50, None)],
)
def test_partial_score_inputs_dont_break_detector(prev, curr):
    report = detect_drift(previous_score=prev, current_score=curr)
    # Should never raise — drift defaults to False when there's no
    # numeric comparison available.
    assert isinstance(report, DriftReport)
