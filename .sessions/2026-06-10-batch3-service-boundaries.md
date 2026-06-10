# 2026-06-10 — Batch 3: service-boundary fixes (PR #652)

**Arc:** continuation session (same chat as the Batch 1 lane, resumed after #650
merged): synced onto main (#649/#651 in), executed the consolidated plan's
**Batch 3** (RS03 · RS06 · RS17; RS07 deliberately deferred) end-to-end, full CI
mirror green, draft PR at first push → ready at session end.

**Shipped (PR #652 — verify merged):**

- **RS03** — `services/command_routing.set_policy` became the canonical routing
  mutation owner: old-row read (real `prev_value`) → upsert → best-effort
  `audit.action_recorded` → typed `RoutingMutationResult`. New import-fence
  invariant `test_no_direct_command_routing_writes.py` (only the service may
  import `utils.db.command_routing`).
- **RS17** — the setup dispatcher's `set_cog_routing` arm thinned to
  validation + result consumption (its private uuid/audit machinery deleted).
- **RS06** — `role_automation.clear_time_threshold` / `clear_xp_threshold`
  added (old-row read for prev_value + id-keyed target → field-specific clear →
  XP-cache invalidate → audit emit); the three direct clear sites migrated
  (both remove-selects + `!unsetrole`); the threshold invariant widened to
  fence setters **+ clears + `remove_role_threshold`**.
- `docs/ownership.md`: `command_routing_policy` row added to Platform
  ownership; role row + NORMALIZED drift note updated.

**Deferred:** RS07 (chain service extraction) — optional slice, new-service
design; deserves its own PR. Stays queued in Batch 3's card.

## Decisions made alone (ratify if they matter)

1. **Routing fence = import-level**, not attribute-call AST (the module is
   consumed as a module object; `set_one`/`get_one` are too generic to scan).
2. **`audit_emitted` keeps the publish-accepted convention** of every sibling
   pipeline — Batch 9 (RS05) owns renaming/hardening those semantics globally;
   not relitigated here.
3. **Caller-side `invalidate_xp_threshold_roles` calls kept** after the seam
   migration (seam also invalidates → harmless double drop) — the
   `test_xp_cog_caching` invariant requires the *import to be used*, and an
   unused import would be auto-stripped by the ruff hook.
4. **Clear methods read the old row** for prev_value/id-keyed targets even
   though the P0C setters pass `prev_value=None` — for a removal, the previous
   value IS the audit row's information content. Setters left as-is (their
   upgrade wasn't in scope and touches no honesty bug).

## Flagged for maintainer / known limits

- Routing audit is still event-only (no routing audit *table*); write+audit
  atomicity would need a schema change — explicitly stopped by the batch card.
  The event now carries real prev_value, which closes the actual RS03 gap.
- The setters (`set_time/xp_threshold`) still emit `prev_value=None`; the
  clears don't. Symmetric prev-value on setters is a small follow-up if wanted.

## Context delta

- **Needed but not pointed to:** the dispatcher tests' mocked `set_policy`
  (bare `AsyncMock`) would have silently passed Mock objects into
  `SetupOperationResult.mutation_id` after the result change — found only by
  reading the tests; typed-result returns in mocks are now the pattern there.
- **Pointed to but didn't need:** nothing notable; the batch card's file list
  was exact.
- **Discovered by hand:** `remove_role_threshold` (full-row delete) has zero
  callers anywhere — fenced preventively; the routing DB module is imported by
  exactly one module (clean baseline made the import fence trivial).
- **One change that would have helped:** none — the RS03/RS06 evidence lines
  (file:line) were current except for one shifted line number (role_cog clear
  moved 482→510; trivially re-grepped).
