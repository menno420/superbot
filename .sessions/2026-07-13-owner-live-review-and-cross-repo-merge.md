# 2026-07-13 — Owner-live hub session: reviews, doctrine, cross-repo merge sweep

> **Status:** `complete`
> **Branch:** `claude/session-doc-2026-07-13` (documentation close-out; the session's work shipped across many PRs below)
> **📊 Model:** Fable 5 → **Opus 4.8** (owner switched mid-session)
> **Venue:** owner-live chat, remote container (superbot hub; superbot-next + gba-homebrew added mid-session for the merge sweep)

## Arc

A long owner-live session that started as a fleet review and grew, ask by ask, into a
doctrine rewrite, three website/design reviews, a friend-onboarding deliverable, EAP email
prep, and finally an owner-directed **cross-repo merge sweep**. Every superbot deliverable
shipped as its own PR and auto-merged on green; the cross-repo work was done directly in the
sibling repos under explicit owner authorization.

## Shipped — superbot PRs (all merged)

- **#2064** — Fleet night review 2026-07-13 (`docs/eap/night-review-2026-07-13.md`), run through
  the Q-0272 multi-repo orientation path; verified per-lane digest, 3 manager-tally
  mismatches caught, consolidated owner-action queue. Also fixed orientation drift on sight
  (curious-research added to `fleet_status.py` + reading path; api.github.com proxy-wall documented).
- **#2065** — **Universal session-ender v3.4 "wind down and land"** (`docs/owner/universal-session-ender-v3.4.md`)
  — owner-directed rewrite of v3.3: land-first (finish or documented seam, nothing rushed) →
  REVIEW → REFRESH → BAKE, all v3.3 incident mechanics preserved. **This is the ender being
  applied to close this very session.**
- **#2066** — Websites fleet-data-plane design (`docs/planning/websites-fleet-data-plane-2026-07-13.md`)
  — one derived manifest + misplaced-file failsafe (commit-time recency, drift-flagging). Routes to websites lane.
- **#2068** — Friend-onboarding prompt (`docs/owner/friend-onboarding-prompt-webshop-2026-07-13.md`)
  — paste-into-free-claude.ai prompt for a beginner selling online; **owner has sent it.**
- **#2069** — Codex P2 fixes from #2068 (telemetry model-name `opus-4-8`→`opus-4.8`; prompt
  instruction-boundary so a beginner's Claude treats linked files as reference not commands).
- **#2070** — Control-plane live centralization review (`docs/planning/control-plane-centralization-review-2026-07-13.md`)
  — the "six different fleet sizes across pages" root-cause + false-"all quiet" homepage + doubled
  Railway estate + seat/repo naming split + blind deploy state + un-observable prompt re-paste. Routes to websites lane.
- **#2071** — EAP email-3 made **send-ready** (`docs/eap/anthropic-email-3-draft-2026-07-13.md`):
  Part 2 filled with verified night-review figures, 7 probes reframed as optional. **Owner sends
  tomorrow (07-14, EAP window's last day) — needs only his Part-1 voice + the roster screenshot.**

## Shipped — cross-repo merge sweep (owner-directed: "make sure everything complete is merged properly")

**superbot-next** (added to scope; energy foundation landed):
- Merged **#320** (mining energy domain core, `e902b0d`) + **#384** (energy slice 1: persistence
  + migration, `dc0e73d`) — both were clean/green.
- **NOT merged — the write-parity stack #312→#317→#335→#344→#371 (routed to the seat).** I cloned
  and attempted the merge: it is **not** a mechanical rebase. Main's energy work made `!cook`/`!use`
  **live** while keeping craft/skill/build **pending**; the stack made craft/skill/build **live**
  while keeping cook/use pending — the correct merged state (all live) exists on **neither** branch.
  Reconciling touches routing dispatch + the manifest PENDING-roster + parity count-pins and must
  re-pass the golden-parity gate. Force-resolving from the hub could pass CI yet be subtly wrong,
  which would violate the rebuild's byte-parity invariant. Left the branches clean; pushed nothing.
- **#385** (energy slice 2) skipped — `tests`/`gate`/`pip-audit` genuinely failing (unfinished).

**gba-homebrew** (added to scope; games landing after the owner added the `ROM builds` required check):
- Merged **#83** Deepcast (`5c910f3`) + **#84** Drift Garden (`7ffcf1c`) — clean.
- **#82** Brineward + **#86** Cindervault conflicted only on `dist/README.md` (each appended a ROM
  row). Resolved the union in a clone, pushed, and **armed auto-merge** (squash) — they self-land on
  green ROM-build CI. Note: they append to the same row, so whichever lands second may re-conflict —
  the gba seat finishes that one.
- Left for the seat: #85 (packaging, now stale), #87–#90 (control/report docs, conflict pairwise on
  `outbox.md`), #91/#92 (born-red / in progress).

## Investigations (no code change)

- **Routine duplicates** (owner flagged the panel): scanned the first 300 triggers — **exactly one
  enabled failsafe per seat, zero duplicated *active* wakes.** The panel repeats are almost certainly
  older *disabled* leftovers from reboots (cross-session delete is org-walled, so old failsafes
  linger). Harmless clutter, not a live double-fire. Offered to page deeper + delete stale ones; not
  yet done (lower priority than the merges).

## ⚑ Self-initiated (Q-0172)

- Orientation fixes in #2064 (curious-research seat + api.github.com wall) — contained, reversible.
- The `docs/owner/README.md` "paste-ready prompts" index entry (#2068 homing).
- Everything else this session was owner-directed.

## 💡 Session idea (Q-0089)

**A fleet-wide "self-land readiness + shared-file-append" pre-check.** This session's merge sweep
hit the same wall twice in different repos: N complete PRs each append to one registry file
(`parity.yml`/`manifest.snapshot.json` in superbot-next; `dist/README.md` in gba), so they serialize
and every PR after the first re-conflicts — turning "merge everything" into an O(N) rebase dance.
A tiny checker that, per repo, flags **open PRs that all touch the same append-target file** would
surface this "these will pairwise-conflict, land them via one integration or a union merge-driver"
*before* the sweep, and a `.gitattributes` `merge=union` on pure-append ledgers (READMEs, dist
manifests, telemetry) would auto-resolve the trivial ones. **BAKE note — superbot already solved this
for itself:** its `.gitattributes` carries `merge=union` on `telemetry/*.jsonl` /
`docs/owner/active-work.md` / `docs/ideas/README.md` *and* a documented take-theirs+regenerate recipe
for generated JSON (`docs/operations/generated-data-merge-recipe.md`) — the exact proven template. So
the fix is **propagation**, not invention: gba's `dist/README.md` and superbot-next's
`parity.yml`/`manifest.snapshot.json` (or its resolve-recipe, since those are generated) should adopt
the same. Dedup: no existing idea covers append-target conflict prediction (the #2066 data-plane
manifest is about *reads*, not this). Routes fleet-wide (kit candidate) + gba/superbot-next `.gitattributes`.

## ⟲ Previous-session review (Q-0102)

The EAP-email/owner-batch session (#2071) correctly reframed the day around "build a lot to review
later" and made the email genuinely send-ready — good judgment under the owner's time pressure. What
it *couldn't* have known: the owner-queue "just click Allow auto-merge" advice was too optimistic for
superbot-next — those PRs don't merge on a settings toggle because they carry genuine content
conflicts (this session found that out by actually attempting the merge). **System lesson:** "enable
auto-merge to unblock" is only true for PRs that are *mergeable-but-unarmed*; for *conflicted* stacks
it's misleading. The owner-queue's merge-enabler items should distinguish "unarmed (toggle fixes it)"
from "conflicted (needs a rebase)". A cheap check — read each parked PR's `mergeable_state` before
telling the owner a toggle unblocks it — would stop that false-hope class. (This is the enforcing
version of the same "verify against ground truth before asserting" instinct, Q-0120.)

## Docs audit (Q-0104)

- **REFRESH:** `docs/current-state.md` head updated this session — cross-repo sweep result + the
  superbot-next WP-stack-needs-seat carry-forward + email-3 send-ready state (see the ▶ block).
- **Hub heartbeat** `control/status.md` re-stamped (this session's landmarks + the WP-stack pointer).
- New docs reachable: all seven superbot PRs' docs were homed at their own merge (verified — recon
  routine ran band-2070 #2074 cleanly). This log is linked from current-state.
- **Routine disposition:** the two `send_later` self-check-ins I armed (for #2064, #2065) were both
  deleted mid-session (delete confirmations received); I armed no others — nothing dangling.
- Telemetry row appended (Q-0194, opus-4.8).
- Cross-repo merges are durably recorded in the target repos' git history (the authoritative record);
  this log is the superbot-side index of the session.

## Baton — what the NEXT session most needs

1. **EAP email 3 → send today (07-14, window closes).** Send-ready at
   `docs/eap/anthropic-email-3-draft-2026-07-13.md`; needs Part-1 voice + roster screenshot.
2. **superbot-next WP stack** — the live seat must rebase #312→#371 (reason above) + finish #385.
   Biggest stuck value in the fleet.
3. **gba #82/#86** — verify they auto-landed; if the second re-conflicted on `dist/README.md`, the
   gba seat unions it.
4. **Website centralization** — #2066 (data-plane) + #2070 (control-plane review) are routable to the
   websites lane as ORDERs; the cheap wins are the honest homepage headline + the prompt "not
   recorded" relabel.
5. **Owner-action queue** (settings toggles, the ≤07-14 sitting bundle, venture "go with defaults")
   — unchanged, consolidated in `docs/eap/night-review-2026-07-13.md` §7.
