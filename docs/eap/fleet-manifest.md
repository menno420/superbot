# Fleet manifest — Project registry

> **Status:** `living-ledger` — maintained by the **manager Project** (its sole-writer file, like each
> Project's `inbox.md`). One row per Project; the manager updates `last-seen` from each Project's
> `control/status.md` heartbeat. Protocol:
> [fleet-coordination-protocol-2026-07-09.md](../planning/fleet-coordination-protocol-2026-07-09.md).
> Seeded 2026-07-09T12:07Z at manager kickoff (start-off step 4).

| Project | Repo(s) | Model | Routine cadence | Last-seen | Notes |
|---|---|---|---|---|---|
| **manager** | all program repos (control chair; builds nothing) | — | daily rollup + owner pings (self-scheduling unavailable — owner-armed) | 2026-07-09T12:07Z (kickoff) | v2 autonomous director; sole writer of every `control/inbox.md` + this manifest |
| **SuperBot coordinator** | menno420/superbot · menno420/superbot-next | unknown | **not yet armed** (owner action: create self-poll routine, ~2–4 h while live) | 2026-07-09 (recon: next#55 merged; superbot green, recon band #1890 next) | rebuild complete (49 PRs, ~1000 tests); live-testing ledger step 1 PASS; golden-parity red-by-design (465 pending) |
| **kit-lab** | menno420/substrate-kit | unknown | **not yet armed** (owner action) | 2026-07-09 (recon: #25 merged @ eb540d9) | v1.0.0 released, 637 tests, CI green; PR #26 owner-gated; B1 benchmark next; ORDER 002 = ship the control/ kit band |
| **websites** | menno420/websites | unknown | **not yet armed** (owner action) | 2026-07-09 (recon: 20/20 PRs merged @ d0e9b33) | 3 services live on Railway; quality (required) green; Q4/Q5 owner-gated |
| **trading-lab** | menno420/trading-strategy | default (Opus 4.8) | **not yet armed** (owner action) | 2026-07-09 (repo created, scaffold in progress) | autonomous trading-strategy research lab (backtesting; research-only, no live trading); founding docs in its repo |
| codetool-lab-fable5 | menno420/codetool-lab-fable5 | Fable 5 | planned | 2026-07-09 (seeded; Project launching) | model-comparison coding arm (docs/planning/eap-project-fleet-2026-07-09.md) |
| codetool-lab-opus48 | menno420/codetool-lab-opus4.8 | Opus 4.8 | planned | 2026-07-09 (seeded; Project launching) | model-comparison coding arm (identical brief; only the model differs) |
| codetool-lab-sonnet5 | menno420/codetool-lab-sonnet5 | Sonnet 5 | planned | 2026-07-09 (seeded; Project launching) | model-comparison coding arm (third arm, added by owner decision 2026-07-09) |

Deferred fleet menu (same doc): codetool-lab-sonnet5 · game-lab · bot-lab · research-lab ·
design-lab · personal-lab · wildcard-lab. EAP free window closes Friday 2026-07-10.
