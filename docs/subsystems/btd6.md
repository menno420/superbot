# BTD6 data / tools subsystem — folio

> **Status:** `living-ledger` (area index). Source + ADR-006 + current state win.
> **Last updated:** 2026-06-10 (ADR-006 wording fix; the 2026-06-10 cutover/
> decode/answerability campaign lives in `btd6-gamedata-decode-status.md` ⭐ +
> `docs/current-state.md` — this folio routes, it does not restate).

## What & where

BTD6 spans reference/data ingestion, provenance/source registry, caches, live
queries/events, strategies, browsers, calculators, and grounded AI context. Start in
`disbot/cogs/btd6/`, `disbot/cogs/btd6_cog.py`, the other `disbot/cogs/btd6_*_cog.py`
files, `disbot/services/btd6_*`, `disbot/views/btd6/`, `disbot/utils/db/btd6_*`,
`disbot/utils/settings_keys/btd6.py`, and `disbot/data/btd6/`.

## Rules & approved structures (binding — link, don't restate)

- **ADR-006** (`docs/decisions/006-btd6-data-provenance-ownership.md`) binds the
  provenance object, owner-per-fact-type matrix, hybrid storage choice, and source
  registry linkage. The schema is **implemented**
  (`docs/btd6/btd6-provenance-schema.md`) and extraction runs against the
  decode-status backlog under that contract *(stale "extraction remains paused"
  wording corrected 2026-06-10 — the v55.1 cutover + decode campaign, #649–#668,
  shipped under the implemented schema)*.
- Provider/provenance checks, caching/source-health clarity, and AI behavior/config
  correctness are gates, not optional polish. `docs/current-state.md` owns the global
  gate wording.
- Preserve groundedness and absence-claim guards. Derived values must carry enough
  evidence/provenance to distinguish sourced facts from calculations; see
  `docs/btd6/btd6-derived-value-groundedness-finding.md` and
  `docs/btd6/btd6-absence-claim-guard-design.md`.
- BTD6 AI behavior is configuration/capability gated; shared media/YouTube is owned
  by `docs/subsystems/media-youtube.md`, not BTD6 (ADR-007).

## Current state

- ADR-006 provenance schema **implemented** (`docs/btd6/btd6-provenance-schema.md`).
  BTD6 data extraction may resume against the ordered backlog in
  `docs/btd6/btd6-gamedata-decode-status.md`. The broader AI/BTD6 feature-expansion
  gate (stability + caching + AI config) still applies per `docs/current-state.md`.
- The repo already contains source registry, ingestion, fact-store, data-provider,
  cache, grounding, resolver, live-query, strategy, and ops-readiness services plus
  migrations/data. Their existence is not proof that provenance/source health is
  sufficient for new extraction.
- Existing UI direction is visible in live-event, tower, hero, leaderboard, strategy,
  CT-map, and paragon browser/calculator views. Paragon and other env-gated paths may
  run degraded in the sandbox; do not call them broken or production-verified.
- **Production data lane (learned live 2026-06-10):** prod runs
  `BTD6_DATA_BACKEND=postgres` — fixtures are served from the `btd6_data_blobs`
  table (warmed once at boot), **not** the repo files, so a merged data PR does
  NOT change what prod serves until the store is re-seeded. Since PR #676
  seed-data **applies immediately** (re-warms + drops the dataset cache; no
  restart), and version drift between bundled files and the store is surfaced
  in the boot log + a `!btd6 status` ⚠️ field.
- **Auto-seed-on-boot (Q-0077(b), PR #1255):** `cog_load` re-seeds the postgres
  store from the deployed files **when they carry a strictly newer `game_version`**
  (`auto_seed_enabled()` + `bundled_newer_than_served()` → `seed_postgres_from_files()`;
  defensive, kill-switch `BTD6_AUTO_SEED=0`). So a **version bump** is zero-touch
  (merge → deploy → current). **A same-`version` data edit (e.g. a buff-stat fix
  with no version bump) is NOT auto-applied** — by the owner's strict-(b) choice
  (2026-06-21) it still needs a one-time `!btd6 ops seed-data`. Code deploys
  themselves are Railway auto-deploy-on-merge; `!restart` exits nonzero since
  PR #675 so the platform relaunches it.
- **Same-version drift is now surfaced (PR #1258):** since strict (b) ignores
  same-`version` edits and `served_data_drift()` is version-only, a buff/stat fix
  with no version bump used to stay stale silently. `content_drift()` (sha over the
  canonical JSON, the seed digest) now flags those at boot **and** in `!btd6 status`
  with a "run `!btd6 ops seed-data`" reminder — warn-only, no auto-write.

## Plans / pending approval

The BTD6 docs describe decode/extraction, pipeline, backend, cloud-data, AI tool
calling, and smoke-test directions. They are indexed in
[`../btd6/README.md`](../btd6/README.md) and remain subordinate to ADR-006 and the global
AI/BTD6 gate. Do not duplicate their detailed sequences here.

- **`docs/planning/ai-btd6-answerability-roadmap-2026-06-09.md`** (`plan`) — maps the gap between already-known deterministic BTD6 data and reliable AI selection, grounding, explanation, and introspection. It is not a broad extraction pass and remains under the global AI/BTD6 gate.

## Ideas (not approved)

Further live-event/tower/hero/leaderboard browsing, richer paragon calculation, and
additional AI tools are candidates only after provenance, caching, source health, and
behavior/config gates are satisfied.

## Next candidates

1. Before restarting extraction, verify ADR-006's provenance schema is implemented,
   source-registry references and owner matrix are enforced, migrations are safe,
   and cache/source-health behavior is observable and tested.
2. Reconcile provider/provenance and freshness claims across the source registry,
   ingestion supervisor, fact store, cache, and rendered responses.
3. Only after the global gate clears, choose a bounded browser/calculator/AI change
   and prove derived-value groundedness plus degraded-source behavior.

## Related docs

`docs/decisions/006-btd6-data-provenance-ownership.md`, the BTD6 docs indexed in
[`../btd6/README.md`](../btd6/README.md),
`docs/audits/agent-d-btd6-ai-subsystem-audit-2026-06-05.md`,
[`docs/planning/production-readiness/btd6-production-readiness-map-2026-06-12.md`](../planning/production-readiness/btd6-production-readiness-map-2026-06-12.md),
`docs/current-state.md`, `docs/subsystems/ai.md`, `docs/subsystems/media-youtube.md`.

## Product-extension routing (not approved)

The [BTD6 product-extension routing draft](../btd6/btd6-product-extension-routing-2026-06-08.md) routes rules/trivia, challenge generation, score/run tracking, and leaderboards without bypassing ADR-006, provenance, source-health, provider, or groundedness gates.
