"""Import-cycle regression for services.settings_resolution — S3.

The resolver composes ``core.runtime.subsystem_schema``,
``core.runtime.guild_config``, ``utils.db.settings``, and
``services.diagnostics_service``. Each of these transitively touches
runtime primitives that themselves walk ``core.runtime`` modules,
so importing any at module scope risks re-entering partially loaded
packages during startup. The discipline mirrors
:mod:`services.platform_consistency`,
:mod:`services.customization_catalogue`, and
:mod:`services.resource_provisioning_catalogue`: top-level imports
are stdlib only; every cross-package import is function-local.

Mirrors:

* tests/unit/runtime/test_command_surface_ledger_import_cycle.py
* tests/unit/runtime/test_settings_registry_import_cycle.py
* tests/unit/services/test_customization_catalogue_import_cycle.py
* tests/unit/services/test_resource_provisioning_catalogue_import_cycle.py
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE_PATH = _REPO_ROOT / "disbot" / "services" / "settings_resolution.py"

_FORBIDDEN_TOP_LEVEL_PREFIXES = (
    "cogs",
    "core",
    "discord",
    "services.customization_catalogue",
    "services.diagnostics_service",
    "services.platform_consistency",
    "services.resource_provisioning_catalogue",
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


def test_settings_resolution_no_top_level_cycle_imports():
    offenders = _module_level_imports(_MODULE_PATH)
    assert not offenders, (
        "services.settings_resolution has cycle-sensitive "
        "top-level imports:\n  " + "\n  ".join(offenders)
    )


def test_settings_resolution_imports_in_fresh_interpreter():
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, "disbot")
        import services.settings_resolution  # noqa: F401
        from services import diagnostics_service

        assert "settings_resolution" in diagnostics_service.registered_names()
        snap = diagnostics_service.snapshot("settings_resolution")
        assert "counters" in snap
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
        f"services.settings_resolution import failed in subprocess.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert "ok" in result.stdout
