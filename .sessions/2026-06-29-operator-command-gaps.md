# 2026-06-29 — Best-in-class operator command gaps (slowmode · topic · roleinfo)

> **Status:** `complete`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire scheduled dispatch (no work order). Acting on the live **S1 ▶ Next** offline-startable
completion-first deepening picks, specifically the assessment punch-list's named *"best-in-class command
gaps (channel slowmode/topic, utility roleinfo/channelinfo)"*. `channelinfo` already exists
(`channel_cog`); the genuine gaps are **`!slowmode`**, **`!topic`**, and **`!roleinfo`**.

**The slices (aim 2–3, self-mergeable on green):**

- **Slice 1 — `!slowmode` + `!topic`** (channel-edit commands). Both are channel *mutations*, so they
  ship through the audited `ChannelLifecycleService` seam (two new REVERSIBLE operations
  `set_slowmode` / `set_topic`, request fields, `_apply_one`/`_summary` branches) — same pattern as
  `rename`, so each fires the audit companion + `channel.lifecycle_changed` event. Cog commands gated by
  `is_admin_or_owner`, matching the existing channel ops.
- **Slice 2 — `!roleinfo <role>`** (read-only role detail card in `role_cog`): members count, color,
  position, mentionable/hoisted, key permissions, created date. No seam needed (read-only).

Each slice is contained, additive, offline-unit-tested → self-merge on green per CLAUDE.md.

## What shipped (PR #1561)

Three best-in-class operator command gaps named by the completion assessments, all CI-green.

### Slice 1 — `!slowmode` + `!topic` (channel-edit commands, audited)
Both are channel *mutations*, so they ship through the audited `ChannelLifecycleService` seam rather
than touching `channel.edit` from the cog: two new **REVERSIBLE** operations `set_slowmode` / `set_topic`
(+ request fields `slowmode_seconds` / `topic`, `_apply_one` / `_summary` branches), so each fires the
audit companion + `channel.lifecycle_changed` event exactly like `rename`. The service **clamps** to
Discord's caps (`MAX_SLOWMODE_SECONDS=21600` 6h, `MAX_TOPIC_LENGTH=1024`); an empty topic clears it.
Cog commands `!slowmode` (alias `!slow`) + `!topic` (alias `!settopic`) gated by `is_admin_or_owner`,
matching the existing channel ops; they validate (negative / over-cap / missing channel) before calling
the seam. +13 service/cog tests.

### Slice 2 — `!roleinfo <@role|name|id>` (read-only)
The role sibling of `!channelinfo` / `!info user`: member-tier, read-only (no audited seam needed) —
colour, member count, position, hoisted/mentionable/managed flags, created date, and a notable-permission
summary (`administrator` short-circuits; otherwise the staff/moderation flags). Uses discord.py's
`discord.Role` converter (mention/id/name for free) + a friendly `@roleinfo.error` handler. Reachability
guard: 0 GAP (role subsystem is homed + discoverable). +8 tests.

### Decomposition (friction→clean-fix)
Adding `!roleinfo` pushed `role_cog.py` to 840 LOC, over the 800-LOC fail threshold (`test_cog_size`).
Per architecture ("move view code to `views/<sub>/`"), the embed builder + permission summariser were
extracted to **`views/roles/role_info.py`** (`build_role_info_embed` / `summarize_role_permissions`),
leaving the cog command a thin resolve → render → send wrapper. `role_cog.py` back to **782 LOC**.

Regenerated the dashboard/site artifacts (`dashboard.json` / `site.json` / `data.js`) since 3 new
commands changed the command scan (460 → 463). CI mirror **green**: `check_quality --full`
(black/isort/ruff/mypy + **13,109** tests) + `check_architecture --mode strict` (exit 0) +
`check_command_reachability` (0 GAP) + `check_consistency`. Self-merged on green (contained, additive,
`CLASS: feature` self-initiated Q-0172; the channel mutations stay behind the audited seam).

## 📤 Run report

- **Did:** shipped 3 best-in-class operator command gaps (`!slowmode`, `!topic` via the audited
  ChannelLifecycleService seam; `!roleinfo` read-only) + extracted the role-info renderer to keep
  `role_cog` under the decomposition threshold · **Outcome:** shipped (CI green, auto-merge armed)
- **Shipped:** #1561 — `disbot/services/channel_lifecycle_service.py` (set_slowmode/set_topic ops) ·
  `disbot/cogs/channel_cog.py` (slowmode/topic) · `disbot/cogs/role_cog.py` + `disbot/views/roles/role_info.py`
  (roleinfo) · 3 test files (+44 cases) · regenerated dashboard/site artifacts · S1 sector + claim.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (no migration / data step — pure command additions; live on next auto-deploy)
- **⚑ Self-initiated:** yes — empty-fire scheduled dispatch (no work order); built the S1 ▶ Next
  offline-startable named "best-in-class command gaps" from the completion assessment punch-list, grounded
  in the live queue → shipped without a dispatch/owner ask (Q-0172).
- **↪ Next:** S1 ▶ Next offline-startable picks remain — within games **Blackjack split/insurance/surrender**
  (bigger engine work, owner-paced); fishing rare *material*-drop feeding a *new* craft target, or the
  rod-ladder recipe-browser UI; other punch-list deepening (logging ignored-lists/channel+voice events,
  best-in-class command gaps now narrowed to channel slowmode/topic + roleinfo DONE). `channelinfo`/`userinfo`
  already exist. All pure + self-mergeable.

## 💡 Session idea (Q-0089)

**A read-only operator-info hub button or `!info role` sub-target unifying `serverinfo` / `userinfo` /
`channelinfo` / `roleinfo`.** Today these four read-only lookups live in three different cogs (utility,
channel, role) with inconsistent surfacing — `info` has server/user but not channel/role. A small win
would be a single `!info <server|user|channel|role> <target>` dispatcher (or a one-screen "Info" utility
panel button) so a user doesn't have to know which cog owns which lookup. Genuine (the four-way split is
a real discoverability seam the completion-first posture would flag), not filler — route to `docs/ideas/`
if a later session picks it up.

## ⟲ Previous-session review (Q-0102)

The previous run (#1553, inventory sort/filter + the registry↔ledger parity guard) was clean,
well-scoped, shipped three complete slices in one PR, and correctly did fix-on-sight stale-claim cleanup
— a strong example of the completion-first deepening pattern. **One improvement it surfaces:** it left
*two* stale claim files behind (its own report notes "2 stale claims removed"), and this run found *yet
another* stale claim (`claude-funny-franklin-2fdlvx`) from the very session that opened #1553 — i.e. claim
GC is still lagging by one session because a session can't delete its *own* claim until after it has
merged. The Q-0206 claim-GC automation exists; a tiny hardening would be to have the born-red **session
gate** (or `/session-close`) assert "no claim file older than the newest merged PR's branch survives",
turning the recurring manual fix-on-sight into an enforced one (friction→guard, Q-0194). Captured as a
candidate, not built this run (it touches the gate, which is owner-gated executable config).

## Doc audit (Q-0104)

`check_current_state_ledger --strict` not newly affected (no *prior*-merge ledger change this run — #1561
is this session's own PR, reconciled at merge by convention). New code reachable + documented: the two
channel ops are in the service docstring's operation set; `!roleinfo` renderer is in `views/roles/`;
S1 sector recently-shipped updated. No owner decisions to route. Fix-on-sight: removed the stale
`claude-funny-franklin-2fdlvx` claim left by the #1553 session.
