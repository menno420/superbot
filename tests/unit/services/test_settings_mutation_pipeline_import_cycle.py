"""Import-cycle regression for services.settings_mutation — S4.

The pipeline composes ``core.runtime.subsystem_schema``,
``core.events.bus``, ``utils.db.settings_audit``,
``utils.guild_config_accessors``, ``utils.subsystem_registry``, and
``services.settings_resolution``.  Each of those transitively touches
runtime primitives whose ``__init__`` modules walk ``core.runtime``;
importing any at module scope risks re-entering partially loaded
packages during startup.

Discipline mirrors :mod:`services.platform_consistency`,
:mod:`services.customization_catalogue`,
:mod:`services.resource_provisioning_catalogue`, and
:mod:`services.settings_resolution`: top-level imports are stdlib
only; every cross-package import is function-local.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE_PATH = _REPO_ROOT / "disbot" / "services" / "settings_mutation.py"

_FORBIDDEN_TOP_LEVEL_PREFIXES = (
    "cogs",
    "core",
    "discord",
    "services.customization_catalogue",
    "services.diagnostics_service",
    "services.platform_consistency",
    "services.resource_provisioning_catalogue",
    "services.settings_resolution",
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


def test_settings_mutation_no_top_level_cycle_imports():
    offenders = _module_level_imports(_MODULE_PATH)
    assert not offenders, (
        "services.settings_mutation has cycle-sensitive top-level imports:\n  "
        + "\n  ".join(offenders)
    )


def test_settings_mutation_imports_in_fresh_interpreter():
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, "disbot")
        import services.settings_mutation as sm  # noqa: F401

        assert sm.EVT_SETTINGS_CHANGED == "settings.changed"
        assert sm.SettingsMutationPipeline is not None
        # Catalogue + flag wired up at import time of the sibling modules.
        from core.events_catalogue import KNOWN_EVENTS
        assert sm.EVT_SETTINGS_CHANGED in KNOWN_EVENTS
        from core.runtime.feature_flags import SETTINGS_MUTATION_PRIMARY
        assert SETTINGS_MUTATION_PRIMARY.default_value is False
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
        f"services.settings_mutation import failed in subprocess.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert "ok" in result.stdout
