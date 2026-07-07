# Automod — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `automod` · **Type:** server-fn · **Family:** moderation
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/automod_cog.py` (`!automod` status + Help hook + pipeline stage, order 5) ·
> `disbot/cogs/automod/listener.py` (the stage body) · `disbot/cogs/automod/schemas.py`
> (15 SettingSpecs) · `disbot/services/automod_service.py` (detection engine + SpamTracker +
> DuplicateTracker) · `disbot/services/automod_config.py` (read model + defaults) ·
> `disbot/utils/settings_keys/automod.py` · folio `docs/subsystems/server-management.md`

> Assessed during the completion-first arc (Q-0209). Automod is **moderation's automated message-filter
> layer**: six rule types — spam burst (sliding window), cross-channel spam burst, repeated/duplicate
> content, invite-link filter, excessive caps, and mass-mention — evaluated on the message pipeline
> (stage order 5), with per-rule exemptions (roles/channels). Actions route through the audited
> `moderation_service` seam (`auto_delete` + `warn` with `actor_id=None`, reusing moderation's
> escalation ladder — no second ladder). All flags default **OFF** so a fresh guild is unaffected;
> config is the standard `!settings` widget gated by `moderation.settings.configure` (automod *is*
> moderation's automated layer). **Punch #5/#6 SHIPPED 2026-07-07** (owner-raised gap, fixed the same
> day): the original spam rule was rate-only (no content-duplicate detection) and keyed per-channel
> (a multi-channel burst never tripped it) — both closed by two new rules, `automod.cross_channel_spam`
> and `automod.duplicate`, riding the same audited seam. Detail:
> [`../../../ideas/automod-spam-detection-gaps-2026-07-07.md`](../../../ideas/automod-spam-detection-gaps-2026-07-07.md).
> Remaining gaps are best-in-class
> breadth (word-blacklist is cleanup's; no attachment/embed rules; no rule-stats view) and the live ✔.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — spam/cross-channel-spam/duplicate/invite/caps/mention detection
      (`automod_service.py` `find_invite`/`caps_ratio`/`mention_count`/`evaluate`), exemptions
      short-circuit, fail-open on detector/config fault (`listener.py`); SpamTracker/DuplicateTracker
      windows reset on restart by design (ADR-002).
- [ ] **Every best-in-class sub-option** — ⚠ **partial.** Four owner-approved rule types ship; **missing**
      vs Carl-bot/MEE6/Dyno: word blacklist (owned by `cleanup`), attachment/embed rules, link filters
      beyond invites, per-rule action escalation (escalation is moderation's shared ladder). → punch #1.
- [x] **Failure modes honest** — config/detector/delete faults are caught + logged; the message passes
      (fail-open); DM messages are a no-op.
- [x] **Idempotent** — pipeline short-circuits a deleted message; verdict is a pure threshold compare.

### B. Reachability & UI
- [x] **A command panel exists** — `!automod` renders the effective-policy embed (rules + thresholds +
      exemptions); `manage_guild`-gated.
- [x] **Reachable every natural way** — `!automod` entry point + `build_help_menu_view` hook +
      Moderation-hub child (`parent_hub: moderation`); config via `!settings → Automod`.
- [N/A] **Integrated into Setup** — no dedicated wizard step (defaults-off; tuned via `!settings`).
      Acceptable waiver.
- [x] **Return navigation** — the Help hook returns a HubView (back to Moderation); status view is a leaf.
- [x] **In-place, not spammy** — config edits go through `!settings`; no ambient spam.

### C. Convenience
- [x] **Low-step + presets** — numeric-preset widgets on thresholds (`input_hint="numeric_presets"`).
- [x] **Sensible defaults** — every rule defaults OFF (`automod_config.py`); fresh guild unaffected.
- [x] **Clear feedback** — `!automod` policy embed; mod-log attribution per action
      (`auto_delete:automod.<rule>`).

### D. Authority & safety
- [x] **Authority re-checked at callback** — every SettingSpec `capability_required =
      moderation.settings.configure`; `!automod` is `manage_guild`-gated.
- [x] **All writes through the audited seam** — deletes via `moderation_service.auto_delete`, warns via
      `moderation_service.warn` (system actor) → `mod_logs` + `audit.action_recorded` + `EVT_MOD_ACTION`;
      advisory `automod.rule_triggered` best-effort.
- [N/A] **Provisioning pipeline** — no resource creation; config is guild KV.
- [x] **Reuses governance** — shares moderation's escalation ladder + capability; no second allowlist.

### E. Configuration
- [x] **Settings pipeline** — `AUTOMOD_CONFIG_SCHEMA` (SubsystemSchema) registered at cog load; scalars
      via the standard `SettingsMutationPipeline` dispatch.
- [x] **config-input widgets** — 15 SettingSpecs (master + 6 toggles + 6 thresholds + 2 exempt CSV),
      validators tied to the config defaults (pinned by a defaults-parity test).
- [x] **Everything configurable that should be** — master + per-rule toggles + thresholds + exempt lists;
      fixed by design: pipeline order, prefixes, spam window.

### F. Wiring & discoverability
- [x] **Registry** — key `automod`, `category: moderation`, `visibility_tier: administrator`,
      `parent_hub: moderation`, entry `automod`, capability `automod.settings.configure`.
- [x] **Discoverable in Help** — `build_help_menu_view` hook; pipeline stage registered at cog load.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_automod_service.py` (detectors, SpamTracker + DuplicateTracker windows,
      cross-channel/duplicate rule tripping incl. the "different messages never trip duplicate" case,
      evaluate ordering + exemptions); `test_automod_config.py` (typed load + tolerant CSV).
- [x] **Authority tests** — `test_automod_schemas.py` (every spec requires the configure capability;
      all defaults OFF).
- [x] **Mutation-seam tests** — `test_automod_listener.py` (verdict → delete+warn+events; disabled no-op;
      fail-open; DM no-op).
- [ ] **Live walkthrough recorded** — pending → punch #2.
- [ ] **Owner ✔** — pending → punch #3.

## Punch-list (clear these to certify)
1. **Best-in-class breadth** *(offline/owner, deepening)* — consider attachment/embed rules, broader link
   filtering, and per-guild rule presets (community/gaming/professional). Word blacklist stays cleanup's;
   escalation stays moderation's (no second ladder).
2. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + trigger each rule (spam/invite/caps/
   mention), confirm delete + warn + mod-log, with screenshots; check false-positive rate.
3. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."
4. **Rule-stats view** *(offline, deepening, optional)* — per-rule trigger counts to help tune thresholds.
5. ✅ **Cross-channel spam keying** *(owner-raised + SHIPPED 2026-07-07)* — `SpamTracker.
   record_and_count_any_channel` adds a guild+user-only bucket (reusing the same sliding-window
   mechanics via a sentinel channel key) alongside the existing per-channel one; new
   `automod.cross_channel_spam` rule, `cross_channel_spam_enabled`/`cross_channel_spam_count`
   settings. Detail: [`automod-spam-detection-gaps-2026-07-07.md`](../../../ideas/automod-spam-detection-gaps-2026-07-07.md).
6. ✅ **Content-duplicate detection** *(owner-raised + SHIPPED 2026-07-07)* — new `DuplicateTracker`
   (guild+user-keyed sliding window of normalized content) and `automod.duplicate` rule, through the
   same audited `moderation_service` seam as every other rule; `duplicate_enabled`/`duplicate_count`
   settings. Same doc as #5.

## Evidence
- **Tests:** `tests/unit/services/test_automod_service.py` · `…/test_automod_config.py` ·
  `tests/unit/cogs/test_automod_listener.py` · `…/test_automod_schemas.py` (extended 2026-07-07 with
  cross-channel-spam + duplicate-content coverage, incl. the "burst of different messages must not
  trip duplicate" negative case)
- **Walkthrough:** pending (punch #2)
- **Owner sign-off:** pending (punch #3)

## Verdict
Automod is a **structurally complete, fully-audited** filter layer — six rule types on the message
pipeline, exemptions, fail-open discipline, and actions through the shared moderation seam + escalation
ladder, all defaults-OFF and config-driven. It is **not yet `✔ certified`**: the gaps are
**best-in-class breadth** (#1/#4 — deliberately scoped) and the owner walkthrough/sign-off (#2/#3).
No safety/audit/dead-end issues found.
