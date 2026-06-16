# 2026-06-16 — TPM result confirmed (5-mini 500K) + reconcile the compaction guidance

> **Status:** `complete` — follow-up to the merged #978 (same session), shipped as #980. Docs-only.
> Session enders (Q-0089 idea, Q-0102 review, Q-0104 audit) were satisfied in this session's first
> card (`2026-06-16-model-comparison-gpt5mini.md`, merged in #978) — not repeated here.

## What I'm about to do

The owner pulled their OpenAI **Project → Rate limits** page and it confirmed the empirical answer +
gave a config directive. Capturing both durably (I promised "I'll add the result to the doc"):

- **Confirmed:** `gpt-5-mini` = **500K TPM** vs `gpt-5.4-mini` = **200K TPM** on the same account
  (dated 5.4 snapshot also 200K; `gpt-4o-mini` 200K; org Default 250K; all 500 RPM). It's case (b) —
  the 200K is a per-model throttle on the newer 5.4-mini, not an org ceiling. Switching to 5-mini =
  2.5× headroom → the chosen fix.
- **Owner directive:** **leave compaction at default** — do NOT lower `compression.threshold`. With
  500K headroom it isn't needed, and lowering it interrupts tasks mid-flow (prunes context the turn
  still needs). The bot "can just do its tasks normally without interruption."

## Edits

- `docs/operations/hermes-control-plane.md` — table row → confirmed per-account caps; replaced the
  "either/or decisive test" with the ✅ confirmed result + the durable lesson (published per-tier
  tables are uniform — only the project/org Limits page shows an account's real per-model cap) + the
  decision (switch to 5-mini; compaction stays default, owner-declined).
- `docs/operations/hermes-session-reset.md` — the #976 "compaction is the primary lever" framing is
  superseded for this account: added a ✅ RESOLVED note (model-cap is the fix; compaction declined),
  demoted the compaction bullet to "only when you can't switch to a higher-cap model," and reset the
  order-of-preference (model swap → /new → compaction-if-no-alternative).
