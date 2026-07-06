# GATE-V-SYNTHESIS — the reconciled verification-fleet verdict (2026-07-06)

> **Status:** `plan` — **Arm Σ**, the final Gate V synthesis (Q-0234). Reconciles the four verified
> evidence arms into one verdict + a Phase-B punch-list. Built on the verified evidence layer
> [`../../../planning/rebuild-gate-v-findings-corrections-2026-07-06.md`](../../../planning/rebuild-gate-v-findings-corrections-2026-07-06.md)
> and the arm reports (Arm A `SONNET-5-ULTRACODE-CORE-READINESS-REVIEW.md`; Arm B Codex C1–C5 PRs
> #1758/#1755/#1754/#1753/#1752; Arm C Agent Mode; Arm D `../../../planning/LIVE-VERIFIED-EVIDENCE-PACK.md`).
> **Ledgers joined on the §3.3 claim-anchor key; disagreements adjudicated by evidence tier
> (live/test-confirmed > source-read > inference), never by majority vote.** Genuine owner decisions
> are *routed* to the question router, **not decided here**.

---

## 0. Executive verdict

**Gate V (the verification-fleet pass) is COMPLETE.** The plan is source-accurate enough to proceed to
Phase-B per-step planning, **adopting Sequence C** (capability-class, bounded interleave) — *conditional*
on the named punch-list (§5) and the two pre-existing owner-gated program gates (Gate-0 ratification,
Phase-2.5 cold-start), which are **independent of Gate V and remain the owner's to clear**.

The single biggest thing the fleet settled: **the maintainer's "games later" instinct is correct and
now evidence-backed at the strongest tier.** Games can defer past the frozen L3 slot because — verified
three independent ways (Arm A grep, Codex C5 source, **Arm D live**) — the frozen **L3→L4/L5 dependency
edge is fabricated**, and Arm D **empirically exercised every shared primitive games "prove" (including
the game-only-wired PvP wager engine) with no game at all**, via a same-process service-layer harness.
The replacement oracles are not hypothetical; Arm D prototyped them.

Two headline corrections to the plan's self-justification, both now firm:
1. **The "two live money bugs prove K7/settle-once must ship early" argument is dissolved.** Arm D
   proved (test-confirmed) the wager escrow/settle engine is *already* idempotent under real
   concurrency (`double_paid=False`). The one real open gap is the **deathmatch `_DuelView`
   double-write** (no `SettleOnceMixin`) — a Phase-B mixin retrofit, **not** a reason to build the
   (zero-code) K7 workflow engine early.
2. **Audited-write atomicity is a SYSTEMIC contract-freeze item across economy/karma/xp**, not a
   karma-only anomaly — but it is a *contract* gap, not a live defect (Arm D wrote real audit rows on
   every credit/debit). See §2 reconciliation R-1.

---

## 1. Reconciled contradiction ledger (joined on §3.3 keys)

Precedence: **live/test-confirmed (Arm D) > source-read (Codex/Arm A) > inference.** "Winner" = the arm
whose evidence tier resolves the claim.

| §3.3 key | Disputed claim | Arms & evidence | Resolution |
|---|---|---|---|
| `NEW-BOT-BUILD-PLAN.md` §2 build-order | L3 Games must precede L4/L5 | A (grep: zero L3 dep) · C5 (source: no import edge) · D (**live: primitives run without games**) | **CONTRADICTED — 3 arms, top tier D.** The edge is fabricated; adopt Sequence C. |
| `game_wager_workflow` settle_pvp / "live wager double-pay" | Wager double-pay is a live Gate-V risk | A (source: `SettleOnceMixin` exists, 4/6 adopters) · C5 (READY primitive) · **D (test-confirmed idempotent, `double_paid=False`)** | **REFUTED at the escrow engine.** Re-scope the risk to deathmatch `_DuelView` only. |
| `deathmatch_cog.py` `_DuelView` | Deathmatch human-duel settle-once | A (source: ad-hoc `is_over`) · **D (CONFIRMED open: 2 concurrent calls → wins=2)** | **CONFIRMED real open gap** → Phase-B delta (retrofit `SettleOnceMixin`). |
| `docs/ownership.md` §economy / `economy_service` | Economy is an atomic, "richly proved" audited seam | A (prose "proved" / row NEEDS_CONTRACT_FREEZE) · C4 (non-transactional) · **D (live: works, audit row written)** | **Functional (D) but non-atomic multi-leg (A+C4)** → `NEEDS_CONTRACT_FREEZE`, not a bug. See R-1. |
| `karma_service.give` | Karma is a clean audited exemplar | A (Important #7: 3 un-transacted writes → freeze) · C4 (READY: sole owner + audit log) | **`NEEDS_CONTRACT_FREEZE`** — both true; the atomicity call (A) binds over the ownership call (C4). |
| `xp_service.award` | XP award audit parity | A (R-15 split ownership) · C4 (no audit companion) · D (live: works, events fire) | **Works live (D); audit granularity is `NEEDS_OWNER_DECISION` (C4) + ownership reconcile (A).** |
| `parity/COVERAGE.md` L15-17 | Parity goldens prove shared runtime/events/settings | **C3 (source: 21% events / 25% tables / 2% settings)** — uncontested | **CONTRADICTED.** Parity proves command *breadth*, not event/DB/settings *depth*. Punch-list item. |
| `.github/workflows/code-quality.yml` L194+ / `ai-evals.yml` | CI enforces audit-seam / deferred-recovery / AI-eval quality | C3 (advisory `continue-on-error`; `\|\| true`) · corrections-doc (Agent-Mode `ci-gate` error) | **CONTRADICTED.** Those checkers are advisory; live gate is `code-quality`. Do **not** report them as gating. |
| `NEW-BOT-BUILD-PLAN.md`:82 profile / `:visual-card` | profile / card-engine are unbuilt ADDs | A (C-2/C-9: already built) · C2 (source: `card_render.py` 517L, profile 318L+editor 620L) | **CONTRADICTED — already built.** Reclassify as "formalize into spec + finish holdouts," not from-scratch. |
| K1 `NamespaceRegistry` → K2 | K1→K2 is a ready ordered foundation | A (Blocker #2: K1 zero code) · C1 (`SUBSYSTEMS` hand-authored, not the K1 compiler) | **CONFIRMED gap.** "Gate-0 docs complete ≠ build prerequisites in place." |

---

## 2. Cross-arm reconciliations (where the evidence tiers matter)

**R-1 — audited-write atomicity: systemic, but a contract gap, not a live defect.** The paper arms read
economy/karma/xp differently; Arm D's live run resolves it. The seams **function today** — Arm D wrote
real `economy_audit_log` rows on every live credit/debit and fired XP events on a real level-up. What
A+C4 correctly flag is that the multi-leg writes (`balance-update → append-audit → emit`) are **not
wrapped in one transaction**, so a crash mid-sequence can desync balance and audit. The `*_in_txn`
helpers already exist. **Verdict: `NEEDS_CONTRACT_FREEZE` for atomic multi-leg money/progression writes
across economy + karma + xp — one systemic Phase-B contract, not three isolated notes, and not a
"broken today" claim.** (Corrects Arm A's "economy already richly proved" framing for the deferral
argument, per the corrections-doc directive.)

**R-2 — the money-bug narrative, precisely scoped.** Converged: wager engine hardened (D, test-confirmed)
→ the only real settle-once gap is deathmatch `_DuelView` + the blackjack free-tournament path (single-
call-by-construction today, wants an explicit idempotency contract per C-owner-decision). K7 is not on
the critical path for either.

**R-3 — parity is necessary but insufficient.** No arm disputes C3: broad command coverage
(96%/88%/94%/82%) but shallow structural coverage (events 21%, tables 25%, settings 2%). The rebuild's
"shared primitive proven" claim cannot rest on parity alone; Arm D's non-game harnesses are the
depth-side complement, and Phase-B must widen event/table/settings goldens.

**R-4 — L0 split is clean and cross-confirmed.** C1 + Arm A agree: **READY** = DB seam, lifecycle/
readiness, `tasks.spawn`, observability, K5. **NEEDS_CONTRACT_FREEZE / SOURCE_RECONCILIATION** =
composition-root, loader, import-safe config, EventBus→outbox, authority-unify, interaction-runtime
single-seam, namespace registry (K1). **NEEDS_ORACLE** = K7 (zero code), parity depth.

---

## 3. Reconciled system readiness matrix

Enum per §3.1. "Tier" = strongest evidence backing the row (D live > Codex/A source-read). Where arms
differ, the adjudicated class is shown with the reconciliation note.

### L0 — kernel / foundation
| System | Class | Tier | Note |
|---|---|---|---|
| DB seam (`utils/db`) | `READY_FOR_TEST_DESIGN` | source (C1) + live (D) | Pool/txn/migration order strong; `once()`/IdempotencyKey the only real add |
| Lifecycle + readiness (K5) | `READY_FOR_TEST_DESIGN` | source (C1/A) | `/ready` gates on lifecycle not just gateway; mature |
| Task supervisor (`tasks.spawn`) | `READY_FOR_TEST_DESIGN` | source (C1) | Strong refs/metrics/cancel |
| Observability | `READY_FOR_TEST_DESIGN` | source (C1) | Freeze cardinality rules |
| Composition root (`bot1.py`) | `NEEDS_CONTRACT_FREEZE` | source (C1/A) | Hand-composed, not manifest-generated |
| Loader (`INITIAL_EXTENSIONS`) | `NEEDS_SOURCE_RECONCILIATION` | source (C1) | Static list; `bootstrap_access_cog` must load first |
| Config (`config.py`) | `NEEDS_CONTRACT_FREEZE` | source (C1/A) | Import requires a prod token → hostile to unit/manifest import |
| EventBus (K4) | `NEEDS_CONTRACT_FREEZE` | source (C4/A) | In-process publish-accepted; durable-outbox has zero code |
| Authority (K6) | `NEEDS_CONTRACT_FREEZE` | source (C1/A) | Real+tested, not the unified `AuthorityDecision` shape |
| Interaction runtime (K8) | `NEEDS_CONTRACT_FREEZE` | source (C1/A) | custom_id == authority boundary; carries a known views→cogs violation |
| Namespace registry (K1) | `NEEDS_OWNER_DECISION` | source (A) | **Zero code**, hard prereq to K2 — Blocker #2 |
| Manifest compiler (K2) | `NEEDS_CONTRACT_FREEZE` | prototype (A) | `grammar_spike` proven (13 tests); real compiler doesn't exist |
| Workflow engine (K7) | `NEEDS_ORACLE` | source (A) | **Zero code/prototype/oracle** — Blocker #1; urgency borrowed (R-2) |
| K9/K10 definitions | `NEEDS_SOURCE_RECONCILIATION` | source (A) | Two frozen docs disagree on what they are (C-5) |
| Substrate-kit cold-start | `BLOCKED_BY_GATE` | source (A) | Phase-2.5 A/B never run in repo history |
| Gate-0 ratification | `NEEDS_OWNER_DECISION` | source (A) | 12 Q-D rows + L-21 unstarted — Blocker #3 |

### L1 — operator spine & presentation
| System | Class | Tier | Note |
|---|---|---|---|
| L1a+L1b (17 owner-decided rows) | `READY_FOR_TEST_DESIGN` | source (A) | *test-spec-ready, NOT implemented* — the 14 committed "implement-now" items are unbuilt |
| L1b operator domains (slash parity) | `NEEDS_CONTRACT_FREEZE` | source (C2) | Still prefix-first (channel 17p/0s, role 15p/0s) |
| L1b ticket | `READY_FOR_TEST_DESIGN` | source (A) | Thinnest coverage; new work lands on under-tested base |
| Visual card engine (L1c) | `NEEDS_SOURCE_RECONCILIATION` | source (A/C2) | **Mis-labeled ADD — already built** (`card_render.py` 517L, 5 consumers) |
| welcome / ux_lab (L1c) | `NEEDS_OWNER_DECISION` | source (A) | Not yet walked; both low-risk fast walks |

### L2 — deterministic non-game foundations
| System | Class | Tier | Note |
|---|---|---|---|
| treasury | `READY_FOR_TEST_DESIGN` | source (A) | Clean exemplar; composes transactional multi-leg writes |
| community hub | `READY_FOR_TEST_DESIGN` | source (A) | 100%/100% fit |
| leaderboard | `READY_FOR_TEST_DESIGN` | source (A) | MERGE-into-kernel already half-done (12-provider registry; 4/12 non-game) |
| economy | `NEEDS_CONTRACT_FREEZE` | **live (D)** + source (A/C4) | Works live; multi-leg atomicity (R-1) + `transfer()` unwired crash history (C-10) |
| karma | `NEEDS_CONTRACT_FREEZE` | source (A/C4) | Sole owner + audit log, but 3 un-transacted writes (R-1) |
| xp | `NEEDS_OWNER_DECISION` | **live (D)** + source (A/C4) | Works live; audit granularity owner-decision + R-15 ownership reconcile |
| inventory | `NEEDS_OWNER_DECISION` | source (A) + live (D) | Live idempotent grant; but BIGINT-vs-TEXT user_id migration decision (Important #12) |
| community_spotlight | `NEEDS_SOURCE_RECONCILIATION` | source (A) | Games sub-panel hard-coupled to 4 L3 providers (Important #13) |
| profile surface | `NEEDS_SOURCE_RECONCILIATION` | source (A/C2) | **Already built** (`NEW-BOT-BUILD-PLAN.md`:82 stale) |

### L3 — games (deferred dependency/oracle only)
| System | Class | Tier | Note |
|---|---|---|---|
| Wager escrow / settle-once | `READY_FOR_TEST_DESIGN` | **live (D)** + source (C5) | Idempotent under real concurrency; **exercisable without games** |
| `SettleOnceMixin` | `READY_FOR_TEST_DESIGN` | **live (D)** | Concurrent claim → exactly one True; zero game/Discord dep |
| Deathmatch `_DuelView` | `NEEDS_CONTRACT_FREEZE` | **live (D)** | Real double-write gap → mixin retrofit (Phase-B delta) |
| Mining whole-stack | `NEEDS_ORACLE` | source (C5) | `dig()` couples coin+item+wear+xp+grid in one txn — broadest consumer; needs a deferral oracle |

### L4 / L5 — post-core platform & control plane
| System | Class | Tier | Note |
|---|---|---|---|
| ai / btd6 / project_moon (L4) | `NEEDS_OWNER_DECISION` | source (A/C2) | Genuine platform primitives; **zero L3 dependency** (only reach L1a/L2) |
| web dashboard / boards / migration (L5) | `NEEDS_CONTRACT_FREEZE` | source (C2) | dashboards never import `disbot`; read generated data — no L3 dep |

---

## 4. Sequencing verdict — adopt Sequence C

**Sequence C (capability-class, bounded interleave):** foundation contracts → operator core →
deterministic non-game foundations → essential post-core platform/control → optional domain/growth →
**games/world as late consumers.**

- **Sequence A (frozen, L3 before L4/L5) is rejected** — its L3→L4/L5 edge is fabricated (§1, verified
  3× incl. live). Its ordering is the current bot's historical growth order, not a build requirement.
- **Sequence B (strict games-last) is dependency-correct but over-reads "defer games" as "defer the
  concurrency contract."** Arm D shows the concurrency primitives are exercisable *now* without games,
  so they need not wait for L3.
- **Sequence C wins** because it defers game *features* while pulling the bounded set of game-*proved*
  primitives forward as non-game oracles (which Arm D proved feasible). Bound: keep each stage
  production-grade; the interleave is "prove the primitive early via a synthetic harness," not "build a
  game early."

**Grammar-fit verdict `GO-with-amendments` stands** (Arm A) — Sequence C changes *what remains to prove
and in what order*, not the feasibility conclusion.

---

## 5. Phase-B punch-list (the deltas Gate V hands forward)

| # | Delta | Source | Owning artifact | Owner-gated? |
|---|---|---|---|---|
| P-1 | Freeze the **atomic multi-leg money/progression write** contract across economy+karma+xp (one systemic contract; use `*_in_txn`/outbox) | R-1 (A/C4/D) | ownership.md + L2 plan | design → no; policy → see O-1 |
| P-2 | Retrofit `SettleOnceMixin` onto deathmatch `_DuelView` + widen the Rule-6 checker to catch non-adopters | R-2 (A/D) | games plan | no (contained fix) |
| P-3 | Freeze the ~11 **L0 contracts** (composition root, loader manifest, import-safe config, EventBus→outbox, authority-unify, interaction single-seam) | C1 §10 + A | Gate-0 packet | partly (Gate-0) |
| P-4 | Stand up the **5 named non-game replacement oracles** (wager-idempotency, settle-once, deathmatch-stats, economy/xp, mining whole-stack) — Arm D prototyped #1–4 | C5 + D | verification plan | no |
| P-5 | **Widen parity depth** — raise event/table/settings golden coverage from 21%/25%/2% before "shared primitive proven" | C3 (R-3) | verification plan | no |
| P-6 | Reclassify **already-built "ADD" rows** (visual card engine, profile surface) from from-scratch to formalize-spec-+-finish-holdouts | A (C-2/C-9) + C2 | stage-2 walk + build plan | no |
| P-7 | Enumerate **unowned Discord-object mutations** (channel overwrites/lock/create/category; role member-assignment) as ownership deltas | C4 | ownership.md | no |
| P-8 | Correct stale CI/plan readings — audit-seam/deferred-recovery are **advisory**; parity-replay/ai-evals are **non-gating**; live gate is `code-quality` (**not** `ci-gate`) | C3 + corrections-doc | ci docs | no |
| P-9 | Build **K1 NamespaceRegistry + `tools/check_amendments.py`** before treating K2 as settled (Gate-0 docs ≠ build prereqs) | A Blocker #2 | Gate-0 packet | partly (Gate-0) |

---

## 6. Gate-V lift/hold verdict

- **Gate V (the verification pass) — COMPLETE.** It found the final improvements before Phase B (§5)
  and resolved the sequencing question (§4). Its output feeds Phase-B per-step planning.
- **Program-wide readiness — HOLD, on two owner-gated gates that are NOT Gate V's to lift:**
  1. **Gate-0 ratification** (12 Q-D rows + L-21) — unstarted; blocks all new-repo code.
  2. **Phase-2.5 substrate cold-start A/B** — never run; gates Phase 3.
- **What Gate V clears:** the sequencing decision (Sequence C), the K7-urgency myth (R-2), and the
  live-co-test half of the oracle (Arm D is the first concrete instance).
- **Net:** proceed to **Phase-B per-step planning under Sequence C** in parallel with the owner clearing
  Gate-0 and Phase-2.5. No new-repo code starts until both program gates clear (unchanged).

---

## 7. Genuine owner decisions — routed to the question router (not decided here)

These need the maintainer; the synthesis does not decide them.

- **O-1 (atomicity policy):** should economy/xp/karma money-writes require single-transaction atomicity
  (+ unify `economy_audit_log` with the generic audit event), or is best-effort audit acceptable? (R-1)
- **O-2 (XP audit granularity):** does `xp.award` need audit parity with economy/karma, or stay
  event-only progression? (C4/A R-15)
- **O-3 (workflow engine):** do automation/setup/mining patterns become one generic `WorkflowSpec`
  engine (K7), or stay domain-specific? (C1/A) — note its urgency is *not* the money bugs (R-2).
- **O-4 (EventBus durability):** which rebuild events require durable delivery/outbox vs remain
  in-process advisory? (C4)
- **O-5 (inventory migration):** BIGINT-vs-TEXT `user_id` cast + `guild_id=0` legacy bucket. (A #12)
- **O-6 (deathmatch fix shape):** retrofit `SettleOnceMixin` onto `_DuelView` vs an equivalent guard. (D)
- **O-7 (advisory→hard checkers):** promote audit-seam + deferred-recovery AST checks from advisory to
  gating? (C3) — *executable-config; route as a DISCUSS Q.*
- **O-8 (Gate-0 + Phase-2.5):** the two program gates themselves — owner-run.

---

## 8. Evidence base

Arm A `docs/analysis/rebuild-discovery/gate-v/SONNET-5-ULTRACODE-CORE-READINESS-REVIEW.md` (merged);
Arm B Codex C1–C5 PRs #1758/#1755/#1754/#1753/#1752 (all source-read; verified sound); Arm C Agent Mode
(external constraints; `ci-gate` error rejected per corrections-doc §3); Arm D
`docs/planning/LIVE-VERIFIED-EVIDENCE-PACK.md` (operator live run — the only **test-confirmed** tier,
service-layer fidelity; command-pipeline tier still `NEEDS_EXTERNAL_VALIDATION`). Reconciliation method
+ per-arm verification: `docs/planning/rebuild-gate-v-findings-corrections-2026-07-06.md`. Source wins
over every arm (Q-0120).
