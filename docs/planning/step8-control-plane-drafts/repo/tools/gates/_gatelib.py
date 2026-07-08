"""Shared plumbing for the six named required gates (design-spec SS6).

Provenance (Q-0105 convention): added 2026-07-07 by the step-8 control-plane draft.
UNVERIFIED: confirm each gate's pass/fail output against ground truth a few times across
sessions before trusting it; the arming tests in tests/test_gate_arming.py are the
standing prove-can-fail harness. Delete or fix any gate that proves unreliable over
multiple sessions rather than working around it.

THE DESIGN PROBLEM these gates share: the kernel they protect does not exist yet (S1-S9
unstarted), yet every gate is a REQUIRED branch-protection check from day 0. Each runner
therefore implements a SELF-ARMING posture:

  1. PRE-KERNEL PASS is a positive assertion, never a bare `exit 0`: the runner verifies
     that the *entire* artifact family it guards is absent AND that its own pinned
     baselines are in their virgin state. "Expected absence" is checked, not assumed.
  2. PARTIAL STATE FAILS: if some guarded artifacts exist without their checker/siblings,
     the gate goes red. This is the anti-rot tripwire -- the gate cannot silently stay
     green while the thing it protects grows underneath it.
  3. ARMED = REAL: the moment the arming trigger appears (documented per runner), the
     runner delegates to / inlines the real validation with no workflow change.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, NoReturn

# GATE_ROOT override exists for the arming tests (sandbox repos).
ROOT = Path(os.environ.get("GATE_ROOT", Path(__file__).resolve().parents[2]))


class Gate:
    def __init__(self, name: str) -> None:
        self.name = name

    def note(self, msg: str) -> None:
        print(f"[{self.name}] {msg}")

    def ok(self, msg: str) -> NoReturn:
        print(f"[{self.name}] PASS: {msg}")
        sys.exit(0)

    def fail(self, msg: str) -> NoReturn:
        print(f"[{self.name}] FAIL: {msg}", file=sys.stderr)
        sys.exit(1)


def p(*rel: str) -> Path:
    return ROOT.joinpath(*rel)


def any_py(rel_dir: str) -> bool:
    d = p(rel_dir)
    return d.is_dir() and any(d.rglob("*.py"))


def run(cmd: list[str], **kw: Any) -> "subprocess.CompletedProcess[Any]":
    kw.setdefault("cwd", ROOT)
    return subprocess.run(cmd, **kw)


def base_sha() -> str:
    """The merge-base side of PR diffs. Empty when unset or the all-zeros push sentinel."""
    s = os.environ.get("GATE_BASE_SHA", "").strip()
    if not s or set(s) == {"0"}:
        return ""
    return s


def show_at_base(rel: str) -> str | None:
    """Contents of `rel` at GATE_BASE_SHA, or None if absent there / no base."""
    b = base_sha()
    if not b:
        return None
    r = run(["git", "show", f"{b}:{rel}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def load_json(path: Path):
    return json.loads(path.read_text())


def load_yaml(path_or_text):
    import yaml  # pinned in constraints/tools.txt; CI-only dep

    if isinstance(path_or_text, Path):
        return yaml.safe_load(path_or_text.read_text())
    return yaml.safe_load(path_or_text)
