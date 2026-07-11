# 2026-07-11 — Multi-project review + fleet centralization plan + dispatch kit

> **Status:** `complete`

📊 Model: Opus 4.8 · owner-directed hub session (fleet management / planning + triage) · ultracode

## What this session did

Owner-directed continuation of global fleet management: review the Codex results, triage
every project (keep/replace/delete), plan getting the fleet centralized, and produce the
re-dispatch kit — plus fix the one urgent live bug the review surfaced.

Ran a **19-agent verified discovery fan-out** (14 repo scans + 5 cross-cutting probes,
~2.9M tokens, 0 errors) with every load-bearing claim confirmed against live source (Q-0120,
two agents even diverged on substrate-kit #228 → flagged, not resolved from memory).

## Shipped

- **`docs/planning/fleet-review-2026-07-11.md`** — verified 19-repo triage register (15
  KEEP-family · 3 ARCHIVE codetool-labs · 1 SEED plugin-hello · **0 DELETE**), the Codex
  verdict (trustworthy this round — no phantom commits; real bugs live), ranked verified
  errors, the drift map (all in fleet-manager), the products conversion queue.
- **`docs/planning/fleet-centralization-plan-2026-07-11.md`** — `fleet-manager` as the
  single source of truth: it's already ~70% there (generated roster); the plan is a refocus
  + 6 verified gap-fixes + a timely-trigger regen loop. **Owner decision folded: Option A
  (custodian-primary).**
- **`docs/owner/dispatch-prompts-2026-07-11.md`** — the fleet Permissions & Workarounds
  block (bake into every Claude routine) + 6 paste-ready prompts (2 Sol, 2 Codex, 1 Sonnet-5
  ultracode, 1 fleet-manager).
- **`docs/current-state.md`** — pointer to the three (reachability).
- **venture-lab PR #49 (MERGED)** — the verified real-money fail-open fix: `/webhook` now
  fails CLOSED on a partial Stripe config (was granting membership from unsigned JSON);
  regression test + 2 LISTING truth-fixes; 24 tests green. Owner-authorized cross-repo hotfix.

## Owner decisions this session (Q-0240 decide-and-flag; both owner-confirmed live)

- **Centralization scope = Option A** (custodian-primary; relay retained as secondary).
- **Fix venture-lab live = yes** → shipped as PR #49 (merged).

## 💡 Session idea (Q-0089)

**`gen_dispatch_block.py` (fleet-manager): generate the Permissions & Workarounds prompt
preamble from the capability ledger, don't hand-maintain it.** This session hand-assembled
the Part-A block from `fleet-manager/docs/capabilities.md` + `env-grant-policy.md` + lane
`PLATFORM-LIMITS.md`. That block goes stale the moment a new wall/workaround is discovered.
A generator that emits the current block straight from `capabilities.md` (the master ledger)
means every new dispatch prompt / founding package / routine gets the *latest verified* walls
automatically — the prompts stop drifting from reality the same way the roster stops the
fleet-state from drifting. Dedup: distinct from the roster (fleet state) and owner-queue
(owner asks) generators — this generates the *prompt preamble* agents are born with. Grounded
in exactly the by-hand work this session did. Fits the centralization plan as a P2/P3 rider.

## ⟲ Previous-session review (Q-0102)

The `env-grant-and-relaunch-handoff` session's "NEXT SESSION — START HERE" block was
excellent — I oriented and named scope in minutes with zero re-derivation; that pattern is
load-bearing, keep it. Its triage *scaffold* (the KEEP-verdict table) was a good seed but
**unverified**, and the fan-out found several of its rows needed correction against source:
superbot-idle was self-parked on a blocker (PLUG-001) that is actually **already resolved**
upstream, and the "games lanes blocked on the plugin contract" framing understated that the
contract + exemplar already exist in-tree. **Workflow improvement (built into this session):**
a handoff triage scaffold should tag each verdict `verified`/`unverified` so the next session
knows which to re-check — and the durable answer is the centralization plan's `fleet-triage.md`
register, which carries verified verdicts with source citations rather than a one-time
chat-scaffold. No fix owed the prior session; the improvement is the register + the
verify-against-source discipline this review applied.

## Documentation audit (Q-0104)

`check_docs.py --strict` ✓ (3 new docs made reachable via the current-state pointer; the 5
pre-existing supersede-banner soft warnings are untouched and not mine). `check_current_state_ledger
--strict` = benign newest-merge lag only (13 PRs newer than marker #1980; next recon at #2010
records them — informational, not drift). Both owner decisions recorded in the docs + this
card; the venture-lab fix is recorded in its own repo's session card + PR #49. The fan-out's
verified findings are cited to the run journal in the review doc's provenance note. Nothing
chat-only left un-homed.

## Grooming (Q-0015)

Moved two existing ideas a full lifecycle step: the handoff's **fleet-triage register** idea
(Q-0089 from the prior session) → landed as the review §1 register + a plan to port it into
`fleet-manager/docs/fleet-triage.md` (centralization §4); and the fleet-overview session's
**`verify_owner_queue.py`** idea → promoted into the centralization plan as P2
(`check_owner_queue.py`, the PR-state prober). Both now sit in an executable plan, not as raw
ideas.

## 📤 Run report

- **Did:** verified full-fleet review + triage + Codex verdict, the fleet-manager
  single-source-of-truth centralization plan, the 6-prompt dispatch kit, and a live
  cross-repo hotfix of the venture-lab real-money fail-open · **Outcome:** shipped
- **Shipped:** superbot #1998 (review + centralization plan + dispatch kit) · venture-lab
  #49 (Stripe fail-closed hotfix, MERGED)
- **Run type:** `manual` (owner-directed hub session, ultracode)
- **⚑ Owner decisions:** Option A centralization scope (confirmed) · fix venture-lab live
  (confirmed) — both folded in; `none` blocking
- **⚑ Owner manual steps (from the review):** run the venture-lab live Stripe test-key E2E
  before publish (⚑A) · attach each lane repo to its routine + set model per routine ·
  make `pytest` required (mineverse first) · the built→live click queue (Lumen Drift Release,
  product-forge Pages, "push the plugin seed", mineverse secrets after its CSRF fix)
- **⚑ Self-initiated:** `none` (all work owner-directed in-session; the venture-lab fix was
  explicitly owner-authorized via AskUserQuestion)
- **↪ Next:** dispatch the 6 help-session prompts (owner pastes Sol/Codex; the 2 Claude
  prompts → new routine/Project sessions); execute the centralization plan (fleet-manager
  session, P1 freshness first); the superbot Rule-6 false-green checker fix (routed to the
  superbot Codex prompt)

## 📊 Telemetry

| Metric | Value |
|---|---|
| Deliverable docs shipped | 3 (review · centralization plan · dispatch kit) |
| Cross-repo fixes merged | 1 (venture-lab #49 — real-money fail-open) |
| Discovery agents / tokens | 19 agents · ~2.9M subagent tokens · 0 errors |
| Verified live bugs surfaced | 6 ranked (1 fixed this session; 5 routed) |
| CI-red rounds (this PR) | born-red gate holds only (Q-0133), no real red |
| New ideas contributed | 1 (`gen_dispatch_block.py`) |
| Ideas groomed | 2 (fleet-triage register · verify_owner_queue → check_owner_queue) |
