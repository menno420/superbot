"""Import-cycle regression for services.server_logging — PR-11.

The service is subscribed to ``moderation.action_taken`` at startup
from ``bot1.py``.  It must keep ``core.runtime`` / ``utils.db`` /
``utils.subsystem_registry`` imports inside function bodies so loading
the service module never re-enters a partially-loaded ``core.runtime``
during startup.

This mirrors the platform-consistency / utils.helpers regression
patterns.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SERVICE_PATH = _REPO_ROOT / "disbot" / "services" / "server_logging.py"

# core.runtime / utils.subsystem_registry are the cycle-sensitive
# paths.  utils.db is safe at module scope (it imports only
# asyncpg / utils.db.pool which do not touch core.runtime).
_FORBIDDEN_TOP_LEVEL_PREFIXES = (
    "core.runtime",
    "utils.subsystem_registry",
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


def test_server_logging_has_no_top_level_cycle_imports():
    offenders = _module_level_imports(_SERVICE_PATH)
    assert not offenders, (
        "services.server_logging has cycle-sensitive top-level imports:\n  "
        + "\n  ".join(offenders)
    )


def test_server_logging_imports_in_fresh_interpreter():
    """`python -c "import services.server_logging"` in a fresh
    interpreter, so cached modules in the pytest process cannot mask a
    cycle introduced by the new module."""
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, "disbot")
        import services.server_logging  # noqa: F401
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
        f"services.server_logging import failed in subprocess.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert "ok" in result.stdout
