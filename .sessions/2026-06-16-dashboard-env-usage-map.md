# Session — Dashboard Phase 3 (read-only env-var usage map)

> **Status:** `complete`

## Origin

Scheduled dispatch, empty work order → advance the next plan slice. The `ready` decade-queue
(band-#930 §4) is consumed: slots 2/3 shipped (#937/#938/#940), slots 4/5 are `needs-hermes-review`
(#929/#941), slots 6–9 are plan-first/creds/data-gated. The freshest owner-requested lane is the
**developer dashboard** ([`docs/planning/developer-dashboard-plan.md`](../docs/planning/developer-dashboard-plan.md),
Phase 1 MVP shipped #967). The plan explicitly names the next buildable, non-gated artifact:

> "**Usage map is static analysis.** A `scripts/scan_env_usage.py` maps each env var → every
> file/line that reads it → its subsystem + required/optional. … This part is read-only and
> **safe, so it ships first within Phase 3.**"

This is a contained, reversible, test-covered, in-repo, **decoupled** slice with no creds and no
owner gate — it reads env var *names and usage locations only*, never values, never `.env`.

## What this session is doing (HOLD — born-red per Q-0133)

1. **`scripts/scan_env_usage.py`** (stdlib, AST) — scan `disbot/**/*.py` for `os.getenv` /
   `os.environ.get` / `os.environ[...]` (+ `from os import getenv/environ` forms). For each env
   var: name, every usage (file·line·layer), `required` (no default anywhere ⇒ required), and the
   set of layers/areas that read it. Never reads a value.
2. **Wire into the exporter** — `export_dashboard_data.build_data` gains an `env_usage` section +
   count (calls the scanner; both stdlib, so CI's `requirements.txt`-only install is unaffected).
3. **`/env` dashboard page** — `dashboard/app.py` route + `templates/env.html` + nav link in
   `base.html`; renders the usage map (required-first), masked-by-design (no values present).
4. **Tests** — scanner unit tests (each pattern · required/optional · area mapping · no-value
   guarantee) + an exporter `env_usage` shape test + an app smoke assertion for `/env`.
5. **De-stale** — mark the plan's Phase 3 usage-map slice shipped; ledger entry next-session per
   the merged-only convention.

**Decoupling guarantee:** `dashboard/` still never imports `disbot/`. The scanner is a `scripts/`
seam (like the exporter) that produces JSON; the app renders JSON. No bot runtime is touched, no
new bot dependency added. CI green + arch 0 are the gate.

## What shipped (PR #969)

Two slices, both decoupled (`dashboard/` never imports `disbot/`), no `disbot/` runtime touched:

1. **`scripts/scan_env_usage.py`** — stdlib AST scanner. Detects `os.getenv` / `os.environ.get` /
   `os.environ[...]` (+ `from os import getenv/environ`) across `disbot/**/*.py`. Per var: name,
   every usage (file·line·layer), `required` (read without a default *anywhere* ⇒ required), layer
   set. **Names + locations only — never a value, never `.env`.** Found 34 vars (3 required:
   `DATABASE_URL`, `DISCORD_BOT_TOKEN_PRODUCTION`, `YOUTUBE_API_KEY` — verified against source per
   Q-0120). Wired into `export_dashboard_data.build_data` (`env_usage` section + count) and a new
   dashboard `/env` page (`templates/env.html`, required-first, masked-by-design) + nav link.
2. **`docs/operations/env-vars.md`** — a `--write-doc` mode renders the inventory as a committed,
   `living-ledger`-badged reference (the in-repo human-readable form of `/env`, useful *now* while
   the dashboard service isn't deployed). Generated **from the same scanner** (one parser, no
   parallel logic); a sync test (`test_committed_env_vars_doc_is_in_sync`) pins the committed file to
   a fresh render. Linked from `production-deployment.md` for reachability. A hard sync guard is
   defensible here (unlike `dashboard.json`, env vars change rarely → low friction, enforces
   one-source-of-truth).

De-staled: the dashboard plan (Phase 3 usage-map ✅), `dashboard/README.md` (`/env` row + secrets-
safety note), the ideas README (#969), and the current-state ▶ NEXT pointer (dashboard handoff).

## Verification

- `python3.10 scripts/check_quality.py --full` → **green (10138 passed, 38 skipped)**.
- `python3.10 scripts/check_architecture.py --mode strict` → **0 errors** (no `disbot/` touched).
- `python3.10 scripts/check_docs.py --strict` → green (new docs + idea files reachable/indexed).
- Scanner verified against ground truth (Q-0120): the 3 `required` vars are read without a default
  in source. fastapi/httpx not installable in this sandbox → the `/env` app smoke skips (by design,
  `importorskip`-guarded), but the route + template mirror the 5 working Phase-1 pages exactly.

**Merge ≠ deploy:** purely additive, no bot runtime changed. The `/env` page goes live only when the
owner creates the second Railway service (`dashboard/README.md`); merging does not affect the bot.

## 💡 Session idea (Q-0089)

**Turn the env-usage map into a deploy-readiness check** —
[`docs/ideas/env-map-deploy-readiness-cross-check-2026-06-16.md`](../docs/ideas/env-map-deploy-readiness-cross-check-2026-06-16.md).
The scanner now knows the *required* var set; when the Phase 3 Railway-API integration lands,
cross-reference it against the names present in the target service (names only) so `/env` shows a
**deploy-ready / N required unset** banner — catching the highest-severity config error (a forgotten
required secret) before a crash-loop, from data the scanner already produces.

## ⟲ Previous-session review (Q-0102)

Previous session: **Developer dashboard MVP (#967)** — designed the dashboard + shipped the
read-only Phase 1.
- **Did well:** a genuinely strong decoupling discipline (`dashboard/` never imports `disbot/`, web
  deps quarantined to `dashboard/requirements.txt`, app smoke `importorskip`-guarded) — that
  architecture is *why* this session's Phase 3 slice was clean and low-risk to add. And it captured
  the four owner decisions in router Q-0155 before building, so the phases were unambiguous.
- **Could have surfaced:** its own Q-0089 idea (the shared `docs_ledger` parsing helper) was recorded
  **only in the session log**, which sessions don't read top-to-bottom — so it was effectively
  orphaned. This session caught it and promoted it to a real idea file
  (`docs/ideas/docs-ledger-parsing-helper-2026-06-16.md`, the grooming move below). The lesson: a
  Q-0089 idea that's worth keeping belongs in `docs/ideas/` (indexed), not just the log.
- **Workflow improvement:** the dashboard is now the owner-facing surface, but several owner-facing
  rituals (idea-spotlight, morning-briefing, and now the env map) each live in their own place. The
  recurring fix is the one #967 itself named — a **shared parsing primitive** + the dashboard as the
  single render surface. Promoting the helper idea is the concrete first step toward that.

## Backlog grooming (Q-0015)

Moved the orphaned **`docs_ledger` parsing helper** idea one step down its lifecycle:
`raw`/in-session-log → **`captured`** as `docs/ideas/docs-ledger-parsing-helper-2026-06-16.md`
(+ README index entry), with a sequencing caveat (don't refactor `check_session_gate` in a session
whose own merge it gates).

## Documentation audit (Q-0104)

- `check_docs.py --strict` → green (the two new idea files + `env-vars.md` reachable and indexed;
  `env-vars.md` linked from `production-deployment.md`). `check_architecture --mode strict` → 0.
- No new owner decisions this session → no router Q-block needed (the dashboard's Q-0155 decisions
  predate it; this slice executed within them).
- `current-state.md` ▶ NEXT updated with the dashboard handoff; Recently-shipped stays merged-only,
  so #969 is left for the merge-time reconciliation (the expected lag; the routine runs the recon
  pass per Q-0124, not this scheduled dispatch). The pre-existing ledger drift (12 merged PRs not yet
  in current-state at session start; soft ratchet +1) is the reconciliation routine's job.
- No chat-only durable info outstanding — design + decisions live in the plan, the idea files, and
  this log.
