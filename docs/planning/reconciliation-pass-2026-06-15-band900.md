# Reconciliation pass — 2026-06-15 · the band-#900 Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed
> **#900** (cadence = every **30th** merged PR per Q-0134; previous cadence pass
> [the band-#870 pass](reconciliation-pass-2026-06-14-band870.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#901**
> (`.github/workflows/reconciliation-trigger.yml`) — the **sixth** consecutive real cadence
> fire of the autonomous issue-trigger (after #781, #801/#822, #841, #871), so the self-fire
> path is fully routine.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 priorities
> restated · §4 the next ~9 PRs · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#900** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the band-#870 pass (band #871–#900):** the band was large and almost entirely
self-reconciled — every code session added its own `Recently shipped` entry under the born-red
Q-0133 gate. The only genuinely-not-yet-entered PR at pass start (per
`check_current_state_ledger --strict`): **#898** (docs-only). #899 and #900 were already present
(stamp-line block). #887, #890 were never merged (no merge commit — skipped/closed numbers);
#893 is **open** (see disposition below).

- **#898** — `docs(phase-gate): clarify dispatched vs. agent-self-originated features (Q-0114)`.
  Documents the owner's in-session clarification in its canonical homes (router Q-0114 +
  `check_phase_gate.py` docstring) so a literal agent doesn't re-derive it: a **dispatched** work
  order (the `/fire` endpoint, even `CLASS: feature`) is owner-directed and flows freely; the
  phase gate is **only** for features an agent invents itself. → folded into the §5 `#898 + #892 +
  #889` loop-hygiene ledger entry (same theme).

**Open PRs at pass time (disposition — Q-0125):**

| PR | What | Disposition |
|---|---|---|
| **#893** | `docs(mining): handoff PR 884/891 + continuation options for next session` — owner-authored (`menno420`), opened 2026-06-15, docs-only mining-lane handoff | **leave open / owner's** — it is the owner's own handoff PR (not a `claude/*` session PR), and the mining structures work it hands off (#884 Vault, #891 skill tree, #897 Vault v2) has since shipped. Not in this reconciler's merge authority; flagged here so it doesn't silently rot. **If it carries to the band-#930 pass, surface it to the owner to merge or close.** |

No `claude/*` session PR is open and stale — the #766/#771 rot class stays clear across the whole
#871–#900 band.

## 2. Band scorecard (the band-#870 pass §4 queue, band #871–#900 → reality)

| Slot (from the band-#870 pass §4) | Outcome |
|---|---|
| 1 · the band-#870 pass itself | ✅ (the pass that wrote that queue) |
| 2 · **P1-1 eval-smoke matrix (offline half) + absence-guard Layer B** | ✅ **offline half MASSIVELY EXECUTED** — #878 (real-gateway smoke matrix, 16 cases) + #879 (self-cleaning drift guard) + #881/#886/#895/#896 drove the AI tool-surface coverage **8 → 14 → 20 → 27 → 34/34 FULL**; `_ACK_UNCOVERED_TOOLS` empty, the drift guard now fails closed on any new tool. **Layer B + the live-quality battery carried** (design-for-review / creds-gated). |
| 3 · Railway log-triage skill | ❌ → carried (slot below) — no log-triage skill this band |
| 4 · substrate-kit PR 2 remainder + PR 3 | ❌ → **FOURTH consecutive carry** — the §6 escalation trigger from the band-#870 pass **fires this pass** (see §6). |
| 5 · P1-3 invariants | ❌ → carried — each new P0/feature still landed its own inline parity invariant (the RS02 write-boundary ratchet guarded `set_vault_level`/`update_vault_item`; the eval drift guard); no dedicated slice. |
| 6 · safety welcome phase 2 (PIL cards) | ❌ → carried |
| 7 · security service tiers 1+2 | ❌ → carried |
| 8 · Hermes bug-triage build | ❌ → carried |
| 9 · AI §7 deterministic list-builders (BUG-0009) | ❌ → carried (BUG-0009 still OPEN) |
| 10 · buffer / steered | consumed by **three** owner-steered threads (below) |

**Slot 2 over-delivered (P1-1's whole offline half is DONE — 34/34 tool coverage); the other
eight planned slots carried, and the buffer (slot 10) again became the band.** This band the
buffer split three ways:

- **Mining structures product burst** — #884 (§7.5 Vault v1), #891 (§7.4 capped skill tree, the
  marquee), #897 (Vault v2 — pack soft-cap + upgradeable vault capacity). The owner steered the
  night routine at the mining lane; the structures plan's turn-key slices are executing.
- **Routine-consolidation / sector-dispatch arc** — #877 (roadmap restructured by sector → S1–S5
  dispatch queues), #880 (dispatch contract: executor dimension + startability tags, Q-0143), #882
  (sector tooling: `check_sector_map.py` + `dispatch_menu.py`), #899 (foolproof routine-prompt
  canon + idea→plan promotion, Q-0144), #900 (routine fleet consolidated 2→… → **2 prompts:
  dispatch + reconciliation**, Q-0145), #898 (phase-gate dispatched-vs-self clarification, Q-0114).
- **Loop/ledger hygiene** — #883, #885, #889, #892 + the per-session close-outs.

This is the **fourth** band running (#820→#840→#870→#900) where the active autonomous-loop /
owner-product threads fill the buffer while the gated planned slots carry. But this band differs
in one important way the §3/§6 act on: **slot 2 finally executed** (the offline eval matrix the
band-#870 §6 deliberately split out of the creds-blocked lump shipped in full) — evidence the
band-#870 planning fix (split gated slots; ship the buildable half) **worked**.

## 3. Priorities restated (what the next band is for)

**The P0 integrity spine is finished, P1-2 is done, and P1-1's entire offline/CI half is now
DONE (full 34/34 AI tool-surface eval coverage + the self-cleaning drift guard).** The standing
priority is **the remaining P1 deterministic work + the active owner-steered product / autonomous
threads**:

1. **P1 correctness — the deterministic remainder.** With the eval matrix complete, the next
   *buildable-now* P1 work is **P1-3 invariants** (one parity/fence invariant per shipped P0 track
   that lacks a dedicated one). The remaining P1-1 pieces are both gated — **absence-guard Layer B**
   (design-for-review) and the **live-quality battery** (prod creds) — so they stay `creds`/`plan`.
2. **Mining structures is the active owner-steered product lane** — the owner has steered the
   night routine here for two sessions and the structures plan is turn-key: **Forge (Slice B)**,
   **Home (Slice C)**, **respec-polish / skill-titles (E/F**, unblocked by #891). Each a ▶ startable
   PR slice in [`mining-structures-skill-tree-plan-2026-06-14.md`](mining-structures-skill-tree-plan-2026-06-14.md).
3. **The autonomous-loop / Hermes thread** stays active (it consumed much of the buffer again).
   The reserved high-leverage slice is still the **read-only Railway log-triage skill** (Railway
   access verified live #840; the dispatch loop is operational and the fleet just consolidated to
   2 routines #900) — content-free prod-log surfacing for the caretaker routine. Reserve it a slot.
4. **AI §7 deterministic list-builders (BUG-0009)** — clears an OPEN bug; plan-first.
5. **Safety/community remainder** (plan-first) — welcome phase 2 PIL cards (quick-win; prototype
   exists), security service tiers 1+2 (Q-0111), image moderation (Q-0108), NL event scheduler
   (Q-0112, own AI-cost design first).
6. **Owner-led in parallel:** add `ROUTINE_PAT` · P1-4 live walks · `!uxlab` walk · mining V-16
   phase 2 PNG pack · BTD6 owner spot-check · **the substrate-kit (now owner-action — §6)**.

## 4. The next ~9 slices (planned after #900)

> Modular but not over-segmented (Q-0107): each slot is a real slice. The `#` column is
> **slot sequence, NOT reserved PR numbers** — GitHub assigns PR numbers globally across all
> parallel + housekeeping work, so do NOT map a slot to a predicted PR number or read this as a
> "#901–#930" schedule (Q-0142 — that misread fired a stale reconciliation dispatch). Pick the
> next slice by its **description**, verified against the live ledger. Each slot carries a
> **gate-state** tag: `ready` (buildable now) · `creds` (needs prod-like creds for part) ·
> `owner` (owner-steered) · `plan-first`. Owner steers override freely; note swaps here.

| # | PR (one session each) | Gate-state | Scope anchor |
|---|---|---|---|
| 1 | **This pass** — reconcile (#898) + plan + #893 disposition + substrate-kit escalation | — | Q-0107 (issue #901) |
| 2 | **Mining — Forge (Slice B)** | `ready` (owner-steered, active lane) | [structures plan §Forge](mining-structures-skill-tree-plan-2026-06-14.md); the active product burst, turn-key — upgrade/combine path on the audited `mining_workflow` seam |
| 3 | **P1-3 invariants — one per shipped P0 track that lacks a dedicated one** | `ready` | [hardening §P1-3](production-readiness/hardening-roadmap-2026-06-12.md); land the parity/fence invariant for each P0 as a focused slice (the last buildable-now P1 deterministic work) |
| 4 | **Railway log-triage skill** (autonomous-loop thread) | `ready` | the read-only log-triage skill (Railway logs verified live #840; dispatch loop operational, fleet consolidated #900); content-free surfacing of prod log signal for the caretaker routine — Q-0130 |
| 5 | **Mining — Home (Slice C) + respec-polish/skill-titles (E/F)** | `ready` (owner-steered) | [structures plan §Home/§E/§F](mining-structures-skill-tree-plan-2026-06-14.md); E/F now unblocked by the #891 skill tree |
| 6 | **AI §7 deterministic list-builders** (BUG-0009) | `plan-first` | the AI orchestration §7 list-answer builders BUG-0009 needs — plan-level; clears an OPEN bug |
| 7 | **Safety lane — welcome phase 2 (PIL cards)** | `ready` (quick-win) | Q-0110 — the `render_welcome_card` prototype exists; small follow-up on the stable embed-first v1 |
| 8 | **P1-1 — absence-guard Layer B** (negative-existential gate) | `creds` / design-for-review | [hardening §P1-1](production-readiness/hardening-roadmap-2026-06-12.md) §4.3 crux; the last P1-1 piece — needs the design review + prod-like creds |
| 9 | **Safety lane — security service tiers 1+2** | `plan-first` | Q-0111 — raid detection + account-age filter (tiers 3+4 declined); cite `ux/pattern-library.md` `mock_security_*` pattern_ids |
| 10 | **Buffer / steered slot** — owner-steered product (mining V-16 phase 2 PNG pack / BTD6 decode ⭐ item 3) or autonomous-loop maturation (Hermes bug-triage build, Q-0121) | `owner` | in-flight / owner-led |

**Deliberately *not* in this band** (unchanged unless the owner steers): the NL event scheduler
build (Q-0112 — own AI-cost design first) · P1-4 owner live-walks (owner-led) · myprofile PR A ·
the live-quality eval battery (prod creds) · the CV2-adoption ADR (wants the owner's `!uxlab`
walk) · candidate-rule promotion (gated Q-0120).

**Escalated off the queue this pass:** the **portable substrate-kit PR 2 remainder + PR 3** has
now carried **four consecutive bands** (#820→#840→#870→#900 untouched). Per the band-#870 §6
escalation rule, it is **removed from the plannable decade queue and moved to the owner-action
list** (§3 item 6 + the roadmap's owner-led row): it is genuinely owed but is owner-steered OSS
productization, so it cannot keep occupying a plannable slot that an autonomous session would skip
as `owner`-gated. It returns to the queue only when the owner re-steers it.

## 5. Pruned / fixed by this pass

- **Ledger reconciled.** The one genuinely-missing PR, **#898** (phase-gate dispatched-vs-self
  clarification, Q-0114), was folded into the existing `#892 + #889` loop-hygiene `Recently
  shipped` entry (same phase-gate/loop-hygiene theme) — retitled **`#898 + #892 + #889`** — so the
  ledger count holds at 20 without archiving (no new standalone entry needed for a small docs PR).
- **[reconciliation-pass-2026-06-14-band870.md](reconciliation-pass-2026-06-14-band870.md)
  re-badged `historical`** — its band (#871–#900) is fully scored in §2 above.
- **`docs/current-state.md` ▶ Next action re-pointed** at *this* doc (by name/date, no PR-number
  range — the band-#800 §6 discipline), and the **P0 spine + P1-2 + P1-1 offline half (34/34)
  complete / next = P1-3 invariants + mining structures + log-triage** state restated.
- **`docs/roadmap.md`** — the live-decade-queue pointer and the **Now** horizon re-pointed from
  the band-#870 pass to this pass; P1-1 eval matrix marked ✅ COMPLETE (offline half).
- **Open-PR disposition (Q-0125):** recorded #893 (owner's mining handoff) in §1 with a
  band-#930 escalation trigger.
- **Substrate-kit escalated** to the owner-action list after its fourth carry (§4, §6).
- **Marker reset** — `Last reconciliation pass` → **#900**; `check_reconciliation_due.py` next
  fires at #930.
- **No runtime bugs noticed** (docs-only pass) → nothing appended to the bug book; **BUG-0009 /
  BUG-0011** stay OPEN for the AI / caretaker lanes.

## 6. The system improvement this pass made (the point of the loop)

**The band-#870 planning fix worked — and proved the escalation rule must actually fire.** Last
pass (§6) made two structural changes to the queue: tag every slot with a `gate-state`, and give a
multi-band-carried slot an explicit "**escalate if it carries a fourth band**" trigger. This pass
is the first chance to evaluate both:

1. **Gate-state tagging worked.** The band-#870 §4 split slot 2 into "ship the offline/deterministic
   eval half now, defer only the creds-gated live battery." That half **shipped in full this band**
   (#878→#896, 34/34). The tag did exactly what it was for — it made the *buildable* portion of a
   gated slot legible, so the work got picked up instead of carrying whole as a creds-blocked lump.
   **Keep gate-state tags; they are now load-bearing.**

2. **The escalation trigger had to be honored, not just written.** The substrate-kit slot carried
   its **fourth** band. The band-#870 §6 rule said "escalate to the owner-action list if it carries
   a fourth band" — and the failure mode this rule guards against is precisely an agent *writing*
   the rule and then, next pass, re-listing the slot in the queue anyway out of momentum. So this
   pass **acts on it**: the substrate-kit is removed from the plannable decade queue (§4) and moved
   to the owner-action list (§3.6 + roadmap). A queue slot that an autonomous session will always
   skip as `owner`-gated is not plannable capacity — keeping it in the list overstated the band's
   plan every time and crowded out a `ready` slice.

   **The generalized rule (new this pass):** a slot tagged `owner` that carries **four** bands is
   **demoted from the decade queue to the owner-action list** automatically — it returns only when
   the owner re-steers it. `ready`/`plan-first` slots are not demoted (they're the autonomous
   session's actual work); only `owner`-gated slots are, because only they have an external blocker
   the loop cannot clear itself. This makes the decade queue an honest list of **autonomously
   achievable** work, with owner-blocked threads tracked where the owner will see them.

The forward idea this pass contributes (Q-0089) is in `docs/ideas/` — and it targets the *other*
recurring pattern this scorecard shows: the buffer slot has *been* the band four times running, so
the buffer should be planned as a first-class "active-thread" slot, not overflow.
