# Security — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `security` · **Type:** server-fn · **Family:** moderation
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/security_cog.py` (`!security` status + Help hook + `on_member_join` listener) ·
> `disbot/cogs/security/schemas.py` (11 SettingSpecs) · `disbot/services/security_service.py`
> (RaidTracker + account-age detection + orchestration) · `disbot/services/security_config.py`
> (read model + guardrail clamps) · `disbot/utils/settings_keys/security.py` · folio
> `docs/subsystems/server-management.md`

> Assessed during the completion-first arc (Q-0209). Security is the **automated join-screening** layer,
> the two owner-approved tiers (Q-0111): **Tier 1 raid detection** (per-guild sliding join window →
> deduplicated staff alert + optional auto-restored slowmode) and **Tier 2 account-age filter** (young
> account → alert or kick). The two declined tiers (alt-detection / VPN blocking) own no code by design.
> Pure detection (no external calls, no PII — account age from the public snowflake), fail-open so a
> fault never blocks a join, both tiers independent. Kicks route through the audited `moderation_service`;
> every numeric setting is clamped to guardrails at read so no configuration can produce an absurd
> detector. Defaults all-OFF (fresh guild unaffected). Runtime state is process-local by design (ADR-002).
> Gaps are the live walkthrough + a couple of explicit edge-case tests.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — RaidTracker sliding window + `account_age_days`
      (`security_service.py`); raid tier dedups per guild (alerts/slowmodes once per lockdown), age tier
      alert-or-kick; both tiers independent; orchestration fail-open (join always completes).
- [x] **Every best-in-class sub-option** — the two owner-approved tiers match Wick/Carl-bot's raid-gate +
      account-age gate; alt/VPN tiers deliberately out of scope (Q-0111). Honest, not silently absent.
- [x] **Failure modes honest** — config/slowmode/detector faults logged + swallowed (join proceeds);
      missing join timestamp → not-young (fail-open).
- [x] **Idempotent** — raid dedup per guild (re-entry during a lockdown re-counts but does not re-alert /
      re-apply slowmode); window resets on restart (conservative, ADR-002).

### B. Reachability & UI
- [x] **A command panel exists** — `!security` renders the effective-policy embed (master + both tiers +
      thresholds, 🟢/⚫ flags); administrator-gated.
- [x] **Reachable every natural way** — `!security` entry point + `build_help_menu_view` hook +
      Moderation-hub child (`parent_hub: moderation`); config via `!settings → Security`.
- [N/A] **Integrated into Setup** — no dedicated wizard step (defaults-off; tuned via `!settings`).
- [x] **Return navigation** — Help hook returns a HubView; status view is a leaf.
- [x] **In-place, not spammy** — alerts are color-coded one-shot staff posts (deduplicated); config via
      `!settings`.

### C. Convenience
- [x] **Defaults + presets** — master + both tier flags default OFF; sane starting thresholds (raid 10/60s;
      age 7 days), all guardrail-clamped (`security_config.py`).
- [x] **Clear feedback** — `!security` policy embed; staff alerts carry the reason + suggested action.
- [x] **No needless steps** — single status command; config is the standard widget.

### D. Authority & safety
- [x] **Authority re-checked at callback** — `!security` administrator-gated; every SettingSpec
      `capability_required = security.settings.configure`.
- [x] **All writes through the audited seam** — kicks via `moderation_service.kick` → `_record_action` →
      `emit_audit_action`; raid/age alerts are advisory fire-and-forget bus events
      (`EVT_RAID_DETECTED`/`EVT_ACCOUNT_FLAGGED`).
- [N/A] **Provisioning pipeline** — no resource creation (slowmode toggles an existing channel; config is
      guild KV, no migration).
- [x] **Reuses governance** — administrator tier + security capability; numeric guardrail clamps prevent
      a hostile/fat-fingered detector.

### E. Configuration
- [x] **Settings pipeline** — `SECURITY_CONFIG_SCHEMA` registered at cog load; `load_policy` reads
      settings_resolution + clamps every numeric to guardrails.
- [x] **config-input widgets** — 11 SettingSpecs (master + 6 raid + 3 age + alert channel) with
      per-spec validators; `input_hint="channel"` on the channel pointers; defaults pinned to config.
- [x] **Everything configurable that should be** — master, both tiers, all thresholds, the action
      (alert/kick), the alert channel; nothing security-sensitive editable below the administrator floor.

### F. Wiring & discoverability
- [x] **Registry** — key `security`, `category: moderation`, `visibility_tier: administrator`,
      `parent_hub: moderation`, entry `security`, capability `security.settings.configure`.
- [x] **Discoverable in Help** — `build_help_menu_view` hook; the `on_member_join` listener registered
      at cog load.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_security_service.py` (window mechanics, age math, raid dedup, the
      lock-clear regression, alert-only vs kick, fail-open) — 15 cases.
- [x] **Authority tests** — `test_security_config.py` (master/tier gating, guardrail clamp/coerce of
      hostile values) — 8 cases.
- [x] **Mutation-seam tests** — `test_security_schemas.py` (registration idempotent, defaults parity,
      every spec requires the capability, channel input-hints, action enum) — 9 cases.
- [ ] **Live walkthrough recorded** — pending → punch #2.
- [ ] **Owner ✔** — pending → punch #3.

## Punch-list (clear these to certify)
1. **Edge-case tests** *(offline, minor)* — explicit tests for slowmode-restore-on-error and the
   lockdown-flag dedup when the slowmode channel resolves to `None` (behavior is correct + implicitly
   covered today).
2. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot, simulate a join burst (raid alert +
   slowmode apply/restore) and a young-account join (alert + kick → audit row), with screenshots.
3. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_security_service.py` · `…/test_security_config.py` ·
  `tests/unit/cogs/test_security_schemas.py` (~32 cases total)
- **Walkthrough:** pending (punch #2)
- **Owner sign-off:** pending (punch #3)

## Verdict
Security is a **structurally complete, fully-audited, fail-open** join-screening unit — the two
owner-approved tiers (raid + account-age) with deduplicated alerts, audited kicks, and guardrail-clamped
configuration, defaults-OFF, with ~32 test cases. It is **not yet `✔ certified`**: the gaps are two
explicit edge-case tests (#1) and the owner walkthrough/sign-off (#2/#3). The declined alt/VPN tiers are
out of scope by design (Q-0111). No safety/audit/dead-end issues found.
