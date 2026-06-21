# 2026-06-21 — Reaction roles: message picker (no more copy-paste message ID)

> **Status:** `complete` — owner-directed follow-up to #1234/#1237 (Q-0191 → merge on green). PR #1243.

> **Run type:** `manual`

## Arc

The emoji reaction-role **Add** flow still asked the operator to paste a raw Message ID — the
clunkiest step, and a frequent Carl complaint. Replaced it with a source chooser on
`ReactionRolesPanel`: **➕ Add → `_AddSourceView`** with four ways to identify the message —

- **📍 Most recent** — binds to the latest message in this channel (no id).
- **📜 Pick recent** — a select of recent messages (`author: preview`), windowed via
  `PaginatedSelectView`.
- **🆕 New message** — `_NewMessageModal` posts an embed/text message, then binds to it.
- **🔢 By ID** — the original `_AddBindingModal`, kept as a fallback.

Every path lands in the existing per-emote role picker (`_BindEmotesView`), so "multiple emotes →
each its own role" (from #1234) still holds. The old `_MoreEmotesModal` was generalised to
`_EmotesModal` (used by the picker paths *and* the "add more emotes" toast).

## Findings / decisions

- **Decision made alone — the controlling constraint is Discord's "a modal must be the *first*
  response to an interaction."** That shaped the whole flow: paths needing an async lookup before the
  message is known can't then open a modal in the same interaction. So **pick-recent** resolves the
  message via a select first, and the *select pick* opens the emotes modal (modal = first response to
  the select); **new-message** uses one modal that captures title+text+**emotes** together, posts,
  then continues to role-picking; **most-recent** does a small `history(limit=5)` then opens the modal
  (one fast call, inside the 3s window).
- **Decision made alone:** the picker excludes the panel's own message (`_panel_message_id`) so it's
  never offered as a target, and `_recent_messages` degrades to `[]` when history can't be read
  (missing permission) — routing the operator to By-ID / New-message instead of erroring.
- **No new service/DB/schema** — this is entirely the `reaction_panel` view; it reuses the audited
  `bind_emoji` seam and `parse_emotes` from #1234.

## Context delta

- **Needed but not pointed to:** the "modal must be the first interaction response" rule is the single
  most important Discord-UI constraint for multi-step flows, and it isn't in the orientation route or
  `.claude/rules/discord-views.md`. It dictates flow shape (you cannot `defer()`/`await` then
  `send_modal`). Worth a one-line rule in `discord-views.md`.
- **Pointed to but didn't need:** nothing new — the existing `reaction_panel` Add flow (#1234) was the
  only context needed; I reused its `_BindEmotesView`/`parse_emotes` wholesale.
- **Discovered by hand:** `PaginatedSelectView`'s on-pick callback receives an *unconsumed*
  interaction, so a select pick can open a modal directly — the linchpin that makes pick-recent work.
- **Decisions made alone:** see Findings (modal-first flow shaping; panel-message exclusion; history
  degrade).
- **Weak point / unverified:** the picker is **not live-walked** — `history()` latency vs. the 3s
  modal window on most-recent, and the select→modal handoff, want a runtime smoke. Pure helpers are
  unit-tested; the interaction wiring is a thin shell over them.
- **One docs/tooling change that would help:** add the modal-first-response rule to
  `.claude/rules/discord-views.md` (did not self-edit — owner-governed file; flagged here instead).

## 📤 Run report

- **Did:** replaced the raw-message-ID Add step with a native message picker (most-recent / pick /
  new / by-id) · **Outcome:** shipped (PR #1243, auto-merge on green)
- **Shipped:** #1243 — reaction-roles Add message picker
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none (owner-directed)
- **⚑ Owner manual steps:** none — merge ≠ deploy; the prod restart stays yours. (The picker needs the
  bot's **Read Message History** permission for most-recent/pick-recent; it degrades to By-ID/New if
  absent.)
- **⚑ Self-initiated:** none (direct owner request, picked via the next-step question)
- **↪ Next:** the gradient-presets-gallery idea (from #1237) is still on the shelf; otherwise a live
  smoke-walk of the three reaction-roles PRs (#1234/#1237/#1243).

## 💡 Session idea

**Add the "modal-must-be-first-response" rule to `.claude/rules/discord-views.md`.** It bit the flow
shape of this PR (and is implicit in several existing views). A one-line binding rule — *"a modal can
only be opened as the first response to an interaction; if you must `await`/`defer` first, route
through a button/select whose callback opens the modal"* — would save the next agent the
reverse-engineering. (Proposed, not applied — `.claude/` is owner-governed; routing as a router
DISCUSS item would be the channel.)

## ⟲ Previous-session review

The #1237 session shipped a lot (channel + colour + gradient) cleanly and answered the gradient
question with ground-truth introspection (good instinct). What it could have done better: it created
**a third same-day branch** for tightly-related reaction-roles work, when the prior two had already
shown the parallel-session branch-name collision risk. **System improvement (carried from #1237's own
review):** `check_lane_overlap.py` should flag two live sessions targeting the same `claude/*` branch,
not just overlapping files — the recurring collision axis this session-chain keeps hitting. (This run
used a fresh, uniquely-named branch precisely to avoid it.)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (pending #1243, auto-merge on green) |
| CI-red rounds | 0 real (born-red HOLD only, by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (modal-first-response rule for discord-views) |
| Ideas groomed | 0 |
