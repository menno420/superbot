# 2026-06-24 — BTD6 per-round economy slash commands (cash / RBE / bloons)

> **Status:** `complete` — owner-directed (Discord screen recording). PR #1404;
> auto-merge armed; merges on green. Full CI mirror green (12,329 passed).

> **Run type:** `manual · owner-directed`

> **⚑ Self-initiated:** none — the feature itself was owner-directed (the
> recording). The AI-tool follow-up (below) is *captured*, not built.

Owner ask (Discord, screen recording of CyberQuincy's `/income start_round:100
end_round:120`): *"so people can see cash, rbe, bloons etc per round via slash
commands."* He wants **our** bot to have per-round economy lookups — like
CyberQuincy's `/income`, but extended to RBE + bloon composition, and showing
**our verified numbers** (last session proved CyberQuincy over-counts: its
$139,067 for r100-120 vs our $89,878, which matched the in-game double-cash test).

## Shipped (PR #1404)
All per-round data already existed from this session-arc — this is an exposure
layer, not new modelling. Prefix + slash twins in `btd6_reference_cog` via
`cogs.btd6._builders` (shared-backbone parity held):
- **`/btd6ref income <start> [end] [roundset]`** — verified cash table
  (`round_cash`): per-round + cumulative + range total. r100-120 = **$89,878**
  (vs CyberQuincy's inflated $139,067). Public, not ephemeral (shareable, like
  the demo). Full `_CASH_ASSUMPTIONS` in the footer.
- **`/btd6ref rbe <start> [end]`** — **new `round_rbe`**: base (wiki
  `RoundEntry.rbe`) + effective freeplay-scaled (`bloon_rbe_at_round` summed over
  groups). Two columns where they diverge (81+); collapses to one ≤ r80. Anchor
  BAD r100 = 67,200 vs 55,760 base.
- **`/btd6ref round <n>`** (enhanced) — now lists the bloon **composition**
  (canonical + camo/regrow/fortified tags) and the effective RBE for 81+.
- `btd6-gamedata-dictionary.md` — breadcrumb: these facts are now player-queryable
  via the commands.

**Rigor:** the load-bearing invariant — effective RBE *reconstructs* base for
every round ≤80 (test-pinned), so the 81+ divergence is provably the freeplay
rules, not a methodology mismatch. Effective is labelled "freeplay-scaled (model)"
vs the wiki base; neither is misrepresented. 22 new tests; full mirror green.

## Mid-session course-corrections (both caught by the full mirror, then fixed)
1. **Duplicated an existing function.** I wrote a second `round_composition`
   (single-round, resolved) that shadowed the *existing* range/AI one — breaking
   its AI-tool + ABR tests. Root cause: my pre-build dedup grep keyed on the
   *concepts* (cash/income/rbe) and command names, not the **exact function name**
   I was about to define. Fix: deleted the duplicate, reused the existing function;
   the round embed formats composition from raw `RoundEntry.groups` (which also
   surfaces the modifiers the existing function drops). `round_rbe` was unique — no
   collision.
2. **Command count 389 → 393** (income + rbe, ×2 surfaces) is baked into generated
   artifacts — regenerated `site.json` / `dashboard.json` / `data.js` and updated
   the per-cog leaf-set test (`test_btd6_split_command_parity`).

## 💡 Session idea (Q-0089)
**Wire `round_rbe` into the AI grounding/tools**, alongside the *already-wired*
`round_cash` + `round_composition` AI tools. Right now the bot answers per-round
cash and composition in free text, but for RBE it only has the base figure in
grounding — so "what's the *real* RBE at round 120?" gets 258k (base), not 432k
(effective). Wiring `round_rbe` (a thin `_btd6_round_rbe` tool spec, mirroring
`_btd6_round_composition`) closes that — the bot would answer freeplay-scaled RBE
with the same engine the new `/btd6ref rbe` command uses. Dedup-checked: no
existing `round_rbe` AI tool. Small, contained, builds directly on today.

## ⟲ Previous-session review (Q-0102)
Reviewed **2026-06-24-btd6-paragon-elite-boss-damage**. Did well: held the PR
born-red until the elite ×2 *constancy* was independently re-verified (2nd Fandom
source) rather than shipping on the one screenshot — exactly the discipline the
owner keeps having to enforce. **System improvement surfaced this session:** the
"claim before starting / don't duplicate" rule (and `helper-policy.md`) should
add one concrete step — *before defining a new service function, grep `def
<exact_name>` in the target module AND for the nearest concept synonyms.* My
collision (#1) is the precise failure that step prevents: I checked for income/
cash/rbe and command names, but never grepped `def round_composition`. Cheap,
mechanical, and would have caught it pre-implementation instead of at the full
mirror. (Routing this as a router DISCUSS Q is the right next move — it's a
CLAUDE.md/helper-policy rule change, which I propose, not self-apply.)

## Backlog grooming (Q-0015)
Reviewed the per-round-economy ideas. `round-range-comparison-bare-range-list-
2026-06-16.md` (accept comma-list "rounds 1-30, 30-60" phrasing in the §7.5 cash
floor) remains the most-ready **decided-lane** item — small, test-bounded, AI-
floor surface (distinct from today's slash commands). Teed up as a clean next-
session quick win; not promoted here to stay focused on the owner-directed build.

## Doc audit (Q-0104)
`check_docs --strict` ✓, `check_current_state_ledger --strict` exit 0,
`check_quality --full` green. New commands expose *existing* curated facts (no new
runtime-formula fact); the gamedata-dictionary breadcrumb is the durable home for
discoverability. No owner-decision/router change beyond the proposed DISCUSS Q
above. Ledger entry for #1404 lands via the next reconciliation pass (Q-0052).
