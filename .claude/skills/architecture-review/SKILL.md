# /architecture-review

Perform a focused architecture review of the current branch's changes.

## What this does

- Finds all Python files changed vs `origin/main`.
- For each changed file, checks layer boundary compliance, mutation ownership,
  settings-key usage, and BaseView inheritance.
- Reports ERRORs (new violations that must be fixed) and WARNs (pre-existing
  tracked violations).
- Flags any file whose layer imports have changed vs what the YAML allowlists permit.

## Invocation

```
/architecture-review
/architecture-review disbot/services/some_service.py   # single file
```

## Instructions for Claude

When this skill is invoked with no argument:

1. Run `python scripts/check_architecture.py --mode strict --changed-only` and capture full output.
2. Parse the output into three buckets:
   - **Errors** — lines with `[ERROR]`
   - **Warnings** — lines with `[ WARN]`
   - **Passed** — "all checks passed ✓"
3. For each ERROR, explain:
   - Which layer rule it violates (from `docs/architecture.md` or `architecture_rules/layers.yaml`).
   - What the correct fix is (e.g., "move this import inside the function body",
     "route through the EventBus instead of importing the cog", "add to known_violations
     only if it is a genuine pre-existing case").
4. For each WARN, confirm it matches a known_violation entry in the YAML. If a WARN
   does NOT appear in `architecture_rules/layers.yaml` known_violations, escalate it
   to an ERROR and explain why.
5. Print a summary:

   ```
   Architecture review — branch: <branch>
   Changed files: N
   Errors: N  (must fix before merge)
   Warnings: N (pre-existing, tracked)
   ```

When invoked with a single file path, run the same check but scoped to that file only:
`python scripts/check_architecture.py --mode strict <file>`.

## Binding rules (do not relax these)

- `services/` MUST NOT import from `views/`. Zero tolerance — no known_violations
  entries are valid for this direction.
- `views/` MUST NOT import from `cogs/` at module level (function-body imports
  for Discord dispatch are allowed but must be minimised).
- New cross-layer imports that are not in `known_violations` are always ERRORs,
  never WARNs.
- Do not suggest adding a new entry to `known_violations` as a fix — that is only
  for cataloguing violations that existed before the rule engine was added.
