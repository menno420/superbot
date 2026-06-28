# Leaderboards — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `leaderboard` · **Type:** server-fn · **Family:** progression
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/leaderboard_cog.py` (`!leaderboard` + aliases + `LeaderboardView` + Help hook) ·
> `disbot/services/rank_providers.py` (the provider registry + 10 providers + alias map) ·
> the per-category `utils/db` top-N reads · the leaderboard image renderer ·
> `disbot/utils/hub_registry.py` (Economy-hub child)

> Assessed during the completion-first arc (Q-0209). Leaderboards is a **clean, read-only** unit built on
> a tidy **provider-registry** pattern: a new category is one `RankProvider` class, no cog edits. Ten
> categories (XP · coins · mining · creatures · game-XP · crafting · deathmatch · RPS · counting · karma)
> are reachable via `!leaderboard` + legacy aliases, with a runtime category-switcher select and a themed
> top-N **image card** (embed fallback) and consistent actionable empty-state hints. It is read-only
> (no mutations; reads through `utils/db`), so authority is light by design. The honest gaps are
> **coverage + depth**: several games have **no provider yet** (notably **Fishing** — which has its own
> separate `!trophies` board but no unified-panel provider — plus Blackjack/Casino/Word-Chain/Farm), no
> time-window (weekly/monthly) boards, fixed top-10 with **no self-rank when off-board** (the
> `member_rank()` infra exists but isn't surfaced here), and no web leaderboard.

## Rubric (server function)

### A. Functional completeness — "does its job, in every case"
- [x] **Core promise delivered** — 10 categories via the provider registry (`rank_providers.py`), each a
      top-N read with medal-prefixed rows + a themed image card; `!leaderboard [category]` + aliases
      (`!lb`/`!minelb`/`!rpslb`/`!countlb`/…); runtime category switcher.
- [ ] **Category coverage complete** — ❌ **partial.** **Missing providers** for existing games:
      **Fishing** (subsystem + a separate `!trophies` heaviest-catch board exist, but no unified-panel
      provider), **Blackjack**, **Casino**, **Word Chain**, **Farm**. → punch-list #1 (the headline gap).
- [ ] **Best-in-class breadth** — ❌ no time-window (weekly/monthly/all-time) boards; fixed top-10 with
      **no "your rank when off-board"** surfaced (the `RankProvider.member_rank()` contract exists and is
      used by `!rank`, but not by the leaderboard panel). → punch-list #2.
- [x] **Failure modes honest** — each provider declares an actionable `empty_hint` (e.g. "Use `!daily`");
      departed members resolve via `resources.member_display`; Pillow-absent → embed-only.

### B. Reachability & UI — "the most convenient way"
- [x] **A command panel exists** — `LeaderboardView` with a runtime-built category `Select` (options from
      `provider_names()`); switching re-renders the same message in place.
- [x] **Reachable every natural way** — `!leaderboard` + 8 legacy aliases + Help hook
      (`build_help_menu_view`); Economy-hub child (`parent_hub: economy`, `hub_registry`).
- [x] **Setup wizard — N/A** — read-only display; nothing to configure at onboarding (correct waiver).
- [x] **Return navigation** — the category select persists; no dead-ends; errors are ephemeral.
- [x] **In-place, not spammy** — category switch edits the original message; one card per render.

### C. Convenience
- [x] **Category switch without retyping** — the select dropdown; aliases jump straight to a board.
- [x] **Rendered card + themes** — per-category skins (abyss/verdant/ember/midnight), embed fallback.
- [ ] **Depth/default** — ⚠️ fixed top-10, no pagination, no self-rank injection; no configurable default
      category. → punch-list #2.

### D. Authority & safety
- [x] **Read-only by design** — no INSERT/UPDATE/DELETE; all reads through `utils/db` (confirmed by the
      provider tests mocking `db.*` with no transaction/conn). Authority is light (visibility tier `user`).
- [x] **No mutation seam needed** — nothing to audit; no direct writes.
- [x] **Reuses governance** — registry `visibility_tier: user`; no second allowlist.

### E. Configuration
- [x] **N/A (read-only display)** — nothing operator-tunable today (no enabled-board toggle, no default
      category). Acceptable for a read-only board; a future "enabled boards" / default-category setting is
      a *deepening* item, not a gap that blocks the read-only promise. → noted under punch-list #2.

### F. Wiring & discoverability
- [x] **Registry** — key `leaderboard`, `category: progression`, `visibility_tier: user`,
      `entry_points: [leaderboard, lb]`, `parent_hub: economy`, capabilities `leaderboard.*.view`
      (`subsystem_registry.py`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook; Economy-hub primary child
      (`hub_registry.py`).
- [x] **Homed in `ownership.md`** — leaderboard reads every owner's tables, **no writes**.
- [x] **Provider-registry pattern** — `_PROVIDERS` dict + alias map + `get_provider`/`provider_names`
      (registration order drives the select).

### G. Tests & evidence (required for ✔)
- [x] **Provider-registry tests** — `test_rank_providers.py` (10 categories exposed; alias mappings;
      every provider declares a valid card theme; structured `name/score/value_text` per category; medal
      prefixes; `member_rank` off-board → `(None, None)`).
- [x] **Render + empty-state tests** — `test_leaderboard_card.py` (attach/fallback decision, theme
      forwarding, Pillow-absent degrade); `test_leaderboard_empty_states.py` (per-category hints);
      `test_counting_leaderboard.py`.
- [ ] **Coverage gaps** — no test for the category-switcher select callback, the card-vs-no-card
      attachment wiring, or timeout/expiry. → punch-list #3 (minor).
- [ ] **Live walkthrough recorded** — pending. → punch-list #4.
- [ ] **Owner ✔** — pending. → punch-list #5.

## Punch-list (clear these to certify)

1. **Add the missing game providers (rubric A) — the headline gap** *(offline, deepening, turn-key per
   game)* — a **Fishing** provider first (Fishdex total or trophy-weight; reconcile with the existing
   `!trophies` board so there's one home), then Blackjack/Casino/Word-Chain/Farm. Each is one
   `RankProvider` class + a `utils/db` top-N read; the registry pattern makes them isolated additions.
2. **Depth (rubric A/C)** *(deepening)* — surface **self-rank when off-board** in the panel (the
   `member_rank()` infra already exists) · time-window (weekly/monthly) boards · optional pagination /
   configurable default category.
3. **Switcher/render tests** *(offline, minor)* — cover the category-select callback + card-attachment
   wiring.
4. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (`!leaderboard`
   → switch categories → empty board hint → card render), screenshots.
5. **Owner sign-off** — maintainer uses it and confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_rank_providers.py` · `tests/unit/cogs/test_leaderboard_card.py` ·
  `…/test_leaderboard_empty_states.py` · `…/test_counting_leaderboard.py`
- **Walkthrough:** pending (punch-list #4)
- **Owner sign-off:** pending (punch-list #5)

## Verdict
Leaderboards is **clean and read-only-safe** with an extensible provider-registry, a category switcher,
themed image cards, and consistent empty-state UX. It is **not yet `✔ certified`**: the headline gap is
**missing providers for several existing games** (Fishing first — #1), with depth items (self-rank,
time windows — #2) and minor test gaps (#3) behind it, plus the owner walkthrough/sign-off (#4/#5). No
safety/dead-end issues found.
