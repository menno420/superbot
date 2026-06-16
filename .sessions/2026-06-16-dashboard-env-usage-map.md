# Session — Dashboard Phase 3 (read-only env-var usage map)

> **Status:** `in-progress`

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

## Verification (to fill at close)

- `python3.10 scripts/check_quality.py --full`
- `python3.10 scripts/check_architecture.py --mode strict`
- `python3.10 scripts/check_docs.py --strict`
