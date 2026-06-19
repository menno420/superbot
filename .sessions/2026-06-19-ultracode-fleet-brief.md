# 2026-06-19 — Ultracode fleet brief

> **Status:** `complete`

## Arc

Follow-on to the governance/supply-chain session (PR #1064). The owner is about to run Claude's desktop
**ultracode** (parallel multi-agent) mode and asked for the most valuable thing to do with it + a
coordination brief. I fanned out three read-only scout agents (architecture boundary-debt · ungated
hardening/bugs · buildable idea backlog) and synthesized a **file-disjoint fleet plan**.

## Shipped (PR #1079)

- `docs/planning/ultracode-fleet-plan-2026-06-19.md` — **Lane A** = 8 architecture boundary-debt
  burndown units (verified live, 76 warns / 0 errors; clears ~48), **Lane B** = 8 ungated tooling/ops/docs
  quick-wins (file-disjoint from Lane A, run concurrently), + rules of engagement, the held/do-not-fleet
  list, and a paste-ready kickoff prompt.
- Reachability pointer added in the repo-structure plan. `check_docs --strict` green.

## Method note

The recommendation itself was produced *via* multi-agent orchestration — 3 parallel `general-purpose`
scouts (sonnet) scoping the three candidate lanes against live source — so the brief is grounded, not
guessed. That doubled as a small live demo of the fan-out pattern the brief prescribes.

## Context delta

- **Discovered by hand:** the **shared-ledger collision** a parallel fleet hits — the repo's per-session
  `.sessions/` files solve card collisions, but `docs/owner/active-work.md` and `docs/current-state.md`
  are single shared files that 16 simultaneous agents *would* conflict on. The brief's "the brief IS the
  claim ledger; agents don't each edit the shared ledgers" rule is the mitigation. → captured as the idea.
- **Pointed to and needed:** scout A's `check_architecture --mode strict` verification — it corrected the
  arch-debt counts to live (76/0) rather than trusting the 2-week-old architecture-atlas figures.

## ⟲ Previous-session review (Q-0102)

Previous session = #1064 (governance/supply-chain baseline, this conversation). **Did well:** caught a
real latent bug (the `httpx 0.28` dashboard cookie-jar drift) *because* it actually ran a fresh install
while wiring the new CI — verification surfaced the defect, not luck. **Could improve:** it modernized
the test fixture but left the per-request-cookie deprecation warnings (a fuller test modernization was
deferred). **System improvement:** that the drift was invisible until a fresh install argues the routed
dependency-lockfile (Q-0177 P1.1) is the highest-value follow-up — the dashboard-CI job now catches the
*class*, but a lockfile prevents it.

## 💡 Session idea (Q-0089)

**A collision-safe claim mechanism for parallel fleets.** `.sessions/` per-file design solved card
collisions, but `active-work.md` / `current-state.md` remain single shared files — a real bottleneck the
moment >2 agents run. Idea: per-agent claim *files* (`docs/owner/claims/<branch>.md`, append-free) that a
small script aggregates into a rendered view, so a fleet claims without conflicting. Distinct from the
existing ledger-dedup-linter idea (that *detects* dup claims; this *prevents* the merge conflict). Worth
a capture file if the fleet pattern recurs; noted here for now.

## 📊 Doc audit (Q-0104)

- Fleet brief in `docs/planning/` ✓ (badge `plan`, reachable via the repo-structure plan pointer),
  session card ✓, claim updated in `active-work.md` ✓. `check_docs --strict` green.
- No new owner decisions, no router entry (the brief is execution guidance, not a decision).
- Ledger lag (newest-merge, marker #1050) unchanged — deferred to the #1080 reconciliation pass per the
  standing decision; not this session's drift.

## 📤 Run report

- **Did:** shipped a file-disjoint fleet coordination brief for the owner's ultracode run, produced via 3
  parallel scout agents. · **Outcome:** shipped
- **Shipped:** #1079 — `docs/planning/ultracode-fleet-plan-2026-06-19.md` + repo-structure pointer.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** `none` (lane selection is the owner's at run time).
- **⚑ Owner manual steps:** run the fleet on **desktop ultracode** by pasting the brief's kickoff prompt
  (off-repo owner action).
- **⚑ Self-initiated:** `none` (owner-requested brief; the 3 scout agents were the method, not unprompted builds).
- **↪ Next:** owner runs the fleet; the held `core/runtime → services` serial PR follows after Lane A lands.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1079, auto-merge on green) |
| Scout agents orchestrated | 3 (parallel, read-only) |
| CI-red rounds | 1 (born-red gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (collision-safe fleet claim mechanism) |
| Ideas groomed | ~16 ungated ideas/plans operationalized into buildable fleet units |
