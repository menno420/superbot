# 2026-06-21 — Reaction roles: message picker (no more copy-paste message ID)

> **Status:** `in-progress` — born-red HOLD (Q-0133). Owner-directed follow-up to #1234/#1237
> (Q-0191 → merge on green). Fresh branch (Q-0014).

> **Run type:** `manual`

## What I'm about to do

The emoji reaction-role **Add** flow still asks the operator to paste a raw Message ID — the
clunkiest step (a frequent Carl complaint). Replace it with native message-source options, mirroring
Carl's three setup methods, on `ReactionRolesPanel`:

- **📍 Most recent** — bind to the latest message in this channel (no ID).
- **📜 Pick recent** — choose from a list of recent messages (author + preview).
- **🆕 New message** — the bot posts a message/embed, then binds to it.
- **🔢 By ID** — the existing modal, kept as a fallback.

Each path lands in the existing per-emote role flow (`_BindEmotesView`). Respects Discord's
"modal must be the first response" constraint (recent-pick → select → modal; new-message → one modal
that also takes the emotes). Pure helpers (message label/most-recent resolution) get unit tests.

Verify: `check_quality.py --full` + `check_architecture.py --mode strict`.
