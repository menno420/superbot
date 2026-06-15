# Reconciliation pass — 2026-06-14 · the band-#870 Q-0107 cadence pass

> **Status:** `historical` — superseded by [the band-#900 pass](reconciliation-pass-2026-06-15-band900.md)
> (its band #871–#900 is scored in that pass §2). The docs-only review + planning pass for the band
> that crossed
> **#870** (cadence = every **30th** merged PR per Q-0134; previous cadence pass
> [the band-#840 pass](reconciliation-pass-2026-06-14-band840.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#871**
> (`.github/workflows/reconciliation-trigger.yml`) — the **fifth** consecutive real cadence
> fire of the autonomous issue-trigger (after #781, #801/#822, #841), so the self-fire path is
> routine.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 priorities
> restated · §4 the next ~9 PRs · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#870** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the band-#840 pass (band #841–#870):** most entries were already in the ledger
from their own sessions (the born-red Q-0133 gate is holding — sessions add their own cards) or
from the ad-hoc band #841–#860 window catch-up (**#867**). The genuinely-new, not-yet-entered
PRs at pass start (per `check_current_state_ledger --strict`): **#867, #868, #869, #870** — all
docs-only:

- **#867** — `docs(ledger): reconcile band #841–#860 + window catch-up`. An *ad-hoc* ledger-hygiene
  reconcile (between cadence passes) that added eight live entries (#866/#865/#864/#863/#862/#859,
  the #856+#853 group, the #851/#850/#848/#852 group) and archived eight old ones. It did **not**
  reset the cadence marker or write a planning doc — correctly, it was ledger hygiene, not a Q-0107
  pass. → ledger entry added §5.
- **#868** — `docs(hermes): pick next slice from live state, not plan PR-numbers (Q-0142)`. The
  workflow rule that fixed a real misread: a stale reconciliation dispatch fired because a slot in
  the decade queue was read as a reserved PR number. Hermes' dispatch skill + operating prompt now
  pick the next slice by **description verified against the live ledger**, never a predicted #. → §5.
- **#869** — `fix(hermes): run stdlib tooling under python3, not python3.10`. Hermes' VPS skills
  (dispatch/log-triage/repo-health/skill-author + `build_skills.py`) run stdlib-only tooling under
  the VPS's `python3`, not the repo's CI-pinned `python3.10`. → §5.
- **#870** — `docs(hermes): record Python 3.10 VPS prerequisite (deadsnakes, verified)`. Records the
  verified deadsnakes Python 3.10 prerequisite in the Hermes control-plane doc. → §5.

`#867`–`#870` form a coherent tail: one ad-hoc ledger catch-up + a three-PR **Hermes
operating-layer hardening arc** (next-slice rule · tooling interpreter fix · VPS prereq). They are
grouped into two `Recently shipped` entries (§5).

**Open PRs at pass time (disposition — Q-0125), the standing recorded snapshot:**

| PR | What | Disposition |
|---|---|---|
| *(none)* | `list_pull_requests state=open` returned **zero** open PRs at pass start | **clean** — #704 (owner live-test screenshots) was triaged + **closed** in #866; #834 (owner permissions-review capture) has since closed. No `claude/*` PR is open; the #766/#771 rot class stays clear across the whole #841–#870 band. |

This is the **first band in the recorded-snapshot's history with zero open PRs** — the cleanest
disposition outcome the Q-0125 section has logged.

## 2. Band scorecard (the band-#840 pass §4 queue, band #841–#870 → reality)

| Slot (from the band-#840 pass §4) | Outcome |
|---|---|
| 1 · the band-#840 pass itself | ✅ (the pass that wrote that queue) |
| 2 · P1-1 eval-smoke matrix + absence-claim guard | 🟡 **partial — #855** shipped the absence-guard **Layer A** (path/line grounding); the versioned eval-matrix + Layer B carried (needs prod-like creds) |
| 3 · P1-2 health findings lifecycle + retention | ✅ **#843** (Q-0097 — operator transition path + daily `HealthMaintenanceCog` retention) |
| 4 · substrate-kit PR 2 remainder + PR 3 | ❌ → carried (slot 4 below) — no substrate work this band (third consecutive carry; **see §6**) |
| 5 · security service tiers 1+2 | ❌ → carried (slot 5 below) |
| 6 · welcome phase 2 (PIL cards) | ❌ → carried (slot 6 below) |
| 7 · Railway log-triage skill | 🟡 **infrastructure landed, skill not built** — #862 fixed the prod backup pipeline live, #865 hardened the dispatch helper; the read-only log-triage skill itself carried (slot 7 below) |
| 8 · P1-3 invariants per shipped P0 | 🟡 partial — each shipped P0 landed its own parity invariant inline; no dedicated slice |
| 9 · `check_current_state_ledger` prints missing-PR subjects | ✅ **#864** (shipped **both** the band-#840 Q-0089 idea *and* the range-scope idea — the merge-subjects printed in *this* pass's checker run, closing the loop) |
| 10 · buffer / steered | consumed by the **Hermes control-plane / autonomous-loop operationalization arc** (#863 skill-author meta-skill + Q-0140 docs-PR write scope · #865 `routine_fire.py` + Q-0141 · #868 next-slice rule Q-0142 · #869/#870 tooling/prereq) + the **#704 live-test triage/close** (#866) + the prod **backup-pipeline fix** (#862) + the #839 chat-export follow-ups |

**~3 of 10 planned slots executed (P1-2 #843 ✅, ledger-checker #864 ✅, P1-1 Layer A 🟡 #855); the
band's headline is the unplanned-but-high-value Hermes / autonomous-loop operationalization arc.**
The buffer (slot 10) again carried the band — this time the **Hermes control-plane maturing into a
working dispatch loop** (a meta-skill that lets Hermes author its own skills as docs-only PRs, a
robust stdlib dispatch helper, the next-slice-from-live-state rule, and a live-fixed production
backup). That is the autonomous loop the whole system exists to build — not plan drift. But it is
now the **third** band running (#820→#840→#870) where the active autonomous-loop thread filled the
buffer while two planned slots (P1-1 full matrix, substrate-kit remainder) carried untouched — the
planning lesson §6 acts on.

## 3. Priorities restated (what the next band is for)

**The P0 integrity spine is finished and P1-2 is done**, so the standing priority is **P1
correctness + the active autonomous-loop / owner threads**:

1. **P1 correctness — finish the P1 tier.** The versioned AI/BTD6 **eval-smoke matrix** (P1-1,
   relates **BUG-0009**) + the absence-claim guard **Layer B** (Layer A shipped #855), then
   **P1-3 invariants** (one parity/fence invariant per shipped P0 track that lacks one). The
   live half of P1-1 still needs prod-like creds — but the **deterministic / offline half is
   buildable now** and should ship rather than carry whole.
2. **The autonomous-loop / Hermes thread is now the dominant active thread** — it consumed the
   buffer two bands running. The next high-leverage slice is the **read-only Railway log-triage
   skill** (Railway access verified live #840; the dispatch loop is now operational after #865/#868)
   — content-free surfacing of prod log signal for the caretaker routine. Reserve it an **explicit
   slot**, not buffer (§6).
3. **The substrate-kit is the owner's owed thread** — resume at the PR-2 remainder (modes +
   contract templates + triggers) → PR 3. Third consecutive carry; genuinely owed, but **owner-
   steered** — if it carries a fourth band, escalate to the owner-action list (§6).
4. **The safety/community remainder** (plan-first) — security service tiers 1+2 (Q-0111), welcome
   phase 2 PIL cards (small; prototype exists), image moderation (Q-0108), NL event scheduler
   (Q-0112, own AI-cost design first).
5. **The autonomous loop runs in parallel, calibrating** — this is its **fifth** clean cadence
   fire. The bot-authored-trigger path still needs the **`ROUTINE_PAT`** secret to be fully live;
   the (working) ledger checker remains the net.
6. **Owner-led in parallel:** add `ROUTINE_PAT` · the P1-4 live walks · `!uxlab` walk · mining
   V-16 phase 2 PNG pack · BTD6 owner spot-check.

## 4. The next ~9 slices (planned after #870)

> Modular but not over-segmented (Q-0107): each slot is a real slice. The `#` column is
> **slot sequence, NOT reserved PR numbers** — GitHub assigns PR numbers globally across all
> parallel + housekeeping work, so do NOT map a slot to a predicted PR number or read this as a
> "#871–#900" schedule (Q-0142 — that misread fired a stale reconciliation dispatch). Pick the
> next slice by its **description**, verified against the live ledger. Each slot carries a
> **gate-state** tag (per §6): `ready` (buildable now) · `creds` (needs prod-like creds for part)
> · `owner` (owner-steered) · `plan-first`. Owner steers override freely; note swaps here.

| # | PR (one session each) | Gate-state | Scope anchor |
|---|---|---|---|
| 1 | **This pass** — reconcile (#867/#868/#869/#870) + plan + disposition | — | Q-0107 (issue #871) |
| 2 | **P1-1 — versioned AI/BTD6 eval-smoke matrix (offline half) + absence-guard Layer B** | `creds` (live half) / `ready` (offline half) | [hardening §P1-1](production-readiness/hardening-roadmap-2026-06-12.md); gates/fallback/tool-use/grounding-refusal/audit; ship the deterministic matrix + Layer B now, defer only the creds-gated live battery (relates **BUG-0009**) |
| 3 | **Railway log-triage skill** (autonomous-loop thread) | `ready` | the read-only log-triage skill (Railway logs verified live #840; dispatch loop operational #865/#868); content-free surfacing of prod log signal for the caretaker routine — Q-0130 |
| 4 | **Substrate-kit PR 2 remainder + PR 3** (owner-steered, owed) | `owner` | [extraction plan §Execution log](portable-substrate-kit-extraction-2026-06-13.md) — modes + contract templates + triggers, then the next layer. **Third carry — escalate to owner-action if it carries a fourth band.** |
| 5 | **P1-3 invariants — one per shipped P0 track that lacks one** | `ready` | [hardening §P1-3](production-readiness/hardening-roadmap-2026-06-12.md); land the parity/fence invariant for each P0 as a focused slice |
| 6 | **Safety lane — welcome phase 2 (PIL cards)** | `ready` (quick-win) | Q-0110 — the `render_welcome_card` prototype exists; small follow-up on the stable embed-first v1 |
| 7 | **Safety lane — security service tiers 1+2** | `plan-first` | Q-0111 — raid detection + account-age filter (tiers 3+4 declined); cite `ux/pattern-library.md` `mock_security_*` pattern_ids |
| 8 | **Hermes bug-triage build** (autonomous-loop thread) | `plan-first` | Q-0121 (gated) — now more tractable: Hermes can author docs-only PRs (Q-0140) and the dispatch loop is operational; design the `gh issue create` write path |
| 9 | **AI §7 deterministic list-builders** (BUG-0009) | `plan-first` | the AI orchestration §7 list-answer builders that BUG-0009 needs — plan-level; clears an OPEN bug |
| 10 | **Buffer / steered slot** — owner-steered product (mining V-16 phase 2 PNG pack / BTD6 decode ⭐ item 3) or autonomous-loop maturation | `owner` | in-flight / owner-led |

**Deliberately *not* in this band** (unchanged unless the owner steers): the NL event scheduler
build (Q-0112 — own AI-cost design first) · P1-4 owner live-walks (owner-led) · myprofile PR A ·
the §7.5 structures / §7.4 skill tree · the CV2-adoption ADR (wants the owner's `!uxlab` walk) ·
the substrate-kit public-OSS productization phase · candidate-rule promotion (gated Q-0120).

## 5. Pruned / fixed by this pass

- **Ledger reconciled.** Added two `Recently shipped` entries covering the band's genuinely-new
  PRs: **#870 + #869 + #868** (the Hermes operating-layer hardening arc — Q-0142 next-slice rule,
  the python3 tooling-interpreter fix, the VPS python3.10 prereq) and **#867** (the ad-hoc band
  #841–#860 ledger window catch-up). Trimmed the two oldest live entries (the #803… reconciliation +
  workflow-rules group · the #827… Railway agent-access session group) into
  [`current-state-archive.md`](../current-state-archive.md) to hold the ratchet at 20.
- **[reconciliation-pass-2026-06-14-band840.md](reconciliation-pass-2026-06-14-band840.md)
  re-badged `historical`** — its band (#841–#870) is fully scored in §2 above.
- **`docs/current-state.md` ▶ Next action re-pointed** at *this* doc (by name/date, no PR-number
  range — the band-#800 §6 discipline), and the **P0 spine + P1-2 complete / next = finish P1 +
  autonomous-loop thread** state restated.
- **`docs/roadmap.md`** — the live-decade-queue pointer and the **Now** horizon re-pointed from
  the band-#840 pass to this pass.
- **Open-PR disposition (Q-0125):** recorded the **zero-open-PRs** state in §1 (the cleanest
  outcome the snapshot has logged).
- **Marker reset** — `Last reconciliation pass` → **#870**; `check_reconciliation_due.py` next
  fires at #900.
- **No runtime bugs noticed** (docs-only pass) → nothing appended to the bug book; **BUG-0009 /
  BUG-0011** stay OPEN for the AI / caretaker lanes.

## 6. The system improvement this pass made (the point of the loop)

**The observation.** Three consecutive bands (#820 → #840 → #870) have now ended the same way:
two planned slots — **P1-1's full eval-matrix** and the **substrate-kit remainder** — carry
untouched while the buffer slot absorbs a large, valuable, *unplanned* thread (Railway access,
then the Hermes control-plane operationalization). The plan keeps predicting those two slots will
execute, and they keep not executing, because both are **gated** (P1-1's live half needs prod
creds; the substrate-kit is owner-steered). A queue whose top slots never execute looks like a
plan that doesn't work, even though the system is shipping plenty.

**The improvement, applied this pass.** Two changes to the planning loop:

1. **Every slot now carries a `gate-state` tag** (`ready` / `creds` / `owner` / `plan-first`) in
   §4's table — so the plannable capacity is legible at a glance and Hermes' next-slice picker
   (Q-0142, "pick by description verified against the ledger") can prefer a `ready` slot over a
   gated one rather than stalling on the top-of-list gated slot.
2. **Gated slots that carry are split, not parked whole.** Slot 2 no longer carries P1-1 as one
   creds-blocked lump — it explicitly **ships the offline/deterministic half now** and defers only
   the live battery. And a slot that carries **N bands** gets an escalation rule: the substrate-kit
   (slot 4) is on its **third** carry and now has an explicit "**escalate to the owner-action list
   if it carries a fourth band**" trigger, so an owner-steered thread can't silently rot in the
   queue forever (the rot class the open-PR snapshot guards against, applied to *plan slots*).
3. **The active autonomous-loop thread gets its own reserved slot** (slot 3, the Railway
   log-triage skill), not buffer overflow — because for two bands running it has *been* the band,
   so planning it as buffer under-counts it every time.

This is the band-#840 §6 discipline (make a recurring reality a structured, diff-able artifact)
applied to the queue itself: the slot-carry pattern was invisible across three pass docs; it is
now a tagged, escalating, legible part of the plan.

The forward idea this pass contributes (Q-0089) is in `docs/ideas/` — a checker that surfaces the
slot-carry-count automatically, so the §6 escalation trigger fires on data instead of an agent
remembering to diff three pass docs by hand.
