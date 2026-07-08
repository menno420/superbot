# superbot-next — token & auth posture (design-spec §6)

**The rule (plan §5 step 8, hard):** *"PAT machinery never enters the new repo."* No PAT
secrets, no PAT-based workflows, nothing that assumes a PAT will exist — the verified
7-workflow `ROUTINE_PAT` single-point-of-failure of the old repo does not carry over.

## 1. What workflows use instead

**The default `GITHUB_TOKEN` with least-privilege `permissions:` blocks — nothing else.**

Spec §6 says "OIDC / GitHub-App auth for every workflow that acts on the repo." Reading,
made concrete here: `GITHUB_TOKEN` **is** a GitHub-App installation token (the built-in
`github-actions` app), minted per-job, auto-expiring, permission-scoped by the workflow's
`permissions:` block. It satisfies the spec's GitHub-App clause with zero secrets to rotate:

| Workflow | permissions | Why |
|---|---|---|
| `gates.yml` (all six required checks; triggers: `pull_request`, `push` to main, `schedule` every 6h + `workflow_dispatch` — the scheduled run is the merge-race backstop, DECISIONS.md D-22) | `contents: read` | gates only read the tree (+ public oracle fetch, unauthenticated) |
| `automerge-enabler.yml` (triggers: PR `opened`/`ready_for_review`/`labeled`/`unlabeled` — arm on open, disarm on `do-not-automerge`, re-arm on label removal) | `contents: write`, `pull-requests: write` | `gh pr merge --auto` / `--disable-auto` need both |

Repo-level default is hardened to read-only (settings checklist §4), so a future workflow
that forgets a `permissions:` block gets read-only, not write.

OIDC proper (`id-token: write` + a cloud trust policy) is for keyless auth **to external
clouds**. Railway does not consume GitHub OIDC for deploys — it deploys via its own GitHub
integration watching pushes — so no workflow needs `id-token` today. If a future workflow
must call an external cloud, OIDC federation is the required path; a long-lived cloud key
in a secret is the PAT pattern wearing a different hat.

## 2. Self-healing watcher routines (later)

Spec §6 carries over "the self-healing watcher routines (re-authored on app tokens as
versioned `WorkflowRoutineSpec`s)". When those land (post-kernel), anything `GITHUB_TOKEN`
cannot do from inside the repo (cross-repo writes, workflow-triggering merges) uses a
**dedicated GitHub App** (owner-created once, OWNER-ACTIONS.md §4) with
`actions/create-github-app-token` minting short-lived installation tokens from an App ID
variable + private-key secret. An App private key is not a PAT: it is revocable per-app,
permission-scoped at install time, mints 1-hour tokens, and survives no user account.

## 3. Known GITHUB_TOKEN limitations (accepted, documented)

1. **Merges armed by `GITHUB_TOKEN` don't trigger downstream workflows** — the push to main
   from auto-merge is attributed to `github-actions`, so the push-triggered `gates` run may
   not fire. Accepted: the six required checks already gated the PR (that is the merge
   condition). Because the ruleset also keeps `strict_required_status_checks_policy: false`
   (D-13), two individually-green PRs that collide only in combination could land with **no
   on-main CI signal at all** — the residual §3.2 merge-race gap. Mitigation: the `gates`
   workflow runs on a **6-hourly schedule + `workflow_dispatch`** on main (DECISIONS.md
   D-22), so a landed collision is detected within hours, loudly, instead of never. If a
   merge-must-rerun need appears later, the dedicated App (§2) arms auto-merge instead —
   never a PAT.
2. **Fork PRs get a read-only token** — enabler skips forks; this repo's writers push
   branches. Required checks still run on fork PRs (read-only is enough for all six gates).
3. **Label-disarm has a race window** — `do-not-automerge` applied after arming is honored
   by the enabler's `labeled` job calling `gh pr merge --disable-auto` (GITHUB_TOKEN is
   sufficient: `pull-requests: write` covers the disable mutation). Between the label click
   and that job completing, a PR whose checks go green can still merge. Accepted: the label
   is a brake for humans reacting in minutes, not a transactional lock; the true block for
   never-merge work is closing the PR.

## 4. The cross-repo goldens read (gate 5)

**Verified 2026-07-07 via the GitHub API: `menno420/superbot` is PUBLIC**
(`"private": false`, `"visibility": "public"`). Design as shipped:

- `run_golden_parity.py` fetches `https://github.com/menno420/superbot.git` at the exact
  SHA pinned in `parity/goldens-source.lock` (`git fetch --depth 1 <url> <sha>`), read-only,
  **no credential of any kind**. The goldens are never copied into superbot-next
  (spec §6: "the goldens live outside the new repo's write reach").
- **Contingency, pre-designed (⚑):** if superbot ever flips private, the fetch 404s and the
  gate goes red loudly (fail-closed — it cannot silently pass). The fix is the §2 App:
  install it on `menno420/superbot` with `contents: read`, add
  `actions/create-github-app-token` before the fetch, pass the token in the fetch URL.
  Never a PAT. Recorded in OWNER-ACTIONS.md §4 as a dormant item.

## 5. superbot-next is PUBLIC — secrets discipline

Nothing sensitive exists in this control plane: no tokens, no user data, no guild ids.
The flip-to-private checkpoint (before CUT-2 artifacts, HARD before step 15) is when real
data first approaches the repo; the settings checklist carries the GHAS caveat for that flip.
