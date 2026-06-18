# 2026-06-16 — capture the Hermes TPM rate-limit finding (docs/script corrections)

> **Status:** `complete` — docs/script-only corrections from a live debugging incident; one push.

## Arc

While helping the owner re-install the lean skills on the VPS, the real reason both scheduled skills
"hit rate limits" surfaced in the gateway logs — and it's **not** what the existing docs assume.
Captured the findings durably so the next agent/owner doesn't repeat the wrong-direction mistake.

## The finding (from live `journalctl`)

- Failure is **TPM — tokens *per minute*** (`Rate limit reached for gpt-5.4-mini … on tokens per min
  (TPM): Limit 200000, Used …, Requested ~100k`), **not** the context window. The interactive session
  had grown to **79 msgs / ~110K tokens**; the model window is 400K (fits fine), but the OpenAI org
  TPM cap is **200K/min**, so every ~100K-token reply lets only ~2 calls/min through. A `bg-review`
  background thread firing concurrent ~100K calls compounds it. The bot looked "down" but was
  `active (running)` — it was starved, not crashed.
- **No first-class CLI resets the live gateway conversation** — verified `hermes gateway --help`
  (lifecycle only; restart KEEPS state) + `hermes sessions --help` (store mgmt; the bloated session
  is the *newest* so `prune` won't touch it). The only clean live reset is **`/new`** in Telegram.
- **Compaction is the primary durable fix, not a 6h hard-reset:** lower `compression.threshold`
  (0.50 → 0.25) so the gateway keeps each call small *continuously*. This is the **opposite** of
  `apply_context_fixes.sh` (which raises it for the doc-pruning problem) — running that for a TPM
  limit makes it worse.

## Shipped (this PR — docs/scripts only)

- `docs/operations/hermes-session-reset.md` — added "⚠️ Root cause clarification (2026-06-16)": the
  TPM-vs-window distinction, the verified no-clean-CLI-reset reality, compaction as the primary lever,
  `/new` as the immediate unstick; corrected the "one knob" section's bogus `hermes session new`
  candidates.
- `scripts/hermes/apply_context_fixes.sh` — prominent "DO NOT run for a TPM rate-limit (it raises the
  threshold = wrong direction)" warning.
- `docs/operations/hermes-token-efficiency-investigation-2026-06-15.md` — a "2026-06-16 follow-up"
  section separating this TPM failure from the 2026-06-15 context-window one (opposite fix direction).
- `scripts/hermes/session_reset.sh` — header now states the no-clean-CLI-reset reality + points at
  compaction as the preferred lever.

`bash -n` on both scripts ✓, `session_reset.sh` dry-run ✓, `check_docs --strict` ✓.

## Context delta

- **Discovered by hand (the load-bearing lesson):** a 400K context **window** and a 200K-tokens-per
  **minute** rate limit are different ceilings; a model that can *hold* a big conversation can still
  be unable to *send* it under the per-minute budget. The repo's prior context docs only addressed the
  window; this adds the TPM axis.
- **Decision made alone:** landed the *certain* corrections now (CLI reality, wrong-direction warning,
  TPM distinction) rather than waiting on the owner's live confirmation of the exact threshold value —
  those facts hold regardless of how 0.25 tunes. The specific value is left as "tune + verify".
- **Flagged for maintainer:** the exact best `compression.threshold` and whether the OpenAI TPM tier
  needs raising are still pending the owner's live confirmation on the VPS; the bg-review concurrency
  is an unquantified secondary load.

## 📤 Run report

- **Did:** captured the TPM rate-limit root cause + corrected the misleading reset/compaction docs ·
  **Outcome:** shipped (docs/scripts only)
- **Shipped:** this PR — session-reset runbook clarification + apply_context_fixes warning +
  investigation-doc follow-up + session_reset header
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps (VPS, the actual fix):** `/new` in Telegram (immediate); `hermes config set
  compression.threshold 0.25` + `sudo systemctl restart hermes-gateway` (durable); optionally raise
  the OpenAI TPM tier / throttle `bg-review`. Do **not** run `apply_context_fixes.sh` for this.
- **↪ Next:** owner confirms the compaction change holds; if so the skills + bot run clean.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 5 (#959, #965, #966, #968, #971; this one auto-merges on green) |
| CI-red rounds | 0 (docs/scripts only; verified locally) |
| Repo-rule trips | 0 |
| New ideas contributed | 0 this follow-up (1 already this session — verdict loop) |
| Ideas groomed | 0 this follow-up |
