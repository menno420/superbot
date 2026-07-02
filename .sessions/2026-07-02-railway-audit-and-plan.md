# 2026-07-02 — Railway: token-capability audit + new-project setup plan

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Docs-only in the repo; **zero Railway mutations executed** (Q-0130 honored — all probing was
> read-only GraphQL). `check_docs --strict` ✓, ledger ✓ (benign lag). PR #1638.

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7` (restarted from `main` @ #1637 merged).

## What I'm about to do (intentions — as declared born-red)

Probe the owner's Railway token (type/capabilities/limits) strictly read-only; inventory the live
project; write the Railway setup plan + roadmap for the rebuild.

## What shipped

**[`docs/planning/railway-setup-plan-2026-07-02.md`](../docs/planning/railway-setup-plan-2026-07-02.md)**
(opens with a plain-language summary — the new owner-gate-doc convention, applied):

- **§1 Token audit (verified live):** it is a **personal account token** (`me` works over Bearer;
  the `Project-Access-Token` header is rejected) — Railway-documented scope "all your resources
  and workspaces," **no scoping/read-only/expiry mechanism exists** for this type; 129 queries +
  197 mutations introspected as reachable (incl. `projectDelete`/`volumeDelete`/variable
  read-write — i.e. "alter everything" is literally true); real limits = Hobby rate limits
  (1,000 RPH / 10 RPS), plan caps (8 vCPU / 8 GB), custody. Recommendation: scoped **project
  tokens** for routine agent/CI use, account token to owner custody + rotation.
- **§2 As-is inventory:** project `reliable-grace` (Hobby, one `production` env, 4 services);
  worker/dashboard/botsite all deploy from `main` with **`checkSuites: false`** (deploys never
  wait for CI) and no watch paths (every merge redeploys all three); Postgres volume 5 GB /
  ~724 MB used, `europe-west4`; **zero Railway backups or schedules** — the mitigating repo-side
  daily pg_dump→artifact workflow is **verified green** (last 5 runs success) but single-layer and
  never restore-drilled; no config-as-code anywhere; botsite healthcheck missing (endpoint exists,
  `botsite/app.py:97`, verified — only the Railway field is unset).
- **§3 ranked gaps · §4 new-project day-one architecture** (own project + `production`/`shadow`
  envs, per-service `railway.json`, wait-for-CI from first deploy, worker health-gated via the
  kernel observability endpoint, sealed+reference variables, region pins, three backup layers,
  scoped tokens, usage alerts) · **§5 Phase-5 cutover choreography on Railway primitives**
  (shadow on restored snapshots only; flip = token swap; rollback = old project intact) ·
  **§6 roadmap** (R-now hygiene items R1–R7 · R-3 bootstrap · R-4/5) · **§7 open owner decisions.**
- **Drift fixes (Q-0166):** `production-deployment.md` said "two services" — corrected to the
  verified four + linked the plan; planning-README indexed the plan.

## Verification notes

Every live-account claim came from direct read-only GraphQL probes this session (identity, project,
per-service instances, triggers, deployments, variable *names only* — secret values never entered
the transcript — volume/backup state, limits, mutation-surface introspection), plus two Railway
docs fetches (token taxonomy + backups) and the repo's own workflow-run history via the GitHub API.

## Context delta

- **Q-0130 is the standing Railway authority boundary** (agents: logs read + owner-authorised env
  vars; deploy/restart/scale/rollback = maintainer). Today's "you can alter everything" is a
  *capability* statement; the plan treats scope-of-*authority* as §7 decision 1 rather than
  assuming the grant.
- **Capability ≠ custody:** the strongest possible token sitting in every agent container is the
  account's single biggest infra risk — the fix (project tokens) costs ~10 minutes and is the
  plan's top custody recommendation.
- **The two most valuable findings were absences** (no wait-for-CI, no Railway backups) — found
  only because the probe enumerated what *should* exist. Same lesson as the docs checkers: watch
  live state, don't trust intent (→ the session idea).

## 🛠 Friction → guard

The urllib path 403'd through the agent proxy (curl works — env proxy handling differs); noted
here as the journal-grade workaround (use curl for Railway GraphQL in this environment). No repo
guard applicable — environment quirk, not a repo footgun.

## 💡 Session idea (Q-0089)

**[`railway-config-drift-checker-2026-07-02.md`](../docs/ideas/railway-config-drift-checker-2026-07-02.md)**
— a read-only checker + weekly routine diffing live Railway config (wait-for-CI, healthchecks,
backup schedules, watch paths, variable names) against a committed expected-state file. Worth
having because both headline gaps this session were silent dashboard state nothing watched, and it
makes the R-now fixes regression-proof ("enforce, don't exhort" for infra).

## ⟲ Previous-session review (Q-0102)

Previous session (#1637, the spec revision): the adopt/decline-with-reasons disposition was the
right pattern — the owner immediately engaged with the revised spec, and nothing declined has been
re-proposed. What it missed: §10.3 named the ops contracts as future deliverables but seeded no
hook for them — this session had to build the Railway picture from zero, and the owner had to ask
for it explicitly. **Concrete improvement:** when a spec names a deliverable-to-be, immediately
drop a stub idea/plan file for it (one paragraph + route) so the lane is visible in the backlog
the moment the spec merges — the conveyor should never depend on the owner re-asking.

## 📤 Run report

- **Did:** verified exactly what the Railway account token can/can't do (read-only), inventoried
  the live project, shipped the Railway setup plan + roadmap for the rebuild · **Outcome:** shipped
- **Shipped:** #1638 — railway-setup-plan + production-deployment drift fix + README index + 1 idea
- **Run type:** `manual` (owner-directed)
- **⚑ Owner decisions needed:** plan §7 — foremost **(1) who executes the R-now hygiene items**
  (R1 wait-for-CI · R2 backup schedules · R3 watch paths · R4 botsite healthcheck · R5 usage
  limit): owner-in-dashboard vs agent-via-API with an explicit grant (updates Q-0130 either way);
  also **(3) token custody** (scoped project tokens + rotate the account token, recommended).
- **⚑ Owner manual steps:** none until the §7.1 decision (then either ~15 min of dashboard toggles,
  or a one-line grant to an agent).
- **⚑ Self-initiated:** none (owner-directed; idea file is capture)
- **↪ Next:** owner answers plan §7.1/§7.3 → execute R-now; the rebuild owner gate on the design
  spec is still the big open decision; Phase 0.5 remains the best parallel build.
