# 2026-06-21 — BTD6 buff-uptime: model attack-speed buffs on the Alchemist

> **Status:** `complete`

## Arc (owner-chosen via question panel)
The capstone of buff-uptime realism: when the **Alchemist itself** is sped up, its brew-throw
cadence drops, and below the per-target `rebuffBlockTime` floor (decoded #1251) it keeps MORE
towers buffed — the one scenario where that floor binds. **Under the ~2-PR estimate:** the speed
multipliers are already in committed data, so no decode pass — one clean calc PR.

## Shipped (PR #1268)
- `buff_uptime(buff_source, target, targets=1, alch_speed=None)` — `alch_speed` resolves
  **grounded** to a cooldown multiplier: a Power's `rate_scale` (Monkey Boost ×0.5), else an
  upgrade's attack-speed `rateMultiplier` (Jungle Drums = Village 2-0-0 ×0.85, Overclock ×0.25)
  via `resolve_upgrade` → the tier's rate buff. `effective_cadence = cadence × mult`;
  `rebuff_interval = max(targets × effective_cadence, rebuff_block)`. Surfaces
  `alch_speed_source/multiplier`, `effective_throw_cadence_seconds`, `rebuff_floor_binds`.
  Unknown / non-speed source → honest `found=False`.
- `btd6_buff_uptime` tool: optional `alch_speed` param.
- Tests (Monkey Boost + Jungle Drums real-data, floor-binds, multi-target improvement, unknown
  source) + decode-status note.

## Verification
- `python3.10 scripts/check_quality.py --full` → all checks passed (11412 passed).
- Real data: 4-0-0 → 5-0-0 Ninja, 2 targets — unboosted 54.2%; **Monkey Boost 100%** (×0.5 throw,
  5s floor binds at N=1); Jungle Drums 63.8%. Unknown source → found=False. Ledger + docs green.

## Decisions made alone
- **Two grounded resolution paths** (Power `rate_scale`, upgrade `rateMultiplier<1`) rather than a
  raw numeric multiplier param — keeps it fabrication-free (the AI names a buff; the number comes
  from data). Unknown source fails closed with the supported kinds named.

## Context delta
- Mid-build I corrected a wrong assumption: **Jungle Drums is Monkey Village 2-0-0, not a Druid
  buff** — and its ×0.85 aura was already in committed data on every top-path-≥2 tier. So the
  feared "~2 PRs incl. a decode pass" collapsed to one calc PR. (Lesson: verify the buff's
  tower/tier via `resolve_upgrade` before assuming a decode gap.)

## ⟲ Previous-session review
#1263 (seed-data changed-file report) was a clean, correctly-scoped small PR — and notably it was
the FIRST in this BTD6 chain that *didn't* spawn a follow-up "one more consumer" PR, because the
content_drift consumers were finally exhausted. This alch_speed PR applied the #1263 review's own
lesson: it shipped the whole feature (resolver + tool param + both real-data + edge tests) in one
pass instead of dribbling consumers across PRs. Workflow holding well; nothing to fix.

## 💡 Session idea
**Symmetric feature — speed buffs on the TARGET.** A sped-up *buffed tower* (e.g. a Monkey-Boosted
Ninja) attacks faster → burns the alch buff's attack-cap SOONER → LOWER uptime (the inverse of
this PR). `buff_uptime(..., target_speed=…)` would reuse the exact same grounded resolver
(`_alch_speed_multiplier`) applied to `tgt_cd` instead of the cadence. Small, symmetric, grounded.
(Captured, not built.)

## 📤 Run report
- **Did:** Modeled attack-speed buffs on the alch in buff_uptime (alch_speed) · **Outcome:** shipped (PR #1268)
- **Shipped:** PR #1268 — `alch_speed` resolver + tool param + tests + decode-status
- **Run type:** `manual` (owner-chosen via question panel)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** still the one-time `!btd6ops seed-data` for the buff window data
  (unchanged; this PR adds no new data).
- **⚑ Self-initiated:** no — owner-directed (the AskUserQuestion pick). Came in under the
  estimate (1 PR, no decode needed).
- **↪ Next:** the symmetric target-speed idea (this 💡), or a fresh lane — BTD6 buff-uptime is now
  comprehensively complete (calc · data · multi-target · auto-seed · drift warning · seed receipt ·
  alch-speed).
