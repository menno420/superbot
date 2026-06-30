# 2026-06-30 — Welcome age-gating + ping-then-delete (completion-first deepening)

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did
Empty-fire dispatch advancing the S1 completion-first arc (Q-0209). Closed the **Welcome** completion
cert's **punch-list #2 remainder** (best-in-class options) — the last two named gaps vs
Carl-bot/MEE6/Dyno — in one focused PR (#1581). **Punch-list #2 is now CLOSED.**

### Join-delay age-gating (anti-raid)
- **`welcome_config.account_is_too_young(created_at, *, min_age_days, now)`** — a pure, tz-aware helper
  (fail-open on `min_age_days <= 0`, a `None` created_at, or a naive/aware mismatch — better to greet a
  legit member than silently drop them).
- **`WelcomePolicy.min_account_age_days`** + `age_gate_enabled` property; resolved in `load_policy`.
- **`welcome_service.handle_member_join`** gates right after `any_action_enabled`: a below-threshold
  account gets **no greeting, no DM, no entry role** (logged). `_account_too_young` wraps the pure
  helper with `discord.utils.utcnow()`.
- Setting `welcome_min_account_age_days` (int, default 0 = off, capped 0..365), `numeric_presets` (0/1/7).

### Ping-then-delete
- **`WelcomePolicy.greeting_delete_after`** property → `float | None`; `_post` forwards `delete_after`
  to discord.py's native `send`, applied to **both** the channel greeting and the farewell. The **DM
  greeting is never deleted**.
- Setting `welcome_delete_after_seconds` (int, default 0 = keep, capped 0..3600), `numeric_presets`
  (0/30/60).

Both are additive scalar settings on the existing welcome policy model — **no migration**, default-off,
**byte-identical** for every existing config. Surfaced in the `!welcome` status embed when set.

### Tests (+18) / docs
- `test_welcome_config.py` — the age-gate helper (off / below / at-threshold / unknown-age fail-open /
  mixed-awareness) + the two policy properties + a defaults-stay-off pin.
- `test_welcome_service.py` — too-young skips greeting/DM/role; old-enough greets; gate-off greets a
  brand-new account; unknown-age fails open; `delete_after` forwarded on join + leave; off ⇒ `None`;
  DM never carries `delete_after`.
- `test_welcome_schemas.py` — int validators (bounds + bool/str rejection) + `numeric_presets` hint +
  the defaults-match-config pin updated for both new specs.
- `test_welcome_cog.py` — the `!welcome` embed shows/hides the age-gate + auto-delete lines.
- De-staled the Welcome completion cert (punch #2 CLOSED), the settings command-map doc (both new
  keys/specs), and regenerated the 4 generated artifacts (site.json / data.js / dashboard.json —
  `setting_keys` 110 → 112).

## Verification
- `python3.10 scripts/check_quality.py --full` GREEN (the only failures were the expected
  settings-doc + artifact-freshness checks, fixed by listing the new keys/specs + regenerating).
- `python3.10 scripts/check_architecture.py --mode strict` — 0 errors (warnings pre-existing).
- `check_docs --strict` / `check_current_state_ledger --strict` — clean (only benign newest-merge lag).
- **Process note (for the next run):** a stray `python3.10 -m black .` / `isort .` reformatted ~370
  unrelated files (CI excludes `tests/`, so they were never red); reverted everything outside the
  intended keep-list before pushing. The Stop hook prints the right command — trust
  `check_quality.py`, never bare `black .` (CLAUDE.md §"Match CI exactly").

## Handoff — next ▶
**Welcome punch-list #2 is fully CLOSED** — every named best-in-class option now exists. Welcome's
remaining gaps are all `[owner]`/minor: #1 bespoke command panel (or owner waiver) · #3 binding-pipeline
seam · #4 cog-integration test · #5/#6 owner walkthrough + sign-off.

**Next turn-key offline completion-first picks (other units):**
- **Diagnostics** list pagination (cert punch #2 — apply `_PaginatorView` to long findings/consistency
  output) + #5 (health-metrics reconcile).
- **Cleanup #4** — surface the spam dedupe window as a real per-guild setting *with* a config-input
  widget (a constant rename isn't "configurable" — deferred by the #1566 run).
See `docs/planning/feature-completion/units/`.

## 💡 Session idea
**Anti-raid defaults in the Essential Setup "block spam" step.** The new welcome age-gate +
auto-delete are exactly the knobs a server owner wants pre-set after a raid scare, but they're only
reachable via `!settings → Welcome`. The Essential Setup spine already has a "block spam" step — it
could offer a one-tap **"Raid protection"** toggle that sets a sensible `min_account_age_days` (e.g. 1
day) alongside the automod spam rule, so a fresh server gets layered anti-raid defaults without
hunting through settings. Small, additive, composes the two subsystems through their existing audited
seams. Dedup-checked `docs/ideas/` — not present.

## ⟲ Previous-session review
The previous run (#1579, Welcome random messages + DM greeting) was a clean, well-scoped
completion-first slice that did the *harder* half of punch-list #2 first (random variants touch the
embed builders + validator + preview) and left the two additive single-knob options (this run) — a
sensible ordering. One thing it could have done while in the file: it added `dm_enabled`/`dm_message`
but didn't surface the new options in the Essential Setup spine, so the discoverability gap the cert
flags (#1 panel) widened slightly with each new setting. **System improvement surfaced this run:** the
`test_spec_defaults_match_config_defaults` set-equality assertion is doing real work — it forced this
run to register both new specs in the doc + test in lockstep, catching drift at the source. That
"defaults are one source of truth, pinned by a set-equality test" pattern is worth replicating for the
other subsystem schemas that don't yet have it.

## 📤 Run report
- **Run type:** routine · dispatch
- **PR:** #1581 (Welcome age-gating + ping-then-delete) — self-merge on green.
- **⚑ Self-initiated:** none (completion-first arc is the standing S1 dispatch lane; this is the named
  Welcome cert punch-list #2 remainder, not an unprompted idea→plan promotion).
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (no migration, no data step; the settings are scalar KV — merge
  auto-deploys).
- **Bugs:** none opened; none fixed.
