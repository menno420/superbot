# 2026-06-24 — BTD6 paragon elite-boss damage multiplier

> **Status:** `complete` — owner-directed (Discord); owner confirmed ship after the
> verification (he wanted to be sure the ×2 is a *global* paragon bonus, not per-
> paragon — it is). PR #1402; auto-merge armed; merges on green.

> **Run type:** `manual · owner-directed`

Owner-reported gap (Discord): the bot can't answer about the **elite boss damage
multiplier** for paragons. Owner showed JonnyBoy/hemi's bot displaying `ed: elite
boss dmg` = `×2` the boss damage (`326 = 2×163`).

## What I'm about to do
- **Verified** (this session): the ×2 elite factor is **NOT in the dump** — checked
  the Dart *and* Ice Monkey paragon models (only Boss/Ceramic/Moabs damage tags, all
  multiplier 1.0) and `paragonDegreeData.json` (one boss field, no elite). It's a
  **universal runtime constant**: per the Fandom *Extra Damage to Boss* / *Paragons*
  pages, **paragons deal 2× their bonus boss damage to Elite Bosses**, paragon-category
  only, at **all degrees including degree 1**. (Same shape as the freeplay/cash
  runtime constants — curate it, the dump doesn't have it.)
- Add `ELITE_BOSS_DAMAGE_MULTIPLIER = 2.0` + `elite_boss_multiplier(degree)` (=
  `boss_multiplier(degree) × 2`) to `paragon_degrees.py`, surface it in the paragon
  degree embed and the `[btd6_paragon_stats]` grounding so the bot answers it, with
  tests pinning the anchors (deg 35 → ×2.5, deg 100 → ×4.5; ×2 vs normal boss).

## Verification update
Owner challenged whether the ×2 is **constant** across degrees or assumed from the
one (deg-35) screenshot. **Resolved:** a *second* independent search of the Fandom
*Extra Damage to Boss* / *Paragons* pages states it explicitly — *"Elite Bosses take
double damage from Paragons. This is a **flat bonus that applies to all Paragon
degrees**"* and *"applies from the very first degree."* So constant ×2 is confirmed by
two independent community sources + the screenshot — not an extrapolation. (It hits
the **total** boss damage, matching JonnyBoy `ed = 2× bd`, not just the bonus.) Full
CI mirror green (12,280 passed); the only red is the born-red gate. **Holding the
final flip for the owner's nod** since this point was explicitly contested.

**Owner nod (resolved):** *"you can ship it, I just wanted to be sure it was a global
bonus and not something different per paragon."* It IS global — verified no per-paragon
elite field in the dump (Dart + Ice models) and the wiki says it applies to the whole
Paragons *category*. One global constant, applied to every paragon. Shipping.

## Shipped (PR #1402)
- `paragon_degrees.py` — `ELITE_BOSS_DAMAGE_MULTIPLIER = 2.0` (provenance-noted) +
  `elite_boss_multiplier(degree)` (= boss×2) + `DegreeRow.elite_boss_multiplier`.
- `stats_embed.py` — paragon degree embed shows the elite-boss multiplier.
- `btd6_context_service.py` — `[btd6_paragon_stats]` grounding carries it + the
  "2× vs Elite Bosses, all degrees, paragon-only" rule, so the model answers it.
- Tests pin `elite = boss×2` at every degree (deg1 ×2, deg35 ×2.5, deg100 ×4.5).
- `btd6-gamedata-dictionary.md` — added to the "Runtime-formula facts the dump does
  NOT store" registry. Full mirror green (12,280 passed).

## 💡 Session idea (Q-0089)
We now have **both** paragon elite-boss damage (×2) *and* elite boss HP (`elite_tiers`).
A natural high-value floor: a **"paragon vs elite boss" effectiveness** answer — combine
the two so the bot can field "how much does <paragon> deal to an Elite <boss>, and roughly
how many hits" (boss-damage × elite ×2 × degree, vs the elite tier HP). Builds directly on
this session; dedup-checked — no existing entry. (Not built; flagged for grooming.)

## ⟲ Previous-session review (Q-0102)
Reviewed **2026-06-23-btd6-cash-empirical-validation**. Did well: validated the cash model
against a real in-game run and **transparently walked back** wrong mid-thread conclusions as
confounds (double-cash, sandbox-no-bonus) surfaced. The pattern it and this session share:
the *owner* keeps catching the agent shipping on an assumption (cash confounds there; the
constant-/global-×2 here). **System improvement (applied this session):** treat a curated
runtime constant as *unverified* until it has **≥2 independent sources or a multi-point
check** — and hold the PR born-red until then. I did exactly that this time (held for the
2nd Fandom source before flipping). Worth baking into the curated-constant convention.

## Doc audit (Q-0104)
`check_docs --strict` + ledger check run before push. The ×2 mechanic lives in its durable
home (the `ELITE_BOSS_DAMAGE_MULTIPLIER` provenance note + the gamedata-dictionary registry
entry + this log). No owner-decision/router change. Ledger entry for #1402 lands via the
next reconciliation pass (no placeholder — Q-0052).
