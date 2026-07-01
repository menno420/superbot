# 2026-07-01 — Utility completion-first deepening

> **Status:** `complete`

**Run type:** routine · dispatch (empty fire — advanced the S1 completion-first ▶ Next queue)

## What I did

Cleared the offline punch-list on the **Utility** completion certificate
(`docs/planning/feature-completion/units/utility.md`, `◐ assessed`), moving it toward `✔`:

1. **Punch #1 — resolved `utility.tool.ping`.** The registry declared the `utility.tool.ping`
   capability but Utility had no ping; the only `!ping` was an **admin-tier** alias of diagnostic's
   `!latency`, so ordinary members had none. Added a real **user-tier `!ping`** (gateway + message
   round-trip) and **re-homed the `ping` alias off** diagnostic's `latency` (diagnostic keeps admin
   `!latency`). Updated both registry `entry_points` (utility gains `ping`; diagnostic `ping`→`latency`).
2. **Punch #4 — best-in-class commands.** Added `!botinfo` (`about`) and `!membercount` (`members`) —
   the named missing Carl-bot/MEE6 parity commands (roleinfo/channelinfo/userinfo already exist, #1561).
3. **Punch #2/#3 — command-behaviour + authority tests.** New `tests/unit/cogs/test_utility_commands.py`
   (21 cases) covers the previously-untested command paths (info/avatar/poll/remind/clear/ping/botinfo/
   membercount + `_format_uptime`) and pins `clear` (manage_messages) / `invite` (create_instant_invite)
   authority — denied for a member without the perm, allowed with it and for the platform owner (Q-0212).

**Collision-checked first (BUG-0030 lesson, the same-day prod outage):** grepped every `ping` claimant
before touching the name — it existed only as diagnostic's alias, so freeing it for Utility's user-tier
command was safe. The boot-smoke (`test_cog_load_smoke`) + extension-integrity guards confirm no collision.

Regenerated the committed dashboard/site artifacts (`site.json`/`dashboard.json`/`data.js`) for the 3 new
commands (BUG-0018/0022 class). Full CI mirror green (`check_quality.py --full` + `check_architecture
--mode strict`, 0 GAP reachability).

## 📤 Run report

- **Did:** Utility completion-first deepening — a real user-tier `!ping` (resolving the declared
  `utility.tool.ping` capability by re-homing the alias off admin-tier diagnostic), `!botinfo` +
  `!membercount` best-in-class commands, and the first command-behaviour + authority test coverage for
  the unit · **Outcome:** shipped (born-red flipped complete; CI green, auto-merge armed on #1609).
- **Shipped:** #1609 — `disbot/cogs/utility_cog.py` (+3 commands, `_format_uptime`), `disbot/cogs/
  diagnostic_cog.py` (drop `ping` alias), `disbot/utils/subsystem_registry.py` (entry_points),
  `tests/unit/cogs/test_utility_commands.py` (21 tests), utility cert punch-list, regenerated artifacts.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** none (pure additive commands + a re-homed alias; live on next auto-deploy).
- **⚑ Self-initiated:** none in the invent-a-feature sense — this is dispatched completion-first work
  straight off the S1 ▶ Next queue (the Utility cert punch-list). The pick of *Utility* over "yet another
  fishing structure" was a deliberate judgment call (fishing had heavy same-day churn + caused BUG-0030),
  flagged here for visibility.
- **↪ Next:** Utility cert remaining = punch #5 (feedback-tone polish, offline) + #6/#7 (owner live
  walkthrough + sign-off, `[owner]`). Other startable offline completion deepening: Treasury cog-level
  command tests (punch #1), Community-Spotlight view-callback tests (punch #1/#2), Karma bespoke panel.

## 💡 Session idea (Q-0089)

**A "declared-capability → real-command" completion guard.** This session's punch #1 was a *declared but
unimplemented* registry capability (`utility.tool.ping`) — a class the completion assessments keep
surfacing by hand (Inventory unenforced capabilities, etc.). A checker that, for each subsystem, verifies
every declared `capabilities`/`entry_points` token resolves to a *real reachable command at the declared
tier* would turn "is this capability actually implemented?" from a manual assessment step into CI. Genuine
(it's exactly what I just did by hand), dedup-checked against `check_command_reachability` (which checks
reachability, not the capability↔command mapping).

## ⟲ Previous-session review (Q-0102)

The prior dispatch run (#1602, owner "bypass all permission gates") did excellent root-cause work: it
built a *guard that enumerates every gate* so completeness is machine-checked, and its own review honestly
named the three narrow-scope round-trips as the lesson. **What the broader same-day chain missed:** the
fishing-structure runs (#1598/#1599/#1603/#1605) churned four near-identical structures in a day and #1599
caused a **boot-loop prod outage** (BUG-0030) from a command-name collision — a sign the dispatch loop was
over-fitting one narrow lane without a namespace check. **System improvement (acted on this session):** I
treated "pick a command name" as a *collision-check first*, not a naming task — the exact discipline
BUG-0030's root-cause note asked for. The durable version is the Q-0089 idea above + the already-shipped
`test_cog_load_smoke` boot guard; the behavioural half is picking varied, certification-advancing work over
repeating the highest-churn lane.

## Doc audit (Q-0104)

- Utility completion certificate updated (punch #1/#2/#3 done, #4 advanced) + a `Deepened:` line.
- No new owner decision → no router entry. New commands documented at their code sites + regenerated
  command artifacts. Ledger untouched (no *prior* merge drift; #1609 is this session's own PR, reconciled
  by the next run per the newest-merge-lag carve-out).
- `check_docs`/`check_consistency`/`check_artifacts_fresh` green via the full mirror.

## 🛠 Friction → guard (Q-0194)

- **Friction:** adding commands silently drifted the committed `site.json`/`dashboard.json`/`data.js`
  (BUG-0018/0022 class) — caught by `check_artifacts_fresh` + `test_committed_site_json_...`. **Guard:**
  already enforced (the freshness umbrella + the equality test both red on drift); the fix is `python3.10
  scripts/export_dashboard_data.py`. No new guard needed — the existing ones did their job.
- **Friction (recurring, cross-session):** rapid same-lane churn → BUG-0030 collision. **Guard:** the
  `test_cog_load_smoke` dynamic boot test (shipped in #1601) now fails CI on any `add_cog` collision, so
  the whole boot-break class is caught before merge — verified green with the 3 new commands this session.
