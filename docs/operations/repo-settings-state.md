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

## Rules / branch protection / required checks (NOT in the recording — confirm)

| Aspect | superbot | substrate-kit | superbot-next |
|---|---|---|---|
| Required status check(s) | `Code Quality` (the auto-merge gate) + `CodeQL`; `codex-final-review` advisory | TBD | per step-8 decisions — confirm live |
| Ruleset / approvals | — | TBD | **0 required approvals** (a required review would deadlock single-owner auto-merge), strict status checks off + a 6-hourly `main` backstop (`staging/step8-control-plane-drafts` `DECISIONS.md`) |
| Delete-protection | branch deletion is auto-mode-walled regardless (see capability facts) | same | same |

## Automation / tokens

- **`ROUTINE_PAT`** (real fine-grained PAT) drives `auto-merge-enabler`, `ci-rerun-watchdog`,
  `pr-auto-update`, `reconciliation-trigger` on **superbot** — needed because app/integration-token
  actions don't fire workflows. New repos: **TBD** whether they carry the same automation set.

## Auto-mode capability facts (what a session can/can't do — the walls)

Full evidence: `docs/planning/projects-eap-permission-probe-report-2026-07-08.md`.

| Action | Autonomous session? | Clears how |
|---|---|---|
| Read / local write / outbound net / `pip install` | ✅ allowed | — |
| Push a **new** branch to an existing repo | ✅ allowed | — |
| GitHub-API object create (issue, **file/first-commit**) | ✅ allowed | — the API bypasses the git-push publish wall (2026-07-08) |
| First-publish to an empty **public** repo via `git push` | ❌ denied | human, token-backed Action, or the API path above |
| Force-push / remote-branch delete (`git push`) | ❌ denied (2 layers) | present operator clears the classifier; the git credential still 403s — no in-session path |

## Next

Phase 2 = `scripts/generate_repo_settings_state.py` (auto-regenerate the API-readable rows).
Phase 3 = optional dev-website panel. Plan: `docs/planning/per-repo-settings-state-ledger-2026-07-08.md`.
