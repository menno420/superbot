# 2026-06-23 — Remove the legacy cleanup channel whitelist

> **Status:** `in-progress` — owner-directed follow-up to #1345. The owner confirmed the hardcoded
> whitelist is a remnant of an old bot version / old servers and that whitelisting "isn't really a
> thing" anymore. Open PR born-red per Q-0133; flip to `complete` as the final step.

> **Run type:** `manual · owner-directed`

## What I'm about to do

#1345 fixed the *display* of `config.CLEANUP_WHITELIST_CHANNELS` (resolve names, filter to the current
guild). The owner then asked to remove the hardcoded list entirely — it's a leftover from an old bot
version, the 4 IDs are dead old-server channels, and per-channel **cleanup policies** (`Off`) already
fully replace the "exempt this channel from command-deletion" function.

Complete removal of the whitelist concept:

1. **`disbot/config.py`** — delete `CLEANUP_WHITELIST_CHANNELS` (+ the 4 hardcoded IDs + the
   `BOT_CLEANUP_WHITELIST` env hook) and `_parse_channel_ids` (its only consumer).
2. **`disbot/governance/cleanup.py`** — delete the resolver's whitelist fallback branch (+ the now-unused
   `import config`); a channel with no policy row just resolves to the compat default (delete after 5s).
3. **`disbot/cogs/cleanup_cog.py`** — drop `self.whitelisted_channels`; the DM/unknown-guild auto-mod
   fallback (which deleted command-style messages in "non-whitelisted" channels) stops auto-deleting.
   Deletion is now purely governance-policy-driven. (Realistic trigger was DMs, where the bot can't
   delete user messages anyway, so near-zero real behavior change.)
4. **`disbot/cogs/cleanup/panel.py`** — remove the "Whitelisted Channels" field + the resolve/filter code
   added in #1345; update the Hub copy.
5. Tests + the one living doc (`settings-customization-command-map.md`) updated; the historical audit
   snapshots are left as dated records.

**Replacement for operators:** to exempt a channel from command cleanup, set that channel's cleanup
policy to `Off` in the Cleanup Policies panel.

## What shipped

_(filled in at close)_
