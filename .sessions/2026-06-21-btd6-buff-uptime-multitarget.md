# 2026-06-21 — BTD6 buff-uptime: rebuffBlockTime decode + multi-target uptime

> **Status:** `complete`

## Arc
Owner: "go ahead [wire rebuffBlockTime], any improvements welcome." Follow-up to #1235/#1249.
The dump's `AddBerserkerBrewToProjectileModel` carries `rebuffBlockTime` (per-target re-buff
cooldown) — decoded-available but unused. Its real significance is **multi-target** (the floor on
how soon a tower can be re-buffed → bounds how many towers one alch keeps buffed — the wiki's
"88% on two towers"). Single-target is unaffected (cadence 8s/6.4s always exceeds the 5s/4s block).

## Shipped (PR #1251)
- **Parser** — `_buff_window` now returns `rebuffBlockTime` too → emitted as `buff_rebuff_block`;
  committed `alchemist.json` overlaid (5s @ x-0-0, 4s @ x-2-x; clean, no version bump, idempotent).
- **Calc** — `buff_uptime(buff_source, target, targets=N)`: round-robin model — a given tower is
  re-buffed every `max(N × throw_cadence, rebuff_block)`; per-tower uptime = `min(1, window /
  interval)`. `targets=1` (default) is unchanged. Surfaces `rebuff_block_seconds` /
  `rebuff_interval_seconds` / `targets` + a multi-target note. `targets` clamped ≥ 1.
- **Tool** — optional `targets` param.
- **Docs** — decode-status: rebuffBlockTime now committed + the multi-target model + the honest note
  that the floor only binds under alch attack-speed buffs (Jungle Drums/Overclock).

## Verification
- `python3.10 scripts/check_quality.py --full` → **all checks passed ✓** (11355 passed).
- Real data: 4-0-0 on 5-0-0 Ninja — targets=1 → 100% (interval 8s); targets=2 → 54.2% (interval
  16s); targets=3 → 36.2% (interval 24s); permanent unaffected by targets; rebuff_block 5.0 surfaced.
- Ledger + docs `--strict` green.

## Decisions made alone
- **Round-robin model** (`max(N × cadence, rebuff_block)`) over a fuller throw-distribution sim — it
  matches the wiki's per-tower framing, is grounded in the two real numbers (cadence + rebuff_block),
  and degrades exactly to the verified single-target case at N=1. Noted in the tool/docs that it
  assumes the alch evenly serves N towers in range.
- Kept `rebuffBlockTime` wired as the interval **floor** even though it doesn't bind for a standalone
  alch (cadence > block) — so it's correct the moment an alch attack-speed buff enters the picture.

## Context delta
- The chain #1235 → #1249 → #1251 is a clean worked example of the decode loop: ship calculator →
  verify+populate from the real dump → wire the remaining decoded field + the capability it unlocks.
  Each step left the next obvious.

## ⟲ Previous-session review
#1249 (verify + populate) was excellent — it cloned the public dump, caught its own predecessor's
wrong guesses, and populated clean data. Its one small gap: it decoded `rebuffBlockTime` far enough
to *document* it ("decoded-available, not yet a calc input") but didn't emit it into the data, so the
field sat in a code comment rather than the committed JSON — a reader couldn't see it without
re-deriving. **Workflow note (applied here):** when you've already confirmed a field's value against
the dump, emit it (even if no consumer yet) rather than leaving it as prose — a committed field is
discoverable + testable; a comment is neither. (It *was* captured as the session idea, so not
orphaned — this is a "emit-don't-describe" refinement, not a miss.)

## 💡 Session idea
**Model alch attack-speed buffs in `btd6_buff_uptime`.** `rebuffBlockTime` only *binds* when the
alch throws faster than the block (Jungle Drums, Overclock, Primary Mentoring, village speed) — the
exact case the current calc can't express (it reads the static `rate`). A `throw_speed_multiplier`
input (or a known-buff enum) would let it answer "with Jungle Drums, can one 4-0-0 keep 2 towers at
100%?" — and it's where the `rebuff_block` floor finally matters. (Captured, not built.)

## 📤 Run report
- **Did:** Decoded `rebuffBlockTime` into the data + added `targets=N` multi-target uptime ·
  **Outcome:** shipped (PR #1251)
- **Shipped:** PR #1251 — `buff_rebuff_block` decode + overlay + `buff_uptime(targets=N)` + tool param
  + tests + decode-status
- **Run type:** `manual` (owner: "go ahead, improvements welcome")
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — data populated, verified
- **⚑ Self-initiated:** the multi-target `targets=N` capability is an improvement I chose on top of
  the literal `rebuffBlockTime` ask (Q-0172; owner pre-sanctioned "any improvements welcome")
- **↪ Next:** model alch attack-speed buffs (this session's 💡), else resume the current-state ▶
  ungated lane
