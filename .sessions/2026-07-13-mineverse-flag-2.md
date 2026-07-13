# 2026-07-13 — mineverse FLAG 2: HMAC mining write endpoint

> **Status:** `complete`
> **Branch:** `claude/mineverse-flag-2` · **PR:** #2061 (**held DRAFT deliberately** — merge=deploy
> Q-0193; the owner flips it ready and controls the deploy moment).
> **Venue:** remote container (worker session, orchestrated). **📊 Model:** fable-5
> **Scope:** the bot side of mineverse FLAG 2 (`control/status.md` on superbot-mineverse main,
> spec-of-record @52fe2ca): the HMAC-signed action-proposal WRITE endpoint per
> `docs/mining-write-contract.md` + the two v1 write schemas. Runtime `disbot/` change,
> dormant-by-default, TEST GUILD ONLY.

## Arc

FLAG 2 asks the bot for a signed POST action endpoint (`/relay/mining/action`, web reads
`MINING_WRITE_ENDPOINT`): HMAC over `METHOD\nPATH\nTIMESTAMP\nsha256_hex(body)` (±300s skew, key
`MINING_WRITE_SHARED_SECRET`), validation against `schemas/mining_action.v1.schema.json`, the
closed 7-action enum mapped 1:1 to `mining_workflow` ops, idempotency by `action_id` (≥24h,
replay vs 409 `replayed_action`), 10/10s + 60/min rate limits with `Retry-After`, an
`emit_audit_action` row for EVERY attributable web action, and a hard test-guild allowlist
(other guilds 403 until the owner's stage-(d) flag). Done-bar: the mineverse shim contract
fixtures' semantics (`tests/test_actions.py`) hold against the real endpoint.

## Shipped

- **`disbot/mining_write_api.py`** — the endpoint (the `control_api` pattern: same healthserver
  aiohttp app, no second server; dormant unless `MINING_WRITE_SHARED_SECRET` is set):
  - HMAC verify byte-compatible with mineverse `server/actions.py` (the contract's canonical
    signing): constant-time, signature BEFORE the skew window; pre-auth rejections answer
    v1 envelopes with the placeholder action_id and are never audited/stored.
  - stdlib request classifier mirroring the shim's reason-code order (version → enum →
    envelope `malformed_request` → params `invalid_params`), proven equivalent to the vendored
    Draft 2020-12 schema by an agreement battery (dev-env `jsonschema` gate).
  - Idempotency: `mining_web_actions` table (migration 105; `utils/db/mining_web_actions.py`)
    keyed `(guild_id, action_id)` — byte-identical replay returns the ORIGINAL response with
    `replayed: true`, never re-executes, never re-audits; different body → 409
    `replayed_action` (audited, never stored); accepted AND rejected outcomes stored;
    `rate_limited` + `internal_error` never stored (retry with the same id is a fresh run).
    Retention 24h enforced at read time + opportunistic purge — restart-safe (merge=deploy
    means an in-memory store would shed replay protection on every deploy).
  - Rate limits per `(suid, guild_id)`: sliding 10/10s + 60/60s → 429 + integer `Retry-After`.
  - Execution ONLY via `services/mining_workflow.py` ops (`mine`/`descend`/`ascend`/`sell`/
    `vault_deposit`/`vault_withdraw`/`equip`); domain refusals (`TradeResult.ok=False`,
    unmoved descend/ascend) relay as 422 `economy_rejection`; unexpected faults answer 500
    `internal_error`. `result.state_delta` re-projects the touched READ-contract fields with
    the FLAG 1 field semantics (count-map clamps, gear wear = max − remaining, shared level
    curve).
  - Audit per the contract's binding requirement: `emit_audit_action(subsystem="mining",
    actor_type="web_player", ...)` + `extra_fields` carrying
    action_id/action/suid/params_digest/outcome/timestamp/contract_version/origin="web"
    (guild_id rides the canonical field). Accepted and every attributable rejection audited.
  - Hard allowlist `MINING_WRITE_GUILD_ALLOWLIST` (comma-separated snowflakes; empty =
    fail-closed 403 for all guilds). No stage-(d) bypass exists in code — owner-only, future.
- **`disbot/services/audit_events.py`** — additive `extra_fields` param on `emit_audit_action`
  (merged into the bus payload; the canonical 11 win collisions; the subscriber already takes
  `**_extras`).
- **`disbot/utils/db/games/mining_player_state.py`** — `has_player_state` read probe (the
  `actor_not_found` gate, mirroring the READ contract's population rule).
- **`disbot/healthserver.py`** — registration hook, wrapped so the relay can never break the
  health server or bot startup.
- **Tests — `tests/unit/runtime/test_mining_write_api.py`** (46): ports the semantics of
  mineverse `tests/test_actions.py` against the real handler — signing round-trip/bad-sig
  battery/skew both directions/signature-before-timestamp, per-action happy paths asserting
  the 1:1 workflow calls, schema taxonomy (malformed/unknown/invalid/version/extra-key/
  placeholder echo), allowlist 403 + fail-closed, actor 404, economy 422, replay (accepted
  AND rejected) + 409 key reuse, both rate windows + Retry-After + (suid,guild) keying,
  audit fields on accept and reject, dormancy/registration, allowlist parsing. Dual-gate:
  every response passes an always-running stdlib structural gate derived from the vendored
  response schema, plus full `Draft202012Validator` when `jsonschema` is present
  (`requirements-dev.txt` — dev/agent-only, not CI).
- **`tests/fixtures/mineverse/mining_action.v1.schema.json` +
  `mining_action_response.v1.schema.json`** — vendored verbatim from superbot-mineverse main
  (2026-07-13).
- Guard-driven collateral: `scripts/context_map.py` + `tests/unit/scripts/test_atlas.py`
  (`mining_write_api` as a known top-level composition-root module, the `control_api`
  precedent), regenerated `docs/operations/env-vars.md` + `dashboard/data/dashboard.json`
  (+ botsite exports), telemetry row (Q-0194).

## Honest nulls / decisions made alone

- **`vault_deposit`/`vault_withdraw` param mapping**: the contract moves COINS
  (`{"amount": N}`), but superbot's mining vault is an ITEM store
  (`mining_workflow.vault_deposit(user, guild, item, qty)`) and coins live in the economy
  table, never in the mining pack. Chosen 1:1 mapping: the vault op on the `"coins"` item —
  today the domain itself vetoes it (422 `economy_rejection`, honest: the live game has no
  coin vault), and it becomes real automatically if coins ever join the mining inventory.
  Flagged for the owner: if a coin-vault is wanted for the web game, that is a
  `mining_workflow` feature, not an endpoint hack.
- **`equip` slot mismatch**: the proposal names a slot; superbot derives the slot from the
  item. If `equipment.slot_for(item)` ≠ the proposed slot, the endpoint vetoes with 422
  rather than equipping somewhere the player didn't ask (executing would betray the proposal).
- **Rate-limit placement**: after the idempotency lookup (replays don't burn budget — a replay
  executes nothing) and before allowlist/actor/execution. 429s are audited (attributable);
  the contract is silent, the shim has no limiter.
- **`internal_error` (500)**: audited `rejected:internal_error`, never stored (contract: safe
  to retry with the same action_id). The response-schema taxonomy includes it; the shim never
  emits it.
- **Idempotency storage**: Postgres table via a numbered migration (repo convention;
  `proof_channel_locks` precedent for restart-safe deadlines) rather than in-memory —
  merge=deploy makes restarts routine, and the contract demands ≥24h retention ACROSS runs.
- **Where mineverse's files were silent** (exact 401/400 message strings), the shim's message
  strings were reused verbatim where they exist; response `message` strings from
  `mining_workflow` relay as-is (they carry Discord markdown — safe plain text for the web UI).

## Context delta

- **Needed but not pointed to:** mineverse `tests/shim/shim_bot.py` + `server/actions.py` are
  the real executable contract (status-code order, placeholder action_id, audit outcome format
  `accepted:ok`/`rejected:<code>`) — the schemas alone underdetermine the endpoint; the
  handover pointed at `tests/test_actions.py`, which pointed onward.
- **Pointed to but didn't need:** `architecture_rules/extension_roles.yaml` — no cog was added,
  so the extension-guard family (crosswalk, help-surface pins) never fired.
- **Discovered by hand:** `scan_env_usage.py` only sees string-LITERAL env reads (a
  `os.environ.get(CONST)` is invisible — FLAG 1's two relay vars are in fact missing from
  `docs/operations/env-vars.md` for this reason); `scripts/atlas.py` requires new top-level
  disbot modules in `context_map.TOP_LEVEL_MODULES` + the test's layerless allowlist;
  `emit_audit_action` is a closed 11-field contract whose subscriber already tolerates extras.
- **Decisions made alone:** the six flagged above, plus env var name
  `MINING_WRITE_GUILD_ALLOWLIST` and the audit `extra_fields` seam extension.
- **Flagged for maintainer / weak point:** end-to-end conformance against mineverse's actual
  fixtures (`SHIM_CONFORMANCE_BASE_URL` seam) is unverified by construction — no live endpoint
  exists until this deploys with the secret set; the unit suite ports the fixtures' semantics
  but is not the fixtures. DB-backed idempotency SQL is exercised via a dict twin, not live
  Postgres.
- **Docs/tooling change that would have helped:** make `scan_env_usage.py` resolve
  module-level string constants (it silently under-documents env vars read via constants) —
  filed as the session idea below.
- **🛠 Friction → guard:** friction — (a) the atlas orphan trip on a new top-level module is
  only discoverable by running the suite; the existing test IS the guard (it bit; nothing new
  needed). (b) `scan_env_usage`'s literal-only blindness produced a silent doc gap in FLAG 1;
  cheapest durable fix is the scanner enhancement (proposed below — shared checker, so
  proposed rather than applied, the FLAG 1 session's Q-0194 precedent). Worked around
  in-code with literal reads + a comment pinning them to the constants.

## 📤 Run report

- **Did:** built mineverse FLAG 2 — the HMAC-signed, schema-validated, idempotent,
  rate-limited, hard-allowlisted, fully audited mining WRITE endpoint on the healthserver app,
  dormant by default. · **Outcome:** shipped (PR open, deliberately draft).
- **Shipped:** #2061 — `POST /relay/mining/action` (endpoint + idempotency migration/CRUD +
  audit seam extension + 46 tests + vendored write schemas + guard collateral); held DRAFT
  for the owner's deploy moment.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** ratify the vault coins-item mapping (or commission a real
  coin-vault op in `mining_workflow`); ratify auditing 429s + the `extra_fields` audit-seam
  extension.
- **⚑ Owner manual steps:** flip PR #2061 ready to land+deploy (Q-0193); then on Railway set
  `MINING_WRITE_SHARED_SECRET` (both sides: bot service + mineverse web host) and
  `MINING_WRITE_GUILD_ALLOWLIST` (the test guild snowflake) — and on the mineverse side
  `MINING_WRITE_ENDPOINT` (the bot's private URL + `/relay/mining/action`); then run the
  mineverse conformance sweep (`SHIM_CONFORMANCE_BASE_URL` per its
  `docs/live-prod-cutover.md` §1) as the cutover check.
- **⚑ Self-initiated:** none — dispatched work (mineverse FLAG 2 via the coordinator).
- **↪ Next:** run mineverse's conformance fixtures against the deployed endpoint (the FLAG 2
  done-bar's live half); mineverse-lane follow-up: the web-side ingest for FLAG 1's READ
  relay is still missing.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (1 opened, held draft by design) |
| CI-red rounds | 0 local mirror reds fixed pre-push (atlas orphan, dashboard drift, ruff); CI pending at close |
| Repo-rule trips | 2 (atlas top-level-module pin; dashboard env-var freshness) — both guard-caught, fixed same session |
| New ideas contributed | 1 |
| Ideas groomed | 1 |

## 💡 Session idea

**Teach `scan_env_usage.py` to resolve module-level string constants** (one extra AST pass:
`NAME = "LITERAL"` assignments, then treat `os.environ.get(NAME)` as a read of the literal).
Today any module that names its env vars in constants — the pattern our own style rewards —
silently vanishes from `docs/operations/env-vars.md` and the dashboard env inventory (FLAG 1's
two relay vars are missing right now; FLAG 2 worked around it with literal reads). Small,
stdlib-only, and it would also let the freshness guard catch the FLAG 1 gap retroactively.
(Deduped against `docs/ideas/` — nothing covers the env scanner.)

## ⟲ Previous-session review

The FLAG 1 session (#2058) left an excellent handover: the vendored-fixture dual-gate pattern
and the new-module guard checklist were both directly reusable, and its "honest null" framing
(transport unspecified → groundable seam + flag) is the right template. One gap its card
couldn't know: its `docs/operations/env-vars.md` regen was a no-op (the scanner can't see
constant-name reads), so the card overstates that artifact — worth a one-line correction in
the next reconciliation pass. **Workflow improvement:** the new-cog/new-module guard checklist
it wished for should also name the atlas top-level-module pin (this session's trip).

## Grooming pass (Q-0015)

Annotated `docs/ideas/games-theme-engine-website-first-2026-07-10.md` §3 with a dated groom
note: the write seam its "phase 2 interactivity" depends on now exists (PR #2061, FLAG 2) —
both halves of the mineverse read/write contract pair have bot-side implementations in flight,
so the idea's dependency list is current again.
