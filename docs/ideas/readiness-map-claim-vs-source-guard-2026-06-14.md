# Idea — a doc-claim ↔ source guard for readiness maps & ownership rows

> **Status:** `ideas` — captured 2026-06-14 (P0-4 PR 2 session). Tooling lane. Small/safe.
> **Provenance:** surfaced directly by a real drift this session caught.

## The problem it kills

Production-readiness maps and `ownership.md` rows make **routing claims** about source:
"routes through `X`", "uses the resource-provisioning lane", "audited via `Y`", "Done".
Nothing verifies the claim against the code, so a row can assert a convergence that the
source doesn't actually have — a silent, confidence-eroding lie that misroutes the next agent.

**Concrete instance (this session):** the server-management readiness map marked
`views/channels/create_panel.py` **"Done — uses the resource-provisioning lane,"** but the
source still called `guild.create_text_channel(...)` directly until P0-4 PR 2 converged it.
The drift sat unnoticed across the original audit *and* the band-#800 reconciliation pass.
It was caught only because a human-style read happened to open the file.

## The guard

A lightweight checker (custom, on the repo's AST/grep — the
`check_no_*`/`settings_lane_matrix.py` family is the precedent) that, for a small set of
**machine-checkable claim phrases**, fails when the cited source contradicts the claim:

- A row that says a channel/role/category path is **converged / audited / routes through a
  lifecycle service** ⇒ the cited file must NOT contain a direct `guild.create_*` /
  `.set_permissions` / `.edit` / `.delete` call (reuse the `_FORBIDDEN`/`_FORBIDDEN_CREATE_METHODS`
  sets the two channel invariants already define — single source of truth).
- Inversely, a file on a "still direct / Partial" row **should** still contain one (so the row
  can't quietly go stale in the other direction either).

Scope it narrowly to the routing-convergence vocabulary first (that's where the harm is);
do **not** try to parse free-form prose. The map row already names its source file in the
`Path` column, so the mapping is mechanical.

## Why it's first-class

This is the structural version of the per-PR `test_no_direct_*` invariants, lifted one level
up to the **docs that describe** those invariants. The invariants keep the *code* honest; this
keeps the *map* honest. It converts "an agent happened to read the file" into a CI signal, and
it would have caught the create_panel drift the moment it was written.

## Disposition

- **Lane:** tooling / grooming. Runtime-adjacent (`scripts/` + `tests/unit/docs/`), so not a
  docs-only self-merge — a small focused PR.
- **Reliability header (per Q-0105):** when built, mark it *unverified — confirm its
  claim-detection against ground truth across a few sessions before trusting it; delete if it
  proves noisy/unreliable over multiple sessions.*
- **Size:** small. One claim-vocabulary table + one AST pass + a handful of fixture rows.
