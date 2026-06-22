# S2 — BTD6 · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S2 · Folio:
> [btd6](../subsystems/btd6.md) · Decode backlog:
> [btd6-gamedata-decode-status](../btd6/btd6-gamedata-decode-status.md).

**Recently shipped (this sector):**
- **Buff-uptime upgrade-detail model** — `btd6_upgrade_detail_service` + AI tool + `parse_gamedata`
  extraction, multi-target uptime (#1235/#1249/#1251).
- **Data-lifecycle hardening** — auto-seed BTD6 blob data on boot (#1255), content-drift surface
  (#1258), `!btd6ops seed-data` changed-report (#1263). **Closes the standing "owner must remember
  to run `seed-data`" manual step.**

**▶ Next startable:**
- Decode-status ⭐ item 3 (buff/zone tail, demand-driven) + item 4 (maintainer live spot-check).
- P1-1 eval-smoke matrix (creds-gated) + absence-guard **Layer B** (the negative-existential gate,
  design-for-review; needs prod creds).

**Gate:** the broad AI/BTD6 feature-expansion gate (stability + provider/provenance + caching + AI
config) still applies — see [`../current-state.md`](../current-state.md) § Gates / blocked work.

*Note: the in-bot AI eval **harness** is S1; the BTD6 **data/grounding** correctness it checks is
S2. Probe a live grounding miss with `python3.10 scripts/btd6_probe.py "<exact user text>"`.*
