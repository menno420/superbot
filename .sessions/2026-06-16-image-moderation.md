# Session — Image moderation (Q-0108) — the safety-community family's last buildable slice

> **Status:** `in-progress`

## What I'm about to do (born-red card, Q-0133)

Dispatch run, empty work order → take the live ▶ NEXT plan-first slice. The `ready`
decade-queue is consumed (faucet/sink #937, myprofile A/B #938/#940); the safety-community
family has automod ✅, server logging ✅, welcome ✅, security tiers 🟡 in-flight (#929). The
one remaining **buildable** family slice is **image moderation (Q-0108)** — owner-APPROVED
(OpenAI `omni-moderation-latest` only, free, existing key, threshold ≥0.80), turn-key design
in `docs/planning/safety-community-family-plan-2026-06-13.md` §4.

Building it mirrors the automod shape exactly:
- `services/image_moderation_service.py` — **pure** decision layer (no I/O, no `openai`):
  category-score → verdict threshold logic + image-attachment detection.
- `services/image_moderation_config.py` — frozen `ImageModerationPolicy` + `load_policy`.
- `core/runtime/ai/providers/openai_moderation.py` — the **only** new module importing the
  `openai` SDK (the invariant chokepoint); `classify_image(url)` → category-score dict;
  `ProviderUnavailableError` (no key) ⇒ the listener fails open.
- `cogs/image_moderation/` (`listener.py` + `schemas.py`) + `cogs/image_moderation_cog.py`
  — the `ImageModerationStage` (auto-mod tier, order 25 — after the cheap text rules, before
  rewards), acts through `moderation_service.auto_delete` + `warn`, emits
  `image_moderation.flagged`.
- `utils/settings_keys/image_moderation.py` + `__init__` re-export · `events_catalogue` ·
  `config.INITIAL_EXTENSIONS` · `docs/ownership.md`.

Off by default · fail-open · only the image URL leaves the bot (privacy disclosed in the
setting hint + ownership doc). No migration. The live OpenAI call is **not** exercised in this
session (no key in the sandbox — degrades exactly like the AI cog); the pure decision layer is
fully unit-tested.

I will flip this card to `complete` as the deliberate final step.
