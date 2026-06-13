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

from __future__ import annotations

from engine.stances.stances import COMMENT, EDIT, READ, RUN, action_allowed

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
