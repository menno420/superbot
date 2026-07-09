# Per-repo settings state ledger

> **Status:** `reference` · Phase 1 (manual capture) of
> `docs/planning/per-repo-settings-state-ledger-2026-07-08.md`.
> **So future sessions read the state instead of guessing.** Cross-repo: `superbot` (live),
> `substrate-kit`, `superbot-next` (both bootstrapped 2026-07-08).

## How this doc is maintained (read before trusting a row)

Captured **manually** on 2026-07-08 — the `superbot-next` General-settings rows are **verified
from the owner's screen recording**; `substrate-kit` and `superbot` are marked as the owner is
applying the **same** settings uniformly (confirm before relying on a per-repo value). The GitHub
MCP tools available to a session **cannot read** merge/branch toggles, rulesets, or branch
protection — only visibility + default branch — so this ledger is hand-maintained until Phase 2
(a `scripts/generate_repo_settings_state.py` that queries the API) lands. **That read-visibility
gap is itself an EAP finding** (an agent can't introspect the repo config it operates under).

## General settings (verified from the 2026-07-08 recording; applied uniformly)

| Setting | superbot | substrate-kit | superbot-next |
|---|---|---|---|
| Visibility | Public | Public | **Public** ✓ |
| Default branch | `main` | `main` | **`main`** ✓ |
| Template repository | No | No | **No** ✓ |
| Issues | On | On | **On** ✓ (create: all users) |
| Projects | On | On | **On** ✓ |
| Pull requests | On | On | **On** ✓ (create: all users) |
| Discussions | Off | Off | **Off** ✓ |
| Sponsorships | Off | Off | **Off** ✓ |
| Wiki — restrict editing to collaborators | On | On | **On** ✓ |
| Preserve repository (Archive Program) | On | On | **On** ✓ |
| Allow merge commits | On | On | **On** ✓ |
| Allow squash merging | On | On | **On** ✓ |
| Allow rebase merging | On | On | **On** ✓ |
| Always suggest updating PR branches | On | On | **On** ✓ |
| **Allow auto-merge** | On | On | **On** ✓ |
| **Automatically delete head branches** | On | On | **On** ✓ |
| Require sign-off on web commits | Off | Off | **Off** ✓ |
| Allow comments on individual commits | On | On | **On** ✓ |
| Include LFS objects in archives | Off | Off | **Off** ✓ |
| Limit branches/tags per push | Off | Off | **Off** ✓ |
| Auto-close linked issues on merge | On | On | **On** ✓ |

✓ = verified from the recording (superbot-next). Other columns = owner replicating to match —
**confirm per repo.**

## Rules / branch protection / required checks

**Updated 2026-07-09** — `superbot-next` and `substrate-kit` both now have a `main-branch-protection`
ruleset (owner-created via the directing session's runbook, verified from the owner's screen
recordings — the GitHub MCP tools available to this session still cannot read rulesets back, so
this row is manual-confirm same as the rest of this doc until Phase 2 lands).

| Aspect | superbot | substrate-kit | superbot-next |
|---|---|---|---|
| Required status check(s) | `Code Quality` (the auto-merge gate) + `CodeQL`; `codex-final-review` advisory | `Kit test suite`, `Cold-adoption smoke (adopt + check --strict)` | `tests, ci`, `checkers, ci`, `lockfile-fresh, ci`, `pip-audit`, `gate, golden-parity` (never `report, golden-parity` — that job is red-until-parity by design) |
| Ruleset / approvals | single-owner (no required approvals) | `main-branch-protection`, Active, 0 required approvals, **Require review from Code Owners: off** (kept consistent with the CI-only-gate model everywhere else in this program), bypass list empty | same shape as substrate-kit |
| Workflows / Actions | full CI suite | `ci.yml` (2 jobs) | `ci.yml` (4 jobs), `golden-parity.yml` (2 jobs, `report` intentionally red), `backup-db.yml`, `restore-verify.yml` |
| CODEOWNERS | n/a (single-owner) | `.github/CODEOWNERS` — blanket `* @menno420`, present but **not enforced** (review not required) | same |
| Delete-protection | branch deletion is auto-mode-walled regardless (see capability facts) | same | same |

## Automation / tokens

- **`ROUTINE_PAT`** (real fine-grained PAT) drives `auto-merge-enabler`, `ci-rerun-watchdog`,
  `pr-auto-update`, `reconciliation-trigger` on **superbot** — needed because app/integration-token
  actions don't fire workflows. **`substrate-kit` / `superbot-next`: still none.** Neither repo has
  an `auto-merge-enabler` workflow yet (a gap flagged back to the coordinator, not yet fixed) — PRs
  there merge via direct API call by whichever session is driving, not native GitHub auto-merge.
  Adding `ROUTINE_PAT` + the enabler workflow is a prerequisite for that to change.

## Dependabot PR policy (owner decision Q-0256, 2026-07-09)

Dependabot PRs land on `dependabot/*` branches, so the `auto-merge-enabler` never arms them —
**by design** (`.github/dependabot.yml` provenance comment); they have no merge actor until a
session acts. The owner's standing rule:

- **Review-on-sight, then merge.** The *first* session that sees an open dependabot PR reviews
  it — diff + upstream changelog/breaking-changes check + grep of the repo's *actual* usage of
  the package — and merges it (squash; **CI green on the final head** required, as always).
  An open dependabot PR is unclaimed work for whoever sees it; don't leave it for later.
- **Major version bumps:** assess the breaking changes against real usage. Contained
  adaptation → **fix it, then merge** (green CI on the dependabot head is itself the evidence
  when no code change is needed — CI installs the bumped floor and runs the full suite). Too
  large for this session → **don't merge**; write a dedicated-session work item
  (`docs/planning/` or `docs/ideas/`) and note it on the PR.
- Grouped PRs from different ecosystems can overlap (root pip vs `/dashboard` pip both touched
  `dashboard/requirements.*` in #1761/#1762) — check whether one diff is a superset before
  calling them duplicates; merge the superset, close the subset with a one-line comment.
- Merging = deploying (Q-0193) applies unchanged. Extending the enabler workflow to auto-arm
  dependabot PRs was considered and **not** shipped — proposal + rationale: router Q-0257.

## Auto-mode capability facts (what a session can/can't do — the walls)

Full evidence: `docs/planning/projects-eap-permission-probe-report-2026-07-08.md`.

| Action | Autonomous session? | Clears how |
|---|---|---|
| Read / local write / outbound net / `pip install` | ✅ allowed | — |
| Push a **new** branch to an existing repo | ✅ allowed | — |
| GitHub Contents API — create / update / **delete** a file, incl. first-commit **and `.github/workflows/*`** | ✅ allowed | bypasses the git-push publish wall; no workflow-scope block (all confirmed 2026-07-08) |
| First-publish to an empty **public** repo via `git push` | ❌ denied | human, token-backed Action, or the Contents-API path above |
| Force-push / remote-branch delete (`git push` ref-rewrite) | ❌ denied (2 layers) | present operator clears the classifier; the git credential still 403s — no in-session path |

**Implication for standing up the new repos:** the entire **file/content layer** — source, all
`.github/workflows/` CI, scripts, config, docs, kit content — is agent-doable via the Contents API
(create/update/delete). Only the **settings layer** (rulesets, branch protection, required checks,
General toggles, secrets/PATs) is owner-only. So the new-repo build is ~90% agent-doable; the
git-ref *rewrite* walls (force-push, branch-delete) do not affect this file-layer work.

## Next

Phase 2 = `scripts/generate_repo_settings_state.py` (auto-regenerate the API-readable rows).
Phase 3 = optional dev-website panel. Plan: `docs/planning/per-repo-settings-state-ledger-2026-07-08.md`.
