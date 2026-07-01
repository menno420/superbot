# Bug book — live-reported bugs, root causes, and their fixes

> **Status:** `living-ledger` — the durable intake for bugs observed in
> production/live use (founded 2026-06-11 at the owner's request, during the
> first live-user bug report). **Convention:** one numbered entry per bug —
> verbatim symptom, expected behavior, root cause (filled at fix time), fix PR,
> status. Newest first. A bug here jumps the queue per the CLAUDE.md
> "bugs first, durably" rule: root cause over symptom-patch, one source of
> truth, and a **stays-fixed guard named in the entry** — a regression test (or
> CI invariant) that *fails against the pre-fix behavior*, shipped in the **same**
> fix PR, never deferred to "later". **A fix goes live automatically:** a merge to
> `main` auto-deploys to Railway (≈ CI build time; a failing build never deploys,
> and the old container stays up until the new one connects), so mark a fixed entry
> simply `FIXED` — do **not** add a "needs a manual Railway deploy" step (a phantom
> owner to-do that recurred across sessions; see
> [`operations/production-deployment.md`](../operations/production-deployment.md)).
> Owner-reported inconsistencies he hasn't formalized yet (see current-state
> 2026-06-10 standing invite) land here as they surface.
>
> **Deferred-root-fix backlog:** when an entry lands a *symptom* fix but defers the durable
> root fix (status `PARTIALLY FIXED` / `root-fix RECOMMENDED` / `FIXED (immediate)` without
> `(root)`), `python3.10 scripts/check_bug_book_rootfix_backlog.py` lists those entries so a
> later empty-fire dispatch run can pick them up instead of them sitting un-promoted (the
> trap BUG-0018 hit). Advisory by default; `--strict` exits 1 on a non-empty backlog.

## BUG-0031 — building a **Boathouse** raises `KeyError: 'boathouse'` (structure never added to the build-reason map) — FIXED (root)

- **Symptom (latent, found by inspection during the PR #1626 dispatch run):** invoking `!boathouse`
  and pressing **Build** — or any build of the Boathouse structure — raises
  `KeyError: 'boathouse'` inside `services.mining_workflow.build_structure` before the transaction,
  so the build never happens and the panel would surface an error. Shipped live in **#1605** (the
  Boathouse structure); no test exercised the *build* path so CI was green.
- **Root cause — a hand-maintained map that must be kept in sync, and wasn't:** `build_structure`
  resolved the economy-audit reason via `reason = _STRUCTURE_BUILD_REASON[structure]` — a literal
  `{structure: market.*_BUILD_REASON}` dict. When #1605 registered the `boathouse` structure it added
  the ladder, level names, and panel but **not** a `_STRUCTURE_BUILD_REASON` entry, so the direct
  `[structure]` index raised. Same drift class as the `give` collision — a second source of truth that
  a new structure silently omits. Notably **every** existing reason constant was exactly
  `mining:{structure}_build`, so the map added zero information over deriving it — pure drift surface.
- **Fix (root — PR #1626, this entry):** deleted the map; `build_structure` now derives the reason
  generically via `market.structure_build_reason(structure)` (`mining:{structure}_build`), so a
  newly-registered structure can **never** crash the build path for want of a map entry. The named
  `*_BUILD_REASON` constants stay (public, unchanged strings) + `BOATHOUSE`/`FISHERY` added for parity.
- **Stays-fixed guard (same PR):** `test_every_registered_structure_resolves_a_build_reason`
  (`tests/unit/utils/test_mining_structures.py`) asserts `structure_build_reason` returns a non-empty
  `mining:<key>_build` for **every** structure in `structures.STRUCTURES` — fails against the pre-fix
  direct-index map (which had no `boathouse` key) and catches any future registered-but-unmapped
  structure.
- **Status:** FIXED (root) 2026-07-01 (dispatch run). Live on the next auto-deploy; no data step.

## BUG-0030 — `!dock` structure command collides with `!sail`'s `dock` alias → `fishing` cog fails to load → boot crash loop — FIXED (root)

- **Symptom (live PROD outage, 2026-07-01):** after PR #1599 (fishing Dock structure) merged and
  auto-deployed, the `worker` entered a **boot crash loop** — restart every ~30s, never reaching the
  gateway. `cogs.fishing_cog` failed to load with `CommandRegistrationError: The command dock is
  already an existing command or alias`, so the `fishing` subsystem had no loaded commands, its
  declared entry points (`fish`/`fishlog`) went missing, and the STRICT identity-contract aborted
  startup. The bot was **offline** until #1600 merged and redeployed.
- **Root cause — a *same-cog* top-level command-token collision, and a review miss:** `!sail` had
  carried `dock` as an **alias** (the "return to shore" venue toggle) since 2026-06-29. PR #1599 added
  a first-class command literally **named** `dock` (the Dock structure). At `add_cog`, discord.py's
  single global prefix-command namespace rejects the second claim of `dock`. **This was avoidable:**
  the dispatch run that shipped #1599 had *read* the `sail` command definition (with its `dock` alias)
  minutes earlier and still chose the name `dock` — it treated "pick a command name" as a naming task,
  not a namespace-collision check, and never ran the one `grep '"dock"'` that would have caught it. It
  is the same class as BUG's-worth-of `give` collision (#1541/#1544) — the *second* boot-loop from a
  command-token collision. Green CI did not catch it because **no CI check loads the cogs onto a bot**
  the way boot does, and the existing static token guard de-duplicated claimants *by cog*, so a single
  cog claiming a token twice slipped through.
- **Fix (root — PR #1600, separate session):** dropped the vestigial `dock` alias from `!sail`; the new
  `!dock` structure command owns the name (`!sail`/`!setsail` still cover the venue toggle).
- **Stays-fixed guards (two layers):**
  1. **Static (PR #1600):** broadened `test_no_duplicate_top_level_command_names_across_cogs`
     (`tests/unit/invariants/test_extension_integrity.py`) to count distinct **commands** per token, so
     it catches **same-cog** *and* cross-cog name/alias collisions (fails against re-adding the alias).
  2. **Dynamic (PR #1601, this entry):** `tests/unit/invariants/test_cog_load_smoke.py` — constructs a
     bot like `bot1` and **loads every `INITIAL_EXTENSIONS` cog**, failing CI if any raises at
     `add_cog`. This is the "did the bot actually boot?" check and catches the whole boot-break class
     (token collisions *and* a raising `cog_load`, a bad import, a duplicate app-command), not just the
     token subclass. Fails against the pre-#1600 tree; passes 58/58 on fixed `main`.
- **Status:** FIXED (root) 2026-07-01. Code fix live via #1600's auto-deploy (no data step). Prevention
  live via #1600's broadened static guard + #1601's dynamic boot smoke test.

## BUG-0029 — XP level-up role grants bypass the audited role seam (no `audit.action_recorded`, no shared hierarchy preflight) — FIXED (root)

- **Symptom (found 2026-06-28 by a dispatch run during the XP feature-completion assessment — code
  inspection, not a live report, but a real audit gap):** when a member levels up and earns an
  XP-threshold role, the grant/removal was performed by a **direct `member.add_roles()` /
  `member.remove_roles()`** call in `disbot/cogs/xp/listener.py::_apply_xp_threshold_roles` — so the
  role change fired **no `audit.action_recorded` event** and did **not** appear on the audit/server-log
  surface, unlike every *other* role mutation in the bot. It also ran its own bare
  `discord.Forbidden`/`HTTPException` catch instead of the shared manage-roles + hierarchy preflight.
- **Root cause:** the XP listener was written against the raw discord.py member API rather than the
  canonical `services.role_automation.apply` seam. The seam is what Welcome's entry-role grant, the
  role cog, and the time-threshold automation all use (it emits `audit.action_recorded` per change via
  `_apply_single` and preempts predictable blockers once per batch). The `test_no_direct_role_mutations`
  invariant deliberately scopes only the role cog/views and its own docstring *assumes* "the automation
  apply path in `services.role_automation` is already audited" — so nothing caught the XP listener doing
  its own thing. Classic "added the feature against the low-level API, skipped the audited seam" gap.
- **Fix (root, this PR):** `_apply_xp_threshold_roles` now builds `role_automation.Assignment` rows
  (one promote-assignment per newly-earned role in stacking mode; one promote+demote assignment in
  single-role mode) and calls `role_automation.apply(guild, assignments, actor_type="system")`. Every
  XP role change now fires `audit.action_recorded` (subsystem `role_automation`, `assign_role` /
  `remove_role`) and reuses the shared preflight. Behaviour is otherwise identical (same roles added /
  removed for stacking vs. single-role mode; exempt members still get nothing).
- **Stays-fixed guard:** `tests/unit/invariants/test_no_direct_xp_role_mutations.py` — an AST invariant
  that `cogs/xp/listener.py` contains **no** direct `member.add_roles` / `remove_roles` call (fails
  against the pre-fix direct-call behaviour). Plus the updated behaviour tests in
  `tests/unit/cogs/test_xp_listener_roles.py` (stacking + single-role now assert the audited
  `role_automation.apply` is awaited with the right `Assignment`s and `actor_type="system"`; the exempt
  case asserts the seam is **not** hit).
- **Status:** FIXED (root) 2026-06-28 (dispatch run). Live on the next auto-deploy; no data step needed.

## BUG-0028 — panel-initiated PvP deathmatch crashes on resolve (`ctx=None` → `self.ctx.guild.id` AttributeError) — FIXED (root)

- **Symptom (found 2026-06-28 by a dispatch run via code inspection during the Deathmatch
  completion-cert dead-end fix — not a live report, but a real latent crash):** a PvP duel started
  from the **panel** (`👤 Challenge Player` → opponent select, not the `!deathmatch @user` command)
  would raise `AttributeError: 'NoneType' object has no attribute 'guild'` the moment the duel
  **resolved** (a finishing blow or a turn timeout) — i.e. the whole panel-PvP path was broken at the
  finish line.
- **Root cause:** `views/games/deathmatch_panel.py::_DeathmatchOpponentSelect.callback` builds
  `_ChallengeView(cog, challenger, opponent, duel_key, None)` — `ctx=None`, since the panel only has
  an `interaction`. On accept that `None` ctx is forwarded into `_DuelView`, whose `_resolve` /
  `on_timeout` computed the originating guild as `self.ctx.guild.id if self.ctx.guild else 0` —
  `None.guild` raises. (The `!deathmatch` command path was unaffected: it passes a real ctx.) It also
  meant the panel path would have recorded results under the wrong guild even if it hadn't crashed.
- **Fix (root, PR #1527):** thread an **explicit `guild_id`** through the duel instead of reaching
  into `ctx`. `_ChallengeView.btn_accept` already had `gid = interaction.guild_id or 0` (for gear); it
  now passes `guild_id=gid` into `_DuelView`, which stores `self.guild_id` (falling back to
  `ctx.guild.id` only when no `guild_id` is given, preserving the command path + existing tests) and
  uses `self.guild_id` for the leaderboard + gear-wear writes. The panel/rematch path can now pass
  `ctx=None` safely.
- **Stays-fixed guard:** `tests/unit/cogs/test_deathmatch_pvp_deadend.py::`
  `test_pvp_duel_timeout_swaps_to_result_view_and_uses_guild_id` builds a `_DuelView` with `ctx=None`
  and `guild_id=777`, runs `on_timeout`, and asserts the write is recorded under `777` with **no
  crash** (fails against the pre-fix `self.ctx.guild.id`); `test_duelview_guild_id_falls_back_to_ctx`
  pins the backward-compatible ctx fallback (and that `ctx=None`+no-guild_id degrades to `0`, never
  raises).
- **Status:** FIXED (root) 2026-06-28. Fixed alongside the PvP trapped-view dead-end gap (Deathmatch
  completion cert punch-list #1); live on the next auto-deploy.

## BUG-0027 — born-red merge-gate silently fails open on a session-card slug collision (a partial PR auto-merged and clobbered a prior session log) — FIXED (root)

- **Symptom (found 2026-06-28 by a dispatch run, from its own behavior — not a live user report):**
  an empty-fire dispatch session opened its born-red PR (#1523) with an `in-progress` session card,
  per the Q-0133 flow — and GitHub **auto-merged it immediately**, while the card still said
  `in-progress` and before any real work landed. The born-red gate (`check_session_gate.py`, the
  whole point of which is to hold a partial PR red until the card flips to `complete`) did **not**
  engage. CI proof: `code-quality` went green in 8 s, logging `check_session_gate: no new session
  card in this PR — not gated. ✓`, even though the same job's docs-detector had just printed the
  card in its changed-files list.
- **Root cause (two stacked faults, one root):** the session card filename
  `.sessions/2026-06-28-feature-completion-assessments.md` **already existed in `main`** — a *prior*
  dispatch run that day (the Blackjack/Counting completion-assessment run) had used the same slug. So
  this run's `cat > … <<EOF` (and `git add -A`) **clobbered** that prior `complete` log with its own
  `in-progress` content, and git recorded the change as a **modification (`M`)**, not an addition
  (`A`). The gate's discovery used `git diff --diff-filter=A` (added-only) — so a *modified* card was
  invisible to it, the gate found "no new card", failed open, and auto-merge fired on the partial PR.
  The collision also caused **silent data loss**: the prior session's log was overwritten in `main`.
- **Fix (root, PR #1524):**
  1. **Gate now inspects added *or modified* cards** — the merge-gate path uses
     `git diff --diff-filter=AM` (`gate_session_cards`), so a collision-modified born-red card is
     held. A re-badged *old* log (a reconciliation pass flipping a card to `historical`/`archived`)
     is carved out via `_TERMINAL_OK_STATUSES` so reconciliation PRs are never wrongly held. The
     Codex `--require-ready-card` trigger keeps its added-only semantics (it asks a different
     question — "did this PR *add* a card that just went ready?").
  2. **Collision hint** — when the gate holds a card that was modified (not added), it prints
     "this card was MODIFIED, not added — if you reused an existing session slug, rename your card
     to a unique slug", so the next agent fixes the real cause (the slug) rather than the symptom.
  3. **Restored the clobbered prior log** — `.sessions/2026-06-28-feature-completion-assessments.md`
     is restored from git history (commit `a182ac30`); this run's card uses a unique slug
     (`…-games-and-gate-fix.md`).
- **Stays-fixed guard:** `tests/unit/scripts/test_check_session_gate.py` —
  `test_main_modified_card_collision_held_with_hint` reproduces the exact #1523 scenario (a card seen
  by `gate_session_cards` but **not** by `added_session_cards`, status `in-progress`) and asserts the
  gate exits 1 with the rename hint; `test_main_reconciliation_rebadge_not_held` pins the
  reconciliation carve-out (a modified `historical` card merges freely). Both fail against the pre-fix
  added-only gate. Verified directly against the real #1523 SHAs: with the head card content in the
  tree the gate now prints `MERGE HELD` (rc=1).
- **Status:** FIXED (root) 2026-06-28. Checker-only change (no `disbot/` runtime code).

## BUG-0026 — `EffectiveStats.light_radius` and `.luck` are dead stats (gear grants them, no game reads them) — FIXED (wired — owner decision Q-0208)

- **Symptom (found 2026-06-27 by code inspection while building the Q-0089 `EffectiveStats`
  knob-coverage guard, PR #1505 — not a live report, but a real latent gap):** two fields on the
  cross-game `utils/equipment.EffectiveStats` block are **defined, summed (`__add__`), and labelled
  (`STAT_LABELS`/`STAT_GLYPHS`) but read by no game's consumption path**, so the gear that grants them
  does nothing:
  - **`light_radius`** — every torch/lantern grants it (`torch` 1, `lantern` 2, `diamond lantern` 3),
    but mining descent gates only on `depth_access` (`utils/mining/world.py:descend`), never on
    `light_radius`. The "Light" stat shown on the gear panel has zero mechanical effect.
  - **`luck`** — the `diamond pickaxe` (`luck=1`) and the `lucky charm` (`luck=1, loot_bonus=1`) grant
    it, but only `loot_bonus` is read (`utils/mining/exploration.py`). The `luck` half of the lucky
    charm — and the diamond pickaxe's luck — do nothing.
- **Root cause:** the stat fields were added to the shared block ahead of (or without) a consumer — the
  "added the stat, summed it, labelled it, forgot the knob" half-ship class. Every *other* field is
  wired: `mining_power`/`loot_bonus` (exploration yield), `depth_access` (descent gate), `damage`/
  `defense`/`max_health` (the duel), `fishing_power`/`bite_luck` (the cast, #1504).
- **Owner decision (Q-0208, 2026-06-27): WIRE them** (not remove). The owner chose to give the gear that
  grants these stats a real effect, with the mechanics the agent proposed (reversible + sim-pinned).
- **Fix — both wired, byte-identical when the stat is 0:**
  - **`light_radius` → the fog-of-war window.** `utils/mining/grid.reveal_radius(light_radius)` maps the
    summed light to the navigator's reveal half-width; `views/mining/grid_mine_view.build_grid_embed` now
    computes it from the player's `character_stats(...).light_radius` and feeds it to **both** the
    discovered-cell query and the render. **Non-regressive:** light 0–1 → the prior default 2; a lantern
    (2) → 3, a diamond lantern (3) → 4 (capped at 4). A brighter light literally lets you see more of the
    map at once.
  - **`luck` → rare-find weighting.** `utils/mining/exploration.resolve` now biases the weighted outcome
    pick toward rarer finds by `luck` (`_luck_weighted`: Common stays flat, Uncommon ×1.15, Rare ×1.4,
    Legendary ×1.6 per luck point), so the diamond pickaxe's and lucky charm's `luck` makes fortunate
    finds more frequent. **Byte-identical when `luck <= 0`.** Numbers pinned in
    [`docs/planning/mining-luck-light-numbers-2026-06-27.md`](../planning/mining-luck-light-numbers-2026-06-27.md).
- **Stays-fixed guard:** `tests/unit/invariants/test_effective_stats_consumed.py` — its `_UNWIRED_STATS`
  allowlist is now **empty**, so the invariant (every `EffectiveStats` field is read by a `disbot/`
  consumer) *requires* `light_radius` + `luck` to stay wired; the moment a reader is removed the test
  fails. Plus the wiring tests: `test_mining_grid.py::test_reveal_radius_*`,
  `test_mining_exploration.py::test_luck_*`, and
  `test_mining_grid_view.py::test_build_grid_embed_widens_window_with_a_brighter_light`.
- **Status:** FIXED 2026-06-27 (owner-greenlit Q-0208). Live on the next auto-deploy; no data step needed.

## BUG-0025 — hero-card image stranded/lost when navigating into an image-less sub-panel (profile + XP hub) — FIXED (root)

- **Symptom (found 2026-06-25 by code inspection during the visual card-engine H3 adoption audit;
  not a live report, but a visible defect on the showpiece image cards):** navigating from an
  image-card hub into an image-less sub-panel strands or drops the rendered hero card. **Profile:**
  opening **⚙️ Manage settings** from the `/myprofile` card leaves the card image lingering as a stray
  attachment under the (image-less) settings editor, and **◀ Back to card** returns a plain embed
  without its designed hero card. **XP hub:** opening **⚙️ Configure** from the `!xpmenu` rank-card hub
  leaves the rank card lingering as a stray image under the (image-less) config panel.
- **Root cause:** `interaction.response.edit_message(...)` calls that navigate to an image-less panel
  omitted the `attachments` argument. Discord **retains** the prior message attachments when
  `attachments` is not passed on an edit, so the leaving hub's hero card stayed attached under a panel
  that never references it. The profile `back_to_card` leg additionally rebuilt from
  `build_profile_embed` (a plain embed, no `set_image`) without re-attaching the file — losing the card
  on the way back. Every *same-file* image-card transition already passes `attachments` explicitly
  (`ProfileHomeView.refresh`, the XP stat toggles in `_switch_stat`, mining `character_hub`/`gear_panel`,
  `role_menu_view`); the bug was confined to the **cross-panel navigations** that open/return an
  image-less sibling — the two places that forgot the canonical pattern.
- **Three call sites fixed (this PR):**
  1. `views/profile/profile_view.py` `ProfileHomeView.manage` → `attachments=[]` (clear on open).
  2. `views/profile/editor.py` `back_to_card` → re-render via `build_profile_card` + re-attach
     (`attachments=[file]`, or `[]` on a Pillow-less host).
  3. `views/xp/main_panel.py` `_XpHubView.btn_config` → `attachments=[]` (clear on open).
- **Sweep:** a repo-wide check of every view file that both renders an `attachment://` image card and
  calls `edit_message` confirmed these were the only offenders; all other image-card hubs already pass
  `attachments` explicitly.
- **Stays-fixed guard (same PR):** four regression tests, each asserting the `attachments=` payload and
  each failing against the pre-fix behaviour —
  `tests/unit/views/test_profile_card.py::test_manage_clears_the_hero_card_when_opening_the_editor`,
  `tests/unit/views/test_profile_editor.py::test_back_to_card_rerenders_and_reattaches_the_hero_card`
  and `::test_back_to_card_clears_attachments_when_renderer_unavailable`,
  `tests/unit/views/xp/test_xp_hub_panel.py::test_config_button_clears_the_rank_card_attachment`.
- **Status:** FIXED (root) 2026-06-25 (dispatch run).

## BUG-0024 — `test_generated_at_is_deterministic_not_wall_clock` flaky under `pytest -n auto` (real-clock dependent) — FIXED (root)

- **Symptom (observed 2026-06-22, in a full `check_quality.py --full` run during the Q-0195
  state-file-restructure session):** `tests/unit/scripts/test_export_dashboard_data.py::
  test_generated_at_is_deterministic_not_wall_clock` fails intermittently in the parallel
  (`-n auto`) suite, but **passes 3/3 in isolation** on both the working tree and clean
  `origin/main`. Unrelated to the session's docs/script changes (no mechanism connects them).
- **Root cause (confirmed, PR #1291):** `export_dashboard_data._git_meta` runs `git` with
  `timeout=5, check=True`. Under a saturated `-n auto` run a call can time out → `_git_meta` returns
  `{}` → `generated_at` falls back to wall-clock (`datetime.now()`). The test calls `build_data()`
  twice and asserts the two `generated_at` values match — only true when git succeeds both times.
  The **production** logic is correct (commit time is deterministic; the wall-clock fallback is an
  intentional git-absent degrade); the **test** was non-hermetic — the same real-clock class as the
  FIXED BUG-0021.
- **Fix (PR #1291):** make the test hermetic — pin `_git_meta` (clock/source injection, the BUG-0021
  pattern) so the determinism logic runs without a real subprocess that can time out. No production
  change.
- **Stays-fixed guard:** the determinism test now passes deterministically under `-n auto` (verified
  35/35 ×3), and a new `test_generated_at_falls_back_to_wall_clock_when_git_unavailable` covers the
  intentional git-absent fallback branch — so both branches stay tested and the flake cannot recur.

## BUG-0023 — public command counts differ between the bot status embed and the website (354 = 283 prefix · 71 slash vs ~280) — EXPECTED (documented); slash under-coverage = FIXED (root)

- **Symptom (owner-reported, 2026-06-20, live):** the bot's `Bot Online` embed shows **`Commands
  354 (283 prefix · 71 slash)`**, the public website shows **~280**, and `site.json` says **308** —
  "completely different numbers," with "a lot of `/` commands that are mostly duplicates of the
  prefix ones."
- **Where:** bot count = `disbot/services/webhook_reporter.py:_command_counts` (`len(bot.walk_commands())`
  prefix incl. subcommands + `len(bot.tree.walk_commands())` slash). Website count = `botsite/site/app.js`
  rendering `D.COMMANDS.length` from `data.js`, generated by `botsite/site_data.py` from `site.json`
  (`scripts/scan_commands.py` static AST scan).
- **Root cause (three different, all-defensible metrics — not corruption):**
  1. **Live registry vs. source snapshot** — the bot counts what discord.py registered *now*; the
     site counts what the static scan found at the last export.
  2. **Per-surface incl. subcommands vs. unique names** — the bot counts every command object on each
     surface (a dual-surface command is counted in *both* 283 and 71 → "mostly duplicates"); the site
     **dedupes by name** (308 source defs → 280 unique, one page per `#/command/<name>`). Verified:
     source scan = **283 prefix + 25 slash = 308**, prefix matching the bot **exactly**.
  3. **Slash under-coverage (the one real gap — ROOT-CAUSED + FIXED 2026-06-22):** static scan found
     **25** slash, the live tree has **71**. The earlier hypothesis here — *"dynamically-registered app
     commands / context menus / tree additions the AST cannot see"* — was **wrong** (investigated
     2026-06-22: 0 context menus, 0 `tree.add_command`, 0 hybrids in the codebase). The real cause: 6
     cogs (ai · btd6 · btd6_events · btd6_ops · btd6_reference · btd6_strategy) declare their slash
     group as a **class *attribute*** — `ai_app_group = app_commands.Group(name="ai", …)` — with
     subcommands decorated `@ai_app_group.command(…)`. `scan_commands._find_groups` only detected groups
     declared as **decorated methods** (`@app_commands.group`), so it missed these 6 groups **and all 40
     subcommands under them**. Exact reconciliation: **25 standalone + 40 subcommands + 6 groups = 71** =
     the live tree count → every missing command is **statically discoverable** (no runtime-aware
     counting needed; the prior "needs a runtime-aware session" scoping note was based on the wrong
     hypothesis).
- **Fix:**
  - **Count-*difference* (#1 + #2): documentation** — reconciled in
    [`website-explained.md`](../owner/website-explained.md) ("why the counts differ") and the
    [React-migration plan §9](../planning/botsite-react-spa-migration-plan-2026-06-20.md). The *display*
    reconciliation (show the bot's `prefix · slash` breakdown on the site) is still an `app.js`/React
    edit folded into the migration **PR 1**.
  - **Slash under-coverage (#3): root fix (2026-06-22)** — `scripts/scan_commands.py` now detects
    attribute-assigned `app_commands.Group` / `HybridGroup` groups (`_find_attr_groups`), registers
    them so their `@<group>.command` subcommands are scanned (inheriting slash/both), and emits the
    synthesized group record. The scanner's `by_type["slash"]` is now **71** (was 25), matching the live
    tree; the regenerated `site.json` / `dashboard.json` / `data.js` carry the 46 previously-missing
    commands so the website documents them.
- **Stays-fixed guard:** `tests/unit/scripts/test_scan_commands.py` ::
  `test_attribute_assigned_app_command_group_is_scanned` (a sample cog whose slash group + subcommand
  are now scanned — fails against the pre-fix decorator-only behaviour) +
  `test_attribute_app_group_subcommands_counted_in_real_repo` (the real-repo slash total reconciles to
  the bot tree, `>= 70`).
- **Status:** **EXPECTED / documented** for the count *difference* (#1 + #2); **slash under-coverage
  (#3) = FIXED (root) 2026-06-22** (PR #1272).

## BUG-0022 — full test suite rewrites the tracked `botsite/site/data.js` (live-HEAD build sha) → `git add -A` reddens botsite-tests — FIXED

- **Symptom (found 2026-06-21, dispatch run):** an unrelated PR (a tooling/docs fix) reddened **both**
  `botsite-tests` and `code-quality` on `test_committed_data_js_is_in_sync_with_site_json` — the
  committed `botsite/site/data.js` was "stale" vs `site.json`. The data.js in the commit carried the
  session's own HEAD short-sha in its CHANGELOG `build` field while `site.json` still carried the older
  committed sha, so the two disagreed.
- **Expected:** running the test suite (or `check_quality.py --full`) never modifies a tracked repo
  file; a broad `git add -A` cannot accidentally capture a regenerated artifact.
- **Root cause:** `scripts/export_dashboard_data.py main()` wrote the SPA data layer to a **hardcoded**
  `REPO_ROOT/botsite/site/data.js`, ignoring its output args. The CLI tests
  (`test_cli_targets_both_writes_both`, `test_cli_targets_site_writes_only_site_json`) drive `main()`
  with `tmp_path` outputs for dashboard.json + site.json — but data.js was still written to the **real**
  tracked path, stamped with `git rev-parse --short HEAD` (the live session commit, line ~618). So every
  full-suite run silently rewrote the working-tree data.js; the next `git add -A` swept it into the
  commit, desynced from the committed site.json → red botsite-tests.
- **Fix (root):** `main()` now takes a `--data-js-output` arg (default `DATA_JS_OUTPUT_FILE` = the real
  path, so the reconciliation routine's `python3.10 scripts/export_dashboard_data.py` is unchanged), and
  the two CLI tests redirect it to `tmp_path`. The suite can no longer touch the tracked file.
- **Stays-fixed guard:** `tests/unit/scripts/test_export_dashboard_data.py::test_cli_does_not_clobber_tracked_data_js_when_redirected`
  snapshots the real `DATA_JS_OUTPUT_FILE`, runs `main()` with all outputs redirected, and asserts the
  tracked file is byte-identical afterward (fails against the pre-fix hardcoded-path behavior).
- **Status:** FIXED 2026-06-21 (dispatch run, PR #1206). Note for future sessions: this is *why* a stray
  `M botsite/site/data.js` could appear after running tests — that recurrence is now closed at the root.

## BUG-0021 — `test_acquire_lock_or_exit_exits_zero_after_wait_timeout` is flaky under `pytest -n auto` (real-clock dependent) — FIXED

- **Symptom (observed 2026-06-21, dispatch run, during a `check_quality.py --full` mirror):**
  `tests/unit/services/test_runtime.py::test_acquire_lock_or_exit_exits_zero_after_wait_timeout`
  failed once in a parallel (`-n auto`) run, then **passed in isolation** on re-run. A classic
  real-wall-clock flake, not a logic bug — and not caused by the change under test (a docs/tooling PR).
- **Expected:** the test is deterministic regardless of host load / parallel scheduling.
- **Root cause:** the test drives `runtime.acquire_lock_or_exit(boot_wait_seconds=0.05,
  boot_poll_seconds=0.01)` against the **real** `time.monotonic` clock (deliberately un-mocked — the
  inline comment says "Use a tiny budget so the test finishes quickly without mocking time.monotonic"),
  while `asyncio.sleep` is mocked to return instantly. The loop therefore spins doing `try_acquire`
  calls until 0.05 s of real wall-clock elapses, and asserts `try_acquire.await_count >= 2`. Under
  CPU starvation (many parallel xdist workers) the process can be scheduled out so that the 0.05 s
  budget elapses after only **one** attempt → the `>= 2` assertion fails.
- **Proposed fix (test-only — needs no runtime change):** patch `services.runtime.time.monotonic` with
  a controlled fake that returns a deterministic increasing sequence (e.g. `0.0, 0.0, 0.06`), so the
  deadline crosses *after* exactly the intended number of attempts independent of host timing. Mirrors
  the already-mocked `asyncio.sleep` so the whole loop is clock-controlled.
- **Stays-fixed guard:** the same test, made deterministic, run under `-n auto` — it can no longer
  depend on real elapsed time.
- **Status:** FIXED 2026-06-21 (dispatch run, PR #1206) — the test now patches
  `services.runtime.time.monotonic` with a fake clock that only advances when the (already-mocked)
  `asyncio.sleep` runs; one sleep jumps it past the 0.05 s budget, so the loop gives up on exactly the
  second attempt (`assert try_acquire.await_count == 2`, tightened from the timing-dependent `>= 2`).
  No runtime code changed — the production `time.monotonic` path is unaltered. Verified deterministic
  (5× + full file green).

## BUG-0020 — `trim_recently_shipped.py` floor-pointer recompute matches stray `#N` in prose (writes a wrong "Older merges (#HIGH … #LOW)" span) — FIXED

- **Symptom (caught 2026-06-20, seventeenth Q-0107 reconciliation pass, first real use of the actuator):**
  after `scripts/trim_recently_shipped.py --apply` moved the 8 oldest Recently-shipped bullets to the
  archive, it recomputed the floor pointer as **"Older merges (#1170 … #1)"** — both ends wrong. The true
  archive span is **#1129 … #535**.
- **Expected:** the recomputed `(#HIGH … #LOW)` pointer should reflect the **highest/lowest archived PR
  *bullet*** — not any `#N` token anywhere in the archive prose.
- **Root cause:** the pointer recompute scans the *whole* archive for `#\d+` and takes min/max over **all**
  matches, so it picks up non-bullet references: `#1170` came from a parenthetical note
  (`*(Trimmed … band-#1170 …)*`, archive L123) and `#1` came from rank/list notation in prose
  (`#1`, `#1,` at L883/972/973/1216). The tool's own docstring warns the floor pointer "is the fragile
  part" — confirmed.
- **Proposed fix (tooling — for a dispatch run, needs a test so out of this docs-only pass's scope):**
  recompute the span from **only the leading PR id of each archived bullet** — i.e. numbers matched by the
  bullet regex `^- \*\*#(\d+)` (the same anchor the ledger checker uses), never free-floating `#N` in prose.
  Add a regression test in `tests/unit/scripts/` that feeds an archive whose prose contains a stray high/low
  `#N` and asserts the computed span ignores it.
- **Stays-fixed guard (to ship with the fix):** the `tests/unit/scripts/` case above, failing against the
  current all-`#N`-match behavior.
- **Status:** FIXED 2026-06-21 (dispatch run, PR #1206) — root fix: `_rewrite_floor` now derives the span
  from a new `_archive_span_numbers(archive_text)` helper that reads **only archived bullet headers**
  (`^- \*\*#…`), taking each bullet's leading `#A · #B …` cluster (the run before the first ` (` date paren
  or `**` bold close). Grouped non-monotonic bands (`#690 · #721`) still contribute their newest member;
  free-floating `#N` in prose (a `band-#1170` note, a `#1` rank token) no longer widens the span.
  Stays-fixed guard: `tests/unit/scripts/test_trim_recently_shipped.py::test_floor_pointer_ignores_stray_pr_refs_in_prose`
  feeds an archive whose prose carries a stray high (`band-#9999`) + low (`#1`) `#N` and asserts the
  recomputed span ignores both. The Q-0105 "keep an eye on it" note stands for the *rest* of the actuator,
  but its one mis-writing failure mode is now closed at the root with a regression test.

## BUG-0019 — AI replies to messages aimed at *other* bots and claims "you've just pinged me" — PARTIALLY FIXED (mechanism #2 hardened; #1 awaits one owner behavior decision)

- **Symptom (owner-reported, 2026-06-20, live in a community server):** a user pinged
  **another** bot — `@Carl-bot (?)` — in a channel, and **SuperBot replied anyway**: *"Hey!
  You've just pinged me. What can I help you with? … feel free to ask me anything…"*. The
  owner's words: *"the AI is responding to mentions of other bots."* Context: the report user
  cited this as a reason he still runs multiple bots.
- **Expected:** SuperBot should **not** barge into a message clearly addressed to a different
  user/bot, and should **never** claim it was "pinged" when it was not directly mentioned.
- **Where:** `disbot/core/runtime/ai/natural_language_stage.py` (the single "should the bot
  reply?" stage) + `disbot/services/ai_natural_language_policy.py` (the mode gate).
- **Root cause — two independent mechanisms (the screenshot is almost certainly #1):**
  1. **`always_reply` ambient mode answers *everything*.** A channel/category/guild AI profile
     with `mode="always_reply"` (`ai_natural_language_policy.py:122,343`) responds to **every**
     message regardless of who it addresses — so a message that only pings `@Carl-bot` still gets
     a reply. The mode gate only special-cases `mention_only` (requires a mention) and `disabled`;
     `always_reply` has **no "is this addressed to someone else?" guard**. Separately, the model
     produced a *"you've just pinged me"* greeting for a low-content message even though SuperBot
     was **not** in `message.mentions` — i.e. the prompt/context does not tell the model "you were
     NOT actually mentioned; another user/bot was," so it hallucinates the ping framing. (We strip
     *SuperBot's own* mention from the text — `_strip_bot_mention` — but leave **other** users'
     mention tokens in, so the model still sees a `<@id>` and reads it as a ping at itself.)
  2. **`mentioned_in` treats `@everyone`/`@here` as a direct ping (latent footgun).**
     `natural_language_stage.py:229` — `is_mention = ctx.bot.user.mentioned_in(message)`.
     discord.py's `mentioned_in` returns **True when `message.mention_everyone` is set**, so a
     server-wide `@everyone`/`@here` reads as "the bot was personally pinged" and flips the
     `mention_only` gate open. Independent of the screenshot, but the same "false personal ping"
     class.
- **Proposed fix (needs one owner behavior decision — see flag):**
  - **#2 is unambiguous → hardening — DONE (2026-06-20 dispatch run):** `is_mention` is now computed
    by `natural_language_stage._is_direct_bot_mention(message, bot_user)` — membership of the bot's
    own id in `message.mentions` — replacing the `ctx.bot.user.mentioned_in(message)` call (which
    short-circuits `True` on `message.mention_everyone`). A server-wide `@everyone`/`@here` blast no
    longer reads as a personal ping and so can no longer flip the `mention_only` policy gate open.
    The helper is defensive (missing bot id / non-iterable `mentions` → `False`, never raises).
    **Stays-fixed guard (same PR):** `tests/unit/runtime/ai/test_natural_language_stage.py` ::
    `test_everyone_blast_is_not_a_personal_ping` (+ `…_direct_bot_mention_is_a_personal_ping` /
    `…_mention_of_another_user_or_bot…` / `…_direct_mention_alongside_everyone…` /
    `…_missing_bot_id_or_uniterable_mentions…`) — the everyone-blast case fails against the old
    `mentioned_in` path. **Mechanism #1 is untouched** (the `always_reply` design fork below).
  - **#1 is a design fork (the owner's call):** in `always_reply` mode, should SuperBot
    **(a)** stay silent when a message mentions another user/bot and **not** SuperBot (don't barge
    into others' conversations — the most likely intended behavior), **(b)** keep answering
    everything but **strip *all* mention tokens** before the model and pass an explicit
    `is_mention=False` framing so it never says "you pinged me", or **(c)** leave `always_reply` as
    a power-user opt-in and only fix the "pinged me" copy? These change ambient semantics the owner
    configured intentionally, so they are flagged, not patched unilaterally.
- **Stays-fixed guard (to ship with the chosen fix):** a `natural_language_stage` unit test that a
  message pinging only another user/bot (and `@everyone`) does **not** set `is_mention` / does not
  trigger a reply under the chosen rule. (Live AI path → also wants a Q-0086 runtime walk.)
- **Status:** PARTIALLY FIXED — mechanism **#2** (the `@everyone`/`@here` false-personal-ping
  footgun) was root-fixed + regression-guarded 2026-06-20 (dispatch run); it was offline-unit-
  testable and unambiguous, so it shipped on its own. Mechanism **#1** (the `always_reply`
  ambient-mode "barge into others' conversations" design fork) stays **OPEN, routed to the owner**
  (agent recommendation: option **(a)** — stay silent when a message pings another user/bot and not
  SuperBot) — it changes ambient semantics the owner configured intentionally and wants a
  Q-0086 runtime-verified session, so it is not patched unilaterally.

## BUG-0018 — committed `botsite/data/site.json` drifts red whenever idea docs change (hard equality test over a high-churn derived field) — FIXED (root)

- **Symptom:** `tests/unit/scripts/test_export_dashboard_data.py::test_committed_site_json_matches_a_fresh_build`
  failed on `main` — `commands drifted — re-export`. The committed `site.json`'s
  `commands[].linked_ideas` no longer matched a fresh build.
- **Where:** `botsite/data/site.json` (committed generated artifact) vs.
  `scripts/export_dashboard_data.py:build_site_subset` (its producer). The test asserts
  byte-equality (modulo volatile `meta`) of the `counts`/`catalogue`/`commands`/`bot_changelog`
  families.
- **Root cause:** `commands[].linked_ideas` is **derived from `docs/ideas/`**, which churns far
  more often than `site.json` is regenerated. Every idea-doc PR that adds/restatuses an idea
  linked to a command (here #1115/#1124/#1126's idea additions) silently drifts `site.json`, so
  the **hard** equality test goes red between regenerations — a recurring trap, not a one-off.
  The drift was 963 insertions / 80 deletions, **all** `linked_ideas` (status/title) + meta.
- **Fix (immediate, this PR):** regenerated the artifact — `python3.10 scripts/export_dashboard_data.py
  --targets site` — bringing the committed file back in step; the test (and the full suite) go green.
- **Stays-fixed guard:** the failing test itself **is** the guard (it failed pre-regen, passes
  after). No new test needed.
- **Root-fix DONE (recommendation (a), 2026-06-19 dispatch run):** a hard byte-equality test over a
  high-churn derived field would keep reddening `main` on every idea-doc PR. Implemented (a):
  `test_committed_site_json_matches_a_fresh_build` now **excludes the idea/bug-derived command fields
  (`linked_ideas` *and* `status`)** from the hard `commands` comparison — the stable command fields
  (name/aliases/category/cooldown/permissions/usage/description/use_cases/examples/notes) stay pinned.
  Both excluded fields derive from `docs/ideas/`/the bug book (`status` flips `finished`↔`in-progress`
  with a subsystem's open work), so both churned. Their structural identity is already covered by the
  **warn-only** generated-artifact freshness umbrella (`check_generated_artifacts_fresh.py`, #1027) —
  the "a generated file rotted" class it exists for (Q-0105). Option (b) (auto-regen in CI) was not
  taken: it would re-introduce a per-PR churn commit the umbrella avoids.
- **Stays-fixed guard:** the relaxed test still fails on any *stable*-field drift (a real un-exported
  source change); the freshness umbrella warns on derived-field identity drift. The original immediate
  regen guard is preserved for the stable families.
- **Status:** FIXED (root) 2026-06-19 (dispatch run) — the recurring trap is closed at the test
  contract, not just regenerated.

## BUG-0017 — interactive Cog Manager dropdown silently drops cogs past the 25th (`options[:25]`) — FIXED

- **Symptom:** the owner Cog Manager panel (`!coglist` / Admin hub → 📋 Cog List) lists every
  `*_cog.py` in a single Discord select, but a select caps at **25** options. There are currently
  **46** cogs, so the panel could only ever show the first 25 (alphabetically); the **22** cogs
  sorting from `health_maintenance_cog` onward (… `image_moderation`, `inventory`, `leaderboard`,
  `logging`, `mining`, `moderation`, `paragon`, `role`, `security`, `settings`, `setup`, `welcome`,
  `xp`, …) were **unreachable** from the panel — the owner had to fall back to the `!cog <op> <name>`
  prefix escape hatch.
- **Where:** `disbot/cogs/admin/cog_manager.py` — `_CogManagerSelect.__init__` did
  `options=options[:25]  # Discord cap`, front-truncating instead of paginating.
- **Root cause:** the #1040 **select-option-truncation class** (silent front-truncate of a
  >25-item collection feeding a `Select`), here in the **cog layer** — which the consistency
  linter's `select_option_truncation` rule does **not** scan (it is scoped to `views/`), so the
  guard that exists for exactly this class never saw it.
- **Fix (root, one source of truth):** replaced the bespoke `_CogManagerSelect` + `options[:25]`
  with the project's windowing primitive `views.paginated_select.attach_windowed_select` (◀ Prev /
  Next ▶ paging), so the **full** cog list stays selectable (`select_row=0`, `nav_row=3` leave the
  Load/Unload/Reload row, the Refresh row, and the opener's row-4 Back button clear). Option-building
  moved to a module-level `_build_cog_options(loaded)` helper.
- **Stays-fixed guard (same PR):** `tests/unit/cogs/test_admin_cog_manager.py` ::
  `test_cog_manager_view_windows_more_than_25_cogs_no_silent_drop` — asserts the visible page is
  capped at 25 **and** that ◀/▶ paging is present when >25 cogs exist (fails against the old
  `options[:25]` behaviour, which exposed no nav). Plus `…_cog_select_callback_stashes_selection…`
  pins the new windowed-select callback.
- **Follow-up (routed) — DONE 2026-06-19 (dispatch run):** the linter blind spot itself was closed.
  `scripts/check_consistency.py` rule scope is now **per-rule** (`Rule.roots`); `select_option_truncation`
  (rule 4) and `panel_base_class` (rule 3) carry `roots=("views/", "cogs/")`, so a cog-layer truncation
  or direct-`discord.ui.View` panel is now caught in CI (both rules are GRADUATED → `--mode strict`).
  Extending scope surfaced 7 existing cog-layer findings, all triaged to 0 (2 spotlight top-N embed
  displays + 5 documented specialized-lifecycle cog views — allowlisted in
  `consistency_exceptions.yml`); rules 1+2 stay `views/`-only by design.
- **Status:** FIXED 2026-06-19 (dispatch run) — found by code inspection while gauging the
  "extend rule 4 to cogs" candidate; fixed at the root the same session, and the routed linter-scope
  follow-up shipped the same day (above).

## BUG-0016 — reconciliation-trigger workflow issue-body says "multiple-of-20" / "next ~9 PRs" (stale cadence copy) — FIXED

- **Symptom:** the auto-opened `reconcile` trigger issue (e.g. #1095) reads *"A multiple-of-20 PR
  band was crossed"* and *"plans the next ~9 PRs"*. Both numbers are stale: the Q-0107 cadence was
  raised 20 → **30** (Q-0134, 2026-06-14) and the planning horizon is the **full band** (depth ≥ the
  cadence, Q-0164), not "~9 PRs".
- **Where:** `.github/workflows/reconciliation-trigger.yml` — the comment on **L4** and the
  `--body $'…'` string on **L73**. The *firing logic* is correct (it keys off
  `scripts/check_reconciliation_due.py`, which uses 30); only the human-readable copy drifted.
- **Impact:** cosmetic only — no behavioral effect (the band still fires at the right boundary). It
  misleads a reader/agent about the live cadence + planning depth.
- **Fix (not docs-only — out of scope for the Q-0107 pass):** change "multiple-of-20" → "30-PR band"
  and "next ~9 PRs" → "next full band" in both spots. A dispatch routine (full write scope) can land
  it in one tiny PR. No regression guard needed (a string); optionally have
  `check_reconciliation_due.py`'s message be the single source the workflow echoes.
- **Status:** FIXED — the dispatch run (2026-06-19) updated both spots: the header comment now
  reads "cadence raised 10 → 20 … then 20 → 30 per Q-0134 … cross a 30-PR band" and the issue
  `--body` reads "A 30-PR band was crossed … plans the next full band (depth ≥ the cadence,
  Q-0164)". Added a one-line note in the workflow header that `check_reconciliation_due.py`
  (`STEP = 30`) owns the firing boundary and the copy must track it. No regression guard (a
  string; the firing logic was already correct and is covered by the script's own tests).
- **Root-cause hardening (follow-up dispatch run, 2026-06-19):** the first fix corrected the
  copy but left it hardcoded in the workflow — the *drift class itself* (two places that must be
  kept in sync) remained. Eliminated it: `check_reconciliation_due.py` now owns the canonical
  body too (`issue_body()`, built from `STEP`, exposed via `--issue-body`), and the workflow
  **echoes** it (`--body "$(python3.10 scripts/check_reconciliation_due.py --issue-body)"`)
  instead of carrying a copy. The cadence numbers now live in exactly one place and can never
  desync again. Guarded by `test_issue_body_tracks_the_live_cadence` /
  `test_issue_body_flag_prints_body_and_exits_zero`.

## BUG-0015 — "d67 dart paragon" misread as upgrade path "0-6-7" (paragon degree ignored) — FIXED

- **Symptom (owner-reported via screenshot, 2026-06-16):** asked *"whats the damage
  of a **d67 dart**"* and *"a **d67 dart praragon**"*, SuperBot replied *"A 0-6-7
  Dart Paragon doesn't exist — upgrade tiers cap at 5, so the maximum is 0-5-5."*
  It read the shorthand **"d67" = degree 67** as an upgrade-path code "0-6-7".
  Paragons have **degrees 1-100** (the Apex Plasma Master is the Dart Monkey
  paragon); "d67" is the degree, not a crosspath.
- **Affected surface:** the AI natural-language path — `services.ai_task_router`
  (routing), `services.btd6_context_service` (grounding),
  `services.ai_instruction_service` (the model contract), and the shared cue in
  `utils.btd6.keywords`.
- **Root cause (two stacked gaps — the BUG-0003/0004 "freelance on the unguarded
  general path" class):** (1) **Routing** — `classify("a d67 dart praragon")`
  returned `GENERAL_NL_ANSWER`: no keyword matched (`paragon` is deliberately
  excluded as ordinary English), no entity matched (the single-word tower "dart"
  is deliberately dropped by the entity matcher), and no round/money/follow-up
  cue fired. The general path has **no grounding and no number guard**, so the
  model answered from memory and misread the shorthand. (2) **Grounding** — even
  on the BTD6 path, `_render_paragon_stats` only anchors **Degree 1 and Degree
  100**, so there was no degree-67 figure and nothing told the model "d67" is a
  degree. The exact-degree machinery already existed
  (`utils.btd6.paragon_degrees`, `_paragon_main_bits`,
  `btd6_stats_service.paragon_stats_at_degree`) — only the parse → route → ground
  legs were missing.
- **Fix (this PR — three coordinated layers):** (1) `utils.btd6.keywords` gains
  `DEGREE_CUE_RE` + `degree_in_text()` — one shared cue (the `ABR_CUE_RE`
  pattern) recognising "d67" / "degree 67" / "deg 67", digit-boundary guarded so
  a round ("r67") / version ("v55") / dice ("5d6") / temperature ("67 degrees")
  never matches, range-checked to 1-100. (2) `ai_task_router._looks_like_paragon_degree`
  routes a degree token **+** a paragon reference (the word "paragon", or a
  tower/paragon that resolves) to `btd6.answer`; a bare "degree 5" with no
  paragon stays general. (3) `btd6_context_service._paragon_degree_facts` (new
  Pass 3b3) grounds the in-scope paragon's exact, **non-linear** headline at the
  requested intermediate degree, explicitly labelled "Degree N", plus a note that
  a degree is NOT an upgrade-path code. (4) `ai_instruction_service` task contract
  gains one clause teaching the model the "d67"/"degree 67" shorthand (defense in
  depth for the production tool path). D1/D100 stay the `_render_paragon_stats`
  anchors (no duplication).
- **Regression tests:** `tests/unit/utils/test_btd6_keywords_degree.py` (the
  parser: recognises the forms, rejects round/version/dice/temperature/out-of-range) ·
  `test_paragon_degree_questions_route_to_btd6_answer` +
  `test_degree_without_paragon_or_paragon_without_degree_stays_general`
  (`tests/unit/services/test_ai_task_router_btd6_natural.py` — routes the
  screenshot phrasings, conservatism negatives) ·
  `test_paragon_degree_facts_*` (`tests/unit/services/test_btd6_paragon_stats.py`
  — grounds the exact non-linear degree, skips the D1/D100 anchors, stays silent
  without both signals, names a directly-named paragon too).
- **Status:** FIXED — live on the next auto-deploy (a merge to `main` auto-deploys
  to Railway). The fix is deterministic (parse/route/ground) — no `!btd6ops
  seed-data` step needed (no data file changed).

## BUG-0014 — `!coglist` infinite "assumed from" command-resolution loop — FIXED

- **Symptom (owner-reported via screen recording, 2026-06-16):** typing `!coglist`
  (or `!cogs`) made SuperBot spam "↩️ Ran `!coglist` — assumed from `!coglist`."
  **endlessly — it did not stop until the bot was restarted.** A runaway message
  loop (channel spam + rate-limit risk).
- **Affected surface:** `bot1.on_command_error` (the `CommandNotFound` typo-resolver
  re-dispatch) + the data in `disbot/utils/synonyms.py`.
- **Root cause:** `COMMAND_SYNONYMS` declared `"coglist": ["listcogs", "cogslist"]`,
  but **no `coglist` command is registered** (audited: the only orphaned canonical of
  32). So `command_resolution.classify` fuzzy-matched the typed token to the phantom
  canonical `coglist` and returned `Outcome.AUTO`; `on_command_error` rewrote the
  message to `!coglist` (the *same* token) and re-dispatched via `process_commands`;
  `!coglist` still wasn't a real command → `CommandNotFound` → re-resolved to the same
  phantom → **infinite loop.** The amplifier was structural: the handler re-dispatched
  an AUTO correction without checking the target actually exists or differs from input.
- **Fix (this PR):** (1) **loop-breaker** — `on_command_error` only re-dispatches an
  AUTO correction when it is a *registered* command (`bot.get_command`) *different* from
  the raw token; an unsafe/identity/phantom correction falls through to the normal
  not-found reply (makes the loop class impossible regardless of synonym data). (2)
  removed the orphaned `coglist` synonym. (3) **CI invariant** —
  `tests/unit/invariants/test_command_synonyms_resolve_to_real_commands.py` AST-asserts
  every `COMMAND_SYNONYMS` canonical is a registered command name/alias, so an orphan
  can't ship again.
- **Regression test:** `tests/unit/test_bot1_command_resolution_loop.py` — phantom and
  identity AUTO corrections do NOT re-dispatch (single terminal not-found reply); a
  valid correction (registered + different) still auto-runs exactly once. Plus the
  synonym-orphan invariant above (verified to flag the re-added `coglist`).
- **Status:** FIXED — live on the next auto-deploy (a merge to `main` auto-deploys to Railway).

## BUG-0013 — 1v1 challenge timer keeps running after accept, overwrites the live duel — FIXED

- **Symptom (owner-reported via Hermes, 2026-06-16):** "there is a problem with
  the deathmatch cog, the 1v1 vs player command accept timer seems to keep
  running while a match is active, and even when a match is completed it will
  default to 'player didn't respond in time etc'." The accept/decline challenge
  prompt's 30-second timer kept firing after the challenge was answered, replacing
  the live (or already-finished) duel message with "⚔️ Challenge Expired — did
  not respond in time."
- **Affected surface:** `_ChallengeView` in `disbot/cogs/deathmatch_cog.py` (the
  accept/decline pre-match view). `_DuelView` was never the problem — it already
  guards on `duel.is_over`.
- **Root cause:** `_ChallengeView` is created with `timeout=30.0`, but
  `btn_accept()` (which starts the real `_DuelView`) and `btn_decline()` **never
  called `self.stop()`**, and `on_timeout()` had **no guard** for an
  already-answered challenge. So the challenge view lived on in the background;
  when its timeout fired, `on_timeout()` edited its message — the *same* message
  that now showed the duel — to the expired notice.
- **Fix (this PR):** `btn_accept`/`btn_decline` set a `_resolved` flag and call
  `self.stop()` (which cancels the pending timeout); `on_timeout()` returns early
  when `_resolved` (belt-and-suspenders for the race where the timeout was already
  firing). **Diagnosis credit:** the Hermes `intake` skill (gpt-5.4-mini)
  root-caused this correctly from the live report — its first real bug, end to
  end.
- **Regression test:** `tests/unit/cogs/test_deathmatch_challenge_timeout.py` —
  accept and decline stop the view + guard a late `on_timeout`; an un-answered
  challenge still expires (no regression).
- **Status:** FIXED.

## BUG-0012 — counting staff check trusts role *names*, not permissions (privilege bypass) — FIXED

- **Symptom (owner-reported, 2026-06-14):** "you could give yourself a role
  called 'admin' while the admin role did not have any actual permissions — the
  fact that it was named 'admin' overruled the bot's permission system and
  allowed users to execute admin commands." A non-privileged member who holds
  (or can self-assign) a **cosmetic role merely named** `Admin` or `Moderator`
  — carrying zero Discord permissions — passed the counting staff gate.
- **Affected surface:** `CountingCog.is_staff_or_owner` (`disbot/cogs/counting_cog.py`),
  which gates the `@staff_or_owner()`-decorated counting management commands
  (`!countingmenu`/`!cm` and siblings). Scope was limited to the counting cog;
  every other cog already gates on real permissions
  (`@commands.has_permissions(...)`) or the governance visibility tier.
- **Root cause:** the check was `staff_roles = ["Admin", "Moderator"]; return
  any(role.name in staff_roles for role in ctx.author.roles)` — a **role-name
  string match**, never the role's actual permissions. Discord role names are
  arbitrary and self-assignable, so the name `"Admin"` granted authority a
  powerless role does not actually carry. This is the owner's "missing bindings"
  class: with no permission/binding check, authority fell back to a name. The
  gap was **noted as a code-quality observation since 2026-06-05**
  (`docs/audits/general-feature-layer-analysis-2026-06-05.md` §"Counting uses
  hardcoded role names") but never recognized as a security issue or fixed.
- **Impact:** privilege escalation within the counting subsystem on any guild
  where a non-privileged member can obtain a role named `Admin`/`Moderator`.
  No data-loss path, but it defeats the permission model for that surface.
- **Fix (PR — this entry):** `is_staff_or_owner` now resolves the member's
  **real** tier via the canonical `utils.visibility_rules.get_member_visibility_tier`
  (which reads `guild_permissions`: `administrator` / `moderate_members` /
  guild-owner) and requires `is_tier_sufficient(tier, "moderator")`; the bot
  owner still short-circuits true. A role *name* now confers nothing.
- **Regression test:** `tests/unit/cogs/test_counting_permissions.py` — pins
  that a powerless role named `Admin`/`Moderator` is denied, while real
  administrator / moderator / bot-owner / guild-owner are allowed and a plain
  member is denied.
- **Process note:** this bug had been captured by a routine as a vague
  *permissions-arrangement review* idea in `docs/ideas/` (PR #834) — the wrong
  home for a concrete bug. It belongs here in the bug book; #834 should be
  closed (or refocused into a router DISCUSS item if a broader permission-model
  audit is still wanted).
- **Status:** FIXED — root-caused + fixed + regression-tested 2026-06-14.

## BUG-0011 — Hermes gateway crash-loops on restart (Telegram 409) + periodic status=1 — OPEN

- **Symptom:** the `hermes-gateway` systemd service exits `Main process exited, code=exited,
  status=1/FAILURE` on (a) **every `systemctl restart`** — the new instance starts, prints the
  "Messaging platforms + cron scheduler" banner, then dies within ~1s — and (b) **periodically**
  while running (observed unprompted at 2026-06-12 20:41 and 22:31 UTC, hours apart). `Restart=always`
  (RestartSec=10) recovers it each time, so `is-active` reads `active` and service stays usable,
  but the red `status=1` noise repeatedly obscured real diagnosis during the 2026-06-12 Discord
  setup (it masked, then was confused with, the genuine `PrivilegedIntentsRequired` Discord error).
- **Likely root cause (unconfirmed):** Telegram **409 Conflict** — on restart the new instance
  begins long-polling `getUpdates` while the old instance's poll is still held briefly by
  Telegram's side, so the new one exits. The 2026-06-12 systemd-unit fix (TimeoutStopSec ≥ drain)
  reduced but did not remove it. The periodic (non-restart) crashes are unexplained — one was
  preceded by a "Self-improvement review: User profile updated" log line; needs a clean foreground
  repro (`systemctl stop` then `hermes gateway`) to capture the actual exit cause.
- **Impact:** cosmetic + self-healing today (control plane, low traffic), but: noisy logs,
  ~10–15s Telegram/Discord drop on each restart, and it actively hindered diagnosis. Worth fixing
  before the gateway becomes more load-bearing.
- **Candidate fixes:** confirm the 409 theory from a clean foreground run; on restart, have the
  adapter **retry on 409** instead of exiting, or lengthen the drain so the old poll fully closes
  before the new instance starts; investigate the periodic non-restart crashes separately.
- **Status:** OPEN — captured 2026-06-13 during the Hermes dual-platform setup session.

## BUG-0010 — the "in ABR" qualifier is ignored by auto-grounding and the round-cash workflow

- **Reported:** 2026-06-11 ~15:06–15:07 (owner, Haiku round): "how much cash
  do I get in ABR from r25 to r83 when I have double cash and I started with
  5443" → honest but **underclaiming** answer (served the standard $107,164.60
  correctly labeled "that's not ABR", then claimed the calculator can't do
  ABR — it can); "how much RBE is in r87 in ABR" → floored (the reply's
  honest "Alternate Bloons Rounds" naming wasn't in the haystack).
- **Probe evidence:** both phrasings route `btd6.answer` and the workflow
  MATCHES the range — but every grounded `[btd6_round]` fact and the workflow
  plan are **standard-roundset** (r87 grounds standard's 4-ZOMG/66,624-RBE
  round, not ABR's). The guard accidentally protects today: the mislabel
  can't pass because ABR facts are never in the haystack — so the failure
  mode is refusal, not a wrong number.
- **What already works:** the dataset carries all 140 ABR rounds
  (`abr_rounds.json`); the `btd6_round_composition` and round-cash TOOLS take
  `roundset='abr'` (the capabilities list advertises it). Only the
  deterministic legs lack the qualifier.
- **Fix sketch (focused slice):** (1) an ABR cue ("abr", "alternate bloons")
  in the resolver/grounding round legs → resolve round numbers against
  `abr_rounds` and label the lines `[ABR]`; (2) `RoundCashPlan` gains a
  `roundset` field + matcher cue so the workflow computes/labels the ABR
  range; (3) regression: the two live phrasings above.
- **Fix (follow-up session, same day):** one shared `ABR_CUE_RE`
  (`utils/btd6/keywords.py`) consumed by both legs. Grounding: the round
  legs re-fetch each resolver-matched round via `get_round(n, roundset="abr")`
  and stamp **every** line `Round N (ABR)` with an ABR economy note (no
  silent standard-as-ABR possible; a missing ABR entry says so explicitly).
  Workflow: `RoundCashPlan` gained `roundset` + `unsupported_modifier`; the
  matcher parses the cue and the named cash modifier; all three executors
  compute on the plan's roundset, label the economy in `result_text`, carry
  `roundset` in the evidence inputs/id, and emit an explicit "<modifier> is
  NOT applied" warning. Live phrasing now answers deterministically:
  **$113,872.30** ABR rounds 25-83 (≈ $119,315.30 projected with the stated
  $5,443) + the double-cash warning; "r87 in ABR" grounds **83,280 RBE /
  5 ZOMG (ABR)** instead of standard's 66,624 / 4 ZOMG.
- **Regression tests:**
  `test_plan_abr_qualifier_and_modifier_production_phrasing` ·
  `test_run_abr_range_uses_abr_economy_and_flags_modifier` ·
  `test_standard_phrasings_stay_default_roundset` ·
  `test_abr_qualifier_grounds_abr_round_entries` · live-battery
  `knowledge.btd6_abr_range_cash_bug_0010`.
- **Status:** FIXED — follow-up session 2026-06-11 (the PR after #707).

## BUG-0009 — grounded facts, wrong assembly: lists mislabeled / badly grouped (the claim-assembly class) — PARTIALLY FIXED (MK-related family)

- **Reported:** 2026-06-11 ~14:07–14:18 (owner, first Q-0086 live session):
  "what are all the monkey knowledges related to the farm" listed the whole
  Support MK category as "related to the Banana Farm" (Big Traps/One More
  Spike/Vigilant Sentries are Engineer/Spike Factory); owner verdict on the
  list-style answers broadly: *"some of these are correct but most of them
  are either slightly wrong or badly grouped etc"* (Geraldo per-level
  groupings, "3 newest towers" ordering, mode groupings).
- **Root cause:** the faithfulness guard checks **values, not claims** —
  every name/number is individually grounded, but the *grouping/labeling/
  ordering* is model-assembled. Third member of the BUG-0002/0004 mislabel
  class; the proven fix shape is "the deterministic layer owns the labeled
  answer" (rosters and the capabilities reply already work this way).
- **Direction (plan-level, not a quick patch):** deterministic list-answer
  builders for the high-traffic list families — "MK related to X" (filter MK
  by entity mention), per-level item lists, newest-towers — served as
  grounding blocks or floor replies. Route: AI orchestration plan §7
  families.
- **Fix — slice 1: the "MK related to <tower>" family (PR #924):** the model
  no longer assembles this list. `btd6_data_service.monkey_knowledge_referencing(tower)`
  derives the relation deterministically — an MK *references* a tower when its
  in-game description names the tower's canonical name or an upgrade-path name
  (strong) or a recognised alias (weak, suppressed when the MK strongly
  references a *different* tower, or is a Powers/Heroes-tab point that modifies
  a power/hero rather than the tower). `btd6_context_service.deterministic_mk_reference_reply`
  detects the "which MK relate to <tower>" shape (MK cue + relation/list cue +
  resolvable tower; `None` for single-MK lookups / strategy / no-tower) and
  formats the honest labelled answer ("…that reference the Banana Farm (7) —
  these name the Banana Farm or one of its upgrades"). It is served as a
  **pre-emptive floor on the BTD6 path** (`natural_language_stage`), *before*
  the model — this class **passes** the value-only faithfulness guard, so the
  existing post-hoc roster floor never caught it. The owner's exact case is
  fixed: "all monkey knowledges related to the farm" now lists the 7 genuinely
  farm-referencing MK, never the whole 22-entry Support category.
- **Regression tests:** `tests/unit/services/test_btd6_mk_reference.py`
  (relation + reply, incl. farm-not-whole-category, road-spike-Powers
  excluded, conservatism) · `test_mk_reference_question_floored_before_model`
  + `test_non_mk_btd6_question_still_reaches_model`
  (`tests/unit/runtime/ai/test_natural_language_stage.py` — the pre-emptive
  short-circuit, and that ordinary BTD6 questions still reach the model).
- **Fix — slice 2: the "Geraldo items per level" family (PR #926):** the model
  no longer assembles the level→item grouping (it mislabelled which item unlocks
  at which Geraldo level — every name grounded, so the value-only faithfulness
  guard passed the wrong *grouping*). `btd6_data_service.geraldo_items_by_unlock_level()`
  owns the deterministic ascending level→items map;
  `btd6_context_service.deterministic_geraldo_per_level_reply` detects the
  per-level / by-level / "level N" shape (Geraldo cue + level/list cue; `None`
  for single-item lookups like "what does the Genie Bottle do" and strategy
  questions) and formats either the whole grouping or a single level's unlocks
  (an empty level answers honestly — "no new item unlocks at level N"). Both
  BUG-0009 builders now front a single dispatcher
  `btd6_context_service.deterministic_btd6_list_reply` served as the pre-emptive
  BTD6 floor in `natural_language_stage` (MK first, then Geraldo) — slice 3
  (newest-towers ordering) appends its builder there.
- **Regression tests:** `tests/unit/services/test_btd6_geraldo_per_level.py`
  (grouping ascending/complete/level-0 starting items · full-list + single-level
  + empty-level replies · single-item/strategy/non-Geraldo fall-through · the
  dispatcher routing both families and falling through on an ordinary question) ·
  `test_geraldo_per_level_question_floored_before_model`
  (`tests/unit/runtime/ai/test_natural_language_stage.py` — the pre-emptive
  short-circuit through the unified dispatcher).
- **Fix — slice 2b: the "game mode groupings" family (PR #926):** the owner's
  third named mislabel ("mode groupings" — the model calls a *difficulty* a
  *mode*, etc.). `btd6_data_service.modes_by_kind()` owns the deterministic
  kind-grouping (difficulty → mode → modifier, BTD6's own `ModeEntry.kind`
  split); `btd6_context_service.deterministic_modes_reply` fires on a clear
  modes enumeration (mode/difficulty cue + the roster floor's strong list-intent
  cue) and is guarded against the qualifier over-route — a message naming
  another roster entity ("which towers work on impoppable **mode**") defers to
  the model. Appended to the `deterministic_btd6_list_reply` dispatcher after MK
  and Geraldo. CHIMPS is now always grouped as a mode, Easy/Medium/Hard as
  difficulties.
- **Regression tests:** `tests/unit/services/test_btd6_modes_grouping.py`
  (grouping order/coverage/kind-assignment · CHIMPS-is-a-mode-not-a-difficulty ·
  list / how-many / what-are-all replies · single-mode + qualifier + strategy +
  non-modes fall-through · the dispatcher routing the modes family).
- **Status:** PARTIALLY FIXED — the **MK-related** (#924), **Geraldo per-level**
  (#926), and **game-mode grouping** (#926) families are fixed. One list family
  remains OPEN for a follow-on slice, same proven shape (deterministic builder →
  pre-emptive floor, appended to `deterministic_btd6_list_reply`):
  **newest-towers ordering** — *data-gated*: `towers.json` carries no
  release-order field, so it needs sourced release-order data first (the ADR-006
  / `!btd6ops seed-data` provenance lane) before the builder.

## BUG-0008 — "420 farm" income freelanced on the general path (keyword gap)

- **Reported:** 2026-06-11 ~14:03 (owner: "this one it does answer from memory")
- **Surface:** AI task router keyword coverage → unguarded general path
- **Symptom:** "how much money does a 420 farm make" → invented economy
  ($45 bunches, "$1,725/round", invented build costs). No router keyword
  matched ("farm" is dropped from the entity matcher as ≤4 chars; "banana"
  absent; "420" can't route — FourTwenty owns it), so the model freelanced
  on the general path; name-guard outcomes varied per turn (tool-call turns
  self-grounded names; numbers are never checked on the general path).
  Variant: "list all the ways you can increase your farm income" (no money
  cue — "income" wasn't one) floored to the BTD6 refusal instead.
- **Fix (this PR):** "banana" curated keyword; router short-alias+money-cue
  leg (`farm|farms` + cash/money/how much/income/earn(s|ing)); the same cue
  extension benefits the r-shorthand leg. Farm questions now route
  `btd6.answer` → real Farm grounding + the full number guard.
- **Regression tests:** `test_farm_money_questions_route_to_btd6_answer` ·
  `test_farm_without_money_cue_stays_general`.
- **Status:** FIXED — this PR

## BUG-0007 — conversation-meta question answered with the BTD6 data refusal

- **Reported:** 2026-06-11 ~13:56 (owner transcript)
- **Surface:** general-path faithfulness guard floor
- **Symptom:** "what is the last message you can see" → "I don't have
  verified BTD6 data… (55.1)". The reply legitimately quoted the prior
  Desperado turns; the guard treated those names as ungrounded and the floor
  copy is a non-sequitur for a non-BTD6 question.
- **Fix (this PR):** the channel's recent conversation turns (the always-on
  3-turn floor) join the guard's trusted haystack on the **general path
  only** (BTD6-path numbers still require real grounding); when the floor
  still triggers on a question that is not itself BTD6-themed, a generic
  "I held back unverifiable game details" copy replaces the version-stamped
  refusal.
- **Regression tests:**
  `test_general_path_reply_may_quote_recent_conversation` ·
  `test_general_path_btd6_leak_is_refused` (generic copy) ·
  `test_general_path_btd6_themed_leak_keeps_version_refusal`.
- **Status:** FIXED — this PR

## BUG-0006 — conversation carryover unreachable: pronoun follow-ups never route BTD6

- **Reported:** 2026-06-11 ~13:56 (owner transcript — the eval checklist's
  own Tier-1.4 phrase)
- **Surface:** AI task router (text-only) vs the #668 carryover grounding
- **Symptom:** "does the navarch of seas paragon make coin" answered
  correctly, then "does it make coins at the end of the round?" refused.
  Same shape: "which of those items can damage lead" after the Geraldo list.
- **Root cause:** the #668 carryover lives in `btd6_context_service.build`,
  which only runs on `AITask.BTD6_ANSWER` — but `classify()` is text-only
  and an entity-less pronoun follow-up has no BTD6 token ("…the round?"
  even misses the `"round "` keyword on punctuation). The carryover shipped
  with its routing leg missing; its unit tests called `build()` directly.
- **Fix (this PR):** `classify(..., conversation_btd6_context=)` — the stage
  scans the in-process conversation floor (≤3 turns) with the curated
  keyword predicate and passes the cue; a follow-up-shaped question
  (it/its/they/them/those/these + question shape) with the cue routes
  `btd6.answer`, where carryover resolves the pronoun. Standalone questions
  stay general regardless of the cue.
- **Regression tests:**
  `test_pronoun_followup_routes_btd6_with_conversation_cue` ·
  `test_pronoun_followup_stays_general_without_cue` ·
  `test_conversation_cue_does_not_route_standalone_questions`.
- **Status:** FIXED — this PR

## BUG-0005 — BUG-0003 recurrence in the model loop: the tool laundered a misread quantity ($120,743,025)

- **Reported:** 2026-06-11 ~13:55 (owner transcript — first live tool-loop
  test under Q-0086 keys; the deterministic layer was verified correct in
  #703 but the model leg was untestable then)
- **Surface:** AI model loop × bulk-pricing tools × faithfulness guard
- **Symptom:** "how much do 10 041 despos cost on impop" → "$120,743,025"
  (= 10,041 × $12,025) despite the grounding line carrying the correct
  "×10 towers → Impoppable $120,250".
- **Root cause:** the model preferred its own "10 041 = 10,041" reading and
  passed it as the tool `quantity` — the tool computed the product, the
  result entered the trusted ledger, and the guard then **validated the
  wrong number against the model's own tool call** (laundering). The
  grounding line implied ×10 but never negated the misreading.
- **Fix (this PR):** (1) the `[btd6_pricing]` line now explicitly negates it
  ("means 10 towers at crosspath 0-4-1 — NOT the single number 10041; use
  these grounded totals verbatim; do not recompute"); (2) both bulk-pricing
  tools fail closed on implausible counts (>999) with a note that teaches
  the `<quantity> <crosspath>` reading mid-loop.
- **Regression tests:**
  `test_quantity_laundering_gate_rejects_implausible_counts` ·
  `test_pricing_line_quantity_crosspath_production_phrasing` (negation
  asserts).
- **Status:** FIXED — this PR

## BUG-0004 — r-shorthand round projection answered with the wrong total (cumulative-from-round-1 mislabel)

- **Reported:** 2026-06-11 ~12:39 (owner screenshot, #general — post-#703
  deploy; the owner flagged it as "probably fixed *if* those numbers are
  correct" — they were not)
- **Surface:** AI natural-language → BTD6 round-cash routing + workflow matcher
- **Symptom (verbatim):** "How much do I have on r70 if I had 26932 at the
  end of r53" → "At the end of round 70, you would have a total of
  **$71,315.20**" (plus a correct $29,386.70 rounds-54-70 breakdown).
  $71,315.20 is the cumulative from **round 1** through 70 — not the user's
  scenario. Truth: 26,932 + 29,386.70 = **$56,318.70**.
- **Root cause (four stacked gaps):** (1) every workflow range pattern
  demanded the literal word "round" — the r-shorthand anchors ("r70",
  "r53") matched nothing, so the deterministic workflow stayed out; (2) the
  router had no r-form cue either, so the message routed
  `general.nl_answer` — the model called the round tools itself and the
  general path checks names only, so each number was individually grounded
  (cumulative(70), range(54,70), round 53) while the **assembly** was wrong
  — the faithfulness guard checks values, not claims (the BUG-0002 mislabel
  class again); (3) "at the END of r53" semantics didn't exist — even a
  match would have double-counted round 53; (4) "if I **had**" wasn't a
  balance cue (only have/got/hold).
- **Fix (this PR):** one shared round-token vocabulary (`round 53` / `r53` /
  `r 53`, digit-boundary-guarded so "r2d2" stays out) across all range/afford
  anchors; a completion-cue start shift ("end of/after/finished/cleared
  round N" on the range's lower round → start N+1, no-op on the upper) with
  an explicit assumption line; had/held/started-with balance cues; r-form
  round masking before amount extraction; and a conservative router leg —
  two r-round tokens, or one plus a money cue, route `btd6.answer` (arming
  the number guard). The default-profile workflow (#703) then owns the
  projection: $56,318.70, deterministic.
- **Regression tests:**
  `test_plan_r_shorthand_with_completed_round_production_phrasing` ·
  `test_run_completed_round_projection_counts_from_next_round` ·
  `test_completed_cue_on_upper_round_is_a_no_op` ·
  `test_r_token_requires_digit_boundary` ·
  `test_r_shorthand_round_questions_route_to_btd6_answer` (+ the
  over-route negatives) · live-battery
  `knowledge.btd6_round_cash_r_shorthand_bug_0004`.
- **Status:** FIXED — this PR

## BUG-0003 — "despos" hallucinated as Plasma Monkey Fan Club (unguarded general path)

- **Reported:** 2026-06-11 ~10:32 (owner screenshot, #general)
- **Surface:** AI natural-language → BTD6 routing + grounding
- **Symptom (verbatim):** "@SuperBot how much do 10 041 despos cost on impop"
  → "A single Plasma Monkey Fan Club (Despo) costs $54,000 on Impoppable.
  For 10,041 Despos: 10,041 × $54,000 = $542,214,000 (542.2 million)."
- **Expected (owner-corrected 2026-06-11):** "despo" is community shorthand
  for the **Desperado** tower, and "10 041" is **quantity + crosspath** —
  *ten 0-4-1 Desperados* (the standard community phrasing), not the number
  10,041. Correct answer: $12,025 per 0-4-1 Desperado on Impoppable,
  $120,250 for the ten — or an honest refusal if unresolvable. Never a
  confident wrong entity.
- **Root cause (four stacked gaps):** (1) the task router had no cue for the
  message — "impop"/"despos" matched no keyword and no entity alias — so it
  routed `general.nl_answer`, where the model answers from memory; (2) the
  dataset's Desperado aliases (`des`, `cowboy`, `gunslinger`) lacked `despo`,
  and the resolver's single-word alias matching had no plural fold, so even
  `despo` would have missed the token "despos"; (3) grounding had **no
  pricing leg for the `<quantity> <crosspath> <tower>` family** — the
  crosspath regex fed only a *stats* line, no cost — and the faithfulness
  guard (rightly) blocks any sum the model derives, so the question was
  unanswerable on every path; (4) on the general path numbers are never
  guarded (by design) — the wrong-entity answer shipped.
- **Fix (this PR):** `impop` + `despo` joined the curated BTD6 keywords
  (substring match covers "impoppable"/"despos"); `despo` added as a
  Desperado alias in towers.json; the resolver's single-word alias matching
  gained a conservative plural fold (`alias + "s"`); boss canonicals joined
  the router's entity set (see BUG-0002). **The pricing leg:**
  `btd6_data_service.crosspath_cost(tower, code, quantity=…)` computes the
  full per-difficulty cost of any legal upgrade state (each purchase rounded
  to $5, then summed — the same rule as `cumulative_upgrade_costs`), and
  grounding emits a `[btd6_pricing]` line for every named crosspath with the
  preceding quantity parsed (digits or word numbers: "10 041 despos",
  "five 0-2-4 dart monkeys"); a bare "N <tower>s" grounds the base-tower
  bulk line. `btd6_cumulative_cost` gained `crosspath`/`quantity` params and
  `btd6_difficulty_cost` a `quantity` param for the tool lane.
- **Regression tests:** `test_boss_and_shorthand_questions_route_to_btd6_answer`
  (router) · `test_resolves_single_word_alias_plural` (resolver) ·
  `test_crosspath_cost_*` (service math) · `test_pricing_line_*` (grounding,
  verbatim phrasing) · `test_btd6_cumulative_cost_crosspath_quantity` +
  `test_btd6_difficulty_cost_quantity_grounds_bulk_totals` (tools) ·
  live-battery `knowledge.btd6_despo_bulk_cost_bug_0003`.
- **Deploy note:** the alias lives in towers.json — prod serves it only after
  `!btd6ops seed-data` (postgres blob lane).
- **Status:** FIXED — this PR

## BUG-0002 — Elite boss HP answered with the Standard table labeled "Elite"

- **Reported:** 2026-06-11 ~10:34 (owner screenshot, #general; the answer even
  drew a 🔥 reaction — confident wrong numbers read as authoritative)
- **Surface:** AI natural-language → BTD6 routing + boss dataset
- **Symptom (verbatim):** "@SuperBot what is the hp of elite lych per tier" →
  "Elite Lych health per tier: Tier 1: 14,000 … Tier 5: 2,100,000" — those
  are the **Standard** Lych figures. Elite Lych is 30,000 / 180,000 /
  1,100,000 / 4,800,000 / 24,000,000 (2-11× higher).
- **Root cause (two stacked gaps):** (1) boss names were not router entities
  and no keyword matched, so the question routed `general.nl_answer` and the
  model answered from training memory unguarded (numbers are not checked on
  the general path); (2) the dataset had **no elite figures at all** —
  bosses.json carried only the five standard tiers, so even the grounded
  path could only mislabel (the faithfulness guard checks numbers, not the
  labels next to them).
- **Fix (this PR):** `map_bosses` now also reads the dump's
  `Bloons/<Family>/<Family>Elite{1..5}.json` models → `elite_tiers` on every
  boss (regenerated from the pinned v55.1 cutover SHA `4e22e586`,
  byte-identical otherwise); `BossEntry.elite_tiers`; grounding emits an
  explicitly-labeled ELITE line on elite questions and the standard line is
  now labeled "Standard (non-Elite)"; the honesty note remains only for a
  dataset predating the backfill; `btd6_boss_lookup` surfaces `elite_tiers`;
  boss canonicals joined the router's entity set and the faithfulness name
  index.
- **Regression tests:** `test_boss_elite_questions_ground_the_elite_table` ·
  `test_boss_elite_honesty_note_when_dataset_predates_backfill` ·
  `test_map_bosses_reads_elite_tier_models` ·
  `test_btd6_boss_lookup_surfaces_elite_tiers` ·
  `test_bosses_load_resolve_and_carry_tiers` (elite > standard per tier, all
  7 bosses) · live-battery `knowledge.btd6_elite_lych_hp_bug_0002`.
- **Deploy note:** elite data lives in bosses.json — prod serves it only
  after `!btd6ops seed-data` (postgres blob lane).
- **Status:** FIXED — this PR

## BUG-0001 — Round-cash question misrouted to the no-data denial

- **Reported:** 2026-06-11 01:53 (owner screenshot of live server; reporter:
  member `tposergaming`)
- **Surface:** AI natural-language → BTD6 round-cash workflow (#634, Q-0043
  inclusive ranges)
- **Symptom (verbatim):** user asked "@SuperBot lets say i have 8094$ at
  round 60, what is the cash that i will get by going to round 68" → bot
  replied "I don't have verified BTD6 data to answer that for the current
  game version (55.1). I won't state names or numbers I can't ground in my
  data — try asking about a specific tower, hero, or paragon."
- **Expected:** route to the round-cash plan→execute→verify workflow
  (a simpler phrasing passed the owner's live eval — checklist Tier 1.1);
  compute the inclusive range sum, ideally honoring the stated starting
  balance (8094 + range), and answer with evidence.
- **Root cause:** two stacked gaps in
  `disbot/services/ai_round_cash_workflow.py`: (1) all three range patterns
  required the connector immediately after the first round number — anchors
  separated by a clause ("at round 60, … by going to round 68") never
  matched, so the workflow stayed out and the (correct) number-guard then
  blocked the model's ungrounded arithmetic → refusal floor; (2) the plan had
  no starting-balance concept, so even a matched range couldn't ground the
  "+8094" total (and the `$`-postfix amount form "8094$" wasn't parsed). The
  workflow's "a missed match costs nothing" design assumption is false for
  arithmetic questions — the normal path *cannot* answer them by design.
- **Fix (PR #694):** a fourth, still-conservative range pattern (both anchors
  must carry the literal word "round", within one sentence / ≤80 chars; cash
  keyword gate unchanged) + `starting_balance` on the plan (ownership-cue
  gated, round-spans masked before amount extraction) + deterministic
  `projected_total = balance + range_cash` in the evidence/result text (so
  every figure the model may state is in the grounding haystack) + postfix-`$`
  amount support.
- **Regression test:** `test_plan_separated_anchors_production_phrasing_bug_0001`
  + `test_range_answer_projects_stated_starting_balance_bug_0001`
  (`tests/unit/services/test_ai_round_cash_workflow.py`, production phrasing
  verbatim) · live-battery case `knowledge.btd6_round_cash_balance_bug_0001`
  (`tests/evals/cases.py`) · conservatism pins (no-cash-keyword and
  cross-sentence anchors stay out).
- **Deploy note:** the workflow only engages on the `btd6_grounded(:strict)`
  orchestration profiles — the reporting channel must keep that profile (the
  owner's eval walk set it during Tier 1.2). On the default profile this
  question refuses *by design*.
- **Status:** FIXED — merged via PR #694 (auto-deploys on merge)
- **Recurrence (2026-06-11 ~10:30-10:34, owner screenshots):** the *verbatim*
  phrasing refused again in #general, hours after #694 deployed — plus a new
  miss: "if I have 20K by round 50, how much would I have by round 60?".
  Root causes: (1) the deploy note above was the bug — #general runs the
  **default** profile, where the workflow never engaged, and the round-cash
  *tool* can't ground a starting-balance projection (the model's `20000 + X`
  is exactly what the number guard blocks), so "refuses by design" was a
  standing landmine on every default channel; (2) the matcher's cash-keyword
  gate had no cash noun to match ("how much would I have") and no pattern
  covered "by round A … by round B" anchors. **Follow-up fix (this PR):** the
  `compatible_default` + `balanced_helper` presets now declare the
  `analyze_execute_verify` workflow (read-only deterministic, Q-0048
  standing lift; `no_tools` keeps it off), the gate gained a money-question
  alternative ("how much … have/get/make/earn/gain"), and "by" joined both
  anchor sets. Regression tests:
  `test_plan_by_round_anchors_with_balance_production_phrasing` ·
  `test_plan_money_question_gate_stays_conservative` ·
  `test_default_and_balanced_engage_round_cash_workflow` · live-battery
  `knowledge.btd6_round_cash_by_round_projection`. No channel setup is
  needed anymore for round-cash questions.
