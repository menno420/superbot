# 2026-07-11 — fleet inbox for the hub + 📊 Model attribution line

> **Status:** `complete`
> **Run type:** fleet-manager lane dispatch (ORDER 010 relay gap closure)
> **Model/time:** fable-5 · 2026-07-11 ~04:30Z → ~04:4xZ
> Branch: `claude/fleet-inbox-hub` · PR #1977.

📊 Model: fable-5

## What happened

- **`control/inbox.md` created** — superbot was the ONLY fleet repo with no inbox, so the
  fleet-manager ORDER 010 relay could not land here (fm PR #63 slice record: "NOT relayed
  + why: superbot — no `control/inbox.md` exists at main HEAD"; fm PR #64: "The only
  unrelayed repo remains superbot"). Header mirrors the kit inbox grammar
  (`## ORDER <nnn> · <ISO8601> · status: <state>` + priority/do/why/done-when, one writer,
  append-only), adapted to the hub role: **Q-0264 — no standing seat; ORDERs here are
  consumed by the next hub-touching session.**
- **ORDER 001 appended** = the one outstanding named relay ("superbot rides next contact",
  fm PR #63/#64 slice records): the ORDER 010 model-attribution ground truth, grammar
  mirrored verbatim from the sibling append (superbot-games ORDER 003, relayed via fm
  PR #63), adapted only in executor naming. Status written `done` rather than `new` —
  the relaying PR itself executes both done-when halves (template line + this card), so a
  born-`new` order would be stale on arrival; decided-and-flagged (Q-0240).
- **`📊 Model:` line added to the card convention** (`.sessions/README.md`) — family-level
  names only (fleet Q-0262); per-session self-report in the committed card is the fleet's
  only reliable attribution surface (fm `docs/findings/model-matrix-2026-07.md`). The
  convention lives in `.sessions/README.md` (not only CLAUDE.md), so no CLAUDE.md edit and
  no router proposal was needed (Q-0106 untouched).
- Ledger entry #1977 in `docs/current-state.md`.

## Decisions made alone

- ORDER 001 `status: done (executed by the relaying session itself …)` instead of `new`
  (rationale above; fm's own inbox uses the same DONE-with-parenthetical style).
- Inbox header wording for the hub role (no standing seat → "next hub-touching session"
  as consumer; progress reported in session cards, ORDER bytes append-only).

## Flagged for maintainer / known limits

- The inbox now exists but **nothing routes hub sessions to read it** — see the session
  idea below. Until that lands, an ORDER appended here is only seen by a session that
  greps for it.

## Context delta

- **Needed but not pointed to:** the fleet inbox grammar + hub-role adaptation had to be
  assembled from fleet-manager `control/status.md` slice records and a sibling repo's
  inbox — nothing in superbot's orientation mentions `control/` at all (expected: the
  surface didn't exist until this PR).
- **Pointed to but didn't need:** none notable — the task brief carried its own route.
- **Discovered by hand:** superbot session cards already used `📊 Model:` ad hoc
  (e.g. `.sessions/2026-07-10-gen2-night-prep.md`) without the convention naming it —
  the README edit turns practice into rule.

## 🛠 Friction → guard

None hit — auto-merge armed first try (the known fleet wall of arming-at-creation did not
recur here), checks green first run. Nothing to guard.

## 💡 Session idea

**Wire `control/inbox.md` into hub orientation + a stale-ORDER check.** An inbox nobody
reads is a dead letterbox: add a one-line pointer in the read-first route (orientation /
`docs/AGENT_ORIENTATION.md`) telling hub-touching sessions to check `control/inbox.md`
for `status: new` ORDERs at session start, and (cheaper, enforcing — Q-0194) a small
checker line that flags a `status: new` ORDER older than N days so an unconsumed relay
becomes visible drift instead of silence. Dedup-grepped `docs/ideas/` — no existing
inbox-routing idea. Kept inline (small; a grooming pass or the next hub session can ship
the pointer in minutes).

## ⟲ Previous-session review

The 4j check-in (`2026-07-11-round3-dispatch-4j-checkin-venture.md`) did the right thing
verifying ground truth before recording (it caught the actively-misleading "⚑B/⚑D FROZEN"
line and unfroze it). The system improvement it surfaces, generalized by this session:
staleness isn't only in *existing* surfaces (its owner-click-tail point) — sometimes the
drift is a **missing landing surface** (superbot had no inbox at all, so a fleet-wide
relay silently skipped the hub twice). A kit-adoption gap sweep ("does every fleet repo
have the control-plane files the manager's relays assume?") would have caught this before
two relay passes documented it as a wall.

## Documentation audit (Q-0104)

`check_quality --check-only` ✓ · `check_docs --strict` ✓ (pre-existing SUPERSEDED-badge
warnings in two round-3 founding-package plans, untouched by this PR) ·
`check_current_state_ledger --strict` ✓ (23 post-marker merges = benign lag; #1977 entry
added). Chat-only material: none — everything landed in the inbox, README, ledger, and
this card. Claim file deleted this commit.

## 📤 Run report

- **Did:** created superbot's fleet-relay landing surface (`control/inbox.md`, hub-role kit grammar) + executed the outstanding ORDER 010 model-attribution relay (ORDER 001) + added the fleet-standard `📊 Model:` line to the card convention · **Outcome:** shipped
- **Shipped:** #1977 — hub inbox + ORDER 001 + `.sessions/README.md` Model line + ledger entry
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (dispatched fleet-lane work; the inbox-orientation idea stays an idea)
- **↪ Next:** wire `control/inbox.md` into hub orientation (session idea above) so appended ORDERs are actually consumed

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1977, auto-merge on green) |
| CI-red rounds | 0 (born-red card hold only) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 |
| Ideas groomed | 0 (dispatch slice; no capacity claim beyond scope) |
