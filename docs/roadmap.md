# SuperBot — Implementation Roadmap

> **Status:** `living-ledger` — the one cross-area "what's planned, for which sector, in
> what order" index, now organised under the **5 planning sectors** (S1–S5, Q-0137) so each
> sector is a self-contained dispatch queue. **Last updated:** 2026-06-19 (planning-map cleanup —
> ▶ pointer de-staled to the live band + the new [plan index](planning/README.md); restructured by
> sector 2026-06-14, [sector map](repo-sector-map.md)).
>
> **▶ The live queue — read [`docs/current-state.md`](current-state.md) ▶ Next action.** That is the
> single live "what is startable right now" pointer; this page intentionally **does not restate it**
> (restating it inline is exactly what kept going stale — the pointer used to lag several bands behind).
> The current 30-PR band queue is owned by the **newest** reconciliation pass —
> [`planning/reconciliation-pass-2026-06-19-band1110.md`](planning/reconciliation-pass-2026-06-19-band1110.md)
> §4 (fourteenth Q-0107 pass; the 30-PR cadence is Q-0134). **The full plan inventory — active plans by
> sector + the historical/superseded set — is the new [`planning/README.md`](planning/README.md)
> (2026-06-19).** The **developer-dashboard / control-API / website** initiative (the dominant active
> thread) is homed there and in the
> [website next-steps handoff](operations/website-split-next-steps-2026-06-19.md) — it was previously
> unrouted from this roadmap.
>
> **What this is:** a thin router over the detailed plans. Each row is a one-line
> description + a link to the **authoritative plan** and the area **folio** — it restates
> nothing. The plan and the folio win over this page.
>
> **What this is *not*:** a schedule. Horizons are **relative sequencing, not dates** — the
> maintainer works associatively ([`owner/maintainer-working-profile.md`](owner/maintainer-working-profile.md))
> and idea-order ≠ implementation-order. A "gate" is what must clear before an item is
> ready, not a deadline.
>
> **Initial cut — evolving, not locked.** New plans get slotted into their area below as
> they land (see [Adding a plan](#adding-a-plan)); horizons will re-sequence as plans
> arrive and gates clear. Treat the ordering as a current best-guess, not a commitment.
>
> **▶ Production-readiness:** the seven per-subsystem readiness maps + the consolidated
> [**hardening roadmap**](planning/production-readiness/hardening-roadmap-2026-06-12.md)
> (P0 integrity → P1 correctness → P2 drift, with the gating owner Qs) are the
> risk-ranked "what's left to be production-ready" view across all subsystems. Index:
> [`planning/production-readiness/`](planning/production-readiness/README.md).
> **All gating decisions answered as of 2026-06-12 evening** (Q-0098/Q-0099/Q-0100 + Q-0097
> = operator-managed findings lifecycle); no hardening track waits on a decision. **P0 spine
> progress: the P0 spine is COMPLETE.** P0-1 wager money-safety (#748) ✅ · P0-3 settings
> pointer-lane (#777/#794) + **arc PR 3 delegated-Setup apply (#817, Q-0098)** ✅ · **P0-4 channel
> ownership — PR 1 clone/overwrite (#820) + PR 2 creation/category (#825), Q-0100** ✅ · **P0-2
> media/YouTube retention + data-minimization (#829, Q-0099)** ✅. **Next = the P1 correctness
> tier** (P1-1 eval-smoke matrix → P1-2 health-findings lifecycle → P1-3 invariants) — see the
> [band-#840 decade queue](planning/reconciliation-pass-2026-06-14-band840.md) §4.

> **▶ Product North Star (Q-0190, 2026-06-21):** SuperBot is **free for everyone, forever** — every
> function available to all users, with **no paywalls, premium tiers, or freemium feature-gating**. The
> strategy is **consolidation**: one free, all-inclusive bot that replaces 5+ paywalled bots, so *free
> **and** better — and all-in-one* is the competitive wedge (pairs with the V-14 feature-mining lane +
> the Q-0080 public-bot goal). The only allowed money surface is a voluntary *zero-benefit* support link
> to offset hosting + AI cost (extends Q-0039 cosmetic-only / no-P2W). Every new plan inherits this as a
> design filter. Full statement: [`ideas/free-for-everyone-mission-2026-06-21.md`](ideas/free-for-everyone-mission-2026-06-21.md).

## How to read

- **Now** = active lane / owed verification · **Next** = queued and ready (no blocking
  gate) · **Later** = wants a decision or a gate to clear first · **Someday** = captured
  ideas, not approved.
- **Gate** = the concrete thing that must clear first (a decision, a dependency, a
  stability bar). An item doesn't move up until its gate clears.
- **Authority:** `docs/current-state.md` owns *what is true now*; the **folios** own
  per-area detail; the **trackers/plans** own scope. This page only sequences them.
- **Ideas flow in here.** A captured idea (`docs/ideas/`) is routed onto a horizon below
  once it has a clear direction; until then it sits in **Someday** or in discussion (the
  question router). The intake → route → groom mechanism is
  [`ideas/README.md`](ideas/README.md) — promoting a backlog idea to a horizon is standing
  grooming work, not scope creep.

## By sector — the live dispatch queues

> **This is the top layer.** The repo divides into **five planning sectors**
> ([`repo-sector-map.md`](repo-sector-map.md), owner decision Q-0137): **S1 Bot product · S2 BTD6 ·
> S3 AI-Memory system (the *mechanism*) · S4 Documentation system (the *content*) · S5 Operations /
> control-plane.** Each has a self-contained **Now / Next / Later** below; the detailed plans are in
> the [area drill-down](#area-drill-down-each-area-homed-to-a-sector) further down, every area homed
> to exactly one sector.
>
> **Why sectors — the dispatch model.** A worker is dispatched by **sector + action + executor**: e.g.
> *"continue the S2 BTD6 plan execution"* or *"plan the S3 AI-Memory sector, then an hour later execute
> it."* The worker reads its sector's **Now** here, opens the linked plan/folio, and advances it. Each
> `Now` item is tagged **▶ startable / ⛔ gated / 👤 maintainer**, and each sector carries a default
> **executor** (Claude-in-repo · Hermes-VPS · maintainer) — both defined in the dispatch contract
> ([`repo-sector-map.md`](repo-sector-map.md) § "dispatch targets"); a `Now` that is entirely ⛔/👤 is
> **not** autonomously dispatchable (fall through to the first ▶). Each sector's **Dispatch** line says
> what *plan* vs *execute·continue* mean for it, **plus an orthogonal unattended-fit tag** — 🟢 `auto`
> (offline-verifiable + self-mergeable) · 🟡 `review` (substantial/risky runtime — still auto-merges on
> green, just worth a careful build + second look) · 🔵
> `live` (needs a live guild walk / creds to verify) · 🟠 `ext-data` (commits external data, owner-confirm
> first) — so a *scheduled empty-fire* run can tell whether a `▶` lane is one it can actually **complete
> and merge** unattended, not just begin (the dimension `python3.10 scripts/dispatch_menu.py --unattended`
> resolves; contract in `repo-sector-map.md` § "the unattended-fit tag"; Q-0143/#1285). This index makes the
> sectors **dispatch-ready**; the Hermes/routine **wiring** that turns a phone message into a `/fire`
> is **Q-0137 Thread 1** (owner-undecided) and is *not* built here — the actions map onto the existing
> routine fleet in [`operations/autonomous-routines.md`](operations/autonomous-routines.md).
>
> **Sector ⇄ review-unit:** S1–S5 (planning) coarsen the A1–A5 **review** domains
> ([`repo-review-map.md`](repo-review-map.md)); the mapping table lives in
> [`repo-sector-map.md`](repo-sector-map.md) § "Two taxonomies". Plan a roadmap → use **sector**;
> scope a PR review → use **review unit**.

### S1 — Bot product  ·  *the Discord bot users interact with (in-bot AI is a slice within it)*
- **Now:** the **P1-1 AI eval-smoke matrix**
  ([plan §P1-1](planning/production-readiness/hardening-roadmap-2026-06-12.md)) — in-bot AI correctness
  (gates · fallback · grounding-refusal). Layer A ✅ #855; the **offline eval/smoke matrix ✅ SHIPPED
  #878** (`tests/evals/smoke.py`, CI-gated); **▶ Layer B** (the absence-guard negative-existential gate)
  is startable; the **⛔ live half** is creds-gated (owner-led P1-4); BUG-0009 open
  ([bug book](health/bug-book.md)). **The P0 integrity spine AND P1-2 are COMPLETE.** Product alternates
  (owner-steered): *(games **P0-1 wager money-safety ✅ #748**; the cross-game **settle-once** terminal
  guard ✅ #1444/#1445 + its **CI adoption guard** ✅ #1454)* · **▶ mining structures/skill-tree**
  ([turn-key plan](planning/mining-structures-skill-tree-plan-2026-06-14.md) — Vault shipped #884;
  skill tree + cap + Forge/Home are startable; **⛔ V-16 phase 2** still owner PNG pack) ·
  **⛔ AI §7 workflow families** (post-prod-check).
- **Next:** safety/community remainder (image moderation · security tiers 1+2 · NL event scheduler) ·
  `myprofile` PR A (turn-key) · help home/navigation plan · settings Phase 2 tail → Phase 3.
- **Later:** server-mgmt **PR13 AI generation layer** + governance setup (gated Q-0008/Q-0011) · media
  channel-summary (gated Q-0099) · the 4-button Help Home navigation doctrine (Q-0078) · games deferred
  follow-ups · the product-growth drafts (most of the Later/Someday product-growth list below).
- **Dispatch:** `S1` (executor **Claude-in-repo**, unattended-fit **🟡 review**) · *plan* = pick a
  verified slice from a folio / production-readiness map and write or refine its plan · *execute·continue*
  = advance the next **▶ startable** Now item (currently Layer B or games P0-1). *(Both are groundedness-/
  money-safety runtime → build carefully; they self-merge on green like any PR.)* **Live queue →** the eight S1 areas in the
  drill-down below; folios: [`subsystems/`](subsystems/README.md).

### S2 — BTD6  ·  *the Bloons TD 6 vertical — runtime + offline data, one standing sector*
- **Now:** **the cutover is DONE.** Post-cutover decode backlog: ⭐ **item 3** (buff/zone tail —
  **⛔ demand-driven**) · **item 4** (the maintainer's live spot-check — **👤 maintainer**, owed). Triage
  tool: `scripts/btd6_probe.py "<exact user text>"`. *Both Now items are blocked, so a "dispatch S2
  execute" falls through to the startable item in Next.*
- **Next:** the **▶ P1-1 BTD6 eval cases** — the #704 finding's **offline half SHIPPED** (the
  grounding-anchor guard `tests/evals/test_btd6_grounding_anchors.py`: every number the golden set
  asserts — Despo price, Elite Lych HP, ABR/round cash — is now pinned to a deterministic
  `btd6_data_service` re-derivation *and* the case rubric, so data-drift or prose-drift fails CI;
  plus a capability/answerability-consistency guard). **What remains is the live `llm_judge` battery**
  (the model actually using the facts — creds-gated, the S1 harness × these BTD6 facts). *The in-bot
  AI eval **harness** is S1; the BTD6 **data/grounding** correctness it checks is S2.*
- **Later:** BTD6 product-extension routing (rules/trivia · challenges · runs · leaderboards) — gated
  on ADR-006 provenance / source-health.
- **Dispatch:** `S2` (executor **Claude-in-repo**, unattended-fit **🟢 auto**) · *plan* = structure a
  decode item or an extension feature into a plan · *execute·continue* = the next **▶ startable** item
  (the BTD6 grounding-eval cases — both Now items are ⛔/👤). *(The eval cases are offline test
  assertions over already-grounded facts → offline-verifiable + self-mergeable.)* **Live queue →** the **S2 BTD6**
  area in the drill-down below; folio: [`subsystems/btd6.md`](subsystems/btd6.md) · provenance:
  [ADR-006](decisions/006-btd6-data-provenance-ownership.md).

### S3 — AI-Memory system  ·  *the mechanism — the self-improving-agent engine (shippable on its own)*
- **Now:** **the rebuild is UN-GATED and in motion (2026-07-07).** Plan of record =
  **[rebuild-canonical-plan-2026-07-06.md](planning/rebuild-canonical-plan-2026-07-06.md)** (#1770;
  supersedes the design-spec / linchpin / handoff framing below). **Q-0241 (#1776)** retired the owner
  go/no-go gate — the coordinator builds in logical order, live-tests in a server, silence=consent. **Gate
  V is COMPLETE (#1767)**; **Phase-2.5 is CLOSED** (#1775 FAIL-as-tested → the adopt-render fix + re-run
  pair, final-review session #1778); **the FINAL plan review ran 2026-07-07** (#1778 — verdict: ready,
  §11 amendments folded; [report](planning/rebuild-final-review-report-2026-07-07.md)). ▶ next per
  canonical §5: **create `superbot-next` (step 6)** → bootstrap kit (7) → control plane (8) → kernel
  S1–S9 → layer V → K10 → port bands; **Projects-EAP as the coordinator**
  ([owner-sendable review](planning/projects-eap-product-review-2026-07-07.md)).
  *(Historical: the 👤 owner-gate framing + the design-spec/linchpin/handoff pointers are superseded by
  the canonical plan §9.)*
- **Now:** **▶ FINALIZE THE MEMORY SUBSTRATE** — owner-queued 2026-07-02 as a **Fable 5 ultracode**
  session; canonical startup prompt =
  **[rebuild handoff §5.B](planning/rebuild-ultracode-handoff-2026-07-02.md)** (extended with the
  context-economy engine per **Q-0214** / the
  [retention plan](planning/memory-retention-and-context-economy-plan-2026-07-02.md) §10 + a verified
  gap/uncertainty addendum). Subsumes the old "resume at the PR-2 remainder → PR 3" framing of the
  **[portable substrate-kit](planning/portable-substrate-kit-extraction-2026-06-13.md)** OSS arc.
  **Owner re-elevated this to top focus 2026-06-30** (fresh-rebuild vision #1589/#1590: "bot is  mostly production ready, focus on the AI-memory project now") — this **supersedes any earlier "demoted
  after fourth band-carry" language** in the cross-horizon snapshot below. The **autonomous-loop
  mechanism** is live (#742/#753–#761; operating layer hardened #863/#865/#868/#869/#870) — its
  *operation* is S5, its *design* is here.
- **Next:** the **bot self-test walker** eval harness (pairs with S1 P1-1) · the **Hermes bug-triage
  flow** mechanism (gated Q-0121). *(Shipped this lane: **`scripts/check_sector_map.py`** + **`dispatch_menu.py`**
  — the sector-partition guards (folio homing / executor / startability) + the live dispatch-menu
  generator, Q-0143.)*
- **Later:** promote the journal's earned candidate rules into CLAUDE.md (Q-0120) · the Context7-adopted
  plugins remainder (Postgres-MCP · pyright-LSP, Q-0096) · substrate-as-product productization (the
  future S5-of-S3 outward face).
- **Dispatch:** `S3` (executor **Claude-in-repo**, unattended-fit **🟢 auto**) · *plan* = design a new
  mechanism (a checker, a hook, a loop seam, a substrate-kit layer) · *execute·continue* = build the next
  substrate-kit / tooling slice. *(Mechanism/tooling slices are offline-verifiable + self-mergeable; a
  CLAUDE.md/executable-config edit is the 🟡 exception — born-red for owner review per Q-0106.)* **Live queue →** the
  **S3** area in the drill-down below; refs:
  [`operations/autonomous-routines.md`](operations/autonomous-routines.md) ·
  [`operations/hook-policy.md`](operations/hook-policy.md) ·
  [the loop vision](ideas/autonomous-improvement-loop-vision-2026-06-12.md).

### S4 — Documentation system  ·  *the content the engine produces — memory, folios, contracts*
- **Now:** sector-roadmap mapping **✅ #877** (+ the dispatch-test follow-up #880) · **▶** the 3-tap nav
  **middle/bottom layers** (folio completeness + cog/idea leaf-wiring — the "larger nav build" the
  sector-map session flagged).
- **Next:** idea-backlog **grooming** cadence (Q-0015 — every idea ends implemented or discussed) ·
  orientation-route upkeep mined from `.sessions/` **context-deltas** · doc-reachability maintenance.
- **Later / recurring:** the **Q-0107 reconciliation** *content* pass (de-stale docs · refactor the
  roadmap · keep the ledger honest) — its trigger/checker **machinery** is S3, the docs it produces are
  S4. Cadence: every 30th PR (Q-0134).
- **Dispatch:** `S4` (executor **Claude-in-repo**, unattended-fit **🟢 auto**) · *plan* = identify a doc
  gap / drift and scope its fix · *execute·continue* = groom the idea backlog, de-stale a doc area, or run
  the docs-reconciliation pass. *(Docs/folio/leaf-wiring work is offline-verifiable + self-mergeable.)* **Live queue →** the
  **S4** area in the drill-down below; refs:
  [`AGENT_ORIENTATION.md`](AGENT_ORIENTATION.md) · [`repo-sector-map.md`](repo-sector-map.md).

### S5 — Operations / control-plane  ·  *the operational health that isn't a file — deploy · secrets · loop*
- **Now:** the read-only **Railway log-triage skill** (**👤 maintainer** one-time Railway token on the
  VPS → then **Hermes-run**; access verified live #840) · **verify the daily backup cron end-to-end**
  (**👤 maintainer / observe** the next scheduled `backup-db.yml` run after the #862 pg18-client fix).
  *S5's Claude-in-repo work is thin — mostly the in-repo control-plane tooling (a `check_*`, a workflow guard).*
- **Next:** **dispatch reliability** (Q-0137 Thread 1 — move the night executor off GitHub's flaky
  `schedule:` cron onto the always-on Hermes VPS **and keep cron as a degraded backstop**;
  owner-undecided) · `ROUTINE_PAT` expiry monitoring · a Neon read-only role for DB-level checks.
- **Later:** Hermes Docker backend + SSH-key hardening · security/authority tracking as Hermes gains
  write scope (Q-0117/Q-0121) · `BUG-0011` Hermes gateway restart crash-loop ([bug book](health/bug-book.md)).
- **Dispatch:** `S5` (executor **Hermes-VPS / maintainer** — the outlier, unattended-fit **🔵 live**;
  only in-repo `check_*` / workflow tooling is Claude-in-repo) · *plan* = design an ops check / a
  control-plane improvement · *execute·continue* = build a read-only ops skill, verify a live
  control-plane row, or harden the loop's reliability. *(The live ops lanes need a maintainer token /
  runtime to verify; the thin in-repo `check_*`/workflow-tooling sub-lane is itself 🟢 auto.)*
  **Live queue →** the **S5** area in the drill-down below; refs:
  [`operations/production-deployment.md`](operations/production-deployment.md) ·
  [`operations/hermes-control-plane.md`](operations/hermes-control-plane.md) ·
  [autonomous-routines § Control-plane state](operations/autonomous-routines.md) · `scripts/check_loop_health.py`.

---

## Cross-horizon snapshot (all sectors)

> The pre-sector view, kept for the cross-cutting band picture. The **active band** is always the
> live decade queue (the `▶` pointer at the top); the per-sector queues above are the standing home.

| Horizon | Items |
|---|---|
| **Now** | The **[band-#930 decade queue](planning/reconciliation-pass-2026-06-15-band930.md)** (ninth Q-0107 pass, issue #931): the **safety/community band ✅ COMPLETE** (#772 automod · #774 logging · #775 welcome+counters) + backup posture ✅ #769/#862 + **native auto-merge migration ✅ #786/#787 (Q-0123)**. **The P0 integrity spine, P1-2, AND P1-1's whole offline eval half are COMPLETE** ([hardening roadmap](planning/production-readiness/hardening-roadmap-2026-06-12.md) — **P0-3 ✅** (#777/#794 + #817, Q-0098); **P0-4 ✅** (#820 + #825, Q-0100); **P0-2 ✅** (media retention #829, Q-0099); **P1-2 ✅** health-findings lifecycle #843, Q-0097; **P1-1 eval matrix ✅** offline half DONE — AI tool-surface coverage **34/34 full** #878→#896 + the self-cleaning drift guard #879; **absence-guard Layer A ✅ #855**). **Active Now = the now-ungated turn-key slices + the gated remainder:** the **games-economy faucet/sink diagnostic** (read-only economy-flow observability — promoted to a plan this pass, its sink-heavy gate cleared by respec #912 + structures #905/#910) · **myprofile PR A** (read-only profile card, plan exists). The band-#900 `ready` queue **shipped**: P1-3 invariants ✅#917/#918 · mining structures lane COMPLETE (Forge #905 · Home #910 · respec/titles #912) · Railway log-triage ✅#906 · BUG-0009 3/4 ✅#924/#926. **In flight:** security service tiers 1+2 (#929, `needs-hermes-review`). **Gated/deferred:** the remaining P1-1 (absence-guard **Layer B** + the live-quality battery — creds/design-for-review) · BUG-0009 slice 3 (newest-towers — data-gated) · image moderation + NL event scheduler (plan-first). **Owner-action (off the plannable queue):** the **[portable substrate-kit](planning/portable-substrate-kit-extraction-2026-06-13.md)** OSS arc — **demoted after its fourth carry** (§6 escalation); returns when the owner re-steers it. The product lanes stay open as owner-steered alternates: **mining** (V-16 phase 2 — gated on the owner's PNG pack) · **BTD6** (decode ⭐ item 3 demand-driven; owner live spot-check owed) · **AI** (§7 workflow families post-prod-check; BUG-0009 open in the [bug book](health/bug-book.md)) |
| **Next** | Safety/community lane remainder (image moderation · security tiers 1+2 · NL event scheduler — all plan-first, see the lane section) · P1-1 versioned AI eval/smoke matrix · myprofile PR A ([plan](planning/myprofile-foundation-plan-2026-06-10.md), turn-key) · help home/navigation plan (editor-UI gate cleared via #677/#679) · V-14 harvest structuring ([dossier](ideas/competitive-teardown-2026-06-10.md); ecosystem-#2 = fishing, owner ratification pending) · the 2026-06-10 [consolidated implementation plan](planning/consolidated-implementation-plan-2026-06-10.md) is **FULLY EXECUTED** (`historical`; [EOD verification](audits/past-day-verification-2026-06-10.md)) |
| **Later** | P1-2 health findings lifecycle (Q-0097 answered 2026-06-12 — operator-managed; ready when queued) · continuation dispatch = the **Routine seam** (Stage 0's GH Action folded in — Q-0115; activates on Routine wired + calibrated) · BTD6 post-cutover decode backlog · server-management **PR13 AI generation layer** + deferred governance setup (gated — Q-0008/Q-0011) · broad AI expansion beyond the active lanes (gated) · media channel-summary (now shaped by Q-0099) · games deferred follow-ups |
| **Someday** | The ideas backlog — not approved (see [§Someday](#someday--ideas-not-approved--capture-only)) |

> **Standing posture (router §35, 2026-06-10):** the end-state is a **public
> bot** (Q-0080 — every new plan inherits stranger-grade onboarding/abuse/cost
> filters) · the flagship RPG is **solo core + co-op overlays** (Q-0081) · AI
> spend = **owner-set hard ceiling, visible graceful degrade** (Q-0082 — **interim
> €30/month set 2026-06-12**; refine after first prod measurements) · the
> workflow converges toward **full self-driving — explicitly not near-term**
> (Q-0083).
>
> **Session queue → superseded 2026-06-12.** The 2026-06-10 recommended queue completed
> items 1 + 6 (untested-surface checklist **#731**/**#732** · the V-16 gear slice **#702**);
> its remainder (Stage 0 · backup posture · help home/navigation · V-14 structuring) and
> the build-ready alternates (myprofile PR A · survival **P0 balance-sim harness, Q-0087** ·
> duel-XP quick-win · **gap items 2/4/5** — [gap file](ideas/gap-analysis-2026-06-11.md))
> are folded into the **[decade queue](planning/reconciliation-pass-2026-06-12.md)** §4 and
> its "deliberately not in this decade" list. One queue home — don't restate it here.

---

## Area drill-down (each area homed to a sector)

> The detailed per-area plans. Each area heading carries its **sector chip** (S1–S5); the live
> per-sector queues are the [dispatch index](#by-sector--the-live-dispatch-queues) above. The eight
> bot areas are **S1**; **BTD6** is **S2**; the former "agent ecosystem" lane is split into **S3 /
> S4 / S5** at the end.

### 🛡️ Server management · **S1 Bot** — structurally complete (gated tail only)

Folio: [server-management](subsystems/server-management.md) · **historical record** (initiative
complete through PR14; the gated PR13 AI tail is in *Later* below):
[status tracker](planning/server-management-status-2026-06-05.md) (re-badged `historical` 2026-06-13)

- **Shipped through PR14** *(routing corrected 2026-06-10 — this page queued the hub
  long after it merged)*: the unified **Server Management Hub** merged **2026-06-08 via
  #584** ([plan](planning/server-management-pr14-hub-plan.md), executed/`historical`);
  PR10 moderation config (all six slices), PR11 moderation + roles setup sections,
  PR12 setup diagnostics & repair, and PR13's **deterministic** role-templates slice
  all shipped before it.
- **Later (gated)** — the **PR13 AI generation layer** ("Generate with AI" role
  templates; AI per-exposure gate) → the deferred **governance** setup section
  (capability overrides + command-access — owner decisions Q-0008/Q-0011).
- Plans (context, not sequence): [roadmap](planning/server-management-roadmap-2026-06-05.md)
  (target architecture) · [implementation-plan](planning/server-management-implementation-plan-2026-06-05.md)
  (PR scope; shipped through PR14 — the tracker is authoritative).

### 🚨 Server safety & community platform · **S1 Bot** — first band shipped; remainder Next

**New lane (2026-06-12):** the owner uploaded competitor/safety research (#739 →
[server-safety-and-automod](ideas/server-safety-and-automod-2026-06-12.md) ·
[community-platform-features](ideas/community-platform-features-2026-06-12.md)) and answered
the five scope questions same day (**Q-0108–Q-0112**, #740 — decisions recorded in the
router + both idea docs' routing tables). The lane's entry doc is the
**[safety/community family plan](planning/safety-community-family-plan-2026-06-13.md)**
(2026-06-13, band slot 4 — shared architecture + sliced build order, citing
`ux/pattern-library.md` pattern_ids; **automod v1 shipped in the same PR**). UI/attachment
numbers: [discord-platform-limits](operations/discord-platform-limits.md).

- **Shipped (band slots 4–6, 2026-06-13) ✅** — the family plan (slot 4) +
  **automod v1** (#772, Q-0108 — all four rule types through `moderation_service`) →
  **server event logging v1** (#774, Q-0109 — edits/deletes · join/leave · role changes,
  **extending the existing `services/server_logging.py` seam**) → **welcome v1 + server
  counters** (#775, Q-0110 — greetings/farewell/entry-role + statdock channels; two
  hub-less new subsystems, embed-first). The first band is COMPLETE.
- **Next (after the hardening spine)** — **image moderation** (Q-0108 — OpenAI
  `omni-moderation-latest` only; paid tiers declined) · **security service tiers 1+2**
  (Q-0111 — raid detection + account-age filter; tiers 3+4 **declined**, GDPR) · **welcome
  phase 2** (PIL image cards — the `render_welcome_card` prototype already exists, so this
  is a small follow-up on the stable embed-first v1) · the **NL event scheduler** (Q-0112,
  own AI-cost design under the Q-0082 ceiling). A read-only **operator landing** for the
  whole lane is captured as an idea ([safety-community-operator-landing](ideas/safety-community-operator-landing-2026-06-13.md)).
- **Later (plan-first, AI cost design)** — **NL event scheduler** (Q-0112 — NL time parsing
  from day one, metered under the Q-0082 ceiling; availability polls proposed day-one;
  check existing scheduler infra before designing reminders).
- **Later** — social feed notifications, YouTube-first (Q-0041 direction approved; the
  summarization enrichment layer rides the Q-0082 ceiling). Other sources + custom
  commands: Someday (see below).
- **Later (owner-directed, plan-first)** — **Karma (thanks/upvote reputation)**: members grant each
  other peer reputation; per-user totals + a leaderboard provider, on an audited mutation seam
  modelled on economy/XP. Buildable 2–3-PR spec in
  [karma-reputation-plan](planning/karma-reputation-plan-2026-06-22.md); gate: the owner's answers to
  the 5 design questions (grant surface · downvotes · pure-rep vs. economy bridge · karma-roles ·
  defaults). Idea: [karma-reputation-system](ideas/karma-reputation-system-2026-06-22.md).

### ⚙️ Settings / bindings / provisioning · **S1 Bot** — Next

Folio: [settings-bindings-provisioning](subsystems/settings-bindings-provisioning.md)

- **Next** — **setup `/myprofile` foundation (wizard plan PR4)** — **plan ready
  2026-06-10:** [myprofile-foundation-plan](planning/myprofile-foundation-plan-2026-06-10.md)
  (PR A read-only card, zero writes · PR B the participation pipeline's first
  UI consumer · PR C onboarding **gated** on an owner decision; Q-0080
  stranger-grade envelope applied). The finalization tranche (PR1–PR3) was
  verified already shipped via #435 (DT09, PR #672).
- **Next** — settings coverage: pick a *verified* inconsistency from the
  [consistency ledger](health/platform-consistency-ledger.md); the three-lane model is
  [settings-customization-roadmap](setup-platform/settings-customization-roadmap.md).
- **Shipped 2026-06-09 (#640, scoreboard Lane 7)** — **settings audit Phases 0+1**:
  actionable-groups-only hub (`actionable_settings_groups()`, 11 live groups) +
  paginated >25-option reachability + per-guild routing availability markers.
  Sequencing home: [settings audit §11](planning/settings-cog-centralization-audit-2026-06-09.md).
- **Phase 2 core merged 2026-06-10 (#654**, consolidated-plan Batch 4):
  real domain-panel registrations (`DomainPanelSpec`) replaced the Phase 1
  `DOMAIN_CONFIG_SUBSYSTEMS` seam (+ DT06 coverage invariant); **Q-0064** BTD6
  announcement-channel binding + CT guided flow landed with it. Open tail:
  pointer-migration classification rows; then **Phase 3** duplicate-path
  convergence (**Q-0063** converge-gradually — router §27).
- **Phase 1 complete** — [Adaptive Setup, Access, Profile, and Routine Platform](planning/adaptive-setup-access-routine-platform-2026-06-08.md):
  P0 + P1A + P1B + P1C shipped (#588/#589/#591/#592/#632 + the 2026-06-10
  Batch 5 subpanels, **merged #656**; Q-0032 hub-buttons-only honored). **P2 next** (own planning first). *(Horizon corrected
  2026-06-10: this row said "Later" while the at-a-glance table said P1C "Next".)*
- **Later** — [setup-platform roadmap](setup-platform/roadmap_setup_platform.md) is the *aspirational*
  8-phase vision; the shipped wizard is a pragmatic subset. Direction, not queue.

### 🖥️ Building / interface (Discord-native UI) · **S1 Bot** — Next

- **Complete (2026-06-10)** — the **platform-surface mapping campaign**: the
  [mapping standard](planning/platform-surface-mapping-standard-2026-06-09.md) (#641),
  Agent A's [user-surface map](planning/platform-mapping-a-user-surface.md) (#643),
  Agent B's [admin-surface map](planning/platform-mapping-b-admin-surface.md) (#644),
  and the two follow-on **untapped maps** —
  [runtime/services/workflows](planning/untapped-runtime-services-workflows-map-2026-06-10.md)
  (#646) · [docs/tests/verification](planning/untapped-docs-tests-verification-map-2026-06-10.md)
  (#647) — all merged; findings verified + reconciled 2026-06-10.
- **Next** — **implement the verified mapping batches**: the one active queue is the
  [consolidated implementation plan](planning/consolidated-implementation-plan-2026-06-10.md)
  — **Batches 1–8 all executed + merged 2026-06-10**; **#671** added RS07 +
  Batch 9's RS08 + the Help-Preview Tier-2 fix, and **#672** completed the
  Batch 4 pointer tail (proof-channel declaration) + the Batch 10 selections;
  Batch 9 completed in **#681** (RS05 publish-accepted contract + observability ·
  RS10 economy family onto BaseView) and the Help overlay editor UI executed
  same day (PR A #677 + PR B #679) — **the plan is fully executed** (re-badged
  `historical`); remaining work is plan-first/gated, routed from
  `docs/current-state.md` ▶.
- **Next** — **interface completion**: the live sequence is
  [mother-hub-map](building-roadmap/mother-hub-map.md) (S1–S13).
  [interface-completion-roadmap](building-roadmap/interface-completion-roadmap.md) is the
  arc; [loose-ends-audit](planning/loose-ends-audit-roadmap.md) is the source audit (its L1–L6
  sequence is superseded by mother-hub).
- **Later (planning target — Q-0078)** — the **4-button Help Home + panel
  navigation doctrine** from the owner's vision statement
  ([superbot-vision](ideas/superbot-vision-2026-06-10.md) V-02/V-03 + AG-01/AG-03):
  Play · Server & Info · My Stuff · Manage top level (layout decided Q-0078),
  update-in-place + mother/help links on every panel, one-active-panel + summon,
  and the ≤3-clicks reachability invariant (navigation depth — per-panel
  button caps rejected, Q-0079). Owner-picked as a next planning
  target; its sequencing gate — the Help overlay editor UI — **cleared 2026-06-10**
  (the editor shipped as **#677 + #679**), so it is ready to structure into its own
  plan on the same projection seam (capture-doc T-4) before building.
- **SHIPPED (2026-06-12, owner-steered same-day build)** — the **UX Lab
  interface-gallery cog** (`!uxlab`, admin-gated, zero-write): PRs **#758/#760/#762**
  — 64 registered patterns across 7 wings + a 10-probe limit bench + clickable
  **mockups of the whole Q-0108–Q-0112 lane** (review those features by clicking
  before the family plan is written) + ⚖️ compare-with-verdicts. The durable design
  vocabulary is **[ux/pattern-library.md](ux/pattern-library.md)** (registry-generated,
  doc-pinned) — future panel plans reference its `pattern_id`s instead of re-describing
  layouts. CV2 adoption for real panels stays a future ADR on the lab's evidence
  ([plan](planning/ux-lab-interface-gallery-plan-2026-06-12.md), now `historical`).
- **Later** — [command-expansion-backlog](building-roadmap/command-expansion-backlog.md)
  and [admin-powers config-coverage](building-roadmap/admin-powers-config-coverage.md):
  backlogs — cross-check source before pulling one.
- Standards (read when building, not roadmap items):
  [command-integration](building-roadmap/command-integration-standard.md) ·
  [hub-ui](building-roadmap/hub-ui-standard.md) ·
  [config-input](building-roadmap/config-input-standard.md).

### 🩺 Health / diagnostics · **S1 Bot** — Now (verification owed)

Folio: [health-diagnostics](subsystems/health-diagnostics.md)

- **Now** — all bot-awareness phases (PR1–6) shipped; what's owed is **maintainer
  production live-tests**: owner receives `diagnostics_health_snapshot` (a non-owner does
  not), plus grouped-findings / recurrence rendering. The sandbox can't do this (no AI key).
- **Maintenance** — no unshipped phase pending; a new write-capable diagnostics flow needs
  a fresh approved plan. Execution authority:
  [bot-awareness-implementation-plan](health/bot-awareness-implementation-plan.md).

### 🤖 AI (in-bot slice) · **S1 Bot** — Now (active lane; per-exposure gate lifts)

Folio: [ai](subsystems/ai.md) · **Gate (re-postured 2026-06-09, Q-0048):** **read-only,
deterministic tools carry a standing lift** (no per-case ask; audience-tiered, no writes /
external calls); anything that **writes, costs money, calls external services, or adds UI**
still needs a per-exposure lift (precedents: `btd6_round_cash` #612, `ai:tools` UI #619).
Broad expansion stays gated on *all* of bot-wide stability + provider/provenance +
caching/source-health + behavior-config correctness (`docs/current-state.md`), **plus a
dedicated decision** for any action capability.

> **AI sequencing lives in the dedicated AI roadmap:**
> [`planning/ai-roadmap-2026-06-07.md`](planning/ai-roadmap-2026-06-07.md) (Phase 0–11,
> source-verified, planning-only) — the **AI-area authority**; the plans below are the
> inputs it consolidates. **First Opus AI target (AR-10, 2026-06-07): lock the orchestration
> foundation** before any net-new tools; audience posture is **tiered** (AR-08) and AI stays
> **explanation-only** (AR-09). Decisions: [`owner/maintainer-question-router.md`](owner/maintainer-question-router.md) §18.

- **Now (active lane)** — the **orchestration foundation**
  ([ai-complex-request-tool-orchestration-plan](ai/ai-complex-request-tool-orchestration-plan.md))
  **Phases 1–4 MVP shipped** (#612 catalogue+selector, #618 tool-choice+budgets, #619 typed
  policy + the gate-lifted `ai:tools` operator UI, **#634 the Phase 4 MVP slice** — the
  round-cash plan→execute→verify workflow + the first typed answer-with-evidence contract,
  profile-gated, default byte-identical; model loop awaits the maintainer's prod check).
  **Next:** the remaining §7 workflow families + the §12.1 durable audit trace follow the
  proven template.
- **Now (active lane)** — [AI Cog Completion + BTD6 Answerability](planning/ai-btd6-answerability-roadmap-2026-06-09.md):
  **Phase 1A/1B shipped** (#612 — `btd6_round_cash`, gate lifted per-tool), **Phase 2
  shipped** (#616 — the read-only introspection read model), and **Phase 3 shipped**
  (**#639**, 2026-06-09, Q-0047 — execution-plan Lane 4): all three read-only
  self-awareness tools in one slice (`get_ai_tool_catalog` · `get_ai_policy_explanation` ·
  `btd6_answerability`), audience-tiered at construction; model loop awaits the
  maintainer's prod check. **Next:** Phase 4 (AI settings UI) and Phase 5 (generated
  answerability dashboard) stay gated — Phase 4 behind the settings foundation, both
  behind their per-exposure asks.
- **Later** — [ai-tool-capability-roadmap](ai/ai-tool-capability-roadmap.md) sequences the
  backlog onto that foundation · [ai-readiness-plan](ai/ai-readiness-plan.md) M2 (typed policy
  tables + central NL stage) · [provider-switch + grounding fix](ai/ai-provider-and-grounding-fix-plan.md).
  Map: [ai-service-integration-map](ai/ai-service-integration-map.md).
- **Later (UX debt — owner-requested)** — [AI panel in-place navigation](ideas/ai-panel-inplace-navigation-2026-06-11.md):
  migrate the `views/ai/` settings family off per-click ephemeral messages + the blanket
  raw-`discord.ui.View` yaml exemption onto the rest-of-bot in-place **HubView** pattern
  (V-02 navigation doctrine), and centralize the seven scattered subpanels. Clear
  direction + a source-confirmed scope sketch in the idea file. **Now an executable plan**
  ([ai-panel-inplace-navigation-plan-2026-06-19](planning/ai-panel-inplace-navigation-plan-2026-06-19.md),
  2–3 PRs) — also the blocker for graduating the consistency linter's `edit_in_place` rule (its 17
  remaining findings are this family); each PR is substantial runtime + wants a live guild walk.

### 🎈 BTD6 data / tools · **S2 BTD6** — Now (THE CUTOVER IS DONE — post-cutover decode backlog)

Folio: [btd6](subsystems/btd6.md) · index: [docs/btd6/](btd6/README.md) · ADR-006
provenance schema is implemented.

- **Shipped (2026-06-10 — PR #649, merged, the Q-0066 dedicated cutover
  session)** — **every committed stats file is game-native v55.1**: 25 towers +
  17 heroes + 13 paragons via `parse_gamedata.py --all` through the new cutover
  merge layer (curated names preserved + set-level name guard); Q-0067
  (Farm/Village full tiers + decoded income auras) and Q-0068 (per-tier beast
  names) executed in the same pass; source labels now read "BTD6 game data".
- **Post-cutover verification + carry-forward decode pass (2026-06-10 — PR
  #655)** — dump fidelity re-proven (byte-identical regeneration, rounds
  parity 140/140), all 2,022 menu embeds + the AI tool battery green; fixed:
  mode-rules dark data (now on both surfaces), the `!btd6 diagnostics` 400,
  the version-stamp-rot class (everything reports 55.1), the container-path
  leak. Then **every #649 carry-forward decoded** (`_CUTOVER_CARRYFORWARD`
  empty; audit **91 CLEAN / 0 DELTA / 0 SUSPECT**) — druid + paragon thorn
  rings, engineer typed-sentry rosters, sub Energizer/paragon support, bucc
  sellback + Flagship dedup, striker auras (+ dump fills committed holes),
  Magus phoenix.
  In parallel, **#653 (wave 1)** decoded thorn rings + 4-x-x sentries + the
  **banana economy** (bananaValue/bank capacity+interest as specials) —
  reconciled at the merge.
- **Answerability tail (2026-06-10)** — items 5+6d in **#658** (deterministic
  Ask parity · Pro views render Effects/Minions · Striker fraction fix);
  items **6a–c + the Navarch "no coins" routing fix in #662** (the live wrong
  answer was **routing, not data**: name-resolution miss → 0 facts, the
  cap-truncated income sentence, no paragon income/effect grounding leg —
  fixed across grounding/menus/AI tool, + minion-name grounding, the Pouākai
  diacritic tokenizer fix, honest dataset source labels).
  **Item 7 slice 1 shipped same day (#668)** — zero-fact questions now ground
  the conversation's entity via labeled `[btd6_carryover]` facts, + the
  zero-fact sweep fixes (ranking rosters · bare distinctive shorthand); the
  [conversation-carryover grounding plan](planning/btd6-conversation-grounding-plan-2026-06-10.md)
  carries the remaining unapproved tail (eval-harness pin · wider window).
  **Next:** decode-status ⭐ item 3 (buff/zone tail — demand-driven), the
  maintainer's live spot-check (item 4). Triage tool (#666):
  `scripts/btd6_probe.py "<exact user text>"`.
- **Earlier (#638, merged 2026-06-10)** — ABR rounds + income sets ingested
  game-natively (roundset-aware `btd6_round_composition`/`btd6_round_cash`);
  subtower mechanisms 7/7; buffs 15/38 confirmed.
- **Built (Q-0049 — #633, merged 2026-06-09)** — the
  "fetch-everything-on-update" data refresh is a committed **manual-dispatch GitHub
  Actions workflow** (`workflow_dispatch` only, no schedule): one-click refresh after a
  game update, no unattended fetches, output is a reviewable PR (never a push to main).
  Remaining: the first real dispatch from the Actions tab. Plan + how-to-run:
  [data-refresh-pipeline](btd6/btd6-data-refresh-pipeline-plan.md).

### 🎮 Games · **S1 Bot** — Now (mining character platform active lane)

Folio: [games](subsystems/games.md) · **Boundary:** ADR-002 (game state not restart-safe —
accepted, not a target).

- **✅ P0-1 wager money-safety — SHIPPED #748 (2026-06-12, owner-picked).** The audited
  `services/game_wager_workflow.py` (escrow-at-accept, idempotent settle/payout, all four RPS +
  blackjack PvP/tournament call-sites migrated, AST fence + failure-injection tests) — plan is
  `historical`: [games-wager-money-safety-plan](planning/games-wager-money-safety-plan-2026-06-12.md).
  *(Money-safety lineage continued in the settle-once guards #1444/#1445/#1454.)*
- **Now (active lane)** — the **mining character platform** (from the
  [mining brainstorm](ideas/mining_exploration_brainstorm.md) §7 vision). Wave-1 chain
  shipped #606–#610 + #624 (explore wiring + equipment seam, persistent Descent, combat
  gear → deathmatch, market loop, Character overview, Workshop + durability keystone).
  **The 2026-06-10 finalization session executed Batch 7 + the Wave-2 seed as a 4-PR
  stack — all merged, landed on `main` via #667: #661 → #663 → #664 → #665** — the Q-0071/Q-0072 write
  boundary is **complete** (every mining write through `services/mining_workflow.py`,
  one transaction per op, AST-fenced; pure domain in `utils/mining/`), recipes are
  catalog-reconciled under an alignment lint (Q-0075), the **shared game-XP track**
  exists (migrations 065/066: awards atomic with their actions, daily soft cap, shared
  derived level, `gamexp`/`crafting` leaderboards, depth records), the **deeper
  ladders** land (gold/diamond tiers — the diamond lantern finally unlocks MAGMA),
  the Gear panel / Recipe browser / fuzzy names / `!fastmine` modernize the old UX,
  **duels tick weapon/armor wear (Q-0054 closed)**, and the §7.6 PIL inventory +
  stat cards ship (Q-0076). **§7.5 structures started: the Vault (safe stash)
  shipped 2026-06-14 (#884)** — `mining_vault` + audited deposit/withdraw + a
  `🏦 Vault` panel (v1 has no cap yet). **The rest of §7.5 + the §7.4 skill tree are
  now turn-key + ▶ startable** in [`planning/mining-structures-skill-tree-plan-2026-06-14.md`](planning/mining-structures-skill-tree-plan-2026-06-14.md)
  (recommended marquee = the **capped skill tree** — its `game_xp` substrate +
  `EffectiveStats` merge point are in place; plus the Vault inventory-cap sink, Forge,
  Home). **⛔ V-16 phase 2** paper-doll sprites stay owner-blocked on the PNG pack.
- **Now (owner-directed UX, 2026-06-15)** — **mining hub redesign**: the 16-button hub splits
  into dedicated sub-hubs (Option A — main = Mine·Harvest·Explore·Character·Gear·Workshop), the
  inventory/gear image cards render in place (PR #911), and Mine becomes a 3D grid navigator;
  Explore becomes an open-world hub. Plan + IA:
  [`planning/mining-hub-redesign-2026-06-15.md`](planning/mining-hub-redesign-2026-06-15.md). The
  **fishing + open-world expansion** (21 fish / 7 levels · unified gear-type switching · the boat & real
  destinations) is the next big games lane —
  [`planning/fishing-open-world-expansion-plan-2026-06-18.md`](planning/fishing-open-world-expansion-plan-2026-06-18.md)
  (Q-0175; **Phase 1 = fishing v1 + gear-switching is buildable**; the canonical Q-0172 self-build).
- **Later** — bounded deferred actionability follow-ups (inventory architecture,
  leaderboards, bot-duel stats, shared back-button adoption) from the completed
  [actionability roadmap](archive/games-actionability-roadmap.md). Low priority; pick one bounded
  slice.
- **Later** — [**Pet companions**](planning/pets-companions-plan-2026-06-09.md): nameable
  pets from exploration drops + a care-loop coin/ore sink + tiny non-P2W perks; the
  owner's ⭐ pick from the 2026-06-09 fun/ease brainstorm (Q-0053). Gate: Wave-1
  keystone slices (Workshop + durability) + balance review + owner promotion.
  **Amended 2026-06-10 (Q-0078 "both paths"):** quest-rescue joins as the
  rare-species path once the quest engine exists; party cap grows 1→3 later.
- **Later** — [**RPG survival & difficulty design**](planning/rpg-survival-difficulty-design-2026-06-10.md):
  difficulty modes (Easy ≡ today's game, byte-identical) + energy/health/hunger +
  fishing/cooking + biome×difficulty encounters + hard-mode death-as-rescue; from the
  owner's vision statement ([superbot-vision](ideas/superbot-vision-2026-06-10.md)
  V-05…V-08), picked as a planning target in **Q-0078** (one-way-ascent switching
  decided there). Gates: sequencing behind §7.5 structures / §7.4 skill tree + the
  owner numbers-confirm (plan G1/G2). Its D6 (duel XP both sides) is a standalone
  quick-win.

### 📺 Media / YouTube · **S1 Bot** — Later (needs an approved plan)

Folio: [media-youtube](subsystems/media-youtube.md) · **Gate:** ADR-007 + a
privacy/provenance/moderation review before any public surface.

- **Later** — a channel-summary / content-status feature would need a bounded read-only
  first slice and an explicit privacy/security review. No public media command ships today.
- **Done (hardening P0-2, #829)** — retention/data-minimization per **Q-0099** (bounded
  projection at the cache write + the scheduled `MediaMaintenanceCog` purge + thumbnail-URL
  validation) shipped. **Follow-ups** (content-free media diagnostics · provider-execution
  hardening · maintainer live-verify) are queued behind P1-1 in the
  [band-#840 decade queue](planning/reconciliation-pass-2026-06-14-band840.md) §3.

> **The former "Agent ecosystem / workflow" lane is split here into its three sectors** — **S3**
> (the mechanism/engine), **S4** (the docs content it produces), **S5** (the live operations). The
> workflow substrate is first-class work (CLAUDE.md working agreement); these three sections map its
> *plans* so they're sequenced like any other area.

### 🧠 AI-Memory system (mechanism) · **S3** — standing lane

The self-improving-agent **engine** — the shippable substrate (hooks · autonomous loop · checkers ·
context-compiler · governance scaffolding). Content-agnostic and liftable; the
`portable-substrate-kit` is S3 extracted. Mechanism shelf:
[hooks & plugins](operations/claude-code-hooks-and-plugins.md) ·
[MCP servers](operations/mcp-servers.md) ·
[hook policy](operations/hook-policy.md) ·
[autonomous routines](operations/autonomous-routines.md).

- **Now (owner-steered OSS arc — #813)** — the
  [portable substrate-kit extraction](planning/portable-substrate-kit-extraction-2026-06-13.md):
  externalize the workflow substrate into a single-file, stdlib-only kit (`substrate-kit/`) that
  bootstraps the loop in any project. **PRs 1a/1b + the 1b tail are DONE** (#789 · #791–#793 · #802 —
  skeleton, interview engine, templates, render, the `check_docs`/`check_session_log` ports + a
  `check` CLI); **PR 2's capability layer §3b/§3c is COMPLETE** — **stances (#805) + skills (#811) +
  personas (#812)** — and the **PreToolUse stance-guard hook (#813)** makes stances *enforced*.
  **Next = the PR-2 remainder** (the three modes' per-session behaviors + contract-doc templates +
  trigger/drift detection + the remaining engine hooks), then PR 3 (self-maintenance loop + review
  seam + productization). **— third carry; escalate if a fourth.**
- **Live (mechanism is built)** — the
  [autonomous self-improvement loop](ideas/autonomous-improvement-loop-vision-2026-06-12.md)'s
  repo-side seams (#742, Q-0113/Q-0114): the Hermes `superbot-review` skill (independent non-Claude
  critique) · `scripts/check_phase_gate.py` (fix-phase vs. invent-phase; invent requires zero OPEN
  bugs + zero Not-Done readiness rows — currently **FIX-PHASE**) · the
  [Hermes → Claude dispatch bridge](ideas/hermes-claude-dispatch-bridge-2026-06-12.md)
  (`superbot-dispatch`) + the **#753–#761 wiring arc** (issue-triggered reconciliation · routine
  prompts as loop turns · the Q-0117 review-merge gate · `/bugreport` dispatch). *The loop's live
  **operation** — firing, cron lag, reliability — is **S5**.*
- **Next (structure-or-defer, 2026-06-13)** — [bot self-test walker](ideas/bot-self-test-walker-2026-06-10.md):
  the owner-gated in-process command walker + AI eval mode; clear direction, wants its own plan (pairs
  with the **S1 P1-1 AI eval matrix** — the walker harness is S3, the bot behaviour it checks is S1).
- **Next (gated Q-0121)** — [Hermes bug-triage flow](ideas/hermes-bug-triage-flow-2026-06-13.md): route
  `/bugreport` through Hermes (triage → curated `bug` issue → nightly executor batch-fix), replacing the
  cap-hungry direct instant-fire. The dispatch *mechanism* is S3; build waits on the Q-0121 write
  decision (the live Hermes *operation* is S5).
- **Next (tooling)** — **`scripts/check_sector_map.py`**: assert every top-level `disbot/` area and
  every `docs/subsystems/` folio is reachable from **exactly one** sector — turns the "≤3 taps" promise
  + this roadmap's sector-homing into a checkable completeness invariant (no orphan, no double-home).
- **Open mechanism decisions** — **Q-0096 remainder** (Context7 adopted #737; Postgres-MCP +
  pyright-LSP still open — [plugins eval](ideas/claude-code-plugins-evaluation-2026-06-12.md)) ·
  **Q-0120** (promote the journal's earned candidate rules into CLAUDE.md).
- **Someday (vision, not approved)** — the
  [portable agent-memory package](ideas/portable-agent-memory-package-2026-06-12.md)
  (owner-shaped strategic direction; the outward S5-of-S3 face once the kit is real).

### 📚 Documentation system (content) · **S4** — standing lane

SuperBot's knowledge corpus — what S3 produces and consumes (current-state · journal · sessions ·
ideas · folios · binding contracts · this roadmap). Entry:
[`AGENT_ORIENTATION.md`](AGENT_ORIENTATION.md) · [`repo-sector-map.md`](repo-sector-map.md). *This
sector was under-planned; populated here so it has a live queue (the Q-0137 deep-clean terminal
condition — every sector non-empty).*

- **Now** — **this sector-roadmap mapping** (organising the roadmap + plans under S1–S5, making each
  sector a dispatch target) · the **3-tap nav middle/bottom layers** (folio completeness + cog/idea
  leaf-wiring — the "larger nav build" the sector-map session flagged as next).
- **Standing (recurring)** — the **Q-0107 reconciliation** *content* pass (docs-only — de-stale docs,
  fix the ledger, refactor the roadmap) each time merged PRs cross a **multiple of 30** (Q-0134; the
  trigger/checker **machinery is S3**, the docs it writes are S4) · the session enders (Q-0089 idea ·
  Q-0102 prev-session review · Q-0104 closing audit).
- **Next** — the **procedures→skills conversion**
  ([`procedures-to-skills-conversion-plan-2026-06-17.md`](planning/procedures-to-skills-conversion-plan-2026-06-17.md);
  Q-0170/Q-0172 — relocate ~25% of always-loaded `CLAUDE.md` into on-demand skills; **batch 1 shipped
  #1029**, batches 2–4 next, incorporating the PR-#1028 Codex review notes) · the **thin architecture
  atlas** (PR 2 of
  [`extension-taxonomy-crosswalk-plan-2026-06-16.md`](planning/extension-taxonomy-crosswalk-plan-2026-06-16.md);
  Q-0151a — a companion to orientation, composing `context_map`/`wiring_map`/`review_scope` + the role
  data into one repo-wide CI-`--check` index) · idea-backlog **grooming** (Q-0015 — every idea ends
  implemented or discussed) · orientation-route upkeep mined from `.sessions/` **context-deltas** ·
  doc-reachability maintenance (`check_docs --strict`).
- **Shipped** — the **extension-type taxonomy crosswalk** (Q-0151c, PR #958): the curated role overlay
  `architecture_rules/extension_roles.yaml` + `scripts/extension_crosswalk.py` →
  [`extension-taxonomy-crosswalk.md`](architecture/extension-taxonomy-crosswalk.md), CI-enforced — the 43↔33
  extension/subsystem map, 10 non-1:1 classified.

### 🛠️ Operations / control-plane · **S5** — standing lane

The operational health that **isn't a file**: is the loop firing? is the backup working? are the
secrets set? is Hermes up? **Every recent silent failure lived here.** Entry:
[Hermes control plane](operations/hermes-control-plane.md) +
[operating prompt](operations/hermes-operating-prompt.md) ·
[production deployment](operations/production-deployment.md) ·
[autonomous routines + control-plane state ledger](operations/autonomous-routines.md). *The "forgotten
sector" (Q-0137); under-planned before — populated here.*

- **Now (governance/supply-chain baseline, Q-0177)** — the
  [repo-structure improvement plan](planning/repo-structure-improvement-plan-2026-06-19.md) shipped the
  outward-facing layer the repo lacked: `LICENSE` (MIT) · `SECURITY.md` · `CONTRIBUTING.md` ·
  `CITATION.cff` · `.github/dependabot.yml` · CodeQL · a **dashboard-CI** job (the dashboard tests were
  silently `importorskip`-skipped) · issue/PR templates. **Routed next:** dependency-lock strategy ·
  control-API hardening (HMAC/idempotency/rotation) · making CodeQL/dashboard-CI required + enabling
  Dependabot alerts (owner repo-Settings steps).
- **Now** — the read-only **Railway log-triage skill** (Railway access verified live #840 — the
  reserved decade-queue slot; look-but-don't-touch ops graduation) · **verify the daily backup cron
  end-to-end** (the next scheduled `backup-db.yml` run confirms the cron path after the #862
  pg18-client fix).
- **Now (reliability posture)** — the **live loop runs** (issue-triggered reconciliation ·
  executor-nightly cron · `/bugreport` dispatch, #753–#761) but on GitHub's best-effort `schedule:` —
  measured **hours late**; **Q-0105 calibration** holds (verify each run against ground truth before
  trusting it unattended).
- **Next — dispatch reliability (Q-0137 Thread 1, owner-undecided)** — move the night executor off
  GitHub cron onto the always-on **Hermes VPS**, keeping `schedule:` as a **degraded backstop** (an
  outage means "late," not "stopped"). This supersedes the framing of continuation dispatch as the
  Routine seam (Q-0115); the bounded-session protocol ([§10](owner/ai-project-workflow.md), Q-0088)
  activates once dispatch is **wired + calibrated**.
- **Quick-win** — [backup-dump integrity check](ideas/backup-integrity-check-2026-06-13.md): a
  `CREATE TABLE`-count gate in `backup-db.yml` so a silent empty dump never uploads as a "backup".
- **Next — usage-limit-aware routines**
  ([plan](planning/usage-limit-aware-routines-plan-2026-07-08.md), structured 2026-07-08 from the
  2026-07-07 idea): every routine prompt + orchestration treats the account usage-limit error as
  its own failure class — `limit-deferred` + `send_later` re-arm at the stated reset, limit-killed
  lanes never counted as evidence — plus a stdlib deferral counter for the Q-0248/Q-0249 spend
  dataset. 2 PRs, ungated.
- **Next — per-repo settings state ledger**
  ([plan](planning/per-repo-settings-state-ledger-2026-07-08.md), owner-raised 2026-07-08): a
  durable, ideally auto-generated per-repo settings ledger (rulesets · merge gate · token map ·
  auto-mode capability facts) sessions read at orientation instead of guessing repo state. Phase 1
  (capture doc) shippable now.
- **Later** — `ROUTINE_PAT` expiry monitoring · a Neon read-only role for DB-level checks · Hermes
  Docker backend + SSH-key hardening · security/authority tracking as Hermes gains write scope
  (Q-0117/Q-0121) · **BUG-0011** Hermes gateway restart crash-loop ([bug book](health/bug-book.md)).

---

## Product-growth roadmap drafts — **Later / Someday** (not approved)

> **Sector:** these are all **S1 Bot product** (BTD6 product-extension → **S2**) — captured drafts on
> the *Later/Someday* horizon, not active dispatch targets. They feed S1/S2's *Later* once a gate clears.

- **Later** — [social/community/progression](planning/social-community-progression-roadmap-2026-06-08.md): guilds, achievements, profiles, leaderboards, and notifications; gate: privacy/new-owner decision (Q-0038 answered 2026-06-09: server-scoped clans).
- **Later** — [economy/marketplace/rewards](planning/economy-marketplace-rewards-roadmap-2026-06-08.md): trade, rewards, sinks, onboarding, and crafting; gate: economy-health review + chance-reward review (Q-0039 answered 2026-06-09: donation = cosmetic-only, no bot-side billing) — the fairness boundary now sits under the **Q-0190 "free for everyone" North Star**.
- **Later** — [games/mining/idle growth](planning/games-mining-idle-roadmap-2026-06-08.md): poker, blackjack follow-ups, mining depth/co-op/idle; gate: ADR-002 + balance/ownership review.
- **Later (needs source verification)** — **mining UX polish** (from [voice-mode capture](ideas/voice-mode-planning-capture-2026-06-11.md) §4): crafting category filters + craft-and-equip shortcut + inventory/gear display consistency. Identified as the strongest near-term candidates from the 2026-06-11 brainstorm; gate: source verification of existing crafting/equipment flow ownership before planning.
- **Later (fully gated)** — [AI product-extension routing](ai/ai-product-extension-routing-2026-06-08.md): DM/events/NL/tool ideas routed under the authoritative AI roadmap; gate: all AI readiness/orchestration/action decisions (Q-0040 answered 2026-06-09: bounded-menu DM posture; building still needs its plan + per-exposure lift).
- **Later (gated)** — [BTD6 product-extension routing](btd6/btd6-product-extension-routing-2026-06-08.md): rules/trivia, challenges, runs, leaderboards; gate: ADR-006/provenance/source-health.
- **Existing plans** — [server-management/setup/access/routine extension routing](planning/server-management-extension-routing-2026-06-08.md): announcements, anti-spam, availability, explanations, analytics; gate: authoritative trackers and privacy/AI decisions.
- **Someday / Later** — [integrations/media/voice/website](planning/integrations-media-voice-website-roadmap-2026-06-08.md): provider alerts, activity, voice, and web projection; gate: privacy/security/moderation review (Q-0041/Q-0042 answered 2026-06-09: YouTube-first posture; staged Someday website).
- **Later** — [UX/discoverability/mobile-first](planning/ux-discoverability-mobile-roadmap-2026-06-08.md): help, changelog, copy, and mobile conformance through existing UI standards; gate: authoritative interface sequencing and copy/release-manifest decisions.
- **Next (editor UI only)** — [Help cog customization audit and roadmap](planning/help-cog-customization-audit-2026-06-09.md): the **seam (#657) and the HLP-3 overlay store/mutation/render integration (#659) both merged 2026-06-10** (audit Phases 1+2+3); the **editor UI executed 2026-06-10** ([plan](planning/help-overlay-editor-ui-plan-2026-06-10.md) → **PR A #677** editor · **PR B #679** Q-0059 Home builder, mandatory preview, migration 067); the remaining piece is Phase 4 command/panel-action records (Q-0057 rider: no ordering until stable action identities). *(The #656 Help Preview migration onto the seam — [EOD verification §4](audits/past-day-verification-2026-06-10.md)'s Tier-2 finding — shipped in PR #671, 2026-06-10.)*
- Routing ledger: [idea-to-roadmap inventory](planning/idea-roadmap-inventory-2026-06-08.md).

## Someday / ideas (NOT approved — capture only)

> These are **not** queued work — captured so the picture is complete. Promoting one
> requires the gates in [`ideas/README.md`](ideas/README.md). Do not treat anything here as
> a priority.

- [superbot-vision-2026-06-10](ideas/superbot-vision-2026-06-10.md) — the maintainer's
  written product-vision statement + agent response: 2-minute setup KPI, panel
  navigation doctrine, 4-button help home, per-user preferences, RPG
  difficulty/survival/energy, story pets, AI-as-panel-orchestrator (inside the Q-0040
  posture); routing ledger inside. **Owner picks recorded same day (Q-0078):**
  one-way-ascent difficulty · both pet paths · the 4-button layout · next planning
  targets = RPG survival design (structured →
  [plan](planning/rpg-survival-difficulty-design-2026-06-10.md)) + help home/navigation.
- [fun-and-ease-brainstorm](ideas/fun-and-ease-brainstorm-2026-06-09.md) — 24
  dedup-verified fun + ease-of-use ideas (social/competition, ambient delight, member
  UX); owner picks recorded (Q-0053; pets structured → a games-lane plan).
- [settings-presets-and-ai-template-advisor](ideas/settings-presets-and-ai-template-advisor.md) —
  the AI template/preset advisor for settings (modular prompt designs the AI can
  suggest per task); the presets-everywhere *posture* itself is decided (Q-0070 →
  settings-audit Phase 4), only the advisor is Someday.
- [future-product-direction](ideas/future-product-direction-2026-06-07.md) — source-aware
  future product direction (polish, extensions, reusable systems, long-term).
- [ai-extra-tool-capability-ideas](ideas/ai-extra-tool-capability-ideas.md) — AI capability
  backlog (web / vision / file / KB / connectors / scheduler).
- [mining-exploration-brainstorm](ideas/mining_exploration_brainstorm.md) — mining design intent.
  *(§5 step 1 promoted 2026-06-08 to a [plan](planning/mining-wire-exploration-plan.md) + the
  Games lane; the rest stays captured.)*
- [superbot-ideas-lab](planning/superbot-ideas-lab-2026-06-05.md) — broad brainstorm; its
  §2 (operating decisions) + §6 (rejection ledger) are **binding do-not-propose**.
- **Custom commands** (operator-defined trigger→template responses, sandboxed) + **social
  feeds beyond YouTube** (Twitch/RSS/Reddit/…) — captured in
  [community-platform-features](ideas/community-platform-features-2026-06-12.md) §§2/4;
  groom toward Later once the safety/community lane's first slices land.

---

## Adding a plan

When a new plan doc lands (e.g. a fresh Codex/Opus planning doc):

1. **Home it to a sector first** (S1–S5 — use the [sector map](repo-sector-map.md) test: mechanism →
   S3, content → S4, ops → S5, BTD6 → S2, else S1). Add a **one-line row under its area** in that
   sector's drill-down — description + link to the plan + a horizon + a gate (or "—" if none) — and, if
   it changes the sector's live state, update that sector's **Now/Next** in the [dispatch
   index](#by-sector--the-live-dispatch-queues). If it fits no existing area, add it under the closest
   one and note the folio assignment is pending.
2. A new plan is **not auto-prioritized** — idea-order ≠ implementation-order. Default it
   to *Later* (or *Next* only if the maintainer says it's ready and nothing gates it).
3. Link the plan from its area **folio** too, so it's reachable both ways (the
   `scripts/check_docs.py` reachability gate enforces this).

This page is the *index*; the new plan doc stays the authority for its own scope.

## Maintenance

When work ships: update the area **folio** + `docs/current-state.md`, move the item's
horizon here (or drop it), and re-badge a finished plan `historical`. When a **gate**
clears (a decision lands, a dependency ships), promote the gated item from *Later* to
*Next*. The reachability gate (`scripts/check_docs.py`) keeps every plan linked here
findable.
