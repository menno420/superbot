# Session — P0-4 PR 2: channel creation + category lifecycle convergence

**Date:** 2026-06-14 · **Branch:** `claude/gracious-ramanujan-a8nnjf` · **PRs:** #825 (code, merged), #826 (ledger follow-up)
**Class:** correctness (hardening P0) · **Continuation of:** issue #821 (Q-0100, P0-4)

## What shipped (#825)

Converged the **last two** uncovered channel-mutation paths — ad-hoc channel creation and
category lifecycle — under the audited `ChannelLifecycleService`, closing the final P0
integrity track.

- New **`ChannelLifecycleService.create_channels`** — the audited *manual-channel creator*,
  the channel-domain sibling of the allowlisted `RoleLifecycleService`. Bot-perm check →
  category resolve (by id) / get-or-create (by name) → safe-named text/voice create → typed
  per-name `LifecycleResult` (`StepResult.target_id` = new channel id) + audit companion +
  `channel.lifecycle_changed` event.
- 4 call sites routed off direct Discord: `channel_cog.manage_event`/`create_channel_with_role`/
  `bulk_create_channels` + `views/channels/create_panel.py`.
- Invariants: `test_no_direct_channel_mutations.py` now pins `create_text_channel`/
  `create_voice_channel`/category creation; `test_no_silent_auto_create.py` adds the service to
  the allowlist and **removes** `channel_cog` + `create_panel` (net tightening).
- 9 new `create_channels` unit tests; updated the panel multi-tests to drive the service.
- CI mirror green (9453); arch 0 errors.

## The design decision (Q-0100)

The handoff (#821) leaned "converge under `ResourceProvisioningPipeline`." Reading the pipeline
showed that's a **poor fit**: `provision()` is catalogue-driven — it resolves a
`(subsystem, binding_name)` option, checks the option's capability, *always* writes a binding row,
and its audit table is keyed on `subsystem`/`binding_name`. **Ad-hoc operator channels have no
binding**, so forcing them through it would need a synthetic binding + a nullable-column audit
migration + a step-8 bypass. Took the better path (Q-0014): own ad-hoc creation in
`ChannelLifecycleService` (sibling of the already-allowlisted `RoleLifecycleService`); subsystem-
*bound* creation stays on the pipeline. Documented the split in the readiness map + roadmap +
ownership.

## Drift caught

The readiness map marked `create_panel.py` "Done — uses the resource-provisioning lane," but the
source called `guild.create_text_channel` directly until this PR. Corrected the row; this drift
class motivated this session's idea (below).

## Process notes

- The dispatch arrived with a **contradictory flag** — `CLASS: correctness` ("build it") but
  `NOTES: read-only inspection only`. First ran it read-only and delivered a plan to #821; the
  owner then corrected: it should have been a build session. ~One cycle spent on a read-only pass
  that produced a plan an implementation session then re-walked.
- #825 auto-merged in ~2 min (before the `needs-hermes-review` label could block it — see Q-0127,
  the MCP-created-PR auto-merge gap). The `current-state` ledger edits made *after* the first push
  didn't ride along, so they went into #826; meanwhile the **band-#820 reconcile routine** merged
  to main, causing a conflict that a session-resume left mid-merge. Resolved by resetting to
  `origin/main` (which already had #825's code) and re-applying minimal ledger deltas.

## ⟲ Previous-session review (Q-0102)

The **read-only analysis pass earlier this session** did its job well — it correctly identified
P0-4 PR 2 as the top unblocked work, verified #821's claims against source, resolved the
provisioning-pipeline design wrinkle *before* any code was written, and caught the create_panel
doc-drift. Its one miss was structural, not its own fault: it was constrained read-only by a
mis-set dispatch flag, so the conclusion had to be re-derived by the implementation pass.
**System improvement:** the dispatch harness should reject/flag a payload whose `CLASS` (an
implement verb) contradicts its `NOTES` ("read-only inspection only") — contradictory steering
wastes a whole cycle. Captured the broader honesty-guard idea below.

## 💡 Session idea (Q-0089)

`docs/ideas/readiness-map-claim-vs-source-guard-2026-06-14.md` — a guard that fails when a
readiness-map / ownership row's routing claim ("routes through X", "Done") contradicts the cited
source file, reusing the channel invariants' forbidden-call sets. The structural version of the
per-PR `test_no_direct_*` invariants, lifted to the docs that *describe* them. Born directly from
the create_panel drift this session caught.

## Doc audit (Q-0104)

`check_docs --strict` clean (Recently-shipped held at 20/20 by archiving the #746–#754 entry to
offset #825). `check_current_state_ledger --strict` still flags #824/#827 — concurrent band-#821+
merges owned by the **next** reconcile pass (#840 boundary), not this manual session (Q-0124).
