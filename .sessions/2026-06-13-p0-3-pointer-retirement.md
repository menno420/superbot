# 2026-06-13 — P0-3 arc PR 2: retire XP-announce + economy-log scalar pointers

**PR:** [#794](https://github.com/menno420/superbot/pull/794) (ready, auto-merge armed) ·
**Plan:** [settings pointer-lane convergence](../docs/planning/settings-pointer-lane-convergence-plan-2026-06-13.md) §3 ·
**Authoritative state:** `docs/current-state.md` (stamp line) + the plan (arc table §7).

## Arc

Executed the documented next step — P0-3 **arc PR 2**: retire the two
`binding_backed_convergeable` pointer settings so each Discord-resource pointer has one
canonical binding owner (no parallel editable scalar):
`xp.xp_announce_channel` → `xp.announce_channel`, `economy.economy_log_channel` →
`economy.log_channel`.

## Shipped

- **Deleted both scalar `SettingSpec`s** (+ validators / imports); `ECONOMY_SETTINGS` is
  now empty (binding remains).
- **`config_arbitration` — new `pointer_retired=True`**: a retired pointer reads
  binding-first *regardless* of the OFF-by-default `bindings.primary` canary flag. This
  is the load-bearing correctness fix (see Context delta). Legacy KV stays the rollback
  fallback. The two retired accessors opt in; everything else unchanged (additive).
- **`BindingMutationPipeline` — `actor_type='system'`/`'backfill'` support**: needed for
  the economy log-channel auto-provision on join (a system write). System writes record
  the bot's id as the audit `actor_id` (`binding_audit_log.actor_id` is NOT NULL);
  capability bypass lives in `actor_holds_capability`, mirroring the settings pipeline.
  Backward-compatible (keyword-only, default `'user'`).
- **Repointed writers → binding lane:** XP channel modal (set/clear), economy
  `_record_log_channel` (×3 sites). **Repointed stale legacy reads → arbitration:** XP
  config panel, economy `_ensure_log_channel`.
- **Adjacent bugs fixed:** `logging_presets.py` + `channels.py` hint maps keyed the
  economy/xp channel bindings by their legacy *settings* keys
  (`economy_log_channel`/`xp_announce_channel`) instead of the real binding names
  (`log_channel`/`announce_channel`) — so the economy-logs wizard preset was silently
  filtered out and the channel hints never fired.
- **Ledger:** emptied `CONVERGEABLE_POINTERS` + added `test_no_dual_declared_pointer`.
- Updated ~6 affected test files; updated plan / current-state / roadmap / the two
  command-map docs.

## Verification

- `check_quality.py --full` → 9328 passed, 34 skipped (lint + mypy clean).
- `check_architecture --mode strict` → 0 errors.
- `check_docs --strict` ✓ · `check_current_state_ledger --strict` ✓ · doc-pinning 70 ✓.
- **Real Postgres** (throwaway proof, swept): unconfigured→None; **bound binding +
  flag OFF → reads binding** (the retired-pointer proof); legacy-only → fallback;
  backfill classifier → CANDIDATE_VALID. Clean live boot (both cogs loaded, 0 errors).

## Context delta

- **Needed but not pointed to:** the plan §3 framed arc PR 2 as "turn-key / delete the
  scalar, keep legacy readable." Three things it did *not* surface, all discovered by
  reading source: (1) the **writers** (not just reads) were bound to the scalar
  SettingSpec, so retirement requires repointing them; (2) **`bindings.primary` is
  `default=False` and unflipped in prod** — so `config_arbitration` reads legacy-only
  and binding-only writes would be *invisible* after retirement (a latent prod break);
  (3) `BindingMutationPipeline` had **no system-actor path**, which is *why* the economy
  log channel was a scalar in the first place.
- **Pointed to but didn't need:** nothing material — the route (folio → convergence plan
  → source) was efficient.
- **Discovered by hand:** the flag-OFF read gap (biggest); the binding-pipeline
  system-actor gap; the two binding-name map bugs.
- **Decisions made alone:** (a) **Design A** — retired pointers decouple from the global
  flag (`pointer_retired`) rather than flipping `bindings.primary` ON globally (Design B
  would ship a prod break gated on a manual maintainer flag flip, which I won't do —
  deploys are the owner's). (b) Extending the binding pipeline for system actors. (c)
  Fixing the two adjacent binding-name bugs in scope. All contained/reversible/tested;
  documented in the PR + plan refinement note.

## Flagged for maintainer

- **Rollback semantics changed from the plan's stated mechanism.** For a *retired*
  pointer, "flip `bindings.primary` OFF" is **no longer** the rollback (that flag no
  longer governs it) — rollback is the still-live legacy-KV fallback + PR revert. The
  plan §3/§6 are updated to say so. Future retirements (families 3–5) must pass
  `pointer_retired=True` for the same reason.
- The real-Postgres proof was a **throwaway script**, not a committed integration test
  (the logic is locked by unit tests + the new invariant). A permanent real-PG
  integration test for the retired-pointer read would be a stronger net.

## Gates / next

- **Next P0** = arc PR 3 (delegated-apply authority, Q-0098 — design pinned in plan §4).
  Then P0-4 (channel-ownership, Q-0100) → P0-2 (media retention, Q-0099) → P1-1.

## 💡 Session idea

**Sunset the global `bindings.primary` flag in favour of per-key `pointer_retired`.**
This session showed the per-key retirement model (binding-first by completion, legacy as
fallback) is cleaner and safer to deploy than a guild-wide canary flip — it needs no
coordinated production flag flip. Once families 3–5 are retired and the *non-pointer*
migrated keys (governance roles) get a binding home (Q-0119), the global
`bindings.primary` flag governs nothing and can be removed. Captured as a follow-up in the
convergence plan rather than a new orphan idea file (its natural home). Worth it because a
dead-but-load-bearing-looking feature flag is exactly the kind of latent trap an agent
later works *around* instead of removing.

## ⟲ Previous-session review (the third Q-0107 reconciliation pass, #780/#781)

- **Did well:** the reconciliation pass made the single highest-leverage edit available —
  collapsing the `▶ Next action` line from a 15-line struck-through history wall to one
  scannable priority. That tightened line is exactly what let *this* session orient in
  minutes. Good instinct.
- **Missed / could improve:** it propagated "arc PR 2 is turn-key against §3" without the
  plan (or the readiness map it cites) having surfaced the **runtime feature-flag
  precondition** — that `bindings.primary` is OFF, so binding-only reads break until
  retired pointers are decoupled. "Turn-key" hid a real prod-safety gap.
- **Concrete system improvement (initiated):** planning/reconciliation docs that label a
  slot **"turn-key" / "unblocked"** should be required to state its **runtime
  preconditions** — feature-flag states it depends on, and any deploy/flag step the owner
  must take. A one-line "Deploy preconditions:" field per planned slot would have caught
  the flag-OFF gap at *plan* time instead of mid-build. (This is the same insight as the
  session idea, applied to the workflow rather than the code.) If genuinely nothing else
  to improve I'd say so — but this one is real and recurring (a plan under-specifying a
  runtime precondition).
