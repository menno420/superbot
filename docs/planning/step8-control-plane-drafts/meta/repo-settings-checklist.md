# superbot-next — repo settings checklist (step 8)

Spec §6: "Secret scanning + push protection + Dependabot security updates on at repo
creation"; rulesets (not classic branch protection); auto-delete-head-branches.
**Note (spec-vs-GitHub reality):** spec §6 lists auto-delete-head-branches in the ruleset
sentence, but it is a **repo setting**, not a ruleset field — handled in §1 below.

Legend: **[API]** = settable with a repo-scoped GitHub App installation token (or GITHUB_TOKEN
of an admin-authorized app) via the REST API/MCP — the agent can do it. **[OWNER]** = owner
click-path (or the API needs scopes the session token won't have). Verify each API call's
response; anything that 403s moves to OWNER-ACTIONS.md.

## 1. Merge + branch hygiene — [API]

`PATCH /repos/menno420/superbot-next` body:

```json
{
  "allow_auto_merge": true,
  "delete_branch_on_merge": true,
  "allow_merge_commit": false,
  "allow_squash_merge": true,
  "allow_rebase_merge": true,
  "squash_merge_commit_title": "PR_TITLE",
  "squash_merge_commit_message": "PR_BODY"
}
```

- `allow_auto_merge: true` is REQUIRED for the automerge-enabler workflow to work.
- `delete_branch_on_merge: true` = the auto-delete-head-branches item (repo setting, not ruleset).
- Merge commits off: the ruleset requires linear history; leaving merge commits enabled would
  just let auto-merge pick a method the ruleset then rejects.

## 2. Security — [API], with caveats

`PATCH /repos/menno420/superbot-next` body:

```json
{
  "security_and_analysis": {
    "secret_scanning": { "status": "enabled" },
    "secret_scanning_push_protection": { "status": "enabled" }
  }
}
```

Dependabot (two separate calls):

- `PUT /repos/menno420/superbot-next/vulnerability-alerts` (Dependabot alerts ON)
- `PUT /repos/menno420/superbot-next/automated-security-fixes` (Dependabot security updates ON)

Caveats:
- Repo is **public**: secret scanning + push protection are free and API-settable.
- ⚠ At the **flip-to-private checkpoint** (plan §5 step 8 note; HARD before step 15): secret
  scanning/push protection on a private user-owned repo requires GitHub Advanced Security
  (paid). Record the loss or budget for it at flip time — on OWNER-ACTIONS.md.

## 3. Ruleset — [API]

`POST /repos/menno420/superbot-next/rulesets` with `meta/ruleset.json` as the body.
Enforces: linear history, force-push blocked (`non_fast_forward`), main deletion blocked,
PRs required (0 approvals — see DECISIONS.md D-3 ⚑), the six required checks by exact name.
- Apply **after** the first `gates` workflow run has produced the six check names, or PRs
  opened in between cannot merge (checks "expected" but never reported). Sequencing: land the
  workflows commit → see six greens on it → apply the ruleset.
- Optional hardening: add `"integration_id": 15368` (GitHub Actions) to each required check
  so only Actions can satisfy the contexts.

## 4. Actions hardening — [API]

- `PUT /repos/menno420/superbot-next/actions/permissions/workflow` body:
  `{"default_workflow_permissions": "read", "can_approve_pull_request_reviews": false}`
  (workflows get read-only GITHUB_TOKEN unless they declare more — the automerge-enabler
  declares its own `permissions:` block).

## 5. Owner-only / deferred — see OWNER-ACTIONS.md

- Flip-to-private checkpoint (step 8 note; HARD before step 15 — CUT-2 dry-run artifacts
  carry real user balances). Also the free-Actions cost checkpoint.
- Railway project `superbot-next` (railway plan §4/R-3) — **deferred whole if owner absent**
  (nothing before CUT-1/step 12 needs it; per the kickoff brief, never block on it).
- GitHub App creation/installation for cross-repo reads **iff** menno420/superbot ever flips
  private (today it is public — verified 2026-07-07; goldens fetch needs no auth).

## 6. Deliberately NOT set

- No PAT secrets of any kind (plan §5 step 8: "PAT machinery never enters the new repo").
- No `needs-hermes-review`-style gate labels (retired, Q-0197). The only recognized label is
  `do-not-automerge` (create it: `POST /repos/.../labels {"name": "do-not-automerge",
  "color": "d93f0b", "description": "never auto-armed"}` — [API]).
- No merge queue (single-lane agent traffic; revisit if PR contention appears).
