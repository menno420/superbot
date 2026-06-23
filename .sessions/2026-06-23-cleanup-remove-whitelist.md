# 2026-06-23 — Remove the legacy cleanup channel whitelist

> **Status:** `complete` — owner-directed follow-up to #1345. The owner confirmed the hardcoded
> whitelist is a remnant of an old bot version / old servers and that whitelisting "isn't really a
> thing" anymore. PR #1350, auto-merge armed on green (Q-0127); owner-directed → merge immediately
> (Q-0191).

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

The whitelist concept removed end-to-end:

- **`disbot/config.py`** — deleted `CLEANUP_WHITELIST_CHANNELS` (+ the 4 hardcoded old-server IDs + the
  `BOT_CLEANUP_WHITELIST` env hook) and the now-orphaned `_parse_channel_ids` helper (its only consumer).
  Left a comment pointing future readers at per-channel `Off` policies.
- **`disbot/governance/cleanup.py`** — removed the resolver's whitelist fallback branch + the unused
  `import config`. A channel with no override row now resolves straight to the compat default
  (delete=True / 5s / FALLBACK_DEFAULT).
- **`disbot/cogs/cleanup_cog.py`** — dropped `self.whitelisted_channels` + the unused `import config`;
  the DM/unknown-guild auto-mod fallback now `return False` (no auto-delete) instead of deleting
  command-style messages in "non-whitelisted" channels.
- **`disbot/cogs/cleanup/panel.py`** — removed the "Whitelisted Channels" Hub field + the #1345
  resolve/filter code; the overview copy now points at the Cleanup Policies panel and the `Off` exemption.
- **Tests** — `test_config_env_cleanup` flipped from *asserts-preserved* to *asserts-removed* + the
  hardcoded-ID scan now confines the two IDs to migration 051; `test_cleanup_resolution_behavior` dropped
  the whitelist monkeypatch; `test_cleanup_stage` rewrote the whitelist-fallback case to assert no-delete;
  `test_cleanup_panel` dropped the whitelist-display cases (replaced with a "no whitelist field" pin).
- **Docs** — `settings-customization-command-map.md` de-referenced the constant (3 spots); regenerated
  `docs/operations/env-vars.md` (38 vars, `BOT_CLEANUP_WHITELIST` gone). Historical audit/archive
  snapshots left as dated records.

Full suite 11992 green; mypy clean; arch 0 errors.

## Findings / decisions

- **Owner decision (in-session): the cleanup channel whitelist is retired.** Channel exemption from
  command cleanup is now done the modern way — set that channel's cleanup policy to `Off`. The old
  `CLEANUP_WHITELIST_CHANNELS` was a hardcoded list of dead old-server channels from an earlier bot
  version. (Provenance: owner request this session, follow-up to #1345.)
- **Behavior change, judged negligible: the cog's DM/unknown-guild fallback no longer auto-deletes.** It
  was only reached when `command_pattern` matched but governance couldn't be consulted (no guild, or an
  unparseable command name). The realistic trigger is DMs — where a bot *cannot* delete a user's message
  anyway, so the old `auto_delete` was an effective no-op that still returned `True`. Making deletion
  purely policy-driven is the correct end-state and matches the owner's intent.
- **`_parse_channel_ids` removed, not kept.** It had exactly one consumer (the whitelist); leaving a dead
  helper + a dead `BOT_CLEANUP_WHITELIST` env var would have been an incoherent half-removal.

## 💡 Session idea

**A `dead-config-symbol` lint that flags `config.py` constants with zero production readers.** This
removal hinged on me grep-confirming `_parse_channel_ids` and `CLEANUP_WHITELIST_CHANNELS` had no other
consumers before deleting them — by hand. A tiny stdlib check (reuse the repo's AST tooling + the
`scan_env_usage` scanner pattern) that lists `config.*` module-level names never referenced outside
`config.py`/tests would make "is this config still load-bearing?" answerable at a glance, and would have
*directly* surfaced this whitelist as dead config a session earlier. (Dedup-checked `docs/ideas/` — the
existing env-scanner idea covers env *vars*, not unreferenced config *constants*; this is the constant
sibling.)

## ⟲ Previous-session review (Q-0102)

The previous session was *this same session's* #1345 — strong work, but it carried a self-aware gap: its
own findings noted "Whitelist is global static config… I did not migrate it" and filed a *migrate-to-DB*
follow-up idea. The owner's actual answer ("just remove it") is the better call the idea didn't reach for
— a reminder that when something is **legacy cruft**, "delete it" should be weighed before "migrate it to
a nicer version of itself." **System improvement (initiated):** the #1345 session fixed the whitelist
*display* without questioning whether the whitelist *should exist* — a checklist prompt like "is this
surface still wanted, or is it legacy I should propose removing?" belongs in the UX-fix reflex, so an
agent polishing an old surface at least *asks* the delete-vs-improve question. Captured as the dead-config
lint idea above (the mechanical half) + this note (the judgment half).

## 📤 Run report

- **Did:** Removed the legacy hardcoded cleanup channel whitelist end-to-end (config + resolver + cog +
  panel + tests + docs); exemption is now a per-channel `Off` policy · **Outcome:** shipped (PR #1350,
  auto-merge armed on green)
- **Shipped:** #1350 — remove the legacy cleanup channel whitelist
- **Run type:** `manual · owner-directed`
- **⚑ Owner decisions needed:** none (the retire-the-whitelist decision was the owner's own in-session
  directive)
- **⚑ Owner manual steps:** none — merged = deployed (Railway auto-redeploys `worker` on merge; no
  migration, no data step). If any server actually relied on a whitelisted channel, re-create that
  exemption by setting the channel's cleanup policy to `Off`.
- **⚑ Self-initiated:** no — owner-directed (the "can you completely remove the hardcoded list?" request).
- **↪ Next:** nothing pending in this lane; the whitelist is fully gone.

## ⟳ Doc audit (Q-0104)

`check_docs --strict` green; `check_consistency` 0 errors; arch 0. Regenerated `env-vars.md` (the
generated-head sync guard caught the stale `BOT_CLEANUP_WHITELIST` entry — fixed). The living
`settings-customization-command-map.md` de-referenced the removed constant; historical
audit/archive snapshots intentionally left as dated records. The PR isn't in `current-state`
Recently-shipped yet (benign newest-merge lag — the next reconciliation pass records it; #1350 is itself
the next reconciliation boundary, run automatically by the routine, not this manual session — Q-0124).
