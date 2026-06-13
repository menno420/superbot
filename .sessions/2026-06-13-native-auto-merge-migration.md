# 2026-06-13 — Native auto-merge migration (merge mechanics off the Claude session)

**Shipped (all merged):** #779 (`auto-merge-enabler` workflow) · #786 (strip self-merge envelope
from CLAUDE.md + router **Q-0123**). Builds on #778 (routine-trigger `ROUTINE_PAT` fix, this
session's earlier phase).

## What & why

Started from the owner's report that the autonomous routines weren't booting. Root cause:
**`ROUTINE_PAT` did not exist** — the #778 routine-trigger fix depends on a real-user PAT to make
Action-created issues fire downstream workflows, but the secret was never populated (confirmed
live with the owner: *"it didn't exist yet"*). So the #778 fix had been inert.

The owner then directed, in-session, that **merging be removed from Claude's side entirely**
("completely remove merging from claude's side") and chose **"Native auto-merge + enabler"** (via
AskUserQuestion). Delivered as 2 PRs:

- **#779** — `.github/workflows/auto-merge-enabler.yml`: arms GitHub-native auto-merge on every
  non-draft `claude/*` PR at open. Carve-outs: `needs-hermes-review` (Q-0117) / `do-not-automerge`
  (Q-0114). Uses `ROUTINE_PAT` (not `GITHUB_TOKEN`) so the merge attributes to a real user →
  keeps `reconciliation-trigger.yml` (on: push to main) firing — the #778 bot-author gotcha.
- **#786** — strips the Q-0084 manual self-merge envelope from `.claude/CLAUDE.md` (always-loaded
  context savings) → native-auto-merge model; records **Q-0123** (provenance; supersedes Q-0084;
  preserves Q-0103; + the defense-in-depth behavior rule: re-verify CI on the final head before
  any *residual* hand-merge, and never defer a merge to the maintainer's next message — the #778
  root cause).

**Owner one-time setup (guided live, all confirmed):** *Allow auto-merge* ON · `main` requires the
`code-quality` check · a fresh fine-grained `ROUTINE_PAT` (Contents + Issues + Pull requests R/W,
scoped to superbot).

**Proof:** #786 merged itself hands-off in ~15 s — `enable-auto-merge` armed it, `code-quality`
passed, GitHub merged, `merged_by: menno420` (PAT attribution correct). End-to-end confirmation of
all three setup steps. (`code-quality` is path-aware: ~3 min on code #779, ~6 s on docs-only #786.)

## Follow-up (handed off)

- `self-merge on green` wording still lives in `docs/operations/autonomous-routines.md` (routine
  prompts) + several `.sessions/` logs / idea docs → reconcile to "auto-merge on green" in the next
  Q-0107 sweep (noted in Q-0123). Not chased across ~40 files here.
- Live routine-boot verification deferred — the PAT now exists with correct scopes (#786's merge
  proves it triggers workflows + merges); a routine run would confirm the issue-trigger path
  end-to-end.

## 💡 Session idea (Q-0089) — Auto-merge health beacon

A tiny scheduled assertion (or a line in the existing nightly) that the last N `claude/*` PRs
actually *merged* (not stuck "auto-merge enabled, waiting") and that recent `main` merges are
attributed to a real user, not `github-actions[bot]`. Native auto-merge is now load-bearing and
**silent** — its failure mode (a lapsed/expired `ROUTINE_PAT`, a toggled-off setting) strands PRs
invisibly. A beacon makes it loud. Candidate for a `docs/ideas/` file next session.

## ⟲ Previous-session review (Q-0102)

The routine-trigger fix (#778) correctly diagnosed the "Action token doesn't trigger workflows"
class and wired `ROUTINE_PAT` — but **shipped depending on a secret it never verified existed**, so
it was inert until today. **System improvement surfaced:** a PAT-backed workflow should fail
*loudly* when its required secret is missing. The enabler does (`::warning::`); the routine triggers
failed silently. Concrete seed → the 💡 beacon above; minimally, a "required secret present?" line
in routine-workflow run summaries so an absent/expired secret is never silent again.

## Housekeeping

Grooming pass (Q-0015) deferred at the owner's request to keep this close short; backlog is healthy
(the decade queue #781–#800 is freshly planned by today's reconciliation pass). Doc audit:
`check_quality --full` green (9305 passed) on the #786 head; `check_current_state_ledger --strict`
green; current-state stamp line updated with this migration.
