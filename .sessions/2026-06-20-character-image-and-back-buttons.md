# 2026-06-20 — `!character` paper-doll + back-button dead-ends

> **Status:** `complete`
> **Run type:** `manual` — owner bug report (screenshots) on the live bot.

## Arc

Owner sent two screenshots (the Community Hub from `!help`, and `!character`) with:
"Missing back buttons and `!character` does not show the character image — `!gear`
shows your character; I'd like `!character` to show it too, but with less specific
gear information." Two issues, both fixed on `claude/gallant-volta-bk3qvf`.

## Shipped (no PR — pushed to branch per env instruction; offered to open one)

**1. `!character` shows the paper-doll (was: a text stat-card).**
- `views/mining/character_panel.py`: added `build_character_doll(user_id, guild_id)`
  → the V-16 paper-doll (`render_character_for`, same figure `!gear` shows, over the
  built-Home backdrop). Removed the now-unused `build_character_card` (text stat-card;
  its only consumer was this command — `render_stat_card`/`build_stat_card_spec` stay,
  the UX-lab gallery still uses them).
- Trimmed `build_character_embed` gear field to **high-level** via `_gear_overview`:
  equipped item *names* + set-bonus status, **no per-slot durability** (that detail
  lives in `!gear`; the doll is the visual) — the "less specific gear information" ask.
- `cogs/mining_cog.py` `!character`: sends the embed with the doll `set_image`'d in.
- `views/mining/character_hub.py` Overview button: same doll, for parity with the cmd.

**2. Back-button dead-ends.**
- **Explore world hub** (`ExploreWorldHubView`): reached from Mining Hub → 🗺️ Explore
  with **no way back** (the `!world` root open is fine — a root needs none).
  `views/mining/main_panel.py` `explore_btn` now attaches "↩ Mining Hub" externally
  (the Help/Games pattern). The consistency linter's `back_button` rule **misses this
  class** — it only detects `@ui.button`-decorated controls, and this hub adds its
  buttons dynamically via `add_item` (see Session idea).
- **Community hub** (the screenshotted one): unlike the Games hub it did **not**
  preserve the back-to-Help chain — Help → Community → child → "↩ Back to Community"
  silently dropped "↩ Back to Help", and a child had no direct back-to-Help.
  Mirrored `GamesHubView.handle_select`'s `chain_back`/`BackTarget` propagation in
  `views/community/hub.py` (child now gets both backs; the rebuilt hub keeps Help).

Tests: `test_mining_character.py` (+`_gear_overview`/`build_character_doll`),
`test_mining_character_hub.py` (overview doll mock), `test_community_hub_view.py`
(back-chain), `test_explore_world_hub.py` (mining-explore back + `!world` root none).
Regenerated `botsite/data/site.json` (the docstring change drifted the commands family).

## Verification

- `check_architecture --mode strict`: 0 errors. `check_consistency --mode strict`: 0.
- `check_quality --full`: green except (a) the `site.json` drift — fixed by re-export,
  test now passes; (b) `test_game_wager_workflow_integration` flaked under `-n auto`
  (real-Postgres parallel-DB collision, the journal's documented caveat) — passes
  serially, skips in CI. Neither touches the changed files.
- Booted the bot: all 46 cogs load, no tracebacks. Rendered the doll and eyeballed it.

## Context delta

- **Needed but not pointed to:** the `chain_back`/`BackTarget` back-nav mechanism
  (`views/navigation.py`) is the canonical way hubs preserve a grandparent back button,
  but only the Games hub uses it — there's no folio note that "a router-only hub opened
  from Help must thread `self._back_target` to its children." Reverse-engineered from
  `games/hub.py`. Candidate for `hub-ui-standard.md`.
- **Discovered by hand:** the `back_button` consistency rule (`scripts/check_consistency.py`)
  only flags HubViews with `@ui.button`-**decorated** controls; registry-driven hubs that
  `add_item` dynamically (ExploreWorldHubView) are invisible to it — which is exactly how
  that dead-end shipped past a graduated (error-level) CI rule.
- **Pointed to but didn't need:** the heavy CodeGraph boot stats — a `context_map` +
  grep + reading the three panel modules carried the whole task.
- **Decisions made alone:** (1) "less specific gear" = drop per-slot durability, keep
  item names + set status (the doll is the visual; `!gear` owns condition). (2) Removed
  the text stat-card from `!character` rather than showing both (owner said "show it,
  with less … gear info" → replace, not stack). (3) Did **not** open a PR (env rule);
  pushed to the branch and offered. Revert/redo all cheap.
- **Flagged for maintainer:** the Community-hub screenshot shows the hub with **no**
  back button at all. In current `main`, opening it via `!help` → Community *does* add
  "↩ Back to Help" (now preserved through children too); a hub with zero back nav
  matches the **`!community` root** open (a root has no parent) — so if the live miss is
  on `!help`, a redeploy of this branch fixes it; if it's the root `!community`, tell me
  and I'll add a Home/close affordance.

## 💡 Session idea

**Extend the `back_button` consistency rule to detect dynamically-added controls.**
Today it only counts `@ui.button`/`@ui.select`-decorated callbacks as "child controls",
so a registry-driven HubView that builds its buttons with `self.add_item(...)` (like
`ExploreWorldHubView`) is never flagged — the gap that let the Explore dead-end ship past
a graduated error-level rule. Treat any `self.add_item(...)` in a HubView as a child
control; `_module_has_back_affordance` already correctly exempts hubs whose module
attaches a back (Games/Community), so the net-new finding is just the genuinely-bare ones.
Deferred from this PR only to keep the triage (allowlisting the legit roots that use
`add_item`) out of a focused bugfix — it's a clean one-rule follow-up.

## ⟲ Previous-session review

The 2026-06-20 federated-Explore world-card run (`world_card.py`, PR 3) shipped a
read-only cross-game card cleanly and registry-driven — good. **What it missed:** it
re-parented the mining `🗺️ Explore` button onto the new `ExploreWorldHubView` (PR 1) and
added the world card, but never gave that hub a **back button** — a player entering
Explore from mining was stranded, and the close-out didn't catch it because the
`back_button` linter can't see dynamically-added buttons. **System improvement:** the
Session idea above closes that exact detection gap so the next registry-driven hub can't
ship a dead-end silently.

## 📤 Run report

- **Did:** `!character` now renders the paper-doll with a high-level gear embed; fixed
  two back-button dead-ends (Explore hub, Community→child Help chain). · **Outcome:** shipped
- **Shipped:** no PR — env instruction is "commit + push, don't open a PR unless asked";
  pushed to `claude/gallant-volta-bk3qvf`, offered to open one.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none (one clarification offered, not blocking — see
  Flagged for maintainer re: the root `!community` back affordance).
- **⚑ Owner manual steps:** none (a merge to `main` auto-deploys; nothing off-repo).
- **⚑ Self-initiated:** none (both fixes are the owner's reported bugs; the linter
  generalization is filed as an idea, not built).
- **↪ Next:** if the owner wants it, open the PR; optionally build the Session-idea
  linter rule extension as a focused follow-up.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (branch push; no PR per env rule) |
| CI-red rounds | 1 (the `site.json` drift from the docstring change; re-exported) |
| Repo-rule trips | 0 (arch + consistency clean) |
| New ideas contributed | 1 (back_button rule → detect `add_item` controls) |
| Ideas groomed | 0 |
