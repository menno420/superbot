# 2026-06-10 — Queue remainder: RS07 chain service · RS08 read models · Help-Preview Tier-2 fix

**PR:** #671 (draft → ready at session end). **Prompt:** open-ended ("read the
docs, do the most useful thing, continue documented open work").

## Arc

Orientation route (CLAUDE.md → collaboration model → current-state ▶ →
consolidated plan §5/§8 → EOD audit §6) converged in minutes on the
implementation-ready remainder: the audit's §6 alternates 2 + 3-first-half are
exactly RS07 + RS08 + the Tier-2 Help-Preview drift — all bounded,
decision-free, and none stacking on the unverified-surface debt (which the
audit warns against; mining structures was deliberately *not* picked for that
reason). Verified queue truth live first (0 open PRs, HEAD = #669 merge).

## Shipped (one PR, three commits)

1. **RS07** — `services/chain_service.py` on the Batch 3 pattern (typed
   `ChainMutationResult`, old-value read, `emit_audit_action` with real
   `prev_value`; rejection paths write/emit nothing). Cog + all 4 modals
   converted; `chain_count` increment rides the service (sole-writer rule);
   repo-wide AST fence. Latent bug fixed: chain-create on a limit-only row no
   longer resets `word_limit` to 0 (pinned). `ownership.md` + exception-ledger
   rows updated (incl. two *other* stale ledger rows: mining + role-thresholds
   still said "no mutation service").
2. **RS08** — diagnostic builders render-only: sessions/anchors/schema-check
   SQL → owning `utils/db` modules; `xp/_helpers` rank SQL → the existing
   `rank_providers.member_rank` (its docstring named this consumer; migration
   was never finished). New class-killing invariant
   `test_no_raw_sql_in_cogs.py` (cogs/ + views/).
3. **Tier-2 fix** — Help Preview rebuilt on `project_help_with_execution`
   (first production consumer): governance-deny → Hidden (was "locked"),
   overlay hides/renames render, orphaned overlay rows get their first
   operator reporter. New public `access_projection.safe_locked_reason`.

**Verification:** CI mirror 8,840 passed / 22 skipped (+23 new); arch 0
errors; clean boot (0 errors); live Postgres round-trip (chain
create→dup→limit→no-change→delete with 3 correct audit events; read models
against the live schema; preview user 18 adv/11 hidden vs admin 29/0).

## Context delta

- **Needed but not pointed to:** that `services/rank_providers.py` exists and
  was *supposed* to own `_build_rank_embed`'s ranks — found only by grepping
  `ORDER BY xp DESC` before writing a new reader (the do-not-duplicate check
  that saved a wrong fix). No folio/route covers "canonical leaderboard/rank
  read path"; the games folio could name it.
- **Pointed to but didn't need:** nothing significant — the route
  (current-state ▶ → plan §5 banner → audit §6) was the most efficient
  orientation experienced in the logs I read; the per-lane bullet +
  queue-state banner conventions are paying off exactly as designed.
- **Discovered by hand:** (a) six consumer tests pinned the *old call shapes*
  (SQL text / `utils.db.fetchall` patches) — converting a seam means grepping
  tests for patch-paths, not just symbols (existing journal rule, confirmed
  again); (b) `_chunk_field` silently drops empty buckets (a "(0)" field never
  renders) — cost one wrong test assertion; (c) the exception ledger rows rot
  silently when seams ship — three rows were stale at once.
- **Decisions made alone:** (1) RS08's "service read models" implemented as
  `utils/db` owner-module functions, not a new `services/` wrapper — followed
  the file's own established idiom (`bindings_db.count_by_status` etc.);
  disposition noted in the plan's Batch 9 notes. (2) `record_chain_progress`
  rides the service unaudited (hot path) so the fence is exception-free.
  (3) Chain-create now preserves an existing word limit (behavior
  improvement, pinned, flagged in the PR body). (4) The `set_word_limit`
  no-change path skips write + audit (caller messages preserved).
- **Flagged for maintainer:** the chain panel's modals were live-verified at
  the service level, not click-through (no human in the sandbox guild this
  session) — the standing ~15-min production walk (audit §6) still covers
  it; nothing here widens that debt. The Help Preview's *hub button*
  click-path is unchanged (only the embed builder changed).
- **One change that would have helped:** a one-line "canonical read paths"
  note in the games folio (rank_providers) — filed via the grooming note
  below rather than a new doc.

## Grooming

Routed the EOD audit's Tier-4 stacked-PR-check idea (capture-only in a dated
audit) into the journal's process-tooling ideas list — its conveyor home;
build-only-if-recurs noted. Journal tidied: the migrations-count runbook line
de-numbered (it rotted twice in two days).

## Open after this session

The consolidated plan §5 banner is current: Batch 4 pointer tail · Batch 9
RS05/RS10 · Batch 10 (planning) · Help overlay editor UI (plan-first) — plus
the maintainer-only production walk, which the audit (and this session)
consider the single highest-value next action.

---

## Continuation (same session): Batch 4 complete + Batch 10 selections — PR #672

After #671 merged the maintainer said "continue with the plan" (+ confirmed
most commands working live; a dedicated eval session is coming). Picked the
two remaining non-observability queue items; deliberately did NOT pick
mining structures (waits for the eval/balance pass) or RS05/RS10 (own
focused session).

**Shipped (PR #672):**

1. **Batch 4 pointer tail → COMPLETE** — proof_channel promoted per audit §4:
   `cogs/proof_channel/schemas.py` (channel binding + OPTIONAL `proof`
   resource requirement), `proof_channel.settings.configure` capability,
   binding-first `get_proof_channel` with the name-`proof` legacy fallback
   (the Q-0064 pattern), panel/commands/modals async-converted; subsystem now
   an actionable Settings-hub group (taxonomy 11 → 12). Logging rows
   **verified satisfied** (7 bindings declared; `resolve_log_channel`
   binding-first; adapters classified) — disposition recorded, no code
   needed. Verified: identity contract clean at boot (STRICT=on); live
   Postgres binding round-trip (unbound→fallback · bound→wins ·
   deleted→degrade).
2. **Batch 10 → EXECUTED** — DT09: the wizard plan's PR1–PR3 tranche was
   **already shipped via #435** (attribution, readiness rollup +
   SETUP_PREFLIGHT_DIFF surfaced, flag-manager labels, advisor wire-in w/
   read-only invariant); the plan's "🟢 active" header was exactly the
   stale-status drift DT09 predicted → re-badged; **PR4 `/myprofile`
   selected** (planning session first). DT10: **§7.5 multi-entity
   comparison** selected (deterministic rank/diff + typed comparison
   evidence on the #634 template; profile-gated; **after the prod check**).

**Context delta (continuation):**

- **Discovered by hand:** the wizard finalization tranche being long-shipped
  (#435) — nothing routed to that fact; the plan's stale "🟢 active" header
  actively misled (now fixed at the source). Lesson: a `plan`-badged doc's
  *status header* is load-bearing; DT09-style re-verification before
  trusting any pre-2026-06 plan remains worth its cost.
- **Verification gotchas (smoke-script-side, not code):** binding rows use
  status `'bound'` (CHECK-constrained) + UUID mutation ids; the audit table
  is `binding_audit_log`. Worth knowing for future binding live-smokes.
- **Decisions made alone:** binding name `proof_channel` (self-describing in
  binding lists, matching `mod_channel` idiom); OPTIONAL provisioning
  priority (niche feature — info-only in readiness); §7.5 sequenced after
  the prod check (a second unverified AI family shouldn't stack on an
  unverified template).
- **Flagged for maintainer:** the eval session can now also click the
  Settings hub → proof_channel group (new) and `!prizemenu` (read path
  changed to binding-first; behavior identical while unbound).

**Open after continuation:** Batch 9 RS05/RS10 · Help overlay editor UI
(plan-first) · setup PR4 planning session · AI §7.5 (post-prod-check) ·
the maintainer's eval session.
