# 2026-06-27 — AI answer review-log (didn't-know + user corrections)

> **Status:** `complete`

## What this session did

Owner request: *"anytime the AI does not know an answer properly, or gets corrected
by a user, log the question and its answer someplace we can review it."*

Built a purpose-built, redacted, reviewable log for exactly those two cases. The
existing `ai_decision_audit` row classifies the "didn't-know" outcomes but
**deliberately stores no message text** (only metadata + the message id), so it
records *that* the bot didn't know, not *what* was asked/answered — and there was
no user-correction signal anywhere. This PR fills both gaps.

Two owner design calls (AskUserQuestion, 2026-06-27):
- **Correction detection** = react **and** reply.
- **Review surface** = a dedicated channel **and** a queryable log.

## Shipped (PR #1494)

- **Migration 100** `ai_review_log` — redacted question + answer (+ correction),
  `kind` ∈ {`unknown`, `correction`}, `reason_code`, retention `expires_at`,
  `reviewed` flag; three indexes. Guild teardown wired in `utils/db/ai.py`.
- **`utils/db/ai_review.py`** — CRUD primitives (record / query / mark_reviewed /
  count_unreviewed).
- **`services/ai_review_log_service.py`** — the chokepoint: `record_unknown` /
  `record_correction` (redact + cap text, persist, emit `ai.review_logged`),
  `query` / `mark_reviewed` / `count_unreviewed`, the typed `set_review_channel`
  pointer-writer, and the in-memory **answer registry** (`remember_answer` /
  `lookup_answer` / `already_flagged`) that lets a later 👎/reply recover the
  original Q&A. Every public call is fail-safe.
- **`utils/ai_correction_cues.py`** — pure `looks_like_correction()` heuristic.
- **`cogs/ai_review_cog.py`** — the 👎-reaction listener (`on_raw_reaction_add`),
  the **`AICorrectionStage`** message-pipeline stage (order 55) for the
  reply-correction half (a cog may not install its own `on_message`), the
  `ai.review_logged` → review-channel **poster**, and the `!aireview` staff
  command group (status / channel / off / list / resolve).
- **`natural_language_stage.py`** — best-effort `record_unknown` at the three
  "didn't-know" seams (errored, empty/no-route, BTD6 + Project Moon grounding
  floors — the floor stores the *rejected* ungrounded answer, which is the
  high-value "what it almost said") + `remember_answer` after a reply is sent.
- Wiring + guards: event catalogue (`ai.review_logged`), `AI_REVIEW_CHANNEL`
  settings key, cog registered in `config.py`, ownership.md (service + event +
  write-owner rows), ai-config-ownership.md (the new key), the `set_setting`
  allowlist, the reset-hook classification, the extension-roles overlay, the
  dashboard unregistered-cog allowlist, and the regenerated artifacts
  (crosswalk / env-vars / dashboard / site) + surface-doc counts.

Tests: 24 new (cues / service / cog-stage). Full CI mirror green (12,790 passed,
0 failed); `check_architecture --mode strict` 0 errors.

## Context delta (reflection interview)

- **Needed but not pointed to.** Orientation routes to the *binding contracts* but
  not to the **"adding a cog/extension touches these N registries+guards"** set. A
  new extension must be added to: `config.INITIAL_EXTENSIONS`,
  `architecture_rules/extension_roles.yaml` (overlay), `check_dashboard_data.py`'s
  `_UNREGISTERED_COG_ALLOWLIST` (if it owns no subsystem), the
  settings-customization command-map cog list, the help-surface-map counts, and
  the regenerated dashboard/crosswalk/env artifacts; a new *settings key* must
  appear in `ai-config-ownership.md`; a *message observer* must be a
  `message_pipeline` stage (no cog `on_message`); a *reset hook* must be
  classified in `tests/_isolation.py`; a *`set_setting`* must be allowlisted. I
  rediscovered every one of these by hitting its guard in the full suite (19
  failures, found one ~3.5-min run at a time).
- **Pointed to but didn't need.** CodeGraph / the SessionStart graph stats —
  targeted `grep` + `context_map.py` + reading source carried the whole build.
- **Discovered by hand.** The `btd6_version_announce` precedent: a per-guild
  channel *pointer* with no SettingSpec is written through its **own typed
  service** (allowlisted), not the SettingsMutationPipeline — that pattern is the
  clean fix for `AI_REVIEW_CHANNEL`, but it lives only in the allowlist comment.

## Decisions made alone (owner should be aware)

- **Storing redacted message text is a privacy-posture change** from the
  deliberately text-free `ai_decision_audit`. The owner explicitly asked to "log
  the question and its answer," so I store it — scrubbed through the same
  outbound redactor, capped at 2000 chars, with a 90-day `expires_at`.
- Retention is **metadata-only for now** — `expires_at` is written but no purge
  loop runs yet (rows persist until guild teardown). A `MediaMaintenanceCog`-style
  daily purge is the obvious follow-up.
- The correction **answer registry is in-memory + best-effort** (ADR-001/002): a
  correction to an answer the bot sent before its last restart is not enriched.
- `ai_review` classified **`shared_platform`** (sibling to `ai`), no subsystem.

## Flagged for maintainer (weak point / unverified)

- **No live Discord run.** End-to-end behaviour (a real 👎/reply → a channel post;
  a real grounding-floor → an `unknown` entry) is unverified on a live bot — the
  sandbox has no provider key (the standing AI gate). Verify on the next prod
  walk: set `!aireview channel #chan`, ask something it can't ground, then 👎 /
  reply-correct a real answer.
- The reply heuristic (`looks_like_correction`) is conservative but will have
  some false +/− in real chat; the registry-gate (only known AI answers) keeps
  noise low.

## 💡 Session idea (Q-0089)

**A `scripts/check_new_extension.py` (or a one-page "new-extension ripple"
checklist).** Given a cog added to `INITIAL_EXTENSIONS`, it would verify/print
every registry + allowlist + doc + generated artifact that the new extension must
touch (overlay role, dashboard allowlist, the two surface docs, the regenerators
to re-run; and for a new settings key / message observer / reset hook / set_setting,
the matching guard). This session hit those guards one full-suite-run at a time —
a single upfront list collapses that loop. Genuinely wanted; I just lived the pain.
(Dedup-checked `docs/ideas/` — closest is the extension-crosswalk tooling, which
checks *taxonomy*, not the full add-a-cog ripple.) Filed below as the friction guard.

## ⟲ Previous-session review (Q-0102)

Previous session = the BTD6 QA-accuracy arc (`claude/btd6-qa-accuracy`, #1492/#1493).
**Did well:** tight, test-covered grounding fixes (VERIFIED DDT counter towers; the
over-refusal fix) with a clean session-close consolidating the QA arc + a live-test
checklist — exactly the "ship something real + leave a checklist for the owner walk"
shape. **Missed / system improvement:** like this session, it added runtime surface
without anything routing it to the cross-cutting guard set; the recurring gap is
real and not BTD6-specific. The concrete system improvement is the Q-0089 idea
above — a discoverable new-extension ripple checklist/checker — which would have
saved this session a full guard-discovery loop and is the internal mirror of the
Hermes-as-independent-reviewer loop (each session's pain → a durable guard).

## 🛠 Friction → guard

- **Friction:** discovering the 19 cross-cutting guard failures (cog registries,
  allowlists, generated-artifact freshness) only by running the full ~3.5-min
  suite, iteratively. **Guard shipped now (free lane):** this `.sessions/` log's
  *Context delta → Needed but not pointed to* enumerates the complete add-a-cog
  ripple so the next agent has the list. **Guard proposed (owner-gated tooling):**
  the Q-0089 `check_new_extension.py` — a checker is the "enforce, don't exhort"
  upgrade over a prose list, but new tooling/CI wiring is owner-gated, so it's a
  proposal, not a self-applied hook.

## ⚑ Self-initiated

None — owner-directed feature (the request came from the owner in-session). No
unprompted idea→plan promotions to flag; the contained sub-decisions are listed
under *Decisions made alone* above for ratification.

## Doc audit (Q-0104)

`check_current_state_ledger.py --strict` exit 0; `check_docs` green (full suite);
ownership.md + ai-config-ownership.md updated and the generated surface docs
regenerated. No new owner *rules* (the two AskUserQuestion answers are
feature-config, not router-level policy) — router untouched. Did **not** add #1494
to the Recently-shipped ledger: convention is merged-PRs-only, and the next
session/reconciliation reconciles the merge.
