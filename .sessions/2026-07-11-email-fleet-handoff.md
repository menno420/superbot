# 2026-07-11 — Anthropic email #2 + fleet-management session (HANDOFF BRIEF)

> **Status:** `complete`

📊 Model: Claude Opus 4.8 · owner-directed hub session (fleet management + EAP email) · day

## ▶ NEXT SESSION — START HERE

**The one live thread: the second Anthropic email.** Draft is COMPLETE on Claude's side
(`docs/eap/anthropic-email-2-draft-2026-07-11.md`, PR #1986). It is **owner-action-blocked**,
not Claude-blocked. The owner must, before the EAP closes **Tue 2026-07-14**:
1. Rewrite **Part 1** in his own voice (it's a MOCK — every line tagged `‹src›` to a real
   thing he said; delete the tags).
2. **Attach the 4 phone shots** (figs 15a/15b/15c/17 — the model-mismatch trio + the git-403
   shot; they're on his phone, not in the repo).
3. Send — reply on Gmail thread `19f41cd2e5380bb3` (to `claude-code-early-access@anthropic.com`,
   reply-all keeps Diana/Omid/Matt).
4. Optional: Matt Gallivan's 10–15 min UX interview (listenlabs link in his 2026-07-10 mail) —
   Part 1 already answers his "how does it fit your work" question.

**If the owner asks Claude to help further on the email:** offer to (a) tighten Part 2 to any
length, (b) draft the reply *into Gmail as a real draft* he presses send on (never auto-send),
or (c) take a full pass at Part 1 so he reacts to a fuller draft than the mock. The 16 curated
figures are committed at `docs/eap/screenshots-2026-07-11/` (see `index.md` for captions +
the send-set + the "if you only send ~8" pick).

## What this session shipped (all merged unless noted)

- **Games program:** founding packages for **Retro-Games** (gba-homebrew + pokemon-mod-lab)
  + **Mining Browsergame** (new repo) → superbot **PR #1972 (merged)**; **seeded
  `superbot-mineverse` born-right** (kit v1.8.0 `adopt --wire-enforcement`, live
  substrate-gate + enabler, pushed to main).
- **Fleet instruction + env audit** → fleet-manager **PR #60 (merged)** carrying **ORDER 016**:
  the owner-landed `UNIVERSAL.md` merge clause tells every seat to do the classifier-**walled**
  thing (arm/REST-merge yourself) → 12/13 lanes walled; the fix (open READY, let the
  enabler workflow land it) is routed to the owner-queue + the manager. Also: env archetypes
  ≈ one base + 3 knobs; 5 lanes unregistered. Doc: `fleet-manager/docs/findings/instruction-and-env-audit-2026-07-11.md`.
- **Fleet night-review** → superbot **PR #1985 (merged)**: `docs/eap/night-review-2026-07-11.md`
  + the owner **`fleet-vocab.md`** shorthand file + the **`/fleet-review` skill** + the
  routine/model findings.
- **Second Anthropic email** → superbot **PR #1986 (OPEN, WIP)**: the draft + 16 figures + index.

## Key durable findings (don't lose these)

1. **Merge-classifier is context-sensitive.** The wall tracks the *session's context*, not the
   PR — a session saturated with merge/permission-doctrine text (e.g. the audit we ran) gets
   read as instruction-manipulation-adjacent and denied, while a content-neutral session merges
   the identical PR the same minute. Only a **live in-session human authorization** clears it
   (a relayed coordinator grant does not).
2. **A routine's configured model ≠ the model that runs.** pokemon/gba routines configured
   **Opus 4.8**; the session woke ran **Sonnet 5** (agent's own words). Config and running
   reality silently diverge; no surface reconciles them.
3. **Routines spawn without their repo attached** (gba ~1/3 fail); owner can edit a routine to
   attach repos + set model. Fix both owner-side (attach) and doctrine-side (routine self-heal).
4. **Owner-click backlog blocks all shippable value:** venture-lab Stripe keys + publish,
   product-forge GitHub Pages, websites `DATABASE_URL` + `GITHUB_TOKEN`.

## Open owner-action queue (surface these when relevant)

- Send email #2 + Matt's interview (before 7/14) — the top item.
- Attach each project's repo to its routine + set the model (kills the repo-spawn + model bugs).
- Clear the owner-click backlog above.
- ORDER 016's UNIVERSAL merge-clause fix awaits the owner landing it (owner-provenance).

## Session mechanics for the next session

- **Repos added to scope THIS session** (a fresh session starts scoped to `superbot` only —
  re-`add_repo` as needed): superbot-mineverse, substrate-kit, venture-lab, fleet-manager,
  superbot-next, superbot-games, superbot-idle, trading-strategy, sim-lab, product-forge,
  idea-engine, websites, gba-homebrew, pokemon-mod-lab.
- **Shorthand is live:** say **"review"** → the `/fleet-review` skill runs the night-review
  workflow; `docs/owner/fleet-vocab.md` is the owner's growing command dictionary.
- **This hub session CAN merge/sync normally** — the merge/permission classifier wall is
  **Project-session-only**. Avoid `delete_trigger` / destructive approval-gated ops only when
  the owner is away and can't approve a prompt (his standing constraint this session).
- Screenshot review worktrees (`scratchpad/ss-patch-*`) were removed at close.

## ⟲ Previous-session review

The prior night-review session (#1985) did the fleet survey well but buried two lanes'
self-reviews inside overwritten `status.md` files (superbot-next, product-forge) — a durability
risk flagged in the review; the manager order to move them to `docs/retro/` is still worth
issuing. Improvement this session applied: routing the email's figure provenance into a
committed `index.md` rather than chat, so nothing lives only in the conversation.

## 💡 Session idea

**A `capabilities-facts` file the manager keeps and seats read at boot** (Codex-enabled repos,
required-check names, retired walls, model/quota caveats) — tonight's model-mismatch + the
merge-context finding both come from seats acting on stale capability truth they can't probe.
The read half of capability self-awareness, maintained centrally. (Dedup: distinct from a
per-seat `capabilities --probe`.)

## Documentation audit (Q-0104)

`check_docs --strict` ✓. Email draft + figures + index committed to PR #1986; night-review +
vocab + skill on main (#1985); ORDER 016 on fleet-manager main (#60). Bulk screenshot PRs
#1987/#1988/#1989 CLOSED (keepers curated into the folder). No chat-only material left un-homed.
