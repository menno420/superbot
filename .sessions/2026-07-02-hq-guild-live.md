# 2026-07-02 — HQ guild live: Railway feed moved + invite-flow fix + cutover-token confirmation

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Docs-only in the repo; live operations under Q-0213 all additive + read-back-verified, no
> deletes, no secrets in transcripts. `check_docs --strict` ✓. PR #1645.

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7` (restarted from `main` @ #1644 merged).

## What shipped (docs) + what ran (live)

**Live, this turn-cluster:**

1. **Invite-flow diagnosis from the owner's screen recording** (frames extracted via
   `imageio-ffmpeg` — no ffmpeg in the container): the in-client "Add App" flow used Discord's
   2024 per-app **default install settings**, and Galaxy Bot's were commands-only → app authorized,
   **no bot member joined**. Fix: `PATCH /applications/@me` set Galaxy's guild-install defaults to
   `bot + applications.commands` / admin — read-back verified; SuperBot's were already correct
   (why it "still worked"), so the difference was configuration, not app age.
2. **The HQ guild is live:** owner created **"Superbot Admin"** (`1522099141671653417`), both bots
   joined; owner keeps **Galaxy Bot as HQ operator** and removes production SuperBot for now.
3. **Railway alerts feed moved to HQ:** `#railway-alerts` (`1522212273240801510`) + webhook minted
   via Galaxy Bot; notification rule `8d8fc9b4…` updated **in place** (same event set; destination
   hash-verified sha8 `e4c08da7`); move notice posted. Old test-guild channel retired — owner may
   delete it (I don't delete).

**Owner decision recorded (in-chat, folded into the HQ idea file):** **the rebuilt bot inherits
SuperBot's token at cutover** — the owner independently articulated the design spec §5 flip model
("when the rebuilt bot matches and exceeds the current state of superbot we will use superbot's
token"). This is owner *alignment with* the pending spec, not a new gate decision — noted, not
re-routered.

**Docs:** HQ idea §4 update (live state + the SuperBot-out-for-now and token-continuity notes +
"design HQ surfaces for the rebuild's grammar first") · Railway plan §4 alerts row → HQ
destination.

## Context delta

- **Discord's 2024 install-flow split is a standing trap:** in-client "Add App" obeys
  `integration_types_config` defaults; classic links obey their own query params. An app never
  invited via the new flow can look "broken" overnight. Both bots now have correct defaults —
  fixed at the *app* level, so it can't recur per-server.
- **Video uploads are usable evidence:** no ffmpeg in the container, but `pip install
  imageio-ffmpeg` ships a bundled binary — frames → Read-as-image made the diagnosis trivial.
  (Journal-grade note; also useful for future owner screen-recordings.)
- The production bot token can be used **REST-only** from agent sessions (read in-process from
  Railway vars) without touching the live gateway session — used twice today for read-only guild
  inventory + the app-config read; the rebuilt-bot cutover will use the same property.

## 🛠 Friction → guard

The invite trap is now structurally fixed for both apps (defaults corrected at the source). The
video-frames technique + REST-only-prod-token rule recorded here as journal-grade practice; no new
checker warranted (one-time app config, verified by read-back).

## 💡 Session idea (Q-0089)

Folded into the HQ idea file rather than a new capture (dedup discipline): **"HQ = the rebuild's
operator console"** — design the §1 admin-guild surfaces in the rebuild's manifest grammar first
(a `PanelContext.target_guild` + platform-owner capability declaration) and skip the current-bot
retrofit entirely, since the owner has now confirmed token-continuity cutover; the HQ guild then
becomes the rebuild's first *live* consumer surface. One line of why: it converts an idea that
looked like a costly retrofit into a pure Phase-4 subsystem with zero throwaway work.

## ⟲ Previous-session review (Q-0102)

Previous session (#1644, HQ capture + webhook restore): reading live state before writing
(discovering the surviving rule) was the session's best move and got validated again today — the
move took one minute because the restore had already scripted it. What it missed: it recommended
SuperBot for the HQ guild without flagging the state-pollution angle the owner spotted himself
(production bot in a management guild writes production settings rows for that guild). **Concrete
improvement:** recommendations that put the *production* bot anywhere new should note the
state/side-effect footprint by default — the owner's instinct was ahead of mine here.

## 📤 Run report

- **Did:** diagnosed the invite failure from the owner's recording, fixed Galaxy Bot's install
  defaults, moved the Railway alerts feed into the new HQ guild, recorded the owner's
  token-continuity confirmation · **Outcome:** shipped
- **Shipped:** #1645 (docs). Live: app-defaults PATCH, `#railway-alerts` in Superbot Admin, rule
  re-point (all verified).
- **Run type:** `manual` (owner-directed)
- **⚑ Owner decisions needed:** the §2 member-content logging policy (before any log mirroring
  into HQ); the design-spec owner gate (standing).
- **⚑ Owner manual steps:** kick SuperBot from Superbot Admin (your stated intent — member
  removal is yours); optionally delete the retired `#railway-alerts` in MineSnakeBotTest;
  the artifact-retention dropdown (#1640) still stands.
- **⚑ Self-initiated:** none (owner-directed)
- **↪ Next:** HQ ops-lane channels (health findings, error feed) are buildable freely whenever
  wanted; the design-spec owner gate remains the big one.
