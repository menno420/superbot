# 2026-07-10 — EAP docs: two verified factual corrections (from fleet-manager ultracode verification)

> **Status:** `in-progress`

- **📊 Model:** claude-fable-5 · worker session (coordinator-dispatched)

## About to do

Apply two one-line corrections sourced from fleet-manager's
`docs/findings/ultracode-verification-2026-07-10.md`, each independently re-verified
against live repo data before editing:

1. `docs/eap/gen1-grand-review-2026-07-09.md` (PR #1911) — "Parity rows exist for each
   in `parity/parity.yml`" is false for 2 of the 8 missing subsystems: **starboard and
   paragon have no rows** (re-verified against `superbot-next/parity/parity.yml` at HEAD).
2. `docs/eap/fleet-winddown-audit-2026-07-09.md` (PR #1913) — sonnet5 was **not** the
   "only lane to ship an actual shell script": five other lanes shipped real setup
   scripts (re-verified: opus4.8 `environments/setup.sh`, websites `scripts/setup-env.sh`,
   trading-strategy + fable5 `environments/setup-universal.sh`, superbot-games
   `environment/setup-exploration.sh` — all present at HEAD).

Docs-only; each corrected sentence gets a dated correction note citing the source.
