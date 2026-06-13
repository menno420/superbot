"""substrate-kit bootstrap — GENERATED, DO NOT EDIT.

Single-file, stdlib-only. Regenerate from source with:
    python3 substrate-kit/src/build_bootstrap.py
Source of truth: substrate-kit/src/engine/. Edits here are overwritten.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any
import argparse
import copy
import json
import os
import sys
import tempfile
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
    """Return the default cadence knobs."""
    return {"reconciliation_prs": 20}


@dataclass
class Config:
    """Host-project configuration for one substrate-kit install."""

    project_id: str = field(default_factory=_new_project_id)
    interpreter: str = field(default_factory=lambda: sys.executable)
    interpreter_for_checks: str | None = None
    state_dir: str = DEFAULT_STATE_DIR
    paths: dict[str, str] = field(default_factory=dict)
    cadence: dict[str, int] = field(default_factory=_default_cadence)
    scopes: dict[str, str] = field(default_factory=dict)

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
        "open_questions": [],
        "graduation": {
            "soft_target_sessions": 50,
            "criteria": {
                "critical_slots_filled_pct": 0.8,
                "blocking_questions": 0,
            },
        },
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
        self._in_txn = False

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
        if not self._in_txn:
            self._flush()

    def query(self, prefix: str = "") -> dict[str, Any]:
        """Return all key/value pairs whose key starts with ``prefix``."""
        return {k: v for k, v in self._data.items() if k.startswith(prefix)}

    @contextmanager
    def transaction(self) -> Iterator[JsonStateBackend]:
        """Buffer writes; roll back the whole document on error, else flush once."""
        snapshot = copy.deepcopy(self._data)
        self._in_txn = True
        try:
            yield self
        except Exception:
            self._data = snapshot
            raise
        finally:
            self._in_txn = False
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

    Safe: the system temp tree, an ``examples/`` subtree of ``kit_root``, or any
    path outside ``kit_root``. Unsafe: ``kit_root`` itself or a non-``examples``
    path inside it.
    """
    target = Path(target).resolve()
    kit_root = Path(kit_root).resolve()
    tmp_root = Path(tempfile.gettempdir()).resolve()
    if target.is_relative_to(tmp_root):
        return
    inside_kit = target == kit_root or target.is_relative_to(kit_root)
    inside_examples = target.is_relative_to(kit_root / "examples")
    if inside_kit and not inside_examples:
        msg = f"refusing to operate on the kit's own tree: {target}"
        raise UnsafeTargetError(msg)

# --- engine/cli.py ---
"""The substrate-kit bootstrap command line.

PR-1a surface: ``init`` (idempotent), ``status``, ``mode <name>``, and
``--simulate N`` (the CI / proving smoke). The richer interview surface — the
staged questions and templates — arrives in PR 1b. Output goes through ``_emit``
(``sys.stdout.write``) rather than ``print`` to keep the engine lint-clean.
"""





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

_ENGINE_MANIFEST = {
    'engine/__init__.py': '',
    'engine/lib/__init__.py': '',
    'engine/lib/atomicio.py': '"""Atomic file writes for crash-safe state.\n\nA write goes to a sibling ``*.tmp`` file and is renamed into place with\n``os.replace`` — an atomic rename on POSIX and Windows — so a process that dies\nmid-write can never leave a half-written, unparseable file behind. This is the\nrobustness floor the whole engine builds on (plan: Gemini round).\n"""\n\nfrom __future__ import annotations\n\nimport os\nfrom pathlib import Path\n\n\ndef atomic_write_text(path: Path, text: str) -> None:\n    """Write ``text`` to ``path`` atomically via a temp file + ``os.replace``."""\n    path.parent.mkdir(parents=True, exist_ok=True)\n    tmp = path.with_name(path.name + ".tmp")\n    tmp.write_text(text, encoding="utf-8")\n    os.replace(tmp, path)\n',
    'engine/lib/config.py': '"""Host-project configuration for one substrate-kit install.\n\nReads and writes ``substrate.config.json`` — the single file that absorbs every\nhost-specific knob so the engine code never hardcodes a project value. Two\ninterpreters are kept explicitly separate (Hermes-final): ``interpreter`` is the\nkit\'s own runtime, ``interpreter_for_checks`` is the host project\'s verification\nruntime (e.g. ``python3.10`` for a repo whose CI pins 3.10).\n"""\n\nfrom __future__ import annotations\n\nimport json\nimport sys\nimport uuid\nfrom dataclasses import asdict, dataclass, field, fields\nfrom pathlib import Path\n\nfrom engine.lib.atomicio import atomic_write_text\n\nCONFIG_FILENAME = "substrate.config.json"\nDEFAULT_STATE_DIR = ".substrate"\n\n\ndef _new_project_id() -> str:\n    """Return a short, stable identifier for one install."""\n    return uuid.uuid4().hex[:12]\n\n\ndef _default_cadence() -> dict[str, int]:\n    """Return the default cadence knobs."""\n    return {"reconciliation_prs": 20}\n\n\n@dataclass\nclass Config:\n    """Host-project configuration for one substrate-kit install."""\n\n    project_id: str = field(default_factory=_new_project_id)\n    interpreter: str = field(default_factory=lambda: sys.executable)\n    interpreter_for_checks: str | None = None\n    state_dir: str = DEFAULT_STATE_DIR\n    paths: dict[str, str] = field(default_factory=dict)\n    cadence: dict[str, int] = field(default_factory=_default_cadence)\n    scopes: dict[str, str] = field(default_factory=dict)\n\n    def to_json(self) -> str:\n        """Serialise the config to indented, key-sorted JSON."""\n        return json.dumps(asdict(self), indent=2, sort_keys=True)\n\n    @classmethod\n    def from_dict(cls, data: dict) -> Config:\n        """Build a Config from a parsed dict, ignoring unknown keys."""\n        known = {f.name for f in fields(cls)}\n        return cls(**{k: v for k, v in data.items() if k in known})\n\n\ndef config_path(root: Path) -> Path:\n    """Return the config-file path for a project ``root``."""\n    return root / CONFIG_FILENAME\n\n\ndef load_config(root: Path) -> Config:\n    """Load the config from ``root``; return defaults if none exists."""\n    path = config_path(root)\n    if not path.exists():\n        return Config()\n    data = json.loads(path.read_text(encoding="utf-8"))\n    return Config.from_dict(data)\n\n\ndef save_config(root: Path, config: Config) -> None:\n    """Write ``config`` to ``root`` atomically."""\n    atomic_write_text(config_path(root), config.to_json() + "\\n")\n',
    'engine/lib/state.py': '"""The state-backend interface and its default JSON implementation.\n\nThe *interface* — not a raw JSON shape — is the contract the rest of the engine\ncodes against (Hermes-final, plan §2), so a future SQLite backend can replace the\nJSON one without a rewrite. The default backend is one JSON file written\natomically; mutations inside a ``transaction`` roll back on error and flush once.\n"""\n\nfrom __future__ import annotations\n\nimport copy\nimport json\nfrom abc import ABC, abstractmethod\nfrom collections.abc import Iterator\nfrom contextlib import AbstractContextManager, contextmanager\nfrom pathlib import Path\nfrom typing import Any\n\nfrom engine.lib.atomicio import atomic_write_text\n\nSTATE_SCHEMA_VERSION = 1\n\n\ndef default_state(project_id: str) -> dict[str, Any]:\n    """Return the initial state document for a fresh install."""\n    return {\n        "version": STATE_SCHEMA_VERSION,\n        "project_id": project_id,\n        "mode": "guided",\n        "promotion_rights": "propose",\n        "stage": "integration",\n        "stance": "analysis",\n        "session_count": 0,\n        "slots": {},\n        "open_questions": [],\n        "graduation": {\n            "soft_target_sessions": 50,\n            "criteria": {\n                "critical_slots_filled_pct": 0.8,\n                "blocking_questions": 0,\n            },\n        },\n    }\n\n\nclass StateBackend(ABC):\n    """Read / write / query / transaction / migrate contract for engine state."""\n\n    version: int = STATE_SCHEMA_VERSION\n\n    @abstractmethod\n    def get(self, key: str, default: Any = None) -> Any:\n        """Return the value stored at ``key`` or ``default``."""\n\n    @abstractmethod\n    def set(self, key: str, value: Any) -> None:\n        """Store ``value`` at ``key`` (flushing unless inside a transaction)."""\n\n    @abstractmethod\n    def query(self, prefix: str = "") -> dict[str, Any]:\n        """Return all key/value pairs whose key starts with ``prefix``."""\n\n    @abstractmethod\n    def transaction(self) -> AbstractContextManager[StateBackend]:\n        """Return a context manager that commits on success, rolls back on error."""\n\n    @abstractmethod\n    def migrate(self, to_version: int) -> None:\n        """Migrate the stored document to schema ``to_version``."""\n\n\nclass JsonStateBackend(StateBackend):\n    """A StateBackend backed by one atomically-written JSON file."""\n\n    def __init__(self, path: Path) -> None:\n        self._path = Path(path)\n        self._data: dict[str, Any] = self._read()\n        self._in_txn = False\n\n    def _read(self) -> dict[str, Any]:\n        if not self._path.exists():\n            return {}\n        return json.loads(self._path.read_text(encoding="utf-8"))\n\n    def _flush(self) -> None:\n        atomic_write_text(\n            self._path,\n            json.dumps(self._data, indent=2, sort_keys=True) + "\\n",\n        )\n\n    def get(self, key: str, default: Any = None) -> Any:\n        """Return the value stored at ``key`` or ``default``."""\n        return self._data.get(key, default)\n\n    def set(self, key: str, value: Any) -> None:\n        """Store ``value`` at ``key``; flush now unless inside a transaction."""\n        self._data[key] = value\n        if not self._in_txn:\n            self._flush()\n\n    def query(self, prefix: str = "") -> dict[str, Any]:\n        """Return all key/value pairs whose key starts with ``prefix``."""\n        return {k: v for k, v in self._data.items() if k.startswith(prefix)}\n\n    @contextmanager\n    def transaction(self) -> Iterator[JsonStateBackend]:\n        """Buffer writes; roll back the whole document on error, else flush once."""\n        snapshot = copy.deepcopy(self._data)\n        self._in_txn = True\n        try:\n            yield self\n        except Exception:\n            self._data = snapshot\n            raise\n        finally:\n            self._in_txn = False\n        self._flush()\n\n    def migrate(self, to_version: int) -> None:\n        """Set the stored schema version (no transforms needed at v1)."""\n        self._data["version"] = to_version\n        self._flush()\n\n    @property\n    def data(self) -> dict[str, Any]:\n        """Return a shallow copy of the current state document."""\n        return dict(self._data)\n',
    'engine/lib/guardrail.py': '"""The live-loop guardrail.\n\nA mechanical guarantee (plan: design-corroboration) that the kit never operates\non its own repository root — which would let it mutate the very workflow it runs\ninside. Safe targets are the system temp tree, an ``examples/`` subtree of the\nkit, or any directory outside the kit. Enforced in code, in the first commit —\nnot left as a doc.\n"""\n\nfrom __future__ import annotations\n\nimport tempfile\nfrom pathlib import Path\n\n\nclass UnsafeTargetError(Exception):\n    """Raised when a target directory would corrupt the kit\'s own live loop."""\n\n\ndef assert_safe_target(target: Path, kit_root: Path) -> None:\n    """Refuse to operate on the kit\'s own repo root.\n\n    Safe: the system temp tree, an ``examples/`` subtree of ``kit_root``, or any\n    path outside ``kit_root``. Unsafe: ``kit_root`` itself or a non-``examples``\n    path inside it.\n    """\n    target = Path(target).resolve()\n    kit_root = Path(kit_root).resolve()\n    tmp_root = Path(tempfile.gettempdir()).resolve()\n    if target.is_relative_to(tmp_root):\n        return\n    inside_kit = target == kit_root or target.is_relative_to(kit_root)\n    inside_examples = target.is_relative_to(kit_root / "examples")\n    if inside_kit and not inside_examples:\n        msg = f"refusing to operate on the kit\'s own tree: {target}"\n        raise UnsafeTargetError(msg)\n',
    'engine/cli.py': '"""The substrate-kit bootstrap command line.\n\nPR-1a surface: ``init`` (idempotent), ``status``, ``mode <name>``, and\n``--simulate N`` (the CI / proving smoke). The richer interview surface — the\nstaged questions and templates — arrives in PR 1b. Output goes through ``_emit``\n(``sys.stdout.write``) rather than ``print`` to keep the engine lint-clean.\n"""\n\nfrom __future__ import annotations\n\nimport argparse\nimport sys\nimport tempfile\nfrom pathlib import Path\n\nfrom engine.lib.config import Config, config_path, load_config, save_config\nfrom engine.lib.guardrail import UnsafeTargetError, assert_safe_target\nfrom engine.lib.state import JsonStateBackend, default_state\n\n\ndef _emit(line: str = "") -> None:\n    """Write a line to stdout (avoids the print() lint ban in engine code)."""\n    sys.stdout.write(line + "\\n")\n\n\ndef _kit_root() -> Path:\n    """Return the kit root (``substrate-kit/``) for the guardrail check."""\n    return Path(__file__).resolve().parents[2]\n\n\ndef _state_path(root: Path, config: Config) -> Path:\n    """Return the state-file path under a project ``root``."""\n    return root / config.state_dir / "state.json"\n\n\ndef cmd_init(target: Path) -> int:\n    """Create config + state under ``target`` if absent; never clobber."""\n    assert_safe_target(target, _kit_root())\n    target.mkdir(parents=True, exist_ok=True)\n    if config_path(target).exists():\n        config = load_config(target)\n    else:\n        config = Config()\n        save_config(target, config)\n    state_path = _state_path(target, config)\n    if state_path.exists():\n        _emit(f"init: already initialised at {target} (idempotent no-op).")\n        return 0\n    backend = JsonStateBackend(state_path)\n    with backend.transaction():\n        for key, value in default_state(config.project_id).items():\n            backend.set(key, value)\n    _emit(f"init: created {state_path} (project_id={config.project_id}).")\n    return 0\n\n\ndef cmd_status(target: Path) -> int:\n    """Print a one-screen summary of the install\'s state."""\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    data = backend.data\n    if not data:\n        _emit(f"status: no state at {target} (run init first).")\n        return 1\n    _emit(f"project_id : {data.get(\'project_id\')}")\n    _emit(f"stage      : {data.get(\'stage\')}")\n    _emit(f"mode       : {data.get(\'mode\')}")\n    _emit(f"stance     : {data.get(\'stance\')}")\n    _emit(f"sessions   : {data.get(\'session_count\')}")\n    return 0\n\n\ndef cmd_mode(target: Path, name: str) -> int:\n    """Set the integration mode (observe | guided | active)."""\n    valid = ("observe", "guided", "active")\n    if name not in valid:\n        _emit(f"mode: invalid mode {name!r} (choose from {list(valid)}).")\n        return 2\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    if not backend.data:\n        _emit(f"mode: no state at {target} (run init first).")\n        return 1\n    backend.set("mode", name)\n    _emit(f"mode: set to {name}.")\n    return 0\n\n\ndef _run_session(target: Path, config: Config) -> None:\n    """Advance one synthetic session (PR-1a: bump the session counter)."""\n    backend = JsonStateBackend(_state_path(target, config))\n    with backend.transaction():\n        backend.set("session_count", int(backend.get("session_count", 0)) + 1)\n\n\ndef cmd_simulate(n: int) -> int:\n    """Init into a temp dir and drive ``n`` synthetic sessions; verify the count."""\n    with tempfile.TemporaryDirectory(prefix="substrate-sim-") as tmp:\n        target = Path(tmp)\n        rc = cmd_init(target)\n        if rc != 0:\n            return rc\n        config = load_config(target)\n        for _ in range(n):\n            _run_session(target, config)\n        backend = JsonStateBackend(_state_path(target, config))\n        final = int(backend.get("session_count", 0))\n        if final != n:\n            _emit(f"simulate: FAILED (expected {n} sessions, got {final}).")\n            return 1\n        _emit(f"simulate: OK — {n} synthetic sessions, state intact.")\n    return 0\n\n\ndef build_parser() -> argparse.ArgumentParser:\n    """Construct the bootstrap argument parser."""\n    parser = argparse.ArgumentParser(prog="bootstrap", description="substrate-kit")\n    parser.add_argument(\n        "--simulate",\n        type=int,\n        metavar="N",\n        help="run N synthetic sessions in a temp dir, then exit",\n    )\n    sub = parser.add_subparsers(dest="command")\n    for name, helptext in (\n        ("init", "initialise a project"),\n        ("status", "show install state"),\n    ):\n        child = sub.add_parser(name, help=helptext)\n        child.add_argument("--target", type=Path, default=Path.cwd())\n    mode = sub.add_parser("mode", help="set the integration mode")\n    mode.add_argument("name")\n    mode.add_argument("--target", type=Path, default=Path.cwd())\n    return parser\n\n\ndef main(argv: list[str] | None = None) -> int:\n    """Run the bootstrap CLI; return a process exit code."""\n    parser = build_parser()\n    args = parser.parse_args(argv)\n    try:\n        if args.simulate is not None:\n            return cmd_simulate(args.simulate)\n        if args.command == "init":\n            return cmd_init(args.target)\n        if args.command == "status":\n            return cmd_status(args.target)\n        if args.command == "mode":\n            return cmd_mode(args.target, args.name)\n    except UnsafeTargetError as exc:\n        _emit(f"refused: {exc}")\n        return 2\n    parser.print_help()\n    return 0\n',
}

if __name__ == "__main__":
    raise SystemExit(main())
