# Gate V — corrected evidence findings (Codex C2–C5 + Agent Mode), 2026-07-06

> **Status:** `plan` — the **verified evidence layer** the final Gate V synthesis (Arm Σ) should
> consume *instead of* the raw arm sub-reports. Every arm output is evidence to verify, never truth
> (Q-0120); this doc records what survived verification against live source at HEAD `015349e`, what
> was corrected, and the one propagated error the synthesis must reject. Companion to the launch pad
> [`rebuild-gate-v-verification-fleet-2026-07-06.md`](rebuild-gate-v-verification-fleet-2026-07-06.md).
>
> **Method:** the four Codex PRs were each re-verified against the local source tree by an independent
> review fan-out; the Agent Mode report's load-bearing repo-facts were spot-checked by hand. Source
> wins over every sub-report.

## 1. Fleet completion state (2026-07-06)

| Arm | Status | Artifact | Notes |
|---|---|---|---|
| A — Sonnet 5 / Ultracode | **running** | `SONNET-5-ULTRACODE-CORE-READINESS-REVIEW.md` (pending) | left untouched |
| B — Codex C1 (L0/runtime) | **❌ FAILED TO START** | none | no PR in any state; **must be re-run** (§4) |
| B — Codex C2 (capability/invocation) | ✅ done | PR #1755 → `C2-capability-invocation.md` | verdict **sound** |
| B — Codex C3 (tests/parity/oracle) | ✅ done | PR #1754 → `C3-tests-parity-oracle.md` | verdict **sound** |
| B — Codex C4 (ownership/mutation/event) | ✅ done | PR #1753 → `C4-ownership-mutation-event.md` | verdict **sound** |
| B — Codex C5 (games-deferral) | ✅ done | PR #1752 → `docs/planning/C5-games-deferral.md` | verdict **sound** |
| C — Agent Mode (integration/external) | ✅ done | report delivered (this session) | sound **except** one error (§3) |
| D — live-testing | ✅ merged | `LIVE-VERIFIED-EVIDENCE-PACK` (commit `af77f6a`) | empirical pack landed on main |
| Σ — final synthesis | not started | `GATE-V-SYNTHESIS.md` | consumes this doc |

**C1 is the highest-stakes gap:** L0/runtime is the foundation every other layer's readiness depends
on, and it is the one scope with no evidence. Do not run the synthesis as final until C1 lands.

## 2. Codex C2–C5 — verification ledger (all four verdict: SOUND)

All four are read-only, docs-only evidence artifacts. Every load-bearing claim spot-checked reproduces
against live source; **none reproduced the `ci-gate` error**; none fell for the graph-tool dead-code
trap (C4 correctly grep-verified dynamic emitters rather than trusting a blast radius).

| PR | Confirmed against source (highlights) | Corrections / caveats |
|---|---|---|
| **C2 #1755** | Scanner top-line 55 cogs / 484 records / 243 prefix / 209 subcmd reproduces exactly via `scripts/scan_commands.py --summary`; per-domain counts, BTD6 112 records, `subsystem_registry.py` as immutable single-source, ADD subsystems genuinely unbuilt — all confirmed. | Cosmetic: one §3.3 ledger row (`NEW-BOT-BUILD-PLAN.md:L82`) puts a readiness-enum value in the evidence-label column. |
| **C3 #1754** | Parity corpus 465 goldens; breadth 96%/88%/94% vs structural 21% events / 25% DB tables / **2% settings keys**; `code-quality.yml` = live gate (ruff replaced black+isort), architecture = HARD gate, audit-seam + deferred-recovery = **advisory** (`continue-on-error`); `parity-replay`/`ai-evals` are manual & non-required (`ai-evals` appends `\|\| true`). All confirmed. | Self-claim **contradicted**: preflight said the launch-pad doc was "not on main" — it *is* (merged #1750). Benign (ran pre-merge). |
| **C4 #1753** | EventBus is **in-process, publish-accepted, per-handler timeout; a subscriber failure never fails the mutation**; moderation `_record_action` fans out 3 signals; **economy credit/debit is non-transactional** (audit then emit); **XP award emits events with NO audit companion**; channel lifecycle does **not** yet own overwrites/lock CRUD (proof_channel still edits overwrites). `wiring_map.py` maps 30 events, `--check` passes. | No `test-confirmed` evidence (discord/yaml absent in sandbox → all `source-read`). One anchor imprecision (`ownership.md:L52`). |
| **C5 #1752** | `game_wager_workflow` primitives; `settle_pvp`/`refund_pvp` lock escrow `FOR UPDATE` and pay only if rows remain; `enter_tournament` debits + writes recovery row in one txn; `mining_workflow` is a single service-owned write boundary; **`ai_cog` and `btd6_cog` have zero dependency on L3 game cogs**; dashboards never import `disbot`. All confirmed. | Ledger anchors L191/L202 point at section headers rather than the claim line. Correctly placed under `docs/planning/`. |

**Cross-cutting caveats for the synthesis:**
- **All four ran on a stale local HEAD (`cf5a234`, pre-#1750/#1751)** with no git remote — self-disclosed. Every numeric claim still reproduces at current HEAD, but treat any "not on main / unmerged" preflight note as stale.
- **All Codex evidence is `source-read`, not `test-confirmed`** — the sandbox lacked Postgres/discord/yaml, so no runtime/parity/invariant suite actually ran. The synthesis must **not** upgrade any of it to test-confirmed; the concurrency/settle-once/atomicity claims (escrow `FOR UPDATE`, XP no-audit) are read from source and still need a DB-backed run (that is Arm D's / a live suite's job).
- **File placement:** C2/C3/C4 dropped their sub-reports at the **repo root** (clutter); only C5 used `docs/planning/`. Relocate C2/C3/C4 under `docs/planning/` (or `docs/analysis/rebuild-discovery/`) before merging any of them; the C1 re-run prompt (§4) pins the correct path.

## 3. Agent Mode (Arm C) — corrections

The report is genuinely strong on external constraints (Discord interaction/component/command quotas,
discord.py 2.7.1, Railway PITR) and correctly caught the `.python-version` = **3.13.13** runtime-pin
nuance (verified — it is the Railway/railpack runtime pin, distinct from CI's Python 3.10). But:

| Claim in report | Verified reality | Disposition |
|---|---|---|
| **`ci-gate` is the required status context; `code-quality` is stale** (§2, §11 Important, §14) | **CONTRADICTED.** `.github/` contains **no `ci-gate`**; the live required check is **`code-quality`** (`.github/workflows/code-quality.yml`, name "Code Quality") — PR #1750 *and* this PR merge on it. The report read the `ci-setup-redesign-2026-07-05.md` **`plan`** (which explicitly *proposes* owner-gated config) as applied state — the "don't confuse plans with source truth" trap its own quality bar warns against. | **Arm Σ must REJECT** the "migrate docs from code-quality → ci-gate" recommendation (or downgrade it to conditional: "*if/when* the CI redesign is applied"). |
| "PR #1737 consolidated 17 → 14 workflows" (§2) | `ci-setup-redesign` is real (PR #1737) but a **`plan`**; `.github/workflows/` currently holds **17** files. The 17→14 is the plan's *target*, not applied state. | Treat as **planned**, not done. |
| `.python-version` pins 3.13.13 (§2) | **CONFIRMED.** | Keep. |
| discord.py pinned `>=2.7,<2.8` ↔ real 2.7.1 (§2, §9) | Pin **CONFIRMED** in `requirements.txt`; the 2.7.1/Mar-2026 release fact is external (not re-verified offline). | Keep, labelled EXTERNAL. |
| No Railway PITR; all-powerful account token (§8, §10, §13) | Quoted from repo docs (`railway-setup-plan`, `S5-ops`); accurate as **owner-decision recommendations**, not Gate-V blockers. | Keep as `NEEDS_OWNER_DECISION`, not blocker. |

## 4. Re-run prompt for the failed C1 session

```
Repo menno420/superbot. Open docs/planning/rebuild-gate-v-verification-fleet-2026-07-06.md
on the main branch. You are Codex session C1 of Arm B in the Gate V verification fleet.
Prepend the §5 "Common Codex preamble" and embed the §3 shared fleet contracts verbatim,
then execute ONLY scope C1 — L0 / runtime source truth: map the actual source counterparts
for bootstrap/composition, loader, config, DB seam, EventBus, lifecycle, task supervision,
health/readiness, authority/governance, workflow orchestration, interaction runtime,
namespace/collision handling, observability, and parity/simulation foundations. Deliver a
source map, preserve-vs-redesign evidence, hidden dependencies, test evidence, unsupported
plan claims, and the contracts requiring freeze. Read-only throughout. Emit your scoped
sub-report as docs/planning/C1-l0-runtime.md (match C5's placement — docs/planning/, not the
repo root). Do not do the other scopes.

Note on the CI gate: the live required merge check is "code-quality"
(.github/workflows/code-quality.yml). There is NO "ci-gate" in .github/ — ci-setup-redesign
is a proposed plan, not applied state. Do not report ci-gate as live.
```

## 5. Substantive findings worth carrying into synthesis (verified)

Beyond verification bookkeeping, these source-confirmed facts are genuine Gate-V inputs:

- **Non-transactional mutation seams (C4):** economy credit/debit emits its event *after* the audit
  append (not atomic), and **XP award emits events with no audit companion at all**. These are exactly
  the "one mutation path / audit completeness / event atomicity" contracts the rebuild must freeze —
  flag `NEEDS_CONTRACT_FREEZE`, and they need a **DB-backed** test (still `source-read` today).
- **Channel lifecycle ownership gap (C4):** channel create/clone/overwrites/lock CRUD is **not** yet
  owned by a channel service — `proof_channel_cog` still edits overwrites directly. A real ownership
  seam to resolve before L1 test design.
- **Games-deferral evidence (C5):** `ai_cog`/`btd6_cog` have **zero** dependency on L3 game cogs, and
  wager settlement already locks escrow `FOR UPDATE` in service-owned workflows. This *supports*
  deferring game **features** — but the shared **primitives** (settle-once, escrow races, mining
  whole-stack) are today proved only through games, so C5's verdict stands: **defer games only if
  those primitive proofs are replaced early** (contract tests + a DB-backed concurrency harness). This
  is the source-reality half; Arm A owns the design and Arm D the empirical exercisability.

## 6. Directives for Arm Σ (final synthesis)

1. **Reject** the Agent Mode `ci-gate` migration recommendation; the live gate is `code-quality`.
2. **Do not** treat any Codex claim as `test-confirmed` — all are `source-read` (no DB/discord in
   sandbox). The escrow/settle-once/XP-audit findings need a live DB-backed run before test-confirmed.
3. **C1 (L0/runtime) is missing** — the readiness matrix's L0 rows are unproven until it lands. Mark
   L0 `NEEDS_SOURCE_RECONCILIATION` pending C1, not `READY_FOR_TEST_DESIGN`.
4. **Relocate** the root-level C2/C3/C4 sub-reports under `docs/planning/` before merging.
5. Fold §5's contract-freeze findings (economy/XP atomicity, channel ownership) into the Phase-B
   plan template.
