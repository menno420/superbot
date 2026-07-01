# 2026-07-01 — Server-log embeds: a face per entry (avatar in the author slot)

> **Status:** `in-progress` — born-red (Q-0133). Run type: manual · owner-directed.
> PR # pending first push.

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

_(filled in at close)_

## Context delta

_(filled in at close)_
