# OWNER-ACTIONS — superbot-next control plane

Per Q-0241 nothing here blocks the build; each item gates only its own line. Everything the
agent could plausibly do via API is attempted first (settings checklist); items land here
when they 403 or are inherently owner-side.

## 1. Now / at step 8 (only if the agent's API attempts 403)

Each is Settings → the named page on https://github.com/menno420/superbot-next:

1. **General → Pull Requests**: ✅ Allow auto-merge · ✅ Automatically delete head branches ·
   ❌ Allow merge commits · ✅ Allow squash merging · ✅ Allow rebase merging.
2. **Advanced Security** (public repo, free): ✅ Secret scanning · ✅ Push protection.
3. **Security → Dependabot**: ✅ Dependabot alerts · ✅ Dependabot security updates.
4. **Actions → General → Workflow permissions**: ● Read repository contents (read-only) ·
   ❌ Allow GitHub Actions to create and approve pull requests.
5. **Rules → Rulesets → New branch ruleset → Import a ruleset** → upload `meta/ruleset.json`
   (or paste it) → Enforcement: **Active**. Do this only AFTER the six checks have reported
   green once on a real commit (see DECISIONS.md R-1).

## 2. Standing checkpoints (from the plan, restated so they don't evaporate)

- **Flip superbot-next to PRIVATE** — checkpoint at step 8, **HARD before step 15** (CUT-2
  dry-run artifacts carry real user balances). Settings → General → Danger Zone → Change
  visibility. Note: private user repos lose free secret scanning/push protection (GHAS);
  free Actions minutes also end — this is the plan's named cost checkpoint.
- **Railway project `superbot-next`** (railway plan §4/R-3): production + shadow services,
  config-as-code, sealed/reference variables — you paste secrets (bot tokens, DB URLs),
  approve plan/spend, set region pins + backups per Q-D14, create project tokens.
  `EXTRA_OWNER_USER_IDS` goes in from day one (A-21/Q-0245). **Deferred whole this step**
  unless you're present — nothing before CUT-1 (step 12) needs it.
- Standing reminder (unrelated to this repo): set `EXTRA_OWNER_USER_IDS` on the LIVE bot's
  Railway service (Q-0245).

## 3. Vetoable decisions awaiting your (optional) reaction — silence = consent

- **D-3**: CODEOWNERS routes review but does not block merges (0 required approvals). Veto =
  say so; the agent flips `require_code_owner_review: true` + `required_approving_review_count: 1`
  in the ruleset (accepting that auto-merge then waits on your approval for protected paths).
- **D-6**: Python 3.12 as the new repo's pinned interpreter.
- **D-14**: the four draft parity-exemption reason classes.
- **D-17**: A-22 grammar carrier untouched here, decided at the K2/K6 fold (per A-22 itself).

## 4. Dormant (do nothing today)

- **GitHub App for cross-repo/watcher auth**: only needed if (a) menno420/superbot flips
  private (goldens fetch then needs `contents: read` on it) or (b) the self-healing watcher
  routines return and need cross-repo writes. Creation is owner-only: Settings → Developer
  settings → GitHub Apps → New App (name e.g. `superbot-next-ops`; permissions: Contents
  read, Pull requests write; no webhook) → generate private key → install on the needed
  repos → give the agent the App ID (variable `OPS_APP_ID`) + private key (secret
  `OPS_APP_PRIVATE_KEY`). This is the no-PAT escalation path — never create a PAT.
