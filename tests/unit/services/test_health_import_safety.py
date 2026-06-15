"""Import-safety pin for services.health_snapshot_service — PR1.

The aggregator composes heavy / cycle-sensitive sources (the AI
read-models, ``utils.db``, ``platform_consistency``, ``core.runtime.*``).
All of those imports must stay **function-local** so that importing the
module — which happens at cog-import = bot-startup time — does not eagerly
pull the AI/DB graph or re-enter partially-loaded ``core.runtime``
packages.

Mirrors ``tests/unit/runtime/test_consistency_import_cycle.py``: an AST
scan for forbidden top-level imports plus a fresh-interpreter check that
the heavy modules are absent from ``sys.modules`` after import.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SERVICE_PATH = _REPO_ROOT / "disbot" / "services" / "health_snapshot_service.py"

# Modules whose top-level import would defeat the function-local discipline.
_FORBIDDEN_TOP_LEVEL_PREFIXES = (
    "core.runtime",
    "utils.db",
    "services.diagnostics_service",
    "services.platform_consistency",
    "services.resource_health",
    "services.ai_diagnostics_service",
)

# Heavy modules that must NOT be imported merely by importing the service.
_HEAVY_MODULES = (
    "services.diagnostics_service",
    "services.platform_consistency",
    "services.resource_health",
    "services.ai_diagnostics_service",
    "core.runtime.lifecycle",
    "core.runtime.tasks",
    "core.runtime.startup_outcome",
    "utils.db.health",
    "utils.db.pool",
)


def _module_level_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    offenders: list[str] = []
    for node in tree.body:  # module-level statements only
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if any(
                module == p or module.startswith(p + ".")
                for p in _FORBIDDEN_TOP_LEVEL_PREFIXES
            ):
                names = ", ".join(a.name for a in node.names)
                offenders.append(f"from {module} import {names}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if any(
                    alias.name == p or alias.name.startswith(p + ".")
                    for p in _FORBIDDEN_TOP_LEVEL_PREFIXES
                ):
                    offenders.append(f"import {alias.name}")
    return offenders


def test_no_heavy_top_level_imports() -> None:
    offenders = _module_level_imports(_SERVICE_PATH)
    assert not offenders, (
        "services.health_snapshot_service has heavy top-level imports — move "
        "them into the adapter functions:\n  " + "\n  ".join(offenders)
    )


def test_import_does_not_pull_heavy_modules() -> None:
    """A fresh interpreter importing the service must not eagerly load the
    AI/DB/consistency graph."""
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, "disbot")
        import services.health_snapshot_service  # noqa: F401
        heavy = [m for m in {heavy!r} if m in sys.modules]
        print("HEAVY:" + ",".join(heavy))
        """
    ).format(heavy=list(_HEAVY_MODULES))
    result = subprocess.run(  # noqa: S603 — script literal under our control
        [sys.executable, "-c", script],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (
        f"import failed:\nstdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    line = next(
        (ln for ln in result.stdout.splitlines() if ln.startswith("HEAVY:")), ""
    )
    leaked = line[len("HEAVY:") :].strip()
    assert leaked == "", f"health_snapshot_service eagerly imported: {leaked}"
