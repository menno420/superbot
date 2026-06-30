# 2026-06-30 — Welcome multiple/random greeting messages (S1 completion deepening)

> **Status:** `in-progress` — born-red session card (Q-0133). Run type: `routine · dispatch`.

**Branch:** `claude/funny-franklin-7y6goi`.

## What I'm about to do (intentions)

Dispatch run, no specific work order → advance the next S1 completion-first slice. Picked the
**Welcome** unit's punch-list **#2** (best-in-class options): ship **multiple / random welcome
messages** (Carl-bot / MEE6 / Dyno parity) — a discrete, additive, migration-free deepening.

An operator can now define several greeting (and farewell) variants separated by a `---` line; the
bot picks one at random per join/leave. Single-message config stays **byte-identical** (one variant =
that message). No migration (the welcome settings are scalar KV values). Updates the validator to
cap per-variant length + variant count, the cog status preview to show the variant count, and the
welcome completion cert to mark #2 partially cleared.
