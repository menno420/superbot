"""M4 pin — AI code paths cannot write to ``btd6_facts``.

The fact store is the single writer of ``btd6_facts``. Any AI
service / cog / view that ends up needing to "remember a stat"
must instead route through the strategy-memory tables (which carry
audit + reversibility) — not the global facts table.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SERVICES = _REPO / "disbot" / "services"
_COGS = _REPO / "disbot" / "cogs"
_RUNTIME = _REPO / "disbot" / "core" / "runtime" / "ai"


def _scans_ai_modules() -> list[Path]:
    out: list[Path] = []
    # All AI-named services + the central AI runtime package.
    for path in _SERVICES.glob("ai_*.py"):
        out.append(path)
    for path in _RUNTIME.rglob("*.py"):
        out.append(path)
    for path in _COGS.rglob("ai_*.py"):
        out.append(path)
    # The natural-language stage + the BTD6 context service (the AI
    # side of the M4 strategy flow).
    out.append(_RUNTIME / "natural_language_stage.py")
    return [p for p in out if p.exists()]


def _imports_fact_store(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.endswith("btd6_fact_store"):
                return True
            if node.module and node.module.endswith("btd6_sources"):
                return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in (
                    "services.btd6_fact_store",
                    "utils.db.btd6_sources",
                ):
                    return True
    return False


def test_no_ai_module_imports_btd6_fact_store():
    offenders: list[str] = []
    for path in _scans_ai_modules():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        if _imports_fact_store(tree):
            offenders.append(str(path.relative_to(_REPO)))
    assert not offenders, (
        "AI code path imports a BTD6 fact writer — route through "
        "btd6_strategy_mutation (audit + reversible) instead. "
        f"Offenders: {offenders}"
    )
