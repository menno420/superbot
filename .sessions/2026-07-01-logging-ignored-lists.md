# 2026-07-01 — Logging: ignored channels/users exclusion lists (completion deepening)

> **Status:** `complete`

**Run type:** `routine · dispatch`

## What I'm about to do

Empty work order (scheduled fire) → advance the next real S1 plan slice. Per
`docs/current-state/S1-bot.md` ▶ Next, the standing offline deepening is clearing the assessed
completion certs' punch-lists. Picking **Logging punch #1 — ignored channels / users exclusion
lists** (`[offline, deepening]`), the named best-in-class gap vs Carl-bot/Dyno
(`docs/planning/feature-completion/units/logging.md`).

**Scope:** add two per-guild scalar settings — `logging_ignored_channels` and `logging_ignored_users`
(comma-separated id CSV, default empty) — so an operator can log every category *except* in named
channels / for named users (e.g. "log all deletes except in #bot-testing"). Mirror the proven
`automod_config` exempt-list pattern exactly (`parse_id_csv` → `frozenset[int]`, tolerant read /
loud write validator). Wire the exclusion into the shared passive-event gate
(`_log_event_if_enabled`) so every category respects it; add the `event_skipped_ignored` counter;
add the two `SettingSpec`s to the logging schema (version 3→4); tests + docs.

Additive, default-off, byte-identical for every existing guild. Then flip this card to `complete`.

Also: deleted a stale claim file (`claude__ai-answer-storage-plan-3fvdit.md`) for already-merged
BTD6 track-length work (#1578) on sight (Q-0166).

## What shipped (PR #1594)

Logging completion cert **punch #1 CLOSED**. Two per-guild scalar settings, additive/default-off,
**no migration**, byte-identical for every existing guild.

- **`utils/settings_keys/logging.py`** — `LOGGING_IGNORED_CHANNELS` / `LOGGING_IGNORED_USERS` (+
  re-export in `settings_keys/__init__.py`).
- **`services/server_logging_config.py`** — `DEFAULT_IGNORED_CHANNELS`/`_USERS`; `EventLoggingPolicy`
  gains `ignored_channel_ids` / `ignored_user_ids` (`frozenset[int]`, `field(default_factory=frozenset)`)
  + an `is_ignored(channel_id, user_id)` gate; `load_policy` resolves the two CSVs via the tolerant
  `parse_id_csv` **reused from `automod_config`** (function-local import — the module's stdlib-only
  top-level discipline; mirrors what `image_moderation_config` already does).
- **`services/server_logging.py`** — `_log_event_if_enabled` takes `channel_id` / `user_id` and skips
  (new `event_skipped_ignored` counter) after the `should_log` gate when either is ignored; the five
  passive handlers pass their context (`getattr(..., "id", None)`, fail-safe).
- **`cogs/logging/schemas.py`** — two `SettingSpec`s + `_validate_id_csv` (loud write-time gate),
  schema **v3→v4**.
- **Tests (+8 net):** `test_server_logging_events.py` (policy gate · CSV parse · channel-ignored ·
  user-ignored · not-ignored-sends), `test_logging_schemas.py` (v4 pin + spec assertions). Extended
  the settings edit/reset round-trip pickers with a numeric-id-CSV candidate (their own comment says
  those candidates exist for exactly this: validated free-form str specs). Regenerated `dashboard.json`
  / `site.json` / `data.js` (2 new setting keys). Doc-pinned in the settings-customization command map.
- **Full CI mirror GREEN** (13,392 passed); arch strict clean (no new warnings).

## 📤 Run report

- **Did:** shipped Logging completion cert punch #1 — ignored channels/users exclusion lists for the
  passive event log · **Outcome:** shipped (CI green, auto-merge armed)
- **Shipped:** #1594 — `utils/settings_keys/logging.py` (+`__init__`) · `services/server_logging_config.py`
  · `services/server_logging.py` · `cogs/logging/schemas.py` · `tests/unit/services/test_server_logging_events.py`
  · `tests/unit/cogs/test_logging_schemas.py` · `tests/unit/views/test_settings_{edit,reset}_round_trip.py`
  · regenerated `dashboard/data/dashboard.json` · `botsite/data/site.json` · `botsite/site/data.js` ·
  docs (`feature-completion/units/logging.md`, `settings-customization-command-map.md`, `current-state/S1-bot.md`).
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** none (no migration / data step — legacy KV scalars; live on next auto-deploy).
- **⚑ Self-initiated:** the slice itself is the standing S1 offline deepening ▶ Next (not self-invented).
  The stale-claim-file deletion (already-merged #1578 BTD6 work) was a fix-on-sight drift cleanup (Q-0166).
- **↪ Next:** Logging punch #2 (channel-create/delete/rename + voice `on_voice_state_update` events —
  `[owner]`, needs a volume-tuning call) · punch #3 (in-panel event-toggle presets — `[offline]`).
  Other units' offline picks: Inventory item-detail density (#4) · Proof-channel binding-write UI. The
  ignore lists are settings-only today (no dedicated picker UI) — a `channels`/`users` multi-select
  editor in the `!logging` panel is a natural `[offline]` follow-on.

## 💡 Session idea (Q-0089)

**A `check_settings_schema_version_bumped.py` guard** (or a pytest regression) that fails when a
`SubsystemSchema`'s `settings`/`bindings` **tuple changes shape** (a spec added/removed/renamed) but
its `version=` integer is **not** bumped in the same diff. This session bumped logging v3→v4 by hand
and the only thing pinning it was a hand-written `test_logging_schema_version_bumped_to_v4` I had to
remember to update; nothing *forces* the bump. A schema whose shape drifts without a version bump is a
silent migration-provenance hole (the version is how the settings registry reasons about compatibility).
Genuine "enforce, don't exhort" (Q-0132) — route to `docs/ideas/` if a later session wants it. Not
filler: the exact class of drift this session could have shipped unnoticed if I'd forgotten the bump.

## ⟲ Previous-session review (Q-0102)

The previous run (#1573/#1577/#1582, bot-owner platform-admin override) is a strong example of
completion-first, root-cause work: it didn't just add one override, it **consolidated ~9 scattered
inline owner/admin checks onto one `config.is_platform_owner` helper** and flagged the duplication as a
latent bug farm — exactly the "one source + a guard that keeps it one source" instinct. What it
*surfaced but left open* (and its own Q-0089 idea proposed): a CI guard pinning the single-source rule.
The system-level improvement this session reinforces: **the schema-version-bump guard idea above is the
same shape** — the codebase keeps generating "one place should be the source, and a checker should keep
it that way" opportunities faster than they're built. That's healthy (the friction→guard loop is
working), but it means the *ideas backlog of enforcement guards* is itself a lane worth a grooming pass:
several sessions in a row have ended with an "enforce-don't-exhort" idea that then waits. A future
session could batch-build the 3-4 cheapest ones (schema-version, single-owner-source, exact-name) in one
checker-hardening PR rather than one-per-session. No workflow defect; a batching opportunity.

## Doc audit (Q-0104)

`check_current_state_ledger --strict` → clean (the merges newer than marker #1590 are benign
newest-merge lag the next reconciliation pass records; this session adds no *prior*-merge ledger
change — #1594 is the current head). New behaviour reachable + documented: logging completion cert
punch #1 marked done, S1-bot recently-shipped + ▶ Next updated, settings-customization command map
carries the two new keys + spec names (doc-test-pinned). Generated artifacts regenerated + fresh-checked.
No chat-only decisions left unrouted (no new owner decision this run). `check_quality --full` green.

## 🛠 Friction → guard (Q-0194)

- **Friction:** adding two `SettingSpec`s reddened **5 unexpected tests** — 2 settings-customization
  doc-pins, 2 settings round-trip parametrizations (edit + reset), 1 dashboard-artifact freshness — none
  obvious from the touched files. **Guard (already exists, worked as designed):** every one of those
  *is* an enforcing guard that caught real drift (doc must list the key; every writable spec must survive
  a round trip; the committed dashboard.json must match a fresh export). No new guard needed — noting the
  fan-out so the next settings-spec editor expects it: **adding a `SettingSpec` touches the doc-pin, the
  round-trip picker (if validated free-form), and the dashboard export.** The round-trip picker needed a
  numeric-id-CSV sample candidate (added) — that's the one spot that isn't self-maintaining for a *new
  shape* of validated str spec.
- **Candidate guard (proposed):** the Q-0089 schema-version-bump checker — free-to-ship (a test/checker),
  but recorded as a candidate rather than wired since it would gate CI on a new convention.

## Context delta

- **Needed but not pointed to:** the orientation route doesn't surface the **settings-spec ripple set**
  (doc-pin + round-trip picker + dashboard export). A one-liner in `helper-policy.md` or the settings
  folio — "adding a `SettingSpec` requires: the command-map doc entry, a round-trip-compatible sample
  value, and `export_dashboard_data.py`" — would save the next editor the red-CI discovery loop. The
  per-file context-map hook (importers + blast radius) does *not* reveal these test couplings.
- **Pointed to but didn't need:** CodeGraph — this was a localized additive change on a known seam;
  grep + the context-map hook + reading the two config/schema files carried it.
- **Reused, one-source:** `parse_id_csv` from `automod_config` (the same import `image_moderation_config`
  already uses) — no new duplicate parser; the established convention held.
- **Decisions made alone:** exclusion is **OR across channel/user** and applied *after* `should_log`
  (so a disabled category still short-circuits first); `None` ids never match (a channel-less member
  event is only filtered by the user list). Settings-only surface (no dedicated picker UI) this PR —
  flagged as a natural follow-on.
