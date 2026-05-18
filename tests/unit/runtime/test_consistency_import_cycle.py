"""Import-cycle regression for services.platform_consistency — PR-10.

The collection service must keep all cycle-sensitive imports
(core.runtime.*, utils.subsystem_registry, utils.db.*,
core.events_catalogue) function-local.  Re-introducing them at module
scope would re-enter partially-loaded core.runtime modules during
startup and crash the bot with the same ImportError pattern the
Phase 2b hotfix fixed.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SERVICE_PATH = (
    _REPO_ROOT / "disbot" / "services" / "platform_consistency.py"
)

# Modules whose top-level import would re-enter a partially-loaded
# parent package during startup.
_FORBIDDEN_TOP_LEVEL_PREFIXES = (
    "core.runtime",
    "utils.subsystem_registry",
    "utils.db",
    "core.events_catalogue",
)


def _module_level_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    offenders: list[str] = []
    for node in tree.body:  # module-level only
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


def test_platform_consistency_has_no_top_level_cycle_imports():
    """services.platform_consistency must NOT carry top-level imports of
    core.runtime / utils.subsystem_registry / utils.db /
    core.events_catalogue.  Move them into the collector functions."""
    offenders = _module_level_imports(_SERVICE_PATH)
    assert not offenders, (
        "services.platform_consistency has cycle-sensitive top-level "
        "imports:\n  " + "\n  ".join(offenders)
    )


def test_platform_consistency_imports_in_fresh_interpreter():
    """Run `python -c "import services.platform_consistency"` in a
    fresh interpreter so cached modules in the pytest process cannot
    mask a cycle introduced by the new module."""
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, "disbot")
        import services.platform_consistency  # noqa: F401
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
        f"services.platform_consistency import failed in subprocess.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert "ok" in result.stdout
