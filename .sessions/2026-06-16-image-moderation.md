# Session — Image moderation (Q-0108) — the safety-community family's last buildable slice

> **Status:** `complete`

## What I did

Dispatch run, empty work order → took the live ▶ NEXT plan-first slice. Verified the `ready`
decade-queue is consumed (faucet/sink #937, myprofile A/B #938/#940) and that **automod, server
logging, welcome** are already shipped — so the one remaining **buildable** safety-community
family slice (per `docs/planning/safety-community-family-plan-2026-06-13.md` §4) is **image
moderation (Q-0108)**, owner-APPROVED (OpenAI `omni-moderation-latest` only; paid tiers declined;
threshold ≥0.80). Built it end-to-end, mirroring the automod shape exactly.

## What shipped (PR #941 — `needs-hermes-review`, NOT self-merged)

New hub-less `image_moderation` subsystem — **off by default · fail-open · no migration · only
the image URL leaves the bot**:

- **`services/image_moderation_service.py`** — **pure** decision layer (no I/O, no `openai`):
  four owner-named buckets (sexual · violence · harassment · hate), each mapping to the raw
  `omni-moderation` category keys (worst-score wins); `evaluate_scores` threshold logic +
  `image_attachment_urls` detection.
- **`services/image_moderation_config.py`** — frozen `ImageModerationPolicy` + `load_policy`
  (mirrors `automod_config`; reuses its tolerant `parse_id_csv` exempt-list parser).
- **`core/runtime/ai/providers/openai_moderation.py`** — the **only** new module importing the
  `openai` SDK (the `test_provider_sdk_imports_only_in_providers` chokepoint); `classify_image`
  → category-score dict; no key/SDK ⇒ `ProviderUnavailableError` ⇒ the listener fails open
  (the live call is **not** exercised in the sandbox — degrades like the AI cog).
- **`cogs/image_moderation/`** (`listener.py` + `schemas.py`) + **`cogs/image_moderation_cog.py`**
  — the `ImageModerationStage` (auto-mod tier, **order 25** — after the cheap text rules, before
  rewards), acting through `moderation_service.auto_delete` + `warn` (one audit authority),
  emitting the advisory `image_moderation.flagged`. `!imagemod` shows the policy.
- Pinned-surface cascade handled: `utils/settings_keys/image_moderation.py` + `__init__`
  re-export · `events_catalogue` · `config.INITIAL_EXTENSIONS` · `subsystem_registry` (moderation
  child) · `hub_registry` moderation children + its test · `docs/ownership.md` ·
  `docs/help-command-surface-map.md` (+ count preamble 33→34 subs / 43→44 exts) ·
  `docs/setup-platform/settings-customization-command-map.md`.
- **Drive-by fix:** the canonical stage-order table in `message_pipeline.py` omitted automod=5;
  added automod=5 + image_mod=25.

**Verification:** `python3.10 scripts/check_quality.py --full` GREEN (9974 passed, +33 new);
`check_architecture --mode strict` 0 errors; mypy/black/isort/ruff/check_docs all pass; cog +
stage import-register cleanly (order 25, distinct). Tests: `test_image_moderation_service.py`
(buckets/threshold/order/attachment-filter) · `test_image_moderation_config.py` (load_policy +
exemptions) · `test_image_moderation_schemas.py` (defaults-alignment/off-by-default/validators) ·
`test_image_moderation_listener.py` (disabled/no-image/exempt/provider-unavailable/classify-error
fail-open + flagged deletes+warns+emits) · `test_openai_moderation.py` (score extraction + URL-only
payload + no-key ProviderUnavailableError).

## Why needs-hermes-review (not self-merged)

A complete new subsystem **and** a new external-egress path (uploaded images → OpenAI). Even
off-by-default + fail-open, a capability that sends user content externally warrants a human glance
before it can ever go live — and the sibling **#929** (security tiers, same family) carries the
same `needs-hermes-review` carve-out (Q-0117). Auto-merge disarmed; awaiting Hermes/owner merge.

## Handoff / next

- **PR #941** is green-but-for-the-card, `needs-hermes-review`, awaiting human merge. Once merged,
  add a `Recently shipped` ledger entry (the convention is merged-only).
- **The safety-community family is now buildable-complete** (automod ✅ · server logging ✅ ·
  welcome ✅/phase-2 ✅ · image moderation ✅ this PR · security tiers 🟡 #929 in review). The
  remaining family items are `plan-first` (NL event scheduler Q-0112 — own AI-cost design first)
  or owner-led.
- **Next ▶ buildable = the remaining plan-first slices** (current-state ▶ NEXT): image-mod is now
  done, so the live trio is **NL event scheduler (Q-0112, plan-first, must meter under Q-0082)** ·
  the **AI §7 next workflow family** (post-prod-check) · the **Hermes bug-triage `gh issue create`
  write (Q-0121)**. BUG-0009 slice 3 (newest-towers) stays `data`-gated; BUG-0011 (Hermes gateway
  crash-loop) stays OPEN/creds-gated.
- **Follow-up worth a slice (see the Q-0089 idea below):** image-mod makes one OpenAI call per
  image with **no cost accounting** — it should be metered under the Q-0082 spend ceiling, the
  same gate Q-0112 carries. Captured as an idea, not built (kept this PR focused).

## 💡 Session idea (Q-0089)

**Meter image moderation under the Q-0082 AI spend ceiling.** Right now `image_moderation` calls
OpenAI's moderation endpoint once per uploaded image when enabled, with no token/cost accounting —
the same un-metered-external-call gap the NL event scheduler (Q-0112) was explicitly told to close.
A high-traffic image channel could quietly run up calls. The fix is small and reuses existing
machinery: route the `openai_moderation` call through (or alongside) the AI cost-meter so it counts
against the per-guild ceiling, and skip the scan (fail-open) when the ceiling is hit. Recorded in
`docs/ideas/` for grooming; a natural next-band slice once the spend-meter seam is confirmed.

## ⟲ Previous-session review (Q-0102)

**Previous session:** `2026-06-15-hermes-soul-guard.md` (Hermes VPS context-fix script + SOUL size
guard, PR #914). **Did well:** it correctly resisted shipping *manual steps* and instead built an
idempotent, reversible, `--dry-run`-able operator script — exactly the "make it executable, not a
checklist" discipline the project values; and it honestly flagged that the `hermes config set`
calls couldn't be exercised in-container (caveat over false confidence). **Could improve:** it left
BUG-0011 (gateway crash-loop) OPEN without a concrete next experiment named beyond "clean foreground
repro" — a session that touches the gateway could have at least scripted that repro. **System
improvement it surfaces:** the recurring "this can't be verified in the sandbox" caveat (Hermes
config there, the OpenAI call here) is a *pattern* — several features now ship with a real, gated
external dependency that no agent session can exercise. Worth a small **`docs/operations/`
"sandbox-ungated capabilities" register** listing each such surface (image-mod OpenAI call, Hermes
`config set`, Railway token, live AI eval battery) + the owner action that verifies it — so the
"owner must check this live" debt is tracked in one place instead of scattered across session logs.

## Doc audit (Q-0104)

`check_docs --strict` ✓ (part of `check_quality --full`). New owner decision: none (Q-0108 was
already recorded; this is its execution). New docs reachable: the subsystem is documented in
`ownership.md` + both surface maps; no new standalone doc needed. The `current-state.md` ▶ NEXT
pointer is updated to mark image-mod in-flight (#941). The merged-PR ledger entry is deferred to
post-merge per the merged-only convention (PR is `needs-hermes-review`, not yet merged).
