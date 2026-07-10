# Fleet manifest — Project registry

> **Status:** `living-ledger` — maintained by the **manager Project** (its sole-writer file, like each
> Project's `inbox.md`). One row per Project; the manager updates `last-seen` from each Project's
> `control/status.md` heartbeat. Protocol:
> [fleet-coordination-protocol-2026-07-09.md](../planning/fleet-coordination-protocol-2026-07-09.md).
> Seeded 2026-07-09T12:07Z at manager kickoff (start-off step 4).
> **Re-stamped 2026-07-10T16:38Z by the fleet-manager standing wake (16:31Z second pass, manager
> ORDER 002)** — every row rewritten to verified post-launch reality; evidence = fleet-manager
> `docs/launch-readiness-2026-07-10.md` + `control/status.md` @ a70bcb9 + live `list_triggers` +
> per-repo git fetch of each lane's `control/status.md` `updated:` header at re-stamp time.
> Note: this staleness class is slated to die structurally — a **generated-from-heartbeats roster**
> proposal (fleet-manager `docs/proposals/generated-roster-from-heartbeats.md`, ORDER 009) would make
> this file a pointer to a roster regenerated at every manager wake.

| Project | Repo(s) | Model | Routine cadence | Last-seen | Notes |
|---|---|---|---|---|---|
| **manager** | menno420/fleet-manager (home; control chair over all program repos) | — | **2-hourly standing wake — WORKS, self-armed** (`trig_01QBrp5MjZL3F9mv6KsTXTzN`, cron `30 */2 * * *`; live-fired 14:36Z + 16:31Z) | 2026-07-10 (status 16:02Z; HEAD a70bcb9) | coordinator seat **LIVE** (booted 2026-07-10); kit v1.4.0 (3 MINOR behind); ORDERs 001/003/007/008 open, 002 done this pass, 004–006 done |
| **superbot (hub)** | menno420/superbot | — | reconciliation loop self-fires (issue #1951); no standing seat wake — Idea Engine seat pending owner Project click | 2026-07-10 (PR #1948 MERGED 16:01:56Z, merge 658d29e6) | **#1948 merged by the owner** — Q-0260/Q-0261 material + all three founding packages now ON MAIN (the round-opening prerequisite is cleared); Idea Engine boot = owner creates the Project + pastes the founding package (~5 min) |
| **superbot-next (Builder)** | menno420/superbot-next | — | **none** — ORDER 008 (self-arm 2-hourly, stagger even hours) unacked/unexecuted; no Builder trigger in the account registry | 2026-07-10 (HEAD b63b933 15:57Z; status 01:05Z — **ENDER-MISSING**, ~15 h stale) | gen-1 MID-MISSION band 5 (BUILD+REPLAY landed #95/#97, live-drive next); ORDER 010 (@codex rule) DONE PR #103 (b63b933); ORDERs 008 (boot-gating) + 009 (Q-0262 flag-13) pending; kit v1.6.0 |
| **kit-lab** | menno420/substrate-kit | — | **2-hourly standing wake — WORKS, self-armed by the fresh seat** (`trig_016EfUawz6KxEYqUM6f1BqDw`, cron `0 */2 * * *`, armed 15:53Z, fired 16:02:43Z; old hourly `trig_01FnqnAQjLU2T8d16iHwWQ2h` DELETED — F-1 rebind-then-delete executed) | 2026-07-10 (status 16:17:12Z — first fresh-seat heartbeat; HEAD 2ba610a 16:29Z) | gen-2 CLOSED handoff-ready at **v1.7.0**; **fresh seat now LIVE past the boot gate**; carried owner items: OA8 setup-script paste + F-5 one-letter ruling (HOT — gates B1 run-5 dispatch); ORDER 011 (Q-0262) at HEAD; write-all distribution scope per Q-0261.3 |
| **websites** | menno420/websites | — | **4-hourly fresh-session wake — WORKS, self-armed** (`trig_017H9Qb9oxtLgUy6sw2gnSHg`, cron `0 */4 * * *`, armed 13:49Z; **FIRST FIRE VERIFIED 16:01:32Z**, next 20:01Z; archive-immune by construction) | 2026-07-10 (close-out #58 / d493792 13:57Z; status 13:56Z; first routine-woken heartbeat pending at re-stamp time) | ORDERs 001–008 ALL done (done=001–008 @ d493792); 3 services live on Railway; required check `quality` green; kit v1.6.0; owner items non-gating (botsite Postgres, PAT) |
| **trading-strategy** | menno420/trading-strategy | — | **4-hourly standing wake — WORKS, self-armed** (`trig_01Mvn5xRmqGmZJNRHgjqyLpN`, cron `0 */4 * * *`; 3+ confirmed fires 04:08/08:00/12:00Z; session-bound — F-1 watch item) | 2026-07-10 (status 16:21:48Z; HEAD e713abb 16:24Z — ORDER 007 lane live) | *(row formerly "trading-lab" — renamed to match the repo)* P1–P5 prep DONE, **PARKED GREEN** (close-out #34); **holdout SEALED** (no unlock marker, all ledger rows data_end ≤ 2025-01-08) with unlock **ORDER 008 landed @ fd5e9fe** (Q-0262.2, sequences AFTER ORDER 007); ORDER 007 (significance bar + AAPL-donchian re-grade) in flight; kit v1.1.0 (oldest pin) |
| **venture-lab** | menno420/venture-lab | — | **none** — ORDER 002 (self-arm hourly) pending; ENDER rides ORDER 004 at fresh boot | 2026-07-10 (HEAD af11bdb 14:49Z — boot ORDER PR #12; status 04:57Z stale-by-design until ORDER 004) | **9 PRs landed; 2 sellable products + buyer zips ON MAIN** (#9 merged 05:11:50Z: membership-kit v0.2 + template-packs v0.1 + $59 bundle); **⚑B/⚑D publish clicks FROZEN** pending ORDER 003 (P0 real-Stripe-path fix D1/D2/D3); ORDERs 002/003/004 all pending; kit v1.6.0 |
| **games-plugins** | menno420/superbot-games (merged-lane identity: mining + exploration) | — | **none** — ORDER 002 (self-arm wake) landed in inbox PR #21 (adb5f9b), unexecuted; relaunches clockless until it runs | 2026-07-10 (HEAD adb5f9b 15:57Z; lane close-outs #19/#20 13:49–13:53Z) | both gen-1 lanes closed green (mining @b0541bf, exploration archived-pending-gen-2 @7d9663f); **ORDER 001 (P0 CI-collection: gate collects 73/121 tests) pending — boot-gating**; kit v1.2.0 (v1.7.0 `adopt --lane` is the fix for its two-writer ⚑) |
| **pokemon-mod-lab** | menno420/pokemon-mod-lab | — | **none** — ORDER 002 (self-arm hourly) pending; first relaunch session must be externally fired | 2026-07-10 (HEAD a76ada7 12:56Z; status 07:49Z — session-008 ender) | **PRIVATE ✅ (API-verified 2026-07-10 ~15:12Z — the URGENT flip happened)**; LANE PARKED at session 008 (PRs #2–#10, 12 QoL patches, queue exhausted); ORDERs 002/003 pending, consumable at first boot; kit v1.6.0; owner: playtest verdict + concept pick (rec: Emerald QoL+, effective post-core per Q-0262.7) |
| **gba-homebrew** | menno420/gba-homebrew | — | **none** — ORDER 002 (self-arm hourly) pending; same clockless-first-session caveat | 2026-07-10 (HEAD b607365 11:13Z — ORDER 002 append; status 07:14Z — session-7 ender) | **Lumen Drift SCOPE-COMPLETE** (session 7, close-out #24); public-by-design (no Nintendo-derived content); 11 review-queue rows are agent work at next boot; kit v1.6.0; owner: play it (~15 min) + concept pick |
| codetool-lab-fable5 | menno420/codetool-lab-fable5 | Fable 5 | none (Project CLOSED) | 2026-07-10 (HEAD a6cf1a9 12:07Z — ORDER-006 succession fix; status 07-09 20:06Z) | **Project CLOSED; repo retained, NOT platform-archived** (`archived:false` API 07-10); PLATFORM-LIMITS item 4 corrected (release wall is SEAT-dependent, not model); envdrift v0.1.0/v0.2.0 tags+Releases parked owner-click |
| codetool-lab-opus48 | menno420/codetool-lab-opus4.8 | Opus 4.8 | none (Project CLOSED) | 2026-07-09 (HEAD 80f6cd1 20:13Z; status 20:11Z) | **Project CLOSED; repo retained, NOT platform-archived**; **2 LIVE releases shipped via Actions `workflow_dispatch`** (v0.1.0 published 2026-07-09T16:56:21Z, v0.2.0 17:57:53Z — the proven release route); 1 stale branch for owner sweep |
| codetool-lab-sonnet5 | menno420/codetool-lab-sonnet5 | Sonnet 5 | none (Project CLOSED) | 2026-07-09 (HEAD 66c3dfc 20:09Z; status 20:02Z) | **Project CLOSED; repo retained, NOT platform-archived**; cfgdiff **v0.1.1 on main, unreleased — pending 2 owner clicks** (PyPI trusted publisher + `v0.1.1` tag @ 0b1eb60; do NOT tag v0.1.0 @ 0260aae); release.yml has never fired |
| mobile-lab | *(repos NOT created — 6-repo harness experiment, ready-not-launched)* | — | n/a | 2026-07-10 (packages/prompts committed paste-ready in fleet-manager) | launch is owner-gated on repo creation (agent repo-create = verified 403 wall); no lane state exists to track yet |

## Post-launch note (2026-07-10)

*(Replaces the gen-1 wind-down lane notes and every "▶ tonight" plan — those plans
**executed overnight**: launch 00:00–06:15Z landed **116 PRs fleet-wide, zero stuck**; full
record: fleet-manager `docs/planning/gen2-launch-record-2026-07-10.md`.)*

- **Gen-2 fleet is LIVE.** Standing wakes verified self-armable and recurring on four seats
  (fleet-manager, substrate-kit fresh seat, websites, trading-strategy); the remaining live
  lanes carry pending self-arm ORDERs (superbot-next 008, games 002, venture 002,
  pokemon 002, gba 002).
- **Round-3 opening prerequisite CLEARED:** superbot PR #1948 merged 2026-07-10T16:01:56Z
  (owner) — Q-0260/Q-0261 + the founding packages are on main.
- **Wind-down history (compressed):** all 9 gen-1 lanes closed clean by 2026-07-10 morning;
  codetool ×3 Projects CLOSED with repos retained un-archived (owner archive toggle is a
  parked click, recommendation: archive only after the gen-3 succession question settles).
- **EAP window:** through **2026-07-14** (Anthropic email 22:29Z 2026-07-09); fleet economics
  ledger banked pre-close (fleet-manager `docs/findings/fleet-economics-2026-07.md`, ORDER 004).
