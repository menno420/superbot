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

from __future__ import annotations

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
