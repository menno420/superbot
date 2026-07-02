# Production deployment — Railway

> **Status:** `living-ledger` — operational facts about where production runs and how code
> reaches it. Facts verified 2026-06-10 (PR #685); deploy-config + Railway-API access added
> 2026-06-14 (Q-0130). **Agent authority re-scoped 2026-07-02 (owner directive Q-0213):** the
> full-access Railway account token in agent containers is **deliberate** — agents operate the
> Railway control plane directly (service/environment config, variables, deploy-affecting
> settings, creating services), with **read-back verification and a session-log record of every
> change**. The unchanged boundary: **destructive/hard-to-reverse operations — any `*Delete`
> mutation, backup/volume restores, data-loss ops, plan/billing changes — stay ask-first, always.**
> Known-bad setting: do **not** enable Railway's *wait-for-CI* deploy gating on this repo — tried
> before, kept failing under the fast auto-merge cadence (Q-0213 item 5).

## Where production runs

- **Platform:** [Railway](https://railway.com) — project `reliable-grace`, environment
  `production`, **four services** (count re-verified against the Railway API 2026-07-02):
  - **`worker`** — the bot, built from this GitHub repo (start: `python disbot/bot1.py`).
  - **`Postgres`** — Railway-native Postgres with a `postgres-volume` for data (EU region).
  - **`dashboard`** — the FastAPI operator dashboard (repo `dashboard/`, healthcheck `/healthz`).
  - **`botsite`** — the public site (repo `botsite/`).
  A full verified as-is inventory (triggers, healthchecks, backups, token capabilities) + the
  new-project Railway plan live in
  [`planning/railway-setup-plan-2026-07-02.md`](../planning/railway-setup-plan-2026-07-02.md).
- **Runtime secrets** (Discord token, `DATABASE_URL`, AI provider keys, …) live in
  Railway **service variables**, not in the repo. For the complete inventory of every
  environment variable the bot reads — where each is read, and whether it is required or
  optional (names + locations only, no values) — see the generated
  [`env-vars.md`](env-vars.md) reference (`scripts/scan_env_usage.py`).

## How code reaches production

> **Merge = deploy.** Merging a PR to `main` triggers an **immediate Railway auto-deploy** of
> `worker` — the change is **live within minutes, on its own, with no manual deploy or restart**.
> The deploy *is* the restart (a fresh container). **Never tell the maintainer to "restart" or
> "deploy" a merged change to make it take effect** — that just happened automatically. What
> genuinely stays the maintainer's is **live verification, rollback, and eval walks**, plus any
> per-PR *data* step a change explicitly names (e.g. `!btd6ops seed-data`, or clicking an
> operator button to clear stale rows).

- The Railway GitHub integration **auto-builds and deploys `worker` on every push to
  `main`** — each merge commit shows up as a deployment ("Merge pull request #NNN …
  via GitHub" in the dashboard).
- **Consequence for merge autonomy (Q-0084):** an agent merging a green session PR
  *is* shipping to production — true for the maintainer's merges too. It does **not**
  mean a separate manual deploy/restart is needed; it means **prod verification,
  rollback, and live eval walks** (not the deploy) stay the maintainer's.
- **Builder:** [railpack](https://railpack.com) (v0.27.x at write time). It detects
  Python + pip, creates `/app/.venv`, runs `pip install -r requirements.txt`, and
  starts the `worker` command from the **`Procfile`**: `python disbot/bot1.py`.
- **Slash-command propagation is automatic (#1424).** On boot the bot diff-checks its
  local app-command tree against Discord's live global commands and only calls
  `tree.sync()` when the command *paths* changed — so a deploy that adds/removes/renames
  a slash command propagates on its own, **with no manual `!syncslash`**. (Kill-switch:
  `AUTO_SYNC_COMMANDS=0`.) The manual command stays the backstop: `!syncslash global`
  previews the live-vs-local diff and syncs only if it changed, and `!syncslash global
  force` resyncs unconditionally for parameter/description-only edits the conservative
  path-diff deliberately misses (`!syncslash guild` is still the instant per-guild dev
  refresh). So slash propagation is **not** a maintainer post-deploy step.

## Python version — pinned, and why

- **The pin: `.python-version` (repo root) = `3.13.13`.** Railpack reads
  mise-compatible version files and installs that exact interpreter from
  precompiled [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
  (pbs) binaries.
- **Why pinned:** with no pin, railpack floats on its default (`3.13` → *latest*
  patch). On 2026-06-10 that resolved to CPython **3.13.14**, released upstream
  *after* pbs's latest binary release (`20260602`) — no precompiled binary for
  `x86_64-unknown-linux-gnu` existed, and every build failed at `mise install`
  (`mise ERROR … no precompiled python found`). A known Railway failure class (the
  same race hit other users on 3.13.11). A floating version re-runs this race on
  every CPython patch release; a pinned one never does.
- **Precedence:** a `RAILPACK_PYTHON_VERSION` service variable would override the
  file — keep it **unset** so the repo stays the single source of truth.
- **Bump procedure** (deliberate, never automatic):
  1. Pick the target patch and verify a pbs binary exists for Railway's platform:
     ```
     curl -s -o /dev/null -w "%{http_code}" -I -L \
       "https://github.com/astral-sh/python-build-standalone/releases/download/<TAG>/cpython-<VER>+<TAG>-x86_64-unknown-linux-gnu-install_only.tar.gz"
     ```
     (`<TAG>` from [latest-release.json](https://raw.githubusercontent.com/astral-sh/python-build-standalone/latest-release/latest-release.json);
     expect `200`.)
  2. Change `.python-version`, merge, and watch the Railway build log: the Packages
     table must read `python │ <VER> │ .python-version` (not `railpack default`).
- **Known drift (open question Q-0085):** CI and local tooling run **Python 3.10**
  (pinned in the workflows and every `python3.10 -m` rule); production runs
  **3.13** and always has (the unpinned default predates this doc). Alignment
  direction is an owner decision —
  [`owner/maintainer-question-router.md`](../owner/maintainer-question-router.md) §36.

## Deploy configuration (Railway service settings)

Verified from the dashboard 2026-06-14 (the `worker` service, `production`
environment). These are the settings worth knowing; everything else is Railway's
default.

| Setting | Value | Note |
|---|---|---|
| Custom Start Command | `python disbot/bot1.py` | Set in the service UI; matches the `Procfile`. |
| Custom Build Command | (none) | railpack autodetects Python + pip. |
| Watch Paths | (none) | Every push to `main` builds; no path filter. |
| Healthcheck Path | (none) | No HTTP healthcheck — the bot is a gateway worker, not a web service. |
| Cron Schedule | (none) | Long-running process, not a scheduled job. |
| Teardown | off | The old deployment is not force-stopped the instant a new one starts. |
| Serverless | off | The bot must stay resident (persistent Discord gateway); never scale-to-zero. |
| Skipped Builds | off | Always rebuild (this flag is GitHub-only). |
| Railway config file | (none) | Config lives in the dashboard + repo `Procfile` / `.python-version`. |

**Do not enable Serverless or a Healthcheck Path** without rethinking the bot's
lifecycle: a Discord gateway bot has no inbound HTTP to health-check and must not
sleep, so either would break it.

## Which Railway token? (account vs project)

Railway has **two** kinds of API token, on two different pages — this is the part that
trips people up. Both work with the tools here; pick by how much scope you want.

| | **Project token** (preferred) | **Account / workspace token** |
|---|---|---|
| Where | **Project → Settings → Tokens** (set environment `production`) | Account **Settings → Tokens** |
| Scope | just this one project + environment (least-privilege) | your whole account / workspace |
| Env var to set | **`RAILWAY_TOKEN`** (the var Railway's own hint names) | `RAILWAY_API_TOKEN` |
| GraphQL header | `Project-Access-Token` (the tools set this for you) | `Authorization: Bearer` |
| Verify with | `railway_vars.py list` (a project token has no `--whoami` identity) | `railway_logs.py --whoami` |

**Recommendation:** create a **project token** (e.g. named `claude`, environment
`production`) and set it as **`RAILWAY_TOKEN`** in the agent's environment. Only reach for
an account token if a project token returns "Not Authorized". (`RAILWAY_PROJECT_TOKEN` is
accepted as an alias for `RAILWAY_TOKEN`.) The **ids** are still required either way — the
token says *who you are*, the ids say *which resource*.

## Hermes read-only log access (Railway API)

**Posture (Q-0130, 2026-06-14):** the "no Railway access" rule now has one
**read-only** exception — Hermes (and any agent) can read the bot's production logs
through the Railway public GraphQL API. This unblocks the `superbot-log-triage`
skill. It is **read-only by construction**: the reader issues GraphQL *queries*
only, never a mutation — no deploy / restart / scale / delete. Operate/write access
stays the maintainer's (the broader-access ladder is the open half of Q-0130).

**Reader:** [`scripts/hermes/railway_logs.py`](../../scripts/hermes/railway_logs.py)
(stdlib-only). It resolves the bot service's latest deployment and prints its logs.

```
python3.10 scripts/hermes/railway_logs.py -n 400     # latest deployment's logs
python3.10 scripts/hermes/railway_logs.py --whoami   # verify the token works
python3.10 scripts/hermes/railway_logs.py --json     # raw JSON for tooling
```

**One-time maintainer setup:**

1. Create a **read-only token** at <https://railway.com/account/tokens>. A **project
   token** scoped to the `reliable-grace` production project is least-privilege and
   preferred; an account/workspace token also works (broader scope).
2. Find the ids in the dashboard URL
   `railway.com/project/<PROJECT_ID>/service/<SERVICE_ID>` (the `worker` service).
   The production environment id is optional.
3. Put them in **Hermes's environment** (the VPS — never the repo):
   - **`RAILWAY_TOKEN`** (project token) **or** `RAILWAY_API_TOKEN` (account token) —
     see *Which Railway token?* above
   - `RAILWAY_PROJECT_ID`, `RAILWAY_SERVICE_ID`, optional `RAILWAY_ENVIRONMENT_ID`
4. Verify: `railway_vars.py list` (project token) or `railway_logs.py --whoami` (account
   token), then `python3.10 scripts/hermes/railway_logs.py -n 50`.

**Auth detail:** account/workspace tokens use `Authorization: Bearer <token>`;
project tokens use `Project-Access-Token: <token>` — the script picks the header from
whichever env var is set (project token preferred when both are present). Endpoint:
`https://backboard.railway.com/graphql/v2`.

**Network:** running it from a cloud routine/sandbox needs that environment's network
policy to allow `backboard.railway.com`; on Hermes's VPS normal outbound is enough.

## Env variable read/write (Railway API)

**Posture (Q-0130, 2026-06-14 — owner-authorised _write_).** Beyond read-only logs,
the owner explicitly granted agents **read _and write_ access to the bot's service
environment variables** (the Discord token, `DATABASE_URL`, AI keys, …) via the Railway
API — to verify them at a glance and change them quickly, accepting the risk. This is a
genuine write capability. It is **separate from** deploy / restart / scale / rollback,
which remain the maintainer's.

**Tool:** [`scripts/hermes/railway_vars.py`](../../scripts/hermes/railway_vars.py)
(reuses the logs reader's transport).

```
python3.10 scripts/hermes/railway_vars.py list             # names, values masked
python3.10 scripts/hermes/railway_vars.py list --reveal     # names + values (SECRETS!)
python3.10 scripts/hermes/railway_vars.py get DATABASE_URL  # one value, to verify it
python3.10 scripts/hermes/railway_vars.py set NAME VALUE     # create/update (redeploys)
echo -n "secret" | python3.10 scripts/hermes/railway_vars.py set NAME   # value via stdin
python3.10 scripts/hermes/railway_vars.py set NAME VALUE --no-deploy   # stage only
python3.10 scripts/hermes/railway_vars.py unset OLD_NAME    # delete
```

**Guardrails baked in:** `list` / `get` never mutate; `list` masks values unless
`--reveal`; `set` / `unset` print an audit line to stderr and never echo the token;
`set` reads the value from stdin when omitted so secrets stay out of `argv`.

> **A `set` / `unset` triggers a Railway redeploy by default** — that is how the change
> takes effect. Pass `--no-deploy` to stage a value without redeploying. So an env-var
> edit *is* effectively a deploy unless you stage it; keep that in mind, since deploys
> otherwise stay the maintainer's.

**Setup (one-time, maintainer):** needs a **write-capable** token (a project token set as
**`RAILWAY_TOKEN`** — see *Which Railway token?* above — or an account token as
`RAILWAY_API_TOKEN`) **and all three ids** — variables are per-environment, so
`RAILWAY_ENVIRONMENT_ID` (production) is required alongside `RAILWAY_PROJECT_ID` and
`RAILWAY_SERVICE_ID`. Put them in the agent's environment (the Claude Code cloud
environment's variables and/or Hermes's VPS), and allow `backboard.railway.com` in that
environment's network policy.

## Backups

**Posture (2026-06-13, band slot 3; monthly tier added 2026-07-02, Q-0213 session):** daily
automated `pg_dump` to GitHub Actions artifacts (90-day rolling window) **+ a monthly
long-retention artifact (1st of the month, 400-day retention)** + a local-run script for
ad-hoc dumps.

> **Why the pg_dump workflow is the ONLY backup layer (verified 2026-07-02):** Railway-native
> volume backups are **plan-gated on Hobby** — both `volumeInstanceBackupScheduleUpdate` and a
> manual `volumeInstanceBackupCreate` return `Not Authorized` via the account token (correct
> ids; reads work). Upgrading the plan, or accepting the single-layer posture, is an owner
> call recorded in `../planning/railway-setup-plan-2026-07-02.md` §6 R2.
>
> **Owner one-time step for the monthly tier:** GitHub → Settings → Actions → General →
> *Artifact and log retention* → raise to **400 days**. GitHub silently clamps
> `retention-days` to this repo setting (default 90), so until it is raised the monthly
> artifact quietly keeps only 90-day retention.

### What runs automatically

`.github/workflows/backup-db.yml` fires at **02:00 UTC every day** (also available
as a manual `workflow_dispatch`). It runs `pg_dump --no-owner --no-acl` against the
Railway public proxy URL, compresses with gzip, and uploads as an artifact named
`postgres-backup-<run-id>` with 90-day retention. **On the 1st of every month (03:00 UTC)
a second scheduled run uploads `postgres-backup-monthly-<run-id>` with 400-day retention**
(subject to the repo-setting clamp above). On failure it opens a GitHub issue.

### One-time owner setup (required before the first scheduled run works)

1. Railway dashboard → **Postgres service → Connect tab**.  Under
   "Public networking" copy the URL labelled **"Database URL"** (the public proxy
   URL — *not* the internal `DATABASE_PRIVATE_URL`).
2. GitHub repo → **Settings → Secrets and variables → Actions →
   New repository secret**.  Name: `DATABASE_PUBLIC_URL`.  Paste the URL.
3. Manually trigger the workflow once (`Actions → Postgres backup → Run workflow`)
   to verify an artifact appears and is non-zero.

> **Note on rotation:** Railway may rotate the public URL when the Postgres service
> is recreated or manually rotated.  If the backup fails, the first thing to check
> is whether the secret is stale.

### Restore procedure

1. Download the desired artifact from **Actions → Postgres backup (daily) → the
   run → Artifacts → postgres-backup-\<run-id\>** and unzip it.
2. Obtain `DATABASE_URL` for the target Postgres (Railway dashboard or local).
3. ```
   gunzip -c superbot-backup-<timestamp>.sql.gz | psql <DATABASE_URL>
   ```
4. Restart the Railway worker service so it reconnects cleanly.

### Ad-hoc / local backup

```
DATABASE_PUBLIC_URL=<url> python3.10 scripts/backup_db.py [--output-dir /path]
```

Requires `pg_dump` on PATH (`brew install libpq` on macOS;
`apt-get install postgresql-client` on Debian/Ubuntu).

### Railway-native snapshots (complement, not replacement)

Railway's Pro plan includes **Point-In-Time Recovery** and database snapshots in the
Postgres service UI.  Enable them if available on the current plan — they recover
from in-cluster data corruption, while the offsite `pg_dump` above survives a full
Railway service loss.  The two are complementary.

## Incident log

- **2026-06-10 — worker build outage (~21:00–21:45 UTC).** Three consecutive build
  failures (the #681 and #680 merge deploys + a manual retry): railpack default
  resolved to binary-less CPython 3.13.14 (see "Why pinned" above).
  **Impact (owner-corrected 2026-06-11): no user-facing downtime** — Railway
  keeps the active deployment serving until a new build goes live, so the
  previous instance ran throughout; Postgres Online throughout. The real
  impact was a **silent ship-blocker**: no new code could reach production
  until the pin landed. Fix: the `.python-version` pin, PR #685, merged the
  same hour. Diagnosis artifacts: the maintainer's uploaded build log; pbs
  asset probes (3.13.13 → 200, 3.13.14 → 404).
