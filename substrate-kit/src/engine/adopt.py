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

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

from engine.agents.agents import AGENTS, agent_document, agent_relpath
from engine.contextpack import pack_index_skeleton
from engine.derive import derive_slots, record_derived_slots
from engine.hooks.settings import full_settings_template, hooks_fill_table
from engine.lib.atomicio import atomic_write_text
from engine.lib.config import Config
from engine.lib.guardrail import assert_safe_target
from engine.render import build_context, find_placeholders, load_templates, render
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
