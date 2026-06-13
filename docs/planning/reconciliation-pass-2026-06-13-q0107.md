# Reconciliation pass — 2026-06-13 · the third Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed
> **#780** (cadence = every 20th merged PR; last cadence pass
> [#763](reconciliation-pass-2026-06-12-night.md)). Triggered by the auto-opened
> `reconcile` issue **#781** (`.github/workflows/reconciliation-trigger.yml`) — the
> first time the autonomous issue-trigger fired a real cadence pass. Sections:
> §1 verified state · §2 band scorecard · §3 priorities restated · §4 the next ~9 PRs
> · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#780** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the #763 pass:** #764, #765, #767, #769, #770, #772, #774, #775, #777,
#778, #780 (#766, #771, #779 are open, not gaps — see below). Both audit checkers are
**green** at pass start (`check_current_state_ledger --strict`: last 15 present;
`check_docs --strict`: 223 docs, all reachable) — the #763 regex root-fix is holding, and
the #780 interim pass had already reconciled the #778 ledger gap. I re-ran both and
eyeballed `git log` against the ledger per the #763 lesson; no drift found.

The band's spine was the **safety/community lane + the hardening P0-3 foundation**, exactly
as the #763 night pass queued it — a rare band that ran almost entirely to plan:

- **Safety/community band slots 4–6 COMPLETE** — automod v1 (#772, Q-0108, the family
  plan's entry doc) → server event logging v1 (#774, Q-0109, extending the existing
  `server_logging` seam) → welcome v1 + counters (#775, Q-0110, two hub-less subsystems).
  The first safety band shipped end-to-end.
- **Hardening P0-3 foundation shipped (#777)** — `scripts/settings_lane_matrix.py`, the
  `governance.trusted_role` backfill reframe (Required #2 fixed), two parity invariants
  (the `test_pointer_lane_ledger` ratchet caught the #775 welcome/counters orphan pattern),
  and the [convergence plan](settings-pointer-lane-convergence-plan-2026-06-13.md) with
  arc PRs 2–3 designed. Opened **Q-0119** (governance role-pointer home, OPEN).
- **Backup posture shipped (#769)** + autonomous-loop follow-ups (#765/#767/#770).
- **Two unplanned high-value items consumed the buffer slot:** **#778** root-caused why
  the autonomous loop had **never self-fired** (cron/cadence trigger issues were
  bot-authored → don't start a routine; now author with `ROUTINE_PAT`, inert until the
  owner adds the secret) — and the **#780 interim workflow-hardening pass** (by-judgment,
  owner-requested: re-badged stale docs, added the control-plane state ledger, routed loose
  ideas, proposed Q-0120/Q-0121). *This very pass — fired by issue #781 — is the proof
  #778's fix works: the trigger issue was authored such that the routine started.*

**Open PRs (left untouched — other lanes / owner's):** **#779** (native auto-merge enabler
— owner's, workflow-runtime, inert until the owner does the three setup items in its body) ·
**#771** (a ledger PR for #765/#767/#769 — **now redundant**, #777's close already recorded
them; recommend close) · **#766** (3 orientation ideas — another session's docs PR) ·
**#704** (owner's screenshot test).

## 2. Band scorecard (the #763 night-pass queue, band #761–#780 → reality)

| Slot (from the #763 pass §4) | Outcome |
|---|---|
| 1 · the pass itself | ✅ #763 |
| 2 · P2 doc-drift sweep | ✅ #764 |
| 3 · Postgres backup posture | ✅ #769 |
| 4 · safety family plan + automod v1 | ✅ #772 |
| 5 · server event logging v1 | ✅ #774 |
| 6 · welcome v1 + counters | ✅ #775 |
| 7 · P0-3 settings pointer-lane convergence | 🟡 **foundation #777** (arc PRs 2–3 carry) |
| 8 · P0-4 server-mgmt channel ownership | ❌ → **carried (slot 5 below)** |
| 9 · P0-2 media retention | ❌ → **carried (slot 6 below)** |
| 10 · buffer / steered | consumed by **#778** (loop self-fire root-fix) + **#780** (interim workflow pass) |

**7 of 10 slots executed to plan** — the strongest plan-fidelity band yet (contrast the
#763 band, where two owner-steered arcs displaced the whole queue). The three misses are
the *harder* P0 tracks (P0-4/P0-2) plus the P0-3 arc tail — and P0-3 got its de-risking
foundation, so the remaining arc PRs are now turn-key against a pinned plan. The two
unplanned items were both high-value (the loop finally self-fires; the docs drift swept).

## 3. Priorities restated (what the next band is for)

The product lanes are healthy and owner-steered on demand; the **standing priority is the
production-hardening P0 spine** — it is the only thing between the current Partial ratings
and a public posture, and **every gating decision is answered** (Q-0098/0099/0100 + Q-0097).
Ordered highest-value-first, that means *integrity before correctness before the safety
remainder*:

1. **Finish the P0 integrity spine** — P0-3 arc PRs 2–3 (designed, turn-key), then P0-4
   (channel-ownership, Q-0100), then P0-2 (media retention/privacy, Q-0099). These close
   real harm classes: silent authority divergence, audit-trail gaps, indefinite raw-payload
   retention. No owner gate remains on any of them.
2. **P1 correctness** — the versioned AI/BTD6 eval-smoke matrix (P1-1) + the BTD6
   absence-claim guard; this is the durable net under the live-eval defect rate that PRs
   #703/#706/#707/#709 each patched reactively, and it is adjacent to **BUG-0009** (the
   claim-assembly class). Then P1-2 health findings lifecycle (Q-0097 answered).
3. **The safety/community remainder** (plan-first) — security service tiers 1+2 (Q-0111),
   image moderation (Q-0108), welcome phase 2 PIL cards (small, prototype exists), the NL
   event scheduler (Q-0112, own AI-cost design under the €30/mo ceiling).
4. **The autonomous loop runs in parallel, calibrating** — now that #778 fixed the
   self-fire blocker, the loop is *one maintainer secret* (`ROUTINE_PAT`) from live; the
   first real cadence fire is **this pass**. Routines that skip session-enders are expected;
   the (now-working) ledger checker is the net.
5. **Owner-led in parallel:** add `ROUTINE_PAT` (unblocks the loop) · the P1-4 live walks
   (the smoke checklists each map flagged) · `!uxlab` walk · #704/#771/#779 disposition.

## 4. The next ~9 PRs (band #781–#800)

> Modular but not over-segmented (Q-0107): each slot is a real slice. Numbers are
> **sequence, not reserved PR numbers**. Owner steers override freely; note swaps here.
> Ordered so the highest-value (P0 integrity) comes first.

| # | PR (one session each) | Scope anchor | Gate |
|---|---|---|---|
| 1 | **This pass** — reconcile + plan + tighten current-state ▶ Next action | Q-0107 (issue #781) | — |
| 2 | **P0-3 arc PR 2 — retire XP-announce + economy-log scalars** | [convergence plan §3](settings-pointer-lane-convergence-plan-2026-06-13.md) (families 1+2 *ready*) + `test_no_dual_declared_pointer` invariant + real-Postgres binding-first proof | unblocked |
| 3 | **P0-3 arc PR 3 — delegated-apply authority contract** | [convergence plan §4](settings-pointer-lane-convergence-plan-2026-06-13.md) — the fenced `setup_delegate` actor_type + AST fence + audit | Q-0098 (answered); design pinned |
| 4 | **P0-4 — server-mgmt channel-ownership convergence** | [hardening §P0-4](production-readiness/hardening-roadmap-2026-06-12.md); converge create/clone/overwrite/category under the audited seam + extend the channel invariant | Q-0100 (answered) |
| 5 | **P0-2 — media/YouTube retention + data-minimization** | [hardening §P0-2](production-readiness/hardening-roadmap-2026-06-12.md); bounded projection, wire `purge_expired_video_cache` through the managed-task owner, fix `YOUTUBE_CONTEXT_ENABLED` ownership | Q-0099 (answered) |
| 6 | **P1-1 — versioned AI/BTD6 eval-smoke matrix + BTD6 absence-claim guard** | [hardening §P1-1](production-readiness/hardening-roadmap-2026-06-12.md); gates/fallback/tool-use/grounding-refusal/audit, run with prod-like creds; implements the absence-claim guard (relates to **BUG-0009**) | needs prod-like creds for the live half |
| 7 | **Safety lane — security service tiers 1+2** (plan-first) | Q-0111 — raid detection + account-age filter (tiers 3+4 declined); cite `ux/pattern-library.md` `mock_security_*` pattern_ids | family plan; plan-first |
| 8 | **Safety lane — welcome phase 2 (PIL cards)** | Q-0110 — the `render_welcome_card` prototype exists; small follow-up on the stable embed-first v1 | quick-win |
| 9 | **P1-2 — health findings lifecycle + retention** | [hardening §P1-2](production-readiness/hardening-roadmap-2026-06-12.md); transition findings through the sole `health_findings_service` writer + scheduled retention | Q-0097 (answered) |
| 10 | **Buffer / steered slot** — likely: land **#757** (HermesCog, its lane) · or **image moderation** plan (Q-0108) · or the **#779 auto-merge envelope-strip PR 2** once the owner does the setup | in-flight / owner-led | — |

**Deliberately *not* in this band** (unchanged unless the owner steers): the NL event
scheduler build (Q-0112 — own AI-cost design first) · P1-3 as a mega-session (it lands one
invariant *per track* as each P0 ships) · P1-4 owner live-walks (owner-led) · myprofile
PR A · mining V-16 phase 2 (owner PNG pack) · the §7.5 structures / §7.4 skill tree ·
CV2-adoption ADR (wants the owner's `!uxlab` walk) · the Hermes bug-triage build
(gated Q-0121) · the candidate-rule promotion (gated Q-0120).

## 5. Pruned / fixed by this pass

- **[reconciliation-pass-2026-06-12-night.md](reconciliation-pass-2026-06-12-night.md)
  re-badged `historical`** — its band (#761–#780) is fully scored in §2 above; this record
  supersedes it as the live decade queue.
- **`docs/current-state.md` ▶ Next action rewritten** (the system improvement, §6): the
  one-live-queue pointer now points at *this* doc, and the bullet was collapsed from a
  ~15-line struck-through history wall to a clean current-priority line. The struck-through
  band-slot history moved into §2 here (its durable home).
- **`docs/roadmap.md`** — the "live decade queue" pointer (top) and the **Now** horizon
  re-pointed from the #763 night pass to this pass; the safety-band slots 4–6 marked ✅.
- **Marker reset** — `Last reconciliation pass` → **#780**; `check_reconciliation_due.py`
  next fires at #800 (auto-opened `reconcile` issue, the mechanism this pass proved live).
- **No runtime bugs noticed** (docs-only pass) → nothing appended to the bug book; BUG-0009
  / BUG-0011 stay OPEN for the caretaker/AI lanes.

## 6. The system improvement this pass made (the point of the loop)

**The `▶ Next action` line in `current-state.md` had become the exact run-on anti-pattern
the file warns against.** It had grown to ~15 dense lines of `~~struck-through~~` band
history with the actual *next action* buried at the very end — a new session (or routine)
had to parse a wall to learn "what do I do now." That is orientation drift: the highest-read
line in the highest-read doc was the least scannable.

**Fix:** the band history is *record*, and its home is a reconciliation-pass doc (§2 here),
not the live ledger's lead line. I collapsed `▶ Next action` to a single scannable
current-priority sentence pointing at this decade queue, and left the history to §2. This
is the same "one-fact-one-home; the live ledger links, it doesn't restate" discipline the
doc itself preaches at the bottom — applied to its own top. The next reader gets the
priority in one line; the curious reader follows the link to the full scorecard.

**Why this is the loop working, not make-work:** a routine fired by issue #781 read its own
orientation file and found the orientation file's most important line unreadable — so it
fixed it. Each pass should leave the next better-equipped; a tighter `▶ Next action` is the
most-leveraged single edit available, because every future session reads it first.
