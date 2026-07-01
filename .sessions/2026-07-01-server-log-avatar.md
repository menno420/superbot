# 2026-07-01 — Server-log embeds: a face per entry (avatar in the author slot)

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Full CI mirror green (**13610 passed**; ruff/black/isort/mypy clean; arch 0 new). PR #1618.

**Branch:** `claude/visual-comparison-other-bots-89vna4` (restarted from `main` @ #1614 merged).

## What I'm about to do (intentions)

The owner compared our `#server-log` style with **Dyno's** and said ours is already nice — but asked for
one improvement idea. Ours is genuinely good (colour-coded borders, emoji titles, structured
Author/Channel/Content/Before/After/Attachments/Jump fields, full IDs). The **one thing Dyno has that we
don't** is a per-entry **avatar** — a small round face beside the name at the top of each log embed, so you
see *who* at a glance while scanning.

The idea (purely additive — changes no field the owner likes): add the event **subject's** avatar + display
name to each passive-event log embed's **author slot** (`embed.set_author(name=…, icon_url=…)`). The five
`format_*_embed` builders in `services/server_logging.py` already hold the `discord.Member`/`User` object
(`message.author`, `after.author`, `member`) with `.display_avatar.url` + `.display_name` right there, and an
embed references the CDN url directly — **zero network on our side, no failure path**. The structured fields
(mention + copyable id) stay exactly as they are.

Scope: the 5 passive builders shown in the screenshot (message delete/edit, member join/leave, role change).
The moderation/audit embeds (`format_log_embed`/`format_audit_embed`) only carry ids, not objects — noted as
a trivial follow-up (resolve the member from the guild), out of scope here.

## What shipped

One small, additive change to `services/server_logging.py`:

1. **`_set_subject_author(embed, user)`** — a defensive helper that puts the subject's `display_name` +
   `display_avatar.url` in the embed **author slot** (`set_author`). A partial/odd object (no
   `display_name`/`name`) yields no author line rather than raising into the fail-safe handler. No network
   on our side — the embed references the CDN url.
2. Wired into all **five** passive-event builders: `format_message_delete_embed` (author),
   `format_message_edit_embed` (after.author), `format_member_join_embed` / `format_member_leave_embed` /
   `format_role_change_embed` (member). Every structured field is untouched — the avatar is strictly extra.
3. **Tests (+3)** — message embeds set the author avatar, member/role embeds set it, and the helper is
   defensive on a partial object. Updated the two mock factories (`_message`, `_member`) to carry
   `display_name` + `display_avatar.url`. Full logging suite green (124 passed); full CI mirror green; arch 0.
4. **Docs** — `docs/server-logging.md` "Server event logging v1 → Handlers + embeds" notes the author-slot
   avatar (+ that mod/audit embeds are the follow-up).

Approximate before/after embed mockup shared in chat (embeds can't be rendered to PNG; Discord draws the
real chrome + the colour emoji).

## Context delta

- **Right altitude for "come up with an idea":** the owner said our style is already nice and asked for *an
  idea* — so the win had to be **purely additive** (add a face, remove nothing he likes), not a restyle.
  `set_author` (a small avatar+name header) is exactly that and is the one thing Dyno had that we didn't.
- **`set_author` over `set_thumbnail`:** the author slot is the compact, top-left "who" indicator (Dyno's
  look); a thumbnail would be a big right-side image that fights the structured fields.
- **Scoped to the 5 passive builders** (the screenshot surface). The mod/audit embeds only carry ids, so
  their avatar needs a guild member-resolve — deliberately deferred as a clean follow-up, not stretched
  into this PR.
- **Cheaper than the card avatars:** unlike the rank card (which fetches bytes), an embed references the
  avatar URL directly — zero network, no fallback path, so this is lower-risk than last session's avatar work.
- **Verification gap for embeds:** I can render image *cards* to PNG and Read them, but an *embed* can't be
  screenshotted here — the honest verification is the unit test (author slot asserted) + the owner's live
  check post-merge. The mockup is an approximation, flagged as such.

## 🛠 Friction → guard

None this session — the change was additive with no footgun, CI was green first try after the local mirror,
and the born-red/force-with-lease branch restart (last PR merged) went cleanly once the stale remote ref was
refreshed (already a documented journal Rule: sync/branch-fresh on a resumed session). No new guard warranted.

## 💡 Session idea

**Consolidate bulk deletes into one log embed.** A moderator purge fires `on_bulk_message_delete` (or N
rapid `on_message_delete`s); if we log each individually the channel floods with dozens of near-identical
"Message deleted" embeds. Add an `on_bulk_message_delete` listener that posts **one** embed — "N messages
deleted in #channel" with a small sample — instead of N. Genuinely useful (purges are the common case that
makes a log channel unreadable) and distinct from today's per-message path. Flagged here per Q-0089; modest
scope, so a log flag rather than a full idea file.

## ⟲ Previous-session review

Prev: `2026-07-01-visual-comparison-cards.md` (PR #1614 — rank/leaderboard card polish). **Did well:**
rendered the actual before/after PNGs and *Read* them to verify (the real "visualize, then build" loop),
fixed emoji tofu at the engine seam (root-cause, one place), and scoped cleanly (deferred `member_display`
+ `/myprofile`). **Could improve:** the leaderboard `_bar_fraction` floor (0.12) left the mid-pack bars a
bit clustered — I picked a curve and shipped without A/B-rendering two or three alternatives to compare,
which for a purely-visual choice would have been cheap and more defensible. **Workflow surface:** visual
work now has *numeric* property guards (the `_bar_fraction` monotonicity test) but no *golden-image*
regression — a future edit could quietly re-introduce the outlier-squash and no test would catch it.
Worth considering a lightweight golden-PNG (or perceptual-hash) guard for the card engine, so the visual
contract is enforced, not just the numeric one. (Captured as a thought — same no-filler bar as Q-0089.)
