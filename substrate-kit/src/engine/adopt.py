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

Unfilled ``${slot}`` placeholders survive rendering visibly, so a
half-onboarded adoption shows its gaps instead of going silently blank. The
guardrail runs first: the kit refuses to adopt into its own tree. Pure
stdlib; every write goes through ``atomic_write_text``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from engine.agents.agents import AGENTS, agent_document, agent_relpath
from engine.contextpack import pack_index_skeleton
from engine.hooks.settings import full_settings_template, hooks_fill_table
from engine.lib.atomicio import atomic_write_text
from engine.lib.config import Config
from engine.lib.guardrail import assert_safe_target
from engine.render import build_context, load_templates, render
from engine.skills.skills import SKILLS, skill_document, skill_relpath

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
    "answer them so the docs re-render filled (`bootstrap render`), and set "
    "the integration mode with `bootstrap mode <observe|guided|active>`."
)


def _adopt_dest(relpath: str, config: Config) -> str:
    """Remap the plan's ``docs/`` prefix onto the host's configured docs root."""
    prefix = "docs/"
    if relpath.startswith(prefix) and config.docs_root != "docs":
        return f"{config.docs_root}/{relpath[len(prefix):]}"
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


def adopt(
    root: Path,
    config: Config,
    backend: Any,
    *,
    kit_root: Path,
    include_claude: bool = False,
) -> list[str]:
    """Adopt the substrate workflow into ``root``; return the report lines.

    Steps (all idempotent): (0) guardrail — refuse the kit's own tree;
    (1) plant every ``ADOPT_PLAN`` doc rendered from the current slots,
    skip-if-exists; (2) plant ``<sessions_dir>/README.md``; (3) plant the
    ``project.index.json`` skeleton; (4) stage the ``.claude`` material
    (CLAUDE.md, skills, personas, hook settings + fill-table README) under
    ``<state_dir>``; (5) stage the CI example; (6) with ``include_claude``,
    additionally write ``.claude/CLAUDE.md`` + ``.claude/settings.json``
    if absent; (7) close with the next-steps line.
    """
    assert_safe_target(root, kit_root)
    templates = load_templates()
    context = build_context(backend.data)
    report: list[str] = []

    # (1) Plant the live docs — never clobber; unfilled ${slots} stay visible.
    for template_name, plan_rel in ADOPT_PLAN:
        rel = _adopt_dest(plan_rel, config)
        text = render(templates[template_name], context)
        if template_name == "decisions.md.tmpl":
            # The example D-0001 records THIS adoption — stamp the real date so
            # the planted ledger is check_ledger-clean from its first commit.
            text = text.replace("- date:\n", f"- date: {date.today().isoformat()}\n")
        _adopt_plant(root / rel, rel, text, report)

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
    claude_doc = render(templates["CLAUDE.md.tmpl"], context)
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
    settings_text = full_settings_template(config)
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

    # (7) Point the adopter at the interview loop.
    report.append(_ADOPT_NEXT_STEPS)
    return report
