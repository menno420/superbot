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

from __future__ import annotations

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
