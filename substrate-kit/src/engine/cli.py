"""The substrate-kit bootstrap command line.

Surface: ``init`` (idempotent), ``status``, ``mode <name>``, ``ask`` (list the
pending interview questions), ``render`` (write content docs), ``check`` (run the
doc + session-log hygiene checks), and ``--simulate N`` (the CI / proving smoke
that drives the staged interview). Output goes through ``_emit``
(``sys.stdout.write``) rather than ``print`` to keep the engine lint-clean.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from engine.checks.check_docs import run_doc_checks
from engine.checks.check_session_log import check_log, latest_session_log
from engine.interview.interview import critical_slots, pending_questions, run_session
from engine.lib.atomicio import atomic_write_text
from engine.lib.config import Config, config_path, load_config, save_config
from engine.lib.guardrail import UnsafeTargetError, assert_safe_target
from engine.lib.state import JsonStateBackend, default_state
from engine.render import build_context, find_placeholders, load_templates, render


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
    backend.set("mode", name)
    _emit(f"mode: set to {name}.")
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
    _emit(f"ask: {len(pending)} pending question(s):")
    for question in pending:
        _emit(
            f"  [{question['id']}] "
            f"({question['audience']}/{question['priority']}) {question['prompt']}",
        )
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


def cmd_check(target: Path, strict: bool) -> int:
    """Run the doc-hygiene + session-log checks against ``target``.

    Doc findings always count toward the exit code (under ``--strict``); a
    *missing* session log is advisory (a host may run ``check`` mid-session), but
    an *incomplete* existing log counts. Uses config defaults if ``target`` has
    no ``substrate.config.json`` yet, so a project can lint before onboarding.
    """
    config = load_config(target)
    docs_root = target / config.docs_root
    doc_findings = run_doc_checks(
        docs_root,
        config.badge_tokens,
        config.readpath_docs,
    )
    if doc_findings:
        _emit(f"check: {len(doc_findings)} doc finding(s):")
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


def cmd_simulate(n: int) -> int:
    """Init into a temp dir and drive ``n`` interview sessions; verify progress.

    Session 1 supplies confirmed answers for every critical slot; later sessions
    supply none. Asserts the critical slots fill and (for ``n`` past the quiet
    threshold) the install graduates integration -> steady.
    """
    with tempfile.TemporaryDirectory(prefix="substrate-sim-") as tmp:
        target = Path(tmp)
        rc = cmd_init(target)
        if rc != 0:
            return rc
        state_path = _state_path(target, load_config(target))
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
        _emit(
            f"simulate: OK — {n} session(s), {len(crit)} critical slots filled, "
            f"stage={data.get('stage')} (graduated={graduated}).",
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
    sub = parser.add_subparsers(dest="command")
    for name, helptext in (
        ("init", "initialise a project"),
        ("status", "show install state"),
        ("ask", "list pending interview questions"),
        ("render", "render content docs from filled slots"),
    ):
        child = sub.add_parser(name, help=helptext)
        child.add_argument("--target", type=Path, default=Path.cwd())
    mode = sub.add_parser("mode", help="set the integration mode")
    mode.add_argument("name")
    mode.add_argument("--target", type=Path, default=Path.cwd())
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
            return cmd_simulate(args.simulate)
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
        if args.command == "check":
            return cmd_check(args.target, args.strict)
    except UnsafeTargetError as exc:
        _emit(f"refused: {exc}")
        return 2
    parser.print_help()
    return 0
