# 2026-06-24 — BTD6 per-round economy slash commands (cash / RBE / bloons)

> **Status:** `in-progress` — owner-directed (Discord screen recording). Born-red
> card; flips to `complete` as the final step once the work + close-out land.

> **Run type:** `manual · owner-directed`

Owner ask (Discord, screen recording of CyberQuincy's `/income start_round:100
end_round:120`): *"so people can see cash, rbe, bloons etc per round via slash
commands."* He wants **our** bot to have per-round economy lookups — like
CyberQuincy's `/income`, but extended to RBE + bloon composition, and showing
**our verified numbers** (last session proved CyberQuincy over-counts: its
$139,067 for r100-120 vs our $89,878, which matched the in-game double-cash test).

## What I'm about to do
All the per-round data already exists from this session-arc — this is an
exposure layer, not new modelling:
- **Cash** → `btd6_data_service.round_cash(start, end, roundset)` (verified model;
  r100-120 = $89,877.6, vs CyberQuincy's inflated $139,067).
- **RBE** → base (wiki `RoundEntry.rbe`) + effective freeplay-scaled
  (`bloon_rbe_at_round` summed over `groups`; verified anchor BAD r100 = 67,200,
  vs 55,760 base). Base and effective diverge for rounds 81+ (MOAB scaling +
  superceramic swap) — both shown, clearly labelled, neither misrepresented.
- **Bloons** → `RoundEntry.groups` (wiki composition).

Plan (mirrors the existing `btd6ref` tower/hero/round pattern; prefix + slash
twins via `cogs.btd6._builders`):
1. `btd6_data_service.round_rbe(start, end=None, roundset)` — base+effective per
   round, structured like `round_cash` (+ per-bloon breakdown for a single round).
2. `btd6_data_service.round_composition(round, roundset)` — resolved spawn groups.
3. `_builders.build_income_embed` / `build_rbe_embed`; enhance `build_round_embed`
   to add composition + effective RBE for 81+.
4. `btd6_reference_cog`: `income` / `rbe` commands (prefix + slash), enhanced
   `round`.
5. Tests: round_rbe (r100 eff 67200 / base 55760; r6 equal; range shape),
   round_composition, builders. Full CI mirror green before flip.

Rigor note: effective RBE is our engine's output, verified at the r100 anchor and
labelled "freeplay-scaled (model)"; base RBE is the directly-sourced wiki value.
Cash carries its `_CASH_ASSUMPTIONS` (Medium, no income towers, standard set).
