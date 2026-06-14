# Reconciliation pass — 2026-06-13 · the band-#800 Q-0107 cadence pass

> **Status:** `historical` — superseded by the [band-#820 pass](reconciliation-pass-2026-06-14-band820.md)
> (its #801–#820 queue is fully scored there §2). The docs-only review + planning pass for the band that crossed
> **#800** (cadence = every 20th merged PR; previous cadence pass
> [#781, band #761–#780](reconciliation-pass-2026-06-13-q0107.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#801**
> (`.github/workflows/reconciliation-trigger.yml`) — the **second** real cadence fire of
> the autonomous issue-trigger, confirming #778's self-fire fix holds across boundaries.
> Sections: §1 verified state · §2 band scorecard · §3 priorities restated · §4 the next
> ~9 PRs · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#800** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the #781 pass:** #782, #783, #784, #785 (session-close housekeeping), #786,
#787 (native auto-merge migration, Q-0123), #788, #789, #790, #791, #792, #793 (the
substrate-kit extraction arc, PR 1a + 1b), #794 (hardening P0-3 arc PR 2), #795, #796
(substrate-kit docs/resume recipe), #797 (P0-3 session log), #798 (settings allowlist),
#799 (Q-0119 record), #800 (journal calibration rules). **Open PRs left untouched** (other
lanes / owner's): **#771** (a redundant ledger PR for #765/#767/#769 — #777's close already
recorded them; **recommend close**, flagged here for the third pass running), **#766** (3
orientation ideas — another session's docs PR), **#704** (owner's screenshot test).

**Ledger drift found and fixed (the headline of this pass).** Both audit checkers reported
**green** at pass start — but the green was *false*. `check_current_state_ledger --strict`
passed only because the `▶ Next action` line literally contained the planning range
`(band #781–#800)`, and the checker expands every `#AAA–#BBB` range it finds anywhere in
`current-state.md` into "present" coverage. So the **entire substrate-kit arc and the
auto-merge migration — ~14 merged PRs — were masked from the ledger and never individually
recorded.** This is the same drift class the #763 pass thought it had closed (the
"Merge PR #N:" regex blindness); this is a *different* leak in the same guard. §5 lists the
real entries this pass added; §6 is the durable fix so it can't recur.

The band's spine was **not** the planned production-hardening P0 queue — it was the owner's
strategic refocus onto the **portable substrate-kit** (the OSS agent-memory/workflow package),
plus the auto-merge migration. The P0 spine carried forward almost intact (only arc PR 2
landed), exactly as the #763 band did when two owner-steered arcs displaced the queue.

- **Portable substrate-kit — PR 1a + 1b DONE (#788–#796, #798).** The repo's *real artifact*
  (cross-session memory + self-improving workflow) extracted into a self-contained,
  stdlib-only `substrate-kit/` tree that **never mutates superbot's live `.claude/`/`docs/`**
  ([extraction plan](portable-substrate-kit-extraction-2026-06-13.md), owner-approved after
  10 external-review rounds; [revision report](portable-agent-substrate-revision-2026-06-13.md)).
  PR 1a (#789) = locked-contract skeleton + state-backend interface; PR 1b (#791→#792→#793)
  = the staged-learning loop (interview engine, template render + core orientation docs, the
  6-doc orientation template set). **Resume point: the 1b tail (two stdlib checker ports) →
  PR 2 (the capability/modes layer).**
- **Native auto-merge migration shipped (#786 + #787, Q-0123).** Merge mechanics moved off
  the Claude session: `auto-merge-enabler.yml` arms GitHub-native auto-merge on every
  non-draft `claude/*` PR; the Q-0084 manual self-merge envelope was struck from CLAUDE.md.
  Removes the #778 "forgotten deferred merge" failure class server-side.
- **Hardening P0-3 arc PR 2 shipped (#794)** — retired the XP-announce + economy-log scalar
  pointers so each Discord-resource pointer has one canonical binding owner; a *retired*
  pointer reads binding-first regardless of the OFF-by-default `bindings.primary` flag (new
  `config_arbitration` `pointer_retired=True`), deploying with no coordinated flag flip.
  Emptied `CONVERGEABLE_POINTERS`; added `test_no_dual_declared_pointer`. **The only P0-spine
  slot of the planned 3–9 that executed.**
- **Q-0119 answered (#799)** — governance role pointers get their own reserved-namespace
  `governance` schema home (option a); P0-3 family 3 is unblocked for a future arc PR.

## 2. Band scorecard (the #781 pass §4 queue, band #781–#800 → reality)

| Slot (from the #781 pass §4) | Outcome |
|---|---|
| 1 · the pass itself | ✅ #781 |
| 2 · P0-3 arc PR 2 (retire scalars) | ✅ #794 |
| 3 · P0-3 arc PR 3 (delegated-apply) | ❌ → **carried (slot 2 below)** |
| 4 · P0-4 channel ownership | ❌ → **carried (slot 3 below)** |
| 5 · P0-2 media retention | ❌ → **carried (slot 4 below)** |
| 6 · P1-1 eval-smoke matrix | ❌ → **carried (slot 5 below)** |
| 7 · security tiers 1+2 | ❌ → **carried (slot 7 below)** |
| 8 · welcome phase 2 (PIL cards) | ❌ → **carried (slot 8 below)** |
| 9 · P1-2 health findings | ❌ → **carried (slot 9 below)** |
| 10 · buffer / steered | consumed by the **substrate-kit arc** (#788–#796, #798) + the **auto-merge migration** (#786/#787) |

**2 of 10 slots executed to plan** — the *weakest* plan-fidelity band since #763, but for a
good reason: capacity went to the owner's explicit strategic refocus (the substrate-kit OSS
package — the 2026-06-12 "the real artifact is the workflow" direction made concrete) and to
the auto-merge migration that removes a real failure class. Both are high-value and
owner-aligned; neither was make-work. The lesson is the **recurring pattern**: when the owner
has an active strategic thread, it consumes the band and the standing P0 hardening spine
carries forward intact (as in #763). The plan is a default, not a contract.

## 3. Priorities restated (what the next band is for)

Unchanged from the #781 pass — the substrate arc displaced the queue, it did not re-order it.
The **standing priority is the production-hardening P0 spine, integrity-first** — every
gating decision is answered (Q-0098/0099/0100 + Q-0097), so nothing waits on the owner:

1. **Finish the P0 integrity spine** — P0-3 arc PR 3 (delegated-apply, Q-0098 — designed,
   turn-key against the [convergence plan §4](settings-pointer-lane-convergence-plan-2026-06-13.md)),
   then P0-4 (channel-ownership, Q-0100), then P0-2 (media retention/privacy, Q-0099). These
   close real harm classes: silent authority divergence, audit-trail gaps, indefinite
   raw-payload retention.
2. **P1 correctness** — the versioned AI/BTD6 eval-smoke matrix (P1-1, relates **BUG-0009**)
   + the BTD6 absence-claim guard, then P1-2 health findings lifecycle (Q-0097 answered).
3. **The substrate-kit continues in parallel as the active owner thread** — resume at the 1b
   tail (two stdlib checker ports) → PR 2 (capability/modes layer). Owner-steered; it has
   consumed two recent bands' worth of buffer and will keep doing so while it is the focus.
4. **The safety/community remainder** (plan-first) — security service tiers 1+2 (Q-0111),
   image moderation (Q-0108), welcome phase 2 PIL cards (small, prototype exists), the NL
   event scheduler (Q-0112, own AI-cost design under the €30/mo ceiling).
5. **The autonomous loop runs in parallel, calibrating** — this pass is its second clean
   cadence fire (after #781). Still **one maintainer secret (`ROUTINE_PAT`) from live** for
   the bot-authored trigger path; the (now-working) ledger checker is the net.
6. **Owner-led in parallel:** add `ROUTINE_PAT` · the P1-4 live walks · `!uxlab` walk ·
   #771/#766/#704 disposition.

## 4. The next ~9 PRs (band #801–#820)

> Modular but not over-segmented (Q-0107): each slot is a real slice. Numbers are
> **sequence, not reserved PR numbers**. Owner steers override freely; note swaps here.
> Ordered so the highest-value (P0 integrity) comes first, with the active substrate thread
> interleaved where it is the owner's focus.

| # | PR (one session each) | Scope anchor | Gate |
|---|---|---|---|
| 1 | **This pass** — reconcile (the masking-range drift) + plan + drop the live-pointer PR range | Q-0107 (issue #801) | — |
| 2 | **P0-3 arc PR 3 — delegated-apply authority contract** | [convergence plan §4](settings-pointer-lane-convergence-plan-2026-06-13.md) — the fenced `setup_delegate` actor_type + AST fence + audit | Q-0098 (answered); design pinned |
| 3 | **P0-4 — server-mgmt channel-ownership convergence** | [hardening §P0-4](production-readiness/hardening-roadmap-2026-06-12.md); converge create/clone/overwrite/category under the audited seam + extend the channel invariant | Q-0100 (answered) |
| 4 | **P0-2 — media/YouTube retention + data-minimization** | [hardening §P0-2](production-readiness/hardening-roadmap-2026-06-12.md); bounded projection, wire `purge_expired_video_cache` through the managed-task owner, fix `YOUTUBE_CONTEXT_ENABLED` ownership | Q-0099 (answered) |
| 5 | **P1-1 — versioned AI/BTD6 eval-smoke matrix + BTD6 absence-claim guard** | [hardening §P1-1](production-readiness/hardening-roadmap-2026-06-12.md); gates/fallback/tool-use/grounding-refusal/audit; implements the absence-claim guard (relates **BUG-0009**) | needs prod-like creds for the live half |
| 6 | **Substrate-kit PR 1b tail + PR 2** (owner-steered, active thread) | [extraction plan §Execution log](portable-substrate-kit-extraction-2026-06-13.md) — the two stdlib checker ports, then the capability/modes/triggers layer | owner-approved; resume recipe pinned |
| 7 | **Safety lane — security service tiers 1+2** (plan-first) | Q-0111 — raid detection + account-age filter (tiers 3+4 declined); cite `ux/pattern-library.md` `mock_security_*` pattern_ids | family plan; plan-first |
| 8 | **Safety lane — welcome phase 2 (PIL cards)** | Q-0110 — the `render_welcome_card` prototype exists; small follow-up on the stable embed-first v1 | quick-win |
| 9 | **P1-2 — health findings lifecycle + retention** | [hardening §P1-2](production-readiness/hardening-roadmap-2026-06-12.md); transition findings through the sole `health_findings_service` writer + scheduled retention | Q-0097 (answered) |
| 10 | **Buffer / steered slot** — likely more substrate-kit (PR 3), or owner-steered product work (mining V-16 phase 2 / BTD6 decode), or the #771/#766 dispositions | in-flight / owner-led | — |

**Deliberately *not* in this band** (unchanged unless the owner steers): the NL event
scheduler build (Q-0112 — own AI-cost design first) · P1-3 as a mega-session (lands one
invariant *per track* as each P0 ships) · P1-4 owner live-walks (owner-led) · myprofile PR A ·
mining V-16 phase 2 (owner PNG pack) · the §7.5 structures / §7.4 skill tree · the
CV2-adoption ADR (wants the owner's `!uxlab` walk) · the substrate-kit public-OSS
productization phase (separate, later, ~160–276 h) · the Hermes bug-triage build (gated
Q-0121) · candidate-rule promotion (gated Q-0120).

## 5. Pruned / fixed by this pass

- **The masking ledger drift fixed (the headline).** Added real `Recently shipped` entries
  for the three band arcs the `#781–#800` range had masked: the **substrate-kit extraction**
  (#788–#796 + #798), the **native auto-merge migration** (#786 + #787), and **P0-3 arc PR 2**
  (#794) — plus a housekeeping line for the reconciliation/session-close/Q-0119 PRs (#781–#785,
  #797, #799, #800). Trimmed the three oldest live entries (#732/#736/#737) into
  [`current-state-archive.md`](../current-state-archive.md) to hold the ratchet at 20.
- **[reconciliation-pass-2026-06-13-q0107.md](reconciliation-pass-2026-06-13-q0107.md)
  re-badged `historical`** — its band (#781–#800) is fully scored in §2 above; this record
  supersedes it as the live decade queue.
- **`docs/current-state.md` ▶ Next action re-pointed** at *this* doc and the **PR-number
  range dropped from the live pointer** (the system improvement, §6) — it now references the
  pass by name, so a planning range can never again mask the band it plans.
- **`docs/roadmap.md`** — the live-decade-queue pointer and the **Now** horizon re-pointed
  from the #781 pass to this pass; the range dropped from the pointer for the same reason.
- **Marker reset** — `Last reconciliation pass` → **#800**; `check_reconciliation_due.py`
  next fires at #820 (auto-opened `reconcile` issue).
- **No runtime bugs noticed** (docs-only pass) → nothing appended to the bug book; BUG-0009 /
  BUG-0011 stay OPEN for the caretaker/AI lanes.

## 6. The system improvement this pass made (the point of the loop)

**A forward-looking PR-number range in the `▶ Next action` pointer silently disabled the
ledger drift guard for the whole band it named.** The #781 pass wrote `(band #781–#800)` into
the live-queue pointer; `check_current_state_ledger` expands every `#AAA–#BBB` range it finds
*anywhere* in `current-state.md` into "present" coverage, so the moment those 20 PRs merged,
all of them — the entire substrate-kit arc and the auto-merge migration — were marked
"recorded" while in fact they were never individually written into the ledger. The guard
reported green; the ledger was 14 entries short. This is **not** the #763 "Merge PR #N:"
regex leak — it is a *second, independent* false-green in the same guard, and worse, it
**recurs at every boundary** as long as the live pointer names a band by its PR-number range.

**Fix (durable, zero code risk): the live-queue pointer references the pass *by name/date*,
never by an inline PR-number range.** The band range belongs in the pass doc (which lives in
`docs/planning/` and is *not* scanned by the checker), not restated in `current-state.md`'s
top pointer — the same "one-fact-one-home; link, don't restate" discipline the file preaches
at the bottom, applied to its own top. With the range gone from the pointer, the checker
correctly forces a real `Recently shipped` entry for every merged band PR *between* passes,
which is exactly its job. A docstring caveat was added to the checker so a future agent
understands the trap. (The deeper structural fix — scope range-expansion to the
`## Recently shipped` section only — needs a checker-logic + test change and is therefore
out of scope for a docs-only self-merge pass; it is **captured as an idea** for a runtime-lane
session: [`../ideas/ledger-checker-range-scope-2026-06-13.md`](../ideas/ledger-checker-range-scope-2026-06-13.md).)

**Why this is the loop working, not make-work:** a routine fired by issue #801 ran its own
orientation checkers, saw them report green, distrusted the green (the #763 lesson:
"eyeball `git log` against the ledger"), and found the guard had been quietly lying for an
entire band. It fixed the data, fixed the convention that caused it, and left the next pass a
guard that can't tell the same lie. Each pass leaves the next better-equipped.
