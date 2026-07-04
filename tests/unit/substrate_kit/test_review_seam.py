"""Tests for the external-review seam (Lane B3).

Covers the anti-anchor payload shape (no confidence field, no author
commentary), the objective/subjective stop-condition split, the non-provisional
empty payload, the payload file write, the three verdict outcomes (confirmed /
recorded / escalated with promotion downgrade), and the wiring doc content.
"""

import datetime
import json
from pathlib import Path

import pytest

from engine.lib.config import Config
from engine.lib.state import JsonStateBackend, default_state
from engine.loop.review_seam import (
    REVIEW_DIR,
    apply_review_verdict,
    build_review_payload,
    seam_wiring_doc,
    write_review_payload,
)

_PAYLOAD_KEYS = {
    "format_version",
    "slot",
    "proposition",
    "evidence",
    "stop_conditions",
    "objective",
}


def _backend(tmp_path: Path, **over) -> JsonStateBackend:
    backend = JsonStateBackend(tmp_path / ".substrate" / "state.json")
    state = default_state("pid")
    state.update(over)
    for key, value in state.items():
        backend.set(key, value)
    return backend


def _provisional(tmp_path: Path, slot: str, question_id: str) -> JsonStateBackend:
    return _backend(
        tmp_path,
        slots={slot: "provisional"},
        slot_values={
            slot: {
                "value": f"ASSUMED: {slot}",
                "source": "assumption",
                "question_id": question_id,
            },
        },
    )


# ---------------------------------------------------------------------------
# build_review_payload — the anti-anchor shape
# ---------------------------------------------------------------------------


def test_payload_objective_slot_shape(tmp_path):
    backend = _provisional(tmp_path, "project_name", "Q-002")
    payload = build_review_payload(backend, "project_name")
    assert set(payload) == _PAYLOAD_KEYS  # nothing extra — no author commentary
    assert "confidence" not in payload
    assert payload["format_version"] == 1
    assert payload["slot"] == "project_name"
    assert payload["proposition"] == "ASSUMED: project_name"
    assert payload["objective"] is True
    assert payload["stop_conditions"] == [
        "verify against repository source",
        "run the project verify command",
    ]


def test_payload_evidence_carries_prompt_and_source(tmp_path):
    backend = _provisional(tmp_path, "project_name", "Q-002")
    payload = build_review_payload(backend, "project_name")
    assert "What is this project called?" in payload["evidence"]
    assert "assumption" in payload["evidence"]


def test_payload_subjective_slot_routes_to_owner(tmp_path):
    backend = _provisional(tmp_path, "owner_profile", "Q-008")
    payload = build_review_payload(backend, "owner_profile")
    assert payload["objective"] is False
    assert payload["stop_conditions"] == ["route to the owner - subjective slot"]


def test_payload_empty_for_non_provisional_slot(tmp_path):
    backend = _backend(
        tmp_path,
        slots={"project_name": "filled"},
        slot_values={"project_name": {"value": "superbot", "source": "user"}},
    )
    assert build_review_payload(backend, "project_name") == {}
    assert build_review_payload(backend, "never_recorded") == {}


def test_payload_unknown_slot_is_keyerror_free(tmp_path):
    backend = _backend(tmp_path, slots={"mystery": "provisional"})
    payload = build_review_payload(backend, "mystery")  # no bank entry, no value
    assert payload["proposition"] == ""
    assert payload["objective"] is False


# ---------------------------------------------------------------------------
# write_review_payload
# ---------------------------------------------------------------------------


def test_write_review_payload_path_and_roundtrip(tmp_path):
    backend = _provisional(tmp_path, "project_name", "Q-002")
    payload = build_review_payload(backend, "project_name")
    path = write_review_payload(tmp_path, Config(state_dir=".substrate"), payload)
    expected = tmp_path / ".substrate" / REVIEW_DIR / "payload-project_name.json"
    assert path == expected
    assert json.loads(path.read_text(encoding="utf-8")) == payload


# ---------------------------------------------------------------------------
# apply_review_verdict — the three outcomes
# ---------------------------------------------------------------------------


def test_pass_on_objective_slot_confirms(tmp_path):
    backend = _provisional(tmp_path, "project_name", "Q-002")
    result = apply_review_verdict(
        backend,
        "project_name",
        verdict="pass",
        reviewer="gpt",
    )
    assert result == "confirmed"
    assert backend.get("slots")["project_name"] == "filled"
    assert backend.get("slot_values")["project_name"]["source"] == (
        "confirmed:reviewer:gpt"
    )
    entry = backend.get("review_log")[-1]
    assert entry["slot"] == "project_name"
    assert entry["verdict"] == "pass"
    assert entry["reviewer"] == "gpt"
    assert entry["date"] == datetime.date.today().isoformat()


def test_pass_on_subjective_slot_only_records(tmp_path):
    backend = _provisional(tmp_path, "owner_profile", "Q-008")
    result = apply_review_verdict(
        backend,
        "owner_profile",
        verdict="pass",
        reviewer="gpt",
    )
    assert result == "recorded"
    assert backend.get("slots")["owner_profile"] == "provisional"  # stays capped
    assert backend.get("promotion_rights") == "propose"
    assert backend.get("review_log")[-1]["verdict"] == "pass"


def test_fail_escalates_and_downgrades_promotion(tmp_path):
    backend = _provisional(tmp_path, "project_name", "Q-002")
    backend.set("promotion_rights", "promote")
    result = apply_review_verdict(
        backend,
        "project_name",
        verdict="fail",
        reviewer="gpt",
    )
    assert result == "escalated"
    assert backend.get("open_questions") == ["Q-002"]
    assert backend.get("slots")["project_name"] == "provisional"  # not confirmed
    assert backend.get("promotion_rights") == "propose"
    events = [e.get("event") for e in backend.get("review_log")]
    assert "promotion_downgrade" in events
    assert backend.get("review_log")[-1]["verdict"] == "fail"


def test_fail_without_recorded_question_id_uses_bank_id(tmp_path):
    backend = _backend(tmp_path, slots={"project_name": "provisional"})
    apply_review_verdict(backend, "project_name", verdict="fail", reviewer="gpt")
    assert backend.get("open_questions") == ["Q-002"]  # from the bank entry


def test_unknown_verdict_raises(tmp_path):
    backend = _provisional(tmp_path, "project_name", "Q-002")
    with pytest.raises(ValueError, match="unknown review verdict"):
        apply_review_verdict(backend, "project_name", verdict="maybe", reviewer="x")


# ---------------------------------------------------------------------------
# seam_wiring_doc
# ---------------------------------------------------------------------------


def test_wiring_doc_names_the_entry_points_and_fallback():
    doc = seam_wiring_doc()
    assert "provisioned, not wired" in doc
    assert "bootstrap review build <slot>" in doc
    assert "bootstrap review confirm <slot> --verdict pass|fail --reviewer" in doc
    assert "ONLY that payload" in doc
    assert "accumulate" in doc  # graceful no-reviewer fallback
    assert "NO confidence score" in doc  # the anti-anchor rule
    assert "calibrate a new reviewer against known-answer issues" in doc


def test_review_dir_mirrors_maintenance_literal():
    """maintenance._mnt_review_dir inlines REVIEW_DIR to avoid a circular import."""
    from engine.loop.maintenance import _mnt_review_dir

    assert _mnt_review_dir() == REVIEW_DIR


def test_verdict_on_non_provisional_slot_is_inert(tmp_path):
    """A stray verdict must neither confirm, escalate, nor downgrade.

    Regression (review finding): a 'fail' on a typo'd slot escalated a bogus
    question and downgraded promotion rights; a 'pass' falsely reported
    'confirmed'.
    """
    backend = _backend(tmp_path, promotion_rights="promote")
    for verdict in ("pass", "fail"):
        outcome = apply_review_verdict(
            backend,
            "never_answered_slot",
            verdict=verdict,
            reviewer="x",
        )
        assert outcome == "not-provisional"
    assert backend.get("promotion_rights") == "promote"
    assert backend.get("open_questions") == []
    assert backend.get("review_log") == []


def test_clear_review_payload_removes_consumed_payload(tmp_path):
    # A recorded verdict consumes the payload, but the FILE persisted and
    # maintenance kept counting it as "awaiting a reviewer" forever. Clearing it
    # is how the count reflects reality; a missing payload is an idempotent no-op.
    from engine.loop.review_seam import clear_review_payload

    config = Config(state_dir=".substrate")
    backend = _provisional(tmp_path, "project_name", "Q-002")
    payload = build_review_payload(backend, "project_name")
    path = write_review_payload(tmp_path, config, payload)
    assert path.exists()
    assert clear_review_payload(tmp_path, config, "project_name") is True
    assert not path.exists()
    assert clear_review_payload(tmp_path, config, "project_name") is False
