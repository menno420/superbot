# S2 — BTD6 · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S2 · Folio:
> [btd6](../subsystems/btd6.md) · Decode backlog:
> [btd6-gamedata-decode-status](../btd6/btd6-gamedata-decode-status.md).

**Recently shipped (this sector):**
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
  *truths* are anchored — not distractors or convention-dependent cumulative totals).
- **Buff-uptime upgrade-detail model** — `btd6_upgrade_detail_service` + AI tool + `parse_gamedata`
  extraction, multi-target uptime (#1235/#1249/#1251).
- **Data-lifecycle hardening** — auto-seed BTD6 blob data on boot (#1255), content-drift surface
  (#1258), `!btd6ops seed-data` changed-report (#1263). **Closes the standing "owner must remember
  to run `seed-data`" manual step.**

**▶ Next startable:**
- Decode-status ⭐ item 3 (buff/zone tail, demand-driven) + item 4 (maintainer live spot-check).
- **P1-1 live `llm_judge` battery** (the model actually using the grounded facts — creds-gated; the
  offline grounding half now shipped, above) + absence-guard **Layer B** (the negative-existential
  gate, design-for-review; needs prod creds).
- **Anchor the remaining range-cash convention figures** (offline, but needs the *exact* cumulative
  convention first): the `knowledge.btd6_round_cash_*` / `_abr_*` rubrics assert cumulative totals
  ($56,318.70, ABR $119,315.30, $5,443, …) that a naive `round_cash(1, N)` re-derives ~$10 off — so
  they are deliberately **unanchored** (see the curation note in `test_btd6_grounding_anchors.py`).
  A future slice that nails the cumulative/starting-cash convention can add these anchors safely;
  until then, anchoring them would assert a wrong "truth".

**Gate:** the broad AI/BTD6 feature-expansion gate (stability + provider/provenance + caching + AI
config) still applies — see [`../current-state.md`](../current-state.md) § Gates / blocked work.

*Note: the in-bot AI eval **harness** is S1; the BTD6 **data/grounding** correctness it checks is
S2. Probe a live grounding miss with `python3.10 scripts/btd6_probe.py "<exact user text>"`.*
