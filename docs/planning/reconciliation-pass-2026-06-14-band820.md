# Reconciliation pass — 2026-06-14 · the band-#820 Q-0107 cadence pass

> **Status:** `historical` — superseded by the [band-#840 pass](reconciliation-pass-2026-06-14-band840.md)
> (which scores this band's #821–#840 queue in its §2). The docs-only review + planning pass for
> the band that crossed
> **#820** (cadence = every 20th merged PR; previous cadence pass
> [#803, band #781–#800](reconciliation-pass-2026-06-13-band800.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#822**
> (`.github/workflows/reconciliation-trigger.yml`) — the **third** consecutive real cadence
> fire of the autonomous issue-trigger (after #781, #801), so the self-fire path is now
> routine.
> Sections: §1 verified state · §2 band scorecard · §3 priorities restated · §4 the next
> ~9 PRs · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#820** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the #803 pass (band #801–#820):** #802 (substrate-kit PR 1b tail — stdlib
checker ports), #803 (the band-#800 reconciliation pass itself), #804 (substrate docs), #805
(substrate PR 2 — stances), #806 (workflow rules Q-0124/Q-0125), #808 (issue-spec
preservation), #810 (session-close), #811 (substrate PR 2 — skills), #812 (substrate PR 2 —
personas), #813 (substrate PR 2 — stance-guard hook), #814 + #815 (the CI-efficiency arc),
#816 (session-close), #817 (hardening P0-3 arc PR 3 — delegated-Setup apply, Q-0098), #818
(#817 merge note + Q-0127), #820 (hardening P0-4 PR 1 — channel clone/overwrite convergence,
Q-0100). *(#807/#809/#819 are gaps — closed/unmerged PRs or scheduled `continue` issues; #819
was the scheduled continue-issue that drove #820.)*

**Open PRs at pass time (disposition — Q-0125):** only **#704** (the owner's "screenshots from
live testing" PR — left open, owner's). The two stale PRs the previous passes flagged —
**#766** (orientation ideas) and **#771** (redundant ledger PR) — are **no longer open**
(closed/merged since #803), so the Q-0125 disposition gap is clear this band. No red-CI or
conflicted `claude/*` PR is rotting.

**Ledger drift found and fixed.** `check_current_state_ledger --strict` reported **12 missing
merged PRs** at pass start (#803, #805, #806, #808, #810, #811, #812, #813, #814, #815, #816,
#818) — the normal between-pass lag now that the masking-range trap is gone (the band-#800
pass's §6 fix is working: the live pointer no longer carries a PR-number range, so the checker
correctly forces a real entry per merged PR). §5 lists the real entries this pass added.

The band's spine **was** the planned production-hardening P0 queue this time — the strongest
plan-fidelity band since #763. P0-3 completed (arc PR 3, #817) and P0-4 advanced to its
half-way point (#820). The owner's substrate-kit thread continued in parallel (PR 2 capability
layer complete), and an unplanned-but-high-value CI-efficiency arc (#814/#815) consumed the
buffer slot.

- **Hardening P0-3 COMPLETE (#817, arc PR 3 — delegated-Setup apply authority, Q-0098).** A
  bounded `actor_type="setup_delegate"` authorized at the capability floor, minted only by
  `apply_operations` after a live `can_apply_setup` re-check, threaded to all three capability
  pipelines (migration 069 widens the audit CHECKs), AST-fenced. Closed the "you may apply,
  then every per-op write fails" gap for an owner-delegated non-administrator.
- **Hardening P0-4 PR 1 (#820, channel clone + overwrite convergence, Q-0100).**
  `.set_permissions()`/`.clone()` pinned by the channel-mutation invariant, routed through
  `ChannelLifecycleService` (new `set_overwrite`/`clone` ops, guild-resource resolution, audit
  branches); the `!list` paginator extracted out of `channel_cog.py` (layering smell removed).
  **PR 2 (creation/category under `ResourceProvisioningPipeline`) carried.**
- **Substrate-kit PR 1b tail + PR 2 capability layer COMPLETE (#802, #805, #811, #812, #813).**
  The stdlib checker ports, then task-stances + skills + personas + the PreToolUse stance-guard
  hook (stances enforced). Owner-steered; resume at the PR-2 remainder (modes + contract
  templates + triggers).
- **CI-efficiency arc (#814 + #815, Q-0126).** Concurrency-cancel + caching + the claim-ledger
  convention, then a parallel-safe suite (`pytest -n auto`, ~3× speedup) after root-fixing
  three leaked process-global singletons.
- **Workflow rules (#806):** Q-0124 (manual sessions don't run the reconciliation pass — the
  routines do, automatically) + Q-0125 (passes must disposition stale open PRs). **Q-0127
  (#818):** the auto-merge-enabler doesn't fire for MCP-created PRs.

## 2. Band scorecard (the #803 pass §4 queue, band #801–#820 → reality)

| Slot (from the #803 pass §4) | Outcome |
|---|---|
| 1 · the pass itself | ✅ #803 |
| 2 · P0-3 arc PR 3 (delegated-apply) | ✅ #817 |
| 3 · P0-4 channel-ownership convergence | 🟡 **half** — PR 1 (clone+overwrite) ✅ #820; PR 2 (creation/category) **carried** |
| 4 · P0-2 media/YouTube retention | ❌ → **carried (slot 3 below)** |
| 5 · P1-1 eval-smoke matrix | ❌ → **carried (slot 4 below)** |
| 6 · substrate-kit 1b tail + PR 2 | ✅ #802 (tail) + #805/#811/#812/#813 (PR 2 complete) |
| 7 · security service tiers 1+2 | ❌ → **carried (slot 5 below)** |
| 8 · welcome phase 2 (PIL cards) | ❌ → **carried (slot 6 below)** |
| 9 · P1-2 health findings lifecycle | ❌ → **carried (slot 8 below)** |
| 10 · buffer / steered | consumed by the **CI-efficiency arc** (#814/#815) + workflow rules (#806/#818) + session-closes (#810/#816) |

**~4 of 10 slots executed to plan (pass · P0-3 PR 3 · half of P0-4 · substrate PR 2), plus a
high-value unplanned CI-efficiency arc** — the best plan-fidelity band since #763. The P0 spine
genuinely advanced: P0-3 is done, P0-4 is half done. The lesson holds — the plan is a default,
and an unplanned arc that removes a real cost/failure class (CI minutes, flaky parallel tests)
is not make-work.

## 3. Priorities restated (what the next band is for)

Unchanged in shape from the #803 pass — the band executed the queue rather than displacing it,
so the priorities simply advance one notch. The **standing priority is the production-hardening
P0 spine, integrity-first** — every gating decision is answered (Q-0099/Q-0100 + Q-0097), so
nothing waits on the owner:

1. **Finish the P0 integrity spine** — **P0-4 PR 2** (channel creation/category under
   `ResourceProvisioningPipeline`, Q-0100 — resume recipe in the open `continue` issue; the
   wrinkle to design: ad-hoc operator `!create`/`!evt`/`!bulkcreate` channels have no declared
   binding), then **P0-2** (media/YouTube retention + data-minimization, Q-0099). These close
   real harm classes: audit-trail gaps on channel ops, indefinite raw-payload retention.
2. **P1 correctness** — the versioned AI/BTD6 eval-smoke matrix (P1-1, relates **BUG-0009**) +
   the BTD6 absence-claim guard, then P1-2 health findings lifecycle (Q-0097 answered).
3. **The substrate-kit continues in parallel as the active owner thread** — resume at the PR-2
   remainder (modes + contract templates + triggers) → PR 3. Owner-steered.
4. **The safety/community remainder** (plan-first) — security service tiers 1+2 (Q-0111), image
   moderation (Q-0108), welcome phase 2 PIL cards (small, prototype exists), the NL event
   scheduler (Q-0112, own AI-cost design under the €30/mo ceiling).
5. **The autonomous loop runs in parallel, calibrating** — this pass is its third clean cadence
   fire. Still **one maintainer secret (`ROUTINE_PAT`) from live** for the bot-authored trigger
   path; the (working) ledger checker is the net.
6. **Owner-led in parallel:** add `ROUTINE_PAT` · the P1-4 live walks · `!uxlab` walk · #704
   disposition.

## 4. The next ~9 PRs (band #821–#840)

> Modular but not over-segmented (Q-0107): each slot is a real slice. Numbers are
> **sequence, not reserved PR numbers**. Owner steers override freely; note swaps here.
> Ordered so the highest-value (P0 integrity) comes first, with the active substrate thread
> interleaved where it is the owner's focus.

| # | PR (one session each) | Scope anchor | Gate |
|---|---|---|---|
| 1 | **This pass** — reconcile (the 12 between-pass entries) + plan + disposition open PRs | Q-0107 (issue #822) | — |
| 2 | **P0-4 PR 2 — channel creation/category convergence** | [hardening §P0-4](production-readiness/hardening-roadmap-2026-06-12.md); converge `create_*`/category under `ResourceProvisioningPipeline`, extend the channel invariant to pin `create_*`; design the ad-hoc-operator-create binding gap | Q-0100 (answered); resume recipe in the `continue` issue |
| 3 | **P0-2 — media/YouTube retention + data-minimization** | [hardening §P0-2](production-readiness/hardening-roadmap-2026-06-12.md); bounded projection, wire `purge_expired_video_cache` through the managed-task owner, fix `YOUTUBE_CONTEXT_ENABLED` ownership | Q-0099 (answered) |
| 4 | **P1-1 — versioned AI/BTD6 eval-smoke matrix + BTD6 absence-claim guard** | [hardening §P1-1](production-readiness/hardening-roadmap-2026-06-12.md); gates/fallback/tool-use/grounding-refusal/audit; implements the absence-claim guard (relates **BUG-0009**) | needs prod-like creds for the live half |
| 5 | **Safety lane — security service tiers 1+2** (plan-first) | Q-0111 — raid detection + account-age filter (tiers 3+4 declined); cite `ux/pattern-library.md` `mock_security_*` pattern_ids | family plan; plan-first |
| 6 | **Safety lane — welcome phase 2 (PIL cards)** | Q-0110 — the `render_welcome_card` prototype exists; small follow-up on the stable embed-first v1 | quick-win |
| 7 | **Substrate-kit PR 2 remainder + PR 3** (owner-steered, active thread) | [extraction plan §Execution log](portable-substrate-kit-extraction-2026-06-13.md) — modes + contract templates + triggers, then the next layer | owner-approved; resume recipe pinned |
| 8 | **P1-2 — health findings lifecycle + retention** | [hardening §P1-2](production-readiness/hardening-roadmap-2026-06-12.md); transition findings through the sole `health_findings_service` writer + scheduled retention | Q-0097 (answered) |
| 9 | **P1-3 invariants — one per shipped P0 track** | [hardening §P1-3](production-readiness/hardening-roadmap-2026-06-12.md); land the parity/fence invariant for each P0 as it ships (not a mega-session) | — |
| 10 | **Buffer / steered slot** — likely more substrate-kit, or owner-steered product work (mining V-16 phase 2 / BTD6 decode), or the ledger-checker range-scope runtime fix ([idea](../ideas/ledger-checker-range-scope-2026-06-13.md)) | in-flight / owner-led | — |

**Deliberately *not* in this band** (unchanged unless the owner steers): the NL event scheduler
build (Q-0112 — own AI-cost design first) · P1-4 owner live-walks (owner-led) · myprofile PR A ·
mining V-16 phase 2 (owner PNG pack) · the §7.5 structures / §7.4 skill tree · the CV2-adoption
ADR (wants the owner's `!uxlab` walk) · the substrate-kit public-OSS productization phase
(separate, later) · the Hermes bug-triage build (gated Q-0121) · candidate-rule promotion
(gated Q-0120).

## 5. Pruned / fixed by this pass

- **Ledger reconciled.** Added four consolidated `Recently shipped` entries covering the 14
  recorded band PRs: **#820** (P0-4 PR 1), **#814 + #815** (CI-efficiency arc), **#802 + #805 +
  #811 + #812 + #813** (substrate-kit 1b tail + PR 2), and **#803 + #806 + #808 + #810 + #816 +
  #818** (reconciliation + workflow rules + session-close housekeeping). #817 was already in the
  ledger from its own session. Trimmed the four oldest live entries (#741, #742, #745, #748) into
  [`current-state-archive.md`](../current-state-archive.md) to hold the ratchet at 20.
- **[reconciliation-pass-2026-06-13-band800.md](reconciliation-pass-2026-06-13-band800.md)
  re-badged `historical`** — its band (#801–#820) is fully scored in §2 above.
- **`docs/current-state.md` ▶ Next action re-pointed** at *this* doc (by name/date, no PR-number
  range — the band-#800 §6 discipline) and the **P0-4 PR 1 shipped / next = P0-4 PR 2** state
  restated.
- **`docs/roadmap.md`** — the live-decade-queue pointer and the **Now** horizon re-pointed from
  the #803 pass to this pass.
- **Open-PR disposition (Q-0125):** verified only the owner's #704 is open; the previously-flagged
  #766/#771 are closed. Nothing to prune.
- **Marker reset** — `Last reconciliation pass` → **#820**; `check_reconciliation_due.py` next
  fires at #840.
- **No runtime bugs noticed** (docs-only pass) → nothing appended to the bug book; BUG-0009 /
  BUG-0011 stay OPEN for the caretaker/AI lanes.

## 6. The system improvement this pass made (the point of the loop)

The band-#800 pass's masking-range fix **held**: this pass started with the ledger checker
reporting an honest 12-PR gap (not a false green), which is exactly the behavior the fix was
meant to restore. So the headline this time is not a guard bug — it is the **Q-0125 disposition
step proving its worth on its first full run**. The band-#800 pass *flagged* #766/#771 as stale
but, being a planning doc, could only recommend; this pass confirmed both are now closed, so the
"stale open PR rots across passes" failure (#766/#771 the original evidence) did not recur. The
durable improvement captured here: **every pass's §1 must list open PRs with their state**, so
the disposition is a recorded fact, not a recommendation — a future pass can diff against it. This
pass added that as a standing section shape (it is now in §1 of both the band-#800 and this doc),
which is the cheapest possible guard against the rot class: visibility in the record itself.

The idea this pass contributes (Q-0089) is in `docs/ideas/` — a self-auditing improvement for the
*next* reconciliation, not this one.
