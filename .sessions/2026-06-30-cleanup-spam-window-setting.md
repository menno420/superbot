# 2026-06-30 — Cleanup spam-window per-guild setting (completion-first deepening)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What this run is about to do
Empty-fire dispatch advancing the S1 completion-first arc (Q-0209). Closing **Cleanup completion
cert punch #4** — surface the hardcoded `!cleanuphistory` spam-duplicate window
(`SPAM_DUPLICATE_WINDOW_SECONDS = 15`) as a **real per-guild scalar setting with a config-input
widget** (the `numeric_presets` Settings widget, mirroring automod's `spam_window_seconds`), read at
command time via `settings_resolution.resolve_value`. Default-off / byte-identical (default stays 15),
no migration (scalar KV). Then groom one more turn-key completion-first slice if budget allows.
