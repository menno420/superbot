# 2026-07-13 — mineverse FLAG 1: mining snapshot relay

> **Status:** `complete`
> **Branch:** `claude/mineverse-flag-1` · **PR:** #2058 (**held DRAFT deliberately** — merge=deploy
> Q-0193; the owner flips it ready and controls the deploy moment).
> **Venue:** remote container (worker session, orchestrated). **📊 Model:** fable-5
> **Scope:** the bot side of mineverse FLAG 1 (`control/status.md` on superbot-mineverse main,
> spec-of-record @52fe2ca): emit a v1-conformant mining snapshot into the part-4d bot→web READ
> relay. Runtime `disbot/` change, dormant-by-default.

## Arc

FLAG 1 (carried verbatim by the 2026-07-12 owner-queue session) asks the bot to project live
mining state into the read relay per `schemas/mining_snapshot.v1.schema.json` +
`docs/mining-data-contract.md` (superbot-mineverse main): envelope `schema_version "1"` /
`generated_at` ISO8601 UTC / `guild_id` STRING / `miners[]` with 16 per-miner v1 fields, ~60s
cadence, done = payload validates under `Draft202012Validator`.

## Shipped

- **`disbot/services/mining_snapshot_service.py`** — the projection + transport service:
  - `build_snapshot(guild_id, ...)` — the v1 envelope; one miner per `mining_player_state` row
    (`db.list_guild_miner_ids`, new reader). Field sources exactly as the contract names them:
    `mining_player_state`/`mining_grid` (depth, record_depth, position, energy, vault_level),
    `mining_equipment`/`mining_gear_wear`/`mining_inventory`/`mining_vault`/`player_skills`/
    `mining_structures` maps, `economy` coins, `game_xp` → `xp {game, game_total, shared_total,
    level}` via the one shared level curve. Optional world-shape hints `max_depth`/`biomes`
    included (they mirror `utils/mining/world` exactly — the sample snapshot's labels).
  - **Energy settled at projection time** (pure `utils.mining.energy.settle`, read-only).
  - **`gear_wear` = accumulated wear** (contract semantics) projected from the DB's
    *remaining durability* as `max_durability − remaining`.
  - Defensive clamps (depth 0–3, vault_level 0–6, coins ≥ 0, count-maps ≥ 0, equipment keyed to
    the closed slot enum) so an out-of-band oracle value can never emit a payload the web side's
    ingestion validation (mineverse PR #42) would refuse.
  - `push_snapshot(...)` — HTTP POST via aiohttp, 10s timeout, **never raises** (every failure
    class logged + absorbed; a dead relay degrades the website, never the bot).
  - `relay_config()` — dormant-by-default (the `control_api` discipline): arms only when BOTH
    `MINING_SNAPSHOT_RELAY_URL` and `MINING_SNAPSHOT_RELAY_GUILD_ID` are set.
- **`disbot/cogs/mining_relay_cog.py`** — glue-only, command-free loop cog
  (`media_maintenance_cog` pattern): 60s `tasks.loop` (the contract's suggested cadence), one
  startup log line stating ENABLED/OFF, display names via `core.runtime.guild_resources
  .resolve_member` (cache-only, suid fallback). `push_now()` is the single build+push seam —
  the loop uses it and it is the ready on-demand hook for a future owner surface.
  Registered in `config.INITIAL_EXTENSIONS` after `mining_cog`.
- **`disbot/utils/db/games/mining_player_state.py`** — `list_guild_miner_ids(guild_id)` (+ the
  `utils.db` re-export): read-only guild enumeration, the contract's population rule. Reads stay
  direct per `docs/ownership.md` RS02.
- **Tests — `tests/unit/services/test_mining_snapshot_service.py`** (17): the schema gate runs
  twice — full `jsonschema.Draft202012Validator` (the FLAG 1 done-criterion, dev-env only via
  `importorskip`; `jsonschema==4.23.0` added to `requirements-dev.txt`, NOT a CI or runtime dep)
  plus an **always-running stdlib structural gate** that derives required lists / enums / bounds
  from the schema JSON itself (the mineverse no-drift rule), so CI still validates the shape.
  Also pinned: wear projection, energy settling, xp derivation, defensive clamps, suid fallback,
  dormant no-op, both-vars-required, non-snowflake rejection, push success / non-2xx / raising
  transport (mocked HTTP), cog dormancy, builder-failure absorption.
- **`tests/fixtures/mineverse/mining_snapshot.v1.schema.json`** — vendored copy of the v1 schema,
  verbatim from superbot-mineverse main (2026-07-13). Refresh it when v1 gains additive fields.
- Guard-driven collateral: `architecture_rules/extension_roles.yaml` (`mining_relay` →
  `operational_adapter`, backs `mining`) + regenerated
  `docs/architecture/extension-taxonomy-crosswalk.md` and `docs/operations/env-vars.md`
  (the two new env vars); count/reference updates in `docs/help-command-surface-map.md` and
  `docs/setup-platform/settings-customization-command-map.md`.

Quality mirror green before push: `python3.10 scripts/check_quality.py --full` →
**All checks passed ✓** (13904 passed, 49 skipped, 2 xfailed). `check_docs --strict` +
`check_current_state_ledger --strict` green (ledger: benign #2057 newest-merge lag only).
No `docs/current-state.md` ledger entry — the ledger is merged-PRs-only and this PR is
deliberately held draft; the next reconciliation pass records it post-merge.

## Honest nulls / decisions made alone

- **The READ-relay transport is genuinely unspecified** — the FLAG 1 spec + data contract define
  payload, cadence and validation but name **no** bot-side endpoint or env var (unlike FLAG 2's
  `MINING_WRITE_ENDPOINT`), and the mineverse web server currently *reads a local file*
  (`data/sample_snapshot.json`) with **no ingest route**. Implemented to the groundable seam:
  builder + validated payload + 60s loop + a configurable poster. **Chosen (decide-and-flag):
  HTTP POST of the snapshot JSON to `MINING_SNAPSHOT_RELAY_URL`**, guild-scoped by
  `MINING_SNAPSHOT_RELAY_GUILD_ID` (names mirror FLAG 2's `MINING_WRITE_*` family). The
  matching web-side ingest (or a different transport decision) is the mineverse lane's
  follow-up — routed below.
- `gear_wear` projected as accumulated wear (`max − remaining`) because the contract prose says
  "accumulated wear" while the DB column stores remaining durability; the sample snapshot's
  `diamond pickaxe: 58` (= 400 − 342) corroborates.
- Envelope is single-guild by contract; multi-guild fan-out (if ever wanted) is a v2/tuple
  concern, not guessed at here.
- Per-miner reads are N-per-miner single-row queries (reusing the existing RS02 readers) — fine
  at 60s cadence for realistic miner counts; batch readers are a later optimization if a big
  guild ever arms the relay.

## Context delta

- **Needed but not pointed to:** the fact that the mineverse "read relay" has no receiving
  endpoint yet (had to read `server/app.py` on mineverse main to establish the honest null);
  the guard set a new extension trips (`extension_roles.yaml` overlay, guild-resources
  invariant, help-surface/settings-map count pins, env-vars doc regen) — discovered by running
  the mirror, which is fine but a one-line "new cog checklist" pointer would have saved a cycle.
- **Pointed to but didn't need:** nothing notable.
- **Discovered by hand:** DB `mining_gear_wear.durability` counts *down* (remaining), contract
  wear counts *up* — only visible from `_apply_wear_writes` + the sample payload; CI installs
  `requirements.txt` only, so a jsonschema-based gate must be importorskip'd with a stdlib
  fallback that still runs in CI.
- **Decisions made alone:** the two env-var names + POST-JSON transport (flagged above); vendored
  schema location `tests/fixtures/mineverse/`; `operational_adapter` role for the cog.
- **Flagged for maintainer / weak point:** the push path is unit-tested against a mocked HTTP
  layer only — there is no live endpoint to hit yet, so end-to-end delivery is unverified by
  construction (the honest null). The Draft202012 gate runs in dev envs, not CI (stdlib gate
  covers CI).
- **Docs/tooling change that would have helped:** a "adding a new extension" checklist doc
  naming the guard set (overlay → crosswalk regen → env-vars regen → count-pinned docs).
- **🛠 Friction → guard (Q-0194):** friction — four generated/count-pinned artifacts went stale
  the moment a cog was added; the existing guards caught 100% of them (crosswalk test,
  help-surface count pin, settings-map reference pin, env-usage sync test), so the system already
  enforces this — no new guard needed, and none shipped (nothing was missable).

## 📤 Run report

- **Did:** built mineverse FLAG 1 — the bot-side v1 mining-snapshot projection + dormant 60s
  push relay, schema-gated by tests against the vendored v1 contract. · **Outcome:** shipped
  (PR open, deliberately draft).
- **Shipped:** #2058 — mining snapshot READ-relay (service + cog + db reader + 17 tests +
  guard collateral); held DRAFT for the owner's deploy moment.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** ratify the READ-relay transport choice (POST to
  `MINING_SNAPSHOT_RELAY_URL`) — or redirect; the web side needs a matching ingest either way.
- **⚑ Owner manual steps:** flip PR #2058 ready to land+deploy (draft held for deploy safety,
  Q-0193); later, when the web-side ingest exists: set `MINING_SNAPSHOT_RELAY_URL` +
  `MINING_SNAPSHOT_RELAY_GUILD_ID` on the bot's Railway service to arm the relay.
- **⚑ Self-initiated:** none — dispatched work (mineverse FLAG 1 via the coordinator).
- **↪ Next:** FLAG 2 (HMAC write endpoint, spec verbatim in mineverse `control/status.md`) —
  can reuse this session's vendored-fixture pattern + the relay env-var family; and the
  mineverse-lane follow-up: a web-side ingest for the READ relay (its stage-1 file read has no
  push receiver).

## 📊 Telemetry

| PRs merged | CI-red rounds | rule trips | ideas contributed | ideas groomed |
|---|---|---|---|---|
| 0 (1 opened, held draft by design) | 0 | 0 | 1 | 1 |

## 💡 Session idea

**Relay self-conformance check at push time:** reuse the tests' schema-derived stdlib structural
validator inside `mining_snapshot_service.push_snapshot` (log-loud + skip push on
non-conformance). The web side already refuses malformed relays with a 503; a producer-side
check would surface the same drift *in the bot's own logs at the moment a schema/oracle change
lands*, instead of as a mysterious stale website later. Small, stdlib-only, no new dep.
(Deduped against `docs/ideas/` — nothing existing covers producer-side contract self-checks.)

## ⟲ Previous-session review

The 2026-07-13 hub-upkeep Codex-P2 session (#2055 lane) was tight and evidence-first — it
verified D-0043's owning artifact live before wording a cross-repo pointer, exactly the Q-0120
instinct. Miss worth naming: its card skipped the Q-0089 `💡 Session idea` and Q-0102 review
enders (allowed for orchestrated micro-sessions in practice, but the README doesn't say so).
**Workflow improvement:** `.sessions/README.md` could state explicitly whether orchestrated
worker micro-sessions may abbreviate the ender set — today each worker re-decides it.

## Grooming pass (Q-0015)

Moved `docs/ideas/games-theme-engine-website-first-2026-07-10.md` one step down its lifecycle:
its §3 read-path dependency ("the part-4d relay") is no longer hypothetical — annotated in place
with a dated groom note pointing at the shipped projection (PR #2058), so the next agent
evaluating that idea knows the read seam exists.
