# Developer dashboard (personal website) — plan

> **Status:** `plan` — owner-approved direction (2026-06-16, router Q-0154). Phase 1
> (read-only MVP) ships in **PR #967**; Phases 2–4 are planned, not yet built. Source
> code and merged PRs win over this document.

## What this is

A personal website **and** developer dashboard for SuperBot, deployed as a **second
Railway service** alongside the bot. Owner request (2026-06-16): *"build me a personal
website that's linked to my project"* — usable as a checklist, an update tracker, a
bot-function catalogue, an ideas/bug board, a **public** bug-reporting surface, a way to
link multiple AIs together, a developer dashboard that integrates with the project, and
**a place to safely store env values and track where each is used.**

## Owner decisions (2026-06-16, router Q-0154)

| Decision | Choice |
|---|---|
| **Link multiple AIs** | **Control board over the current flow** — show each idea's pipeline stage, trigger the existing Claude routines (the `/fire` API), and surface an agent activity feed. *Not* a live multi-provider dispatcher (deferred to a later phase). |
| **Secrets** | **Usage map + manage values via Railway** — Railway stays the single source of truth; the dashboard is a UI over its env vars (no second copy of secrets). |
| **Bug reports** | Stored in the dashboard **and** mirrored to GitHub issues. |
| **Start** | Design doc in the repo **plus** a working read-only MVP this session. |

## Core principle — surface, don't duplicate

Most of what the owner asked for already exists as structured data in the repo, on
GitHub, or on Railway. The dashboard's job is to **surface and add to** those sources,
not re-implement them:

| Feature | How it's built | Existing data source |
|---|---|---|
| Bot-function catalogue | catalogue page | `disbot/utils/subsystem_registry.py` (AST-parsed; never imported) |
| Update tracking / changelog | updates feed | `.sessions/*.md` logs (+ later GitHub PRs, `current-state.md`) |
| Ideas board | ideas page | `docs/ideas/*.md` |
| Bug board | bugs page | `docs/health/bug-book.md` |
| Public bug reporting | form (Phase 2) | new → dashboard DB **+** GitHub issues |
| Checklist | personal to-do (Phase 2) | new → dashboard DB |
| Link multiple AIs | control board (Phase 4) | `CLAUDE_ROUTINE_FIRE_URL` (`/fire`), GitHub PRs, `ai-project-workflow.md` |
| Secrets store + usage map | secrets zone (Phase 3) | Railway API (values) + static code scan (usage) |

## Architecture

### Two zones (hard boundary)

* **Public zone** (no auth): showcase landing, bot-function catalogue, public
  bug-report form. Read-only and write-only-intake; spam-protected.
* **Private zone** (owner auth): checklist, ideas/bug management, updates, the AI
  control board, and the **secrets** area.

The secrets area is **never** reachable from the public side — they do not share a
trust boundary.

### Stack

FastAPI + Jinja2 templates + Tailwind (CDN, no JS build step), Python 3.10+, with its
own small Postgres for mutable state (checklist, bug mirror). Single language (Python)
so the agents that maintain this repo stay fluent; server-rendered for simplicity and
security.

**Decoupling guarantee:** `dashboard/` does **not** import `disbot/`. It reads the
generated `dashboard/data/dashboard.json` and (in later phases) the GitHub and Railway
APIs. The bot runtime is never in the dashboard's process.

### Deployment (Railway)

A **second service** in the existing Railway project:

* Root directory: repo root · Start: `uvicorn dashboard.app:app --host 0.0.0.0 --port $PORT`
* Dependencies: `dashboard/requirements.txt` (kept separate from the bot's root
  `requirements.txt`, so the bot's build and CI install are unaffected)
* Watch paths: `dashboard/**` (bot-only changes don't rebuild the dashboard, and
  vice-versa)
* Shares the existing Railway Postgres (its own tables) and reads/writes env values
  through the Railway API. The bot's `worker` service is untouched.
* Public URL: the service's `*.up.railway.app` domain (or a custom domain). The private
  dashboard sits behind a login on the same service.

### Data flow

`scripts/export_dashboard_data.py` (stdlib only) reads the repo sources and writes
`dashboard/data/dashboard.json`; the app renders that JSON. A CI step / Railway build
hook can regenerate it; later phases add live GitHub/Railway API reads and DB writes.

## Secrets — done safely

1. **No second vault.** Secrets already live in Railway (encrypted, read by the deploy).
   The dashboard is a *UI over Railway's env vars* via its API — no second copy to breach.
2. **Usage map is static analysis.** A `scripts/scan_env_usage.py` maps each env var →
   every file/line that reads it → its subsystem + required/optional. ~36 vars across
   ~20 modules, mostly centralised in `disbot/config.py`. This part is read-only and
   safe, so it ships first within Phase 3.
3. **Owner-auth only, masked by default, never logged or committed.** The public zone
   has zero secret access.

## Phases

* **Phase 1 — read-only MVP (this PR #967):** catalogue, ideas, bugs, updates feed,
  public showcase. ✅
* **Phase 2 — interactivity:** owner auth · personal checklist (own DB) · public
  bug-report form → stored in the dashboard **and** mirrored to a GitHub issue
  (spam-protected).
* **Phase 3 — env/secrets:** the usage map (read-only, safe) first, then Railway-backed
  value management behind login (masked, audited).
* **Phase 4 — multi-AI control board:** pipeline-stage view · routine trigger buttons
  (`/fire`) · agent activity feed (sessions + PRs).

## What Phase 1 builds

* `dashboard/` — FastAPI app (5 pages + `/healthz`), Jinja2 templates, static asset.
* `scripts/export_dashboard_data.py` + committed `dashboard/data/dashboard.json`.
* Tests — exporter parsers (run in CI); app smoke test (`importorskip`-guarded, skipped
  in CI where the web deps are absent).
* `dashboard/README.md` — run + deploy instructions.

## Verification

```bash
python3.10 scripts/export_dashboard_data.py
python3.10 -m pytest tests/unit/scripts/test_export_dashboard_data.py
# local app smoke (optional — web deps not in CI):
pip install -r dashboard/requirements.txt httpx
python3.10 -m pytest tests/unit/dashboard/
uvicorn dashboard.app:app --reload   # then open http://127.0.0.1:8000
```

## Open questions (decide at the relevant phase)

* **Auth method** (owner login) — GitHub OAuth vs a simple password — Phase 2.
* **DB** — shared Railway Postgres vs its own instance — Phase 2.
* **Live refresh** — CI-regenerated JSON vs app-side live build — Phase 1 uses committed
  JSON; revisit if staleness becomes an issue.
