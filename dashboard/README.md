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
| `/ideas` | Idea backlog (from `docs/ideas/`) |
| `/bugs` | Bug board (from `docs/health/bug-book.md`) + a "report a bug" CTA |
| `/updates` | Updates feed (from `.sessions/` logs) |
| `/env` | Env-var **usage map** — each variable → every file/line that reads it, required/optional, by layer. **Names + locations only, never values** (`scripts/scan_env_usage.py`). |
| `/healthz` | Liveness probe (JSON) for Railway |

## Decoupling

This app **never imports `disbot/`.** It reads only `dashboard/data/dashboard.json`,
produced by `scripts/export_dashboard_data.py` (pure stdlib — which calls the equally
pure-stdlib `scripts/scan_env_usage.py` for the env map). The bot and its Railway service
are completely independent of this one.

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

1. New service in the existing Railway project, from this repo.
2. **Root directory:** repo root (so the start command can import `dashboard.app`).
3. **Start command:** `uvicorn dashboard.app:app --host 0.0.0.0 --port $PORT`
4. **Install:** `pip install -r dashboard/requirements.txt`
5. **Watch paths:** `dashboard/**` (so bot-only changes don't rebuild this service).

The bot's `worker` service is untouched — it keeps using the root `requirements.txt` and
`Procfile`. Later phases attach this service to the existing Railway Postgres and the
Railway API (for the secrets zone).
