# 2026-06-21 — BTD6 buff-uptime: rebuffBlockTime decode + multi-target uptime

> **Status:** `in-progress`

## Arc (what I'm about to do)
Owner: "go ahead [wire rebuffBlockTime], any improvements welcome." Follow-up to #1235/#1249.

The dump's `AddBerserkerBrewToProjectileModel` carries `rebuffBlockTime` (the per-target
re-buff cooldown: 5s @ 4-0-0, 4s with Perishing) — decoded-available but unused. Its real
significance is **multi-target**: it's the floor on how soon a given tower can be re-buffed,
which is what bounds "how many towers can one alch keep buffed" (the wiki's "88% on two
towers" framing). Single-target is unaffected (throw cadence 8s/6.4s always exceeds the 5s/4s
block), so the meaningful improvement is the multi-target case that rebuffBlockTime enables.

## Plan
1. Parser: emit `buff_rebuff_block` (seconds) from `rebuffBlockTime`; re-overlay committed
   `alchemist.json` (add the field; keep existing buff fields).
2. Calc: `buff_uptime(..., targets=N)` — round-robin model: a tower is re-buffed every
   `max(N × throw_cadence, rebuff_block)`; per-tower uptime = `min(1, window / interval)`.
   N=1 default = unchanged. Surface `rebuff_block_seconds` + multi-target note.
3. Tool: optional `targets` param.
4. Tests (parser fixture + real-data multi-target) + decode-status doc.
