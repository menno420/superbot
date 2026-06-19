# 2026-06-19 — Ultracode fleet orchestration (mining hub + codex-review; the B4 collision)

> **Status:** `complete`

## Arc
Ran an ultracode parallel-build fleet as **orchestrator**. Before dispatching, verified the session
prompt's 9-lane roster against live source — **6 of 9 were stale-shipped, gated, or owner-design
territory** — then spawned **3 file-disjoint worktree agents** for the genuinely-buildable lanes.
This card is the orchestrator close-out: the run record + the one costly lesson (the B4 duplicate-work
collision) folded into the fleet protocol.

## Shipped
- **A1 — mining hub declutter (Option A PR2)** — PR **#1131 merged**. Main hub 14→6 buttons; new
  `character_hub.py` + `explore_hub.py` (stub) sub-hubs; Descend/Ascend + the depth-event mining
  "explore" folded into the Mine action. PR3 (grid Mine) left out (owner-sign-off-gated).
- **B5 — codex-review integration** — PR **#1132 merged**. Part A routine fix-first "check Codex"
  step (dispatch + reconciliation prompts) + Part B the issue-only `superbot-pr-check` Hermes 6H skill.
- **B4 — consistency linter → cogs** — PR **#1133 closed (duplicate)**: a concurrent session shipped
  the same (and more complete) work as **#1128** ~8 min earlier.
- This session's docs close-out (this PR): a fleet-dispatch pre-flight overlap-check rule + the
  #1133/#1128 incident note.

## Dropped after source verification (the stale-roster finding)
A3 (shipped #937) · A4 (shipped #854) · B3 (shipped #960) already done; **A2** fishing loadout-presets
owner-design-gated (Q-0175); **B1** batches 3-4 skills already exist + batch 2 edits `CLAUDE.md`
(owner-live, Q-0106); **B2** remaining items Q-0177 owner-gated. Convergent signal: a parallel session
(#1135/#1136) independently built `scripts/check_plan_code_drift.py` + rebadged A3/A4 `historical` —
the same stale-plan class, now tooled.

## Findings
- **The B4 duplicate-work collision is the costly lesson.** The claim ledger (`active-work.md`) was
  reset to a stale state mid-run, so neither this session nor #1128's could see the other's claim. The
  actual load-bearing guard is **`list_pull_requests` (open + recently-merged)**, which the
  orchestrator did NOT fully run before dispatch (it relied on the claim ledger + current-state).
  Captured as a fleet-plan Rules-of-engagement item + a note on the duplicate-work idea.

## Context delta
- **Needed but not pointed to:** the fleet-plan's "Rules of engagement" told the orchestrator to scan
  `active-work.md` but not to run `list_pull_requests` before dispatch — and the ledger can go
  stale/uncommitted. Fixed this session.
- **Pointed to but didn't need:** the fleet-plan doc's own Lane A/B rosters were fully consumed (Wave
  A/B shipped) — stale; the real lanes came from the session prompt + `current-state.md` ▶ Next action.
- **Discovered by hand:** the session prompt's lanes were ~66% stale; only grepping for shipped
  artifacts + reading plan badges caught it. `check_plan_code_drift.py` (#1135) now automates part of this.

## Decisions made alone
- Dropped 6 of 9 prompt lanes as stale/gated/shipped; ran only A1/B4/B5 (B4 turned out a dup).
- **Closed #1133** as a duplicate of merged #1128 rather than rebasing — no unique value; merging its
  warn-only cog-scope would regress #1128's `error`-level graduation.
- Spawned agents in isolated **worktrees** so file-disjoint lanes each get their own branch/PR.

## Flagged for maintainer
- **A1 (#1131, merged)** is a visual UX change to the headline mining hub — please live-verify the new
  layout on next deploy (fully reversible, UI reorg only).
- The **claim-ledger reset mid-run** is a real workflow gap — the duplicate-work guard went blind.

## 📤 Run report

- **Did:** orchestrated a 3-lane ultracode fleet + this docs close-out · **Outcome:** shipped (2 merged, 1 dup-closed)
- **Shipped:** #1131 mining hub declutter · #1132 codex-review integration · this PR — fleet-dispatch overlap-check rule + #1133/#1128 incident note
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** B5 (#1132) — re-paste the dispatch + reconciliation routine prompts into their console configs, and run `bash scripts/hermes/install-skills.sh` on the VPS for the new pr-check skill; A1 (#1131) — live-verify the mining hub layout on next deploy
- **⚑ Self-initiated:** the fleet-dispatch pre-flight overlap-check rule (this PR) — refines [`ultracode-fleet-plan-2026-06-19.md`](../docs/planning/ultracode-fleet-plan-2026-06-19.md) + [`ci-cost-and-duplicate-work-prevention-2026-06-14.md`](../docs/ideas/ci-cost-and-duplicate-work-prevention-2026-06-14.md) (Q-0172)
- **↪ Next:** buildable queue stays the website P1–P8 wave (in-flight by other sessions) + consistency rule-1 AI-nav; recon due at #1140

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 2 (#1131, #1132) + this docs PR pending |
| CI-red rounds | 0 (born-red session gate only; no genuine CI failures) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (fleet-dispatch pre-flight overlap check) |
| Ideas groomed | 1 (annotated the duplicate-work idea with the #1133/#1128 incident) |

## 💡 Session idea
**Fleet-dispatch pre-flight overlap check.** Before an ultracode orchestrator spawns lanes, it must run
`list_pull_requests` (open + recently-merged) and grep recent merge commits for each lane's scope — the
claim ledger alone is insufficient (it can be stale/uncommitted, and a concurrent session's work may be
an open or just-merged PR not in any ledger). The #1133/#1128 collision this session is the worked
example. Folded into the fleet-plan Rules of engagement + the duplicate-work idea.

## ⟲ Previous-session review
The previous band's sessions kept the plan index + idea taxonomy current (good), but left the
**ultracode-fleet-plan doc's Lane A/B rosters stale** (all shipped) without rebadging — which cost this
session a verification pass to realize the prompt's lanes were ~66% stale. **System improvement:** the
new `check_plan_code_drift.py` (#1135) is the right direction — extend it (or a sibling) to also flag a
*coordination/dispatch* doc whose named work-units are all merged, so a fleet brief can't silently rot
into a stale dispatch list. (Nothing to hallucinate here — this is a genuine, specific gap.)
