# Idea — a shared `effective_check_constraint(table, column)` test helper

> **Status:** `ideas` — not approved. Captured 2026-06-14 (P0-3 arc PR 3 session, PR #817).
> Small/safe tooling improvement; **grooming-lane candidate** (build + migrate the 3 existing
> alignment tests onto it).

## The pain

Several invariant tests pin a Python `frozenset` to a SQL `CHECK (col IN (...))` literal so the
two can't drift (`test_settings_mutation_audit_alignment`, `test_resource_provisioning_audit_alignment`,
`test_setup_draft_op_kind_parity`). Each one hard-codes a single `_MIGRATION` path and a bespoke
regex. **When a constraint is widened in a *later* migration** (the only safe way — migrations are
append-only), the alignment test has to be **manually repointed** to the new migration, or it
silently keeps reading the stale set:

- migration **059** moved `setup_draft_operations.op_kind` → its parity test reads 059, not 035.
- migration **069** (this PR) moved the settings/resource `actor_type` CHECK → the two alignment
  tests grew a second `_ACTOR_TYPE_MIGRATION` pointer + a second bespoke extractor.

The repointing is exactly the silent-staleness the alignment test exists to prevent — a drift-guard
that itself goes stale when the thing it guards evolves. (Same class as the ledger-checker
range-expansion fix the band-#800 reconciliation pass deferred.)

## The idea

One shared helper — `tests/unit/invariants/_constraint_alignment.py`:

```python
def effective_check_constraint(table: str, column: str) -> set[str]:
    """The CURRENT allowed literal-set for table.column, derived by scanning
    every disbot/migrations/*.sql in order and applying the LAST definition
    (inline CHECK or a later ADD CONSTRAINT ... CHECK (column IN (...)))."""
```

Then each alignment test becomes one line — `assert effective_check_constraint("settings_mutation_audit",
"actor_type") == set(_ALLOWED_ACTOR_TYPES)` — and **never needs repointing** when a constraint moves.
It also catches a constraint widened in SQL but not in Python (and vice-versa) regardless of which
migration owns it.

## Scope / why it's safe

- Pure test-infra; no runtime change. Tests/ only.
- Migrate the 3 existing alignment tests onto it in the same PR (delete their bespoke regexes).
- Handles both inline column/table CHECKs and `ADD CONSTRAINT ... CHECK` ALTERs; "last wins" by
  migration number gives the effective DB shape.
- Edge: a `DROP CONSTRAINT` with no re-add (rare) should make the column unconstrained — handle or
  assert it's not used.

## Provenance

Re-derived the bespoke extractor twice in one session (PR #817). Per Q-0105: **unverified** — confirm
the helper's "last definition wins" matches the live DB shape (boot + `pg_get_constraintdef`) a couple
of times before trusting it as the sole alignment guard; **delete it if it proves unreliable over
multiple sessions.**
