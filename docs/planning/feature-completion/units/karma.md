# Karma — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `karma` · **Type:** server-fn · **Family:** progression
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/karma_cog.py` (`!thanks`/`!karma` + Help hook) ·
> `disbot/services/karma_service.py` (audited grant seam) · `disbot/services/karma_config.py` (policy
> read model) · `disbot/utils/db/karma.py` (migration; credit + audit log + anti-abuse reads) ·
> `disbot/cogs/karma/schemas.py` (4-spec settings group) · `disbot/utils/settings_keys/karma.py` ·
> the `KarmaProvider` in `services/rank_providers.py` · folio `docs/subsystems/karma.md`

> Assessed during the completion-first arc (Q-0209). Karma is a **clean, well-guarded MVP** peer-
> reputation system: `!thanks @user` grants 1 karma, blocked by a self-give guard, a per-(giver→receiver)
> cooldown (default 1h), and a per-giver rolling 24h daily cap (default 10) — all enforced at the service
> with **no write on a blocked grant**. Every grant appends to `karma_audit_log` (which doubles as the
> anti-abuse read) and emits `EVT_KARMA_GRANTED`, with INV-K fencing direct writes out of the cog/view;
> config is a typed 4-spec settings group; the karma leaderboard is a registered provider. The honest
> gaps are **deliberately-deferred breadth** (karma roles/rewards, decay, negative rep, per-channel
> enable, an admin adjust panel) and one **audit-consistency** note (it uses a domain-specific audit log
> like Economy, not the generic `audit.action_recorded`). *(**React-to-thank shipped 2026-07-01, PR
> #1620** — an opt-in per-guild trigger emoji, off by default, grants karma through the same audited
> seam.)*

## Rubric (server function)

### A. Functional completeness — "does its job, in every case"
- [x] **Core promise delivered** — `!thanks @user [reason]` / `!karma give` (aliases `!rep`/`!thank`)
      grants 1 karma; `!karma` shows a reputation card; karma leaderboard via the provider
      (`karma_service.py`, `karma_cog.py`, `rank_providers.py`).
- [ ] **Every best-in-class sub-option exists** — ⚠️ **partial (react-to-thank now done).**
      ✅ **React-to-thank** (opt-in trigger emoji, PR #1620). **Deferred (folio-documented):** karma
      roles/rewards at thresholds · milestone announcements · decay · negative rep · per-channel enable.
      → punch-list #2.
- [x] **Failure modes honest** — self-give → `SelfKarmaError`; bot recipient rejected at the cog;
      disabled guild, cooldown-active, and daily-cap-hit each return a friendly message; absent target
      reads as zeros.
- [x] **Idempotent / atomic** — `credit_karma` is an atomic `ON CONFLICT … RETURNING` upsert; each grant
      appends exactly one audit row; **a blocked grant writes nothing** (all-or-nothing).

### B. Reachability & UI — "the most convenient way"
- [ ] **A command panel exists** — ⚠️ **partial.** `!karma` renders a reputation **card** (+ a back-nav
      `HubView` via the Help hook), but there is **no bespoke action panel** — config is the generic
      `!settings → Karma` widget group. Whether the card + settings-group clears the panel bar is an owner
      call (same shape as Welcome). → punch-list #1.
- [x] **Reachable every natural way** — `!thanks`/`!karma` entry points + Help hook
      (`build_help_menu_view`) + Community-hub child (`parent_hub: community`); karma board via
      `!leaderboard karma`.
- [x] **Integrated into the Setup wizard** — a "Thanks & Karma" card in Essential Setup
      (`essential_setup.py`).
- [x] **Return navigation** — the Help hook returns a `HubView`; the card is display-only (no trapped
      view).
- [x] **In-place, not spammy** — grants post a single confirmation; the card is one message.

### C. Convenience
- [x] **React-to-thank** — ✅ **shipped (PR #1620).** An opt-in per-guild trigger emoji
      (`karma.reaction_emoji`, empty = off); reacting with it grants karma to the message author through
      the audited `karma_service.give(source="reaction")` seam (cooldown + daily cap + self-give guard
      all apply). Silent (no channel spam); byte-identical when unset.
- [x] **Sensible defaults** — cooldown 1h, daily cap 10, enabled by default (opt-out)
      (`karma_config.py`).
- [x] **Clear feedback** — success shows the recipient's new total; cooldown shows the retry time; cap
      shows the cap; every block has a friendly reason.

### D. Authority & safety
- [x] **Authority re-checked** — user self-gating (no self/bot grant); policy + cooldown + cap re-checked
      fresh on every `give()` (no cached bypass). No admin set/reset commands exist (see punch-list #2).
- [x] **Mutations through an audited seam** — every grant goes through `karma_service`, which writes
      `karma_audit_log` (`db.insert_karma_audit`) + emits `EVT_KARMA_GRANTED`; INV-K
      (`test_inv_k_karma_service.py`) fences `credit_karma`/`increment_given`/`insert_karma_audit` out of
      the cog/view. ⚠️ **Note:** it uses a **domain-specific** audit log (the Economy pattern), **not** the
      generic `audit.action_recorded` seam — audited + invariant-protected, but inconsistent with
      Welcome/Moderation/Settings. → punch-list #3 (consistency).
- [x] **Self-give guard** — enforced at both the cog and the service (`SelfKarmaError`), tested.
- [x] **Reuses governance** — capability floor `karma.settings.configure` on the settings specs.

### E. Configuration
- [x] **Settings route through the pipeline** — `KARMA_CONFIG_SCHEMA` (4 specs: `enabled`,
      `cooldown_seconds` 0–604800, `daily_cap` 1–1000, `reaction_emoji` free-text) via `SubsystemSchema`/`SettingsMutationPipeline`
      (`karma/schemas.py`); defaults pinned to the policy (single source of truth, tested).
- [x] **`settings_keys` constants** — `KARMA_ENABLED`/`KARMA_COOLDOWN`/`KARMA_DAILY_CAP`/`KARMA_REACTION_EMOJI`
      (`utils/settings_keys/karma.py`).
- [x] **Typed widgets** — bool + numeric-preset + free-text specs with validators.

### F. Wiring & discoverability
- [x] **Registry** — key `karma`, `category: progression`, `visibility_tier: user`,
      `entry_points: [thanks, karma]`, `parent_hub: community`, related `[xp, leaderboard]`, 3
      capabilities (`subsystem_registry.py`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook; Community-hub child.
- [x] **Homed in `ownership.md`** — `karma_service` owns karma writes (INV-K); the audit log doubles as
      the anti-abuse read.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_karma_service.py` (grant credits/audits/emits; non-positive amount
      guard; disabled-guild; cooldown blocks + **doesn't write**; daily cap blocks + **doesn't write**;
      zero-cooldown skip; rank retrieval).
- [x] **Authority/self-give + schema tests** — self-give `SelfKarmaError`; `test_karma_schemas.py`
      (registration, idempotent, spec defaults ≡ policy, every spec requires the capability).
- [x] **Mutation-seam tests** — `test_inv_k_karma_service.py` (AST: no direct karma mutation / raw SQL
      outside service+db).
- [ ] **Coverage gaps** — bot-recipient rejection tested only in cog context; no event-catalogue
      registration test. → punch-list #4 (minor).
- [ ] **Live walkthrough recorded** — pending. → punch-list #5.
- [ ] **Owner ✔** — pending. → punch-list #6.

## Punch-list (clear these to certify)

1. **Bespoke command panel (rubric B)** *(deepening, or owner waiver)* — an actionable Karma panel (give
   / view card / settings link / back) rather than relying on the card + generic settings group — or the
   owner waives it (the card + settings group may suffice for a light user feature, the Welcome shape).
2. **Best-in-class breadth (rubric A/C)** *(owner-paced, deferred)* — karma
   roles/rewards at thresholds · milestone announcements · decay · negative rep · per-channel enable ·
   an admin adjust/reset panel. The folio already lists these as the phase-2 deferral.
3. **Audit-consistency** *(offline, minor)* — decide whether karma should also emit the generic
   `audit.action_recorded` (as Welcome/Moderation/Settings do) in addition to its domain audit log, or
   keep the Economy-style domain-only pattern by design.
4. **Cog-integration tests** *(offline, minor)* — bot-recipient rejection + event-catalogue registration.
5. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (`!thanks` →
   cooldown block → daily-cap block → `!karma` card → `!leaderboard karma`), screenshots.
6. **Owner sign-off** — maintainer uses it and confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_karma_service.py` · `tests/unit/cogs/test_karma_schemas.py` ·
  `tests/unit/invariants/test_inv_k_karma_service.py`
- **Walkthrough:** pending (punch-list #5)
- **Owner sign-off:** pending (punch-list #6)

## Verdict
Karma is a **clean, well-guarded MVP** — atomic grants, a self-give guard, cooldown + daily-cap
anti-abuse that never writes on a block, an audited seam (INV-K-fenced), typed config, and a leaderboard
provider. It is **not yet `✔ certified`**: the gaps are a missing **bespoke panel** (#1, or a waiver),
**deliberately-deferred breadth** (karma roles, decay, negative rep — #2; react-to-thank ✅ #1620), a minor audit-consistency
note (#3), small cog-test gaps (#4), and the owner walkthrough/sign-off (#5/#6). No safety/audit/dead-end
issues found.
