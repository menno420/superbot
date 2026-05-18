"""Import-cycle regression for services.resource_provisioning — S4.5.

The pipeline composes several runtime + service modules:
``core.runtime.subsystem_schema`` / ``guild_resources``,
``core.events.bus``, ``services.binding_mutation``,
``services.resource_provisioning_catalogue``,
``utils.db.resource_provisioning_audit``,
``utils.visibility_rules``.

Each of those transitively touches packages whose ``__init__``
modules walk ``core.runtime``; importing any at module scope risks
re-entering partially-loaded packages during startup.

Discipline mirrors :mod:`services.platform_consistency`,
:mod:`services.customization_catalogue`,
:mod:`services.resource_provisioning_catalogue`,
:mod:`services.settings_resolution`, and
:mod:`services.settings_mutation`: top-level imports are stdlib
only; every cross-package import is function-local.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE_PATH = _REPO_ROOT / "disbot" / "services" / "resource_provisioning.py"

_FORBIDDEN_TOP_LEVEL_PREFIXES = (
    "cogs",
    "core",
    "discord",
    "services.binding_mutation",
    "services.customization_catalogue",
    "services.diagnostics_service",
    "services.platform_consistency",
    "services.resource_provisioning_catalogue",
    "services.settings_mutation",
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


def test_resource_provisioning_no_top_level_cycle_imports():
    offenders = _module_level_imports(_MODULE_PATH)
    assert not offenders, (
        "services.resource_provisioning has cycle-sensitive top-level imports:\n  "
        + "\n  ".join(offenders)
    )


def test_resource_provisioning_imports_in_fresh_interpreter():
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, "disbot")
        import services.resource_provisioning as rp  # noqa: F401

        assert rp.EVT_RESOURCE_PROVISIONED == "resource.provisioned"
        assert rp.ResourceProvisioningPipeline is not None
        from core.events_catalogue import KNOWN_EVENTS
        assert rp.EVT_RESOURCE_PROVISIONED in KNOWN_EVENTS
        from core.runtime.feature_flags import RESOURCE_PROVISIONING_PRIMARY
        assert RESOURCE_PROVISIONING_PRIMARY.default_value is False
        # Helpers wired into core.runtime.guild_resources.
        from core.runtime import guild_resources
        assert hasattr(guild_resources, "ensure_role")
        assert hasattr(guild_resources, "ensure_category")
        assert hasattr(guild_resources, "resolve_category")
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
        f"services.resource_provisioning import failed in subprocess.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert "ok" in result.stdout
