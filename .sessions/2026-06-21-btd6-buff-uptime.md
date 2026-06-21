# 2026-06-21 — BTD6 Alchemist buff-uptime calculator + game-data decode

> **Status:** `complete`

## Arc
Owner live-test (Discord screenshot): asked the bot for the buff **uptime** of a
4-0-0 Alchemist on a 5-0-0 Ninja. The bot punted — it had the brew **throw cadence**
(8s) but said the buff **duration** "isn't grounded in the data." Task: find out if
the data has it, then make the bot able to compute uptime (time + attacks + the alch's
own attack speed). Owner chose (this session) the **game-data-only / parser** sourcing
path for the missing values, not a curated table.

## Investigation result (the owner's hypothesis was right)
Two of the three uptime inputs **were** already in the committed data; one was not:
- ✅ Alch **throw cadence** — `stats/alchemist.json` `BeserkerBrewAttack.rate` (8s @ 4-0-0,
  6.4s with Faster Throwing x-0-1/2); `AcidicMixture.rate` for the lead buff.
- ✅ Target **attack speed** — every tier's `attacks[0].rate` (Ninja 5-0-0 = 0.217s).
- ❌ Buff **time-duration + attack-cap** — *not* in the data. The brew is a
  **projectile-applied** buff (inside `BeserkerBrewAttack`'s projectile), so the top-level
  `_buffs()` support-model walker never captured it (Alchemist has zero committed buffs),
  and the parser only decoded buff *magnitudes*.

The buff is **dual-limited** (time OR attacks, whichever first) — exactly the owner's
model. Verified windows (Bloons-wiki cross-check): Berserker Brew 3-0-0 = **5s/25**, 3-2-0
= 6s/40, **Stronger Stimulant 4-0-0 = 12s/40**, 4-2-0 = 13s/55, Acidic Mixture Dip 2-0-0
= 10 shots (12 @ 2-2-0). A 5-0-0 Ninja (0.217s) burns 40 attacks in ~8.7s **before** the
12s timer → **attack-cap-limited**, ~100% uptime (re-thrown every 8s).

## Shipped
- **Calculator** `btd6_upgrade_detail_service.buff_uptime(buff_source, target)` — joins
  cadence + duration + attack-cap + the target's attack speed → which limiter binds + the
  effective window + attacks-buffed + uptime%. Honest `found=False` when the window isn't
  decoded yet (says the cadence + target speed it *does* know) or the target has no attack.
- **AI tool** `btd6_buff_uptime` (spec + handler + registry + catalogue), mirrors
  `btd6_power_effect`. Eval case `tool.btd6_buff_uptime` (owner's exact question);
  coverage floor 34 → 35.
- **Parser** `parse_gamedata._buff_window()` — for `BeserkerBrewAttack` / `AcidicMixture`
  decodes the buff **duration** (frame fields ÷60) + **attack-cap** off the projectile's
  behaviors, **excluding** the `Travel*Model` flight-time `lifespan` (the 0.6s false
  positive); emits `buff_duration` / `buff_attack_cap` / `buff_permanent`.
- **Docs** — `btd6-gamedata-decode-status.md` ▶ "Next session" entry: the decode gap, the
  verified windows (the `--audit` target), and the one open binding step.

## Verification
- `python3.10 scripts/check_quality.py --full` → **all checks passed ✓** (11296 passed).
- New tests: calculator (attack- vs time-limited, permanent, honest-undecoded, non-alch +
  economy-target rejection, no-buff tier); parser window decode (frames/seconds/permanent/
  scoped, travel-lifespan exclusion); tool parity (74) + eval coverage (12).
- Manual: `buff_uptime("alchemist 4-0-0","ninja 5-0-0")` (with the window injected as the
  parser will emit) → `limiter=attacks`, window 8.68s, 40 attacks, 100% uptime — the
  owner's exact case.

## Decisions made alone
- Calculator assumes the alch re-buffs **this** target each throw cycle (per-tower uptime);
  noted the multi-target split as the Q-0089 idea, not built (keeps the PR focused).
- Scoped the buff-window decode to the two **named** buff-throwing attacks rather than a
  generic projectile scan — avoids false positives across the roster, and is the honest
  surface for the one buff family the owner asked about.

## Context delta
- **Discovered by hand:** the Alchemist's Berserker Brew / Acidic Mixture Dip buff is
  **projectile-applied**, so `_buffs()` (top-level support-model walker only) structurally
  cannot see it — this is *why* the Alchemist has zero committed buffs. Now recorded in
  decode-status; worth keeping in mind for any other projectile-applied buff (e.g. MIB).
- **Needed but not pointed to:** there is no raw NK dump in-repo and no buff-applying
  projectile fixture, so the exact dump field names for the buff window can't be verified
  here — the binding is a documented next-dump-run step (Q-0105 candidate set).

## ⚠️ OPEN — owner manual step (one binding step)
The buff window won't appear in the committed data until the game-data parse is re-run
against a live dump: `parse_gamedata.py --dump <clone> --tower alchemist --dry-run`, confirm
`buff_duration` / `buff_attack_cap` appear, `--audit` them against the verified windows
above, then `--all`. If a candidate field name never matches, read the real one off the
dry-run and swap it in (delete the dead candidates). Until then `btd6_buff_uptime` honestly
returns `found=false` with the cadence + target speed.

## ⟲ Previous-session review
The previous session (`2026-06-21-permission-overlap-guard.md`) was strong: it caught a
*residual* bug in its own predecessor (#1211's `git push --force*` ask shadowing
`--force-with-lease`) and shipped a guard for the whole class — exactly the
root-cause-over-symptom bar. One thing it left implicit: its guard is advisory-only and the
decision to wire it into `code-quality.yml` was deferred to the owner without a router
Q-block, so that follow-up has no durable home and will likely be forgotten. **Workflow
improvement it surfaces (and that this session honored):** when a session defers a
"should-we-enforce-this" decision, route it to the question router immediately rather than
leaving it as prose in a session log — otherwise advisory guards accrete with no path to
becoming load-bearing. (My own advisory-vs-enforced call here — the parser candidate-set
binding — is instead captured as a concrete owner manual step with the exact commands.)

## 💡 Session idea
**Generalize buff-uptime to multi-target + other buffers.** The wiki frames alch uptime as
e.g. "176% = 88% on two towers" — the alch splits throws across towers in range, so
single-target uptime overstates it. A follow-up: `buff_uptime(..., targets=N)` that divides
throw cadence across N buffed towers, and extends the same dual-limit engine to other
buffers (Overclock/Engineer, Ezili/MIB debuffs, Village). The calculator + the
`limiter`-binds logic shipped here is the reusable core. (Captured, not built — keeps this
PR scoped; good next grooming pick.)

## 📤 Run report
- **Did:** Investigated + shipped the Alchemist buff-uptime calculator (`btd6_buff_uptime`)
  + the game-data buff-window decode · **Outcome:** shipped (PR #1235, auto-merge on green)
- **Shipped:** PR #1235 — `buff_uptime()` + tool + parser `_buff_window()` + tests + eval
  case + decode-status doc
- **Run type:** `manual` (owner live-test driven)
- **⚑ Owner decisions needed:** none (the sourcing fork was answered in-session → parser path)
- **⚑ Owner manual steps:** re-run `parse_gamedata.py` against a live dump to populate +
  confirm the buff-window field binding (see ⚠️ OPEN above) — until then the tool returns
  `found=false`
- **⚑ Self-initiated:** none — owner-directed (live-test request)
- **↪ Next:** the multi-target buff-uptime generalization (this session's 💡), or resume the
  current-state ▶ ungated lane (botsite React-SPA migration / creature-PvP leaderboards)
