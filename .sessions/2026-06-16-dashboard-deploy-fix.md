# Session — Dashboard deploy fix (StaticFiles crash) + Railway deploy config

> **Status:** `in-progress`

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

_(Close-out — 💡 idea, ⟲ previous-session review, docs audit — added before the badge flips to
`complete`.)_
