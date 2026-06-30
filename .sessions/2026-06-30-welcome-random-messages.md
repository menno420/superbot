# 2026-06-30 — Welcome random messages + opt-in DM greeting (S1 completion deepening)

> **Status:** `complete` — ready to merge (Q-0133). Run type: `routine · dispatch`.
> Full CI mirror green (`check_quality.py --full` → **All checks passed ✓**, 13313+ pass; black/isort/
> ruff + mypy clean; arch strict 0 new). PR #1579.

**Branch:** `claude/funny-franklin-7y6goi`.

## What I did (intentions → shipped)

Dispatch run, no specific work order → advanced the next S1 completion-first slice (Q-0209). Picked
the **Welcome** unit's completion-cert punch-list **#2** (best-in-class options) and shipped **two**
of its items in one cohesive batch:

**1 · Multiple / random messages.** An operator stores several greeting / farewell / DM variants in
one message setting, separated by a `---` line; the bot picks one **at random** per greeting
(Carl-bot / MEE6 / Dyno parity).
- `welcome_config.split_message_variants` + `pick_message` — pure, seeded-rng-testable; a value with
  no `---` is a single variant → **byte-identical** for every existing config.
- `welcome_service.format_join_embed` / `format_leave_embed` select a variant (`rng` injectable).
- `_validate_message` now caps **per variant** length (≤500) + variant count (≤10).
- `!welcome` status preview renders the first variant + a "1 of N random variants" note (never the
  raw `---` separators).

**2 · Opt-in DM greeting.** A new `dm_enabled` flag + dedicated `dm_message` template also DMs the
joining member the greeting — **independent** of the channel greeting, **fail-safe on closed DMs**
(`discord.Forbidden`/HTTP/any error swallowed → the join dispatch always completes). The DM body
supports the same `---` random variants.
- `WelcomePolicy.dm_on_join` predicate (needs only master + dm flag, no channel); folded into
  `any_action_enabled`. `format_dm_embed` + `_send_dm`. New `dm_enabled`/`dm_message` SettingSpecs +
  `WELCOME_DM_ENABLED`/`WELCOME_DM_MESSAGE` keys; defaults single-sourced in `welcome_config`.

**Migration-free** throughout (welcome settings are scalar KV); DM off by default.

## Files

- `disbot/services/welcome_config.py` · `disbot/services/welcome_service.py`
- `disbot/cogs/welcome/schemas.py` · `disbot/cogs/welcome_cog.py`
- `disbot/utils/settings_keys/welcome.py` (+ `__init__.py` export)
- Tests: `tests/unit/services/test_welcome_config.py` · `…/test_welcome_service.py` ·
  `tests/unit/cogs/test_welcome_schemas.py` · **new** `tests/unit/cogs/test_welcome_cog.py` (+51
  welcome tests total).
- Docs/artifacts: welcome completion cert (#2 narrowed) · `current-state/S1-bot.md` recently-shipped ·
  `settings-customization-command-map.md` (new keys) · regenerated `dashboard.json` / `site.json` /
  `botsite/site/data.js` for the two new setting keys.

## Why this is contained / safe

Additive + default-off (DM off; a single message = one variant) → every existing guild renders
byte-identically; no data backfill, no migration. All config still flows through the audited
`SettingsMutationPipeline`; the DM send is read-only of the member and swallows every failure, so a
DM that can't be delivered never affects the channel greeting, the entry-role grant, or the join
dispatch. Architecture strict: 0 new violations.

## Context delta

- The welcome message settings are scalar KV (the module docstrings stress "no migration"), so the
  variant feature is a pure render-time split on the existing field — no schema change. The validator
  shift from a whole-value length cap to a **per-variant** cap is back-compatible (single message =
  one variant, same gate).
- **Wide blast radius caught by the full mirror:** adding two `settings_keys` reddened three things a
  `--check-only` pass misses — `settings-customization-command-map.md` (a doc test asserts every
  `WELCOME_*` constant + SettingSpec name appears), `dashboard.json` freshness, and the
  `dashboard.json`/`site.json`/`data.js` sync tests. Fixed the doc + regenerated the artifacts with
  `scripts/export_dashboard_data.py` (the intended path; BUG-0022 only stopped the *test suite* from
  clobbering data.js, not the explicit export). **Lesson for next session: any new `settings_keys`
  constant means "update the command-map doc + re-run `export_dashboard_data.py`" — run the *full*
  mirror, not `--check-only`, when touching settings keys.**
- **🛠 Friction → guard:** the doc-reference + artifact-freshness tests already *enforce* this
  (they're why CI would have caught it) — no new guard needed; the existing checkers did their job.
  The gap was purely my running `--check-only` first; noted above so the next session reaches for
  `--full` on a settings-keys change.

## 💡 Session idea (Q-0089)

**Welcome "test greeting" button/command** — a `!welcome test` (or a button on the `!welcome` status
embed) that fires the *actual* greeting pipeline once against the invoking admin (channel post + DM if
enabled), so an operator can see a random variant land for real before a member ever joins. Closes the
"I configured it but can't tell what it looks like live" gap that random variants make sharper (you
can't eyeball which of 5 variants posts). Cheap: reuse `format_join_embed`/`format_dm_embed` +
`_post`/`_send_dm` with the admin as the member. Dedup-checked `docs/ideas/` — no welcome-preview
idea exists. Worth having: it's the live-walkthrough half of the Welcome cert (#5) turned into a
self-serve operator tool, and generalizes to any greeting-style subsystem.

## ⟲ Previous-session review (Q-0102)

The previous run (PR #1571, reaction-roles "Who's in?" roster) was a clean, tightly-scoped
owner-directed follow-on — good: read-only, no migration, gated on the same opt-in flag, +12 tests,
honest about the truncation tail. One thing it *could* have done: the roster and the #1570 counter
both compute over `guild.members`, and a "Who's in?" with hundreds of holders truncates to the field
cap — the session noted it but didn't add a follow-up idea for a paginated roster. **System
improvement it surfaces:** the completion-cert flow is working well for *deepening*, but the certs all
sit at `◐` with **0 certified** because every one needs an owner live-walkthrough (#5/#6). My Q-0089
idea above (a self-serve "test greeting" preview) is one concrete pattern to make the walkthrough
half cheaper to assemble — worth generalizing: each unit cert could name a "how an agent can
pre-stage the walkthrough evidence offline" line, shrinking the owner's step to a yes/no.

## 📤 Run report footer

- **Run type:** `routine · dispatch`
- **PR:** #1579 (Welcome random messages + opt-in DM greeting) — self-merge on green (small, contained,
  default-off completion deepening; not a substantial plan step).
- **Bugs:** none fixed/opened this run (no bug-book entries touched).
- **⚑ Self-initiated:** Welcome completion-cert punch-list #2 (random messages + DM greeting) — no
  dispatch payload named it; selected as the next S1 completion-first slice (idea→build is open,
  Q-0172). Flagged here for owner review.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (migration-free; merge auto-deploys via Railway — no seed-data, no
  restart).
- **Next ▶:** Welcome cert #2 remainder — **join-delay age-gating** (skip greeting/role for accounts
  younger than a configurable threshold; anti-raid, additive, default 0 = off) and **ping-then-delete**
  (post the greeting then auto-delete after N seconds). Both discrete additive slices on the same
  policy model; each its own PR. Cert: `docs/planning/feature-completion/units/welcome.md` punch-list.
