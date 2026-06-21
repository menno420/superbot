# 2026-06-21 — BTD6 buff-uptime: verify binding against the real dump + populate data

> **Status:** `complete`

## Arc
Follow-up to PR #1235 (Alchemist buff-uptime calculator). #1235 shipped the parser
buff-window decode as an **unverified candidate field-set** (I'd wrongly concluded "no
dump in-repo ⇒ can't verify") and left data population as an owner manual step. The owner
corrected me: the dump is the **public BTD Mod Helper repo**, clonable. So I cloned it and
turned the guess into a verified, populated, working feature.

## Shipped (PR #1249)
- **Verified the real structure** — `git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data`.
  My #1235 candidate field-set was **wrong** (would've extracted nothing). The real buff
  applier is `Add{BerserkerBrew,AcidicMixture}ToProjectileModel` on the thrown projectile:
  `lifespan` (**seconds**; `lifespanFrames` is 0/unused; `-1` = permanent; absent on the
  lead buff = cap-only), nested `…CheckModel.maxCount` (cap; `9999999` = permanent),
  `rebuffBlockTime` (per-target re-buff cd, 5s @ 4-0-0).
- **Rewrote `parse_gamedata._buff_window`** to that structure. Dry-run against the real dump
  matches the wiki exactly across every tier + crosspath (300=5s/25, 320=6s/40, 400=12s/40,
  402=12s/40@6.4, 420=13s/55, 500=permanent; lead cap 10/12).
- **Populated `stats/alchemist.json`** via a surgical buff-field overlay — `buff_duration` /
  `buff_attack_cap` / `buff_permanent` only, **zero value churn / no version bump**, idempotent
  with the parser (next `--all` reproduces it). The bot now answers **live**: 4-0-0 on 5-0-0
  Ninja = attack-cap-limited 100%; 3-0-0 = 62.5% (time-limited); Acidic Dip = 21.7%.
- **Calc polish** (dedupe "Berserker Brew (Berserker Brew)" → just the name when the upgrade
  IS the buff); **fixture tests** rewritten to the real `Add…ToProjectileModel` shape;
  **real-data calculator tests** (no monkeypatch); decode-status marked VERIFIED + populated,
  manual-step caveat dropped.

## Verification
- `python3.10 scripts/check_quality.py --full` → **all checks passed ✓** (11349 passed).
- Dry-run `map_tower(/tmp/btd6gd, alchemist)` → buff windows match the wiki on every tier.
- Real-data: `buff_uptime("alchemist 4-0-0","ninja 5-0-0")` → found, `limiter=attacks`,
  `buff_duration_seconds=12.0`, `buff_attack_cap=40`, `uptime_percent=100.0`.
- Ledger + docs `--strict` green.

## Decisions made alone
- **Surgical overlay over `--all` regen**: the cloned dump HEAD is a newer/undetected version
  (`game_version` came out `""`, `filterInvisible` churn), so a full `--tower`/`--all` regen
  would be a version bump, not a buff-field add. Overlaying only the three buff fields keeps the
  diff clean and consistent with the parser. The owner's canonical `--all` at the pinned dump
  still reproduces the same fields.
- Left `rebuffBlockTime` decoded-but-unused (captured as the session idea) to keep the calc
  change minimal; the throw-cadence model already gives correct single-target uptime.

## Context delta
- **Corrected belief:** "not vendored in our repo" ≠ "unreachable." The BTD Mod Helper dump is
  public + clonable; the decode-status doc *named the repo* — I should have cloned it in #1235
  instead of shipping a candidate set. Now stated loudly in decode-status ("no 'no dump in-repo'
  excuse — clone it").

## ⟲ Previous-session review
The previous session (this task's #1235) shipped a genuinely useful calculator and was honest
about the gap — but it **built ahead of verifiable data and guessed the field names** rather than
checking whether the dump was obtainable, even though its own decode-status entry named the public
repo. The candidate set was 100% wrong (it would have extracted nothing), so the "fixture-tested
logic" gave false confidence. **Workflow improvement (applied this session):** before shipping an
*unverified* decode against an external source, spend one step checking if that source is
fetchable (public clone / raw URL) — a 30-second `git clone` converts a guess into ground truth.
"No raw data in our repo" is a prompt to *go get it*, not a license to guess. Worth a
`.session-journal.md` line.

## 💡 Session idea
**Make `rebuffBlockTime` a `btd6_buff_uptime` input.** The dump carries a per-target re-buff
cooldown (5s @ 4-0-0, 4s with Perishing) distinct from the throw cadence — the *real* floor on how
soon a given tower can be re-buffed. Decoding + feeding it would sharpen single-target uptime
(and is the natural companion to the multi-target generalization #1235 flagged). The value is
already decoded-available off the applier; only the calc wiring + an emitted `buff_rebuff_block`
field remain. (Captured, not built — kept this PR to the verified binding + population.)

## 📤 Run report
- **Did:** Cloned the public dump, corrected the parser binding to verified, populated the
  Alchemist buff data so `btd6_buff_uptime` answers live · **Outcome:** shipped (PR #1249)
- **Shipped:** PR #1249 — verified `_buff_window` + `stats/alchemist.json` overlay + calc polish
  + real-data tests + decode-status VERIFIED
- **Run type:** `manual` (owner pointed at the public dump)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** **none** — the previous manual-step (re-run the dump) is now done;
  data is populated and the binding is verified. (Future game patches: the normal `--all` refresh
  reproduces the buff fields automatically.)
- **⚑ Self-initiated:** this whole follow-up was self-initiated (Q-0172) off the owner's "you can
  clone it" pointer — verifying + populating beyond the merged #1235.
- **↪ Next:** wire `rebuffBlockTime` into the calc (this session's 💡) and/or the multi-target
  generalization; else resume the current-state ▶ ungated lane.
