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

**37 variables** — 3 required · 34 optional.

## Required (read without a default — the deploy must set these)

| Variable | Layers | Usages |
|---|---|---|
| `DATABASE_URL` | utils | `disbot/utils/db/pool.py:41` |
| `DISCORD_BOT_TOKEN_PRODUCTION` | config | `disbot/config.py:19` |
| `YOUTUBE_API_KEY` | services | `disbot/services/diagnostic_embeds.py:1265`<br>`disbot/services/youtube_fetch_service.py:22` |

## Optional (a default is always supplied)

| Variable | Layers | Usages |
|---|---|---|
| `AI_DEFAULT_PROVIDER` | config, core | `disbot/config.py:180` *(default)*<br>`disbot/core/runtime/ai/feature_flags.py:66` *(default)* |
| `AI_ENABLED` | config | `disbot/config.py:179` *(default)* |
| `AI_FALLBACK_PROVIDER` | core | `disbot/core/runtime/ai/routing.py:128` *(default)* |
| `ANTHROPIC_API_KEY` | config, core | `disbot/config.py:163` *(default)*<br>`disbot/core/runtime/ai/providers/anthropic_provider.py:93` *(default)* |
| `AUTOMATION_SCHEDULER_ENABLED` | services | `disbot/services/automation_scheduler.py:397` *(default)* |
| `BOT_OWNER_USER_ID` | config | `disbot/config.py:40` *(default)* |
| `BOT_PREFIX` | config | `disbot/config.py:28` *(default)* |
| `BTD6_CONFIDENCE_THRESHOLD` | cogs | `disbot/cogs/btd6/stage.py:94` *(default)* |
| `BTD6_COOLDOWN_SECONDS` | cogs | `disbot/cogs/btd6/stage.py:102` *(default)* |
| `BTD6_DATA_BACKEND` | config | `disbot/config.py:206` *(default)* |
| `BTD6_DATA_BASE_URL` | config | `disbot/config.py:209` *(default)* |
| `BTD6_DATA_CACHE_DIR` | config | `disbot/config.py:212` *(default)* |
| `BTD6_INGESTION_DEFAULT_INTERVAL_S` | services | `disbot/services/btd6_ingestion_supervisor.py:35` *(default)* |
| `BTD6_INGESTION_ENABLED` | services | `disbot/services/btd6_ingestion_supervisor.py:32` *(default)* |
| `BTD6_INGESTION_STARTUP_DELAY_S` | services | `disbot/services/btd6_ingestion_supervisor.py:34` *(default)* |
| `BTD6_PASSIVE_CHANNELS` | cogs | `disbot/cogs/btd6/stage.py:80` *(default)* |
| `CLAUDE_ROUTINE_BETA` | cogs | `disbot/cogs/hermes_cog.py:51` *(default)* |
| `CLAUDE_ROUTINE_FIRE_URL` | cogs | `disbot/cogs/hermes_cog.py:49` *(default)* |
| `CLAUDE_ROUTINE_TOKEN` | cogs | `disbot/cogs/hermes_cog.py:50` *(default)* |
| `CLAUDE_ROUTINE_VERSION` | cogs | `disbot/cogs/hermes_cog.py:52` *(default)* |
| `CONTROL_API_TOKEN` | control_api | `disbot/control_api.py:111` *(default)* |
| `DISCORD_WEBHOOK_URL` | config | `disbot/config.py:105` *(default)* |
| `HEALTH_GROUPED_FINDINGS` | services | `disbot/services/health_snapshot_service.py:267` *(default)* |
| `HEALTH_HOST` | healthserver | `disbot/healthserver.py:70` *(default)* |
| `HEALTH_PORT` | healthserver | `disbot/healthserver.py:64` *(default)* |
| `IDENTITY_CONTRACT_STRICT` | bot1 | `disbot/bot1.py:175` *(default)* |
| `LOG_LEVEL` | config | `disbot/config.py:106` *(default)* |
| `OPENAI_API_KEY` | config, core, services | `disbot/config.py:162` *(default)*<br>`disbot/core/runtime/ai/providers/openai_moderation.py:68` *(default)*<br>`disbot/core/runtime/ai/providers/openai_provider.py:74` *(default)*<br>`disbot/services/setup_ai_advisor.py:175` *(default)*<br>`disbot/services/setup_ai_advisor.py:406` *(default)* |
| `PARAGON_API_BASE_URL` | config, services | `disbot/config.py:189` *(default)*<br>`disbot/services/paragon_service.py:49` *(default)* |
| `PARAGON_API_KEY` | config, services | `disbot/config.py:193` *(default)*<br>`disbot/services/paragon_service.py:50` *(default)* |
| `RAILWAY_GIT_COMMIT_SHA` | core | `disbot/core/runtime/command_manifest.py:243` *(default)* |
| `SETUP_ADVISOR_OPENAI_MODEL` | config, services | `disbot/config.py:161` *(default)*<br>`disbot/services/setup_ai_advisor.py:173` *(default)* |
| `SETUP_ADVISOR_PROVIDER` | config, core, services | `disbot/config.py:160` *(default)*<br>`disbot/core/runtime/ai/feature_flags.py:129` *(default)*<br>`disbot/services/setup_ai_advisor.py:393` *(default)* |
| `STRICT_DISABLED` | bot1 | `disbot/bot1.py:172` *(default)* |
