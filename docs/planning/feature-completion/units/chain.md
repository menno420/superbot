# Word Chain — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `chain` · **Type:** game (per registry) · **Family:** activity
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/chain_cog.py` · `disbot/services/chain_service.py` ·
> `disbot/utils/db/` (chain channel CRUD)

> ⚠️ **Assessment headline — this unit is mis-classified.** The registry advertises `chain` as a
> "Word-chaining **game**" (`category: games`, `parent_hub: games`, caps `chain.game.play` /
> `chain.game.configure`), but the shipped implementation is a **channel content-restriction
> moderation tool**, not a game. This is the single biggest finding and gates everything else — it
> needs an owner decision before the rubric can be meaningfully completed (punch-list #1).

## What the code actually does

`chain` lets an **admin** restrict a channel so that **only one specific allowed word** may be posted
there (`!chain create [channel] <word>`), and/or enforce a **per-message word limit**
(`!chain setlimit`). Any non-conforming message is **auto-deleted** through `moderation_service`
(`chain_cog.py:331-360`), with a transient warning. The user-facing commands are all admin-only
(`create`/`delete`/`setlimit`/`removelimit` + `chainmenu`), plus a public `list`. The only thing a
*player* does is post the allowed word (or get their message deleted).

There is **no game loop**: no turn-taking, no "next word starts with the previous word's last
letter", no scoring/streak visible to players, no win/lose, no PvP. `record_chain_progress`
(`chain_cog.py:337`) increments a counter, but it is **never surfaced** to anyone. So as a *game*,
this unit is ~0% complete; as a *moderation/channel-restriction tool*, it is small but functional.

## Rubric (game) — assessed against the *advertised* type

> Most game-rubric items are **N/A or fail** because the feature is not a game. Listed honestly rather
> than force-ticked.

### A. Game-loop completeness
- [ ] **Modes exist** — ❌ there are no game modes; there is a word-allow rule and a word-limit rule.
- [ ] **Standard actions exist** — ❌ no turn/word-chain actions; only admin config + auto-delete.
- [ ] **Loop runs start→finish** — ❌ no game loop; the "loop" is moderation enforcement.
- [x] **No dead-end controls** — the admin `_ChainMenuView` buttons all work (create/delete/set/clear/
      refresh, `chain_cog.py:621-654`).
- [ ] **Rewards/XP wired** — ❌ none; `record_chain_progress` writes a counter nobody reads.

### B. UI & buttons
- [~] **A panel exists** — an **admin** management panel (`_ChainMenuView`), not a player game panel.
- [x] **Admin actions have controls** — create/delete/set-limit/clear-limit/refresh are all present.
- [x] **Authority re-checked** — `interaction_check` re-checks admin on every button because the panel
      is also reachable from the (non-admin) Help hook (`chain_cog.py:587-599`) — a correct guard.
- [ ] **Return navigation** — the admin panel has Refresh but no Help/Games back-nav (minor; it is an
      admin tool, not a game in a hub).
- [x] **Consistent copy/embeds** — clean embeds + clear error copy.

### C. Convenience — N/A (not a player-facing game).
### D. Edge cases & lifecycle
- [x] **Permissions** — every mutating command is `@has_permissions(administrator=True)` with explicit
      error handlers (`chain_cog.py:120-131`, etc.).
- [x] **Audited removal** — deletions route through `moderation_service.auto_delete` (lands in mod_logs
      + emits the mod-action event) rather than a raw `message.delete()` (`chain_cog.py:356-360`).
- [x] **Command pass-through** — command messages are not auto-deleted (`chain_cog.py:319-321`).
- [x] **Restart** — config is DB-persisted (survives restart, as a moderation rule should).

### E. Money-safety — N/A (no economy surface).
### F. Wiring & discoverability
- [⚠] **Registry** — present, but **mis-typed**: `category: games` / `parent_hub: games` /
      `chain.game.*` caps for a moderation tool (`subsystem_registry.py:901`). → punch-list #1.
- [x] **Write boundary guarded** — `tests/unit/invariants/test_chain_write_boundary.py` pins the
      audited mutation seam.
### G. Tests & evidence
- [x] **Logic/stage tests** — `test_chain_service.py`, `test_chain_stage.py`,
      `test_chain_cog_prefix.py`, `test_chain_write_boundary.py` cover the moderation behaviour well.
- [ ] **Live walkthrough** — pending (but see #1 — walk the *real* feature, not the advertised one).
- [ ] **Owner ✔** — pending.

## Punch-list (clear these to certify)

1. **OWNER DECISION — what is this unit?** Two coherent resolutions, both reasonable:
   - **(a) It is a moderation/channel-restriction tool** — then **re-classify** it: rename the
     registry entry (e.g. "Channel Word Lock" / move under moderation), fix `description`,
     `category`, `parent_hub`, and the `chain.game.*` capabilities, and **assess it against the
     server-function rubric** instead (a fresh `chain.md` keyed to that rubric). The feature is then
     close to complete and the punch-list shrinks to the items below.
   - **(b) A real word-chain game was intended** — then it is essentially **unbuilt** as a game; this
     becomes a build plan (turn-taking, last-letter chaining or sequence rules, scoring, a player
     panel, XP), which is a brand-new unit behind the completion gate.
   This finding is **why** the unit can't simply be ticked: the rubric type itself is in question.
2. **Surface or remove `record_chain_progress`** — it writes a counter no command/panel ever reads
   (dead write). Either show it (a streak the channel is "chaining") or drop it.
3. *(resolution-dependent)* if (a): add Help/Games-style nav to the admin panel only if it lands in a
   hub; if (b): the full game build.
4. **Live walkthrough** — of whichever real feature #1 settles on.
5. **Owner sign-off.**

## Evidence

- **Tests:** `tests/unit/cogs/test_chain_cog_prefix.py` · `tests/unit/cogs/test_chain_stage.py` ·
  `tests/unit/services/test_chain_service.py` · `tests/unit/invariants/test_chain_write_boundary.py`
- **Walkthrough:** pending (punch-list #4)
- **Owner sign-off:** pending (punch-list #5)

## Verdict

As shipped, `chain` is a **small, functional, well-guarded channel word-restriction moderation tool**
that is **mis-advertised as a game**. It cannot be certified against the game rubric because it isn't
one. The certifying step is an **owner decision (#1)**: re-classify it as a server-function (and
re-assess against that rubric — at which point it is near-complete), or treat the "Word Chain game" as
an unbuilt unit and plan it. Until then this stays `◐ assessed` with the classification finding as the
blocking item.
