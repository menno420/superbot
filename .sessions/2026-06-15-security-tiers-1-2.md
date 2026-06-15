# Session — security service tiers 1+2 (raid detection + account-age filter)

> **Status:** `in-progress`

**Dispatch:** continued from the live ▶ Next action = **security service tiers 1+2**
(band-#900 decade-queue slot 9, plan-first, Q-0111). Clean slate — zero open PRs.

**Scope (substantial → Q-0117 `needs-hermes-review`, NOT self-merged):** a new
hub-less `security` subsystem implementing the two APPROVED tiers only (tiers 3+4
alt-detection / VPN were DECLINED — kept absent). Mirrors the welcome/automod
shape from the safety-community family plan.

## What I'm building
- **Tier 1 — raid detection:** pure `RaidTracker` (per-guild sliding join window)
  + on-join orchestration → staff alert (always) + optional auto-slowmode on a
  configured channel (with auto-restore). No external API.
- **Tier 2 — account-age filter:** reject/quarantine/alert accounts younger than
  N days on join; actions route through `moderation_service` (kick) /
  `role_automation` (quarantine), never around them.
- Off by default · fail-open · privacy-free (self-contained, no external calls).
- Files: `utils/settings_keys/security.py` · `services/security_config.py` ·
  `services/security_service.py` · `cogs/security/schemas.py` ·
  `cogs/security_cog.py` · events_catalogue advisory events · INITIAL_EXTENSIONS ·
  the 6 new-subsystem cascade touch-points · family-plan §security · ownership doc
  · tests.

CI mirror (`check_quality --full` + `check_architecture --mode strict`) green
before flipping this card to `complete`.
