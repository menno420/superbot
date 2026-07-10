# Fleet manifest — Project registry

> **Status:** `living-ledger` — maintained by the **manager Project** (its sole-writer file, like each
> Project's `inbox.md`). One row per Project; the manager updates `last-seen` from each Project's
> `control/status.md` heartbeat. Protocol:
> [fleet-coordination-protocol-2026-07-09.md](../planning/fleet-coordination-protocol-2026-07-09.md).
> Seeded 2026-07-09T12:07Z at manager kickoff (start-off step 4).

| Project | Repo(s) | Model | Routine cadence | Last-seen | Notes |
|---|---|---|---|---|---|
| **manager** | menno420/fleet-manager (home; control chair over all program repos) | — | daily rollup + owner pings (self-scheduling unavailable — owner-armed) | 2026-07-09 | manager home repo seeded (playbook/templates/owner-queue); program record stays in superbot |
| **SuperBot coordinator** | menno420/superbot · menno420/superbot-next | unknown | **not yet armed** (owner action: create self-poll routine, ~2–4 h while live) | 2026-07-10 (gen-1 grand review #1911 merged; next: bands 1–5 all landed via #95/#97) | rebuild bands 1–5 landed (~1,132 tests); golden-parity report red-by-design (the parity dashboard — see next `docs/status/README-first.md`); ▶ tonight: band-5 live-drive (testing ladder step 7 — #95 was the replay/seams leg; the live leg is still pending), then band-6; first `ported` flip gated on the owner's flag-13 ruling |
| **kit-lab** | menno420/substrate-kit | unknown | **not yet armed** (owner action) | 2026-07-10 (#26 + #49 ratified-by-merge; wind-down complete #77) | v1.6.0 (7 releases in one day), 722 tests, CI green; PL-011 now law; ▶ tonight: B1 run-3 (UNBLOCKED by #49) |
| **websites** | menno420/websites | unknown | **not yet armed** (owner action) | 2026-07-10 (45 merged; wind-down complete #46–#48) | 3 services live on Railway; quality (required) green; ▶ tonight: ORDER 005 — the succession docs' "#1 TRAP: looks done, is NOT"; run `scripts/healthcheck.py` first |
| **trading-lab** | menno420/trading-strategy | default (Opus 4.8) | **not yet armed** (owner action) | 2026-07-09 (repo created, scaffold in progress) | autonomous trading-strategy research lab (backtesting; research-only, no live trading); founding docs in its repo |
| **game-mining** | menno420/superbot-games (shared, lanes) | default | **not yet armed** (owner action) | 2026-07-10 (#5/#11/#14 ALL merged — lane fully landed; wind-down complete) | pure domain (18 modules, 62 tests) + grid-encounters on main; ▶ tonight per queue-state: mint parity goldens while porting the workflow layer |
| **game-exploration** | menno420/superbot-games (shared, lanes) | default | **not yet armed** (owner action) | 2026-07-09 (wind-down complete, #13) | quest/encounter engine (48 tests) on main; ▶ tonight per succession doc: live-host seam / D&D plan next |
| codetool-lab-fable5 | menno420/codetool-lab-fable5 | Fable 5 | planned | 2026-07-09 (seeded; Project launching) | model-comparison coding arm (docs/planning/eap-project-fleet-2026-07-09.md) |
| codetool-lab-opus48 | menno420/codetool-lab-opus4.8 | Opus 4.8 | planned | 2026-07-09 (seeded; Project launching) | model-comparison coding arm (identical brief; only the model differs) |
| codetool-lab-sonnet5 | menno420/codetool-lab-sonnet5 | Sonnet 5 | planned | 2026-07-09 (seeded; Project launching) | model-comparison coding arm (third arm, added by owner decision 2026-07-09) |
| **venture-lab** | menno420/venture-lab | default | hourly (cadence class A) | 2026-07-09 (repo seeded @ d065c68) | first gen-2 born-right lane; Project boot pending owner clicks |

## Lane notes — gen-1 wind-down

*(2026-07-09; corrected 2026-07-10 by the grand-review session per
[gen1-grand-review-2026-07-09.md](gen1-grand-review-2026-07-09.md) §5 — manager re-stamps
at next rollup.)*

- **Wind-down complete ×9 — ALL lanes closed:** kit, websites, trading, 3 codetools
  (fable5 / opus48 / sonnet5), games-exploration, **games-mining** (#5/#11/#14 landed
  2026-07-10 under the owner's sweep authorization), and **superbot-next's retro pair is
  on its main** (#87 self-review + #92 project review — the earlier "no wind-down
  reaction" cell was stale; the lane itself stays mid-rebuild by design, Q-0241).
- **Pending ×0.** Open PRs across the six core repos at 2026-07-10 00:19Z: zero
  (grand-review report §3), plus the live #1913 audit lane.

Deferred fleet menu (same doc): codetool-lab-sonnet5 · game-lab · bot-lab · research-lab ·
design-lab · personal-lab · wildcard-lab. **EAP window extended to 2026-07-14** (Anthropic
email 22:29Z, 2026-07-09; supersedes the Friday 2026-07-10 close recorded at seeding).
