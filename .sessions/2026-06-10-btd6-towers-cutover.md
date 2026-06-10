# 2026-06-10 — BTD6 towers cutover (Q-0066/Q-0067/Q-0068), PR #649

**Task:** "continue with the btd6 data cutover" — the owner-decided (Q-0066)
dedicated session executing the `--all` cutover end-to-end.
**Shipped:** PR #649 (draft at first push per Q-0052) — every committed BTD6
stats file (25 towers, 17 heroes, 13 paragons) is now **game-native v55.1**,
written through a new cutover merge layer in `parse_gamedata.py`
(`cutover_payload`: curated-name renames/stripping, carry-forwards, scalar
transplants, upgrade-name restore, a set-level name guard green across all 55
entities). Q-0067 (Farm/Village 0→64 tiers, damage-based nominal-attack
suppression, prose-pinned income-aura decodes) and Q-0068 (per-tier beast names
from upgrade cards) executed in the same pass. Full CI mirror 8543 passed;
post-cutover `--audit` 76 CLEAN · 9 DELTA · 0 SUSPECT. Technical detail lives
in the decode-status session log (its ⭐ header carries the new backlog) — this
file carries the process learnings.

## Process learnings (the durable part)

- **The guard-driven loop beat up-front cataloguing.** Instead of trying to
  enumerate every curated-name correspondence first, I built the name guard
  early and let it FAIL across all 55 entities — each failure was then resolved
  consciously (rename / decode / carry-forward / retire). Two iterations got
  53/55 → 55/55. The failures even exposed wiki-vs-game *upgrade-name*
  divergence (Buccaneer's whole roster is internally prefixed) nobody had
  catalogued.
- **The audit cannot detect an empty mapped list** (`_walk_audit` only compares
  keys present in both trees). Monkey Ace mapped with ZERO attacks (its whole
  kit is `AttackAirUnitModel`) and the audit stayed silent — a value-pinned
  test caught it. After structural mapper changes, diff per-tier entity counts;
  don't trust the audit alone for *presence*.
- **3-scout fan-out worked again** (tests inventory / runtime consumers / dump
  evidence, ~390K subagent tokens). The dump-evidence scout's premise
  corrections were load-bearing: beast per-tier names do NOT exist on the
  models (upgrade names are the only source — changed the Q-0068 design),
  Village's Mega Ballista is a real damaging attack (changed suppression from
  blanket to damage-based), and committed "Sellback rate buff" is a
  buff-ification of a zone model. I spot-checked the load-bearing claims
  against source before acting; all held.
- **Run scouts and your own evidence pass in parallel, then reconcile.** I had
  answered ~60% of scout C's questions myself by the time it returned; the
  remaining 40% (engineer sentry mechanism, totem shared-internal-name, exact
  tier lists) would have been expensive solo. The overlap was cheap insurance
  against a scout error.
- **Same-session sibling hazard from last time didn't recur** (no parallel
  agents on this branch), but the pipe-status and format-hook traps from the
  journal were live: CI-mirror before every push, formatters via
  `python3.10 -m black` explicitly after heredoc-driven test appends.
- **Heredoc `str.replace` editing failed silently once** (a no-op replace I
  didn't assert on). The later batch asserted `old in s` before writing —
  do that always, or use the Edit tool.

## Owner-visible result

"What can the bot answer now that it couldn't yesterday": Farm/Village
questions (Wall Street $4,000/round, IMF Loan 85s, 10%/5% discounts with the
tier-3 cap, Radar Scanner camo grant, MIB all-types, Primary Training auras),
per-tier beast names ("what's the Orca / Pouākai"), Spectre / Mini Sun Avatar
minion stats, Bloon Crush knockback details — and every stats answer now
carries an honest "BTD6 game data 55.1" label instead of "bloonswiki 53.0/54.0".

## Grooming pass (Q-0015)

This session WAS the top backlog item (roadmap "Later" → shipped). Routed the
post-cutover decode backlog into the decode-status ⭐ header (5 ordered items,
incl. the banana-economy decode idea that surfaced from scout evidence — kept
in decode-status rather than `docs/ideas/` since it's a continuation of an
active lane, not a new product idea).

**Resume point:** decode-status ⭐ header. The maintainer owes a live
spot-check of the new surfaces (item 4 there); PR #649 review = the full data
diff.
