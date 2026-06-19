# Bot site (`botsite/`) deploy — the 2nd Railway web service

> **Status:** `living-ledger` — the deploy recipe + rollout/rollback sequence for the **public
> marketing bot site** (`botsite/`), a *second* Railway web service alongside the developer
> dashboard. Operational facts; the maintainer owns the Railway dashboard. Source + the live
> Railway config win over this file. Written 2026-06-19 for the website two-site-split
> ([plan](../planning/website-two-site-split-plan-2026-06-19.md) §6 / §2.1 / §4.4).

The website two-site-split runs the public bot site as its **own Railway service**, deployed the
same proven way as `dashboard/`: a service whose **Root Directory** is the app's own folder, so
Railway installs *that folder's* `requirements.txt` and runs *that folder's* `Procfile`. This is
what keeps each web service's build scoped to its own deps and the bot's deploy untouched.

> **It never imports `disbot`.** Like the dashboard, the bot site reads only a committed generated
> artifact — `botsite/data/site.json` (the public whitelist subset produced by
> `scripts/export_dashboard_data.py`). Decoupling is preserved; see `botsite/README.md`.

## The two (eventually three) web services

| Service | Root Dir | What it is | Auth posture | Secrets it holds |
|---|---|---|---|---|
| `worker` | repo root | the **bot** | — | bot's Postgres DSN, Discord token, AI keys ([`env-vars.md`](env-vars.md)) |
| dev site (current) | `dashboard/` | developer dashboard + control panel + submission moderation | public read pages · OAuth/owner-gated edits | `GITHUB_ISSUE_MIRROR_TOKEN`, full submissions DSN, OAuth/session, `CONTROL_API_TOKEN` |
| **bot site (new)** | **`botsite/`** | **public marketing + reference + `/submit` intake** | **fully public** | **exactly one — the INSERT-only submissions DSN** |

The per-server control panel's future move to the bot side adds a **third** service (a gated
"manage my server" manager, isolated at the process + secret level — plan §4.4 / §7.4). That slice
is gated on the control-API public-exposure security review and lands *after* the first additive
wave; it is **not** part of standing up the public bot site below, and the public marketing
service stays secret-free regardless.

## Deploy recipe (mirrors the dashboard's proven shape)

The bot site reuses the exact recipe `dashboard/` proved out (see
[`production-deployment.md`](production-deployment.md) for the bot's Railway facts and
`dashboard/README.md` for the dashboard's):

1. **New Railway service, same project.** In the production Railway project, add a **new service**
   from the same GitHub repo. It auto-builds and auto-redeploys on push to `main`, like the others.
2. **Set Root Directory = `botsite`.** This is the load-bearing setting — Railway scopes the
   build to that folder, so it installs **`botsite/requirements.txt`** (FastAPI + Jinja2 +
   uvicorn + asyncpg, kept separate from the bot's and the dashboard's deps) and **not** the bot's
   root `requirements.txt`. Without it, the service would try to install the bot's full deps (the
   trap the per-service split exists to avoid).
3. **Start command = the `Procfile`.** `botsite/Procfile` is
   `web: uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}` — identical in shape to the
   dashboard's. Because Root Directory is `botsite`, the import path is `app:app` (the module is
   `botsite/app.py`, imported as top-level `app` from inside the root dir), exactly as the
   dashboard runs `app:app` from `dashboard/`.
4. **Python pin.** The repo-root `.python-version` (`3.13.13`) applies to all repo-built services;
   keep `RAILPACK_PYTHON_VERSION` **unset** on this service so the repo stays the single source of
   truth (same rule as the bot — see [`production-deployment.md`](production-deployment.md)
   § "Python version — pinned, and why").
5. **Env vars** — see [`env-vars.md`](env-vars.md) § "Website tier". The public bot site needs
   **only** `SUBMISSIONS_DB_DSN` (an **INSERT-only** DB role) + optionally `SUBMISSIONS_IP_SALT`.
   It holds **no** OAuth secret, **no** GitHub token, **no** control-API token (plan §4.4). With
   `SUBMISSIONS_DB_DSN` unset the site still serves — `/submit` shows a "temporarily unavailable"
   state and everything else renders (dormant-by-default, same discipline as the control API).

### ⚠️ The no-`static/` gotcha (the #970 deploy-crash class)

The repo root `.gitignore` ignores `static/` (and `staticfiles/`). The dashboard hit a deploy
crash (#970) when code referenced a `static/` mount that was never committed — git-ignored, so it
existed locally but not in the Railway build. **The bot site must not rely on a committed
`static/` directory.** It mounts no static dir; CSS is Tailwind-via-CDN and any
progressive-enhancement JS is inlined in templates. If you ever add assets, either commit them
under a **non-ignored** path or serve them another way — never assume a `static/` folder survives
the build. (This is why both web services are "no JS build, no `static/` dir".)

## Run + verify locally (the `importorskip`-guarded path)

Mirrors the dashboard's local flow:

```bash
pip install -r botsite/requirements.txt
python3.10 scripts/export_dashboard_data.py     # (re)generate botsite/data/site.json (+ dashboard.json)
uvicorn app:app --reload --app-dir botsite       # http://127.0.0.1:8000
python3.10 -m pytest tests/unit/botsite/          # app smoke (local; importorskip-guarded like dashboard)
```

The committed `botsite/data/site.json` is a **generated artifact** — re-run
`scripts/export_dashboard_data.py` after its sources change; the freshness + whitelist guard
(`scripts/check_dashboard_data.py`) asserts it is regenerable-identical **and** that its top-level
keys stay within the redaction whitelist (fails closed on a new private family).

## Submissions DB + the dev-site moderation note

The public `/submit` form's only write is `INSERT … status='pending'` into a **separate,
dashboard-owned Postgres** (plan §2.3 / §7.3 / Q-0178 — *not* the bot's DB, so decoupling holds).
The one canonical schema is `botsite/migrations/001_submissions.sql`; apply it once against that
Postgres at rollout. Two helpers share **only that contract, never code**:

- `botsite/submissions_db.py` — **INSERT-only** (`insert_pending`), on the public site.
- `dashboard/submissions_db.py` — SELECT + UPDATE (`list_pending` / `set_status` /
  `attach_issue_url`), on the dev site behind the owner gate.

**Moderation lives on the dev site, never the bot site.** Nothing a user submits is shown
publicly — rows land `pending` and are invisible until the owner approves them on the dev site's
**owner-gated `/admin/moderation`** page (CSRF-protected, renders all fields **escaped**). On
approve, the **dev site** (which alone holds `GITHUB_ISSUE_MIRROR_TOKEN`) mirrors the row to a
GitHub issue using the matching `.github/ISSUE_TEMPLATE/` shape and records `github_issue_url`;
reject just flips the status. The public site never holds the GitHub token and never reaches
GitHub. Abuse defenses (honeypot + per-IP rate-limit + server-side validation, salted IP **hash**
only) are layered *before* anything is stored-visibly or mirrored (plan §4.2). See
[`dashboard-redaction-audit.md`](dashboard-redaction-audit.md) for the per-page public-read
certification and `dashboard/README.md` § Moderation for the owner-side flow.

## Rollout — additive, no downtime (plan §6)

The split is **additive**, which is what makes it safe. Sequence:

1. **The dev site never stops serving.** It *is* the current live dashboard. The split only
   **adds** to it (the public-subset emission, moderation, the GitHub mirror, these docs) — no
   existing route changes behaviour. Each piece lands green on `main` and auto-redeploys as today.
2. **Stand the bot site up dark.** Provision the new `botsite/` service once the bot-site code has
   landed. It serves on its **Railway-generated URL first** — no public domain, no announcement —
   so it is verifiable in production without being "the website" yet.
3. **Provision the submissions DB + wire env per the §4.4 matrix** (owner step): create the
   dashboard-owned Postgres, apply `001_submissions.sql`, grant the public service an
   **INSERT-only** role and the dev service a full role, set the DSNs + `GITHUB_ISSUE_MIRROR_TOKEN`
   on the dev service. Intake (`/submit`) and moderation light up only when their env is set
   (dormant-by-default).
4. **Cut over deliberately.** When the bot site is complete + reviewed, point the **marketing
   domain** at it and link it from the dev site / Discord. The dev site keeps its existing domain
   (e.g. `superbot-dashboard.up.railway.app`) for the owner + agents. *(Domains are deferred to
   cutover — Q-0178 decision 1; build on Railway URLs until then.)*

## Rollback — at every step

- **The bot site is a separate service** → if it misbehaves, **pause/delete the service** or
  **revert DNS**; the dev site and the bot are wholly unaffected.
- **The submissions DB is additive** → `DROP TABLE submissions;` fully unwinds intake (the
  migration is `CREATE TABLE IF NOT EXISTS`, forward-only + idempotent; nothing else references
  it).
- **Each dev-site PR is independently revertible** — no coupled migrations on the bot's DB
  (decoupling guarantees this).

## See also

- [`../planning/website-two-site-split-plan-2026-06-19.md`](../planning/website-two-site-split-plan-2026-06-19.md)
  — the full plan (§2 architecture, §4.4 secret matrix, §6 rollout).
- [`env-vars.md`](env-vars.md) — every env var, names + locations only (the website-tier names
  are in its own section).
- [`dashboard-redaction-audit.md`](dashboard-redaction-audit.md) — the public-read certification.
- [`production-deployment.md`](production-deployment.md) — the bot's Railway facts + the Python pin.
- `botsite/README.md` — the app's own readme (owned by P1; not edited here).
