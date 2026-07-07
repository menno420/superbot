# SuperBot — public bot site

> **New here / learning the web side?** Read
> [`docs/owner/website-explained.md`](../docs/owner/website-explained.md) first — a
> plain-language tour of Jinja vs. the SPA, the data pipeline, and how to work with
> Claude Design.

The **public marketing + reference website** for SuperBot, deployed as its own
Railway service (separate from both the bot and the developer dashboard). It is the
public half of the website two-site split — full design, topology, security model,
and the build decomposition live in
[`docs/planning/website-two-site-split-plan-2026-06-19.md`](../docs/planning/website-two-site-split-plan-2026-06-19.md).

**The public front-end is now the Claude-Design SPA** (`botsite/site/`), served by
this FastAPI app with its data layer generated live from `site.json`. The earlier
server-rendered Jinja pages (`templates/`) remain wired as a working fallback.

**The v2 estate (2026-07-07, the program design session)** adds three new surfaces
on top — all new files; the v1 design-owned files stay untouched:

- **`botsite/ds/` — the program design system.** Shared foundation for every
  program site: `tokens.css` (semantic tokens, dark-first + a full light theme),
  `components.css` (the component library), `ds.js` (theme manager, icons,
  dataviz-spec chart renderers, the Ctrl+K command palette). Living style guide at
  **`/design`** — it renders every token + component from the real CSS and is the
  system's own test surface.
- **`botsite/site/v2/` — the v2 public site** on that system, always reachable at
  **`/v2`**. `/` keeps serving v1 until the owner sets **`BOTSITE_FRONTEND=v2`** on
  the Railway service (rollback = unset it). v2 adds the full 43-feature catalogue
  with per-feature pages + area hubs, a filterable commands browser, the global
  command palette, a real light theme, honest build provenance, and suggestion
  links that route to the real `/submit` intake.
- **`botsite/console/` — the program console** at **`/console`**: the owner's
  one-glance page. Real lanes render the committed `botsite/data/console.json`
  feed (session run reports with ⚑ self-initiated flags, ideas/bugs counters, the
  changelog); missing feeds render as *declared* pending lanes (Q-0248 telemetry,
  rebuild parity, Q-0251 trading) — never fake data. Regenerate the feed with
  `python3.10 scripts/export_dashboard_data.py --targets console` (the default
  export also writes it).

The UX regression harness for all of this lives in `tools/web_ux/`
(`check_web_ux.py` — task-success checklist with interaction budgets, nav
coverage, perf + a11y budgets; `screenshot_pages.py` — full-page captures both
themes × three widths). Run it before shipping front-end changes.

## The front-end — the Claude-Design SPA (what visitors see)

The public front-end is the **Claude-Design single-page app** in `botsite/site/`
(neon theme: Home / Features / Commands / Games / Changelog / Status). It is a
vanilla-JS, no-build, hash-routed SPA whose every page renders from one global
`window.SBDATA` object. Three of its files are **design-owned and copied verbatim**
from the Claude-Design handoff — **do not edit them** (the design is finished;
touching them drifts from the intended look and breaks the round-trip with Claude
Design):

- `botsite/site/index.html` — the shell (nav + an empty `<main id="app">`).
- `botsite/site/app.js` — the hash router + view renderers.
- `botsite/site/app.css` — the theme.

The **only** data file we own is `botsite/site/data.js`, and we **generate** it
(never hand-write it) from the canonical `site.json` — see "Data flow" below.

## What it serves

| Route | What | Source |
|---|---|---|
| `/` | The SPA shell (the public site) | `site/index.html` |
| `/app.js`, `/app.css` | SPA router + theme (verbatim design assets) | `site/*` |
| `/data.js` | **The SPA data layer — generated live from `site.json` per request** | `site_data.py` |
| `/commands` `/features` `/changelog` `/status` | **Legacy** Jinja pages — kept as a working fallback (the SPA equivalents are `/#/commands` …) | `templates/*.html` ← `site.json` |
| `/submit` | Public bug/suggestion form → `pending` intake | `botsite/submit.py` + `submit.html` |
| `/healthz` | Liveness probe (JSON) for Railway | app constant |

`app.py` stays the **single owner of routing**. The SPA's own nav uses in-page hash
routes (`#/commands`, …), so visitors land on `/` and never hit the legacy path
routes; those remain wired for old bookmarks / no-JS fallback.

## Data flow — one pipeline, no drift

```
disbot/  ──(scripts/export_dashboard_data.py)──▶  botsite/data/site.json   (CI-guarded public subset)
                                                       │
                                       botsite/site_data.py  (build_prototype_data + render_data_js)
                                                       ▼
                                   window.SBDATA  ──▶  /data.js (live, per request)
                                                  └─▶  botsite/site/data.js (committed static fallback)
```

`site_data.py` maps the `site.json` subset onto the SPA data contract
(`ICONS` / `AREAS` / `COMMANDS` / `GAMES` / `CHANGELOG` / `STATUS` + lookup helpers).
It is **stdlib-only and never imports `disbot`**, so it ships inside `botsite/` and
the `/data.js` route renders it live. The committed `botsite/site/data.js` is the
static fallback (so the prototype also works opened as a bare file); in the running
service the dynamic route wins. Contract invariants (every `area`/`command`
cross-reference resolves, icons/colors are valid) are guarded by
`tests/unit/botsite/test_site_data.py` (stdlib → runs in CI).

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
python3.10 scripts/export_dashboard_data.py --targets site   # regenerate site.json + site/data.js
uvicorn botsite.app:app --reload                             # http://127.0.0.1:8000  (→ the SPA)
```

Open <http://127.0.0.1:8000> for the SPA. `/data.js` is served live from the current
`site.json`, so editing data is just: regenerate `site.json` (above) and refresh.

## Regenerate the data

The committed `botsite/data/site.json` **and** `botsite/site/data.js` are generated
artifacts (same producer as the dashboard). Re-run after the sources change:

```bash
python3.10 scripts/export_dashboard_data.py     # writes dashboard.json + site.json + site/data.js
python3.10 -m botsite.site_data                 # just regenerate site/data.js from site.json
```

> The running service does **not** need `site/data.js` refreshed by hand — `/data.js`
> renders live from `site.json`. The committed file is only the static/offline
> fallback, kept in sync by the export above (a CI test fails if it drifts).

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
