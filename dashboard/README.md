# SuperBot developer dashboard

A personal website + developer dashboard for SuperBot, deployed as a **second Railway
service** alongside the bot. **Phase 1 (this directory) is the read-only MVP**; the
**Phase 3 env-var usage map** (`/env`, read-only) has also shipped. Full design, phases,
and the secrets model live in
[`docs/planning/developer-dashboard-plan.md`](../docs/planning/developer-dashboard-plan.md).

## What it shows

| Page | Source |
|---|---|
| `/` | Showcase landing — counts + recent updates |
| `/functions` | Bot-function catalogue (from the subsystem registry) |
| `/commands` | **Cog & command explorer** — every cog's commands, each badged prefix/slash and whether it's button-backed (a panel action or opens a view); live search + filters (`scripts/scan_commands.py`). |
| `/aliases` | **Suggest a command alias** — pick a command, propose an alias, get a live collision check against every command/alias/synonym, a prefilled GitHub issue, and a paste-ready `synonyms.py` snippet (`scripts/scan_synonyms.py`). Client-side; no backend yet. |
| `/settings` | **Settings catalogue** — every per-guild setting key, grouped by owning subsystem, with live filter. Typed settings also show their **type, default, hint, and enum choices** from the bot's `SettingSpec`s (`scripts/scan_settings.py` + `scripts/scan_setting_specs.py`). Names + metadata only, never a stored value. |
| `/access` | **Permissions & access map** — the visibility-tier ladder + which subsystems each tier can see. A faithful static mirror of `disbot/utils/visibility_rules.py` (`scripts/scan_access.py`). Visibility, **not** execution. |
| `/ideas` | Idea backlog (from `docs/ideas/`) |
| `/bugs` | Bug board (from `docs/health/bug-book.md`) + a "report a bug" CTA |
| `/updates` | Updates feed (from `.sessions/` logs) |
| `/status` | Dashboard inventory/status page — generated build metadata, artifact counts, open bug summary, and access-tier health from `dashboard.json`. |
| `/env` | Env-var **usage map** — each variable → every file/line that reads it, required/optional, by layer. **Names + locations only, never values** (`scripts/scan_env_usage.py`). |
| `/healthz` | Liveness probe (JSON) for Railway |

## Decoupling

This app **never imports `disbot/`.** It reads only `dashboard/data/dashboard.json`,
produced by `scripts/export_dashboard_data.py` (pure stdlib — which calls the equally
pure-stdlib `scripts/scan_env_usage.py` for the env map and `scripts/scan_commands.py` for
the command explorer). The bot and its Railway service are completely independent of this one.

## Secrets safety (the `/env` map)

The env-var map is **static analysis** of the bot source: it surfaces variable *names*
and the *code locations* that read them — it never reads, stores, or renders a secret
**value**, and it never opens an `.env` file. Railway stays the single source of truth for
the values; managed value editing (behind owner login, masked) is a later Phase 3 slice.

## Run locally

```bash
pip install -r dashboard/requirements.txt
python3.10 scripts/export_dashboard_data.py     # (re)generate dashboard/data/dashboard.json
uvicorn dashboard.app:app --reload              # http://127.0.0.1:8000
```

## Regenerate the data

The committed `dashboard/data/dashboard.json` is a generated artifact. Re-run after the
sources (subsystem registry, ideas, bug book, session logs) change:

```bash
python3.10 scripts/export_dashboard_data.py
```

## Tests

```bash
python3.10 -m pytest tests/unit/scripts/test_export_dashboard_data.py   # runs in CI (stdlib)
pip install -r dashboard/requirements.txt httpx
python3.10 -m pytest tests/unit/dashboard/                              # app smoke (local)
```

The app smoke test is `importorskip`-guarded, so it skips automatically in CI (which
installs only the bot's `requirements.txt`).

## Deploy on Railway (second service)

Deploy as a **second service** in the existing Railway project — the bot's `worker`
service is untouched (it keeps using the root `Procfile` + `requirements.txt`).

1. Railway → your project → **New → GitHub Repo** → `menno420/superbot`.
2. Open the new service → **Settings → Source**: set **Root Directory** to `dashboard`.
   This is essential — it makes Railway build *this* folder (installing
   `dashboard/requirements.txt`, **not** the bot's deps) and run `dashboard/Procfile`.
   With the repo root as the directory, Railway installs the bot's requirements
   (no FastAPI) and the service fails to start.
3. **Start command:** taken from `dashboard/Procfile`
   (`uvicorn app:app --host 0.0.0.0 --port $PORT`) — no need to set it by hand.
4. **Healthcheck path** (optional): `/healthz`.
5. **Environment variables:** none required — the read-only MVP serves the committed
   `dashboard/data/dashboard.json` (no DB, no secrets, no API keys). Later phases add them.
6. **Networking → Generate Domain** for a public URL.

Redeploys automatically on push to `main`. To refresh the displayed data, regenerate
`dashboard/data/dashboard.json` and commit it.

> **Note:** the dashboard intentionally has **no `static/` directory** — the repo's root
> `.gitignore` ignores `static/`, so a file there would never be committed or deployed.
> Styling is the Tailwind CDN plus a small inline `<style>` block in `base.html`.
