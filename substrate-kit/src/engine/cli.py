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

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

from engine.adopt import adopt
from engine.agents.agents import AGENTS, agent_document, agent_relpath
from engine.checks.check_docs import run_doc_checks
from engine.checks.check_namespace import check_namespace
from engine.checks.check_orientation_budget import check_orientation_budget
from engine.checks.check_seam_authority import check_seam_authority
from engine.checks.check_session_log import check_log, latest_session_log
from engine.contextpack import generate_packs, load_pack_index
from engine.economy.engine import economy_actuate, economy_check, issue_body
from engine.economy.harvest import parse_harvest_tables
from engine.economy.simulator import calibration_recipe, default_calibration, run_search
from engine.hooks.post_edit import evaluate_edit
from engine.hooks.session_start import compose_orientation
from engine.hooks.settings import full_settings_template, hooks_fill_table
from engine.hooks.stance_guard import evaluate_tool, settings_snippet, tool_from_payload
from engine.hooks.stop_check import evaluate_stop
from engine.interview.interview import (
    confirm_slot,
    critical_slots,
    pending_questions,
    record_answer,
    run_session,
    session_questions,
)
from engine.interview.question_bank import QUESTIONS
from engine.ledger import LEDGER_FILENAME, append_decision, check_ledger
from engine.ledger import check_stamp_discipline as ledger_stamp_check
from engine.lib.atomicio import atomic_write_text
from engine.lib.config import Config, config_path, load_config, save_config
from engine.lib.guardrail import UnsafeTargetError, assert_safe_target
from engine.lib.modes import triggers_mandate
from engine.lib.state import JsonStateBackend, default_state
from engine.loop.episodes import (
    EPISODIC_INDEX_FILENAME,
    rebuild_episodic_index,
    search_episodes,
)
from engine.loop.kpis import kpi_footer, workflow_kpis
from engine.loop.maintenance import compaction_due, maintenance_report, run_compaction
from engine.loop.reflections import (
    REFLECTIONS_FILENAME,
    add_reflection,
    lessons_block,
    load_reflections,
    mine_reflections,
)
from engine.loop.review_seam import (
    apply_review_verdict,
    build_review_payload,
    seam_wiring_doc,
    write_review_payload,
)
from engine.loop.triggers import check_triggers, mandatory_questions, trigger_block
from engine.render import build_context, find_placeholders, load_templates, render
from engine.skills.skills import (
    SKILLS,
    skill_capabilities,
    skill_document,
    skill_relpath,
)
from engine.stances.stances import DEFAULT_STANCE, stance_briefing, stance_names


def _emit(line: str = "") -> None:
    """Write a line to stdout (avoids the print() lint ban in engine code)."""
    sys.stdout.write(line + "\n")


def _kit_root() -> Path:
    """Return the kit root (``substrate-kit/``) for the guardrail check."""
    return Path(__file__).resolve().parents[2]


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


def cmd_render(target: Path) -> int:
    """Render the content docs from the current filled slots into ``target``."""
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    if not backend.data:
        _emit(f"render: no state at {target} (run init first).")
        return 1
    context = build_context(backend.data)
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
    """PostToolUse: warn on stderr for a generated-artifact / unbadged-doc edit."""
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    file_path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
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
    return handler(target) if handler else 0


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
        findings += ledger_stamp_check(target / config.docs_root, ledger_path)
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


def cmd_check(target: Path, strict: bool) -> int:
    """Run every hygiene checker against ``target``.

    Docs (badge/link/reachable), the decisions ledger + stamp discipline, the
    namespace/shadowing guard, the seam-authority fences, and the orientation
    word budget — each engaging only when its inputs exist. Findings always
    count toward the exit code (under ``--strict``); a *missing* session log is
    advisory (a host may run ``check`` mid-session), but an *incomplete*
    existing log counts. Uses config defaults if ``target`` has no
    ``substrate.config.json`` yet, so a project can lint before onboarding.
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
    if log is None:
        _emit("check: no session log found yet (advisory — not a failure).")
    else:
        rel = log.relative_to(target) if log.is_relative_to(target) else log
        if log_missing:
            _emit(f"check: session log {rel} is missing: {', '.join(log_missing)}")
        else:
            _emit(f"check: session log {rel} complete.")

    if not doc_findings and not log_missing:
        _emit("check: all checks passed.")
        return 0
    return 1 if strict else 0


def _require_state(
    target: Path,
    command: str,
) -> tuple[Config, JsonStateBackend] | None:
    """Load config + state; None (with a message) when the install is missing."""
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
        candidates = mine_reflections(target / config.sessions_dir)
        for cand in candidates:
            entry = add_reflection(
                path,
                lesson=cand["lesson"],
                evidence=cand.get("evidence", ""),
                tags=list(cand.get("tags", [])),
                buffer_size=buffer_size,
            )
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
        return 0
    _emit(f"review: unknown action {action!r} (build | confirm | doc).")
    return 2


def cmd_economy(
    target: Path,
    action: str,
    *,
    strict: bool,
    apply: bool,
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
    harvested = parse_harvest_tables(target / config.docs_root / "planning")
    report = economy_check(target, config, harvested=harvested)
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
        lines = economy_actuate(target, config, report, apply=apply)
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


def cmd_adopt(target: Path, include_claude: bool) -> int:
    """Adopt the workflow into ``target``: plant the docs, stage the packs."""
    target.mkdir(parents=True, exist_ok=True)
    if config_path(target).exists():
        config = load_config(target)
    else:
        config = Config()
        assert_safe_target(target, _kit_root())
        save_config(target, config)
    backend = JsonStateBackend(_state_path(target, config))
    lines = adopt(
        target,
        config,
        backend,
        kit_root=_kit_root(),
        include_claude=include_claude,
    )
    for line in lines:
        _emit(f"adopt: {line}")
    return 0


def cmd_contextpack(target: Path, index: Path | None) -> int:
    """Generate agent context packs from the project index (or a manifest)."""
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
    config, backend = loaded
    rc = cmd_reflect(target, add=None, evidence="", tags="", mine=True)
    if rc != 0:
        return rc
    index_path = target / config.state_dir / EPISODIC_INDEX_FILENAME
    entries = rebuild_episodic_index(target / config.sessions_dir, index_path)
    _emit(f"session-close: indexed {len(entries)} session(s).")
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
        ("render", "render content docs from filled slots"),
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
            return cmd_render(args.target)
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
            return cmd_check(args.target, args.strict)
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
                bands=args.bands,
            )
        if args.command == "adopt":
            return cmd_adopt(args.target, args.include_claude)
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
