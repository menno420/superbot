"""The external-review seam — provisioned, not wired (plan section 6, Lane B3).

A second model can audit the interview's provisional self-answers, but the kit
never talks to one (no subprocess, no network): it emits an **anti-anchor**
payload — the proposition and its evidence, NO confidence score, NO author
commentary — and the host records the verdict through one entry point. With no
reviewer configured, payloads simply accumulate for the owner; nothing blocks.
Pure stdlib; writes via ``atomic_write_text``.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from engine.interview.interview import confirm_slot
from engine.interview.question_bank import QUESTIONS
from engine.lib.atomicio import atomic_write_text
from engine.lib.config import Config
from engine.loop.maintenance import downgrade_promotion, escalate_blocking

REVIEW_DIR = "review"

# Deterministic checks first — the reviewer runs mechanical verification
# before exercising judgment; subjective slots route straight to the owner.
_REV_OBJECTIVE_STOPS = (
    "verify against repository source",
    "run the project verify command",
)
_REV_SUBJECTIVE_STOPS = ("route to the owner - subjective slot",)

_REV_WIRING_DOC = """\
# Review seam — provisioned, not wired

The kit never calls an external model. It defines a payload format and two
entry points; the host wires ANY reviewer (a second model, a CLI, a human)
around them:

1. `bootstrap review build <slot>` emits the payload JSON to
   `<state_dir>/review/payload-<slot>.json`.
2. The external reviewer reads ONLY that payload — never the chat context,
   never the author's notes or working files.
3. The host records the verdict:
   `bootstrap review confirm <slot> --verdict pass|fail --reviewer <name>`.
   A `pass` on an objective slot confirms it; a `pass` on a subjective slot is
   recorded but the slot stays provisional (only the owner confirms taste);
   a `fail` escalates the question as blocking and downgrades promotion
   rights to propose-only.

Graceful no-reviewer fallback: with no reviewer configured, payloads simply
accumulate in the review directory for the owner to work through — nothing
blocks, and the maintenance report counts them.

Anti-anchor rule: the payload carries the proposition, its evidence, and
deterministic stop conditions — NO confidence score and NO author commentary,
so the reviewer cannot anchor on the author's own belief.

Unverified reviewer: calibrate a new reviewer against known-answer issues
before trusting its dissent — a verdict that fights the evidence is the
reviewer's bug until proven otherwise.
"""


def _rev_bank_entry(slot: str) -> dict:
    """Return the question-bank entry for ``slot`` (``{}`` when unknown)."""
    for question in QUESTIONS:
        if question.get("slot") == slot:
            return question
    return {}


def _rev_slot_value(backend: Any, slot: str) -> dict:
    """Return the recorded slot-value entry for ``slot`` (``{}`` when absent)."""
    entry = dict(backend.get("slot_values", {})).get(slot, {})
    return entry if isinstance(entry, dict) else {}


def build_review_payload(backend: Any, slot: str) -> dict:
    """Build the anti-anchor review payload for a provisional ``slot``.

    The payload carries the proposition and its evidence ONLY — no confidence
    score, no author commentary — so the reviewing model cannot anchor on the
    author's belief. Objective slots get deterministic stop conditions first;
    subjective slots route to the owner. Returns ``{}`` when the slot is not
    provisional (nothing to review). Never raises ``KeyError``.
    """
    if dict(backend.get("slots", {})).get(slot) != "provisional":
        return {}
    entry = _rev_slot_value(backend, slot)
    question = _rev_bank_entry(slot)
    objective = bool(question.get("objective", False))
    stops = _REV_OBJECTIVE_STOPS if objective else _REV_SUBJECTIVE_STOPS
    evidence = (
        f"question: {question.get('prompt', '')} | "
        f"recorded source: {entry.get('source', '')}"
    )
    return {
        "format_version": 1,
        "slot": slot,
        "proposition": entry.get("value", ""),
        "evidence": evidence,
        "stop_conditions": list(stops),
        "objective": objective,
    }


def write_review_payload(root: Path, config: Config, payload: dict) -> Path:
    """Write ``payload`` to ``<state_dir>/review/payload-<slot>.json``.

    Atomic, indented, key-sorted JSON; returns the written path.
    """
    slot = str(payload.get("slot", "unknown"))
    path = root / config.state_dir / REVIEW_DIR / f"payload-{slot}.json"
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def clear_review_payload(root: Path, config: Config, slot: str) -> bool:
    """Remove the consumed payload for ``slot``; True when one was present.

    A verdict recorded via ``apply_review_verdict`` consumes the payload, but the
    payload FILE persists — and ``maintenance._mnt_advisories`` counts every
    ``payload-*.json`` as "awaiting a reviewer", so without this the count never
    decrements after a review (it grows without bound under a wired reviewer).
    Idempotent: a missing payload is a no-op.
    """
    path = root / config.state_dir / REVIEW_DIR / f"payload-{slot}.json"
    existed = path.exists()
    path.unlink(missing_ok=True)
    return existed


def _rev_log(backend: Any, slot: str, verdict: str, reviewer: str) -> None:
    """Append one review-log entry (the state contract's four-field shape)."""
    log = list(backend.get("review_log", []))
    log.append(
        {
            "slot": slot,
            "verdict": verdict,
            "reviewer": reviewer,
            "date": date.today().isoformat(),
        },
    )
    backend.set("review_log", log)


def apply_review_verdict(
    backend: Any,
    slot: str,
    *,
    verdict: str,
    reviewer: str,
) -> str:
    """Record an external reviewer's verdict on a provisional slot.

    Three outcomes:

    - ``pass`` on an *objective* slot confirms it (provisional → filled,
      source ``reviewer:<name>``) → returns ``"confirmed"``.
    - ``pass`` on a *subjective* slot is recorded only — the slot stays
      provisional and promotion stays capped at propose → ``"recorded"``.
    - ``fail`` escalates the slot's question as blocking AND downgrades
      promotion rights to propose-only → ``"escalated"``.

    Every outcome appends a review-log entry. Raises ``ValueError`` on any
    verdict other than ``"pass"`` / ``"fail"``. A slot that is not currently
    ``provisional`` (typo'd, already confirmed, never answered) returns
    ``"not-provisional"`` untouched — mirroring ``build_review_payload``'s
    guard, so a stray verdict can neither falsely confirm nor escalate.
    """
    if verdict not in ("pass", "fail"):
        raise ValueError(f"unknown review verdict: {verdict!r}")
    if backend.get("slots", {}).get(slot) != "provisional":
        return "not-provisional"
    question = _rev_bank_entry(slot)
    # Each multi-write outcome is one transaction (Q-0223 tail ①): the escalate/
    # downgrade/log (and confirm/log) legs land together or not at all. The
    # helpers open their own transactions internally — safe, because the JSON
    # backend's transaction is re-entrant and only the outermost exit flushes.
    if verdict == "fail":
        question_id = str(_rev_slot_value(backend, slot).get("question_id", ""))
        question_id = question_id or str(question.get("id", slot))
        with backend.transaction():
            escalate_blocking(backend, question_id)
            downgrade_promotion(
                backend,
                reason=f"review fail on slot '{slot}' by {reviewer}",
            )
            _rev_log(backend, slot, verdict, reviewer)
        return "escalated"
    if question.get("objective", False):
        with backend.transaction():
            confirm_slot(backend, slot, source=f"reviewer:{reviewer}")
            _rev_log(backend, slot, verdict, reviewer)
        return "confirmed"
    _rev_log(backend, slot, verdict, reviewer)
    return "recorded"


def seam_wiring_doc() -> str:
    """Return the wiring instructions for hosting ANY external reviewer.

    The seam ships provisioned, not wired: the kit defines the payload format
    and the verdict entry points; the host decides which model (if any) reads
    the payloads — and without one, they accumulate gracefully for the owner.
    """
    return _REV_WIRING_DOC
