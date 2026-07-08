"""Gate 3: `architecture` (design-spec SS6) -- layer table, lazy-import ban, complexity
budget, symbol-shadowing pass.

Day-0 posture: SELF-ARMING with inline teeth.
  * Pre-kernel (no sb/**/*.py): asserts gates/architecture-rules.yml exists and its
    exception/allowlist ledgers are in virgin (empty) state, then passes. The rules file
    missing is a FAILURE even pre-kernel -- the gate's own config cannot rot away.
  * Armed (any sb/**/*.py exists): two inline checks run IMMEDIATELY with no dependency on
    kernel tooling -- (a) the SS1.6 function-body-import ban (AST scan, allowlist from the
    rules file), (b) the SS1.5 module-length budget (<= 500 lines). Additionally the full
    checker tools/check_architecture.py (an S1 deliverable, "from commit 1" of sb/ code)
    MUST exist and pass -- sb/ code without it is a red partial state, so the layer table +
    cognitive-complexity + symbol-shadowing passes cannot be deferred silently.
Arming trigger: the first sb/**/*.py file.
"""

from __future__ import annotations

import ast
import sys

from _gatelib import Gate, any_py, load_yaml, p, run

g = Gate("architecture")
RULES = p("gates", "architecture-rules.yml")


def inline_lazy_import_ban(allowlist: set[str]) -> list[str]:
    errors = []
    for f in sorted(p("sb").rglob("*.py")):
        tree = ast.parse(f.read_text(), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for inner in ast.walk(node):
                    if isinstance(inner, (ast.Import, ast.ImportFrom)):
                        key = f"{f.relative_to(p())}::{node.name}"
                        if key not in allowlist:
                            errors.append(
                                f"{key}:L{inner.lineno} function-body import "
                                "(SS1.6 lazy-import ban; allowlist is shrink-only)"
                            )
    return errors


def inline_module_length(max_lines: int) -> list[str]:
    return [
        f"{f.relative_to(p())}: {n} lines > {max_lines} (SS1.5 module budget)"
        for f in sorted(p("sb").rglob("*.py"))
        if (n := len(f.read_text().splitlines())) > max_lines
    ]


def main() -> None:
    if not RULES.exists():
        g.fail(
            "gates/architecture-rules.yml missing -- the gate's own layer table rotted away"
        )
    rules = load_yaml(RULES)

    if not any_py("sb"):
        if rules["complexity_budget"]["exceptions"]:
            g.fail(
                "pre-kernel but complexity exceptions ledger is non-empty (inconsistent)"
            )
        if rules["lazy_import_ban"]["allowlist"]:
            g.fail("pre-kernel but lazy-import allowlist is non-empty (inconsistent)")
        g.ok(
            "pre-kernel: no sb/ package yet; rules file present, ledgers virgin. "
            "Arms automatically on the first sb/**/*.py."
        )

    g.note("armed: sb/ package exists")
    errors = inline_lazy_import_ban(set(rules["lazy_import_ban"]["allowlist"]))
    errors += inline_module_length(int(rules["complexity_budget"]["lines_per_module"]))
    if errors:
        g.fail("inline checks:\n  " + "\n  ".join(errors))

    checker = p("tools", "check_architecture.py")
    if not checker.exists():
        g.fail(
            "sb/ code exists but tools/check_architecture.py does not -- SS1.1 requires the "
            "full checker 'from commit 1'; partial state is red, never silently green"
        )
    if (
        run(
            [sys.executable, str(checker), "--rules", str(RULES), "--mode", "strict"]
        ).returncode
        != 0
    ):
        g.fail("tools/check_architecture.py strict pass failed")
    g.ok("layer table + lazy-import ban + budgets green")


if __name__ == "__main__":
    main()
