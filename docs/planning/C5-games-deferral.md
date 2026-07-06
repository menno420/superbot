# C5 — games-deferral dependency attack

## Common Codex preamble and embedded fleet contracts

You are a GPT Codex session on menno420/superbot, Arm B (session C5) of a four-arm GATE V verification fleet. Do a READ-ONLY, source-first verification pass over your assigned scope only. Use Plan mode for initial investigation and Extra High reasoning if available.

You are the fleet's empirical source/test spine: prove or disprove dated planning claims against live source at current HEAD — do NOT produce a broad architecture brainstorm (that is Arm A's job; defer to it and add only source deltas).

Shared contracts used verbatim for this report: readiness enum = `READY_FOR_TEST_DESIGN` · `NEEDS_CONTRACT_FREEZE` · `NEEDS_OWNER_DECISION` · `NEEDS_SOURCE_RECONCILIATION` · `NEEDS_ORACLE` · `NEEDS_EXTERNAL_VALIDATION` · `BLOCKED_BY_GATE` · `DEFERRED`; evidence labels = `CONFIRMED` · `INFERRED` · `STALE` · `CONTRADICTED` · `UNVERIFIED`, with Arm-B method tags `source-read` and `test-confirmed`; claim anchors use `path:line` or `path:§x.y`; CodeGraph/import-graph caveats apply, especially invisible EventBus/registry edges; CI parity requires `python3.10` and source verification over false-green checks; degrade gracefully by preserving primary deliverables and the contradiction ledger; Arms A/B/C are read-only except for their single output report; canonical paths are the dated rebuild findings and per-sector ledgers; startup route was sampled through the current-state/rebuild artifacts and live source, not trusted from dated planning alone.

Scope C5 only: Treat L3 only as a dependency/oracle problem. What depends on L3; what L3 depends on; which shared primitives originate for games; whether any pre-existing primitive gets meaningful validation only from games; whether L4/L5 depend on them; what is lost by postponing blackjack/RPS vs mining; whether equivalent earlier proof can be created. Try to falsify both “games must stay before L4/L5” and “games can safely move to the very end”; return surviving evidence.

## Preflight

- Checkout/local HEAD: `cf5a234 Merge pull request #1749 from menno420/bot/dashboard-refresh`.
- Live GitHub unavailable in this container checkout: no `origin` remote is configured and `gh` is not installed, so this report distinguishes local HEAD evidence from live GitHub state.
- The launch-pad file is absent locally; I read PR-branch raw content for `docs/planning/rebuild-gate-v-verification-fleet-2026-07-06.md` and used only its C5 charter plus §3/§5 contracts as instructions.
- Test execution status: targeted collect-only was attempted with CI-parity `python3.10` via `PYENV_VERSION=3.10.20`; collection was blocked by missing `asyncpg` for DB-backed service tests, but 5 wager-boundary/blackjack tests were discoverable before collection aborted. Evidence from those tests is therefore `source-read`, not `test-confirmed`.

## Executive C5 verdict

**Surviving evidence falsifies both extreme claims.**

1. **“Games must stay before L4/L5” is not source-proven.** L4 AI/BTD6 and L5 dashboard/boards/migration rows are anchored to L0/L1/L2 contracts, manifest/settings lanes, AI platform, and knowledge-domain sources — not to shipped L3 game features. Current source has AI diagnostics and BTD6 lifecycle code with no dependency on game cogs, and dashboard/botsite apps are decoupled from `disbot` imports. This supports moving at least some L4/L5 platform/control work before game feature shipment, provided shared contracts are proved elsewhere.

2. **“Games can safely move to the very end” is also not source-proven.** Games currently carry the richest concrete source oracles for the exact primitives the rebuild says must become kernel guarantees: two-sided escrow, settle-once/idempotent row consumption, tournament entry/payout recovery, restartable game state, leaderboard provider breadth, mining’s multi-store atomic workflow, item/progression/world-grid integration, and race/write-boundary ratchets. Moving all L3 to the very end would remove early proof unless those primitives get deterministic replacements before L4/L5 relies on them.

3. **Best surviving C5 dependency shape:** game *features* can move later than frozen L3, but game-derived *primitive proofs* cannot be deferred wholesale. A safe reorder is “L2 shared kernels + synthetic/non-game oracles + selected narrow game-shaped proof harnesses before L4/L5; full blackjack/RPS/mining feature shipment can follow later.”

## Source-reality map: what L3 depends on

| L3 area | Source/planning evidence | C5 classification |
|---|---|---|
| Blackjack/RPS wager paths | Build plan places blackjack/RPS first in L3 because they depend on economy and ChallengeSessionSpec / G-17, and call them richest goldens / escrow seam. Current `game_wager_workflow` implements escrow-at-accept, row-locked idempotent settle/refund, tournament entry/payout, and recovery. | `NEEDS_ORACLE` if feature-deferred; the primitive itself must be proved before dependents. |
| Mining | Build plan explicitly makes mining last in L3 because it exercises G-12/G-13/G-14/G-15/R-8/R-12. Current `mining_workflow` is a service-owned write boundary for inventory + coins + XP + grid/fog/energy/wear in one transaction. | `NEEDS_ORACLE`; mining feature can defer, but its “whole-stack acceptance” role needs an earlier replacement. |
| Leaderboards | Build plan dissolves leaderboard into L2 kernel, then L3 games add providers/stat writers. Current provider registry includes non-game and game providers. | `READY_FOR_TEST_DESIGN` for kernel with non-game providers; game-provider breadth can defer. |
| Economy/inventory/progression | L3 uses these; it does not own their base contracts. Economy service and mining workflow show these primitives already exist before/under games. | `NEEDS_CONTRACT_FREEZE` for rebuild contracts; not a reason to ship L3 first. |

## Source-reality map: what depends on L3

| Candidate downstream | Evidence | Does it depend on L3 features? | Does it depend on game-proved primitives? |
|---|---|---:|---:|
| L4 AI platform | `ai_cog.py` is read-only diagnostics over `core.runtime.ai`/`services.ai_gateway`; no game import surfaced in sampled source. | No source proof. | Indirectly may need deterministic provider/eval/audit contracts, not game features. |
| L4 BTD6 | `btd6_cog.py` owns BTD6 schema/ingestion lifecycle and reads AI decision audit; no dependency on L3 games in its architecture docstring. | No source proof. | Needs KnowledgeDomainSpec/evals/ingestion; not blackjack/RPS/mining. |
| L5 dashboard + live editor | Build plan says manifest snapshot/settings lanes; `dashboard/app.py` says the app reads generated dashboard JSON and never imports `disbot`. | No source proof for read-only dashboard; live editor must write through settings/workflow lanes. | Yes for authority/audit/mutation lanes, but not game-specific. |
| L5 public botsite | `botsite/app.py` reads committed public site JSON and never imports `disbot`; this is even less game-dependent. | No. | No, except generated data freshness. |
| L5 boards family | Build plan ties boards to G-20-adjacent/P-1, not L3. | No source proof. | Needs lifecycle/tag/index/idempotent sync oracles, not game features. |
| L5 bot-migration assistant | Build plan depends on L1 complete + manifest corpus. | No source proof. | Needs manifest/command corpus fidelity; games only matter if migration maps game commands. |

## Lost oracles if blackjack/RPS are postponed

| Lost early oracle | Source evidence | Replacement feasibility | Required replacement if games defer |
|---|---|---|---|
| Two-player wager escrow and settle-once | `game_wager_workflow.open_pvp_wager()` debits both players and writes escrow rows in one transaction; `settle_pvp()` locks rows and pays only if escrow remains; `refund_pvp()` uses the same guard. | High. Service-level contract/concurrency tests can open, settle, replay, and race without a Discord game UI. | Synthetic `ChallengeSessionSpec` harness + DB-backed race tests for escrow rows, replay, restart/recovery. |
| Tournament entry/payout recovery | `enter_tournament()` debits fee and writes recovery row in one transaction; `payout_tournament()` consumes rows before payout, but free rewards are explicitly not row-guarded. | Medium. Paid-tournament pot is straightforward; free-reward idempotency needs a contract decision. | Contract test for paid pot consume-once; owner/design decision or idempotency key for free rewards before trusting games-last. |
| Callback/result double-settle UI guard | `tests/unit/views/test_blackjack_pvp_settle_once.py` asserts blackjack PvP terminal resolution calls settle/refund only once. | Medium. Can be generalized into a view/session terminal-state mixin test independent of blackjack. | Generic terminal-state idempotency tests for callbacks and stale/replayed interactions. |
| Wager write-boundary ratchet | `tests/unit/invariants/test_game_wager_write_boundary.py` names RPS/blackjack wager files and forbids direct economy credit/debit outside the service. | High. Ratchet can run against synthetic game-shaped modules or the service itself. | Keep AST ratchet but make it kernel-owned, with fixture consumers not tied to L3 shipment. |

## Lost oracles if mining is postponed

| Lost early oracle | Source evidence | Replacement feasibility | Required replacement if mining defers |
|---|---|---|---|
| Whole-stack multi-write transaction | `mining_workflow` documents and implements one service-owned boundary for coin + mining inventory + wear + XP + event-after-commit; `mine()` commits item grant, wear, and XP in one transaction. | Medium/high. A non-game “inventory purchase/craft” or synthetic workflow can prove atomic legs, but not all mining world invariants. | Deterministic compound-workflow tests over economy + inventory + XP + audit + EventBus with forced-failure rollback. |
| Item/progression/world-grid integrated acceptance | `dig()` couples energy, position/depth, seed-grid cell, loot, fog, wear, and XP in one transaction. | Low/medium. Only mining currently stresses all of these together. | Either keep a narrow mining spike/harness before L4/L5 or split into synthetic world-store + inventory + XP + fog tests. |
| Characterization breadth | Mining has many current tests and source comments naming byte-identical characterization plus AST write-boundary ratchets. | Medium. Characterization can exist without shipping user-facing mining if a headless service harness is retained. | Headless mining-workflow characterization suite, not necessarily command/UI shipment. |

## Discrepancy ledger (§3.3 keyed)

| Plan claim anchor | Source evidence | Test evidence | Status | Severity | Required final-session action |
|---|---|---|---|---|---|
| `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md:178` | Wager games are indeed rich oracles for escrow/settle, but source now exposes these as `services.game_wager_workflow` primitives callable without shipping a game feature. | Collect-only blocked for service tests by missing `asyncpg`; blackjack view tests were discovered but not run. | `CONFIRMED source-read` for richness; `CONTRADICTED source-read` if interpreted as “must ship games first.” | Important | Preserve wager primitive proof early; do not require full blackjack/RPS feature shipment solely for escrow proof. |
| `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md:182` | Mining is currently the broadest real consumer of game/economy/item/progression/world primitives; `mining_workflow.dig()` combines many writes. | Collect-only blocked by missing `asyncpg`. | `CONFIRMED source-read` | Blocker for strict games-last | If mining moves late, create a deterministic whole-stack replacement or narrow mining spike before L4/L5. |
| `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md:191` | AI/BTD6 source docs show L4 depends on AI platform/knowledge-domain ingestion/evals, not L3 game features. | Not run. | `CONTRADICTED source-read` for any hard claim that L4 must wait for L3 feature shipment. | Important | Allow L4 platform planning after primitive proof gates, independent of full L3 feature completion. |
| `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md:202` | Dashboard/botsite source is decoupled/read-only; L5 dashboard live-editor needs manifest/settings lanes, not games. | Not run. | `CONTRADICTED source-read` for any hard claim that L5 read-only/control surfaces require shipped games. | Important | Split L5 read-only/generated projections from write-capable live editor and migration assistant. |
| `docs/planning/rebuild-stage2-subsystem-walk-2026-07-05.md:97` | Row says mining ports last as whole-stack acceptance test; source supports this as an oracle role, not as an unavoidable user-facing shipping order. | Not run. | `CONFIRMED source-read` oracle role; `NEEDS_OWNER_DECISION` sequence implication. | Important | Decide whether “ports last” means feature shipment last or proof harness last within an earlier primitive gate. |
| `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md:103` | `dashboard/app.py` now includes login/edit/moderation rate limiters and owner gate, so local HEAD is beyond a purely read-only MVP despite the file docstring’s first line. | Not run. | `NEEDS_SOURCE_RECONCILIATION source-read` | Cleanup/Important | Reconcile L5 dashboard row against local HEAD before synthesis uses dated “read-only only” phrasing. |

## Readiness rows for C5 systems

| System / primitive | Readiness | Evidence label | Rationale |
|---|---|---|---|
| Economy transaction legs (`debit_in_txn`, `credit_in_txn`, transfer) | `READY_FOR_TEST_DESIGN` | `CONFIRMED source-read` | Service exposes transaction-aware legs and audit/event semantics; tests were not runnable here due dependency gap. |
| Wager escrow / settle-once | `READY_FOR_TEST_DESIGN` | `CONFIRMED source-read` | Source has a coherent service seam and named tests; needs DB-backed run/race proof. |
| Free tournament reward idempotency | `NEEDS_CONTRACT_FREEZE` | `CONFIRMED source-read` | Source says free rewards are not row-guarded and single-call by construction; rebuild should not rely on that as a kernel guarantee without a contract. |
| Game state recovery | `READY_FOR_TEST_DESIGN` | `CONFIRMED source-read` | Wager recovery uses game-state rows and `bet` convention; requires restart/recovery oracle. |
| Mining whole-stack acceptance | `NEEDS_ORACLE` | `CONFIRMED source-read` | Strong current oracle; if feature-deferred, equivalent headless/synthetic proof is mandatory. |
| Leaderboard kernel with mixed providers | `READY_FOR_TEST_DESIGN` | `CONFIRMED source-read` | Provider registry mixes non-game and game providers; kernel can be tested on non-game providers first. |
| L4 AI/BTD6 dependency on L3 | `READY_FOR_TEST_DESIGN` | `CONFIRMED source-read` | No sampled source dependency on L3 games; still needs L4’s own provider/eval contracts. |
| L5 read-only generated projections | `READY_FOR_TEST_DESIGN` | `CONFIRMED source-read` | Current apps are decoupled from bot imports; live-editor writes remain separate. |
| Strict games-last sequencing | `BLOCKED_BY_GATE` | `INFERRED source-read` | Blocked unless early oracle replacements exist for wager/mining primitives. |
| Frozen L3-before-L4/L5 sequencing | `NEEDS_OWNER_DECISION` | `INFERRED source-read` | Not source-required as feature order; survives only as an oracle/proof-order requirement. |

## Searches and commands performed

- `find .. -name AGENTS.md -print`
- `git status --short`; `git branch --show-current`; `git log --oneline -10`
- `git fetch origin main claude/chatgpt-prompt-review-kzvr4v` (failed: no `origin` remote)
- `gh pr view 1750 --repo menno420/superbot --json files,headRefName,body,title,url` (failed: `gh` unavailable)
- Browser read of raw PR-branch launch pad.
- `rg -n "L3|Games|blackjack|RPS|rps|mining|ChallengeSession|settle|escrow|..." ...`
- `rg --files | rg '(^cogs/|^services/|^utils/|^views/|^tests/).*?(blackjack|rps|...)'`
- `rg -n "class GameWager|settle_once|..." disbot tests/...`
- `PYENV_VERSION=3.10.20 python3.10 -m pytest --collect-only tests/unit/services/test_game_wager_workflow.py tests/unit/views/test_blackjack_pvp_settle_once.py tests/unit/invariants/test_game_wager_write_boundary.py tests/unit/cogs/test_mining_workflow_characterization.py tests/unit/services/test_economy_service_concurrent.py`

## Confidence and limits

Confidence: **medium-high** for source-dependency conclusions, **medium** for test/oracle conclusions because DB-backed collection was blocked by missing `asyncpg` and no live bot/Postgres was available. This report intentionally does not resolve Arm A’s sequencing design or Arm D’s empirical live exercisability; it only supplies C5 source-reality evidence.
