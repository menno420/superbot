# 2026-06-19 — Codex reviews the final head, not the born-red opener

> **Status:** `complete`

## Arc

Owner asked (in-session): does Codex re-review a PR after the final commits, and would it be a good
idea to (a) explain the born-red card to Codex so it stops re-flagging it, or (b) make every final push
`@codex review` for a forced review on the final head. Investigate → recommend → build the chosen path.

## Finding (verified empirically on live PRs)

**Codex reviews only the opening commit and never re-reviews after the final push.** Its trigger set is
exactly three events — *PR opened · draft marked ready · `@codex review` comment*; **a plain push is not
a trigger.** In the born-red flow the PR opens on the card-first commit before the code lands, so:

- **#1097** (code PR): Codex reviewed the opener `51b0a6e…` and left a **P1 "mark the session card ready
  before merge"** — a pure born-red false positive (the card is *meant* to be `in-progress` at open) —
  now `is_outdated`; it **never reviewed** the final head `da4df4f…`.
- **#1100** (docs PR): same — reviewed the born-red opener, never the final content commit; auto-merged.

So idea (a) "explain the red card" is weak (Codex reviews the incomplete opener regardless, and the PR
body *already* says "born-red"); idea (b) `@codex review` on the final head is the correct fix — it's a
documented trigger and the only way to point Codex at the complete diff. Owner picked: **automated
Action + accept post-merge review.**

## Shipped (PR #1105)

- **`.github/workflows/codex-final-review.yml`** — on `pull_request` `synchronize`/`ready_for_review`,
  for `claude/*` non-draft PRs (carve-outs mirror `auto-merge-enabler`), posts `@codex review` when the
  session card flips to a ready status. Idempotent via a hidden `<!-- codex-final-review -->` marker.
  SHA-pinned `actions/checkout` (post-#1088). Q-0105 disposable header.
- **`scripts/check_session_gate.py --require-ready-card`** — the precise "card just flipped to complete"
  signal (exit 0 only when an added card exists *and* none are held). Reuses the tested born-red logic;
  4 new unit tests. `check_quality.py --check-only` green (CI mirror).
- **Docs:** router **Q-0180** (decision + empirical proof) · Codex idea doc marked **BUILT**.

## Context delta

- **The merge race is real and accepted.** The card-flip-to-green is *also* what releases auto-merge, so
  `@codex review` usually lands as the PR merges → Codex reviews the **merged** PR. That's by design:
  Q-0174 already makes routines scan recently-merged PRs for Codex comments and fix real ones first. This
  is a second reviewer *for the next session*, not a pre-merge gate (owner chose this over holding every
  merge on an external bot's latency).
- **Why an Action over a CLAUDE.md rule:** deterministic (no reliance on the agent remembering), fires
  exactly on the final-head signal, and CLAUDE.md is owner-directed-only anyway. The Action keys off the
  *existing* born-red card signal, so it needs no new convention.

## ⟲ Previous-session review (Q-0102)

**#1103 (`router_status.py`) — strong, self-aware tooling:** it removed a real recurring friction (find
the next Q / scan OPEN) and was honest about its own UNCLASSIFIED limit (Q-0120). **What the chain
missed until now:** the Codex final-head gap has been a known "still open" item since Q-0171/Q-0174 + the
#1031 session idea, yet sat unbuilt across many sessions while everyone treated its born-red false
positives as noise to ignore. **System improvement (built into this session):** when a known
workflow-friction item is *captured as an idea but keeps recurring as live noise* (here: Codex re-flagging
born-red cards every PR), that recurrence should itself promote the idea to a build — the cost of the
workaround (every agent mentally discarding the P1) exceeded the cost of the fix. The idea gate is open
(Q-0172); recurring noise is a build signal.

## 💡 Session idea (Q-0089)

**Suppress Codex's born-red P1 at the source via a tiny PR-body or first-comment note that Codex reads.**
Even with final-head review, Codex still wastes its *opening* review on the born-red card. Idea: have the
born-red opening commit's PR body carry a machine-readable `<!-- born-red: implementation lands in a
follow-up commit; review deferred to final head -->` line, and research whether Codex's connector honours
a "skip until ready" hint (some review bots do). If it does, we stop the opening false-positive entirely
rather than only adding a second, correct review. Distinct from this session's build (which fixes the
*final* review, not the *opening* one). Small research spike first — believe in it because the opening
P1 is pure wasted Codex spend on every single born-red PR.

## 📊 Doc audit (Q-0104)

- New files: a workflow + a script flag + tests; docs updated = router Q-0180 + the idea doc. No new
  `docs/**` page needs a reachability link (`check_docs` unaffected). The workflow self-documents
  (header) and advertises its Q-0105 deletion criteria.
- Ledger: only benign newest-merge lag (#1095…#1104, newer than the #1094 marker → the #1110
  reconciliation pass's job; a manual session does not run it, Q-0124). Not this session's drift.

## 📤 Run report

- **Did:** investigated whether Codex re-reviews after final commits (it does not — verified on
  #1097/#1100), then built the owner-chosen fix: an Action posting `@codex review` on the session-card
  flip so Codex reviews the complete diff. · **Outcome:** shipped.
- **Shipped:** #1105 — `codex-final-review.yml` + `check_session_gate.py --require-ready-card` + tests +
  router Q-0180 + idea-doc BUILT mark.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** `none` — Q-0180 decided in-session. Optional later: revisit holding the
  merge for Codex (rejected now) once its post-merge catches prove valuable.
- **⚑ Owner manual steps:** `none` — `ROUTINE_PAT` already covers PR-comment scope (same as
  auto-merge-enabler); GITHUB_TOKEN is a working fallback for the comment.
- **⚑ Self-initiated:** partial — the *build* was owner-directed (Q-0180); the doc/idea-doc reconciliation
  and the Q-0089 idea are the standard self-initiated session enders.
- **↪ Next:** watch the first few `claude/*` PRs to confirm the Action fires once, on the final head, and
  Codex re-reviews the complete diff (Q-0105 verification). Then the born-red opening-P1 suppression idea.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1105, auto-merge on green) |
| New workflow | `.github/workflows/codex-final-review.yml` (Q-0105) |
| Script flag added | `check_session_gate.py --require-ready-card` |
| Tests added | 3 (14 total in the file, all green) |
| Codex behaviour verified on | #1097, #1100 (reviews opener only, never final head) |
| CI-red rounds | 1 (born-red gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (suppress the born-red opening P1 at source) |
