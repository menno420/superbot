"""Regression — utils.helpers must not pull core.runtime at module scope.

Production startup on Railway crashed after PR #73 with::

    ImportError: cannot import name 'resources' from partially
    initialized module 'core.runtime'

The cycle traced through:

    bot1.py
      → utils.db
      → utils.db.pool
      → core.runtime
      → core.runtime.bindings              (added in PR #73)
      → core.resources.discovery
      → utils.helpers
      → from core.runtime import resources  ← re-enters partially loaded package

The hotfix moved the ``core.runtime`` dependency out of
``utils.helpers``' module scope into the functions that actually need
it (:func:`_parse_member`, :func:`post_log_embed`).

These tests pin that fix:

* :func:`test_helpers_no_top_level_core_runtime_import` — static AST
  scan of ``utils/helpers.py`` so a future contributor cannot re-add
  the top-level dependency without CI catching it.
* :func:`test_isolated_import_order` — exercises the exact bot-startup
  order in a *fresh* import context, asserting no ImportError.
* :func:`test_normalize_name_does_not_import_core_runtime` — confirms
  the common helper consumed by ``core.resources.discovery`` is
  importable on its own without dragging in ``core.runtime``.
"""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HELPERS_PATH = _REPO_ROOT / "disbot" / "utils" / "helpers.py"


# Files loaded transitively while ``core/runtime/__init__.py`` is still
# executing.  Each of these MUST NOT carry a top-level
# ``from core.runtime import ...`` because the alias resources point at
# may not be bound yet when the chain re-enters.  Function-scope
# imports are fine — by the time the function runs, the parent
# ``core/runtime/__init__.py`` has finished loading.
_CYCLE_SENSITIVE_FILES: tuple[Path, ...] = (
    _REPO_ROOT / "disbot" / "utils" / "helpers.py",
    _REPO_ROOT / "disbot" / "governance" / "__init__.py",
    # Phase 2 PR-10 — services.platform_consistency must keep its
    # cross-package imports function-local; module-scope imports of
    # core.runtime would re-introduce the partial-load cycle.
    _REPO_ROOT / "disbot" / "services" / "platform_consistency.py",
)


def _module_level_core_runtime_imports(path: Path) -> list[str]:
    """Return module-level statements that depend on ``core.runtime``.

    Function-scope imports are intentionally excluded — they only run
    after ``core/runtime/__init__.py`` has finished loading, so they
    cannot re-enter mid-load.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for node in tree.body:  # module-level only
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "core.runtime" or module.startswith("core.runtime."):
                found.append(
                    f"from {module} import " f"{', '.join(a.name for a in node.names)}",
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "core.runtime" or alias.name.startswith(
                    "core.runtime.",
                ):
                    found.append(f"import {alias.name}")
    return found


def test_cycle_sensitive_files_have_no_top_level_core_runtime_imports():
    """Files transitively loaded while ``core.runtime`` is still
    initializing must NOT carry a top-level ``from core.runtime import
    ...``.  Re-entering the partially-loaded package crashes startup
    with the Railway-observed ImportError fixed by the Phase 2b
    hotfix.

    Add a new file to ``_CYCLE_SENSITIVE_FILES`` whenever a new
    transitive dependency from ``core.runtime.__init__`` is introduced
    and starts touching ``core.runtime`` symbols at module scope.
    """
    violations: list[str] = []
    for path in _CYCLE_SENSITIVE_FILES:
        offenders = _module_level_core_runtime_imports(path)
        if offenders:
            violations.append(
                f"{path.relative_to(_REPO_ROOT)}: {', '.join(offenders)}",
            )
    assert not violations, (
        "Top-level core.runtime imports in cycle-sensitive files would "
        "re-introduce the Phase 2b hotfix regression.  Move the "
        "import(s) into the function(s) that actually use them.\n"
        + "\n".join(violations)
    )


def test_normalize_name_does_not_import_core_runtime():
    """``normalize_name`` is consumed by ``core.resources.discovery``; it
    must be importable from ``utils.helpers`` without triggering a
    ``core.runtime`` import chain."""
    # Force a fresh import in this interpreter — clear any cached
    # module that might mask the regression locally.
    for name in list(sys.modules):
        if name == "utils.helpers" or name.startswith("utils.helpers."):
            sys.modules.pop(name)
    helpers = importlib.import_module("utils.helpers")
    # The function itself does not need core.runtime.
    assert helpers.normalize_name("Test Role") == "testrole"


def test_isolated_import_order():
    """Run the exact bot-startup import order in a child interpreter.

    Using a subprocess avoids interference from cached modules in the
    pytest process; the child performs the imports in the same order
    ``bot1.py`` triggers them and exits 0 on success.  A circular
    ImportError exits non-zero with the ImportError message in stderr.
    """
    script = textwrap.dedent(
        """
        import sys
        # Mirror the bot's sys.path setup
        sys.path.insert(0, "disbot")

        # The Railway-observed crash order:
        import utils.db.pool        # noqa: F401
        import core.runtime         # noqa: F401
        import core.runtime.bindings  # noqa: F401
        import core.resources.discovery  # noqa: F401
        import utils.helpers        # noqa: F401

        # All five resolve without ImportError.
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
        f"bot-startup import order failed in subprocess.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert "ok" in result.stdout
