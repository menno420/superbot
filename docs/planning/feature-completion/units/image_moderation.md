# Image moderation — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `image_moderation` · **Type:** server-fn · **Family:** moderation
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/image_moderation_cog.py` (`!imagemod` status + Help hook + pipeline stage) ·
> `disbot/cogs/image_moderation/listener.py` (the stage body) · `disbot/cogs/image_moderation/schemas.py`
> (8 SettingSpecs) · `disbot/services/image_moderation_service.py` (scoring/verdict) ·
> `disbot/services/image_moderation_config.py` · `disbot/core/runtime/ai/` OpenAI
> `omni-moderation-latest` provider · `disbot/utils/settings_keys/image_moderation.py` · folio
> `docs/subsystems/server-management.md`

> Assessed during the completion-first arc (Q-0209). Image moderation scans posted images via OpenAI's
> free `omni-moderation-latest` endpoint against four owner-named buckets (sexual / violence / harassment
> / hate), each toggleable, with a configurable threshold (50–100%, default 80) and role/channel
> exemptions checked **before** any API call (cost discipline). Flagged images route the delete + warn
> through the audited `moderation_service` seam (system actor). Defaults are all-OFF (no scanning, no API
> cost on a fresh guild); the provider fails open (missing key / SDK / network → image allowed, logged).
> **Env-gated** — degraded in the sandbox (no `OPENAI_API_KEY`). Gaps are best-in-class action breadth
> (no timeout-only action) and the live ✔ on real Discord.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — detect (`image_moderation_service.evaluate_scores`) + act
      (`listener._act`: `auto_delete` + `warn` + `EVT_IMAGE_MODERATION_FLAGGED`); awkward cases handled
      (provider/classify/config fault → fail-open; exempt channel/role short-circuits before the API).
- [ ] **Every best-in-class sub-option** — ⚠ **partial.** Per-bucket toggles + threshold + exemptions
      ship; action is delete+warn (warn carries moderation's escalation). **Missing** an explicit
      timeout-only / log-only action mode. → punch #1.
- [x] **Failure modes honest** — `ProviderUnavailableError`/classify/config faults fail open + log; the
      message passes; privacy disclosed in the setting hints (URL-only sent to OpenAI).
- [x] **Idempotent** — fresh policy load per message; pure threshold verdict; deleted message
      short-circuits downstream stages.

### B. Reachability & UI
- [x] **A command panel exists** — `!imagemod` renders the policy embed (master + per-bucket flags +
      threshold + exemptions); `manage_guild`-gated.
- [x] **Reachable every natural way** — `!imagemod` entry point + `build_help_menu_view` hook +
      Moderation-hub child; config via `!settings → Image moderation`.
- [N/A] **Integrated into Setup** — no dedicated wizard step (defaults-off; tuned via `!settings`).
- [x] **Return navigation** — Help hook returns a HubView; status view points to `!settings`.
- [x] **In-place, not spammy** — config via `!settings`; scanning is ambient on the pipeline.

### C. Convenience
- [x] **Defaults** — master + all buckets OFF, threshold 80, exemptions empty (`…_config.py`); fresh
      guild does zero scanning / zero API spend.
- [x] **Clear feedback** — `!imagemod` policy embed; per-setting plain-English hints incl. the privacy
      disclosure; all fail-open paths log at WARNING with context.
- [x] **Preset** — `threshold_percent` uses a numeric-presets widget (70/80/90).

### D. Authority & safety
- [x] **Authority re-checked at callback** — `!imagemod` `manage_guild`-gated; every SettingSpec
      `capability_required = moderation.settings.configure`.
- [x] **All writes through the audited seam** — `moderation_service.auto_delete`
      (`rule=image_moderation.<category>`) + `moderation_service.warn` (system actor) → moderation audit;
      advisory `image_moderation.flagged` event.
- [N/A] **Provisioning pipeline** — no resource creation; config is guild KV.
- [x] **Reuses governance** — administrator tier + moderation capability; no second allowlist.

### E. Configuration
- [x] **Settings pipeline** — `register_schemas()` at cog load; `load_policy` composes typed values via
      `settings_resolution` with default fallback.
- [x] **config-input widgets** — 8 SettingSpecs (master + 4 bucket toggles + threshold + 2 exempt CSV),
      validators (bool / 50–100 threshold / id-CSV), defaults pinned to config by a parity test.
- [x] **Everything configurable that should be** — master, per-bucket, threshold, exemptions.

### F. Wiring & discoverability
- [x] **Registry** — key `image_moderation`, `category: moderation`, `visibility_tier: administrator`,
      `parent_hub: moderation`, entry `imagemod`, capability `image_moderation.settings.configure`.
- [x] **Discoverable in Help** — `build_help_menu_view` hook; pipeline stage registered at cog load.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_image_moderation_service.py` (attachment detection, bucket scoring,
      verdict/threshold); `test_image_moderation_config.py` (typed load + defaults).
- [x] **Authority tests** — `test_image_moderation_schemas.py` (uniform capability gating; all flags OFF;
      validator bounds).
- [x] **Mutation-seam tests** — `test_image_moderation_listener.py` (flagged → delete+warn+emit;
      disabled/no-image/exempt no-op; provider/classify/config fault fail-open; DM no-op);
      `test_openai_moderation.py` (score extraction, classify, `ProviderUnavailableError`).
- [ ] **Live walkthrough recorded** — pending → punch #2 (needs `OPENAI_API_KEY` / live bot).
- [ ] **Owner ✔** — pending → punch #3.

## Punch-list (clear these to certify)
1. **Action-mode breadth** *(offline/owner, deepening)* — add an explicit log-only / timeout action mode
   (today: delete + warn, with warn carrying moderation's escalation).
2. **Live walkthrough** *(needs-live-bot / owner)* — `/verify-bot` boot with a key, post a flagged image,
   confirm delete + warn + audit row + the privacy disclosure render, with screenshots.
3. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."
4. **Threshold-rationale doc** *(offline, minor)* — record the 80%-default false-positive rationale in
   the folio (today only a code comment).

## Evidence
- **Tests:** `tests/unit/services/test_image_moderation_service.py` · `…/test_image_moderation_config.py` ·
  `tests/unit/cogs/test_image_moderation_listener.py` · `…/test_image_moderation_schemas.py` ·
  `tests/unit/runtime/ai/test_openai_moderation.py` (~554 lines total)
- **Walkthrough:** pending (punch #2)
- **Owner sign-off:** pending (punch #3)

## Verdict
Image moderation is a **structurally complete, fully-audited, fail-open** unit — OpenAI-backed NSFW
detection across four toggleable buckets with a tunable threshold and pre-API exemptions, acting through
the shared moderation seam, defaults-OFF, with ~554 lines of tests. It is **not yet `✔ certified`**: the
gaps are **action-mode breadth** (#1), the **env-gated live walkthrough** (#2, needs an API key + live
bot), and the owner sign-off (#3). No safety/audit/dead-end issues found.
