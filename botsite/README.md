# SuperBot — public bot site

The **public marketing + reference website** for SuperBot, deployed as its own
Railway service (separate from both the bot and the developer dashboard). It is the
public half of the website two-site split — full design, topology, security model,
and the build decomposition live in
[`docs/planning/website-two-site-split-plan-2026-06-19.md`](../docs/planning/website-two-site-split-plan-2026-06-19.md).

**This directory is the serial foundation (units S1 + S2 + P1).** The app wires every
route up front; the reference/changelog/status page templates and the `/submit`
intake form land in the parallel back-half units (P2–P4).

## What it serves

| Route | What | Template / source |
|---|---|---|
| `/` | Marketing landing — hero, feature bands, honest capability counts, "Add to Discord" | `index.html` (this unit) |
| `/commands` | Read-only command reference (search + filters) | `commands.html` (P2) |
| `/features` | Feature showcase (function + game catalogue, user-framed) | `features.html` (P2) |
| `/changelog` | User-facing bot changelog | `changelog.html` (P3) ← `site.json.bot_changelog` |
| `/status` | User trust band — online (as of last deploy) · build · counts | `status.html` (P3) |
| `/submit` | Public bug/suggestion form → `pending` intake | `botsite/submit.py` + `submit.html` (P4) |
| `/healthz` | Liveness probe (JSON) for Railway | app constant |

The routes for the P2/P3 templates are **wired now** (in `app.py`) but reference
template files that land in those later units — that is by design, so `app.py` stays
the single owner of routing and the back half is file-disjoint.

## Decoupling (the hard rule)

This app **never imports `disbot/`.** It reads only the committed public subset
`botsite/data/site.json`, produced by `scripts/export_dashboard_data.py`
(`--targets site`). That subset is **redaction by construction** — an explicit
top-level whitelist (`meta`, `counts`, `catalogue`, `commands`, `bot_changelog`) that
*physically cannot* contain a dev-only family (env vars, settings, access, reviews,
ideas, raw bugs) or any per-guild value. A CI guard asserts the file's keys stay a
subset of that whitelist (fails closed on a new key).

## Secret posture — and why it stays clean

This is the **public, secret-free** surface. It holds **at most one** secret: the
**INSERT-only** submissions DB DSN (`SUBMISSIONS_DB_DSN`) used by `/submit` to write
one `pending` row. It never holds the GitHub mirror token, the control-API token, or
any OAuth secret (plan §4.4 secret matrix). A full compromise of this service cannot
read submissions, reach GitHub, reach the bot, or touch the bot's DB.

**The future "manage my server" control panel is a *separate service*, not a router
mounted here** (plan §4.4 / §7.4). Mounting a control-API-writing editor inside this
process would make a marketing-surface compromise reach `CONTROL_API_TOKEN` — defeating
the invariant. So the gated manager gets its own process + env scope and drops in under
the bot-site domain **without any refactor of this app**: `app.py` keeps wiring only the
public routes, and `botsite/submit.py` is the one write seam (INSERT-only).

## Run locally

```bash
pip install -r botsite/requirements.txt
python3.10 scripts/export_dashboard_data.py --targets site   # (re)generate site.json
uvicorn botsite.app:app --reload                             # http://127.0.0.1:8000
```

## Regenerate the data

The committed `botsite/data/site.json` is a generated artifact (same producer as the
dashboard). Re-run after the sources change:

```bash
python3.10 scripts/export_dashboard_data.py                  # writes BOTH artifacts
```

## Tests

```bash
python3.10 -m pytest tests/unit/scripts/test_export_dashboard_data.py   # runs in CI (stdlib)
pip install -r botsite/requirements.txt
python3.10 -m pytest tests/unit/botsite/                                # app + db smoke (local)
```

The app smoke test is `importorskip`-guarded, so it skips automatically in CI (which
installs only the bot's `requirements.txt`).

## Deploy on Railway (a new service)

Deploy as a **new service** in the existing Railway project — the bot's `worker` and
the dashboard service are untouched.

1. Railway → your project → **New → GitHub Repo** → `menno420/superbot`.
2. New service → **Settings → Source**: set **Root Directory** to `botsite`. This is
   essential — it makes Railway build *this* folder (installing `botsite/requirements.txt`,
   **not** the bot's deps) and run `botsite/Procfile`.
3. **Start command:** taken from `botsite/Procfile` (`uvicorn app:app --host 0.0.0.0
   --port $PORT`).
4. **Healthcheck path** (optional): `/healthz`.
5. **Environment variables:** none required for the read-only pages. `/submit` lights
   up only when `SUBMISSIONS_DB_DSN` (an INSERT-only role on the dashboard-owned
   submissions DB) is set — dormant-by-default until then.
6. **Networking → Generate Domain** for a public URL (domains are deferred to cutover —
   plan §7.1; dark-launch on the Railway URL first).

Redeploys automatically on push to `main`. Refresh the data by regenerating
`botsite/data/site.json` and committing it.

> **Note:** the bot site intentionally has **no `static/` directory** — the repo's root
> `.gitignore` ignores `static/`, so a file there would never be committed or deployed
> (the #970 deploy-crash gotcha). Styling is the Tailwind CDN + a small inline `<style>`
> block in `base.html`.
