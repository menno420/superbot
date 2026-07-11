# 2026-07-11 — Email #2: idle-Project empty-session-list finding (owner recording) → fig-19 + b6

> **Status:** `complete`

📊 Model: Fable 5 · owner-directed hub session (EAP email) · afternoon

## What happened

Reviewed the owner's 18s screen recording frame-by-frame (ffmpeg 1fps extraction via
imageio-ffmpeg — no system ffmpeg in the container). Findings:

1. **The heterogeneous wake methods he observed are by design** — lightning icons =
   standing cron routine fires (each lane's failsafe wake), plain sessions = send_later
   continuation-chain slices + coordinator-dispatched workers. Both mechanisms are
   documented fleet doctrine (failsafe + pacemaker chain); the mix per project reflects
   each lane's cadence class, not divergence.
2. **NEW finding — Idle Game Project renders an EMPTY session list** while its lane's
   repo carries 44+ agent-merged PRs and a same-day heartbeat (owner confirmed the PRs
   himself). Sibling Projects (MineVerse, Sim Lab) show fully populated nested lists in
   the same frame. Third instance of the b6 observability class (UI disagrees with git).
   → committed the proving frame as
   `docs/eap/screenshots-2026-07-11/fig-19-idle-project-empty-session-list.png`,
   added the instance + `[Fig 19]` to email finding b6, figures table + index rows.
3. **Recording also closes two loops:** the SuperBot World chat thanks this hub session
   for the #34/#36/#46/#47 merges and confirms #38/#32/#27 rebased + #48 queued; the
   SuperBot 2.0 digest's "waiting only on you" list matches the owner-queue distillation
   (API-key envelope, plugin-hello, merge-queue tweak) — independent confirmation both
   documents are current.

## ⚑ Self-initiated

Committing the video frame as a figure (the intake offer was this session's own prior
idea — executed here on the owner's evidence-bearing upload).

## 💡 Session idea

**Lane-side "sessions-list truth probe":** each lane's session card already self-reports
its model; add one line — *did this session appear in your Project's sidebar list?* is
unanswerable from inside (two-vantage), but the lane CAN commit its session id + start
time, letting the operator spot-check the UI against a committed session census. Turns
the fig-19 class from anecdote into a measurable rate. (Dedup: capabilities-facts and
the roster cover repo truth, not UI-listing truth.)

## ⟲ Previous-session review (Q-0102)

The sidebar-correction slice (minutes ago) turned owner UI evidence into a committed
correction cleanly, and its "platform-UI claims are operator-verify items" lesson paid
off immediately — this recording is the operator doing exactly that verification, and it
yielded both a confirmation (nesting works) and a new bug (idle's empty list). No
workflow change needed beyond what it already proposed; the loop it designed is working.

## Documentation audit (Q-0104)

`check_docs --strict` run at close · telemetry row appended this PR · claim deleted ·
the recording's other content (games-lane merge thanks, SuperBot 2.0 digest) needed no
doc home beyond this card — both restate state already in durable docs.
