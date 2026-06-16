# Session — Developer dashboard (personal website) — design + read-only MVP

> **Status:** `complete`

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

## What shipped (PR #967)

Phase 1 read-only MVP of the developer dashboard — a **decoupled** FastAPI app under `dashboard/`
that never imports `disbot/`:

- `dashboard/` — FastAPI app: 5 pages (`/`, `/functions`, `/ideas`, `/bugs`, `/updates`) + `/healthz`,
  Jinja2 templates + Tailwind (CDN), serving the function catalogue, idea backlog, bug board, updates
  feed, and a public showcase landing.
- `scripts/export_dashboard_data.py` (stdlib) — AST-parses the subsystem registry and parses
  `docs/ideas/`, `docs/health/bug-book.md`, and `.sessions/` into `dashboard/data/dashboard.json`
  (33 functions · 69 ideas · 14 bugs · 60 updates).
- Tests: exporter parsers (CI, stdlib) + an `importorskip`-guarded app smoke test (skips in CI where
  the web deps are absent).
- Docs: [`docs/planning/developer-dashboard-plan.md`](../docs/planning/developer-dashboard-plan.md)
  (architecture, two zones, stack, Railway deploy, secrets-safety, 4 phases),
  [`docs/ideas/developer-dashboard-2026-06-16.md`](../docs/ideas/developer-dashboard-2026-06-16.md)
  (indexed), `dashboard/README.md`, and router **Q-0154** (the four owner decisions).

## Verification

- `python3.10 scripts/check_quality.py --full` → **green (10089 passed, 37 skipped)**.
- `python3.10 scripts/check_architecture.py --mode strict` → **exit 0** (no new violations — no
  `disbot/` code touched).
- `python3.10 scripts/check_docs.py --strict` → green (new docs reachable + indexed).
- Local app smoke (fastapi installed): all 5 pages return 200 with real data (the Economy subsystem +
  its `!` commands; the BUG-0014 FIXED badge; live counts).

**Merge ≠ deploy:** this PR is purely additive and changes no bot runtime. The dashboard goes live
only once the owner creates the second Railway service (steps in `dashboard/README.md`); merging does
not affect the bot's Railway deploy.

## 💡 Session idea (Q-0089)

**A shared `docs_ledger` parsing helper.** Writing `export_dashboard_data.py` surfaced that the repo's
markdown ledgers are *almost* machine-readable but every consumer re-implements the extraction: my
exporter's `_STATUS_RE` is nearly identical to `check_session_gate.py`'s, and `check_session_log.py` /
`check_docs.py` each re-derive "parse a Status badge / a `BUG-NNNN` entry / an idea file" themselves.
A tiny shared stdlib module (one source of truth for those parsers) would let the dashboard *and* the
checker scripts share it — fewer drifting regexes, and it makes the "surface the repo's data"
principle reusable. Small/decided-lane; recorded here, not built.

## ⟲ Previous-session review (Q-0102)

Previous session: **Hermes efficiency skills (#959)** — idea-spotlight / morning-briefing /
dispatch-resolve + a 6h interactive session auto-reset.
- **Did well:** strong consolidation instinct — "one morning message instead of several pings" and a
  daily idea-spotlight that turns the backlog into a decision queue; each skill shipped with a clear
  home doc.
- **Could have surfaced:** those skills make the agent network more legible to the owner, but they
  live on the VPS/Hermes side with manual install steps and **no owner-facing surface to see their
  output in one place.** This session's dashboard is the natural complement — the Phase 4 "AI control
  board" should ingest the idea-spotlight verdict ledger + the morning-briefing digest so the rituals
  are visible in the web UI, not only in Discord.
- **Workflow improvement:** when a session ships an *owner-facing ritual* (a digest, a spotlight), add
  a one-line "where will the owner see this?" check — several such rituals now exist with no shared
  surface, which is exactly the gap this dashboard fills.

## Documentation audit (Q-0104)

- `check_docs.py --strict` → green (idea file + plan reachable and indexed). `check_architecture
  --mode strict` → exit 0.
- Owner decisions recorded in the question router (**Q-0154**). Not a bug → no bug-book entry.
- `current-state.md` In-flight deliberately names no open PRs (convention) and Recently-shipped is
  merged-only, so #967 is left for the merge-time reconciliation — the expected lag (Q-0124: a manual
  session does not run the recon pass; the pre-existing 11-PR ledger drift stays the routine's job).
- No chat-only durable info outstanding — the design + decisions live in the plan, the idea file,
  router Q-0154, and this log.
