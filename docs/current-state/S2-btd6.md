# S2 — BTD6 · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S2 · Folio:
> [btd6](../subsystems/btd6.md) · Decode backlog:
> [btd6-gamedata-decode-status](../btd6/btd6-gamedata-decode-status.md).

**Recently shipped (this sector):**
- **Damage-type / status-effect interaction grounding** (PR #1487, owner-directed from live DDT/glue
  screenshots) — a new `[btd6_interaction]` grounding pass (`btd6_interaction_service` +
  `data/btd6/damage_types.json`) fixes the "can tower X deal with bloon Y?" error class at the root: the
  model was handed bloon immunities + tower descriptions separately and invented the rule (it said *"Lead
  resists glue"* — false). The curated damage→property table is **cross-checked against the game-sourced
  `immune_to` data** (a curated typo or re-seed fails CI). Plus a verified
  [QA-accuracy corpus](../btd6/qa-accuracy-corpus-2026-06-27.md) (the "big list of questions") and bloon
  prose completion. Caught + excluded a wrong research claim (Sniper is Sharp/no-lead at base, not Normal).
- **P1-1 BTD6 grounding-anchor eval guard** (the #704 finding, offline half) — every number the
  golden set asserts (Despo $12,025 / ×10 $120,250 on Impoppable, Elite Lych HP per tier, ABR/round
  cash ranges) is now pinned to a deterministic `btd6_data_service` re-derivation **and** the case
  rubric, so a re-seed that changes a price *or* an edited rubric number fails CI; plus a
  capability/answerability-consistency guard (`tests/evals/test_btd6_grounding_anchors.py`).
  **Fixture-drift extension (2026-06-25 dispatch run, PR #1458):** the BTD6 *grounding* cases that use
  `contains(...)` graders bake their truth into the `tool_results` **fixture** (not a rubric), so those
  numbers had no data-drift guard — now a `FixtureAnchor` table pins Navarch income ($3,200) + paragon
  cost ($550,000) to `btd6_stats_service` re-derivations and asserts they still appear in the case
  fixture (data-drift + fixture-drift), with the curation principle documented (only exactly-derivable
  *truths* are anchored — not distractors). **Projected-total extension (2026-06-25 dispatch run, PR
  #1460):** the starting-cash convention is nailed — `projected_total = stated_start + round_cash(start,
  end).range_cash` (the stated start is the user-message constant, NOT cumulative-from-round-1; the
  earlier "~$10 off" was a wrong-accessor probe) — so the four `knowledge.btd6_round_cash_*` / `_abr_*`
  projected totals ($21,187.90, $39,840, $56,318.70, ABR $119,315.30) now carry both drift guards via
  `_projected_total`. Only the **distractors** ($71,315.20, $107,164.60) and the bare user-supplied
  starting figures stay deliberately unanchored.
- **Buff-uptime upgrade-detail model** — `btd6_upgrade_detail_service` + AI tool + `parse_gamedata`
  extraction, multi-target uptime (#1235/#1249/#1251).
- **Data-lifecycle hardening** — auto-seed BTD6 blob data on boot (#1255), content-drift surface
  (#1258), `!btd6ops seed-data` changed-report (#1263). **Closes the standing "owner must remember
  to run `seed-data`" manual step.**

**▶ Next startable:**
*(offline-fit tags — `[offline]` self-mergeable now · `[needs-live-bot]` needs a running bot / runtime
creds · `[owner]` needs an owner decision/action; see [`../repo-sector-map.md`](../repo-sector-map.md)
§ "the offline-fit startability tag".)*
- `[owner]` Decode-status ⭐ item 3 (buff/zone tail, demand-driven) + item 4 (maintainer live spot-check).
- `[needs-live-bot]` **P1-1 live `llm_judge` battery** (the model actually using the grounded facts — creds-gated; the
  offline grounding half now shipped, above) + absence-guard **Layer B** (the negative-existential
  gate, design-for-review; needs prod creds).
- `[offline]` **Anchor-tooling follow-ons** (offline, self-mergeable) — *(the range-cash + projected-total figures
  AND the #855 MOAB-class bonuses +15/+30/+99 are now anchored, #1460 above — the BTD6 knowledge/
  grounding cases are anchor-complete for every cleanly-derivable truth; **the eval-anchor coverage
  report + distractor negative-anchor guard both shipped 2026-06-26, PR #1466**)*: the **coverage
  guard** now inventories every significant (≥ $1,000) rubric/fixture number per BTD6 case and asserts
  it is anchored or on a documented distractor/user-input allowlist (a new dollar/HP truth left
  unanchored fails CI); the **distractor negative-anchor guard** pins each documented distractor
  ($71,315.20, $107,164.60, the standard-Lych-as-elite HP) distinct from the truths its case asserts (a
  re-seed can't silently collapse a case's discrimination), and pins the standard-set-range alias for
  the one derivable distractor. ▶ remaining anchor-tooling tail: none cleanly offline — the live
  `llm_judge` battery (below) is the next BTD6 correctness step.

**Gate:** the broad AI/BTD6 feature-expansion gate (stability + provider/provenance + caching + AI
config) still applies — see [`../current-state.md`](../current-state.md) § Gates / blocked work.

*Note: the in-bot AI eval **harness** is S1; the BTD6 **data/grounding** correctness it checks is
S2. Probe a live grounding miss with `python3.10 scripts/btd6_probe.py "<exact user text>"`.*
