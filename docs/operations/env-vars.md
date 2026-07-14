# Environment variables — usage reference

> **Status:** `living-ledger` — generated inventory of every environment
> variable read by the bot source. **Source + the scanner win over this file.**

<!-- GENERATED FILE — do not edit by hand. Refresh with:
       python3.10 scripts/scan_env_usage.py --write-doc -->

This is the in-repo, human-readable form of the dashboard `/env` usage map
(`scripts/scan_env_usage.py`). It lists every variable the bot **reads**, where
it reads it, and whether it is **required** (read without a default anywhere) or
**optional** (a default is always supplied). It shows **names and code locations
only — never a value**; the values live in Railway service variables
(see [`production-deployment.md`](production-deployment.md)).

**42 variables** — 3 required · 39 optional.

## Required (read without a default — the deploy must set these)

| Variable | Layers | Usages |
|---|---|---|
| `DATABASE_URL` | utils | `disbot/utils/db/pool.py:41` |
| `DISCORD_BOT_TOKEN_PRODUCTION` | config | `disbot/config.py:19` |
| `YOUTUBE_API_KEY` | services | `disbot/services/diagnostic_embeds.py:1417`<br>`disbot/services/youtube_fetch_service.py:22` |

## Optional (a default is always supplied)

| Variable | Layers | Usages |
|---|---|---|
| `AI_DEFAULT_PROVIDER` | config, core | `disbot/config.py:236` *(default)*<br>`disbot/core/runtime/ai/feature_flags.py:66` *(default)* |
| `AI_ENABLED` | config | `disbot/config.py:235` *(default)* |
| `AI_FALLBACK_PROVIDER` | core | `disbot/core/runtime/ai/routing.py:128` *(default)* |
| `ANTHROPIC_API_KEY` | config, core | `disbot/config.py:219` *(default)*<br>`disbot/core/runtime/ai/providers/anthropic_provider.py:93` *(default)* |
| `AUTOMATION_SCHEDULER_ENABLED` | services | `disbot/services/automation_scheduler.py:396` *(default)* |
| `AUTO_SYNC_COMMANDS` | config | `disbot/config.py:282` *(default)* |
| `BOT_OWNER_USER_ID` | config | `disbot/config.py:40` *(default)* |
| `BOT_PREFIX` | config | `disbot/config.py:28` *(default)* |
| `BTD6_AUTO_SEED` | config | `disbot/config.py:274` *(default)* |
| `BTD6_CONFIDENCE_THRESHOLD` | cogs | `disbot/cogs/btd6/stage.py:94` *(default)* |
| `BTD6_COOLDOWN_SECONDS` | cogs | `disbot/cogs/btd6/stage.py:102` *(default)* |
| `BTD6_DATA_BACKEND` | config | `disbot/config.py:262` *(default)* |
| `BTD6_DATA_BASE_URL` | config | `disbot/config.py:265` *(default)* |
| `BTD6_DATA_CACHE_DIR` | config | `disbot/config.py:268` *(default)* |
| `BTD6_INGESTION_DEFAULT_INTERVAL_S` | services | `disbot/services/btd6_ingestion_supervisor.py:35` *(default)* |
| `BTD6_INGESTION_ENABLED` | services | `disbot/services/btd6_ingestion_supervisor.py:32` *(default)* |
| `BTD6_INGESTION_STARTUP_DELAY_S` | services | `disbot/services/btd6_ingestion_supervisor.py:34` *(default)* |
| `BTD6_PASSIVE_CHANNELS` | cogs | `disbot/cogs/btd6/stage.py:80` *(default)* |
| `CLAUDE_ROUTINE_BETA` | cogs | `disbot/cogs/hermes_cog.py:52` *(default)* |
| `CLAUDE_ROUTINE_FIRE_URL` | cogs | `disbot/cogs/hermes_cog.py:50` *(default)* |
| `CLAUDE_ROUTINE_TOKEN` | cogs | `disbot/cogs/hermes_cog.py:51` *(default)* |
| `CLAUDE_ROUTINE_VERSION` | cogs | `disbot/cogs/hermes_cog.py:53` *(default)* |
| `CONTROL_API_TOKEN` | control_api | `disbot/control_api.py:111` *(default)* |
| `DISCORD_WEBHOOK_URL` | config | `disbot/config.py:181` *(default)* |
| `EXTRA_OWNER_USER_IDS` | config | `disbot/config.py:70` *(default)* |
| `HEALTH_GROUPED_FINDINGS` | services | `disbot/services/health_snapshot_service.py:268` *(default)* |
| `HEALTH_HOST` | healthserver | `disbot/healthserver.py:70` *(default)* |
| `HEALTH_PORT` | healthserver | `disbot/healthserver.py:64` *(default)* |
| `IDENTITY_CONTRACT_STRICT` | bot1 | `disbot/bot1.py:198` *(default)* |
| `LOG_LEVEL` | config | `disbot/config.py:182` *(default)* |
| `MINING_WRITE_GUILD_ALLOWLIST` | mining_write_api | `disbot/mining_write_api.py:139` *(default)* |
| `MINING_WRITE_SHARED_SECRET` | mining_write_api | `disbot/mining_write_api.py:127` *(default)* |
| `OPENAI_API_KEY` | config, core, services | `disbot/config.py:218` *(default)*<br>`disbot/core/runtime/ai/providers/openai_moderation.py:68` *(default)*<br>`disbot/core/runtime/ai/providers/openai_provider.py:74` *(default)*<br>`disbot/services/setup_ai_advisor.py:205` *(default)*<br>`disbot/services/setup_ai_advisor.py:485` *(default)* |
| `PARAGON_API_BASE_URL` | config, services | `disbot/config.py:245` *(default)*<br>`disbot/services/paragon_service.py:49` *(default)* |
| `PARAGON_API_KEY` | config, services | `disbot/config.py:249` *(default)*<br>`disbot/services/paragon_service.py:50` *(default)* |
| `RAILWAY_GIT_COMMIT_SHA` | core | `disbot/core/runtime/command_manifest.py:243` *(default)* |
| `SETUP_ADVISOR_OPENAI_MODEL` | config, services | `disbot/config.py:217` *(default)*<br>`disbot/services/setup_ai_advisor.py:203` *(default)* |
| `SETUP_ADVISOR_PROVIDER` | config, core, services | `disbot/config.py:216` *(default)*<br>`disbot/core/runtime/ai/feature_flags.py:129` *(default)*<br>`disbot/services/setup_ai_advisor.py:472` *(default)* |
| `STRICT_DISABLED` | bot1 | `disbot/bot1.py:195` *(default)* |

<!-- END GENERATED — everything below is hand-maintained (web-tier env vars the disbot scanner can't see); the scanner preserves it across --write-doc. -->

## Website tier (hand-maintained — not from the disbot scan)

These power the **two web services** (the public bot site + the dev dashboard) of the
website two-site split, not the bot worker, so the `disbot/` scanner above never emits
them. They are **dormant by default** — each service is a safe no-op until its var is set
(see [`botsite-deploy.md`](botsite-deploy.md) and the plan's §4.4 secret matrix). Names +
purpose only — never a value.

| Variable | Service(s) | Purpose / scope |
|---|---|---|
| `SUBMISSIONS_DB_DSN` | bot site (INSERT-only role) · dev site (full role) | The dashboard-owned submissions Postgres. The public site holds an **INSERT-only** role; the dev site holds the read/moderate role. Unset → `/submit` + moderation are dormant. |
| `SUBMISSIONS_IP_SALT` | bot site | Salt for the stored `source_ip_hash` (abuse forensics) — never the raw IP. Falls back to a per-process random salt when unset. |
| `GITHUB_ISSUE_MIRROR_TOKEN` | dev site only | Fine-grained PAT, repo-scoped to `menno420/superbot`, **Issues: Read & write only**. Mirrors an approved submission to one GitHub issue. **Never** on the public bot site. Unset → approve is disabled. |
| `BOT_OWNER_USER_ID` | dev site (also read by the bot) | Gates the owner-only moderation ring (`/admin/moderation`). Blank/garbage fails closed (matches nobody). |
| `DISCORD_OAUTH_CLIENT_ID` / `DISCORD_OAUTH_CLIENT_SECRET` / `DASHBOARD_SESSION_SECRET` | dev site (future gated manager) | Discord OAuth + signed-session secret for the per-guild control panel. Unset → the control zone is dormant. |
| `CONTROL_API_TOKEN` | dev site · bot worker | Bearer for the bot's private control API (per-guild writes, over the private network). Never on the public bot site. |
| `TURNSTILE_SECRET` / `HCAPTCHA_SECRET` *(optional)* | bot site | Reserved for a fast-follow `/submit` captcha (honeypot + rate-limit is the v1 default — plan §4.2 / §7 decision 6). Unset → no captcha. |
