"""Architectural boundaries for the AI platform layer and the BTD6 cog.

Five static checks enforce the dependency direction promised by the
"Separate AI Cog + BTD6 Cog, Shared AI Platform Helpers" plan:

1. Provider SDK imports (``openai``/``anthropic``) only inside
   ``disbot/core/runtime/ai/providers/`` — the gateway is the single
   external-provider chokepoint.
2. ``disbot/core/runtime/ai/`` never imports from ``cogs/`` or from
   any BTD6 service. AI runtime is product-agnostic.
3. ``disbot/services/ai_*.py`` never imports BTD6 services or BTD6
   cogs. AI services are reusable, not domain-coupled.
4. BTD6 modules (``cogs/btd6*``, ``services/btd6_*.py``) never import
   the AI cog. They consume AI through ``services.ai_gateway`` and
   ``core.runtime.ai.*`` only — never via cog-to-cog imports.
5. No BTD6 module installs its own ``on_message`` listener. BTD6
   message handling, when added, goes through the existing
   ``core.runtime.message_pipeline.register(stage)`` API.

The tests scan production files with ``ast`` (same convention as
``test_inv_f_economy_service.py`` and ``test_no_direct_bindings_primary_branch.py``).
Vacuous-true is fine: until BTD6 modules exist, the BTD6 checks
simply scan an empty file set.

The setup advisor temporarily appears in the OpenAI allowlist
because Module 1 of the plan migrates it behind the gateway. After
Module 1 lands, ``_OPENAI_ALLOWLIST_TRANSITIONAL`` is removed; the
only remaining allowed path is ``providers/openai_provider.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Paths permitted to import the OpenAI or Anthropic SDK. The plan
# eventually narrows this to ``providers/`` only; the setup-advisor
# entry is a transitional exception removed by Module 1.
_PROVIDER_DIR = _DISBOT / "core" / "runtime" / "ai" / "providers"
_OPENAI_ALLOWLIST_TRANSITIONAL = {
    _DISBOT / "services" / "setup_ai_advisor.py",
}

_PROVIDER_SDKS = ("openai", "anthropic")


def _iter_production_py_files() -> list[Path]:
    return [
        p
        for p in _DISBOT.rglob("*.py")
        if "__pycache__" not in p.parts
    ]


def _files_under(*roots: Path) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix == ".py":
            out.append(root)
            continue
        for p in root.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            out.append(p)
    return out


def _btd6_files() -> list[Path]:
    """Every BTD6 production file (cogs and services)."""
    out: list[Path] = []
    cogs_dir = _DISBOT / "cogs"
    if cogs_dir.exists():
        for p in cogs_dir.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            name = p.name
            rel = p.relative_to(cogs_dir)
            if name.startswith("btd6") or rel.parts[0].startswith("btd6"):
                out.append(p)
    services_dir = _DISBOT / "services"
    if services_dir.exists():
        for p in services_dir.glob("btd6_*.py"):
            out.append(p)
    return out


def _ai_service_files() -> list[Path]:
    """Every ``services/ai_*.py`` production file."""
    services_dir = _DISBOT / "services"
    if not services_dir.exists():
        return []
    return [p for p in services_dir.glob("ai_*.py")]


def _imported_modules(tree: ast.AST) -> list[str]:
    """Return every imported module name (from-imports and plain imports)."""
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                out.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                out.append(alias.name)
    return out


def _imports_root(module: str) -> str:
    """Return the top-level package of an imported module."""
    return module.split(".", 1)[0]


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _matches_btd6_import(module: str) -> bool:
    """True if ``module`` resolves to a BTD6 cog or BTD6 service."""
    parts = module.split(".")
    # Accept absolute (``disbot.cogs.btd6_cog``) and runtime forms
    # (``cogs.btd6_cog``, ``services.btd6_knowledge_service``).
    if parts and parts[0] == "disbot":
        parts = parts[1:]
    if len(parts) < 2:
        return False
    if parts[0] == "cogs" and (
        parts[1].startswith("btd6") or (len(parts) > 2 and parts[1] == "btd6")
    ):
        return True
    if parts[0] == "services" and parts[1].startswith("btd6_"):
        return True
    return False


def _matches_ai_cog_import(module: str) -> bool:
    """True if ``module`` resolves to the AI cog (forbidden for BTD6)."""
    parts = module.split(".")
    if parts and parts[0] == "disbot":
        parts = parts[1:]
    if len(parts) < 2:
        return False
    if parts[0] != "cogs":
        return False
    # Forbid the AI cog package and module entry.
    return parts[1] in {"ai_cog", "ai"}


def _matches_cogs_import(module: str) -> bool:
    """True if ``module`` resolves to anything under ``cogs/`` (forbidden for AI runtime)."""
    parts = module.split(".")
    if parts and parts[0] == "disbot":
        parts = parts[1:]
    return bool(parts) and parts[0] == "cogs"


# ---------------------------------------------------------------------------
# Test 1 — provider SDK imports
# ---------------------------------------------------------------------------


def test_provider_sdk_imports_only_in_providers() -> None:
    """``from openai``/``from anthropic`` only inside ``core/runtime/ai/providers/``.

    Transitional exception: ``services/setup_ai_advisor.py`` is allowed
    until Module 1 of the AI/BTD6 plan migrates it behind the gateway.
    """
    violations: list[str] = []
    for path in _iter_production_py_files():
        if path == _DISBOT / "core" / "runtime" / "ai" / "providers" / "__init__.py":
            continue
        if path.is_relative_to(_PROVIDER_DIR):
            continue
        if path in _OPENAI_ALLOWLIST_TRANSITIONAL:
            continue
        try:
            tree = _parse(path)
        except SyntaxError:
            continue
        for module in _imported_modules(tree):
            root = _imports_root(module)
            if root in _PROVIDER_SDKS:
                violations.append(f"{path.relative_to(_REPO_ROOT)}: imports {module!r}")
    if violations:
        pytest.fail(
            "Provider SDK imports must live only under "
            "disbot/core/runtime/ai/providers/. Violations:\n  "
            + "\n  ".join(violations),
        )


# ---------------------------------------------------------------------------
# Test 2 — AI runtime is product-agnostic
# ---------------------------------------------------------------------------


def test_core_runtime_ai_does_not_import_cogs_or_btd6() -> None:
    """``disbot/core/runtime/ai/`` must not import any cog or any BTD6 service."""
    ai_dir = _DISBOT / "core" / "runtime" / "ai"
    if not ai_dir.exists():
        pytest.skip("core/runtime/ai not present yet")
    violations: list[str] = []
    for path in _files_under(ai_dir):
        try:
            tree = _parse(path)
        except SyntaxError:
            continue
        for module in _imported_modules(tree):
            if _matches_cogs_import(module):
                violations.append(
                    f"{path.relative_to(_REPO_ROOT)}: imports cog module {module!r}",
                )
                continue
            if _matches_btd6_import(module):
                violations.append(
                    f"{path.relative_to(_REPO_ROOT)}: imports BTD6 module {module!r}",
                )
    if violations:
        pytest.fail(
            "core/runtime/ai/ must not depend on cogs or BTD6 services. "
            "Violations:\n  " + "\n  ".join(violations),
        )


# ---------------------------------------------------------------------------
# Test 3 — AI services must not import BTD6
# ---------------------------------------------------------------------------


def test_ai_services_do_not_import_btd6() -> None:
    """Any ``services/ai_*.py`` must not import BTD6 cogs or services."""
    violations: list[str] = []
    for path in _ai_service_files():
        try:
            tree = _parse(path)
        except SyntaxError:
            continue
        for module in _imported_modules(tree):
            if _matches_btd6_import(module):
                violations.append(
                    f"{path.relative_to(_REPO_ROOT)}: imports BTD6 module {module!r}",
                )
    if violations:
        pytest.fail(
            "services/ai_*.py must not depend on BTD6 cogs or BTD6 services. "
            "Violations:\n  " + "\n  ".join(violations),
        )


# ---------------------------------------------------------------------------
# Test 4 — BTD6 must consume AI only through service boundaries
# ---------------------------------------------------------------------------


def test_btd6_does_not_import_ai_cog() -> None:
    """BTD6 cogs and services must not import the AI cog directly.

    BTD6 reaches AI through ``services.ai_gateway`` and ``core.runtime.ai.*``.
    Cog-to-cog imports are forbidden per the global architecture rule.
    """
    violations: list[str] = []
    for path in _btd6_files():
        try:
            tree = _parse(path)
        except SyntaxError:
            continue
        for module in _imported_modules(tree):
            if _matches_ai_cog_import(module):
                violations.append(
                    f"{path.relative_to(_REPO_ROOT)}: imports AI cog module {module!r}",
                )
    if violations:
        pytest.fail(
            "BTD6 modules must not import the AI cog directly. "
            "Use services.ai_gateway / core.runtime.ai instead. "
            "Violations:\n  " + "\n  ".join(violations),
        )


# ---------------------------------------------------------------------------
# Test 5 — BTD6 must use the message pipeline, not a direct listener
# ---------------------------------------------------------------------------


def _declares_on_message_listener(tree: ast.AST) -> list[str]:
    """Return the locations of any ``on_message`` listener registration.

    Catches three patterns:
      * ``@bot.event`` / ``@self.bot.event`` decorating ``async def on_message``
      * ``@commands.Cog.listener("on_message")`` /
        ``@commands.Cog.listener()`` decorating ``async def on_message``
      * Plain ``async def on_message`` inside a ``commands.Cog`` subclass
        (discord.py auto-binds ``on_message`` methods on cogs)
    """
    findings: list[str] = []

    def _decorator_targets_on_message(dec: ast.expr) -> bool:
        # @<x>.event, @<x>.listener, @commands.Cog.listener(...)
        if isinstance(dec, ast.Attribute):
            return dec.attr in {"event", "listener"}
        if isinstance(dec, ast.Call):
            return _decorator_targets_on_message(dec.func)
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "on_message":
            findings.append(f"async def on_message at line {node.lineno}")
            continue
        if isinstance(node, ast.FunctionDef) and node.name == "on_message":
            findings.append(f"def on_message at line {node.lineno}")
            continue

    # Also scan for explicit bot.add_listener("on_message", ...) calls.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "add_listener"
                and any(
                    isinstance(arg, ast.Constant) and arg.value == "on_message"
                    for arg in node.args
                )
            ):
                findings.append(f"add_listener('on_message', ...) at line {node.lineno}")
    return findings


def test_btd6_does_not_install_on_message_listener() -> None:
    """BTD6 must register via ``message_pipeline.register()`` only."""
    violations: list[str] = []
    for path in _btd6_files():
        try:
            tree = _parse(path)
        except SyntaxError:
            continue
        for finding in _declares_on_message_listener(tree):
            violations.append(f"{path.relative_to(_REPO_ROOT)}: {finding}")
    if violations:
        pytest.fail(
            "BTD6 modules must not declare on_message listeners. "
            "Register a MessageStage via core.runtime.message_pipeline.register(). "
            "Violations:\n  " + "\n  ".join(violations),
        )
