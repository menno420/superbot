# Session — Developer dashboard (personal website) — design + read-only MVP

> **Status:** `in-progress`

## Origin

Owner request (2026-06-16): *"build me a personal website that's linked to my project"* — usable as a
checklist, update tracker, bot-function catalogue, ideas/bug board, **public** bug reporting, a way to
link multiple AIs together, a developer dashboard that integrates with the project, and a place to
**safely store env values and track where each is used.** Asked: *is this possible, and can you help
design it?* — Yes. He answered the four shaping questions:

- **AI linking** → *control board over the current flow* (pipeline stages + trigger the existing Claude
  routines via the `/fire` API + agent activity feed). Not a live multi-provider dispatcher (yet).
- **Secrets** → *usage map + manage values via Railway* (Railway stays the single source of truth — no
  second copy of secrets).
- **Bug reports** → stored in the dashboard **and** mirrored to GitHub issues.
- **Start** → design doc in the repo **plus** a working read-only MVP this session.

## What this session is doing (HOLD — born-red per Q-0133)

1. **Design** — `docs/ideas/developer-dashboard-2026-06-16.md` (+ README index entry) and the phased
   plan `docs/planning/developer-dashboard-plan.md` (two zones public/private, FastAPI+HTMX stack,
   Railway second-service deploy, the secrets-done-safely model, 4 phases).
2. **Read-only MVP** — a decoupled FastAPI app under `dashboard/` that reads the repo's existing
   structured data and renders: bot-function catalogue, ideas, bug board, an updates feed, and a public
   showcase landing page.
3. **Data layer** — `scripts/export_dashboard_data.py` (stdlib only) + `dashboard/repo_data.py`
   serialize the subsystem registry, `docs/ideas/`, `docs/health/bug-book.md`, `.sessions/` logs and
   `docs/current-state.md` into JSON; unit tests for the parsers.
4. **Deploy notes** — `dashboard/README.md`: how to run it as a second Railway service.

**Decoupling guarantee:** `dashboard/` does **not** import `disbot/` — it reads generated JSON (and,
in later phases, the GitHub/Railway APIs). The bot runtime and its Railway service are untouched; this
PR is purely additive. New web deps live in `dashboard/requirements.txt` (not the bot's), so CI's
`requirements.txt`-only install is unaffected; the FastAPI smoke test is `importorskip`-guarded.

_(Close-out — 💡 session idea, ⟲ previous-session review, docs audit — added before the badge flips to
`complete` as the deliberate final step.)_
