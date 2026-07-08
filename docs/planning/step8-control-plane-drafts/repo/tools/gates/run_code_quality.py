"""Gate 1: `code-quality` (design-spec SS6) -- format/lint/mypy/pytest under the pinned
interpreter; tool versions pinned in constraints/tools.txt (the ONE pin file).

Day-0 posture: REAL from birth, no stub tier.
  * ruff format/check runs over the whole repo (the gate scripts + kit files exist day 0).
  * mypy runs over tools/gates (self-hosting) + sb/ once it exists (auto-widens).
  * pytest runs the suite; tests/test_gate_arming.py exists from day 0, so "no tests
    collected" (pytest exit 5) is a FAILURE -- the suite vanishing can never read as green.
Arming trigger for the sb/ scope: the first sb/**/*.py file widens mypy automatically.
"""

from __future__ import annotations

import sys

from _gatelib import Gate, any_py, p, run

g = Gate("code-quality")


def sh(cmd: list[str], what: str) -> None:
    g.note(f"$ {' '.join(cmd)}")
    if run(cmd).returncode != 0:
        g.fail(f"{what} failed")


def main() -> None:
    py = sys.executable

    sh([py, "-m", "ruff", "format", "--check", "."], "ruff format --check")
    sh([py, "-m", "ruff", "check", "."], "ruff check")

    mypy_targets = ["tools/gates"]
    if any_py("sb"):
        mypy_targets.append("sb")
        g.note("sb/ detected -> mypy scope widened (armed)")
    else:
        g.note("pre-kernel: no sb/ package; mypy runs over tools/gates only")
    sh([py, "-m", "mypy", *mypy_targets], "mypy")

    if not p("tests").is_dir():
        g.fail(
            "tests/ directory missing -- the day-0 arming tests must exist (anti-rot)"
        )
    r = run([py, "-m", "pytest", "-q"])
    if r.returncode == 5:
        g.fail(
            "pytest collected no tests -- the suite vanished; this gate never passes empty"
        )
    if r.returncode != 0:
        g.fail("pytest failed")

    g.ok("format+lint+mypy+pytest green under the pinned toolchain")


if __name__ == "__main__":
    main()
