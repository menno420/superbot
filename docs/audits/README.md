# Audits & reviews index

> **Status:** `reference` — index of point-in-time audits, reviews, and investigations under
> `docs/audits/`. Each audit is a dated snapshot of findings; **source code and merged PRs win**
> over any audit. New audits: add a row here so they stay reachable (`check_docs` reachability).

Audits are *investigations*, not contracts — they record what was true and what was decided at a
moment, and the reasoning behind it. Read the binding docs (`architecture.md`, `ownership.md`,
`runtime_contracts.md`) for current rules; read audits for *why* and for historical context.

## Investigations

- [`fleet-doctrine-enforcement-audit-2026-07-10.md`](fleet-doctrine-enforcement-audit-2026-07-10.md)
  — adversarial audit of fleet-manager gen-2 blueprint/playbook doctrine against public repo evidence: enforcement inventory, falsified claims, and top prose-only risks.
- [`../analysis/server-management-audit-2026-07-08.md`](../analysis/server-management-audit-2026-07-08.md)
  — server-management contract-vs-code audit (Wave-1 lane A, docs-only): runtime seams conform
  (0 RISKY); 6 LOW findings — ownership.md/folio drift on reaction-role tables, channel-lifecycle
  scope, server-logging v2, plus a missing reaction-role write-boundary invariant.
- [`dashboard-autopr-conflict-rootcause-2026-06-21.md`](dashboard-autopr-conflict-rootcause-2026-06-21.md)
  — why the automated `bot/dashboard-refresh` PR conflicts (volatile generated-file metadata), the
  fixes shipped, and the carried-forward analysis of the wider "CI doesn't fire / false-`dirty`"
  GitHub flakiness + a forensics plan.

## Earlier audits (subsystem & repo reviews)

- [`repo-review-2026-06-09.md`](repo-review-2026-06-09.md) — full repo review.
- [`agent-memory-system-review-2026-06-09.md`](agent-memory-system-review-2026-06-09.md) — did the
  orientation/memory system work in practice?
- [`implementation-readiness-review-2026-06-06.md`](implementation-readiness-review-2026-06-06.md)
- [`cog-hub-coverage-audit.md`](cog-hub-coverage-audit.md) ·
  [`mutation_boundary_audit.md`](mutation_boundary_audit.md) ·
  [`helper-debt-inventory.md`](helper-debt-inventory.md) ·
  [`direct-db-exception-ledger.md`](direct-db-exception-ledger.md) ·
  [`general-feature-layer-analysis-2026-06-05.md`](general-feature-layer-analysis-2026-06-05.md)
- 2026-06-05 agent sweep: [`agent-b-governance-control-audit-2026-06-05.md`](agent-b-governance-control-audit-2026-06-05.md)
  · [`agent-d-btd6-ai-subsystem-audit-2026-06-05.md`](agent-d-btd6-ai-subsystem-audit-2026-06-05.md)

*(Not every historical audit is listed — `ls docs/audits/` for the full set. Add new audits here.)*
