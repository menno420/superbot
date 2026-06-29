# Counters — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `counters` · **Type:** server-fn · **Family:** community
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/counters_cog.py` (`!counters` status + Help hook + 10-min update loop) ·
> `disbot/cogs/counters/schemas.py` (7 SettingSpecs) · `disbot/services/counter_service.py`
> (sync + change-detection) · `disbot/services/counter_config.py` (read model + name render) ·
> `disbot/utils/settings_keys/counters.py` · folio community

> Assessed during the completion-first arc (Q-0209). Counters is the **live stat-channel** feature
> (Statbot/Carl-bot "statdock" equivalent): up to three auto-updating counter channels (total members /
> humans / bots) renamed on a 10-minute loop with change-detection (to stay under Discord's
> ~2-renames/10-min cap). It **never creates channels** — it only renames operator-bound pre-existing
> ones, so no provisioning pipeline is needed. Custom `{count}` templates; fully fail-safe (a per-guild
> fault is logged + skipped, never re-raised, never blocks the loop). Defaults all-OFF (channels unbound)
> so a fresh guild is unaffected. Config is the standard `!settings → Counters` widget gated by
> `counters.settings.configure`. (Distinct from the `counting` game — shares no code.) Gaps are polish:
> preset templates, a slash surface, loop backoff, and an integration test.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — 10-min loop renames bound channels to the rendered name
      (`counter_service.sync_guild`); three stats (total/humans/bots); custom `{count}` templates
      (`render_counter_name`); no channel-type restriction.
- [x] **Every best-in-class sub-option** — the three core stats + custom templates + throttle match the
      statdock pattern; preset bundles are the one nice-to-have → punch #1.
- [x] **Failure modes honest** — per-guild try/except, policy-load fault → 0, Forbidden/HTTPException
      logged + swallowed (never re-raised).
- [x] **Idempotent** — change-detection skips no-op renames, making the 10-min cadence safe.

### B. Reachability & UI
- [x] **A command panel exists** — `!counters` renders the policy embed (rendered names + flags);
      `manage_guild`-gated.
- [x] **Reachable every natural way** — `!counters` entry point + `build_help_menu_view` hook +
      Community-hub child; config via `!settings → Counters`.
- [N/A] **Integrated into Setup** — no dedicated wizard step (bound via `!settings`).
- [x] **Return navigation** — Help hook returns a HubView; status view is a leaf.
- [x] **In-place, not spammy** — config via `!settings`; the loop edits channel names, not chat.

### C. Convenience
- [x] **Defaults** — master OFF, all channels unbound (`counter_config.py`); fresh guild unaffected.
- [ ] **Presets** — ⚠ only the hardcoded default templates; no curated preset picker. → punch #1.
- [x] **Clear feedback** — `!counters` shows the rendered names; channel-picker `input_hint` on the
      binding specs.

### D. Authority & safety
- [x] **Authority re-checked at callback** — `!counters` `manage_guild`-gated; every SettingSpec
      `capability_required = counters.settings.configure` (enforced by `SettingsMutationPipeline`).
- [x] **All writes through the audited seam** — config writes via the `SettingsMutationPipeline`
      (DB + audit in one txn); advisory `counters.updated` event on rename. The rename itself is a
      Discord channel-name edit on an operator-bound channel (not a DB mutation).
- [N/A] **Provisioning pipeline** — counters **never creates** channels; it renames pre-existing bound
      ones (so the no-direct-create concern doesn't apply).
- [x] **Reuses governance** — administrator-grade config capability; no second allowlist.

### E. Configuration
- [x] **Settings pipeline** — `COUNTERS_*` SubsystemSchema registered at cog load; 7 scalar settings via
      `SettingsMutationPipeline`.
- [x] **config-input widgets** — master toggle + 3 channel bindings (`input_hint="channel"`) + 3
      templates, validators (bool / numeric id / non-empty ≤80-char template), defaults pinned to config.
- [x] **Everything configurable that should be** — enable, the three channel bindings, the three
      templates.

### F. Wiring & discoverability
- [x] **Registry** — key `counters`, `category: community`, `parent_hub: community`, entry `counters`,
      capability `counters.settings.configure`.
- [x] **Discoverable in Help** — `build_help_menu_view` hook; schema registered idempotently at cog load.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_counter_config.py` (policy composition, active enumeration, defaults
      parity) + `test_counter_service.py` (sync, change-detection, fail-safe, rate-limit compliance).
- [x] **Authority tests** — `test_counters_schemas.py` (every spec requires the capability) + the generic
      `SettingsMutationPipeline` enforcement tests.
- [x] **Mutation-seam tests** — pipeline `set_value` + audit covered by the shared pipeline tests;
      schema registration idempotent.
- [ ] **Live walkthrough recorded** — pending → punch #6.
- [ ] **Owner ✔** — pending → punch #7.

## Punch-list (clear these to certify)
1. **Preset templates** *(offline, minor)* — 2–3 curated `{count}` templates / a preset picker.
2. **Slash surface** *(offline, deepening)* — `/counters status` for modern-UX parity (typed-command only
   today).
3. **Loop backoff** *(offline, deepening)* — per-guild cooldown / backoff so a persistently-failing guild
   isn't silently skipped forever.
4. **Channel-type handling** *(offline, minor)* — document/test category vs voice vs text rename behavior
   (voice preferred per a code comment, not enforced).
5. **Integration test** *(offline, deepening)* — end-to-end settings-mutation → loop sync → event with a
   real policy object (today `load_policy` is mocked).
6. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot, bind a channel, watch it rename, with
   screenshots.
7. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_counter_config.py` · `…/test_counter_service.py` ·
  `tests/unit/cogs/test_counters_schemas.py` (~25 cases total) + shared `SettingsMutationPipeline` tests
- **Walkthrough:** pending (punch #6)
- **Owner sign-off:** pending (punch #7)

## Verdict
Counters is a **structurally complete, fail-safe, fully-audited** stat-channel unit — three live counters
on a rate-limit-aware change-detection loop, never creating channels (rename-only), config-driven and
defaults-OFF, with ~25 tests. It is **not yet `✔ certified`**: the gaps are polish (preset templates,
slash surface, loop backoff, an integration test — #1–#5) and the owner walkthrough/sign-off (#6/#7). No
safety/audit/dead-end issues found.
