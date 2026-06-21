# 2026-06-21 — Reaction roles: clean up dead bindings

> **Status:** `complete` — owner-directed (screenshots). Q-0191 → merge on green. PR #1248.

> **Run type:** `manual`

## Arc

Owner reported (with screenshots) that the Reaction Roles panel kept showing leftover cruft from old
pre-#1234 testing: `1518271910256054385 · 💀❤️😘 → (deleted role 1515523817881993439)` — a binding
whose role was deleted. They want it gone; the modal `💀 ❤️ 😘` placeholder is a *good* multi-emote
preview and **stays** (no change).

Built a dead-binding cleanup:
- `services/reaction_role_service.py` — `prune_dead_bindings(guild, *, actor_id)` removes every emoji
  binding whose role no longer resolves (each through the audited `unbind_emoji`), returns the removed
  rows; `count_dead_bindings(guild)` is the read-only counterpart.
- `views/roles/reaction_panel.py` — a **🧹 Clean up** button (row 1) that prunes + reports what it
  removed + re-renders, and a `build_embed` "⚠️ Needs cleanup" hint when any binding points to a
  deleted role, so the cruft is self-explanatory and one tap from gone.

## Findings / decisions

- **Decision made alone — explicit cleanup, not silent auto-prune.** A binding to a deleted role is
  100% dead, so auto-removing it on render would be defensible — but silent data mutation on a *read*
  path (`build_embed`) is an anti-pattern, and the owner benefits from *seeing* the cruft + a one-tap
  fix. So: flag it in the embed + a dedicated button. After one tap it's gone, and #1234 stopped new
  dead rows from being created, so "should not remain" holds going forward.
- **Decision made alone — scope = emoji bindings only.** Menus already skip deleted roles on render
  (`build_menu_embed`) and have a Delete action, so the visible rot is the emoji surface. Kept the
  change tight to that.
- **Root cause was already fixed (#1234):** the old concatenated-emoji binding (`💀❤️😘` as one key)
  came from the pre-#1234 single-emote modal; this PR is purely the cleanup for rows left behind.

## Context delta

- **Needed but not pointed to:** nothing new — `list_bindings` + `resources.resolve_role` +
  `unbind_emoji` (all from the existing seam) were everything. The cleanup is the actionable form of
  the health-audit idea I'd queued, so the prior session's idea fed straight into this owner request.
- **Pointed to but didn't need:** the `check_quality --full` mypy leg — the change is small + typed.
- **Discovered by hand:** the legacy `reaction_roles` table stores no `channel_id`, so message-deleted
  (vs role-deleted) bindings can't be detected without the channel — hence cleanup keys on *role*
  deletion (which is the owner's case and the common rot). Worth knowing for any future audit.
- **Decisions made alone:** explicit-cleanup-not-auto; emoji-bindings-only (see Findings).
- **Weak point / unverified:** not live-walked — the button + prune are unit-tested with mocks; the
  actual removal on the owner's server happens when they tap 🧹 Clean up after deploy.
- **One docs/tooling change that would help:** still the modal-first-response rule for
  `discord-views.md` (carried from #1243/#1246; owner-governed, needs a router Q-block).

## 📤 Run report

- **Did:** dead-binding cleanup (🧹 Clean up button + `prune_dead_bindings` + panel hint) ·
  **Outcome:** shipped (PR #1248, auto-merge on green)
- **Shipped:** #1248 — reaction-roles dead-binding cleanup
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none (owner-directed)
- **⚑ Owner manual steps:** after deploy, open `!roles → Reaction Roles → 🧹 Clean up` once to remove
  the existing `💀❤️😘 → (deleted role)` binding. (Deploy itself is automatic on merge per Q-0193.)
- **⚑ Self-initiated:** none (direct owner request)
- **↪ Next:** reaction-roles is feature-complete + self-healing; the modal-first-response docs rule
  remains the one open workflow follow-up (router DISCUSS).

## 💡 Session idea

**Auto-prune dead bindings on the reaction listener's miss path.** When `on_raw_reaction_add` fires
for a bound emoji whose role no longer resolves, that's a definitive signal the binding is dead —
the listener could opportunistically remove it (audited) right then, so dead config self-heals
without anyone opening the panel. Cheaper + more thorough than a manual sweep; gated behind the
existing `reaction_roles_enabled`. (Dedup-checked `docs/ideas/` — not captured.)

## ⟲ Previous-session review

The #1246 (self-initiated gradient presets) session was a clean, small, flagged increment — good
example of the autonomy loop. But it (and I, this chain) kept *queuing* a "reaction-role health
audit" idea while the owner actually wanted the **actionable** version (remove the rot, not just
report it). **System improvement:** when an idea is "detect/surface problem X," prefer shipping the
*fix-X* action over a read-only audit unless the fix is risky — an audit that only lists a problem
the operator must then fix by hand is half a feature. The owner's report confirmed it: they didn't
want to *see* the dead binding flagged, they wanted it *gone*.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (pending #1248, auto-merge on green) |
| CI-red rounds | 0 real (born-red HOLD only, by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (listener-path dead-binding self-heal) |
| Ideas groomed | 1 (turned the queued health-audit idea into the shipped cleanup) |
