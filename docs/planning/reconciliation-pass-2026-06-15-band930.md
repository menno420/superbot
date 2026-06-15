# Reconciliation pass — 2026-06-15 · the band-#930 Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed
> **#930** (cadence = every **30th** merged PR per Q-0134; previous cadence pass
> [the band-#900 pass](reconciliation-pass-2026-06-15-band900.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#931**
> (`.github/workflows/reconciliation-trigger.yml`) — the **seventh** consecutive real cadence
> fire of the autonomous issue-trigger (after #781, #801/#822, #841, #871, #901), and a live
> proof the loop self-fires: #931 was authored by **`menno420`** (the `ROUTINE_PAT` owner), not
> `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 priorities
> restated · §4 the next ~9 PRs · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#930** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the band-#900 pass (band #901–#930):** the band was again almost entirely
self-reconciled — each code session added its own `Recently shipped` entry under the born-red
Q-0133 gate. The genuinely-not-yet-entered PRs at pass start (per `check_current_state_ledger
--strict`): the **#915–#928 docs band** (#915/#916/#919/#921/#923/#925/#927/#928 — all docs/skill/ops
only, the Hermes gpt-5.4-mini model-swap + ops-docs maturation work) plus #925 (current-state
scannability). #930 was already present (stamp-line block). #917/#918/#920/#924/#926/#910/#912/
#905/#906/#897 were already entered by their own sessions. #887/#890/#902/#903/#904/#907/#908/
#909/#911/#913/#914/#922 were never merged or are not present as merge commits (skipped/closed/
branch-only numbers — GitHub assigns numbers globally across PRs **and** issues).

**Ledger reconciled:** the #915–#928 docs band entered as **one grouped `Recently shipped` entry**
(all docs-only, one theme); the three oldest live entries (#862/#859/#855) archived to
[`current-state-archive.md`](../current-state-archive.md) to hold the soft ratchet at 20.

**Open PRs at pass time (disposition — Q-0125):**

| PR | What | Disposition |
|---|---|---|
| **#929** | `feat(security): tiers 1+2 — raid detection + account-age filter (Q-0111)` — a `claude/*` session PR opened 2026-06-15 22:48, labelled **`needs-hermes-review`** (Q-0117 carve-out: a substantial new subsystem, not auto-merged), born-red session card | **leave open / Hermes-review carve-out** — it is in active review (the Q-0117 independent-review gate), not stale or redundant, opened minutes before this pass. Not in this reconciler's merge authority (the `needs-hermes-review` label explicitly removes it from auto-merge). No action; it is the in-flight execution of band-#900 slot 9. |

The owner's mining-handoff PR **#893** (open at the band-#900 pass, flagged to surface this band)
is **no longer open** — resolved (merged/closed) since. The #766/#771 stale/redundant rot class
stays clear across the whole #901–#930 band.

## 2. Band scorecard (the band-#900 pass §4 queue, band #901–#930 → reality)

| Slot (from the band-#900 pass §4) | Outcome |
|---|---|
| 1 · the band-#900 pass itself | ✅ (the pass that wrote that queue) |
| 2 · **Mining — Forge (Slice B)** | ✅ **#905** (gear-tier crafting gate on the generic `mining_structures` table) |
| 3 · **P1-3 invariants** | ✅ **#917** (settings declared⇔consumed parity + games two-sided-economy fence + disposition doc) **+ #918** (settings reverse-parity bijection) — P1-3 SUBSTANTIALLY COMPLETE |
| 4 · **Railway log-triage skill** | ✅ **#906** (`scripts/hermes/log_triage.py` — content-free deterministic error-scan/crash-loop analyzer, Q-0130) |
| 5 · **Mining — Home (Slice C) + respec/titles (E/F)** | ✅ **#910** (Home backdrop) **+ #912** (respec polish + skill/milestone titles) — **mining structures lane COMPLETE** |
| 6 · **AI §7 deterministic list-builders (BUG-0009)** | ✅ **#924** (slice 1, MK-related) **+ #926** (slices 2/2b, Geraldo per-level + mode groupings) — 3 of 4 families shipped; slice 3 (newest-towers ordering) **data-gated** (`towers.json` has no release-order field) |
| 7 · **Safety — welcome phase 2 (PIL cards)** | ✅ **#920** (was already DONE per the band-#900 queue) |
| 8 · **P1-1 — absence-guard Layer B** | ❌ → carried (design-for-review + creds) |
| 9 · **Safety — security service tiers 1+2** | 🟡 **in flight #929** (`needs-hermes-review`) |
| 10 · **Buffer / steered** | consumed by the Hermes gpt-5.4-mini model-swap + ops-docs band (#915–#930) |

**Seven of ten planned slots executed (2/3/4/5/6/7 fully shipped; 9 in flight) — the highest
plan-execution ratio of any band so far.** The band-#900 §6 lesson ("gate-state tags are
load-bearing; ship the buildable half of a gated slot") held: every `ready`-tagged slot landed,
and the only carries are the two genuinely-gated pieces (Layer B `creds`/design-for-review; slice
9 mid-review). The buffer (slot 10) was a coherent owner-steered thread (the Hermes model swap),
not scattered overflow — a healthier buffer than the prior three bands.

## 3. Priorities restated (what the next band is for)

**The P0 integrity spine is finished, P1-2 is done, P1-1's whole offline/CI half is done (34/34),
P1-3 is substantially complete, the mining structures lane is COMPLETE, BUG-0009 is 3/4 done, and
the Railway log-triage skill shipped.** The buildable-now `ready` queue has genuinely **thinned** —
most remaining named work is `plan-first`, `creds`-gated, `owner`-steered, or `data`-gated. The
next band is therefore weighted toward **promoting plan-first ideas into executable plans** (this
pass promotes one — §5) and the remaining turn-key slices:

1. **The now-ungated turn-key slices.** The **games-economy faucet/sink diagnostic** (its
   sink-heavy gate cleared by respec #912 + structures #905/#910 — promoted to a full plan this
   pass, §5) and **myprofile PR A** (read-only profile card, plan already exists) are the two
   clean `ready` slices left.
2. **Security tiers 1+2 lands** (#929 finishes Hermes review) — then **image moderation** (Q-0108)
   and the **NL event scheduler** (Q-0112, own AI-cost design first) are the safety/community
   remainder, both `plan-first`.
3. **BUG-0009 slice 3** (newest-towers ordering) is `data`-gated — needs sourced release-order data
   via the ADR-006 / `!btd6ops seed-data` provenance lane, then appends one builder to
   `deterministic_btd6_list_reply`.
4. **The P1 remainder is gated** — absence-guard **Layer B** (design-for-review) + the
   **live-quality eval battery** (prod creds). Both stay `creds`/`plan`.
5. **The autonomous-loop / Hermes thread** stays active (it was the buffer again). The reserved
   high-leverage build is the **Hermes bug-triage `gh issue create` write** (Q-0121) and the
   **executor-chain trigger via workflow** idea (the `continue`-issue self-chaining gap).
6. **Owner-led in parallel:** P1-4 live walks · `!uxlab` walk · mining V-16 phase 2 PNG pack ·
   BTD6 owner spot-check · **the substrate-kit** (owner-action since its band-#900 demotion).

## 4. The next ~9 slices (planned after #930)

> Modular but not over-segmented (Q-0107): each slot is a real slice. The `#` column is
> **slot sequence, NOT reserved PR numbers** — GitHub assigns numbers globally across all parallel
> + housekeeping work **and issues**, so do NOT map a slot to a predicted PR number or read this as
> a "#931–#960" schedule (Q-0142 — that misread fired a stale reconciliation dispatch). Pick the
> next slice by its **description**, verified against the live ledger. Each slot carries a
> **gate-state** tag: `ready` (buildable now) · `creds` (needs prod-like creds for part) ·
> `owner` (owner-steered) · `plan-first` · `data` (needs sourced data). Owner steers override
> freely; note swaps here.

| # | PR (one session each) | Gate-state | Scope anchor |
|---|---|---|---|
| 1 | **This pass** — reconcile (#915–#928 band) + plan + #929 disposition + control-plane drift fix + idea→plan promotion | — | Q-0107 (issue #931) |
| 2 | **Games-economy faucet/sink diagnostic** | `ready` | [the plan promoted this pass](games-economy-faucet-sink-diagnostic-plan-2026-06-15.md); read-only `diagnostics_service` provider summing economy audit reasons into a per-guild net-coin-flow view — the now-ungated turn-key slice |
| 3 | **myprofile PR A — read-only profile card** | `ready` | [`myprofile-foundation-plan-2026-06-10.md`](myprofile-foundation-plan-2026-06-10.md) §PR A; zero writes, turn-key — the pipeline's read-only card |
| 4 | **Security tiers 1+2 review + land** (#929) | `owner`/review | finish the Q-0117 Hermes review on #929; the safety/community slot 9 in flight |
| 5 | **Image moderation (Q-0108)** | `plan-first` | safety/community lane; own a small plan first (cite `ux/pattern-library.md` patterns) |
| 6 | **AI §7 next workflow family** (post-prod-check) | `plan-first` | the AI orchestration §7 families beyond the BUG-0009 list-builders; plan-level |
| 7 | **Hermes bug-triage `gh issue create` write (Q-0121)** | `plan-first` | the autonomous-loop maturation slice — let the caretaker routine open a bug-book-backed issue; design the write scope first |
| 8 | **P1-1 — absence-guard Layer B** (negative-existential gate) | `creds` / design-for-review | [hardening §P1-1](production-readiness/hardening-roadmap-2026-06-12.md) §4.3 crux; the last P1-1 deterministic piece — needs the design review + prod-like creds |
| 9 | **BUG-0009 slice 3 — newest-towers ordering** | `data` | needs sourced release-order data (ADR-006 / `!btd6ops seed-data` provenance lane); then one builder appended to `deterministic_btd6_list_reply` |
| 10 | **Buffer / steered slot** — owner-steered product (mining V-16 phase 2 PNG pack / BTD6 decode ⭐ item 3) or autonomous-loop maturation (executor-chain trigger via workflow) | `owner` | in-flight / owner-led |

**Deliberately *not* in this band** (unchanged unless the owner steers): the NL event scheduler
build (Q-0112 — own AI-cost design first) · P1-4 owner live-walks (owner-led) · the live-quality
eval battery (prod creds) · the CV2-adoption ADR (wants the owner's `!uxlab` walk) · candidate-rule
promotion (gated Q-0120) · the substrate-kit (owner-action since the band-#900 demotion).

## 5. Pruned / fixed by this pass

- **Ledger reconciled.** The #915–#928 docs band added as **one grouped `Recently shipped` entry**
  (Hermes gpt-5.4-mini model-swap + ops-docs maturation); the three oldest live entries
  (#862/#859/#855) archived to hold the soft ratchet at 20.
- **Control-plane drift FIXED (the headline fix this pass).** The `Gates / blocked work` section
  still claimed the autonomous loop "has **never self-fired**" and "stays inert until the owner adds
  `ROUTINE_PAT`" — **stale and contradicted by both the canonical control-plane table (rows 1/2/6 ✅)
  and the live read**: issue #931 (this pass's trigger) was auto-opened authored by **`menno420`**,
  the `ROUTINE_PAT` owner, which is only possible if the PAT is set and the loop self-fires. Rewrote
  the Gates bullet to "**LIVE and self-firing**" with the live tell (trigger-issue author) recorded,
  matching the canonical table. This is exactly the Q-0135 control-plane drift class the loop-health
  probe guards against — caught here via the GitHub-MCP read because `gh`/`check_loop_health.py` was
  unavailable in the sandbox (SKIP).
- **[reconciliation-pass-2026-06-15-band900.md](reconciliation-pass-2026-06-15-band900.md)
  re-badged `historical`** — its band (#901–#930) is fully scored in §2 above.
- **`docs/current-state.md` ▶ pointers re-pointed** at *this* doc (by name/date, no PR-number range
  — the band-#800 §6 discipline); the live ▶ NEXT moved from "security tiers 1+2" (now in flight
  #929) to the **games-economy faucet/sink diagnostic** (the now-ungated turn-key slice).
- **`docs/roadmap.md`** — the live-decade-queue pointer + the **Now** horizon re-pointed from the
  band-#900 pass to this pass; mining structures lane marked ✅ COMPLETE, P1-3 ✅ substantially
  complete, BUG-0009 3/4.
- **Idea → plan promotion (the "keep the plans fed" step, Q-0144).** With the `ready` queue
  thinning, promoted the best now-ungated idea — the **games-economy faucet/sink diagnostic**
  (gate "promote once a sink-heavy slice lands" cleared by respec #912 + structures) — into a
  **fully executable plan**: [`games-economy-faucet-sink-diagnostic-plan-2026-06-15.md`](games-economy-faucet-sink-diagnostic-plan-2026-06-15.md).
  Re-badged the idea capture `historical` (promoted) + annotated the ideas README.
- **Open-PR disposition (Q-0125):** #929 recorded in §1 as the `needs-hermes-review` carve-out
  (leave open / not this reconciler's merge authority).
- **Marker reset** — `Last reconciliation pass` → **#930**; `check_reconciliation_due.py` next
  fires at #960.
- **No runtime bugs noticed** (docs-only pass) → nothing appended to the bug book; **BUG-0009**
  (slice 3 data-gated) / **BUG-0011** (Hermes gateway crash-loop) stay OPEN.

## 6. The system improvement this pass made (the point of the loop)

**This pass caught the first control-plane drift the new `check_loop_health.py` guard (Q-0135) was
built to catch — and proved the *fallback* read path is the load-bearing one.** Q-0135 added a live
GitHub probe so the control-plane table can't silently drift the way it did before 2026-06-14 (when
it claimed the loop had never self-fired while live GitHub already proved it had). This pass, the
probe itself **SKIPped** — `gh` is unavailable in the reconciliation sandbox — yet the same drift
had re-appeared in a *different* doc (the `current-state.md` Gates section, which the probe doesn't
read). The drift was caught anyway, via the routine's documented fallback: **read the trigger
issue's author through the GitHub MCP** (`menno420` = PAT set). 

**The generalized improvement (recorded for the next pass):** the control-plane truth has **two**
homes — the canonical table in `autonomous-routines.md` (which the band-#870 pass fixed and is
correct) **and** the `current-state.md` Gates bullet (which drifted again). A single fact in two
prose homes is a standing drift risk. The durable fix is to make the Gates bullet **point at** the
canonical table rather than restate its verdict — so there is one source of truth and the second
home can't contradict it. This pass took the smaller step (re-synced the Gates bullet + made it
reference the table); the next pass that touches this should consider collapsing the Gates bullet to
a pure pointer. This is the Q-0089 forward idea this pass contributes (in `docs/ideas/`).
