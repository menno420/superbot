# 2026-06-30 — Reaction-roles live sign-up counter (S1 deepening)

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Full CI mirror green (**13175 passed**, 48 skipped; black/isort/ruff + mypy clean; arch strict 0
> new). PR #1570.

**Branch:** `claude/reaction-roles-counter-bgxnyd`.

## What I'm about to do (intentions)

Owner request (Discord screenshots): an event organiser wants members to press a button to signal
"I'm in" for an event (e.g. *"see how many people are planning to get 15K stars"*) — and wants a
**counter that keeps track of how many people pressed the button**, visible on the message itself
(the value-add over native emoji reactions, which only count anonymously and don't persist a role).
Mid-session the owner clarified: it should support **multiple options** (join / don't join /
participate a little) — i.e. a multi-button RSVP poll, each option counted.

## What shipped

An **opt-in live sign-up counter** on role menus, plus a two-tap path to the multi-option RSVP poll:

1. **migration 103** — `role_menus.show_counts BOOLEAN NOT NULL DEFAULT FALSE` (additive; existing
   menus byte-identical).
2. **`utils/db/role_menus.py`** — `show_counts` threaded through `create_menu` / `update_menu`.
3. **`services/reaction_role_service.py`** — `show_counts` threaded through the audited create/update;
   surfaced in the audit `_summarize` (so turning the counter on/off is in the audit trail).
4. **`views/roles/role_menu_counter.py`** (new) — `collect_counts(guild, role_ids)` computes per-role
   **current-holder** counts + a **distinct-member total** in **one pass** over `guild.members` (a
   member holding two of the menu's roles is counted once); `format_count` / `format_total`; and a
   **debounced** `schedule_count_refresh(message, menu_id)` — a trailing-edge edit (~2.5 s) that
   coalesces a click-burst into **≤1 message edit per window per message** and re-reads counts live, so
   a popular event can't trip Discord's edit rate-limit.
5. **`views/roles/role_menu_view.py`** — `build_menu_embed` renders the inline per-role count + a
   footer headcount when `show_counts`; the button/select callbacks fire a debounced refresh after a
   successful change (cheap `_view_shows_counts` gate so non-counted menus schedule nothing).
6. **`views/roles/role_menu_builder.py`** — a **📊 Counts** toggle (row 2, within the 5-button cap) +
   a "Sign-up counts: on/off" preview line + threaded through Post/Save + `from_menu` load.
7. **Multi-option ergonomics** — a **📣 Event RSVP** starter template (`role_menu_presentation`:
   button + `unique` + counts on) so the live poll is one tap; `MenuTemplate` gained `mode` +
   `show_counts` fields (the per-key mode special-casing in the builder moved into the template data —
   single source of truth); a matching **📣 Event RSVP** role pack (`role_packs`: Going / Maybe /
   Can't make it).
8. **Tests** — +35: counter one-pass math + distinct-total + debounce coalescing + the refresh
   re-render/bail/swallow paths; embed-with/without-counts rendering; service threading + audit
   summary; db INSERT/UPDATE param pinning; template fields + RSVP template/pack.

**Semantics decision (made alone, reversible):** the counter is **current holders**
(`guild.members` ∩ role), not a cumulative press tally — an RSVP must drop when someone un-signs or
leaves, and a live membership count is self-correcting (never drifts). Deliberately distinct from the
operator-only cumulative `role_menu_pickup_stats` rollup (Diagnostics). The bot runs the members
intent + startup chunking, so the count is accurate.

## Why this is contained / safe

Additive + default-off → every existing menu renders byte-identically; no data backfill. No new
commands (UI lives in the existing `!roles` builder). All writes stay on the audited
`reaction_role_service` seam; the counter reads only (no DB writes, no role math in views). The
refresh is best-effort and swallows every failure — a bad cosmetic edit can never undo the role
mutation that triggered it. Architecture strict: 0 new violations; no import cycle (the view→counter
edge is module-level, counter→view is lazy inside the refresh).

## Context delta

- **Discovered:** the role-menu surface **already supports multiple options** (one `_RoleButton` per
  role in button style, ≤25), and `unique` mode already makes them mutually exclusive — so the
  owner's "join / don't join / maybe" poll needed **no engine change**, just the counter + a starter
  template/pack to make it discoverable. The existing `role_menu_pickup_stats` (migration 081) looked
  related but is the wrong primitive (cumulative events, operator-only) — confirming current-holders
  was the right semantic took reading the migration's own header note.
- **Decisions made alone (all reversible):** current-holders over cumulative; opt-in per-menu over
  always-on (counts are noise on a colours/pronouns menu); footer distinct-total over a redundant
  field; debounced trailing-edit over live-edit-per-click (rate-limit safety) and over a periodic
  sweep (no managed-task cost — the number is always live at render time anyway).
- **🛠 Friction → guard:** the existing `test_builder_keeps_every_action_row_within_discords_five_button_cap`
  regression guard already covers the new 📊 Counts button (row 2 = Card/Counts/Post/Back = 4 ≤ 5) —
  no new guard needed; the row-cap footgun is already enforced.

## 💡 Session idea (Q-0089)

**RSVP roster view** — for a counted menu, a `👥 Who's in?` affordance that shows the *ephemeral list
of members* under each option (not just the count). The organiser's natural next question after "how
many" is "who" — and because every option is a real role, the roster is a free `role.members` read
(no new storage), the same primitive the counter already uses. Pairs perfectly with the Event RSVP
template. Recorded here per Q-0089 (kept in the log rather than a file — it's a small, well-scoped
follow-on on the seam this PR just built).

## ⟲ Previous-session review (Q-0102)

Predecessor by the S1 ledger is **#1568 (Counters completion deepening)**. **Did well:** textbook
completion-first discipline — picked one `◐ assessed` unit, closed its four *buildable* punch-list
items end-to-end, routed every preset write through the audited `SettingsMutationPipeline` rather than
a shortcut, and was scrupulously honest about the one stateful item (loop backoff) it left open.
**Could improve / system note:** that session (like several before it) re-derived "does this need a
site.json/dashboard regen?" by hand. This session confirmed the *inverse* is also a silent trap —
a **non-command** feature (mine adds none) needs **no** regen, but there's no cheap signal telling an
agent which side of that line they're on, so each session reasons it out from scratch. **Improvement:**
a one-line `check_quality`/pre-pr readout — "commands changed vs last commit: 0" — would let a session
*know* whether the generated-artifact regen applies instead of inferring it. (Captured as the workflow
takeaway; not built this session to keep scope on the owner's feature.)

## 📤 Run report

- **Did:** shipped an opt-in **live sign-up counter** on role menus (current-holder headcount per
  option + distinct total, debounced live refresh) + an **Event RSVP** template & role pack that make
  the multi-option "Going / Maybe / Can't make it" live poll two taps away. · **Outcome:** shipped
- **Shipped:** PR #1570 — feat(roles): live sign-up counter on role menus (auto-merge on green CI)
- **Run type:** `manual · owner-directed`
- **Class:** feature/deepening (additive, opt-in, reversible, audited-seam, test-covered)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — merge auto-deploys (migration 103 applies on next boot; no data
  backfill, the column defaults off)
- **⚑ Self-initiated:** no — owner-directed (the Discord request + mid-session multi-option
  clarification). The Event RSVP template + role pack are the path to the stated goal (Q-0014: approving
  the goal approves the path), not a separate self-initiated feature.
- **↪ Next:** the **RSVP roster view** idea above; or per-menu counter polish (counts on the button
  labels / dropdown descriptions); or continue the S1 completion-first punch-lists (Counters loop
  backoff · Diagnostics pagination).
