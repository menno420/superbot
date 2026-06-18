# Session — fix the deploy-freezing dashboard-data-refresh workflow

> **Status:** `complete`

## What happened (the diagnosis)

The owner reported the fishing commands didn't work / no fishing cog in the live bot.
Using the read-only Railway API (`scripts/hermes/railway_logs.py`), I found production
was **frozen on deployment #1036** (00:37 UTC) — every deploy since (incl. #1033, which
adds the fishing cog) was Railway-status **`SKIPPED`**. The running deployment's boot log
confirmed no `FishingCog` loaded; a full **local boot** confirmed the code is correct
(FishingCog + migrations 075/076 load cleanly, commands register).

**Root cause:** the `dashboard-data-refresh` workflow (added yesterday, #1026/Q-0167)
`git push`es the regenerated `dashboard.json` straight to `main`. The `main` branch
ruleset requires the `code-quality` status check on any pushed commit, so GitHub rejects
the bot's direct push (`GH013`). The workflow therefore **failed on every merge**, turning
each commit's CI check-suite red — and Railway's "wait for CI before deploy" setting waits
for the **whole** suite, so one red check **silently SKIPPED every deploy**. This explains
the owner's "why only now": "wait for CI" was fine for 2 days until #1026 added a workflow
that can't satisfy its own ruleset.

The owner unblocked deploys immediately by disabling Railway's "wait for CI" (fishing is
now live — verified `FishingCog LIVE in prod` on deployment #1044). This PR fixes the
**workflow** so it stops failing and actually works.

## What shipped

Rewrote `.github/workflows/dashboard-data-refresh.yml`:

- **PR-flow instead of direct push.** It now lands the refresh through a normal PR that
  **auto-merges** once `code-quality` is green (`gh pr merge --auto --merge` with
  `ROUTINE_PAT`, the same mechanism `auto-merge-enabler.yml` uses). This is the only path
  that satisfies the `main` ruleset without a privileged push — **no GitHub-settings change
  required**. It reuses one branch (`bot/dashboard-refresh`), so at most one refresh PR is
  ever open.
- **Scheduled (every 2h) + `workflow_dispatch`, not per-merge.** This keeps the site fresh
  within the interval, bounds noise to ≤1 auto-PR per run, and — critically — **removes the
  per-merge failures and the deploy landmine entirely**: the workflow no longer runs in any
  commit's check-suite, so it can never re-freeze deploys, even if "wait for CI" is
  re-enabled (which becomes safe again).
- **Documented the optional zero-PR upgrade**: if the owner adds the bot identity to the
  `main` ruleset's bypass list, it could direct-push invisibly (no auto-PRs). Self-contained
  PR-flow until then.

`export_dashboard_data.py` is stdlib-only (verified) so the CI job needs no `pip install`.
YAML validated; export runs clean.

## 💡 Session idea

**A read-only "deploy health" line in the routine SessionStart banner.** This whole outage
was invisible for ~9h because nothing surfaced "production is N deploys behind / last deploy
SKIPPED." `scripts/hermes/railway_logs.py` already exposes deployment status read-only; a
tiny `scripts/hermes/deploy_status.py` that prints "prod = deployment #X (SUCCESS, 3h ago);
HEAD is #Y — N commits ahead, last deploy SKIPPED" in the SessionStart hook would catch a
frozen/failed deploy on the next routine run instead of waiting for the owner to notice.

## ⟲ Previous-session review

The previous step (the fishing arc) did everything right *in the repo* — code correct,
tested, merged — yet the feature never reached users because of an **infra failure two
layers away** (a sibling workflow + a Railway setting). The lesson: "merged + CI-green" is
not "live." A routine that ships user-facing features should **verify the deploy landed**,
not just the merge — exactly the deploy-health idea above. Also: the `dashboard-data-refresh`
workflow was merged (#1026) flagged "UNVERIFIED — watch the first few merges"; nobody did,
and it silently broke deploys. The Q-0105 "watch unverified tooling" instruction needs a
teeth — the deploy-health line would have been that teeth.

## 📤 Run report

- **Did:** root-caused a ~9h production deploy freeze to the `dashboard-data-refresh`
  workflow's un-pushable direct-push-to-main, and rewrote it to a self-contained
  auto-merging PR-flow (scheduled, loop-safe, never reddens CI) · **Outcome:** shipped
- **Shipped:** the workflow rewrite (this PR). Owner separately unblocked deploys by
  disabling Railway "wait for CI"; fishing verified live on prod (#1044).
- **⚑ Self-initiated:** owner-directed ("make it actually work properly, also improve it").
- **⚑ Owner decisions needed:** optional — add the bot to the `main` ruleset bypass list for
  a zero-PR (invisible direct-push) refresh; otherwise the PR-flow is fully self-contained.
  Re-enabling Railway "wait for CI" is now safe (this workflow no longer fails per-merge).
- **⚑ Owner manual steps:** `none` required (the fix is self-contained). Optional bypass above.
- **↪ Next:** consider the deploy-health SessionStart line (idea above); the ledger has
  drift (#1038–#1044) for the next reconciliation pass (due at #1050).
- **Run type:** `routine · dispatch`
