# SuperBot — Cog Hub Command-Coverage Audit

> **Status:** `audit` — inventory snapshot, dated 2026-05-24.
> Companion to `docs/audits/ui-view-adoption-audit.md` (per-view adoption)
> and `docs/help-command-surface-map.md` (Help route structure).
>
> **What this is:** the third audit in the "Smooth Interaction Pass"
> series. Where the UI audit asks *"do views use the canonical
> primitives?"*, this one asks *"does every typed command have a
> discoverable counterpart in its cog's interactive hub?"*.
>
> **What this is not:** a code-change PR. Items are recommendations;
> each gap classified `needs fix` becomes its own follow-up PR.

---

## 1. Coverage rubric

For each cog with a typed-command surface AND a hub view, every
typed command is classified as:

- **covered** — the hub exposes a button / Select option / sub-panel
  that triggers the same effect.
- **typed-only by design** — text-arg / power-user command
  (`!platform locks <prefix>`, `!lock <channel>`); the hub default
  args are explicit, retaining the typed path for filters.
- **intentional gap** — owner-only, admin-only mutation,
  diagnostic, modal-only command intentionally excluded from the
  user-facing hub.
- **needs fix** — operator-visible action that the hub *could* and
  *should* expose, but currently doesn't.

A cog is **green** if every typed command falls in one of the first
three categories; **yellow** if there is one `needs fix`; **red**
if there are multiple or the gap is on a high-frequency user action.

---

## 2. Group-command cogs (`@commands.group`)

These are the cogs where the typed surface is most clearly a "menu
tree" that the hub should mirror. Diagnostic is omitted here — it
was the subject of PR 1 of the Smooth Interaction Pass and is
already aligned.

### 2.1 `chain` — `chain_cog.py`

- **Group:** `chain` (`disbot/cogs/chain_cog.py:76` onward).
- **Hub view:** `_ChainMenuView` (`chain_cog.py:509`); panel
  command `!chainmenu` (`chain_cog.py:236`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `chain create` | 76 | covered — `➕ Create Chain` button → `_CreateChainModal` |
| `chain delete` | 124 | covered — `🗑️ Delete Chain` button → `_DeleteChainModal` |
| `chain setlimit` | 156 | covered — `📏 Set Limit` button → `_SetLimitModal` |
| `chain removelimit` | 203 | **needs fix** — no hub control. Remove-limit is a single action that fits naturally on the limit modal as a "Clear limit" checkbox, or as a separate `🚫 Remove limit` button. |
| `chain list` | 253 | covered — `🔄 Refresh` re-renders the chain inventory in the hub's embed. |
| `chainmenu` | 236 | (panel entry, not a command gap) |

**Status:** yellow. One `needs fix` (`chain removelimit`).

---

### 2.2 `cleanup` / `word` — `cleanup_cog.py` + `cleanup/panel.py`

- **Groups:** `word` (`cleanup_cog.py:332`); flat command `cleanup`
  is the hub entry.
- **Hub view:** `CleanupPanelView` (`disbot/cogs/cleanup/panel.py:133`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `cleanup` | 407 | (panel entry) |
| `cleanuphistory` | 185 | **needs fix** — high-value filter-based scan/delete. Hub should expose either a modal taking `keyword/commands/prohibited/limit` or three preset buttons (`Scan keyword`, `Scan commands`, `Scan prohibited`). Currently typed-only despite being one of the most-used mod tools. |
| `word add` | 346 | covered — `🔤 Prohibited Words` → `_WordMenuView` exposes Add. |
| `word remove` | 365 | covered — same panel exposes Remove. |
| `word list` | 384 | covered — same panel renders the list on open and refresh. |
| `word` (base) | 332 | covered — invoking the group with no sub prints help, identical to opening the panel. |
| `wordmenu` | 398 | covered — alias for the same panel branch. |

**Status:** yellow. `cleanuphistory` is the only operator-visible gap.

---

### 2.3 `logging` — `logging_cog.py` + `logging/panel.py`

- **Group:** `logging` (`logging_cog.py:119` onward).
- **Hub view:** `LoggingPanelView` (`disbot/cogs/logging/panel.py:49`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `logging status` | 119 | covered — `📝 Refresh Status` button + hub default render. |
| `logging set` | 125 | covered — `🔗 Set Mod Channel` + `🔗 Set Cleanup Channel` buttons. |
| `logging create` | 162 | covered — `🆕 Create Mod Channel` + `🆕 Create Cleanup Channel`. |
| `logging routes` | 191 | covered — `🗺️ Routes` → `LoggingRoutesView`. |
| `logging test` | 211 | covered — `🔔 Test` fires a test event. |

**Status:** green.

---

### 2.4 `settings` — `settings_cog.py`

- **Group:** `settings` (`settings_cog.py:120`).
- **Hub view:** `SettingsHubView` (registered dynamically; entry
  via the Help / Settings route).

| Typed command | Line | Hub coverage |
|---|---|---|
| `settings` | 120 | (panel entry) |
| `settings access` | 144 | intentional gap — separate `AccessExplorerView` diagnostic, not part of the per-subsystem hub. Surfacing it would require a new "Diagnostics" lane in `SettingsHubView`; out of scope for the Smooth Pass. |

**Status:** green (only intentional gap).

---

### 2.5 `platform` — `diagnostic_cog.py`

Covered by **PR 1 of the Smooth Interaction Pass**. `lifecycle`,
`setup-readiness`, and `flag` are now reachable from the hub.
No further gaps. **Status:** green.

---

## 3. Flat-command cogs with a hub view

These cogs do not use `@commands.group` but still expose a hub via
`build_help_menu_view` (or a `!<sub>menu` command). The audit asks
the same question: is each typed command discoverable from the hub?

### 3.1 `admin_cog.py`

- **Hub view:** `_AdminPanelView` (`admin_cog.py:408`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `adminmenu` | 34 | (panel entry) |
| `serverstats` | 73 | covered — `📊 Server Stats` button. |
| `cog`, `loadall`, `unloadall` | 95, 122, 145 | intentional gap — owner-only cog-management; surfaced indirectly via `📋 Cog List` aggregate (read-only). Mutation surface is intentionally typed-only. |
| `syncslash`, `slashes` | 174, 236 | intentional gap — owner-only slash-sync; typed-only by design. |
| `restart` | 306 | intentional gap — owner-only restart; never reachable via panel by policy. |
| `loglevel` | 334 | covered — `📝 Log Level` button → modal. |

**Status:** green. Owner-only gaps are policy.

---

### 3.2 `blackjack_cog.py`

- **Hub view:** `BlackjackPanelView` (`views/games/blackjack_panel.py:414`);
  reached via `!games` → Blackjack.

| Typed command | Line | Hub coverage |
|---|---|---|
| `blackjack`, `bj` | 408 | covered — `🎰 Play Solo` / preset bet buttons. |
| `bjtournament`, `bjtourn` | 493 | covered — `🏆 Tournament` button on the panel. |
| `bjstart`, `bjstatus` | 557, 569 | intentional gap — admin-only tournament controls; typed-only. |

**Status:** green.

---

### 3.3 `channel_cog.py`

- **Hub view:** `_ChannelManagerView` (`views/channels/main_panel.py`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `channelmenu` | (panel entry) | — |
| `lock`, `unlock` | 341, 351 | typed-only by design — text-arg quick action; the panel's `Manage Restrictions` subpanel does the same thing via selects. |
| create / delete / restrict / visibility subpanels | — | covered — `Create / Delete / Manage Restrictions / Subsystem Visibility` buttons. |
| Other channel admin commands (rename, slowmode, etc.) | various | mixed — needs a focused mini-audit (see **needs fix** below). |

**Status:** yellow. The 16 typed commands include several
power-user commands that the panel does not surface (e.g.
slowmode-style tweaks). Audit gap deferred to a follow-up
`channel_cog` mini-audit (out of Smooth Pass scope).

---

### 3.4 `community_cog.py`

- **Hub view:** `CommunityHubView` (`views/community/hub.py`).
- Typed surface is a thin entry command (`!community`); the panel
  routes to subsystems (games / counting / RPS) by subsystem
  discovery.

**Status:** green.

---

### 3.5 `counting_cog.py`

- **Hub view:** `_CountingHubView` (`views/counting/hub_panel.py:21`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `countingmenu`, `cm` | 121 | (panel entry) |
| `start_match`, `sm` | 138 | **needs fix** — most-used operator command; not in panel. Add a `▶ Start match` button that opens a modal taking the same args. |
| `end_match`, `em` | 301 | **needs fix** — pair with `▶ Start match`. Add `■ End match` button. |
| `reset_count`, `rc` | 350 | covered — `🔁 Reset Count` button. |
| `toggle_turns`, `tt` | 404 | covered — `🔄 Toggle Turns` button. |
| `count_info`, `ci` | 434 | covered — hub embed already renders match info on open. |
| `count_rules`, `cr` | 473 | **needs fix** — add a `📜 Rules` button that re-uses the existing rules embed builder. |
| `set_skip_numbers`, `ssn` | 504 | typed-only by design (text arg list); could surface as a modal but lower priority. |
| `toggle_reset_on_wrong_count`, `trwc` | 552 | covered — `🔄 Reset on Wrong` button. |

**Status:** red. Three operator-visible gaps (`start_match`,
`end_match`, `count_rules`).

---

### 3.6 `deathmatch_cog.py`

- **Hub view:** `DeathmatchPanelView` (via `!games` Deathmatch).

| Typed command | Line | Hub coverage |
|---|---|---|
| `dm_challenge`, `deathmatch`, `challenge`, `dm` | 284 | covered — `⚔ Challenge` button on the panel. |
| `dm_help`, `deathmatch_help` | 333 | covered — `❓ Rules` / help section. |

**Status:** green.

---

### 3.7 `economy_cog.py`

- **Hub view:** `EconomyPanelView` (`views/economy/main_panel.py`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `economymenu` | 65 | (panel entry) |
| `daily` | 201 | covered — `🎁 Daily` button. |
| `work` | 267 | covered — `💼 Work` button. |
| `shop` | 309 | covered — `🛒 Shop` button. |
| `balance`, `bal`, `wallet` | 318 | covered — `💰 Balance` button. |
| `setlogchannel` | 335 | intentional gap — admin-only mutation; not surfaced in user-facing hub. |
| `joblist`, `jobs` | 348 | covered — `📋 Jobs` button (also surfaced inside Work panel). |

**Status:** green.

---

### 3.8 `games_cog.py`

- **Hub view:** `GamesHubView` (`views/games/hub.py`); pure router.
- Typed surface: `!games`. No coverage gap possible.

**Status:** green.

---

### 3.9 `inventory_cog.py`

- **Hub view:** none dedicated; surfaced through `EconomyPanelView`'s
  `🎒 Inventory` button (cross-package leak tracked in
  `helper-debt-inventory.md` § 7).

| Typed command | Line | Hub coverage |
|---|---|---|
| `inventory`, `inv` | 364 | covered (via Economy hub button). |

**Status:** green for coverage; cross-package leak tracked separately.

---

### 3.10 `leaderboard_cog.py`

- **Hub view:** read-only embed view (`leaderboard_cog.py:164`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `leaderboard` | 127 | covered — view exposes subsystem-filter selector. |

**Status:** green.

---

### 3.11 `mining_cog.py`

- **Hub view:** `MiningHubView` (`views/mining/main_panel.py`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `mine` | 59 | covered — `⛏️ Mine` button. |
| `harvest`, `explore` | 73, 87 | covered — dedicated buttons (hidden CLI variants exist). |
| `mineinv`, `mineinventory` | 100 | covered — `📦 Inventory` button. |
| `minestats` | 109 | covered — `📊 Stats` button. |
| `build` | 127 | covered — `🔨 Build` button. |
| `shop`, `prestige` and other hidden variants | 262+ | typed-only by design — power-user shortcuts to actions also reachable via the buttons. |

**Status:** green.

---

### 3.12 `moderation_cog.py`

- **Hub view:** `ModPanelView` (`views/moderation/main_panel.py`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `modmenu` | 62 | (panel entry) |
| `warn`, `timeout`, `kick`, `ban`, `unban` | 102-185 | covered — `⚠️ Warn`, `⏳ Timeout`, `👢 Kick`, `🚫 Ban`, `✅ Unban` modal buttons. |
| `clearwarnings` | 208 | covered — `⬛ Clear Warnings` button. |
| `modlogs` | 216 | covered — `📋 Mod Logs` button. |

**Status:** green.

---

### 3.13 `proof_channel_cog.py`

- **Hub view:** `!prizemenu` entry (`proof_channel_cog.py:106`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `+prize` | 58 | **needs verification** — admin add; hub should expose. |
| `-prize` | 75 | **needs verification** — admin remove; hub should expose. |
| `prizestatus` | 89 | likely covered (hub default render). |
| `prizemenu` | 106 | (panel entry) |
| `timedprize` | 121 | **needs verification** — admin command; may be intentional gap. |

**Status:** yellow — pending verification, not high traffic.

---

### 3.14 `role_cog.py`

- **Hub view:** `RoleHubView` (`views/roles/main_panel.py`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `roles`, `rolesettings`, `rolemenu` | 287-310 | (panel entries) |
| `rolecreator`, `createrole` | 315, 328 | covered — `📝 Create` button → Create subpanel. |
| `assignroles`, `setrole`, `unsetrole` | 321, 371, 391 | covered — `🗂️ Manage` button → Management subpanel. |
| `deleterole` | 355 | covered — `🗂️ Manage` exposes delete. |
| `debugroles`, `refreshmembers` | 411, 418 | covered — `🔧 Diagnostics` subpanel. |
| `reactroles`, `removereactrole`, `listreactroles` | 477-524 | covered — `💬 Reaction Roles` subpanel. |

**Status:** green.

---

### 3.15 `rps_tournament_cog.py`

- **Hub view:** RPS panel from `!games` (`views/games/rps_panel.py`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `rpsregister`, `rpsreg` | 180 | covered — Tournament register button. |
| `rpsstart`, `rpsbegin` | 350 | intentional gap — admin-only start. |
| `rpsbot` | 393 | covered — solo play button (the focus of PR 6 in this pass). |
| `rpsmatchup` | 405 | **needs fix** — current matchup view is not exposed in the panel; add a `🆚 Matchup` button. |
| `rpshelp` | 727 | covered — Help section in the panel. |
| `rpssettings` | 743 | intentional gap — admin settings. |
| `rps` | 775 | (panel entry) |

**Status:** yellow. `rpsmatchup` is a real visibility gap during
active tournaments.

---

### 3.16 `utility_cog.py`

- **Hub view:** `!utilitymenu` entry (`utility_cog.py:42`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `clear`, `purge` | 74 | likely covered via modal; **verify** in the panel. |
| `info`, `serverinfo`, `userinfo`, `avatar` | 94-170 | covered — info buttons. |
| `remind` | 178 | **needs verification** — should be a modal in the hub. |
| `invite` | 192 | covered. |
| `poll` | 199 | **needs verification** — should be a modal. |

**Status:** yellow — minor verification work; not in Smooth Pass scope.

---

### 3.17 `xp_cog.py`

- **Hub view:** `_XpHubView` (`views/xp/main_panel.py`).

| Typed command | Line | Hub coverage |
|---|---|---|
| `xpmenu` | 67 | (panel entry) |
| `rank` | 85 | covered — `📊 Both` / `🏆 XP` / `🪙 Coins` rank buttons. |
| `givexp` | 133 | covered — `🎁 Give XP` modal. |
| `resetxp` | 151 | covered — `🔄 Reset XP` confirm. |
| `xpconfig` | 163 | covered — `⚙️ Configure` opens `XpConfigView` (which **PR 5** of the Smooth Pass also adds a back button to). |

**Status:** green.

---

### 3.18 `general_cog.py`

- **Hub view:** fun-content hub (`general_cog.py:97`).
- All typed commands are read-only content (`fact`, `joke`, `quote`,
  `greet`); the hub surfaces each one as a button.

**Status:** green.

---

## 4. Aggregate gap list (operator-visible only)

These are the `needs fix` rows worth a follow-up PR. Cross-cutting
cog-internal redesigns are excluded.

| # | Cog | Command | Severity | Suggested fix |
|---|---|---|---|---|
| 1 | `counting` | `start_match` | **P1** | Add `▶ Start match` button → modal taking the same args. |
| 2 | `counting` | `end_match` | **P1** | Add `■ End match` button (paired with start). |
| 3 | `counting` | `count_rules` | P2 | Add `📜 Rules` button reusing the existing rules embed. |
| 4 | `cleanup` | `cleanuphistory` | P2 | Add modal or preset buttons for keyword/commands/prohibited scans. |
| 5 | `chain` | `chain removelimit` | P3 | Add "Clear limit" checkbox to the limit modal, or a `🚫 Remove limit` button. |
| 6 | `rps_tournament` | `rpsmatchup` | P3 | Add `🆚 Matchup` button (active-tournament visibility). |
| 7 | `proof_channel` | `+prize` / `-prize` / `timedprize` | verify | Confirm whether `!prizemenu` already covers these. |
| 8 | `utility` | `remind` / `poll` | verify | Confirm whether the panel already exposes modals. |
| 9 | `channel` | broader command set | verify | Mini-audit deferred — many typed commands are quick-actions paired with panel selects. |

**Severity rationale:** P1 = high-traffic operator command with no
hub path; P2 = lower frequency or has a workaround; P3 = nice-to-have.

---

## 5. Out of scope

- **Owner-only commands** (`cog`, `restart`, `syncslash`, `loadall`,
  `unloadall`, `bjstart`, `rpsstart`, etc.) — intentional gaps by
  policy.
- **Settings access explorer** (`!settings access`) — separate
  diagnostic surface, not the per-subsystem hub.
- **Admin-only logging channel setters** that map 1:1 to a typed
  command but live in the parent admin panel rather than per-cog
  hub — out of scope.
- **Cross-cog redesigns** (e.g. unifying counting's match controls
  with the games hub) — too large for the Smooth Pass.

---

## 6. Pinning intent

This doc is a snapshot, not a binding contract. It should be
re-run whenever:

1. A new `@commands.group` cog is added.
2. A cog's hub view is restructured (a follow-up here, not a
   blanket re-audit).
3. PRs that close the §4 gaps land — mark the row as resolved.

The doc does not (yet) have a pinning test in `tests/unit/docs/`.
A future small PR could parse §3's tables and grep for each typed
command's existence; out of scope here.
