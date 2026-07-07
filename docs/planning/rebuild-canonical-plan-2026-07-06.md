# SuperBot rebuild — THE canonical plan (2026-07-06)

> **Status:** `plan` — **the single source of truth for the fresh-repo rebuild.** Consolidates the
> scattered rebuild corpus into one comprehensive, correctly-layered, internally-consistent plan:
> the corrected foundational-layer taxonomy (§2), the one canonical phase arc (§3), the canonical
> gate list (§4), and the ordered start sequence (§5). Produced by the Fable-5 consolidation
> session ([brief §3](rebuild-newrepo-start-fable5-ultracode-brief-2026-07-06.md), PR #1770) under
> the **decide-and-flag** model (owner directive **Q-0240**,
> [`../owner/agent-decision-authority.md`](../owner/agent-decision-authority.md)): every call here
> is **decided, with rationale**, in §8's decisions log; the high-stakes calls are flagged in §1
> for the owner's one-pass veto at the go/no-go. Grounded by a 7-lane source-verification fan-out
> (evidence base §10). **Supersede scope:** §9 lists what this replaces and what stays live.
> Source + merged PRs win over this file (Q-0120). Companions:
> [test-guild design](rebuild-test-guild-design-2026-07-06.md) ·
> [Phase-2.5 runnable procedure](rebuild-phase-2.5-procedure-2026-07-06.md).

> **⚠ AMENDMENT — owner directive Q-0241 (2026-07-07): the owner gates are retired.** The **G1
> go/no-go sitting** (§1, §4, §5 step 5), **G2 "owner accepts the verdict"** on Phase-2.5 (§4), and every
> **👤 owner-gated step** in §5 (notably step 6 "create the repo") are **no longer blockers.** The
> coordinator builds everything **in logical order**, **live-tests each piece in a real server** (an
> agent drives all commands live), and **never waits for the owner — silence = consent = done.** Read
> §1/§4/§5 as *sequencing + rationale*, not as owner stop-points; the 🔒/👤 markers are historical.
> **Retained (flagged, vetoable):** the **destructive tier** (prod data import, CUT-3 token swap,
> deleting old-bot data) still executes via the reversible path this plan already specifies — shadow-
> first, N=7d rollback window (Q-D15), reverse-import valve (F-1/F-2) — which is *reversibility, not a
> gate* (no pause). *The owner may veto this rider for straight destructive execution.* Merge=deploy
> still requires **CI green**. Full model:
> [`../owner/agent-decision-authority.md`](../owner/agent-decision-authority.md) § Q-0241;
> [`../owner/maintainer-question-router.md`](../owner/maintainer-question-router.md) Q-0241.

---

## 0. Where the program stands (verified at head, 2026-07-06)

**Everything before Phase 3 that agents can build is built, except three small things** — and none
is new-repo code:

| Done (with anchor) | Remaining before new-repo code |
|---|---|
| Substrate-kit finished (#1649; 422/422 → 432 tests green under python3.10, stdlib-only, one-step `dist/bootstrap.py adopt` re-proven live in a scratch dir this session) | ~~**Phase-2.5 cold-start A/B**~~ ✅ **RUN #1775 (FAIL as-tested) → adopt-render fix + re-run pair executed 2026-07-07** (§11 A-1; [final-review report](rebuild-final-review-report-2026-07-07.md)) |
| Golden harness built + measured (#1639; `parity/`, 465 goldens, drives the **full real command pipeline in-process** — see §6) | ~~**Kit tail ①**~~ ✅ **SHIPPED #1775** (`substrate-kit/src/engine/lib/state.py:112-133` — re-entrant txn + txn-wrapped `apply_review_verdict`, Q-0223). *This §0 cell was written pre-#1775; §5 step 1 is current.* |
| Harvest + design spec (`rebuild-design-spec-2026-07-02.md`) — now **superseded-in-part**, see §9 | ~~The owner go/no-go sitting~~ **RETIRED (Q-0241)** — the §1 flag list stays the react-anytime veto surface |
| Capability audit → frozen `NEW-BOT-BUILD-PLAN.md` (#1674, GO-with-amendments, fit 85.1% — re-verified live this session at 85.26%) | `tools/check_amendments.py` — ✅ **BUILT #1775** (S0's enforcing half; `rebuild-amendments.yml` names it; advisory tier Q-0105). *K1 NamespaceRegistry — P-9's other half — remains unbuilt.* |
| Phase-A Stage 1 + conventions freeze (#1679/#1680) · Stage-2 walk L1a+L1b decided (#1725; 33+ rows remain, owner-live) | Stage-2 walk continuation (owner-live; blocks *those subsystems' port plans*, not the repo start) |
| Gate-0 grammar freeze (#1716): 14 specs → frozen L0 grammar, S0–S15 build order, owner-decision packet | Phase-B per-step plans for L1+ consumers (L0 is planned: the 14 specs + S0–S15) |
| **Gate V complete** (`GATE-V-SYNTHESIS.md`): plan source-accurate, **Sequence C adopted**, punch-list P-1…P-9 | — |

The maintainer can green-light Phase 3 by reading §1 (the veto list) and §5 (the start sequence).
Nothing else needs re-deriving.

---

## 1. Flag-for-gate — the owner's one-pass veto list

Per Q-0240 these are **decided recommendations, not open questions**: skim, veto what you disagree
with, bless the rest. Full rationale in §8.

### F-1 · The backward-compat DATA contract *(irreversible once executed — the big one)*

**Recommended ruling:** the design-spec §10.2(9) shape — **fresh schema from `0001` + a one-time
importer with owner-reviewed dry-run reconciliation**, preserving verbatim: user **balances,
inventory, XP, karma, settings values**, persistent **`custom_id` strings** (the eight `ai:*` ids
included), **subsystem-registry keys**, and the governance tables (`help_overlay`, visibility,
cleanup); event names + audit payload shapes carried per the frozen grammar. The
**carry-the-chain zero-migration cutover stays the specified fallback** if reconciliation fails
review. Rollback protection per Q-D15 (F-2): declared-loss + the narrow reverse-import valve for
money/audit. *Why this shape:* it is what the design spec already specifies and Gate V
re-verified; "migrate only the important data" and "start fresh" both destroy user trust for zero
build savings. **Nothing irreversible happens on paper** — the contract executes only at
CUT-2/CUT-3, each owner-verified.

### F-2 · The Gate-0 packet — 12 rows + L-21, pre-filled

Recommended ruling per row (packet: [`owner-decision-packet.md`](../analysis/rebuild-discovery/foundations/gate-0/owner-decision-packet.md)).
**Bless-the-shipped-default** unless marked ⚠ (the one deliberate divergence):

| Row | Call | Recommended ruling | One-line why |
|---|---|---|---|
| 🔴 Q-D8 | store-drop disposition default | **(b) no default — `disposition` REQUIRED per retirement** (= shipped) | a silent global disposition is a silent data-loss path |
| 🔴 Q-D13 | money-repair direction | **(C) `QUARANTINE_ONLY`** (= shipped) | never auto-mint or auto-claw; you sign each case |
| 🔴 Q-D14 | RPO target + backup source | **(A) daily `pg_dump` ≤24 h floor now**, with a **named revisit at CUT-1** (B off-box audit-log export vs C plan-upgrade PITR) | Railway backup schedules verified plan-gated on Hobby ([railway plan §6 R2](railway-setup-plan-2026-07-02.md)); minutes-RPO is a spend call that deserves cutover-time data |
| 🔴 Q-D15 | rollback disposition + window N | **(B) declared-loss + narrow reverse-import valve** (= shipped) · **N = 7 days** | round-trip only the money/audit tier; short forward-fix-biased window matches merge=deploy velocity; N was the one blank the packet carried |
| ⚠ Q-D5 | intent posture | **(a) DEGRADE** — flip the frozen `required=True` floor at this sitting (the design recommendation, diverging from the shipped fail-closed floor; = open fork F-3/PG-2) | slash-first survivability (Q-D21) is incoherent with a bot that refuses to boot on intent denial; this sitting IS the PG-2 ruling the flip waits on |
| Q-D16 | credential recovery arm | **(a) full arm** (= shipped) | removes owner-dependency at compromise time; orthogonal to Q-0213 |
| Q-D17 | revocation carve-out | **(a) agent-runnable credential revoke** (= shipped) | a token revoke loses no data; Q-0213's brake is about data loss |
| Q-D18 | lockfile + pip-audit gate | **(a) lockfile + CI gate** (= shipped) | composes with adopt-freely: adopt → regenerate lock → CI verifies |
| Q-D19 | `SB_PROD_ATTEST` custody | **(a) presence-gated env `SecretSpec`** (= shipped) | buildable now; custody-source upgrade stays a CUT-1 line item |
| Q-D20 | rubric classes 11/12/13 | **adopt all three + forward-plus-one-retro + dedicated adversarial agent** (= shipped) | three orthogonal victim axes; the one pass is the retro coverage |
| Q-D21 | growth posture | **(a) slash-first survivability** (= shipped) | a hard gate freezes the mission on Discord's review queue |
| Q-D24 | concurrency primitive | **(A) name K7 `NATURAL_KEY` + compile fence now** (= shipped) | Gate-V Arm D *live-confirmed* the deathmatch double-write — the class is real; give the golden its mechanism |
| L-21 | old-bot change policy | **freeze-aligned:** old-bot work continues (bugs-first, walk §7.2 lock-in), but any PR that changes behavior a golden captures must **re-capture the affected goldens in the same PR** (checker-advisory first, then CI) | keeps the oracle honest without freezing the live bot |

### F-3 · The layer-taxonomy corrections *(architectural; re-numbers frozen vocabulary)*

**Recommended ruling — four one-line veto items** (evidence + full rulings in §2):

1. **Canonize the Gate-0 K-numbering** (K9 = durability band; the design-spec §9.1 / BUILD-PLAN
   "K9 = kernel/ai · K10 = loops" numbering is retired — all 14 specs' §11 sections are verified
   against the Gate-0 legend).
2. **K10 = the AI invocation kernel** (was "reserved") — the re-homed `kernel/ai` band, with a
   **domain-registered task registry replacing the closed `AITask` enum** and the grounded-answer
   engine hoisted out of the btd6 namespace (§2.4 B-1).
3. **The verification loops become layer V** — a *named* foundational verification substrate
   (parity · grammar-fit · sims · test guild · `verified_live`), outside the boot chain, with its
   own build step (§5 step 11) so the old design-spec-K10 content cannot evaporate (§2.2).
4. **Three under-specified kernel capabilities get named landing steps** (the K-walk's
   missing-layer finds): the **settings-resolution engine** and the **panel/presentation runtime**
   (both in design-spec K7/K8 prose but absent from the S0–S15 PROVIDES lists → widen S8/S9 or add
   an explicit S9b), and the **findings/diagnostics engine** (frozen grammar self-admits
   "not-yet-frozen" → fold at the K5 health leg).

### F-4 · The test-guild full-pipeline driver *(ToS-sensitive)*

**Recommended ruling — the two-lane fidelity model** (source-verified in lane 5; detail in
[companion C](rebuild-test-guild-design-2026-07-06.md) §4):

- **Automated lane:** the **in-process synthetic-gateway technique parity/ already uses** (real
  `parse_message_create` / `parse_interaction_create` → real converters, cooldowns,
  `before_invoke`, error handler; fake HTTP), **extended with a real HTTP boundary for prefix
  commands** so live Discord-visible output exists (the hybrid Arm D itself names).
- **Human lane:** the maintainer (or a *manually operated* low-privilege second account) drives
  slash commands, component clicks, and panels for the `verified_live` sign-off — a human is
  *required* by Q-0234's "self-explanatory" criterion anyway.
- **No user-account automation ever** (ToS-prohibited self-botting), and no bot-token wire driver:
  verified structurally closed — discord.py's library-default `author.bot` guard
  (`ext/commands/bot.py:1413`), disbot's own pipeline drop (`message_pipeline.py:279`), and
  Discord-minted interaction tokens (no bot API can invoke another app's commands). The
  wire-level-live-bot-loop idea doc's coverage claim is **contradicted by source** for passive
  pipelines and unvalidated for slash/components — do not build on it as written.
- Build the **`verified_live` sign-off registry** (zero source implementation today; schema =
  verification-review §3.3) before CUT-1 live testing starts.

### F-5 · Phase-2.5 pass bar + verdict acceptance

**Recommended ruling:** run per [companion D](rebuild-phase-2.5-procedure-2026-07-06.md); pass bar
= **substrate-ON beats OFF on ≥2 of the 3 primary measures with none regressing, and the ON arm's
first session boots inside the ≤7,000-word orientation budget with zero unrecoverable workflow
errors**. **Agents run it; the owner accepts the verdict at (or before) the G1 sitting** — this
reconciles the strategy's "no owner gate" with Gate-V's "owner-run" (O-8). Also formally closes
the strategy-§7 leftover: the A/B target is a **small throwaway repo**, not the full rebuild.

---

## 2. The foundational-layer taxonomy (corrected + complete)

### 2.1 The kernel bands K0–K10 (canonical numbering)

The **Gate-0 numbering wins** (decision D-1): it is newer, verified edge-by-edge against the 14
specs' §11 build-orders, and S0–S15 is written against it. This resolves Gate-V finding **C-5**
(`rebuild-design-spec-2026-07-02.md:1614-1618` vs `phase-b-l0-build-order.md:54-58`). The design
spec's two displaced bands are **re-homed, not dropped** (rows K10 and layer V below).

| Band | Name | Contract (one line) | Build step(s) |
|---|---|---|---|
| **K0** | config + observability + substrate | `preflight()→Config` (import-safe — the live `config.py:19-23` import-time token crash is the anti-pattern), metrics/structured-logging leaf, `IntentSpec`; **plus the repo substrate: substrate-kit bootstrap, control plane (rulesets + OIDC + named gates), CODEOWNERS** | S1 (+ §5 steps 6–8) |
| **K1** | namespace registry | `namespace.validate(snapshot)`, reserve-at-declaration, tombstones + `legacy_reservations.json`, collision = fail **before** boot (zero live code today — the hand-authored `SUBSYSTEMS` manifest is not it) | S2 |
| **K2** | manifest compiler + snapshot | the 9-pass compiler, `*Ref` grammar, `manifest.snapshot.json` + `stable_hash`, recompile-parity boot gate — **the linchpin** (live counterpart: the `grammar_spike` prototype only); **+ the schema-growth ledger + CI checker (§11 A-2)** | S3 (S0 = its amendment registry, pre-Gate-0) |
| **K3** | DB seam + idempotency | `db.transaction()`, data-plane rails, fresh migration runner, `IdempotencyKey`/`once()` (the one add — zero live hits in `disbot/`) | S4 |
| **K4** | event outbox | `DeliveryClass` (canonical home), durable `event_outbox` + atomic claim, `enqueue_audit_action` audit twin (live `EventBus` is in-process only; no outbox code exists) | S5 (lanes registered S6) |
| **K5** | lifecycle + health + poll host | 7-phase lifecycle, `/ready` RUNNING-only + drain, the **one** supervised `PollSupervisor` all poll lanes register on; **+ the findings/diagnostics engine folds here** (F-3.4) | S6 |
| **K6** | authority engine | `resolve_authority` → 10-field `AuthorityDecision`, owner-override-once, `TransparencySink` (+ the pure `outcomes.py` leaf per the 04-wins placement); **+ the role-scoped lane `Lane.ROLE_SET` + channel-access role-sets (§11b A-12, rider R-16)** | S7 |
| **K7** | workflow / compound-op engine | `run()`/`run_ref()`/`apply()`/`preview()` over one `_execute` core, `CompoundOpSpec`/`LegSpec`, central audit row, **`NATURAL_KEY` session concurrency (Q-D24)**, **settings resolution (§4.1–4.3 of the design spec) explicitly in its PROVIDES** (F-3.4), idempotency + audit-completeness fences **(+ the fence's AST complement, §11 A-5)** | S8 |
| **K8** | interaction runtime | the single `resolve()` seam, **6 surface adapters (slash · prefix · fuzzy · component · modal · nl)** — the invocation ladder's dispatch home (the live central typo resolver `utils/command_resolution.py` is K8 material, **not** AI); **+ the panel/presentation runtime (PanelRuntimeView, EmbedFrame, navigation, generated settings panels, help-as-projection) explicitly in its PROVIDES** (F-3.4) **+ the navigation-completeness golden (§11 A-3)** | S9 (+S9b if split) |
| **K9** | durability band | draft pipeline (`sb_drafts`, N-ops-as-N-rows, per-op K7 resume) + due-queue (`sb_due_queue`, `ManagedTaskSpec` Interval/Cron/OneShot/EventTrigger, misfire/catch-up, boot-reconcile, `VersionPolicy`); **+ the user-self-service automation source (§11b A-13: `user_automation:*` producer, quiet-hours/delivery-window + condition-poll trigger via rider R-17, `automation_eligibility` via provisional P-5, category B fenced OFF pending the pricing session)** | S10 |
| **K10** | **AI invocation kernel** *(was "reserved" — F-3.2)* | provider port + adapters (anthropic/openai/deterministic), gateway pipeline (flags→safety→redaction→routing→provider→metrics→degrade, never-raises), redaction, socket-deny eval guard; the **NL front-end** (should-reply policy, decision audit, conversation memory, instruction assembly) terminating in K8's `nl` adapter; the **tool-orchestration machinery** (catalogue structure, scope gating, profile resolver, tool-dispatch loop, plan→execute→verify template); the **grounded-answer engine** hoisted from the btd6 namespace (name-guard, `grounding_format`, `GroundingResult`, verify+regenerate-once loop — projmoon already consumes it cross-domain); a **domain-registered task registry** replacing the closed `AITask` enum | §5 step 12 (after S10, before the L4 ports) |

Strand-3 (specs 10–14: security rubric, data-integrity/repair, credential lifecycle, backup/DR,
platform-governance) rides the frozen grammar across S11–S15 — cross-cutting kernel *facets*, not
new bands. **No new bands** for caching, i18n, cooldowns, backup/DR, audit, migrations, or the
capability catalog — each verified correctly homed or legitimately a declaration-level leaf
(K-walk lane, §8 D-6).

### 2.2 The verification substrate **V** (a defined foundational layer — F-3.3)

The verification/command-probing tooling is a **named foundational layer**, not an afterthought.
It lives *outside* the runtime boot chain (so it is not a K-band) but **every phase gates on it**
— nothing ships without passing through it. Its five organs:

| Organ | What it proves | State at head |
|---|---|---|
| **V-1 golden parity** (`parity/` — 465 goldens; capture/check/coverage) | old-bot behavior = new-bot behavior, red-until-parity. **Drives the full real command pipeline in-process** (real gateway-payload parsing → converters, cooldowns, `before_invoke`, error handler; the only fake seam is HTTP) | built (#1639); depth thin: events 21% · tables 25% · settings 2% (P-5); **not yet wired into any Postgres-serviced CI** |
| **V-2 grammar-fit measurement** (`tools/grammar_spike/`) | the declarative bet holds — **85.26% verified live this session** (81/95 units; as-written 72.6%; conditional on the folded G-1…G-5 families; a hand-classified judgment ledger, so a per-band re-run means *extending the UNITS ledger*, and that classification procedure still needs writing) | built; re-run per port band |
| **V-3 the simulator fleet** (`tools/sim/` 8 + `tools/game_sim/` 2 + the future `sim/` runner + `check_sim_gate`) | arrangement/layout/economy decisions are searched, not guessed | design-time sims live (2 already CI-wired, 3 drift-pinned; per-sim dispositions in §8 D-17); the `sim/` runner + `check_sim_gate` **exist nowhere yet** — built at §5 step 11 |
| **V-4 the test guild + drivers** ([companion C](rebuild-test-guild-design-2026-07-06.md)) | the FULL pipeline **live** (the tier parity can't reach) + a per-subsystem observable home | designed; stands up at CUT-1; two-lane driver model (F-4) |
| **V-5 `verified_live` sign-off** (Q-0222/Q-0234) + Arm-D-style service harnesses | human-tier live co-test ("works · logical · self-explanatory") | pattern proven (Arm D); **registry has zero source implementation** — build to the verification-review §3.3 schema before CUT-1 |

### 2.3 The consumer layers under Sequence C

The frozen L-vocabulary stands (BUILD-PLAN §2): **L1a** settings/diagnostic/help → **L1b**
operator spine → **L1c** presentation (card engine first — *reclassified formalize-not-build, P-6*)
→ **L2** deterministic non-game (economy, inventory, treasury, xp, karma, community) → **essential
L4/L5 platform + control-plane** → **L3 games + growth-L4 as late consumers** — per Gate V's
Sequence-C verdict (the frozen L3→L4/L5 edge is fabricated, verified 3× incl. live; the
game-proved primitives are pulled forward as the five non-game oracles instead, P-4).

### 2.4 The foundational-completeness rulings (deliverable B — evidence-grounded)

**B-1 · AI integration splits at the engine/data seam; the engine is foundational (K10).**
Verified against live source (lane 2a): the provider seam is already a single never-raises
chokepoint (`disbot/core/runtime/ai/gateway.py`; client construction confined to `providers/`);
the NL front-end's policy/audit/memory/instruction-assembly are domain-agnostic resolvers; the
tool-orchestration machinery is generic (scope ranks, budgets, never-widen-authority) carrying
domain *data* (5 of 9+ toolsets are BTD6). Three contaminations must be cut when K10 is built:
the closed `AITask` enum hardcoding domain members (`contracts.py:30-38`) → **a domain-registered
task registry** (the `response_renderer_registry` pattern, already proven next to it); the
hand-branched `_gather_feature_facts` domain if-chain → registry hooks; and the grounded-answer
engine living under `utils/btd6/` while projmoon imports across it → **hoist to K10**. The
knowledge domains themselves (btd6\_\* ~40 services, projmoon\_\* 3, corpora, keywords, ingestion)
stay **L4**. Invocation-ladder placement: rungs 1–2 are **K8** (exact dispatch + the *existing*
central typo resolver `utils/command_resolution.py` — which the conventions doc wrongly says
doesn't exist; source wins, Q-0120); rung 3 (NL→command) **does not exist today** and is
greenfield K8(`nl` adapter)+K10 work, its intent surface generated from the command manifest;
rung 4 exists only as three disconnected precursors — the general goal→draft→preview→accept
engine is new K10+K9 work, not a port.

**B-2 · Automation/scheduling is foundational but NOT a new layer — it is a named spread:
K5 + K9 for the "when", K7 for the "what", spec-06 PRESET drafts for templates; the automation
*feature* is an L1/L2 declaration layer.** Verified (lane 2b): today's bot has **four**
"when-to-fire" mechanisms sharing one "how-to-spawn" primitive — the env-gated-OFF
`AutomationScheduler` (with a latent **NULL-`next_run_at`-means-due re-fire bug** and a
uuid-defeated dedup claim), six `tasks.loop` cogs, ~5 hand-written while/sleep loops, and ~8
in-memory one-shots **lost on every merge=deploy**. The frozen specs already close all of it
(spec 09 retires `automation_scheduler.py`; always-on `PollSupervisor`, durable `sb_due_queue`
with SKIP-LOCKED lease + deterministic dedup + boot-reconcile + `MisfirePolicy`; templates unify
into the PRESET-producer draft lane; multi-step actions are K7 `CompoundOpSpec`s). *(Corrected
2026-07-07, §11b A-13: not quite all — the live substrate's three **condition-poll trigger kinds**
(channel_inactive / setup_readiness_below / binding_missing) and its shipped **quiet-hours**
semantics map to nothing frozen; rider R-17 adds both carriers.)* Two binding
riders: **never carry the "NULL means due" query shape into `sb/`**, and **do not flip
`AUTOMATION_SCHEDULER_ENABLED` on the old bot before cutover** (the latent re-fire path goes live).

**B-3 · The verification substrate is layer V** (§2.2) — with the F-4 two-lane live-fidelity
model and the V-5 registry build as its two open design items.

**B-4 · Missing/mis-placed foundational capabilities found and homed** (lane 2c): the
**settings-resolution engine** (live `get_setting`/`settings_keys`/`settings_registry` machinery —
load-bearing for nearly every subsystem, and port band 1 is *settings*) and the
**panel/presentation runtime** (the live bot's largest interaction layer: `panel_manager`,
`navigation_stack`, `persistent_views`, the 465-golden surface) are frozen as *types* but have
**no landing step** in S0–S15 → named in K7/K8's PROVIDES (F-3.4). The **findings/diagnostics
engine** (8+ live modules) is self-admittedly not-yet-frozen → folds at K5. Checked and
deliberately **not** new layers: caching/read-models (declaration-level `cache_scope`), i18n (the
L-24 copy-resolver leaf), cooldowns (K8 `CooldownSpec` + Q-D29 deferral), audit (K4/K7),
migrations (K3), capability catalog (K6/K1), backup/DR (S14).

---

## 3. The canonical phase arc (two vocabularies reconciled)

The two vocabularies never disagreed on substance — the **planning-phase arc is the expansion of
the strategy arc's "Phase 2 → Phase 3" stretch**. Canonical names = the left column; the old
names stay greppable here and are retired as aliases.

| Canonical phase | = strategy (07-02) | = planning-phase (07-03) | State at head |
|---|---|---|---|
| **P0 · Substrate-kit** | Phase 0 | — | ✅ #1649 (never stamped in the strategy doc — stamped by §9 here) |
| **P0.5 · Golden harness** | Phase 0.5 | — | ✅ #1639 (`parity/`); **telemetry-sidecar capture still open — must run before the old repo is ever frozen** |
| **P1 · Harvest** | Phase 1 | — | ✅ (superseded by the Capstone) |
| **P2 · Design** | Phase 2 | Capstone → **Phase A** (Stages 1–3) → **Gate V** → **Phase B** (per-step plans) | spec ✅ (now superseded-in-part) · capstone ✅ #1674 · Phase-A Stage 1 ✅ / Stage 2 partial (L1a+L1b) · **Gate V ✅ closed 2026-07-06** · Phase B started (the Gate-0 freeze #1716 was designated the first Phase-B plan) |
| **P2.5 · Cold-start proof** | Phase 2.5 | — | ❌ **never run** → companion D (prereq: kit tail ①) |
| **🔒 G1 · The go/no-go sitting** | "owner approval" | "Gate 1" / "the Phase-3 gate" / "Gate-0 ratification" | 🗑 **RETIRED as a blocker by Q-0241** (historical row; no owner sitting required) |
| **P3 · Skeleton** | Phase 3 | Phase C (kernel half), executed as **S0–S15** | not started — **no `sb/` code exists (verified)** |
| **P4 · Port** | Phase 4 | Phase C (port half), **re-sequenced by Sequence C** | not started |
| **P5 · Cutover** | Phase 5 | **Migration** (its own plan) + railway plan §4–6 | not started (CUT-1/2/3, Q-0222) |

Phase A's walk and Phase B's per-step plans continue **inside** the arc, in parallel with P2.5 and
G1 — per Gate V §6 they are not start-blockers; each subsystem needs its walk row + per-step plan
before *its port band*, not before the repo exists.

**Model allocation, re-keyed** (the strategy §3.1 table was keyed to the dead vocabulary; only two
rows remain forward-relevant): **P3 kernel** = Opus/Fable `xhigh`–`max`, one ultracode session per
band; **P4 port** = Sonnet 5 workhorse + Opus escalation + Haiku boilerplate, made safe by V-1
red-until-parity; **P5 cutover** = Opus `high`, single-threaded. Independent review stays a
different model than built it.

---

## 4. The gates (canonical — this list prunes every older gate mention)

The corpus named ~14 gates across four docs with **four different gate sets and one overloaded
name** ("Gate-0" = the *done* grammar-freeze docs pass #1716 **and** the *open* owner ruling).
Canonical de-overload: **"Gate-0" refers only to the (done) docs pass; the owner ruling is part of
G1.**

**Two hard program gates block all new-repo code:** *(⚠ both RETIRED as blockers by the Q-0241 amendment at top — kept below as historical sequencing + rationale, not as owner stop-points.)*

| Gate | What it is | Who clears it | State |
|---|---|---|---|
| **G1 · The owner go/no-go sitting** | ONE sitting: ratify the design spec (§10.2's 14 points, as amended by F-3) **+** the Gate-0 packet rows (F-2 pre-fills) **+** the data contract (F-1) **+** veto-or-bless F-3/F-4/F-5 | owner | ⏳ ready — read §1 |
| **G2 · Phase-2.5 cold-start A/B** | substrate-on/off evidence (offline) | agents run · **owner accepts the verdict** (F-5) | 🟡 **RUN 2026-07-07 (PR #1775) — verdict: FAIL as-tested** (adopt ships the kit *inert*: unrendered templates cost orientation in 3/4 pairs, zero measured benefit). Recommended ruling: fix adopt-renders-what-it-knows + re-run one pair → [report](phase-2.5-cold-start-report-2026-07-07.md) |

**Cleared gates (do not re-open):** "wait for Fable 5" (redeployed 2026-07-01) · the linchpin
commit-gate (#1639 — coverage 96/88/94%, fit 85%) · the memory-system start-gate (#1649, kit
before K0) · **Gate V** (closed 2026-07-06). *The parallel-execution plan's "two gates" were the
middle two — both cleared; that doc's gate vocabulary is superseded here.*

**Later, in-flight gates (not start-blockers):** the three sim "why-it-won" ratifications (P4 —
three *new* sims over the new manifest: hub topology, settings grouping, dense-panel layout; the
existing fleet is precedent, not re-run) · CUT-2 importer dry-run reconciliation review (owner) ·
CUT-3 cutover + rollback-window exit (owner) · the new repo's own six named required CI gates
(golden-parity born-red, `check_compat_frozen`, sim-reviewed-or-exempt, …) which **do not exist
until §5 steps 7/11 build them** · per the standing rules, any per-PR data step a change names.

**Standing constraints (not phase gates):** Q-0213 ask-first `*Delete`/`*Restore` brake ·
`check_phase_gate.py` is advisory-only · L-21 old-bot policy (F-2) guards the oracle during the
whole window.

---

## 5. The start sequence — "to start the new repo, do these N steps"

Ordered; **owner-gated steps marked 👤**. Steps 1–4 are startable **today, in parallel**; nothing
before step 6 touches the new repo.

| # | Step | Who | Notes |
|---|---|---|---|
| 1 | ✅ **Kit tail ① shipped** (Q-0223, PR #1775): re-entrant `JsonStateBackend.transaction` + atomic `apply_review_verdict` | agent | done — 427 kit tests green |
| 2 | ✅ **Phase-2.5 COMPLETE as an experiment** (RUN #1775 FAIL-as-tested → the adopt-renders-what-it-knows kit fix + the T2/T4 **re-run pair** 2026-07-07 → **re-run verdict: overhead still ON-negative; the cold-start *benefit* claim stays unproven** — [report + §5 addendum](phase-2.5-cold-start-report-2026-07-07.md)). The mechanical fix stands (hooks resolve, docs render, cold strict-check green); K0's bootstrap step keeps its role on *invested-adoption* grounds, with the unproven-benefit caveat carried honestly | agent (verdict agent-accepted per Q-0241, flagged ⚑) | done |
| 3 | ✅ **`tools/check_amendments.py` BUILT #1775** (S0's enforcing half; green spot-checked truthful this session, Q-0105) + the #1716 ledger drift fixed #1770 | agent | done |
| 4 | Continue the **Stage-2 walk** (L1c → L5, 33+ rows) | 👤 owner-live | parallel; blocks later port bands only |
| 5 | 👤 **The go/no-go sitting (G1):** read §1, veto/bless, stamp the rulings into the router | owner | the ONE sitting; F-2 rows land as router entries |
| 6 | **Create the repo** (`superbot-next`; empty, private) | agent (coordinator) | **un-gated per the Q-0241 amendment above** — an empty private repo is reversible; no longer behind G1/G2 |
| 7 | **Bootstrap the substrate-kit**: `python3 dist/bootstrap.py adopt` → doc skeletons, decision ledger, orientation-budget checker, namespace/seam checkers, staged hooks | agent | K0's first act; adopt re-proven live this session (17 planted + 14 staged artifacts, `check --strict` clean) |
| 8 | **Control plane**: rulesets + OIDC, the named-gate workflows (incl. `golden-parity` born-red + `check_compat_frozen`), CODEOWNERS, branch protection; 👤 **Railway project `superbot-next`** per [railway plan §4/R-3](railway-setup-plan-2026-07-02.md) (production + shadow, config-as-code, sealed/reference variables — owner pastes secrets, region pins, backups per the Q-D14 ruling, project tokens) | agent executes; owner approves the spend + supplies secrets | PAT machinery never enters the new repo |
| 9 | **Build the kernel S1→S9** (K0→K8 per the [S0–S15 build order](../analysis/rebuild-discovery/foundations/gate-0/phase-b-l0-build-order.md)). **Strand 1 is a near-linear chain** — S8 (K7) consumes K4+K5+K6, so S5/S6/S7 sit ON the chain (the parallel plan's "K4/K5/K6 run concurrently off-spine" is corrected here); the real parallelism lever is fan-out *within* a band. RC-12 (`member_tier`) lands before S9 wires K8 | agent fleet — one ultracode session per band | ~5–8 days; the settings-engine + panel-runtime PROVIDES (F-3.4) land inside S8/S9 |
| 10 | **S10–S15**: K9 durability band, then strand-3 (rubric · integrity/repair · credentials · backup/DR · platform-governance) in parallel | agent fleet | F-3/PG-2 intent posture lands per the Q-D5 ruling |
| 11 | **Wire layer V**: import the parity goldens (`golden-parity` red) into a Postgres-serviced required workflow; build the `sim/` runner + `check_sim_gate` (exist nowhere today; **`check_sim_gate`'s contract is in the design spec, not here — what it diffs, gate semantics, and the per-manifest `sim-optimized \| exempt` declaration live at design-spec §5 ~L992/L1029; build to that, don't re-derive**); build the `verified_live` registry (V-5); **widen parity depth** (events 21% / tables 25% / settings 2% → per-band curated goldens, P-5); write the per-band grammar-spike classification procedure (V-2). **The `sim/` runner is a shared harness** — manifest = search space, candidate generation, rank + `check_sim_gate` drift-pin — hosting **pluggable per-surface scoring oracles**: its first oracle is the **instruction-driven navigation engine** (deterministic label-match user model + optional AI-naive-user; score = task-success-rate / path-length / wrong-turns on "find/do X" — the Q-0235 layout-success idea, powering the hub-topology ratification). It does **not** subsume the other two manifest sims: settings-grouping keeps a scroll-to-coverage-over-the-fallback-DAG scorer and dense-panel an ergonomic-interaction-cost scorer, plugged into the same runner as distinct oracles; the navigation corpus stays **independent** of the NL-router eval corpus (the #1701 Goodhart caution). Also lands here: the **navigation-completeness golden** (drive the generated hub through every declared node + re-render path; assert framework-injected working Back/Home per state + every feature in ≥1 preset — the CI proof of Q-0231). **Also lands here: the A-16 parity-depth floor** — `check_parity_depth` inside the `golden-parity` gate (100% declared-surface-or-exempt at every `pending → ported` flip + post-flip count ratchet; §11b A-16) | agent | the repo is born red on parity, green on everything else |
| 12 | **Build K10 (AI invocation kernel)** per §2.4 B-1 — incl. the **eval harness + socket-deny guard** (the A-17 deterministic gate's machinery) — + stand up the **test guild** (companion C) + build the **tiered V-5 registry** (§11b A-18: human-required tier vs automated tier) + **CUT-1**: the new bot boots container-only on the **test-bot token** into the test guild; live smoke per companion C's per-zone map | agent + 👤 owner walks the `verified_live` items (batched per band per A-18) | CUT-1 is the first live milestone |
| 13 | **Port bands 1–7 under Sequence C** (P4): settings/diag/help → operator spine → economy/inventory/treasury → xp/karma/community → essential platform/control → games late → knowledge domains onto K10. Per subsystem: walk row + per-step plan + manifest (sim-optimized or exempt) + service + goldens green **+ the A-16 depth floor at the flip**. Includes the P-1 atomic-multi-leg contract and P-2 `SettleOnceMixin` retrofit as Phase-B deltas. §11b landings inside the bands: band 1 = guild-restore + the export command (A-15); band 2 = the moderation decide-at-port anchors (A-14); band 7 = the deterministic eval gate per domain (A-17) | agent fleet, claim-per-subsystem | 👤 three sim ratifications land here |
| 14 | **Run the telemetry-sidecar capture on the OLD bot** (the open P0.5 sibling) — before any freeze | agent | capture-before-freeze rule; feeds sim objectives |
| 15 | **CUT-2**: manifest-driven selective import — permission census, importer dry-run reconciliation (**posted as a reaction window, not a pause** — Q-0241: the agent proceeds into *shadow* on its own; the dry-run diff is published so the owner *can* react before CUT-3), then the real import into shadow. **The importer manifest pins column carriage for state co-located in money stores** (streaks/cooldowns — §11b A-20), and a **prod-config census** here conditions the A-20 post-window checklist | agent runs; owner may react | F-1 executes here first (against shadow, never live — shadow-first IS the reversibility, so no approval is waited for) |
| 16 | **Shadow-run window**: goldens + compat scoreboard green against a restored-snapshot DB; exactly one bot writes prod at all times | agent; owner watches the server | |
| 17 | **CUT-3**: freeze old bot → final delta import → **token swap** onto the new worker → bounded **rollback window N=7d** (Q-D15) → old project winds down to an **archived backup**. Riders (§11b): the **A-18 coverage-debt list** (unsigned human-tier `verified_live` rows) publishes in this reaction window; the **A-20 day ~8–10 post-window checklist** runs after N closes; the **A-19 escape-hatch baseline stamps as the permanent year-two ceiling**; verify-boots inherit **spec-13 T-7 containment** (fake-sink egress — overdue durable timers fire once at boot) | agent executes; owner's control = the reaction window | end state: the rebuilt bot in production; old repo = frozen artifact. **Why this step is safe to run un-gated (the honest justification, per the 2026-07-07 final review): NOT because it is "shadow" — CUT-3 is live prod — but because every leg stays reversible while the owner reacts**: the swap reverses by swapping the token back, the N=7d window + the archived backup + the reverse-import valve (F-1/F-2) round-trip the data tier, and nothing is *deleted* until the window closes. This is the Q-0241 reversibility rider doing the work the retired gate used to do; the Q-0213 prod-data brake is satisfied by that same rider, not bypassed |

**The repo-as-artifact framing stands throughout:** the current repo is the *what/why/how* record
(decision logs, rubric, frozen reference, this plan); the new repo is the clean source of truth.

---

## 6. Verification + the test guild (deliverable C — summary)

One correction the lanes forced on the whole verification story: **`parity/` already drives the
full real command pipeline in-process** — real gateway-payload parsing through real converters,
cooldowns, the governance `before_invoke` gate, and the error handler, with HTTP as the only fake
seam (`parity/README.md:11-18`, `boot.py:272/292/316`; it bypasses the `author.bot` guard
legitimately by marking synthetic authors non-bot, `world.py:298`). So the fidelity gap is **live
(real-HTTP / real-Discord) exercise**, not pipeline coverage — which the test guild + the F-4
two-lane driver model close. The full design — 9 zones, ~40-channel manifest, per-zone
exercise/proof map, CUT-1 mapping, and the driver architecture — is
**[companion C](rebuild-test-guild-design-2026-07-06.md)**.

## 7. Phase-2.5 made runnable (deliverable D — summary)

Everything needed to *run* the A/B exists (one-step adopt proven live; the kit ships its own
measurement surfaces — KPI metrics, economy gauges incl. the ≤7,000-word orientation budget,
session orchestration). What was never specified — target, arm protocol, measures, pass bar,
blinding, artifact home, the operational meaning of "cold" — is now specified in
**[companion D](rebuild-phase-2.5-procedure-2026-07-06.md)**: a local throwaway repo, N≥3 paired
same-model sessions over a fixed task list, three primary measures (orientation footprint vs
budget · steering/wrong-turn count · workflow-correctness + task completion), Opus-judged with a
written rubric, artifact = `docs/planning/phase-2.5-cold-start-report-<date>.md`. Prereq: kit
tail ① (§5 step 1). Pass bar + verdict acceptance = flag F-5.

---

## 8. Decisions log (Q-0240 — every call this consolidation made)

| # | Decision | Options weighed | Rationale (one line) |
|---|---|---|---|
| D-1 | Canonical K-numbering = the Gate-0 legend | design-spec §9.1 numbering · Gate-0 legend · hybrid | all 14 specs' §11 build-orders verified against Gate-0; reverting invalidates every spec-internal K-ref |
| D-2 | K10 = AI invocation kernel | leave "reserved" · K10 · a "K11/strand-4" band | AI's runtime seam boots with the bot (a genuine K-band); "reserved" was a hole; K11 adds a band for no gain |
| D-3 | Verification loops = layer V, not a K-band | reclaim K10 for loops (K-walk lane's letter) · V layer with a named build step | the loops are repo-level CI/tooling outside the boot chain; V honors the lane's substance (nothing evaporates — §5 step 11 builds it) while keeping K-bands runtime-only |
| D-4 | AI engine/data split per §2.4 B-1 (registry replaces `AITask`; grounding engine hoisted; `command_resolution.py` → K8; ops surfaces mid-layer) | keep AI wholly L4 · move all ai_* foundational · split at the engine/data seam | source shows a domain-agnostic chokepoint carrying domain data; the registry pattern already exists next to it |
| D-5 | Automation = named spread (K5+K9 when · K7 what · PRESET templates · feature L1/L2); adopt spec-09's contract; riders: never carry NULL-means-due; don't flip the old bot's scheduler env-flag | new K-band · fold into K5 alone · the spread | frozen specs 06/07/09 already decompose it correctly; a new band would duplicate spec 09 and reopen the grammar |
| D-6 | Missing-layer finds homed: settings engine → K7/K8 PROVIDES; panel runtime → K8/S9b; findings engine → K5; **no** new bands for caching/i18n/cooldowns/audit/migrations/capability/backup | per-capability | the three have live load-bearing counterparts + frozen types but no S-step; the rest verified homed or leaf-level |
| D-7 | One merged phase arc (P0…P5 + Phase A/B/C inside P2/P3-4); old numberings retired as aliases | keep both vocabularies · merge | both are half-dead at head; only the merged arc reflects verified state |
| D-8 | Gate de-overload: "Gate-0" = the done docs pass; the owner sitting = **G1**; A/B = **G2**; publish the full census (§4) so pruned gates are visibly retired | leave overloaded · rename | two different things shared one name across four docs — the corpus's top confusion source |
| D-9 | Gate-0 pre-fills as in F-2, incl. Q-D5→DEGRADE (the one divergence), Q-D15 N=7d, L-21 = goldens-fresh-or-re-captured | bless-all-shipped · per-row judgment | only Q-D5 had recommendation≠default; N and L-21 were the two blanks |
| D-10 | Data contract = fresh-0001 + importer + owner dry-run reconciliation; carry-the-chain fallback (F-1) | importer · carry-the-chain primary · fresh-start | already specified + Gate-V-verified; alternatives destroy user trust for no savings |
| D-11 | Test-guild fidelity = the two-lane model (F-4); no user-account automation; no bot-token wire driver; build the `verified_live` registry first | test-mode allowlist seam (my draft) · wire-level driver (idea doc) · two-lane | lane 5 source-verified the wire-level idea's passive-pipeline claim false and interactions structurally closed; parity's technique already proves the automatable tier |
| D-12 | Test-guild layout = 9 zones / ~40 channels, games get per-game channels, guild builds out in port-band order (companion C) | flat guild · zone model | observability per subsystem is the point; channel-scoped games need isolation |
| D-13 | Phase-2.5 protocol + measures + pass bar per companion D; agents run, owner accepts (F-5) | owner-run · agent-run silent · agent-run + owner-accept | reconciles strategy "no owner gate" with Gate-V O-8 "owner-run" without blocking the work |
| D-14 | Kit tail ① scheduled as step 1; the brief's "ONE open kit item" framing corrected to "one proof item (A/B) + one code item (tail ①)" | ignore (brief's framing) · fold | Q-0223 (owner-decided) + source verification win over the brief (Q-0120) |
| D-15 | Doc dispositions per §9 | delete · supersede-in-part markers | link-don't-delete (brief), and frozen docs are overlaid, never edited |
| D-16 | Numeric bases stated once: command surface = 484 records (C2 scanner) for *surface* work, 271 rows (BUILD-PLAN) for the *capability corpus*; kit tests = **422**; settings keys = 120 | reconcile everywhere · state once here | the drift is benign snapshot lag; one canonical statement stops the re-litigating |
| D-17 | Sim dispositions: grammar_spike re-run per band; help_menu_grouping + settings_order stay living CI checks; creature/mining **+ role_menu** keep their drift-pins *(corrected 2026-07-07 — the final-review fleet audit found `test_role_menu_layout_sim.py::test_inventory_matches_the_live_builder` is a live CI drift-pin, matching §2.2's "3 drift-pinned" count; the original row mis-filed role_menu as archived)*; claim_layout/casino/fishing/setup_wizard archive as decision-records; retention_policy re-run at implementation time, never CI | per-sim | wiring only where a sim guards an *ongoing* invariant; the fleet lane verified current wiring state |
| D-18 | Model allocation re-keyed (§3): only kernel/port/cutover rows carried forward | keep table · re-key | the old table was keyed to the dead vocabulary and Gate V ran on a different roster anyway |
| D-19 | Start-sequence concurrency corrected: S5–S7 sit ON the strand-1 chain (S8 consumes K4–K6); parallelism = within-band fan-out | carry the parallel plan's claim · correct | the edge-verified build order contradicts the parallel plan; floor math must be honest |
| D-20 | Fix the #1716 ledger drift (claims a "uniqueness checker" that doesn't exist) on sight | defer to recon pass · fix now | Q-0166: spotted drift is fixed now; the recon failsafe is not a licence |
| D-21 | (Session, pre-brief) CI slug-checker fix: drop the bogus `--strict` from the workflow + a workflow↔script flag-parity test | patch the script to accept `--strict` · fix the invocation | the script's contract was right; the workflow passed a flag that never existed, so the advisory checker never ran |

## 9. Superseded / disposition of the scattered docs

| Doc | Disposition |
|---|---|
| [`rebuild-planning-phase-2026-07-03.md`](rebuild-planning-phase-2026-07-03.md) | **Superseded by this plan** (§3 arc + §4 gates absorb it; its Phase-B template rules carry forward unchanged) |
| [`fresh-rebuild-strategy-2026-07-02.md`](fresh-rebuild-strategy-2026-07-02.md) | **§3 arc + §3.1 model table superseded** (this §3); §1 verified baseline, §4 design principles, §5 kit-improvement notes, §6 external findings stay reference |
| [`rebuild-parallel-execution-plan-2026-07-02.md`](rebuild-parallel-execution-plan-2026-07-02.md) | **Superseded** (gate vocabulary → §4; concurrency claim corrected by D-19); §1 velocity baseline stays citable data |
| [`rebuild-design-spec-2026-07-02.md`](rebuild-design-spec-2026-07-02.md) | **Keep-live with supersede-in-part stamps:** §9.1's K9/K10 + §9.2's port order → this §2.1/§2.3 + S0–S15 + Sequence C; §2's grammar → **the Gate-0 frozen grammar + 14 specs win where they differ** (the two-frozen-grammar-homes hazard, closed); §10.2 ratification list stays the G1 payload as amended by F-3 |
| `NEW-BOT-BUILD-PLAN.md` + `FINAL-REVIEW.md` | **Frozen reference** (never edited; overlaid by Sequence C + P-6 reclassifications) |
| Gate-0 packet + S0–S15 build order + `frozen-l0-grammar.md` | **Keep-live** (the L0 source of truth; F-3.4's landing-step widenings are the one delta) |
| [`railway-setup-plan-2026-07-02.md`](railway-setup-plan-2026-07-02.md) | **Keep-live** (the P5/Migration Railway arm, referenced by §5 steps 8/15–17) |
| [`GATE-V-SYNTHESIS.md`](../analysis/rebuild-discovery/gate-v/GATE-V-SYNTHESIS.md) + corrections doc | **Frozen evidence** (P-1…P-9 absorbed into §5; O-1…O-8: O-3/O-5/O-6 resolve inside the Phase-B plans named there, O-1/O-2 inside the P-1 contract, O-4 inside spec 08, O-7 stays a router DISCUSS, O-8 = G1/G2) |
| [`rebuild-newrepo-start-fable5-ultracode-brief-2026-07-06.md`](rebuild-newrepo-start-fable5-ultracode-brief-2026-07-06.md) | **Executed** (this doc + companions are its output) |
| [`next-session-priority-2026-07-05.md`](next-session-priority-2026-07-05.md) | **Superseded by §5 steps 1–4** (same recommendation, now sequenced) |
| [`wire-level-live-bot-loop-2026-07-02.md`](../ideas/wire-level-live-bot-loop-2026-07-02.md) (idea) | **Contradicted-in-part by source** (F-4): keep as idea history; do not build as written |

## 10. Evidence base

Firsthand reads: the Gate-V synthesis + corrections, strategy, planning-phase, Gate-0 packet +
S0–S15, design-spec §9/§10, parallel-execution, railway, handoff §5.B(-addendum), BUILD-PLAN,
`rebuild-amendments.yml` (+ `tools/check_amendments.py` verified absent), `parity/` + sims on
disk. Seven review lanes (Fable-5 sub-agents, 2026-07-06) verified the rest against live source
with `path:line` citations — substrate-kit (adopt executed live in a scratch dir) · AI seam ·
automation · K0–K10 walk · plans/gates census · simulators (grammar-spike fit recomputed live:
85.26%) · test infra (author.bot guard traced to discord.py `ext/commands/bot.py:1413` +
`message_pipeline.py:279`). Where any lane and a planning doc disagreed, source won and the
disagreement is recorded here (Q-0120).

## 11. Final-review amendments (2026-07-07 — the A–H review's folds; full evidence in [`rebuild-final-review-report-2026-07-07.md`](rebuild-final-review-report-2026-07-07.md))

Folded per Q-0241/Q-0172 (build/decide freely, flag it). Each is a named landing so it cannot
evaporate; §8-style provenance in the report's decisions log.

| # | Amendment | Lands at |
|---|---|---|
| A-1 | **Phase-2.5 closed**: the adopt-renders-what-it-knows kit fix shipped (derived slots → provisional interview answers; loud UNRENDERED banner; vendored `bootstrap.py` so staged hooks resolve in-repo; 432 kit tests) + the T2/T4 **re-run pair** — see the G2 report's re-run addendum | §5 step 2 ✅ |
| A-2 | **Schema-growth ledger** (Q-0219 second-consumer rule, mechanically enforced): every field added to the manifest grammar's declaration schema mints a same-PR ledger entry (field · the ≥2 consuming manifest paths · the rejected tier-3 alternative); a CI checker diffs the grammar's field set against the ledger — no entry or <2 consumers fails the build (enforce-don't-exhort, Q-0132) | K2 row / S3 |
| A-3 | **Navigation-completeness golden** (Q-0231 Back+Home guarantee as CI) — text now in §5 step 11 | K8 / step 11 |
| A-4 | **Unified layout-success sim** folded as the `sim/` runner's first pluggable oracle (NOT a subsume-all engine) — text now in §5 step 11; `check_sim_gate` builds to the design-spec §5 contract | step 11 |
| A-5 | **K7 audit-fence AST complement**: the `audit_completeness` fence trusts the declared `effect` field (never an AST); add its AST complement — a body-scan verifier that a unit's declared `effect` matches what it actually writes — and **extend the S11 `ChannelEmitter` egress fence from `channel.send` to raw Discord state mutations** (`channel.edit`/`member.ban`/`add_roles`). Current-repo prior art: `check_audit_seam`/`check_deferred_recovery` (#1747/#1748, advisory) | K7 PROVIDES + S11 |
| A-6 | **Off-Discord surface disposition** (was unhomed): repoint `scripts/export_dashboard_data.py` (feeds `botsite/` + the dev dashboard by AST-parsing the OLD repo — both die at cutover otherwise) at the new repo's manifest + release/coverage stores as a **band-13 manifest-consumer deliverable**; the public changelog doubles as the **CUT-3 user-comms face** ("what changed / what to test"). An owner-facing progress dashboard stays an open fork on this lane | step 13 + step 17 |
| A-7 | **In-server release→test→verify loop, the un-covered 3 of 4 parts**: a release **announcer** (manifest × changelog, release-triggered), a **per-command usage-coverage oracle** ("changed since vN but not exercised since" — a layer-V organ complementing parity), and a **test/debug mode** riding K7's existing `WorkflowContext.test_mode`. (Part 4, explain-then-approve, is already V-5's UI.) | walk rows + step 13 + layer V |
| A-8 | **Background-obligation landings the census found homeless**: the **media purge loop** (Q-0099 privacy obligation — named `ManagedTaskSpec` consumer + `StoreSpec.retention` on the youtube-cache store, twin of the already-named health loop); **role_grants expiry sweep** (privilege-retention — the reference temp-ban/mute durable OneShot consumer); **session_gc TTL sweep** (data-minimization — named DURABLE recurring `ManagedTaskSpec`); the **WebhookReporter operator-alert feed** (startup/shutdown/cog-fail/task-died embeds) lands as a K5/observability **operator-alert sink spec carrying its `redact_text` secret-redaction obligation** | K9 (spec-09) + K5 |
| A-9 | **Setup-wizard hardening of the plan** (the review confirmed the brief's concern): (1) promote walk row 5a to a first-class `setup` roster line — the wizard lifecycle (sections registry → recommended-ops → customize → preview → apply → audit), the quick/essential presets, and the AI advisor each carry their row-5a KEEP verdicts here so none rests on a side clause; (2) **freeze G-19 WizardSectionSpec at the Gate-0 registry** (today `pending-gate-0, spec_ref: null`) and **widen its consumers from [cleanup, role, ticket] to all 10 live `views/setup/sections/*` registrants**; (3) **the draft-lane fork is decided as: the K9 kernel draft pipeline ships as specced (spec-06 — many producers need it), while the setup *feature* folds into Essential's direct lane per row 5a — the two frozen docs are reconciled by K9 keeping `Producer.HUMAN_SETUP` reserved but initially unconsumed**; `setup_diagnostics.staged_repair_ops` re-homes onto the surviving draft lane in the same band (flagged ⚑, vetoable) | step 13 band 1 + Gate-0 registry |
| A-10 | **Companion C freeze note**: the interaction-token constraint was validated against official Discord docs 2026-07-07 (Ed25519-signed webhook delivery / Discord-minted tokens / no cross-app invocation endpoint; user-installable apps + Components v2 don't change it) — lane B's scope is final | companion C §4 |
| A-11 | **hermes `/dispatch` disposition made explicit**: the owner's 2026-07-05 drop covers the *surface*; the underlying capability (owner → autonomous work-order) is deliberately **not reconstituted in the new bot** — it lives in the agent-workflow layer (routines / Projects coordinator), not the bot. Recorded so the census stops re-finding it | §9-adjacent (this row) |

**Deliberately NOT folded** (rationale in the report): `check_doc_cites.py` (current-repo doc hygiene — routes as its own idea/PR, gates nothing here); Projects-EAP as coordinator (the plan stays product-agnostic; a thin wiring note lands on §5 if the owner accepts the EAP); C-7 one-description-surface (already structurally covered: K2 manifest + help-as-projection + manifest-generated intent surface); a standalone START-HERE index (this plan + §9 already are it).

### §11b. Idea-consolidation amendments (2026-07-07, second batch — the four owner captures + the §3.C re-verify; full evidence in [`rebuild-idea-consolidation-report-2026-07-07.md`](rebuild-idea-consolidation-report-2026-07-07.md))

Folded per Q-0241/Q-0240 by the idea-consolidation session (9-lane source-verification fan-out;
decisions log + veto list in the report). Grammar-touching rows minted their registry IDs
(**R-16, R-17, P-5**) in `rebuild-amendments.yml` in the same PR — the owning-spec + Gate-0
freeze edits execute at each row's named build step, per the R-1…R-15 mint-now/freeze-at-fold
convention.

| # | Amendment | Lands at |
|---|---|---|
| A-12 | **Role-scoped authority lane (K6)** — the 2026-07-07 owner gap, confirmed at both layers (no live path and no frozen primitive expresses "only role X in channel Y" or "only role X may use feature Z"; K6 is unbuilt and on the strand-1 chain, so this is the cheapest moment the primitive will ever have). ONE amendment, two additive legs, minted as **rider R-16**: (1) **`Lane.ROLE_SET`** alongside CAPABILITY/TIER with the namespaced ref form `role:<binding_name>` — classified by prefix *before* the dot rule so the classifier stays total; refs name a **declared role binding** (BindingKind.ROLE + multiplicity, already frozen), never literal role IDs (specs are guild-agnostic); `AuthorityRequest` + spec-02 `ActorRef` gain `role_ids: frozenset[int]`, riding the still-pending RC-12 member_tier seam batch (S9 absorption); `AuthorityDecision` stays 10 fields; (2) an optional **per-channel role-set constraint on the channel-access policy** — NOT a 4th AccessMode (the three shipped value strings stay verbatim; usable under ALL_CHANNELS); new detail token `role_not_held`. The lane must express **both allow-sets and quarantine/deny-until-role** (A-14's join-verification gate is its first consumer). Interaction-time re-check is inherited structurally (K8 no-skip resolver + `re_check_actor`; the adapter derives role_ids fresh per interaction). The K6/S7 fold executes the R-16 spec-04 + Gate-0 freeze edits and lands **R-2 + R-16 together** (the classifier is amended once). **Kill note:** the live bot's vestigial, never-activatable role-override plumbing (`PolicySource.ROLE_OVERRIDE`, `_guild_has_role_overrides`) is NOT ported. The live-bot convenience half (`!channel restrict <channel> <role>` over the existing overwrite plumbing) is separable → live-bot backlog; the new-bot equivalent rides G-18 at the channel port band | K6/S7 (+ S9 RC-12 batch) |
| A-13 | **User-self-service automation scheduler (K9)** — owner-proposed foundational primitive (guardrailed, unlockable per-user recurring automations). Shape: a user-scoped task source on K9's due-queue — reserved K1 namespace `user_automation:*` + a per-user **domain store** (participation side; `data_class=MEMBER_ID`, so erasure/guild-leave reclaim ride the S11 walk — no `TaskScope.USER`, no `sb_due_queue` schema change, no Producer-enum change) whose **producer** arms DURABLE timers — the spec-09 §5 automation_rules pattern. One manifest field — **`automation_eligibility {none \| notify_only \| action}` + `min_interval_s`** (Group-1 routable-field pattern; category-B target = `IdleAccrualSpec.collect_workflow`, already declared transactional+idempotent) — minted **provisional P-5** (ratify_when = second ported consumer; A-2 ledger entry at build time). Kernel guardrails at the producer/arm seam: interval-floor fence; per-user active-automation cap (the spec-10 **PER_ACTOR_QUOTA** socket); per-user timezone + **quiet-hours/delivery-window** as a ManagedTaskSpec field (the one live scheduler behavior with no frozen carrier; skip-vs-defer × MisfirePolicy pinned at the fold); delivery exclusively via the frozen AT_LEAST_ONCE outbox path (category-A fires need zero new machinery). **Category B (auto-acting) ships structurally reserved but OFF**: a compile fence makes `action` eligibility a SEMANTIC_VIOLATION until the dedicated pricing session mints its ruling Q — the A-9 reserved-but-unconsumed pattern; the split is verified uncoupled (the economy engine ports at band 3, after K9 at step 10, so K9 cannot stall on economics and the pricing session cannot be forced early). Unlock economics ride Q-0039's **earned-track** allowance (not the cosmetic clause); automation capability is **never** donation/real-money purchasable. **Authority rider (closes the A-12 × A-13 interaction):** user-scoped fires carry the **creator's ActorRef and re-resolve K6 at fire time** — never the SYSTEM_ACTOR scripted bypass (which stays correct for system tasks); category-B additionally re-checks unlock at fire time. **TriggerKind rider (R-17):** a condition-poll trigger kind is added — the live substrate's channel_inactive / setup_readiness_below / binding_missing kinds map to nothing frozen (§2.4 B-2's "the frozen specs already close all of it" is corrected accordingly), and it is the natural carrier for category-B "check the chicken farm" asks; category-A wording stays trigger-agnostic (EventTrigger may serve some cases better than polling). **Pricing-method rider (owner ruling Q-0243, 2026-07-07):** the dedicated pricing session decides via a **dedicated simulation** (V-3 sim-decides-design pattern: automated-vs-manual player expected value over time per candidate pricing shape; the price is the sim's output, drift-pinnable — never a guessed number) | K9/S10 + step 13 consumers |
| A-14 | **Moderation decide-at-port anchors (band 2)** — elevated thin (named so they cannot evaporate), NOT as new committed scope: (1) the **join-verification gate** is decided alongside walk row 9's already-committed quarantine build — same join-defense family, same audited system-actor role seam, G-1 listener + K9 durable OneShot; **first consumer of A-12's role lane** (deny-until-role); MUST keep the Q-0111 zero-PII/no-external-call posture (**button-verify, never a third-party CAPTCHA**); (2) **ban-appeal intake** is decided alongside walk row 6's already-committed case/appeal design, with the banned-user (non-member) **DM-intake surface question explicitly named** there (K5 admission owns the DM leg; the live ticket system is guild-only); (3) **trigger→response stays backlog** — a full prior design already exists (`community-platform-features-2026-06-12.md` §4, Roadmap Someday) and G-11 is minted pending; nothing can evaporate | step 13 band 2 (walk rows 6/9/14) |
| A-15 | **Privacy export + per-guild config backup/restore** (the two adjacent 2026-07-07 captures — both fold; neither widens S14): (1) **S11's PROVIDES widens with `run_export`** — the read-only twin of `run_erasure` over the SAME compiled `data_class != NONE` StoreSpec slice (completeness inherited from `check_data_lifecycle` by construction; no new grammar field → no A-2 entry; one audited export event; post-erasure **tombstone-ordering** semantics stated). The user-facing command (JSON delivery, `cost_posture`/`quota_ref` throttle — same-step S11 machinery — cross-guild scope, GDPR Art. 15(4) third-party filtering) lands as a step-13 consumer. **Shared fix:** both walks gain the **account-level cross-guild iteration** the single-guild `run_erasure(guild_id=…)` signature currently lacks (a GDPR request is account-level). (2) **Guild-config backup/restore is explicitly NOT S14** (whole-DB DR only, verified) — it lands at step 13 **band 1** as a **spec-06 draft-lane consumer**: snapshot = manifest-driven read of per-guild explicit setting rows + binding rows (design-spec §4.1/§4.5); restore = a draft over the reserved **`Producer.IMPORT_REPAIR`** (or PRESET) → DraftPreview diff → derived Accept → per-op idempotent K7 apply — audited/previewed/reversible entirely on existing machinery; converges with the guild-template idea (one desired-state model serves both). **One-inventory rule:** export, erasure, the CUT-2 importer manifest, and guild-restore all walk the same compiled store inventory — build it once | S11 + step 13 band 1 |
| A-16 | **Parity-depth floor** — the plan's own #1 risk (layer-V thinness at the moment the human gates retired) hardened from a discipline commitment into machinery (Q-0132): **`check_parity_depth`** lands **inside the existing `golden-parity` named gate** (no 7th gate), DB-free (reads golden JSON + the manifest snapshot + `parity.yml`, which does not exist yet — adding its depth section now costs nothing): (1) **floor at the flip** — flipping a subsystem `pending → ported` requires **100% declared-surface touch coverage** (every manifest-declared EventSpec / StoreSpec table / SettingSpec key exercised by ≥1 golden) **or a per-surface `exempt: <reason>` row** in parity.yml (the `_sweep_skips` honesty pattern; parity/ is CODEOWNERS-owner-reviewed; exemption reasons must cite a COVERAGE.md-style reason class, never a bare "flaky"). 100%-or-exempt beats any X%: per-subsystem denominators are 1–5 items so percentages degenerate, and the manifest is the floor-setter — no arbitrary number; (2) **count-ratchet after the flip** — covered-surface counts never decrease, and newly declared surfaces arrive covered-or-exempt in the same PR; (3) **kernel/governance-owned surfaces** (~11 of 28 live event prefixes) get their own K-band-golden coverage home so they don't silently escape every band's floor; (4) the design-spec §10.1 per-flip coverage **note** (uncovered *flows*) stays as the judgment layer — the floor is a floor, not the definition of depth; P-5's word "curated" stands. **Band-declared targets rejected:** under never-wait the declarer and the satisfier are the same unsupervised agent — self-grading. Built once in the new repo against manifest denominators (exact), not retrofitted onto the current repo's heuristic ones | step 11 + design-spec §6 gate 5 |
| A-17 | **Knowledge-domain eval gate for port band 7 — HYBRID, deterministic tier REQUIRED**: band 7's per-domain exit criterion becomes "**eval_suite gate green (deterministic)**" — the domain's `EvalSuiteSpec` corpus runs under the K10 deterministic provider + socket-deny inside the required code-quality gate, asserting (a) every probe's answer-bearing fact grounds through the real context builder + every forbid-string absent; (b) every rubric-asserted number re-derives from the domain dataset (the anchor gate; content-version hash binds data bump ⇒ golden bump); (c) the verify + regenerate-once + refusal loop passes an injected-hallucination pin end-to-end; (d) the coverage ratchet + ≥10-probe corpus floor holds. `KnowledgeDomainSpec.eval_suite` is already a frozen [S] field, so a domain without a corpus fails manifest-validate. BTD6 imports its existing 16-probe grown-from-real-misses corpus; **projmoon must mint one** (it has none today — a named band-7 deliverable, or the gate is a one-domain gate wearing a two-domain name). The harness lands in **K10 (step 12)** per design-spec §9.1. **Fresh semantic grading (llm_judge) stays advisory** — a required live-judge gate is both operationally flaky (judge-outage⇒FAIL, provider-degrade⇒FAIL) and **forbidden by the frozen design-spec §8 Q9 socket-deny decision** — but becomes **mandatory-to-RUN** (not to pass) at band-7 completion and pre-CUT-1/CUT-3, scorecard tracked against a pinned baseline, loud flag on drop. Honesty note: three deterministic eval layers already run in *today's* required CI — this row mostly prevents a regression, since parity goldens capture only the AI path's deterministic denial and prove nothing about generative answers. Corpus independence per the #1701 Goodhart caution holds (knowledge-QA ≠ NL-router ≠ navigation corpora) | step 12 (harness) + step 13 band 7 (gate) |
| A-18 | **The human `verified_live` lane named as the real pacing + coverage item** (restores final-judgment-fable5 finding #8 — "the owner is the plan's serial bottleneck and nobody did the arithmetic" — which the consolidation dropped; the ~2-week floor is agent-velocity math and never budgeted human verification). The honest surface: **~150–250 human click-through units** (73 slash + 64 persistent custom_ids + panels/modals; × the Q-0234 4-path protocol ≈ 210–220 scenario rows ≈ 15–30 h serial if big-banged). Package: (1) **tier the V-5 registry** — a human-required tier (the Q-0234 judgment + the A-10-frozen automation-unreachable surfaces) vs an automated tier (the 406 prefix commands via lane A + parity replay) — one schema field, costless before CUT-1, expensive after; (2) **batch lane-B walks per band** riding companion C's zone build-out (~15–30 min/band × 7 bands), never a pre-CUT-3 backlog; (3) **CUT-3 debt disposition** — under silence=consent, unsigned human-tier rows are **published as a named coverage-debt list in the CUT-2/CUT-3 reaction window**, never silently dropped (reconciles never-wait with verification-review §4.6; ⚑ the owner may instead want human-tier rows to hard-block CUT-3); (4) **capability-claim correction** ⚑ — Q-0241's parenthetical "an agent can now drive all commands — slash, prefix, components — in a live bot session" contradicts the same-day source-validated + frozen A-10 constraint (agents drive prefix live; slash/components only in-process pipeline-true; the human lane is the only live slash/component driver). The frozen constraint wins per Q-0120 at citing sites (the owner briefing is corrected in this PR); the router parenthetical itself is flagged for the owner rather than edited. Delegation ambiguity (Q-0222 "owner sign-off" vs Q-0234 "a human"; may a delegated alt-account operator sign?) is flagged as a genuine owner-intent question. **RESOLVED by owner ruling Q-0244 (2026-07-07):** slash/component surfaces count as **verified when their prefix twins pass live agent testing + the slash path passes the in-process pipeline-true replay** — no separate human click-through required for sign-off; the owner **flags dysfunctional slash commands reactively** (bugs-first) as he encounters them; **nothing in the human lane blocks CUT-3** (the debt-list model is confirmed; the human tier shrinks to the optional Q-0234 judgment walks at the owner's leisure; Q-0222's per-command one-by-one sign-off is superseded-in-part). The A-10 capability *fact* stands (agents still cannot drive slash/components live) — only the verification *requirement* changed, which moots the IC-13 wording conflict operationally | V-5 (step 12) + steps 13/15–17 |
| A-19 | **The escape-hatch ratchet wired, hardened, and made permanent** (the ratchet-permanence probe found worse than suspected: the design-spec §2.9 ratchet checker has **no landing step anywhere** — K-bands, S0–S15, step 11, and Gate-0 all omit it, so as the plan stood it would silently never be built; and design-spec:75 *declined* a reviewer's per-subsystem manifest budget on the premise that this checker enforces the same thing): (1) **`check_escape_hatches`** is a named deliverable **inside the `manifest-validate` gate** (snapshot-derived validator family; no 7th gate), landing at **K2/S3 with the compiler** — required CI from the first kernel PR **through post-cutover, no expiry**; invariant: every compiled surface unit is tier-1/2 or a tier-3 registration with a non-empty `justification`; `domain/<x>/ui/` modules unreachable from a registered ref fail; (2) **semantics hardened** from §2.9's "acknowledged in the PR" (mechanically undefined) to the proven A-2 ledger pattern — the generated escape_hatch_report is diffed against a **committed pinned baseline** (per-subsystem tier-3 **count** + repo total; counts, not share — share is gameable by denominator stuffing); any rise fails CI unless the same PR updates the baseline with a ledger entry (what grew, why, the rejected tier-2 alternative); reductions auto-tighten one-way; (3) at **CUT-3 the baseline stamps as the permanent year-two ceiling** (the post-parity reduction bands then ratchet it down) — this is what stops year-two feature work eroding back toward the smeared-file pattern; (4) consolidation gaming is bounded by the §1.5 complexity budget (the pair closes the loop); the baseline file joins the CODEOWNERS owner-review set; **V-2 (the 85.26% hand-judgment fit ledger) retires at cutover as specced** — the mechanical tier-3 count is its permanent successor (stated here so nobody later hunts for a missing "fit gate"). ⚑ strengthens owner-ratified §10.2(4) semantics — vetoable | K2/S3 + §4 gates |
| A-20 | **N=7d affirmed; targeted post-window checklist + importer column pin** (the cadence probe, grounded in real cadences, not hypotheticals): no live game/economy system has a weekly-or-longer bot-side cycle — the weekly automation templates are dormant (scheduler env-gated OFF + the §2.4 B-2 rider keeps it off through cutover) and BTD6 CT weekly is external read-only; the true >7d-latency mechanisms (temp role grants ≤1y, 30/90/365d time tiers, karma's configurable ≤7d pair cooldown) are all forward-fixable/re-derivable — **extending N buys nothing, and a late rollback destroys more than these bugs cost**. Instead: (1) CUT-3 gains a **day ~8–10 post-window checklist** — temp-role expiries that fell inside the window revoked on schedule (grant rows vs audit rows), time-tier grants continuing, and (only if the scheduler was enabled post-cutover) each weekly rule fired exactly once — conditioned on a quick prod-config census at CUT-2; (2) the CUT-2 importer manifest gains **one line pinning column carriage for state co-located in money stores** (`economy.daily_streak`/`last_daily`/`daily_count`, karma cooldown timestamps): spec-13's aggregate upsert leaves column scope unstated and a day-1 streak reset is the likeliest visible import bug (belt-and-suspenders if F-1's "balances" is read row-inclusive — flagged, cheap either way); (3) the CUT-3 runbook inherits **spec-13 T-7's containment** — a restored/imported `next_run_at` fires every overdue durable timer once at boot, so egress is fake-sinked during verify-boots | steps 15/17 |

**Deliberately NOT folded (this batch;** rationale in the report**):** a live-LLM-judge *required* gate (forbidden by frozen design-spec §8 Q9; the deterministic tier is the required half); `TaskScope.USER` (domain-store identity + `data_class=MEMBER_ID` reclaim is smaller and rides the S11 walk); extending the Q-D15 rollback window (see A-20); trigger→response elevation (backlog with an existing design, see A-14); the live-bot `!channel restrict` convenience command (live-bot backlog — value decays at CUT-3; see A-12).
