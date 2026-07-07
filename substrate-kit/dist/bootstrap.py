"""substrate-kit bootstrap — GENERATED, DO NOT EDIT.

Single-file, stdlib-only. Regenerate from source with:
    python3 substrate-kit/src/build_bootstrap.py
Source of truth: substrate-kit/src/engine/. Edits here are overwritten.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Collection, Sequence
from collections.abc import Iterator
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager, contextmanager
from dataclasses import asdict, dataclass, field, fields
from datetime import date
from datetime import date as _led_date
from pathlib import Path
from typing import Any
from typing import Any, NamedTuple
from typing import NamedTuple
import argparse
import ast
import copy
import itertools
import json
import os
import random
import re
import string
import sys
import tempfile
import time
import uuid

# --- engine/lib/atomicio.py ---
"""Atomic file writes for crash-safe state.

A write goes to a sibling ``*.tmp`` file and is renamed into place with
``os.replace`` — an atomic rename on POSIX and Windows — so a process that dies
mid-write can never leave a half-written, unparseable file behind. This is the
robustness floor the whole engine builds on (plan: Gemini round).
"""




def atomic_write_text(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically via a temp file + ``os.replace``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

# --- engine/lib/config.py ---
"""Host-project configuration for one substrate-kit install.

Reads and writes ``substrate.config.json`` — the single file that absorbs every
host-specific knob so the engine code never hardcodes a project value. Two
interpreters are kept explicitly separate (Hermes-final): ``interpreter`` is the
kit's own runtime, ``interpreter_for_checks`` is the host project's verification
runtime (e.g. ``python3.10`` for a repo whose CI pins 3.10).
"""




CONFIG_FILENAME = "substrate.config.json"
DEFAULT_STATE_DIR = ".substrate"


def _new_project_id() -> str:
    """Return a short, stable identifier for one install."""
    return uuid.uuid4().hex[:12]


def _default_cadence() -> dict[str, int]:
    """Return the default cadence knobs (every hardcoded cadence lives here)."""
    return {
        "reconciliation_prs": 20,
        "reconciliation_sessions": 20,
        "compaction_sessions": 20,
        "critical_slot_grace_sessions": 3,
        "staleness_days": 14,
        "guided_practice_sessions": 3,
    }


def _default_reflection() -> dict:
    """Return the reflection-buffer knobs (size cap is a hard context guard)."""
    return {"enabled": True, "buffer_size": 5}


def _default_orientation() -> dict:
    """Return the orientation-budget knobs (the K0 ≤7,000-word gate).

    ``boot_docs`` empty means "fall back to ``readpath_docs``" — the
    unconditional boot-read set the budget counts.
    """
    return {"budget_words": 7000, "boot_docs": []}


def _default_economy() -> dict:
    """Return the context-economy knobs (taxonomy/gauges are host policy).

    ``maturity`` gates the actuator: ``shadow`` (report only, the first-prune
    safety protocol) -> ``gated`` (apply with review) -> ``normal``. Classes and
    gauges ship empty — the engine supplies a documented generic default when
    unset; each adopting repo declares its own table (the kit ships the search,
    not our constants).
    """
    return {
        "maturity": "shadow",
        "pass_records_dir": "planning",
        "reference_roots": [],
        "id_patterns": [r"Q-\d{3,}", r"D-\d{3,}", r"R-\d{3,}"],
        "classes": [],
        "gauges": [],
        "debt_threshold": 10,
    }


def _default_namespace() -> dict:
    """Return the namespace-guard knobs (roots to scan + reserved-name map)."""
    return {"roots": [], "reserved": {}}


def _default_review_seam() -> dict:
    """Return the review-seam knobs (provisioned, not wired — no live reviewer)."""
    return {"reviewer": None}


def _default_badge_tokens() -> list[str]:
    """Return the default Status-badge taxonomy the doc checker accepts."""
    return [
        "binding",
        "living-ledger",
        "reference",
        "plan",
        "historical",
        "audit",
        "owner-guidance",
        "ideas",
        "archive",
    ]


def _default_readpath_docs() -> list[str]:
    """Return the read-path doc names that seed the reachability roots."""
    return ["AGENT_ORIENTATION.md", "current-state.md"]


def _default_session_markers() -> list[dict[str, str]]:
    """Return the markers every session log must carry (label + substring)."""
    return [
        {"label": "Status badge", "needle": "**Status:**"},
        {"label": "Session idea", "needle": "💡"},
        {"label": "Previous-session review", "needle": "previous-session review"},
    ]


@dataclass
class Config:
    """Host-project configuration for one substrate-kit install."""

    project_id: str = field(default_factory=_new_project_id)
    interpreter: str = field(default_factory=lambda: sys.executable)
    interpreter_for_checks: str | None = None
    state_dir: str = DEFAULT_STATE_DIR
    docs_root: str = "docs"
    sessions_dir: str = ".sessions"
    paths: dict[str, str] = field(default_factory=dict)
    cadence: dict[str, int] = field(default_factory=_default_cadence)
    scopes: dict[str, str] = field(default_factory=dict)
    badge_tokens: list[str] = field(default_factory=_default_badge_tokens)
    readpath_docs: list[str] = field(default_factory=_default_readpath_docs)
    session_markers: list[dict[str, str]] = field(
        default_factory=_default_session_markers,
    )
    reflection: dict = field(default_factory=_default_reflection)
    orientation: dict = field(default_factory=_default_orientation)
    economy: dict = field(default_factory=_default_economy)
    namespace: dict = field(default_factory=_default_namespace)
    seams: list[dict] = field(default_factory=list)
    review_seam: dict = field(default_factory=_default_review_seam)

    def to_json(self) -> str:
        """Serialise the config to indented, key-sorted JSON."""
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> Config:
        """Build a Config from a parsed dict, ignoring unknown keys."""
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


def config_path(root: Path) -> Path:
    """Return the config-file path for a project ``root``."""
    return root / CONFIG_FILENAME


def load_config(root: Path) -> Config:
    """Load the config from ``root``; return defaults if none exists."""
    path = config_path(root)
    if not path.exists():
        return Config()
    data = json.loads(path.read_text(encoding="utf-8"))
    return Config.from_dict(data)


def save_config(root: Path, config: Config) -> None:
    """Write ``config`` to ``root`` atomically."""
    atomic_write_text(config_path(root), config.to_json() + "\n")

# --- engine/lib/state.py ---
"""The state-backend interface and its default JSON implementation.

The *interface* — not a raw JSON shape — is the contract the rest of the engine
codes against (Hermes-final, plan §2), so a future SQLite backend can replace the
JSON one without a rewrite. The default backend is one JSON file written
atomically; mutations inside a ``transaction`` roll back on error and flush once.
"""




STATE_SCHEMA_VERSION = 1


def default_state(project_id: str) -> dict[str, Any]:
    """Return the initial state document for a fresh install."""
    return {
        "version": STATE_SCHEMA_VERSION,
        "project_id": project_id,
        "mode": "guided",
        "promotion_rights": "propose",
        "stage": "integration",
        "stance": "analysis",
        "session_count": 0,
        "slots": {},
        "slot_values": {},
        "open_questions": [],
        "quiet_sessions": 0,
        "graduation": {
            "soft_target_sessions": 50,
            "criteria": {
                "critical_slots_filled_pct": 0.8,
                "blocking_questions": 0,
            },
        },
        "mode_history": [],
        "reflection_buffer": {"active_count": 0, "last_mined": None},
        "graduation_proposed": False,
        "last_compaction_session": 0,
        "review_log": [],
    }


class StateBackend(ABC):
    """Read / write / query / transaction / migrate contract for engine state."""

    version: int = STATE_SCHEMA_VERSION

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Return the value stored at ``key`` or ``default``."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Store ``value`` at ``key`` (flushing unless inside a transaction)."""

    @abstractmethod
    def query(self, prefix: str = "") -> dict[str, Any]:
        """Return all key/value pairs whose key starts with ``prefix``."""

    @abstractmethod
    def transaction(self) -> AbstractContextManager[StateBackend]:
        """Return a context manager that commits on success, rolls back on error."""

    @abstractmethod
    def migrate(self, to_version: int) -> None:
        """Migrate the stored document to schema ``to_version``."""


class JsonStateBackend(StateBackend):
    """A StateBackend backed by one atomically-written JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._data: dict[str, Any] = self._read()
        self._txn_depth = 0

    def _read(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _flush(self) -> None:
        atomic_write_text(
            self._path,
            json.dumps(self._data, indent=2, sort_keys=True) + "\n",
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value stored at ``key`` or ``default``."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store ``value`` at ``key``; flush now unless inside a transaction."""
        self._data[key] = value
        if self._txn_depth == 0:
            self._flush()

    def query(self, prefix: str = "") -> dict[str, Any]:
        """Return all key/value pairs whose key starts with ``prefix``."""
        return {k: v for k, v in self._data.items() if k.startswith(prefix)}

    @contextmanager
    def transaction(self) -> Iterator[JsonStateBackend]:
        """Buffer writes; roll back the whole document on error, else flush once.

        Re-entrant (Q-0223 tail ①): a helper that opens its own transaction may
        be composed inside a caller's wider transaction. Each level snapshots on
        entry and restores its own snapshot on error; only the *outermost* exit
        flushes, so a composed multi-write either fully lands or fully rolls
        back to the enclosing level's snapshot — never a partial flush.
        """
        snapshot = copy.deepcopy(self._data)
        self._txn_depth += 1
        try:
            yield self
        except Exception:
            self._data = snapshot
            raise
        finally:
            self._txn_depth -= 1
        if self._txn_depth == 0:
            self._flush()

    def migrate(self, to_version: int) -> None:
        """Set the stored schema version (no transforms needed at v1)."""
        self._data["version"] = to_version
        self._flush()

    @property
    def data(self) -> dict[str, Any]:
        """Return a shallow copy of the current state document."""
        return dict(self._data)

# --- engine/lib/guardrail.py ---
"""The live-loop guardrail.

A mechanical guarantee (plan: design-corroboration) that the kit never operates
on its own repository root — which would let it mutate the very workflow it runs
inside. Safe targets are the system temp tree, an ``examples/`` subtree of the
kit, or any directory outside the kit. Enforced in code, in the first commit —
not left as a doc.
"""




class UnsafeTargetError(Exception):
    """Raised when a target directory would corrupt the kit's own live loop."""


def assert_safe_target(target: Path, kit_root: Path) -> None:
    """Refuse to operate on the kit's own repo root.

    Unsafe: ``kit_root`` itself or a non-``examples`` path inside it — even
    when the kit checkout lives under the system temp tree (an earlier
    temp-tree shortcut ran first and silently voided the whole guarantee for a
    kit cloned into ``/tmp``). Everything outside ``kit_root``, and the
    ``examples/`` subtree, is safe. A ``kit_root`` that is a *file* (the
    single-file bootstrap has no kit tree to protect) never matches.
    """
    target = Path(target).resolve()
    kit_root = Path(kit_root).resolve()
    inside_kit = target == kit_root or target.is_relative_to(kit_root)
    inside_examples = target.is_relative_to(kit_root / "examples")
    if inside_kit and not inside_examples:
        msg = f"refusing to operate on the kit's own tree: {target}"
        raise UnsafeTargetError(msg)

# --- engine/lib/modes.py ---
"""Integration-mode behavior policies (plan section 3 — the adoption-pace axis).

The ``mode`` state field (observe | guided | active) existed since PR 1 but nothing
read it; this module is the single place its *behavior* is defined, so every
consumer (interview quota, orientation depth, trigger mandates, actuator gating,
graduation) asks one policy table instead of re-deriving the semantics.

The three modes, per the approved plan:

- **observe** — the kit imposes nothing: each session writes a light note, asks
  only 1-2 observation questions, and passively profiles how the user already
  works; after enough sessions it *proposes* a tailored workflow (never
  auto-graduates — proposal only).
- **guided** — the default: the workflow rolls out one practice at a time in a
  fixed order (session logs → idea lifecycle → question router → session-enders
  → gates), each arriving only after the prior is established; triggers may
  mandate questions.
- **active** — the full workflow from session 1; the interview runs aggressively
  (no quota) to fill slots fast.

``promotion_rights`` is the *separate* autonomy axis: what the agent may change
without sign-off. Actuators (economy prunes, maintenance writes) may apply only
when the mode allows it AND promotion_rights is ``"promote"`` — otherwise they
stay dry-run/propose.
"""



MODES = ("observe", "guided", "active")

# The guided-mode rollout order is fixed by the plan; only the pacing is ours.
GUIDED_ROLLOUT = (
    "session_logs",
    "idea_lifecycle",
    "question_router",
    "session_enders",
    "gates",
)

DEFAULT_MODE = "guided"

# One behavior record per mode. quota None = unlimited questions per session.
_MODE_POLICIES: dict[str, dict[str, Any]] = {
    "observe": {
        "question_quota": 2,
        "orientation_depth": "minimal",
        "practices": "none",
        "triggers_mandate": False,
        "actuators_allowed": False,
        "auto_graduate": False,
        "workflow_proposal_after_sessions": 5,
    },
    "guided": {
        "question_quota": 3,
        "orientation_depth": "standard",
        "practices": "rollout",
        "triggers_mandate": True,
        "actuators_allowed": True,
        "auto_graduate": True,
        "workflow_proposal_after_sessions": None,
    },
    "active": {
        "question_quota": None,
        "orientation_depth": "full",
        "practices": "all",
        "triggers_mandate": True,
        "actuators_allowed": True,
        "auto_graduate": True,
        "workflow_proposal_after_sessions": None,
    },
}


def mode_policy(state: dict[str, Any]) -> dict[str, Any]:
    """Return the behavior policy for the state's active mode.

    An unknown or missing mode falls back to the default (``guided``) so every
    consumer fails open onto sane behavior rather than crashing on bad state.
    """
    mode = state.get("mode", DEFAULT_MODE)
    return dict(_MODE_POLICIES.get(mode, _MODE_POLICIES[DEFAULT_MODE]))


def question_quota(state: dict[str, Any]) -> int | None:
    """Return the per-session interview question quota (None = unlimited)."""
    quota = mode_policy(state)["question_quota"]
    return quota if quota is None else int(quota)


def orientation_depth(state: dict[str, Any]) -> str:
    """Return the orientation-injection depth: minimal | standard | full."""
    return str(mode_policy(state)["orientation_depth"])


def triggers_mandate(state: dict[str, Any]) -> bool:
    """True when fired triggers may *mandate* questions (guided/active only)."""
    return bool(mode_policy(state)["triggers_mandate"])


def actuators_may_apply(state: dict[str, Any]) -> bool:
    """True when actuators may apply changes (mode allows AND rights say promote).

    This is the promotion-rights enforcement point: whatever the mode, an agent
    whose ``promotion_rights`` is ``"propose"`` (or ``"observe"``) only ever
    produces dry-run reports.
    """
    if not mode_policy(state)["actuators_allowed"]:
        return False
    return state.get("promotion_rights") == "promote"


def may_auto_graduate(state: dict[str, Any]) -> bool:
    """True when graduation may fire automatically (observe mode proposes only)."""
    return bool(mode_policy(state)["auto_graduate"])


def workflow_proposal_due(state: dict[str, Any]) -> bool:
    """True when observe mode has watched long enough to propose its workflow."""
    threshold = mode_policy(state)["workflow_proposal_after_sessions"]
    if threshold is None:
        return False
    return int(state.get("session_count", 0)) >= int(threshold)


def active_practices(
    state: dict[str, Any],
    cadence: dict[str, int] | None = None,
) -> list[str]:
    """Return the workflow practices currently active under the mode's pacing.

    observe: none (the kit imposes nothing). active: all from session 1.
    guided: one practice unlocks per ``guided_practice_sessions`` sessions
    (config cadence, default 3), in the fixed rollout order — the "only after
    the prior is established" pacing, made deterministic.
    """
    practices = mode_policy(state)["practices"]
    if practices == "none":
        return []
    if practices == "all":
        return list(GUIDED_ROLLOUT)
    interval = int((cadence or {}).get("guided_practice_sessions", 3))
    interval = max(interval, 1)
    sessions = int(state.get("session_count", 0))
    unlocked = 1 + sessions // interval
    return list(GUIDED_ROLLOUT[:unlocked])

# --- engine/interview/question_bank.py ---
"""The interview question bank — the seed set the staged onboarding draws from.

Curation policy (Hermes #7): keep this lean. Add a question only when its slot
genuinely blocks graduation, or a checker keeps flagging its absence; prune
questions that no longer earn their place. Each entry is a plain dict so the bank
ships inside the stdlib-only bootstrap with no parser (the plan named
``question_bank.yml``; a Python module is the simplest form that embeds and runs
identically in ``src`` and the single-file ``dist`` — no YAML/JSON dependency).

Entry fields:
  id        — stable "Q-NNN" identifier.
  slot      — the content slot it fills (matches the project index).
  audience  — "user" (ask the maintainer) or "self" (the agent infers).
  prompt    — the question text.
  routing   — where a confirmed answer lands (a doc:field or state:key).
  priority  — "blocking" | "high" | "normal".
  critical  — True if graduation requires this slot filled (confirmed, not assumed).

Optional fields:
  trigger   — a trigger kind (see engine/loop/triggers.py); the question is pulled
              into a mandatory-question session when that trigger fires.
  objective — True when a different model can verify the answer against evidence
              (the review seam may then confirm a provisional answer); subjective
              slots stay provisional until the user confirms.
  min_len   — anti-gaming floor: an answer shorter than this never fills the slot.
"""


CURATION_RULE = (
    "Lean bank: add a question only when it blocks graduation or a checker keeps "
    "flagging its slot; prune questions that no longer earn their place."
)

QUESTIONS: list[dict] = [
    {
        "id": "Q-001",
        "slot": "integration_mode",
        "audience": "user",
        "prompt": "Adoption pace for the workflow? observe | guided | active.",
        "routing": "state:mode",
        "priority": "blocking",
        "critical": True,
        # The sole blocking+critical slot needs an anti-gaming floor too — the
        # valid values (observe/guided/active) are all >=6 chars, so a floor of
        # 4 rejects a hollow single-char graduation without ever rejecting a
        # real mode.
        "min_len": 4,
    },
    {
        "id": "Q-002",
        "slot": "project_name",
        "audience": "user",
        "prompt": "What is this project called?",
        "routing": "templates/CLAUDE.md:project_name",
        "priority": "high",
        "critical": True,
        "objective": True,
        "min_len": 2,
    },
    {
        "id": "Q-003",
        "slot": "primary_language",
        "audience": "user",
        "prompt": "Primary language / runtime (e.g. Python 3.10, TypeScript)?",
        "routing": "templates/CLAUDE.md:language",
        "priority": "high",
        "critical": True,
        "objective": True,
        "min_len": 3,
    },
    {
        "id": "Q-004",
        "slot": "architecture_layers",
        "audience": "user",
        "prompt": "What are the top-level layers and their import rules?",
        "routing": "templates/architecture.md:layers",
        "priority": "high",
        "critical": True,
        "trigger": "critical_unfilled",
        "objective": True,
        "min_len": 20,
    },
    {
        "id": "Q-005",
        "slot": "verify_command",
        "audience": "user",
        "prompt": "One command that proves a change is good (tests + lint)?",
        "routing": "templates/CLAUDE.md:verify_command",
        "priority": "high",
        "critical": True,
        "objective": True,
        "min_len": 4,
    },
    {
        "id": "Q-006",
        "slot": "ownership_model",
        "audience": "self",
        "prompt": "Which component owns each data store / write path?",
        "routing": "templates/ownership.md:owners",
        "priority": "normal",
        "critical": False,
        "objective": True,
        "min_len": 20,
    },
    {
        "id": "Q-007",
        "slot": "doc_roots",
        "audience": "self",
        "prompt": "Where does durable documentation live?",
        "routing": "state:paths.docs",
        "priority": "normal",
        "critical": False,
    },
    {
        "id": "Q-008",
        "slot": "owner_profile",
        "audience": "user",
        "prompt": "How do you like an agent to work (tone, detail, autonomy)?",
        "routing": "templates/owner-profile.md:style",
        "priority": "normal",
        "critical": False,
    },
    {
        "id": "Q-009",
        "slot": "mutation_seam",
        "audience": "self",
        "prompt": "How are writes gated (the audited mutation seam)?",
        "routing": "templates/runtime_contracts.md:mutations",
        "priority": "normal",
        "critical": False,
        "objective": True,
        "min_len": 20,
    },
    {
        "id": "Q-010",
        "slot": "review_ritual",
        "audience": "user",
        "prompt": "Your PR-review and release rhythm?",
        "routing": "templates/owner-profile.md:procedures",
        "priority": "normal",
        "critical": False,
    },
    {
        "id": "Q-011",
        "slot": "drift_resolution",
        "audience": "self",
        "prompt": "Doc-hygiene checks are failing - what drifted, and what fixes it?",
        "routing": "state:open_questions",
        "priority": "high",
        "critical": False,
        "trigger": "drift",
    },
    {
        "id": "Q-012",
        "slot": "staleness_review",
        "audience": "user",
        "prompt": "Memory looks stale (reconciliation overdue) - what changed since the last update?",
        "routing": "templates/current-state.md:refresh",
        "priority": "normal",
        "critical": False,
        "trigger": "staleness",
    },
    {
        "id": "Q-013",
        "slot": "new_area_ownership",
        "audience": "user",
        "prompt": "A new area appeared with no ownership/folio entry - which component owns it?",
        "routing": "templates/ownership.md:owners",
        "priority": "high",
        "critical": False,
        "trigger": "new_area",
    },
]

# --- engine/interview/stages.py ---
"""Stage state machine + adaptive graduation (plan section 2).

Stage 1 (``integration``) graduates to stage 2 (``steady``) *adaptively* — when
the project's **critical** content slots are mostly filled (by confirmed, not
assumed, answers), no blocking questions remain, and several consecutive sessions
surface no new mandatory question — not at a hard session count.
"""




STAGE_INTEGRATION = "integration"
STAGE_STEADY = "steady"

_DEFAULT_FILL_PCT = 0.8
_DEFAULT_QUIET_SESSIONS = 3


def critical_fill_ratio(slots: dict[str, str], critical: list[str]) -> float:
    """Return the fraction of ``critical`` slots marked ``filled``."""
    if not critical:
        return 1.0
    filled = sum(1 for name in critical if slots.get(name) == "filled")
    return filled / len(critical)


def graduation_ready(
    state: dict[str, Any],
    critical: list[str],
) -> tuple[bool, list[str]]:
    """Return ``(ready, reasons)`` for graduating integration -> steady.

    ``reasons`` lists the unmet criteria when not ready (empty when ready).
    """
    criteria = state.get("graduation", {}).get("criteria", {})
    want_pct = criteria.get("critical_slots_filled_pct", _DEFAULT_FILL_PCT)
    want_quiet = criteria.get("quiet_sessions_required", _DEFAULT_QUIET_SESSIONS)
    reasons: list[str] = []

    ratio = critical_fill_ratio(state.get("slots", {}), critical)
    if ratio < want_pct:
        reasons.append(f"critical slots {ratio:.0%} < {want_pct:.0%}")
    blocking = len(state.get("open_questions", []))
    if blocking:
        reasons.append(f"{blocking} blocking question(s) open")
    quiet = state.get("quiet_sessions", 0)
    if quiet < want_quiet:
        reasons.append(f"quiet streak {quiet} < {want_quiet}")
    return (not reasons, reasons)


def maybe_graduate(backend: Any, critical: list[str]) -> bool:
    """Advance integration -> steady if ready; return whether it graduated.

    Mode-conditional (the plan's per-mode behavior): ``observe`` mode never
    auto-graduates — when ready it records a *proposal* (``graduation_proposed``)
    for the user to accept (switch mode or graduate explicitly); guided/active
    graduate automatically.
    """
    if backend.get("stage") != STAGE_INTEGRATION:
        return False
    ready, _ = graduation_ready(backend.data, critical)
    if not ready:
        return False
    if not may_auto_graduate(backend.data):
        backend.set("graduation_proposed", True)
        return False
    backend.set("stage", STAGE_STEADY)
    return True

# --- engine/interview/interview.py ---
"""The interview pass — fills content slots from the question bank (plan section 4).

A session asks its pending questions. A user-facing answer fills a slot
(``filled``); when no human is present the agent self-answers, recording a
*provisional* assumption (``provisional``) that never counts toward graduation
until confirmed. This is what lets an autonomous run keep moving without blocking:
it records assumptions, flags them, and moves on.
"""




_PRIORITY_ORDER = {"blocking": 0, "high": 1, "normal": 2}
_PLACEHOLDER_ANSWERS = frozenset({"todo", "tbd", "...", "n/a", "?"})
_ANSWER_STRIP = string.punctuation + string.whitespace


def critical_slots(bank: list[dict] | None = None) -> list[str]:
    """Return the slot names the bank marks as critical."""
    bank = QUESTIONS if bank is None else bank
    return [q["slot"] for q in bank if q.get("critical")]


def pending_questions(
    state: dict[str, Any],
    bank: list[dict] | None = None,
) -> list[dict]:
    """Return bank questions whose slot is not yet ``filled``."""
    bank = QUESTIONS if bank is None else bank
    slots = state.get("slots", {})
    return [q for q in bank if slots.get(q["slot"]) != "filled"]


def session_questions(
    state: dict[str, Any],
    bank: list[dict] | None = None,
) -> list[dict]:
    """Return this session's ask list: pending, priority-ordered, quota-capped.

    The cap is the integration mode's question quota (observe asks 1-2, guided a
    few, active unlimited). Blocking questions sort first, so a quota can never
    hide one.
    """
    pending = sorted(
        pending_questions(state, bank),
        key=lambda q: _PRIORITY_ORDER.get(q.get("priority", "normal"), 2),
    )
    quota = question_quota(state)
    return pending if quota is None else pending[:quota]


def answer_is_substantive(question: dict, answer: str) -> bool:
    """True when ``answer`` passes the anti-gaming floor for this slot.

    Completeness counts only non-placeholder content: no leftover ``${slot}``
    marker, not a stock placeholder word, and at least the slot's ``min_len``
    characters — so an autonomous run can't graduate on hollow answers.
    """
    text = answer.strip()
    if not text or "${" in text:
        return False
    # Strip surrounding punctuation before the placeholder-word check so
    # "todo." / "tbd!" / "n/a?" cannot slip past the exact-match set.
    if text.lower().strip(_ANSWER_STRIP) in _PLACEHOLDER_ANSWERS:
        return False
    # Content-free answers never fill a slot: no alphanumeric char at all
    # ("??", "...", "!!"), or a single character repeated ("aaaa", "....").
    if not any(ch.isalnum() for ch in text) or len(set(text)) == 1:
        return False
    return len(text) >= int(question.get("min_len", 1))


def _set_without_open_question(backend: Any, question_id: str | None) -> None:
    """Drop ``question_id`` from open_questions via ``backend.set`` (no flush).

    Called *inside* a transaction so the slot fill and its escalation
    resolution commit in one atomic flush — a crash between two separate
    flushes once left a filled slot with a stale open question that nothing
    automatic could clear.
    """
    if not question_id:
        return
    open_questions = list(backend.get("open_questions", []))
    if question_id in open_questions:
        open_questions.remove(question_id)
        backend.set("open_questions", open_questions)


def record_answer(backend: Any, question: dict, answer: str, *, source: str) -> None:
    """Fill ``question``'s slot from an answer.

    ``source="user"`` confirms the slot (``filled``) when the answer passes the
    anti-gaming floor (``partial`` otherwise); any other source records a
    ``provisional`` self-answer that must be confirmed before it counts. A
    filled answer also resolves the question's escalated open-question entry.
    """
    if source == "user":
        status = "filled" if answer_is_substantive(question, answer) else "partial"
    else:
        status = "provisional"
    slots = dict(backend.get("slots", {}))
    values = dict(backend.get("slot_values", {}))
    slots[question["slot"]] = status
    values[question["slot"]] = {
        "value": answer,
        "source": source,
        "question_id": question["id"],
    }
    with backend.transaction():
        backend.set("slots", slots)
        backend.set("slot_values", values)
        if status == "filled":
            _set_without_open_question(backend, question["id"])


def confirm_slot(backend: Any, slot: str, *, source: str) -> bool:
    """Promote a ``provisional`` slot to ``filled`` (the confirmation seam).

    ``source`` records who confirmed (``"user"`` or ``"reviewer:<name>"``).
    Returns False when the slot is not provisional (nothing to confirm).
    """
    slots = dict(backend.get("slots", {}))
    if slots.get(slot) != "provisional":
        return False
    values = dict(backend.get("slot_values", {}))
    entry = dict(values.get(slot, {}))
    entry["source"] = f"confirmed:{source}"
    slots[slot] = "filled"
    values[slot] = entry
    with backend.transaction():
        backend.set("slots", slots)
        backend.set("slot_values", values)
        _set_without_open_question(backend, entry.get("question_id"))
    return True


def run_session(
    backend: Any,
    answers: dict[str, str],
    *,
    autonomous: bool = False,
    bank: list[dict] | None = None,
) -> dict[str, Any]:
    """Run one interview session, then attempt graduation.

    ``answers`` maps slot -> user answer. A pending question with a user answer is
    confirmed; otherwise, in ``autonomous`` mode it is self-answered provisionally
    (within the integration mode's question quota — blocking questions sort first,
    so the quota never starves one). A session that leaves no blocking question
    unanswered extends the quiet streak; any unanswered blocking question resets
    it AND escalates onto ``open_questions``, which holds graduation until the
    question is answered.
    """
    bank = QUESTIONS if bank is None else bank
    pending = sorted(
        pending_questions(backend.data, bank),
        key=lambda q: _PRIORITY_ORDER.get(q.get("priority", "normal"), 2),
    )
    quota = question_quota(backend.data)
    left_blocking = False
    self_answered = 0
    for question in pending:
        slot = question["slot"]
        blocking = question.get("priority") == "blocking"
        if slot in answers:
            record_answer(backend, question, answers[slot], source="user")
            continue
        if autonomous and (quota is None or self_answered < quota):
            # Never downgrade an existing provisional value (e.g. an
            # adopt-time derived answer) to a placeholder assumption — the
            # slot already carries better content awaiting confirmation.
            if backend.get("slots", {}).get(slot) != "provisional":
                record_answer(
                    backend, question, f"ASSUMED: {slot}", source="assumption"
                )
                self_answered += 1
            if not blocking:
                continue
            # A provisional self-answer does NOT discharge a blocking question
            # — it must still escalate, or an autonomous run could graduate on
            # an unconfirmed assumption for the one slot marked blocking.
        elif not blocking:
            continue
        left_blocking = True
        open_questions = list(backend.get("open_questions", []))
        if question["id"] not in open_questions:
            open_questions.append(question["id"])
            backend.set("open_questions", open_questions)

    backend.set("session_count", int(backend.get("session_count", 0)) + 1)
    quiet = int(backend.get("quiet_sessions", 0))
    backend.set("quiet_sessions", 0 if left_blocking else quiet + 1)

    graduated = maybe_graduate(backend, critical_slots(bank))
    return {
        "session": backend.get("session_count"),
        "pending_after": len(pending_questions(backend.data, bank)),
        "graduated": graduated,
        "stage": backend.get("stage"),
    }

# --- engine/checks/check_docs.py ---
"""Generic doc-hygiene checker (config-driven port of ``check_docs``).

Three portable checks, every input supplied by the caller (from config) rather
than hardcoded:

  1. **badge**      — every ``*.md`` under ``docs_root`` (non-ADR) carries a
     ``> **Status:** `<token>``` line in its first 12 lines, ``<token>`` drawn
     from the project's allowed taxonomy.
  2. **link**       — every relative markdown link ``[text](path)`` resolves to
     an existing file (external / anchor-only links are skipped).
  3. **reachable**  — every live doc is reachable by following links + backtick
     ``<docs>/*.md`` refs from a read-path root (the read-path docs + any
     ``README.md``). Orphans fail unless badged ``historical`` / ``archive`` or
     an ADR.

The host's soft ratchets (top-level pile, recently-shipped) and the
superbot-specific freshness rule are intentionally left behind — they are
project policy, not portable mechanism. Pure stdlib; returns findings rather
than printing so the CLI owns all output.
"""




class Finding(NamedTuple):
    """One doc-hygiene violation: ``path`` is relative to ``docs_root``."""

    path: str
    kind: str
    message: str


# `> **Status:** `<token>`` — the machine-readable badge (rich text may follow).
_BADGE_RE = re.compile(r"\*\*Status:\*\*\s*`([a-z-]+)`")
# ADR filename: NNN-something.md (exempt — ADRs use their own Accepted/Superseded).
_ADR_RE = re.compile(r"^\d+-.*\.md$")
# Markdown link target: [text](target).
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Badges whose docs are retired content and need no inbound link.
_EXEMPT_BADGES = frozenset({"historical", "archive"})

_BADGE_MISSING = "missing `> **Status:** `<token>`` in first 12 lines"
_ORPHAN_MSG = (
    "orphan: not reachable from any read-path doc / README "
    "(link it from one, or badge it historical/archive)"
)


def _md_files(docs_root: Path) -> list[Path]:
    """Return every ``*.md`` under ``docs_root`` (sorted, empty if absent)."""
    if not docs_root.exists():
        return []
    return sorted(docs_root.rglob("*.md"))


def _is_adr(path: Path) -> bool:
    """True for ``decisions/NNN-*.md`` ADR files (badge-exempt)."""
    return path.parent.name == "decisions" and bool(_ADR_RE.match(path.name))


def badge_token(path: Path) -> str | None:
    """Return the doc's Status-badge token from its first 12 lines, or None.

    Public: the trigger detector (and any host tooling) classifies docs by this
    same badge scan — one badge reader, not per-module copies. An unreadable or
    non-UTF-8 file reads as badge-less rather than crashing the whole scan.
    """
    try:
        head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:12])
    except (OSError, UnicodeDecodeError):
        return None
    match = _BADGE_RE.search(head)
    return match.group(1) if match else None


# Backward-compatible alias for the original private name.
_badge_token = badge_token


def _link_target(raw: str) -> str:
    """Normalise a markdown link target (drop ``<>``, title, ``#anchor``)."""
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1:].split(">", 1)[0]
    parts = target.split()
    target = parts[0] if parts else target
    return target.split("#", 1)[0]


def _backtick_docs_re(docs_root: Path) -> re.Pattern[str]:
    """Compile the ``<docs>/*.md`` backtick-ref pattern for this doc root."""
    name = re.escape(docs_root.name)
    return re.compile(rf"`({name}/[\w./-]+\.md)`")


def check_badges(docs_root: Path, badge_tokens: Collection[str]) -> list[Finding]:
    """Every non-ADR doc must declare a Status badge from the taxonomy."""
    allowed = set(badge_tokens)
    findings: list[Finding] = []
    for f in _md_files(docs_root):
        if _is_adr(f):
            continue
        rel = f.relative_to(docs_root).as_posix()
        token = badge_token(f)
        if token is None:
            findings.append(Finding(rel, "badge", _BADGE_MISSING))
        elif token not in allowed:
            allowed_list = ", ".join(sorted(allowed))
            findings.append(
                Finding(
                    rel,
                    "badge",
                    f"invalid badge token `{token}` (allowed: {allowed_list})",
                ),
            )
    return findings


def check_links(docs_root: Path) -> list[Finding]:
    """Relative markdown links inside ``docs_root`` must resolve.

    An unreadable / non-UTF-8 file is reported as an ``encoding`` finding
    instead of crashing the scan (one bad byte must not take down triggers,
    ``maintain``, and ``check`` together).
    """
    findings: list[Finding] = []
    for f in _md_files(docs_root):
        rel = f.relative_to(docs_root).as_posix()
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            findings.append(Finding(rel, "encoding", f"unreadable as UTF-8: {exc}"))
            continue
        for lineno, line in enumerate(lines, 1):
            for raw in _MD_LINK_RE.findall(line):
                if raw.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = _link_target(raw)
                if not target or target.startswith(("http", "mailto:")):
                    continue
                if not (f.parent / target).resolve().exists():
                    msg = f"L{lineno}: dead link -> {raw}"
                    findings.append(Finding(rel, "link", msg))
    return findings


def _outgoing_links(path: Path, docs_root: Path) -> set[Path]:
    """Resolve every relative markdown link + backtick ``<docs>/*.md`` ref."""
    out: set[Path] = set()
    backtick = _backtick_docs_re(docs_root)
    root = docs_root.parent
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return out
    for line in text.splitlines():
        for raw in _MD_LINK_RE.findall(line):
            if raw.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = _link_target(raw)
            if target:
                out.add((path.parent / target).resolve())
        for ref in backtick.findall(line):
            out.add((root / ref).resolve())
    return out


def check_reachable(docs_root: Path, readpath_docs: Sequence[str]) -> list[Finding]:
    """Every live doc must be reachable from a read-path root / README.

    Walks the doc graph (markdown links + backtick ``<docs>/*.md`` refs) from the
    roots; any doc not reached — and not ``historical`` / ``archive`` badged or an
    ADR — is an orphan.
    """
    roots = [docs_root / name for name in readpath_docs]
    roots += sorted(docs_root.rglob("README.md"))
    seen: set[Path] = set()
    queue: deque[Path] = deque()
    for root in roots:
        resolved = root.resolve()
        if root.exists() and resolved not in seen:
            seen.add(resolved)
            queue.append(resolved)
    while queue:
        cur = queue.popleft()
        if cur.suffix != ".md" or not cur.exists():
            continue
        for nxt in _outgoing_links(cur, docs_root):
            if nxt not in seen and nxt.suffix == ".md" and nxt.exists():
                seen.add(nxt)
                queue.append(nxt)

    findings: list[Finding] = []
    for f in _md_files(docs_root):
        if f.resolve() in seen or _is_adr(f):
            continue
        if badge_token(f) in _EXEMPT_BADGES:
            continue
        rel = f.relative_to(docs_root).as_posix()
        findings.append(Finding(rel, "reachable", _ORPHAN_MSG))
    return findings


def run_doc_checks(
    docs_root: Path,
    badge_tokens: Collection[str],
    readpath_docs: Sequence[str],
) -> list[Finding]:
    """Run every doc check and return the combined findings."""
    return (
        check_badges(docs_root, badge_tokens)
        + check_links(docs_root)
        + check_reachable(docs_root, readpath_docs)
    )

# --- engine/checks/check_session_log.py ---
"""Generic session-log completeness checker (config-driven port).

The session workflow asks every session to end with a
``<sessions_dir>/<date>-<slug>.md`` log that carries a set of required markers
(by default: a Status badge, a session-idea flag, and a previous-session review).
Each marker is a ``{"label", "needle"}`` pair from ``substrate.config.json``, so a
host tunes the ritual without touching engine code.

Unlike the host's version this port does **not** shell out to ``git`` to pick the
"current" log — ``subprocess`` is banned in engine code and is host-CI sugar
anyway. The current log is the newest ``*.md`` by mtime under ``sessions_dir``
(the CLI also accepts an explicit ``--file``). Pure stdlib; returns the missing
markers rather than printing.
"""




def missing_markers(text: str, markers: Sequence[Mapping[str, str]]) -> list[str]:
    """Return the labels of markers whose needle is absent from ``text``.

    Tolerant of partial host-config entries: a marker without a ``needle`` is
    skipped (nothing to search for) rather than raising, and a missing
    ``label`` reports as ``"?"``.
    """
    lower = text.lower()
    return [
        m.get("label", "?")
        for m in markers
        if m.get("needle") and m.get("needle", "").lower() not in lower
    ]


def latest_session_log(sessions_dir: Path) -> Path | None:
    """Best guess at this session's log: newest ``*.md`` by mtime (skip README)."""
    if not sessions_dir.is_dir():
        return None
    candidates = [p for p in sessions_dir.glob("*.md") if p.name != "README.md"]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def check_log(path: Path, markers: Sequence[Mapping[str, str]]) -> list[str]:
    """Return the missing-marker labels for one log file (all if unreadable)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return [m["label"] for m in markers]
    return missing_markers(text, markers)

# --- engine/checks/check_namespace.py ---
"""Portable namespace / shadowing guard (Lane B6, the Q-0200 class).

Three AST-level checks over the Python roots a host configures
(``config.namespace``):

  1. **in-module shadowing** — the same top-level ``def`` / ``class`` name
     bound twice in one module; the later binding silently wins and the
     earlier one dies unnoticed (superbot's ``round_composition`` collision,
     caught only at CI).
  2. **cross-module collision** — the same public (non-underscore) top-level
     name defined in two modules of one package, unless one of the two is the
     package's ``__init__.py`` (the deliberate re-export pattern).
  3. **reserved names** — a name from the configured reserved map
     (``{"Name": "canonical/module.py"}``) defined outside its canonical
     module.

Uses only stdlib ``ast``; a file that fails to parse becomes a
``namespace-parse`` finding, never an exception. Findings reuse the
``Finding`` record from ``engine.checks.check_docs`` with paths relative to
the scanned root where possible.
"""




_NS_DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _ns_rel(path: Path, root: Path) -> str:
    """Return ``path`` relative to ``root`` (posix) when possible, else str."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _ns_py_files(root: Path) -> list[Path]:
    """Return the ``*.py`` files under ``root`` (or ``root`` itself if a file)."""
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _ns_top_level_defs(tree: ast.Module) -> list[tuple[str, int]]:
    """Return ``(name, lineno)`` for every top-level def/class in ``tree``."""
    return [
        (node.name, node.lineno)
        for node in tree.body
        if isinstance(node, _NS_DEF_NODES)
    ]


def _ns_overloaded_names(tree: ast.Module) -> set[str]:
    """Names whose top-level defs carry ``@overload`` — not shadowing.

    ``@typing.overload`` stacks re-bind the same name by design; flagging them
    as in-module shadowing was a verified false positive.
    """
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            if (
                isinstance(deco, ast.Name)
                and deco.id == "overload"
                or isinstance(deco, ast.Attribute)
                and deco.attr == "overload"
            ):
                names.add(node.name)
    return names


def _ns_dispatch_registered_names(tree: ast.Module) -> set[str]:
    """Names whose top-level defs carry ``@<x>.register`` — not shadowing.

    The ``functools.singledispatch`` idiom re-binds the same name (canonically
    ``def _``) once per registered type; the ``.register`` decorator captures
    each function, so the last global binding is irrelevant. Flagging the
    repeated defs as in-module shadowing was a verified false positive.
    Handles both ``@process.register`` and ``@process.register(int)``.
    """
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            target = deco.func if isinstance(deco, ast.Call) else deco
            if isinstance(target, ast.Attribute) and target.attr == "register":
                names.add(node.name)
    return names


def _ns_matches_canonical(rel: str, canonical: str) -> bool:
    """True when the scanned relpath is the reserved name's canonical module."""
    canon = canonical.replace("\\", "/").lstrip("./")
    return rel == canon or rel.endswith(f"/{canon}")


def check_namespace(
    roots: list[Path],
    *,
    reserved: dict[str, str] | None = None,
) -> list[Finding]:
    """Run the three namespace checks over ``roots``; return the findings.

    ``reserved`` maps a name to the canonical module relpath allowed to define
    it. Kinds: ``namespace`` for collisions, ``namespace-parse`` for files
    that fail to parse (reported, never raised).
    """
    reserved = reserved or {}
    findings: list[Finding] = []
    # (package dir, public name) -> [(rel, module filename, lineno)]
    package_defs: dict[tuple[str, str], list[tuple[str, str, int]]] = {}

    for root in roots:
        rel_base = root.parent if root.is_file() else root
        for py in _ns_py_files(root):
            rel = _ns_rel(py, rel_base)
            try:
                tree = ast.parse(py.read_text(encoding="utf-8"))
            except (SyntaxError, ValueError, OSError, UnicodeDecodeError) as exc:
                lineno = getattr(exc, "lineno", None)
                where = f"L{lineno}: " if lineno else ""
                msg = f"{where}failed to parse: {exc.__class__.__name__}: {exc}"
                findings.append(Finding(rel, "namespace-parse", msg))
                continue

            seen: dict[str, int] = {}
            # `_` is the conventional throwaway (and the canonical
            # singledispatch register target); `.register`-decorated defs are
            # the named-function dispatch form — neither is real shadowing.
            exempt_shadow = _ns_overloaded_names(tree)
            exempt_shadow |= _ns_dispatch_registered_names(tree)
            for name, lineno in _ns_top_level_defs(tree):
                if name in seen and name not in exempt_shadow and name != "_":
                    msg = (
                        f"`{name}` defined twice in one module "
                        f"(L{seen[name]} and L{lineno}) — the later def "
                        "silently shadows the earlier"
                    )
                    findings.append(Finding(rel, "namespace", msg))
                seen.setdefault(name, lineno)
                if not name.startswith("_"):
                    key = (py.parent.resolve().as_posix(), name)
                    package_defs.setdefault(key, []).append(
                        (rel, py.name, lineno),
                    )
                canonical = reserved.get(name)
                if canonical is not None and not _ns_matches_canonical(
                    rel,
                    canonical,
                ):
                    msg = (
                        f"L{lineno}: reserved name `{name}` defined outside "
                        f"its canonical module `{canonical}`"
                    )
                    findings.append(Finding(rel, "namespace", msg))

    for (_, name), sites in sorted(package_defs.items()):
        modules = {filename for _, filename, _ in sites}
        non_init = [s for s in sites if s[1] != "__init__.py"]
        if len(modules) < 2 or len({s[1] for s in non_init}) < 2:
            continue  # one module, or an __init__ re-export pair
        site_list = ", ".join(f"{rel}:L{lineno}" for rel, _, lineno in non_init)
        msg = (
            f"public name `{name}` defined in multiple modules of one "
            f"package ({site_list}) — rename or move to a shared home"
        )
        findings.append(Finding(non_init[0][0], "namespace", msg))
    return findings

# --- engine/checks/check_seam_authority.py ---
r"""Config-driven seam-authority fences (Lane B6).

A *seam* is a boundary the host declares in ``config.seams`` — "all writes go
through the mutation service", "no direct pool access outside the db layer" —
generalising superbot's hardcoded architecture fences into pure data. Each
seam is a dict::

    {"name": "db-seam",
     "paths": ["src/**/*.py"],        # globs to scan, relative to root
     "forbidden": "pool\\.execute",   # regex; a hit is a violation
     "allowed": ["src/db/**"],        # exempt globs (the seam's own home)
     "message": "call db.* helpers, never the pool directly"}

The scan is plain line-by-line text matching (no AST, no imports) so it works
on any language the host points it at. A regex hit in a non-exempt file
becomes a ``Finding(kind="seam")`` whose message carries the seam name, the
configured message, and the line number. Findings reuse the ``Finding``
record from ``engine.checks.check_docs``; unreadable/binary files are skipped.
"""





def _seam_files(root: Path, globs: list[str]) -> list[Path]:
    """Return the de-duplicated files matched by ``globs`` under ``root``."""
    matched: set[Path] = set()
    for pattern in globs:
        for candidate in root.glob(pattern):
            if candidate.is_file():
                matched.add(candidate)
    return sorted(matched)


def _seam_exempt_files(root: Path, allowed: list[str]) -> set[Path]:
    """Resolve the exempt set with the SAME glob semantics as ``paths``.

    fnmatch let ``*`` cross ``/`` — an ``allowed`` pattern like ``src/*``
    silently exempted ``src/sub/hack.py`` and opened a fence gap. Re-globbing
    with ``root.glob`` keeps both sides of the seam on pathlib semantics.

    A glob hit that is a *directory* is expanded to the files under it — a
    trailing ``**`` (the documented ``src/db/**`` "own home" form) matches only
    directories in ``Path.glob``, so exempting by raw glob hits compared the
    file being scanned against a set of dirs and exempted **nothing**: a seam
    flagged its own home. Directory hits now contribute their whole file
    subtree (the ``economy`` reference-scan idiom), so ``src/db/**``,
    ``src/db/*`` and ``src/db/**/*`` all exempt the subtree as documented.
    """
    exempt: set[Path] = set()
    for pattern in allowed:
        for hit in root.glob(pattern):
            if hit.is_file():
                exempt.add(hit)
            elif hit.is_dir():
                exempt.update(p for p in hit.rglob("*") if p.is_file())
    return exempt


def check_seam_authority(root: Path, seams: list[dict]) -> list[Finding]:
    """Scan the configured seams under ``root``; return the violations.

    Each seam dict supplies ``name``, ``paths`` (globs to scan), ``forbidden``
    (a regex), optional ``allowed`` (exempt globs), and ``message``. A seam
    with an invalid regex is itself reported as a finding rather than raising
    (a broken fence should fail loud in the report, not crash the check).
    """
    findings: list[Finding] = []
    for seam in seams:
        name = seam.get("name", "unnamed")
        message = seam.get("message", "forbidden pattern")
        pattern = seam.get("forbidden", "")
        if not pattern:
            # An empty pattern's ``.search`` matches every line — a seam with no
            # ``forbidden`` would flag every line of every in-scope file. That is
            # a misconfiguration; report it loud instead of drowning the report.
            msg = f"seam `{name}`: no `forbidden` regex configured — seam skipped"
            findings.append(Finding("", "seam", msg))
            continue
        try:
            forbidden = re.compile(pattern)
        except re.error as exc:
            msg = f"seam `{name}`: invalid forbidden regex: {exc}"
            findings.append(Finding("", "seam", msg))
            continue
        exempt = _seam_exempt_files(root, list(seam.get("allowed", [])))
        for path in _seam_files(root, list(seam.get("paths", []))):
            rel = path.relative_to(root).as_posix()
            if path in exempt:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if forbidden.search(line):
                    msg = f"L{lineno}: seam `{name}`: {message}"
                    findings.append(Finding(rel, "seam", msg))
    return findings

# --- engine/checks/check_orientation_budget.py ---
"""Orientation-budget gate — the K0 <=7,000-word boot-read cap (Lane B6).

Orientation cost is the tax every session pays before real work starts, so
the kit meters it: the *boot set* (``config.orientation["boot_docs"]``,
falling back to ``config.readpath_docs`` when empty) must total no more than
``config.orientation["budget_words"]`` words. Boot-doc entries name files
under ``docs_root``; an entry containing ``/`` resolves from the project root
instead, so hosts can meter root-level docs (a journal, a CLAUDE.md) too.

Per-doc self-caps ride on top: a doc whose first 12 lines declare
``substrate-budget: N words`` is individually capped at N — a living doc can
pin its own growth ceiling without touching config.

Finding kinds: ``orientation-missing`` (a boot doc is absent),
``orientation-budget`` (the total blows the budget), ``orientation-doc-cap``
(a self-capped doc outgrew its declared cap). Findings reuse the ``Finding``
record from ``engine.checks.check_docs``.
"""




# `substrate-budget: 500 words` — the per-doc self-cap declaration.
_OB_SELF_CAP_RE = re.compile(r"substrate-budget:\s*(\d+)\s*words", re.IGNORECASE)
_OB_HEAD_LINES = 12
_OB_TOTAL_KEY = "_total"


def _ob_word_count(path: Path) -> int | None:
    """Return the doc's word count, or ``None`` when it cannot be read."""
    try:
        return len(path.read_text(encoding="utf-8").split())
    except (OSError, UnicodeDecodeError):
        return None


def _ob_self_cap(path: Path) -> int | None:
    """Return the doc's declared self-cap from its first 12 lines, if any."""
    try:
        head = path.read_text(encoding="utf-8").splitlines()[:_OB_HEAD_LINES]
    except (OSError, UnicodeDecodeError):
        return None
    match = _OB_SELF_CAP_RE.search("\n".join(head))
    return int(match.group(1)) if match else None


def _ob_rel(path: Path, root: Path) -> str:
    """Return ``path`` relative to ``root`` (posix) when possible, else str."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def orientation_word_count(root: Path, boot_docs: list[Path]) -> dict[str, int]:
    """Return per-doc word counts plus a ``_total`` for the boot set.

    Keys are paths relative to ``root`` where possible. A missing or
    unreadable doc counts 0 here — ``check_orientation_budget`` is the layer
    that reports it.
    """
    counts: dict[str, int] = {}
    total = 0
    for doc in boot_docs:
        words = _ob_word_count(doc) or 0
        counts[_ob_rel(doc, root)] = words
        total += words
    counts[_OB_TOTAL_KEY] = total
    return counts


def _ob_boot_paths(root: Path, config: Config) -> list[Path]:
    """Resolve the configured boot set to concrete paths.

    Explicit ``orientation["boot_docs"]`` entries: a bare name resolves under
    ``docs_root``, an entry with ``/`` resolves from the project root. The
    ``readpath_docs`` fallback resolves under ``docs_root`` unconditionally —
    matching ``check_reachable``, which reads the same key.
    """
    orientation = config.orientation or {}
    docs_root = root / config.docs_root
    explicit = list(orientation.get("boot_docs") or [])
    if explicit:
        # Explicit boot docs: a bare name resolves under docs_root, an entry
        # with "/" resolves from the project root (CONSTITUTION.md etc.).
        return [root / e if "/" in e else docs_root / e for e in explicit]
    # readpath_docs fallback: resolve under docs_root unconditionally, matching
    # check_reachable — the two consumers of that key must agree.
    return [docs_root / e for e in config.readpath_docs]


def check_orientation_budget(root: Path, config: Config) -> list[Finding]:
    """Meter the boot-read set against the orientation budget.

    Reports missing boot docs (``orientation-missing``), a total word count
    over ``orientation["budget_words"]`` (``orientation-budget``), and any doc
    that outgrew its own ``substrate-budget: N words`` self-cap
    (``orientation-doc-cap``).
    """
    findings: list[Finding] = []
    boot_paths = _ob_boot_paths(root, config)
    for doc in boot_paths:
        if not doc.is_file():
            msg = "boot doc missing — fix the path or the orientation config"
            findings.append(Finding(_ob_rel(doc, root), "orientation-missing", msg))

    counts = orientation_word_count(root, boot_paths)
    budget = int((config.orientation or {}).get("budget_words", 7000))
    total = counts[_OB_TOTAL_KEY]
    if total > budget:
        msg = (
            f"boot-read set totals {total} words, over the "
            f"{budget}-word orientation budget — trim or demote a boot doc"
        )
        findings.append(Finding(_OB_TOTAL_KEY, "orientation-budget", msg))

    for doc in boot_paths:
        cap = _ob_self_cap(doc)
        if cap is None:
            continue
        words = counts.get(_ob_rel(doc, root), 0)
        if words > cap:
            msg = f"doc is {words} words, over its {cap}-word self-cap"
            findings.append(Finding(_ob_rel(doc, root), "orientation-doc-cap", msg))
    return findings

# --- engine/ledger.py ---
"""Decision ledger — the ``[D-NNNN]`` provenance-separated rulebook (Lane B6).

Implements the kit's ``docs/decisions.md`` grammar (plan: Q-0214.4 depth — a
constitution cites decisions by id instead of narrating them inline). One
entry is::

    ## [D-0001] <title>
    - status: decided | superseded | retired
    - date: YYYY-MM-DD
    - supersedes: D-NNNN        (optional)
    - superseded-by: D-NNNN     (stamped on the OLD entry when superseded)
    - verdict: <one ruling line>
    - why: <2-3 lines, continuation lines allowed>
    - provenance: <link or ref>

``parse_ledger`` is tolerant of prose between entries (the ledger is a living
markdown doc, not a database). ``append_decision`` assigns the next id and —
when superseding — rewrites the old entry in place so the chain is stamped on
both ends. ``check_ledger`` and ``check_stamp_discipline`` are the hygiene
checkers, reusing the ``Finding`` record from ``engine.checks.check_docs``.
Pure stdlib; every write goes through ``atomic_write_text``.
"""




LEDGER_FILENAME = "decisions.md"

# `## [D-0001] <title>` — the strict entry heading.
_LED_HEADING_RE = re.compile(r"^## \[(D-\d{3,})\] (.+)$")
# Any `## ` heading that *tries* to be an entry but fails the strict form.
_LED_HEADING_ATTEMPT_RE = re.compile(r"^##\s*\[?\s*D-", re.IGNORECASE)
# `- key: value` field line inside an entry block.
_LED_FIELD_RE = re.compile(r"^- ([a-z-]+):\s*(.*)$")
# A bare decision id, for supersedes targets and stamp-discipline citations.
_LED_ID_RE = re.compile(r"\bD-\d{3,}\b")
_LED_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_LED_STATUSES = frozenset({"decided", "superseded", "retired"})
_LED_REQUIRED_FIELDS = ("status", "date", "verdict", "why", "provenance")

_LED_HEADER = """# Decisions

> **Status:** `living-ledger` — append-only decision ledger; entries are \
superseded, never deleted.

<!-- Grammar: ## [D-NNNN] <title> / - status: decided|superseded|retired / \
- date: YYYY-MM-DD / - supersedes: D-NNNN (opt) / - superseded-by: D-NNNN \
(opt) / - verdict: <one line> / - why: <2-3 lines> / - provenance: <ref> -->
"""


def _led_field_key(raw: str) -> str:
    """Map a grammar field name to its entry-dict key (``-`` -> ``_``)."""
    return raw.replace("-", "_")


def _led_blocks(text: str) -> list[tuple[int, list[str]]]:
    """Split ``text`` into entry blocks: ``(heading lineno, block lines)``.

    A block starts at any ``## `` heading that looks like a decision entry
    (strict or malformed) and runs until the next ``## `` heading or EOF.
    Prose outside blocks is ignored.
    """
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] | None = None
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            current = None
            if _LED_HEADING_ATTEMPT_RE.match(line):
                current = [line]
                blocks.append((lineno, current))
        elif current is not None:
            current.append(line)
    return blocks


def _led_parse_block(lines: list[str]) -> dict | None:
    """Parse one entry block into a dict, or ``None`` if the heading is bad."""
    match = _LED_HEADING_RE.match(lines[0])
    if match is None:
        return None
    entry: dict = {
        "id": match.group(1),
        "title": match.group(2).strip(),
        "status": None,
        "date": None,
        "supersedes": None,
        "superseded_by": None,
        "verdict": None,
        "why": None,
        "provenance": None,
    }
    last_key: str | None = None
    for line in lines[1:]:
        field = _LED_FIELD_RE.match(line)
        if field is not None:
            key = _led_field_key(field.group(1))
            if key in entry and key not in ("id", "title"):
                entry[key] = field.group(2).strip()
                last_key = key
            else:
                last_key = None
        elif line[:1].isspace() and line.strip() and last_key is not None:
            # Continuation line (indented) — the multi-line `why` case.
            entry[last_key] = f"{entry[last_key]}\n{line.strip()}"
        elif not line.strip():
            last_key = None
    return entry


def parse_ledger(text: str) -> list[dict]:
    """Parse ledger ``text`` into entry dicts, tolerating prose between entries.

    Malformed headings are skipped here (``check_ledger`` reports them);
    missing fields parse as ``None``.
    """
    entries: list[dict] = []
    for _, lines in _led_blocks(text):
        entry = _led_parse_block(lines)
        if entry is not None:
            entries.append(entry)
    return entries


def next_decision_id(entries: list[dict]) -> str:
    """Return the next free decision id (``D-0001`` for an empty ledger)."""
    highest = 0
    for entry in entries:
        try:
            highest = max(highest, int(entry["id"].split("-", 1)[1]))
        except (KeyError, IndexError, ValueError):
            continue
    return f"D-{highest + 1:04d}"


def _led_format_entry(entry: dict) -> str:
    """Render one entry dict back into its grammar block."""
    lines = [f"## [{entry['id']}] {entry['title']}"]
    lines.append(f"- status: {entry['status']}")
    lines.append(f"- date: {entry['date']}")
    if entry.get("supersedes"):
        lines.append(f"- supersedes: {entry['supersedes']}")
    if entry.get("superseded_by"):
        lines.append(f"- superseded-by: {entry['superseded_by']}")
    lines.append(f"- verdict: {entry['verdict']}")
    why = str(entry["why"]).split("\n")
    lines.append(f"- why: {why[0]}")
    lines.extend(f"  {cont}" for cont in why[1:])
    lines.append(f"- provenance: {entry['provenance']}")
    return "\n".join(lines)


def _led_stamp_superseded(text: str, old_id: str, new_id: str) -> str:
    """Rewrite ``old_id``'s entry in ``text``: status + superseded-by stamp."""
    out: list[str] = []
    in_target = False
    stamped = False
    for line in text.splitlines():
        if line.startswith("## "):
            # ANY level-2 heading ends the current block (mirrors _led_blocks)
            # — a prose section after the target must never get stamped.
            heading = _LED_HEADING_RE.match(line)
            in_target = heading is not None and heading.group(1) == old_id
        elif in_target and not line.strip():
            # An entry's field block is contiguous and ends at its first blank
            # line. Without this, a target that is the LAST entry keeps
            # ``in_target`` true to EOF (no later ``## `` to reset it) and would
            # silently stamp any field-shaped bullet in trailing prose.
            in_target = False
        field = _LED_FIELD_RE.match(line) if in_target else None
        if field is not None:
            key = field.group(1)
            if key == "status":
                out.append("- status: superseded")
                out.append(f"- superseded-by: {new_id}")
                stamped = True
                continue
            if key == "superseded-by" and stamped:
                continue  # replaced above
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def append_decision(
    path: Path,
    *,
    title: str,
    verdict: str,
    why: str,
    provenance: str,
    supersedes: str | None = None,
    date: str | None = None,
) -> dict:
    """Append a new decision to the ledger at ``path`` and return its dict.

    Creates the file (header + grammar comment) when absent, assigns the next
    free id, and — when ``supersedes`` names an existing entry — rewrites that
    old entry in place (``status: superseded`` plus a ``superseded-by`` stamp)
    so the chain is recorded on both ends. The whole file is written atomically.
    Raises ``ValueError`` when ``supersedes`` names an id not in the ledger.
    """
    text = path.read_text(encoding="utf-8") if path.exists() else _LED_HEADER
    entries = parse_ledger(text)
    if supersedes is not None:
        known = {entry["id"] for entry in entries}
        if supersedes not in known:
            msg = f"supersedes target {supersedes} not found in {path.name}"
            raise ValueError(msg)
    entry = {
        "id": next_decision_id(entries),
        "title": title,
        "status": "decided",
        "date": date or _led_date.today().isoformat(),
        "supersedes": supersedes,
        "superseded_by": None,
        "verdict": verdict,
        "why": why,
        "provenance": provenance,
    }
    if supersedes is not None:
        text = _led_stamp_superseded(text, supersedes, entry["id"])
    if not text.endswith("\n"):
        text += "\n"
    atomic_write_text(path, f"{text}\n{_led_format_entry(entry)}\n")
    return entry


def current_rules(entries: list[dict]) -> list[dict]:
    """Return the live rule set: supersedes chains resolved, retired dropped.

    An entry is live when its status is neither ``superseded`` nor ``retired``
    *and* no other entry names it as a supersedes target (chain resolution
    holds even when the old entry missed its stamp).
    """
    replaced = {e["supersedes"] for e in entries if e.get("supersedes")}
    return [
        e
        for e in entries
        if e.get("status") not in ("superseded", "retired") and e["id"] not in replaced
    ]


def check_ledger(path: Path) -> list[Finding]:
    """Validate the ledger grammar; return findings (empty for a clean file).

    Flags: unparseable entry blocks, missing/invalid required fields, duplicate
    ids, dangling ``supersedes`` targets, non-monotonic ids, and a superseded
    entry missing its ``superseded-by`` stamp. An absent ledger yields no
    findings (adoption plants it).
    """
    if not path.exists():
        return []
    rel = path.name
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    entries: list[dict] = []
    for lineno, lines in _led_blocks(text):
        entry = _led_parse_block(lines)
        if entry is None:
            msg = f"L{lineno}: unparseable entry heading: {lines[0].strip()}"
            findings.append(Finding(rel, "ledger", msg))
            continue
        entries.append(entry)
        for field in _LED_REQUIRED_FIELDS:
            if not entry.get(field):
                msg = f"L{lineno}: {entry['id']} missing required field `{field}`"
                findings.append(Finding(rel, "ledger", msg))
        status = entry.get("status")
        if status and status not in _LED_STATUSES:
            allowed = ", ".join(sorted(_LED_STATUSES))
            msg = f"L{lineno}: {entry['id']} invalid status `{status}` ({allowed})"
            findings.append(Finding(rel, "ledger", msg))
        if entry.get("date") and not _LED_DATE_RE.match(entry["date"]):
            msg = f"L{lineno}: {entry['id']} invalid date `{entry['date']}`"
            findings.append(Finding(rel, "ledger", msg))
        if status == "superseded" and not entry.get("superseded_by"):
            msg = f"L{lineno}: {entry['id']} superseded without a superseded-by stamp"
            findings.append(Finding(rel, "ledger", msg))

    seen: set[str] = set()
    known = {entry["id"] for entry in entries}
    previous = 0
    for entry in entries:
        number = int(entry["id"].split("-", 1)[1])
        if entry["id"] in seen:
            findings.append(Finding(rel, "ledger", f"duplicate id {entry['id']}"))
        elif number <= previous:
            msg = f"non-monotonic id {entry['id']} after D-{previous:04d}"
            findings.append(Finding(rel, "ledger", msg))
        seen.add(entry["id"])
        previous = max(previous, number)
        target = entry.get("supersedes")
        if target and target not in known:
            msg = f"{entry['id']} supersedes dangling target {target}"
            findings.append(Finding(rel, "ledger", msg))
    return findings


def check_stamp_discipline(docs_root: Path, ledger_path: Path) -> list[Finding]:
    """Flag a decision id cited from more than one doc outside the ledger.

    The provenance-separated model wants each ``D-NNNN`` stamped at exactly one
    home (the rule it justifies); a second citation is drift risk — when the
    decision changes, one of the two goes stale. Kind ``stamp`` (warn-class).
    """
    if not docs_root.exists():
        return []
    ledger_resolved = ledger_path.resolve()
    citations: dict[str, list[str]] = {}
    for doc in sorted(docs_root.rglob("*.md")):
        if doc.resolve() == ledger_resolved:
            continue
        try:
            text = doc.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = doc.relative_to(docs_root).as_posix()
        for cited in set(_LED_ID_RE.findall(text)):
            citations.setdefault(cited, []).append(rel)
    findings: list[Finding] = []
    for cited, docs in sorted(citations.items()):
        if len(docs) > 1:
            cite_list = ", ".join(sorted(docs))
            msg = (
                f"{cited} cited from {len(docs)} docs ({cite_list}) — "
                "stamp each decision at one home"
            )
            findings.append(Finding(sorted(docs)[0], "stamp", msg))
    return findings

# --- engine/loop/kpis.py ---
"""Workflow KPIs for the self-improving loop (plan section 5, Lane B1).

Deterministic read-only metrics over the state document + sessions directory:
``router_metrics`` measures the question-router's health (slot completeness,
open questions, the assumption-confirmation rate that keeps autonomous runs
honest), ``workflow_kpis`` adds the session/reflection counters, and
``kpi_footer`` renders the one-line 📊 summary the orientation and reports
embed. Pure stdlib; returns data / text, never prints.
"""




def _kpi_confirmation_rate(slot_values: dict[str, Any]) -> float:
    """Return confirmed-over-self-answered for the recorded slot values.

    Self-answered slots are those whose ``source`` is ``"assumption"`` or
    starts with ``"confirmed:"`` (a confirmed former assumption). With no
    self-answered slots there is nothing to confirm — the rate is 1.0.
    """
    confirmed = 0
    self_answered = 0
    if not isinstance(slot_values, dict):
        return 1.0
    for entry in slot_values.values():
        if not isinstance(entry, dict):
            # A hand-corrupted state.json can carry a non-dict slot value; skip
            # it rather than raising (the kit's read-side fail-open contract —
            # a KPI read must never brick session-close / maintain). Matches the
            # non-dict guards in reflections / episodes / maintenance.
            continue
        source = str(entry.get("source", ""))
        if source.startswith("confirmed:"):
            confirmed += 1
            self_answered += 1
        elif source == "assumption":
            self_answered += 1
    if self_answered == 0:
        return 1.0
    return confirmed / self_answered


def router_metrics(state: dict[str, Any]) -> dict[str, Any]:
    """Return the question-router health metrics for one state document.

    ``completeness_pct`` counts ``filled`` slots only — ``provisional`` and
    ``partial`` answers never inflate completeness (the anti-gaming floor's
    KPI mirror). With no recorded slots completeness is 0.0.
    """
    slots = state.get("slots", {})
    statuses = list(slots.values())
    total = len(statuses)
    filled = statuses.count("filled")
    provisional = statuses.count("provisional")
    completeness = round(100.0 * filled / total, 1) if total else 0.0
    return {
        "slots_total": total,
        "slots_filled": filled,
        "slots_provisional": provisional,
        "completeness_pct": completeness,
        "open_questions": len(state.get("open_questions", [])),
        "assumption_confirmation_rate": _kpi_confirmation_rate(
            state.get("slot_values", {}),
        ),
        "quiet_sessions": int(state.get("quiet_sessions", 0)),
        "session_count": int(state.get("session_count", 0)),
    }


def workflow_kpis(state: dict[str, Any], sessions_dir: Path) -> dict[str, Any]:
    """Return the full workflow KPI record: router metrics + session counters.

    ``sessions_logged`` counts ``*.md`` logs under ``sessions_dir`` (README
    excluded, 0 when the directory is absent); ``reflections_active`` reads
    the state's reflection-buffer counter.
    """
    kpis = router_metrics(state)
    logged = 0
    if sessions_dir.is_dir():
        logged = sum(1 for p in sessions_dir.glob("*.md") if p.name != "README.md")
    buffer = state.get("reflection_buffer", {})
    kpis["sessions_logged"] = logged
    kpis["reflections_active"] = int(buffer.get("active_count", 0))
    kpis["stage"] = state.get("stage")
    kpis["mode"] = state.get("mode")
    return kpis


def kpi_footer(kpis: dict[str, Any]) -> str:
    """Render the one-line 📊 KPI summary for orientation blocks and reports.

    Router metrics always appear; the workflow extras (logged sessions,
    active lessons, mode, stage) appear when present in ``kpis``.
    """
    completeness = float(kpis.get("completeness_pct", 0.0))
    parts = [
        f"completeness {completeness:.0f}%",
        f"open-Q {kpis.get('open_questions', 0)}",
        f"sessions {kpis.get('session_count', 0)}",
        f"quiet {kpis.get('quiet_sessions', 0)}",
    ]
    if "sessions_logged" in kpis:
        parts.append(f"logged {kpis['sessions_logged']}")
    if "reflections_active" in kpis:
        parts.append(f"lessons {kpis['reflections_active']}")
    if kpis.get("mode") is not None:
        parts.append(f"mode {kpis['mode']}")
    if kpis.get("stage") is not None:
        parts.append(f"stage {kpis['stage']}")
    return "📊 substrate: " + " · ".join(parts)

# --- engine/loop/reflections.py ---
"""Reflection buffer — the loop's compact learned-lesson memory (plan lane B2).

Reflections are small ``{"lesson", "evidence", "tags"}`` records mined from
session logs or added deliberately, stored in one atomically-written JSON file
(``<state_dir>/reflections.json``). The buffer is deliberately tiny — a hard
``buffer_size`` cap keeps the orientation injection cheap — and fail-open: a
missing or corrupt file reads as an empty list, never a crash. The miner is
deterministic and read-only; the caller decides what (if anything) becomes a
stored reflection.
"""




REFLECTIONS_FILENAME = "reflections.json"

_REF_ID_RE = re.compile(r"^R-(\d+)$")
_REF_IDEA_MARK = "\N{ELECTRIC LIGHT BULB}"  # 💡 — session-idea lines
_REF_FLAG_MARK = "\N{BLACK FLAG}"  # ⚑ — self-initiated / friction flags
_REF_PATH_SUFFIXES = (".py", ".md", ".js", ".ts", ".yml", ".json")
_REF_STRIP_CHARS = "`'\"()[]<>,;:!?."


def load_reflections(path: Path) -> list[dict]:
    """Return the reflection entries at ``path`` — ``[]`` on absent/corrupt."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def _ref_save(path: Path, entries: list[dict]) -> None:
    """Write ``entries`` to ``path`` atomically as pretty-printed JSON."""
    atomic_write_text(path, json.dumps(entries, indent=2) + "\n")


def _ref_next_id(entries: list[dict]) -> str:
    """Return the next ``R-NNNN`` id, monotonic over the ids already present."""
    highest = 0
    for entry in entries:
        match = _REF_ID_RE.match(str(entry.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"R-{highest + 1:04d}"


def _ref_is_inactive(entry: dict) -> bool:
    """True when an entry is deprecated or superseded (prune/skip candidate)."""
    return entry.get("status") == "deprecated" or bool(entry.get("superseded_by"))


def _ref_prune(entries: list[dict], buffer_size: int) -> list[dict]:
    """Drop overflow beyond ``buffer_size``: oldest inactive first, then oldest.

    ``buffer_size`` is clamped to at least 1 — a zero/negative host config must
    never silently discard every lesson (or crash), and the entry just added is
    never its own prune victim.
    """
    buffer_size = max(1, int(buffer_size))
    pruned = list(entries)
    while len(pruned) > buffer_size:
        victim = next((e for e in pruned[:-1] if _ref_is_inactive(e)), pruned[0])
        pruned.remove(victim)
    return pruned


def add_reflection(
    path: Path,
    *,
    lesson: str,
    evidence: str,
    tags: list[str],
    status: str = "provisional",
    buffer_size: int = 5,
) -> dict:
    """Append a reflection to the buffer at ``path`` and return the new entry.

    Assigns the next monotonic ``R-NNNN`` id, stamps today's ISO date, and
    prunes overflow beyond ``buffer_size`` (oldest superseded/deprecated
    entries first, then oldest overall). ``status`` is ``provisional`` until a
    later session confirms the lesson held up.
    """
    entries = load_reflections(path)
    entry = {
        "id": _ref_next_id(entries),
        "lesson": lesson,
        "evidence": evidence,
        "tags": list(tags),
        "status": status,
        "date": date.today().isoformat(),
    }
    entries.append(entry)
    _ref_save(path, _ref_prune(entries, buffer_size))
    return entry


def active_lessons(entries: list[dict], buffer_size: int) -> list[dict]:
    """Return live lessons newest-first, capped at ``buffer_size``.

    Skips entries whose status is ``deprecated`` and entries carrying a
    ``superseded_by`` stamp.
    """
    live = [entry for entry in entries if not _ref_is_inactive(entry)]
    live.reverse()
    return live[:buffer_size]


def supersede_reflection(path: Path, old_id: str, new_id: str) -> bool:
    """Stamp ``superseded_by`` on ``old_id``'s entry; False when it is absent."""
    entries = load_reflections(path)
    for entry in entries:
        if entry.get("id") == old_id:
            entry["superseded_by"] = new_id
            _ref_save(path, entries)
            return True
    return False


def lessons_block(entries: list[dict]) -> str:
    """Render the "Learned lessons" orientation block ("" when nothing active).

    Provisional entries are flagged ``(provisional)`` so the reading agent
    weighs them as candidates, not settled rules.
    """
    live = active_lessons(entries, len(entries))
    if not live:
        return ""
    lines = ["## Learned lessons", ""]
    for entry in live:
        flag = " (provisional)" if entry.get("status") == "provisional" else ""
        lines.append(f"- [{entry.get('id', '?')}] {entry.get('lesson', '')}{flag}")
    return "\n".join(lines) + "\n"


def _ref_newest_logs(sessions_dir: Path, last_n: int) -> list[Path]:
    """Return the newest ``last_n`` logs by mtime (name-tiebroken), oldest first."""
    if not sessions_dir.is_dir() or last_n < 1:
        return []
    logs = [p for p in sessions_dir.glob("*.md") if p.name != "README.md"]
    logs.sort(key=lambda p: (p.stat().st_mtime, p.name))
    return logs[-last_n:]


def _ref_clean_line(line: str) -> str:
    """Strip bullets, blockquote marks, and the emoji markers from a mined line."""
    text = line.strip().lstrip("-*> ").strip()
    for mark in (_REF_IDEA_MARK, _REF_FLAG_MARK):
        text = text.replace(mark, "")
    return text.strip().lstrip(":").strip()


def _ref_marker_tags(line: str) -> list[str]:
    """Return the candidate tags for a line's emoji markers (may be empty)."""
    tags: list[str] = []
    if _REF_IDEA_MARK in line:
        tags.append("idea")
    if _REF_FLAG_MARK in line:
        tags.append("flag")
    return tags


def _ref_path_tokens(line: str) -> list[str]:
    """Return file-path tokens: contain ``/`` and end in a known code/doc suffix."""
    tokens: list[str] = []
    for raw in line.split():
        token = raw.strip(_REF_STRIP_CHARS)
        if "/" in token and token.endswith(_REF_PATH_SUFFIXES):
            tokens.append(token)
    return tokens


def _ref_mine_log(log: Path) -> tuple[list[dict], dict[str, str]]:
    """Mine one log: (marker-line candidates, first evidence per cited path)."""
    candidates: list[dict] = []
    paths_seen: dict[str, str] = {}
    try:
        lines = log.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return candidates, paths_seen
    for lineno, line in enumerate(lines, 1):
        if "[DEPRECATED]" in line:
            continue
        evidence = f"{log.name}:L{lineno}"
        tags = _ref_marker_tags(line)
        if tags:
            candidates.append(
                {"lesson": _ref_clean_line(line), "evidence": evidence, "tags": tags},
            )
        for token in _ref_path_tokens(line):
            paths_seen.setdefault(token, evidence)
    return candidates, paths_seen


def mine_reflections(sessions_dir: Path, *, last_n: int = 5) -> list[dict]:
    """Mine candidate lessons from the newest ``last_n`` session logs.

    Deterministic and read-only — never writes state; the caller decides what
    to promote into the buffer. Three extraction passes:

      1. 💡 idea lines → ``{"lesson", "evidence", "tags": ["idea"]}``.
      2. ⚑ flag lines → the same shape, tagged ``flag``.
      3. Any file path cited in >= 2 different logs → one
         ``Recurring attention on <path>`` candidate.

    Lines containing ``[DEPRECATED]`` are skipped entirely.
    """
    candidates: list[dict] = []
    sightings: dict[str, dict[str, str]] = {}
    for log in _ref_newest_logs(sessions_dir, last_n):
        mined, paths_seen = _ref_mine_log(log)
        candidates.extend(mined)
        for token, evidence in paths_seen.items():
            sightings.setdefault(token, {})[log.name] = evidence
    for token in sorted(sightings):
        seen = sightings[token]
        if len(seen) < 2:
            continue
        evidence = ", ".join(seen[name] for name in sorted(seen))
        candidates.append(
            {
                "lesson": f"Recurring attention on {token}",
                "evidence": evidence,
                "tags": ["recurring-path"],
            },
        )
    return candidates

# --- engine/loop/episodes.py ---
"""Episodic index — a tiny searchable memory over session logs (plan lane B2).

Each session log becomes one compact ``{"slug", "date", "tags", "summary"}``
record in ``<state_dir>/episodic_index.json``, so an agent can grep *which*
past session touched a topic without reading every log top-to-bottom. Tags
come from the log's first heading (minus stopwords) plus the workflow's marker
emojis (💡 idea, ⚑ flag, ⟲ review, 📊 telemetry). The index is a derived
artifact: rebuildable from the logs at any time, written atomically, and
fail-open on absence/corruption.
"""




EPISODIC_INDEX_FILENAME = "episodic_index.json"

_EPI_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
_EPI_WORD_RE = re.compile(r"[a-z0-9][\w-]*")
_EPI_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "at",
        "by",
        "for",
        "from",
        "in",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    },
)
_EPI_MARKERS = (
    "\N{ELECTRIC LIGHT BULB}",  # 💡 session idea
    "\N{BLACK FLAG}",  # ⚑ self-initiated / friction flag
    "\N{ANTICLOCKWISE GAPPED CIRCLE ARROW}",  # ⟲ previous-session review
    "\N{BAR CHART}",  # 📊 telemetry / KPI footer
)
_EPI_SUMMARY_LIMIT = 140


def _epi_load(index_path: Path) -> list[dict]:
    """Return the index entries at ``index_path`` — ``[]`` on absent/corrupt."""
    try:
        raw = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def _epi_save(index_path: Path, entries: list[dict]) -> None:
    """Write ``entries`` to ``index_path`` atomically as pretty-printed JSON."""
    atomic_write_text(index_path, json.dumps(entries, indent=2) + "\n")


def _epi_tags(text: str) -> list[str]:
    """Tags: first ``# `` heading words minus stopwords, plus marker emojis."""
    tags: list[str] = []
    for line in text.splitlines():
        if line.startswith("# "):
            words = _EPI_WORD_RE.findall(line[2:].lower())
            tags.extend(word for word in words if word not in _EPI_STOPWORDS)
            break
    tags.extend(mark for mark in _EPI_MARKERS if mark in text)
    return list(dict.fromkeys(tags))


def _epi_summary(text: str) -> str:
    """Return the first non-blank non-heading line, truncated to 140 chars."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:_EPI_SUMMARY_LIMIT]
    return ""


def index_session(log_path: Path) -> dict:
    """Summarise one session log into ``{"slug", "date", "tags", "summary"}``.

    ``slug`` and ``date`` parse from the ``YYYY-MM-DD-<slug>.md`` filename
    convention; a non-conforming name degrades gracefully to the whole stem as
    the slug with an empty date. An unreadable file yields empty tags/summary.
    """
    match = _EPI_NAME_RE.match(log_path.stem)
    if match:
        session_date, slug = match.group(1), match.group(2)
    else:
        session_date, slug = "", log_path.stem
    try:
        text = log_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    return {
        "slug": slug,
        "date": session_date,
        "tags": _epi_tags(text),
        "summary": _epi_summary(text),
    }


def rebuild_episodic_index(sessions_dir: Path, index_path: Path) -> list[dict]:
    """Rebuild the whole index from ``sessions_dir`` and write it atomically.

    Scans ``*.md`` excluding ``README.md``, sorted by filename (the date-first
    naming convention makes that chronological). Returns the entries written;
    an absent sessions dir yields an empty index.
    """
    logs: list[Path] = []
    if sessions_dir.is_dir():
        logs = sorted(p for p in sessions_dir.glob("*.md") if p.name != "README.md")
    entries = [index_session(p) for p in logs]
    _epi_save(index_path, entries)
    return entries


def append_episode(index_path: Path, entry: dict) -> None:
    """Add ``entry`` to the index, replacing an existing (slug, date) match.

    Keyed on slug *and* date: re-indexing the same log updates in place, while
    a same-slug session from a different day appends instead of silently
    deleting the earlier episode.
    """
    entries = _epi_load(index_path)
    key = (entry.get("slug"), entry.get("date"))
    for i, existing in enumerate(entries):
        if (existing.get("slug"), existing.get("date")) == key:
            entries[i] = entry
            break
    else:
        entries.append(entry)
    _epi_save(index_path, entries)


def search_episodes(index_path: Path, tag: str) -> list[dict]:
    """Return every indexed episode carrying ``tag`` in its tag list."""
    return [entry for entry in _epi_load(index_path) if tag in entry.get("tags", [])]

# --- engine/loop/triggers.py ---
"""Trigger scan for the self-improving loop (plan section 5, Lane B1).

The loop's sensory layer: ``check_triggers`` inspects the project tree plus the
state document and reports which of the five trigger kinds fired —

- ``critical_unfilled`` — a graduation-critical slot is still not ``filled``
  after the cadence's grace window (one trigger per slot).
- ``blocking_open``     — escalated blocking questions sit on
  ``state["open_questions"]``.
- ``drift``             — the doc-hygiene checks (badge / link / reachable)
  report findings.
- ``staleness``         — the newest session log is older than
  ``cadence["staleness_days"]`` days, or reconciliation is overdue by session
  count.
- ``new_area``          — a direct subdirectory of the docs root holds only
  unreachable *and* unbadged markdown (nobody owns it yet).

``mandatory_questions`` then maps fired triggers back onto question-bank
entries, and ``trigger_block`` renders the orientation text block. The mode
policy (``engine.lib.modes.triggers_mandate``) decides whether the block is a
mandate or an advisory — this module only renders whichever the caller picked.
Pure stdlib; returns data / text, never prints.
"""




_TRG_PRIORITY_ORDER = {"blocking": 0, "high": 1, "normal": 2}
_TRG_SECONDS_PER_DAY = 86_400.0


class Trigger(NamedTuple):
    """One fired trigger: kind, severity, human message, related question ids."""

    kind: str
    severity: str
    message: str
    question_ids: tuple[str, ...]


def _trg_critical_unfilled(
    state: dict[str, Any],
    cadence: dict[str, int],
    bank: list[dict],
) -> list[Trigger]:
    """One trigger per critical slot still unfilled past the grace window."""
    grace = int(cadence.get("critical_slot_grace_sessions", 3))
    if int(state.get("session_count", 0)) <= grace:
        return []
    slots = state.get("slots", {})
    critical = dict.fromkeys(q["slot"] for q in bank if q.get("critical"))
    triggers: list[Trigger] = []
    for slot in critical:
        if slots.get(slot) == "filled":
            continue
        ids = tuple(q["id"] for q in bank if q["slot"] == slot)
        message = (
            f"critical slot '{slot}' is not filled after the "
            f"{grace}-session grace window"
        )
        triggers.append(Trigger("critical_unfilled", "blocking", message, ids))
    return triggers


def _trg_blocking_open(state: dict[str, Any]) -> list[Trigger]:
    """One trigger when escalated blocking questions are open."""
    open_questions = [str(q) for q in state.get("open_questions", [])]
    if not open_questions:
        return []
    listed = ", ".join(open_questions)
    message = f"{len(open_questions)} blocking question(s) open: {listed}"
    return [Trigger("blocking_open", "blocking", message, tuple(open_questions))]


def _trg_drift(docs_root: Path, config: Config) -> list[Trigger]:
    """One trigger when the doc-hygiene checks report any finding."""
    findings = run_doc_checks(docs_root, config.badge_tokens, config.readpath_docs)
    if not findings:
        return []
    kinds = ", ".join(sorted({f.kind for f in findings}))
    message = f"doc hygiene reports {len(findings)} finding(s) ({kinds})"
    return [Trigger("drift", "high", message, ())]


def _trg_staleness(
    state: dict[str, Any],
    cadence: dict[str, int],
    sessions_dir: Path,
) -> list[Trigger]:
    """One trigger when memory looks stale (old log or overdue reconciliation)."""
    reasons: list[str] = []
    stale_days = int(cadence.get("staleness_days", 14))
    newest = latest_session_log(sessions_dir)
    if newest is not None:
        age_days = (time.time() - newest.stat().st_mtime) / _TRG_SECONDS_PER_DAY
        if age_days > stale_days:
            reasons.append(
                f"newest session log is {int(age_days)} days old "
                f"(threshold {stale_days})",
            )
    overdue = int(cadence.get("reconciliation_sessions", 20))
    since = int(state.get("session_count", 0)) - int(
        state.get("last_compaction_session", 0),
    )
    if since >= overdue:
        reasons.append(
            f"{since} sessions since the last compaction (cadence {overdue})",
        )
    if not reasons:
        return []
    return [Trigger("staleness", "normal", "; ".join(reasons), ())]


def _trg_new_area(docs_root: Path, config: Config) -> list[Trigger]:
    """One trigger per docs subdirectory whose docs are all orphaned + unbadged."""
    if not docs_root.is_dir():
        return []
    orphans = {f.path for f in check_reachable(docs_root, config.readpath_docs)}
    triggers: list[Trigger] = []
    for sub in sorted(p for p in docs_root.iterdir() if p.is_dir()):
        files = sorted(sub.rglob("*.md"))
        if not files:
            continue
        all_unowned = all(
            f.relative_to(docs_root).as_posix() in orphans and badge_token(f) is None
            for f in files
        )
        if all_unowned:
            message = (
                f"new docs area '{sub.name}/' ({len(files)} file(s)) is "
                "entirely unreachable and unbadged — no ownership entry yet"
            )
            triggers.append(Trigger("new_area", "high", message, ()))
    return triggers


def check_triggers(
    root: Path,
    config: Config,
    state: dict[str, Any],
    bank: list[dict] | None = None,
) -> list[Trigger]:
    """Scan the project tree + state and return every fired trigger.

    ``root`` is the project root; the docs root and sessions dir are resolved
    from ``config``. Returns triggers grouped by kind in the fixed order
    critical_unfilled, blocking_open, drift, staleness, new_area.
    """
    bank = QUESTIONS if bank is None else bank
    cadence = dict(config.cadence or {})
    docs_root = root / config.docs_root
    sessions_dir = root / config.sessions_dir
    return (
        _trg_critical_unfilled(state, cadence, bank)
        + _trg_blocking_open(state)
        + _trg_drift(docs_root, config)
        + _trg_staleness(state, cadence, sessions_dir)
        + _trg_new_area(docs_root, config)
    )


def mandatory_questions(
    triggers: list[Trigger],
    bank: list[dict] | None = None,
) -> list[dict]:
    """Return the bank questions the fired triggers pull into this session.

    Selects entries whose ``trigger`` field matches a fired kind, plus the
    entries a ``critical_unfilled`` trigger names via ``question_ids``.
    De-duplicated by id; priority-ordered (blocking, high, normal — stable).
    """
    bank = QUESTIONS if bank is None else bank
    fired_kinds = {t.kind for t in triggers}
    named_ids = {
        qid for t in triggers if t.kind == "critical_unfilled" for qid in t.question_ids
    }
    selected: list[dict] = []
    seen: set[str] = set()
    for question in bank:
        wanted = question.get("trigger") in fired_kinds or question["id"] in named_ids
        if wanted and question["id"] not in seen:
            seen.add(question["id"])
            selected.append(question)
    return sorted(
        selected,
        key=lambda q: _TRG_PRIORITY_ORDER.get(q.get("priority", "normal"), 2),
    )


def trigger_block(
    triggers: list[Trigger],
    questions: list[dict],
    *,
    mandate: bool,
) -> str:
    """Render the orientation trigger block ('' when nothing fired).

    ``mandate=True`` (guided/active modes) opens with a MANDATORY
    question-session header; otherwise the block is an advisory.
    """
    if not triggers:
        return ""
    if mandate:
        header = "## ⚠️ MANDATORY question session — triggers fired"
    else:
        header = "## Trigger advisory (non-mandatory)"
    lines = [header, ""]
    lines += [f"- [{t.severity}] {t.kind}: {t.message}" for t in triggers]
    if questions:
        lines += ["", "Questions to ask this session:"]
        lines += [
            f"- {q['id']} ({q.get('priority', 'normal')}): {q['prompt']}"
            for q in questions
        ]
    return "\n".join(lines) + "\n"

# --- engine/loop/maintenance.py ---
"""Maintenance actuators for the self-improving loop (plan section 5, Lane B3).

The loop's housekeeping arm: the compaction cadence and its pre-compaction
"State Delta" snapshot, the escalated open-question list (the blocking-question
brake graduation waits on), the promotion-rights downgrade, and the composed
``maintain`` human report. Pure stdlib; every file write goes through
``atomic_write_text``; functions return data / text, never print — the CLI
owns all output.

The sibling loop modules (``reflections``, ``kpis``, ``review_seam``) are
imported lazily with fail-open fallbacks, so this module keeps working when a
build ships without them (the single-file bootstrap concatenation case).
"""




_MNT_VALUE_WIDTH = 80


def compaction_due(state: dict[str, Any], cadence: dict[str, int]) -> bool:
    """True when the compaction cadence window has elapsed.

    Fires when ``session_count - last_compaction_session`` reaches
    ``cadence["compaction_sessions"]`` (default 20).

    Deliberate reduction of the plan's "~700K tokens OR 20 sessions": the kit
    has no token telemetry (stdlib-only, no provider hooks), so only the
    session-count half ships; hosts with token accounting can trigger
    ``run_compaction`` directly when their own meter trips.
    """
    every = int(cadence.get("compaction_sessions", 20))
    since = int(state.get("session_count", 0)) - int(
        state.get("last_compaction_session", 0),
    )
    return since >= every


def _mnt_cell(value: Any) -> str:
    """Collapse ``value`` to one table-safe line truncated to 80 chars."""
    text = " ".join(str(value).split()).replace("|", "/")
    return text[:_MNT_VALUE_WIDTH]


def _mnt_lesson_lines(reflections: list[dict]) -> list[str]:
    """Render the active-lesson lines from the reflection entries."""
    live = active_lessons(reflections, len(reflections))
    return [f"- [{e.get('id', '?')}] {e.get('lesson', '')}" for e in live]


def _mnt_slot_lines(state: dict[str, Any]) -> list[str]:
    """Render the slot table (name-sorted; values truncated to 80 chars)."""
    slots = state.get("slots", {})
    if not slots:
        return []
    values = state.get("slot_values", {})
    lines = ["| slot | status | value |", "| --- | --- | --- |"]
    for slot in sorted(slots):
        entry = values.get(slot, {})
        value = entry.get("value", "") if isinstance(entry, dict) else entry
        lines.append(f"| {slot} | {slots[slot]} | {_mnt_cell(value)} |")
    return lines


def state_delta(state: dict[str, Any], reflections: list[dict]) -> str:
    """Render the pre-compaction State Delta markdown — dense, deterministic.

    The counters line always appears; the slot table, open-questions list, and
    active-lessons list appear only when non-empty. No timestamps: two calls
    over the same inputs return identical text.
    """
    lines = [
        f"# State Delta — session {int(state.get('session_count', 0))}",
        "",
        f"- mode: {state.get('mode', '?')} · stage: {state.get('stage', '?')} · "
        f"sessions: {int(state.get('session_count', 0))} · "
        f"quiet: {int(state.get('quiet_sessions', 0))}",
    ]
    slot_lines = _mnt_slot_lines(state)
    if slot_lines:
        lines += ["", "## Slots", "", *slot_lines]
    open_questions = [str(q) for q in state.get("open_questions", [])]
    if open_questions:
        lines += ["", "## Open questions", ""]
        lines += [f"- {qid}" for qid in open_questions]
    lesson_lines = _mnt_lesson_lines(reflections)
    if lesson_lines:
        lines += ["", "## Active lessons", "", *lesson_lines]
    return "\n".join(lines) + "\n"


def _mnt_load_reflections(state_dir: Path) -> list[dict]:
    """Load the reflection buffer for the delta (``[]`` when unavailable)."""
    return load_reflections(state_dir / REFLECTIONS_FILENAME)


def run_compaction(root: Path, config: Config, backend: Any) -> Path:
    """Write the State Delta snapshot and reset the compaction counter.

    Writes ``<state_dir>/state-delta-<session_count>.md`` atomically, then
    stamps ``last_compaction_session`` so ``compaction_due`` stays quiet until
    the next cadence window. Returns the written path.
    """
    state_dir = root / config.state_dir
    session = int(backend.get("session_count", 0))
    delta = state_delta(backend.data, _mnt_load_reflections(state_dir))
    path = state_dir / f"state-delta-{session}.md"
    atomic_write_text(path, delta)
    backend.set("last_compaction_session", session)
    return path


def escalate_blocking(backend: Any, question_id: str) -> bool:
    """Append ``question_id`` to the escalated open-questions list once.

    Idempotent: True when it appended, False when the id was already open.
    Open questions hold graduation until answered (the blocking brake).
    """
    open_questions = list(backend.get("open_questions", []))
    if question_id in open_questions:
        return False
    open_questions.append(question_id)
    backend.set("open_questions", open_questions)
    return True


def resolve_open_question(backend: Any, question_id: str) -> bool:
    """Drop ``question_id`` from the open-questions list; False when absent."""
    open_questions = list(backend.get("open_questions", []))
    if question_id not in open_questions:
        return False
    open_questions.remove(question_id)
    backend.set("open_questions", open_questions)
    return True


def downgrade_promotion(backend: Any, *, reason: str) -> None:
    """Cap autonomy: ``promotion_rights`` → ``"propose"``, logged with why.

    Appends a ``promotion_downgrade`` event to ``review_log`` so the loss of
    apply-rights always carries its provenance.
    """
    log = list(backend.get("review_log", []))
    log.append(
        {
            "event": "promotion_downgrade",
            "reason": reason,
            "date": date.today().isoformat(),
        },
    )
    with backend.transaction():
        backend.set("promotion_rights", "propose")
        backend.set("review_log", log)


def _mnt_item_line(item: Any) -> str:
    """Render one report line for a trigger or a checker finding.

    Triggers (kind/severity/message) render like the orientation block;
    findings (path/kind/message) render path-first; anything else renders as
    its ``str``.
    """
    kind = getattr(item, "kind", None)
    message = getattr(item, "message", None)
    if kind is None or message is None:
        return f"- {item}"
    severity = getattr(item, "severity", None)
    if severity is not None:
        return f"- [{severity}] {kind}: {message}"
    path = getattr(item, "path", None)
    prefix = f"{path}: " if path else ""
    return f"- {prefix}[{kind}] {message}"


def _mnt_review_dir() -> str:
    """Return the review-payload directory name.

    Mirrors ``review_seam.REVIEW_DIR`` as a literal: ``review_seam`` imports
    this module at top level, so importing it back would be circular — the
    seam's own test pins the two values equal.
    """
    return "review"


def _mnt_advisories(root: Path, config: Config, backend: Any) -> list[str]:
    """Return the maintenance advisories: compaction due, payloads waiting."""
    advisories: list[str] = []
    if compaction_due(backend.data, dict(config.cadence or {})):
        advisories.append("compaction due — write the State Delta snapshot")
    review_dir = root / config.state_dir / _mnt_review_dir()
    if review_dir.is_dir():
        pending = sorted(review_dir.glob("payload-*.json"))
        if pending:
            advisories.append(
                f"{len(pending)} review payload(s) awaiting a reviewer",
            )
    return advisories


def _mnt_footer(kpis: dict[str, Any]) -> str:
    """Render the KPI footer line for the report."""
    return kpi_footer(kpis)


def maintenance_report(
    root: Path,
    config: Config,
    backend: Any,
    *,
    triggers: list[Any],
    economy_findings: list[Any],
    ledger_findings: list[Any],
    kpis: dict[str, Any],
) -> str:
    """Compose the ``maintain`` human report from the loop's sensor outputs.

    Every section is skipped when its input is empty; a maintenance-advisories
    section surfaces compaction cadence and accumulated review payloads (the
    no-reviewer graceful fallback); the report ends with the KPI footer when
    ``kpis`` is non-empty.
    """
    lines = [
        f"# Maintenance report — session {int(backend.get('session_count', 0))}",
    ]
    sections: tuple[tuple[str, list[Any]], ...] = (
        ("Triggers", triggers),
        ("Economy findings", economy_findings),
        ("Ledger findings", ledger_findings),
    )
    for title, items in sections:
        if not items:
            continue
        lines += ["", f"## {title}", ""]
        lines += [_mnt_item_line(item) for item in items]
    advisories = _mnt_advisories(root, config, backend)
    if advisories:
        lines += ["", "## Maintenance", ""]
        lines += [f"- {advisory}" for advisory in advisories]
    if kpis:
        lines += ["", _mnt_footer(kpis)]
    return "\n".join(lines) + "\n"

# --- engine/loop/review_seam.py ---
"""The external-review seam — provisioned, not wired (plan section 6, Lane B3).

A second model can audit the interview's provisional self-answers, but the kit
never talks to one (no subprocess, no network): it emits an **anti-anchor**
payload — the proposition and its evidence, NO confidence score, NO author
commentary — and the host records the verdict through one entry point. With no
reviewer configured, payloads simply accumulate for the owner; nothing blocks.
Pure stdlib; writes via ``atomic_write_text``.
"""




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

# --- engine/economy/engine.py ---
"""The context-economy engine (plan §5.B, Lane B4).

The retention/taxonomy layer of the self-improving loop: docs are classified
into host-declared classes (badge- and/or glob-matched), gauges watch word and
count budgets, an inbound-reference scan protects cited files, and the actuator
applies the TRIPLE FILTER (harvested AND past window AND zero inbound refs)
before any deletion — writing one tombstone line per pruned file into a
per-band shard. Retention windows are measured in **days** from file mtime:
the kit supports day windows only; "bands" are a host cadence unit layered on
top of it, never a kit unit. ``economy["maturity"]`` gates the actuator —
``"shadow"`` never applies. Pure stdlib; returns data / text, never prints.
"""




# Minimal inline copy of check_docs._badge_token's regex (private there); drop
# once the helper is promoted to a public name in engine/checks/check_docs.py.
_ECO_BADGE_RE = re.compile(r"\*\*Status:\*\*\s*`([a-z-]+)`")

_ECO_SECONDS_PER_DAY = 86400.0


class EconomyFinding(NamedTuple):
    """One economy finding: ``path`` is relative to the project root."""

    path: str
    kind: str
    message: str


DEFAULT_CLASSES: list[dict] = [
    {
        "name": "sessions",
        "globs": ["<sessions_dir>/*.md"],
        "mode": "delete_tomb",
        "window_days": 14,
        "tombstone_dir": "<sessions_dir>/pruned",
    },
    {
        "name": "plans",
        "badges": ["plan"],
        "mode": "archive",
        "window_days": 60,
    },
    {
        "name": "living",
        "badges": ["living-ledger", "reference", "binding"],
        "mode": "keep",
    },
]
"""Minimal generic class profile — a STARTING POINT, not shipped policy.

Used only when ``config.economy["classes"]`` is empty. Every adopting host is
expected to replace it with its own measured taxonomy (the kit ships the
search, not our constants). Placeholder tokens (``<sessions_dir>`` etc.) are
expanded from the host config at evaluation time.
"""


def _eco_expand(pattern: str, config: Config) -> str:
    """Expand ``<sessions_dir>`` / ``<docs_root>`` / ``<state_dir>`` tokens."""
    return (
        pattern.replace("<sessions_dir>", config.sessions_dir)
        .replace("<docs_root>", config.docs_root)
        .replace("<state_dir>", config.state_dir)
    )


def _eco_classes(config: Config) -> list[dict]:
    """Return the active class table (host classes or the generic default)."""
    return list(config.economy.get("classes") or DEFAULT_CLASSES)


def _eco_md_files(docs_root: Path) -> list[Path]:
    """Return every ``*.md`` under ``docs_root`` (sorted, empty if absent)."""
    if not docs_root.exists():
        return []
    return sorted(docs_root.rglob("*.md"))


def _eco_read_text(path: Path) -> str | None:
    """Read ``path`` as UTF-8 text; None when unreadable or not text."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _eco_badge_token(path: Path) -> str | None:
    """Return the doc's Status-badge token from its first 12 lines, or None."""
    text = _eco_read_text(path)
    if text is None:
        return None
    match = _ECO_BADGE_RE.search("\n".join(text.splitlines()[:12]))
    return match.group(1) if match else None


def _eco_wc(path: Path) -> int:
    """Return the whitespace word count of one text file (0 if unreadable)."""
    text = _eco_read_text(path)
    return len(text.split()) if text else 0


def _eco_rel(path: Path, root: Path) -> str:
    """Return ``path`` relative to ``root`` as posix (absolute-safe fallback)."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def classify_docs(root: Path, config: Config) -> dict[str, list[Path]]:
    """Bucket project docs into economy classes plus the ``_unbadged`` bucket.

    Classes come from ``config.economy["classes"]`` (``DEFAULT_CLASSES`` when
    empty); each class matches by Status-badge token (``badges``, scanned from
    a doc's first 12 lines with the check_docs regex convention) and/or by
    root-relative ``globs``. The first matching class wins. Docs under the
    docs root that match no class AND carry no badge land in ``"_unbadged"``.
    """
    docs = _eco_md_files(root / config.docs_root)
    buckets: dict[str, list[Path]] = {}
    assigned: set[Path] = set()
    for cls in _eco_classes(config):
        matched: set[Path] = set()
        for pattern in cls.get("globs", []):
            expanded = _eco_expand(str(pattern), config)
            matched.update(p for p in root.glob(expanded) if p.is_file())
        badges = set(cls.get("badges", []))
        if badges:
            matched.update(f for f in docs if _eco_badge_token(f) in badges)
        fresh = sorted(p for p in matched if p.resolve() not in assigned)
        assigned.update(p.resolve() for p in fresh)
        buckets[cls["name"]] = fresh
    buckets["_unbadged"] = [
        f for f in docs if f.resolve() not in assigned and _eco_badge_token(f) is None
    ]
    return buckets


def _eco_word_cap_value(root: Path, config: Config, gauge: dict) -> int:
    """Return a word_cap gauge's value: one file's words, or a dir's summed."""
    target = root / _eco_expand(str(gauge.get("path", "")), config)
    if target.is_dir():
        return sum(_eco_wc(f) for f in sorted(target.rglob("*.md")))
    if target.is_file():
        return _eco_wc(target)
    return 0


def _eco_count_cap_value(root: Path, config: Config, gauge: dict) -> int:
    """Return a count_cap gauge's value: file count under its glob."""
    pattern = _eco_expand(str(gauge.get("glob", "")), config)
    if not pattern:
        return 0
    return sum(1 for p in root.glob(pattern) if p.is_file())


def _eco_route_budget(root: Path, config: Config) -> tuple[int, int]:
    """Return (value, cap) for the boot-route word budget.

    Value sums word counts over the boot set resolved by the orientation
    checker's own ``_ob_boot_paths`` (ONE resolver for both consumers — the
    gauge once resolved everything under docs_root and undercounted
    root-level boot docs to 0); cap is ``orientation["budget_words"]``.
    """
    value = sum(_eco_wc(path) for path in _ob_boot_paths(root, config))
    cap = int(config.orientation.get("budget_words", 7000))
    return value, cap


def economy_gauges(root: Path, config: Config) -> list[dict]:
    """Evaluate the configured gauges (word_cap / count_cap / route_budget).

    When ``config.economy["gauges"]`` is empty, falls back to one
    ``route_budget`` gauge derived from ``config.orientation``. Unknown kinds
    are skipped. Each result is ``{"name", "kind", "value", "cap", "over"}``.
    """
    gauges = list(config.economy.get("gauges") or [])
    if not gauges:
        gauges = [{"name": "route_budget", "kind": "route_budget"}]
    results: list[dict] = []
    for gauge in gauges:
        kind = str(gauge.get("kind", ""))
        cap = int(gauge.get("cap") or 0)
        if kind == "word_cap":
            value = _eco_word_cap_value(root, config, gauge)
        elif kind == "count_cap":
            value = _eco_count_cap_value(root, config, gauge)
        elif kind == "route_budget":
            value, default_cap = _eco_route_budget(root, config)
            cap = int(gauge.get("cap") or default_cap)
        else:
            continue
        results.append(
            {
                "name": str(gauge.get("name", kind)),
                "kind": kind,
                "value": value,
                "cap": cap,
                "over": value > cap,
            },
        )
    return results


def _eco_scan_files(root: Path, config: Config) -> list[Path]:
    """Return the reference-scan set: docs-root ``*.md`` + reference roots."""
    files: set[Path] = set(_eco_md_files(root / config.docs_root))
    for pattern in config.economy.get("reference_roots", []):
        expanded = _eco_expand(str(pattern), config)
        for hit in root.glob(expanded):
            if hit.is_file():
                files.add(hit)
            elif hit.is_dir():
                files.update(p for p in hit.rglob("*") if p.is_file())
    return sorted(files)


def inbound_references(
    root: Path,
    config: Config,
    targets: list[Path],
    exclude: dict[str, set[str]] | None = None,
) -> dict[str, list[str]]:
    """Map each target to the files that cite it (plain-text scan, stdlib).

    A scanner file cites a target when it contains (a) an id-pattern token
    (``config.economy["id_patterns"]``) drawn from the target's filename, or
    (b) the target's filename stem. Scans every ``*.md`` under the docs root
    plus every text file under each ``economy["reference_roots"]`` glob; a
    file never counts as citing itself. ``exclude`` maps a target *stem* to
    resolved scanner paths that must not count as citations — the pass record
    whose harvest table licenses a slug's deletion would otherwise hold every
    harvested file forever (the triple filter became unsatisfiable).
    """
    exclude = exclude or {}
    patterns = [re.compile(p) for p in config.economy.get("id_patterns", [])]
    scanners: list[tuple[Path, str]] = []
    for f in _eco_scan_files(root, config):
        text = _eco_read_text(f)
        if text is not None:
            scanners.append((f, text))
    refs: dict[str, list[str]] = {}
    for target in targets:
        ids = {m for pat in patterns for m in pat.findall(target.name)}
        needles = ids | {target.stem}
        excluded = exclude.get(target.stem, set())
        citing = {
            _eco_rel(f, root)
            for f, text in scanners
            if f.resolve() != target.resolve()
            and f.resolve().as_posix() not in excluded
            and any(needle in text for needle in needles)
        }
        refs[_eco_rel(target, root)] = sorted(citing)
    return refs


def _eco_expired(path: Path, window_days: Any) -> tuple[bool, int]:
    """Return (past-window?, age-in-days) for ``path`` (mtime-based)."""
    if window_days is None:
        return False, 0
    age = (time.time() - path.stat().st_mtime) / _ECO_SECONDS_PER_DAY
    return age > float(window_days), int(age)


def _eco_delete_row(
    rel: str,
    cls: dict,
    *,
    expired: bool,
    in_harvest: bool,
    n_refs: int,
) -> dict:
    """Build one delete would-act row carrying the TRIPLE FILTER verdict."""
    blockers: list[str] = []
    if not in_harvest:
        blockers.append("not harvested")
    if n_refs:
        blockers.append(f"inbound refs: {n_refs}")
    if not expired:
        blockers.append("window not reached")
    return {
        "path": rel,
        "action": "delete",
        "reason": f"class '{cls['name']}' ({cls.get('window_days')}d window)",
        "eligible": not blockers,
        "blockers": blockers,
        "class": cls["name"],
    }


def _eco_archive_row(rel: str, cls: dict, *, expired: bool) -> dict:
    """Build one archive would-act row (window is the only gate)."""
    return {
        "path": rel,
        "action": "archive",
        "reason": f"class '{cls['name']}' ({cls.get('window_days')}d window)",
        "eligible": expired,
        "blockers": [] if expired else ["window not reached"],
        "class": cls["name"],
    }


def _eco_class_files(classes: list[dict], buckets: dict[str, list[Path]]) -> list:
    """Return (class, file) pairs over every classified file, class order."""
    return [(cls, f) for cls in classes for f in buckets.get(cls["name"], [])]


def _eco_class_rows(
    root: Path,
    classes: list[dict],
    buckets: dict[str, list[Path]],
    harvested: set[str],
    refs: dict[str, list[str]],
) -> tuple[list[dict], list[EconomyFinding], int]:
    """Return (would-act rows, expired/delete_with_refs findings, debt)."""
    rows: list[dict] = []
    findings: list[EconomyFinding] = []
    debt = 0
    for cls, f in _eco_class_files(classes, buckets):
        expired, age = _eco_expired(f, cls.get("window_days"))
        rel = _eco_rel(f, root)
        if expired:
            debt += 1
            message = (
                f"{age}d old exceeds the {cls.get('window_days')}d "
                f"'{cls['name']}' window"
            )
            findings.append(EconomyFinding(rel, "expired", message))
        mode = cls.get("mode")
        if mode == "delete_tomb":
            n_refs = len(refs.get(rel, []))
            in_harvest = f.stem in harvested
            rows.append(
                _eco_delete_row(
                    rel,
                    cls,
                    expired=expired,
                    in_harvest=in_harvest,
                    n_refs=n_refs,
                ),
            )
            if expired and n_refs:
                message = f"expired but still cited by {n_refs} file(s)"
                findings.append(EconomyFinding(rel, "delete_with_refs", message))
        elif mode == "archive":
            rows.append(_eco_archive_row(rel, cls, expired=expired))
    return rows, findings, debt


def _eco_base_findings(
    root: Path,
    buckets: dict[str, list[Path]],
    gauges: list[dict],
) -> list[EconomyFinding]:
    """Return the unbadged + over_cap findings."""
    findings = [
        EconomyFinding(
            _eco_rel(f, root),
            "unbadged",
            "no Status badge and no economy class",
        )
        for f in buckets.get("_unbadged", [])
    ]
    findings += [
        EconomyFinding(
            g["name"],
            "over_cap",
            f"gauge '{g['name']}' at {g['value']} words/files vs cap {g['cap']}",
        )
        for g in gauges
        if g["over"]
    ]
    return findings


def economy_check(
    root: Path,
    config: Config,
    *,
    harvested: set[str] | None = None,
    harvest_exclude: dict[str, set[str]] | None = None,
) -> dict:
    """Run the full economy pass: census, gauges, findings, debt, would-act.

    Findings: ``unbadged`` (doc with no badge and no class), ``over_cap`` (a
    gauge over its cap), ``expired`` (file past its class window — the kit
    supports **day** windows only; "bands" are a host cadence unit, not a kit
    unit), and ``delete_with_refs`` (an expired delete-class file still
    cited). ``debt`` counts expired files. ``would_act`` delete rows carry the
    TRIPLE FILTER: eligible only when the file's stem (slug) is in
    ``harvested`` AND it is past its window AND it has zero inbound refs;
    blockers are the explicit strings ``"not harvested"`` /
    ``"inbound refs: N"`` / ``"window not reached"``.
    """
    harvested = set(harvested or set())
    classes = _eco_classes(config)
    buckets = classify_docs(root, config)
    census = {
        name: {"files": len(files), "words": sum(_eco_wc(f) for f in files)}
        for name, files in buckets.items()
    }
    gauges = economy_gauges(root, config)
    delete_targets = [
        f
        for cls in classes
        if cls.get("mode") == "delete_tomb"
        for f in buckets.get(cls["name"], [])
    ]
    refs = (
        inbound_references(root, config, delete_targets, harvest_exclude)
        if delete_targets
        else {}
    )
    rows, class_findings, debt = _eco_class_rows(
        root,
        classes,
        buckets,
        harvested,
        refs,
    )
    findings = _eco_base_findings(root, buckets, gauges) + class_findings
    return {
        "census": census,
        "gauges": gauges,
        "findings": findings,
        "debt": debt,
        "would_act": rows,
    }


def tombstone_line(path: Path, summary: str) -> str:
    """Render one ~20-word tombstone: ``slug - date - last path - what-it-was``."""
    short = " ".join(summary.split()[:12])
    return f"- {path.stem} - {date.today().isoformat()} - {path.as_posix()} - {short}"


def _eco_doc_summary(path: Path) -> str:
    """Return a short what-it-was summary: first heading or non-blank line."""
    text = _eco_read_text(path) or ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return lines[0] if lines else "(empty file)"


def _eco_tombstone_shard(
    root: Path,
    config: Config,
    cls: dict,
    rel_path: Path,
) -> Path:
    """Return the per-band tombstone shard path for one deleted file's class."""
    tomb = cls.get("tombstone_dir")
    if tomb:
        tomb_dir = root / _eco_expand(str(tomb), config)
    else:
        tomb_dir = root / rel_path.parent / "pruned"
    return tomb_dir / f"band-{date.today().strftime('%Y%m')}.md"


def _eco_append_tombstone(shard: Path, line: str) -> None:
    """Append one tombstone line to the shard (create with banner if absent).

    Read-modify-write through ``atomic_write_text`` so a crash mid-append can
    never leave a truncated shard.
    """
    if shard.exists():
        text = shard.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
    else:
        today = date.today()
        text = (
            f"# Tombstones — band {today.strftime('%Y%m')}\n\n"
            "> **Status:** `archive`\n\n"
            f"> Pruned by the context-economy actuator; created "
            f"{today.isoformat()}. One line per deleted file: "
            "slug - date - last path - what-it-was.\n\n"
        )
    atomic_write_text(shard, text + line + "\n")


def _eco_dry_line(row: dict) -> str:
    """Render one would-act row as a dry-run report line."""
    if row.get("eligible"):
        return f"would {row['action']} {row['path']} ({row['reason']})"
    return f"hold {row['path']}: " + "; ".join(row.get("blockers", []))


def _eco_apply_rows(root: Path, config: Config, rows: list[dict]) -> list[str]:
    """Delete eligible delete rows, tombstoning each; archive rows advisory."""
    class_by_name = {c["name"]: c for c in _eco_classes(config)}
    lines: list[str] = []
    for row in rows:
        if not row.get("eligible"):
            lines.append(_eco_dry_line(row))
            continue
        if row.get("action") != "delete":
            lines.append(
                f"advisory: {row['action']} {row['path']} is a host action — "
                "the kit never moves files",
            )
            continue
        path = root / row["path"]
        if not path.is_file():
            lines.append(f"skipped {row['path']}: file no longer exists")
            continue
        cls = class_by_name.get(str(row.get("class", "")), {})
        shard = _eco_tombstone_shard(root, config, cls, Path(row["path"]))
        summary = _eco_doc_summary(path)
        _eco_append_tombstone(shard, tombstone_line(Path(row["path"]), summary))
        path.unlink()
        lines.append(f"deleted {row['path']} -> tombstone {_eco_rel(shard, root)}")
    return lines


def economy_actuate(
    root: Path,
    config: Config,
    report: dict,
    *,
    apply: bool = False,
    acknowledged: bool = False,
) -> list[str]:
    """Apply (or dry-run) the would-act plan from ``economy_check``.

    Dry-run (the default) returns the would-act lines without touching
    anything. ``apply=True`` acts only under the maturity ALLOWLIST:
    ``"normal"`` applies, ``"gated"`` applies only with
    ``acknowledged=True`` (the CE-14 first-prune human-review tier), and
    anything else — including ``"shadow"`` and any typo — refuses outright.
    The lock is acquired atomically (``O_CREAT|O_EXCL``); a pre-existing lock
    refuses (another actuation in flight) and is left in place. It then
    deletes ONLY eligible delete rows (one tombstone line per deletion,
    appended to the class's ``<tombstone_dir>/band-<YYYYMM>.md`` shard),
    removes its own lock in a ``finally`` block, and returns the action
    lines. Archive rows are advisory — the kit never moves files.
    """
    if not apply:
        return [_eco_dry_line(row) for row in report.get("would_act", [])]
    maturity = str(config.economy.get("maturity", "shadow")).strip().lower()
    if maturity not in ("gated", "normal"):
        # Allowlist, not a blocklist: a typo'd maturity ("Shadow", "shadoww")
        # must refuse, never silently apply — deletion is the one place the
        # kit's fail-open posture inverts to fail-closed.
        return [
            f"refused: economy maturity {maturity!r} does not permit apply "
            "(allowed: 'gated' with --reviewed, 'normal') — nothing changed",
        ]
    if maturity == "gated" and not acknowledged:
        return [
            "refused: economy maturity is 'gated' — the first executing prune "
            "needs an explicit human review acknowledgment (pass --reviewed); "
            "promote maturity to 'normal' once the first prune has been "
            "reviewed — nothing changed",
        ]
    lock = root / config.state_dir / "economy.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        # O_CREAT|O_EXCL: atomic acquire — check-then-create raced, and two
        # concurrent actuations could clobber a tombstone shard.
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return [
            f"refused: {config.state_dir}/economy.lock exists — another "
            "actuation may be in flight; nothing changed",
        ]
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"locked {date.today().isoformat()}\n")
        return _eco_apply_rows(root, config, report.get("would_act", []))
    finally:
        lock.unlink(missing_ok=True)


def issue_body(report: dict) -> str:
    """Render the retention-debt routine issue body (markdown).

    Census table + debt count + the top would-act rows (eligible first) — the
    ``--issue-body`` emit the debt-threshold routine posts.
    """
    lines = [
        "## Context-economy retention debt",
        "",
        f"**Debt (expired files): {report.get('debt', 0)}**",
        "",
        "### Census",
        "",
        "| class | files | words |",
        "| --- | --- | --- |",
    ]
    for name, row in sorted(report.get("census", {}).items()):
        lines.append(f"| {name} | {row['files']} | {row['words']} |")
    top = sorted(report.get("would_act", []), key=lambda r: not r.get("eligible"))
    if top:
        lines += ["", "### Top would-act rows", ""]
        lines += [f"- {_eco_dry_line(row)}" for row in top[:10]]
    return "\n".join(lines) + "\n"

# --- engine/economy/harvest.py ---
"""Harvest-table parsing + stub rendering (plan §5.B, Lane B4).

The harvest table is the delete-side safety input of the TRIPLE FILTER: a
pass record commits what it *harvested* from the files it reviewed into a
markdown table under a heading containing "harvest". ``parse_harvest_tables``
recovers the committed slugs (a file is delete-eligible only once its slug
appears here); ``harvest_table_stub`` renders the kit-defined row format,
which round-trips through the parser. Pure stdlib; returns data / text.
"""



_HRV_HEADING_RE = re.compile(r"^#{1,6}\s")
# A table separator row: only pipes, dashes, colons, and whitespace.
_HRV_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|?$")

_HRV_HEADER_ROW = "| slug | status/PR | ⚑ flags | 💡 ideas | 📊 telemetry |"
_HRV_SEPARATOR_ROW = "| --- | --- | --- | --- | --- |"


def _hrv_first_cell(line: str) -> str | None:
    """Return a table row's first-column cell (None when empty)."""
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if not cells:
        return None
    cell = cells[0].strip("`* ")
    return cell or None


def _hrv_slugs_from_text(text: str) -> set[str]:
    """Collect first-column data cells from tables under harvest headings.

    A "harvest heading" is any markdown heading containing ``harvest``
    (case-insensitive). Within such a section, each contiguous run of ``|``
    lines is one table: its first row is the header (skipped), separator rows
    are skipped, every other row contributes its first cell. Surrounding
    prose is tolerated.
    """
    slugs: set[str] = set()
    in_harvest = False
    in_table = False
    table_is_harvest = False
    for line in text.splitlines():
        if _HRV_HEADING_RE.match(line):
            in_harvest = "harvest" in line.lower()
            in_table = False
            continue
        if not in_harvest or not line.lstrip().startswith("|"):
            in_table = False
            continue
        if not in_table:
            # First row of a new table = header. Only a table whose FIRST
            # header cell is "slug" is a harvest table — an inventory or
            # pending table under a "Harvest backlog" heading must never mark
            # files as harvested (that is a deletion license).
            in_table = True
            header = (_hrv_first_cell(line) or "").lower()
            table_is_harvest = header == "slug"
            continue
        if not table_is_harvest or _HRV_SEPARATOR_RE.match(line.strip()):
            continue
        cell = _hrv_first_cell(line)
        if cell:
            slugs.add(cell)
    return slugs


def parse_harvest_tables(pass_records_dir: Path) -> set[str]:
    """Return every harvested slug committed in the pass-record tables.

    Scans ``*.md`` under ``pass_records_dir`` for markdown tables sitting
    under any heading containing ``"harvest"`` (case-insensitive) and
    collects the first-column cell of each data row (header + separator rows
    skipped). Tolerant of surrounding prose; empty set when the directory is
    absent.
    """
    if not pass_records_dir.is_dir():
        return set()
    slugs: set[str] = set()
    for f in sorted(pass_records_dir.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        slugs |= _hrv_slugs_from_text(text)
    return slugs


def harvest_table_stub(entries: list[dict]) -> str:
    """Render the kit-defined harvest table for ``entries``.

    Columns: ``slug | status/PR | ⚑ flags | 💡 ideas | 📊 telemetry``. Each
    entry supplies ``slug`` (required) plus optional ``status`` / ``flags`` /
    ``ideas`` / ``telemetry``. The output includes the ``## Harvest`` heading
    so it round-trips through ``parse_harvest_tables`` unchanged.
    """
    lines = ["## Harvest", "", _HRV_HEADER_ROW, _HRV_SEPARATOR_ROW]
    for entry in entries:
        lines.append(
            "| {slug} | {status} | {flags} | {ideas} | {telemetry} |".format(
                slug=entry.get("slug", ""),
                status=entry.get("status", "—"),
                flags=entry.get("flags", "—"),
                ideas=entry.get("ideas", "—"),
                telemetry=entry.get("telemetry", "—"),
            ),
        )
    return "\n".join(lines) + "\n"


def harvest_sources(pass_records_dir: Path) -> dict[str, set[str]]:
    """Map each harvested slug to the pass-record files that harvested it.

    The harvest table row is the *deletion license* for its slug — the pass
    record naming a slug must not count as an inbound reference to it, or the
    triple filter becomes unsatisfiable (every harvested file is "referenced"
    by its own harvest record).
    """
    sources: dict[str, set[str]] = {}
    if not pass_records_dir.is_dir():
        return sources
    for record in sorted(pass_records_dir.glob("*.md")):
        try:
            text = record.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for slug in _hrv_slugs_from_text(text):
            sources.setdefault(slug, set()).add(record.resolve().as_posix())
    return sources

# --- engine/economy/simulator.py ---
"""Retention-policy simulator for the context economy (plan §5.B, Lane B5).

A generalized port of superbot's ``tools/sim/retention_policy_sim.py``
(sim-driven design applied to the memory system itself). It models a docs
corpus growing over sessions, agents reading it (boot route, grep discovery,
directory scans, back-references into pruned content, stale encounters), and a
candidate retention policy acting on it. The grid search scores each candidate
on expected agent context cost (words per session) under a hard feasibility
constraint (retrieval-miss risk), with a secondary lean-by-construction
objective (smallest tree at horizon among near-best feasible policies) and a
×1/3–×3 sensitivity sweep over the assumption-grade constants.

The kit ships the SEARCH, not any project's constants: every number returned
by ``default_calibration()`` is an UNVERIFIED illustrative placeholder. Run
``calibration_recipe()`` for the measurement plan, replace the numbers with
your repo's, then re-run ``run_search``.

Calibration shape (one plain dict; all costs are words unless noted)::

    {
      # velocity
      "sessions_per_band": 20.0,     # sessions per reconciliation band
      "words_per_token": 0.75,       # for the tokens-saved line in why-it-won
      "initial_age_bands": 12,       # today's stock spread uniformly this deep
      # living-file stocks and boot route
      "live_files": 100.0,           # living/working docs (non-terminal)
      "live_words": 150000.0,
      "boot_fixed_words": 6000.0,    # always-read orientation route
      "journal_words": 4000.0,       # cappable process-memory journal
      "journal_caps": [1000000, 2000],   # grid toggle: uncapped vs capped
      "ledger_base_words": 1500.0,   # living ledger lean head
      "ledger_tail_per_band": 300.0, # narrative accretion per band if untrimmed
      "ledger_tail_bands_initial": 6,
      "ledger_tail_compressed_bands": 2,
      "index_active_line_words": 20.0,
      "index_hist_line_words": 18.0,
      "tombstone_words": 20.0,       # one tombstone index line
      # discovery tax
      "greps_per_session": 8.0,
      "grep_hits_per_1k_files": 50.0,
      "skim_words_per_hit": 12.0,    # path skim in -l output
      "open_frac_per_hit": 0.10,     # fraction opened before badge-bail
      "open_words_per_hit": 200.0,
      "archive_pollution_w_per_mw": 25.0,  # content-grep noise per Mw archived
      "maintenance_w_per_mw": 8.0,   # sweep/link-check burden per Mw in tree
      "ls_scan_words_per_file": 5.0,
      "ls_scans_per_session": 2.0,
      # back-references into terminal content
      "backref_halflife_bands": 3.0, # demand decays with age (exponential)
      "tombstone_hop_words": 300.0,  # tombstone -> history-recovery effort
      "bare_rederive_words": 3000.0, # no pointer: re-derive / re-decide
      "bare_find_fail": 0.5,         # P(recovery fails without a tombstone)
      # staleness (assumption-grade; sweep it)
      "stale_act_base": 0.01,        # P/session of acting on stale content
      "stale_act_cost": 10000.0,
      # feasibility + search knobs
      "miss_per_band_max": 0.005,    # hard constraint on retrieval-miss risk
      "near_best_frac": 0.05,        # secondary-objective envelope
      "grid_scale": 1,               # widening knob: N multiplies each class's
                                     # candidate windows by 1..N (bigger grid)
      "sensitivity_multipliers": [1/3, 3],
      "sensitivity_keys": ["stale_act_base", "classes.sessions.backref_rate"],
      # document classes (per-class mode × window searched per declarations)
      "classes": [
        {
          "name": "sessions",
          "birth_rate": 1.0,         # new files per session
          "words_each": 700.0,
          "initial_files": 240.0,
          "cited_frac": 0.05,        # inbound-live-reference blocking fraction
          "cascade_unlock_frac": 0.0,  # share of cited_frac released when the
                                       # living tails compress (ledger cascade)
          "backref_rate": 0.05,      # back-reference demand per session
          "tombstone_lines_each": 0.0,  # index lines left per deleted doc
          "indexed": False,          # hist files add boot-index lines
          "active_pool": None,       # or {"initial": F, "lifetime_bands": B}
                                     # for classes born active, then terminal
          "modes": ["keep", "archive", "delete_tomb", "delete_bare"],
          "windows": [1, 2, 4],      # candidate windows, in bands
        },
        ...
      ],
    }

Policy shape (``policy_grid`` builds these; you can hand-craft one too)::

    {"name": str,   # optional on hand-crafted policies; derived when absent
     "classes": {<class name>: {"mode": <RETENTION_MODES member>, "window": int}},
     "ledger_compress": bool, "journal_cap": float,
     "index_hist_tombstones": bool}

Pure stdlib, deterministic per seed (``random.Random`` instances only, no
randomness at import), no I/O, never prints — the CLI wires presentation.
"""



RETENTION_MODES: tuple[str, ...] = ("keep", "archive", "delete_tomb", "delete_bare")


def default_calibration() -> dict[str, Any]:
    """Return a neutral, illustrative calibration — every value UNVERIFIED.

    These numbers exist so the search runs out of the box and the shape is
    executable documentation; they are NOT measurements of any repo. Follow
    ``calibration_recipe()`` to measure your own corpus before trusting a
    winner. The default grid is deliberately small (a few seconds end to end);
    raise ``grid_scale`` to widen the candidate windows.
    """
    return {
        "sessions_per_band": 20.0,
        "words_per_token": 0.75,
        "initial_age_bands": 12,
        "live_files": 100.0,
        "live_words": 150000.0,
        "boot_fixed_words": 6000.0,
        "journal_words": 4000.0,
        "journal_caps": [1000000, 2000],
        "ledger_base_words": 1500.0,
        "ledger_tail_per_band": 300.0,
        "ledger_tail_bands_initial": 6,
        "ledger_tail_compressed_bands": 2,
        "index_active_line_words": 20.0,
        "index_hist_line_words": 18.0,
        "tombstone_words": 20.0,
        "greps_per_session": 8.0,
        "grep_hits_per_1k_files": 50.0,
        "skim_words_per_hit": 12.0,
        "open_frac_per_hit": 0.10,
        "open_words_per_hit": 200.0,
        "archive_pollution_w_per_mw": 25.0,
        "maintenance_w_per_mw": 8.0,
        "ls_scan_words_per_file": 5.0,
        "ls_scans_per_session": 2.0,
        "backref_halflife_bands": 3.0,
        "tombstone_hop_words": 300.0,
        "bare_rederive_words": 3000.0,
        "bare_find_fail": 0.5,
        "stale_act_base": 0.01,
        "stale_act_cost": 10000.0,
        "miss_per_band_max": 0.005,
        "near_best_frac": 0.05,
        "grid_scale": 1,
        "sensitivity_multipliers": [1 / 3, 3],
        "sensitivity_keys": [
            "stale_act_base",
            "grep_hits_per_1k_files",
            "maintenance_w_per_mw",
            "archive_pollution_w_per_mw",
            "classes.sessions.backref_rate",
            "classes.plans.backref_rate",
        ],
        "classes": [
            {
                "name": "sessions",
                "birth_rate": 1.0,
                "words_each": 700.0,
                "initial_files": 240.0,
                "cited_frac": 0.05,
                "cascade_unlock_frac": 0.0,
                "backref_rate": 0.05,
                "tombstone_lines_each": 0.0,
                "indexed": False,
                "active_pool": None,
                "modes": ["keep", "archive", "delete_tomb", "delete_bare"],
                "windows": [1, 2, 4],
            },
            {
                "name": "plans",
                "birth_rate": 0.25,
                "words_each": 2500.0,
                "initial_files": 60.0,
                "cited_frac": 0.90,
                "cascade_unlock_frac": 0.85,
                "backref_rate": 0.20,
                "tombstone_lines_each": 1.0,
                "indexed": True,
                "active_pool": {"initial": 40.0, "lifetime_bands": 4.0},
                "modes": ["keep", "archive", "delete_tomb"],
                "windows": [2, 4],
            },
            {
                "name": "notes",
                "birth_rate": 0.20,
                "words_each": 800.0,
                "initial_files": 40.0,
                "cited_frac": 0.10,
                "cascade_unlock_frac": 0.0,
                "backref_rate": 0.02,
                "tombstone_lines_each": 1.0,
                "indexed": False,
                "active_pool": None,
                "modes": ["delete_tomb"],
                "windows": [4],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Policy space
# ---------------------------------------------------------------------------


def _sim_policy_name(policy: dict[str, Any]) -> str:
    """Render the deterministic display name for one policy dict."""
    parts = [
        f"{name}={spec['mode']}@{spec['window']}b"
        for name, spec in sorted(policy["classes"].items())
    ]
    parts.append(f"ledger={'compress' if policy['ledger_compress'] else 'grow'}")
    parts.append(f"journal<={policy['journal_cap']:g}")
    parts.append(f"idx={'tomb' if policy['index_hist_tombstones'] else 'full'}")
    return " ".join(parts)


def _sim_class_candidates(
    cls_cal: dict[str, Any],
    grid_scale: int,
) -> list[tuple[str, int]]:
    """Return the (mode, window) candidates one class declaration allows.

    ``keep`` collapses to a single ``(keep, 0)`` candidate (its window is
    meaningless); ``grid_scale`` N widens each declared window by factors
    1..N, deduplicated and sorted, so hosts can search deeper without editing
    the class declarations.
    """
    windows = sorted(
        {
            int(w) * f
            for w in cls_cal["windows"]
            for f in range(1, max(grid_scale, 1) + 1)
        },
    )
    candidates: list[tuple[str, int]] = []
    for mode in cls_cal["modes"]:
        if mode == "keep":
            candidates.append(("keep", 0))
        else:
            candidates.extend((mode, w) for w in windows)
    return candidates


def policy_grid(calibration: dict[str, Any]) -> list[dict[str, Any]]:
    """Build the candidate-policy grid from the calibration's class declarations.

    The grid is the cartesian product of every class's ``modes`` × ``windows``
    (widened by ``grid_scale``), crossed with the living-file toggles: ledger
    compression on/off and each ``journal_caps`` value. Historical index lines
    are always tombstone-compressed in generated candidates (the status-quo
    baseline inside ``run_search`` covers the full-line alternative).
    """
    grid_scale = int(calibration.get("grid_scale", 1))
    class_names = [c["name"] for c in calibration["classes"]]
    per_class = [_sim_class_candidates(c, grid_scale) for c in calibration["classes"]]
    journal_caps = calibration.get("journal_caps", [10**9])
    policies: list[dict[str, Any]] = []
    for combo in itertools.product(*per_class):
        for ledger_compress, journal_cap in itertools.product(
            (True, False),
            journal_caps,
        ):
            policy: dict[str, Any] = {
                "classes": {
                    name: {"mode": mode, "window": window}
                    for name, (mode, window) in zip(class_names, combo, strict=True)
                },
                "ledger_compress": ledger_compress,
                "journal_cap": float(journal_cap),
                "index_hist_tombstones": True,
            }
            policy["name"] = _sim_policy_name(policy)
            policies.append(policy)
    return policies


def _sim_status_quo(calibration: dict[str, Any]) -> dict[str, Any]:
    """Return the keep-everything baseline policy for this calibration."""
    policy: dict[str, Any] = {
        "classes": {
            c["name"]: {"mode": "keep", "window": 0} for c in calibration["classes"]
        },
        "ledger_compress": False,
        "journal_cap": float(10**9),
        "index_hist_tombstones": False,
    }
    policy["name"] = _sim_policy_name(policy)
    return policy


# ---------------------------------------------------------------------------
# Corpus state: per class, bucketed by age-in-bands since terminal
# ---------------------------------------------------------------------------


def _sim_initial_state(calibration: dict[str, Any]) -> dict[str, Any]:
    """Build the initial corpus state from the calibration's stocks.

    Each class's initial terminal stock is spread uniformly over
    ``initial_age_bands`` age buckets (bucket index = bands since the file
    went terminal); classes with an ``active_pool`` start with its declared
    active count.
    """
    age_bands = max(int(calibration.get("initial_age_bands", 12)), 1)
    classes: dict[str, dict[str, Any]] = {}
    for cls in calibration["classes"]:
        pool = cls.get("active_pool") or {}
        classes[cls["name"]] = {
            "buckets": [float(cls.get("initial_files", 0.0)) / age_bands] * age_bands,
            "active": float(pool.get("initial", 0.0)),
        }
    return {
        "classes": classes,
        "archived_words": 0.0,
        "tombstone_lines": 0.0,
        "ledger_tail_bands": float(calibration.get("ledger_tail_bands_initial", 0)),
    }


def _sim_age_out(buckets: list[float], window: int, keep_frac: float) -> float:
    """Prune buckets older than ``window`` in place; return files removed.

    ``keep_frac`` is the citation-locked fraction that stays in place (still
    referenced by living docs, so not yet removable).
    """
    removed = 0.0
    for i in range(len(buckets)):
        if i >= window and buckets[i] > 0:
            hold = buckets[i] * keep_frac
            removed += buckets[i] - hold
            buckets[i] = hold
    return removed


def _sim_grow(
    state: dict[str, Any],
    calibration: dict[str, Any],
    rng: random.Random,
) -> None:
    """Advance one band of corpus growth (births, completions, tail accretion).

    Births carry a small deterministic-per-seed jitter (±10%) so the seed is
    load-bearing; the draw count per band is policy-independent, which keeps
    same-seed policy comparisons exact.
    """
    n_sessions = float(calibration["sessions_per_band"])
    for cls in calibration["classes"]:
        cs = state["classes"][cls["name"]]
        births = float(cls["birth_rate"]) * n_sessions * (0.9 + 0.2 * rng.random())
        pool = cls.get("active_pool")
        if pool:
            lifetime = max(float(pool.get("lifetime_bands", 1.0)), 1.0)
            completions = cs["active"] / lifetime
            cs["active"] += births - completions
            cs["buckets"].insert(0, completions)
        else:
            cs["buckets"].insert(0, births)


def _sim_prune(
    state: dict[str, Any],
    policy: dict[str, Any],
    calibration: dict[str, Any],
) -> None:
    """Apply one band of the policy's per-class retention actions.

    Inbound-reference blocking: a class's ``cited_frac`` locks that share of
    delete-eligible files in place; when the policy compresses the living
    tails, ``cascade_unlock_frac`` of that lock is released (the deletability
    cascade — provenance decoration in living history tails is the top citer).
    Archiving is never citation-blocked: the body stays recoverable in-tree.
    """
    for cls in calibration["classes"]:
        spec = policy["classes"][cls["name"]]
        mode, window = spec["mode"], int(spec["window"])
        if mode == "keep" or window <= 0:
            continue
        block = float(cls.get("cited_frac", 0.0))
        if policy["ledger_compress"]:
            block *= 1.0 - float(cls.get("cascade_unlock_frac", 0.0))
        buckets = state["classes"][cls["name"]]["buckets"]
        if mode == "archive":
            moved = _sim_age_out(buckets, window, keep_frac=0.0)
            state["archived_words"] += moved * float(cls["words_each"])
        elif mode == "delete_tomb":
            gone = _sim_age_out(buckets, window, keep_frac=block)
            state["tombstone_lines"] += gone * float(
                cls.get("tombstone_lines_each", 1.0),
            )
        elif mode == "delete_bare":
            _sim_age_out(buckets, window, keep_frac=block)


def _sim_dispo(mode: str, window: int, halflife: float) -> tuple[float, float, float]:
    """Split back-reference demand into (in-tree, tombstone, bare) fractions.

    Demand decays exponentially with age (``halflife`` in bands); the share
    older than the prune window lands on the pruned disposition.
    """
    if mode in ("keep", "archive") or window <= 0:
        return 1.0, 0.0, 0.0
    p_old = 0.5 ** (window / max(halflife, 0.1))
    if mode == "delete_tomb":
        return 1.0 - p_old, p_old, 0.0
    return 1.0 - p_old, 0.0, p_old


def _sim_boot_cost(
    state: dict[str, Any],
    policy: dict[str, Any],
    calibration: dict[str, Any],
) -> float:
    """Return the per-session boot tax (always-read route, words)."""
    tail_bands = (
        float(calibration.get("ledger_tail_compressed_bands", 2))
        if policy["ledger_compress"]
        else state["ledger_tail_bands"]
    )
    ledger_tail = tail_bands * float(calibration["ledger_tail_per_band"])
    journal = min(float(calibration["journal_words"]), float(policy["journal_cap"]))
    per_hist = (
        float(calibration["tombstone_words"])
        if policy["index_hist_tombstones"]
        else float(calibration["index_hist_line_words"])
    )
    index_words = state["tombstone_lines"] * float(calibration["tombstone_words"])
    for cls in calibration["classes"]:
        if not cls.get("indexed", False):
            continue
        cs = state["classes"][cls["name"]]
        index_words += cs["active"] * float(calibration["index_active_line_words"])
        index_words += sum(cs["buckets"]) * per_hist
    return (
        float(calibration["boot_fixed_words"])
        + journal
        + float(calibration["ledger_base_words"])
        + ledger_tail
        + index_words
    )


def _sim_discovery_cost(
    state: dict[str, Any],
    calibration: dict[str, Any],
    term_files: float,
    term_words: float,
) -> float:
    """Return the per-session discovery tax (grep noise, scans, maintenance)."""
    live_files = float(calibration["live_files"]) + sum(
        cs["active"] for cs in state["classes"].values()
    )
    total_files = term_files + live_files
    hits_per_grep = float(calibration["grep_hits_per_1k_files"]) * total_files / 1000.0
    term_share = term_files / max(total_files, 1.0)
    per_hit = float(calibration["skim_words_per_hit"]) + float(
        calibration["open_frac_per_hit"],
    ) * float(calibration["open_words_per_hit"])
    grep_noise = (
        float(calibration["greps_per_session"]) * hits_per_grep * term_share * per_hit
    )
    ls_noise = (
        float(calibration["ls_scans_per_session"])
        * term_files
        * float(calibration["ls_scan_words_per_file"])
    )
    arch_noise = (
        float(calibration["archive_pollution_w_per_mw"]) * state["archived_words"] / 1e6
    )
    tree_words = term_words + float(calibration["live_words"]) + state["archived_words"]
    maintenance = float(calibration["maintenance_w_per_mw"]) * tree_words / 1e6
    return grep_noise + ls_noise + arch_noise + maintenance


def _sim_backref_and_miss(
    policy: dict[str, Any],
    calibration: dict[str, Any],
) -> tuple[float, float]:
    """Return (back-reference cost, retrieval-miss events), both per session.

    In-tree demand costs nothing extra (reading a present body is work, not
    waste); a tombstone costs one recovery hop; a bare deletion costs a full
    re-derivation when recovery fails and a doubled hop when it succeeds. The
    miss metric counts only failed bare recoveries — the risk the feasibility
    constraint bounds.
    """
    halflife = float(calibration["backref_halflife_bands"])
    hop = float(calibration["tombstone_hop_words"])
    fail = float(calibration["bare_find_fail"])
    rederive = float(calibration["bare_rederive_words"])
    backref = miss = 0.0
    for cls in calibration["classes"]:
        spec = policy["classes"][cls["name"]]
        _in_tree, tomb, bare = _sim_dispo(spec["mode"], int(spec["window"]), halflife)
        rate = float(cls.get("backref_rate", 0.0))
        backref += rate * tomb * hop
        backref += rate * bare * (fail * rederive + (1.0 - fail) * hop * 2.0)
        miss += rate * bare * fail
    return backref, miss


def _sim_stale_cost(
    state: dict[str, Any],
    policy: dict[str, Any],
    calibration: dict[str, Any],
    term_words: float,
    initial_term_words: float,
) -> float:
    """Return the per-session staleness cost (acting on dead content as live)."""
    tail_bands = (
        float(calibration.get("ledger_tail_compressed_bands", 2))
        if policy["ledger_compress"]
        else state["ledger_tail_bands"]
    )
    ledger_tail = tail_bands * float(calibration["ledger_tail_per_band"])
    norm_tail = max(
        float(calibration.get("ledger_tail_bands_initial", 1)),
        1.0,
    ) * float(calibration["ledger_tail_per_band"])
    scale = (term_words / (initial_term_words + 1.0)) * 0.6 + (
        ledger_tail / max(norm_tail, 1.0)
    ) * 0.4
    return (
        float(calibration["stale_act_base"])
        * scale
        * float(
            calibration["stale_act_cost"],
        )
    )


def simulate_policy(
    policy: dict[str, Any],
    calibration: dict[str, Any],
    *,
    bands: int,
    seed: int = 7,
) -> dict[str, Any]:
    """Simulate one policy over ``bands`` reconciliation bands; score it.

    Returns the per-policy result record: the four per-session cost components
    (``boot``, ``discovery``, ``backref``, ``stale``, band-averaged words per
    session), their ``total``, the ``miss_per_band`` risk metric with its
    ``feasible`` verdict (< ``miss_per_band_max``), and the horizon-end tree
    size (``end_terminal_files``, ``end_tree_kwords``). Deterministic for a
    given (policy, calibration, bands, seed).
    """
    rng = random.Random(seed)
    name = policy.get("name") or _sim_policy_name(policy)
    state = _sim_initial_state(calibration)
    initial_term_words = sum(
        float(c.get("initial_files", 0.0)) * float(c["words_each"])
        for c in calibration["classes"]
    )
    totals = {"boot": 0.0, "discovery": 0.0, "backref": 0.0, "stale": 0.0}
    miss_events = 0.0
    term_files = term_words = 0.0
    n_bands = max(int(bands), 1)
    for _ in range(n_bands):
        _sim_grow(state, calibration, rng)
        if not policy["ledger_compress"]:
            state["ledger_tail_bands"] += 1.0
        _sim_prune(state, policy, calibration)
        term_files = sum(sum(cs["buckets"]) for cs in state["classes"].values())
        term_words = sum(
            sum(state["classes"][c["name"]]["buckets"]) * float(c["words_each"])
            for c in calibration["classes"]
        )
        totals["boot"] += _sim_boot_cost(state, policy, calibration)
        totals["discovery"] += _sim_discovery_cost(
            state,
            calibration,
            term_files,
            term_words,
        )
        backref, miss = _sim_backref_and_miss(policy, calibration)
        totals["backref"] += backref
        miss_events += miss
        totals["stale"] += _sim_stale_cost(
            state,
            policy,
            calibration,
            term_words,
            initial_term_words,
        )
    per = {k: v / n_bands for k, v in totals.items()}
    per_total = sum(per.values())
    miss_per_band = miss_events / n_bands
    return {
        "policy": policy,
        "name": name,
        **per,
        "total": per_total,
        "miss_per_band": miss_per_band,
        "feasible": miss_per_band < float(calibration.get("miss_per_band_max", 0.005)),
        "end_terminal_files": term_files,
        "end_tree_kwords": (
            term_words + float(calibration["live_words"]) + state["archived_words"]
        )
        / 1000.0,
    }


# ---------------------------------------------------------------------------
# Search, sensitivity, why-it-won
# ---------------------------------------------------------------------------


def _sim_scaled(calibration: dict[str, Any], key: str, mult: float) -> dict[str, Any]:
    """Return a deep copy of the calibration with one constant multiplied.

    ``key`` is either a top-level constant name or a class field addressed as
    ``classes.<class name>.<field>``. Unknown class addresses scale nothing
    (the copy is returned unchanged) so pruned class lists stay sweepable.
    """
    scaled = copy.deepcopy(calibration)
    if key.startswith("classes."):
        _, cls_name, field = key.split(".", 2)
        for cls in scaled["classes"]:
            if cls["name"] == cls_name and field in cls:
                cls[field] = float(cls[field]) * mult
        return scaled
    scaled[key] = float(scaled[key]) * mult
    return scaled


def _sim_sensitivity(
    policy: dict[str, Any],
    calibration: dict[str, Any],
    *,
    bands: int,
    seed: int,
    base_total: float,
) -> list[dict[str, Any]]:
    """Re-score the winner under each sweep multiplier on each swept constant."""
    entries: list[dict[str, Any]] = []
    multipliers = calibration.get("sensitivity_multipliers", [1 / 3, 3])
    for key in calibration.get("sensitivity_keys", []):
        for mult in multipliers:
            scaled = _sim_scaled(calibration, key, float(mult))
            total = simulate_policy(policy, scaled, bands=bands, seed=seed)["total"]
            entries.append(
                {
                    "key": key,
                    "multiplier": float(mult),
                    "total": total,
                    "delta": total - base_total,
                },
            )
    return entries


def _sim_why_it_won(
    winner: dict[str, Any],
    baseline: dict[str, Any],
    calibration: dict[str, Any],
    *,
    feasible_count: int,
    grid_size: int,
    near_count: int,
) -> str:
    """Render the WHY-IT-WON record for one search outcome."""
    words_per_token = max(float(calibration.get("words_per_token", 0.75)), 0.01)
    base_total = baseline["total"]
    saved = base_total - winner["total"]
    pct = 100.0 * saved / base_total if base_total > 0 else 0.0
    near_frac = float(calibration.get("near_best_frac", 0.05))
    lines = [
        f"winner: {winner['name']}",
        (
            f"vs keep-everything baseline: {base_total:,.0f} -> "
            f"{winner['total']:,.0f} words/session ({pct:.0f}% lower), "
            f"~{saved / words_per_token / 1000:.1f}k tokens/session saved"
        ),
        (
            f"tree size at horizon: {baseline['end_tree_kwords']:,.0f}kw -> "
            f"{winner['end_tree_kwords']:,.0f}kw"
        ),
        (
            f"retrieval-miss events/band: {winner['miss_per_band']:.4f} "
            f"(constraint < {float(calibration.get('miss_per_band_max', 0.005)):g})"
        ),
        (
            f"feasible policies: {feasible_count} of {grid_size}; secondary "
            f"objective picked the smallest tree among {near_count} within "
            f"{near_frac:.0%} of the best primary score"
        ),
    ]
    if not winner["feasible"]:
        lines.append(
            "WARNING: no candidate met the miss constraint — winner is the "
            "lowest-cost INFEASIBLE policy; loosen windows or drop delete_bare",
        )
    return "\n".join(lines)


def run_search(
    calibration: dict[str, Any],
    *,
    bands: int = 24,
    seed: int = 7,
) -> dict[str, Any]:
    """Run the full policy-grid search and return the winner with its record.

    Primary objective: lowest expected words/session among FEASIBLE policies
    (``miss_per_band`` under the calibration's bound). Secondary objective
    (lean by construction): among feasible policies within ``near_best_frac``
    of the best primary score, the smallest tree at horizon wins. Returns
    ``{"winner", "why_it_won", "feasible_count", "sensitivity"}`` — the winner
    is the full ``simulate_policy`` record (policy dict under ``"winner"["policy"]``).
    If nothing is feasible the search degrades gracefully: the lowest-cost
    infeasible policy wins and ``why_it_won`` carries a loud warning.
    """
    grid = policy_grid(calibration)
    results = [
        simulate_policy(policy, calibration, bands=bands, seed=seed) for policy in grid
    ]
    feasible = [r for r in results if r["feasible"]]
    pool = feasible or sorted(results, key=lambda r: r["total"])
    best_total = min(r["total"] for r in pool)
    near_frac = float(calibration.get("near_best_frac", 0.05))
    near = [r for r in pool if r["total"] <= best_total * (1.0 + near_frac)]
    near.sort(key=lambda r: (r["end_tree_kwords"], r["total"], r["name"]))
    winner = near[0]
    baseline = simulate_policy(
        _sim_status_quo(calibration),
        calibration,
        bands=bands,
        seed=seed,
    )
    sensitivity = _sim_sensitivity(
        winner["policy"],
        calibration,
        bands=bands,
        seed=seed,
        base_total=winner["total"],
    )
    why = _sim_why_it_won(
        winner,
        baseline,
        calibration,
        feasible_count=len(feasible),
        grid_size=len(grid),
        near_count=len(near),
    )
    return {
        "winner": winner,
        "why_it_won": why,
        "feasible_count": len(feasible),
        "sensitivity": sensitivity,
    }


def calibration_recipe() -> str:
    """Return the re-measurement recipe for grounding a calibration in a repo.

    The kit ships the search, not our constants: every default is a
    placeholder. Measure the five profiles below against YOUR corpus, write
    the numbers into a copy of ``default_calibration()``, then re-run
    ``run_search`` — and re-measure whenever the corpus shape shifts.
    """
    return (
        "Calibration recipe — measure your repo, then edit default_calibration()\n"
        "\n"
        "Every default constant is an UNVERIFIED placeholder. Ground each group\n"
        "in measurements before trusting a winner:\n"
        "\n"
        "```sh\n"
        "# 1) Badge census — per-class stocks (initial_files, words_each):\n"
        "#    count and word-count files per lifecycle class (terminal vs live).\n"
        "grep -rlE '\\*\\*Status:\\*\\* .(historical|archived)' docs/ | wc -l\n"
        "grep -rlE '\\*\\*Status:\\*\\* .(historical|archived)' docs/ | xargs wc -w\n"
        "ls .sessions/*.md | wc -l && wc -w .sessions/*.md | tail -1\n"
        "\n"
        "# 2) Grep-noise profile — discovery constants (grep_hits_per_1k_files,\n"
        "#    share of hits landing in terminal docs): run ~20 representative\n"
        "#    working-term greps and count hit locations.\n"
        'for t in <your 20 working terms>; do grep -rl "$t" docs/ ; done |\n'
        "  sort | uniq -c | sort -rn | head\n"
        "\n"
        "# 3) Velocity — sessions_per_band and per-class birth_rate:\n"
        "#    files born per session over recent history.\n"
        "git log --since='30 days ago' --oneline --merges | wc -l\n"
        "git log --since='30 days ago' --name-only --diff-filter=A -- docs/ |\n"
        "  grep '\\.md$' | sort | uniq | wc -l\n"
        "\n"
        "# 4) Back-reference greps — backref_rate and cited_frac per class:\n"
        "#    how often terminal docs are cited from OUTSIDE their own dir.\n"
        "for f in .sessions/*.md; do\n"
        '  grep -rl "$(basename "$f")" docs/ --include=\'*.md\' |\n'
        "    grep -v '^.sessions/'; done | sort -u | wc -l\n"
        "\n"
        "# 5) Boot word count — boot_fixed_words / journal_words /\n"
        "#    ledger_base_words: word-count the always-read orientation route.\n"
        "wc -w CLAUDE.md .session-journal.md docs/current-state.md\n"
        "```\n"
        "\n"
        "Sweep discipline: constants you could not measure (staleness, archive\n"
        "pollution) stay assumption-grade — list them in sensitivity_keys so\n"
        "every search re-checks the winner under x1/3 and x3. Adopt a winner\n"
        "only when its rank holds across the whole sweep.\n"
    )

# --- engine/stances/stances.py ---
"""Task-stance definitions — the fourth control axis (plan section 3b).

A *stance* is the working agent's operational posture for the current task,
distinct from adoption-pace (``mode``), promotion-rights, and stage. Following
Roo Code's proven mode model, each stance scopes three things to cut context rot
and tool misfires:

  - a **reading-route** — which docs to load first;
  - a **tool-scope** — which action categories are in-bounds;
  - an **output contract** — what the stance is expected to produce.

The active stance lives in state (``"stance"``) and is **advisory**: the contract
guides the agent, and an optional PreToolUse guard can warn on an out-of-stance
action (e.g. an edit while in ``review``) via :func:`is_out_of_stance`.

Like the question bank, the set ships as a Python module — not the plan's literal
``stances.yml`` — so it embeds in the stdlib-only bootstrap with no YAML parser
and runs identically in ``src`` and the single-file ``dist``.
"""


# Canonical action categories a stance's tool-scope is drawn from.
READ = "read"  # read files / memory / source
RUN = "run"  # run read-only tools / commands
EDIT = "edit"  # modify files
COMMENT = "comment"  # emit review comments (no file edits)

ACTIONS = (READ, RUN, EDIT, COMMENT)

DEFAULT_STANCE = "analysis"

STANCES: list[dict] = [
    {
        "name": "question",
        "role": "Answer concisely from memory and source; make no changes.",
        "when_to_use": "A direct question that memory or a quick read can answer.",
        "reading_route": ["current-state.md", "AGENT_ORIENTATION.md"],
        "tools": [READ],
        "output": "A concise answer grounded in memory/source; no edits.",
    },
    {
        "name": "analysis",
        "role": "Read-only deep-dive: investigate and report, do not change.",
        "when_to_use": "Understanding a system, tracing a behavior, scoping work.",
        "reading_route": ["AGENT_ORIENTATION.md", "architecture.md", "ownership.md"],
        "tools": [READ, RUN],
        "output": "Findings (evidence + conclusion), not changes.",
    },
    {
        "name": "debug",
        "role": "Read, run, and make targeted edits to fix a known fault.",
        "when_to_use": "A reproduced, localized fault with a clear blast radius.",
        "reading_route": ["runtime_contracts.md", "current-state.md"],
        "tools": [READ, RUN, EDIT],
        "output": "A targeted fix for the known fault; no broad refactor.",
    },
    {
        "name": "review",
        "role": "Evaluate a diff against the contracts; comment, do not edit.",
        "when_to_use": "Assessing a change someone else (or a prior stance) produced.",
        "reading_route": ["architecture.md", "ownership.md", "runtime_contracts.md"],
        "tools": [READ, COMMENT],
        "output": "A verdict + comments against the contracts; no edits.",
    },
    {
        "name": "plan",
        "role": "Research + safe prototyping, then propose a plan for approval.",
        "when_to_use": "A multi-step or architectural change worth designing first.",
        "reading_route": ["AGENT_ORIENTATION.md", "current-state.md", "roadmap.md"],
        "tools": [READ, RUN],
        "output": "An approved plan (research + safe prototyping; no committed change).",
    },
]

_BY_NAME = {s["name"]: s for s in STANCES}


def stance_names() -> list[str]:
    """Return the available stance names, in declared order."""
    return [s["name"] for s in STANCES]


def get_stance(name: str) -> dict | None:
    """Return the stance definition for ``name`` (or None if unknown)."""
    return _BY_NAME.get(name)


def action_allowed(name: str, action: str) -> bool:
    """True if ``action`` is in ``name``'s tool-scope (False for an unknown stance)."""
    stance = _BY_NAME.get(name)
    return stance is not None and action in stance["tools"]


def is_out_of_stance(name: str, action: str) -> bool:
    """True if ``action`` falls *outside* a known stance's tool-scope.

    The predicate a PreToolUse guard calls to warn on, e.g., an edit while the
    active stance is ``review``. Returns False for an unknown stance (nothing to
    enforce) so the guard fails **open** — it never blocks on a misconfigured name.
    """
    stance = _BY_NAME.get(name)
    if stance is None:
        return False
    return action not in stance["tools"]


def stance_briefing(name: str) -> str:
    """Return the orientation block injected for the active stance.

    The reading-route + tool-scope + output contract, formatted for injection into
    session orientation (alongside the user-style block and reflection buffer).
    """
    stance = _BY_NAME.get(name)
    if stance is None:
        choices = ", ".join(stance_names())
        return f"Unknown stance {name!r} (choose from {choices})."
    route = " -> ".join(stance["reading_route"])
    tools = ", ".join(stance["tools"])
    return (
        f"Stance: {stance['name']} — {stance['role']}\n"
        f"  When: {stance['when_to_use']}\n"
        f"  Read first: {route}\n"
        f"  In-scope actions: {tools}\n"
        f"  Output: {stance['output']}"
    )

# --- engine/skills/skills.py ---
"""Skill sources + the skill/stance precedence model (plan section 3c).

A *skill* is an invokable procedure emitted as a native ``.claude/skills/<name>/
SKILL.md`` (YAML frontmatter for metadata-first loading + a readable body). Unlike
a stance (an ambient posture), a skill is invoked for a specific job and **declares
the capabilities it needs** — so a skill's declared capability **takes precedence
over the ambient stance** (a ``session-close`` that declares it edits can write the
session log even while the active stance is ``review``). Stances stay advisory for
anything a skill has not declared.

Like the question bank and the stances, the set ships as a Python module — embeds
in the stdlib-only bootstrap with no YAML parser, identical in ``src`` and ``dist``.
Bodies use ``${slot}`` placeholders filled from the interview at build time, so a
skill is project-aware (e.g. ``quality-gate`` runs the project's own verify command).
"""



_SESSION_CLOSE_BODY = """\
Close ${project_name}'s current session correctly.

1. Session log — write `.sessions/<date>-<slug>.md`: what changed, one new idea
   you genuinely believe in, and a one-line review of the previous session.
2. Idea backlog — groom one idea forward (the ideas-README lifecycle).
3. Verify — run the project's checks: `${verify_command}` and `bootstrap check`.
4. Commit + push on the session branch; open the PR ready (not draft).
5. Drive the PR to a terminal state — merge on green CI, or close with a reason.

Declared capabilities: edit (the log + docs), run (the checks + git)."""

_QUALITY_GATE_BODY = """\
Prove a change is good before pushing ${project_name}.

1. Run `${verify_command}` — the project's full verification (tests + lint/types).
2. Run `bootstrap check --strict` — doc + session-log hygiene.
3. Report every failure with the exact command to reproduce it.
4. Do NOT push on red — green here should mean green in CI.

Declared capabilities: run."""

_REVIEW_BODY = """\
Review the current branch's diff against ${project_name}'s binding contracts.

1. Read the contracts first (architecture / ownership / runtime), then the diff.
2. For each change check layer boundaries, mutation ownership, and the project's
   invariants. Flag violations with file:line and the rule they break.
3. Produce a verdict (approve / request-changes) + concrete fixes.
4. Do not edit — comment only. (The `review` stance pairs with this skill.)

Declared capabilities: comment."""

_REPO_HEALTH_BODY = """\
Audit ${project_name}'s documentation + session-log hygiene.

1. Run `bootstrap check` — badges, link resolution, doc reachability, and the
   required session-log markers.
2. Summarize the drift: orphaned docs, missing badges, incomplete logs.
3. Fix the small ones (link the orphan, badge the doc); capture the rest as ideas.

Declared capabilities: run."""

_DEEP_RESEARCH_BODY = """\
Answer a multi-source factual question with a cited report.

1. Decompose the question into sub-questions; search broadly (fan out).
2. Fetch the strongest sources; cross-check claims adversarially; prefer
   primary/official docs over memory.
3. Flag uncertainty explicitly; never state a guess as fact.
4. Synthesize a concise report with inline citations.

Declared capabilities: run."""

_QUESTION_BODY = """\
Answer a direct question about ${project_name} concisely.

1. Read current-state + the one relevant doc or source file.
2. Answer in a few sentences, grounded in what you read; cite the source.
3. Make no changes. (The `question` stance pairs with this skill.)

Declared capabilities: read-only."""

_ANALYSIS_BODY = """\
Investigate a ${project_name} system and report findings, changing nothing.

1. Read the binding contracts and trace the behavior across files.
2. Produce evidence (file:line) + a conclusion; name the uncertainty.
3. Do not edit. (The `analysis` stance pairs with this skill.)

Declared capabilities: read-only."""

# Each skill declares the capabilities it needs *beyond* read (read is implicit).
# The declared set is what overrides the ambient stance (the precedence rule).
SKILLS: list[dict] = [
    {
        "name": "session-close",
        "description": "End the session correctly — write the log, groom + add an "
        "idea, verify, commit, push, drive the PR to a terminal state.",
        "capabilities": [EDIT, RUN],
        "body": _SESSION_CLOSE_BODY,
    },
    {
        "name": "quality-gate",
        "description": "Run the project's full verification before pushing and "
        "report what must be fixed.",
        "capabilities": [RUN],
        "body": _QUALITY_GATE_BODY,
    },
    {
        "name": "review",
        "description": "Review the branch diff against the binding contracts; "
        "comment with a verdict and fixes, no edits.",
        "capabilities": [COMMENT],
        "body": _REVIEW_BODY,
    },
    {
        "name": "repo-health",
        "description": "Audit doc + session-log hygiene (bootstrap check) and "
        "summarize drift.",
        "capabilities": [RUN],
        "body": _REPO_HEALTH_BODY,
    },
    {
        "name": "deep-research",
        "description": "Fan out web research, adversarially verify sources, and "
        "synthesize a cited report.",
        "capabilities": [RUN],
        "body": _DEEP_RESEARCH_BODY,
    },
    {
        "name": "question",
        "description": "Answer a direct question concisely from memory and source; "
        "make no changes.",
        "capabilities": [],
        "body": _QUESTION_BODY,
    },
    {
        "name": "analysis",
        "description": "Read-only deep-dive: investigate and report findings "
        "without changing anything.",
        "capabilities": [],
        "body": _ANALYSIS_BODY,
    },
]

_SKILL_BY_NAME = {s["name"]: s for s in SKILLS}


def skill_names() -> list[str]:
    """Return the available skill names, in declared order."""
    return [s["name"] for s in SKILLS]


def get_skill(name: str) -> dict | None:
    """Return the skill definition for ``name`` (or None if unknown)."""
    return _SKILL_BY_NAME.get(name)


def skill_capabilities(name: str) -> list[str]:
    """Return a skill's full capability set (declared + the implicit ``read``)."""
    skill = _SKILL_BY_NAME.get(name)
    if skill is None:
        return []
    return [READ, *skill["capabilities"]]


def skill_permits(name: str, action: str) -> bool:
    """True if skill ``name`` declares (or implies) ``action``."""
    return action in skill_capabilities(name)


def action_permitted(
    stance_name: str,
    action: str,
    skill_name: str | None = None,
) -> bool:
    """Resolve whether ``action`` is permitted under a stance, optionally in a skill.

    Precedence (plan section 3c): a skill's explicitly-declared capability **wins**
    over the ambient stance — so an invoked skill can do what it declares even when
    the stance forbids it. For anything the skill has not declared, the stance's
    advisory tool-scope applies.
    """
    if skill_name is not None and skill_permits(skill_name, action):
        return True
    return action_allowed(stance_name, action)


def skill_frontmatter(skill: dict) -> str:
    """Return the native ``SKILL.md`` YAML frontmatter (metadata-first loading)."""
    return f'---\nname: {skill["name"]}\ndescription: "{skill["description"]}"\n---'


def skill_relpath(skill: dict) -> str:
    """Return the emit path for a skill, relative to the skills root."""
    return f"skills/{skill['name']}/SKILL.md"


def skill_document(skill: dict, body: str) -> str:
    """Compose the full ``SKILL.md`` text from a skill + its (rendered) body."""
    return f"{skill_frontmatter(skill)}\n\n# {skill['name']}\n\n{body.rstrip()}\n"

# --- engine/agents/agents.py ---
"""Persona (sub-agent) sources + native emission (plan section 3c).

A *persona* is a spawnable, read-only specialist (the third capability mechanism
alongside stances and skills): the working agent delegates a focused task —
design review, independent critique, deep exploration — to a fresh sub-agent
context. The kit ships three generalized personas, each emitted as a native
``.claude/agents/<name>.md`` (YAML frontmatter ``name`` / ``description`` /
``tools`` + a system-prompt body).

Personas are **interview-populated**: their binding sources are filled from the
project's own contract slots (``${architecture_layers}``, ``${ownership_model}``,
…) at build time — so a persona reviews against *this* project's rules, not
superbot's. Like the skills, they ship as a Python module (not a subdir of
``templates/``) so they embed in the stdlib-only bootstrap with no extra loader.

Personas are spawned specialists, so — unlike skills — they carry no stance
precedence; they are read-only by construction (their declared ``tools`` grant
no write).
"""


# Native read-only tool set for a spawned specialist (no write/edit/run).
_READONLY_TOOLS = ["Read", "Grep", "Glob"]

_ARCHITECT_BODY = """\
You are ${project_name}'s architecture specialist — read-only. Answer design
questions and review proposed changes for layer/ownership compliance BEFORE they
are coded.

Binding model (this project's contracts):
- Layers & import rules: ${architecture_layers}
- Ownership (who owns each write path): ${ownership_model}
- Mutation seam (how writes are gated): ${mutation_seam}

Method: read the relevant contracts + source, then judge a proposed change
against them. Flag every layer-boundary or ownership violation with file:line and
the rule it breaks; propose the compliant placement. You advise — you do not edit."""

_REVIEWER_BODY = """\
You are ${project_name}'s independent reviewer — a second pair of eyes that does
NOT share the author's assumptions. Evaluate a diff against the binding contracts
and surface the risks the author may have anchored past.

Review against: ${architecture_layers} · ${ownership_model} · the project's
verification (`${verify_command}`).

Anti-anchoring rule: judge the change on its evidence, not the author's stated
confidence. Give a verdict (approve / request-changes) + the specific risks and
fixes. Read-only — you comment, you do not edit. (Wire this persona to the
independent-review seam: a *different* model reviewing breaks the monoculture.)"""

_RESEARCHER_BODY = """\
You are ${project_name}'s researcher — read-only deep exploration. Map unfamiliar
code or trace a behavior across the system and report findings; change nothing.

Start from: ${doc_roots} (where durable documentation lives) and the read-path
docs, then follow the source.

Output: evidence (file:line) + a clear conclusion, with the uncertainty named.
Prefer reading source over assuming. You produce understanding, not edits."""

AGENTS: list[dict] = [
    {
        "name": "architect",
        "description": "Read-only design/layer specialist — answer architecture "
        "questions and flag layer/ownership violations before they are coded.",
        "tools": list(_READONLY_TOOLS),
        "body": _ARCHITECT_BODY,
    },
    {
        "name": "reviewer",
        "description": "Independent critic — evaluate a diff against the contracts "
        "without the author's assumptions; verdict + risks, no edits.",
        "tools": list(_READONLY_TOOLS),
        "body": _REVIEWER_BODY,
    },
    {
        "name": "researcher",
        "description": "Read-only deep exploration — map unfamiliar code / trace a "
        "behavior and report evidence-backed findings; change nothing.",
        "tools": list(_READONLY_TOOLS),
        "body": _RESEARCHER_BODY,
    },
]

_AGENT_BY_NAME = {a["name"]: a for a in AGENTS}


def agent_names() -> list[str]:
    """Return the available persona names, in declared order."""
    return [a["name"] for a in AGENTS]


def get_agent(name: str) -> dict | None:
    """Return the persona definition for ``name`` (or None if unknown)."""
    return _AGENT_BY_NAME.get(name)


def agent_frontmatter(agent: dict) -> str:
    """Return the native ``.claude/agents`` YAML frontmatter (name/description/tools)."""
    tools = ", ".join(agent["tools"])
    return (
        f"---\nname: {agent['name']}\n"
        f'description: "{agent["description"]}"\n'
        f"tools: {tools}\n---"
    )


def agent_relpath(agent: dict) -> str:
    """Return the emit path for a persona, relative to the agents root."""
    return f"agents/{agent['name']}.md"


def agent_document(agent: dict, body: str) -> str:
    """Compose the full agent ``.md`` text from a persona + its (rendered) body."""
    return f"{agent_frontmatter(agent)}\n\n{body.rstrip()}\n"

# --- engine/hooks/stance_guard.py ---
"""PreToolUse stance guard — makes the stance layer enforced, not just advisory.

Claude Code calls a PreToolUse hook before each tool runs, passing the tool name
in a JSON payload on stdin. This maps the tool to a stance action category
(read / run / edit / comment) and, if that action is outside the active stance's
tool-scope, produces an advisory warning — the agent stays free to proceed
(stances are advisory by default, plan section 3b). The bootstrap
``hook pretooluse`` command is the runtime entry point; ``settings_snippet``
generates the ``.claude/settings.json`` wiring a host installs.

Everything here **fails open**: an unknown tool, an unknown stance, or a
malformed payload yields no warning — the guard never gets in the way when it is
unsure.
"""




# Claude Code tool name -> the stance action category it performs. Tools not
# listed (Task, the slash-command tools, …) carry no stance opinion (fail open).
TOOL_ACTIONS: dict[str, str] = {
    "Read": READ,
    "Grep": READ,
    "Glob": READ,
    "NotebookRead": READ,
    "Edit": EDIT,
    "Write": EDIT,
    "NotebookEdit": EDIT,
    "Bash": RUN,
    "WebFetch": RUN,
    "WebSearch": RUN,
}


def tool_to_action(tool_name: str) -> str | None:
    """Return the stance action category a Claude Code tool performs (or None)."""
    return TOOL_ACTIONS.get(tool_name)


def tool_from_payload(raw: str) -> str:
    """Extract the tool name from a PreToolUse stdin payload (``""`` if absent)."""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return ""
    name = payload.get("tool_name", "") if isinstance(payload, dict) else ""
    return name if isinstance(name, str) else ""


def evaluate_tool(stance: str, tool_name: str) -> str | None:
    """Return an out-of-stance warning for ``tool_name`` under ``stance``, or None.

    ``None`` means no objection — the tool carries no stance opinion, or the
    action is within the stance's tool-scope. Fails open: an unknown stance or
    tool never warns.
    """
    action = tool_to_action(tool_name)
    if action is None or not is_out_of_stance(stance, action):
        return None
    return (
        f"out-of-stance: {tool_name} ({action}) while stance is '{stance}'. "
        "Re-check the task, or switch stance (`bootstrap stance <name>`). "
        "(advisory — not blocked)"
    )


def settings_snippet(command: str) -> str:
    """Return a ``.claude/settings.json`` PreToolUse wiring snippet (JSON text).

    ``command`` is the shell command Claude Code runs before each tool (e.g.
    ``python3 bootstrap.py hook pretooluse``). The host merges the returned
    ``hooks.PreToolUse`` block into their ``.claude/settings.json``.
    """
    snippet = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "*",
                    "hooks": [{"type": "command", "command": command}],
                },
            ],
        },
    }
    return json.dumps(snippet, indent=2) + "\n"

# --- engine/hooks/session_start.py ---
"""SessionStart orientation composer (plan section 5.B, Lane B7).

The nervous system's *injection* point: when Claude Code starts a session, the
``bootstrap hook sessionstart`` entry point prints the text this module
composes, so the agent boots already knowing the project's mode, stance,
learned lessons, fired triggers, and pending questions. The composition is
**mode-aware** — ``orientation_depth`` (observe → minimal, guided → standard,
active → full) decides which sections render and how hard they cap.

Section order (the plan's fixed sequence): status header → stance briefing →
user-style block → learned lessons (AFTER user-style) → trigger block →
guided-practices line → economy-gauges advisory (over-cap only) → pending
questions (quota view) → observe-mode workflow proposal.

Every section is defensive: a failure inside one section drops that section,
never the whole composition — orientation must never crash a session. This is
the one place broad ``except Exception`` is correct by design (fail open, like
the stance guard).
"""




# Depth "standard" caps the learned-lessons section at this many entries.
_ORI_STANDARD_LESSON_CAP = 3
# Depth "minimal" (observe) renders only these section numbers: the status
# header (1), the trigger block as an advisory (5), and the workflow proposal
# (9) — observe imposes nothing else.
_ORI_MINIMAL_SECTIONS = frozenset({1, 5, 9})


def _ori_status_header(state: dict[str, Any], config: Config) -> str:
    """Render section 1 — the compact status header line block."""
    project = str(state.get("project_id") or config.project_id)
    return (
        f"# Session orientation — {project}\n"
        f"mode: {state.get('mode', '?')} · stage: {state.get('stage', '?')} · "
        f"stance: {state.get('stance', '?')} · "
        f"session: {int(state.get('session_count', 0))}"
    )


def _ori_stance(state: dict[str, Any]) -> str:
    """Render section 2 — the active stance briefing ('' when no stance set)."""
    stance = state.get("stance")
    if not stance:
        return ""
    return stance_briefing(str(stance))


def _ori_user_style(state: dict[str, Any]) -> str:
    """Render section 3 — the owner_profile user-style block ('' when unfilled)."""
    entry = state.get("slot_values", {}).get("owner_profile")
    value = entry.get("value") if isinstance(entry, dict) else entry
    text = str(value).strip() if value else ""
    if not text:
        return ""
    return f"## How the owner works:\n\n> {text}"


def _ori_lessons(root: Path, config: Config, depth: str) -> str:
    """Render section 4 — learned lessons (standard caps at 3, full uncapped)."""
    entries = load_reflections(root / config.state_dir / REFLECTIONS_FILENAME)
    cap = _ORI_STANDARD_LESSON_CAP if depth == "standard" else len(entries)
    return lessons_block(active_lessons(entries, cap))


def _ori_triggers(root: Path, config: Config, state: dict[str, Any]) -> str:
    """Render section 5 — the trigger block (mandate flag per the mode policy)."""
    triggers = check_triggers(root, config, state)
    questions = mandatory_questions(triggers)
    return trigger_block(triggers, questions, mandate=triggers_mandate(state))


def _ori_practices(state: dict[str, Any], config: Config) -> str:
    """Render section 6 — the one-line guided-practices block ('' when empty)."""
    practices = active_practices(state, dict(config.cadence or {}))
    if not practices:
        return ""
    return "Active practices: " + ", ".join(practices)


def _ori_gauges(root: Path, config: Config) -> str:
    """Render section 7 — economy advisory listing ONLY over-cap gauges."""
    over = [g for g in economy_gauges(root, config) if g.get("over")]
    if not over:
        return ""
    lines = ["## Economy advisory — over-cap gauges", ""]
    lines += [
        f"- {g['name']} ({g['kind']}): {g['value']} words/items over cap {g['cap']}"
        for g in over
    ]
    return "\n".join(lines)


def _ori_questions(state: dict[str, Any]) -> str:
    """Render section 8 — the quota-capped ask list with a '+N more' suffix."""
    asks = session_questions(state)
    if not asks:
        return ""
    lines = ["## Questions this session", ""]
    lines += [
        f"- {q['id']} ({q.get('priority', 'normal')}): {q['prompt']}" for q in asks
    ]
    extra = len(pending_questions(state)) - len(asks)
    if extra > 0:
        lines += ["", f"(+{extra} more later)"]
    return "\n".join(lines)


def _ori_proposal(state: dict[str, Any]) -> str:
    """Render section 9 — observe mode's workflow proposal when it is due."""
    if state.get("mode") != "observe" or not workflow_proposal_due(state):
        return ""
    return (
        "## Proposed workflow\n\n"
        "Observe mode has watched enough sessions to propose a tailored "
        "workflow. If the pacing looks right, switch mode to adopt it: "
        "`bootstrap mode guided` (one practice at a time) or "
        "`bootstrap mode active` (the full workflow now). Observe imposes "
        "nothing until you do."
    )


def _ori_safe(build: Any) -> str:
    """Run one section builder, returning '' on any failure (fail open).

    The one place broad ``except Exception`` is correct by design: a bad state
    document or an unreadable file drops that single section — orientation
    must never crash a session.
    """
    try:
        return str(build()).strip()
    except Exception:  # fail open — one bad section never breaks the whole
        return ""


def compose_orientation(root: Path, config: Config, backend: Any) -> str:
    """Compose the mode-aware SessionStart orientation injection.

    Assembles the nine plan sections in fixed order, gated by
    ``orientation_depth``: ``minimal`` renders only the status header, the
    trigger advisory, and the observe-mode proposal; ``standard`` renders all
    sections but caps lessons at 3; ``full`` renders everything uncapped.
    Every section builder runs inside its own guard — a bad state document or
    an unreadable file drops that one section, never the whole composition
    (orientation must never crash a session).
    """
    try:
        state = dict(backend.data)
    except Exception:  # fail open — orientation never crashes a session
        state = {}
    try:
        depth = orientation_depth(state)
    except Exception:  # fail open — fall back to the default depth
        depth = "standard"
    builders = (
        (1, lambda: _ori_status_header(state, config)),
        (2, lambda: _ori_stance(state)),
        (3, lambda: _ori_user_style(state)),
        (4, lambda: _ori_lessons(root, config, depth)),
        (5, lambda: _ori_triggers(root, config, state)),
        (6, lambda: _ori_practices(state, config)),
        (7, lambda: _ori_gauges(root, config)),
        (8, lambda: _ori_questions(state)),
        (9, lambda: _ori_proposal(state)),
    )
    sections: list[str] = []
    for number, build in builders:
        if depth == "minimal" and number not in _ORI_MINIMAL_SECTIONS:
            continue
        text = _ori_safe(build)
        if text:
            sections.append(text)
    if not sections:
        return ""
    return "\n\n".join(sections) + "\n"

# --- engine/hooks/post_edit.py ---
"""PostToolUse edit advisor (plan section 5.B, Lane B7).

Runs after every Edit/Write tool call: the CLI's ``hook postedit`` entry point
extracts the edited file path from the PostToolUse stdin payload and asks
``evaluate_edit`` whether the edit deserves an advisory —

- **generated artifact** — the file lives under ``<state_dir>/rendered`` or
  ``<state_dir>/contextpacks``, or its head carries the ``NOT SOURCE OF
  TRUTH`` marker: edit the template/index and re-render, not the artifact.
- **missing Status badge** — a ``*.md`` under the docs root without a
  ``> **Status:** `<token>``` badge in its first 12 lines (the same badge scan
  ``check_docs`` runs, via the shared ``badge_token`` reader).

Like every hook evaluator this **fails open**: absolute or root-relative paths
both resolve, and an unreadable / missing file yields ``None`` — the advisor
never gets in the way when it is unsure.
"""




# The HTML-comment form only: planted (hand-editable) docs carry the bare
# phrase "NOT SOURCE OF TRUTH" in their badge prose, and the guard must not
# warn on every legitimate edit of a planted binding doc — only generated
# artifacts (contextpacks etc.) open with this comment marker.
_PE_MARKER = "<!-- NOT SOURCE OF TRUTH"
_PE_HEAD_LINES = 12
# <state_dir> subdirectories that hold build artifacts, never source.
_PE_GENERATED_DIRS = ("rendered", "contextpacks")
_PE_GENERATED_MSG = (
    "generated artifact — edit the template/index and re-render, not this file"
)
_PE_BADGE_MSG = (
    "missing Status badge — add `> **Status:** `<token>`` to its first 12 lines"
)


def _pe_resolve(root: Path, file_path: str) -> tuple[Path, Path | None]:
    """Return ``(absolute path, root-relative path or None)`` for an edit path.

    Accepts absolute and root-relative inputs; the relative half is ``None``
    when the file lives outside ``root`` (nothing to classify against config
    paths there).
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = root / path
    try:
        rel = path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        rel = None
    return path, rel


def _pe_head(path: Path) -> str:
    """Return the file's first 12 lines ('' when unreadable — fail open)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return ""
    return "\n".join(lines[:_PE_HEAD_LINES])


def _pe_is_generated(config: Config, rel: Path | None, head: str) -> bool:
    """True when the edited file is a build artifact (by path or by marker)."""
    if _PE_MARKER in head:
        return True
    if rel is None:
        return False
    state_dir = Path(config.state_dir)
    return any(rel.is_relative_to(state_dir / sub) for sub in _PE_GENERATED_DIRS)


def evaluate_edit(root: Path, config: Config, file_path: str) -> str | None:
    """Return the advisory warning for one edited file, or None.

    Warns on a generated artifact (path under ``<state_dir>/rendered`` /
    ``<state_dir>/contextpacks``, or the generated-artifact HTML-comment marker)
    and on a docs-root ``*.md`` lacking a Status badge. Tolerant of absolute
    or root-relative ``file_path`` and of unreadable / missing files (None).
    """
    try:
        path, rel = _pe_resolve(root, file_path)
        if not path.is_file():
            return None
        name = rel.as_posix() if rel is not None else path.as_posix()
        if _pe_is_generated(config, rel, _pe_head(path)):
            return f"{name}: {_PE_GENERATED_MSG}"
        if (
            rel is not None
            and path.suffix == ".md"
            and rel.is_relative_to(Path(config.docs_root))
            and badge_token(path) is None
        ):
            return f"{name}: {_PE_BADGE_MSG}"
        return None
    except Exception:  # fail open — the advisor never blocks an edit
        return None

# --- engine/hooks/stop_check.py ---
"""Stop-hook session-close advisor (plan section 5.B, Lane B7).

Runs when a Claude Code session stops: the CLI's ``hook stopcheck`` entry
point prints the advisory lines ``evaluate_stop`` returns, reminding the agent
what the session ritual still owes —

- the session log is missing, or exists but lacks required markers
  (``latest_session_log`` + ``check_log`` with ``config.session_markers``);
- escalated blocking questions are still open (``state["open_questions"]``);
- the compaction cadence window has elapsed (``compaction_due``);
- the reflection buffer has not been mined today
  (``reflection_buffer.last_mined`` vs today's ISO date).

Returns ``[]`` when all clean. Advisory only, and it **fails open**: every
check runs inside its own guard, so a bad state document or an unreadable log
drops that one advisory rather than crashing the stop hook.
"""




_STOP_UNMINED_MSG = "reflections unmined this session — run bootstrap reflect --mine"


def _stop_safe(check: Any) -> list[str]:
    """Run one advisory check, returning [] on any failure (fail open).

    Each check is guarded on its own so one bad input never suppresses the
    other advisories — the stop hook is advisory by contract.
    """
    try:
        return list(check())
    except Exception:  # fail open — one bad check drops only itself
        return []


def _stop_state(backend: Any) -> dict[str, Any]:
    """Return the state document ({} when the backend is unusable — fail open)."""
    try:
        return dict(backend.data)
    except Exception:  # fail open — a broken backend yields no state advisories
        return {}


def _stop_log(root: Path, config: Config) -> list[str]:
    """Advise when the session log is missing or lacks required markers."""
    log = latest_session_log(root / config.sessions_dir)
    if log is None:
        return [
            f"no session log found under {config.sessions_dir}/ — "
            "write one before ending the session",
        ]
    missing = check_log(log, config.session_markers)
    if missing:
        return [f"session log {log.name} is missing: {', '.join(missing)}"]
    return []


def _stop_questions(state: dict[str, Any]) -> list[str]:
    """Advise when escalated blocking questions are still open."""
    open_questions = [str(q) for q in state.get("open_questions", [])]
    if not open_questions:
        return []
    listed = ", ".join(open_questions)
    return [f"{len(open_questions)} blocking question(s) open: {listed}"]


def _stop_compaction(state: dict[str, Any], config: Config) -> list[str]:
    """Advise when the compaction cadence window has elapsed."""
    if compaction_due(state, dict(config.cadence or {})):
        return ["compaction due — write the State Delta snapshot (bootstrap maintain)"]
    return []


def _stop_reflections(state: dict[str, Any]) -> list[str]:
    """Advise when the reflection buffer has not been mined today."""
    buffer = state.get("reflection_buffer")
    last_mined = buffer.get("last_mined") if isinstance(buffer, dict) else None
    if last_mined == date.today().isoformat():
        return []
    return [_STOP_UNMINED_MSG]


def evaluate_stop(root: Path, config: Config, backend: Any) -> list[str]:
    """Return the session-close advisory lines ([] when all clean).

    Four checks in fixed order: session log, open blocking questions,
    compaction cadence, reflection mining. Each runs inside its own guard so
    one failing check never suppresses the others — the stop hook is advisory
    and fails open by contract.
    """
    state = _stop_state(backend)
    checks = (
        lambda: _stop_log(root, config),
        lambda: _stop_questions(state),
        lambda: _stop_compaction(state, config),
        lambda: _stop_reflections(state),
    )
    advisories: list[str] = []
    for check in checks:
        advisories.extend(_stop_safe(check))
    return advisories

# --- engine/hooks/settings.py ---
"""Hook settings template + customization contract (plan section 5.B, Lane B7).

The staging half of the hook layer (HOOK-2): ``full_settings_template`` emits
the complete ``.claude`` ``settings.template.json`` wiring all four hook
events — PreToolUse (stance guard), SessionStart (orientation), PostToolUse
(edit advisor), Stop (session-close advisor) — each to
``<interpreter> bootstrap.py hook <event>``, the same command shape the CLI's
``_hook_command`` builds. ``hooks_fill_table`` emits the markdown
customization contract a host reads before merging: which config fields must
match their repo, and the standing rule that the kit *stages* hook settings —
it never writes a live ``.claude/`` tree itself.
"""




# (settings.json event key, bootstrap hook event, tool matcher or None).
_SET_EVENTS: tuple[tuple[str, str, str | None], ...] = (
    ("PreToolUse", "pretooluse", "*"),
    ("SessionStart", "sessionstart", None),
    ("PostToolUse", "postedit", "Edit|Write|NotebookEdit"),
    ("Stop", "stopcheck", None),
)

_SET_FILL_ROWS: tuple[tuple[str, str], ...] = (
    (
        "`interpreter`",
        "the Python that runs the kit itself — every hook command below "
        "starts with it; set it to an interpreter available on your PATH",
    ),
    (
        "`interpreter_for_checks`",
        "your *project's* verification interpreter (the version your CI "
        "pins, e.g. `python3.10`) — kept separate from `interpreter` on "
        "purpose",
    ),
    (
        "`bootstrap.py` path",
        "each hook command assumes `bootstrap.py` sits at your repo root; "
        "rewrite the path inside every command if it lives elsewhere",
    ),
    (
        "`state_dir`",
        "where kit state + staged artifacts live (default `.substrate`) — "
        "the post-edit generated-artifact warning keys off it",
    ),
    (
        "`docs_root`",
        "your documentation root (default `docs`) — the post-edit badge "
        "warning and the SessionStart trigger scan key off it",
    ),
    (
        "`sessions_dir`",
        "where per-session logs live (default `.sessions`) — the Stop-hook "
        "session-log advisory keys off it",
    ),
    (
        "cadence knobs",
        "`cadence.*` in `substrate.config.json` (`compaction_sessions`, "
        "`reconciliation_sessions`, `staleness_days`, "
        "`critical_slot_grace_sessions`, `guided_practice_sessions`) drive "
        "the SessionStart triggers and Stop-hook advisories",
    ),
)


def _set_command(config: Config, event: str, bootstrap_path: str) -> str:
    """Return the shell command Claude Code runs for one hook event."""
    return f"{config.interpreter} {bootstrap_path} hook {event}"


def full_settings_template(config: Config, bootstrap_path: str = "bootstrap.py") -> str:
    """Return the complete ``settings.template.json`` wiring all four hooks.

    JSON text (2-space indent) a host merges into ``.claude/settings.json``:
    PreToolUse (matcher ``*``), SessionStart, PostToolUse (matcher
    ``Edit|Write|NotebookEdit``), and Stop, each running
    ``<interpreter> <bootstrap_path> hook <event>``. Matcher-less events omit
    the ``matcher`` key entirely (they apply unconditionally).
    ``bootstrap_path`` is the path the hook commands reference — adopt passes
    the vendored/root-resolved location so staged hooks resolve inside the
    target repo (the Phase-2.5 staged-hook failure cause).
    """
    hooks: dict[str, list[dict]] = {}
    for settings_event, cli_event, matcher in _SET_EVENTS:
        entry: dict = {}
        if matcher is not None:
            entry["matcher"] = matcher
        entry["hooks"] = [
            {
                "type": "command",
                "command": _set_command(config, cli_event, bootstrap_path),
            },
        ]
        hooks[settings_event] = [entry]
    return json.dumps({"hooks": hooks}, indent=2) + "\n"


def hooks_fill_table() -> str:
    """Return the markdown customization contract for the settings template.

    One ``field | what must match your repo`` row per knob a host must verify
    before installing, plus the install instruction: merge the staged template
    into ``.claude/settings.json`` yourself — the kit stages hook settings, it
    never writes a live ``.claude/`` tree.
    """
    lines = [
        "# Hook settings — customization contract",
        "",
        "The kit **stages** `settings.template.json`; it never writes your",
        "`.claude/` tree. Install by merging the template's `hooks` block into",
        "your repo's `.claude/settings.json` yourself, after checking every",
        "row below against your repo.",
        "",
        "| field | what must match your repo |",
        "| --- | --- |",
    ]
    lines += [f"| {field} | {note} |" for field, note in _SET_FILL_ROWS]
    lines += [
        "",
        "All four hooks are advisory and fail open: they always exit 0 and",
        "never block a tool, an edit, or a session stop.",
    ]
    return "\n".join(lines) + "\n"

# --- engine/render.py ---
"""Render the project's content docs from templates + filled interview slots.

Templates use ``${slot_name}`` placeholders (``string.Template``). A slot the
interview has filled substitutes in; an unfilled slot is left as ``${slot_name}``
and reported — so a half-onboarded project's gaps stay visible rather than going
silently blank. Templates ship embedded in the bootstrap (the generated
``_TEMPLATES`` dict) and, in the source/pip layouts, under
``engine/templates/`` (inside the package so a wheel ships them).
"""



_PLACEHOLDER_RE = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def find_placeholders(text: str) -> set[str]:
    """Return the set of ``${name}`` placeholders remaining in ``text``."""
    return set(_PLACEHOLDER_RE.findall(text))


def render(text: str, context: dict[str, str]) -> str:
    """Substitute ``${slot}`` placeholders from ``context`` (unfilled left as-is).

    Only the braced ``${name}`` form is a placeholder — the *same* form
    ``find_placeholders`` reports, so render and the "unfilled slots stay
    visible" safety net can never disagree. Deliberately NOT
    ``string.Template.safe_substitute``: that also collapses ``$$`` → ``$`` and
    substitutes unbraced ``$word``, silently mangling host-authored ``$``
    content (shell ``$$``/``$1``, ``$5`` prices, ``$$LaTeX$$``) on the routine
    ``render --live`` in-place fill — and turning an escaped ``$${VERSION}``
    into a live-looking ``${VERSION}`` that then reports as an unfilled slot.
    A regex sub over the braced form leaves every other ``$`` byte untouched.
    """
    return _PLACEHOLDER_RE.sub(
        lambda m: context[m.group(1)] if m.group(1) in context else m.group(0),
        text,
    )


def build_context(state: dict[str, Any]) -> dict[str, str]:
    """Build the substitution context from a state document's filled slots."""
    values = state.get("slot_values", {})
    return {slot: str(entry.get("value", "")) for slot, entry in values.items()}


def load_templates() -> dict[str, str]:
    """Return ``{filename: text}`` for every template (embedded or packaged).

    The single-file bootstrap embeds them as ``_TEMPLATES``; the source/pip
    layouts read ``engine/templates/`` (INSIDE the package, so a wheel ships
    them — they once lived a level up and a pip install silently had none).
    An empty template set is a hard error, never a silent no-op render.
    """
    embedded = globals().get("_TEMPLATES")
    if embedded is not None:
        return dict(embedded)
    root = Path(__file__).resolve().parent / "templates"
    templates = {
        p.name: p.read_text(encoding="utf-8") for p in sorted(root.glob("*.tmpl"))
    }
    if not templates:
        msg = f"no templates found at {root} — broken install"
        raise FileNotFoundError(msg)
    return templates

# --- engine/derive.py ---
"""Adopt-time slot derivation — "adopt renders what it knows" (the Phase-2.5 G2 fix).

The cold-start A/B (``phase-2.5-cold-start-report-2026-07-07.md``) failed
because ``adopt`` planted raw ``${...}`` templates: a task-focused cold
session paid the reading cost and (correctly) ignored them. The fix has two
halves; this module is the first — derive every slot the kit can know
**deterministically** from the target tree (project name, primary language,
verify command, docs root) and record each as a *provisional* interview
answer before the adopt render, so the planted docs open readable instead of
inert. Provisional answers never count toward graduation until confirmed
(the interview contract is unchanged) and ``bootstrap ask`` still asks —
derivation seeds the interview, it does not replace it. Detection is
file-presence based, never a guess: a slot with no confident signal stays
unfilled (and the adopt banner marks it — the second half, in ``adopt.py``).
Pure stdlib.
"""




_REQUIRES_PYTHON_RE = re.compile(r'requires-python\s*=\s*"([^"]+)"')
_MAKEFILE_TEST_RE = re.compile(r"^test\s*:", re.MULTILINE)

# Marker files that make a tree confidently Python before any other check.
_PYTHON_MARKERS = ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")


def _read_if_exists(path: Path) -> str:
    """Return the file's text, or empty for a missing/unreadable file."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def detect_language(root: Path) -> str | None:
    """Return the project's primary language from marker files, or None.

    Python wins ties deliberately (the kit's own tooling is Python-first and a
    mixed tree with a ``pyproject.toml`` is Python-led for verification
    purposes). The version qualifier comes only from an explicit
    ``requires-python`` — never inferred.
    """
    if any((root / marker).is_file() for marker in _PYTHON_MARKERS):
        match = _REQUIRES_PYTHON_RE.search(_read_if_exists(root / "pyproject.toml"))
        return f"Python {match.group(1)}" if match else "Python"
    if (root / "package.json").is_file():
        return "TypeScript" if (root / "tsconfig.json").is_file() else "JavaScript"
    if (root / "Cargo.toml").is_file():
        return "Rust"
    if (root / "go.mod").is_file():
        return "Go"
    return None


def _python_has_tests(root: Path) -> bool:
    """True when the tree carries a recognizable pytest surface."""
    if (root / "tests").is_dir() or (root / "pytest.ini").is_file():
        return True
    pyproject = _read_if_exists(root / "pyproject.toml")
    return "[tool.pytest" in pyproject


def _npm_has_real_test_script(root: Path) -> bool:
    """True when package.json declares a test script that isn't npm's stub."""
    text = _read_if_exists(root / "package.json")
    if '"test"' not in text:
        return False
    return "no test specified" not in text


def detect_verify_command(root: Path) -> str | None:
    """Return the one-command verification entry point, or None.

    Order mirrors :func:`detect_language`; each candidate requires a positive
    marker (a test tree, a real test script, a ``test:`` target) so the
    derived command is runnable, not aspirational.
    """
    if any((root / marker).is_file() for marker in _PYTHON_MARKERS):
        if _python_has_tests(root):
            return "python3 -m pytest"
        return None
    if (root / "package.json").is_file() and _npm_has_real_test_script(root):
        return "npm test"
    if (root / "Cargo.toml").is_file():
        return "cargo test"
    if (root / "go.mod").is_file():
        return "go test ./..."
    if _MAKEFILE_TEST_RE.search(_read_if_exists(root / "Makefile")):
        return "make test"
    return None


def derive_slots(root: Path, docs_root: str) -> dict[str, str]:
    """Return every slot value derivable from the target tree.

    Keys match the question bank's slot names. Only confidently-derived
    entries appear — absent key means "leave the slot to the interview".
    """
    derived: dict[str, str] = {"project_name": root.resolve().name}
    language = detect_language(root)
    if language:
        derived["primary_language"] = language
    verify = detect_verify_command(root)
    if verify:
        derived["verify_command"] = verify
    if docs_root:
        derived["doc_roots"] = docs_root
    return derived


def record_derived_slots(backend: Any, derived: dict[str, str]) -> list[str]:
    """Record derived values as provisional answers for still-empty slots.

    Existing answers of any status (filled / partial / provisional) are never
    overwritten — derivation only seeds blanks. Returns report lines in the
    adopt-report format.
    """
    by_slot = {question["slot"]: question for question in QUESTIONS}
    slots = backend.get("slots", {})
    lines: list[str] = []
    for slot, value in derived.items():
        question = by_slot.get(slot)
        if question is None or slots.get(slot):
            continue
        record_answer(backend, question, value, source="derived")
        lines.append(
            f"derived: {slot} = {value!r} (provisional — confirm or correct "
            f"via `bootstrap answer {slot} ...`)",
        )
    return lines

# --- engine/contextpack.py ---
"""AgentContextPack generator — index-or-manifest input (Lane B8, spec 2.10).

Generates per-area *context packs* — the curated "what an agent must know to
work in this area" bundles — from a project index. Two input forms are
accepted (design-spec 2.10: the generator meets hosts where they are):

  1. the kit's own ``project.index.json`` (``{"areas": [...]}``, planted by
     the adopt flow as a skeleton), and
  2. a manifest snapshot (``{"subsystems": [...]}``) as produced by a host's
     existing subsystem manifest — mapped onto the same area shape with
     sensible fallbacks.

Each pack is written under ``<state_dir>/contextpacks/`` and opens with the
``NOT SOURCE OF TRUTH`` marker: packs are build artifacts — regenerate them
from the index, never hand-edit them. Pure stdlib; every write goes through
``atomic_write_text``.
"""




_PACK_MARKER = (
    "<!-- NOT SOURCE OF TRUTH — generated by substrate-kit; "
    "regenerate, do not edit. -->"
)

# The list-valued fields of the canonical area shape, in emit order.
_PACK_LIST_KEYS = (
    "binding_docs",
    "source_roots",
    "do_not_create",
    "gates",
    "verification",
)

_PACK_SECTION_TITLES = {
    "binding_docs": "Binding docs",
    "source_roots": "Source roots",
    "do_not_create": "Do-not-create",
    "gates": "Gates",
    "verification": "Verification",
}

_PACK_SLUG_STRIP_RE = re.compile(r"[^a-z0-9._-]")
_PACK_SLUG_SEP_RE = re.compile(r"[\s/\\]+")


def _pack_slug(name: str) -> str:
    """Slugify an area name for its pack filename (spaces/slashes -> dashes)."""
    slug = _PACK_SLUG_SEP_RE.sub("-", name.strip().lower())
    slug = _PACK_SLUG_STRIP_RE.sub("", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "area"


def _pack_as_list(value: object) -> list[str]:
    """Coerce an index field to a list of strings (unknown/missing -> [])."""
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _pack_area(entry: dict) -> dict:
    """Normalise one raw index entry onto the canonical area shape."""
    name = str(entry.get("name") or "").strip() or "unnamed-area"
    folio = entry.get("folio")
    area: dict = {
        "name": name,
        "folio": str(folio).strip() if isinstance(folio, str) else "",
    }
    for key in _PACK_LIST_KEYS:
        area[key] = _pack_as_list(entry.get(key))
    return area


def _pack_from_subsystem(entry: dict) -> dict:
    """Map a manifest-snapshot subsystem entry onto the area shape."""
    mapped = dict(entry)
    if not mapped.get("binding_docs"):
        mapped["binding_docs"] = mapped.get("docs")
    if not mapped.get("source_roots"):
        mapped["source_roots"] = mapped.get("roots")
    return _pack_area(mapped)


def load_pack_index(path: Path) -> list[dict]:
    """Load a pack index from ``path``, accepting both supported forms.

    Detects the form by top-level key: ``{"areas": [...]}`` is the kit's own
    ``project.index.json``; ``{"subsystems": [...]}`` is a host manifest
    snapshot (``docs``/``roots`` map onto ``binding_docs``/``source_roots``).
    Unknown or missing per-entry keys become empty lists. Raises ``ValueError``
    when the document is neither form (a wrong file, not a quiet no-op).
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("areas"), list):
        return [_pack_area(e) for e in data["areas"] if isinstance(e, dict)]
    if isinstance(data, dict) and isinstance(data.get("subsystems"), list):
        return [
            _pack_from_subsystem(e) for e in data["subsystems"] if isinstance(e, dict)
        ]
    msg = f"{path.name}: expected top-level 'areas' or 'subsystems' list"
    raise ValueError(msg)


def _pack_section(title: str, items: list[str]) -> list[str]:
    """Render one pack section as markdown lines (empty section -> no lines)."""
    if not items:
        return []
    return [f"## {title}", "", *(f"- {item}" for item in items), ""]


def _pack_body(root: Path, area: dict) -> str:
    """Compose one pack's full markdown text from a normalised area."""
    lines = [_PACK_MARKER, "", f"# {area['name']} — agent context pack", ""]
    lines += _pack_section("Folio", [area["folio"]] if area["folio"] else [])
    for key in _PACK_LIST_KEYS:
        items = area[key]
        if key == "source_roots":
            items = [
                entry if (root / entry).exists() else f"{entry} (MISSING)"
                for entry in items
            ]
        lines += _pack_section(_PACK_SECTION_TITLES[key], items)
    return "\n".join(lines).rstrip() + "\n"


def generate_packs(root: Path, config: Config, index: list[dict]) -> list[Path]:
    """Write one context pack per index area; return the written paths.

    Packs land in ``<root>/<state_dir>/contextpacks/<slug>.context.md``.
    ``source_roots`` entries are existence-checked against ``root`` and
    suffixed `` (MISSING)`` when absent, so a stale index is visible in the
    pack instead of silently misleading the agent reading it.
    """
    out_dir = root / config.state_dir / "contextpacks"
    written: list[Path] = []
    used: set[str] = set()
    for entry in index:
        area = _pack_area(entry)
        # Two areas whose names slugify alike (``Economy``/``economy``,
        # ``API v1``/``API-v1``, two unnamed areas → ``area``) must not land on
        # one filename: the later ``atomic_write_text`` would silently erase the
        # earlier pack and ``written`` would double-count one file. Disambiguate
        # to the first free ``slug`` / ``slug-2`` / ``slug-3`` … (robust even if
        # a real ``slug-2`` area also exists); the pack body still names its area
        # in the heading, so a suffixed file stays identifiable.
        base = _pack_slug(area["name"])
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        path = out_dir / f"{slug}.context.md"
        atomic_write_text(path, _pack_body(root, area))
        written.append(path)
    return written


def pack_index_skeleton(project_name: str) -> str:
    """Return the planted ``project.index.json`` skeleton (JSON text).

    One example area with every field present-but-empty, plus a ``_comment``
    explaining how each field feeds the AgentContextPack generator
    (index-or-manifest input, design-spec 2.10).
    """
    skeleton = {
        "_comment": (
            "AgentContextPack index (design-spec 2.10). Each `areas` entry "
            "feeds one generated <state_dir>/contextpacks/<name>.context.md: "
            "`name` (the area; slugified into the pack filename), `folio` "
            "(the canonical entry-point doc for the area), `binding_docs` "
            "(authoritative contracts to read first), `source_roots` (key "
            "files/dirs; existence-checked at generation, missing ones "
            "flagged), `do_not_create` (existing systems an agent must not "
            "duplicate), `gates` (currently active expansion conditions), "
            "`verification` (commands to run before pushing). The generator "
            'also accepts a manifest snapshot ({"subsystems": [...]}) '
            "instead of this file."
        ),
        "project": project_name,
        "areas": [
            {
                "name": "example-area",
                "folio": "",
                "binding_docs": [],
                "source_roots": [],
                "do_not_create": [],
                "gates": [],
                "verification": [],
            },
        ],
    }
    return json.dumps(skeleton, indent=2) + "\n"

# --- engine/adopt.py ---
"""One-step adopt flow — plant the workflow docs, stage the packs (Lane B8).

``adopt`` turns a bare host repo into a substrate-governed one in a single
idempotent pass: it renders every content template with the currently filled
interview slots and *plants* the live docs (constitution, contracts, ledgers,
session scaffolding) — **skip-if-exists, never clobbering** a file the host
already owns — then *stages* the ``.claude`` material (working agreement,
skill pack, persona pack, hook wiring, CI example) under ``<state_dir>`` for
the host to install deliberately. Only an explicit ``include_claude=True``
writes a live ``.claude/`` tree, and even then only files that are absent
(the host opt-in stays non-destructive).

Adopt renders what it knows (the Phase-2.5 G2 fix): before rendering, every
deterministically-derivable slot (project name, language, verify command,
docs root — ``engine/derive.py``) is recorded as a provisional interview
answer, and any doc still carrying unfilled ``${slot}`` placeholders is
planted under a loud UNRENDERED banner instead of silently inert — a cold
session sees at a glance which prose is live and which is an unfilled slot.
The guardrail runs first: the kit refuses to adopt into its own tree. Pure
stdlib; every write goes through ``atomic_write_text``.
"""




# Template filename -> planted relpath. CLAUDE.md.tmpl is deliberately absent:
# it is STAGED under <state_dir>/claude/ (the kit never live-writes .claude/
# without the explicit include_claude opt-in).
ADOPT_PLAN: list[tuple[str, str]] = [
    ("CONSTITUTION.md.tmpl", "CONSTITUTION.md"),
    ("decisions.md.tmpl", "docs/decisions.md"),
    ("architecture.md.tmpl", "docs/architecture.md"),
    ("ownership.md.tmpl", "docs/ownership.md"),
    ("runtime_contracts.md.tmpl", "docs/runtime_contracts.md"),
    ("repo-navigation-map.md.tmpl", "docs/repo-navigation-map.md"),
    ("helper-policy.md.tmpl", "docs/helper-policy.md"),
    ("collaboration-model.md.tmpl", "docs/collaboration-model.md"),
    ("ai-project-workflow.md.tmpl", "docs/ai-project-workflow.md"),
    ("owner-profile.md.tmpl", "docs/owner-profile.md"),
    ("AGENT_ORIENTATION.md.tmpl", "docs/AGENT_ORIENTATION.md"),
    ("current-state.md.tmpl", "docs/current-state.md"),
    ("question-router.md.tmpl", "docs/question-router.md"),
    ("ideas-README.md.tmpl", "docs/ideas/README.md"),
    ("session-journal.md.tmpl", ".session-journal.md"),
]

_ADOPT_NEXT_STEPS = (
    "next steps: run `bootstrap ask` to see the pending interview questions, "
    "answer them and fill the planted docs in place (`bootstrap render --live`), and set "
    "the integration mode with `bootstrap mode <observe|guided|active>`."
)

# First line doubles as the removal marker `strip_unrendered_banner` keys off.
UNRENDERED_BANNER_FIRST_LINE = (
    "> ⚠️ **UNRENDERED SLOTS BELOW — run `python3 bootstrap.py ask`.**"
)
_UNRENDERED_BANNER = (
    UNRENDERED_BANNER_FIRST_LINE + "\n"
    "> Every `${...}` token in this file is an unfilled interview slot, not\n"
    "> project truth. Fill: `bootstrap answer <slot> <value...>`, then\n"
    "> `bootstrap render --live` (fills in place and removes this banner).\n"
    "> Prose without `${...}` tokens is live guidance already.\n\n"
)


def with_unrendered_banner(text: str) -> str:
    """Prepend the loud UNRENDERED banner when ``text`` has unfilled slots.

    An inert-looking doc was the measured Phase-2.5 failure mode: raw
    ``${...}`` placeholders read as non-actionable scaffolding and only cost
    orientation. The banner names what the tokens are and the exact two
    commands that fill them; a fully-rendered doc gets no banner.
    """
    if not find_placeholders(text):
        return text
    return _UNRENDERED_BANNER + text


def strip_unrendered_banner(text: str) -> str:
    """Remove the adopt-time banner (used once a file has no placeholders)."""
    if not text.startswith(UNRENDERED_BANNER_FIRST_LINE):
        return text
    lines = text.split("\n")
    index = 0
    while index < len(lines) and lines[index].startswith(">"):
        index += 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    return "\n".join(lines[index:])


def _vendor_bootstrap(root: Path, report: list[str]) -> str:
    """Vendor the running single-file bootstrap into ``root``; return hook path.

    The staged hook commands run ``<interpreter> bootstrap.py hook <event>``
    relative to the host repo root — in the Phase-2.5 A/B the file was never
    there, so every staged hook pointed outside the target repo (the second
    G2 failure cause). When adopt runs *as* the single-file ``bootstrap.py``,
    copy it to the target root (skip-if-exists, like every plant) so those
    commands resolve. Running from the source/pip layout there is no single
    file to vendor: fall back to an existing root copy, else the absolute
    path of the running entry point, else the documented bare-name contract
    (the hooks README fill-table row covers relocation).
    """
    at_root = root / "bootstrap.py"
    entry = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] else None
    is_bootstrap_entry = (
        entry is not None and entry.name == "bootstrap.py" and entry.is_file()
    )
    if not at_root.exists() and is_bootstrap_entry and entry != at_root:
        _adopt_plant(
            at_root,
            "bootstrap.py",
            entry.read_text(encoding="utf-8"),
            report,
        )
    if at_root.exists():
        return "bootstrap.py"
    if is_bootstrap_entry:
        return str(entry)
    return "bootstrap.py"


def _adopt_dest(relpath: str, config: Config) -> str:
    """Remap the plan's ``docs/`` prefix onto the host's configured docs root."""
    prefix = "docs/"
    if relpath.startswith(prefix) and config.docs_root != "docs":
        return f"{config.docs_root}/{relpath[len(prefix) :]}"
    return relpath


def _adopt_plant(path: Path, relpath: str, text: str, report: list[str]) -> None:
    """Write ``text`` at ``path`` unless it exists; report planted/kept."""
    if path.exists():
        report.append(f"kept: {relpath}")
        return
    atomic_write_text(path, text)
    report.append(f"planted: {relpath}")


def _adopt_stage(path: Path, relpath: str, text: str, report: list[str]) -> None:
    """Write a staged (generated, regenerable) artifact and report it."""
    atomic_write_text(path, text)
    report.append(f"staged: {relpath}")


def _adopt_sessions_readme(markers: list[dict[str, str]]) -> str:
    """Compose the one-paragraph ``.sessions/README.md`` (born-red convention)."""
    labels = ", ".join(m.get("label", "") for m in markers if m.get("label"))
    labels = labels or "(no markers configured)"
    return (
        "# Session logs\n\n"
        "Per-session logs live here as `<date>-<slug>.md`, newest first. "
        "Create the log as the session's FIRST commit with a born-red status "
        "(`> **Status:** `in-progress``) so in-flight work is visible to "
        "parallel sessions, then flip it to `complete` as the deliberate LAST "
        "step once the close-out is written — a half-done session never reads "
        "as finished. Before it counts as complete, a log must carry these "
        f"markers: {labels}.\n"
    )


def ci_snippet() -> str:
    """Return the staged, fully-commented GitHub-Actions-style CI example.

    Everything is commented out: the host copies it into
    ``.github/workflows/`` and uncomments/adjusts deliberately — the kit never
    installs live CI.
    """
    return (
        "# Example GitHub-Actions-style quality gate for a substrate-kit host.\n"
        "# Copy into .github/workflows/, uncomment, and adjust the interpreter\n"
        "# and bootstrap path to match your repo.\n"
        "#\n"
        "# `bootstrap.py check --strict` runs every kit checker in one pass:\n"
        "# docs hygiene (badges / links / reachability), session-log markers,\n"
        "# namespace shadowing, seam authority, orientation budget, and the\n"
        "# decision ledger.\n"
        "#\n"
        "# name: substrate-quality\n"
        "# on:\n"
        "#   pull_request:\n"
        "#   push:\n"
        "#     branches: [main]\n"
        "# jobs:\n"
        "#   substrate-check:\n"
        "#     runs-on: ubuntu-latest\n"
        "#     steps:\n"
        "#       - uses: actions/checkout@v4\n"
        "#       - name: substrate checks\n"
        "#         run: python3 bootstrap.py check --strict\n"
    )


LIVE_CI_RELPATH = ".github/workflows/substrate-gate.yml"


def live_ci_workflow(interpreter: str = "python3") -> str:
    """Return the LIVE (uncommented) CI gate workflow — the locked door.

    Unlike :func:`ci_snippet` (a commented example the host installs by hand),
    this is a working GitHub-Actions workflow ``adopt --wire-enforcement``
    writes into ``.github/workflows/``. It runs
    ``bootstrap.py check --strict --require-session-log`` on every pull request,
    so the merge is **held red** until the session's journal is written and the
    whole hygiene suite passes. This is the forcing function that makes the
    memory ritual non-optional: a nag can be ignored, a failing required check
    cannot. `fetch-depth: 0` gives the checkout full history (the gate itself is
    git-free, but hosts commonly extend this workflow with diff-aware steps).
    A docs-only or bot PR that shouldn't need a session card is handled by the
    host adding a `paths-ignore:` or a label carve-out — kept strict by default
    on purpose (the discipline is the point).
    """
    return (
        "# substrate-kit enforcement gate (LIVE — installed by "
        "`bootstrap.py adopt --wire-enforcement`).\n"
        "# Holds the merge red until the session journal is written and every\n"
        "# hygiene check passes. Edit `paths-ignore` / add a label carve-out if\n"
        "# some PRs legitimately need no session card.\n"
        "name: substrate-gate\n"
        "on:\n"
        "  pull_request:\n"
        "  push:\n"
        "    branches: [main]\n"
        "jobs:\n"
        "  substrate-gate:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "        with:\n"
        "          fetch-depth: 0\n"
        "      - uses: actions/setup-python@v5\n"
        "        with:\n"
        '          python-version: "3.x"\n'
        "      - name: substrate gate (docs + session-log required)\n"
        f"        run: {interpreter} bootstrap.py check --strict --require-session-log\n"
    )


def adopt(
    root: Path,
    config: Config,
    backend: Any,
    *,
    kit_root: Path,
    include_claude: bool = False,
    wire_enforcement: bool = False,
) -> list[str]:
    """Adopt the substrate workflow into ``root``; return the report lines.

    Steps (all idempotent): (0) guardrail — refuse the kit's own tree; then
    derive what the tree can tell us (provisional slots) and vendor the
    single-file bootstrap so hook commands resolve in-repo;
    (1) plant every ``ADOPT_PLAN`` doc rendered from the current slots —
    skip-if-exists, unrendered docs bannered; (2) plant
    ``<sessions_dir>/README.md``; (3) plant the ``project.index.json``
    skeleton; (4) stage the ``.claude`` material (CLAUDE.md, skills,
    personas, hook settings + fill-table README) under ``<state_dir>``;
    (5) stage the CI example; (6) with ``include_claude``, additionally
    write ``.claude/CLAUDE.md`` + ``.claude/settings.json`` if absent;
    (7) close with the next-steps line.

    ``wire_enforcement`` turns on the two **forcing functions** that make the
    memory ritual actually get used (the Phase-2.5 re-run showed docs alone get
    read but not written back): it implies ``include_claude`` (the live Stop-hook
    **nag**) **and** plants a live CI workflow (:data:`LIVE_CI_RELPATH`) running
    the ``--require-session-log`` gate — the **locked door** that holds a merge
    red until the journal is written. Kept opt-in: the kit still never installs
    executable CI/hooks silently (the deliberate safety default), but a host —
    or the rebuild's K0 session — flips this on to reproduce the enforcement
    this repo's discipline actually runs on.
    """
    include_claude = include_claude or wire_enforcement
    assert_safe_target(root, kit_root)
    templates = load_templates()
    report: list[str] = []

    # (0b) Adopt renders what it knows: seed derivable slots (provisional,
    # never overwriting an existing answer), then build the render context.
    report.extend(record_derived_slots(backend, derive_slots(root, config.docs_root)))
    bootstrap_path = _vendor_bootstrap(root, report)
    context = build_context(backend.data)
    # The live integration mode is state, not a slot — render it truthfully.
    context.setdefault("integration_mode", str(backend.get("mode", "guided")))

    # (1) Plant the live docs — never clobber; a doc with unfilled ${slots}
    # is planted under the loud UNRENDERED banner (visible, never inert).
    for template_name, plan_rel in ADOPT_PLAN:
        rel = _adopt_dest(plan_rel, config)
        text = render(templates[template_name], context)
        if template_name == "decisions.md.tmpl":
            # The example D-0001 records THIS adoption — stamp the real date so
            # the planted ledger is check_ledger-clean from its first commit.
            text = text.replace("- date:\n", f"- date: {date.today().isoformat()}\n")
        _adopt_plant(root / rel, rel, with_unrendered_banner(text), report)

    # (2) Session-log scaffolding.
    sessions_rel = f"{config.sessions_dir}/README.md"
    readme = _adopt_sessions_readme(config.session_markers)
    _adopt_plant(root / config.sessions_dir / "README.md", sessions_rel, readme, report)

    # (3) The context-pack index skeleton.
    project_name = context.get("project_name") or root.name
    skeleton = pack_index_skeleton(project_name)
    _adopt_plant(root / "project.index.json", "project.index.json", skeleton, report)

    # (4) Stage the .claude material under <state_dir> (regenerated each run).
    state_base = root / config.state_dir
    claude_doc = with_unrendered_banner(render(templates["CLAUDE.md.tmpl"], context))
    claude_rel = f"{config.state_dir}/claude/CLAUDE.md"
    _adopt_stage(state_base / "claude" / "CLAUDE.md", claude_rel, claude_doc, report)
    for skill in SKILLS:
        rel = skill_relpath(skill)
        body = render(skill["body"], context)
        document = skill_document(skill, body)
        _adopt_stage(state_base / rel, f"{config.state_dir}/{rel}", document, report)
    for agent in AGENTS:
        rel = agent_relpath(agent)
        body = render(agent["body"], context)
        document = agent_document(agent, body)
        _adopt_stage(state_base / rel, f"{config.state_dir}/{rel}", document, report)
    settings_text = full_settings_template(config, bootstrap_path=bootstrap_path)
    settings_rel = f"{config.state_dir}/hooks/settings.template.json"
    settings_path = state_base / "hooks" / "settings.template.json"
    _adopt_stage(settings_path, settings_rel, settings_text, report)
    hooks_readme_rel = f"{config.state_dir}/hooks/README.md"
    hooks_readme = hooks_fill_table()
    _adopt_stage(
        state_base / "hooks" / "README.md",
        hooks_readme_rel,
        hooks_readme,
        report,
    )

    # (5) Stage the CI example.
    ci_rel = f"{config.state_dir}/ci/quality.yml.example"
    _adopt_stage(
        state_base / "ci" / "quality.yml.example",
        ci_rel,
        ci_snippet(),
        report,
    )

    # (6) Explicit host opt-in: live .claude/ (still never overwrites).
    if include_claude:
        claude_dir = root / ".claude"
        _adopt_plant(claude_dir / "CLAUDE.md", ".claude/CLAUDE.md", claude_doc, report)
        _adopt_plant(
            claude_dir / "settings.json",
            ".claude/settings.json",
            settings_text,
            report,
        )

    # (6b) Enforcement opt-in: the LIVE CI gate (the locked door). include_claude
    # above already wired the live nag; this adds the required check that a
    # missing journal can never merge past.
    if wire_enforcement:
        _adopt_plant(
            root / LIVE_CI_RELPATH,
            LIVE_CI_RELPATH,
            live_ci_workflow(config.interpreter_for_checks or "python3"),
            report,
        )

    # (7) Point the adopter at the interview loop.
    report.append(_ADOPT_NEXT_STEPS)
    return report

# --- engine/cli.py ---
"""The substrate-kit bootstrap command line.

Surface: ``init`` (idempotent), ``status``, ``mode <name>``, ``stance [name]``
(show or set the task stance), ``ask`` (list the pending interview questions),
``answer`` / ``confirm`` (fill / confirm a slot), ``render`` (write content
docs), ``skills`` / ``agents`` / ``hooks`` (list / ``--build`` the packs),
``hook <event>`` (the runtime hook entry points), ``check`` (every hygiene
checker), ``triggers``, ``reflect``, ``episodes``, ``metrics``, ``maintain``,
``review`` (the independent-review seam), ``economy`` (the context-economy
engine), ``ledger`` (the [D-NNNN] decisions ledger), and ``--simulate N
[--mode m]`` (the CI / proving smoke that drives the staged interview and
asserts per-mode behavior). Output goes through ``_emit`` (``sys.stdout.write``)
rather than ``print`` to keep the engine lint-clean.
"""





def _emit(line: str = "") -> None:
    """Write a line to stdout (avoids the print() lint ban in engine code)."""
    sys.stdout.write(line + "\n")


def _kit_root() -> Path:
    """Return the tree the guardrail protects (the kit's own checkout).

    Only the source layout (``.../src/engine/cli.py``) has a kit tree to
    protect: there, the checkout root is ``parents[2]``. Running as the
    copied single-file bootstrap or a pip install, this returns the module
    file itself — a *file* matches no target directory, so the guardrail
    never engages (there is no kit tree). The old unconditional
    ``parents[2]`` made the dist's guardrail root the grandparent of the
    user's repo, refusing EVERY real ``adopt``/``init`` outside the temp
    tree — the documented primary flow.
    """
    here = Path(__file__).resolve()
    if here.parent.name == "engine" and here.parent.parent.name == "src":
        return here.parents[2]
    return here


def _state_path(root: Path, config: Config) -> Path:
    """Return the state-file path under a project ``root``."""
    return root / config.state_dir / "state.json"


def cmd_init(target: Path) -> int:
    """Create config + state under ``target`` if absent; never clobber."""
    assert_safe_target(target, _kit_root())
    target.mkdir(parents=True, exist_ok=True)
    if config_path(target).exists():
        config = load_config(target)
    else:
        config = Config()
        save_config(target, config)
    state_path = _state_path(target, config)
    if state_path.exists():
        _emit(f"init: already initialised at {target} (idempotent no-op).")
        return 0
    backend = JsonStateBackend(state_path)
    with backend.transaction():
        for key, value in default_state(config.project_id).items():
            backend.set(key, value)
    _emit(f"init: created {state_path} (project_id={config.project_id}).")
    return 0


def cmd_status(target: Path) -> int:
    """Print a one-screen summary of the install's state."""
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    data = backend.data
    if not data:
        _emit(f"status: no state at {target} (run init first).")
        return 1
    _emit(f"project_id : {data.get('project_id')}")
    _emit(f"stage      : {data.get('stage')}")
    _emit(f"mode       : {data.get('mode')}")
    _emit(f"stance     : {data.get('stance')}")
    _emit(f"sessions   : {data.get('session_count')}")
    return 0


def cmd_mode(target: Path, name: str) -> int:
    """Set the integration mode (observe | guided | active)."""
    valid = ("observe", "guided", "active")
    if name not in valid:
        _emit(f"mode: invalid mode {name!r} (choose from {list(valid)}).")
        return 2
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    if not backend.data:
        _emit(f"mode: no state at {target} (run init first).")
        return 1
    history = list(backend.get("mode_history", []))
    history.append(
        {
            "mode": name,
            "session": int(backend.get("session_count", 0)),
            "date": date.today().isoformat(),
        },
    )
    with backend.transaction():
        backend.set("mode", name)
        backend.set("mode_history", history)
    _emit(f"mode: set to {name} (audit trail: {len(history)} switch(es)).")
    return 0


def cmd_stance(target: Path, name: str | None) -> int:
    """Show or set the active task stance (question|analysis|debug|review|plan).

    With no ``name``, prints the active stance's briefing (reading-route +
    tool-scope + output contract) and the available set. With a ``name``, switches
    the active stance in state. The stance is advisory — it scopes orientation, it
    does not block actions.
    """
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    if not backend.data:
        _emit(f"stance: no state at {target} (run init first).")
        return 1
    if name is None:
        active = backend.data.get("stance", DEFAULT_STANCE)
        _emit(stance_briefing(active))
        _emit(f"  available: {', '.join(stance_names())}")
        return 0
    if name not in stance_names():
        _emit(f"stance: invalid stance {name!r} (choose from {stance_names()}).")
        return 2
    backend.set("stance", name)
    _emit(f"stance: set to {name}.")
    _emit(stance_briefing(name))
    return 0


def cmd_ask(target: Path) -> int:
    """List the interview's currently pending questions."""
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    if not backend.data:
        _emit(f"ask: no state at {target} (run init first).")
        return 1
    pending = pending_questions(backend.data)
    if not pending:
        _emit("ask: no pending questions — all slots filled.")
        return 0
    asked = session_questions(backend.data)
    _emit(f"ask: {len(asked)} question(s) this session (mode quota):")
    for question in asked:
        _emit(
            f"  [{question['id']}] "
            f"({question['audience']}/{question['priority']}) {question['prompt']}",
        )
    remaining = len(pending) - len(asked)
    if remaining > 0:
        _emit(f"  (+{remaining} more later — the mode paces the interview)")
    return 0


def _render_live(target: Path, context: dict[str, str]) -> int:
    """Fill remaining ``${slot}`` placeholders in the PLANTED docs, in place.

    Placeholders survive verbatim in a planted file until their slot fills, so
    substituting over the live text updates exactly the newly-answered slots
    while preserving every hand edit around them. Returns the leftover count.
    """
    leftover_total = 0
    for _, plan_rel in ADOPT_PLAN:
        rel = _adopt_dest(plan_rel, load_config(target))
        path = target / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        filled = render(text, context)
        leftover = find_placeholders(filled)
        leftover_total += len(leftover)
        if not leftover:
            # Fully rendered — the adopt-time UNRENDERED banner has done its job.
            filled = strip_unrendered_banner(filled)
        if filled != text:
            atomic_write_text(path, filled)
            suffix = f" ({len(leftover)} slot(s) still unfilled)" if leftover else ""
            _emit(f"render: filled {rel}{suffix}")
    _emit(f"render: {leftover_total} unfilled placeholder(s) across planted docs.")
    return 0


def cmd_render(target: Path, live: bool = False) -> int:
    """Render the content docs from the current filled slots.

    Default: stage fresh renders of every template into
    ``<state_dir>/rendered/``. With ``live``: fill remaining placeholders in
    the *planted* docs in place (hand edits preserved) — the post-interview
    "make the live docs catch up" pass.
    """
    assert_safe_target(target, _kit_root())
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    if not backend.data:
        _emit(f"render: no state at {target} (run init first).")
        return 1
    context = build_context(backend.data)
    if live:
        return _render_live(target, context)
    out_dir = target / config.state_dir / "rendered"
    leftover_total = 0
    for name, text in load_templates().items():
        rendered = render(text, context)
        leftover = find_placeholders(rendered)
        leftover_total += len(leftover)
        out_name = name[:-5] if name.endswith(".tmpl") else name
        atomic_write_text(out_dir / out_name, rendered)
        suffix = f" ({len(leftover)} slot(s) unfilled)" if leftover else ""
        _emit(f"render: wrote {out_name}{suffix}")
    _emit(f"render: {leftover_total} unfilled placeholder(s) total.")
    return 0


def cmd_skills(target: Path, build: bool) -> int:
    """List the skill pack, or ``--build`` it into ``<state_dir>/skills/``.

    Listing shows each skill + its declared capabilities (what it may do beyond
    read, overriding the ambient stance). Building emits a native ``SKILL.md`` per
    skill into the staging area, body slot-filled from the interview — the host
    then installs them under ``.claude/skills/``. Like ``render``, the kit stages;
    it never writes a live ``.claude/`` tree.
    """
    config = load_config(target)
    if build:
        assert_safe_target(target, _kit_root())
    if not build:
        _emit("skills:")
        for skill in SKILLS:
            caps = ", ".join(skill_capabilities(skill["name"]))
            _emit(f"  {skill['name']} — {skill['description']}")
            _emit(f"    capabilities: {caps}")
        return 0
    backend = JsonStateBackend(_state_path(target, config))
    context = build_context(backend.data) if backend.data else {}
    out_base = target / config.state_dir
    leftover_total = 0
    for skill in SKILLS:
        body = render(skill["body"], context)
        leftover = find_placeholders(body)
        leftover_total += len(leftover)
        atomic_write_text(out_base / skill_relpath(skill), skill_document(skill, body))
        suffix = f" ({len(leftover)} slot(s) unfilled)" if leftover else ""
        _emit(f"skills: wrote {skill_relpath(skill)}{suffix}")
    _emit(f"skills: {len(SKILLS)} skill(s), {leftover_total} unfilled placeholder(s).")
    return 0


def cmd_agents(target: Path, build: bool) -> int:
    """List the persona pack, or ``--build`` it into ``<state_dir>/agents/``.

    Listing shows each persona + its description. Building emits a native
    ``.claude/agents``-style ``<name>.md`` per persona into the staging area, body
    slot-filled from the project's contract slots — the host then installs them
    under ``.claude/agents/``. Like ``render``/``skills``, the kit stages; it never
    writes a live ``.claude/`` tree.
    """
    config = load_config(target)
    if build:
        assert_safe_target(target, _kit_root())
    if not build:
        _emit("agents:")
        for agent in AGENTS:
            _emit(f"  {agent['name']} — {agent['description']}")
        return 0
    backend = JsonStateBackend(_state_path(target, config))
    context = build_context(backend.data) if backend.data else {}
    out_base = target / config.state_dir
    leftover_total = 0
    for agent in AGENTS:
        body = render(agent["body"], context)
        leftover = find_placeholders(body)
        leftover_total += len(leftover)
        atomic_write_text(out_base / agent_relpath(agent), agent_document(agent, body))
        suffix = f" ({len(leftover)} slot(s) unfilled)" if leftover else ""
        _emit(f"agents: wrote {agent_relpath(agent)}{suffix}")
    count = len(AGENTS)
    _emit(f"agents: {count} persona(s), {leftover_total} unfilled placeholder(s).")
    return 0


def _hook_command(config: Config) -> str:
    """Return the shell command Claude Code runs for the PreToolUse guard."""
    return f"{config.interpreter} bootstrap.py hook pretooluse"


def cmd_hooks(target: Path, build: bool) -> int:
    """Show the hook wiring, or ``--build`` the settings files into staging.

    Four hooks: the **PreToolUse stance guard**, **SessionStart orientation**,
    the **PostToolUse edit advisor**, and the **Stop-check advisor**. Building
    stages the PreToolUse snippet, the full four-event
    ``settings.template.json``, and the fill-table README into
    ``<state_dir>/hooks/`` — the host merges them into their own settings
    (adjusting the bootstrap path). Like the other emitters, the kit stages;
    it never writes a live ``.claude/`` tree.
    """
    config = load_config(target)
    if build:
        assert_safe_target(target, _kit_root())
    command = _hook_command(config)
    if not build:
        _emit("hooks:")
        _emit("  pretooluse   — stance guard: warns on an out-of-stance tool.")
        _emit("  sessionstart — prints the mode-aware orientation injection.")
        _emit("  postedit     — warns on generated-artifact / unbadged-doc edits.")
        _emit("  stopcheck    — session-close advisories (log, questions, cadence).")
        _emit(f"  wiring command: {command}")
        return 0
    out = target / config.state_dir / "hooks" / "settings.snippet.json"
    atomic_write_text(out, settings_snippet(command))
    tmpl = target / config.state_dir / "hooks" / "settings.template.json"
    atomic_write_text(tmpl, full_settings_template(config))
    atomic_write_text(
        target / config.state_dir / "hooks" / "README.md",
        hooks_fill_table(),
    )
    _emit(f"hooks: wrote {out.relative_to(target)}")
    _emit(f"hooks: wrote {tmpl.relative_to(target)} (all four events) + README.md")
    _emit("hooks: merge the hook blocks into .claude/settings.json yourself.")
    return 0


def _hook_pretooluse(target: Path) -> int:
    """PreToolUse stance guard: warn on stderr for an out-of-stance tool."""
    tool_name = tool_from_payload(sys.stdin.read())
    if not tool_name:
        return 0
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    stance = backend.data.get("stance") if backend.data else None
    if not stance:
        return 0
    warning = evaluate_tool(stance, tool_name)
    if warning:
        sys.stderr.write(warning + "\n")
    return 0


def _hook_sessionstart(target: Path) -> int:
    """SessionStart: print the mode-aware orientation composition to stdout."""
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    text = compose_orientation(target, config, backend)
    if text:
        sys.stdout.write(text)
    return 0


def _hook_postedit(target: Path) -> int:
    """PostToolUse: warn on stderr for a generated-artifact / unbadged-doc edit.

    Handles Edit/Write (``tool_input.file_path``) and NotebookEdit
    (``tool_input.notebook_path``) — the three tools the settings matcher wires.
    A NotebookEdit carries ``notebook_path``, not ``file_path``, so keying only
    on the latter matched notebook edits but never advised them (the matcher
    over-advertised its coverage).
    """
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    if not isinstance(tool_input, dict):
        return 0
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(file_path, str) or not file_path:
        return 0
    warning = evaluate_edit(target, load_config(target), file_path)
    if warning:
        sys.stderr.write(warning + "\n")
    return 0


def _hook_stopcheck(target: Path) -> int:
    """Stop: print the session-close advisory lines to stderr."""
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    for line in evaluate_stop(target, config, backend):
        sys.stderr.write(line + "\n")
    return 0


_HOOK_EVENTS = {
    "pretooluse": _hook_pretooluse,
    "sessionstart": _hook_sessionstart,
    "postedit": _hook_postedit,
    "stopcheck": _hook_stopcheck,
}


def cmd_hook(target: Path, event: str) -> int:
    """Run a Claude Code hook entry point (all advisory — always exit 0).

    ``pretooluse`` warns on an out-of-stance tool; ``sessionstart`` prints the
    orientation injection to stdout; ``postedit`` reads the PostToolUse stdin
    payload (``tool_input.file_path``) and warns on stderr; ``stopcheck``
    prints session-close advisories to stderr. Every event fails open on a
    missing / malformed payload, config, or state.
    """
    handler = _HOOK_EVENTS.get(event)
    if handler is None:
        return 0
    try:
        return handler(target)
    except Exception:  # noqa: BLE001 — hooks fail open by contract, always 0
        return 0


def _extra_check_findings(target: Path, config: Config) -> list:
    """Run the configured non-doc checkers (ledger, namespace, seams, budget).

    Each checker engages only when its inputs exist — an un-adopted project
    with no ledger, no namespace roots, no seams, and no boot docs runs none of
    them, so ``check`` stays meaningful before onboarding.
    """
    findings: list = []
    ledger_path = target / config.docs_root / LEDGER_FILENAME
    if ledger_path.exists():
        findings += check_ledger(ledger_path)
        findings += check_stamp_discipline(target / config.docs_root, ledger_path)
    roots = [target / r for r in config.namespace.get("roots", [])]
    roots = [r for r in roots if r.exists()]
    if roots:
        findings += check_namespace(
            roots,
            reserved=config.namespace.get("reserved") or None,
        )
    if config.seams:
        findings += check_seam_authority(target, config.seams)
    boot_docs = config.orientation.get("boot_docs") or config.readpath_docs
    docs_root = target / config.docs_root
    if any((docs_root / doc).exists() or (target / doc).exists() for doc in boot_docs):
        findings += check_orientation_budget(target, config)
    return findings


def cmd_check(
    target: Path,
    strict: bool,
    *,
    require_session_log: bool = False,
) -> int:
    """Run every hygiene checker against ``target``.

    Docs (badge/link/reachable), the decisions ledger + stamp discipline, the
    namespace/shadowing guard, the seam-authority fences, and the orientation
    word budget — each engaging only when its inputs exist. Findings always
    count toward the exit code (under ``--strict``); an *incomplete* existing
    session log counts. A *missing* session log is **advisory by default** (a
    host may run ``check`` mid-session) but becomes a **hard failure** under
    ``require_session_log`` — the gate mode the live CI workflow runs, so a
    session that never writes its journal cannot merge (the "locked door" that
    makes the memory ritual non-optional, not merely advised). Uses config
    defaults if ``target`` has no ``substrate.config.json`` yet, so a project
    can lint before onboarding.
    """
    config = load_config(target)
    docs_root = target / config.docs_root
    doc_findings = run_doc_checks(
        docs_root,
        config.badge_tokens,
        config.readpath_docs,
    )
    doc_findings = list(doc_findings) + _extra_check_findings(target, config)
    if doc_findings:
        _emit(f"check: {len(doc_findings)} finding(s):")
        for finding in doc_findings:
            _emit(f"  [{finding.kind}] {finding.path}: {finding.message}")

    log = latest_session_log(target / config.sessions_dir)
    log_missing: list[str] = check_log(log, config.session_markers) if log else []
    # In gate mode an absent log is itself a failing condition, so it must feed
    # the exit code exactly like an incomplete one.
    log_absent_fails = log is None and require_session_log
    if log is None:
        if require_session_log:
            _emit(
                f"check: MERGE HELD — no session log under {config.sessions_dir}/ "
                "(--require-session-log): write one before merging.",
            )
        else:
            _emit("check: no session log found yet (advisory — not a failure).")
    else:
        rel = log.relative_to(target) if log.is_relative_to(target) else log
        if log_missing:
            _emit(f"check: session log {rel} is missing: {', '.join(log_missing)}")
        else:
            _emit(f"check: session log {rel} complete.")

    if not doc_findings and not log_missing and not log_absent_fails:
        _emit("check: all checks passed.")
        return 0
    return 1 if strict else 0


def _require_state(
    target: Path,
    command: str,
) -> tuple[Config, JsonStateBackend] | None:
    """Load config + state; None (with a message) when the install is missing.

    Also runs the live-loop guardrail: state-backed commands read AND write
    the install, and only ``init``/``adopt`` were guarded before — ``ledger``,
    the ``--build`` emitters, and ``episodes --rebuild`` wrote into a target
    the guardrail would have refused.
    """
    assert_safe_target(target, _kit_root())
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    if not backend.data:
        _emit(f"{command}: no state at {target} (run init first).")
        return None
    return config, backend


def _question_for_slot(slot: str) -> dict | None:
    """Return the bank question that fills ``slot`` (None when unknown)."""
    for question in QUESTIONS:
        if question["slot"] == slot:
            return question
    return None


def cmd_answer(target: Path, slot: str, answer: str) -> int:
    """Record a user answer for ``slot`` (fills it, resolves its escalation)."""
    loaded = _require_state(target, "answer")
    if loaded is None:
        return 1
    _, backend = loaded
    question = _question_for_slot(slot)
    if question is None:
        known = ", ".join(q["slot"] for q in QUESTIONS)
        _emit(f"answer: unknown slot {slot!r} (known: {known}).")
        return 2
    record_answer(backend, question, answer, source="user")
    status = backend.get("slots", {}).get(slot)
    _emit(f"answer: {slot} -> {status}.")
    if status == "partial":
        floor = int(question.get("min_len", 1))
        _emit(f"answer: too thin to count (needs >= {floor} chars of substance).")
    return 0


def cmd_confirm(target: Path, slot: str) -> int:
    """Confirm a provisional (self-answered) slot as user-verified."""
    loaded = _require_state(target, "confirm")
    if loaded is None:
        return 1
    _, backend = loaded
    if confirm_slot(backend, slot, source="user"):
        _emit(f"confirm: {slot} confirmed (provisional -> filled).")
        return 0
    _emit(f"confirm: {slot} is not provisional (nothing to confirm).")
    return 1


def cmd_triggers(target: Path) -> int:
    """Scan for fired triggers and show the mandated / advisory questions."""
    loaded = _require_state(target, "triggers")
    if loaded is None:
        return 1
    config, backend = loaded
    triggers = check_triggers(target, config, backend.data)
    if not triggers:
        _emit("triggers: none fired.")
        return 0
    questions = mandatory_questions(triggers)
    block = trigger_block(
        triggers,
        questions,
        mandate=triggers_mandate(backend.data),
    )
    _emit(block)
    return 0


def cmd_reflect(
    target: Path,
    *,
    add: str | None,
    evidence: str,
    tags: str,
    mine: bool,
) -> int:
    """List, add to, or mine the forward reflection buffer."""
    loaded = _require_state(target, "reflect")
    if loaded is None:
        return 1
    config, backend = loaded
    path = target / config.state_dir / REFLECTIONS_FILENAME
    buffer_size = int(config.reflection.get("buffer_size", 5))
    if add is not None:
        entry = add_reflection(
            path,
            lesson=add,
            evidence=evidence,
            tags=[t for t in tags.split(",") if t],
            buffer_size=buffer_size,
        )
        _emit(f"reflect: added {entry['id']}.")
    if mine:
        known = {e.get("lesson", "") for e in load_reflections(path)}
        candidates = [
            c
            for c in mine_reflections(target / config.sessions_dir)
            if c["lesson"] not in known
        ]
        for cand in candidates:
            entry = add_reflection(
                path,
                lesson=cand["lesson"],
                evidence=cand.get("evidence", ""),
                tags=list(cand.get("tags", [])),
                buffer_size=buffer_size,
            )
            known.add(cand["lesson"])
            _emit(f"reflect: mined {entry['id']} — {cand['lesson'][:60]}")
        if not candidates:
            _emit("reflect: mined nothing new.")
    entries = load_reflections(path)
    backend.set(
        "reflection_buffer",
        {
            "active_count": len(entries),
            "last_mined": (
                date.today().isoformat()
                if mine
                else (backend.get("reflection_buffer", {}) or {}).get("last_mined")
            ),
        },
    )
    block = lessons_block(entries)
    _emit(block if block else "reflect: buffer empty.")
    return 0


def cmd_episodes(target: Path, *, rebuild: bool, search: str | None) -> int:
    """Rebuild or search the episodic index over the session logs."""
    config = load_config(target)
    if rebuild:
        assert_safe_target(target, _kit_root())
    index_path = target / config.state_dir / EPISODIC_INDEX_FILENAME
    if rebuild:
        entries = rebuild_episodic_index(target / config.sessions_dir, index_path)
        _emit(f"episodes: indexed {len(entries)} session(s).")
    if search is not None:
        hits = search_episodes(index_path, search)
        for hit in hits:
            _emit(
                f"  {hit.get('date', '?')} {hit.get('slug', '?')} — "
                f"{hit.get('summary', '')}",
            )
        _emit(f"episodes: {len(hits)} hit(s) for {search!r}.")
    if not rebuild and search is None:
        _emit("episodes: pass --rebuild and/or --search TAG.")
    return 0


def cmd_metrics(target: Path) -> int:
    """Emit the router / workflow KPIs (JSON + the one-line footer)."""
    loaded = _require_state(target, "metrics")
    if loaded is None:
        return 1
    config, backend = loaded
    kpis = workflow_kpis(backend.data, target / config.sessions_dir)
    _emit(json.dumps(kpis, indent=2, sort_keys=True))
    _emit(kpi_footer(kpis))
    return 0


def cmd_maintain(target: Path, *, compact: bool) -> int:
    """Run the self-maintenance loop's report (and compaction when asked)."""
    loaded = _require_state(target, "maintain")
    if loaded is None:
        return 1
    config, backend = loaded
    if compact:
        if compaction_due(backend.data, dict(config.cadence or {})):
            path = run_compaction(target, config, backend)
            rel = path.relative_to(target) if path.is_relative_to(target) else path
            _emit(f"maintain: compaction written -> {rel}")
        else:
            _emit("maintain: compaction not due.")
    triggers = check_triggers(target, config, backend.data)
    economy = economy_check(target, config)
    ledger_path = target / config.docs_root / LEDGER_FILENAME
    ledger_findings = check_ledger(ledger_path) if ledger_path.exists() else []
    kpis = workflow_kpis(backend.data, target / config.sessions_dir)
    _emit(
        maintenance_report(
            target,
            config,
            backend,
            triggers=triggers,
            economy_findings=list(economy.get("findings", [])),
            ledger_findings=ledger_findings,
            kpis=kpis,
        ),
    )
    return 0


def cmd_review(
    target: Path,
    action: str,
    slot: str | None,
    *,
    verdict: str,
    reviewer: str,
) -> int:
    """Drive the independent-review seam: build payloads, record verdicts."""
    if action == "doc":
        _emit(seam_wiring_doc())
        return 0
    if slot is None:
        _emit("review: a slot is required for build/confirm.")
        return 2
    loaded = _require_state(target, "review")
    if loaded is None:
        return 1
    config, backend = loaded
    if action == "build":
        payload = build_review_payload(backend, slot)
        if not payload:
            _emit(f"review: slot {slot!r} is not provisional — nothing to review.")
            return 1
        path = write_review_payload(target, config, payload)
        rel = path.relative_to(target) if path.is_relative_to(target) else path
        _emit(f"review: payload written -> {rel}")
        return 0
    if action == "confirm":
        if verdict not in ("pass", "fail"):
            _emit("review: --verdict must be pass or fail.")
            return 2
        outcome = apply_review_verdict(
            backend,
            slot,
            verdict=verdict,
            reviewer=reviewer,
        )
        _emit(f"review: {slot} -> {outcome}.")
        if outcome == "not-provisional":
            _emit(
                "review: nothing recorded — the slot is not provisional "
                "(typo, already confirmed, or never answered).",
            )
            return 1
        # The verdict is recorded → the payload is consumed. Remove it so the
        # maintenance "awaiting a reviewer" count reflects reality.
        if clear_review_payload(target, config, slot):
            _emit(f"review: cleared consumed payload for {slot}.")
        return 0
    _emit(f"review: unknown action {action!r} (build | confirm | doc).")
    return 2


def cmd_economy(
    target: Path,
    action: str,
    *,
    strict: bool,
    apply: bool,
    reviewed: bool,
    bands: int,
) -> int:
    """Drive the context-economy engine: check, apply, simulate, recipe."""
    config = load_config(target)
    if action == "recipe":
        _emit(calibration_recipe())
        return 0
    if action == "simulate":
        result = run_search(default_calibration(), bands=bands)
        _emit(str(result.get("why_it_won", "")))
        winner = result.get("winner", {})
        name = winner.get("name") if isinstance(winner, dict) else winner
        _emit(f"economy: winner {name} (feasible: {result.get('feasible_count')}).")
        return 0
    pass_records = (
        target / config.docs_root / config.economy.get("pass_records_dir", "planning")
    )
    harvested = parse_harvest_tables(pass_records)
    report = economy_check(
        target,
        config,
        harvested=harvested,
        harvest_exclude=harvest_sources(pass_records),
    )
    if action == "issue-body":
        _emit(issue_body(report))
        return 0
    if action == "check":
        census = report.get("census", {})
        for name in sorted(census):
            row = census[name]
            _emit(
                f"  class {name}: {row.get('files', 0)} file(s), "
                f"{row.get('words', 0)} word(s)",
            )
        for gauge in report.get("gauges", []):
            flag = "OVER" if gauge.get("over") else "ok"
            _emit(f"  gauge {gauge['name']}: {gauge['value']}/{gauge['cap']} [{flag}]")
        findings = report.get("findings", [])
        for finding in findings:
            _emit(f"  [{finding.kind}] {finding.path}: {finding.message}")
        for line in economy_actuate(target, config, report, apply=False):
            _emit(f"  would-act: {line}")
        debt = report.get("debt", 0)
        threshold = int(config.economy.get("debt_threshold", 10))
        _emit(f"economy: debt {debt} (threshold {threshold}).")
        over = bool(findings) or debt >= threshold
        return 1 if strict and over else 0
    if action == "apply":
        if apply:
            backend = JsonStateBackend(_state_path(target, config))
            if backend.data and not actuators_may_apply(backend.data):
                _emit(
                    "economy: refused — the mode/promotion policy does not "
                    "permit actuators to apply (promotion_rights must be "
                    "'promote'); dry-run only.",
                )
                return 1
        lines = economy_actuate(
            target,
            config,
            report,
            apply=apply,
            acknowledged=reviewed,
        )
        for line in lines:
            _emit(f"  {line}")
        if not apply:
            _emit("economy: dry-run (pass --yes to act; maturity gates apply).")
        return 0
    _emit(
        f"economy: unknown action {action!r} "
        "(check | apply | simulate | recipe | issue-body).",
    )
    return 2


def cmd_adopt(
    target: Path,
    include_claude: bool,
    wire_enforcement: bool = False,
) -> int:
    """Adopt the workflow into ``target``: init, plant the docs, stage the packs.

    The one-step flow: ``init`` runs first (idempotent — config + state), so a
    bare directory with nothing but the bootstrap file becomes a fully
    substrate-governed project in this single command. ``wire_enforcement``
    additionally turns on the live nag hook + the CI locked door.
    """
    rc = cmd_init(target)
    if rc != 0:
        return rc
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    lines = adopt(
        target,
        config,
        backend,
        kit_root=_kit_root(),
        include_claude=include_claude,
        wire_enforcement=wire_enforcement,
    )
    for line in lines:
        _emit(f"adopt: {line}")
    return 0


def cmd_contextpack(target: Path, index: Path | None) -> int:
    """Generate agent context packs from the project index (or a manifest)."""
    assert_safe_target(target, _kit_root())
    config = load_config(target)
    index_path = index if index is not None else target / "project.index.json"
    if not index_path.exists():
        _emit(f"contextpack: no index at {index_path} (run adopt first).")
        return 1
    try:
        areas = load_pack_index(index_path)
    except ValueError as exc:
        _emit(f"contextpack: {exc}")
        return 2
    if not areas:
        _emit("contextpack: index has no areas — nothing to generate.")
        return 0
    for path in generate_packs(target, config, areas):
        rel = path.relative_to(target) if path.is_relative_to(target) else path
        _emit(f"contextpack: wrote {rel}")
    return 0


def cmd_session_start(target: Path) -> int:
    """Print this session's orientation injection (the SessionStart composition)."""
    loaded = _require_state(target, "session-start")
    if loaded is None:
        return 1
    config, backend = loaded
    _emit(compose_orientation(target, config, backend))
    return 0


def cmd_session_close(target: Path) -> int:
    """Run the session-close ritual: mine, index, advise, and report KPIs.

    Mines the session logs into the reflection buffer, rebuilds the episodic
    index, prints the stop-check advisories, and ends with the KPI footer —
    the engine analog of the one-idea / previous-session-review enders.
    """
    loaded = _require_state(target, "session-close")
    if loaded is None:
        return 1
    config, _ = loaded
    rc = cmd_reflect(target, add=None, evidence="", tags="", mine=True)
    if rc != 0:
        return rc
    index_path = target / config.state_dir / EPISODIC_INDEX_FILENAME
    entries = rebuild_episodic_index(target / config.sessions_dir, index_path)
    _emit(f"session-close: indexed {len(entries)} session(s).")
    # Re-read state: the mine above stamped reflection_buffer.last_mined, and
    # a pre-mine snapshot would re-advise the mine it just ran.
    backend = JsonStateBackend(_state_path(target, config))
    for line in evaluate_stop(target, config, backend):
        _emit(f"session-close: [advisory] {line}")
    kpis = workflow_kpis(backend.data, target / config.sessions_dir)
    _emit(kpi_footer(kpis))
    return 0


def cmd_ledger(
    target: Path,
    *,
    title: str,
    verdict: str,
    why: str,
    provenance: str,
    supersedes: str | None,
) -> int:
    """Append a decision to the [D-NNNN] ledger (created on first use)."""
    assert_safe_target(target, _kit_root())
    config = load_config(target)
    path = target / config.docs_root / LEDGER_FILENAME
    entry = append_decision(
        path,
        title=title,
        verdict=verdict,
        why=why,
        provenance=provenance,
        supersedes=supersedes,
    )
    _emit(f"ledger: recorded {entry['id']} — {title}")
    if supersedes:
        _emit(f"ledger: {supersedes} stamped superseded-by {entry['id']}.")
    return 0


def _simulate_mode_asserts(
    mode: str,
    data: dict,
    graduated: bool,
    n: int,
) -> str | None:
    """Return the per-mode behavior violation, or None when behavior held.

    The behavior-assert half of the simulation: observe must never
    auto-graduate (it proposes), guided/active must graduate once the quiet
    streak is long enough.
    """
    quiet_needed = 3
    if mode == "observe":
        if graduated or data.get("stage") != "integration":
            return "observe mode auto-graduated (must only propose)"
        if n > quiet_needed and not data.get("graduation_proposed"):
            return "observe mode never proposed graduation"
        return None
    if n > quiet_needed and not graduated:
        return f"{mode} mode failed to graduate after the quiet streak"
    return None


def cmd_simulate(n: int, mode: str = "guided") -> int:
    """Init into a temp dir and drive ``n`` interview sessions; verify behavior.

    Session 1 supplies confirmed answers for every critical slot; later sessions
    supply none. Asserts the critical slots fill and that the run behaves
    per ``mode``: guided/active graduate integration -> steady once quiet;
    observe only ever *proposes* graduation.
    """
    with tempfile.TemporaryDirectory(prefix="substrate-sim-") as tmp:
        target = Path(tmp)
        rc = cmd_init(target)
        if rc != 0:
            return rc
        state_path = _state_path(target, load_config(target))
        if mode != "guided":
            rc = cmd_mode(target, mode)
            if rc != 0:
                return rc
        crit = critical_slots()
        answers = {slot: f"value-for-{slot}" for slot in crit}
        graduated = False
        for index in range(n):
            backend = JsonStateBackend(state_path)
            result = run_session(backend, answers if index == 0 else {})
            graduated = graduated or result["graduated"]
        data = JsonStateBackend(state_path).data
        missing = [s for s in crit if data.get("slots", {}).get(s) != "filled"]
        if missing:
            _emit(f"simulate: FAILED — critical slots unfilled: {missing}")
            return 1
        violation = _simulate_mode_asserts(mode, data, graduated, n)
        if violation:
            _emit(f"simulate: FAILED — {violation}")
            return 1
        _emit(
            f"simulate: OK — {n} session(s), {len(crit)} critical slots filled, "
            f"mode={mode}, stage={data.get('stage')} (graduated={graduated}).",
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the bootstrap argument parser."""
    parser = argparse.ArgumentParser(prog="bootstrap", description="substrate-kit")
    parser.add_argument(
        "--simulate",
        type=int,
        metavar="N",
        help="run N synthetic sessions in a temp dir, then exit",
    )
    parser.add_argument(
        "--mode",
        default="guided",
        choices=("observe", "guided", "active"),
        help="integration mode for --simulate (behavior asserts differ per mode)",
    )
    sub = parser.add_subparsers(dest="command")
    for name, helptext in (
        ("init", "initialise a project"),
        ("status", "show install state"),
        ("ask", "list pending interview questions"),
        ("triggers", "scan for fired triggers / mandatory questions"),
        ("metrics", "emit the router + workflow KPIs"),
        ("session-start", "print this session's orientation injection"),
        ("session-close", "mine reflections, index the session, report KPIs"),
    ):
        child = sub.add_parser(name, help=helptext)
        child.add_argument("--target", type=Path, default=Path.cwd())
    adopt_p = sub.add_parser("adopt", help="plant the workflow docs + stage the packs")
    adopt_p.add_argument(
        "--include-claude",
        action="store_true",
        help="also write .claude/CLAUDE.md + .claude/settings.json (skip-if-exists)",
    )
    adopt_p.add_argument(
        "--wire-enforcement",
        action="store_true",
        help=(
            "turn on the forcing functions: the live nag hook (implies "
            "--include-claude) + a live CI gate that holds the merge red until "
            "the session journal is written"
        ),
    )
    adopt_p.add_argument("--target", type=Path, default=Path.cwd())
    contextpack = sub.add_parser(
        "contextpack",
        help="generate agent context packs from the index",
    )
    contextpack.add_argument(
        "--index",
        type=Path,
        default=None,
        help="index or manifest path (default: <target>/project.index.json)",
    )
    contextpack.add_argument("--target", type=Path, default=Path.cwd())
    render_p = sub.add_parser("render", help="render content docs from filled slots")
    render_p.add_argument(
        "--live",
        action="store_true",
        help="fill remaining placeholders in the PLANTED docs in place",
    )
    render_p.add_argument("--target", type=Path, default=Path.cwd())
    answer = sub.add_parser("answer", help="record a user answer for a slot")
    answer.add_argument("slot")
    answer.add_argument("value", nargs="+", help="the answer text")
    answer.add_argument("--target", type=Path, default=Path.cwd())
    confirm = sub.add_parser("confirm", help="confirm a provisional slot")
    confirm.add_argument("slot")
    confirm.add_argument("--target", type=Path, default=Path.cwd())
    reflect = sub.add_parser("reflect", help="list/add/mine the reflection buffer")
    reflect.add_argument("--add", metavar="LESSON", default=None)
    reflect.add_argument("--evidence", default="")
    reflect.add_argument("--tags", default="", help="comma-separated tags")
    reflect.add_argument("--mine", action="store_true")
    reflect.add_argument("--target", type=Path, default=Path.cwd())
    episodes = sub.add_parser("episodes", help="rebuild/search the episodic index")
    episodes.add_argument("--rebuild", action="store_true")
    episodes.add_argument("--search", metavar="TAG", default=None)
    episodes.add_argument("--target", type=Path, default=Path.cwd())
    maintain = sub.add_parser("maintain", help="run the self-maintenance report")
    maintain.add_argument("--compact", action="store_true")
    maintain.add_argument("--target", type=Path, default=Path.cwd())
    review = sub.add_parser("review", help="drive the independent-review seam")
    review.add_argument("action", choices=("build", "confirm", "doc"))
    review.add_argument("slot", nargs="?", default=None)
    review.add_argument("--verdict", default="", help="pass | fail (for confirm)")
    review.add_argument("--reviewer", default="external")
    review.add_argument("--target", type=Path, default=Path.cwd())
    economy = sub.add_parser("economy", help="run the context-economy engine")
    economy.add_argument(
        "action",
        choices=("check", "apply", "simulate", "recipe", "issue-body"),
    )
    economy.add_argument("--strict", action="store_true")
    economy.add_argument("--yes", action="store_true", help="really act (apply)")
    economy.add_argument(
        "--reviewed",
        action="store_true",
        help="acknowledge the human review a 'gated' maturity first prune needs",
    )
    economy.add_argument("--bands", type=int, default=24)
    economy.add_argument("--target", type=Path, default=Path.cwd())
    ledger = sub.add_parser("ledger", help="append a [D-NNNN] decision")
    ledger.add_argument("--title", required=True)
    ledger.add_argument("--verdict", required=True)
    ledger.add_argument("--why", required=True)
    ledger.add_argument("--provenance", required=True)
    ledger.add_argument("--supersedes", default=None)
    ledger.add_argument("--target", type=Path, default=Path.cwd())
    mode = sub.add_parser("mode", help="set the integration mode")
    mode.add_argument("name")
    mode.add_argument("--target", type=Path, default=Path.cwd())
    stance = sub.add_parser("stance", help="show or set the task stance")
    stance.add_argument("name", nargs="?", default=None)
    stance.add_argument("--target", type=Path, default=Path.cwd())
    skills = sub.add_parser("skills", help="list or --build the skill pack")
    skills.add_argument(
        "--build",
        action="store_true",
        help="emit SKILL.md files into <state_dir>/skills/",
    )
    skills.add_argument("--target", type=Path, default=Path.cwd())
    agents = sub.add_parser("agents", help="list or --build the persona pack")
    agents.add_argument(
        "--build",
        action="store_true",
        help="emit agent .md files into <state_dir>/agents/",
    )
    agents.add_argument("--target", type=Path, default=Path.cwd())
    hooks = sub.add_parser("hooks", help="show or --build the hook wiring")
    hooks.add_argument(
        "--build",
        action="store_true",
        help="emit the PreToolUse settings snippet into <state_dir>/hooks/",
    )
    hooks.add_argument("--target", type=Path, default=Path.cwd())
    hook = sub.add_parser("hook", help="run a hook check (e.g. `hook pretooluse`)")
    hook.add_argument("event")
    hook.add_argument("--target", type=Path, default=Path.cwd())
    check = sub.add_parser("check", help="run the doc + session-log hygiene checks")
    check.add_argument("--target", type=Path, default=Path.cwd())
    check.add_argument("--strict", action="store_true", help="exit 1 if any violation")
    check.add_argument(
        "--require-session-log",
        action="store_true",
        help="fail (not just advise) when the session log is missing — the CI gate mode",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the bootstrap CLI; return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.simulate is not None:
            return cmd_simulate(args.simulate, args.mode)
        if args.command == "init":
            return cmd_init(args.target)
        if args.command == "status":
            return cmd_status(args.target)
        if args.command == "ask":
            return cmd_ask(args.target)
        if args.command == "render":
            return cmd_render(args.target, live=args.live)
        if args.command == "mode":
            return cmd_mode(args.target, args.name)
        if args.command == "stance":
            return cmd_stance(args.target, args.name)
        if args.command == "skills":
            return cmd_skills(args.target, args.build)
        if args.command == "agents":
            return cmd_agents(args.target, args.build)
        if args.command == "hooks":
            return cmd_hooks(args.target, args.build)
        if args.command == "hook":
            return cmd_hook(args.target, args.event)
        if args.command == "check":
            return cmd_check(
                args.target,
                args.strict,
                require_session_log=args.require_session_log,
            )
        if args.command == "answer":
            return cmd_answer(args.target, args.slot, " ".join(args.value))
        if args.command == "confirm":
            return cmd_confirm(args.target, args.slot)
        if args.command == "triggers":
            return cmd_triggers(args.target)
        if args.command == "reflect":
            return cmd_reflect(
                args.target,
                add=args.add,
                evidence=args.evidence,
                tags=args.tags,
                mine=args.mine,
            )
        if args.command == "episodes":
            return cmd_episodes(args.target, rebuild=args.rebuild, search=args.search)
        if args.command == "metrics":
            return cmd_metrics(args.target)
        if args.command == "maintain":
            return cmd_maintain(args.target, compact=args.compact)
        if args.command == "review":
            return cmd_review(
                args.target,
                args.action,
                args.slot,
                verdict=args.verdict,
                reviewer=args.reviewer,
            )
        if args.command == "economy":
            return cmd_economy(
                args.target,
                args.action,
                strict=args.strict,
                apply=args.yes,
                reviewed=args.reviewed,
                bands=args.bands,
            )
        if args.command == "adopt":
            return cmd_adopt(
                args.target,
                args.include_claude,
                wire_enforcement=args.wire_enforcement,
            )
        if args.command == "contextpack":
            return cmd_contextpack(args.target, args.index)
        if args.command == "session-start":
            return cmd_session_start(args.target)
        if args.command == "session-close":
            return cmd_session_close(args.target)
        if args.command == "ledger":
            return cmd_ledger(
                args.target,
                title=args.title,
                verdict=args.verdict,
                why=args.why,
                provenance=args.provenance,
                supersedes=args.supersedes,
            )
    except UnsafeTargetError as exc:
        _emit(f"refused: {exc}")
        return 2
    parser.print_help()
    return 0

_ENGINE_MANIFEST = {
    'engine/__init__.py': '',
    'engine/lib/__init__.py': '',
    'engine/interview/__init__.py': '',
    'engine/checks/__init__.py': '"""Generic, config-driven hygiene checkers lifted from the host project.\n\nThese are stdlib-only ports of the proven ``check_docs`` / ``check_session_log``\nscripts, with every host-specific value (doc root, badge taxonomy, read-path\ndocs, sessions dir, required markers) read from ``substrate.config.json`` instead\nof hardcoded. The host project\'s ratchets and freshness rules are intentionally\ndropped — they are superbot-shaped policy, not portable mechanism.\n"""\n',
    'engine/loop/__init__.py': '"""The self-improving loop: triggers, reflections, episodes, maintenance."""\n',
    'engine/economy/__init__.py': '"""The context-economy engine: taxonomy, gauges, retention, tombstones."""\n',
    'engine/stances/__init__.py': '"""Task-stance capability layer (plan section 3b).\n\nA stance is the working agent\'s operational posture for the current task — the\nfourth control axis, distinct from adoption-pace (mode), promotion-rights, and\nstage. Each stance scopes a reading-route, a tool-scope, and an output contract\nto cut context rot and tool misfires. Advisory by default.\n"""\n',
    'engine/skills/__init__.py': '"""Skills — the invoke-a-capability layer (plan section 3c).\n\nA skill is an invokable ``SKILL.md`` procedure (the counterpart to a stance\'s\nambient posture). The kit ships generalized skill *sources* here and emits native\n``.claude/skills/<name>/SKILL.md`` files (metadata-first frontmatter + body) so\nthey load progressively and port across agent CLIs.\n"""\n',
    'engine/agents/__init__.py': '"""Personas — spawnable read-only specialists (plan section 3c).\n\nA persona is a sub-agent the working agent can spawn for a focused, read-only\ntask (design review, independent critique, deep exploration). The kit ships\ngeneralized persona sources here and emits native ``.claude/agents/<name>.md``\nfiles (frontmatter + system-prompt body), each filled from the project\'s own\ncontract docs via ``${slot}`` substitution.\n"""\n',
    'engine/hooks/__init__.py': '"""Hook layer — the kit\'s runtime seams into a Claude Code session.\n\nFour hooks: the **PreToolUse stance guard** (warns on an out-of-stance tool),\n**SessionStart orientation** (injects the mode-aware composition), the\n**PostToolUse edit advisor** (generated-artifact / unbadged-doc warnings), and\nthe **Stop-check advisor** (session-close hygiene). All advisory and fail-open\n— they inform, they never block. ``settings.py`` builds the staged\n``settings.template.json`` + fill-table a host merges into ``.claude/``.\n"""\n',
    'engine/lib/atomicio.py': '"""Atomic file writes for crash-safe state.\n\nA write goes to a sibling ``*.tmp`` file and is renamed into place with\n``os.replace`` — an atomic rename on POSIX and Windows — so a process that dies\nmid-write can never leave a half-written, unparseable file behind. This is the\nrobustness floor the whole engine builds on (plan: Gemini round).\n"""\n\nfrom __future__ import annotations\n\nimport os\nfrom pathlib import Path\n\n\ndef atomic_write_text(path: Path, text: str) -> None:\n    """Write ``text`` to ``path`` atomically via a temp file + ``os.replace``."""\n    path.parent.mkdir(parents=True, exist_ok=True)\n    tmp = path.with_name(path.name + ".tmp")\n    tmp.write_text(text, encoding="utf-8")\n    os.replace(tmp, path)\n',
    'engine/lib/config.py': '"""Host-project configuration for one substrate-kit install.\n\nReads and writes ``substrate.config.json`` — the single file that absorbs every\nhost-specific knob so the engine code never hardcodes a project value. Two\ninterpreters are kept explicitly separate (Hermes-final): ``interpreter`` is the\nkit\'s own runtime, ``interpreter_for_checks`` is the host project\'s verification\nruntime (e.g. ``python3.10`` for a repo whose CI pins 3.10).\n"""\n\nfrom __future__ import annotations\n\nimport json\nimport sys\nimport uuid\nfrom dataclasses import asdict, dataclass, field, fields\nfrom pathlib import Path\n\nfrom engine.lib.atomicio import atomic_write_text\n\nCONFIG_FILENAME = "substrate.config.json"\nDEFAULT_STATE_DIR = ".substrate"\n\n\ndef _new_project_id() -> str:\n    """Return a short, stable identifier for one install."""\n    return uuid.uuid4().hex[:12]\n\n\ndef _default_cadence() -> dict[str, int]:\n    """Return the default cadence knobs (every hardcoded cadence lives here)."""\n    return {\n        "reconciliation_prs": 20,\n        "reconciliation_sessions": 20,\n        "compaction_sessions": 20,\n        "critical_slot_grace_sessions": 3,\n        "staleness_days": 14,\n        "guided_practice_sessions": 3,\n    }\n\n\ndef _default_reflection() -> dict:\n    """Return the reflection-buffer knobs (size cap is a hard context guard)."""\n    return {"enabled": True, "buffer_size": 5}\n\n\ndef _default_orientation() -> dict:\n    """Return the orientation-budget knobs (the K0 ≤7,000-word gate).\n\n    ``boot_docs`` empty means "fall back to ``readpath_docs``" — the\n    unconditional boot-read set the budget counts.\n    """\n    return {"budget_words": 7000, "boot_docs": []}\n\n\ndef _default_economy() -> dict:\n    """Return the context-economy knobs (taxonomy/gauges are host policy).\n\n    ``maturity`` gates the actuator: ``shadow`` (report only, the first-prune\n    safety protocol) -> ``gated`` (apply with review) -> ``normal``. Classes and\n    gauges ship empty — the engine supplies a documented generic default when\n    unset; each adopting repo declares its own table (the kit ships the search,\n    not our constants).\n    """\n    return {\n        "maturity": "shadow",\n        "pass_records_dir": "planning",\n        "reference_roots": [],\n        "id_patterns": [r"Q-\\d{3,}", r"D-\\d{3,}", r"R-\\d{3,}"],\n        "classes": [],\n        "gauges": [],\n        "debt_threshold": 10,\n    }\n\n\ndef _default_namespace() -> dict:\n    """Return the namespace-guard knobs (roots to scan + reserved-name map)."""\n    return {"roots": [], "reserved": {}}\n\n\ndef _default_review_seam() -> dict:\n    """Return the review-seam knobs (provisioned, not wired — no live reviewer)."""\n    return {"reviewer": None}\n\n\ndef _default_badge_tokens() -> list[str]:\n    """Return the default Status-badge taxonomy the doc checker accepts."""\n    return [\n        "binding",\n        "living-ledger",\n        "reference",\n        "plan",\n        "historical",\n        "audit",\n        "owner-guidance",\n        "ideas",\n        "archive",\n    ]\n\n\ndef _default_readpath_docs() -> list[str]:\n    """Return the read-path doc names that seed the reachability roots."""\n    return ["AGENT_ORIENTATION.md", "current-state.md"]\n\n\ndef _default_session_markers() -> list[dict[str, str]]:\n    """Return the markers every session log must carry (label + substring)."""\n    return [\n        {"label": "Status badge", "needle": "**Status:**"},\n        {"label": "Session idea", "needle": "💡"},\n        {"label": "Previous-session review", "needle": "previous-session review"},\n    ]\n\n\n@dataclass\nclass Config:\n    """Host-project configuration for one substrate-kit install."""\n\n    project_id: str = field(default_factory=_new_project_id)\n    interpreter: str = field(default_factory=lambda: sys.executable)\n    interpreter_for_checks: str | None = None\n    state_dir: str = DEFAULT_STATE_DIR\n    docs_root: str = "docs"\n    sessions_dir: str = ".sessions"\n    paths: dict[str, str] = field(default_factory=dict)\n    cadence: dict[str, int] = field(default_factory=_default_cadence)\n    scopes: dict[str, str] = field(default_factory=dict)\n    badge_tokens: list[str] = field(default_factory=_default_badge_tokens)\n    readpath_docs: list[str] = field(default_factory=_default_readpath_docs)\n    session_markers: list[dict[str, str]] = field(\n        default_factory=_default_session_markers,\n    )\n    reflection: dict = field(default_factory=_default_reflection)\n    orientation: dict = field(default_factory=_default_orientation)\n    economy: dict = field(default_factory=_default_economy)\n    namespace: dict = field(default_factory=_default_namespace)\n    seams: list[dict] = field(default_factory=list)\n    review_seam: dict = field(default_factory=_default_review_seam)\n\n    def to_json(self) -> str:\n        """Serialise the config to indented, key-sorted JSON."""\n        return json.dumps(asdict(self), indent=2, sort_keys=True)\n\n    @classmethod\n    def from_dict(cls, data: dict) -> Config:\n        """Build a Config from a parsed dict, ignoring unknown keys."""\n        known = {f.name for f in fields(cls)}\n        return cls(**{k: v for k, v in data.items() if k in known})\n\n\ndef config_path(root: Path) -> Path:\n    """Return the config-file path for a project ``root``."""\n    return root / CONFIG_FILENAME\n\n\ndef load_config(root: Path) -> Config:\n    """Load the config from ``root``; return defaults if none exists."""\n    path = config_path(root)\n    if not path.exists():\n        return Config()\n    data = json.loads(path.read_text(encoding="utf-8"))\n    return Config.from_dict(data)\n\n\ndef save_config(root: Path, config: Config) -> None:\n    """Write ``config`` to ``root`` atomically."""\n    atomic_write_text(config_path(root), config.to_json() + "\\n")\n',
    'engine/lib/state.py': '"""The state-backend interface and its default JSON implementation.\n\nThe *interface* — not a raw JSON shape — is the contract the rest of the engine\ncodes against (Hermes-final, plan §2), so a future SQLite backend can replace the\nJSON one without a rewrite. The default backend is one JSON file written\natomically; mutations inside a ``transaction`` roll back on error and flush once.\n"""\n\nfrom __future__ import annotations\n\nimport copy\nimport json\nfrom abc import ABC, abstractmethod\nfrom collections.abc import Iterator\nfrom contextlib import AbstractContextManager, contextmanager\nfrom pathlib import Path\nfrom typing import Any\n\nfrom engine.lib.atomicio import atomic_write_text\n\nSTATE_SCHEMA_VERSION = 1\n\n\ndef default_state(project_id: str) -> dict[str, Any]:\n    """Return the initial state document for a fresh install."""\n    return {\n        "version": STATE_SCHEMA_VERSION,\n        "project_id": project_id,\n        "mode": "guided",\n        "promotion_rights": "propose",\n        "stage": "integration",\n        "stance": "analysis",\n        "session_count": 0,\n        "slots": {},\n        "slot_values": {},\n        "open_questions": [],\n        "quiet_sessions": 0,\n        "graduation": {\n            "soft_target_sessions": 50,\n            "criteria": {\n                "critical_slots_filled_pct": 0.8,\n                "blocking_questions": 0,\n            },\n        },\n        "mode_history": [],\n        "reflection_buffer": {"active_count": 0, "last_mined": None},\n        "graduation_proposed": False,\n        "last_compaction_session": 0,\n        "review_log": [],\n    }\n\n\nclass StateBackend(ABC):\n    """Read / write / query / transaction / migrate contract for engine state."""\n\n    version: int = STATE_SCHEMA_VERSION\n\n    @abstractmethod\n    def get(self, key: str, default: Any = None) -> Any:\n        """Return the value stored at ``key`` or ``default``."""\n\n    @abstractmethod\n    def set(self, key: str, value: Any) -> None:\n        """Store ``value`` at ``key`` (flushing unless inside a transaction)."""\n\n    @abstractmethod\n    def query(self, prefix: str = "") -> dict[str, Any]:\n        """Return all key/value pairs whose key starts with ``prefix``."""\n\n    @abstractmethod\n    def transaction(self) -> AbstractContextManager[StateBackend]:\n        """Return a context manager that commits on success, rolls back on error."""\n\n    @abstractmethod\n    def migrate(self, to_version: int) -> None:\n        """Migrate the stored document to schema ``to_version``."""\n\n\nclass JsonStateBackend(StateBackend):\n    """A StateBackend backed by one atomically-written JSON file."""\n\n    def __init__(self, path: Path) -> None:\n        self._path = Path(path)\n        self._data: dict[str, Any] = self._read()\n        self._txn_depth = 0\n\n    def _read(self) -> dict[str, Any]:\n        if not self._path.exists():\n            return {}\n        return json.loads(self._path.read_text(encoding="utf-8"))\n\n    def _flush(self) -> None:\n        atomic_write_text(\n            self._path,\n            json.dumps(self._data, indent=2, sort_keys=True) + "\\n",\n        )\n\n    def get(self, key: str, default: Any = None) -> Any:\n        """Return the value stored at ``key`` or ``default``."""\n        return self._data.get(key, default)\n\n    def set(self, key: str, value: Any) -> None:\n        """Store ``value`` at ``key``; flush now unless inside a transaction."""\n        self._data[key] = value\n        if self._txn_depth == 0:\n            self._flush()\n\n    def query(self, prefix: str = "") -> dict[str, Any]:\n        """Return all key/value pairs whose key starts with ``prefix``."""\n        return {k: v for k, v in self._data.items() if k.startswith(prefix)}\n\n    @contextmanager\n    def transaction(self) -> Iterator[JsonStateBackend]:\n        """Buffer writes; roll back the whole document on error, else flush once.\n\n        Re-entrant (Q-0223 tail ①): a helper that opens its own transaction may\n        be composed inside a caller\'s wider transaction. Each level snapshots on\n        entry and restores its own snapshot on error; only the *outermost* exit\n        flushes, so a composed multi-write either fully lands or fully rolls\n        back to the enclosing level\'s snapshot — never a partial flush.\n        """\n        snapshot = copy.deepcopy(self._data)\n        self._txn_depth += 1\n        try:\n            yield self\n        except Exception:\n            self._data = snapshot\n            raise\n        finally:\n            self._txn_depth -= 1\n        if self._txn_depth == 0:\n            self._flush()\n\n    def migrate(self, to_version: int) -> None:\n        """Set the stored schema version (no transforms needed at v1)."""\n        self._data["version"] = to_version\n        self._flush()\n\n    @property\n    def data(self) -> dict[str, Any]:\n        """Return a shallow copy of the current state document."""\n        return dict(self._data)\n',
    'engine/lib/guardrail.py': '"""The live-loop guardrail.\n\nA mechanical guarantee (plan: design-corroboration) that the kit never operates\non its own repository root — which would let it mutate the very workflow it runs\ninside. Safe targets are the system temp tree, an ``examples/`` subtree of the\nkit, or any directory outside the kit. Enforced in code, in the first commit —\nnot left as a doc.\n"""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\n\n\nclass UnsafeTargetError(Exception):\n    """Raised when a target directory would corrupt the kit\'s own live loop."""\n\n\ndef assert_safe_target(target: Path, kit_root: Path) -> None:\n    """Refuse to operate on the kit\'s own repo root.\n\n    Unsafe: ``kit_root`` itself or a non-``examples`` path inside it — even\n    when the kit checkout lives under the system temp tree (an earlier\n    temp-tree shortcut ran first and silently voided the whole guarantee for a\n    kit cloned into ``/tmp``). Everything outside ``kit_root``, and the\n    ``examples/`` subtree, is safe. A ``kit_root`` that is a *file* (the\n    single-file bootstrap has no kit tree to protect) never matches.\n    """\n    target = Path(target).resolve()\n    kit_root = Path(kit_root).resolve()\n    inside_kit = target == kit_root or target.is_relative_to(kit_root)\n    inside_examples = target.is_relative_to(kit_root / "examples")\n    if inside_kit and not inside_examples:\n        msg = f"refusing to operate on the kit\'s own tree: {target}"\n        raise UnsafeTargetError(msg)\n',
    'engine/lib/modes.py': '"""Integration-mode behavior policies (plan section 3 — the adoption-pace axis).\n\nThe ``mode`` state field (observe | guided | active) existed since PR 1 but nothing\nread it; this module is the single place its *behavior* is defined, so every\nconsumer (interview quota, orientation depth, trigger mandates, actuator gating,\ngraduation) asks one policy table instead of re-deriving the semantics.\n\nThe three modes, per the approved plan:\n\n- **observe** — the kit imposes nothing: each session writes a light note, asks\n  only 1-2 observation questions, and passively profiles how the user already\n  works; after enough sessions it *proposes* a tailored workflow (never\n  auto-graduates — proposal only).\n- **guided** — the default: the workflow rolls out one practice at a time in a\n  fixed order (session logs → idea lifecycle → question router → session-enders\n  → gates), each arriving only after the prior is established; triggers may\n  mandate questions.\n- **active** — the full workflow from session 1; the interview runs aggressively\n  (no quota) to fill slots fast.\n\n``promotion_rights`` is the *separate* autonomy axis: what the agent may change\nwithout sign-off. Actuators (economy prunes, maintenance writes) may apply only\nwhen the mode allows it AND promotion_rights is ``"promote"`` — otherwise they\nstay dry-run/propose.\n"""\n\nfrom __future__ import annotations\n\nfrom typing import Any\n\nMODES = ("observe", "guided", "active")\n\n# The guided-mode rollout order is fixed by the plan; only the pacing is ours.\nGUIDED_ROLLOUT = (\n    "session_logs",\n    "idea_lifecycle",\n    "question_router",\n    "session_enders",\n    "gates",\n)\n\nDEFAULT_MODE = "guided"\n\n# One behavior record per mode. quota None = unlimited questions per session.\n_MODE_POLICIES: dict[str, dict[str, Any]] = {\n    "observe": {\n        "question_quota": 2,\n        "orientation_depth": "minimal",\n        "practices": "none",\n        "triggers_mandate": False,\n        "actuators_allowed": False,\n        "auto_graduate": False,\n        "workflow_proposal_after_sessions": 5,\n    },\n    "guided": {\n        "question_quota": 3,\n        "orientation_depth": "standard",\n        "practices": "rollout",\n        "triggers_mandate": True,\n        "actuators_allowed": True,\n        "auto_graduate": True,\n        "workflow_proposal_after_sessions": None,\n    },\n    "active": {\n        "question_quota": None,\n        "orientation_depth": "full",\n        "practices": "all",\n        "triggers_mandate": True,\n        "actuators_allowed": True,\n        "auto_graduate": True,\n        "workflow_proposal_after_sessions": None,\n    },\n}\n\n\ndef mode_policy(state: dict[str, Any]) -> dict[str, Any]:\n    """Return the behavior policy for the state\'s active mode.\n\n    An unknown or missing mode falls back to the default (``guided``) so every\n    consumer fails open onto sane behavior rather than crashing on bad state.\n    """\n    mode = state.get("mode", DEFAULT_MODE)\n    return dict(_MODE_POLICIES.get(mode, _MODE_POLICIES[DEFAULT_MODE]))\n\n\ndef question_quota(state: dict[str, Any]) -> int | None:\n    """Return the per-session interview question quota (None = unlimited)."""\n    quota = mode_policy(state)["question_quota"]\n    return quota if quota is None else int(quota)\n\n\ndef orientation_depth(state: dict[str, Any]) -> str:\n    """Return the orientation-injection depth: minimal | standard | full."""\n    return str(mode_policy(state)["orientation_depth"])\n\n\ndef triggers_mandate(state: dict[str, Any]) -> bool:\n    """True when fired triggers may *mandate* questions (guided/active only)."""\n    return bool(mode_policy(state)["triggers_mandate"])\n\n\ndef actuators_may_apply(state: dict[str, Any]) -> bool:\n    """True when actuators may apply changes (mode allows AND rights say promote).\n\n    This is the promotion-rights enforcement point: whatever the mode, an agent\n    whose ``promotion_rights`` is ``"propose"`` (or ``"observe"``) only ever\n    produces dry-run reports.\n    """\n    if not mode_policy(state)["actuators_allowed"]:\n        return False\n    return state.get("promotion_rights") == "promote"\n\n\ndef may_auto_graduate(state: dict[str, Any]) -> bool:\n    """True when graduation may fire automatically (observe mode proposes only)."""\n    return bool(mode_policy(state)["auto_graduate"])\n\n\ndef workflow_proposal_due(state: dict[str, Any]) -> bool:\n    """True when observe mode has watched long enough to propose its workflow."""\n    threshold = mode_policy(state)["workflow_proposal_after_sessions"]\n    if threshold is None:\n        return False\n    return int(state.get("session_count", 0)) >= int(threshold)\n\n\ndef active_practices(\n    state: dict[str, Any],\n    cadence: dict[str, int] | None = None,\n) -> list[str]:\n    """Return the workflow practices currently active under the mode\'s pacing.\n\n    observe: none (the kit imposes nothing). active: all from session 1.\n    guided: one practice unlocks per ``guided_practice_sessions`` sessions\n    (config cadence, default 3), in the fixed rollout order — the "only after\n    the prior is established" pacing, made deterministic.\n    """\n    practices = mode_policy(state)["practices"]\n    if practices == "none":\n        return []\n    if practices == "all":\n        return list(GUIDED_ROLLOUT)\n    interval = int((cadence or {}).get("guided_practice_sessions", 3))\n    interval = max(interval, 1)\n    sessions = int(state.get("session_count", 0))\n    unlocked = 1 + sessions // interval\n    return list(GUIDED_ROLLOUT[:unlocked])\n',
    'engine/interview/question_bank.py': '"""The interview question bank — the seed set the staged onboarding draws from.\n\nCuration policy (Hermes #7): keep this lean. Add a question only when its slot\ngenuinely blocks graduation, or a checker keeps flagging its absence; prune\nquestions that no longer earn their place. Each entry is a plain dict so the bank\nships inside the stdlib-only bootstrap with no parser (the plan named\n``question_bank.yml``; a Python module is the simplest form that embeds and runs\nidentically in ``src`` and the single-file ``dist`` — no YAML/JSON dependency).\n\nEntry fields:\n  id        — stable "Q-NNN" identifier.\n  slot      — the content slot it fills (matches the project index).\n  audience  — "user" (ask the maintainer) or "self" (the agent infers).\n  prompt    — the question text.\n  routing   — where a confirmed answer lands (a doc:field or state:key).\n  priority  — "blocking" | "high" | "normal".\n  critical  — True if graduation requires this slot filled (confirmed, not assumed).\n\nOptional fields:\n  trigger   — a trigger kind (see engine/loop/triggers.py); the question is pulled\n              into a mandatory-question session when that trigger fires.\n  objective — True when a different model can verify the answer against evidence\n              (the review seam may then confirm a provisional answer); subjective\n              slots stay provisional until the user confirms.\n  min_len   — anti-gaming floor: an answer shorter than this never fills the slot.\n"""\n\nfrom __future__ import annotations\n\nCURATION_RULE = (\n    "Lean bank: add a question only when it blocks graduation or a checker keeps "\n    "flagging its slot; prune questions that no longer earn their place."\n)\n\nQUESTIONS: list[dict] = [\n    {\n        "id": "Q-001",\n        "slot": "integration_mode",\n        "audience": "user",\n        "prompt": "Adoption pace for the workflow? observe | guided | active.",\n        "routing": "state:mode",\n        "priority": "blocking",\n        "critical": True,\n        # The sole blocking+critical slot needs an anti-gaming floor too — the\n        # valid values (observe/guided/active) are all >=6 chars, so a floor of\n        # 4 rejects a hollow single-char graduation without ever rejecting a\n        # real mode.\n        "min_len": 4,\n    },\n    {\n        "id": "Q-002",\n        "slot": "project_name",\n        "audience": "user",\n        "prompt": "What is this project called?",\n        "routing": "templates/CLAUDE.md:project_name",\n        "priority": "high",\n        "critical": True,\n        "objective": True,\n        "min_len": 2,\n    },\n    {\n        "id": "Q-003",\n        "slot": "primary_language",\n        "audience": "user",\n        "prompt": "Primary language / runtime (e.g. Python 3.10, TypeScript)?",\n        "routing": "templates/CLAUDE.md:language",\n        "priority": "high",\n        "critical": True,\n        "objective": True,\n        "min_len": 3,\n    },\n    {\n        "id": "Q-004",\n        "slot": "architecture_layers",\n        "audience": "user",\n        "prompt": "What are the top-level layers and their import rules?",\n        "routing": "templates/architecture.md:layers",\n        "priority": "high",\n        "critical": True,\n        "trigger": "critical_unfilled",\n        "objective": True,\n        "min_len": 20,\n    },\n    {\n        "id": "Q-005",\n        "slot": "verify_command",\n        "audience": "user",\n        "prompt": "One command that proves a change is good (tests + lint)?",\n        "routing": "templates/CLAUDE.md:verify_command",\n        "priority": "high",\n        "critical": True,\n        "objective": True,\n        "min_len": 4,\n    },\n    {\n        "id": "Q-006",\n        "slot": "ownership_model",\n        "audience": "self",\n        "prompt": "Which component owns each data store / write path?",\n        "routing": "templates/ownership.md:owners",\n        "priority": "normal",\n        "critical": False,\n        "objective": True,\n        "min_len": 20,\n    },\n    {\n        "id": "Q-007",\n        "slot": "doc_roots",\n        "audience": "self",\n        "prompt": "Where does durable documentation live?",\n        "routing": "state:paths.docs",\n        "priority": "normal",\n        "critical": False,\n    },\n    {\n        "id": "Q-008",\n        "slot": "owner_profile",\n        "audience": "user",\n        "prompt": "How do you like an agent to work (tone, detail, autonomy)?",\n        "routing": "templates/owner-profile.md:style",\n        "priority": "normal",\n        "critical": False,\n    },\n    {\n        "id": "Q-009",\n        "slot": "mutation_seam",\n        "audience": "self",\n        "prompt": "How are writes gated (the audited mutation seam)?",\n        "routing": "templates/runtime_contracts.md:mutations",\n        "priority": "normal",\n        "critical": False,\n        "objective": True,\n        "min_len": 20,\n    },\n    {\n        "id": "Q-010",\n        "slot": "review_ritual",\n        "audience": "user",\n        "prompt": "Your PR-review and release rhythm?",\n        "routing": "templates/owner-profile.md:procedures",\n        "priority": "normal",\n        "critical": False,\n    },\n    {\n        "id": "Q-011",\n        "slot": "drift_resolution",\n        "audience": "self",\n        "prompt": "Doc-hygiene checks are failing - what drifted, and what fixes it?",\n        "routing": "state:open_questions",\n        "priority": "high",\n        "critical": False,\n        "trigger": "drift",\n    },\n    {\n        "id": "Q-012",\n        "slot": "staleness_review",\n        "audience": "user",\n        "prompt": "Memory looks stale (reconciliation overdue) - what changed since the last update?",\n        "routing": "templates/current-state.md:refresh",\n        "priority": "normal",\n        "critical": False,\n        "trigger": "staleness",\n    },\n    {\n        "id": "Q-013",\n        "slot": "new_area_ownership",\n        "audience": "user",\n        "prompt": "A new area appeared with no ownership/folio entry - which component owns it?",\n        "routing": "templates/ownership.md:owners",\n        "priority": "high",\n        "critical": False,\n        "trigger": "new_area",\n    },\n]\n',
    'engine/interview/stages.py': '"""Stage state machine + adaptive graduation (plan section 2).\n\nStage 1 (``integration``) graduates to stage 2 (``steady``) *adaptively* — when\nthe project\'s **critical** content slots are mostly filled (by confirmed, not\nassumed, answers), no blocking questions remain, and several consecutive sessions\nsurface no new mandatory question — not at a hard session count.\n"""\n\nfrom __future__ import annotations\n\nfrom typing import Any\n\nfrom engine.lib.modes import may_auto_graduate\n\nSTAGE_INTEGRATION = "integration"\nSTAGE_STEADY = "steady"\n\n_DEFAULT_FILL_PCT = 0.8\n_DEFAULT_QUIET_SESSIONS = 3\n\n\ndef critical_fill_ratio(slots: dict[str, str], critical: list[str]) -> float:\n    """Return the fraction of ``critical`` slots marked ``filled``."""\n    if not critical:\n        return 1.0\n    filled = sum(1 for name in critical if slots.get(name) == "filled")\n    return filled / len(critical)\n\n\ndef graduation_ready(\n    state: dict[str, Any],\n    critical: list[str],\n) -> tuple[bool, list[str]]:\n    """Return ``(ready, reasons)`` for graduating integration -> steady.\n\n    ``reasons`` lists the unmet criteria when not ready (empty when ready).\n    """\n    criteria = state.get("graduation", {}).get("criteria", {})\n    want_pct = criteria.get("critical_slots_filled_pct", _DEFAULT_FILL_PCT)\n    want_quiet = criteria.get("quiet_sessions_required", _DEFAULT_QUIET_SESSIONS)\n    reasons: list[str] = []\n\n    ratio = critical_fill_ratio(state.get("slots", {}), critical)\n    if ratio < want_pct:\n        reasons.append(f"critical slots {ratio:.0%} < {want_pct:.0%}")\n    blocking = len(state.get("open_questions", []))\n    if blocking:\n        reasons.append(f"{blocking} blocking question(s) open")\n    quiet = state.get("quiet_sessions", 0)\n    if quiet < want_quiet:\n        reasons.append(f"quiet streak {quiet} < {want_quiet}")\n    return (not reasons, reasons)\n\n\ndef maybe_graduate(backend: Any, critical: list[str]) -> bool:\n    """Advance integration -> steady if ready; return whether it graduated.\n\n    Mode-conditional (the plan\'s per-mode behavior): ``observe`` mode never\n    auto-graduates — when ready it records a *proposal* (``graduation_proposed``)\n    for the user to accept (switch mode or graduate explicitly); guided/active\n    graduate automatically.\n    """\n    if backend.get("stage") != STAGE_INTEGRATION:\n        return False\n    ready, _ = graduation_ready(backend.data, critical)\n    if not ready:\n        return False\n    if not may_auto_graduate(backend.data):\n        backend.set("graduation_proposed", True)\n        return False\n    backend.set("stage", STAGE_STEADY)\n    return True\n',
    'engine/interview/interview.py': '"""The interview pass — fills content slots from the question bank (plan section 4).\n\nA session asks its pending questions. A user-facing answer fills a slot\n(``filled``); when no human is present the agent self-answers, recording a\n*provisional* assumption (``provisional``) that never counts toward graduation\nuntil confirmed. This is what lets an autonomous run keep moving without blocking:\nit records assumptions, flags them, and moves on.\n"""\n\nfrom __future__ import annotations\n\nimport string\nfrom typing import Any\n\nfrom engine.interview.question_bank import QUESTIONS\nfrom engine.interview.stages import maybe_graduate\nfrom engine.lib.modes import question_quota\n\n_PRIORITY_ORDER = {"blocking": 0, "high": 1, "normal": 2}\n_PLACEHOLDER_ANSWERS = frozenset({"todo", "tbd", "...", "n/a", "?"})\n_ANSWER_STRIP = string.punctuation + string.whitespace\n\n\ndef critical_slots(bank: list[dict] | None = None) -> list[str]:\n    """Return the slot names the bank marks as critical."""\n    bank = QUESTIONS if bank is None else bank\n    return [q["slot"] for q in bank if q.get("critical")]\n\n\ndef pending_questions(\n    state: dict[str, Any],\n    bank: list[dict] | None = None,\n) -> list[dict]:\n    """Return bank questions whose slot is not yet ``filled``."""\n    bank = QUESTIONS if bank is None else bank\n    slots = state.get("slots", {})\n    return [q for q in bank if slots.get(q["slot"]) != "filled"]\n\n\ndef session_questions(\n    state: dict[str, Any],\n    bank: list[dict] | None = None,\n) -> list[dict]:\n    """Return this session\'s ask list: pending, priority-ordered, quota-capped.\n\n    The cap is the integration mode\'s question quota (observe asks 1-2, guided a\n    few, active unlimited). Blocking questions sort first, so a quota can never\n    hide one.\n    """\n    pending = sorted(\n        pending_questions(state, bank),\n        key=lambda q: _PRIORITY_ORDER.get(q.get("priority", "normal"), 2),\n    )\n    quota = question_quota(state)\n    return pending if quota is None else pending[:quota]\n\n\ndef answer_is_substantive(question: dict, answer: str) -> bool:\n    """True when ``answer`` passes the anti-gaming floor for this slot.\n\n    Completeness counts only non-placeholder content: no leftover ``${slot}``\n    marker, not a stock placeholder word, and at least the slot\'s ``min_len``\n    characters — so an autonomous run can\'t graduate on hollow answers.\n    """\n    text = answer.strip()\n    if not text or "${" in text:\n        return False\n    # Strip surrounding punctuation before the placeholder-word check so\n    # "todo." / "tbd!" / "n/a?" cannot slip past the exact-match set.\n    if text.lower().strip(_ANSWER_STRIP) in _PLACEHOLDER_ANSWERS:\n        return False\n    # Content-free answers never fill a slot: no alphanumeric char at all\n    # ("??", "...", "!!"), or a single character repeated ("aaaa", "....").\n    if not any(ch.isalnum() for ch in text) or len(set(text)) == 1:\n        return False\n    return len(text) >= int(question.get("min_len", 1))\n\n\ndef _set_without_open_question(backend: Any, question_id: str | None) -> None:\n    """Drop ``question_id`` from open_questions via ``backend.set`` (no flush).\n\n    Called *inside* a transaction so the slot fill and its escalation\n    resolution commit in one atomic flush — a crash between two separate\n    flushes once left a filled slot with a stale open question that nothing\n    automatic could clear.\n    """\n    if not question_id:\n        return\n    open_questions = list(backend.get("open_questions", []))\n    if question_id in open_questions:\n        open_questions.remove(question_id)\n        backend.set("open_questions", open_questions)\n\n\ndef record_answer(backend: Any, question: dict, answer: str, *, source: str) -> None:\n    """Fill ``question``\'s slot from an answer.\n\n    ``source="user"`` confirms the slot (``filled``) when the answer passes the\n    anti-gaming floor (``partial`` otherwise); any other source records a\n    ``provisional`` self-answer that must be confirmed before it counts. A\n    filled answer also resolves the question\'s escalated open-question entry.\n    """\n    if source == "user":\n        status = "filled" if answer_is_substantive(question, answer) else "partial"\n    else:\n        status = "provisional"\n    slots = dict(backend.get("slots", {}))\n    values = dict(backend.get("slot_values", {}))\n    slots[question["slot"]] = status\n    values[question["slot"]] = {\n        "value": answer,\n        "source": source,\n        "question_id": question["id"],\n    }\n    with backend.transaction():\n        backend.set("slots", slots)\n        backend.set("slot_values", values)\n        if status == "filled":\n            _set_without_open_question(backend, question["id"])\n\n\ndef confirm_slot(backend: Any, slot: str, *, source: str) -> bool:\n    """Promote a ``provisional`` slot to ``filled`` (the confirmation seam).\n\n    ``source`` records who confirmed (``"user"`` or ``"reviewer:<name>"``).\n    Returns False when the slot is not provisional (nothing to confirm).\n    """\n    slots = dict(backend.get("slots", {}))\n    if slots.get(slot) != "provisional":\n        return False\n    values = dict(backend.get("slot_values", {}))\n    entry = dict(values.get(slot, {}))\n    entry["source"] = f"confirmed:{source}"\n    slots[slot] = "filled"\n    values[slot] = entry\n    with backend.transaction():\n        backend.set("slots", slots)\n        backend.set("slot_values", values)\n        _set_without_open_question(backend, entry.get("question_id"))\n    return True\n\n\ndef run_session(\n    backend: Any,\n    answers: dict[str, str],\n    *,\n    autonomous: bool = False,\n    bank: list[dict] | None = None,\n) -> dict[str, Any]:\n    """Run one interview session, then attempt graduation.\n\n    ``answers`` maps slot -> user answer. A pending question with a user answer is\n    confirmed; otherwise, in ``autonomous`` mode it is self-answered provisionally\n    (within the integration mode\'s question quota — blocking questions sort first,\n    so the quota never starves one). A session that leaves no blocking question\n    unanswered extends the quiet streak; any unanswered blocking question resets\n    it AND escalates onto ``open_questions``, which holds graduation until the\n    question is answered.\n    """\n    bank = QUESTIONS if bank is None else bank\n    pending = sorted(\n        pending_questions(backend.data, bank),\n        key=lambda q: _PRIORITY_ORDER.get(q.get("priority", "normal"), 2),\n    )\n    quota = question_quota(backend.data)\n    left_blocking = False\n    self_answered = 0\n    for question in pending:\n        slot = question["slot"]\n        blocking = question.get("priority") == "blocking"\n        if slot in answers:\n            record_answer(backend, question, answers[slot], source="user")\n            continue\n        if autonomous and (quota is None or self_answered < quota):\n            # Never downgrade an existing provisional value (e.g. an\n            # adopt-time derived answer) to a placeholder assumption — the\n            # slot already carries better content awaiting confirmation.\n            if backend.get("slots", {}).get(slot) != "provisional":\n                record_answer(\n                    backend, question, f"ASSUMED: {slot}", source="assumption"\n                )\n                self_answered += 1\n            if not blocking:\n                continue\n            # A provisional self-answer does NOT discharge a blocking question\n            # — it must still escalate, or an autonomous run could graduate on\n            # an unconfirmed assumption for the one slot marked blocking.\n        elif not blocking:\n            continue\n        left_blocking = True\n        open_questions = list(backend.get("open_questions", []))\n        if question["id"] not in open_questions:\n            open_questions.append(question["id"])\n            backend.set("open_questions", open_questions)\n\n    backend.set("session_count", int(backend.get("session_count", 0)) + 1)\n    quiet = int(backend.get("quiet_sessions", 0))\n    backend.set("quiet_sessions", 0 if left_blocking else quiet + 1)\n\n    graduated = maybe_graduate(backend, critical_slots(bank))\n    return {\n        "session": backend.get("session_count"),\n        "pending_after": len(pending_questions(backend.data, bank)),\n        "graduated": graduated,\n        "stage": backend.get("stage"),\n    }\n',
    'engine/checks/check_docs.py': '"""Generic doc-hygiene checker (config-driven port of ``check_docs``).\n\nThree portable checks, every input supplied by the caller (from config) rather\nthan hardcoded:\n\n  1. **badge**      — every ``*.md`` under ``docs_root`` (non-ADR) carries a\n     ``> **Status:** `<token>``` line in its first 12 lines, ``<token>`` drawn\n     from the project\'s allowed taxonomy.\n  2. **link**       — every relative markdown link ``[text](path)`` resolves to\n     an existing file (external / anchor-only links are skipped).\n  3. **reachable**  — every live doc is reachable by following links + backtick\n     ``<docs>/*.md`` refs from a read-path root (the read-path docs + any\n     ``README.md``). Orphans fail unless badged ``historical`` / ``archive`` or\n     an ADR.\n\nThe host\'s soft ratchets (top-level pile, recently-shipped) and the\nsuperbot-specific freshness rule are intentionally left behind — they are\nproject policy, not portable mechanism. Pure stdlib; returns findings rather\nthan printing so the CLI owns all output.\n"""\n\nfrom __future__ import annotations\n\nimport re\nfrom collections import deque\nfrom collections.abc import Collection, Sequence\nfrom pathlib import Path\nfrom typing import NamedTuple\n\n\nclass Finding(NamedTuple):\n    """One doc-hygiene violation: ``path`` is relative to ``docs_root``."""\n\n    path: str\n    kind: str\n    message: str\n\n\n# `> **Status:** `<token>`` — the machine-readable badge (rich text may follow).\n_BADGE_RE = re.compile(r"\\*\\*Status:\\*\\*\\s*`([a-z-]+)`")\n# ADR filename: NNN-something.md (exempt — ADRs use their own Accepted/Superseded).\n_ADR_RE = re.compile(r"^\\d+-.*\\.md$")\n# Markdown link target: [text](target).\n_MD_LINK_RE = re.compile(r"\\[[^\\]]*\\]\\(([^)]+)\\)")\n# Badges whose docs are retired content and need no inbound link.\n_EXEMPT_BADGES = frozenset({"historical", "archive"})\n\n_BADGE_MISSING = "missing `> **Status:** `<token>`` in first 12 lines"\n_ORPHAN_MSG = (\n    "orphan: not reachable from any read-path doc / README "\n    "(link it from one, or badge it historical/archive)"\n)\n\n\ndef _md_files(docs_root: Path) -> list[Path]:\n    """Return every ``*.md`` under ``docs_root`` (sorted, empty if absent)."""\n    if not docs_root.exists():\n        return []\n    return sorted(docs_root.rglob("*.md"))\n\n\ndef _is_adr(path: Path) -> bool:\n    """True for ``decisions/NNN-*.md`` ADR files (badge-exempt)."""\n    return path.parent.name == "decisions" and bool(_ADR_RE.match(path.name))\n\n\ndef badge_token(path: Path) -> str | None:\n    """Return the doc\'s Status-badge token from its first 12 lines, or None.\n\n    Public: the trigger detector (and any host tooling) classifies docs by this\n    same badge scan — one badge reader, not per-module copies. An unreadable or\n    non-UTF-8 file reads as badge-less rather than crashing the whole scan.\n    """\n    try:\n        head = "\\n".join(path.read_text(encoding="utf-8").splitlines()[:12])\n    except (OSError, UnicodeDecodeError):\n        return None\n    match = _BADGE_RE.search(head)\n    return match.group(1) if match else None\n\n\n# Backward-compatible alias for the original private name.\n_badge_token = badge_token\n\n\ndef _link_target(raw: str) -> str:\n    """Normalise a markdown link target (drop ``<>``, title, ``#anchor``)."""\n    target = raw.strip()\n    if target.startswith("<") and ">" in target:\n        target = target[1:].split(">", 1)[0]\n    parts = target.split()\n    target = parts[0] if parts else target\n    return target.split("#", 1)[0]\n\n\ndef _backtick_docs_re(docs_root: Path) -> re.Pattern[str]:\n    """Compile the ``<docs>/*.md`` backtick-ref pattern for this doc root."""\n    name = re.escape(docs_root.name)\n    return re.compile(rf"`({name}/[\\w./-]+\\.md)`")\n\n\ndef check_badges(docs_root: Path, badge_tokens: Collection[str]) -> list[Finding]:\n    """Every non-ADR doc must declare a Status badge from the taxonomy."""\n    allowed = set(badge_tokens)\n    findings: list[Finding] = []\n    for f in _md_files(docs_root):\n        if _is_adr(f):\n            continue\n        rel = f.relative_to(docs_root).as_posix()\n        token = badge_token(f)\n        if token is None:\n            findings.append(Finding(rel, "badge", _BADGE_MISSING))\n        elif token not in allowed:\n            allowed_list = ", ".join(sorted(allowed))\n            findings.append(\n                Finding(\n                    rel,\n                    "badge",\n                    f"invalid badge token `{token}` (allowed: {allowed_list})",\n                ),\n            )\n    return findings\n\n\ndef check_links(docs_root: Path) -> list[Finding]:\n    """Relative markdown links inside ``docs_root`` must resolve.\n\n    An unreadable / non-UTF-8 file is reported as an ``encoding`` finding\n    instead of crashing the scan (one bad byte must not take down triggers,\n    ``maintain``, and ``check`` together).\n    """\n    findings: list[Finding] = []\n    for f in _md_files(docs_root):\n        rel = f.relative_to(docs_root).as_posix()\n        try:\n            lines = f.read_text(encoding="utf-8").splitlines()\n        except (OSError, UnicodeDecodeError) as exc:\n            findings.append(Finding(rel, "encoding", f"unreadable as UTF-8: {exc}"))\n            continue\n        for lineno, line in enumerate(lines, 1):\n            for raw in _MD_LINK_RE.findall(line):\n                if raw.startswith(("http://", "https://", "mailto:", "#")):\n                    continue\n                target = _link_target(raw)\n                if not target or target.startswith(("http", "mailto:")):\n                    continue\n                if not (f.parent / target).resolve().exists():\n                    msg = f"L{lineno}: dead link -> {raw}"\n                    findings.append(Finding(rel, "link", msg))\n    return findings\n\n\ndef _outgoing_links(path: Path, docs_root: Path) -> set[Path]:\n    """Resolve every relative markdown link + backtick ``<docs>/*.md`` ref."""\n    out: set[Path] = set()\n    backtick = _backtick_docs_re(docs_root)\n    root = docs_root.parent\n    try:\n        text = path.read_text(encoding="utf-8")\n    except (OSError, UnicodeDecodeError):\n        return out\n    for line in text.splitlines():\n        for raw in _MD_LINK_RE.findall(line):\n            if raw.startswith(("http://", "https://", "mailto:", "#")):\n                continue\n            target = _link_target(raw)\n            if target:\n                out.add((path.parent / target).resolve())\n        for ref in backtick.findall(line):\n            out.add((root / ref).resolve())\n    return out\n\n\ndef check_reachable(docs_root: Path, readpath_docs: Sequence[str]) -> list[Finding]:\n    """Every live doc must be reachable from a read-path root / README.\n\n    Walks the doc graph (markdown links + backtick ``<docs>/*.md`` refs) from the\n    roots; any doc not reached — and not ``historical`` / ``archive`` badged or an\n    ADR — is an orphan.\n    """\n    roots = [docs_root / name for name in readpath_docs]\n    roots += sorted(docs_root.rglob("README.md"))\n    seen: set[Path] = set()\n    queue: deque[Path] = deque()\n    for root in roots:\n        resolved = root.resolve()\n        if root.exists() and resolved not in seen:\n            seen.add(resolved)\n            queue.append(resolved)\n    while queue:\n        cur = queue.popleft()\n        if cur.suffix != ".md" or not cur.exists():\n            continue\n        for nxt in _outgoing_links(cur, docs_root):\n            if nxt not in seen and nxt.suffix == ".md" and nxt.exists():\n                seen.add(nxt)\n                queue.append(nxt)\n\n    findings: list[Finding] = []\n    for f in _md_files(docs_root):\n        if f.resolve() in seen or _is_adr(f):\n            continue\n        if badge_token(f) in _EXEMPT_BADGES:\n            continue\n        rel = f.relative_to(docs_root).as_posix()\n        findings.append(Finding(rel, "reachable", _ORPHAN_MSG))\n    return findings\n\n\ndef run_doc_checks(\n    docs_root: Path,\n    badge_tokens: Collection[str],\n    readpath_docs: Sequence[str],\n) -> list[Finding]:\n    """Run every doc check and return the combined findings."""\n    return (\n        check_badges(docs_root, badge_tokens)\n        + check_links(docs_root)\n        + check_reachable(docs_root, readpath_docs)\n    )\n',
    'engine/checks/check_session_log.py': '"""Generic session-log completeness checker (config-driven port).\n\nThe session workflow asks every session to end with a\n``<sessions_dir>/<date>-<slug>.md`` log that carries a set of required markers\n(by default: a Status badge, a session-idea flag, and a previous-session review).\nEach marker is a ``{"label", "needle"}`` pair from ``substrate.config.json``, so a\nhost tunes the ritual without touching engine code.\n\nUnlike the host\'s version this port does **not** shell out to ``git`` to pick the\n"current" log — ``subprocess`` is banned in engine code and is host-CI sugar\nanyway. The current log is the newest ``*.md`` by mtime under ``sessions_dir``\n(the CLI also accepts an explicit ``--file``). Pure stdlib; returns the missing\nmarkers rather than printing.\n"""\n\nfrom __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\nfrom pathlib import Path\n\n\ndef missing_markers(text: str, markers: Sequence[Mapping[str, str]]) -> list[str]:\n    """Return the labels of markers whose needle is absent from ``text``.\n\n    Tolerant of partial host-config entries: a marker without a ``needle`` is\n    skipped (nothing to search for) rather than raising, and a missing\n    ``label`` reports as ``"?"``.\n    """\n    lower = text.lower()\n    return [\n        m.get("label", "?")\n        for m in markers\n        if m.get("needle") and m.get("needle", "").lower() not in lower\n    ]\n\n\ndef latest_session_log(sessions_dir: Path) -> Path | None:\n    """Best guess at this session\'s log: newest ``*.md`` by mtime (skip README)."""\n    if not sessions_dir.is_dir():\n        return None\n    candidates = [p for p in sessions_dir.glob("*.md") if p.name != "README.md"]\n    if not candidates:\n        return None\n    return max(candidates, key=lambda p: p.stat().st_mtime)\n\n\ndef check_log(path: Path, markers: Sequence[Mapping[str, str]]) -> list[str]:\n    """Return the missing-marker labels for one log file (all if unreadable)."""\n    try:\n        text = path.read_text(encoding="utf-8")\n    except OSError:\n        return [m["label"] for m in markers]\n    return missing_markers(text, markers)\n',
    'engine/checks/check_namespace.py': '"""Portable namespace / shadowing guard (Lane B6, the Q-0200 class).\n\nThree AST-level checks over the Python roots a host configures\n(``config.namespace``):\n\n  1. **in-module shadowing** — the same top-level ``def`` / ``class`` name\n     bound twice in one module; the later binding silently wins and the\n     earlier one dies unnoticed (superbot\'s ``round_composition`` collision,\n     caught only at CI).\n  2. **cross-module collision** — the same public (non-underscore) top-level\n     name defined in two modules of one package, unless one of the two is the\n     package\'s ``__init__.py`` (the deliberate re-export pattern).\n  3. **reserved names** — a name from the configured reserved map\n     (``{"Name": "canonical/module.py"}``) defined outside its canonical\n     module.\n\nUses only stdlib ``ast``; a file that fails to parse becomes a\n``namespace-parse`` finding, never an exception. Findings reuse the\n``Finding`` record from ``engine.checks.check_docs`` with paths relative to\nthe scanned root where possible.\n"""\n\nfrom __future__ import annotations\n\nimport ast\nfrom pathlib import Path\n\nfrom engine.checks.check_docs import Finding\n\n_NS_DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)\n\n\ndef _ns_rel(path: Path, root: Path) -> str:\n    """Return ``path`` relative to ``root`` (posix) when possible, else str."""\n    try:\n        return path.relative_to(root).as_posix()\n    except ValueError:\n        return path.as_posix()\n\n\ndef _ns_py_files(root: Path) -> list[Path]:\n    """Return the ``*.py`` files under ``root`` (or ``root`` itself if a file)."""\n    if root.is_file():\n        return [root] if root.suffix == ".py" else []\n    if not root.is_dir():\n        return []\n    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)\n\n\ndef _ns_top_level_defs(tree: ast.Module) -> list[tuple[str, int]]:\n    """Return ``(name, lineno)`` for every top-level def/class in ``tree``."""\n    return [\n        (node.name, node.lineno)\n        for node in tree.body\n        if isinstance(node, _NS_DEF_NODES)\n    ]\n\n\ndef _ns_overloaded_names(tree: ast.Module) -> set[str]:\n    """Names whose top-level defs carry ``@overload`` — not shadowing.\n\n    ``@typing.overload`` stacks re-bind the same name by design; flagging them\n    as in-module shadowing was a verified false positive.\n    """\n    names: set[str] = set()\n    for node in tree.body:\n        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            continue\n        for deco in node.decorator_list:\n            if (\n                isinstance(deco, ast.Name)\n                and deco.id == "overload"\n                or isinstance(deco, ast.Attribute)\n                and deco.attr == "overload"\n            ):\n                names.add(node.name)\n    return names\n\n\ndef _ns_dispatch_registered_names(tree: ast.Module) -> set[str]:\n    """Names whose top-level defs carry ``@<x>.register`` — not shadowing.\n\n    The ``functools.singledispatch`` idiom re-binds the same name (canonically\n    ``def _``) once per registered type; the ``.register`` decorator captures\n    each function, so the last global binding is irrelevant. Flagging the\n    repeated defs as in-module shadowing was a verified false positive.\n    Handles both ``@process.register`` and ``@process.register(int)``.\n    """\n    names: set[str] = set()\n    for node in tree.body:\n        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            continue\n        for deco in node.decorator_list:\n            target = deco.func if isinstance(deco, ast.Call) else deco\n            if isinstance(target, ast.Attribute) and target.attr == "register":\n                names.add(node.name)\n    return names\n\n\ndef _ns_matches_canonical(rel: str, canonical: str) -> bool:\n    """True when the scanned relpath is the reserved name\'s canonical module."""\n    canon = canonical.replace("\\\\", "/").lstrip("./")\n    return rel == canon or rel.endswith(f"/{canon}")\n\n\ndef check_namespace(\n    roots: list[Path],\n    *,\n    reserved: dict[str, str] | None = None,\n) -> list[Finding]:\n    """Run the three namespace checks over ``roots``; return the findings.\n\n    ``reserved`` maps a name to the canonical module relpath allowed to define\n    it. Kinds: ``namespace`` for collisions, ``namespace-parse`` for files\n    that fail to parse (reported, never raised).\n    """\n    reserved = reserved or {}\n    findings: list[Finding] = []\n    # (package dir, public name) -> [(rel, module filename, lineno)]\n    package_defs: dict[tuple[str, str], list[tuple[str, str, int]]] = {}\n\n    for root in roots:\n        rel_base = root.parent if root.is_file() else root\n        for py in _ns_py_files(root):\n            rel = _ns_rel(py, rel_base)\n            try:\n                tree = ast.parse(py.read_text(encoding="utf-8"))\n            except (SyntaxError, ValueError, OSError, UnicodeDecodeError) as exc:\n                lineno = getattr(exc, "lineno", None)\n                where = f"L{lineno}: " if lineno else ""\n                msg = f"{where}failed to parse: {exc.__class__.__name__}: {exc}"\n                findings.append(Finding(rel, "namespace-parse", msg))\n                continue\n\n            seen: dict[str, int] = {}\n            # `_` is the conventional throwaway (and the canonical\n            # singledispatch register target); `.register`-decorated defs are\n            # the named-function dispatch form — neither is real shadowing.\n            exempt_shadow = _ns_overloaded_names(tree)\n            exempt_shadow |= _ns_dispatch_registered_names(tree)\n            for name, lineno in _ns_top_level_defs(tree):\n                if name in seen and name not in exempt_shadow and name != "_":\n                    msg = (\n                        f"`{name}` defined twice in one module "\n                        f"(L{seen[name]} and L{lineno}) — the later def "\n                        "silently shadows the earlier"\n                    )\n                    findings.append(Finding(rel, "namespace", msg))\n                seen.setdefault(name, lineno)\n                if not name.startswith("_"):\n                    key = (py.parent.resolve().as_posix(), name)\n                    package_defs.setdefault(key, []).append(\n                        (rel, py.name, lineno),\n                    )\n                canonical = reserved.get(name)\n                if canonical is not None and not _ns_matches_canonical(\n                    rel,\n                    canonical,\n                ):\n                    msg = (\n                        f"L{lineno}: reserved name `{name}` defined outside "\n                        f"its canonical module `{canonical}`"\n                    )\n                    findings.append(Finding(rel, "namespace", msg))\n\n    for (_, name), sites in sorted(package_defs.items()):\n        modules = {filename for _, filename, _ in sites}\n        non_init = [s for s in sites if s[1] != "__init__.py"]\n        if len(modules) < 2 or len({s[1] for s in non_init}) < 2:\n            continue  # one module, or an __init__ re-export pair\n        site_list = ", ".join(f"{rel}:L{lineno}" for rel, _, lineno in non_init)\n        msg = (\n            f"public name `{name}` defined in multiple modules of one "\n            f"package ({site_list}) — rename or move to a shared home"\n        )\n        findings.append(Finding(non_init[0][0], "namespace", msg))\n    return findings\n',
    'engine/checks/check_seam_authority.py': 'r"""Config-driven seam-authority fences (Lane B6).\n\nA *seam* is a boundary the host declares in ``config.seams`` — "all writes go\nthrough the mutation service", "no direct pool access outside the db layer" —\ngeneralising superbot\'s hardcoded architecture fences into pure data. Each\nseam is a dict::\n\n    {"name": "db-seam",\n     "paths": ["src/**/*.py"],        # globs to scan, relative to root\n     "forbidden": "pool\\\\.execute",   # regex; a hit is a violation\n     "allowed": ["src/db/**"],        # exempt globs (the seam\'s own home)\n     "message": "call db.* helpers, never the pool directly"}\n\nThe scan is plain line-by-line text matching (no AST, no imports) so it works\non any language the host points it at. A regex hit in a non-exempt file\nbecomes a ``Finding(kind="seam")`` whose message carries the seam name, the\nconfigured message, and the line number. Findings reuse the ``Finding``\nrecord from ``engine.checks.check_docs``; unreadable/binary files are skipped.\n"""\n\nfrom __future__ import annotations\n\nimport re\nfrom pathlib import Path\n\nfrom engine.checks.check_docs import Finding\n\n\ndef _seam_files(root: Path, globs: list[str]) -> list[Path]:\n    """Return the de-duplicated files matched by ``globs`` under ``root``."""\n    matched: set[Path] = set()\n    for pattern in globs:\n        for candidate in root.glob(pattern):\n            if candidate.is_file():\n                matched.add(candidate)\n    return sorted(matched)\n\n\ndef _seam_exempt_files(root: Path, allowed: list[str]) -> set[Path]:\n    """Resolve the exempt set with the SAME glob semantics as ``paths``.\n\n    fnmatch let ``*`` cross ``/`` — an ``allowed`` pattern like ``src/*``\n    silently exempted ``src/sub/hack.py`` and opened a fence gap. Re-globbing\n    with ``root.glob`` keeps both sides of the seam on pathlib semantics.\n\n    A glob hit that is a *directory* is expanded to the files under it — a\n    trailing ``**`` (the documented ``src/db/**`` "own home" form) matches only\n    directories in ``Path.glob``, so exempting by raw glob hits compared the\n    file being scanned against a set of dirs and exempted **nothing**: a seam\n    flagged its own home. Directory hits now contribute their whole file\n    subtree (the ``economy`` reference-scan idiom), so ``src/db/**``,\n    ``src/db/*`` and ``src/db/**/*`` all exempt the subtree as documented.\n    """\n    exempt: set[Path] = set()\n    for pattern in allowed:\n        for hit in root.glob(pattern):\n            if hit.is_file():\n                exempt.add(hit)\n            elif hit.is_dir():\n                exempt.update(p for p in hit.rglob("*") if p.is_file())\n    return exempt\n\n\ndef check_seam_authority(root: Path, seams: list[dict]) -> list[Finding]:\n    """Scan the configured seams under ``root``; return the violations.\n\n    Each seam dict supplies ``name``, ``paths`` (globs to scan), ``forbidden``\n    (a regex), optional ``allowed`` (exempt globs), and ``message``. A seam\n    with an invalid regex is itself reported as a finding rather than raising\n    (a broken fence should fail loud in the report, not crash the check).\n    """\n    findings: list[Finding] = []\n    for seam in seams:\n        name = seam.get("name", "unnamed")\n        message = seam.get("message", "forbidden pattern")\n        pattern = seam.get("forbidden", "")\n        if not pattern:\n            # An empty pattern\'s ``.search`` matches every line — a seam with no\n            # ``forbidden`` would flag every line of every in-scope file. That is\n            # a misconfiguration; report it loud instead of drowning the report.\n            msg = f"seam `{name}`: no `forbidden` regex configured — seam skipped"\n            findings.append(Finding("", "seam", msg))\n            continue\n        try:\n            forbidden = re.compile(pattern)\n        except re.error as exc:\n            msg = f"seam `{name}`: invalid forbidden regex: {exc}"\n            findings.append(Finding("", "seam", msg))\n            continue\n        exempt = _seam_exempt_files(root, list(seam.get("allowed", [])))\n        for path in _seam_files(root, list(seam.get("paths", []))):\n            rel = path.relative_to(root).as_posix()\n            if path in exempt:\n                continue\n            try:\n                text = path.read_text(encoding="utf-8")\n            except (OSError, UnicodeDecodeError):\n                continue\n            for lineno, line in enumerate(text.splitlines(), 1):\n                if forbidden.search(line):\n                    msg = f"L{lineno}: seam `{name}`: {message}"\n                    findings.append(Finding(rel, "seam", msg))\n    return findings\n',
    'engine/checks/check_orientation_budget.py': '"""Orientation-budget gate — the K0 <=7,000-word boot-read cap (Lane B6).\n\nOrientation cost is the tax every session pays before real work starts, so\nthe kit meters it: the *boot set* (``config.orientation["boot_docs"]``,\nfalling back to ``config.readpath_docs`` when empty) must total no more than\n``config.orientation["budget_words"]`` words. Boot-doc entries name files\nunder ``docs_root``; an entry containing ``/`` resolves from the project root\ninstead, so hosts can meter root-level docs (a journal, a CLAUDE.md) too.\n\nPer-doc self-caps ride on top: a doc whose first 12 lines declare\n``substrate-budget: N words`` is individually capped at N — a living doc can\npin its own growth ceiling without touching config.\n\nFinding kinds: ``orientation-missing`` (a boot doc is absent),\n``orientation-budget`` (the total blows the budget), ``orientation-doc-cap``\n(a self-capped doc outgrew its declared cap). Findings reuse the ``Finding``\nrecord from ``engine.checks.check_docs``.\n"""\n\nfrom __future__ import annotations\n\nimport re\nfrom pathlib import Path\n\nfrom engine.checks.check_docs import Finding\nfrom engine.lib.config import Config\n\n# `substrate-budget: 500 words` — the per-doc self-cap declaration.\n_OB_SELF_CAP_RE = re.compile(r"substrate-budget:\\s*(\\d+)\\s*words", re.IGNORECASE)\n_OB_HEAD_LINES = 12\n_OB_TOTAL_KEY = "_total"\n\n\ndef _ob_word_count(path: Path) -> int | None:\n    """Return the doc\'s word count, or ``None`` when it cannot be read."""\n    try:\n        return len(path.read_text(encoding="utf-8").split())\n    except (OSError, UnicodeDecodeError):\n        return None\n\n\ndef _ob_self_cap(path: Path) -> int | None:\n    """Return the doc\'s declared self-cap from its first 12 lines, if any."""\n    try:\n        head = path.read_text(encoding="utf-8").splitlines()[:_OB_HEAD_LINES]\n    except (OSError, UnicodeDecodeError):\n        return None\n    match = _OB_SELF_CAP_RE.search("\\n".join(head))\n    return int(match.group(1)) if match else None\n\n\ndef _ob_rel(path: Path, root: Path) -> str:\n    """Return ``path`` relative to ``root`` (posix) when possible, else str."""\n    try:\n        return path.relative_to(root).as_posix()\n    except ValueError:\n        return path.as_posix()\n\n\ndef orientation_word_count(root: Path, boot_docs: list[Path]) -> dict[str, int]:\n    """Return per-doc word counts plus a ``_total`` for the boot set.\n\n    Keys are paths relative to ``root`` where possible. A missing or\n    unreadable doc counts 0 here — ``check_orientation_budget`` is the layer\n    that reports it.\n    """\n    counts: dict[str, int] = {}\n    total = 0\n    for doc in boot_docs:\n        words = _ob_word_count(doc) or 0\n        counts[_ob_rel(doc, root)] = words\n        total += words\n    counts[_OB_TOTAL_KEY] = total\n    return counts\n\n\ndef _ob_boot_paths(root: Path, config: Config) -> list[Path]:\n    """Resolve the configured boot set to concrete paths.\n\n    Explicit ``orientation["boot_docs"]`` entries: a bare name resolves under\n    ``docs_root``, an entry with ``/`` resolves from the project root. The\n    ``readpath_docs`` fallback resolves under ``docs_root`` unconditionally —\n    matching ``check_reachable``, which reads the same key.\n    """\n    orientation = config.orientation or {}\n    docs_root = root / config.docs_root\n    explicit = list(orientation.get("boot_docs") or [])\n    if explicit:\n        # Explicit boot docs: a bare name resolves under docs_root, an entry\n        # with "/" resolves from the project root (CONSTITUTION.md etc.).\n        return [root / e if "/" in e else docs_root / e for e in explicit]\n    # readpath_docs fallback: resolve under docs_root unconditionally, matching\n    # check_reachable — the two consumers of that key must agree.\n    return [docs_root / e for e in config.readpath_docs]\n\n\ndef check_orientation_budget(root: Path, config: Config) -> list[Finding]:\n    """Meter the boot-read set against the orientation budget.\n\n    Reports missing boot docs (``orientation-missing``), a total word count\n    over ``orientation["budget_words"]`` (``orientation-budget``), and any doc\n    that outgrew its own ``substrate-budget: N words`` self-cap\n    (``orientation-doc-cap``).\n    """\n    findings: list[Finding] = []\n    boot_paths = _ob_boot_paths(root, config)\n    for doc in boot_paths:\n        if not doc.is_file():\n            msg = "boot doc missing — fix the path or the orientation config"\n            findings.append(Finding(_ob_rel(doc, root), "orientation-missing", msg))\n\n    counts = orientation_word_count(root, boot_paths)\n    budget = int((config.orientation or {}).get("budget_words", 7000))\n    total = counts[_OB_TOTAL_KEY]\n    if total > budget:\n        msg = (\n            f"boot-read set totals {total} words, over the "\n            f"{budget}-word orientation budget — trim or demote a boot doc"\n        )\n        findings.append(Finding(_OB_TOTAL_KEY, "orientation-budget", msg))\n\n    for doc in boot_paths:\n        cap = _ob_self_cap(doc)\n        if cap is None:\n            continue\n        words = counts.get(_ob_rel(doc, root), 0)\n        if words > cap:\n            msg = f"doc is {words} words, over its {cap}-word self-cap"\n            findings.append(Finding(_ob_rel(doc, root), "orientation-doc-cap", msg))\n    return findings\n',
    'engine/ledger.py': '"""Decision ledger — the ``[D-NNNN]`` provenance-separated rulebook (Lane B6).\n\nImplements the kit\'s ``docs/decisions.md`` grammar (plan: Q-0214.4 depth — a\nconstitution cites decisions by id instead of narrating them inline). One\nentry is::\n\n    ## [D-0001] <title>\n    - status: decided | superseded | retired\n    - date: YYYY-MM-DD\n    - supersedes: D-NNNN        (optional)\n    - superseded-by: D-NNNN     (stamped on the OLD entry when superseded)\n    - verdict: <one ruling line>\n    - why: <2-3 lines, continuation lines allowed>\n    - provenance: <link or ref>\n\n``parse_ledger`` is tolerant of prose between entries (the ledger is a living\nmarkdown doc, not a database). ``append_decision`` assigns the next id and —\nwhen superseding — rewrites the old entry in place so the chain is stamped on\nboth ends. ``check_ledger`` and ``check_stamp_discipline`` are the hygiene\ncheckers, reusing the ``Finding`` record from ``engine.checks.check_docs``.\nPure stdlib; every write goes through ``atomic_write_text``.\n"""\n\nfrom __future__ import annotations\n\nimport re\nfrom datetime import date as _led_date\nfrom pathlib import Path\n\nfrom engine.checks.check_docs import Finding\nfrom engine.lib.atomicio import atomic_write_text\n\nLEDGER_FILENAME = "decisions.md"\n\n# `## [D-0001] <title>` — the strict entry heading.\n_LED_HEADING_RE = re.compile(r"^## \\[(D-\\d{3,})\\] (.+)$")\n# Any `## ` heading that *tries* to be an entry but fails the strict form.\n_LED_HEADING_ATTEMPT_RE = re.compile(r"^##\\s*\\[?\\s*D-", re.IGNORECASE)\n# `- key: value` field line inside an entry block.\n_LED_FIELD_RE = re.compile(r"^- ([a-z-]+):\\s*(.*)$")\n# A bare decision id, for supersedes targets and stamp-discipline citations.\n_LED_ID_RE = re.compile(r"\\bD-\\d{3,}\\b")\n_LED_DATE_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}$")\n\n_LED_STATUSES = frozenset({"decided", "superseded", "retired"})\n_LED_REQUIRED_FIELDS = ("status", "date", "verdict", "why", "provenance")\n\n_LED_HEADER = """# Decisions\n\n> **Status:** `living-ledger` — append-only decision ledger; entries are \\\nsuperseded, never deleted.\n\n<!-- Grammar: ## [D-NNNN] <title> / - status: decided|superseded|retired / \\\n- date: YYYY-MM-DD / - supersedes: D-NNNN (opt) / - superseded-by: D-NNNN \\\n(opt) / - verdict: <one line> / - why: <2-3 lines> / - provenance: <ref> -->\n"""\n\n\ndef _led_field_key(raw: str) -> str:\n    """Map a grammar field name to its entry-dict key (``-`` -> ``_``)."""\n    return raw.replace("-", "_")\n\n\ndef _led_blocks(text: str) -> list[tuple[int, list[str]]]:\n    """Split ``text`` into entry blocks: ``(heading lineno, block lines)``.\n\n    A block starts at any ``## `` heading that looks like a decision entry\n    (strict or malformed) and runs until the next ``## `` heading or EOF.\n    Prose outside blocks is ignored.\n    """\n    blocks: list[tuple[int, list[str]]] = []\n    current: list[str] | None = None\n    for lineno, line in enumerate(text.splitlines(), 1):\n        if line.startswith("## "):\n            current = None\n            if _LED_HEADING_ATTEMPT_RE.match(line):\n                current = [line]\n                blocks.append((lineno, current))\n        elif current is not None:\n            current.append(line)\n    return blocks\n\n\ndef _led_parse_block(lines: list[str]) -> dict | None:\n    """Parse one entry block into a dict, or ``None`` if the heading is bad."""\n    match = _LED_HEADING_RE.match(lines[0])\n    if match is None:\n        return None\n    entry: dict = {\n        "id": match.group(1),\n        "title": match.group(2).strip(),\n        "status": None,\n        "date": None,\n        "supersedes": None,\n        "superseded_by": None,\n        "verdict": None,\n        "why": None,\n        "provenance": None,\n    }\n    last_key: str | None = None\n    for line in lines[1:]:\n        field = _LED_FIELD_RE.match(line)\n        if field is not None:\n            key = _led_field_key(field.group(1))\n            if key in entry and key not in ("id", "title"):\n                entry[key] = field.group(2).strip()\n                last_key = key\n            else:\n                last_key = None\n        elif line[:1].isspace() and line.strip() and last_key is not None:\n            # Continuation line (indented) — the multi-line `why` case.\n            entry[last_key] = f"{entry[last_key]}\\n{line.strip()}"\n        elif not line.strip():\n            last_key = None\n    return entry\n\n\ndef parse_ledger(text: str) -> list[dict]:\n    """Parse ledger ``text`` into entry dicts, tolerating prose between entries.\n\n    Malformed headings are skipped here (``check_ledger`` reports them);\n    missing fields parse as ``None``.\n    """\n    entries: list[dict] = []\n    for _, lines in _led_blocks(text):\n        entry = _led_parse_block(lines)\n        if entry is not None:\n            entries.append(entry)\n    return entries\n\n\ndef next_decision_id(entries: list[dict]) -> str:\n    """Return the next free decision id (``D-0001`` for an empty ledger)."""\n    highest = 0\n    for entry in entries:\n        try:\n            highest = max(highest, int(entry["id"].split("-", 1)[1]))\n        except (KeyError, IndexError, ValueError):\n            continue\n    return f"D-{highest + 1:04d}"\n\n\ndef _led_format_entry(entry: dict) -> str:\n    """Render one entry dict back into its grammar block."""\n    lines = [f"## [{entry[\'id\']}] {entry[\'title\']}"]\n    lines.append(f"- status: {entry[\'status\']}")\n    lines.append(f"- date: {entry[\'date\']}")\n    if entry.get("supersedes"):\n        lines.append(f"- supersedes: {entry[\'supersedes\']}")\n    if entry.get("superseded_by"):\n        lines.append(f"- superseded-by: {entry[\'superseded_by\']}")\n    lines.append(f"- verdict: {entry[\'verdict\']}")\n    why = str(entry["why"]).split("\\n")\n    lines.append(f"- why: {why[0]}")\n    lines.extend(f"  {cont}" for cont in why[1:])\n    lines.append(f"- provenance: {entry[\'provenance\']}")\n    return "\\n".join(lines)\n\n\ndef _led_stamp_superseded(text: str, old_id: str, new_id: str) -> str:\n    """Rewrite ``old_id``\'s entry in ``text``: status + superseded-by stamp."""\n    out: list[str] = []\n    in_target = False\n    stamped = False\n    for line in text.splitlines():\n        if line.startswith("## "):\n            # ANY level-2 heading ends the current block (mirrors _led_blocks)\n            # — a prose section after the target must never get stamped.\n            heading = _LED_HEADING_RE.match(line)\n            in_target = heading is not None and heading.group(1) == old_id\n        elif in_target and not line.strip():\n            # An entry\'s field block is contiguous and ends at its first blank\n            # line. Without this, a target that is the LAST entry keeps\n            # ``in_target`` true to EOF (no later ``## `` to reset it) and would\n            # silently stamp any field-shaped bullet in trailing prose.\n            in_target = False\n        field = _LED_FIELD_RE.match(line) if in_target else None\n        if field is not None:\n            key = field.group(1)\n            if key == "status":\n                out.append("- status: superseded")\n                out.append(f"- superseded-by: {new_id}")\n                stamped = True\n                continue\n            if key == "superseded-by" and stamped:\n                continue  # replaced above\n        out.append(line)\n    return "\\n".join(out) + ("\\n" if text.endswith("\\n") else "")\n\n\ndef append_decision(\n    path: Path,\n    *,\n    title: str,\n    verdict: str,\n    why: str,\n    provenance: str,\n    supersedes: str | None = None,\n    date: str | None = None,\n) -> dict:\n    """Append a new decision to the ledger at ``path`` and return its dict.\n\n    Creates the file (header + grammar comment) when absent, assigns the next\n    free id, and — when ``supersedes`` names an existing entry — rewrites that\n    old entry in place (``status: superseded`` plus a ``superseded-by`` stamp)\n    so the chain is recorded on both ends. The whole file is written atomically.\n    Raises ``ValueError`` when ``supersedes`` names an id not in the ledger.\n    """\n    text = path.read_text(encoding="utf-8") if path.exists() else _LED_HEADER\n    entries = parse_ledger(text)\n    if supersedes is not None:\n        known = {entry["id"] for entry in entries}\n        if supersedes not in known:\n            msg = f"supersedes target {supersedes} not found in {path.name}"\n            raise ValueError(msg)\n    entry = {\n        "id": next_decision_id(entries),\n        "title": title,\n        "status": "decided",\n        "date": date or _led_date.today().isoformat(),\n        "supersedes": supersedes,\n        "superseded_by": None,\n        "verdict": verdict,\n        "why": why,\n        "provenance": provenance,\n    }\n    if supersedes is not None:\n        text = _led_stamp_superseded(text, supersedes, entry["id"])\n    if not text.endswith("\\n"):\n        text += "\\n"\n    atomic_write_text(path, f"{text}\\n{_led_format_entry(entry)}\\n")\n    return entry\n\n\ndef current_rules(entries: list[dict]) -> list[dict]:\n    """Return the live rule set: supersedes chains resolved, retired dropped.\n\n    An entry is live when its status is neither ``superseded`` nor ``retired``\n    *and* no other entry names it as a supersedes target (chain resolution\n    holds even when the old entry missed its stamp).\n    """\n    replaced = {e["supersedes"] for e in entries if e.get("supersedes")}\n    return [\n        e\n        for e in entries\n        if e.get("status") not in ("superseded", "retired") and e["id"] not in replaced\n    ]\n\n\ndef check_ledger(path: Path) -> list[Finding]:\n    """Validate the ledger grammar; return findings (empty for a clean file).\n\n    Flags: unparseable entry blocks, missing/invalid required fields, duplicate\n    ids, dangling ``supersedes`` targets, non-monotonic ids, and a superseded\n    entry missing its ``superseded-by`` stamp. An absent ledger yields no\n    findings (adoption plants it).\n    """\n    if not path.exists():\n        return []\n    rel = path.name\n    text = path.read_text(encoding="utf-8")\n    findings: list[Finding] = []\n    entries: list[dict] = []\n    for lineno, lines in _led_blocks(text):\n        entry = _led_parse_block(lines)\n        if entry is None:\n            msg = f"L{lineno}: unparseable entry heading: {lines[0].strip()}"\n            findings.append(Finding(rel, "ledger", msg))\n            continue\n        entries.append(entry)\n        for field in _LED_REQUIRED_FIELDS:\n            if not entry.get(field):\n                msg = f"L{lineno}: {entry[\'id\']} missing required field `{field}`"\n                findings.append(Finding(rel, "ledger", msg))\n        status = entry.get("status")\n        if status and status not in _LED_STATUSES:\n            allowed = ", ".join(sorted(_LED_STATUSES))\n            msg = f"L{lineno}: {entry[\'id\']} invalid status `{status}` ({allowed})"\n            findings.append(Finding(rel, "ledger", msg))\n        if entry.get("date") and not _LED_DATE_RE.match(entry["date"]):\n            msg = f"L{lineno}: {entry[\'id\']} invalid date `{entry[\'date\']}`"\n            findings.append(Finding(rel, "ledger", msg))\n        if status == "superseded" and not entry.get("superseded_by"):\n            msg = f"L{lineno}: {entry[\'id\']} superseded without a superseded-by stamp"\n            findings.append(Finding(rel, "ledger", msg))\n\n    seen: set[str] = set()\n    known = {entry["id"] for entry in entries}\n    previous = 0\n    for entry in entries:\n        number = int(entry["id"].split("-", 1)[1])\n        if entry["id"] in seen:\n            findings.append(Finding(rel, "ledger", f"duplicate id {entry[\'id\']}"))\n        elif number <= previous:\n            msg = f"non-monotonic id {entry[\'id\']} after D-{previous:04d}"\n            findings.append(Finding(rel, "ledger", msg))\n        seen.add(entry["id"])\n        previous = max(previous, number)\n        target = entry.get("supersedes")\n        if target and target not in known:\n            msg = f"{entry[\'id\']} supersedes dangling target {target}"\n            findings.append(Finding(rel, "ledger", msg))\n    return findings\n\n\ndef check_stamp_discipline(docs_root: Path, ledger_path: Path) -> list[Finding]:\n    """Flag a decision id cited from more than one doc outside the ledger.\n\n    The provenance-separated model wants each ``D-NNNN`` stamped at exactly one\n    home (the rule it justifies); a second citation is drift risk — when the\n    decision changes, one of the two goes stale. Kind ``stamp`` (warn-class).\n    """\n    if not docs_root.exists():\n        return []\n    ledger_resolved = ledger_path.resolve()\n    citations: dict[str, list[str]] = {}\n    for doc in sorted(docs_root.rglob("*.md")):\n        if doc.resolve() == ledger_resolved:\n            continue\n        try:\n            text = doc.read_text(encoding="utf-8")\n        except (OSError, UnicodeDecodeError):\n            continue\n        rel = doc.relative_to(docs_root).as_posix()\n        for cited in set(_LED_ID_RE.findall(text)):\n            citations.setdefault(cited, []).append(rel)\n    findings: list[Finding] = []\n    for cited, docs in sorted(citations.items()):\n        if len(docs) > 1:\n            cite_list = ", ".join(sorted(docs))\n            msg = (\n                f"{cited} cited from {len(docs)} docs ({cite_list}) — "\n                "stamp each decision at one home"\n            )\n            findings.append(Finding(sorted(docs)[0], "stamp", msg))\n    return findings\n',
    'engine/loop/kpis.py': '"""Workflow KPIs for the self-improving loop (plan section 5, Lane B1).\n\nDeterministic read-only metrics over the state document + sessions directory:\n``router_metrics`` measures the question-router\'s health (slot completeness,\nopen questions, the assumption-confirmation rate that keeps autonomous runs\nhonest), ``workflow_kpis`` adds the session/reflection counters, and\n``kpi_footer`` renders the one-line 📊 summary the orientation and reports\nembed. Pure stdlib; returns data / text, never prints.\n"""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nfrom typing import Any\n\n\ndef _kpi_confirmation_rate(slot_values: dict[str, Any]) -> float:\n    """Return confirmed-over-self-answered for the recorded slot values.\n\n    Self-answered slots are those whose ``source`` is ``"assumption"`` or\n    starts with ``"confirmed:"`` (a confirmed former assumption). With no\n    self-answered slots there is nothing to confirm — the rate is 1.0.\n    """\n    confirmed = 0\n    self_answered = 0\n    if not isinstance(slot_values, dict):\n        return 1.0\n    for entry in slot_values.values():\n        if not isinstance(entry, dict):\n            # A hand-corrupted state.json can carry a non-dict slot value; skip\n            # it rather than raising (the kit\'s read-side fail-open contract —\n            # a KPI read must never brick session-close / maintain). Matches the\n            # non-dict guards in reflections / episodes / maintenance.\n            continue\n        source = str(entry.get("source", ""))\n        if source.startswith("confirmed:"):\n            confirmed += 1\n            self_answered += 1\n        elif source == "assumption":\n            self_answered += 1\n    if self_answered == 0:\n        return 1.0\n    return confirmed / self_answered\n\n\ndef router_metrics(state: dict[str, Any]) -> dict[str, Any]:\n    """Return the question-router health metrics for one state document.\n\n    ``completeness_pct`` counts ``filled`` slots only — ``provisional`` and\n    ``partial`` answers never inflate completeness (the anti-gaming floor\'s\n    KPI mirror). With no recorded slots completeness is 0.0.\n    """\n    slots = state.get("slots", {})\n    statuses = list(slots.values())\n    total = len(statuses)\n    filled = statuses.count("filled")\n    provisional = statuses.count("provisional")\n    completeness = round(100.0 * filled / total, 1) if total else 0.0\n    return {\n        "slots_total": total,\n        "slots_filled": filled,\n        "slots_provisional": provisional,\n        "completeness_pct": completeness,\n        "open_questions": len(state.get("open_questions", [])),\n        "assumption_confirmation_rate": _kpi_confirmation_rate(\n            state.get("slot_values", {}),\n        ),\n        "quiet_sessions": int(state.get("quiet_sessions", 0)),\n        "session_count": int(state.get("session_count", 0)),\n    }\n\n\ndef workflow_kpis(state: dict[str, Any], sessions_dir: Path) -> dict[str, Any]:\n    """Return the full workflow KPI record: router metrics + session counters.\n\n    ``sessions_logged`` counts ``*.md`` logs under ``sessions_dir`` (README\n    excluded, 0 when the directory is absent); ``reflections_active`` reads\n    the state\'s reflection-buffer counter.\n    """\n    kpis = router_metrics(state)\n    logged = 0\n    if sessions_dir.is_dir():\n        logged = sum(1 for p in sessions_dir.glob("*.md") if p.name != "README.md")\n    buffer = state.get("reflection_buffer", {})\n    kpis["sessions_logged"] = logged\n    kpis["reflections_active"] = int(buffer.get("active_count", 0))\n    kpis["stage"] = state.get("stage")\n    kpis["mode"] = state.get("mode")\n    return kpis\n\n\ndef kpi_footer(kpis: dict[str, Any]) -> str:\n    """Render the one-line 📊 KPI summary for orientation blocks and reports.\n\n    Router metrics always appear; the workflow extras (logged sessions,\n    active lessons, mode, stage) appear when present in ``kpis``.\n    """\n    completeness = float(kpis.get("completeness_pct", 0.0))\n    parts = [\n        f"completeness {completeness:.0f}%",\n        f"open-Q {kpis.get(\'open_questions\', 0)}",\n        f"sessions {kpis.get(\'session_count\', 0)}",\n        f"quiet {kpis.get(\'quiet_sessions\', 0)}",\n    ]\n    if "sessions_logged" in kpis:\n        parts.append(f"logged {kpis[\'sessions_logged\']}")\n    if "reflections_active" in kpis:\n        parts.append(f"lessons {kpis[\'reflections_active\']}")\n    if kpis.get("mode") is not None:\n        parts.append(f"mode {kpis[\'mode\']}")\n    if kpis.get("stage") is not None:\n        parts.append(f"stage {kpis[\'stage\']}")\n    return "📊 substrate: " + " · ".join(parts)\n',
    'engine/loop/reflections.py': '"""Reflection buffer — the loop\'s compact learned-lesson memory (plan lane B2).\n\nReflections are small ``{"lesson", "evidence", "tags"}`` records mined from\nsession logs or added deliberately, stored in one atomically-written JSON file\n(``<state_dir>/reflections.json``). The buffer is deliberately tiny — a hard\n``buffer_size`` cap keeps the orientation injection cheap — and fail-open: a\nmissing or corrupt file reads as an empty list, never a crash. The miner is\ndeterministic and read-only; the caller decides what (if anything) becomes a\nstored reflection.\n"""\n\nfrom __future__ import annotations\n\nimport json\nimport re\nfrom datetime import date\nfrom pathlib import Path\n\nfrom engine.lib.atomicio import atomic_write_text\n\nREFLECTIONS_FILENAME = "reflections.json"\n\n_REF_ID_RE = re.compile(r"^R-(\\d+)$")\n_REF_IDEA_MARK = "\\N{ELECTRIC LIGHT BULB}"  # 💡 — session-idea lines\n_REF_FLAG_MARK = "\\N{BLACK FLAG}"  # ⚑ — self-initiated / friction flags\n_REF_PATH_SUFFIXES = (".py", ".md", ".js", ".ts", ".yml", ".json")\n_REF_STRIP_CHARS = "`\'\\"()[]<>,;:!?."\n\n\ndef load_reflections(path: Path) -> list[dict]:\n    """Return the reflection entries at ``path`` — ``[]`` on absent/corrupt."""\n    try:\n        raw = json.loads(path.read_text(encoding="utf-8"))\n    except (OSError, ValueError):\n        return []\n    if not isinstance(raw, list):\n        return []\n    return [entry for entry in raw if isinstance(entry, dict)]\n\n\ndef _ref_save(path: Path, entries: list[dict]) -> None:\n    """Write ``entries`` to ``path`` atomically as pretty-printed JSON."""\n    atomic_write_text(path, json.dumps(entries, indent=2) + "\\n")\n\n\ndef _ref_next_id(entries: list[dict]) -> str:\n    """Return the next ``R-NNNN`` id, monotonic over the ids already present."""\n    highest = 0\n    for entry in entries:\n        match = _REF_ID_RE.match(str(entry.get("id", "")))\n        if match:\n            highest = max(highest, int(match.group(1)))\n    return f"R-{highest + 1:04d}"\n\n\ndef _ref_is_inactive(entry: dict) -> bool:\n    """True when an entry is deprecated or superseded (prune/skip candidate)."""\n    return entry.get("status") == "deprecated" or bool(entry.get("superseded_by"))\n\n\ndef _ref_prune(entries: list[dict], buffer_size: int) -> list[dict]:\n    """Drop overflow beyond ``buffer_size``: oldest inactive first, then oldest.\n\n    ``buffer_size`` is clamped to at least 1 — a zero/negative host config must\n    never silently discard every lesson (or crash), and the entry just added is\n    never its own prune victim.\n    """\n    buffer_size = max(1, int(buffer_size))\n    pruned = list(entries)\n    while len(pruned) > buffer_size:\n        victim = next((e for e in pruned[:-1] if _ref_is_inactive(e)), pruned[0])\n        pruned.remove(victim)\n    return pruned\n\n\ndef add_reflection(\n    path: Path,\n    *,\n    lesson: str,\n    evidence: str,\n    tags: list[str],\n    status: str = "provisional",\n    buffer_size: int = 5,\n) -> dict:\n    """Append a reflection to the buffer at ``path`` and return the new entry.\n\n    Assigns the next monotonic ``R-NNNN`` id, stamps today\'s ISO date, and\n    prunes overflow beyond ``buffer_size`` (oldest superseded/deprecated\n    entries first, then oldest overall). ``status`` is ``provisional`` until a\n    later session confirms the lesson held up.\n    """\n    entries = load_reflections(path)\n    entry = {\n        "id": _ref_next_id(entries),\n        "lesson": lesson,\n        "evidence": evidence,\n        "tags": list(tags),\n        "status": status,\n        "date": date.today().isoformat(),\n    }\n    entries.append(entry)\n    _ref_save(path, _ref_prune(entries, buffer_size))\n    return entry\n\n\ndef active_lessons(entries: list[dict], buffer_size: int) -> list[dict]:\n    """Return live lessons newest-first, capped at ``buffer_size``.\n\n    Skips entries whose status is ``deprecated`` and entries carrying a\n    ``superseded_by`` stamp.\n    """\n    live = [entry for entry in entries if not _ref_is_inactive(entry)]\n    live.reverse()\n    return live[:buffer_size]\n\n\ndef supersede_reflection(path: Path, old_id: str, new_id: str) -> bool:\n    """Stamp ``superseded_by`` on ``old_id``\'s entry; False when it is absent."""\n    entries = load_reflections(path)\n    for entry in entries:\n        if entry.get("id") == old_id:\n            entry["superseded_by"] = new_id\n            _ref_save(path, entries)\n            return True\n    return False\n\n\ndef lessons_block(entries: list[dict]) -> str:\n    """Render the "Learned lessons" orientation block ("" when nothing active).\n\n    Provisional entries are flagged ``(provisional)`` so the reading agent\n    weighs them as candidates, not settled rules.\n    """\n    live = active_lessons(entries, len(entries))\n    if not live:\n        return ""\n    lines = ["## Learned lessons", ""]\n    for entry in live:\n        flag = " (provisional)" if entry.get("status") == "provisional" else ""\n        lines.append(f"- [{entry.get(\'id\', \'?\')}] {entry.get(\'lesson\', \'\')}{flag}")\n    return "\\n".join(lines) + "\\n"\n\n\ndef _ref_newest_logs(sessions_dir: Path, last_n: int) -> list[Path]:\n    """Return the newest ``last_n`` logs by mtime (name-tiebroken), oldest first."""\n    if not sessions_dir.is_dir() or last_n < 1:\n        return []\n    logs = [p for p in sessions_dir.glob("*.md") if p.name != "README.md"]\n    logs.sort(key=lambda p: (p.stat().st_mtime, p.name))\n    return logs[-last_n:]\n\n\ndef _ref_clean_line(line: str) -> str:\n    """Strip bullets, blockquote marks, and the emoji markers from a mined line."""\n    text = line.strip().lstrip("-*> ").strip()\n    for mark in (_REF_IDEA_MARK, _REF_FLAG_MARK):\n        text = text.replace(mark, "")\n    return text.strip().lstrip(":").strip()\n\n\ndef _ref_marker_tags(line: str) -> list[str]:\n    """Return the candidate tags for a line\'s emoji markers (may be empty)."""\n    tags: list[str] = []\n    if _REF_IDEA_MARK in line:\n        tags.append("idea")\n    if _REF_FLAG_MARK in line:\n        tags.append("flag")\n    return tags\n\n\ndef _ref_path_tokens(line: str) -> list[str]:\n    """Return file-path tokens: contain ``/`` and end in a known code/doc suffix."""\n    tokens: list[str] = []\n    for raw in line.split():\n        token = raw.strip(_REF_STRIP_CHARS)\n        if "/" in token and token.endswith(_REF_PATH_SUFFIXES):\n            tokens.append(token)\n    return tokens\n\n\ndef _ref_mine_log(log: Path) -> tuple[list[dict], dict[str, str]]:\n    """Mine one log: (marker-line candidates, first evidence per cited path)."""\n    candidates: list[dict] = []\n    paths_seen: dict[str, str] = {}\n    try:\n        lines = log.read_text(encoding="utf-8").splitlines()\n    except (OSError, UnicodeDecodeError):\n        return candidates, paths_seen\n    for lineno, line in enumerate(lines, 1):\n        if "[DEPRECATED]" in line:\n            continue\n        evidence = f"{log.name}:L{lineno}"\n        tags = _ref_marker_tags(line)\n        if tags:\n            candidates.append(\n                {"lesson": _ref_clean_line(line), "evidence": evidence, "tags": tags},\n            )\n        for token in _ref_path_tokens(line):\n            paths_seen.setdefault(token, evidence)\n    return candidates, paths_seen\n\n\ndef mine_reflections(sessions_dir: Path, *, last_n: int = 5) -> list[dict]:\n    """Mine candidate lessons from the newest ``last_n`` session logs.\n\n    Deterministic and read-only — never writes state; the caller decides what\n    to promote into the buffer. Three extraction passes:\n\n      1. 💡 idea lines → ``{"lesson", "evidence", "tags": ["idea"]}``.\n      2. ⚑ flag lines → the same shape, tagged ``flag``.\n      3. Any file path cited in >= 2 different logs → one\n         ``Recurring attention on <path>`` candidate.\n\n    Lines containing ``[DEPRECATED]`` are skipped entirely.\n    """\n    candidates: list[dict] = []\n    sightings: dict[str, dict[str, str]] = {}\n    for log in _ref_newest_logs(sessions_dir, last_n):\n        mined, paths_seen = _ref_mine_log(log)\n        candidates.extend(mined)\n        for token, evidence in paths_seen.items():\n            sightings.setdefault(token, {})[log.name] = evidence\n    for token in sorted(sightings):\n        seen = sightings[token]\n        if len(seen) < 2:\n            continue\n        evidence = ", ".join(seen[name] for name in sorted(seen))\n        candidates.append(\n            {\n                "lesson": f"Recurring attention on {token}",\n                "evidence": evidence,\n                "tags": ["recurring-path"],\n            },\n        )\n    return candidates\n',
    'engine/loop/episodes.py': '"""Episodic index — a tiny searchable memory over session logs (plan lane B2).\n\nEach session log becomes one compact ``{"slug", "date", "tags", "summary"}``\nrecord in ``<state_dir>/episodic_index.json``, so an agent can grep *which*\npast session touched a topic without reading every log top-to-bottom. Tags\ncome from the log\'s first heading (minus stopwords) plus the workflow\'s marker\nemojis (💡 idea, ⚑ flag, ⟲ review, 📊 telemetry). The index is a derived\nartifact: rebuildable from the logs at any time, written atomically, and\nfail-open on absence/corruption.\n"""\n\nfrom __future__ import annotations\n\nimport json\nimport re\nfrom pathlib import Path\n\nfrom engine.lib.atomicio import atomic_write_text\n\nEPISODIC_INDEX_FILENAME = "episodic_index.json"\n\n_EPI_NAME_RE = re.compile(r"^(\\d{4}-\\d{2}-\\d{2})-(.+)$")\n_EPI_WORD_RE = re.compile(r"[a-z0-9][\\w-]*")\n_EPI_STOPWORDS = frozenset(\n    {\n        "a",\n        "an",\n        "and",\n        "at",\n        "by",\n        "for",\n        "from",\n        "in",\n        "of",\n        "on",\n        "or",\n        "the",\n        "to",\n        "with",\n    },\n)\n_EPI_MARKERS = (\n    "\\N{ELECTRIC LIGHT BULB}",  # 💡 session idea\n    "\\N{BLACK FLAG}",  # ⚑ self-initiated / friction flag\n    "\\N{ANTICLOCKWISE GAPPED CIRCLE ARROW}",  # ⟲ previous-session review\n    "\\N{BAR CHART}",  # 📊 telemetry / KPI footer\n)\n_EPI_SUMMARY_LIMIT = 140\n\n\ndef _epi_load(index_path: Path) -> list[dict]:\n    """Return the index entries at ``index_path`` — ``[]`` on absent/corrupt."""\n    try:\n        raw = json.loads(index_path.read_text(encoding="utf-8"))\n    except (OSError, ValueError):\n        return []\n    if not isinstance(raw, list):\n        return []\n    return [entry for entry in raw if isinstance(entry, dict)]\n\n\ndef _epi_save(index_path: Path, entries: list[dict]) -> None:\n    """Write ``entries`` to ``index_path`` atomically as pretty-printed JSON."""\n    atomic_write_text(index_path, json.dumps(entries, indent=2) + "\\n")\n\n\ndef _epi_tags(text: str) -> list[str]:\n    """Tags: first ``# `` heading words minus stopwords, plus marker emojis."""\n    tags: list[str] = []\n    for line in text.splitlines():\n        if line.startswith("# "):\n            words = _EPI_WORD_RE.findall(line[2:].lower())\n            tags.extend(word for word in words if word not in _EPI_STOPWORDS)\n            break\n    tags.extend(mark for mark in _EPI_MARKERS if mark in text)\n    return list(dict.fromkeys(tags))\n\n\ndef _epi_summary(text: str) -> str:\n    """Return the first non-blank non-heading line, truncated to 140 chars."""\n    for line in text.splitlines():\n        stripped = line.strip()\n        if stripped and not stripped.startswith("#"):\n            return stripped[:_EPI_SUMMARY_LIMIT]\n    return ""\n\n\ndef index_session(log_path: Path) -> dict:\n    """Summarise one session log into ``{"slug", "date", "tags", "summary"}``.\n\n    ``slug`` and ``date`` parse from the ``YYYY-MM-DD-<slug>.md`` filename\n    convention; a non-conforming name degrades gracefully to the whole stem as\n    the slug with an empty date. An unreadable file yields empty tags/summary.\n    """\n    match = _EPI_NAME_RE.match(log_path.stem)\n    if match:\n        session_date, slug = match.group(1), match.group(2)\n    else:\n        session_date, slug = "", log_path.stem\n    try:\n        text = log_path.read_text(encoding="utf-8")\n    except (OSError, UnicodeDecodeError):\n        text = ""\n    return {\n        "slug": slug,\n        "date": session_date,\n        "tags": _epi_tags(text),\n        "summary": _epi_summary(text),\n    }\n\n\ndef rebuild_episodic_index(sessions_dir: Path, index_path: Path) -> list[dict]:\n    """Rebuild the whole index from ``sessions_dir`` and write it atomically.\n\n    Scans ``*.md`` excluding ``README.md``, sorted by filename (the date-first\n    naming convention makes that chronological). Returns the entries written;\n    an absent sessions dir yields an empty index.\n    """\n    logs: list[Path] = []\n    if sessions_dir.is_dir():\n        logs = sorted(p for p in sessions_dir.glob("*.md") if p.name != "README.md")\n    entries = [index_session(p) for p in logs]\n    _epi_save(index_path, entries)\n    return entries\n\n\ndef append_episode(index_path: Path, entry: dict) -> None:\n    """Add ``entry`` to the index, replacing an existing (slug, date) match.\n\n    Keyed on slug *and* date: re-indexing the same log updates in place, while\n    a same-slug session from a different day appends instead of silently\n    deleting the earlier episode.\n    """\n    entries = _epi_load(index_path)\n    key = (entry.get("slug"), entry.get("date"))\n    for i, existing in enumerate(entries):\n        if (existing.get("slug"), existing.get("date")) == key:\n            entries[i] = entry\n            break\n    else:\n        entries.append(entry)\n    _epi_save(index_path, entries)\n\n\ndef search_episodes(index_path: Path, tag: str) -> list[dict]:\n    """Return every indexed episode carrying ``tag`` in its tag list."""\n    return [entry for entry in _epi_load(index_path) if tag in entry.get("tags", [])]\n',
    'engine/loop/triggers.py': '"""Trigger scan for the self-improving loop (plan section 5, Lane B1).\n\nThe loop\'s sensory layer: ``check_triggers`` inspects the project tree plus the\nstate document and reports which of the five trigger kinds fired —\n\n- ``critical_unfilled`` — a graduation-critical slot is still not ``filled``\n  after the cadence\'s grace window (one trigger per slot).\n- ``blocking_open``     — escalated blocking questions sit on\n  ``state["open_questions"]``.\n- ``drift``             — the doc-hygiene checks (badge / link / reachable)\n  report findings.\n- ``staleness``         — the newest session log is older than\n  ``cadence["staleness_days"]`` days, or reconciliation is overdue by session\n  count.\n- ``new_area``          — a direct subdirectory of the docs root holds only\n  unreachable *and* unbadged markdown (nobody owns it yet).\n\n``mandatory_questions`` then maps fired triggers back onto question-bank\nentries, and ``trigger_block`` renders the orientation text block. The mode\npolicy (``engine.lib.modes.triggers_mandate``) decides whether the block is a\nmandate or an advisory — this module only renders whichever the caller picked.\nPure stdlib; returns data / text, never prints.\n"""\n\nfrom __future__ import annotations\n\nimport time\nfrom pathlib import Path\nfrom typing import Any, NamedTuple\n\nfrom engine.checks.check_docs import badge_token, check_reachable, run_doc_checks\nfrom engine.checks.check_session_log import latest_session_log\nfrom engine.interview.question_bank import QUESTIONS\nfrom engine.lib.config import Config\n\n_TRG_PRIORITY_ORDER = {"blocking": 0, "high": 1, "normal": 2}\n_TRG_SECONDS_PER_DAY = 86_400.0\n\n\nclass Trigger(NamedTuple):\n    """One fired trigger: kind, severity, human message, related question ids."""\n\n    kind: str\n    severity: str\n    message: str\n    question_ids: tuple[str, ...]\n\n\ndef _trg_critical_unfilled(\n    state: dict[str, Any],\n    cadence: dict[str, int],\n    bank: list[dict],\n) -> list[Trigger]:\n    """One trigger per critical slot still unfilled past the grace window."""\n    grace = int(cadence.get("critical_slot_grace_sessions", 3))\n    if int(state.get("session_count", 0)) <= grace:\n        return []\n    slots = state.get("slots", {})\n    critical = dict.fromkeys(q["slot"] for q in bank if q.get("critical"))\n    triggers: list[Trigger] = []\n    for slot in critical:\n        if slots.get(slot) == "filled":\n            continue\n        ids = tuple(q["id"] for q in bank if q["slot"] == slot)\n        message = (\n            f"critical slot \'{slot}\' is not filled after the "\n            f"{grace}-session grace window"\n        )\n        triggers.append(Trigger("critical_unfilled", "blocking", message, ids))\n    return triggers\n\n\ndef _trg_blocking_open(state: dict[str, Any]) -> list[Trigger]:\n    """One trigger when escalated blocking questions are open."""\n    open_questions = [str(q) for q in state.get("open_questions", [])]\n    if not open_questions:\n        return []\n    listed = ", ".join(open_questions)\n    message = f"{len(open_questions)} blocking question(s) open: {listed}"\n    return [Trigger("blocking_open", "blocking", message, tuple(open_questions))]\n\n\ndef _trg_drift(docs_root: Path, config: Config) -> list[Trigger]:\n    """One trigger when the doc-hygiene checks report any finding."""\n    findings = run_doc_checks(docs_root, config.badge_tokens, config.readpath_docs)\n    if not findings:\n        return []\n    kinds = ", ".join(sorted({f.kind for f in findings}))\n    message = f"doc hygiene reports {len(findings)} finding(s) ({kinds})"\n    return [Trigger("drift", "high", message, ())]\n\n\ndef _trg_staleness(\n    state: dict[str, Any],\n    cadence: dict[str, int],\n    sessions_dir: Path,\n) -> list[Trigger]:\n    """One trigger when memory looks stale (old log or overdue reconciliation)."""\n    reasons: list[str] = []\n    stale_days = int(cadence.get("staleness_days", 14))\n    newest = latest_session_log(sessions_dir)\n    if newest is not None:\n        age_days = (time.time() - newest.stat().st_mtime) / _TRG_SECONDS_PER_DAY\n        if age_days > stale_days:\n            reasons.append(\n                f"newest session log is {int(age_days)} days old "\n                f"(threshold {stale_days})",\n            )\n    overdue = int(cadence.get("reconciliation_sessions", 20))\n    since = int(state.get("session_count", 0)) - int(\n        state.get("last_compaction_session", 0),\n    )\n    if since >= overdue:\n        reasons.append(\n            f"{since} sessions since the last compaction (cadence {overdue})",\n        )\n    if not reasons:\n        return []\n    return [Trigger("staleness", "normal", "; ".join(reasons), ())]\n\n\ndef _trg_new_area(docs_root: Path, config: Config) -> list[Trigger]:\n    """One trigger per docs subdirectory whose docs are all orphaned + unbadged."""\n    if not docs_root.is_dir():\n        return []\n    orphans = {f.path for f in check_reachable(docs_root, config.readpath_docs)}\n    triggers: list[Trigger] = []\n    for sub in sorted(p for p in docs_root.iterdir() if p.is_dir()):\n        files = sorted(sub.rglob("*.md"))\n        if not files:\n            continue\n        all_unowned = all(\n            f.relative_to(docs_root).as_posix() in orphans and badge_token(f) is None\n            for f in files\n        )\n        if all_unowned:\n            message = (\n                f"new docs area \'{sub.name}/\' ({len(files)} file(s)) is "\n                "entirely unreachable and unbadged — no ownership entry yet"\n            )\n            triggers.append(Trigger("new_area", "high", message, ()))\n    return triggers\n\n\ndef check_triggers(\n    root: Path,\n    config: Config,\n    state: dict[str, Any],\n    bank: list[dict] | None = None,\n) -> list[Trigger]:\n    """Scan the project tree + state and return every fired trigger.\n\n    ``root`` is the project root; the docs root and sessions dir are resolved\n    from ``config``. Returns triggers grouped by kind in the fixed order\n    critical_unfilled, blocking_open, drift, staleness, new_area.\n    """\n    bank = QUESTIONS if bank is None else bank\n    cadence = dict(config.cadence or {})\n    docs_root = root / config.docs_root\n    sessions_dir = root / config.sessions_dir\n    return (\n        _trg_critical_unfilled(state, cadence, bank)\n        + _trg_blocking_open(state)\n        + _trg_drift(docs_root, config)\n        + _trg_staleness(state, cadence, sessions_dir)\n        + _trg_new_area(docs_root, config)\n    )\n\n\ndef mandatory_questions(\n    triggers: list[Trigger],\n    bank: list[dict] | None = None,\n) -> list[dict]:\n    """Return the bank questions the fired triggers pull into this session.\n\n    Selects entries whose ``trigger`` field matches a fired kind, plus the\n    entries a ``critical_unfilled`` trigger names via ``question_ids``.\n    De-duplicated by id; priority-ordered (blocking, high, normal — stable).\n    """\n    bank = QUESTIONS if bank is None else bank\n    fired_kinds = {t.kind for t in triggers}\n    named_ids = {\n        qid for t in triggers if t.kind == "critical_unfilled" for qid in t.question_ids\n    }\n    selected: list[dict] = []\n    seen: set[str] = set()\n    for question in bank:\n        wanted = question.get("trigger") in fired_kinds or question["id"] in named_ids\n        if wanted and question["id"] not in seen:\n            seen.add(question["id"])\n            selected.append(question)\n    return sorted(\n        selected,\n        key=lambda q: _TRG_PRIORITY_ORDER.get(q.get("priority", "normal"), 2),\n    )\n\n\ndef trigger_block(\n    triggers: list[Trigger],\n    questions: list[dict],\n    *,\n    mandate: bool,\n) -> str:\n    """Render the orientation trigger block (\'\' when nothing fired).\n\n    ``mandate=True`` (guided/active modes) opens with a MANDATORY\n    question-session header; otherwise the block is an advisory.\n    """\n    if not triggers:\n        return ""\n    if mandate:\n        header = "## ⚠️ MANDATORY question session — triggers fired"\n    else:\n        header = "## Trigger advisory (non-mandatory)"\n    lines = [header, ""]\n    lines += [f"- [{t.severity}] {t.kind}: {t.message}" for t in triggers]\n    if questions:\n        lines += ["", "Questions to ask this session:"]\n        lines += [\n            f"- {q[\'id\']} ({q.get(\'priority\', \'normal\')}): {q[\'prompt\']}"\n            for q in questions\n        ]\n    return "\\n".join(lines) + "\\n"\n',
    'engine/loop/maintenance.py': '"""Maintenance actuators for the self-improving loop (plan section 5, Lane B3).\n\nThe loop\'s housekeeping arm: the compaction cadence and its pre-compaction\n"State Delta" snapshot, the escalated open-question list (the blocking-question\nbrake graduation waits on), the promotion-rights downgrade, and the composed\n``maintain`` human report. Pure stdlib; every file write goes through\n``atomic_write_text``; functions return data / text, never print — the CLI\nowns all output.\n\nThe sibling loop modules (``reflections``, ``kpis``, ``review_seam``) are\nimported lazily with fail-open fallbacks, so this module keeps working when a\nbuild ships without them (the single-file bootstrap concatenation case).\n"""\n\nfrom __future__ import annotations\n\nfrom datetime import date\nfrom pathlib import Path\nfrom typing import Any\n\nfrom engine.lib.atomicio import atomic_write_text\nfrom engine.lib.config import Config\nfrom engine.loop.kpis import kpi_footer\nfrom engine.loop.reflections import (\n    REFLECTIONS_FILENAME,\n    active_lessons,\n    load_reflections,\n)\n\n_MNT_VALUE_WIDTH = 80\n\n\ndef compaction_due(state: dict[str, Any], cadence: dict[str, int]) -> bool:\n    """True when the compaction cadence window has elapsed.\n\n    Fires when ``session_count - last_compaction_session`` reaches\n    ``cadence["compaction_sessions"]`` (default 20).\n\n    Deliberate reduction of the plan\'s "~700K tokens OR 20 sessions": the kit\n    has no token telemetry (stdlib-only, no provider hooks), so only the\n    session-count half ships; hosts with token accounting can trigger\n    ``run_compaction`` directly when their own meter trips.\n    """\n    every = int(cadence.get("compaction_sessions", 20))\n    since = int(state.get("session_count", 0)) - int(\n        state.get("last_compaction_session", 0),\n    )\n    return since >= every\n\n\ndef _mnt_cell(value: Any) -> str:\n    """Collapse ``value`` to one table-safe line truncated to 80 chars."""\n    text = " ".join(str(value).split()).replace("|", "/")\n    return text[:_MNT_VALUE_WIDTH]\n\n\ndef _mnt_lesson_lines(reflections: list[dict]) -> list[str]:\n    """Render the active-lesson lines from the reflection entries."""\n    live = active_lessons(reflections, len(reflections))\n    return [f"- [{e.get(\'id\', \'?\')}] {e.get(\'lesson\', \'\')}" for e in live]\n\n\ndef _mnt_slot_lines(state: dict[str, Any]) -> list[str]:\n    """Render the slot table (name-sorted; values truncated to 80 chars)."""\n    slots = state.get("slots", {})\n    if not slots:\n        return []\n    values = state.get("slot_values", {})\n    lines = ["| slot | status | value |", "| --- | --- | --- |"]\n    for slot in sorted(slots):\n        entry = values.get(slot, {})\n        value = entry.get("value", "") if isinstance(entry, dict) else entry\n        lines.append(f"| {slot} | {slots[slot]} | {_mnt_cell(value)} |")\n    return lines\n\n\ndef state_delta(state: dict[str, Any], reflections: list[dict]) -> str:\n    """Render the pre-compaction State Delta markdown — dense, deterministic.\n\n    The counters line always appears; the slot table, open-questions list, and\n    active-lessons list appear only when non-empty. No timestamps: two calls\n    over the same inputs return identical text.\n    """\n    lines = [\n        f"# State Delta — session {int(state.get(\'session_count\', 0))}",\n        "",\n        f"- mode: {state.get(\'mode\', \'?\')} · stage: {state.get(\'stage\', \'?\')} · "\n        f"sessions: {int(state.get(\'session_count\', 0))} · "\n        f"quiet: {int(state.get(\'quiet_sessions\', 0))}",\n    ]\n    slot_lines = _mnt_slot_lines(state)\n    if slot_lines:\n        lines += ["", "## Slots", "", *slot_lines]\n    open_questions = [str(q) for q in state.get("open_questions", [])]\n    if open_questions:\n        lines += ["", "## Open questions", ""]\n        lines += [f"- {qid}" for qid in open_questions]\n    lesson_lines = _mnt_lesson_lines(reflections)\n    if lesson_lines:\n        lines += ["", "## Active lessons", "", *lesson_lines]\n    return "\\n".join(lines) + "\\n"\n\n\ndef _mnt_load_reflections(state_dir: Path) -> list[dict]:\n    """Load the reflection buffer for the delta (``[]`` when unavailable)."""\n    return load_reflections(state_dir / REFLECTIONS_FILENAME)\n\n\ndef run_compaction(root: Path, config: Config, backend: Any) -> Path:\n    """Write the State Delta snapshot and reset the compaction counter.\n\n    Writes ``<state_dir>/state-delta-<session_count>.md`` atomically, then\n    stamps ``last_compaction_session`` so ``compaction_due`` stays quiet until\n    the next cadence window. Returns the written path.\n    """\n    state_dir = root / config.state_dir\n    session = int(backend.get("session_count", 0))\n    delta = state_delta(backend.data, _mnt_load_reflections(state_dir))\n    path = state_dir / f"state-delta-{session}.md"\n    atomic_write_text(path, delta)\n    backend.set("last_compaction_session", session)\n    return path\n\n\ndef escalate_blocking(backend: Any, question_id: str) -> bool:\n    """Append ``question_id`` to the escalated open-questions list once.\n\n    Idempotent: True when it appended, False when the id was already open.\n    Open questions hold graduation until answered (the blocking brake).\n    """\n    open_questions = list(backend.get("open_questions", []))\n    if question_id in open_questions:\n        return False\n    open_questions.append(question_id)\n    backend.set("open_questions", open_questions)\n    return True\n\n\ndef resolve_open_question(backend: Any, question_id: str) -> bool:\n    """Drop ``question_id`` from the open-questions list; False when absent."""\n    open_questions = list(backend.get("open_questions", []))\n    if question_id not in open_questions:\n        return False\n    open_questions.remove(question_id)\n    backend.set("open_questions", open_questions)\n    return True\n\n\ndef downgrade_promotion(backend: Any, *, reason: str) -> None:\n    """Cap autonomy: ``promotion_rights`` → ``"propose"``, logged with why.\n\n    Appends a ``promotion_downgrade`` event to ``review_log`` so the loss of\n    apply-rights always carries its provenance.\n    """\n    log = list(backend.get("review_log", []))\n    log.append(\n        {\n            "event": "promotion_downgrade",\n            "reason": reason,\n            "date": date.today().isoformat(),\n        },\n    )\n    with backend.transaction():\n        backend.set("promotion_rights", "propose")\n        backend.set("review_log", log)\n\n\ndef _mnt_item_line(item: Any) -> str:\n    """Render one report line for a trigger or a checker finding.\n\n    Triggers (kind/severity/message) render like the orientation block;\n    findings (path/kind/message) render path-first; anything else renders as\n    its ``str``.\n    """\n    kind = getattr(item, "kind", None)\n    message = getattr(item, "message", None)\n    if kind is None or message is None:\n        return f"- {item}"\n    severity = getattr(item, "severity", None)\n    if severity is not None:\n        return f"- [{severity}] {kind}: {message}"\n    path = getattr(item, "path", None)\n    prefix = f"{path}: " if path else ""\n    return f"- {prefix}[{kind}] {message}"\n\n\ndef _mnt_review_dir() -> str:\n    """Return the review-payload directory name.\n\n    Mirrors ``review_seam.REVIEW_DIR`` as a literal: ``review_seam`` imports\n    this module at top level, so importing it back would be circular — the\n    seam\'s own test pins the two values equal.\n    """\n    return "review"\n\n\ndef _mnt_advisories(root: Path, config: Config, backend: Any) -> list[str]:\n    """Return the maintenance advisories: compaction due, payloads waiting."""\n    advisories: list[str] = []\n    if compaction_due(backend.data, dict(config.cadence or {})):\n        advisories.append("compaction due — write the State Delta snapshot")\n    review_dir = root / config.state_dir / _mnt_review_dir()\n    if review_dir.is_dir():\n        pending = sorted(review_dir.glob("payload-*.json"))\n        if pending:\n            advisories.append(\n                f"{len(pending)} review payload(s) awaiting a reviewer",\n            )\n    return advisories\n\n\ndef _mnt_footer(kpis: dict[str, Any]) -> str:\n    """Render the KPI footer line for the report."""\n    return kpi_footer(kpis)\n\n\ndef maintenance_report(\n    root: Path,\n    config: Config,\n    backend: Any,\n    *,\n    triggers: list[Any],\n    economy_findings: list[Any],\n    ledger_findings: list[Any],\n    kpis: dict[str, Any],\n) -> str:\n    """Compose the ``maintain`` human report from the loop\'s sensor outputs.\n\n    Every section is skipped when its input is empty; a maintenance-advisories\n    section surfaces compaction cadence and accumulated review payloads (the\n    no-reviewer graceful fallback); the report ends with the KPI footer when\n    ``kpis`` is non-empty.\n    """\n    lines = [\n        f"# Maintenance report — session {int(backend.get(\'session_count\', 0))}",\n    ]\n    sections: tuple[tuple[str, list[Any]], ...] = (\n        ("Triggers", triggers),\n        ("Economy findings", economy_findings),\n        ("Ledger findings", ledger_findings),\n    )\n    for title, items in sections:\n        if not items:\n            continue\n        lines += ["", f"## {title}", ""]\n        lines += [_mnt_item_line(item) for item in items]\n    advisories = _mnt_advisories(root, config, backend)\n    if advisories:\n        lines += ["", "## Maintenance", ""]\n        lines += [f"- {advisory}" for advisory in advisories]\n    if kpis:\n        lines += ["", _mnt_footer(kpis)]\n    return "\\n".join(lines) + "\\n"\n',
    'engine/loop/review_seam.py': '"""The external-review seam — provisioned, not wired (plan section 6, Lane B3).\n\nA second model can audit the interview\'s provisional self-answers, but the kit\nnever talks to one (no subprocess, no network): it emits an **anti-anchor**\npayload — the proposition and its evidence, NO confidence score, NO author\ncommentary — and the host records the verdict through one entry point. With no\nreviewer configured, payloads simply accumulate for the owner; nothing blocks.\nPure stdlib; writes via ``atomic_write_text``.\n"""\n\nfrom __future__ import annotations\n\nimport json\nfrom datetime import date\nfrom pathlib import Path\nfrom typing import Any\n\nfrom engine.interview.interview import confirm_slot\nfrom engine.interview.question_bank import QUESTIONS\nfrom engine.lib.atomicio import atomic_write_text\nfrom engine.lib.config import Config\nfrom engine.loop.maintenance import downgrade_promotion, escalate_blocking\n\nREVIEW_DIR = "review"\n\n# Deterministic checks first — the reviewer runs mechanical verification\n# before exercising judgment; subjective slots route straight to the owner.\n_REV_OBJECTIVE_STOPS = (\n    "verify against repository source",\n    "run the project verify command",\n)\n_REV_SUBJECTIVE_STOPS = ("route to the owner - subjective slot",)\n\n_REV_WIRING_DOC = """\\\n# Review seam — provisioned, not wired\n\nThe kit never calls an external model. It defines a payload format and two\nentry points; the host wires ANY reviewer (a second model, a CLI, a human)\naround them:\n\n1. `bootstrap review build <slot>` emits the payload JSON to\n   `<state_dir>/review/payload-<slot>.json`.\n2. The external reviewer reads ONLY that payload — never the chat context,\n   never the author\'s notes or working files.\n3. The host records the verdict:\n   `bootstrap review confirm <slot> --verdict pass|fail --reviewer <name>`.\n   A `pass` on an objective slot confirms it; a `pass` on a subjective slot is\n   recorded but the slot stays provisional (only the owner confirms taste);\n   a `fail` escalates the question as blocking and downgrades promotion\n   rights to propose-only.\n\nGraceful no-reviewer fallback: with no reviewer configured, payloads simply\naccumulate in the review directory for the owner to work through — nothing\nblocks, and the maintenance report counts them.\n\nAnti-anchor rule: the payload carries the proposition, its evidence, and\ndeterministic stop conditions — NO confidence score and NO author commentary,\nso the reviewer cannot anchor on the author\'s own belief.\n\nUnverified reviewer: calibrate a new reviewer against known-answer issues\nbefore trusting its dissent — a verdict that fights the evidence is the\nreviewer\'s bug until proven otherwise.\n"""\n\n\ndef _rev_bank_entry(slot: str) -> dict:\n    """Return the question-bank entry for ``slot`` (``{}`` when unknown)."""\n    for question in QUESTIONS:\n        if question.get("slot") == slot:\n            return question\n    return {}\n\n\ndef _rev_slot_value(backend: Any, slot: str) -> dict:\n    """Return the recorded slot-value entry for ``slot`` (``{}`` when absent)."""\n    entry = dict(backend.get("slot_values", {})).get(slot, {})\n    return entry if isinstance(entry, dict) else {}\n\n\ndef build_review_payload(backend: Any, slot: str) -> dict:\n    """Build the anti-anchor review payload for a provisional ``slot``.\n\n    The payload carries the proposition and its evidence ONLY — no confidence\n    score, no author commentary — so the reviewing model cannot anchor on the\n    author\'s belief. Objective slots get deterministic stop conditions first;\n    subjective slots route to the owner. Returns ``{}`` when the slot is not\n    provisional (nothing to review). Never raises ``KeyError``.\n    """\n    if dict(backend.get("slots", {})).get(slot) != "provisional":\n        return {}\n    entry = _rev_slot_value(backend, slot)\n    question = _rev_bank_entry(slot)\n    objective = bool(question.get("objective", False))\n    stops = _REV_OBJECTIVE_STOPS if objective else _REV_SUBJECTIVE_STOPS\n    evidence = (\n        f"question: {question.get(\'prompt\', \'\')} | "\n        f"recorded source: {entry.get(\'source\', \'\')}"\n    )\n    return {\n        "format_version": 1,\n        "slot": slot,\n        "proposition": entry.get("value", ""),\n        "evidence": evidence,\n        "stop_conditions": list(stops),\n        "objective": objective,\n    }\n\n\ndef write_review_payload(root: Path, config: Config, payload: dict) -> Path:\n    """Write ``payload`` to ``<state_dir>/review/payload-<slot>.json``.\n\n    Atomic, indented, key-sorted JSON; returns the written path.\n    """\n    slot = str(payload.get("slot", "unknown"))\n    path = root / config.state_dir / REVIEW_DIR / f"payload-{slot}.json"\n    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\\n")\n    return path\n\n\ndef clear_review_payload(root: Path, config: Config, slot: str) -> bool:\n    """Remove the consumed payload for ``slot``; True when one was present.\n\n    A verdict recorded via ``apply_review_verdict`` consumes the payload, but the\n    payload FILE persists — and ``maintenance._mnt_advisories`` counts every\n    ``payload-*.json`` as "awaiting a reviewer", so without this the count never\n    decrements after a review (it grows without bound under a wired reviewer).\n    Idempotent: a missing payload is a no-op.\n    """\n    path = root / config.state_dir / REVIEW_DIR / f"payload-{slot}.json"\n    existed = path.exists()\n    path.unlink(missing_ok=True)\n    return existed\n\n\ndef _rev_log(backend: Any, slot: str, verdict: str, reviewer: str) -> None:\n    """Append one review-log entry (the state contract\'s four-field shape)."""\n    log = list(backend.get("review_log", []))\n    log.append(\n        {\n            "slot": slot,\n            "verdict": verdict,\n            "reviewer": reviewer,\n            "date": date.today().isoformat(),\n        },\n    )\n    backend.set("review_log", log)\n\n\ndef apply_review_verdict(\n    backend: Any,\n    slot: str,\n    *,\n    verdict: str,\n    reviewer: str,\n) -> str:\n    """Record an external reviewer\'s verdict on a provisional slot.\n\n    Three outcomes:\n\n    - ``pass`` on an *objective* slot confirms it (provisional → filled,\n      source ``reviewer:<name>``) → returns ``"confirmed"``.\n    - ``pass`` on a *subjective* slot is recorded only — the slot stays\n      provisional and promotion stays capped at propose → ``"recorded"``.\n    - ``fail`` escalates the slot\'s question as blocking AND downgrades\n      promotion rights to propose-only → ``"escalated"``.\n\n    Every outcome appends a review-log entry. Raises ``ValueError`` on any\n    verdict other than ``"pass"`` / ``"fail"``. A slot that is not currently\n    ``provisional`` (typo\'d, already confirmed, never answered) returns\n    ``"not-provisional"`` untouched — mirroring ``build_review_payload``\'s\n    guard, so a stray verdict can neither falsely confirm nor escalate.\n    """\n    if verdict not in ("pass", "fail"):\n        raise ValueError(f"unknown review verdict: {verdict!r}")\n    if backend.get("slots", {}).get(slot) != "provisional":\n        return "not-provisional"\n    question = _rev_bank_entry(slot)\n    # Each multi-write outcome is one transaction (Q-0223 tail ①): the escalate/\n    # downgrade/log (and confirm/log) legs land together or not at all. The\n    # helpers open their own transactions internally — safe, because the JSON\n    # backend\'s transaction is re-entrant and only the outermost exit flushes.\n    if verdict == "fail":\n        question_id = str(_rev_slot_value(backend, slot).get("question_id", ""))\n        question_id = question_id or str(question.get("id", slot))\n        with backend.transaction():\n            escalate_blocking(backend, question_id)\n            downgrade_promotion(\n                backend,\n                reason=f"review fail on slot \'{slot}\' by {reviewer}",\n            )\n            _rev_log(backend, slot, verdict, reviewer)\n        return "escalated"\n    if question.get("objective", False):\n        with backend.transaction():\n            confirm_slot(backend, slot, source=f"reviewer:{reviewer}")\n            _rev_log(backend, slot, verdict, reviewer)\n        return "confirmed"\n    _rev_log(backend, slot, verdict, reviewer)\n    return "recorded"\n\n\ndef seam_wiring_doc() -> str:\n    """Return the wiring instructions for hosting ANY external reviewer.\n\n    The seam ships provisioned, not wired: the kit defines the payload format\n    and the verdict entry points; the host decides which model (if any) reads\n    the payloads — and without one, they accumulate gracefully for the owner.\n    """\n    return _REV_WIRING_DOC\n',
    'engine/economy/engine.py': '"""The context-economy engine (plan §5.B, Lane B4).\n\nThe retention/taxonomy layer of the self-improving loop: docs are classified\ninto host-declared classes (badge- and/or glob-matched), gauges watch word and\ncount budgets, an inbound-reference scan protects cited files, and the actuator\napplies the TRIPLE FILTER (harvested AND past window AND zero inbound refs)\nbefore any deletion — writing one tombstone line per pruned file into a\nper-band shard. Retention windows are measured in **days** from file mtime:\nthe kit supports day windows only; "bands" are a host cadence unit layered on\ntop of it, never a kit unit. ``economy["maturity"]`` gates the actuator —\n``"shadow"`` never applies. Pure stdlib; returns data / text, never prints.\n"""\n\nfrom __future__ import annotations\n\nimport os\nimport re\nimport time\nfrom datetime import date\nfrom pathlib import Path\nfrom typing import Any, NamedTuple\n\nfrom engine.checks.check_orientation_budget import _ob_boot_paths\nfrom engine.lib.atomicio import atomic_write_text\nfrom engine.lib.config import Config\n\n# Minimal inline copy of check_docs._badge_token\'s regex (private there); drop\n# once the helper is promoted to a public name in engine/checks/check_docs.py.\n_ECO_BADGE_RE = re.compile(r"\\*\\*Status:\\*\\*\\s*`([a-z-]+)`")\n\n_ECO_SECONDS_PER_DAY = 86400.0\n\n\nclass EconomyFinding(NamedTuple):\n    """One economy finding: ``path`` is relative to the project root."""\n\n    path: str\n    kind: str\n    message: str\n\n\nDEFAULT_CLASSES: list[dict] = [\n    {\n        "name": "sessions",\n        "globs": ["<sessions_dir>/*.md"],\n        "mode": "delete_tomb",\n        "window_days": 14,\n        "tombstone_dir": "<sessions_dir>/pruned",\n    },\n    {\n        "name": "plans",\n        "badges": ["plan"],\n        "mode": "archive",\n        "window_days": 60,\n    },\n    {\n        "name": "living",\n        "badges": ["living-ledger", "reference", "binding"],\n        "mode": "keep",\n    },\n]\n"""Minimal generic class profile — a STARTING POINT, not shipped policy.\n\nUsed only when ``config.economy["classes"]`` is empty. Every adopting host is\nexpected to replace it with its own measured taxonomy (the kit ships the\nsearch, not our constants). Placeholder tokens (``<sessions_dir>`` etc.) are\nexpanded from the host config at evaluation time.\n"""\n\n\ndef _eco_expand(pattern: str, config: Config) -> str:\n    """Expand ``<sessions_dir>`` / ``<docs_root>`` / ``<state_dir>`` tokens."""\n    return (\n        pattern.replace("<sessions_dir>", config.sessions_dir)\n        .replace("<docs_root>", config.docs_root)\n        .replace("<state_dir>", config.state_dir)\n    )\n\n\ndef _eco_classes(config: Config) -> list[dict]:\n    """Return the active class table (host classes or the generic default)."""\n    return list(config.economy.get("classes") or DEFAULT_CLASSES)\n\n\ndef _eco_md_files(docs_root: Path) -> list[Path]:\n    """Return every ``*.md`` under ``docs_root`` (sorted, empty if absent)."""\n    if not docs_root.exists():\n        return []\n    return sorted(docs_root.rglob("*.md"))\n\n\ndef _eco_read_text(path: Path) -> str | None:\n    """Read ``path`` as UTF-8 text; None when unreadable or not text."""\n    try:\n        return path.read_text(encoding="utf-8")\n    except (OSError, UnicodeDecodeError):\n        return None\n\n\ndef _eco_badge_token(path: Path) -> str | None:\n    """Return the doc\'s Status-badge token from its first 12 lines, or None."""\n    text = _eco_read_text(path)\n    if text is None:\n        return None\n    match = _ECO_BADGE_RE.search("\\n".join(text.splitlines()[:12]))\n    return match.group(1) if match else None\n\n\ndef _eco_wc(path: Path) -> int:\n    """Return the whitespace word count of one text file (0 if unreadable)."""\n    text = _eco_read_text(path)\n    return len(text.split()) if text else 0\n\n\ndef _eco_rel(path: Path, root: Path) -> str:\n    """Return ``path`` relative to ``root`` as posix (absolute-safe fallback)."""\n    try:\n        return path.resolve().relative_to(root.resolve()).as_posix()\n    except ValueError:\n        return path.as_posix()\n\n\ndef classify_docs(root: Path, config: Config) -> dict[str, list[Path]]:\n    """Bucket project docs into economy classes plus the ``_unbadged`` bucket.\n\n    Classes come from ``config.economy["classes"]`` (``DEFAULT_CLASSES`` when\n    empty); each class matches by Status-badge token (``badges``, scanned from\n    a doc\'s first 12 lines with the check_docs regex convention) and/or by\n    root-relative ``globs``. The first matching class wins. Docs under the\n    docs root that match no class AND carry no badge land in ``"_unbadged"``.\n    """\n    docs = _eco_md_files(root / config.docs_root)\n    buckets: dict[str, list[Path]] = {}\n    assigned: set[Path] = set()\n    for cls in _eco_classes(config):\n        matched: set[Path] = set()\n        for pattern in cls.get("globs", []):\n            expanded = _eco_expand(str(pattern), config)\n            matched.update(p for p in root.glob(expanded) if p.is_file())\n        badges = set(cls.get("badges", []))\n        if badges:\n            matched.update(f for f in docs if _eco_badge_token(f) in badges)\n        fresh = sorted(p for p in matched if p.resolve() not in assigned)\n        assigned.update(p.resolve() for p in fresh)\n        buckets[cls["name"]] = fresh\n    buckets["_unbadged"] = [\n        f for f in docs if f.resolve() not in assigned and _eco_badge_token(f) is None\n    ]\n    return buckets\n\n\ndef _eco_word_cap_value(root: Path, config: Config, gauge: dict) -> int:\n    """Return a word_cap gauge\'s value: one file\'s words, or a dir\'s summed."""\n    target = root / _eco_expand(str(gauge.get("path", "")), config)\n    if target.is_dir():\n        return sum(_eco_wc(f) for f in sorted(target.rglob("*.md")))\n    if target.is_file():\n        return _eco_wc(target)\n    return 0\n\n\ndef _eco_count_cap_value(root: Path, config: Config, gauge: dict) -> int:\n    """Return a count_cap gauge\'s value: file count under its glob."""\n    pattern = _eco_expand(str(gauge.get("glob", "")), config)\n    if not pattern:\n        return 0\n    return sum(1 for p in root.glob(pattern) if p.is_file())\n\n\ndef _eco_route_budget(root: Path, config: Config) -> tuple[int, int]:\n    """Return (value, cap) for the boot-route word budget.\n\n    Value sums word counts over the boot set resolved by the orientation\n    checker\'s own ``_ob_boot_paths`` (ONE resolver for both consumers — the\n    gauge once resolved everything under docs_root and undercounted\n    root-level boot docs to 0); cap is ``orientation["budget_words"]``.\n    """\n    value = sum(_eco_wc(path) for path in _ob_boot_paths(root, config))\n    cap = int(config.orientation.get("budget_words", 7000))\n    return value, cap\n\n\ndef economy_gauges(root: Path, config: Config) -> list[dict]:\n    """Evaluate the configured gauges (word_cap / count_cap / route_budget).\n\n    When ``config.economy["gauges"]`` is empty, falls back to one\n    ``route_budget`` gauge derived from ``config.orientation``. Unknown kinds\n    are skipped. Each result is ``{"name", "kind", "value", "cap", "over"}``.\n    """\n    gauges = list(config.economy.get("gauges") or [])\n    if not gauges:\n        gauges = [{"name": "route_budget", "kind": "route_budget"}]\n    results: list[dict] = []\n    for gauge in gauges:\n        kind = str(gauge.get("kind", ""))\n        cap = int(gauge.get("cap") or 0)\n        if kind == "word_cap":\n            value = _eco_word_cap_value(root, config, gauge)\n        elif kind == "count_cap":\n            value = _eco_count_cap_value(root, config, gauge)\n        elif kind == "route_budget":\n            value, default_cap = _eco_route_budget(root, config)\n            cap = int(gauge.get("cap") or default_cap)\n        else:\n            continue\n        results.append(\n            {\n                "name": str(gauge.get("name", kind)),\n                "kind": kind,\n                "value": value,\n                "cap": cap,\n                "over": value > cap,\n            },\n        )\n    return results\n\n\ndef _eco_scan_files(root: Path, config: Config) -> list[Path]:\n    """Return the reference-scan set: docs-root ``*.md`` + reference roots."""\n    files: set[Path] = set(_eco_md_files(root / config.docs_root))\n    for pattern in config.economy.get("reference_roots", []):\n        expanded = _eco_expand(str(pattern), config)\n        for hit in root.glob(expanded):\n            if hit.is_file():\n                files.add(hit)\n            elif hit.is_dir():\n                files.update(p for p in hit.rglob("*") if p.is_file())\n    return sorted(files)\n\n\ndef inbound_references(\n    root: Path,\n    config: Config,\n    targets: list[Path],\n    exclude: dict[str, set[str]] | None = None,\n) -> dict[str, list[str]]:\n    """Map each target to the files that cite it (plain-text scan, stdlib).\n\n    A scanner file cites a target when it contains (a) an id-pattern token\n    (``config.economy["id_patterns"]``) drawn from the target\'s filename, or\n    (b) the target\'s filename stem. Scans every ``*.md`` under the docs root\n    plus every text file under each ``economy["reference_roots"]`` glob; a\n    file never counts as citing itself. ``exclude`` maps a target *stem* to\n    resolved scanner paths that must not count as citations — the pass record\n    whose harvest table licenses a slug\'s deletion would otherwise hold every\n    harvested file forever (the triple filter became unsatisfiable).\n    """\n    exclude = exclude or {}\n    patterns = [re.compile(p) for p in config.economy.get("id_patterns", [])]\n    scanners: list[tuple[Path, str]] = []\n    for f in _eco_scan_files(root, config):\n        text = _eco_read_text(f)\n        if text is not None:\n            scanners.append((f, text))\n    refs: dict[str, list[str]] = {}\n    for target in targets:\n        ids = {m for pat in patterns for m in pat.findall(target.name)}\n        needles = ids | {target.stem}\n        excluded = exclude.get(target.stem, set())\n        citing = {\n            _eco_rel(f, root)\n            for f, text in scanners\n            if f.resolve() != target.resolve()\n            and f.resolve().as_posix() not in excluded\n            and any(needle in text for needle in needles)\n        }\n        refs[_eco_rel(target, root)] = sorted(citing)\n    return refs\n\n\ndef _eco_expired(path: Path, window_days: Any) -> tuple[bool, int]:\n    """Return (past-window?, age-in-days) for ``path`` (mtime-based)."""\n    if window_days is None:\n        return False, 0\n    age = (time.time() - path.stat().st_mtime) / _ECO_SECONDS_PER_DAY\n    return age > float(window_days), int(age)\n\n\ndef _eco_delete_row(\n    rel: str,\n    cls: dict,\n    *,\n    expired: bool,\n    in_harvest: bool,\n    n_refs: int,\n) -> dict:\n    """Build one delete would-act row carrying the TRIPLE FILTER verdict."""\n    blockers: list[str] = []\n    if not in_harvest:\n        blockers.append("not harvested")\n    if n_refs:\n        blockers.append(f"inbound refs: {n_refs}")\n    if not expired:\n        blockers.append("window not reached")\n    return {\n        "path": rel,\n        "action": "delete",\n        "reason": f"class \'{cls[\'name\']}\' ({cls.get(\'window_days\')}d window)",\n        "eligible": not blockers,\n        "blockers": blockers,\n        "class": cls["name"],\n    }\n\n\ndef _eco_archive_row(rel: str, cls: dict, *, expired: bool) -> dict:\n    """Build one archive would-act row (window is the only gate)."""\n    return {\n        "path": rel,\n        "action": "archive",\n        "reason": f"class \'{cls[\'name\']}\' ({cls.get(\'window_days\')}d window)",\n        "eligible": expired,\n        "blockers": [] if expired else ["window not reached"],\n        "class": cls["name"],\n    }\n\n\ndef _eco_class_files(classes: list[dict], buckets: dict[str, list[Path]]) -> list:\n    """Return (class, file) pairs over every classified file, class order."""\n    return [(cls, f) for cls in classes for f in buckets.get(cls["name"], [])]\n\n\ndef _eco_class_rows(\n    root: Path,\n    classes: list[dict],\n    buckets: dict[str, list[Path]],\n    harvested: set[str],\n    refs: dict[str, list[str]],\n) -> tuple[list[dict], list[EconomyFinding], int]:\n    """Return (would-act rows, expired/delete_with_refs findings, debt)."""\n    rows: list[dict] = []\n    findings: list[EconomyFinding] = []\n    debt = 0\n    for cls, f in _eco_class_files(classes, buckets):\n        expired, age = _eco_expired(f, cls.get("window_days"))\n        rel = _eco_rel(f, root)\n        if expired:\n            debt += 1\n            message = (\n                f"{age}d old exceeds the {cls.get(\'window_days\')}d "\n                f"\'{cls[\'name\']}\' window"\n            )\n            findings.append(EconomyFinding(rel, "expired", message))\n        mode = cls.get("mode")\n        if mode == "delete_tomb":\n            n_refs = len(refs.get(rel, []))\n            in_harvest = f.stem in harvested\n            rows.append(\n                _eco_delete_row(\n                    rel,\n                    cls,\n                    expired=expired,\n                    in_harvest=in_harvest,\n                    n_refs=n_refs,\n                ),\n            )\n            if expired and n_refs:\n                message = f"expired but still cited by {n_refs} file(s)"\n                findings.append(EconomyFinding(rel, "delete_with_refs", message))\n        elif mode == "archive":\n            rows.append(_eco_archive_row(rel, cls, expired=expired))\n    return rows, findings, debt\n\n\ndef _eco_base_findings(\n    root: Path,\n    buckets: dict[str, list[Path]],\n    gauges: list[dict],\n) -> list[EconomyFinding]:\n    """Return the unbadged + over_cap findings."""\n    findings = [\n        EconomyFinding(\n            _eco_rel(f, root),\n            "unbadged",\n            "no Status badge and no economy class",\n        )\n        for f in buckets.get("_unbadged", [])\n    ]\n    findings += [\n        EconomyFinding(\n            g["name"],\n            "over_cap",\n            f"gauge \'{g[\'name\']}\' at {g[\'value\']} words/files vs cap {g[\'cap\']}",\n        )\n        for g in gauges\n        if g["over"]\n    ]\n    return findings\n\n\ndef economy_check(\n    root: Path,\n    config: Config,\n    *,\n    harvested: set[str] | None = None,\n    harvest_exclude: dict[str, set[str]] | None = None,\n) -> dict:\n    """Run the full economy pass: census, gauges, findings, debt, would-act.\n\n    Findings: ``unbadged`` (doc with no badge and no class), ``over_cap`` (a\n    gauge over its cap), ``expired`` (file past its class window — the kit\n    supports **day** windows only; "bands" are a host cadence unit, not a kit\n    unit), and ``delete_with_refs`` (an expired delete-class file still\n    cited). ``debt`` counts expired files. ``would_act`` delete rows carry the\n    TRIPLE FILTER: eligible only when the file\'s stem (slug) is in\n    ``harvested`` AND it is past its window AND it has zero inbound refs;\n    blockers are the explicit strings ``"not harvested"`` /\n    ``"inbound refs: N"`` / ``"window not reached"``.\n    """\n    harvested = set(harvested or set())\n    classes = _eco_classes(config)\n    buckets = classify_docs(root, config)\n    census = {\n        name: {"files": len(files), "words": sum(_eco_wc(f) for f in files)}\n        for name, files in buckets.items()\n    }\n    gauges = economy_gauges(root, config)\n    delete_targets = [\n        f\n        for cls in classes\n        if cls.get("mode") == "delete_tomb"\n        for f in buckets.get(cls["name"], [])\n    ]\n    refs = (\n        inbound_references(root, config, delete_targets, harvest_exclude)\n        if delete_targets\n        else {}\n    )\n    rows, class_findings, debt = _eco_class_rows(\n        root,\n        classes,\n        buckets,\n        harvested,\n        refs,\n    )\n    findings = _eco_base_findings(root, buckets, gauges) + class_findings\n    return {\n        "census": census,\n        "gauges": gauges,\n        "findings": findings,\n        "debt": debt,\n        "would_act": rows,\n    }\n\n\ndef tombstone_line(path: Path, summary: str) -> str:\n    """Render one ~20-word tombstone: ``slug - date - last path - what-it-was``."""\n    short = " ".join(summary.split()[:12])\n    return f"- {path.stem} - {date.today().isoformat()} - {path.as_posix()} - {short}"\n\n\ndef _eco_doc_summary(path: Path) -> str:\n    """Return a short what-it-was summary: first heading or non-blank line."""\n    text = _eco_read_text(path) or ""\n    lines = [line.strip() for line in text.splitlines() if line.strip()]\n    for line in lines:\n        if line.startswith("#"):\n            return line.lstrip("#").strip()\n    return lines[0] if lines else "(empty file)"\n\n\ndef _eco_tombstone_shard(\n    root: Path,\n    config: Config,\n    cls: dict,\n    rel_path: Path,\n) -> Path:\n    """Return the per-band tombstone shard path for one deleted file\'s class."""\n    tomb = cls.get("tombstone_dir")\n    if tomb:\n        tomb_dir = root / _eco_expand(str(tomb), config)\n    else:\n        tomb_dir = root / rel_path.parent / "pruned"\n    return tomb_dir / f"band-{date.today().strftime(\'%Y%m\')}.md"\n\n\ndef _eco_append_tombstone(shard: Path, line: str) -> None:\n    """Append one tombstone line to the shard (create with banner if absent).\n\n    Read-modify-write through ``atomic_write_text`` so a crash mid-append can\n    never leave a truncated shard.\n    """\n    if shard.exists():\n        text = shard.read_text(encoding="utf-8")\n        if not text.endswith("\\n"):\n            text += "\\n"\n    else:\n        today = date.today()\n        text = (\n            f"# Tombstones — band {today.strftime(\'%Y%m\')}\\n\\n"\n            "> **Status:** `archive`\\n\\n"\n            f"> Pruned by the context-economy actuator; created "\n            f"{today.isoformat()}. One line per deleted file: "\n            "slug - date - last path - what-it-was.\\n\\n"\n        )\n    atomic_write_text(shard, text + line + "\\n")\n\n\ndef _eco_dry_line(row: dict) -> str:\n    """Render one would-act row as a dry-run report line."""\n    if row.get("eligible"):\n        return f"would {row[\'action\']} {row[\'path\']} ({row[\'reason\']})"\n    return f"hold {row[\'path\']}: " + "; ".join(row.get("blockers", []))\n\n\ndef _eco_apply_rows(root: Path, config: Config, rows: list[dict]) -> list[str]:\n    """Delete eligible delete rows, tombstoning each; archive rows advisory."""\n    class_by_name = {c["name"]: c for c in _eco_classes(config)}\n    lines: list[str] = []\n    for row in rows:\n        if not row.get("eligible"):\n            lines.append(_eco_dry_line(row))\n            continue\n        if row.get("action") != "delete":\n            lines.append(\n                f"advisory: {row[\'action\']} {row[\'path\']} is a host action — "\n                "the kit never moves files",\n            )\n            continue\n        path = root / row["path"]\n        if not path.is_file():\n            lines.append(f"skipped {row[\'path\']}: file no longer exists")\n            continue\n        cls = class_by_name.get(str(row.get("class", "")), {})\n        shard = _eco_tombstone_shard(root, config, cls, Path(row["path"]))\n        summary = _eco_doc_summary(path)\n        _eco_append_tombstone(shard, tombstone_line(Path(row["path"]), summary))\n        path.unlink()\n        lines.append(f"deleted {row[\'path\']} -> tombstone {_eco_rel(shard, root)}")\n    return lines\n\n\ndef economy_actuate(\n    root: Path,\n    config: Config,\n    report: dict,\n    *,\n    apply: bool = False,\n    acknowledged: bool = False,\n) -> list[str]:\n    """Apply (or dry-run) the would-act plan from ``economy_check``.\n\n    Dry-run (the default) returns the would-act lines without touching\n    anything. ``apply=True`` acts only under the maturity ALLOWLIST:\n    ``"normal"`` applies, ``"gated"`` applies only with\n    ``acknowledged=True`` (the CE-14 first-prune human-review tier), and\n    anything else — including ``"shadow"`` and any typo — refuses outright.\n    The lock is acquired atomically (``O_CREAT|O_EXCL``); a pre-existing lock\n    refuses (another actuation in flight) and is left in place. It then\n    deletes ONLY eligible delete rows (one tombstone line per deletion,\n    appended to the class\'s ``<tombstone_dir>/band-<YYYYMM>.md`` shard),\n    removes its own lock in a ``finally`` block, and returns the action\n    lines. Archive rows are advisory — the kit never moves files.\n    """\n    if not apply:\n        return [_eco_dry_line(row) for row in report.get("would_act", [])]\n    maturity = str(config.economy.get("maturity", "shadow")).strip().lower()\n    if maturity not in ("gated", "normal"):\n        # Allowlist, not a blocklist: a typo\'d maturity ("Shadow", "shadoww")\n        # must refuse, never silently apply — deletion is the one place the\n        # kit\'s fail-open posture inverts to fail-closed.\n        return [\n            f"refused: economy maturity {maturity!r} does not permit apply "\n            "(allowed: \'gated\' with --reviewed, \'normal\') — nothing changed",\n        ]\n    if maturity == "gated" and not acknowledged:\n        return [\n            "refused: economy maturity is \'gated\' — the first executing prune "\n            "needs an explicit human review acknowledgment (pass --reviewed); "\n            "promote maturity to \'normal\' once the first prune has been "\n            "reviewed — nothing changed",\n        ]\n    lock = root / config.state_dir / "economy.lock"\n    lock.parent.mkdir(parents=True, exist_ok=True)\n    try:\n        # O_CREAT|O_EXCL: atomic acquire — check-then-create raced, and two\n        # concurrent actuations could clobber a tombstone shard.\n        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)\n    except FileExistsError:\n        return [\n            f"refused: {config.state_dir}/economy.lock exists — another "\n            "actuation may be in flight; nothing changed",\n        ]\n    try:\n        with os.fdopen(fd, "w", encoding="utf-8") as handle:\n            handle.write(f"locked {date.today().isoformat()}\\n")\n        return _eco_apply_rows(root, config, report.get("would_act", []))\n    finally:\n        lock.unlink(missing_ok=True)\n\n\ndef issue_body(report: dict) -> str:\n    """Render the retention-debt routine issue body (markdown).\n\n    Census table + debt count + the top would-act rows (eligible first) — the\n    ``--issue-body`` emit the debt-threshold routine posts.\n    """\n    lines = [\n        "## Context-economy retention debt",\n        "",\n        f"**Debt (expired files): {report.get(\'debt\', 0)}**",\n        "",\n        "### Census",\n        "",\n        "| class | files | words |",\n        "| --- | --- | --- |",\n    ]\n    for name, row in sorted(report.get("census", {}).items()):\n        lines.append(f"| {name} | {row[\'files\']} | {row[\'words\']} |")\n    top = sorted(report.get("would_act", []), key=lambda r: not r.get("eligible"))\n    if top:\n        lines += ["", "### Top would-act rows", ""]\n        lines += [f"- {_eco_dry_line(row)}" for row in top[:10]]\n    return "\\n".join(lines) + "\\n"\n',
    'engine/economy/harvest.py': '"""Harvest-table parsing + stub rendering (plan §5.B, Lane B4).\n\nThe harvest table is the delete-side safety input of the TRIPLE FILTER: a\npass record commits what it *harvested* from the files it reviewed into a\nmarkdown table under a heading containing "harvest". ``parse_harvest_tables``\nrecovers the committed slugs (a file is delete-eligible only once its slug\nappears here); ``harvest_table_stub`` renders the kit-defined row format,\nwhich round-trips through the parser. Pure stdlib; returns data / text.\n"""\n\nfrom __future__ import annotations\n\nimport re\nfrom pathlib import Path\n\n_HRV_HEADING_RE = re.compile(r"^#{1,6}\\s")\n# A table separator row: only pipes, dashes, colons, and whitespace.\n_HRV_SEPARATOR_RE = re.compile(r"^\\|[\\s:|-]+\\|?$")\n\n_HRV_HEADER_ROW = "| slug | status/PR | ⚑ flags | 💡 ideas | 📊 telemetry |"\n_HRV_SEPARATOR_ROW = "| --- | --- | --- | --- | --- |"\n\n\ndef _hrv_first_cell(line: str) -> str | None:\n    """Return a table row\'s first-column cell (None when empty)."""\n    cells = [c.strip() for c in line.strip().strip("|").split("|")]\n    if not cells:\n        return None\n    cell = cells[0].strip("`* ")\n    return cell or None\n\n\ndef _hrv_slugs_from_text(text: str) -> set[str]:\n    """Collect first-column data cells from tables under harvest headings.\n\n    A "harvest heading" is any markdown heading containing ``harvest``\n    (case-insensitive). Within such a section, each contiguous run of ``|``\n    lines is one table: its first row is the header (skipped), separator rows\n    are skipped, every other row contributes its first cell. Surrounding\n    prose is tolerated.\n    """\n    slugs: set[str] = set()\n    in_harvest = False\n    in_table = False\n    table_is_harvest = False\n    for line in text.splitlines():\n        if _HRV_HEADING_RE.match(line):\n            in_harvest = "harvest" in line.lower()\n            in_table = False\n            continue\n        if not in_harvest or not line.lstrip().startswith("|"):\n            in_table = False\n            continue\n        if not in_table:\n            # First row of a new table = header. Only a table whose FIRST\n            # header cell is "slug" is a harvest table — an inventory or\n            # pending table under a "Harvest backlog" heading must never mark\n            # files as harvested (that is a deletion license).\n            in_table = True\n            header = (_hrv_first_cell(line) or "").lower()\n            table_is_harvest = header == "slug"\n            continue\n        if not table_is_harvest or _HRV_SEPARATOR_RE.match(line.strip()):\n            continue\n        cell = _hrv_first_cell(line)\n        if cell:\n            slugs.add(cell)\n    return slugs\n\n\ndef parse_harvest_tables(pass_records_dir: Path) -> set[str]:\n    """Return every harvested slug committed in the pass-record tables.\n\n    Scans ``*.md`` under ``pass_records_dir`` for markdown tables sitting\n    under any heading containing ``"harvest"`` (case-insensitive) and\n    collects the first-column cell of each data row (header + separator rows\n    skipped). Tolerant of surrounding prose; empty set when the directory is\n    absent.\n    """\n    if not pass_records_dir.is_dir():\n        return set()\n    slugs: set[str] = set()\n    for f in sorted(pass_records_dir.glob("*.md")):\n        try:\n            text = f.read_text(encoding="utf-8")\n        except (OSError, UnicodeDecodeError):\n            continue\n        slugs |= _hrv_slugs_from_text(text)\n    return slugs\n\n\ndef harvest_table_stub(entries: list[dict]) -> str:\n    """Render the kit-defined harvest table for ``entries``.\n\n    Columns: ``slug | status/PR | ⚑ flags | 💡 ideas | 📊 telemetry``. Each\n    entry supplies ``slug`` (required) plus optional ``status`` / ``flags`` /\n    ``ideas`` / ``telemetry``. The output includes the ``## Harvest`` heading\n    so it round-trips through ``parse_harvest_tables`` unchanged.\n    """\n    lines = ["## Harvest", "", _HRV_HEADER_ROW, _HRV_SEPARATOR_ROW]\n    for entry in entries:\n        lines.append(\n            "| {slug} | {status} | {flags} | {ideas} | {telemetry} |".format(\n                slug=entry.get("slug", ""),\n                status=entry.get("status", "—"),\n                flags=entry.get("flags", "—"),\n                ideas=entry.get("ideas", "—"),\n                telemetry=entry.get("telemetry", "—"),\n            ),\n        )\n    return "\\n".join(lines) + "\\n"\n\n\ndef harvest_sources(pass_records_dir: Path) -> dict[str, set[str]]:\n    """Map each harvested slug to the pass-record files that harvested it.\n\n    The harvest table row is the *deletion license* for its slug — the pass\n    record naming a slug must not count as an inbound reference to it, or the\n    triple filter becomes unsatisfiable (every harvested file is "referenced"\n    by its own harvest record).\n    """\n    sources: dict[str, set[str]] = {}\n    if not pass_records_dir.is_dir():\n        return sources\n    for record in sorted(pass_records_dir.glob("*.md")):\n        try:\n            text = record.read_text(encoding="utf-8")\n        except (OSError, UnicodeDecodeError):\n            continue\n        for slug in _hrv_slugs_from_text(text):\n            sources.setdefault(slug, set()).add(record.resolve().as_posix())\n    return sources\n',
    'engine/economy/simulator.py': '"""Retention-policy simulator for the context economy (plan §5.B, Lane B5).\n\nA generalized port of superbot\'s ``tools/sim/retention_policy_sim.py``\n(sim-driven design applied to the memory system itself). It models a docs\ncorpus growing over sessions, agents reading it (boot route, grep discovery,\ndirectory scans, back-references into pruned content, stale encounters), and a\ncandidate retention policy acting on it. The grid search scores each candidate\non expected agent context cost (words per session) under a hard feasibility\nconstraint (retrieval-miss risk), with a secondary lean-by-construction\nobjective (smallest tree at horizon among near-best feasible policies) and a\n×1/3–×3 sensitivity sweep over the assumption-grade constants.\n\nThe kit ships the SEARCH, not any project\'s constants: every number returned\nby ``default_calibration()`` is an UNVERIFIED illustrative placeholder. Run\n``calibration_recipe()`` for the measurement plan, replace the numbers with\nyour repo\'s, then re-run ``run_search``.\n\nCalibration shape (one plain dict; all costs are words unless noted)::\n\n    {\n      # velocity\n      "sessions_per_band": 20.0,     # sessions per reconciliation band\n      "words_per_token": 0.75,       # for the tokens-saved line in why-it-won\n      "initial_age_bands": 12,       # today\'s stock spread uniformly this deep\n      # living-file stocks and boot route\n      "live_files": 100.0,           # living/working docs (non-terminal)\n      "live_words": 150000.0,\n      "boot_fixed_words": 6000.0,    # always-read orientation route\n      "journal_words": 4000.0,       # cappable process-memory journal\n      "journal_caps": [1000000, 2000],   # grid toggle: uncapped vs capped\n      "ledger_base_words": 1500.0,   # living ledger lean head\n      "ledger_tail_per_band": 300.0, # narrative accretion per band if untrimmed\n      "ledger_tail_bands_initial": 6,\n      "ledger_tail_compressed_bands": 2,\n      "index_active_line_words": 20.0,\n      "index_hist_line_words": 18.0,\n      "tombstone_words": 20.0,       # one tombstone index line\n      # discovery tax\n      "greps_per_session": 8.0,\n      "grep_hits_per_1k_files": 50.0,\n      "skim_words_per_hit": 12.0,    # path skim in -l output\n      "open_frac_per_hit": 0.10,     # fraction opened before badge-bail\n      "open_words_per_hit": 200.0,\n      "archive_pollution_w_per_mw": 25.0,  # content-grep noise per Mw archived\n      "maintenance_w_per_mw": 8.0,   # sweep/link-check burden per Mw in tree\n      "ls_scan_words_per_file": 5.0,\n      "ls_scans_per_session": 2.0,\n      # back-references into terminal content\n      "backref_halflife_bands": 3.0, # demand decays with age (exponential)\n      "tombstone_hop_words": 300.0,  # tombstone -> history-recovery effort\n      "bare_rederive_words": 3000.0, # no pointer: re-derive / re-decide\n      "bare_find_fail": 0.5,         # P(recovery fails without a tombstone)\n      # staleness (assumption-grade; sweep it)\n      "stale_act_base": 0.01,        # P/session of acting on stale content\n      "stale_act_cost": 10000.0,\n      # feasibility + search knobs\n      "miss_per_band_max": 0.005,    # hard constraint on retrieval-miss risk\n      "near_best_frac": 0.05,        # secondary-objective envelope\n      "grid_scale": 1,               # widening knob: N multiplies each class\'s\n                                     # candidate windows by 1..N (bigger grid)\n      "sensitivity_multipliers": [1/3, 3],\n      "sensitivity_keys": ["stale_act_base", "classes.sessions.backref_rate"],\n      # document classes (per-class mode × window searched per declarations)\n      "classes": [\n        {\n          "name": "sessions",\n          "birth_rate": 1.0,         # new files per session\n          "words_each": 700.0,\n          "initial_files": 240.0,\n          "cited_frac": 0.05,        # inbound-live-reference blocking fraction\n          "cascade_unlock_frac": 0.0,  # share of cited_frac released when the\n                                       # living tails compress (ledger cascade)\n          "backref_rate": 0.05,      # back-reference demand per session\n          "tombstone_lines_each": 0.0,  # index lines left per deleted doc\n          "indexed": False,          # hist files add boot-index lines\n          "active_pool": None,       # or {"initial": F, "lifetime_bands": B}\n                                     # for classes born active, then terminal\n          "modes": ["keep", "archive", "delete_tomb", "delete_bare"],\n          "windows": [1, 2, 4],      # candidate windows, in bands\n        },\n        ...\n      ],\n    }\n\nPolicy shape (``policy_grid`` builds these; you can hand-craft one too)::\n\n    {"name": str,   # optional on hand-crafted policies; derived when absent\n     "classes": {<class name>: {"mode": <RETENTION_MODES member>, "window": int}},\n     "ledger_compress": bool, "journal_cap": float,\n     "index_hist_tombstones": bool}\n\nPure stdlib, deterministic per seed (``random.Random`` instances only, no\nrandomness at import), no I/O, never prints — the CLI wires presentation.\n"""\n\nfrom __future__ import annotations\n\nimport copy\nimport itertools\nimport random\nfrom typing import Any\n\nRETENTION_MODES: tuple[str, ...] = ("keep", "archive", "delete_tomb", "delete_bare")\n\n\ndef default_calibration() -> dict[str, Any]:\n    """Return a neutral, illustrative calibration — every value UNVERIFIED.\n\n    These numbers exist so the search runs out of the box and the shape is\n    executable documentation; they are NOT measurements of any repo. Follow\n    ``calibration_recipe()`` to measure your own corpus before trusting a\n    winner. The default grid is deliberately small (a few seconds end to end);\n    raise ``grid_scale`` to widen the candidate windows.\n    """\n    return {\n        "sessions_per_band": 20.0,\n        "words_per_token": 0.75,\n        "initial_age_bands": 12,\n        "live_files": 100.0,\n        "live_words": 150000.0,\n        "boot_fixed_words": 6000.0,\n        "journal_words": 4000.0,\n        "journal_caps": [1000000, 2000],\n        "ledger_base_words": 1500.0,\n        "ledger_tail_per_band": 300.0,\n        "ledger_tail_bands_initial": 6,\n        "ledger_tail_compressed_bands": 2,\n        "index_active_line_words": 20.0,\n        "index_hist_line_words": 18.0,\n        "tombstone_words": 20.0,\n        "greps_per_session": 8.0,\n        "grep_hits_per_1k_files": 50.0,\n        "skim_words_per_hit": 12.0,\n        "open_frac_per_hit": 0.10,\n        "open_words_per_hit": 200.0,\n        "archive_pollution_w_per_mw": 25.0,\n        "maintenance_w_per_mw": 8.0,\n        "ls_scan_words_per_file": 5.0,\n        "ls_scans_per_session": 2.0,\n        "backref_halflife_bands": 3.0,\n        "tombstone_hop_words": 300.0,\n        "bare_rederive_words": 3000.0,\n        "bare_find_fail": 0.5,\n        "stale_act_base": 0.01,\n        "stale_act_cost": 10000.0,\n        "miss_per_band_max": 0.005,\n        "near_best_frac": 0.05,\n        "grid_scale": 1,\n        "sensitivity_multipliers": [1 / 3, 3],\n        "sensitivity_keys": [\n            "stale_act_base",\n            "grep_hits_per_1k_files",\n            "maintenance_w_per_mw",\n            "archive_pollution_w_per_mw",\n            "classes.sessions.backref_rate",\n            "classes.plans.backref_rate",\n        ],\n        "classes": [\n            {\n                "name": "sessions",\n                "birth_rate": 1.0,\n                "words_each": 700.0,\n                "initial_files": 240.0,\n                "cited_frac": 0.05,\n                "cascade_unlock_frac": 0.0,\n                "backref_rate": 0.05,\n                "tombstone_lines_each": 0.0,\n                "indexed": False,\n                "active_pool": None,\n                "modes": ["keep", "archive", "delete_tomb", "delete_bare"],\n                "windows": [1, 2, 4],\n            },\n            {\n                "name": "plans",\n                "birth_rate": 0.25,\n                "words_each": 2500.0,\n                "initial_files": 60.0,\n                "cited_frac": 0.90,\n                "cascade_unlock_frac": 0.85,\n                "backref_rate": 0.20,\n                "tombstone_lines_each": 1.0,\n                "indexed": True,\n                "active_pool": {"initial": 40.0, "lifetime_bands": 4.0},\n                "modes": ["keep", "archive", "delete_tomb"],\n                "windows": [2, 4],\n            },\n            {\n                "name": "notes",\n                "birth_rate": 0.20,\n                "words_each": 800.0,\n                "initial_files": 40.0,\n                "cited_frac": 0.10,\n                "cascade_unlock_frac": 0.0,\n                "backref_rate": 0.02,\n                "tombstone_lines_each": 1.0,\n                "indexed": False,\n                "active_pool": None,\n                "modes": ["delete_tomb"],\n                "windows": [4],\n            },\n        ],\n    }\n\n\n# ---------------------------------------------------------------------------\n# Policy space\n# ---------------------------------------------------------------------------\n\n\ndef _sim_policy_name(policy: dict[str, Any]) -> str:\n    """Render the deterministic display name for one policy dict."""\n    parts = [\n        f"{name}={spec[\'mode\']}@{spec[\'window\']}b"\n        for name, spec in sorted(policy["classes"].items())\n    ]\n    parts.append(f"ledger={\'compress\' if policy[\'ledger_compress\'] else \'grow\'}")\n    parts.append(f"journal<={policy[\'journal_cap\']:g}")\n    parts.append(f"idx={\'tomb\' if policy[\'index_hist_tombstones\'] else \'full\'}")\n    return " ".join(parts)\n\n\ndef _sim_class_candidates(\n    cls_cal: dict[str, Any],\n    grid_scale: int,\n) -> list[tuple[str, int]]:\n    """Return the (mode, window) candidates one class declaration allows.\n\n    ``keep`` collapses to a single ``(keep, 0)`` candidate (its window is\n    meaningless); ``grid_scale`` N widens each declared window by factors\n    1..N, deduplicated and sorted, so hosts can search deeper without editing\n    the class declarations.\n    """\n    windows = sorted(\n        {\n            int(w) * f\n            for w in cls_cal["windows"]\n            for f in range(1, max(grid_scale, 1) + 1)\n        },\n    )\n    candidates: list[tuple[str, int]] = []\n    for mode in cls_cal["modes"]:\n        if mode == "keep":\n            candidates.append(("keep", 0))\n        else:\n            candidates.extend((mode, w) for w in windows)\n    return candidates\n\n\ndef policy_grid(calibration: dict[str, Any]) -> list[dict[str, Any]]:\n    """Build the candidate-policy grid from the calibration\'s class declarations.\n\n    The grid is the cartesian product of every class\'s ``modes`` × ``windows``\n    (widened by ``grid_scale``), crossed with the living-file toggles: ledger\n    compression on/off and each ``journal_caps`` value. Historical index lines\n    are always tombstone-compressed in generated candidates (the status-quo\n    baseline inside ``run_search`` covers the full-line alternative).\n    """\n    grid_scale = int(calibration.get("grid_scale", 1))\n    class_names = [c["name"] for c in calibration["classes"]]\n    per_class = [_sim_class_candidates(c, grid_scale) for c in calibration["classes"]]\n    journal_caps = calibration.get("journal_caps", [10**9])\n    policies: list[dict[str, Any]] = []\n    for combo in itertools.product(*per_class):\n        for ledger_compress, journal_cap in itertools.product(\n            (True, False),\n            journal_caps,\n        ):\n            policy: dict[str, Any] = {\n                "classes": {\n                    name: {"mode": mode, "window": window}\n                    for name, (mode, window) in zip(class_names, combo, strict=True)\n                },\n                "ledger_compress": ledger_compress,\n                "journal_cap": float(journal_cap),\n                "index_hist_tombstones": True,\n            }\n            policy["name"] = _sim_policy_name(policy)\n            policies.append(policy)\n    return policies\n\n\ndef _sim_status_quo(calibration: dict[str, Any]) -> dict[str, Any]:\n    """Return the keep-everything baseline policy for this calibration."""\n    policy: dict[str, Any] = {\n        "classes": {\n            c["name"]: {"mode": "keep", "window": 0} for c in calibration["classes"]\n        },\n        "ledger_compress": False,\n        "journal_cap": float(10**9),\n        "index_hist_tombstones": False,\n    }\n    policy["name"] = _sim_policy_name(policy)\n    return policy\n\n\n# ---------------------------------------------------------------------------\n# Corpus state: per class, bucketed by age-in-bands since terminal\n# ---------------------------------------------------------------------------\n\n\ndef _sim_initial_state(calibration: dict[str, Any]) -> dict[str, Any]:\n    """Build the initial corpus state from the calibration\'s stocks.\n\n    Each class\'s initial terminal stock is spread uniformly over\n    ``initial_age_bands`` age buckets (bucket index = bands since the file\n    went terminal); classes with an ``active_pool`` start with its declared\n    active count.\n    """\n    age_bands = max(int(calibration.get("initial_age_bands", 12)), 1)\n    classes: dict[str, dict[str, Any]] = {}\n    for cls in calibration["classes"]:\n        pool = cls.get("active_pool") or {}\n        classes[cls["name"]] = {\n            "buckets": [float(cls.get("initial_files", 0.0)) / age_bands] * age_bands,\n            "active": float(pool.get("initial", 0.0)),\n        }\n    return {\n        "classes": classes,\n        "archived_words": 0.0,\n        "tombstone_lines": 0.0,\n        "ledger_tail_bands": float(calibration.get("ledger_tail_bands_initial", 0)),\n    }\n\n\ndef _sim_age_out(buckets: list[float], window: int, keep_frac: float) -> float:\n    """Prune buckets older than ``window`` in place; return files removed.\n\n    ``keep_frac`` is the citation-locked fraction that stays in place (still\n    referenced by living docs, so not yet removable).\n    """\n    removed = 0.0\n    for i in range(len(buckets)):\n        if i >= window and buckets[i] > 0:\n            hold = buckets[i] * keep_frac\n            removed += buckets[i] - hold\n            buckets[i] = hold\n    return removed\n\n\ndef _sim_grow(\n    state: dict[str, Any],\n    calibration: dict[str, Any],\n    rng: random.Random,\n) -> None:\n    """Advance one band of corpus growth (births, completions, tail accretion).\n\n    Births carry a small deterministic-per-seed jitter (±10%) so the seed is\n    load-bearing; the draw count per band is policy-independent, which keeps\n    same-seed policy comparisons exact.\n    """\n    n_sessions = float(calibration["sessions_per_band"])\n    for cls in calibration["classes"]:\n        cs = state["classes"][cls["name"]]\n        births = float(cls["birth_rate"]) * n_sessions * (0.9 + 0.2 * rng.random())\n        pool = cls.get("active_pool")\n        if pool:\n            lifetime = max(float(pool.get("lifetime_bands", 1.0)), 1.0)\n            completions = cs["active"] / lifetime\n            cs["active"] += births - completions\n            cs["buckets"].insert(0, completions)\n        else:\n            cs["buckets"].insert(0, births)\n\n\ndef _sim_prune(\n    state: dict[str, Any],\n    policy: dict[str, Any],\n    calibration: dict[str, Any],\n) -> None:\n    """Apply one band of the policy\'s per-class retention actions.\n\n    Inbound-reference blocking: a class\'s ``cited_frac`` locks that share of\n    delete-eligible files in place; when the policy compresses the living\n    tails, ``cascade_unlock_frac`` of that lock is released (the deletability\n    cascade — provenance decoration in living history tails is the top citer).\n    Archiving is never citation-blocked: the body stays recoverable in-tree.\n    """\n    for cls in calibration["classes"]:\n        spec = policy["classes"][cls["name"]]\n        mode, window = spec["mode"], int(spec["window"])\n        if mode == "keep" or window <= 0:\n            continue\n        block = float(cls.get("cited_frac", 0.0))\n        if policy["ledger_compress"]:\n            block *= 1.0 - float(cls.get("cascade_unlock_frac", 0.0))\n        buckets = state["classes"][cls["name"]]["buckets"]\n        if mode == "archive":\n            moved = _sim_age_out(buckets, window, keep_frac=0.0)\n            state["archived_words"] += moved * float(cls["words_each"])\n        elif mode == "delete_tomb":\n            gone = _sim_age_out(buckets, window, keep_frac=block)\n            state["tombstone_lines"] += gone * float(\n                cls.get("tombstone_lines_each", 1.0),\n            )\n        elif mode == "delete_bare":\n            _sim_age_out(buckets, window, keep_frac=block)\n\n\ndef _sim_dispo(mode: str, window: int, halflife: float) -> tuple[float, float, float]:\n    """Split back-reference demand into (in-tree, tombstone, bare) fractions.\n\n    Demand decays exponentially with age (``halflife`` in bands); the share\n    older than the prune window lands on the pruned disposition.\n    """\n    if mode in ("keep", "archive") or window <= 0:\n        return 1.0, 0.0, 0.0\n    p_old = 0.5 ** (window / max(halflife, 0.1))\n    if mode == "delete_tomb":\n        return 1.0 - p_old, p_old, 0.0\n    return 1.0 - p_old, 0.0, p_old\n\n\ndef _sim_boot_cost(\n    state: dict[str, Any],\n    policy: dict[str, Any],\n    calibration: dict[str, Any],\n) -> float:\n    """Return the per-session boot tax (always-read route, words)."""\n    tail_bands = (\n        float(calibration.get("ledger_tail_compressed_bands", 2))\n        if policy["ledger_compress"]\n        else state["ledger_tail_bands"]\n    )\n    ledger_tail = tail_bands * float(calibration["ledger_tail_per_band"])\n    journal = min(float(calibration["journal_words"]), float(policy["journal_cap"]))\n    per_hist = (\n        float(calibration["tombstone_words"])\n        if policy["index_hist_tombstones"]\n        else float(calibration["index_hist_line_words"])\n    )\n    index_words = state["tombstone_lines"] * float(calibration["tombstone_words"])\n    for cls in calibration["classes"]:\n        if not cls.get("indexed", False):\n            continue\n        cs = state["classes"][cls["name"]]\n        index_words += cs["active"] * float(calibration["index_active_line_words"])\n        index_words += sum(cs["buckets"]) * per_hist\n    return (\n        float(calibration["boot_fixed_words"])\n        + journal\n        + float(calibration["ledger_base_words"])\n        + ledger_tail\n        + index_words\n    )\n\n\ndef _sim_discovery_cost(\n    state: dict[str, Any],\n    calibration: dict[str, Any],\n    term_files: float,\n    term_words: float,\n) -> float:\n    """Return the per-session discovery tax (grep noise, scans, maintenance)."""\n    live_files = float(calibration["live_files"]) + sum(\n        cs["active"] for cs in state["classes"].values()\n    )\n    total_files = term_files + live_files\n    hits_per_grep = float(calibration["grep_hits_per_1k_files"]) * total_files / 1000.0\n    term_share = term_files / max(total_files, 1.0)\n    per_hit = float(calibration["skim_words_per_hit"]) + float(\n        calibration["open_frac_per_hit"],\n    ) * float(calibration["open_words_per_hit"])\n    grep_noise = (\n        float(calibration["greps_per_session"]) * hits_per_grep * term_share * per_hit\n    )\n    ls_noise = (\n        float(calibration["ls_scans_per_session"])\n        * term_files\n        * float(calibration["ls_scan_words_per_file"])\n    )\n    arch_noise = (\n        float(calibration["archive_pollution_w_per_mw"]) * state["archived_words"] / 1e6\n    )\n    tree_words = term_words + float(calibration["live_words"]) + state["archived_words"]\n    maintenance = float(calibration["maintenance_w_per_mw"]) * tree_words / 1e6\n    return grep_noise + ls_noise + arch_noise + maintenance\n\n\ndef _sim_backref_and_miss(\n    policy: dict[str, Any],\n    calibration: dict[str, Any],\n) -> tuple[float, float]:\n    """Return (back-reference cost, retrieval-miss events), both per session.\n\n    In-tree demand costs nothing extra (reading a present body is work, not\n    waste); a tombstone costs one recovery hop; a bare deletion costs a full\n    re-derivation when recovery fails and a doubled hop when it succeeds. The\n    miss metric counts only failed bare recoveries — the risk the feasibility\n    constraint bounds.\n    """\n    halflife = float(calibration["backref_halflife_bands"])\n    hop = float(calibration["tombstone_hop_words"])\n    fail = float(calibration["bare_find_fail"])\n    rederive = float(calibration["bare_rederive_words"])\n    backref = miss = 0.0\n    for cls in calibration["classes"]:\n        spec = policy["classes"][cls["name"]]\n        _in_tree, tomb, bare = _sim_dispo(spec["mode"], int(spec["window"]), halflife)\n        rate = float(cls.get("backref_rate", 0.0))\n        backref += rate * tomb * hop\n        backref += rate * bare * (fail * rederive + (1.0 - fail) * hop * 2.0)\n        miss += rate * bare * fail\n    return backref, miss\n\n\ndef _sim_stale_cost(\n    state: dict[str, Any],\n    policy: dict[str, Any],\n    calibration: dict[str, Any],\n    term_words: float,\n    initial_term_words: float,\n) -> float:\n    """Return the per-session staleness cost (acting on dead content as live)."""\n    tail_bands = (\n        float(calibration.get("ledger_tail_compressed_bands", 2))\n        if policy["ledger_compress"]\n        else state["ledger_tail_bands"]\n    )\n    ledger_tail = tail_bands * float(calibration["ledger_tail_per_band"])\n    norm_tail = max(\n        float(calibration.get("ledger_tail_bands_initial", 1)),\n        1.0,\n    ) * float(calibration["ledger_tail_per_band"])\n    scale = (term_words / (initial_term_words + 1.0)) * 0.6 + (\n        ledger_tail / max(norm_tail, 1.0)\n    ) * 0.4\n    return (\n        float(calibration["stale_act_base"])\n        * scale\n        * float(\n            calibration["stale_act_cost"],\n        )\n    )\n\n\ndef simulate_policy(\n    policy: dict[str, Any],\n    calibration: dict[str, Any],\n    *,\n    bands: int,\n    seed: int = 7,\n) -> dict[str, Any]:\n    """Simulate one policy over ``bands`` reconciliation bands; score it.\n\n    Returns the per-policy result record: the four per-session cost components\n    (``boot``, ``discovery``, ``backref``, ``stale``, band-averaged words per\n    session), their ``total``, the ``miss_per_band`` risk metric with its\n    ``feasible`` verdict (< ``miss_per_band_max``), and the horizon-end tree\n    size (``end_terminal_files``, ``end_tree_kwords``). Deterministic for a\n    given (policy, calibration, bands, seed).\n    """\n    rng = random.Random(seed)\n    name = policy.get("name") or _sim_policy_name(policy)\n    state = _sim_initial_state(calibration)\n    initial_term_words = sum(\n        float(c.get("initial_files", 0.0)) * float(c["words_each"])\n        for c in calibration["classes"]\n    )\n    totals = {"boot": 0.0, "discovery": 0.0, "backref": 0.0, "stale": 0.0}\n    miss_events = 0.0\n    term_files = term_words = 0.0\n    n_bands = max(int(bands), 1)\n    for _ in range(n_bands):\n        _sim_grow(state, calibration, rng)\n        if not policy["ledger_compress"]:\n            state["ledger_tail_bands"] += 1.0\n        _sim_prune(state, policy, calibration)\n        term_files = sum(sum(cs["buckets"]) for cs in state["classes"].values())\n        term_words = sum(\n            sum(state["classes"][c["name"]]["buckets"]) * float(c["words_each"])\n            for c in calibration["classes"]\n        )\n        totals["boot"] += _sim_boot_cost(state, policy, calibration)\n        totals["discovery"] += _sim_discovery_cost(\n            state,\n            calibration,\n            term_files,\n            term_words,\n        )\n        backref, miss = _sim_backref_and_miss(policy, calibration)\n        totals["backref"] += backref\n        miss_events += miss\n        totals["stale"] += _sim_stale_cost(\n            state,\n            policy,\n            calibration,\n            term_words,\n            initial_term_words,\n        )\n    per = {k: v / n_bands for k, v in totals.items()}\n    per_total = sum(per.values())\n    miss_per_band = miss_events / n_bands\n    return {\n        "policy": policy,\n        "name": name,\n        **per,\n        "total": per_total,\n        "miss_per_band": miss_per_band,\n        "feasible": miss_per_band < float(calibration.get("miss_per_band_max", 0.005)),\n        "end_terminal_files": term_files,\n        "end_tree_kwords": (\n            term_words + float(calibration["live_words"]) + state["archived_words"]\n        )\n        / 1000.0,\n    }\n\n\n# ---------------------------------------------------------------------------\n# Search, sensitivity, why-it-won\n# ---------------------------------------------------------------------------\n\n\ndef _sim_scaled(calibration: dict[str, Any], key: str, mult: float) -> dict[str, Any]:\n    """Return a deep copy of the calibration with one constant multiplied.\n\n    ``key`` is either a top-level constant name or a class field addressed as\n    ``classes.<class name>.<field>``. Unknown class addresses scale nothing\n    (the copy is returned unchanged) so pruned class lists stay sweepable.\n    """\n    scaled = copy.deepcopy(calibration)\n    if key.startswith("classes."):\n        _, cls_name, field = key.split(".", 2)\n        for cls in scaled["classes"]:\n            if cls["name"] == cls_name and field in cls:\n                cls[field] = float(cls[field]) * mult\n        return scaled\n    scaled[key] = float(scaled[key]) * mult\n    return scaled\n\n\ndef _sim_sensitivity(\n    policy: dict[str, Any],\n    calibration: dict[str, Any],\n    *,\n    bands: int,\n    seed: int,\n    base_total: float,\n) -> list[dict[str, Any]]:\n    """Re-score the winner under each sweep multiplier on each swept constant."""\n    entries: list[dict[str, Any]] = []\n    multipliers = calibration.get("sensitivity_multipliers", [1 / 3, 3])\n    for key in calibration.get("sensitivity_keys", []):\n        for mult in multipliers:\n            scaled = _sim_scaled(calibration, key, float(mult))\n            total = simulate_policy(policy, scaled, bands=bands, seed=seed)["total"]\n            entries.append(\n                {\n                    "key": key,\n                    "multiplier": float(mult),\n                    "total": total,\n                    "delta": total - base_total,\n                },\n            )\n    return entries\n\n\ndef _sim_why_it_won(\n    winner: dict[str, Any],\n    baseline: dict[str, Any],\n    calibration: dict[str, Any],\n    *,\n    feasible_count: int,\n    grid_size: int,\n    near_count: int,\n) -> str:\n    """Render the WHY-IT-WON record for one search outcome."""\n    words_per_token = max(float(calibration.get("words_per_token", 0.75)), 0.01)\n    base_total = baseline["total"]\n    saved = base_total - winner["total"]\n    pct = 100.0 * saved / base_total if base_total > 0 else 0.0\n    near_frac = float(calibration.get("near_best_frac", 0.05))\n    lines = [\n        f"winner: {winner[\'name\']}",\n        (\n            f"vs keep-everything baseline: {base_total:,.0f} -> "\n            f"{winner[\'total\']:,.0f} words/session ({pct:.0f}% lower), "\n            f"~{saved / words_per_token / 1000:.1f}k tokens/session saved"\n        ),\n        (\n            f"tree size at horizon: {baseline[\'end_tree_kwords\']:,.0f}kw -> "\n            f"{winner[\'end_tree_kwords\']:,.0f}kw"\n        ),\n        (\n            f"retrieval-miss events/band: {winner[\'miss_per_band\']:.4f} "\n            f"(constraint < {float(calibration.get(\'miss_per_band_max\', 0.005)):g})"\n        ),\n        (\n            f"feasible policies: {feasible_count} of {grid_size}; secondary "\n            f"objective picked the smallest tree among {near_count} within "\n            f"{near_frac:.0%} of the best primary score"\n        ),\n    ]\n    if not winner["feasible"]:\n        lines.append(\n            "WARNING: no candidate met the miss constraint — winner is the "\n            "lowest-cost INFEASIBLE policy; loosen windows or drop delete_bare",\n        )\n    return "\\n".join(lines)\n\n\ndef run_search(\n    calibration: dict[str, Any],\n    *,\n    bands: int = 24,\n    seed: int = 7,\n) -> dict[str, Any]:\n    """Run the full policy-grid search and return the winner with its record.\n\n    Primary objective: lowest expected words/session among FEASIBLE policies\n    (``miss_per_band`` under the calibration\'s bound). Secondary objective\n    (lean by construction): among feasible policies within ``near_best_frac``\n    of the best primary score, the smallest tree at horizon wins. Returns\n    ``{"winner", "why_it_won", "feasible_count", "sensitivity"}`` — the winner\n    is the full ``simulate_policy`` record (policy dict under ``"winner"["policy"]``).\n    If nothing is feasible the search degrades gracefully: the lowest-cost\n    infeasible policy wins and ``why_it_won`` carries a loud warning.\n    """\n    grid = policy_grid(calibration)\n    results = [\n        simulate_policy(policy, calibration, bands=bands, seed=seed) for policy in grid\n    ]\n    feasible = [r for r in results if r["feasible"]]\n    pool = feasible or sorted(results, key=lambda r: r["total"])\n    best_total = min(r["total"] for r in pool)\n    near_frac = float(calibration.get("near_best_frac", 0.05))\n    near = [r for r in pool if r["total"] <= best_total * (1.0 + near_frac)]\n    near.sort(key=lambda r: (r["end_tree_kwords"], r["total"], r["name"]))\n    winner = near[0]\n    baseline = simulate_policy(\n        _sim_status_quo(calibration),\n        calibration,\n        bands=bands,\n        seed=seed,\n    )\n    sensitivity = _sim_sensitivity(\n        winner["policy"],\n        calibration,\n        bands=bands,\n        seed=seed,\n        base_total=winner["total"],\n    )\n    why = _sim_why_it_won(\n        winner,\n        baseline,\n        calibration,\n        feasible_count=len(feasible),\n        grid_size=len(grid),\n        near_count=len(near),\n    )\n    return {\n        "winner": winner,\n        "why_it_won": why,\n        "feasible_count": len(feasible),\n        "sensitivity": sensitivity,\n    }\n\n\ndef calibration_recipe() -> str:\n    """Return the re-measurement recipe for grounding a calibration in a repo.\n\n    The kit ships the search, not our constants: every default is a\n    placeholder. Measure the five profiles below against YOUR corpus, write\n    the numbers into a copy of ``default_calibration()``, then re-run\n    ``run_search`` — and re-measure whenever the corpus shape shifts.\n    """\n    return (\n        "Calibration recipe — measure your repo, then edit default_calibration()\\n"\n        "\\n"\n        "Every default constant is an UNVERIFIED placeholder. Ground each group\\n"\n        "in measurements before trusting a winner:\\n"\n        "\\n"\n        "```sh\\n"\n        "# 1) Badge census — per-class stocks (initial_files, words_each):\\n"\n        "#    count and word-count files per lifecycle class (terminal vs live).\\n"\n        "grep -rlE \'\\\\*\\\\*Status:\\\\*\\\\* .(historical|archived)\' docs/ | wc -l\\n"\n        "grep -rlE \'\\\\*\\\\*Status:\\\\*\\\\* .(historical|archived)\' docs/ | xargs wc -w\\n"\n        "ls .sessions/*.md | wc -l && wc -w .sessions/*.md | tail -1\\n"\n        "\\n"\n        "# 2) Grep-noise profile — discovery constants (grep_hits_per_1k_files,\\n"\n        "#    share of hits landing in terminal docs): run ~20 representative\\n"\n        "#    working-term greps and count hit locations.\\n"\n        \'for t in <your 20 working terms>; do grep -rl "$t" docs/ ; done |\\n\'\n        "  sort | uniq -c | sort -rn | head\\n"\n        "\\n"\n        "# 3) Velocity — sessions_per_band and per-class birth_rate:\\n"\n        "#    files born per session over recent history.\\n"\n        "git log --since=\'30 days ago\' --oneline --merges | wc -l\\n"\n        "git log --since=\'30 days ago\' --name-only --diff-filter=A -- docs/ |\\n"\n        "  grep \'\\\\.md$\' | sort | uniq | wc -l\\n"\n        "\\n"\n        "# 4) Back-reference greps — backref_rate and cited_frac per class:\\n"\n        "#    how often terminal docs are cited from OUTSIDE their own dir.\\n"\n        "for f in .sessions/*.md; do\\n"\n        \'  grep -rl "$(basename "$f")" docs/ --include=\\\'*.md\\\' |\\n\'\n        "    grep -v \'^.sessions/\'; done | sort -u | wc -l\\n"\n        "\\n"\n        "# 5) Boot word count — boot_fixed_words / journal_words /\\n"\n        "#    ledger_base_words: word-count the always-read orientation route.\\n"\n        "wc -w CLAUDE.md .session-journal.md docs/current-state.md\\n"\n        "```\\n"\n        "\\n"\n        "Sweep discipline: constants you could not measure (staleness, archive\\n"\n        "pollution) stay assumption-grade — list them in sensitivity_keys so\\n"\n        "every search re-checks the winner under x1/3 and x3. Adopt a winner\\n"\n        "only when its rank holds across the whole sweep.\\n"\n    )\n',
    'engine/stances/stances.py': '"""Task-stance definitions — the fourth control axis (plan section 3b).\n\nA *stance* is the working agent\'s operational posture for the current task,\ndistinct from adoption-pace (``mode``), promotion-rights, and stage. Following\nRoo Code\'s proven mode model, each stance scopes three things to cut context rot\nand tool misfires:\n\n  - a **reading-route** — which docs to load first;\n  - a **tool-scope** — which action categories are in-bounds;\n  - an **output contract** — what the stance is expected to produce.\n\nThe active stance lives in state (``"stance"``) and is **advisory**: the contract\nguides the agent, and an optional PreToolUse guard can warn on an out-of-stance\naction (e.g. an edit while in ``review``) via :func:`is_out_of_stance`.\n\nLike the question bank, the set ships as a Python module — not the plan\'s literal\n``stances.yml`` — so it embeds in the stdlib-only bootstrap with no YAML parser\nand runs identically in ``src`` and the single-file ``dist``.\n"""\n\nfrom __future__ import annotations\n\n# Canonical action categories a stance\'s tool-scope is drawn from.\nREAD = "read"  # read files / memory / source\nRUN = "run"  # run read-only tools / commands\nEDIT = "edit"  # modify files\nCOMMENT = "comment"  # emit review comments (no file edits)\n\nACTIONS = (READ, RUN, EDIT, COMMENT)\n\nDEFAULT_STANCE = "analysis"\n\nSTANCES: list[dict] = [\n    {\n        "name": "question",\n        "role": "Answer concisely from memory and source; make no changes.",\n        "when_to_use": "A direct question that memory or a quick read can answer.",\n        "reading_route": ["current-state.md", "AGENT_ORIENTATION.md"],\n        "tools": [READ],\n        "output": "A concise answer grounded in memory/source; no edits.",\n    },\n    {\n        "name": "analysis",\n        "role": "Read-only deep-dive: investigate and report, do not change.",\n        "when_to_use": "Understanding a system, tracing a behavior, scoping work.",\n        "reading_route": ["AGENT_ORIENTATION.md", "architecture.md", "ownership.md"],\n        "tools": [READ, RUN],\n        "output": "Findings (evidence + conclusion), not changes.",\n    },\n    {\n        "name": "debug",\n        "role": "Read, run, and make targeted edits to fix a known fault.",\n        "when_to_use": "A reproduced, localized fault with a clear blast radius.",\n        "reading_route": ["runtime_contracts.md", "current-state.md"],\n        "tools": [READ, RUN, EDIT],\n        "output": "A targeted fix for the known fault; no broad refactor.",\n    },\n    {\n        "name": "review",\n        "role": "Evaluate a diff against the contracts; comment, do not edit.",\n        "when_to_use": "Assessing a change someone else (or a prior stance) produced.",\n        "reading_route": ["architecture.md", "ownership.md", "runtime_contracts.md"],\n        "tools": [READ, COMMENT],\n        "output": "A verdict + comments against the contracts; no edits.",\n    },\n    {\n        "name": "plan",\n        "role": "Research + safe prototyping, then propose a plan for approval.",\n        "when_to_use": "A multi-step or architectural change worth designing first.",\n        "reading_route": ["AGENT_ORIENTATION.md", "current-state.md", "roadmap.md"],\n        "tools": [READ, RUN],\n        "output": "An approved plan (research + safe prototyping; no committed change).",\n    },\n]\n\n_BY_NAME = {s["name"]: s for s in STANCES}\n\n\ndef stance_names() -> list[str]:\n    """Return the available stance names, in declared order."""\n    return [s["name"] for s in STANCES]\n\n\ndef get_stance(name: str) -> dict | None:\n    """Return the stance definition for ``name`` (or None if unknown)."""\n    return _BY_NAME.get(name)\n\n\ndef action_allowed(name: str, action: str) -> bool:\n    """True if ``action`` is in ``name``\'s tool-scope (False for an unknown stance)."""\n    stance = _BY_NAME.get(name)\n    return stance is not None and action in stance["tools"]\n\n\ndef is_out_of_stance(name: str, action: str) -> bool:\n    """True if ``action`` falls *outside* a known stance\'s tool-scope.\n\n    The predicate a PreToolUse guard calls to warn on, e.g., an edit while the\n    active stance is ``review``. Returns False for an unknown stance (nothing to\n    enforce) so the guard fails **open** — it never blocks on a misconfigured name.\n    """\n    stance = _BY_NAME.get(name)\n    if stance is None:\n        return False\n    return action not in stance["tools"]\n\n\ndef stance_briefing(name: str) -> str:\n    """Return the orientation block injected for the active stance.\n\n    The reading-route + tool-scope + output contract, formatted for injection into\n    session orientation (alongside the user-style block and reflection buffer).\n    """\n    stance = _BY_NAME.get(name)\n    if stance is None:\n        choices = ", ".join(stance_names())\n        return f"Unknown stance {name!r} (choose from {choices})."\n    route = " -> ".join(stance["reading_route"])\n    tools = ", ".join(stance["tools"])\n    return (\n        f"Stance: {stance[\'name\']} — {stance[\'role\']}\\n"\n        f"  When: {stance[\'when_to_use\']}\\n"\n        f"  Read first: {route}\\n"\n        f"  In-scope actions: {tools}\\n"\n        f"  Output: {stance[\'output\']}"\n    )\n',
    'engine/skills/skills.py': '"""Skill sources + the skill/stance precedence model (plan section 3c).\n\nA *skill* is an invokable procedure emitted as a native ``.claude/skills/<name>/\nSKILL.md`` (YAML frontmatter for metadata-first loading + a readable body). Unlike\na stance (an ambient posture), a skill is invoked for a specific job and **declares\nthe capabilities it needs** — so a skill\'s declared capability **takes precedence\nover the ambient stance** (a ``session-close`` that declares it edits can write the\nsession log even while the active stance is ``review``). Stances stay advisory for\nanything a skill has not declared.\n\nLike the question bank and the stances, the set ships as a Python module — embeds\nin the stdlib-only bootstrap with no YAML parser, identical in ``src`` and ``dist``.\nBodies use ``${slot}`` placeholders filled from the interview at build time, so a\nskill is project-aware (e.g. ``quality-gate`` runs the project\'s own verify command).\n"""\n\nfrom __future__ import annotations\n\nfrom engine.stances.stances import COMMENT, EDIT, READ, RUN, action_allowed\n\n_SESSION_CLOSE_BODY = """\\\nClose ${project_name}\'s current session correctly.\n\n1. Session log — write `.sessions/<date>-<slug>.md`: what changed, one new idea\n   you genuinely believe in, and a one-line review of the previous session.\n2. Idea backlog — groom one idea forward (the ideas-README lifecycle).\n3. Verify — run the project\'s checks: `${verify_command}` and `bootstrap check`.\n4. Commit + push on the session branch; open the PR ready (not draft).\n5. Drive the PR to a terminal state — merge on green CI, or close with a reason.\n\nDeclared capabilities: edit (the log + docs), run (the checks + git)."""\n\n_QUALITY_GATE_BODY = """\\\nProve a change is good before pushing ${project_name}.\n\n1. Run `${verify_command}` — the project\'s full verification (tests + lint/types).\n2. Run `bootstrap check --strict` — doc + session-log hygiene.\n3. Report every failure with the exact command to reproduce it.\n4. Do NOT push on red — green here should mean green in CI.\n\nDeclared capabilities: run."""\n\n_REVIEW_BODY = """\\\nReview the current branch\'s diff against ${project_name}\'s binding contracts.\n\n1. Read the contracts first (architecture / ownership / runtime), then the diff.\n2. For each change check layer boundaries, mutation ownership, and the project\'s\n   invariants. Flag violations with file:line and the rule they break.\n3. Produce a verdict (approve / request-changes) + concrete fixes.\n4. Do not edit — comment only. (The `review` stance pairs with this skill.)\n\nDeclared capabilities: comment."""\n\n_REPO_HEALTH_BODY = """\\\nAudit ${project_name}\'s documentation + session-log hygiene.\n\n1. Run `bootstrap check` — badges, link resolution, doc reachability, and the\n   required session-log markers.\n2. Summarize the drift: orphaned docs, missing badges, incomplete logs.\n3. Fix the small ones (link the orphan, badge the doc); capture the rest as ideas.\n\nDeclared capabilities: run."""\n\n_DEEP_RESEARCH_BODY = """\\\nAnswer a multi-source factual question with a cited report.\n\n1. Decompose the question into sub-questions; search broadly (fan out).\n2. Fetch the strongest sources; cross-check claims adversarially; prefer\n   primary/official docs over memory.\n3. Flag uncertainty explicitly; never state a guess as fact.\n4. Synthesize a concise report with inline citations.\n\nDeclared capabilities: run."""\n\n_QUESTION_BODY = """\\\nAnswer a direct question about ${project_name} concisely.\n\n1. Read current-state + the one relevant doc or source file.\n2. Answer in a few sentences, grounded in what you read; cite the source.\n3. Make no changes. (The `question` stance pairs with this skill.)\n\nDeclared capabilities: read-only."""\n\n_ANALYSIS_BODY = """\\\nInvestigate a ${project_name} system and report findings, changing nothing.\n\n1. Read the binding contracts and trace the behavior across files.\n2. Produce evidence (file:line) + a conclusion; name the uncertainty.\n3. Do not edit. (The `analysis` stance pairs with this skill.)\n\nDeclared capabilities: read-only."""\n\n# Each skill declares the capabilities it needs *beyond* read (read is implicit).\n# The declared set is what overrides the ambient stance (the precedence rule).\nSKILLS: list[dict] = [\n    {\n        "name": "session-close",\n        "description": "End the session correctly — write the log, groom + add an "\n        "idea, verify, commit, push, drive the PR to a terminal state.",\n        "capabilities": [EDIT, RUN],\n        "body": _SESSION_CLOSE_BODY,\n    },\n    {\n        "name": "quality-gate",\n        "description": "Run the project\'s full verification before pushing and "\n        "report what must be fixed.",\n        "capabilities": [RUN],\n        "body": _QUALITY_GATE_BODY,\n    },\n    {\n        "name": "review",\n        "description": "Review the branch diff against the binding contracts; "\n        "comment with a verdict and fixes, no edits.",\n        "capabilities": [COMMENT],\n        "body": _REVIEW_BODY,\n    },\n    {\n        "name": "repo-health",\n        "description": "Audit doc + session-log hygiene (bootstrap check) and "\n        "summarize drift.",\n        "capabilities": [RUN],\n        "body": _REPO_HEALTH_BODY,\n    },\n    {\n        "name": "deep-research",\n        "description": "Fan out web research, adversarially verify sources, and "\n        "synthesize a cited report.",\n        "capabilities": [RUN],\n        "body": _DEEP_RESEARCH_BODY,\n    },\n    {\n        "name": "question",\n        "description": "Answer a direct question concisely from memory and source; "\n        "make no changes.",\n        "capabilities": [],\n        "body": _QUESTION_BODY,\n    },\n    {\n        "name": "analysis",\n        "description": "Read-only deep-dive: investigate and report findings "\n        "without changing anything.",\n        "capabilities": [],\n        "body": _ANALYSIS_BODY,\n    },\n]\n\n_SKILL_BY_NAME = {s["name"]: s for s in SKILLS}\n\n\ndef skill_names() -> list[str]:\n    """Return the available skill names, in declared order."""\n    return [s["name"] for s in SKILLS]\n\n\ndef get_skill(name: str) -> dict | None:\n    """Return the skill definition for ``name`` (or None if unknown)."""\n    return _SKILL_BY_NAME.get(name)\n\n\ndef skill_capabilities(name: str) -> list[str]:\n    """Return a skill\'s full capability set (declared + the implicit ``read``)."""\n    skill = _SKILL_BY_NAME.get(name)\n    if skill is None:\n        return []\n    return [READ, *skill["capabilities"]]\n\n\ndef skill_permits(name: str, action: str) -> bool:\n    """True if skill ``name`` declares (or implies) ``action``."""\n    return action in skill_capabilities(name)\n\n\ndef action_permitted(\n    stance_name: str,\n    action: str,\n    skill_name: str | None = None,\n) -> bool:\n    """Resolve whether ``action`` is permitted under a stance, optionally in a skill.\n\n    Precedence (plan section 3c): a skill\'s explicitly-declared capability **wins**\n    over the ambient stance — so an invoked skill can do what it declares even when\n    the stance forbids it. For anything the skill has not declared, the stance\'s\n    advisory tool-scope applies.\n    """\n    if skill_name is not None and skill_permits(skill_name, action):\n        return True\n    return action_allowed(stance_name, action)\n\n\ndef skill_frontmatter(skill: dict) -> str:\n    """Return the native ``SKILL.md`` YAML frontmatter (metadata-first loading)."""\n    return f\'---\\nname: {skill["name"]}\\ndescription: "{skill["description"]}"\\n---\'\n\n\ndef skill_relpath(skill: dict) -> str:\n    """Return the emit path for a skill, relative to the skills root."""\n    return f"skills/{skill[\'name\']}/SKILL.md"\n\n\ndef skill_document(skill: dict, body: str) -> str:\n    """Compose the full ``SKILL.md`` text from a skill + its (rendered) body."""\n    return f"{skill_frontmatter(skill)}\\n\\n# {skill[\'name\']}\\n\\n{body.rstrip()}\\n"\n',
    'engine/agents/agents.py': '"""Persona (sub-agent) sources + native emission (plan section 3c).\n\nA *persona* is a spawnable, read-only specialist (the third capability mechanism\nalongside stances and skills): the working agent delegates a focused task —\ndesign review, independent critique, deep exploration — to a fresh sub-agent\ncontext. The kit ships three generalized personas, each emitted as a native\n``.claude/agents/<name>.md`` (YAML frontmatter ``name`` / ``description`` /\n``tools`` + a system-prompt body).\n\nPersonas are **interview-populated**: their binding sources are filled from the\nproject\'s own contract slots (``${architecture_layers}``, ``${ownership_model}``,\n…) at build time — so a persona reviews against *this* project\'s rules, not\nsuperbot\'s. Like the skills, they ship as a Python module (not a subdir of\n``templates/``) so they embed in the stdlib-only bootstrap with no extra loader.\n\nPersonas are spawned specialists, so — unlike skills — they carry no stance\nprecedence; they are read-only by construction (their declared ``tools`` grant\nno write).\n"""\n\nfrom __future__ import annotations\n\n# Native read-only tool set for a spawned specialist (no write/edit/run).\n_READONLY_TOOLS = ["Read", "Grep", "Glob"]\n\n_ARCHITECT_BODY = """\\\nYou are ${project_name}\'s architecture specialist — read-only. Answer design\nquestions and review proposed changes for layer/ownership compliance BEFORE they\nare coded.\n\nBinding model (this project\'s contracts):\n- Layers & import rules: ${architecture_layers}\n- Ownership (who owns each write path): ${ownership_model}\n- Mutation seam (how writes are gated): ${mutation_seam}\n\nMethod: read the relevant contracts + source, then judge a proposed change\nagainst them. Flag every layer-boundary or ownership violation with file:line and\nthe rule it breaks; propose the compliant placement. You advise — you do not edit."""\n\n_REVIEWER_BODY = """\\\nYou are ${project_name}\'s independent reviewer — a second pair of eyes that does\nNOT share the author\'s assumptions. Evaluate a diff against the binding contracts\nand surface the risks the author may have anchored past.\n\nReview against: ${architecture_layers} · ${ownership_model} · the project\'s\nverification (`${verify_command}`).\n\nAnti-anchoring rule: judge the change on its evidence, not the author\'s stated\nconfidence. Give a verdict (approve / request-changes) + the specific risks and\nfixes. Read-only — you comment, you do not edit. (Wire this persona to the\nindependent-review seam: a *different* model reviewing breaks the monoculture.)"""\n\n_RESEARCHER_BODY = """\\\nYou are ${project_name}\'s researcher — read-only deep exploration. Map unfamiliar\ncode or trace a behavior across the system and report findings; change nothing.\n\nStart from: ${doc_roots} (where durable documentation lives) and the read-path\ndocs, then follow the source.\n\nOutput: evidence (file:line) + a clear conclusion, with the uncertainty named.\nPrefer reading source over assuming. You produce understanding, not edits."""\n\nAGENTS: list[dict] = [\n    {\n        "name": "architect",\n        "description": "Read-only design/layer specialist — answer architecture "\n        "questions and flag layer/ownership violations before they are coded.",\n        "tools": list(_READONLY_TOOLS),\n        "body": _ARCHITECT_BODY,\n    },\n    {\n        "name": "reviewer",\n        "description": "Independent critic — evaluate a diff against the contracts "\n        "without the author\'s assumptions; verdict + risks, no edits.",\n        "tools": list(_READONLY_TOOLS),\n        "body": _REVIEWER_BODY,\n    },\n    {\n        "name": "researcher",\n        "description": "Read-only deep exploration — map unfamiliar code / trace a "\n        "behavior and report evidence-backed findings; change nothing.",\n        "tools": list(_READONLY_TOOLS),\n        "body": _RESEARCHER_BODY,\n    },\n]\n\n_AGENT_BY_NAME = {a["name"]: a for a in AGENTS}\n\n\ndef agent_names() -> list[str]:\n    """Return the available persona names, in declared order."""\n    return [a["name"] for a in AGENTS]\n\n\ndef get_agent(name: str) -> dict | None:\n    """Return the persona definition for ``name`` (or None if unknown)."""\n    return _AGENT_BY_NAME.get(name)\n\n\ndef agent_frontmatter(agent: dict) -> str:\n    """Return the native ``.claude/agents`` YAML frontmatter (name/description/tools)."""\n    tools = ", ".join(agent["tools"])\n    return (\n        f"---\\nname: {agent[\'name\']}\\n"\n        f\'description: "{agent["description"]}"\\n\'\n        f"tools: {tools}\\n---"\n    )\n\n\ndef agent_relpath(agent: dict) -> str:\n    """Return the emit path for a persona, relative to the agents root."""\n    return f"agents/{agent[\'name\']}.md"\n\n\ndef agent_document(agent: dict, body: str) -> str:\n    """Compose the full agent ``.md`` text from a persona + its (rendered) body."""\n    return f"{agent_frontmatter(agent)}\\n\\n{body.rstrip()}\\n"\n',
    'engine/hooks/stance_guard.py': '"""PreToolUse stance guard — makes the stance layer enforced, not just advisory.\n\nClaude Code calls a PreToolUse hook before each tool runs, passing the tool name\nin a JSON payload on stdin. This maps the tool to a stance action category\n(read / run / edit / comment) and, if that action is outside the active stance\'s\ntool-scope, produces an advisory warning — the agent stays free to proceed\n(stances are advisory by default, plan section 3b). The bootstrap\n``hook pretooluse`` command is the runtime entry point; ``settings_snippet``\ngenerates the ``.claude/settings.json`` wiring a host installs.\n\nEverything here **fails open**: an unknown tool, an unknown stance, or a\nmalformed payload yields no warning — the guard never gets in the way when it is\nunsure.\n"""\n\nfrom __future__ import annotations\n\nimport json\n\nfrom engine.stances.stances import EDIT, READ, RUN, is_out_of_stance\n\n# Claude Code tool name -> the stance action category it performs. Tools not\n# listed (Task, the slash-command tools, …) carry no stance opinion (fail open).\nTOOL_ACTIONS: dict[str, str] = {\n    "Read": READ,\n    "Grep": READ,\n    "Glob": READ,\n    "NotebookRead": READ,\n    "Edit": EDIT,\n    "Write": EDIT,\n    "NotebookEdit": EDIT,\n    "Bash": RUN,\n    "WebFetch": RUN,\n    "WebSearch": RUN,\n}\n\n\ndef tool_to_action(tool_name: str) -> str | None:\n    """Return the stance action category a Claude Code tool performs (or None)."""\n    return TOOL_ACTIONS.get(tool_name)\n\n\ndef tool_from_payload(raw: str) -> str:\n    """Extract the tool name from a PreToolUse stdin payload (``""`` if absent)."""\n    try:\n        payload = json.loads(raw) if raw.strip() else {}\n    except json.JSONDecodeError:\n        return ""\n    name = payload.get("tool_name", "") if isinstance(payload, dict) else ""\n    return name if isinstance(name, str) else ""\n\n\ndef evaluate_tool(stance: str, tool_name: str) -> str | None:\n    """Return an out-of-stance warning for ``tool_name`` under ``stance``, or None.\n\n    ``None`` means no objection — the tool carries no stance opinion, or the\n    action is within the stance\'s tool-scope. Fails open: an unknown stance or\n    tool never warns.\n    """\n    action = tool_to_action(tool_name)\n    if action is None or not is_out_of_stance(stance, action):\n        return None\n    return (\n        f"out-of-stance: {tool_name} ({action}) while stance is \'{stance}\'. "\n        "Re-check the task, or switch stance (`bootstrap stance <name>`). "\n        "(advisory — not blocked)"\n    )\n\n\ndef settings_snippet(command: str) -> str:\n    """Return a ``.claude/settings.json`` PreToolUse wiring snippet (JSON text).\n\n    ``command`` is the shell command Claude Code runs before each tool (e.g.\n    ``python3 bootstrap.py hook pretooluse``). The host merges the returned\n    ``hooks.PreToolUse`` block into their ``.claude/settings.json``.\n    """\n    snippet = {\n        "hooks": {\n            "PreToolUse": [\n                {\n                    "matcher": "*",\n                    "hooks": [{"type": "command", "command": command}],\n                },\n            ],\n        },\n    }\n    return json.dumps(snippet, indent=2) + "\\n"\n',
    'engine/hooks/session_start.py': '"""SessionStart orientation composer (plan section 5.B, Lane B7).\n\nThe nervous system\'s *injection* point: when Claude Code starts a session, the\n``bootstrap hook sessionstart`` entry point prints the text this module\ncomposes, so the agent boots already knowing the project\'s mode, stance,\nlearned lessons, fired triggers, and pending questions. The composition is\n**mode-aware** — ``orientation_depth`` (observe → minimal, guided → standard,\nactive → full) decides which sections render and how hard they cap.\n\nSection order (the plan\'s fixed sequence): status header → stance briefing →\nuser-style block → learned lessons (AFTER user-style) → trigger block →\nguided-practices line → economy-gauges advisory (over-cap only) → pending\nquestions (quota view) → observe-mode workflow proposal.\n\nEvery section is defensive: a failure inside one section drops that section,\nnever the whole composition — orientation must never crash a session. This is\nthe one place broad ``except Exception`` is correct by design (fail open, like\nthe stance guard).\n"""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nfrom typing import Any\n\nfrom engine.economy.engine import economy_gauges\nfrom engine.interview.interview import pending_questions, session_questions\nfrom engine.lib.config import Config\nfrom engine.lib.modes import (\n    active_practices,\n    orientation_depth,\n    triggers_mandate,\n    workflow_proposal_due,\n)\nfrom engine.loop.reflections import (\n    REFLECTIONS_FILENAME,\n    active_lessons,\n    lessons_block,\n    load_reflections,\n)\nfrom engine.loop.triggers import check_triggers, mandatory_questions, trigger_block\nfrom engine.stances.stances import stance_briefing\n\n# Depth "standard" caps the learned-lessons section at this many entries.\n_ORI_STANDARD_LESSON_CAP = 3\n# Depth "minimal" (observe) renders only these section numbers: the status\n# header (1), the trigger block as an advisory (5), and the workflow proposal\n# (9) — observe imposes nothing else.\n_ORI_MINIMAL_SECTIONS = frozenset({1, 5, 9})\n\n\ndef _ori_status_header(state: dict[str, Any], config: Config) -> str:\n    """Render section 1 — the compact status header line block."""\n    project = str(state.get("project_id") or config.project_id)\n    return (\n        f"# Session orientation — {project}\\n"\n        f"mode: {state.get(\'mode\', \'?\')} · stage: {state.get(\'stage\', \'?\')} · "\n        f"stance: {state.get(\'stance\', \'?\')} · "\n        f"session: {int(state.get(\'session_count\', 0))}"\n    )\n\n\ndef _ori_stance(state: dict[str, Any]) -> str:\n    """Render section 2 — the active stance briefing (\'\' when no stance set)."""\n    stance = state.get("stance")\n    if not stance:\n        return ""\n    return stance_briefing(str(stance))\n\n\ndef _ori_user_style(state: dict[str, Any]) -> str:\n    """Render section 3 — the owner_profile user-style block (\'\' when unfilled)."""\n    entry = state.get("slot_values", {}).get("owner_profile")\n    value = entry.get("value") if isinstance(entry, dict) else entry\n    text = str(value).strip() if value else ""\n    if not text:\n        return ""\n    return f"## How the owner works:\\n\\n> {text}"\n\n\ndef _ori_lessons(root: Path, config: Config, depth: str) -> str:\n    """Render section 4 — learned lessons (standard caps at 3, full uncapped)."""\n    entries = load_reflections(root / config.state_dir / REFLECTIONS_FILENAME)\n    cap = _ORI_STANDARD_LESSON_CAP if depth == "standard" else len(entries)\n    return lessons_block(active_lessons(entries, cap))\n\n\ndef _ori_triggers(root: Path, config: Config, state: dict[str, Any]) -> str:\n    """Render section 5 — the trigger block (mandate flag per the mode policy)."""\n    triggers = check_triggers(root, config, state)\n    questions = mandatory_questions(triggers)\n    return trigger_block(triggers, questions, mandate=triggers_mandate(state))\n\n\ndef _ori_practices(state: dict[str, Any], config: Config) -> str:\n    """Render section 6 — the one-line guided-practices block (\'\' when empty)."""\n    practices = active_practices(state, dict(config.cadence or {}))\n    if not practices:\n        return ""\n    return "Active practices: " + ", ".join(practices)\n\n\ndef _ori_gauges(root: Path, config: Config) -> str:\n    """Render section 7 — economy advisory listing ONLY over-cap gauges."""\n    over = [g for g in economy_gauges(root, config) if g.get("over")]\n    if not over:\n        return ""\n    lines = ["## Economy advisory — over-cap gauges", ""]\n    lines += [\n        f"- {g[\'name\']} ({g[\'kind\']}): {g[\'value\']} words/items over cap {g[\'cap\']}"\n        for g in over\n    ]\n    return "\\n".join(lines)\n\n\ndef _ori_questions(state: dict[str, Any]) -> str:\n    """Render section 8 — the quota-capped ask list with a \'+N more\' suffix."""\n    asks = session_questions(state)\n    if not asks:\n        return ""\n    lines = ["## Questions this session", ""]\n    lines += [\n        f"- {q[\'id\']} ({q.get(\'priority\', \'normal\')}): {q[\'prompt\']}" for q in asks\n    ]\n    extra = len(pending_questions(state)) - len(asks)\n    if extra > 0:\n        lines += ["", f"(+{extra} more later)"]\n    return "\\n".join(lines)\n\n\ndef _ori_proposal(state: dict[str, Any]) -> str:\n    """Render section 9 — observe mode\'s workflow proposal when it is due."""\n    if state.get("mode") != "observe" or not workflow_proposal_due(state):\n        return ""\n    return (\n        "## Proposed workflow\\n\\n"\n        "Observe mode has watched enough sessions to propose a tailored "\n        "workflow. If the pacing looks right, switch mode to adopt it: "\n        "`bootstrap mode guided` (one practice at a time) or "\n        "`bootstrap mode active` (the full workflow now). Observe imposes "\n        "nothing until you do."\n    )\n\n\ndef _ori_safe(build: Any) -> str:\n    """Run one section builder, returning \'\' on any failure (fail open).\n\n    The one place broad ``except Exception`` is correct by design: a bad state\n    document or an unreadable file drops that single section — orientation\n    must never crash a session.\n    """\n    try:\n        return str(build()).strip()\n    except Exception:  # fail open — one bad section never breaks the whole\n        return ""\n\n\ndef compose_orientation(root: Path, config: Config, backend: Any) -> str:\n    """Compose the mode-aware SessionStart orientation injection.\n\n    Assembles the nine plan sections in fixed order, gated by\n    ``orientation_depth``: ``minimal`` renders only the status header, the\n    trigger advisory, and the observe-mode proposal; ``standard`` renders all\n    sections but caps lessons at 3; ``full`` renders everything uncapped.\n    Every section builder runs inside its own guard — a bad state document or\n    an unreadable file drops that one section, never the whole composition\n    (orientation must never crash a session).\n    """\n    try:\n        state = dict(backend.data)\n    except Exception:  # fail open — orientation never crashes a session\n        state = {}\n    try:\n        depth = orientation_depth(state)\n    except Exception:  # fail open — fall back to the default depth\n        depth = "standard"\n    builders = (\n        (1, lambda: _ori_status_header(state, config)),\n        (2, lambda: _ori_stance(state)),\n        (3, lambda: _ori_user_style(state)),\n        (4, lambda: _ori_lessons(root, config, depth)),\n        (5, lambda: _ori_triggers(root, config, state)),\n        (6, lambda: _ori_practices(state, config)),\n        (7, lambda: _ori_gauges(root, config)),\n        (8, lambda: _ori_questions(state)),\n        (9, lambda: _ori_proposal(state)),\n    )\n    sections: list[str] = []\n    for number, build in builders:\n        if depth == "minimal" and number not in _ORI_MINIMAL_SECTIONS:\n            continue\n        text = _ori_safe(build)\n        if text:\n            sections.append(text)\n    if not sections:\n        return ""\n    return "\\n\\n".join(sections) + "\\n"\n',
    'engine/hooks/post_edit.py': '"""PostToolUse edit advisor (plan section 5.B, Lane B7).\n\nRuns after every Edit/Write tool call: the CLI\'s ``hook postedit`` entry point\nextracts the edited file path from the PostToolUse stdin payload and asks\n``evaluate_edit`` whether the edit deserves an advisory —\n\n- **generated artifact** — the file lives under ``<state_dir>/rendered`` or\n  ``<state_dir>/contextpacks``, or its head carries the ``NOT SOURCE OF\n  TRUTH`` marker: edit the template/index and re-render, not the artifact.\n- **missing Status badge** — a ``*.md`` under the docs root without a\n  ``> **Status:** `<token>``` badge in its first 12 lines (the same badge scan\n  ``check_docs`` runs, via the shared ``badge_token`` reader).\n\nLike every hook evaluator this **fails open**: absolute or root-relative paths\nboth resolve, and an unreadable / missing file yields ``None`` — the advisor\nnever gets in the way when it is unsure.\n"""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\n\nfrom engine.checks.check_docs import badge_token\nfrom engine.lib.config import Config\n\n# The HTML-comment form only: planted (hand-editable) docs carry the bare\n# phrase "NOT SOURCE OF TRUTH" in their badge prose, and the guard must not\n# warn on every legitimate edit of a planted binding doc — only generated\n# artifacts (contextpacks etc.) open with this comment marker.\n_PE_MARKER = "<!-- NOT SOURCE OF TRUTH"\n_PE_HEAD_LINES = 12\n# <state_dir> subdirectories that hold build artifacts, never source.\n_PE_GENERATED_DIRS = ("rendered", "contextpacks")\n_PE_GENERATED_MSG = (\n    "generated artifact — edit the template/index and re-render, not this file"\n)\n_PE_BADGE_MSG = (\n    "missing Status badge — add `> **Status:** `<token>`` to its first 12 lines"\n)\n\n\ndef _pe_resolve(root: Path, file_path: str) -> tuple[Path, Path | None]:\n    """Return ``(absolute path, root-relative path or None)`` for an edit path.\n\n    Accepts absolute and root-relative inputs; the relative half is ``None``\n    when the file lives outside ``root`` (nothing to classify against config\n    paths there).\n    """\n    path = Path(file_path)\n    if not path.is_absolute():\n        path = root / path\n    try:\n        rel = path.resolve().relative_to(root.resolve())\n    except (OSError, ValueError):\n        rel = None\n    return path, rel\n\n\ndef _pe_head(path: Path) -> str:\n    """Return the file\'s first 12 lines (\'\' when unreadable — fail open)."""\n    try:\n        lines = path.read_text(encoding="utf-8").splitlines()\n    except (OSError, UnicodeDecodeError):\n        return ""\n    return "\\n".join(lines[:_PE_HEAD_LINES])\n\n\ndef _pe_is_generated(config: Config, rel: Path | None, head: str) -> bool:\n    """True when the edited file is a build artifact (by path or by marker)."""\n    if _PE_MARKER in head:\n        return True\n    if rel is None:\n        return False\n    state_dir = Path(config.state_dir)\n    return any(rel.is_relative_to(state_dir / sub) for sub in _PE_GENERATED_DIRS)\n\n\ndef evaluate_edit(root: Path, config: Config, file_path: str) -> str | None:\n    """Return the advisory warning for one edited file, or None.\n\n    Warns on a generated artifact (path under ``<state_dir>/rendered`` /\n    ``<state_dir>/contextpacks``, or the generated-artifact HTML-comment marker)\n    and on a docs-root ``*.md`` lacking a Status badge. Tolerant of absolute\n    or root-relative ``file_path`` and of unreadable / missing files (None).\n    """\n    try:\n        path, rel = _pe_resolve(root, file_path)\n        if not path.is_file():\n            return None\n        name = rel.as_posix() if rel is not None else path.as_posix()\n        if _pe_is_generated(config, rel, _pe_head(path)):\n            return f"{name}: {_PE_GENERATED_MSG}"\n        if (\n            rel is not None\n            and path.suffix == ".md"\n            and rel.is_relative_to(Path(config.docs_root))\n            and badge_token(path) is None\n        ):\n            return f"{name}: {_PE_BADGE_MSG}"\n        return None\n    except Exception:  # fail open — the advisor never blocks an edit\n        return None\n',
    'engine/hooks/stop_check.py': '"""Stop-hook session-close advisor (plan section 5.B, Lane B7).\n\nRuns when a Claude Code session stops: the CLI\'s ``hook stopcheck`` entry\npoint prints the advisory lines ``evaluate_stop`` returns, reminding the agent\nwhat the session ritual still owes —\n\n- the session log is missing, or exists but lacks required markers\n  (``latest_session_log`` + ``check_log`` with ``config.session_markers``);\n- escalated blocking questions are still open (``state["open_questions"]``);\n- the compaction cadence window has elapsed (``compaction_due``);\n- the reflection buffer has not been mined today\n  (``reflection_buffer.last_mined`` vs today\'s ISO date).\n\nReturns ``[]`` when all clean. Advisory only, and it **fails open**: every\ncheck runs inside its own guard, so a bad state document or an unreadable log\ndrops that one advisory rather than crashing the stop hook.\n"""\n\nfrom __future__ import annotations\n\nfrom datetime import date\nfrom pathlib import Path\nfrom typing import Any\n\nfrom engine.checks.check_session_log import check_log, latest_session_log\nfrom engine.lib.config import Config\nfrom engine.loop.maintenance import compaction_due\n\n_STOP_UNMINED_MSG = "reflections unmined this session — run bootstrap reflect --mine"\n\n\ndef _stop_safe(check: Any) -> list[str]:\n    """Run one advisory check, returning [] on any failure (fail open).\n\n    Each check is guarded on its own so one bad input never suppresses the\n    other advisories — the stop hook is advisory by contract.\n    """\n    try:\n        return list(check())\n    except Exception:  # fail open — one bad check drops only itself\n        return []\n\n\ndef _stop_state(backend: Any) -> dict[str, Any]:\n    """Return the state document ({} when the backend is unusable — fail open)."""\n    try:\n        return dict(backend.data)\n    except Exception:  # fail open — a broken backend yields no state advisories\n        return {}\n\n\ndef _stop_log(root: Path, config: Config) -> list[str]:\n    """Advise when the session log is missing or lacks required markers."""\n    log = latest_session_log(root / config.sessions_dir)\n    if log is None:\n        return [\n            f"no session log found under {config.sessions_dir}/ — "\n            "write one before ending the session",\n        ]\n    missing = check_log(log, config.session_markers)\n    if missing:\n        return [f"session log {log.name} is missing: {\', \'.join(missing)}"]\n    return []\n\n\ndef _stop_questions(state: dict[str, Any]) -> list[str]:\n    """Advise when escalated blocking questions are still open."""\n    open_questions = [str(q) for q in state.get("open_questions", [])]\n    if not open_questions:\n        return []\n    listed = ", ".join(open_questions)\n    return [f"{len(open_questions)} blocking question(s) open: {listed}"]\n\n\ndef _stop_compaction(state: dict[str, Any], config: Config) -> list[str]:\n    """Advise when the compaction cadence window has elapsed."""\n    if compaction_due(state, dict(config.cadence or {})):\n        return ["compaction due — write the State Delta snapshot (bootstrap maintain)"]\n    return []\n\n\ndef _stop_reflections(state: dict[str, Any]) -> list[str]:\n    """Advise when the reflection buffer has not been mined today."""\n    buffer = state.get("reflection_buffer")\n    last_mined = buffer.get("last_mined") if isinstance(buffer, dict) else None\n    if last_mined == date.today().isoformat():\n        return []\n    return [_STOP_UNMINED_MSG]\n\n\ndef evaluate_stop(root: Path, config: Config, backend: Any) -> list[str]:\n    """Return the session-close advisory lines ([] when all clean).\n\n    Four checks in fixed order: session log, open blocking questions,\n    compaction cadence, reflection mining. Each runs inside its own guard so\n    one failing check never suppresses the others — the stop hook is advisory\n    and fails open by contract.\n    """\n    state = _stop_state(backend)\n    checks = (\n        lambda: _stop_log(root, config),\n        lambda: _stop_questions(state),\n        lambda: _stop_compaction(state, config),\n        lambda: _stop_reflections(state),\n    )\n    advisories: list[str] = []\n    for check in checks:\n        advisories.extend(_stop_safe(check))\n    return advisories\n',
    'engine/hooks/settings.py': '"""Hook settings template + customization contract (plan section 5.B, Lane B7).\n\nThe staging half of the hook layer (HOOK-2): ``full_settings_template`` emits\nthe complete ``.claude`` ``settings.template.json`` wiring all four hook\nevents — PreToolUse (stance guard), SessionStart (orientation), PostToolUse\n(edit advisor), Stop (session-close advisor) — each to\n``<interpreter> bootstrap.py hook <event>``, the same command shape the CLI\'s\n``_hook_command`` builds. ``hooks_fill_table`` emits the markdown\ncustomization contract a host reads before merging: which config fields must\nmatch their repo, and the standing rule that the kit *stages* hook settings —\nit never writes a live ``.claude/`` tree itself.\n"""\n\nfrom __future__ import annotations\n\nimport json\n\nfrom engine.lib.config import Config\n\n# (settings.json event key, bootstrap hook event, tool matcher or None).\n_SET_EVENTS: tuple[tuple[str, str, str | None], ...] = (\n    ("PreToolUse", "pretooluse", "*"),\n    ("SessionStart", "sessionstart", None),\n    ("PostToolUse", "postedit", "Edit|Write|NotebookEdit"),\n    ("Stop", "stopcheck", None),\n)\n\n_SET_FILL_ROWS: tuple[tuple[str, str], ...] = (\n    (\n        "`interpreter`",\n        "the Python that runs the kit itself — every hook command below "\n        "starts with it; set it to an interpreter available on your PATH",\n    ),\n    (\n        "`interpreter_for_checks`",\n        "your *project\'s* verification interpreter (the version your CI "\n        "pins, e.g. `python3.10`) — kept separate from `interpreter` on "\n        "purpose",\n    ),\n    (\n        "`bootstrap.py` path",\n        "each hook command assumes `bootstrap.py` sits at your repo root; "\n        "rewrite the path inside every command if it lives elsewhere",\n    ),\n    (\n        "`state_dir`",\n        "where kit state + staged artifacts live (default `.substrate`) — "\n        "the post-edit generated-artifact warning keys off it",\n    ),\n    (\n        "`docs_root`",\n        "your documentation root (default `docs`) — the post-edit badge "\n        "warning and the SessionStart trigger scan key off it",\n    ),\n    (\n        "`sessions_dir`",\n        "where per-session logs live (default `.sessions`) — the Stop-hook "\n        "session-log advisory keys off it",\n    ),\n    (\n        "cadence knobs",\n        "`cadence.*` in `substrate.config.json` (`compaction_sessions`, "\n        "`reconciliation_sessions`, `staleness_days`, "\n        "`critical_slot_grace_sessions`, `guided_practice_sessions`) drive "\n        "the SessionStart triggers and Stop-hook advisories",\n    ),\n)\n\n\ndef _set_command(config: Config, event: str, bootstrap_path: str) -> str:\n    """Return the shell command Claude Code runs for one hook event."""\n    return f"{config.interpreter} {bootstrap_path} hook {event}"\n\n\ndef full_settings_template(config: Config, bootstrap_path: str = "bootstrap.py") -> str:\n    """Return the complete ``settings.template.json`` wiring all four hooks.\n\n    JSON text (2-space indent) a host merges into ``.claude/settings.json``:\n    PreToolUse (matcher ``*``), SessionStart, PostToolUse (matcher\n    ``Edit|Write|NotebookEdit``), and Stop, each running\n    ``<interpreter> <bootstrap_path> hook <event>``. Matcher-less events omit\n    the ``matcher`` key entirely (they apply unconditionally).\n    ``bootstrap_path`` is the path the hook commands reference — adopt passes\n    the vendored/root-resolved location so staged hooks resolve inside the\n    target repo (the Phase-2.5 staged-hook failure cause).\n    """\n    hooks: dict[str, list[dict]] = {}\n    for settings_event, cli_event, matcher in _SET_EVENTS:\n        entry: dict = {}\n        if matcher is not None:\n            entry["matcher"] = matcher\n        entry["hooks"] = [\n            {\n                "type": "command",\n                "command": _set_command(config, cli_event, bootstrap_path),\n            },\n        ]\n        hooks[settings_event] = [entry]\n    return json.dumps({"hooks": hooks}, indent=2) + "\\n"\n\n\ndef hooks_fill_table() -> str:\n    """Return the markdown customization contract for the settings template.\n\n    One ``field | what must match your repo`` row per knob a host must verify\n    before installing, plus the install instruction: merge the staged template\n    into ``.claude/settings.json`` yourself — the kit stages hook settings, it\n    never writes a live ``.claude/`` tree.\n    """\n    lines = [\n        "# Hook settings — customization contract",\n        "",\n        "The kit **stages** `settings.template.json`; it never writes your",\n        "`.claude/` tree. Install by merging the template\'s `hooks` block into",\n        "your repo\'s `.claude/settings.json` yourself, after checking every",\n        "row below against your repo.",\n        "",\n        "| field | what must match your repo |",\n        "| --- | --- |",\n    ]\n    lines += [f"| {field} | {note} |" for field, note in _SET_FILL_ROWS]\n    lines += [\n        "",\n        "All four hooks are advisory and fail open: they always exit 0 and",\n        "never block a tool, an edit, or a session stop.",\n    ]\n    return "\\n".join(lines) + "\\n"\n',
    'engine/render.py': '"""Render the project\'s content docs from templates + filled interview slots.\n\nTemplates use ``${slot_name}`` placeholders (``string.Template``). A slot the\ninterview has filled substitutes in; an unfilled slot is left as ``${slot_name}``\nand reported — so a half-onboarded project\'s gaps stay visible rather than going\nsilently blank. Templates ship embedded in the bootstrap (the generated\n``_TEMPLATES`` dict) and, in the source/pip layouts, under\n``engine/templates/`` (inside the package so a wheel ships them).\n"""\n\nfrom __future__ import annotations\n\nimport re\nfrom pathlib import Path\nfrom typing import Any\n\n_PLACEHOLDER_RE = re.compile(r"\\$\\{([a-zA-Z_][a-zA-Z0-9_]*)\\}")\n\n\ndef find_placeholders(text: str) -> set[str]:\n    """Return the set of ``${name}`` placeholders remaining in ``text``."""\n    return set(_PLACEHOLDER_RE.findall(text))\n\n\ndef render(text: str, context: dict[str, str]) -> str:\n    """Substitute ``${slot}`` placeholders from ``context`` (unfilled left as-is).\n\n    Only the braced ``${name}`` form is a placeholder — the *same* form\n    ``find_placeholders`` reports, so render and the "unfilled slots stay\n    visible" safety net can never disagree. Deliberately NOT\n    ``string.Template.safe_substitute``: that also collapses ``$$`` → ``$`` and\n    substitutes unbraced ``$word``, silently mangling host-authored ``$``\n    content (shell ``$$``/``$1``, ``$5`` prices, ``$$LaTeX$$``) on the routine\n    ``render --live`` in-place fill — and turning an escaped ``$${VERSION}``\n    into a live-looking ``${VERSION}`` that then reports as an unfilled slot.\n    A regex sub over the braced form leaves every other ``$`` byte untouched.\n    """\n    return _PLACEHOLDER_RE.sub(\n        lambda m: context[m.group(1)] if m.group(1) in context else m.group(0),\n        text,\n    )\n\n\ndef build_context(state: dict[str, Any]) -> dict[str, str]:\n    """Build the substitution context from a state document\'s filled slots."""\n    values = state.get("slot_values", {})\n    return {slot: str(entry.get("value", "")) for slot, entry in values.items()}\n\n\ndef load_templates() -> dict[str, str]:\n    """Return ``{filename: text}`` for every template (embedded or packaged).\n\n    The single-file bootstrap embeds them as ``_TEMPLATES``; the source/pip\n    layouts read ``engine/templates/`` (INSIDE the package, so a wheel ships\n    them — they once lived a level up and a pip install silently had none).\n    An empty template set is a hard error, never a silent no-op render.\n    """\n    embedded = globals().get("_TEMPLATES")\n    if embedded is not None:\n        return dict(embedded)\n    root = Path(__file__).resolve().parent / "templates"\n    templates = {\n        p.name: p.read_text(encoding="utf-8") for p in sorted(root.glob("*.tmpl"))\n    }\n    if not templates:\n        msg = f"no templates found at {root} — broken install"\n        raise FileNotFoundError(msg)\n    return templates\n',
    'engine/derive.py': '"""Adopt-time slot derivation — "adopt renders what it knows" (the Phase-2.5 G2 fix).\n\nThe cold-start A/B (``phase-2.5-cold-start-report-2026-07-07.md``) failed\nbecause ``adopt`` planted raw ``${...}`` templates: a task-focused cold\nsession paid the reading cost and (correctly) ignored them. The fix has two\nhalves; this module is the first — derive every slot the kit can know\n**deterministically** from the target tree (project name, primary language,\nverify command, docs root) and record each as a *provisional* interview\nanswer before the adopt render, so the planted docs open readable instead of\ninert. Provisional answers never count toward graduation until confirmed\n(the interview contract is unchanged) and ``bootstrap ask`` still asks —\nderivation seeds the interview, it does not replace it. Detection is\nfile-presence based, never a guess: a slot with no confident signal stays\nunfilled (and the adopt banner marks it — the second half, in ``adopt.py``).\nPure stdlib.\n"""\n\nfrom __future__ import annotations\n\nimport re\nfrom pathlib import Path\nfrom typing import Any\n\nfrom engine.interview.interview import record_answer\nfrom engine.interview.question_bank import QUESTIONS\n\n_REQUIRES_PYTHON_RE = re.compile(r\'requires-python\\s*=\\s*"([^"]+)"\')\n_MAKEFILE_TEST_RE = re.compile(r"^test\\s*:", re.MULTILINE)\n\n# Marker files that make a tree confidently Python before any other check.\n_PYTHON_MARKERS = ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")\n\n\ndef _read_if_exists(path: Path) -> str:\n    """Return the file\'s text, or empty for a missing/unreadable file."""\n    try:\n        return path.read_text(encoding="utf-8")\n    except (OSError, UnicodeDecodeError):\n        return ""\n\n\ndef detect_language(root: Path) -> str | None:\n    """Return the project\'s primary language from marker files, or None.\n\n    Python wins ties deliberately (the kit\'s own tooling is Python-first and a\n    mixed tree with a ``pyproject.toml`` is Python-led for verification\n    purposes). The version qualifier comes only from an explicit\n    ``requires-python`` — never inferred.\n    """\n    if any((root / marker).is_file() for marker in _PYTHON_MARKERS):\n        match = _REQUIRES_PYTHON_RE.search(_read_if_exists(root / "pyproject.toml"))\n        return f"Python {match.group(1)}" if match else "Python"\n    if (root / "package.json").is_file():\n        return "TypeScript" if (root / "tsconfig.json").is_file() else "JavaScript"\n    if (root / "Cargo.toml").is_file():\n        return "Rust"\n    if (root / "go.mod").is_file():\n        return "Go"\n    return None\n\n\ndef _python_has_tests(root: Path) -> bool:\n    """True when the tree carries a recognizable pytest surface."""\n    if (root / "tests").is_dir() or (root / "pytest.ini").is_file():\n        return True\n    pyproject = _read_if_exists(root / "pyproject.toml")\n    return "[tool.pytest" in pyproject\n\n\ndef _npm_has_real_test_script(root: Path) -> bool:\n    """True when package.json declares a test script that isn\'t npm\'s stub."""\n    text = _read_if_exists(root / "package.json")\n    if \'"test"\' not in text:\n        return False\n    return "no test specified" not in text\n\n\ndef detect_verify_command(root: Path) -> str | None:\n    """Return the one-command verification entry point, or None.\n\n    Order mirrors :func:`detect_language`; each candidate requires a positive\n    marker (a test tree, a real test script, a ``test:`` target) so the\n    derived command is runnable, not aspirational.\n    """\n    if any((root / marker).is_file() for marker in _PYTHON_MARKERS):\n        if _python_has_tests(root):\n            return "python3 -m pytest"\n        return None\n    if (root / "package.json").is_file() and _npm_has_real_test_script(root):\n        return "npm test"\n    if (root / "Cargo.toml").is_file():\n        return "cargo test"\n    if (root / "go.mod").is_file():\n        return "go test ./..."\n    if _MAKEFILE_TEST_RE.search(_read_if_exists(root / "Makefile")):\n        return "make test"\n    return None\n\n\ndef derive_slots(root: Path, docs_root: str) -> dict[str, str]:\n    """Return every slot value derivable from the target tree.\n\n    Keys match the question bank\'s slot names. Only confidently-derived\n    entries appear — absent key means "leave the slot to the interview".\n    """\n    derived: dict[str, str] = {"project_name": root.resolve().name}\n    language = detect_language(root)\n    if language:\n        derived["primary_language"] = language\n    verify = detect_verify_command(root)\n    if verify:\n        derived["verify_command"] = verify\n    if docs_root:\n        derived["doc_roots"] = docs_root\n    return derived\n\n\ndef record_derived_slots(backend: Any, derived: dict[str, str]) -> list[str]:\n    """Record derived values as provisional answers for still-empty slots.\n\n    Existing answers of any status (filled / partial / provisional) are never\n    overwritten — derivation only seeds blanks. Returns report lines in the\n    adopt-report format.\n    """\n    by_slot = {question["slot"]: question for question in QUESTIONS}\n    slots = backend.get("slots", {})\n    lines: list[str] = []\n    for slot, value in derived.items():\n        question = by_slot.get(slot)\n        if question is None or slots.get(slot):\n            continue\n        record_answer(backend, question, value, source="derived")\n        lines.append(\n            f"derived: {slot} = {value!r} (provisional — confirm or correct "\n            f"via `bootstrap answer {slot} ...`)",\n        )\n    return lines\n',
    'engine/contextpack.py': '"""AgentContextPack generator — index-or-manifest input (Lane B8, spec 2.10).\n\nGenerates per-area *context packs* — the curated "what an agent must know to\nwork in this area" bundles — from a project index. Two input forms are\naccepted (design-spec 2.10: the generator meets hosts where they are):\n\n  1. the kit\'s own ``project.index.json`` (``{"areas": [...]}``, planted by\n     the adopt flow as a skeleton), and\n  2. a manifest snapshot (``{"subsystems": [...]}``) as produced by a host\'s\n     existing subsystem manifest — mapped onto the same area shape with\n     sensible fallbacks.\n\nEach pack is written under ``<state_dir>/contextpacks/`` and opens with the\n``NOT SOURCE OF TRUTH`` marker: packs are build artifacts — regenerate them\nfrom the index, never hand-edit them. Pure stdlib; every write goes through\n``atomic_write_text``.\n"""\n\nfrom __future__ import annotations\n\nimport json\nimport re\nfrom pathlib import Path\n\nfrom engine.lib.atomicio import atomic_write_text\nfrom engine.lib.config import Config\n\n_PACK_MARKER = (\n    "<!-- NOT SOURCE OF TRUTH — generated by substrate-kit; "\n    "regenerate, do not edit. -->"\n)\n\n# The list-valued fields of the canonical area shape, in emit order.\n_PACK_LIST_KEYS = (\n    "binding_docs",\n    "source_roots",\n    "do_not_create",\n    "gates",\n    "verification",\n)\n\n_PACK_SECTION_TITLES = {\n    "binding_docs": "Binding docs",\n    "source_roots": "Source roots",\n    "do_not_create": "Do-not-create",\n    "gates": "Gates",\n    "verification": "Verification",\n}\n\n_PACK_SLUG_STRIP_RE = re.compile(r"[^a-z0-9._-]")\n_PACK_SLUG_SEP_RE = re.compile(r"[\\s/\\\\]+")\n\n\ndef _pack_slug(name: str) -> str:\n    """Slugify an area name for its pack filename (spaces/slashes -> dashes)."""\n    slug = _PACK_SLUG_SEP_RE.sub("-", name.strip().lower())\n    slug = _PACK_SLUG_STRIP_RE.sub("", slug)\n    slug = re.sub(r"-{2,}", "-", slug).strip("-")\n    return slug or "area"\n\n\ndef _pack_as_list(value: object) -> list[str]:\n    """Coerce an index field to a list of strings (unknown/missing -> [])."""\n    if isinstance(value, str):\n        return [value] if value.strip() else []\n    if isinstance(value, list):\n        return [str(item) for item in value if str(item).strip()]\n    return []\n\n\ndef _pack_area(entry: dict) -> dict:\n    """Normalise one raw index entry onto the canonical area shape."""\n    name = str(entry.get("name") or "").strip() or "unnamed-area"\n    folio = entry.get("folio")\n    area: dict = {\n        "name": name,\n        "folio": str(folio).strip() if isinstance(folio, str) else "",\n    }\n    for key in _PACK_LIST_KEYS:\n        area[key] = _pack_as_list(entry.get(key))\n    return area\n\n\ndef _pack_from_subsystem(entry: dict) -> dict:\n    """Map a manifest-snapshot subsystem entry onto the area shape."""\n    mapped = dict(entry)\n    if not mapped.get("binding_docs"):\n        mapped["binding_docs"] = mapped.get("docs")\n    if not mapped.get("source_roots"):\n        mapped["source_roots"] = mapped.get("roots")\n    return _pack_area(mapped)\n\n\ndef load_pack_index(path: Path) -> list[dict]:\n    """Load a pack index from ``path``, accepting both supported forms.\n\n    Detects the form by top-level key: ``{"areas": [...]}`` is the kit\'s own\n    ``project.index.json``; ``{"subsystems": [...]}`` is a host manifest\n    snapshot (``docs``/``roots`` map onto ``binding_docs``/``source_roots``).\n    Unknown or missing per-entry keys become empty lists. Raises ``ValueError``\n    when the document is neither form (a wrong file, not a quiet no-op).\n    """\n    data = json.loads(path.read_text(encoding="utf-8"))\n    if isinstance(data, dict) and isinstance(data.get("areas"), list):\n        return [_pack_area(e) for e in data["areas"] if isinstance(e, dict)]\n    if isinstance(data, dict) and isinstance(data.get("subsystems"), list):\n        return [\n            _pack_from_subsystem(e) for e in data["subsystems"] if isinstance(e, dict)\n        ]\n    msg = f"{path.name}: expected top-level \'areas\' or \'subsystems\' list"\n    raise ValueError(msg)\n\n\ndef _pack_section(title: str, items: list[str]) -> list[str]:\n    """Render one pack section as markdown lines (empty section -> no lines)."""\n    if not items:\n        return []\n    return [f"## {title}", "", *(f"- {item}" for item in items), ""]\n\n\ndef _pack_body(root: Path, area: dict) -> str:\n    """Compose one pack\'s full markdown text from a normalised area."""\n    lines = [_PACK_MARKER, "", f"# {area[\'name\']} — agent context pack", ""]\n    lines += _pack_section("Folio", [area["folio"]] if area["folio"] else [])\n    for key in _PACK_LIST_KEYS:\n        items = area[key]\n        if key == "source_roots":\n            items = [\n                entry if (root / entry).exists() else f"{entry} (MISSING)"\n                for entry in items\n            ]\n        lines += _pack_section(_PACK_SECTION_TITLES[key], items)\n    return "\\n".join(lines).rstrip() + "\\n"\n\n\ndef generate_packs(root: Path, config: Config, index: list[dict]) -> list[Path]:\n    """Write one context pack per index area; return the written paths.\n\n    Packs land in ``<root>/<state_dir>/contextpacks/<slug>.context.md``.\n    ``source_roots`` entries are existence-checked against ``root`` and\n    suffixed `` (MISSING)`` when absent, so a stale index is visible in the\n    pack instead of silently misleading the agent reading it.\n    """\n    out_dir = root / config.state_dir / "contextpacks"\n    written: list[Path] = []\n    used: set[str] = set()\n    for entry in index:\n        area = _pack_area(entry)\n        # Two areas whose names slugify alike (``Economy``/``economy``,\n        # ``API v1``/``API-v1``, two unnamed areas → ``area``) must not land on\n        # one filename: the later ``atomic_write_text`` would silently erase the\n        # earlier pack and ``written`` would double-count one file. Disambiguate\n        # to the first free ``slug`` / ``slug-2`` / ``slug-3`` … (robust even if\n        # a real ``slug-2`` area also exists); the pack body still names its area\n        # in the heading, so a suffixed file stays identifiable.\n        base = _pack_slug(area["name"])\n        slug, n = base, 2\n        while slug in used:\n            slug, n = f"{base}-{n}", n + 1\n        used.add(slug)\n        path = out_dir / f"{slug}.context.md"\n        atomic_write_text(path, _pack_body(root, area))\n        written.append(path)\n    return written\n\n\ndef pack_index_skeleton(project_name: str) -> str:\n    """Return the planted ``project.index.json`` skeleton (JSON text).\n\n    One example area with every field present-but-empty, plus a ``_comment``\n    explaining how each field feeds the AgentContextPack generator\n    (index-or-manifest input, design-spec 2.10).\n    """\n    skeleton = {\n        "_comment": (\n            "AgentContextPack index (design-spec 2.10). Each `areas` entry "\n            "feeds one generated <state_dir>/contextpacks/<name>.context.md: "\n            "`name` (the area; slugified into the pack filename), `folio` "\n            "(the canonical entry-point doc for the area), `binding_docs` "\n            "(authoritative contracts to read first), `source_roots` (key "\n            "files/dirs; existence-checked at generation, missing ones "\n            "flagged), `do_not_create` (existing systems an agent must not "\n            "duplicate), `gates` (currently active expansion conditions), "\n            "`verification` (commands to run before pushing). The generator "\n            \'also accepts a manifest snapshot ({"subsystems": [...]}) \'\n            "instead of this file."\n        ),\n        "project": project_name,\n        "areas": [\n            {\n                "name": "example-area",\n                "folio": "",\n                "binding_docs": [],\n                "source_roots": [],\n                "do_not_create": [],\n                "gates": [],\n                "verification": [],\n            },\n        ],\n    }\n    return json.dumps(skeleton, indent=2) + "\\n"\n',
    'engine/adopt.py': '"""One-step adopt flow — plant the workflow docs, stage the packs (Lane B8).\n\n``adopt`` turns a bare host repo into a substrate-governed one in a single\nidempotent pass: it renders every content template with the currently filled\ninterview slots and *plants* the live docs (constitution, contracts, ledgers,\nsession scaffolding) — **skip-if-exists, never clobbering** a file the host\nalready owns — then *stages* the ``.claude`` material (working agreement,\nskill pack, persona pack, hook wiring, CI example) under ``<state_dir>`` for\nthe host to install deliberately. Only an explicit ``include_claude=True``\nwrites a live ``.claude/`` tree, and even then only files that are absent\n(the host opt-in stays non-destructive).\n\nAdopt renders what it knows (the Phase-2.5 G2 fix): before rendering, every\ndeterministically-derivable slot (project name, language, verify command,\ndocs root — ``engine/derive.py``) is recorded as a provisional interview\nanswer, and any doc still carrying unfilled ``${slot}`` placeholders is\nplanted under a loud UNRENDERED banner instead of silently inert — a cold\nsession sees at a glance which prose is live and which is an unfilled slot.\nThe guardrail runs first: the kit refuses to adopt into its own tree. Pure\nstdlib; every write goes through ``atomic_write_text``.\n"""\n\nfrom __future__ import annotations\n\nimport sys\nfrom datetime import date\nfrom pathlib import Path\nfrom typing import Any\n\nfrom engine.agents.agents import AGENTS, agent_document, agent_relpath\nfrom engine.contextpack import pack_index_skeleton\nfrom engine.derive import derive_slots, record_derived_slots\nfrom engine.hooks.settings import full_settings_template, hooks_fill_table\nfrom engine.lib.atomicio import atomic_write_text\nfrom engine.lib.config import Config\nfrom engine.lib.guardrail import assert_safe_target\nfrom engine.render import build_context, find_placeholders, load_templates, render\nfrom engine.skills.skills import SKILLS, skill_document, skill_relpath\n\n# Template filename -> planted relpath. CLAUDE.md.tmpl is deliberately absent:\n# it is STAGED under <state_dir>/claude/ (the kit never live-writes .claude/\n# without the explicit include_claude opt-in).\nADOPT_PLAN: list[tuple[str, str]] = [\n    ("CONSTITUTION.md.tmpl", "CONSTITUTION.md"),\n    ("decisions.md.tmpl", "docs/decisions.md"),\n    ("architecture.md.tmpl", "docs/architecture.md"),\n    ("ownership.md.tmpl", "docs/ownership.md"),\n    ("runtime_contracts.md.tmpl", "docs/runtime_contracts.md"),\n    ("repo-navigation-map.md.tmpl", "docs/repo-navigation-map.md"),\n    ("helper-policy.md.tmpl", "docs/helper-policy.md"),\n    ("collaboration-model.md.tmpl", "docs/collaboration-model.md"),\n    ("ai-project-workflow.md.tmpl", "docs/ai-project-workflow.md"),\n    ("owner-profile.md.tmpl", "docs/owner-profile.md"),\n    ("AGENT_ORIENTATION.md.tmpl", "docs/AGENT_ORIENTATION.md"),\n    ("current-state.md.tmpl", "docs/current-state.md"),\n    ("question-router.md.tmpl", "docs/question-router.md"),\n    ("ideas-README.md.tmpl", "docs/ideas/README.md"),\n    ("session-journal.md.tmpl", ".session-journal.md"),\n]\n\n_ADOPT_NEXT_STEPS = (\n    "next steps: run `bootstrap ask` to see the pending interview questions, "\n    "answer them and fill the planted docs in place (`bootstrap render --live`), and set "\n    "the integration mode with `bootstrap mode <observe|guided|active>`."\n)\n\n# First line doubles as the removal marker `strip_unrendered_banner` keys off.\nUNRENDERED_BANNER_FIRST_LINE = (\n    "> ⚠️ **UNRENDERED SLOTS BELOW — run `python3 bootstrap.py ask`.**"\n)\n_UNRENDERED_BANNER = (\n    UNRENDERED_BANNER_FIRST_LINE + "\\n"\n    "> Every `${...}` token in this file is an unfilled interview slot, not\\n"\n    "> project truth. Fill: `bootstrap answer <slot> <value...>`, then\\n"\n    "> `bootstrap render --live` (fills in place and removes this banner).\\n"\n    "> Prose without `${...}` tokens is live guidance already.\\n\\n"\n)\n\n\ndef with_unrendered_banner(text: str) -> str:\n    """Prepend the loud UNRENDERED banner when ``text`` has unfilled slots.\n\n    An inert-looking doc was the measured Phase-2.5 failure mode: raw\n    ``${...}`` placeholders read as non-actionable scaffolding and only cost\n    orientation. The banner names what the tokens are and the exact two\n    commands that fill them; a fully-rendered doc gets no banner.\n    """\n    if not find_placeholders(text):\n        return text\n    return _UNRENDERED_BANNER + text\n\n\ndef strip_unrendered_banner(text: str) -> str:\n    """Remove the adopt-time banner (used once a file has no placeholders)."""\n    if not text.startswith(UNRENDERED_BANNER_FIRST_LINE):\n        return text\n    lines = text.split("\\n")\n    index = 0\n    while index < len(lines) and lines[index].startswith(">"):\n        index += 1\n    while index < len(lines) and not lines[index].strip():\n        index += 1\n    return "\\n".join(lines[index:])\n\n\ndef _vendor_bootstrap(root: Path, report: list[str]) -> str:\n    """Vendor the running single-file bootstrap into ``root``; return hook path.\n\n    The staged hook commands run ``<interpreter> bootstrap.py hook <event>``\n    relative to the host repo root — in the Phase-2.5 A/B the file was never\n    there, so every staged hook pointed outside the target repo (the second\n    G2 failure cause). When adopt runs *as* the single-file ``bootstrap.py``,\n    copy it to the target root (skip-if-exists, like every plant) so those\n    commands resolve. Running from the source/pip layout there is no single\n    file to vendor: fall back to an existing root copy, else the absolute\n    path of the running entry point, else the documented bare-name contract\n    (the hooks README fill-table row covers relocation).\n    """\n    at_root = root / "bootstrap.py"\n    entry = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] else None\n    is_bootstrap_entry = (\n        entry is not None and entry.name == "bootstrap.py" and entry.is_file()\n    )\n    if not at_root.exists() and is_bootstrap_entry and entry != at_root:\n        _adopt_plant(\n            at_root,\n            "bootstrap.py",\n            entry.read_text(encoding="utf-8"),\n            report,\n        )\n    if at_root.exists():\n        return "bootstrap.py"\n    if is_bootstrap_entry:\n        return str(entry)\n    return "bootstrap.py"\n\n\ndef _adopt_dest(relpath: str, config: Config) -> str:\n    """Remap the plan\'s ``docs/`` prefix onto the host\'s configured docs root."""\n    prefix = "docs/"\n    if relpath.startswith(prefix) and config.docs_root != "docs":\n        return f"{config.docs_root}/{relpath[len(prefix) :]}"\n    return relpath\n\n\ndef _adopt_plant(path: Path, relpath: str, text: str, report: list[str]) -> None:\n    """Write ``text`` at ``path`` unless it exists; report planted/kept."""\n    if path.exists():\n        report.append(f"kept: {relpath}")\n        return\n    atomic_write_text(path, text)\n    report.append(f"planted: {relpath}")\n\n\ndef _adopt_stage(path: Path, relpath: str, text: str, report: list[str]) -> None:\n    """Write a staged (generated, regenerable) artifact and report it."""\n    atomic_write_text(path, text)\n    report.append(f"staged: {relpath}")\n\n\ndef _adopt_sessions_readme(markers: list[dict[str, str]]) -> str:\n    """Compose the one-paragraph ``.sessions/README.md`` (born-red convention)."""\n    labels = ", ".join(m.get("label", "") for m in markers if m.get("label"))\n    labels = labels or "(no markers configured)"\n    return (\n        "# Session logs\\n\\n"\n        "Per-session logs live here as `<date>-<slug>.md`, newest first. "\n        "Create the log as the session\'s FIRST commit with a born-red status "\n        "(`> **Status:** `in-progress``) so in-flight work is visible to "\n        "parallel sessions, then flip it to `complete` as the deliberate LAST "\n        "step once the close-out is written — a half-done session never reads "\n        "as finished. Before it counts as complete, a log must carry these "\n        f"markers: {labels}.\\n"\n    )\n\n\ndef ci_snippet() -> str:\n    """Return the staged, fully-commented GitHub-Actions-style CI example.\n\n    Everything is commented out: the host copies it into\n    ``.github/workflows/`` and uncomments/adjusts deliberately — the kit never\n    installs live CI.\n    """\n    return (\n        "# Example GitHub-Actions-style quality gate for a substrate-kit host.\\n"\n        "# Copy into .github/workflows/, uncomment, and adjust the interpreter\\n"\n        "# and bootstrap path to match your repo.\\n"\n        "#\\n"\n        "# `bootstrap.py check --strict` runs every kit checker in one pass:\\n"\n        "# docs hygiene (badges / links / reachability), session-log markers,\\n"\n        "# namespace shadowing, seam authority, orientation budget, and the\\n"\n        "# decision ledger.\\n"\n        "#\\n"\n        "# name: substrate-quality\\n"\n        "# on:\\n"\n        "#   pull_request:\\n"\n        "#   push:\\n"\n        "#     branches: [main]\\n"\n        "# jobs:\\n"\n        "#   substrate-check:\\n"\n        "#     runs-on: ubuntu-latest\\n"\n        "#     steps:\\n"\n        "#       - uses: actions/checkout@v4\\n"\n        "#       - name: substrate checks\\n"\n        "#         run: python3 bootstrap.py check --strict\\n"\n    )\n\n\nLIVE_CI_RELPATH = ".github/workflows/substrate-gate.yml"\n\n\ndef live_ci_workflow(interpreter: str = "python3") -> str:\n    """Return the LIVE (uncommented) CI gate workflow — the locked door.\n\n    Unlike :func:`ci_snippet` (a commented example the host installs by hand),\n    this is a working GitHub-Actions workflow ``adopt --wire-enforcement``\n    writes into ``.github/workflows/``. It runs\n    ``bootstrap.py check --strict --require-session-log`` on every pull request,\n    so the merge is **held red** until the session\'s journal is written and the\n    whole hygiene suite passes. This is the forcing function that makes the\n    memory ritual non-optional: a nag can be ignored, a failing required check\n    cannot. `fetch-depth: 0` gives the checkout full history (the gate itself is\n    git-free, but hosts commonly extend this workflow with diff-aware steps).\n    A docs-only or bot PR that shouldn\'t need a session card is handled by the\n    host adding a `paths-ignore:` or a label carve-out — kept strict by default\n    on purpose (the discipline is the point).\n    """\n    return (\n        "# substrate-kit enforcement gate (LIVE — installed by "\n        "`bootstrap.py adopt --wire-enforcement`).\\n"\n        "# Holds the merge red until the session journal is written and every\\n"\n        "# hygiene check passes. Edit `paths-ignore` / add a label carve-out if\\n"\n        "# some PRs legitimately need no session card.\\n"\n        "name: substrate-gate\\n"\n        "on:\\n"\n        "  pull_request:\\n"\n        "  push:\\n"\n        "    branches: [main]\\n"\n        "jobs:\\n"\n        "  substrate-gate:\\n"\n        "    runs-on: ubuntu-latest\\n"\n        "    steps:\\n"\n        "      - uses: actions/checkout@v4\\n"\n        "        with:\\n"\n        "          fetch-depth: 0\\n"\n        "      - uses: actions/setup-python@v5\\n"\n        "        with:\\n"\n        \'          python-version: "3.x"\\n\'\n        "      - name: substrate gate (docs + session-log required)\\n"\n        f"        run: {interpreter} bootstrap.py check --strict --require-session-log\\n"\n    )\n\n\ndef adopt(\n    root: Path,\n    config: Config,\n    backend: Any,\n    *,\n    kit_root: Path,\n    include_claude: bool = False,\n    wire_enforcement: bool = False,\n) -> list[str]:\n    """Adopt the substrate workflow into ``root``; return the report lines.\n\n    Steps (all idempotent): (0) guardrail — refuse the kit\'s own tree; then\n    derive what the tree can tell us (provisional slots) and vendor the\n    single-file bootstrap so hook commands resolve in-repo;\n    (1) plant every ``ADOPT_PLAN`` doc rendered from the current slots —\n    skip-if-exists, unrendered docs bannered; (2) plant\n    ``<sessions_dir>/README.md``; (3) plant the ``project.index.json``\n    skeleton; (4) stage the ``.claude`` material (CLAUDE.md, skills,\n    personas, hook settings + fill-table README) under ``<state_dir>``;\n    (5) stage the CI example; (6) with ``include_claude``, additionally\n    write ``.claude/CLAUDE.md`` + ``.claude/settings.json`` if absent;\n    (7) close with the next-steps line.\n\n    ``wire_enforcement`` turns on the two **forcing functions** that make the\n    memory ritual actually get used (the Phase-2.5 re-run showed docs alone get\n    read but not written back): it implies ``include_claude`` (the live Stop-hook\n    **nag**) **and** plants a live CI workflow (:data:`LIVE_CI_RELPATH`) running\n    the ``--require-session-log`` gate — the **locked door** that holds a merge\n    red until the journal is written. Kept opt-in: the kit still never installs\n    executable CI/hooks silently (the deliberate safety default), but a host —\n    or the rebuild\'s K0 session — flips this on to reproduce the enforcement\n    this repo\'s discipline actually runs on.\n    """\n    include_claude = include_claude or wire_enforcement\n    assert_safe_target(root, kit_root)\n    templates = load_templates()\n    report: list[str] = []\n\n    # (0b) Adopt renders what it knows: seed derivable slots (provisional,\n    # never overwriting an existing answer), then build the render context.\n    report.extend(record_derived_slots(backend, derive_slots(root, config.docs_root)))\n    bootstrap_path = _vendor_bootstrap(root, report)\n    context = build_context(backend.data)\n    # The live integration mode is state, not a slot — render it truthfully.\n    context.setdefault("integration_mode", str(backend.get("mode", "guided")))\n\n    # (1) Plant the live docs — never clobber; a doc with unfilled ${slots}\n    # is planted under the loud UNRENDERED banner (visible, never inert).\n    for template_name, plan_rel in ADOPT_PLAN:\n        rel = _adopt_dest(plan_rel, config)\n        text = render(templates[template_name], context)\n        if template_name == "decisions.md.tmpl":\n            # The example D-0001 records THIS adoption — stamp the real date so\n            # the planted ledger is check_ledger-clean from its first commit.\n            text = text.replace("- date:\\n", f"- date: {date.today().isoformat()}\\n")\n        _adopt_plant(root / rel, rel, with_unrendered_banner(text), report)\n\n    # (2) Session-log scaffolding.\n    sessions_rel = f"{config.sessions_dir}/README.md"\n    readme = _adopt_sessions_readme(config.session_markers)\n    _adopt_plant(root / config.sessions_dir / "README.md", sessions_rel, readme, report)\n\n    # (3) The context-pack index skeleton.\n    project_name = context.get("project_name") or root.name\n    skeleton = pack_index_skeleton(project_name)\n    _adopt_plant(root / "project.index.json", "project.index.json", skeleton, report)\n\n    # (4) Stage the .claude material under <state_dir> (regenerated each run).\n    state_base = root / config.state_dir\n    claude_doc = with_unrendered_banner(render(templates["CLAUDE.md.tmpl"], context))\n    claude_rel = f"{config.state_dir}/claude/CLAUDE.md"\n    _adopt_stage(state_base / "claude" / "CLAUDE.md", claude_rel, claude_doc, report)\n    for skill in SKILLS:\n        rel = skill_relpath(skill)\n        body = render(skill["body"], context)\n        document = skill_document(skill, body)\n        _adopt_stage(state_base / rel, f"{config.state_dir}/{rel}", document, report)\n    for agent in AGENTS:\n        rel = agent_relpath(agent)\n        body = render(agent["body"], context)\n        document = agent_document(agent, body)\n        _adopt_stage(state_base / rel, f"{config.state_dir}/{rel}", document, report)\n    settings_text = full_settings_template(config, bootstrap_path=bootstrap_path)\n    settings_rel = f"{config.state_dir}/hooks/settings.template.json"\n    settings_path = state_base / "hooks" / "settings.template.json"\n    _adopt_stage(settings_path, settings_rel, settings_text, report)\n    hooks_readme_rel = f"{config.state_dir}/hooks/README.md"\n    hooks_readme = hooks_fill_table()\n    _adopt_stage(\n        state_base / "hooks" / "README.md",\n        hooks_readme_rel,\n        hooks_readme,\n        report,\n    )\n\n    # (5) Stage the CI example.\n    ci_rel = f"{config.state_dir}/ci/quality.yml.example"\n    _adopt_stage(\n        state_base / "ci" / "quality.yml.example",\n        ci_rel,\n        ci_snippet(),\n        report,\n    )\n\n    # (6) Explicit host opt-in: live .claude/ (still never overwrites).\n    if include_claude:\n        claude_dir = root / ".claude"\n        _adopt_plant(claude_dir / "CLAUDE.md", ".claude/CLAUDE.md", claude_doc, report)\n        _adopt_plant(\n            claude_dir / "settings.json",\n            ".claude/settings.json",\n            settings_text,\n            report,\n        )\n\n    # (6b) Enforcement opt-in: the LIVE CI gate (the locked door). include_claude\n    # above already wired the live nag; this adds the required check that a\n    # missing journal can never merge past.\n    if wire_enforcement:\n        _adopt_plant(\n            root / LIVE_CI_RELPATH,\n            LIVE_CI_RELPATH,\n            live_ci_workflow(config.interpreter_for_checks or "python3"),\n            report,\n        )\n\n    # (7) Point the adopter at the interview loop.\n    report.append(_ADOPT_NEXT_STEPS)\n    return report\n',
    'engine/cli.py': '"""The substrate-kit bootstrap command line.\n\nSurface: ``init`` (idempotent), ``status``, ``mode <name>``, ``stance [name]``\n(show or set the task stance), ``ask`` (list the pending interview questions),\n``answer`` / ``confirm`` (fill / confirm a slot), ``render`` (write content\ndocs), ``skills`` / ``agents`` / ``hooks`` (list / ``--build`` the packs),\n``hook <event>`` (the runtime hook entry points), ``check`` (every hygiene\nchecker), ``triggers``, ``reflect``, ``episodes``, ``metrics``, ``maintain``,\n``review`` (the independent-review seam), ``economy`` (the context-economy\nengine), ``ledger`` (the [D-NNNN] decisions ledger), and ``--simulate N\n[--mode m]`` (the CI / proving smoke that drives the staged interview and\nasserts per-mode behavior). Output goes through ``_emit`` (``sys.stdout.write``)\nrather than ``print`` to keep the engine lint-clean.\n"""\n\nfrom __future__ import annotations\n\nimport argparse\nimport json\nimport sys\nimport tempfile\nfrom datetime import date\nfrom pathlib import Path\n\nfrom engine.adopt import ADOPT_PLAN, _adopt_dest, adopt, strip_unrendered_banner\nfrom engine.agents.agents import AGENTS, agent_document, agent_relpath\nfrom engine.checks.check_docs import run_doc_checks\nfrom engine.checks.check_namespace import check_namespace\nfrom engine.checks.check_orientation_budget import check_orientation_budget\nfrom engine.checks.check_seam_authority import check_seam_authority\nfrom engine.checks.check_session_log import check_log, latest_session_log\nfrom engine.contextpack import generate_packs, load_pack_index\nfrom engine.economy.engine import economy_actuate, economy_check, issue_body\nfrom engine.economy.harvest import harvest_sources, parse_harvest_tables\nfrom engine.economy.simulator import calibration_recipe, default_calibration, run_search\nfrom engine.hooks.post_edit import evaluate_edit\nfrom engine.hooks.session_start import compose_orientation\nfrom engine.hooks.settings import full_settings_template, hooks_fill_table\nfrom engine.hooks.stance_guard import evaluate_tool, settings_snippet, tool_from_payload\nfrom engine.hooks.stop_check import evaluate_stop\nfrom engine.interview.interview import (\n    confirm_slot,\n    critical_slots,\n    pending_questions,\n    record_answer,\n    run_session,\n    session_questions,\n)\nfrom engine.interview.question_bank import QUESTIONS\nfrom engine.ledger import (\n    LEDGER_FILENAME,\n    append_decision,\n    check_ledger,\n    check_stamp_discipline,\n)\nfrom engine.lib.atomicio import atomic_write_text\nfrom engine.lib.config import Config, config_path, load_config, save_config\nfrom engine.lib.guardrail import UnsafeTargetError, assert_safe_target\nfrom engine.lib.modes import actuators_may_apply, triggers_mandate\nfrom engine.lib.state import JsonStateBackend, default_state\nfrom engine.loop.episodes import (\n    EPISODIC_INDEX_FILENAME,\n    rebuild_episodic_index,\n    search_episodes,\n)\nfrom engine.loop.kpis import kpi_footer, workflow_kpis\nfrom engine.loop.maintenance import compaction_due, maintenance_report, run_compaction\nfrom engine.loop.reflections import (\n    REFLECTIONS_FILENAME,\n    add_reflection,\n    lessons_block,\n    load_reflections,\n    mine_reflections,\n)\nfrom engine.loop.review_seam import (\n    apply_review_verdict,\n    build_review_payload,\n    clear_review_payload,\n    seam_wiring_doc,\n    write_review_payload,\n)\nfrom engine.loop.triggers import check_triggers, mandatory_questions, trigger_block\nfrom engine.render import build_context, find_placeholders, load_templates, render\nfrom engine.skills.skills import (\n    SKILLS,\n    skill_capabilities,\n    skill_document,\n    skill_relpath,\n)\nfrom engine.stances.stances import DEFAULT_STANCE, stance_briefing, stance_names\n\n\ndef _emit(line: str = "") -> None:\n    """Write a line to stdout (avoids the print() lint ban in engine code)."""\n    sys.stdout.write(line + "\\n")\n\n\ndef _kit_root() -> Path:\n    """Return the tree the guardrail protects (the kit\'s own checkout).\n\n    Only the source layout (``.../src/engine/cli.py``) has a kit tree to\n    protect: there, the checkout root is ``parents[2]``. Running as the\n    copied single-file bootstrap or a pip install, this returns the module\n    file itself — a *file* matches no target directory, so the guardrail\n    never engages (there is no kit tree). The old unconditional\n    ``parents[2]`` made the dist\'s guardrail root the grandparent of the\n    user\'s repo, refusing EVERY real ``adopt``/``init`` outside the temp\n    tree — the documented primary flow.\n    """\n    here = Path(__file__).resolve()\n    if here.parent.name == "engine" and here.parent.parent.name == "src":\n        return here.parents[2]\n    return here\n\n\ndef _state_path(root: Path, config: Config) -> Path:\n    """Return the state-file path under a project ``root``."""\n    return root / config.state_dir / "state.json"\n\n\ndef cmd_init(target: Path) -> int:\n    """Create config + state under ``target`` if absent; never clobber."""\n    assert_safe_target(target, _kit_root())\n    target.mkdir(parents=True, exist_ok=True)\n    if config_path(target).exists():\n        config = load_config(target)\n    else:\n        config = Config()\n        save_config(target, config)\n    state_path = _state_path(target, config)\n    if state_path.exists():\n        _emit(f"init: already initialised at {target} (idempotent no-op).")\n        return 0\n    backend = JsonStateBackend(state_path)\n    with backend.transaction():\n        for key, value in default_state(config.project_id).items():\n            backend.set(key, value)\n    _emit(f"init: created {state_path} (project_id={config.project_id}).")\n    return 0\n\n\ndef cmd_status(target: Path) -> int:\n    """Print a one-screen summary of the install\'s state."""\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    data = backend.data\n    if not data:\n        _emit(f"status: no state at {target} (run init first).")\n        return 1\n    _emit(f"project_id : {data.get(\'project_id\')}")\n    _emit(f"stage      : {data.get(\'stage\')}")\n    _emit(f"mode       : {data.get(\'mode\')}")\n    _emit(f"stance     : {data.get(\'stance\')}")\n    _emit(f"sessions   : {data.get(\'session_count\')}")\n    return 0\n\n\ndef cmd_mode(target: Path, name: str) -> int:\n    """Set the integration mode (observe | guided | active)."""\n    valid = ("observe", "guided", "active")\n    if name not in valid:\n        _emit(f"mode: invalid mode {name!r} (choose from {list(valid)}).")\n        return 2\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    if not backend.data:\n        _emit(f"mode: no state at {target} (run init first).")\n        return 1\n    history = list(backend.get("mode_history", []))\n    history.append(\n        {\n            "mode": name,\n            "session": int(backend.get("session_count", 0)),\n            "date": date.today().isoformat(),\n        },\n    )\n    with backend.transaction():\n        backend.set("mode", name)\n        backend.set("mode_history", history)\n    _emit(f"mode: set to {name} (audit trail: {len(history)} switch(es)).")\n    return 0\n\n\ndef cmd_stance(target: Path, name: str | None) -> int:\n    """Show or set the active task stance (question|analysis|debug|review|plan).\n\n    With no ``name``, prints the active stance\'s briefing (reading-route +\n    tool-scope + output contract) and the available set. With a ``name``, switches\n    the active stance in state. The stance is advisory — it scopes orientation, it\n    does not block actions.\n    """\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    if not backend.data:\n        _emit(f"stance: no state at {target} (run init first).")\n        return 1\n    if name is None:\n        active = backend.data.get("stance", DEFAULT_STANCE)\n        _emit(stance_briefing(active))\n        _emit(f"  available: {\', \'.join(stance_names())}")\n        return 0\n    if name not in stance_names():\n        _emit(f"stance: invalid stance {name!r} (choose from {stance_names()}).")\n        return 2\n    backend.set("stance", name)\n    _emit(f"stance: set to {name}.")\n    _emit(stance_briefing(name))\n    return 0\n\n\ndef cmd_ask(target: Path) -> int:\n    """List the interview\'s currently pending questions."""\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    if not backend.data:\n        _emit(f"ask: no state at {target} (run init first).")\n        return 1\n    pending = pending_questions(backend.data)\n    if not pending:\n        _emit("ask: no pending questions — all slots filled.")\n        return 0\n    asked = session_questions(backend.data)\n    _emit(f"ask: {len(asked)} question(s) this session (mode quota):")\n    for question in asked:\n        _emit(\n            f"  [{question[\'id\']}] "\n            f"({question[\'audience\']}/{question[\'priority\']}) {question[\'prompt\']}",\n        )\n    remaining = len(pending) - len(asked)\n    if remaining > 0:\n        _emit(f"  (+{remaining} more later — the mode paces the interview)")\n    return 0\n\n\ndef _render_live(target: Path, context: dict[str, str]) -> int:\n    """Fill remaining ``${slot}`` placeholders in the PLANTED docs, in place.\n\n    Placeholders survive verbatim in a planted file until their slot fills, so\n    substituting over the live text updates exactly the newly-answered slots\n    while preserving every hand edit around them. Returns the leftover count.\n    """\n    leftover_total = 0\n    for _, plan_rel in ADOPT_PLAN:\n        rel = _adopt_dest(plan_rel, load_config(target))\n        path = target / rel\n        if not path.exists():\n            continue\n        text = path.read_text(encoding="utf-8")\n        filled = render(text, context)\n        leftover = find_placeholders(filled)\n        leftover_total += len(leftover)\n        if not leftover:\n            # Fully rendered — the adopt-time UNRENDERED banner has done its job.\n            filled = strip_unrendered_banner(filled)\n        if filled != text:\n            atomic_write_text(path, filled)\n            suffix = f" ({len(leftover)} slot(s) still unfilled)" if leftover else ""\n            _emit(f"render: filled {rel}{suffix}")\n    _emit(f"render: {leftover_total} unfilled placeholder(s) across planted docs.")\n    return 0\n\n\ndef cmd_render(target: Path, live: bool = False) -> int:\n    """Render the content docs from the current filled slots.\n\n    Default: stage fresh renders of every template into\n    ``<state_dir>/rendered/``. With ``live``: fill remaining placeholders in\n    the *planted* docs in place (hand edits preserved) — the post-interview\n    "make the live docs catch up" pass.\n    """\n    assert_safe_target(target, _kit_root())\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    if not backend.data:\n        _emit(f"render: no state at {target} (run init first).")\n        return 1\n    context = build_context(backend.data)\n    if live:\n        return _render_live(target, context)\n    out_dir = target / config.state_dir / "rendered"\n    leftover_total = 0\n    for name, text in load_templates().items():\n        rendered = render(text, context)\n        leftover = find_placeholders(rendered)\n        leftover_total += len(leftover)\n        out_name = name[:-5] if name.endswith(".tmpl") else name\n        atomic_write_text(out_dir / out_name, rendered)\n        suffix = f" ({len(leftover)} slot(s) unfilled)" if leftover else ""\n        _emit(f"render: wrote {out_name}{suffix}")\n    _emit(f"render: {leftover_total} unfilled placeholder(s) total.")\n    return 0\n\n\ndef cmd_skills(target: Path, build: bool) -> int:\n    """List the skill pack, or ``--build`` it into ``<state_dir>/skills/``.\n\n    Listing shows each skill + its declared capabilities (what it may do beyond\n    read, overriding the ambient stance). Building emits a native ``SKILL.md`` per\n    skill into the staging area, body slot-filled from the interview — the host\n    then installs them under ``.claude/skills/``. Like ``render``, the kit stages;\n    it never writes a live ``.claude/`` tree.\n    """\n    config = load_config(target)\n    if build:\n        assert_safe_target(target, _kit_root())\n    if not build:\n        _emit("skills:")\n        for skill in SKILLS:\n            caps = ", ".join(skill_capabilities(skill["name"]))\n            _emit(f"  {skill[\'name\']} — {skill[\'description\']}")\n            _emit(f"    capabilities: {caps}")\n        return 0\n    backend = JsonStateBackend(_state_path(target, config))\n    context = build_context(backend.data) if backend.data else {}\n    out_base = target / config.state_dir\n    leftover_total = 0\n    for skill in SKILLS:\n        body = render(skill["body"], context)\n        leftover = find_placeholders(body)\n        leftover_total += len(leftover)\n        atomic_write_text(out_base / skill_relpath(skill), skill_document(skill, body))\n        suffix = f" ({len(leftover)} slot(s) unfilled)" if leftover else ""\n        _emit(f"skills: wrote {skill_relpath(skill)}{suffix}")\n    _emit(f"skills: {len(SKILLS)} skill(s), {leftover_total} unfilled placeholder(s).")\n    return 0\n\n\ndef cmd_agents(target: Path, build: bool) -> int:\n    """List the persona pack, or ``--build`` it into ``<state_dir>/agents/``.\n\n    Listing shows each persona + its description. Building emits a native\n    ``.claude/agents``-style ``<name>.md`` per persona into the staging area, body\n    slot-filled from the project\'s contract slots — the host then installs them\n    under ``.claude/agents/``. Like ``render``/``skills``, the kit stages; it never\n    writes a live ``.claude/`` tree.\n    """\n    config = load_config(target)\n    if build:\n        assert_safe_target(target, _kit_root())\n    if not build:\n        _emit("agents:")\n        for agent in AGENTS:\n            _emit(f"  {agent[\'name\']} — {agent[\'description\']}")\n        return 0\n    backend = JsonStateBackend(_state_path(target, config))\n    context = build_context(backend.data) if backend.data else {}\n    out_base = target / config.state_dir\n    leftover_total = 0\n    for agent in AGENTS:\n        body = render(agent["body"], context)\n        leftover = find_placeholders(body)\n        leftover_total += len(leftover)\n        atomic_write_text(out_base / agent_relpath(agent), agent_document(agent, body))\n        suffix = f" ({len(leftover)} slot(s) unfilled)" if leftover else ""\n        _emit(f"agents: wrote {agent_relpath(agent)}{suffix}")\n    count = len(AGENTS)\n    _emit(f"agents: {count} persona(s), {leftover_total} unfilled placeholder(s).")\n    return 0\n\n\ndef _hook_command(config: Config) -> str:\n    """Return the shell command Claude Code runs for the PreToolUse guard."""\n    return f"{config.interpreter} bootstrap.py hook pretooluse"\n\n\ndef cmd_hooks(target: Path, build: bool) -> int:\n    """Show the hook wiring, or ``--build`` the settings files into staging.\n\n    Four hooks: the **PreToolUse stance guard**, **SessionStart orientation**,\n    the **PostToolUse edit advisor**, and the **Stop-check advisor**. Building\n    stages the PreToolUse snippet, the full four-event\n    ``settings.template.json``, and the fill-table README into\n    ``<state_dir>/hooks/`` — the host merges them into their own settings\n    (adjusting the bootstrap path). Like the other emitters, the kit stages;\n    it never writes a live ``.claude/`` tree.\n    """\n    config = load_config(target)\n    if build:\n        assert_safe_target(target, _kit_root())\n    command = _hook_command(config)\n    if not build:\n        _emit("hooks:")\n        _emit("  pretooluse   — stance guard: warns on an out-of-stance tool.")\n        _emit("  sessionstart — prints the mode-aware orientation injection.")\n        _emit("  postedit     — warns on generated-artifact / unbadged-doc edits.")\n        _emit("  stopcheck    — session-close advisories (log, questions, cadence).")\n        _emit(f"  wiring command: {command}")\n        return 0\n    out = target / config.state_dir / "hooks" / "settings.snippet.json"\n    atomic_write_text(out, settings_snippet(command))\n    tmpl = target / config.state_dir / "hooks" / "settings.template.json"\n    atomic_write_text(tmpl, full_settings_template(config))\n    atomic_write_text(\n        target / config.state_dir / "hooks" / "README.md",\n        hooks_fill_table(),\n    )\n    _emit(f"hooks: wrote {out.relative_to(target)}")\n    _emit(f"hooks: wrote {tmpl.relative_to(target)} (all four events) + README.md")\n    _emit("hooks: merge the hook blocks into .claude/settings.json yourself.")\n    return 0\n\n\ndef _hook_pretooluse(target: Path) -> int:\n    """PreToolUse stance guard: warn on stderr for an out-of-stance tool."""\n    tool_name = tool_from_payload(sys.stdin.read())\n    if not tool_name:\n        return 0\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    stance = backend.data.get("stance") if backend.data else None\n    if not stance:\n        return 0\n    warning = evaluate_tool(stance, tool_name)\n    if warning:\n        sys.stderr.write(warning + "\\n")\n    return 0\n\n\ndef _hook_sessionstart(target: Path) -> int:\n    """SessionStart: print the mode-aware orientation composition to stdout."""\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    text = compose_orientation(target, config, backend)\n    if text:\n        sys.stdout.write(text)\n    return 0\n\n\ndef _hook_postedit(target: Path) -> int:\n    """PostToolUse: warn on stderr for a generated-artifact / unbadged-doc edit.\n\n    Handles Edit/Write (``tool_input.file_path``) and NotebookEdit\n    (``tool_input.notebook_path``) — the three tools the settings matcher wires.\n    A NotebookEdit carries ``notebook_path``, not ``file_path``, so keying only\n    on the latter matched notebook edits but never advised them (the matcher\n    over-advertised its coverage).\n    """\n    raw = sys.stdin.read()\n    try:\n        payload = json.loads(raw) if raw.strip() else {}\n    except json.JSONDecodeError:\n        return 0\n    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None\n    if not isinstance(tool_input, dict):\n        return 0\n    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")\n    if not isinstance(file_path, str) or not file_path:\n        return 0\n    warning = evaluate_edit(target, load_config(target), file_path)\n    if warning:\n        sys.stderr.write(warning + "\\n")\n    return 0\n\n\ndef _hook_stopcheck(target: Path) -> int:\n    """Stop: print the session-close advisory lines to stderr."""\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    for line in evaluate_stop(target, config, backend):\n        sys.stderr.write(line + "\\n")\n    return 0\n\n\n_HOOK_EVENTS = {\n    "pretooluse": _hook_pretooluse,\n    "sessionstart": _hook_sessionstart,\n    "postedit": _hook_postedit,\n    "stopcheck": _hook_stopcheck,\n}\n\n\ndef cmd_hook(target: Path, event: str) -> int:\n    """Run a Claude Code hook entry point (all advisory — always exit 0).\n\n    ``pretooluse`` warns on an out-of-stance tool; ``sessionstart`` prints the\n    orientation injection to stdout; ``postedit`` reads the PostToolUse stdin\n    payload (``tool_input.file_path``) and warns on stderr; ``stopcheck``\n    prints session-close advisories to stderr. Every event fails open on a\n    missing / malformed payload, config, or state.\n    """\n    handler = _HOOK_EVENTS.get(event)\n    if handler is None:\n        return 0\n    try:\n        return handler(target)\n    except Exception:  # noqa: BLE001 — hooks fail open by contract, always 0\n        return 0\n\n\ndef _extra_check_findings(target: Path, config: Config) -> list:\n    """Run the configured non-doc checkers (ledger, namespace, seams, budget).\n\n    Each checker engages only when its inputs exist — an un-adopted project\n    with no ledger, no namespace roots, no seams, and no boot docs runs none of\n    them, so ``check`` stays meaningful before onboarding.\n    """\n    findings: list = []\n    ledger_path = target / config.docs_root / LEDGER_FILENAME\n    if ledger_path.exists():\n        findings += check_ledger(ledger_path)\n        findings += check_stamp_discipline(target / config.docs_root, ledger_path)\n    roots = [target / r for r in config.namespace.get("roots", [])]\n    roots = [r for r in roots if r.exists()]\n    if roots:\n        findings += check_namespace(\n            roots,\n            reserved=config.namespace.get("reserved") or None,\n        )\n    if config.seams:\n        findings += check_seam_authority(target, config.seams)\n    boot_docs = config.orientation.get("boot_docs") or config.readpath_docs\n    docs_root = target / config.docs_root\n    if any((docs_root / doc).exists() or (target / doc).exists() for doc in boot_docs):\n        findings += check_orientation_budget(target, config)\n    return findings\n\n\ndef cmd_check(\n    target: Path,\n    strict: bool,\n    *,\n    require_session_log: bool = False,\n) -> int:\n    """Run every hygiene checker against ``target``.\n\n    Docs (badge/link/reachable), the decisions ledger + stamp discipline, the\n    namespace/shadowing guard, the seam-authority fences, and the orientation\n    word budget — each engaging only when its inputs exist. Findings always\n    count toward the exit code (under ``--strict``); an *incomplete* existing\n    session log counts. A *missing* session log is **advisory by default** (a\n    host may run ``check`` mid-session) but becomes a **hard failure** under\n    ``require_session_log`` — the gate mode the live CI workflow runs, so a\n    session that never writes its journal cannot merge (the "locked door" that\n    makes the memory ritual non-optional, not merely advised). Uses config\n    defaults if ``target`` has no ``substrate.config.json`` yet, so a project\n    can lint before onboarding.\n    """\n    config = load_config(target)\n    docs_root = target / config.docs_root\n    doc_findings = run_doc_checks(\n        docs_root,\n        config.badge_tokens,\n        config.readpath_docs,\n    )\n    doc_findings = list(doc_findings) + _extra_check_findings(target, config)\n    if doc_findings:\n        _emit(f"check: {len(doc_findings)} finding(s):")\n        for finding in doc_findings:\n            _emit(f"  [{finding.kind}] {finding.path}: {finding.message}")\n\n    log = latest_session_log(target / config.sessions_dir)\n    log_missing: list[str] = check_log(log, config.session_markers) if log else []\n    # In gate mode an absent log is itself a failing condition, so it must feed\n    # the exit code exactly like an incomplete one.\n    log_absent_fails = log is None and require_session_log\n    if log is None:\n        if require_session_log:\n            _emit(\n                f"check: MERGE HELD — no session log under {config.sessions_dir}/ "\n                "(--require-session-log): write one before merging.",\n            )\n        else:\n            _emit("check: no session log found yet (advisory — not a failure).")\n    else:\n        rel = log.relative_to(target) if log.is_relative_to(target) else log\n        if log_missing:\n            _emit(f"check: session log {rel} is missing: {\', \'.join(log_missing)}")\n        else:\n            _emit(f"check: session log {rel} complete.")\n\n    if not doc_findings and not log_missing and not log_absent_fails:\n        _emit("check: all checks passed.")\n        return 0\n    return 1 if strict else 0\n\n\ndef _require_state(\n    target: Path,\n    command: str,\n) -> tuple[Config, JsonStateBackend] | None:\n    """Load config + state; None (with a message) when the install is missing.\n\n    Also runs the live-loop guardrail: state-backed commands read AND write\n    the install, and only ``init``/``adopt`` were guarded before — ``ledger``,\n    the ``--build`` emitters, and ``episodes --rebuild`` wrote into a target\n    the guardrail would have refused.\n    """\n    assert_safe_target(target, _kit_root())\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    if not backend.data:\n        _emit(f"{command}: no state at {target} (run init first).")\n        return None\n    return config, backend\n\n\ndef _question_for_slot(slot: str) -> dict | None:\n    """Return the bank question that fills ``slot`` (None when unknown)."""\n    for question in QUESTIONS:\n        if question["slot"] == slot:\n            return question\n    return None\n\n\ndef cmd_answer(target: Path, slot: str, answer: str) -> int:\n    """Record a user answer for ``slot`` (fills it, resolves its escalation)."""\n    loaded = _require_state(target, "answer")\n    if loaded is None:\n        return 1\n    _, backend = loaded\n    question = _question_for_slot(slot)\n    if question is None:\n        known = ", ".join(q["slot"] for q in QUESTIONS)\n        _emit(f"answer: unknown slot {slot!r} (known: {known}).")\n        return 2\n    record_answer(backend, question, answer, source="user")\n    status = backend.get("slots", {}).get(slot)\n    _emit(f"answer: {slot} -> {status}.")\n    if status == "partial":\n        floor = int(question.get("min_len", 1))\n        _emit(f"answer: too thin to count (needs >= {floor} chars of substance).")\n    return 0\n\n\ndef cmd_confirm(target: Path, slot: str) -> int:\n    """Confirm a provisional (self-answered) slot as user-verified."""\n    loaded = _require_state(target, "confirm")\n    if loaded is None:\n        return 1\n    _, backend = loaded\n    if confirm_slot(backend, slot, source="user"):\n        _emit(f"confirm: {slot} confirmed (provisional -> filled).")\n        return 0\n    _emit(f"confirm: {slot} is not provisional (nothing to confirm).")\n    return 1\n\n\ndef cmd_triggers(target: Path) -> int:\n    """Scan for fired triggers and show the mandated / advisory questions."""\n    loaded = _require_state(target, "triggers")\n    if loaded is None:\n        return 1\n    config, backend = loaded\n    triggers = check_triggers(target, config, backend.data)\n    if not triggers:\n        _emit("triggers: none fired.")\n        return 0\n    questions = mandatory_questions(triggers)\n    block = trigger_block(\n        triggers,\n        questions,\n        mandate=triggers_mandate(backend.data),\n    )\n    _emit(block)\n    return 0\n\n\ndef cmd_reflect(\n    target: Path,\n    *,\n    add: str | None,\n    evidence: str,\n    tags: str,\n    mine: bool,\n) -> int:\n    """List, add to, or mine the forward reflection buffer."""\n    loaded = _require_state(target, "reflect")\n    if loaded is None:\n        return 1\n    config, backend = loaded\n    path = target / config.state_dir / REFLECTIONS_FILENAME\n    buffer_size = int(config.reflection.get("buffer_size", 5))\n    if add is not None:\n        entry = add_reflection(\n            path,\n            lesson=add,\n            evidence=evidence,\n            tags=[t for t in tags.split(",") if t],\n            buffer_size=buffer_size,\n        )\n        _emit(f"reflect: added {entry[\'id\']}.")\n    if mine:\n        known = {e.get("lesson", "") for e in load_reflections(path)}\n        candidates = [\n            c\n            for c in mine_reflections(target / config.sessions_dir)\n            if c["lesson"] not in known\n        ]\n        for cand in candidates:\n            entry = add_reflection(\n                path,\n                lesson=cand["lesson"],\n                evidence=cand.get("evidence", ""),\n                tags=list(cand.get("tags", [])),\n                buffer_size=buffer_size,\n            )\n            known.add(cand["lesson"])\n            _emit(f"reflect: mined {entry[\'id\']} — {cand[\'lesson\'][:60]}")\n        if not candidates:\n            _emit("reflect: mined nothing new.")\n    entries = load_reflections(path)\n    backend.set(\n        "reflection_buffer",\n        {\n            "active_count": len(entries),\n            "last_mined": (\n                date.today().isoformat()\n                if mine\n                else (backend.get("reflection_buffer", {}) or {}).get("last_mined")\n            ),\n        },\n    )\n    block = lessons_block(entries)\n    _emit(block if block else "reflect: buffer empty.")\n    return 0\n\n\ndef cmd_episodes(target: Path, *, rebuild: bool, search: str | None) -> int:\n    """Rebuild or search the episodic index over the session logs."""\n    config = load_config(target)\n    if rebuild:\n        assert_safe_target(target, _kit_root())\n    index_path = target / config.state_dir / EPISODIC_INDEX_FILENAME\n    if rebuild:\n        entries = rebuild_episodic_index(target / config.sessions_dir, index_path)\n        _emit(f"episodes: indexed {len(entries)} session(s).")\n    if search is not None:\n        hits = search_episodes(index_path, search)\n        for hit in hits:\n            _emit(\n                f"  {hit.get(\'date\', \'?\')} {hit.get(\'slug\', \'?\')} — "\n                f"{hit.get(\'summary\', \'\')}",\n            )\n        _emit(f"episodes: {len(hits)} hit(s) for {search!r}.")\n    if not rebuild and search is None:\n        _emit("episodes: pass --rebuild and/or --search TAG.")\n    return 0\n\n\ndef cmd_metrics(target: Path) -> int:\n    """Emit the router / workflow KPIs (JSON + the one-line footer)."""\n    loaded = _require_state(target, "metrics")\n    if loaded is None:\n        return 1\n    config, backend = loaded\n    kpis = workflow_kpis(backend.data, target / config.sessions_dir)\n    _emit(json.dumps(kpis, indent=2, sort_keys=True))\n    _emit(kpi_footer(kpis))\n    return 0\n\n\ndef cmd_maintain(target: Path, *, compact: bool) -> int:\n    """Run the self-maintenance loop\'s report (and compaction when asked)."""\n    loaded = _require_state(target, "maintain")\n    if loaded is None:\n        return 1\n    config, backend = loaded\n    if compact:\n        if compaction_due(backend.data, dict(config.cadence or {})):\n            path = run_compaction(target, config, backend)\n            rel = path.relative_to(target) if path.is_relative_to(target) else path\n            _emit(f"maintain: compaction written -> {rel}")\n        else:\n            _emit("maintain: compaction not due.")\n    triggers = check_triggers(target, config, backend.data)\n    economy = economy_check(target, config)\n    ledger_path = target / config.docs_root / LEDGER_FILENAME\n    ledger_findings = check_ledger(ledger_path) if ledger_path.exists() else []\n    kpis = workflow_kpis(backend.data, target / config.sessions_dir)\n    _emit(\n        maintenance_report(\n            target,\n            config,\n            backend,\n            triggers=triggers,\n            economy_findings=list(economy.get("findings", [])),\n            ledger_findings=ledger_findings,\n            kpis=kpis,\n        ),\n    )\n    return 0\n\n\ndef cmd_review(\n    target: Path,\n    action: str,\n    slot: str | None,\n    *,\n    verdict: str,\n    reviewer: str,\n) -> int:\n    """Drive the independent-review seam: build payloads, record verdicts."""\n    if action == "doc":\n        _emit(seam_wiring_doc())\n        return 0\n    if slot is None:\n        _emit("review: a slot is required for build/confirm.")\n        return 2\n    loaded = _require_state(target, "review")\n    if loaded is None:\n        return 1\n    config, backend = loaded\n    if action == "build":\n        payload = build_review_payload(backend, slot)\n        if not payload:\n            _emit(f"review: slot {slot!r} is not provisional — nothing to review.")\n            return 1\n        path = write_review_payload(target, config, payload)\n        rel = path.relative_to(target) if path.is_relative_to(target) else path\n        _emit(f"review: payload written -> {rel}")\n        return 0\n    if action == "confirm":\n        if verdict not in ("pass", "fail"):\n            _emit("review: --verdict must be pass or fail.")\n            return 2\n        outcome = apply_review_verdict(\n            backend,\n            slot,\n            verdict=verdict,\n            reviewer=reviewer,\n        )\n        _emit(f"review: {slot} -> {outcome}.")\n        if outcome == "not-provisional":\n            _emit(\n                "review: nothing recorded — the slot is not provisional "\n                "(typo, already confirmed, or never answered).",\n            )\n            return 1\n        # The verdict is recorded → the payload is consumed. Remove it so the\n        # maintenance "awaiting a reviewer" count reflects reality.\n        if clear_review_payload(target, config, slot):\n            _emit(f"review: cleared consumed payload for {slot}.")\n        return 0\n    _emit(f"review: unknown action {action!r} (build | confirm | doc).")\n    return 2\n\n\ndef cmd_economy(\n    target: Path,\n    action: str,\n    *,\n    strict: bool,\n    apply: bool,\n    reviewed: bool,\n    bands: int,\n) -> int:\n    """Drive the context-economy engine: check, apply, simulate, recipe."""\n    config = load_config(target)\n    if action == "recipe":\n        _emit(calibration_recipe())\n        return 0\n    if action == "simulate":\n        result = run_search(default_calibration(), bands=bands)\n        _emit(str(result.get("why_it_won", "")))\n        winner = result.get("winner", {})\n        name = winner.get("name") if isinstance(winner, dict) else winner\n        _emit(f"economy: winner {name} (feasible: {result.get(\'feasible_count\')}).")\n        return 0\n    pass_records = (\n        target / config.docs_root / config.economy.get("pass_records_dir", "planning")\n    )\n    harvested = parse_harvest_tables(pass_records)\n    report = economy_check(\n        target,\n        config,\n        harvested=harvested,\n        harvest_exclude=harvest_sources(pass_records),\n    )\n    if action == "issue-body":\n        _emit(issue_body(report))\n        return 0\n    if action == "check":\n        census = report.get("census", {})\n        for name in sorted(census):\n            row = census[name]\n            _emit(\n                f"  class {name}: {row.get(\'files\', 0)} file(s), "\n                f"{row.get(\'words\', 0)} word(s)",\n            )\n        for gauge in report.get("gauges", []):\n            flag = "OVER" if gauge.get("over") else "ok"\n            _emit(f"  gauge {gauge[\'name\']}: {gauge[\'value\']}/{gauge[\'cap\']} [{flag}]")\n        findings = report.get("findings", [])\n        for finding in findings:\n            _emit(f"  [{finding.kind}] {finding.path}: {finding.message}")\n        for line in economy_actuate(target, config, report, apply=False):\n            _emit(f"  would-act: {line}")\n        debt = report.get("debt", 0)\n        threshold = int(config.economy.get("debt_threshold", 10))\n        _emit(f"economy: debt {debt} (threshold {threshold}).")\n        over = bool(findings) or debt >= threshold\n        return 1 if strict and over else 0\n    if action == "apply":\n        if apply:\n            backend = JsonStateBackend(_state_path(target, config))\n            if backend.data and not actuators_may_apply(backend.data):\n                _emit(\n                    "economy: refused — the mode/promotion policy does not "\n                    "permit actuators to apply (promotion_rights must be "\n                    "\'promote\'); dry-run only.",\n                )\n                return 1\n        lines = economy_actuate(\n            target,\n            config,\n            report,\n            apply=apply,\n            acknowledged=reviewed,\n        )\n        for line in lines:\n            _emit(f"  {line}")\n        if not apply:\n            _emit("economy: dry-run (pass --yes to act; maturity gates apply).")\n        return 0\n    _emit(\n        f"economy: unknown action {action!r} "\n        "(check | apply | simulate | recipe | issue-body).",\n    )\n    return 2\n\n\ndef cmd_adopt(\n    target: Path,\n    include_claude: bool,\n    wire_enforcement: bool = False,\n) -> int:\n    """Adopt the workflow into ``target``: init, plant the docs, stage the packs.\n\n    The one-step flow: ``init`` runs first (idempotent — config + state), so a\n    bare directory with nothing but the bootstrap file becomes a fully\n    substrate-governed project in this single command. ``wire_enforcement``\n    additionally turns on the live nag hook + the CI locked door.\n    """\n    rc = cmd_init(target)\n    if rc != 0:\n        return rc\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    lines = adopt(\n        target,\n        config,\n        backend,\n        kit_root=_kit_root(),\n        include_claude=include_claude,\n        wire_enforcement=wire_enforcement,\n    )\n    for line in lines:\n        _emit(f"adopt: {line}")\n    return 0\n\n\ndef cmd_contextpack(target: Path, index: Path | None) -> int:\n    """Generate agent context packs from the project index (or a manifest)."""\n    assert_safe_target(target, _kit_root())\n    config = load_config(target)\n    index_path = index if index is not None else target / "project.index.json"\n    if not index_path.exists():\n        _emit(f"contextpack: no index at {index_path} (run adopt first).")\n        return 1\n    try:\n        areas = load_pack_index(index_path)\n    except ValueError as exc:\n        _emit(f"contextpack: {exc}")\n        return 2\n    if not areas:\n        _emit("contextpack: index has no areas — nothing to generate.")\n        return 0\n    for path in generate_packs(target, config, areas):\n        rel = path.relative_to(target) if path.is_relative_to(target) else path\n        _emit(f"contextpack: wrote {rel}")\n    return 0\n\n\ndef cmd_session_start(target: Path) -> int:\n    """Print this session\'s orientation injection (the SessionStart composition)."""\n    loaded = _require_state(target, "session-start")\n    if loaded is None:\n        return 1\n    config, backend = loaded\n    _emit(compose_orientation(target, config, backend))\n    return 0\n\n\ndef cmd_session_close(target: Path) -> int:\n    """Run the session-close ritual: mine, index, advise, and report KPIs.\n\n    Mines the session logs into the reflection buffer, rebuilds the episodic\n    index, prints the stop-check advisories, and ends with the KPI footer —\n    the engine analog of the one-idea / previous-session-review enders.\n    """\n    loaded = _require_state(target, "session-close")\n    if loaded is None:\n        return 1\n    config, _ = loaded\n    rc = cmd_reflect(target, add=None, evidence="", tags="", mine=True)\n    if rc != 0:\n        return rc\n    index_path = target / config.state_dir / EPISODIC_INDEX_FILENAME\n    entries = rebuild_episodic_index(target / config.sessions_dir, index_path)\n    _emit(f"session-close: indexed {len(entries)} session(s).")\n    # Re-read state: the mine above stamped reflection_buffer.last_mined, and\n    # a pre-mine snapshot would re-advise the mine it just ran.\n    backend = JsonStateBackend(_state_path(target, config))\n    for line in evaluate_stop(target, config, backend):\n        _emit(f"session-close: [advisory] {line}")\n    kpis = workflow_kpis(backend.data, target / config.sessions_dir)\n    _emit(kpi_footer(kpis))\n    return 0\n\n\ndef cmd_ledger(\n    target: Path,\n    *,\n    title: str,\n    verdict: str,\n    why: str,\n    provenance: str,\n    supersedes: str | None,\n) -> int:\n    """Append a decision to the [D-NNNN] ledger (created on first use)."""\n    assert_safe_target(target, _kit_root())\n    config = load_config(target)\n    path = target / config.docs_root / LEDGER_FILENAME\n    entry = append_decision(\n        path,\n        title=title,\n        verdict=verdict,\n        why=why,\n        provenance=provenance,\n        supersedes=supersedes,\n    )\n    _emit(f"ledger: recorded {entry[\'id\']} — {title}")\n    if supersedes:\n        _emit(f"ledger: {supersedes} stamped superseded-by {entry[\'id\']}.")\n    return 0\n\n\ndef _simulate_mode_asserts(\n    mode: str,\n    data: dict,\n    graduated: bool,\n    n: int,\n) -> str | None:\n    """Return the per-mode behavior violation, or None when behavior held.\n\n    The behavior-assert half of the simulation: observe must never\n    auto-graduate (it proposes), guided/active must graduate once the quiet\n    streak is long enough.\n    """\n    quiet_needed = 3\n    if mode == "observe":\n        if graduated or data.get("stage") != "integration":\n            return "observe mode auto-graduated (must only propose)"\n        if n > quiet_needed and not data.get("graduation_proposed"):\n            return "observe mode never proposed graduation"\n        return None\n    if n > quiet_needed and not graduated:\n        return f"{mode} mode failed to graduate after the quiet streak"\n    return None\n\n\ndef cmd_simulate(n: int, mode: str = "guided") -> int:\n    """Init into a temp dir and drive ``n`` interview sessions; verify behavior.\n\n    Session 1 supplies confirmed answers for every critical slot; later sessions\n    supply none. Asserts the critical slots fill and that the run behaves\n    per ``mode``: guided/active graduate integration -> steady once quiet;\n    observe only ever *proposes* graduation.\n    """\n    with tempfile.TemporaryDirectory(prefix="substrate-sim-") as tmp:\n        target = Path(tmp)\n        rc = cmd_init(target)\n        if rc != 0:\n            return rc\n        state_path = _state_path(target, load_config(target))\n        if mode != "guided":\n            rc = cmd_mode(target, mode)\n            if rc != 0:\n                return rc\n        crit = critical_slots()\n        answers = {slot: f"value-for-{slot}" for slot in crit}\n        graduated = False\n        for index in range(n):\n            backend = JsonStateBackend(state_path)\n            result = run_session(backend, answers if index == 0 else {})\n            graduated = graduated or result["graduated"]\n        data = JsonStateBackend(state_path).data\n        missing = [s for s in crit if data.get("slots", {}).get(s) != "filled"]\n        if missing:\n            _emit(f"simulate: FAILED — critical slots unfilled: {missing}")\n            return 1\n        violation = _simulate_mode_asserts(mode, data, graduated, n)\n        if violation:\n            _emit(f"simulate: FAILED — {violation}")\n            return 1\n        _emit(\n            f"simulate: OK — {n} session(s), {len(crit)} critical slots filled, "\n            f"mode={mode}, stage={data.get(\'stage\')} (graduated={graduated}).",\n        )\n    return 0\n\n\ndef build_parser() -> argparse.ArgumentParser:\n    """Construct the bootstrap argument parser."""\n    parser = argparse.ArgumentParser(prog="bootstrap", description="substrate-kit")\n    parser.add_argument(\n        "--simulate",\n        type=int,\n        metavar="N",\n        help="run N synthetic sessions in a temp dir, then exit",\n    )\n    parser.add_argument(\n        "--mode",\n        default="guided",\n        choices=("observe", "guided", "active"),\n        help="integration mode for --simulate (behavior asserts differ per mode)",\n    )\n    sub = parser.add_subparsers(dest="command")\n    for name, helptext in (\n        ("init", "initialise a project"),\n        ("status", "show install state"),\n        ("ask", "list pending interview questions"),\n        ("triggers", "scan for fired triggers / mandatory questions"),\n        ("metrics", "emit the router + workflow KPIs"),\n        ("session-start", "print this session\'s orientation injection"),\n        ("session-close", "mine reflections, index the session, report KPIs"),\n    ):\n        child = sub.add_parser(name, help=helptext)\n        child.add_argument("--target", type=Path, default=Path.cwd())\n    adopt_p = sub.add_parser("adopt", help="plant the workflow docs + stage the packs")\n    adopt_p.add_argument(\n        "--include-claude",\n        action="store_true",\n        help="also write .claude/CLAUDE.md + .claude/settings.json (skip-if-exists)",\n    )\n    adopt_p.add_argument(\n        "--wire-enforcement",\n        action="store_true",\n        help=(\n            "turn on the forcing functions: the live nag hook (implies "\n            "--include-claude) + a live CI gate that holds the merge red until "\n            "the session journal is written"\n        ),\n    )\n    adopt_p.add_argument("--target", type=Path, default=Path.cwd())\n    contextpack = sub.add_parser(\n        "contextpack",\n        help="generate agent context packs from the index",\n    )\n    contextpack.add_argument(\n        "--index",\n        type=Path,\n        default=None,\n        help="index or manifest path (default: <target>/project.index.json)",\n    )\n    contextpack.add_argument("--target", type=Path, default=Path.cwd())\n    render_p = sub.add_parser("render", help="render content docs from filled slots")\n    render_p.add_argument(\n        "--live",\n        action="store_true",\n        help="fill remaining placeholders in the PLANTED docs in place",\n    )\n    render_p.add_argument("--target", type=Path, default=Path.cwd())\n    answer = sub.add_parser("answer", help="record a user answer for a slot")\n    answer.add_argument("slot")\n    answer.add_argument("value", nargs="+", help="the answer text")\n    answer.add_argument("--target", type=Path, default=Path.cwd())\n    confirm = sub.add_parser("confirm", help="confirm a provisional slot")\n    confirm.add_argument("slot")\n    confirm.add_argument("--target", type=Path, default=Path.cwd())\n    reflect = sub.add_parser("reflect", help="list/add/mine the reflection buffer")\n    reflect.add_argument("--add", metavar="LESSON", default=None)\n    reflect.add_argument("--evidence", default="")\n    reflect.add_argument("--tags", default="", help="comma-separated tags")\n    reflect.add_argument("--mine", action="store_true")\n    reflect.add_argument("--target", type=Path, default=Path.cwd())\n    episodes = sub.add_parser("episodes", help="rebuild/search the episodic index")\n    episodes.add_argument("--rebuild", action="store_true")\n    episodes.add_argument("--search", metavar="TAG", default=None)\n    episodes.add_argument("--target", type=Path, default=Path.cwd())\n    maintain = sub.add_parser("maintain", help="run the self-maintenance report")\n    maintain.add_argument("--compact", action="store_true")\n    maintain.add_argument("--target", type=Path, default=Path.cwd())\n    review = sub.add_parser("review", help="drive the independent-review seam")\n    review.add_argument("action", choices=("build", "confirm", "doc"))\n    review.add_argument("slot", nargs="?", default=None)\n    review.add_argument("--verdict", default="", help="pass | fail (for confirm)")\n    review.add_argument("--reviewer", default="external")\n    review.add_argument("--target", type=Path, default=Path.cwd())\n    economy = sub.add_parser("economy", help="run the context-economy engine")\n    economy.add_argument(\n        "action",\n        choices=("check", "apply", "simulate", "recipe", "issue-body"),\n    )\n    economy.add_argument("--strict", action="store_true")\n    economy.add_argument("--yes", action="store_true", help="really act (apply)")\n    economy.add_argument(\n        "--reviewed",\n        action="store_true",\n        help="acknowledge the human review a \'gated\' maturity first prune needs",\n    )\n    economy.add_argument("--bands", type=int, default=24)\n    economy.add_argument("--target", type=Path, default=Path.cwd())\n    ledger = sub.add_parser("ledger", help="append a [D-NNNN] decision")\n    ledger.add_argument("--title", required=True)\n    ledger.add_argument("--verdict", required=True)\n    ledger.add_argument("--why", required=True)\n    ledger.add_argument("--provenance", required=True)\n    ledger.add_argument("--supersedes", default=None)\n    ledger.add_argument("--target", type=Path, default=Path.cwd())\n    mode = sub.add_parser("mode", help="set the integration mode")\n    mode.add_argument("name")\n    mode.add_argument("--target", type=Path, default=Path.cwd())\n    stance = sub.add_parser("stance", help="show or set the task stance")\n    stance.add_argument("name", nargs="?", default=None)\n    stance.add_argument("--target", type=Path, default=Path.cwd())\n    skills = sub.add_parser("skills", help="list or --build the skill pack")\n    skills.add_argument(\n        "--build",\n        action="store_true",\n        help="emit SKILL.md files into <state_dir>/skills/",\n    )\n    skills.add_argument("--target", type=Path, default=Path.cwd())\n    agents = sub.add_parser("agents", help="list or --build the persona pack")\n    agents.add_argument(\n        "--build",\n        action="store_true",\n        help="emit agent .md files into <state_dir>/agents/",\n    )\n    agents.add_argument("--target", type=Path, default=Path.cwd())\n    hooks = sub.add_parser("hooks", help="show or --build the hook wiring")\n    hooks.add_argument(\n        "--build",\n        action="store_true",\n        help="emit the PreToolUse settings snippet into <state_dir>/hooks/",\n    )\n    hooks.add_argument("--target", type=Path, default=Path.cwd())\n    hook = sub.add_parser("hook", help="run a hook check (e.g. `hook pretooluse`)")\n    hook.add_argument("event")\n    hook.add_argument("--target", type=Path, default=Path.cwd())\n    check = sub.add_parser("check", help="run the doc + session-log hygiene checks")\n    check.add_argument("--target", type=Path, default=Path.cwd())\n    check.add_argument("--strict", action="store_true", help="exit 1 if any violation")\n    check.add_argument(\n        "--require-session-log",\n        action="store_true",\n        help="fail (not just advise) when the session log is missing — the CI gate mode",\n    )\n    return parser\n\n\ndef main(argv: list[str] | None = None) -> int:\n    """Run the bootstrap CLI; return a process exit code."""\n    parser = build_parser()\n    args = parser.parse_args(argv)\n    try:\n        if args.simulate is not None:\n            return cmd_simulate(args.simulate, args.mode)\n        if args.command == "init":\n            return cmd_init(args.target)\n        if args.command == "status":\n            return cmd_status(args.target)\n        if args.command == "ask":\n            return cmd_ask(args.target)\n        if args.command == "render":\n            return cmd_render(args.target, live=args.live)\n        if args.command == "mode":\n            return cmd_mode(args.target, args.name)\n        if args.command == "stance":\n            return cmd_stance(args.target, args.name)\n        if args.command == "skills":\n            return cmd_skills(args.target, args.build)\n        if args.command == "agents":\n            return cmd_agents(args.target, args.build)\n        if args.command == "hooks":\n            return cmd_hooks(args.target, args.build)\n        if args.command == "hook":\n            return cmd_hook(args.target, args.event)\n        if args.command == "check":\n            return cmd_check(\n                args.target,\n                args.strict,\n                require_session_log=args.require_session_log,\n            )\n        if args.command == "answer":\n            return cmd_answer(args.target, args.slot, " ".join(args.value))\n        if args.command == "confirm":\n            return cmd_confirm(args.target, args.slot)\n        if args.command == "triggers":\n            return cmd_triggers(args.target)\n        if args.command == "reflect":\n            return cmd_reflect(\n                args.target,\n                add=args.add,\n                evidence=args.evidence,\n                tags=args.tags,\n                mine=args.mine,\n            )\n        if args.command == "episodes":\n            return cmd_episodes(args.target, rebuild=args.rebuild, search=args.search)\n        if args.command == "metrics":\n            return cmd_metrics(args.target)\n        if args.command == "maintain":\n            return cmd_maintain(args.target, compact=args.compact)\n        if args.command == "review":\n            return cmd_review(\n                args.target,\n                args.action,\n                args.slot,\n                verdict=args.verdict,\n                reviewer=args.reviewer,\n            )\n        if args.command == "economy":\n            return cmd_economy(\n                args.target,\n                args.action,\n                strict=args.strict,\n                apply=args.yes,\n                reviewed=args.reviewed,\n                bands=args.bands,\n            )\n        if args.command == "adopt":\n            return cmd_adopt(\n                args.target,\n                args.include_claude,\n                wire_enforcement=args.wire_enforcement,\n            )\n        if args.command == "contextpack":\n            return cmd_contextpack(args.target, args.index)\n        if args.command == "session-start":\n            return cmd_session_start(args.target)\n        if args.command == "session-close":\n            return cmd_session_close(args.target)\n        if args.command == "ledger":\n            return cmd_ledger(\n                args.target,\n                title=args.title,\n                verdict=args.verdict,\n                why=args.why,\n                provenance=args.provenance,\n                supersedes=args.supersedes,\n            )\n    except UnsafeTargetError as exc:\n        _emit(f"refused: {exc}")\n        return 2\n    parser.print_help()\n    return 0\n',
}

_TEMPLATES = {
    'AGENT_ORIENTATION.md.tmpl': '# ${project_name} — agent orientation & reading order\n\n> **Status:** `reference`\n>\n> Generated by substrate-kit. The task reading-router: start here to find which\n> docs a given task needs. **NOT SOURCE OF TRUTH** — the binding contracts win.\n\n## Start every session\n\n1. `.claude/CLAUDE.md` — the working agreement.\n2. `docs/current-state.md` — the living status ledger.\n3. This file — task-specific reading routes.\n\n## Binding contracts\n\n- **Architecture / layering:** ${architecture_layers}\n- **Ownership** (who owns each write path): ${ownership_model}\n- **Mutation seam** (how writes are gated): ${mutation_seam}\n\n## Where things live\n\nDocumentation root(s): ${doc_roots}\n\nThe planted doc set (this router reaches every live doc — keep it that way):\n`docs/architecture.md` · `docs/ownership.md` · `docs/runtime_contracts.md` ·\n`docs/collaboration-model.md` · `docs/helper-policy.md` ·\n`docs/repo-navigation-map.md` · `docs/ai-project-workflow.md` ·\n`docs/owner-profile.md` · `docs/current-state.md` · `docs/decisions.md` ·\n`docs/question-router.md` · `docs/ideas/README.md` — plus the root\n`CONSTITUTION.md` (the working agreement) and `.session-journal.md`.\n\n## Verifying any change\n\n```\n${verify_command}\n```\n',
    'CLAUDE.md.tmpl': '# ${project_name} — agent working agreement\n\n> **Status:** `binding`\n>\n> Generated by substrate-kit from the staged interview. **NOT SOURCE OF TRUTH**\n> for code — source files always win. Re-render (`bootstrap render`) after the\n> interview fills more slots.\n\n## What this project is\n\n${project_name} is built in ${primary_language}.\n\n## Orientation — read first, in order\n\n1. This file — the working agreement.\n2. `docs/current-state.md` — what is true right now.\n3. `docs/AGENT_ORIENTATION.md` — the task-specific reading router.\n\n## Architecture — layers & import rules\n\n${architecture_layers}\n\n## Verifying a change\n\nRun before every push:\n\n```\n${verify_command}\n```\n\n## How the maintainer works\n\n${owner_profile}\n\n## Workflow adoption\n\nCurrent adoption pace for the substrate workflow: **${integration_mode}**.\n',
    'CONSTITUTION.md.tmpl': "# ${project_name} — constitution\n\n> **Status:** `binding`\n>\n> Generated by substrate-kit. The working agreement + autonomy rails. **NOT\n> SOURCE OF TRUTH** for code — source files always win. Rules state their\n> **current value only**; provenance lives in `docs/decisions.md` as [D-NNNN]\n> links and is never narrated inline.\n\n## Working agreement\n\n- **The goal comes first.** Achieve the session's goal end-to-end; don't ship\n  the smallest safe slice.\n- **Session prompts are guidance, not orders.** Weigh every prompt (and every\n  cross-agent report) against source and the binding docs before acting.\n- **Approved plan = execute.** Once a plan is approved, finish it in the same\n  session, with the planning context still loaded — no re-confirming.\n- **Understand-and-reflect.** The owner often hands over a rough fragment, not\n  a full spec — and sometimes doesn't know yet if the idea is even possible.\n  Before substantive work, restate the fuller picture built from the ask —\n  the specs it implied but didn't state, and, when feasibility is uncertain,\n  the possibility space — inline in the first substantive response, never as\n  a separate blocking question. Two payoffs, not one: it catches a misread\n  before work happens, and the filled-in picture is itself new material the\n  owner reasons against and redirects.\n- When a doc and a source file disagree: ${drift_resolution}\n\n## Autonomy rails — act vs. ask\n\n- **Act** on contained, reversible, verifiable changes — including a\n  root-cause fix discovered mid-task.\n- **Ask** before anything irreversible (data loss, external publish),\n  large / cross-cutting (architectural), or when the goal itself is\n  genuinely ambiguous. No live owner to ask? Record the question in\n  `docs/question-router.md` instead of skipping it or guessing.\n\n## Changing the rules — propose, don't apply\n\n- A binding rule in this file changes by **proposal**, never by silent edit:\n  record the decision in `docs/decisions.md`, cite it here as its [D-NNNN]\n  id, and let the owner (or the review ritual) confirm before the rule text\n  changes.\n- Every rule change ships with its provenance id. This file carries **no\n  history** — the ledger does; superseded rules are looked up there.\n\n## Rails specific to ${project_name}\n\n(Hand-filled: the project's own hard rules, one bullet each, each citing its\n[D-NNNN]. Keep the whole hand-filled file under 150 lines.)\n",
    'ai-project-workflow.md.tmpl': "# ${project_name} — AI project workflow\n\n> **Status:** `reference`\n>\n> Generated by substrate-kit. The multi-agent pipeline: how ideas become work\n> and how sessions run. **NOT SOURCE OF TRUTH** — the binding contracts win.\n\n## Idea lifecycle\n\n```\ncaptured -> classified -> planned -> built -> verified\n```\n\nEvery idea ends implemented, planned, in discussion, or explicitly rejected —\nnever orphaned. Backlog + routing: `docs/ideas/README.md`.\n\n## Session workflow\n\n```\norient -> claim -> born-red card -> build -> verify -> close\n```\n\n1. **Orient** — working agreement, current state, task-specific reading route.\n2. **Claim** — declare your lane so parallel sessions don't collide.\n3. **Born-red card** — open the session record first, marked in-progress, so\n   the work is visible while it is still incomplete.\n4. **Build** — the goal, end-to-end.\n5. **Verify** — run `${verify_command}` before shipping.\n6. **Close** — flip the card complete; log the session, groom one idea, hand\n   off.\n\n## Handoff template\n\n(What the next session needs, four lines: state of the work · what is\nverified · what is still open · the first next step.)\n\n## Adoption pace\n\nCurrent substrate-workflow adoption: **${integration_mode}**.\n",
    'architecture.md.tmpl': '# ${project_name} — architecture\n\n> **Status:** `binding`\n>\n> Generated by substrate-kit. Layering, invariants, and decomposition rules.\n> **NOT SOURCE OF TRUTH** for code — source files always win.\n\n## Layers & import rules\n\n${architecture_layers}\n\n| Layer | May import | Must NOT import |\n|---|---|---|\n| (one row per layer, expanded from the summary above) | | |\n\n## Invariants\n\n(The rules that must survive every refactor — write each one as a testable\nstatement, and name the check that enforces it where one exists.)\n\n## Namespace protection — two mechanisms, both required\n\nTwo separate mechanisms guard the namespace, and they catch different\nfailure classes:\n\n1. **A registry for runtime string identities** — event names, command\n   names, settings keys, and any other string that selects behavior at\n   runtime. Collisions here are invisible to static analysis.\n2. **A static AST pass for Python symbol shadowing** — a later top-level\n   `def` / `class` with the same name silently shadows the earlier one, and\n   no import fails.\n\nNeither mechanism subsumes the other. The registry cannot see symbol\nshadowing; the AST pass cannot see string-keyed dispatch. Do not delete one\nbelieving the other covers it.\n\n## Verifying a change\n\n```\n${verify_command}\n```\n',
    'collaboration-model.md.tmpl': "# ${project_name} — collaboration model\n\n> **Status:** `binding`\n>\n> Generated by substrate-kit. How the owner and agents work together. **NOT\n> SOURCE OF TRUTH** for code — source files always win.\n\n## The model\n\n- **Goal first.** The owner designs and directs; agents build. Each session\n  achieves its goal end-to-end — not the smallest safe slice.\n- **Session prompts are guidance, not orders.** Weigh every prompt (and every\n  cross-agent report) against source and the binding docs before acting; a\n  prompt is one input, never a command list.\n- **Approved plan = execute.** Once a plan is approved, finish it in the same\n  session, with the planning context still loaded — code, verify, ship —\n  without re-confirming.\n\n## Act vs. ask\n\n- **Act** on contained, reversible, verifiable changes — including a\n  root-cause fix discovered mid-task (that is expected, not scope creep).\n- **Ask** when the change is irreversible (data loss / external publish),\n  large and cross-cutting (architectural), or the goal itself is genuinely\n  ambiguous.\n\n## Friction → guard\n\nAnything that interrupts a session's workflow — a stale file, a checker that\nlied, a footgun — is converted into the **cheapest enforcing prevention**\nbefore the session ends: checker / CI / test first, then hook, then written\nrule. Enforce, don't exhort.\n\n## Guiding questions\n\nDuring exploratory / brainstorming work, surface the single most useful\nquestion about the owner's idea that the agent genuinely cannot derive\nitself — rare and selective, never during routine execution, and only when\nthe answer would actually matter and be actionable. A big or vague idea\nearns a dedicated research pass or its own session before being answered\nfrom memory alone.\n\n## Drift & staleness\n\n- When a doc and a source file disagree: ${drift_resolution}\n- Staleness review cadence: ${staleness_review}\n",
    'current-state.md.tmpl': '# ${project_name} — Current State\n\n> **Status:** `living-ledger`\n>\n> Generated by substrate-kit. **Living status ledger.** Source code and merged\n> work always win over this file. Read it second (right after the working\n> agreement) and keep it current as the project moves.\n\n## Stability baseline\n\n(Describe the accepted-stable baseline once established — what is known-good and\nshould not be re-audited without a reported regression.)\n\n## In flight\n\n(Verify against live source control — this section is a dated snapshot.)\n\n## Recently shipped (newest first)\n\n(Merged work only, newest first.)\n\n## Review rhythm\n\n${review_ritual}\n',
    'decisions.md.tmpl': '# ${project_name} — decisions\n\n> **Status:** `living-ledger`\n>\n> Generated by substrate-kit. Append-only decision ledger — entries are\n> superseded, never deleted. Rule docs cite entries as bare [D-NNNN] ids;\n> this file holds the provenance so rules never narrate it inline.\n\n<!-- Grammar: ## [D-NNNN] <title> / - status: decided|superseded|retired / - date: YYYY-MM-DD / - supersedes: D-NNNN (opt) / - superseded-by: D-NNNN (opt) / - verdict: <one line> / - why: <2-3 lines> / - provenance: <ref> -->\n\n## [D-0001] Adopt the substrate-kit workflow\n\n- status: decided\n- date:\n- verdict: ${project_name} runs on the substrate-kit agent workflow.\n- why: A repo-resident working agreement, decision ledger, and session\n  discipline let agents work correctly with little steering; adopting the\n  kit starts ${project_name} governed instead of accreting rules ad hoc.\n- provenance: substrate-kit adoption interview\n',
    'helper-policy.md.tmpl': '# ${project_name} — helper policy\n\n> **Status:** `binding`\n>\n> Generated by substrate-kit. When to create / move / promote a helper —\n> read this **before** adding a utility function anywhere. **NOT SOURCE OF\n> TRUTH** for code — source files always win.\n\n## Rules\n\n1. **One source of truth.** A behavior lives in exactly one function. Never\n   copy a helper into a second module "for convenience" — import it, or move\n   it (rule 2).\n2. **Shared helpers live below both consumers.** A helper needed by two\n   layers goes in the shared layer *below* both — never in either consumer\n   layer, and never duplicated into each.\n3. **Exact-name guard.** Before defining a new function, grep for\n   `def <exact_name>` in the target module and its siblings (plus the 1–2\n   nearest concept synonyms). A later same-name `def` silently shadows the\n   earlier one — no import fails, no warning fires.\n4. **Promote on second use.** The moment a private helper is wanted by a\n   second module, promote it to the shared layer — don\'t copy it.\n\n## Where helpers go in ${project_name}\n\n(Hand-filled: the concrete shared-layer path(s) for this repo, lowest layer\nfirst, with one line on what belongs in each.)\n',
    'ideas-README.md.tmpl': '# ${project_name} — idea backlog & lifecycle\n\n> **Status:** `ideas`\n>\n> Generated by substrate-kit. Capture ideas here so they live in the repo, not in\n> chat. Nothing here is approved until it graduates. A **conveyor, not a graveyard**:\n> every idea ends implemented, on a roadmap, in discussion, or explicitly rejected.\n\n## Lifecycle\n\n```\n(1) INTAKE   capture the idea (raw -> captured)\n(2) MAP      name the owning area, rough size, rough risk\n(3) ROUTE    -> quick-win | structured plan | discuss-first (question router)\n(4) GROOM    pull one routable idea forward each session\n(5) OUTCOME  implemented | on a roadmap | in discussion | rejected\n```\n\n## Backlog\n\n(Captured ideas, each with a state and a next destination — none left at `raw`.)\n',
    'owner-profile.md.tmpl': "# ${project_name} — owner working profile\n\n> **Status:** `owner-guidance`\n>\n> Generated by substrate-kit. Captures the owner's **working style** so\n> agents collaborate well — never personal data. The person is not shipped\n> with the kit.\n\n## How the owner works\n\n${owner_profile}\n\n## Review ritual\n\n${review_ritual}\n\n## Privacy note\n\nThis doc records working style only: communication preferences, review\ncadence, decision boundaries, autonomy expectations. No contact details, no\npersonal history, nothing that identifies the person beyond their role on\n${project_name}. When in doubt, leave it out.\n",
    'ownership.md.tmpl': "# ${project_name} — ownership\n\n> **Status:** `binding`\n>\n> Generated by substrate-kit. Which area / service / pipeline owns each\n> table, event, and write path. **NOT SOURCE OF TRUTH** for code — source\n> files always win.\n\n> **Steady state:** this doc's table is **generated** from store / manifest\n> specs where those exist — a projection, not hand-prose. This skeleton is\n> the interim hand-maintained form until that projection lands.\n\n## Ownership model\n\n${ownership_model}\n\n## Ownership table\n\n| Area | Owner (module / service) | Writes it owns | Notes |\n|---|---|---|---|\n| (one row per owned area) | | | |\n\n## New areas\n\n${new_area_ownership}\n",
    'question-router.md.tmpl': '# ${project_name} — maintainer question router\n\n> **Status:** `owner-guidance`\n>\n> Generated by substrate-kit. Append-only `## Q-NNNN` blocks capture owner-intent\n> decisions and open questions. The interview writes here; confirmed answers route\n> into the durable docs. **Append only** (next free Q-number) — never rewrite history.\n> Any session may append a block, not only the interview — including an unattended\n> run that hits a genuinely useful, non-derivable question with no live owner to ask.\n\n## Block format\n\n```\n## Q-0001\n- **Area / Type / Priority / Status:** ...\n- **Question:** ...\n- **Why agents need this:** ...\n- **Options:** ...\n- **Safe default:** ...\n- **Maintainer answer:** (verbatim)\n- **Routing result:** (which doc / slot the answer landed in)\n```\n\n## Open questions\n\n(Unanswered Q-blocks live here until the maintainer decides; a blocking one gates\ngraduation.)\n',
    'repo-navigation-map.md.tmpl': '# ${project_name} — repo navigation map\n\n> **Status:** `reference`\n>\n> Generated by substrate-kit. Where things live; where new code goes. **NOT\n> SOURCE OF TRUTH** — the tree itself wins.\n\n## Where things live\n\n| Path | What lives there | New code goes here when… |\n|---|---|---|\n| (one row per top-level area) | | |\n\n## Documentation roots\n\n${doc_roots}\n\n## Placement rule of thumb\n\nBefore creating a new file, find the row above that matches it; if no row\nmatches, the map is stale — extend the table in the same change.\n',
    'runtime_contracts.md.tmpl': '# ${project_name} — runtime contracts\n\n> **Status:** `binding`\n>\n> Generated by substrate-kit. Lifecycle guarantees and failure modes. **NOT\n> SOURCE OF TRUTH** for code — source files always win.\n\n## Lifecycle guarantees\n\n### Startup\n\n(What is guaranteed initialized before work begins, and in what order.)\n\n### Steady state\n\n(The invariants that hold while the system is running — connection health,\nqueue bounds, cache coherence.)\n\n### Shutdown\n\n(What is flushed / persisted / cancelled on the way down, and in what order.)\n\n## Mutation seam\n\n${mutation_seam}\n\n## Failure modes\n\n(For each subsystem: what failing looks like from the outside, the blast\nradius, and the recovery step. One subsection per subsystem.)\n',
    'session-journal.md.tmpl': "# ${project_name} — session journal (process memory)\n\n> **Status:** `reference`\n>\n> Generated by substrate-kit. Cross-session working memory — a **guidebook, not a\n> log**. Per-session logs live in `.sessions/<date>-<slug>.md` (newest first);\n> older history archives out. Keep THIS file lean.\n\n## ⚡ Quick reference\n\n(Boot / run-checks / common-recovery commands for ${project_name}.)\n\n## Environment & boot runbook\n\n(How to bring a working dev/test environment up.)\n\n## Recurring problems + fixes\n\n(Known traps and their resolutions — so the next session doesn't re-discover them.)\n\n## Past mistakes to avoid\n\n(Things that went wrong before; don't repeat them.)\n\n## Candidate rules (not yet promoted)\n\n(Proposed working-agreement rules awaiting owner review.)\n",
}

if __name__ == "__main__":
    raise SystemExit(main())
