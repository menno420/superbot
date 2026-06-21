# 2026-06-21 — Reaction roles: channel picker + auto-created colour/gradient roles

> **Status:** `complete` — owner-directed follow-up to #1234 (Q-0191 → merge on green). PR #1237.

> **Run type:** `manual`

## Arc

Three owner-requested enhancements to the role-menu builder, on a fresh branch
(`claude/reaction-roles-channel-and-colors`, not the merged+contested
`claude/lucid-carson-qsn1gc` — Q-0014: branch identity is not significant):

1. **📍 Post-channel picker** — `RoleMenuBuilder` gained a Channel control so a menu can be posted
   to a dedicated reaction-roles channel, not just the channel the panel is open in. Reuses
   `views.selectors.attach_channel_select`; the target is shown in the builder embed.
2. **🎨 Auto-created colour roles** — a Colours flow: a multi-select of the 8 `_COLOR_OPTIONS`
   presets + a Custom modal (name + 1–3 hex colours). Each chosen colour becomes a role —
   reuse-if-same-name, else create via `reaction_role_service.ensure_color_role` →
   `RoleLifecycleService` (the audited, allowlisted `create_role` caller) — then added to the menu.
3. **✨ Gradient / holographic roles** — `RoleLifecycleRequest` + the create/edit paths now carry
   `secondary_color`/`tertiary_color`; `supports_role_gradients(guild)` gates the gradient UI on the
   guild advertising the Enhanced-Role-Styles feature, with a caught-failure solid-colour fallback.

## Findings / decisions

- **Gradient roles — researched + answered (the owner's question).** discord.py **2.7.1** (our pin)
  *does* support it: `Guild.create_role` and `Role.edit` both accept `secondary_colour`/`secondary_color`
  and `tertiary_colour`/`tertiary_color` (verified by introspecting the installed lib — ground truth,
  not docs). Two colours = gradient, three = holographic. **Discord gates it server-side:** the
  *Enhanced Role Styles* perk needs **3 applied server boosts** (independent of boost *level*); without
  it the API 400s, and if the perk lapses Discord reverts styled roles to their primary solid colour.
  ([support](https://support.discord.com/hc/en-us/articles/31444213087255-Enhanced-Role-Styles),
  [blog](https://discord.com/blog/get-more-from-your-boosts-with-new-server-perks)).
- **Decision made alone:** colour-role creation routes through `RoleLifecycleService` (audited,
  event-emitting, on the `test_no_silent_auto_create` allowlist) rather than a raw `guild.create_role`
  in the view — keeps the create auditable and arch-clean. `ensure_color_role` reuses a same-named
  role rather than making duplicates.
- **Decision made alone:** gradient is **double-gated** — `supports_role_gradients` (a *defensive
  substring* match on `guild.features`, since the exact flag shifted during rollout) decides whether to
  *offer* it, and the create path **retries solid** if a gradient create is rejected anyway. A stale
  feature read is therefore never fatal.
- **Decision made alone:** the post-channel picker offers `guild.text_channels`; Duplicate/Repost
  channel semantics from #1234 are unchanged.

## Context delta

- **Needed but not pointed to:** which discord.py version we run + whether it supports gradients —
  resolved by `python3.10 -c "import discord; inspect.signature(Guild.create_role)"` (ground truth >
  docs). Worth a journal note: *introspect the installed lib for "does our version support X" before
  reaching for docs.*
- **Discovered by hand:** `RoleLifecycleService` is the **single sanctioned `create_role` caller**
  (allowlisted by `tests/unit/invariants/test_no_silent_auto_create.py`) — any new role creation MUST
  go through it or the invariant fails. This is in the service docstring but not the orientation route.
- **Pointed to but didn't need:** the broad `docs/current-state.md` callouts — the plan doc +
  `role_lifecycle_service` docstring were the load-bearing context.
- **Decisions made alone:** see Findings (audited create; double-gated gradient).
- **Weak point / unverified:** the gradient + colour-create paths are unit-tested with the API mocked;
  **not live-walked** against a real boosted guild — the actual `create_role(secondary_color=…)` round
  trip and the 400→solid fallback want a runtime smoke on a 3-boost server.
- **One docs/tooling change that would help:** an orientation line "creating a role at runtime? → only
  via `RoleLifecycleService` (invariant-guarded)" so the next agent doesn't reach for `guild.create_role`.

## 📤 Run report

- **Did:** menu post-channel picker + auto-created colour roles + gradient/holographic support ·
  **Outcome:** shipped (PR #1237, auto-merge on green)
- **Shipped:** #1237 — reaction-roles channel picker + colour/gradient role auto-create
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none (owner-directed)
- **⚑ Owner manual steps:** **gradient/holographic roles need the server to have applied 3 boosts**
  (Enhanced Role Styles) — without it the bot creates solid-colour roles. Merge ≠ deploy: the prod
  restart stays yours.
- **⚑ Self-initiated:** none (direct owner request)
- **↪ Next:** optional live-walk on a boosted guild to confirm the gradient round-trip; the
  message-picker idea from #1234 still stands.

## 💡 Session idea

**Gradient/holographic presets gallery.** Now that gradient roles are wired, a curated gallery of
ready-made two/three-colour styles (e.g. "Sunset", "Ocean", "Holographic") as one-tap picks in the
Colours flow — the blank-page killer for styled roles, mirroring the message-template gallery. Cheap
(pure data + the existing `ensure_color_role` path), only surfaced when the guild has the perk.
(Dedup-checked `docs/ideas/` — not captured.)

## ⟲ Previous-session review

The #1234 session (this chain's predecessor) handled the mid-session branch collision well (clean
rebase, no force-push) and corrected the multi-role misread fast. What it could have done better:
its session card claimed the work "merge on green" while a **parallel session shared the same branch
name** — the collision was only caught at push time. **System improvement:** the claim ledger keys on
*scope*, but the real collision axis is the *branch name*; `check_lane_overlap.py` (shipped #1223)
should also flag when two live sessions target the same `claude/*` branch, not just overlapping files —
that would have surfaced the #1234/creature collision *before* the first push.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (pending #1237, auto-merge on green) |
| CI-red rounds | 0 real (born-red HOLD only, by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (gradient presets gallery) |
| Ideas groomed | 0 |
