# NEW-BOT BUILD PLAN — the single dependency-ordered plan (capstone deliverable 2)

> **Status:** `plan` — **THE** unified build plan the first build session picks up, per
> [`../FINAL-REVIEW-HANDOFF.md`](../FINAL-REVIEW-HANDOFF.md). Folds Axis 1 (the 43 shipped
> subsystems, Lanes A–D), Axis 2 (plans/ideas, Lane E — **independently re-verified and corrected
> by this capstone**, §4.1), and Axis 3 (ecosystem, Lane F — source-corrected) over the L0
> foundation (Lane G).
> **Prepared:** 2026-07-03 (Fable 5 capstone, PR #1674). Companion verdict:
> [`FINAL-REVIEW.md`](./FINAL-REVIEW.md) — **GO-with-amendments**; nothing below starts until its
> §7 spec-amendment pass lands and the owner ratifies the design spec (Phase-3 gate).
> **Provenance rule:** where this plan and a lane file disagree, the lane file's per-unit ledger
> is the deeper record; where any doc and shipped source disagree, source wins (Q-0120).
>
> **▶ What happens next (owner-directed 2026-07-03):** this plan is the **frozen reference**. The
> next phase is (A) one more **content review pass** over the whole surface — commands / functions
> / methods — in dedicated owner-led sessions, then (B) **one 100%-complete design plan per step**
> before any code. The process + the immediate next-session goal live in
> [`../../../../planning/rebuild-planning-phase-2026-07-03.md`](../../../../planning/rebuild-planning-phase-2026-07-03.md).

---

## 0. How to read this plan

- **§1 The capability corpus** — every capability with its disposition. The menu.
- **§2 The build order** — dependency layers L0 → L5. Each layer is **100% production-grade
  before the next begins**; no item sits above an unbuilt dependency. The sequence.
- **§3 Per-capability acceptance** — the done-definition + outperform target per item. The bar.
- **§4 Plan-state corrections + improvements & expansions** — what this capstone's independent
  review of `docs/planning/` + `docs/ideas/` found and proposes. The delta.
- **§5 Deliberate omissions** — labeled, with *why*.

Two standing filters apply to everything below:
1. **The free-for-everyone mission** (Lane E `ProductPolicySpec`): no paywalls, no
   premium-gated features, support link confers zero benefit; every capability declares its
   cost/abuse posture. This is a design constraint, not a feature.
2. **The ideas-lab §6 rejection ledger is binding** (`docs/planning/superbot-ideas-lab-2026-06-05.md`
   §6 + current-state Off-limits): rejected concepts are carried forward as a **what-NOT-to-build
   filter** — do not re-litigate them in the new bot. (The capstone's plans review caught Lane E
   filing this under "stale drop" — the §6 carve-out survives the drop.)

---

## 1. The capability corpus

### 1.1 Axis 1 — the 43 shipped subsystems

Dispositions from [`FINAL-REVIEW.md`](./FINAL-REVIEW.md) §5 (grammar layer over the preserve-map);
layer assignments and dependencies here. **KEEP** = port to manifest as-is · **IMPROVE** = port +
named improvements · **MERGE** = folds into another unit · **REDESIGN** = same capability, new
shape. Full per-unit detail: the lane files.

| Capability | Disposition | Layer | Depends on | Notes |
|---|---|---|---|---|
| L0 runtime skeleton (bootstrap, loader, config, bus, lifecycle, tasks, health, DB seam, namespace) | REDESIGN root / PRESERVE primitives | **L0** | — | Lane G: preserve 6 primitives field-for-field; replace composition root + hardcoded loader + flat env; **build the namespace registry (new)** |
| settings | KEEP | L1a | L0 | the generated-config-hub proof; R-10 enforcement |
| diagnostic | IMPROVE | L1a | L0 | every platform command → declared provider id/schema/gate |
| help | KEEP | L1a | L0 | projection + overlay mutations; G-10 editor forms |
| admin | KEEP+IMPROVE | L1b | L1a | operator audit trail (`admin.operator_action`); PanelRef nav; bot-spam binding fix |
| server_management | KEEP+IMPROVE | L1b | L1a | hub + health badges preserved; register `setup` as real subsystem |
| moderation | IMPROVE | L1b | L1a | one declared authority story (R-2); case/appeal + bulk actions (outperform adds) |
| logging | KEEP | L1b | L1a | the 97% exemplar; G-1×8 + G-3 routes; binding route-truth flip |
| automod | KEEP+IMPROVE | L1b | moderation | G-11 stage; one "auto-mod tier" operator surface with cleanup/image_mod |
| image_moderation | KEEP+IMPROVE | L1b | moderation, AI provider adapter (L4 stub ok — the egress adapter, not the AI band) | off-by-default + fail-open preserved verbatim |
| security | KEEP+IMPROVE | L1b | moderation, logging | G-9 restore timers; audited slowmode; quarantine action |
| cleanup | KEEP+IMPROVE | L1b | moderation | both unaudited paths fixed by construction (audited seam + G-24) |
| welcome | IMPROVE (encoding) | L1b | logging, role | BindingSpecs + R-3 templates + R-1 role-grant workflow |
| counters | KEEP (**re-binned**) | L1b | logging | operator band, not economy (Lane B correction); R-7 backoff |
| channel | IMPROVE | L1b | L1a | G-18 lifecycle; small slash set replaces 17 prefix verbs |
| role | IMPROVE | L1b | channel (G-18 shared) | keep engines; G-21/G-22; teardown gap fixed at StoreSpec level; slash mirrors |
| ticket | KEEP+IMPROVE | L1b | channel, moderation | G-20 lifecycle; R-4 typed-column config; auto-close (ManagedTaskSpec); categories/reopen |
| proof_channel | IMPROVE | L1b | channel, moderation | binding surface + G-9 timed unlock |
| ux_lab | KEEP | L1c | L1a | zero-write gallery; the G-10 modal gallery |
| *visual card engine* (ADD, Lane E) | ADD-from-plans | **L1c** | L0 EmbedFrame | one themed CardTemplateSpec/renderer contract for welcome/rank/leaderboard/profile cards — built **before** the consumers that need it |
| economy | KEEP | **L2** (first) | L0, G-12/13/14 | the currency kernel; wire `transfer()` → `!give/!pay` |
| inventory | REDESIGN | L2 | economy, G-15 | one audited item kernel; merge the two item tables |
| treasury | KEEP | L2 | economy | falls out of G-12 |
| xp | KEEP | L2 | G-11, G-13 | ProgressionSpec curve; import stays a hatch; R-15 split ownership |
| karma | KEEP | L2 | L1a | the exemplar audited seam; karma-roles tail (§4.1) |
| community (hub) | KEEP | L2 | L1a | 100% generated |
| community_spotlight | IMPROVE | L2 | xp, economy | P-1 (when ratified) makes the feed durable |
| leaderboard | **MERGE into kernel** | L2 | R-5 | dissolves into per-subsystem LeaderboardSpecs + one renderer |
| *profile surface* (myprofile tail) | ADD-from-plans | L2 | xp/karma/economy, card engine | PR C decided (Q-0147) but unbuilt — fold into the new bot's profile card |
| games (hub) | IMPROVE | **L3** | L1a | 4 registry hubs → one generated hub |
| blackjack | KEEP | L3 (first, with rps) | economy, ChallengeSessionSpec | richest goldens; stat_writes land here |
| rps_tournament | IMPROVE | L3 | economy, G-17 | lobby → G-17; bracket stays owned tier-3; persist settings |
| deathmatch | KEEP | L3 | ChallengeSessionSpec, mining (gear) | both settle paths under kernel settle_once |
| fishing | KEEP | L3 | economy, items, G-13/14 + R-8 | Q-0175 gates the sell leg |
| farm | KEEP | L3 | economy, G-12/13/14 + R-8 | the clean end — 100% declarative |
| creature | KEEP | L3 | items, xp | coin-free PvP; catch roll stays tier-3 |
| casino | KEEP+IMPROVE | L3 | ChallengeSessionSpec + R-6 | + records store & leaderboard + checkpointed tables (impossible today — no store) |
| counting + chain | KEEP (**merged family**) | L3 | G-11, G-16 | one channel-message-rule family; surface or drop `chain_count` |
| four_twenty | KEEP | L3 | G-11 | the easiest declarative win |
| *giveaways* (ADD) | ADD-from-plans (+ecosystem) | L3 | economy (optional prizes), G-9/ManagedTask, G-20-adjacent | the one genuine ecosystem gap; free + native + audited vs GiveawayBot/Carl |
| *starboard* (ADD) | ADD-from-plans | L3 | logging routes (G-3), G-1 | Lane E keep; Carl/YAGPDB parity target |
| *explore hub + wild encounters* (ADD) | ADD-from-plans | L3 | games hub; mining/fishing/creature | **Q-0182**: start flat HubView router; **Q-0186 order: Wild Encounters → Collection → Quests → Shiny**; outperform = "feature-parity-or-better with Pokétwo's loop" (owner-stated, recovered by §4.1) |
| mining | REDESIGN — **port LAST in L3** | L3 (last) | *every* game family (G-12…G-15, R-8, R-12) | **the acceptance test for the whole game-primitive stack**: if the grammar regenerates mining, it regenerates the lane |
| ai (platform) | REDESIGN into specs | **L4** | L0 K9, G-7/G-8 + R-13 | NL router + per-domain intents; provider calls stay hatches |
| btd6 | KEEP+IMPROVE | L4 | ai platform | the KnowledgeDomainSpec exemplar; sources/freshness/evals as data |
| project_moon | IMPROVE/MERGE | L4 | ai platform | same family; Limbus domain **partially shipped already** (§4.1) — port + finish StaticData tail |
| *youtube / shared ingestion* | ADD-from-plans | L4 | ai platform | third consumer of the shared IngestionPipeline |
| utility | MERGE (pack) | L4/tail | G-9, G-10 | poll → first-class candidate (§5 of Lane F) |
| general | MERGE (pack) | L4/tail | providers | content pack |
| *web dashboard + live editor* | REDESIGN (manifest projection) | **L5** | manifest snapshot (L0), settings lanes | one generated web projection — **not** a parallel hand-built app; current app is FastAPI (not Flask — corrected) |
| *boards family* (owner inbox / feedback / per-command threads) | ADD-from-plans (redesigned) | L5 | G-20-adjacent, P-1 candidate | one tagged-board primitive covers all three plans |
| *bot-migration assistant* | ADD-from-plans | L5 | L1 complete, manifest corpus | detect → map → replicate → retire; the public-bot wedge |
| *Railway / ops control-plane* | ADD-from-plans (owner-gated) | L0-adjacent, ships with cutover | secrets, credentials | drift checker, deploy alerts, shadow clone, verified backups |

### 1.2 Axis 3 — what the ecosystem check actually yields

After source-correcting Lane F (its raw research had flagged six *shipped* subsystems as gaps),
the ecosystem contributes **one genuine build** (native giveaways — already planned, scheduled
L3), **one deferred option** (external feeds — §5), and otherwise **outperform targets on
existing surface**, folded into §3. The "grouped self-roles" candidate is retired — per-menu
`unique`/`verify`/`max_roles` modes ship today (`role_menu_view.py:91-144`).

### 1.3 Not-scheduled corpus (documented, deliberately unbuilt — the known-options menu)

See §5. Everything else in `docs/ideas/` + `docs/planning/` that is neither scheduled above nor
listed in §5 is either shipped (Axis-1 parity material), a workflow/substrate concern (not a bot
capability — e.g. the memory-retention/context-economy program, reconciliation automation), or
dropped per Lane E's ledger + this capstone's §4.1 corrections.

---

## 2. The build order

**Gate 0 — the spec-amendment pass** (docs; FINAL-REVIEW §7): fold G-9…G-24 + riders into the
design spec. **Gate 1 — owner ratifies** the design spec + amendments (the Phase-3 gate), and the
Phase-0.5 siblings run (golden capture + telemetry capture against the live bot). Nothing below
starts before both gates.

### L0 — Foundations (the kernel; design spec K0–K10 = Lane G L0.0–L0.11)

Build order within L0 is fixed and topological; each step lands with its checker
(`lane-G-foundations.md` §8 carries the full table + per-component done-definitions in §9):

K0 substrate+observability → K1 **namespace registry** (the one thing that doesn't exist today;
the Q-0211/BUG-0030 crash-loop class dies here) → K2 grammar+compiler+snapshot (now including the
Gate-0 amendments) → K3 DB seam → K4 EventBus (generated catalogue) → K5 lifecycle+tasks
(+ injectable clock/RNG) → K6 authority → K7 workflow engine → K8 interaction runtime →
K9 kernel/ai → K10 sim runner + golden harness + CI Postgres (**repo born red on parity, green on
everything else**).

**L0 exit bar:** a settings/diagnostic/help subsystem renders panels/settings/help entirely from
its manifest with zero hand-written UI code, passing `golden-parity` — the generated-panel payoff
proven before any feature ports.

### L1 — Core management (the operator's control plane)

- **L1a — the platform proves itself on itself:** settings → diagnostic → help. Exercises all
  four workflow lanes + generated settings panels while the golden oracle is freshest.
- **L1b — the operator spine** (order within band by dependency, then blast radius): admin →
  server_management → moderation → logging → automod → security → cleanup → welcome → counters →
  channel → role → ticket → image_moderation → proof_channel. The generated-panel payoff lands
  here (automod/security/welcome/counters get panels for free); binding route-truth + KV alias
  map; `EVT_MOD_ACTION` payload pins; safe-default-ON flips (the §4.4 showcase) with the owner's
  one-page "what flips ON" diff.
- **L1c — presentation foundation:** the **visual card engine** (CardTemplateSpec + render
  contract + golden image snapshots) — before every card consumer (welcome cards, rank cards,
  leaderboard cards, profile cards). ux_lab ports here as the living gallery.

**L1 exit bar:** every operator function reachable from the hub; every setting/binding/resource
of the band editable through generated panels; parity goldens green for the band; the six §6.3
FINAL-REVIEW bug classes demonstrably impossible (audited seams + bindings by construction).

### L2 — Economy & social foundations

Order: **economy first** (the currency kernel every game composes) → inventory (the audited item
kernel, G-15) + treasury → xp → karma → community hub + spotlight → the **leaderboard kernel**
(the subsystem dissolves; every producing subsystem declares its boards) → profile surface.

**L2 exit bar:** INV-F/G/K carried as generated AST fences; every coin/item/xp/karma move
audited + evented atomically (G-12/G-15 semantics proven under raced-click and concurrency
goldens); the 12 leaderboards render from declarations with the shared card renderer.

### L3 — Games, world & community features

Wager games first (richest goldens, escrow seam): **blackjack + rps_tournament** (G-17) →
deathmatch → checkpoint games: **fishing → farm → creature** → **casino** (+ new records store,
checkpointed tables) → **counting+chain** (merged G-16 family) + four_twenty → ADDs:
**giveaways**, **starboard**, **explore hub (flat router per Q-0182) + wild encounters (Q-0186
order)** → **mining LAST** — the deliberate acceptance test: it exercises every game-family
primitive (G-12/13/14/15, R-8, R-12); *if the grammar can regenerate mining, it can regenerate
the lane.*

**L3 exit bar:** every game's money path settles exactly once under raced inputs (kernel
`settle_once`); restart behavior matches each session's declared persistence class; every
game with persisted stats has a declared leaderboard writer (decision-10 honesty); mining's
characterization suite green on the rebuilt kernel.

### L4 — Knowledge & AI (deliberately after the deterministic platform)

ai platform specs (G-7/G-8 + R-13; NL monolith → router + intents) → **btd6** (the exemplar:
source registry, freshness/trust labels, ingestion-opens-a-PR, offline eval suite) →
project_moon (port the shipped Limbus domain + finish the StaticData tail) → youtube via the
shared ingestion pipeline → utility/general packs (the tail).

**L4 exit bar:** every AI task has provider/fallback/context/eval/redaction declarations; CI
proves no unredacted request path and no live-API eval path (deterministic provider only);
knowledge answers carry source+freshness labels; eval corpora pinned to content versions.

### L5 — Control plane & growth surface

Web dashboard as a **generated manifest projection** (public/config split, live editor writing
through the same workflow lanes as Discord) → boards family (owner inbox / feedback / per-command
threads on one tagged-board primitive — the likely P-1 ratifier) → bot-migration assistant
(detect installed bots → map features to manifests → preview → reversible apply) → ops
control-plane items as the cutover approaches (owner-gated: Railway drift checker, deploy
alerts, shadow clone, verified backups).

**Post-parity bands** (after cutover, per design spec §9.2): remaining `legacy_view`
eliminations, escape-hatch ratchet reductions, telemetry-refreshed sim re-runs, deferred
019-style store collapses.

---

## 3. Per-capability acceptance — done-before-next + outperform

The **full production-grade done-definition for every Axis-1 capability lives in its lane
section** (they are precise, per-unit, and golden-referenced — repeating them here would fork
them). This table is the index + the outperform resolution (Lane F's `pending Lane F` cells
resolved). *Done* always additionally includes: manifest compiles + namespace-clean, sim-reviewed
or exempt, parity golden green, escape hatches justified + counted.

| Capability | Done-definition (one line — full text in lane) | Outperform target (resolved) |
|---|---|---|
| L0 kernel | per-component bars in Lane G §9; born-red parity repo | **nobody has a pre-connect collision gate or a generated panel/settings/help layer** — the two L0 edges are ours alone (Lane G §5.4) |
| settings | every schema setting has generated UI, G-5 bounds, audit, help | Dyno/MEE6 web-config parity *in Discord*, free |
| diagnostic | every platform command = declared provider + schema + gate + audit | ops consoles of hobby bots (no public comparator found — confirm) |
| help | all manifests project into help; overlay drift tests | Carl/Dyno help UX; ours is generated so it cannot drift |
| admin | 4 caps wired-or-removed; operator actions audited; greeting via binding | typical hobby-bot admin cogs (already ahead; audit trail completes it) |
| server_management | badges fail-safe golden; nav via PanelRefs; setup capability-gated | web dashboards — ours is in-Discord, live-health, governance-transparent |
| moderation | Lane A (a)–(d): identical resolution across all 3 surfaces; escalation byte-for-byte | **Dyno** filters: match configurability, beat on free + audited + privacy-forward public log; add case/appeal + bulk |
| logging | Lane D: live-test stays the only tier-3; declared gates on all 8 listeners | **ProBot/Carl**: reach DM-log + webhook-route depth on the route/panel spine |
| automod | 432-line suite ported; fail-open proven under forced faults | **MEE6/Carl/Dyno** baseline matched; ordered fail-open audited pipeline is the edge |
| image_moderation | Lane A's 7-point golden incl. privacy regression (URL-only) | mainstream bots ship none — likely a genuine differentiator (confirm) |
| security | 27 tests + quarantine + audited slowmode; fail-open joins | **Wick**: close quarantine/join-viz gaps; beat on no-PII/fail-open/audited-kick |
| cleanup | every mutation audited identically; 7 scan modes byte-for-byte; slash surface | **Carl/MEE6/Dyno** purge parity (explicit design target) + scope-chain policies beyond it |
| role | reconciliation decision-table golden; teardown per store; one authority string | **Carl-bot**: already ahead on batched failure reporting + server-side menu modes + live counters (Carl paywalls these) |
| channel | 17 verbs' mutations identical; every mutation audited; caps-safe lists | web-dashboard bots: batch ops + in-Discord audit trail is structural |
| welcome | Lane A matrix golden (variants deterministic under injected rng; age-gate all-or-nothing) | **ProBot** card depth via the L1c card engine |
| ticket | identical rows/events across all 3 entry paths; transcripts both-ways | **Ticket Tool**: free transcripts (they paywall); add auto-close/SLA, categories, reopen |
| counters | rename-on-diff only; backoff; presets through audited pipeline | Statbot-class: declarative presets + rate-limit-aware sync |
| proof_channel | binding ownership + audited grants + timed-unlock recovery | niche — parity is enough (deliberate) |
| economy | atomic ledgered moves; no double-charge under race; `!give/!pay` wired | **Dank Memer/UnbelievaBoat**: beat on auditability + atomicity + data-driven jobs/shops |
| inventory | byte-identical browser; every grant audited; unique-grant race golden | unified cross-game inventory + full item audit trail — no comparator does this |
| treasury | no-overdraw conditional debit; concurrent-disburse golden | guild-bank features of economy bots; audited + attributable |
| xp | identical earn/curve/announce/import; audit on admin ops | **MEE6/Arcane/Amari**: declarative curves + free rank cards + one-click import |
| karma | INV-K goldens (4 typed failures write nothing; atomic grant) | **Carl/MEE6 rep**: per-pair cooldown + rolling cap + audit-ledger-as-source |
| community hubs | render = governance-visible children exactly; fail-closed clicks | hardcoded menu trees everywhere else |
| spotlight | identical dashboard; feed survives restart (improvement) | no equivalent unified surface in mainstream bots |
| leaderboard kernel | 12 boards byte-match from declarations; alias table resolves | **MEE6/Arcane paywalled single boards**: 12 free unified themed boards |
| blackjack | Lane C (a)–(e) money-path goldens; stat_writes land | crash-safe escrow/settle-once as kernel guarantee — no mainstream casino bot has it |
| rps_tournament | 8-player bracket golden with bye + pot-once + resume target | web-dashboard bracket bots: full lifecycle in-channel, money-safe |
| deathmatch | settle-exactly-once double-click golden; bots off leaderboard | RNG-only duel bots: gear integration + consent flow + fair ladder |
| counting+chain | scripted-stream replay golden; scope-lock concurrency; DoS bound | **MEE6/Carl single-mode counting**: 11 modes + expression parsing + per-channel boards |
| casino | full-hand parity incl. side pots + timeout; then checkpointed tables + records | per-player live-ephemeral table already unique; records/restart-safety complete it |
| fishing/farm/creature | Lane B per-subsystem goldens (atomic multi-store writes; seeded distributions; settle invariants) | Virtual Fisher / IdleRPG-class: depth-per-declaration + transactional integrity |
| mining | characterization suite + write-boundary ratchet + seed-deterministic grids | IdleRPG/OwO-class: shared-seed roam-and-dig world is distinctive |
| four_twenty | stage observe-only golden; cooldowns | trivial; parity |
| giveaways (ADD) | create/end/reroll/cancel; state survives restart; eligibility + audit; sim covers timeouts/rerolls | **GiveawayBot/Carl**: free + native + audited + restart-safe |
| starboard (ADD) | thresholds configurable; survives restart; moderation exclusions | **Carl/YAGPDB** starboard parity, free |
| explore/encounters (ADD) | flat router (Q-0182); spawn anti-spam; cross-game inventory contracts | **Pokétwo's loop — parity or better** (owner-stated, Q-0186) |
| ai platform | every task declared (provider/fallback/context/eval/redaction); no unredacted path in CI | category-defining — no mainstream equivalent; the bar is eval quality |
| btd6 | every answer source-labelled + fresh; refresh/eval probes ops-visible | — (unique domain) |
| project_moon | source registry + eval parity with btd6 | — (unique domain) |
| utility/general | info commands on shared providers; poll/remind via G-10/G-9 | promote poll toward first-class (community band) |
| dashboard (L5) | React app generated from snapshot; live editor writes through the same lanes | **Dyno/MEE6**: module-toggle + live-editor parity, free |
| boards family (L5) | create/tag/triage/resolve; durable index; idempotent GitHub sync | forum/ticket bots; one primitive, three products |
| migration assistant (L5) | detect known bots; map to manifests; preview; reversible apply; no writes without confirm | **the anti-MEE6/Carl/Dyno wedge**: nobody helps you *leave* a bot |

---

## 4. Plan-state corrections + improvements & expansions (the independent review)

This capstone independently reviewed the full planning/ideas corpus (all 143 `docs/planning/` +
177 `docs/ideas/` files, five parallel reviewers cross-checking Lane E, `current-state`,
`roadmap`, and shipped source). Verdict on Lane E itself: **its structure and dispositions are
mostly right, but it inherited stale plan-badges** — the corrections below are binding over the
raw Lane E rows they touch.

### 4.1 Corrections to the Axis-2 record (drift caught; fix-on-sight class, Q-0166)

1. **Lane E missed the shipped manifest spine** — `manifest-spine-execution-plan-2026-06-17.md`
   (PRs #1018/#1019 + an unmarked-shipped PR3): a **production-tested typed
   CommandManifest/PanelManifest with CI reconciliation drift-guards already runs in the old
   bot** (`core/runtime/command_manifest.py`, `panel_manifest.py`, `manifest_reconciliation.py`).
   This is the strongest prior art for the rebuild's own §2 bet and belongs in the Gate-0 pass
   (see improvement I-1).
2. **Shipped-but-still-badged-`plan` files misled Lane E** (≥17 across both slices): the fishing
   minigame + most of the fishing open-world plan, the mining hub redesign (~90%), the
   extension-taxonomy crosswalk, reaction-roles PR1–5 (+refinements; only optional PR6 remains),
   the safety-community family (all five features shipped), the settings-pointer arc PR3, the
   substrate-kit finalization (#1649), karma's reaction-grant (#1620) — all are **Axis-1 parity
   material, not forward builds**. §1.1's ADD rows already reflect the corrected (much smaller)
   forward tails.
3. **Decided-but-unbuilt turn-key tails surfaced** (invisible because the advertising docs are
   stale): myprofile **PR C** (Q-0147 decided 06-16; roadmap still says "gated"), **karma-roles**
   (the plan's "PR3 deferred" line is stale), the **explore-hub flat router** (Q-0182). All three
   are scheduled in §1.1/§2 — and are also legitimate *current-bot* slices any session can pick
   up now.
4. **The Pokétwo mapping was buried** under Lane E's voice/music defer row, losing the owner's
   decided **Q-0186 build order** and the stated **beat-Pokétwo target**. Recovered into the
   explore/encounters row (§1.1).
5. **Project Moon is not "defer until foundation proven"** — the Limbus knowledge domain
   partially shipped (#1453…#1549). Re-dispositioned: port + finish the tail (L4).
6. **Two recon-pass records and several completed initiatives still carry `plan` badges**
   (band1530/band1560 et al.) — the two unambiguous recon-band mislabels are **fixed in this PR**
   (Q-0166 fix-on-sight); the judgment-needing rest are surfaced by the new checker (§4.3).
7. **The voice/music decision pack is decision-ready and unrouted** since 06-20 — it should go
   to the owner as a router Q so the Q-0041 gate can be lifted or kept deliberately (§5 stays
   the answer until then).
8. **Ideas-side Lane E misses** (owner-decided items that must not be lost): the **Q-0184
   per-user product AI memory** decision (honcho evaluation) and the **answered Q-0091
   cross-server identity/transfer design** — both now carried as P-3/P-4 future-family
   candidates in FINAL-REVIEW §3.3 and attached to their L2/L4 rows; **audit-log catch-up on
   reconnect** (critical under merge=deploy restart cadence) — carried as P-2; the
   **compute-don't-refuse flywheel** (triage → correction ticket → deterministic tool → probe)
   — folded into the L4 ai row's improvement set.
9. **The wire-level live-bot harness is NOT owner-gated anymore** — Q-0213 cleared it; Lane E
   parked it behind a stale gate. Re-dispositioned: buildable, and doubly valuable with a
   record mode that emits `parity/` golden fixtures directly (I-13).
10. **Superseded workflow-idea cluster** (external-cron-trigger→Q-0146, executor-chain→Q-0145,
    phase-gate-precheck→Q-0172, lane-scoped-state→Q-0195) sits unmarked — flagged for re-badge
    with provenance pointers; the new checker's idea-shipped rule catches the class.

### 4.2 Improvements & expansions this capstone endorses

Filtered to what I would defend; each is contained and independently schedulable. I-1…I-4
strengthen the **rebuild gate evidence** (highest leverage first); I-5…I-10 improve capabilities
or the corpus itself.

- **I-1 — Validate the grammar against the shipped manifest spine.** Field-by-field diff of the
  §2 CommandSpec/PanelSpec against the production-tested `command_manifest.py`/`panel_manifest.py`
  shapes, and port the "manifest faithfully projects the ledger" reconciliation-test pattern into
  the `parity/` harness. The rebuild's core bet has running prior art in its own repo — use it.
- **I-2 — Write the giveaway manifest as the first *unbuilt-subsystem* grammar proof.** Every
  fit number so far retrofits shipped code; the rebuild's real mode is expressing capabilities
  that don't exist yet. Giveaways are the cleanest fully-unshipped plan (verified: zero giveaway
  code) and exercise G-9 + scheduling + persistence + anti-abuse in one manifest. Cheap, docs-only,
  and it de-risks the ADD lane before Gate 1.
- **I-3 — Write the Limbus KnowledgeDomainSpec manifest** (4th spike-style worked example) over
  the *shipped* Project Moon domain — the same retrofit validation karma/logging/blackjack gave
  the core grammar, applied to the G-7 facet three Lane E rows hinge on.
- **I-4 — Machine-readable balance corpus.** Convert the ~15 pinned-number ledgers
  (mining/fishing/forge/gear/titles/respec…) into committed YAML/JSON that runtime constants,
  simulators, and a parity test all read — kills the manual three-place sync and gives the
  rebuild a direct numbers→manifest import path.
- **I-5 — Plan-staleness checker** (`scripts/check_plan_staleness.py`, warn-first): flag any
  `docs/planning/*.md` badged `plan` whose body carries shipped markers (`✅ SHIPPED`, `▶ BUILT`,
  `Applied (…PR #N)`, `AUDIT COMPLETE`), and any reconciliation-pass file below the current
  band marker. ≥17 files drifted this way and the drift **materially misled a fleet lane** —
  exactly the Q-0194 friction→guard class. *(Shipped with this PR — see §4.3.)*
- **I-6 — Kernel `settle_once` as a stated money-safety guarantee** in the spec's ChallengeSessionSpec
  section, citing the two live bugs it retroactively kills (FINAL-REVIEW §6.3) — turn the audit
  finding into the spec's own motivation text at Gate 0.
- **I-7 — Casino records store + checkpointed tables** (already folded into §1.1/§3): the only
  Lane B subsystem where the *absence of a store* blocks its outperform bar.
- **I-8 — Moderation case/appeal + bulk actions; ticket auto-close/SLA + categories + reopen**
  (already folded into §3): the two named feature gaps vs best-in-class after everything else is
  parity-or-ahead.
- **I-9 — Orientation-cost measurement using the #1649 context-economy engine** as the harness
  for the still-unexecuted orientation-cost-reduction plan — one instrumented run also feeds the
  substrate Phase-2.5 A/B gate (workflow substrate, not bot capability; routed to the S3 lane).
- **I-10 — Route the voice decision pack to the owner** as a DISCUSS router Q (one file, closes
  an idle decision loop either way; the plan itself stays §5-deferred).
- **I-11 — Gateway catch-up as declared policy (P-2).** Because every merge redeploys the
  worker, gateway events are *routinely* missed in restart windows; a declared
  `catchup_policy` (high-water mark store, bounded replay, dedup-by-entry-id) on G-1 listeners
  turns "logging misses events during deploys" from a known hole into kernel behavior.
- **I-12 — Wire-level harness with a fixture-record mode (Q-0213-cleared).** Build
  `tools/livebot/` so wire-captured embeds/components/DB effects emit `parity/` golden fixtures
  in the #1639 harness format directly — live verification and golden capture become one
  motion, feeding exactly the Phase-0.5 capture task Gate 1 needs.
- **I-13 — Sequence the substrate-kit atomicity fix (re-entrant transaction +
  atomic `apply_review_verdict`) BEFORE the Phase-2.5 cold-start A/B** — a hard prerequisite,
  not a someday-PR (the A/B's numbers are untrustworthy over a known write race).
- **I-14 — Machine-check the balance corpus against the sim** (extends I-4): once the number
  ledgers are data, a parity test asserts runtime constants == corpus == sim assumptions, making
  every tuning change simulation-checked by construction (the standing sim-first rule, cheap).

### 4.3 Friction→guard conversion shipped with this session (Q-0194)

The plans review surfaced a mechanically-detectable drift class that actively misled a lane
agent. Per Q-0194 ("checker guards are free to ship now"), this PR ships **I-5** as
`scripts/check_plan_staleness.py` (warn-first, stdlib-only, provenance header per Q-0105 with
the delete-if-unreliable clause), covering all three rules: `plan`-badged files with shipped
markers, recon-pass records behind the band marker, and `ideas`-badged files with
SHIPPED/EXECUTED markers. First run: 26 findings (matching the review agents' independent
lists — a good initial ground-truth signal). The two unambiguous recon-band mislabels
(band1530/band1560) are fixed in this same PR; the rest need per-file judgment and are left to
the checker's standing output. It is advisory until it proves itself across a few sessions.

---

### 4.4 Rebuild doc-set consistency (what the Gate-0 session must also fix)

A dedicated cross-check of the eight rebuild docs against each other and shipped source found
**source fidelity excellent** (~25 load-bearing `file:line` citations in the design spec all
verify exactly; parity numbers consistent across linchpin/parallel-plan/COVERAGE) — the problems
are *freshness*, and they land squarely in the Gate-0 pass's lap:

1. **[blocker-class] The design spec believes its amendment story is finished** ("six named
   amendments — now folded in") and has zero pointer to this audit. Gate-0's first edit is the
   spec header: link FINAL-REVIEW, state the G-9…G-24 + rider pass, and align §9.2's port order
   with §2's L-layers (ticket/role/channel/image_moderation/proof_channel belong to the operator
   spine, mining ports last).
2. **Stale handoff §C**: it instructs a fresh session to *build* the golden harness that already
   exists (`parity/`, #1639) with a mechanism the linchpin work disproved (dpytest). Rewrite §C
   as "consume the shipped harness".
3. **Phantom "handoff §F"** cited by three docs (the parallel plan twice + the start-here index)
   — the handoff ends at §E; fix the pointers.
4. **Strategy Phase-0 never stamped done** (the kit finalized in #1649; §3/§7 still present it
   as open) and it points at a `rebuild-harvest/` directory that never existed in-tree.
5. **Minor numeric drift** to reconcile in one sweep: command-surface denominators
   (271 registered vs 406+73 walked — different bases, state which is canonical per consumer),
   settings-key counts (~114 vs 120), kit test counts (399/407/422).

Doc-set reviewer proposals adopted into this plan: a **golden-recapture protocol** for the six
§6.3 bug fixes (each current-bot fix must re-capture its goldens or parity later "verifies" the
bug); a **machine-readable gate-state ledger** (`rebuild-gates.yml`: design-approval · Gate-0 ·
kit start-gate · linchpin commit-gate · telemetry capture · cutover — each with state +
evidence link); the **canonical amendment registry** (see the session idea in this PR's session
log — the B/C lanes independently minting colliding G-numbers is the proof it's needed); and a
**named telemetry-capture session** with a paste-ready prompt + a trip-wire that it runs before
the old bot is ever frozen.

## 5. Deliberate omissions & deferred known-options (labeled, with why)

| Option | Status | Why |
|---|---|---|
| **Voice / music** | Deliberate omission (Q-0041 gate) | licensing + complexity + provider dependency; verified zero voice code; decision pack ready for the owner (§4.2 I-10); grammar family (VoiceSessionSpec) would be a new design pass if ever green-lit |
| **External feeds** (RSS/reddit/YouTube-notify) | Deferred known-option | YAGPDB/Dyno have them; no feed primitive here (verified — `youtube_video_cache` is AI grounding, not a feed); would ride G-1/G-3 + ManagedTaskSpec if wanted |
| **Premium/paywall architecture** | Anti-goal | the free-for-everyone mission — competitors' paywall is our positioning, not our gap |
| **Mudae-style gacha** | Deliberate omission | niche; our creature/collection loop is its own design |
| **Open-domain AI chat** | Deferred | grounded/eval-first by design; revisit as the space matures |
| **External analytics dashboards** | Deferred | the L5 dashboard could grow here later |
| **Deep BTD6 decode / live spot-checks** | Demand-gated (S2 owner lane) | provenance-gated; build on demand signals |
| **Ideas-lab §6 rejected concepts** | Binding rejections | carried as the what-NOT-to-build filter (§0) |
| **Vector DB / durable-execution engine / external agent framework / model pinning** | Non-goals in phase 1 | per design spec §10.3 — re-litigating them mid-port is the failure mode |

---

*Corpus pointers: per-unit ledgers + manifest sketches per subsystem — lanes
[A](../lanes/lane-A-governance.md) · [B](../lanes/lane-B-economy.md) ·
[C](../lanes/lane-C-games.md) · [D](../lanes/lane-D-knowledge-platform.md) ·
[G](../lanes/lane-G-foundations.md); forward ledger — [E](../lanes/lane-E-plans-ideas.md) (as
corrected by §4.1); ecosystem — [ecosystem-benchmark.md](./ecosystem-benchmark.md); verdict +
amendments — [FINAL-REVIEW.md](./FINAL-REVIEW.md).*
