# Website two-site split — rollout + next-steps handoff (2026-06-19)

> **Status:** `living-ledger` — the forward-looking companion to the build review
> ([`website-split-review-2026-06-19.md`](website-split-review-2026-06-19.md)). What is **done**, what
> is **left**, and **ideas**, so the next session (or the owner) can pick up without re-deriving state.
> Source + merged PRs win. Tick items off / re-home them as they land.

## 1. Done (merged) — the v1 build is code-complete + reviewed

The plan ([`../planning/website-two-site-split-plan-2026-06-19.md`](../planning/website-two-site-split-plan-2026-06-19.md))
§5 decomposition fully shipped, then hardened by the ultracode review (PR #1122):

- **Foundation** S1/S2/P1 (#1109) · **back half** S1.1/P2/P3/P4/P5/P6/P7/P8 (#1112–#1119).
- **Review pass (#1122):** proved the 4 hard invariants (decoupling · fail-closed redaction · security ·
  dormant-by-default) and fixed 4 defects — the test-isolation `sys.modules` collision
  (`tests/support/web_app_loader.py`), the `_clean` C1 control-char gap, the `chain` idea-mis-map (the new
  explicit `> **Subsystem:**` tag), and the `env-vars.md` web-tier marker drift. Full record:
  [`website-split-review-2026-06-19.md`](website-split-review-2026-06-19.md).

**State:** both web apps are **dormant-by-default** — safe no-ops until their env is set. Nothing is live yet.

## 2. Left to do

### 2a. Owner decisions — the 3 review flags (each a quick yes/no)
- [ ] **Moderation approve double-file race** — two concurrent approves could file two GitHub issues (DB
  guards stop double-status/url, not double-issue). *Recommend: accept for v1* (single owner + CSRF +
  rate-limit). Alt: a transient `mirroring` status before `create_issue`.
- [ ] **Web-CI matrix consolidation** — `dashboard-ci.yml` + `botsite-ci.yml` → one `web-ci.yml` matrix +
  extract the auto-managed-PR predicate. Designed in
  [`../planning/web-tier-centralization-proposal-2026-06-19.md`](../planning/web-tier-centralization-proposal-2026-06-19.md).
  *Clean win; buildable as its own both-legs-verified PR on greenlight.*
- [ ] **Full idea→subsystem mapping** — the *mechanism* shipped; mapping all ~80 ideas
  ([`../ideas/idea-to-cog-command-mapping-2026-06-19.md`](../ideas/idea-to-cog-command-mapping-2026-06-19.md))
  is the owner-paced batch. Confirm it should be pursued in batches.

### 2b. The rollout — turns the build into a live website (owner/infra; plan §6 + [`botsite-deploy.md`](botsite-deploy.md))
- [ ] Provision the **new Railway service**, Root Directory = `botsite/` (own `requirements.txt` + `Procfile`;
  honor the no-`static/` gotcha). Dark-launch on the Railway URL first — verifiable in prod, not "the website" yet.
- [ ] Provision the **dashboard-owned submissions Postgres**; apply `botsite/migrations/001_submissions.sql`
  (idempotent `CREATE TABLE IF NOT EXISTS`).
- [ ] Set env vars per the **Website tier** section of [`env-vars.md`](env-vars.md): `SUBMISSIONS_DB_DSN`
  (INSERT-only role on the public site, full role on the dev site), `SUBMISSIONS_IP_SALT`,
  `GITHUB_ISSUE_MIRROR_TOKEN` (dev-site only; fine-grained PAT, repo-scoped to `menno420/superbot`,
  **Issues: Read & write only**).
- [ ] Verify the dark site, then **cut over the marketing domain**. **Rollback at every step:** delete/pause
  the service · `DROP TABLE submissions` · revert DNS. The dev site is untouched throughout (additive).

### 2c. Deferred-by-design slices — gated on ONE prerequisite
- [ ] **The control-API public-exposure security review** (plan §3 / §4.4 / §7.2 / §7.4) — unlocks both:
  - [ ] The per-server **control-panel migration** to a gated bot-side "manage my server" service (Q-0179),
    isolated as its own Railway service (own process/secret scope).
  - [ ] The **live status aggregator** — the dev site polls the bot's private `/control/ping`, redacts to a
    tiny `{online, build_sha, checked_at}` shape, and exposes a public cached `/status.json` the bot site
    reads. (v1 `/status` is generated build-meta, honestly labelled "as of last deploy".)

### 2d. Future enhancements (separate ideas — each needs a plan before building)
- [ ] **Per-command feedback threads**
  ([`../ideas/per-command-feedback-threads-2026-06-19.md`](../ideas/per-command-feedback-threads-2026-06-19.md))
  — AI-moderated inline threads per command; supersedes the v1 null `notes`. The command-detail view already
  has the drop-in seam (the Notes block in `botsite/templates/_command_detail.html`).
- [ ] Optional `/submit` **captcha** (Turnstile/hCaptcha) — only if honeypot + rate-limit proves insufficient
  (env names already reserved in the env-vars Website tier).

## 3. Suggestions / ideas (prioritised)

1. **Do the rollout next — highest leverage, low risk.** The design is additive + dormant-by-default, so
   dark-launching `botsite/` + the submissions DB is safe and finally makes the work real. An agent can
   produce a step-by-step provisioning checklist or dry-run the migration against a throwaway DB to de-risk
   it — without provisioning anything.
2. **Greenlight the web-CI matrix as a quick focused PR** — a genuine "two sides of one problem" cleanup
   with a clear acceptance bar (both matrix legs green before deleting the per-service files).
3. **Close the MCP-PR workflow gap (needs an owner decision — executable config, Q-0106 → propose not
   self-apply).** MCP-created PRs don't trigger `pr-conflict-guard` *or* `auto-merge-enabler` (the app-token
   recursion guard) — so a born-dirty MCP PR can sit un-flagged until the 3-hourly cron (this exact gap hit
   #1122 — see the review's conflict analysis). Durable fix: have MCP-PR creation also `workflow_dispatch`
   the conflict-guard. File as a router Q-block if wanted.
4. **Per-command status-badge granularity (session idea, Q-0089).** Today one open idea marks *all* of a
   cog's commands `in-progress` (the badge is subsystem-wide). A tiny optional per-command override would make
   the headline maturity badge honest at the command level. Cheap, additive, reuses the redaction lens.

## References
- [`website-split-review-2026-06-19.md`](website-split-review-2026-06-19.md) — the build review (invariants + refactors + flags).
- [`../planning/website-two-site-split-plan-2026-06-19.md`](../planning/website-two-site-split-plan-2026-06-19.md) — the plan (§5 units, §6 rollout, §7 decisions).
- [`botsite-deploy.md`](botsite-deploy.md) · [`env-vars.md`](env-vars.md) — the deploy recipe + the Website-tier env names.
