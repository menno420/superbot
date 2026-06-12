# Community platform features — welcome, feeds, events, counters (2026-06-12)

> **Status:** `ideas` — distilled from research uploaded by the owner
> (2026-06-12: competitor analysis covering ProBot, YAGPDB, Koya, Statbot, Sesh,
> and a broad Discord bot landscape survey). Dedup-checked against `superbot-vision-2026-06-10.md`,
> `owner-vision-ideas-2026-06-08.md`, `competitive-teardown-2026-06-10.md`,
> `fun-and-ease-brainstorm-2026-06-09.md`, and the roadmap.
> **Not a plan, not approval.** Route through `ideas/README.md` before touching code.

## Context

The uploaded research identifies a cluster of "community server management" features
that popular bots (Carl-bot, Dyno, Koya, ProBot, Sesh, Statbot) provide and SuperBot
currently does not. These differ from the game/economy RPG lane — they are server *staff*
and *community engagement* tools, not player progression. The research classifies them
all as "Important improvement" priority.

---

## 1. Welcome service with customizable images

### What competitors do

ProBot and Koya generate customized welcome cards on member join: the user's avatar is
composited onto a template background with their username, discriminator, and server
member count. These are sent to a configurable `#welcome` channel. Koya also supports
join DMs (private greeting to the new member), auto-roles on join (role assigned
immediately, before the member takes any action), and goodbye messages on leave.

### SuperBot gap

SuperBot handles no join/leave events beyond guild_lifecycle.py. There is no welcome
message, no welcome image, and no join auto-role distinct from the time/XP-based
role-automation already in the role hub.

### Proposed design

A `services/welcome_service.py` that:

- Listens for `on_member_join` and `on_member_remove`.
- Sends a configurable welcome embed (or PIL-generated image card) to a designated
  `#welcome` channel.
- Optionally sends a join DM to the new member.
- Assigns a configurable "entry role" on join (distinct from XP/time roles — instant).
- Sends a goodbye message on member remove.
- Config lives in the setup wizard (welcome section) and a settings panel.

### PIL image card specifics

The uploaded research confirms the PIL approach is feasible within Discord's bot constraints:
- Bot upload limit is **~8 MiB per file** (see `docs/operations/discord-platform-limits.md`).
- A 1920×1080 JPEG at medium compression is typically under 1 MB — well within limits.
- Avatar + background + text = straightforward Pillow composite.
- Export as JPEG or WebP, never raw PNG (too large for high-res cards).
- Include an `alt_text` description for accessibility (Discord supports alt-text on attachments).

### Sizing and risk

Medium. The PIL template system is the most novel part; the event subscription and
config UI are straightforward. Risk: avatar-fetch latency (download the avatar URL on
join; handle network failures gracefully with a fallback text-only embed).

### Route

→ **Q-0110** (discuss: does the maintainer want image cards on day one, or start with
embed-only welcome and add PIL cards later?). Then: plan.

---

## 2. Social feed notifications (YouTube, Twitch, RSS, Reddit)

### What competitors do

YAGPDB supports fast Reddit, YouTube, and RSS feeds. Koya extends this to YouTube,
Twitch, Kick, RSS, Reddit, Spotify, and Bluesky — with custom messages, role pings,
content filters, and per-source channels. Carl-bot also provides YouTube and Twitch
notifications.

### SuperBot overlap and gap

The owner already confirmed (Q-0041) a **YouTube-first / dual-opt-in / voice-deferred**
posture. A YouTube notification service (new-video alert in a configured channel) is
approved in principle. The owner vision mentions Twitch and Spotify.

What the research adds is the service design: a unified feed-subscription model where
each guild can subscribe to N external sources (YouTube channel ID, Twitch username,
RSS URL, subreddit) and map each source to a Discord channel and an optional role ping.

### Proposed design

A `services/feed_service.py` (or `notification_service.py`) with a polling scheduler:

- Stores per-guild subscriptions: `(source_type, source_id, discord_channel_id, role_id)`.
- Scheduler runs at configurable intervals per source type (YouTube: every 10 min via
  YouTube Data API; Twitch: on-live webhook or polling; RSS: every 15 min).
- On new content detected: posts an embed with title, thumbnail, URL, and optional role
  mention to the configured channel.
- Per-source filters: exclude certain keywords from titles (e.g., skip a channel's
  "shorts" by keyword).
- Config panel in the setup wizard and a feeds-management hub.

### YouTube summarization extension

The uploaded research also covers YouTube video summarization: fetch the transcript via
the YouTube Data API, send it to an LLM (OpenAI/Claude/Gemini), and return a structured
summary to Discord. This pairs naturally with the feed service — when a new video alert
fires, optionally include an AI-generated summary. Constraints:
- Not all videos have transcripts; auto-generated transcripts may be inaccurate.
- Long transcripts may exceed LLM context windows → chunk + summarize iteratively.
- Adds API cost per video (Q-0082's hard ceiling applies).
- The owner confirmed YouTube-first; this is the enrichment layer on top.

### Sizing and risk

Large scope across all source types; manageable if shipped incrementally (YouTube first,
then RSS, then Twitch). Risk: YouTube Data API quota exhaustion; Twitch webhook setup
complexity. Cost: YouTube summarization adds LLM calls → meter under Q-0082 spend cap.

### Route

→ **Roadmap Later** (Q-0041 approves the direction; no new owner Q needed for YouTube
start). Build plan needed before implementation.

---

## 3. Event scheduler

### What Sesh does

Sesh provides natural-language event creation ("next Friday 8pm" → parsed datetime),
RSVP collection (yes/no/maybe), attendance limits with waitlists, automatic time-zone
conversion per user, availability polls (multiple-time voting), role assignment for
attendees, and Google Calendar export.

### SuperBot gap

No in-Discord event scheduling exists. The owner mentioned timers and polls as part of
the "General commands" section of the ideal help menu.

### Proposed design

A `services/event_service.py` with:

- **Simple tier (no NL):** slash command `/event create` with structured date/time
  input (Discord's built-in datetime picker) + title + description + optional
  attendee limit. Posts a formatted event embed with RSVP buttons (✅ Yes / ❓ Maybe / ❌ No).
- **Reminder tier:** reminder message sent to RSVP'd members N minutes before the event.
- **NL tier (later, gated):** natural-language time parsing via an LLM call → adds AI cost;
  gate on Q-0082 spend ceiling and the maintainer's approval.
- **Availability poll:** an embed listing multiple time slots; members vote; the bot
  highlights the winning slot.
- Time zones: store each user's preferred timezone (extends per-user preferences from
  superbot-vision V-04); display event times in each user's local zone.

### Sizing and risk

Simple tier is small (embed + buttons + reminder scheduler). NL tier adds LLM cost.
Risk: reminders require a persistent scheduler — the bot already has scheduler
infrastructure (check `disbot/` for existing scheduler patterns before designing).

### Route

→ **Q-0112** (discuss: simple tier approved standalone vs. needs the NL tier to be
worthwhile? Any existing scheduler to reuse?). Then: plan.

---

## 4. Custom commands (TagScript-safe)

### What competitors do

Carl-bot, Dyno, and YAGPDB let server operators create custom commands stored in the
DB: a trigger (prefix, exact, contains, or regex match) maps to a templated response.
YAGPDB uses a full TagScript interpreter; Carl-bot uses a simpler variable-substitution
syntax. Both sandbox execution so operators can't run arbitrary code.

### SuperBot gap

All commands are hardcoded in Python cogs. Server operators can't create their own
without a code deployment.

### Proposed design

A `services/custom_command_service.py` with:

- DB table: `(guild_id, trigger, match_type, response_template, created_by, created_at)`.
- Match types: prefix, exact, contains, regex (regex tier: admin-only, size-limited).
- Template variables: `{user}`, `{server}`, `{channel}`, `{args}` — no code execution.
- Management panel: add/edit/delete custom commands, with a live-preview before save.
- Governance: operator or admin role required to create/modify; member-accessible to invoke.
- Sandboxing: response templates are evaluated with a strict whitelist renderer —
  no `exec()`, no imports, no external calls.
- `on_message` handler checks custom commands after built-in command prefix handling
  (lowest priority, so built-in commands always win).

### Sizing and risk

Medium. The DB schema and CRUD panel are straightforward; the sandboxed template
evaluator needs careful implementation (no escape into Python runtime).
Risk: abuse — require admin/operator role to create; log every command creation via
the audit service.

### Route

→ **Roadmap Someday** (no new Q needed; direction is clear but scope is large and
lower-priority than the other items in this file). Groom to Later once the core
moderation/logging layer lands.

---

## 5. Dynamic server counters (Statbot / ServerStats style)

### What competitors do

ServerStats and Statbot provide "statdocks": voice channels whose names are
continuously updated to show live server statistics — member count, online member
count, bot count, server boost level, current date, custom goals.

### SuperBot gap

No such feature exists. The info is available via Discord's API; it just needs a
scheduled task to rename the channels.

### Proposed design

A `services/counter_service.py`:

- Per-guild config: list of `(voice_channel_id, counter_type, display_format)` rows.
- Counter types: total members, online members, bot count, human count, boosts,
  a custom number (set by admin).
- Scheduled task: runs every 10 minutes (Discord rate-limits channel renames to 2/10 min
  per channel, so multiple counters need multiple channels).
- Setup: a counter wizard sub-panel where the admin creates a dedicated voice channel
  (bot auto-names it on creation) per counter type.

### Sizing and risk

Small. Mostly a scheduler task + config panel. Risk: rate limiting (respect Discord's
channel-rename rate limit; log throttle hits). The voice channel is "locked" (no
join permission for members) — standard pattern for counter bots.

### Route

→ **Roadmap Next/Later** (quick-win candidate; small scope; no new Q needed).
Groom into an executable slice once automod or logging is underway.

---

## Routing summary (updated 2026-06-12 — owner decisions via Q-0110/Q-0112)

| Idea | Size | Risk | Decision | Next destination |
|---|---|---|---|---|
| Welcome service — Phase 1 (embed-only) | Small | Low | **APPROVED** (Q-0110) | Plan `services/welcome_service.py` |
| Welcome service — Phase 2 (PIL image cards) | Medium | Low | **APPROVED as follow-up** (Q-0110) | Plan after Phase 1 stable |
| Social feed notifications (YouTube) | Medium | Low–medium | Approved direction (Q-0041) | Roadmap Later — needs plan |
| Social feed notifications (other sources) | Large | Medium | Captured | Roadmap Someday |
| YouTube video summarization | Medium | Medium (AI cost) | Captured | Roadmap Later |
| Event scheduler (NL time parsing from day one) | Medium | Medium (AI cost) | **APPROVED** (Q-0112) | Plan needed before implementation |
| Custom commands | Medium | Medium (sandboxing) | Captured | Roadmap Someday |
| Dynamic server counters | Small | Low | Captured | Roadmap Next (quick-win, no Q needed) |
