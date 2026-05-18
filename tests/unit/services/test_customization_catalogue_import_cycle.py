"""Import-cycle regression for services.customization_catalogue — S2.

The catalogue composes several ``core.runtime`` primitives and reads
``utils.subsystem_registry``. Importing any of them at module scope
would re-enter partially-loaded packages during startup. The
discipline mirrors :mod:`services.platform_consistency`: top-level
imports are stdlib only; every cross-package import is function-local.

Mirrors:

* tests/unit/runtime/test_command_surface_ledger_import_cycle.py
* tests/unit/runtime/test_settings_registry_import_cycle.py
* tests/unit/runtime/test_consistency_import_cycle.py
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CATALOGUE_PATH = (
    _REPO_ROOT / "disbot" / "services" / "customization_catalogue.py"
)

# Forbidden top-level imports — any cross-package access must be
# function-local. ``services.diagnostics_service`` and other siblings
# are also kept function-local to match the platform_consistency
# pattern and keep the cycle test stable as new sources are added.
_FORBIDDEN_TOP_LEVEL_PREFIXES = (
    "core",
    "cogs",
    "discord",
    "services.diagnostics_service",
    "services.platform_consistency",
    "utils",
    "views",
)


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


def test_customization_catalogue_no_top_level_cycle_imports():
    offenders = _module_level_imports(_CATALOGUE_PATH)
    assert not offenders, (
        "services.customization_catalogue has cycle-sensitive "
        "top-level imports:\n  " + "\n  ".join(offenders)
    )


def test_customization_catalogue_imports_in_fresh_interpreter():
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, "disbot")
        import services.customization_catalogue  # noqa: F401
        from services import diagnostics_service

        assert "customization_catalogue" in diagnostics_service.registered_names()
        snap = diagnostics_service.snapshot("customization_catalogue")
        assert snap["status"] == "not_built"
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
        f"services.customization_catalogue import failed in subprocess.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert "ok" in result.stdout
