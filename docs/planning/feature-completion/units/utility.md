# Utility — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `utility` · **Type:** server-fn · **Family:** platform
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> **Deepened:** 2026-07-01 (dispatch run) — punch #1/#2/#3 cleared + #4 advanced (see punch-list).
> Source: `disbot/cogs/utility_cog.py` (`!utilitymenu`/`/utility` + member commands) ·
> `_UtilityPanelView` (hub + General/420 child forwarding) · folio `docs/subsystems/` general

> Assessed during the completion-first arc (Q-0209). Utility is the **general-purpose member command**
> hub: server/user info, avatar, `myprofile`, reaction polls, reminders (in-memory), one-use invites,
> and `clear`/`purge` (manage_messages). Mostly read-only; the two mutating commands are
> permission-gated at both command and button level. Visibility tier `user`; reachable via
> `!utilitymenu`/`/utility` + Help, and it forwards to the General (facts/jokes/8-ball) and four_twenty
> child panels with back-nav. No persistent config by design. The honest gaps: a **declared-but-
> unimplemented `utility.tool.ping` capability** (ping lives in diagnostic, admin-tier), **thin
> command-behavior test coverage**, and **missing best-in-class commands** (roleinfo/channelinfo/botinfo).

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — server/user info, avatar, myprofile, poll (2–10 options), remind,
      invite (one-use), clear (≤100); validation on each (poll options, remind minutes, clear cap).
- [ ] **Every best-in-class sub-option** — ⚠ **partial.** Present: info/avatar/poll/remind/invite/clear;
      **missing** vs Carl-bot/MEE6: roleinfo, channelinfo, botinfo, membercount, math/calc; ping is
      diagnostic's (admin-tier), not a user-tier utility alias. → punch #1/#4.
- [x] **Failure modes honest** — option/limit/permission validation returns clear ephemerals.
- [x] **Idempotent** — info/avatar/poll are read-only; clear/remind/invite are intentionally one-shot
      (not idempotent — appropriate).

### B. Reachability & UI
- [x] **A command panel exists** — `!utilitymenu`/`/utility` → `_UtilityPanelView` (own buttons + child
      forwarding to General/420).
- [x] **Reachable every natural way** — `!utilitymenu` + `/utility` + Help (top-level Utility section,
      ui_priority 5); "More in Utility" surfaces children.
- [N/A] **Integrated into Setup** — no admin setup required.
- [x] **Return navigation** — "↩ Overview" + back-to-Utility chain to Help; child buttons re-resolve
      governance.
- [x] **In-place, not spammy** — button callbacks `edit_message`; modals for poll/remind.

### C. Convenience
- [x] **Defaults** — clear defaults to 5 messages.
- [ ] **Feedback consistency** — ⚠ minor: success is ephemeral; panel-button permission denials are
      ephemeral, not inline. → punch #5.
- [x] **Modals** — remind/poll use modal forms with labelled inputs + ephemeral error paths.

### D. Authority & safety
- [x] **Authority re-checked at callback** — `clear` (`manage_messages`) + `invite` (`create_instant_invite`)
      checked at **both** command and button; read-only commands are user-tier by design.
- [N/A] **All mutations through the audited seam** — no persistent mutations (clear/invite are Discord
      actions; remind is a fire-and-forget task) — no DB audit seam applies.
- [N/A] **Provisioning pipeline** — invite creation is a Discord-native one-use invite, not provisioned
      infrastructure.
- [x] **Reuses governance** — visibility tier `user`; Help renders per tier; no second allowlist.

### E. Configuration
- [N/A] **Settings pipeline** — utility deliberately holds no per-guild config (registry has no
      settings_keys; `has_cleanup_rules: False`).
- [N/A] **config-input widgets** — n/a.
- [N/A] **Everything configurable that should be** — n/a (intended).

### F. Wiring & discoverability
- [x] **Registry** — key `utility`, `visibility_tier: user`, entry `utilitymenu`, `supports_dm: True`,
      capabilities (`utility.info.server/user`, `utility.tool.ping` — **the ping cap is declared but
      not implemented here** → punch #1).
- [x] **Discoverable in Help** — registered hub section; `discover_utility_children()` is metadata-driven.

### G. Tests & evidence (required for ✔)
- [ ] **Behavior tests** — ⚠ `test_utility_hub_children.py` covers the **hub layer** (child discovery,
      view shape, governance forward) but the **16 command paths are untested** (info/avatar/poll/remind/
      invite/clear). → punch #2/#3.
- [ ] **Authority tests** — ❌ no explicit test of `clear`/`invite` permission enforcement → punch #3.
- [N/A] **Mutation-seam tests** — no persistent mutations.
- [ ] **Live walkthrough recorded** — pending → punch #6.
- [ ] **Owner ✔** — pending → punch #7.

## Punch-list (clear these to certify)
1. **✅ DONE 2026-07-01 (dispatch run) — Resolve `utility.tool.ping`.** Implemented a real **user-tier
   `!ping`** in the utility cog (gateway + message round-trip). The `ping` alias was **re-homed off**
   diagnostic's admin-tier `!latency` (diagnostic keeps `!latency`), so ordinary members finally have a
   ping; registry `entry_points` updated on both sides (utility gains `ping`; diagnostic `ping`→`latency`).
   Collision-checked first (BUG-0030 lesson) — `ping` was only diagnostic's alias, so freeing it was safe.
2. **✅ DONE 2026-07-01 (dispatch run) — Command-behavior tests.** `tests/unit/cogs/test_utility_commands.py`
   covers info/avatar/poll(≥2/≤10)/remind(spawn+reject)/clear(bounds+purge)/ping/botinfo/membercount +
   the `_format_uptime` helper.
3. **✅ DONE 2026-07-01 (dispatch run) — Authority tests.** Same file: `clear` (manage_messages) + `invite`
   (create_instant_invite) each denied for a member without the permission, allowed with it **and** for
   the platform owner (Q-0212 owner bypass).
4. **◐ ADVANCED 2026-07-01 (dispatch run) — Best-in-class commands.** Added `!botinfo` (`about`) and
   `!membercount` (`members`); roleinfo/channelinfo/userinfo already exist (#1561). Remaining optional
   deepening: math/calc (owner call on whether it belongs in utility vs a dedicated cog).
5. **Feedback consistency** *(offline, minor)* — uniform tone/format across success + denial paths.
6. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + each command + the child-panel
   forwarding, with screenshots.
7. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/cogs/test_utility_hub_children.py` (hub layer) + the help-render-path tests that
  pin `utility` visibility
- **Walkthrough:** pending (punch #6) · **Owner sign-off:** pending (punch #7)

## Verdict
Utility is a **lean, correct, well-routed** member-command hub — read-only info/avatar/poll + gated
clear/invite + reminders, reachable via command/panel/Help with child forwarding and back-nav, no config
by design. It is **not yet `✔ certified`**: the gaps are a **capability mismatch** (`utility.tool.ping`,
#1), **thin command/authority test coverage** (#2/#3), **missing best-in-class commands** (#4), feedback
polish (#5), and the live walkthrough/sign-off (#6/#7). No safety/dead-end issues (mutations are
permission-gated; no persistent writes).
