# Session — Dashboard deploy fix (StaticFiles crash) + Railway deploy config

> **Status:** `complete`

## Origin

Owner (2026-06-16): *"can you guide me ... correctly put this website online"* → *"you should have
full access to railway ... please do it."* I have Railway API access (`RAILWAY_API_KEY`), so I deployed
the dashboard directly as a **new `dashboard` service** in the `reliable-grace` project (isolated from
`worker`/`Postgres`). The first deploys **FAILED**: the build compiled, but the container crashed at
startup —

```
RuntimeError: Directory '/app/static' does not exist
  app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), ...)
```

**Root cause:** the repo's root `.gitignore` (line 85, `static/`) silently excluded
`dashboard/static/`, so `style.css` was never committed → the dir is absent in the deployed image. It
passed locally only because the file exists on disk. (Found via the Railway runtime logs.)

## What this session is doing (HOLD — born-red per Q-0133)

- `dashboard/app.py`: remove the `StaticFiles` import + `/static` mount (the crash). The app no longer
  needs a `static/` dir at all — styling is the Tailwind CDN + a small inline `<style>` in `base.html`.
- `dashboard/templates/base.html`: inline the two trivial CSS rules instead of `/static/style.css`.
- `dashboard/Procfile`: `web: uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}` → the Railway
  service is zero-config when its **root directory = `dashboard/`**.
- `dashboard/README.md` + `docs/planning/developer-dashboard-plan.md`: correct the deploy steps to
  **root directory = `dashboard/`** (repo-root was wrong — it installs the bot's deps, no FastAPI) and
  record the `static/`-gitignore gotcha.

Builds on top of #969 (env map, merged). No `disbot/` runtime touched; purely the dashboard + docs.

## Outcome — LIVE ✅

Deployed via the Railway API (account token) as a new **`dashboard`** service in `reliable-grace`,
isolated from `worker`/`Postgres`:

- Config: root directory `dashboard/`, start `uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}`,
  healthcheck `/healthz`, public domain **`dashboard-production-746b.up.railway.app`**. **No env vars**
  (the read-only MVP serves committed JSON).
- The first three deploys crashed on the `static/` mount (above). After this fix, deploy `1e7d8af4` is
  **SUCCESS**: `GET /` → 200 (showcase) and `GET /healthz` → 200.
- The service temporarily tracks this branch to bring the site up immediately; it is repointed at
  `main` once this PR merges (the durable state).

## Verification

- `check_quality.py --check-only` → green; `check_docs.py --strict` → green.
- `pytest tests/unit/dashboard/test_app.py` → 8 passed (all routes render without the static mount).
- Live Railway deploy `1e7d8af4` SUCCESS; `/` and `/healthz` both 200.

## 💡 Session idea (Q-0089)

**A "deployed assets are git-tracked" guard.** This was a classic *works-locally / breaks-in-deploy*:
the app referenced `dashboard/static/`, which the root `.gitignore` silently excluded, so it was absent
from the deployed image. A tiny test asserting every directory the dashboard app reads/mounts
(`templates/`, `data/`) is **git-tracked** (`git ls-files` non-empty) would have caught it pre-deploy —
generalisable to "flag code that references a path matched by `.gitignore`." Small/decided-lane.

## ⟲ Previous-session review (Q-0102)

Previous session: **#969 env-usage map**.
- **Did well:** clean stdlib AST scanner, a `/env` page, a generated `env-vars.md`, good tests — a solid
  Phase-3a slice built neatly on the Phase-1 MVP.
- **What it (and #967) missed:** both extended the dashboard without ever **deploying** it, so the
  latent `static/` deploy bug rode along undetected — a web app that had never run in its target
  environment. **Workflow improvement:** for a brand-new deployable surface, do a real deploy (or at
  least the git-tracked-assets guard above) in the *first* slice, not several PRs later. Green local
  tests created false confidence because they ran against the working tree, not the committed image.

## Documentation audit (Q-0104)

- `check_docs --strict` green. Deploy steps corrected in `dashboard/README.md` + the plan; the
  `static/`-gitignore gotcha recorded in both + this log.
- A **deploy-config defect found during deployment**, not a live bot/user bug → no `bug-book` entry
  (that ledger is for bot runtime bugs); root cause + fix live here and in the README.
- `current-state.md` In-flight names no open PRs (convention); #967/#969/#970 land in the merge-time
  reconciliation (Q-0124) — the pre-existing ledger drift stays the routine's job.
