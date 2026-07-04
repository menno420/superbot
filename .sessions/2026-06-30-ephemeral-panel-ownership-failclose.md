# 2026-06-30 — Fix: ephemeral persistent-panel ownership fail-close ("can no longer be verified")

> **Status:** `complete`

**Run type:** owner-directed (bug report — screen recording)

## What I'm about to do

Owner screen recording: opening the **Role hub via `/help` → Community → Roles** and clicking a button
produces **"This panel can no longer be verified — please re-open it."**

**Root cause (confirmed, not the permission work):**
- `RoleHubPanelView` is a `PersistentView` with `FAIL_CLOSED_ON_MISSING_ANCHOR = True`
  (`cogs/role_cog.py:77` — role management is guild-mutating, so opted into fail-closed).
- Its inherited `PersistentView.interaction_check` (`core/runtime/persistent_views.py:114`) verifies
  ownership via a **DB message-anchor row** (`db.get_panel_anchor_by_message`).
- The `/help` path renders the hub via `role_cog.build_help_menu_view()` **ephemerally**, and
  **ephemeral messages are never anchored** (only the `!roles` path anchors, via
  `panel_manager.get_or_render_panel`). Anchor missing + fail-closed → deny → the message
  (`persistent_views.py:127`).
- Anchors are DB-backed, so this is **not** a restart issue; it affects **any** user reaching a
  fail-closed panel through an ephemeral help/nav path, not just the owner.

**Fix (general, safe):** an **ephemeral message is private to the invoking user** — Discord guarantees
nobody else can see/click it — so ownership is implicit and the anchor check is meaningless there. Add a
guard at the top of `PersistentView.interaction_check`: if `interaction.message.flags.ephemeral`, return
`True` before the fail-closed branch. Fixes the whole class with no security loss. Regression test pins:
ephemeral + fail-closed + no anchor → allowed; non-ephemeral + fail-closed + no anchor → still denied.

## What shipped (PR #1582)

- **`core/runtime/persistent_views.py`** — `PersistentView.interaction_check` returns `True` for an
  **ephemeral** message (`interaction.message.flags.ephemeral`) before the anchor lookup / fail-closed
  branch. Ephemeral messages are private to the invoker, so ownership is implicit and the anchor check
  (which exists to stop a *non-owner* clicking a shared panel) is meaningless. No new imports; getattr-guarded.
- **`tests/unit/runtime/test_interaction_fail_open_posture.py`** — `_fake_interaction` now sets
  `message.flags.ephemeral` explicitly (default `False`; a bare MagicMock made it truthy and would have
  silently broken the existing fail-closed tests under this change), and a new regression test
  `test_ephemeral_message_allowed_for_fail_closed_panel` asserts ephemeral + fail-closed + no anchor →
  allowed *and* the anchor lookup is never consulted. Existing fail-closed / fail-open / mismatch tests
  unchanged + still green (9 in the file).

## 📤 Run report

- **Did:** root-caused + fixed the owner-reported "This panel can no longer be verified — please re-open
  it" on the Role hub opened via `/help` — a fail-closed `PersistentView` denying its own opener on an
  ephemeral (anchorless) message · **Outcome:** shipped (CI green, auto-merge armed)
- **Shipped:** #1582 — `disbot/core/runtime/persistent_views.py` (ephemeral short-circuit) +
  `tests/unit/runtime/test_interaction_fail_open_posture.py` (regression + helper hardening).
- **Run type:** `owner-directed` (bug report — screen recording)
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** none (pure logic; live on next auto-deploy). Re-test: `/help` → Roles → click
  a hub button — no more "can no longer be verified". (`!roles` already worked — it anchors the panel.)
- **⚑ Self-initiated:** the bug was owner-reported; the *general* fix (ephemeral-allow for the whole
  fail-closed class, not just role) + the `_fake_interaction` hardening were my judgment calls (Q-0172).
- **↪ Next:** none required. Optional follow-on: the `/help → subsystem` projection opens mutating panels
  ephemerally without anchoring — fine now (ephemeral is owner-safe), but if a *shared* fail-closed panel
  is ever surfaced that way it'd need anchoring; not a current path.

## 💡 Session idea (Q-0089)

**A diagnosis aid for "interaction failed"-class reports: a tiny `tools/` script that extracts evenly
spaced frames from an uploaded screen-recording (imageio-ffmpeg) so an agent can actually *see* the
failing moment.** This session's root cause was only found by frame-extracting the video to the *last*
frame, where the real error ("can no longer be verified") was visible — the earlier frames showed a
red-herring ("This interaction failed"). A reusable `scripts/extract_video_frames.py` (already prototyped
in scratchpad) would make "watch the video" a first-class, repeatable triage step. Genuine (it directly
unblocked this session after three wrong guesses), not filler.

## ⟲ Previous-session review (Q-0102)

The previous run (#1577, the decorator/view completeness fix) was solid and correctly guarded — but **this
session is the real lesson about it and #1573**: I twice declared the bot-owner feature "done" and the
owner twice found it still broken, because I was reasoning from *screenshots/early frames* and my own
mental model instead of the actual failing surface. The first miss was a truncated grep; this one was
diagnosing from frame 0 ("This interaction failed") when the true error was in the final frame ("can no
longer be verified") — a *different bug entirely*. **System improvement:** for any "it still doesn't work"
report with a recording, extract and read the **last** frames first (the terminal error state), and don't
offer a root-cause until the specific on-screen error string is located in the code (grep the literal
message) — which is exactly how this one was finally nailed (`persistent_views.py:127`). "Find the literal
error string in the source before theorising" is the durable habit.

## Doc audit (Q-0104)

No owner *decision* to route (bug fix under the existing ADR-004 contract; the ephemeral carve-out is a
correctness fix to that contract, noted in the code comment + this log). No prior-merge ledger change this
session. `check_docs` / `check_consistency` green via the mirror's `--check-only` equivalent. The fix is
documented at its code site (the interaction_check comment cites the /help → Roles trigger).

## 🛠 Friction → guard (Q-0194)

- **Friction:** the existing `_fake_interaction` test helper used a bare `MagicMock` message, so
  `message.flags.ephemeral` was *truthy by default* — my change would have silently passed the new logic
  while breaking the existing fail-closed assertions in a confusing way. **Guard:** the helper now sets
  `flags.ephemeral` explicitly (default `False`), so every test states the message's ephemerality and the
  short-circuit is exercised deterministically — no future test can accidentally depend on MagicMock truthiness.
- **Friction (diagnosis):** I gave two wrong root causes before locating the real one. **Guard (habit, +
  the Q-0089 idea):** grep the *literal on-screen error string* in source before proposing a cause; for
  recordings, read the final frames first.

## Context delta

- **Needed but not pointed to:** nothing routed me from "This panel can no longer be verified" to
  `persistent_views.py` — the fix was found by grepping the literal string. That's fine (grep works), but
  it confirms the durable habit above. Also: that **ephemeral messages are never anchored** is implicit
  tribal knowledge in the anchor system; the new code comment + test now state it.
- **Pointed to but didn't need:** the persistent_views context-map's large importer list — the change is
  self-contained to one method; blast radius was a non-issue (additive allow, getattr-guarded).
- **Decisions made alone:** made the fix **general** (ephemeral-allow for *all* fail-closed persistent
  panels) rather than special-casing the role hub — ephemeral is owner-private by Discord guarantee, so
  the anchor check is meaningless for any ephemeral panel; safe and removes the whole class.
