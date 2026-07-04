# 2026-07-01 — Server-log embeds: a face per entry (avatar in the author slot)

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Full CI mirror green (**13618 passed**; ruff/black/isort/mypy clean; arch 0 new). PR #1618.
> Scope: subject avatar in **every** server-log embed (passive + moderation + audit).

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

A face in the author slot of **every** server-log embed — additive across all surfaces
(`services/server_logging.py`):

1. **`_set_subject_author(embed, user)`** — defensive helper that puts the subject's `display_name` +
   `display_avatar.url` in the embed **author slot** (`set_author`). A partial/odd object or `None` yields
   no author line rather than raising into the fail-safe handler. No network — the embed references the CDN url.
2. **Passive-event builders (5)** hold the object they log, so they pass it straight in:
   `format_message_delete_embed`/`_edit` (author), `format_member_join`/`leave` + `format_role_change` (member).
3. **Moderation + audit builders (3)** carry only ids, so the *sender* resolves the person via
   **`_resolve_subject_user`** (guild member cache → the bot's global user cache, so a just-banned/kicked
   member still gets a face; **cache-only, never a network call**) and passes it into `format_log_embed`
   (target), `format_public_log_embed` (target — never the moderator, preserving the redaction), and
   `format_audit_embed` (actor). Every structured field on every embed is untouched.
4. **Helpers centralised** — `_set_subject_author` moved up beside the new `_resolve_subject_user`, before
   the first builder, so every call site is a clean backward reference.
5. **Tests (+11 total)** — passive (message/member/role author-avatar + defensive-on-partial), mod-log +
   public-log subject avatar + no-subject-no-author, audit actor avatar + no-subject, and the four
   `_resolve_subject_user` paths (member hit · bot-cache fallback · none-id · unresolvable). Full logging
   suite green (132 passed).
6. **Docs** — `docs/server-logging.md` "Handlers + embeds" now documents the face-per-entry across all
   surfaces (target vs actor vs redacted public) via `_resolve_subject_user`.

Approximate before/after embed mockup (passive "Message deleted") shared in chat — embeds can't be rendered
to PNG, so it's a sketch; Discord draws the real chrome + emoji. The mod/audit embeds gain the identical
author-slot avatar.

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
- **Extension (owner: "make everything the same"):** whose face per surface is a real decision — mod-log →
  the **target** (the person acted on, matching the passive events); audit → the **actor** (there's no
  person "target", the record is a config change, so the face is *who changed it*); public mod-log → the
  **target only**, never resolving the moderator, so that surface's deliberate redaction is preserved.
- **Cache-only resolution, no network in the hot path:** `_resolve_subject_user` tries the guild member
  cache then the bot's global user cache (`bot.get_user`) — the latter is what lets a just-banned/kicked
  member (already gone from the guild) still show a face, without a fetch. Unresolvable → no author line,
  the same graceful degradation as a departed member.
- **Folded into #1618 rather than a follow-up PR:** the owner asked for it while #1618 was still open
  (CI blocked, not merged), so I **disabled auto-merge** to hold it, added the extension, and re-armed at
  the end — one coherent "avatars on every log embed" change instead of two PRs. (If it had already merged,
  the rule is a fresh branch/PR; it hadn't, verified by fetch.)

## 🛠 Friction → guard

**The existing guard did its job — no new one needed.** The mod/audit extension's `_resolve_subject_user`
first used a raw `guild.get_member(...)`, which the **`test_no_raw_guild_lookups_outside_resolver` invariant**
caught in the full CI mirror (raw member/role/channel lookups must go through `core.runtime.guild_resources`).
Fixed by routing through `resources.resolve_member`. This is exactly the "enforce, don't exhort" loop working:
a checker caught a footgun I'd have otherwise shipped, so there's nothing to add — the guard already exists
and fired. (Lesson logged, not a new guard.) The passive-event half was clean first try; the born-red /
force-with-lease branch restart (last PR merged) went fine once the stale remote ref was refreshed (already
a journal Rule).

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
