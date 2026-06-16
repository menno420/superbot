# SuperBot developer dashboard

A personal website + developer dashboard for SuperBot, deployed as a **second Railway
service** alongside the bot. **Phase 1 (this directory) is the read-only MVP.** Full
design, phases, and the secrets model live in
[`docs/planning/developer-dashboard-plan.md`](../docs/planning/developer-dashboard-plan.md).

## What it shows (Phase 1)

| Page | Source |
|---|---|
| `/` | Showcase landing — counts + recent updates |
| `/functions` | Bot-function catalogue (from the subsystem registry) |
| `/ideas` | Idea backlog (from `docs/ideas/`) |
| `/bugs` | Bug board (from `docs/health/bug-book.md`) + a "report a bug" CTA |
| `/updates` | Updates feed (from `.sessions/` logs) |
| `/healthz` | Liveness probe (JSON) for Railway |

## Decoupling

This app **never imports `disbot/`.** It reads only `dashboard/data/dashboard.json`,
produced by `scripts/export_dashboard_data.py` (pure stdlib). The bot and its Railway
service are completely independent of this one.

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
