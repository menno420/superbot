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
    },
    {
        "id": "Q-002",
        "slot": "project_name",
        "audience": "user",
        "prompt": "What is this project called?",
        "routing": "templates/CLAUDE.md:project_name",
        "priority": "high",
        "critical": True,
    },
    {
        "id": "Q-003",
        "slot": "primary_language",
        "audience": "user",
        "prompt": "Primary language / runtime (e.g. Python 3.10, TypeScript)?",
        "routing": "templates/CLAUDE.md:language",
        "priority": "high",
        "critical": True,
    },
    {
        "id": "Q-004",
        "slot": "architecture_layers",
        "audience": "user",
        "prompt": "What are the top-level layers and their import rules?",
        "routing": "templates/architecture.md:layers",
        "priority": "high",
        "critical": True,
    },
    {
        "id": "Q-005",
        "slot": "verify_command",
        "audience": "user",
        "prompt": "One command that proves a change is good (tests + lint)?",
        "routing": "templates/CLAUDE.md:verify_command",
        "priority": "high",
        "critical": True,
    },
    {
        "id": "Q-006",
        "slot": "ownership_model",
        "audience": "self",
        "prompt": "Which component owns each data store / write path?",
        "routing": "templates/ownership.md:owners",
        "priority": "normal",
        "critical": False,
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
]
