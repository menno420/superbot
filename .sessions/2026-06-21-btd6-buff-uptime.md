# 2026-06-21 — BTD6 Alchemist buff-uptime calculator + game-data decode

> **Status:** `in-progress`

## Arc (what I'm about to do)
Owner live-test (Discord screenshot): asked the bot for the buff **uptime** of a
4-0-0 Alchemist on a 5-0-0 Ninja. The bot punted — it had the brew **throw cooldown**
(8s) but said the buff **duration** "isn't grounded in the data." Investigation
confirms: the buff *throw cadence* (`BeserkerBrewAttack.rate`) and the *target's
attack speed* (`attacks[0].rate`) **are** in the committed data, but the buff's **time
duration + attack-count cap are NOT** — the brew is a *projectile-applied* buff, so the
top-level `_buffs()` walker never captures it, and the parser only decodes buff
*magnitudes*, not lifespan/cap.

Verified the real values from the canonical Bloons wikis (cross-check, game-data leads):
Berserker Brew 3-0-0 = **5s OR 25 attacks**; 3-2-0 = 6s/40; **Stronger Stimulant 4-0-0 =
12s OR 40 attacks**; 4-2-0 = 13s/55; Acidic Mixture Dip 2-0-0 = **10 shots** (12 @ 2-2-0).
The buff is **dual-limited** (time OR attacks, whichever first) — exactly the owner's
model. A 5-0-0 Ninja (0.217s) burns 40 attacks in ~8.7s < 12s → **attack-cap-limited**.

Owner chose (this session) the **game-data-only / parser** path for sourcing the
duration/cap (not a curated table): extract them from the dump so values are game-sourced.

## Plan
1. Parser (`parse_gamedata.py`): decode a buff-applying attack's **duration** (frames→s)
   + **attack-cap** onto the attack node (the brew/lead-buff lives on the projectile).
2. Calculator: `btd6_upgrade_detail_service.buff_uptime()` — cadence + duration + cap +
   target attack-speed → which limiter binds + uptime %. Honest `found=False` until decoded.
3. AI tool `btd6_buff_uptime` (spec + handler + registry + catalogue) — mirrors
   `btd6_power_effect`.
4. Tests (calculator math incl. the 4-0-0 Ninja case; parser fixture; tool parity).
5. Docs: decode-status / dictionary / native-schema / current-state ledger + session enders.

## Status / open step
Parser field-name **binding** to the live dump is the one step I can't run here (raw dump
not vendored) — fixture-tested against the verified shape; confirm on next `--all`.
