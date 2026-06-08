---
description: "Mutation seams and direct-DB discipline for disbot/services and disbot/utils/db files"
globs:
  - "disbot/services/**/*.py"
  - "disbot/utils/db/**/*.py"
  - "disbot/governance/**/*.py"
---

# Mutation and DB — rules triggered before editing service or DB files

## Read these first
- `docs/ownership.md` — which service/pipeline owns each table and write.
- `docs/runtime_contracts.md` § 9 — mutation contract checklist.
- `docs/architecture.md` — layer boundaries (services must not import views).

## Run before editing
```
python3.10 scripts/context_map.py <file>   # blast radius + ownership
python3.10 scripts/check_architecture.py --mode strict
```

## Hard rules
- **Never** call `pool.execute()` or `conn.execute()` directly outside `utils/db/`.
- **Always** call `utils.db.[submodule_function]()` from service code.
- **Always** use `settings_keys` constants — never raw string keys to `db.get_setting()`.
- **Always** write through the domain's `*_mutation.py` service.
  No direct DB writes from cogs or views.
- **Always** call `services.audit_events.emit_audit_action()` for auditable mutations.
- A new mutation path that bypasses the audited service seam is an immediate blocker.

## Direct vs. draft lane
The lane choice is canonical in `docs/ownership.md` § "Direct vs. draft mutation lanes".
Pick by the *shape* of the change, not the panel you are in:
- Focused / reversible / single-domain → direct lane (through the audited service).
- Compound / multi-setting / generated → draft lane (`SetupOperation` rows, Final Review).
