# Session — Hermes follow-up: SOUL size guard + sharpen the context diagnosis

> **Status:** `in-progress` — born-red per Q-0133. Continuation after #913 merged. The owner
> added a key data point: even ~5-message, clearly-directed sessions still fail. That sharpens
> (not contradicts) the diagnosis — it points at per-turn **doc volume**, not message count.

## What I'm about to do
- **`scripts/hermes/apply_context_fixes.sh` (NEW — the owner asked for a script, not steps).** A
  safe, idempotent, reversible VPS operator script: backs up `config.yaml`, raises
  `compression.threshold` 0.50→0.75 and `compression.protect_last_n` 20→30 via the validated
  `hermes config set` CLI, attempts `prompt_caching.cache_ttl 1h`, re-installs the sync-fixed
  SOUL.md, runs `hermes config check`, reminds to restart the gateway. `--dry-run` works with no
  Hermes installed (testable here). Provenance + kill-switch header (Q-0105). NOTE: the
  `hermes config set` calls can't be exercised on this container (no Hermes) — only dry-run is.
- `scripts/hermes/install-soul.sh` — add a SOUL.md size guard (the #913 Q-0089 idea). Operating
  prompt is 6478 bytes — ~81% of Hermes' likely ~8KB ceiling. Warn >budget, info >80%, override
  via `HERMES_SOUL_BUDGET`.
- `docs/operations/hermes-token-efficiency-investigation-2026-06-15.md` — add the owner's
  5-message data point: a single large whole-file doc read can cross the 50% compaction line in
  ONE turn, so compaction then prunes the doc Hermes just read. New levers: raise
  `compression.threshold`, use a larger-context model, read doc SECTIONS (grep) not whole files;
  point at the new script.
