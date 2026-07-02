# Railway — token audit + the new-project setup plan & roadmap (2026-07-02)

> **Status:** `plan` — owner-directed. The **runtime half of the rebuild's control plane**: the
> [design spec §6](rebuild-design-spec-2026-07-02.md) covers the GitHub side (rulesets, OIDC,
> required gates); this doc covers the Railway side. Every claim about the live account below was
> **verified read-only against the Railway GraphQL API this session** (no mutation was executed;
> the Q-0130 authority split — deploy/restart/scale/rollback stay the maintainer's — was honored
> and is re-examined in §6). Facts drift; re-verify against the API before acting on numbers.

## Plain-language summary — read this first

**What you asked.** "Find out exactly what my Railway token can and can't do, and plan how we set
Railway up correctly from the start in the new project."

**What the token is.** It is your **personal account token** — the strongest kind Railway issues.
It can see and change *everything* your account can: every service, every secret, every database,
including deleting the project or the whole workspace. Railway offers **no way to restrict this
token type** — no read-only mode, no per-project scope, no expiry. Its "limitations" are only:
Railway's per-plan API rate limits, your plan's resource caps, and the fact that it is yours alone
to revoke. That power is why this plan recommends **downgrading what agents routinely hold** to
scoped project tokens, and keeping the account token for the few operations that genuinely need it.

**What I found on the account (all read-only):** one Hobby project (`reliable-grace`) with the bot
(`worker`), the database (`Postgres`, ~0.7 GB of 5 GB used, EU region), `dashboard`, and `botsite`.
Deploys fire on every merge to `main` — **without waiting for CI** (a toggle exists and is off).
The database has **no Railway-side backups** (the daily GitHub `pg_dump` backup *is* green — one
layer exists, the cheap second layer doesn't). `botsite` has no health check. Nothing is
config-as-code — every setting lives only in the dashboard, invisible to review.

**What this plan does.** Fixes the five cheap gaps on the *current* project now (with your
approval — they are live-infra changes), and specifies the Railway layout the **new** project gets
from day one: its own project, a production + shadow environment pair, config-as-code checked into
the repo, wait-for-CI deploys, layered backups, scoped tokens, and the cutover/rollback choreography
the design spec's Phase 5 needs.

---

## 1. The token — verified capabilities and limits

**Identity + type (probed live):** `me` succeeds over `Authorization: Bearer` and returns your
account (`menno420`, workspace "My Projects"); the `Project-Access-Token` header is rejected
("Project Token not found"). ⇒ This is an **account token**, not a project or workspace token.
Railway's own docs scope it as: *"All your resources and workspaces"* — intended for
*"personal scripts, local development."*

**What it can do (verified):** the full public GraphQL API — **129 queries + 197 mutations**
introspected as available, including reading **all variable values** (secrets: Discord token, AI
provider keys, OAuth secrets — this session printed *names only*), and the full destructive set
(`projectDelete`, `serviceDelete`, `volumeDelete`, `environmentDelete`, `variableUpsert/Delete`,
`workspaceDelete`, `userDelete`, `apiTokenDelete`, deploy/redeploy/rollback, volume backup
create/restore, `volumeInstancePITRRestore`). In short: the owner's claim is accurate — it can see
and alter everything.

**Its actual limitations (the complete list):**

| Limit | Verified detail |
|---|---|
| **No scoping** | Account tokens cannot be made read-only, per-project, or per-environment. All-or-nothing is a *property of the token type*, not a setting. |
| **No expiry** | No TTL mechanism; valid until manually revoked (Account → Tokens). Rotation is a human discipline, not a feature. |
| **Rate limits** | Hobby plan: **1,000 requests/hour, 10 requests/second** (`X-RateLimit-*` headers). Fine for automation; rules out high-frequency polling. |
| **Plan caps** | Cannot exceed plan resources (verified live: containers cap at **8 vCPU / 8 GB RAM** on Hobby). Billing/plan changes are dashboard+payment surfaces, not this API. |
| **Blast radius = the account** | It reaches only your workspaces (one exists). But within them there is *no* guardrail: a single mutation can delete the production database. |

> **⚠️ Custody recommendations below: DECLINED by owner directive Q-0213 (2026-07-02).** The
> full-access account token in agent containers is **deliberate** — Claude is its sole holder and
> the repo's main editor, so the whole project can run fully automated without owner dependency.
> Kept for the record as the road-not-taken; the one piece that *survives* as binding convention:
> **no automation ever calls a `*Delete`/`*Restore`/data-loss mutation without an explicit owner
> ask** (Q-0213 item 4).

**Custody recommendations (superseded — see the Q-0213 note above):**

1. **Agents should not routinely hold the account token.** Railway offers **project tokens**
   (scoped to one project + one environment, `Project-Access-Token` header) — enough for
   deploy/status/logs automation. The account token's standing presence in every agent container
   means any session bug or prompt-injection has account-wide, irreversible reach. Q-0130 already
   scopes what agents may *do*; the token should match that scope mechanically ("enforce, don't
   exhort" — the same principle as the bot's own capability system).
2. **Rotate the account token** after issuing scoped ones, and store it only where the owner acts.
3. **A workspace policy note:** deletions and restores should be dashboard-only owner actions by
   convention — no automation ever calls a `*Delete`/`*Restore` mutation.

## 2. As-is inventory (verified 2026-07-02, read-only)

Project **`reliable-grace`** · Hobby plan · created 2026-05-13 · one environment: **`production`**.

| Service | Source | Start / config | Health check | Restart | Notes |
|---|---|---|---|---|---|
| **worker** (the bot) | repo `main`, RAILPACK | `python disbot/bot1.py` | **none** | ON_FAILURE ×10 | Holds all runtime secrets (33 vars: Discord token, AI keys, control tokens…) |
| **Postgres** | image `postgres-ssl:18` | — | — | ON_FAILURE ×10 | Volume `postgres-volume`: **5 GB, ~724 MB used**, region `europe-west4` (EU). `RAILWAY_DEPLOYMENT_DRAINING_SECONDS` set |
| **dashboard** | repo `main`, root `dashboard/` | `uvicorn app:app …` | `/healthz` ✓ | ON_FAILURE ×10 | OAuth secrets + `CONTROL_API_TOKEN` |
| **botsite** | repo `main`, root `botsite/` | `uvicorn app:app …` | **none** | ON_FAILURE ×10 | Public site |

- **Deploy triggers:** all three repo services deploy from `main`, **`checkSuites: false`** — the
  "wait for CI" toggle is OFF, and there is **no per-service watch-path scoping**, so every merge
  rebuilds and redeploys all three (bot-only merges bounce the dashboard + botsite for nothing).
  Deploy loop confirmed live: merge `a8b2a8b` (PR #1637) → worker `SUCCESS` deploy at 10:16 UTC.
- **Backups:** **zero Railway volume backups, zero schedules** (verified empty). The mitigating
  layer is repo-side and **verified green**: `.github/workflows/backup-db.yml` runs daily
  (02:00 UTC pg_dump → 90-day GitHub artifact; last 5 runs all `success`, latest this morning).
  One layer, not two — and its restore path has never been drilled (its own header says so).
- **No config-as-code:** `railwayConfigFile` is null on every service and no `railway.json/toml`
  exists in the repo — every deploy setting lives only in the dashboard, unreviewable and
  unrecoverable if fat-fingered.
- **No regions pinned** on services (Postgres volume is EU); single replica each — fine for a
  Discord bot (the gateway session must be a singleton anyway).

## 3. Gaps in the current setup — ranked

1. **Deploys don't wait for CI** (`checkSuites: false`). Anything reaching `main` deploys
   immediately — including a direct push that never saw Code Quality. The fix is one toggle per
   service, and it composes with (not replaces) the auto-merge-on-green flow.
2. **No Railway-native backup layer.** The pg_dump artifact is good but single-layer (and GitHub
   artifacts silently expire at 90 days). Railway backups are incremental copy-on-write, billed
   only on delta — at ~724 MB, effectively free. Daily (kept 6 days) + weekly (kept 1 month) +
   monthly (kept 3 months) schedules can be combined.
3. **Restore has never been drilled.** A backup that has never restored is a hope, not a backup —
   the workflow's own Q-0105 header still says "UNVERIFIED … run a test restore."
4. **`botsite` has no health check** (dashboard has one); a bad deploy cuts the public site over
   to a broken container instead of failing the deploy.
5. **Every merge redeploys all three repo services** — wasted builds and needless restarts of the
   web services on bot-only changes (watch paths fix this in minutes).
6. **Nothing is config-as-code** — see §2. (The new project fixes this structurally; retrofitting
   the current project is optional.)
7. **Usage limits/alerts state unverified** — the feature exists (mutations present); whether any
   limit is configured wasn't readable this session. Worth one dashboard glance (Workspace →
   Usage Limits): a hard limit + email alert is the "no surprise bill" backstop.

## 4. Target Railway architecture for the new project

**One new Railway project** (working name `superbot-next`), not new services inside
`reliable-grace`: clean namespace, independent blast radius, per-project tokens, and a cutover that
is a service flip rather than an in-place mutation. The old project stays untouched as the
rollback platform for its bounded window (design spec §5.4), then winds down.

| Element | Day-one shape |
|---|---|
| **Environments** | `production` + **`shadow`** (the spec's shadow-run home: full service set against a **restored-snapshot** Postgres — never the live DB). PR environments stay OFF (cost; CI covers it). |
| **Services** | `worker` (bot kernel), `Postgres` (+ volume), `dashboard` (control surface — a client of the audited control API per spec §6), `botsite`. Same split that exists today; it maps 1:1 onto the spec. |
| **Config-as-code** | Every service carries a checked-in `railway.json` (builder, start command, health check, restart policy, watch patterns, region) — **the Railway analog of the manifest principle**: declared, versioned, reviewable, regenerable. Dashboard-only settings are the exception, not the rule. |
| **Deploy trigger** | `main`, watch paths per service (`sb/**` + shared for worker; `dashboard/**`; `botsite/**`). Merge=deploy stays the model. **Wait-for-CI only under three conditions** (learned the hard way — Q-0213 item 5: it was tried on the current repo and kept failing under fast merges): main-branch CI must run **per-commit** (no shared serial queue), the gating check must be **fast** (<~3 min, not the full suite), and runs must never be cancelled. The new repo's named-gate workflow (design spec §6) should be designed to satisfy these; until it does, the toggle stays off and the merge gate carries correctness. |
| **Health checks** | HTTP checks on dashboard + botsite. **The worker exposes its kernel-observability health endpoint** (spec §1.1 K0 — metrics/health already exist as a leaf) on `PORT`, so Railway health-gates *bot* deploys too: a container that can't pass admission checks never replaces the healthy one. |
| **Variables** | Secrets as **sealed** service variables; `DATABASE_URL` etc. as **reference variables** (never copy-pasted values); per-service scoping exactly as today (worker never holds OAuth secrets, dashboard never holds the bot token); names inventoried by the generated `env-vars.md` equivalent from day one. Spec §5 hazard 8 (env names/meanings) carries over verbatim. |
| **Region** | Pin `europe-west4` explicitly on all services + volume (it's where the data already lives; keeps DB latency low and residency stable). |
| **Backups** | **Three layers:** Railway schedules on the Postgres volume (daily+weekly+monthly, incremental) · the ported pg_dump→artifact workflow (logical, offsite) · a **quarterly restore drill** written into the ops runbook (§10.3's DR deliverable). |
| **Tokens** | Two **project tokens** minted at bootstrap: `shadow` (agents/CI — deploy, status, logs) and `production` (CI deploy only). The **account token** is used once to bootstrap, then goes owner-custody. |
| **Alerts** | Workspace usage limit + email alert (soft $15 set 2026-07-02); deploy/volume/monitor notifications → Discord **verified live 2026-07-02**: the mechanism is a **notification rule** (`notificationRules`/`notificationRuleUpdate`, `channelConfigs: [{type: "webhook", url: <discord webhook>}]`, `eventTypes: Deployment.*/VolumeAlert.*/Monitor.*`) — the current project's rule posts to **`#railway-alerts` in the "Superbot Admin" HQ guild** (`1522099141671653417` — restored in the test guild after an accidental deletion, then moved to HQ the same day); the new project mints its own rule at bootstrap, same destination (see `../ideas/central-admin-and-logging-guilds-2026-07-02.md`). |
| **Cost posture** | Stay Hobby until the shadow window: two full environments during Phase 4/5 roughly double runtime cost for that window (~724 MB DB + three small services — modest). Revisit Pro only if API rate limits (1,000 RPH) or resource caps bite. |

**What deliberately does NOT change:** merge=deploy (Q-0193 — the deploy *is* the restart);
Railway as the platform (the external review's hosting alternatives are a post-parity cost
question, not a Phase-3 one); the four-service split; single-replica worker (Discord gateway
sessions don't horizontally scale).

## 5. Phase-5 choreography on Railway primitives

Mapping the design spec's §5.2/§5.4 cutover to concrete Railway operations:

1. **Shadow-run (weeks):** `shadow` environment runs the new bot against a **restored snapshot**
   volume (Railway backup-restore or pg_dump import); a separate Discord test-guild token; the
   compat scoreboard + goldens replay here. *Exactly one bot writes the production DB at all
   times* — shadow never holds production DB credentials.
2. **Cutover (minutes):** freeze old bot (pause deploys; final pg_dump) → run the final importer
   delta into the new project's Postgres → **flip = swap the production Discord token onto the new
   worker** (a sealed-variable change + redeploy in the new project) → old `worker` stopped, not
   deleted.
3. **Rollback window (bounded, spec §5.4):** old project intact with its untouched database; the
   documented rollback = stop new worker, restart old one with its token. Scoreboard lines (§5.4
   of the spec) decide window exit, then the old project winds down to a final archived backup.

## 6. Roadmap

**R-now — current project hygiene. STATUS 2026-07-02 (executed under the Q-0213 automation grant,
each change read-back-verified; PR #1640):**

| # | Action | Status |
|---|---|---|
| R1 | Flip **Wait for CI** on (worker, dashboard, botsite triggers) | **❌ DROPPED (owner history, Q-0213 item 5):** previously enabled and *"kept failing due to the fast merges"* — main-branch CI runs serialize in one queue (`code-quality-refs/heads/main`, ~10-min full suite, `cancel-in-progress: false`), so burst merges stack deploy delays and any non-success blocks the deploy. Do **not** re-enable here. New-repo condition (§4): wait-for-CI only with per-commit main CI (no shared serial queue), a fast (<~3 min) gate, and no cancellation — else keep it off and rely on the merge gate. |
| R2 | **Railway backup schedules** on `postgres-volume` | **⛔ PLAN-GATED:** schedules *and* manual backup creation return `Not Authorized` on Hobby (verified with API-supplied ids; reads work). **Compensated repo-side:** `backup-db.yml` gained a monthly 400-day-retention artifact tier (owner one-time step: raise the repo artifact-retention setting to 400 days). Enabling Railway backups = a plan-upgrade decision (§7). |
| R3 | **Watch paths** | **✅ DONE for dashboard (`dashboard/**`) + botsite (`botsite/**`)** — verified the recurring dashboard-refresh commits touch only `dashboard/data/`. **Worker deliberately unscoped** (deploy-on-everything): under-deploying the bot is the dangerous direction, and its true input set (`disbot/**`, `data/**`, root `requirements.txt`, …) is wide. |
| R4 | **botsite health check** | **✅ DONE** — `healthcheckPath=/healthz` set + read back (endpoint verified at `botsite/app.py:97`). Takes effect on the next botsite deploy. |
| R5 | **Usage alert** | **✅ DONE** — `softLimitDollars: 15` on the workspace customer (email alert only; **no hard limit set** — a hard limit stops workloads and stays an owner call). First attempt failed with the *workspace* id — Railway wants the **customer** id (`me.workspaces[].customer.id`), and returns the same opaque `Not Authorized` for wrong-id as for plan-gating. |
| R6 | **Restore drill** (download latest pg_dump artifact → restore to scratch Postgres → sanity-check; closes the workflow's "UNVERIFIED" header) | **▶ open — next Railway session** (agent-runnable, read-only vs prod). |
| R7 | **Token hygiene** (project tokens + rotate account token) | **❌ DECLINED by Q-0213** — full-access token is deliberate; see §1. |

**R-3 — new-project bootstrap (rides the Phase-3 owner gate; agent-executable via API once
granted, ~1 session):** create project + `production`/`shadow` envs → services from checked-in
`railway.json` → sealed + reference variables (owner pastes secret values) → region pins → backup
schedules from day one → wait-for-CI triggers wired to the new repo → project tokens into the new
repo's GitHub secrets → deploy-failure webhook → usage alert. Acceptance: a hello-world kernel
deploy that fails CI **does not deploy** (the R1 behavior proven on day one).

**R-4/5 — port + cutover phases:** stand up shadow's restored-snapshot Postgres when the importer
exists (spec §5.2) → scoreboard wiring → the §5 choreography above, owner-verified per the spec's
standing rule.

## 7. Open owner decisions

1. ~~**Grant scope for the R-now items**~~ — **DECIDED (Q-0213, 2026-07-02):** agents execute via
   the API under the full-automation grant; destructive/restore/billing ops stay ask-first.
   Executed same day — see the §6 status column.
2. **New project name** (`superbot-next`?) — cosmetic but persisted in tooling.
3. ~~**Token custody model**~~ — **DECIDED (Q-0213):** the full-access account token stays with
   agents deliberately; recorded as a conscious accepted risk (§1 note).
4. **Shadow-window budget:** accept the temporary ~2× runtime cost during Phase 4/5, or shorten
   the window / run shadow with sleep-enabled web services.
5. *(Deferred by design, §4:)* plan tier and hosting alternatives — revisit post-parity. **One new
   input for this decision (2026-07-02):** Railway-native volume backups turned out plan-gated on
   Hobby (§6 R2) — if a second, platform-level backup layer is wanted for the rebuild's database,
   a plan upgrade is the lever; otherwise the layered pg_dump posture carries it.
6. **Repo artifact-retention setting** (one dropdown, GitHub → Settings → Actions → General): raise
   to **400 days** so the new monthly backup tier actually retains long-term (default 90 clamps it).
