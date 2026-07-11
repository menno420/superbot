# Fleet strategy synthesis — 2026-07-11 (4 independent external reviews + next-batch)

> **Status:** `reference` — synthesis of **four independent external strategy reviews** (2×
> ChatGPT strategy + 2× next-batch design, from the [dispatch
> kit](../owner/dispatch-prompts-2026-07-11.md) Sol prompts, run in regular + deep-research
> mode). Captures the **convergent** signal, the **new** framings beyond the internal [fleet
> review](fleet-review-2026-07-11.md), the next-batch shortlist, and the decisions surfaced.
> External-review caveat (Q-0120): the memos browsed status docs and carry some **stale
> facts** (see §5) — treat specifics as leads.

## 1. What the external reviews CONFIRM (independent corroboration of the internal review)

All four converge on the internal review's core read, which is worth stating because it's now
**independently confirmed**, not just self-assessed:

- **"Coherent architecture, sprawling execution."** The idea→sim→manager→builder→product
  pipeline is a real design, not a random collection — but the portfolio optimizes for
  *producing validated repo state*, not external usage/revenue.
- **Core value = `superbot-next`, `substrate-kit`, `fleet-manager`, `websites`, `venture-lab`.**
  Same four-to-five the internal review named.
- **Archive codetool-labs · park trading-strategy · consolidate the games** (one Games
  portfolio, one flagship at a time) · keep `product-forge` as an on-demand incubator, not a
  standing seat. Matches the triage register.
- **The bottleneck is the owner-click queue.** Confirmed. Value is stuck behind publish /
  merge / deploy / secrets / decisions.

## 2. What's NEW (beyond the internal review — worth adopting)

1. **The "release-operator" gap (the sharpest new insight).** The fleet has builders,
   reviewers, coordinators, simulators, ideators — but **no single accountable function whose
   job ends only when something is publicly usable or purchasable.** The owner-click queue is
   the *symptom*; the missing release-operator role is the *cause*.
2. **"Owner Launch Hour" — empty the queue in one atomic, pre-filled packet** (don't *improve*
   the queue, *empty* it): publish 1 product → 1 real Stripe test purchase → publish its
   acquisition asset → merge the blocked game PRs → publish 1 game release → 1 deployment
   config → record public URLs + failures centrally. Everything pre-filled: destination URLs,
   creds needed, exact clicks, rollback, verification. No decisions hidden in the procedure.
3. **A portfolio WIP-cap stop-rule:** *"No new product/feature lane starts while more than 3
   owner-action items are blocking already-built external value."* A concrete backpressure
   mechanism the fleet currently lacks.
4. **The "portfolio theater" risk:** the fleet is exceptionally good at generating evidence
   that *work exists* and weak at discovering whether anyone *outside* wants it. Tests, parity,
   status ledgers establish *implementation confidence*, never *demand*. Owner remains the real
   single-point-of-failure (all credentials + irreversible + aesthetic + commercial judgment).
5. **Revenue: the $29 Stripe Webhook Test Kit is the strongest first bet** (specific technical
   pain · clear buyer · impulse price · free "gotcha" article as the distribution wedge ·
   search/community-findable) — *over* the $49 membership kit (broad, more competition, needs a
   narrow segment). *(One of the four memos argued membership-kit; the more rigorous three
   favor the test-kit. The internal review listed all three without ranking — this is the
   refinement.)* First goal is **one purchase from someone with no relationship to the fleet.**

## 3. The next-batch shortlist (strong convergence across both design memos)

The design memos agree: **don't found another large autonomous lane — the limiting resource is
activation capacity, not implementation capacity.** Build these as **cross-repo programs /
products inside existing repos**, not new repos (the `product-forge` graduation rule: a new
repo only once a product shows independent users / release cadence).

| Rank | Project | Home | Why |
|---|---|---|---|
| 1 | **Owner Launch Console** | extend `websites` + `fleet-manager` | Turns owner-clicks into a finite, preflighted, auto-verified lifecycle (stable IDs, exact control-surface links, copy-ready values, post-action verifiers). Extends the existing `/queue` + generated owner-queue — **not a new dashboard.** |
| 2 | **Plugin Activation Program** | `superbot-next` + `superbot-plugin-hello` + games/idle | The contract + host + pinning + in-tree exemplar already exist. Work = *activation*: seed the empty public hello repo, prove one real external plugin boots in a test guild, then adapt the finished idle/games engines. |
| 3 | **Fleet Arcade / Play Portal** | new public surface **inside** `websites` | One public front door for the already-built playables (Lumen Drift, mineverse, games-web) with maturity labels + attribution telemetry. Assets exist; the new work is catalog + launch + measurement. |
| — | Repo Truth Audit · Theme Studio · Server Blueprint Packs · cross-game achievements · trivia plugin | incubate in `product-forge` / `websites` | Lower-priority; **Repo Truth Audit** is the most interesting new revenue idea — productize the fleet's own evidence-grounded repo-analysis capability (reuses substrate + sim-lab validity gate + the review funnel). Sequence after real external demand. |

**The "do NOT build" consensus** (both memos, strongly): no second dashboard/queue/registry
(extend `websites`) · no second idea-engine/simulator/coordinator/memory-framework · no plugin
SDK or marketplace before **2** real external plugins run · no new standalone game repos · no
payments/crypto in games · no native mobile app · no multi-tenant hosted fleet platform yet ·
fleet-manager must **not** directly rewrite lane-internal docs (raise ORDERs instead).

## 4. Centralization — the external "sharpest version" (a rider to the [plan](fleet-centralization-plan-2026-07-11.md))

Both design memos **independently endorse custodian-primary** (the owner's Option A) and add a
concrete sharpening the internal plan should adopt:

- **One typed fleet-state model** as the machine contract — a transitional `control/status.v1.json`
  / structured frontmatter companion — with `status.md` / `roster.md` / `/fleet` / `/queue` all
  **generated projections** off it. Stop parsing unbounded free-form Markdown as the integration
  contract (it's the fragility behind the drift the review found).
- **One deterministic event path:** repo-change/wake → ingest → schema-validate → normalize →
  reconcile vs GitHub/deploy truth → canonical snapshot → generated docs/API → freshness+drift
  guards → optional ORDER. No component re-fetches/reinterprets the same fact.
- **Mutation boundary:** each repo authoritative for its internal domain; fleet-manager
  authoritative for normalized *cross-repo* state; websites is a *projection*, never a competing
  store. fleet-manager raises reconciliation ORDERs for a stale lane doc, never rewrites it.

This upgrades the plan's §3 "generate from heartbeats" gap-fixes into a **typed-state-first**
design — recommend folding it into the fleet-manager centralization build (P1/P2).

## 5. Stale-fact flags (Q-0120 — do NOT act on these memo specifics)

- The memos cite drifting counts (37/49 subsystems; 253/245/212 goldens; **"five blocked game
  PRs"**) from status docs. The "5 blocked PRs" is **stale** — 3 (`superbot-games`
  #27/#32/#38) already merged; only #49/#50 remain. Trust live GitHub, not the memo numbers.
- One memo lists the **4 critical fixes as the admission gate** for the next batch — worth noting
  **3 of the 4 are already handled this session:** venture-lab fail-open ✅ (#49), superbot-next
  races 🔧 (in-flight via the Sonnet-5 dispatch, which is also mandated to sweep farm/mining —
  see the Codex §below), substrate-kit gate ✅ (already on main). Only **mineverse CSRF** remains.
- The memos corroborate the internal finding that **`superbot-idle` self-parks on a
  "contract-absent" blocker that is actually resolved** — an unreconciled-status artifact.

## 6. The three decisions the reviews surface (recommendations attached)

1. **Which single game is the flagship release?** (needed to consolidate the Games portfolio.)
2. **What exact threshold triggers the `superbot-next` cutover?** (else permanent dual
   maintenance — both bots keep absorbing work.)
3. **What is the 7-day objective — first external revenue · first public game release · cutover
   progress?** **Converged recommendation: first external revenue, Stripe Webhook Test Kit as
   the one-week flagship**, run as the Owner Launch Hour (§2).

## Codex review note (superbot-next money-race class widened)

The two superbot-next Codex PRs (#196, #206, docs-only reviews) **confirm F-001/F-002/F-003
against source and widen the money-race class**: #206 adds **farm collect (P0 double-credit),
farm buy/upgrade (P1 double-charge), mining sell/sell_all (P0 over-credit)** — same unlocked-read
+ `NATURAL_KEY`-no-fence pattern — and verifies **clean**: treasury (atomic), blackjack tournament
(`FOR UPDATE`), and **AI prompt-injection containment** (`wrap_untrusted_text`). All are within
the Sonnet-5 dispatch's fix mandate (prompt step 3 = sweep the same class across casino/mining/
treasury/farm). Recommend the superbot-next lane consume + close #196/#206 as it lands the fixes.
