"""Import-cycle regression for core.runtime.command_surface_ledger — PR-12.

The ledger module lives inside ``core.runtime`` and is loaded during
runtime setup, so any top-level imports of cycle-sensitive packages
would re-enter a partially-loaded ``core.runtime`` and break startup.

Pattern mirrors:
* tests/unit/runtime/test_consistency_import_cycle.py (PR-10)
* tests/unit/runtime/test_server_logging_import_cycle.py (PR-11)
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LEDGER_PATH = (
    _REPO_ROOT / "disbot" / "core" / "runtime" / "command_surface_ledger.py"
)

# Within core.runtime, we forbid only utils.subsystem_registry at module
# scope (its evaluator helpers reach back into core.runtime through
# transitive chains).  Importing sibling core.runtime modules at top
# level is fine because they share the same package.
_FORBIDDEN_TOP_LEVEL_PREFIXES = ("utils.subsystem_registry",)


def _module_level_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    offenders: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for prefix in _FORBIDDEN_TOP_LEVEL_PREFIXES:
                if module == prefix or module.startswith(prefix + "."):
                    offenders.append(
                        f"from {module} import "
                        f"{', '.join(a.name for a in node.names)}",
                    )
                    break
        elif isinstance(node, ast.Import):
            for alias in node.names:
                for prefix in _FORBIDDEN_TOP_LEVEL_PREFIXES:
                    if alias.name == prefix or alias.name.startswith(prefix + "."):
                        offenders.append(f"import {alias.name}")
                        break
    return offenders


def test_command_surface_ledger_no_top_level_cycle_imports():
    offenders = _module_level_imports(_LEDGER_PATH)
    assert not offenders, (
        "core.runtime.command_surface_ledger has cycle-sensitive "
        "top-level imports:\n  " + "\n  ".join(offenders)
    )


def test_command_surface_ledger_imports_in_fresh_interpreter():
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, "disbot")
        import core.runtime.command_surface_ledger  # noqa: F401
        print("ok")
        """,
    )
    result = subprocess.run(  # noqa: S603 — script literal under our control
        [sys.executable, "-c", script],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (
        f"core.runtime.command_surface_ledger import failed in subprocess.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert "ok" in result.stdout
