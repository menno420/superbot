# 2026-07-08 — Audit: server-management contract-vs-code audit (docs-only)

> **Status:** `complete`
> **Run type:** owner-directed · Wave-1 lane A (AUDIT) of the 3-lane campaign. PR **#1844**.
> Branch: `claude/audit-server-management-2026-07-08`.

**Intent (start declaration):** audit the server-management subsystem against its own
contracts (folio, architecture.md, ownership.md, runtime_contracts.md) and ship a
prioritized findings report. Docs-only session — no runtime code changes; anything
runtime-risky flagged RISKY, never changed.

## What shipped

- **`docs/analysis/server-management-audit-2026-07-08.md`** — the audit report.
  Headline: **the runtime seams conform** (all spot-checked mutation paths route
  through their audited services; `check_architecture --mode strict` 0 errors; the 5
  server-management write-boundary invariant suites 15/15 green). **6 LOW findings,
  0 RISKY**: F1 ownership.md has no owner for the five reaction-role-overhaul tables
  (`role_menus`/`role_menu_options`/`reaction_role_message_modes`/`role_grants`/
  `role_menu_pickup_stats`, migrations 078–081); F2 ownership.md:46 contradicts
  ownership.md:87 + code on ChannelLifecycleService scope (clone/overwrite/create/
  slowmode/topic are owned since P0-4/Q-0100); F3 `channel.lifecycle_changed` payload
  row documents 4 of 9 operation values; F4 the server_logging row is stale at v1
  (v2 audit-log/voice/raw-delete listeners shipped, #1594/#1618/#1619); F5 the folio
  still says clone/overwrites/creation are outside the lifecycle service; F6 no AST
  write-boundary invariant fences the reaction-role tables (every neighboring seam
  has one). Best Wave-2 dispatch: **F1 batched with F2–F5 as one docs-only
  "ownership/folio truth refresh"**; F6 as the tests-only second.
- Reachability: index row in `docs/audits/README.md` + a Related-docs line in the
  server-management folio. `check_docs --strict` ✓.

**Findings are deliberately NOT fixed in this session** — audit-only lane; each
finding carries its proposed durable fix for a follow-up session.

## Session enders

- **💡 Session idea:** a `scripts/check_event_ownership_parity.py` checker — parse
  `core/events_catalogue.KNOWN_EVENTS` and require name-level parity with the
  ownership.md "Event ownership" table (every catalogued event has a row, every row
  names a catalogued event). This session's F3/F4 drift class (event/payload rows
  silently lagging shipped emitters) is exactly the kind of restatement drift a cheap
  mechanical checker catches at CI instead of at the next manual audit
  ("enforce, don't exhort", Q-0132). Dedup-checked `docs/ideas/` — the nearest match
  (agent-tooling-automation-shortlist "where does X live" query tool) is a different
  concern.
- **⟲ Previous-session review:** the band-#1830 reconciliation pass
  (`2026-07-08-reconcile-band1830.md`) was clean and complete — proper Q-0125 open-PR
  disposition, honest control-plane SKIP note, no THIN flag with reasoning. One
  genuine improvement it surfaces: reconciliation passes verify the *ledger* against
  merged PRs but never sample the **binding docs** against code — ownership.md rows
  this audit found stale (F1/F2/F4) drifted through 38 reconciliation passes
  untouched. A cheap addition: each pass spot-checks one binding-doc section against
  source (rotating), or the audit-lane pattern (this session) runs periodically per
  subsystem.
- **Documentation audit (Q-0104):** `check_current_state_ledger.py --strict` exit 0
  (only benign newest-merge lag above marker #1830 — the Q-0166 exception);
  `check_docs.py --strict` ✓; new doc indexed in `docs/audits/README.md` + folio.
  No owner decisions were made this session (audit only) — nothing to route to the
  question router. Backlog grooming (Q-0015): this session's report itself moves the
  audit-campaign lane forward (Wave-2 dispatch candidates ranked); no additional idea
  promoted — capacity went to the audit's verification depth.
- **⚑ Self-initiated:** none — all work was the owner-directed audit task.
