"""The substrate-kit bootstrap command line.

PR-1a surface: ``init`` (idempotent), ``status``, ``mode <name>``, and
``--simulate N`` (the CI / proving smoke). The richer interview surface — the
staged questions and templates — arrives in PR 1b. Output goes through ``_emit``
(``sys.stdout.write``) rather than ``print`` to keep the engine lint-clean.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from engine.lib.config import Config, config_path, load_config, save_config
from engine.lib.guardrail import UnsafeTargetError, assert_safe_target
from engine.lib.state import JsonStateBackend, default_state


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


def _run_session(target: Path, config: Config) -> None:
    """Advance one synthetic session (PR-1a: bump the session counter)."""
    backend = JsonStateBackend(_state_path(target, config))
    with backend.transaction():
        backend.set("session_count", int(backend.get("session_count", 0)) + 1)


def cmd_simulate(n: int) -> int:
    """Init into a temp dir and drive ``n`` synthetic sessions; verify the count."""
    with tempfile.TemporaryDirectory(prefix="substrate-sim-") as tmp:
        target = Path(tmp)
        rc = cmd_init(target)
        if rc != 0:
            return rc
        config = load_config(target)
        for _ in range(n):
            _run_session(target, config)
        backend = JsonStateBackend(_state_path(target, config))
        final = int(backend.get("session_count", 0))
        if final != n:
            _emit(f"simulate: FAILED (expected {n} sessions, got {final}).")
            return 1
        _emit(f"simulate: OK — {n} synthetic sessions, state intact.")
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
    ):
        child = sub.add_parser(name, help=helptext)
        child.add_argument("--target", type=Path, default=Path.cwd())
    mode = sub.add_parser("mode", help="set the integration mode")
    mode.add_argument("name")
    mode.add_argument("--target", type=Path, default=Path.cwd())
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
        if args.command == "mode":
            return cmd_mode(args.target, args.name)
    except UnsafeTargetError as exc:
        _emit(f"refused: {exc}")
        return 2
    parser.print_help()
    return 0
