# /pre-pr

Run all pre-PR checks and report what must be fixed before pushing.

## What this does

1. **Architecture check (strict)** — `python scripts/check_architecture.py --mode strict --changed-only`
   - ERRORs block the PR. Fix every ERROR before continuing.
   - WARNs are pre-existing violations. Do not add new ones; do not ignore existing ones.

2. **Quality check** — `python scripts/check_quality.py --check-only`
   - Runs black, isort, ruff in check mode (no auto-fix — shows what's wrong).
   - Exit 1 means formatting or lint violations exist.

3. **Summary** — print a concise pass/fail table.

## Invocation

```
/pre-pr
```

No arguments. Always runs against the current branch diff vs `origin/main`.

## Instructions for Claude

When this skill is invoked:

1. Run `python scripts/check_architecture.py --mode strict --changed-only` and capture output + exit code.
2. Run `python scripts/check_quality.py --check-only` and capture output + exit code.
3. Print a table:

   | Check | Status | Detail |
   |---|---|---|
   | Architecture | ✅ PASS / ❌ FAIL | N errors, M warnings |
   | Formatting/Lint | ✅ PASS / ❌ FAIL | first failing file or "clean" |

4. If any check failed:
   - List each ERROR from the architecture check with file + line.
   - List each formatting violation from the quality check.
   - State explicitly: "These must be fixed before pushing."
5. If all checks passed: "Ready to push — all pre-PR checks pass."

Do not auto-fix architecture violations. Do auto-fix formatting if the user asks
(`python scripts/check_quality.py` without `--check-only`).
