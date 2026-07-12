# 2026-07-12 — overnight fleet review → Anthropic email finalization (full-day owner-live session)

> **Status:** `complete`

📊 Model: **fable-5** for the working bulk of the session (fleet review, email drafting,
Railway, screenshot/recording review, doctrine); **opus-4.8** for the close-out (owner switched
model via `/model` before the session-close request). Owner-directed, owner-live throughout.

## Arc (what this session became)

Started as an overnight `/fleet-review` and grew, at the owner's direction, into a full-day
push whose real deliverable is a **send-ready second Anthropic email** + the live evidence
site + repo prepared so the next session finalizes the email with him. Thirteen PRs merged
(all auto-merged on green; live-session merges done directly per Q-0269).

**1. Fleet night review** (full record: `docs/eap/night-review-2026-07-12.md`). The "cron
problem" was the **platform trigger scheduler degrading** ~02:30–08:00Z, not the batch: 9
`send_later` one-shots silently dropped, 2 crons wedged; every seat with a healthy `*/2`
failsafe self-revived (**Q-0265 doctrine validated in production**). Manually re-fired the
dropped kit-lab daily loop 08:46Z. Discovered cross-session trigger revival is **org-disabled**.
A ~12:00Z addendum (§8) split the "drops" into serialization-behind-busy-sessions (design) vs.
genuine failure (fresh-session loop + wedged crons) — no surface distinguishes them.

**2. The Anthropic email** — brought `docs/eap/anthropic-email-2-draft-2026-07-11.md` to
send-ready: fact-refreshed numbers (superbot-next 37/49+218/218, kit v1.12.1); new **finding 7**
(the scheduler incident, three self-wake mechanisms, allowlist-not-honored reproduced live);
(d)1 rewritten around the owner's **three-option wake proposal** (Routines-as-product /
Project-native schedule / continuous never-sleep); the model-fix confirmation (fair credit for a
probable platform fix); findings 6 & 7 sharpened from the owner's screen recording; the **➕ NEW
mock addition** section for his Part-1 rewrite; typo-only fixes to his prose (zero style change);
status → FINISHED/send-candidate.

**3. Evidence package** — reviewed **27 screenshots** (PRs #2023/#2024, one by one) + a **32s
screen recording** (installed ffmpeg ad-hoc, extracted frames). Recovered the 4 formerly
phone-only email figures (15a/b/c/17); built `screenshots-2026-07-12/` (figs 20–35) with
send-set captions; 5 uploads dispositioned not-kept with reasons. Raw PRs closed in favor of
the curated set.

**4. Live review site** — created the Railway `review` service via API **under explicit owner
authorization** (project `reliable-grace`, root dir `review`, domain minted, deploy verified —
all routes 200): **https://review-production-f027.up.railway.app**, filled into the email's two
URL slots. Also provisioned `postgres-botsite` + botsite `DATABASE_URL` (unblocks the websites
submission queue).

**5. Doctrine (owner-directed in-session, applied with provenance):** **Q-0269** — live/hub
sessions merge finished PRs immediately, never park them on the owner (the owner: *"it's not my
task to do that"*); executed retroactively (websites #158, fm #92). **Q-0270** — the boot triad:
every session establishes model · venue · ability envelope before directing work (general/fleet
scope; relayed to registry + kit). Both in CLAUDE.md + router.

## Context delta

- **Needed but not pointed to:** fleet-manager's `telemetry/triggers-snapshot.json` (783-record,
  GH-Actions-refreshed) is the cheap trigger-forensics source vs. paging `list_triggers` through
  repeated 25k-token MCP overflows. Route fleet/trigger questions there + `docs/roster.md` first.
- **Pointed to but didn't need:** CodeGraph / arch sections (this was docs/infra, no runtime code).
- **Discovered by hand:** the fired-vs-dropped inference rule; the org wall on cross-session
  trigger ops; the Q-0242 allowlist-not-honored reproduction; that the Railway services live in
  `reliable-grace`, not the "superbot-websites" project the websites docs claim; no ffmpeg in the
  container (had to `pip install imageio-ffmpeg`).
- **Decisions made alone (ratify):** created **real Railway infra** (2 services) under the owner's
  "full permission to use my token to its maximum abilities" — reversible (services deletable) but
  it's live cloud state; the `review` service is intended and verified, `postgres-botsite` cleared
  a standing owner-queue item. Applied Q-0269/Q-0270 to CLAUDE.md directly (owner-directed live, so
  owner is the reviewer — provenance Qs recorded).

## 🛠 Friction → guard

- **Scheduler unreliability** → documented detection signature (night-review §4.1), groomed the
  in-band liveness-sweep idea (build-ready, +2 failure classes) and filed the out-of-band
  `scheduler-independent-trigger-watchdog` idea (fleet-manager `gen_roster.py` home). Enforcing
  checker is cross-repo → paste-ready fm ORDER in the owner queue, not a superbot commit.
- **No video-review tooling** (had to build frame extraction live) → filed the
  `screen-recording-evidence-review` idea (Q-0089 below) so the next recording is one command.
- **Stale-branch / unverified-committer Stop-hook false positive** on GitHub's own merge commits
  after a branch sync → noted; the fix is owner-gated (it's `~/.claude/stop-hook-git-check.sh`) —
  proposed skipping commits reachable from origin/main or authored by `noreply@github.com`.

## Flagged for maintainer (weak points)

- The email's finalization needs **you**: your Part-1 rewrite of the ➕ NEW mock addition, then
  Gmail-draft staging. Handoff: `docs/eap/NEXT-SESSION-finalize-email.md`.
- Railway infra created by an agent is live cloud state — worth a glance that `review` +
  `postgres-botsite` look right in your Railway UI.
- The review site shows honest-but-not-yet-today data until the Websites Project bakes a refresh
  (scheduler incident + v3.3 story). Site is live and truthful now; refresh is a nice-to-have.

## 💡 Session idea (Q-0089)

[`screen-recording-evidence-review-2026-07-12`](../docs/ideas/screen-recording-evidence-review-2026-07-12.md)
— a one-command helper to extract scene-change frames from an owner-uploaded screen recording
(the video sibling of the `screenshots-*/` convention). The friction hit live: a 32s Routines
recording had to be frame-extracted with an ad-hoc ffmpeg install, and those frames became email
figs 33–35. (Earlier in the session I also filed `scheduler-independent-trigger-watchdog` and
groomed `trigger-registry-liveness-sweep` to build-ready — idea-lifecycle movement done, Q-0015.)

## ⟲ Previous-session review (Q-0102)

Previous superbot session (44th reconciliation pass, #2014): clean and honest, correctly named
the cross-repo-checker-awareness recurring class. What it — and every session before this one —
lacked: any glance at **trigger health**, despite `list_triggers` being one call away while the
scheduler was already degrading under it. **System improvement this session acted on:** made
trigger-health a first-class concern (two ideas filed/groomed toward the manager's wake ritual +
roster generator), and added the **Q-0270 boot triad** so every future session orients to its own
venue/abilities before acting — the structural fix for the "a session doesn't check its own
context" gap that let the scheduler degrade unnoticed.

## Documentation audit (Q-0104)

`check_docs --strict` green; ledger checker exit-0 (this session's 13 merged PRs are benign
newest-merge lag — the #2040 reconciliation pass records them). New docs reachable: eap README
(+ both screenshot indexes), ideas README (+ 2 new ideas), current-state top-priority pointer +
07-12 entry, the NEXT-SESSION handoff. Owner decisions recorded in the router: **Q-0269**,
**Q-0270** (both with provenance). Claim deleted at open. Nothing captured only in chat that
belongs in a doc — the handoff doc absorbs the forward context.

## 📤 Run report

- **Did:** overnight fleet review → full-day email finalization (draft send-ready, live review
  site, evidence package, 2 doctrine rules, Railway infra) + next-session handoff · **Outcome:** shipped
- **Shipped:** #2017 (night review) · #2018 (Codex fixes) · #2019/#2020 (email findings+facts) ·
  #2021 (Q-0269/Q-0270) · #2025 (screenshot curation) · #2026 (finding-7 ongoing) · #2027 (email
  finished-state) · #2029 (review-site URL) · #2030 (recording review) — all merged; + this close-out PR
- **Run type:** `manual` (owner-directed, owner-live)
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** **(1) finalize the email** — your Part-1 rewrite + Gmail-draft staging
  (handoff: `eap/NEXT-SESSION-finalize-email.md`; window Tue 07-14) · (2) control-plane **GitHub
  PAT** (owner-only) · (3) optional: tell the Websites Project to refresh the review-site data ·
  (4) glance that the new Railway `review` + `postgres-botsite` services look right
- **⚑ Self-initiated:** filed 2 ideas (watchdog + recording-review); created Railway infra under
  explicit owner authorization; applied Q-0269/Q-0270 (owner-directed live)
- **↪ Next:** **finalize the Anthropic email with the owner** — `eap/NEXT-SESSION-finalize-email.md`
  (top-priority pointer now at the head of `current-state.md`)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 13 (all auto-merge on green; direct live merges per Q-0269) |
| CI-red rounds | 0 (born-red gate only — by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 2 (scheduler-independent watchdog · screen-recording review) |
| Ideas groomed | 1 (trigger-registry liveness sweep → build-ready) |
