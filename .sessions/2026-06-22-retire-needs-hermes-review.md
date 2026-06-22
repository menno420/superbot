# 2026-06-22 — Merge all open PRs + retire the `needs-hermes-review` label/rule

> **Status:** `complete`

## What happened

**Task 1 — merge all open PRs (owner-directed).** Eight open at start:
- Merged green Dependabot bumps directly: **#1309** (fastapi/dashboard), **#1311**
  (python-json-logger), **#1314** (openai).
- **#1310** (python-minor-patch group) and **#1312** (aiohttp) conflicted on
  `requirements.txt` after the above merged → triggered `@dependabot rebase` + armed
  squash auto-merge; both merged on green.
- **#1313** (youtube-transcript-api → ≥1.2.4) was **failing CI**: v1.x removed
  `YouTubeTranscriptApi.get_transcript`. Per owner decision (AskUserQuestion) I fixed the
  caller to the v1.x instance API `YouTubeTranscriptApi().fetch(id).to_raw_data()` (same
  `list[dict]` contract, confirmed via library docs), pushed to the dependabot branch, armed
  auto-merge → merged.
- **#1308** (botsite↔design-system data-contract guard): armed auto-merge → merged on green.
- **#1315** (dev-deps: ruff+pytest) appeared mid-session, merged green. *(It bumped only
  `requirements-dev.txt`, creating tool-pin drift — fixed in Task 2.)*
- **#1279** (reaction-roles PIL banner cards, `needs-hermes-review`): per owner decision
  (AskUserQuestion) merged it now, overriding the review gate.

**Task 2 — retire `needs-hermes-review` completely (owner directive Q-0197).** The label was
unused and only blocked clean merges. Removed:
- Merge-blocking mechanism: the carve-out in `auto-merge-enabler.yml`, `pr-auto-update.yml`,
  `codex-final-review.yml`, and `scripts/check_ci_coverage.py` (`CARVE_OUT_LABELS`). The
  separate `do-not-automerge` hold is **kept**.
- The CLAUDE.md rule (owner-directed in-session → applied directly, provenance Q-0197).
- The dedicated Hermes `review-merge` skill (its only purpose was this queue): deleted the
  source doc + generated `SKILL.md` + `build_skills.py` EXTRAS, regenerated the skill set
  (15 skills), updated the hermes-skills docs and `dispatch_menu.py`.
- Active-policy references in `current-state.md`, `autonomous-routines.md`,
  `hermes-control-plane.md`, `hermes-dispatch-bridge.md`, `roadmap.md`, `repo-sector-map.md`,
  `subsystems/ai.md`, the settings map, and the creature-game forward-looking comments.
- Recorded Q-0197 in the router. Immutable history (`.sessions/`, reconciliation passes, idea
  files, dashboard data) left as written.
- **Drift fixed on sight (Q-0166):** deleted the stale #1279 claim file; reverted #1315's
  `requirements-dev.txt` drift (ruff/pytest/pytest-xdist) back to the workflow's proven-green
  pins to restore 3-way parity (ruff 0.15.18 also introduced a false-positive `ERA001` on
  `botsite/app.py` prose, so down-aligning to 0.15.14 was the safe call).

**Owner action remaining:** delete the `needs-hermes-review` GitHub *label* in repo Settings →
Labels (now unreferenced and harmless; no MCP tool to delete it).

## Verification
- `check_quality.py --check-only` ✓ (black/isort/ruff/tool-pins/docs/consistency)
- `check_quality.py --full` ✓ · `check_architecture.py --mode strict` ✓
- affected unit tests (build_skills freshness, dispatch_menu, check_ci_coverage) ✓
- mypy disbot/ ✓ (782 files) · youtube tests 37 passed

## ⚑ Self-initiated
None beyond the owner-directed tasks. The rule removal + drift fixes were owner-directed /
fix-on-sight, not self-initiated feature work.

## 💡 Session idea
**A `check_tool_pins`-style CI gate (or Dependabot config scope) for the 3-way version pins.**
#1315 merged a Dependabot bump that touched only `requirements-dev.txt`, silently drifting from
`code-quality.yml` + `.pre-commit-config.yaml` — CI stayed green (it uses the workflow pins) so
nothing caught it; only a local `check_quality.py` run surfaced it. Either run `check_tool_pins`
as a CI step, or configure Dependabot to update all three pin locations together (or ignore the
formatter/linter group so bumps are deliberate). Worth an idea file.

## ⟲ Previous-session review
The previous session (#1306, role-list colours) shipped cleanly. What the broader recent chain
*missed* and this session had to clean up: Dependabot dev-dep PRs are being merged without
completing the 3-way pin bump, and `needs-hermes-review` PRs (like #1279) were left to sit
open — both are "merge hygiene" gaps. **System improvement surfaced:** the auto-merge carve-out
for an unused label was pure friction; retiring it (this session) plus the pin-gate idea above
both reduce the manual merge-babysitting the owner keeps hitting.

## Doc audit
Merged PRs this session (#1308–#1315 + #1279) belong in the living ledger — the next
reconciliation pass (#1320) records them; `check_current_state_ledger.py --strict` stays green
because those merges are newest-merge lag (benign per Q-0166), not pre-marker drift.
