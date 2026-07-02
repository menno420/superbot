# 2026-07-02 — Admin/logging guilds idea + Railway alerts webhook restored

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Docs + one additive live execution under Q-0213 (no deletes; secrets never printed — hash
> receipts only). `check_docs --strict` ✓. PR #1644.

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7` (restarted from `main` @ #1642 merged).

## What I'm about to do (intentions — as declared born-red)

Capture the owner's dedicated admin-guild + central-logging-guild idea; restore his
accidentally-deleted Railway webhook channel.

## What shipped

**1. The Railway alerts feed — restored end-to-end (live, verified):**

- Discovery: the owner's original **Railway notification rule survived** the channel deletion —
  rule `8d8fc9b4…` (all `Deployment.*`/`VolumeAlert.*`/`Monitor.*` events, project
  `reliable-grace`) was posting into a dead Discord webhook (verified HTTP 404).
- Restore: `#railway-alerts` channel (id `1522203698665885801`) + "Railway Alerts" webhook created
  in MineSnakeBotTest via Galaxy Bot (full perms verified); the existing rule **updated in place**
  (`notificationRuleUpdate` — no delete mutations, per the Q-0213 boundary) to the new URL;
  read-back config hash-matches the new webhook (sha8 `f5f285ec`); a restoration notice posted
  through the webhook (message id `1522203924386283563`) proves the Discord half. The Railway half
  proves itself on this PR's own merge → worker redeploy → `Deployment.*` events into the channel.
- No-transcript discipline held: the webhook token existed only in-process; outputs carried ids +
  hash receipts (the `no-transcript-secret-plumbing` idea's pattern, exercised by hand).
- `webhookTest` mutation rejected a synthetic payload ("Problem processing request") — noted; not
  needed given direct verification + the natural end-to-end on merge.

**2. The idea capture:**
[`central-admin-and-logging-guilds-2026-07-02.md`](../docs/ideas/central-admin-and-logging-guilds-2026-07-02.md)
— admin guild (cross-guild settings management: Q-0212's authority minus the "must be in the
guild" clause, via a guild-selector panel; clean in the rebuild's `PanelContext.target_guild`,
heavier retrofit in the current bot — wants a `ctx.guild`-seam audit plan first) + central logging
guild with the **privacy split made explicit** (platform/ops lane buildable freely; member-content
mirror owner-gated on a policy, same "content leaves the guild" boundary as image moderation).
Deploy-alerts idea updated (executed; remaining scope = failure-only filtering + HQ move);
Railway plan §4 alerts row updated to the verified mechanism.

## Context delta

- **Deleting a Discord channel kills its webhooks but not the upstream rule** — the Railway side
  keeps posting into a 404 forever, silently. The config-drift-checker idea gains a check: every
  notification rule's destination URL answers non-404.
- **Restoring beat re-creating:** reading the existing rule first (rather than minting a second
  one) meant the exact event set and the muxer-format config shape came for free — and avoided a
  duplicate-rule mess.
- The Railway notification API is `notificationRule*` (the old `webhookCreate` is gone;
  `channelConfigs` is an undocumented scalar whose shape came from reading the owner's live rule).

## 🛠 Friction → guard

The silent-404 webhook class (above): routed into the existing
`railway-config-drift-checker` idea as a concrete check line rather than a new mechanism —
the checker is the single home for "live Railway state nothing watches."

## 💡 Session idea (Q-0089)

Captured as the session's main artifact — the **central admin + logging guilds** file (owner idea,
structured, privacy split flagged). My own genuine addition inside it: the **cross-guild
`PanelContext.target_guild`** mechanism, which makes the admin guild nearly free in the rebuild's
grammar while being an honest retrofit cost in the current bot — that asymmetry is itself an
argument for the rebuild.

## ⟲ Previous-session review (Q-0102)

Previous session (#1641, the ideas harvest): five solid captures, properly deduped — and one of
them (`no-transcript-secret-plumbing`) was *used in anger within the hour* by this session's
webhook work, which is the best possible validation of a capture. What it missed: the harvest
framed the deploy-alerts idea as needing a *new* webhook, when reading live state first would have
revealed the surviving rule + dead webhook (this session found it in one query). **Concrete
improvement:** idea captures that touch live infrastructure should include a 2-minute read of the
live state before writing the idea — "what exists already?" belongs in the capture template, not
just in execution sessions.

## 📤 Run report

- **Did:** captured the owner's HQ-guilds architecture (privacy split flagged) + restored the
  deleted Railway alerts channel end-to-end, verified · **Outcome:** shipped
- **Shipped:** #1644 — idea capture + deploy-alerts/plan updates. Live (not in diff):
  `#railway-alerts` + webhook in MineSnakeBotTest, rule `8d8fc9b4…` re-pointed, notice posted.
- **Run type:** `manual` (owner-directed)
- **⚑ Owner decisions needed:** (1) **HQ guild bootstrap** — create the guild(s) (recommended) and
  invite the bots, or say the word and Galaxy Bot creates one; (2) the §2 **member-content mirror
  policy** (aggregate/redacted vs owner-guilds-only vs full) before any log mirroring ships;
  (3) optional: failure-only filtering on the alerts rule if full deploy chatter is noisy.
- **⚑ Owner manual steps:** none for the restore (done); the artifact-retention dropdown from
  #1640 still stands.
- **⚑ Self-initiated:** none (owner-directed capture + restoration of owner-lost state)
- **↪ Next:** watch `#railway-alerts` light up on this PR's merge-deploy; HQ-guild decisions above;
  the design-spec owner gate remains the big one.
