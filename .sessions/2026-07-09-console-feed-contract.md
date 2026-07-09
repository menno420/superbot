# Session 2026-07-09 — console.json shape contract (superbot half)

> **Status:** `in-progress` — pinning the console.json feed shape shared with
> the websites repo's dashboard consumer (the #1883 session idea, executed).

## What I'm about to do

Execute the `💡 Session idea` from `.sessions/2026-07-09-kl6-console-telemetry.md`
(PR #1883): a **versioned shape contract for `botsite/data/console.json`** so the
two consumers of the committed feed (superbot's own botsite console + the
websites repo's dashboard `/console` page, which reads it over raw GitHub) stop
sharing an *implicit* schema. Plan:

- `botsite/data/console_data_contract.json` — the committed, versioned contract
  (same pattern as the existing `site_data_contract.json`), the single source of
  truth both repos cite.
- Exporter: `console.json` gains `meta.schema_version`; producer constants must
  match the contract file.
- `check_dashboard_data.py` gains a `check_console_subset` guard (`--console`)
  mirroring `check_site_subset`, enforced in CI by tests over the committed file.
- Companion websites PR pins the contract copy + validates at render time.
