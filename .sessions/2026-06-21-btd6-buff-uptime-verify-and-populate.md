# 2026-06-21 — BTD6 buff-uptime: verify binding against the real dump + populate data

> **Status:** `in-progress`

## Arc (what I'm about to do)
Follow-up to PR #1235 (Alchemist buff-uptime calculator). That PR shipped the parser
buff-window decode as an **unverified candidate field-set** (no dump in-repo) and left
data population as an owner manual step. The owner pointed out the dump is the **public
BTD Mod Helper repo** — clonable. So I cloned it and:

- **Found my candidate set was WRONG** (would've extracted nothing). The real applier is
  `Add{BerserkerBrew,AcidicMixture}ToProjectileModel` on the thrown projectile:
  `lifespan` (SECONDS, not frames), nested `…CheckModel.maxCount`, `rebuffBlockTime`.
- **Rewrote `_buff_window`** to the verified structure; dry-run matches the wiki exactly
  (300=5s/25, 320=6s/40, 400=12s/40, 420=13s/55, 500=permanent; lead-buff cap 10/12).
- **Populated the committed data** via a surgical overlay (buff fields only, zero value
  churn / no version bump) → the bot now answers live: 4-0-0 on 5-0-0 Ninja = attack-cap
  limited, 100% uptime; base 3-0-0 = 62.5% (time-limited); Acidic Dip = 21.7%.

## Plan
1. Parser: verified `_buff_window` (done locally) + update the 4 fixture tests to the real
   `AddBerserkerBrewToProjectileModel` shape.
2. Data: committed `alchemist.json` overlay (done locally).
3. Calc: tiny note polish (dedupe "X (X)" when source name == buff label) + a real-data test.
4. Docs: decode-status → VERIFIED + populated; drop the owner manual-step caveat.
