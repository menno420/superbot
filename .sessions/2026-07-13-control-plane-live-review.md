# 2026-07-13 — Control-plane live centralization review (owner ask)

> **Status:** `complete`
> **Branch:** `claude/control-plane-live-review` (restarted from main) · **PR:** #2070
> **📊 Model:** Opus 4.8
> **Venue:** owner-live chat, remote container (hub repo)

## What happened

Owner refreshed all seats' ender + boot prompts and still senses the website isn't fully
centralized; asked for a thorough review of the live control-plane
(https://control-plane-production-abb0.up.railway.app/). I crawled the live site
(homepage + /fleet /freshness /projects /prompts /queue /directory via WebFetch) and
cross-referenced against the architecture I mapped for the #2066 data-plane design.

**Shipped:** [`docs/planning/control-plane-centralization-review-2026-07-13.md`](../docs/planning/control-plane-centralization-review-2026-07-13.md)
— headline: the same fleet renders as **6 different sizes** across pages (homepage 4 ·
prompts 9 · projects 11 · directory 15 · fleet 18 · freshness 18) = non-centralization made
visible (root cause: six source-of-truth lists). Six findings: (1) six lists, (2) homepage
false-"all quiet" scoped to 4/18 lanes while venture-lab is dark, (3) doubled Railway estate
(reliable-grace vs superbot-websites, both live), (4) seat-vs-repo naming split with no
crosswalk, (5) blind deploy state ("unknown", token-starved), (6) why re-pasting prompts
still shows drift (the site can't observe console pastes; 13 "not recorded"). Fair credit
for /prompts, /queue, /directory, /fleet+/freshness. Prioritized fixes; homed in S5-ops next
to the #2066 design it confirms. Routes to the websites lane.

## ⚑ Self-initiated (Q-0172)

None — owner-directed review; the findings doc is the deliverable.

## 💡 Session idea (Q-0089)

**A "fleet-size consistency" checker for the websites repo.** The whole review reduces to
one measurable invariant: every page's fleet count should derive from one list. A tiny CI
check (or a `/freshness`-style self-test) that fetches each page's rendered count and fails
when they disagree would turn "the owner noticed the site felt off" into an automated red.
It's the enforcing version of finding 1 — and it would have caught the 4-vs-18 homepage
gap the day it shipped. Dedup: the #2066 design proposes the manifest (the fix); no idea
proposes the *consistency assertion* that guards it. Routes to the websites lane.

## ⟲ Previous-session review (Q-0102)

The friend-onboarding session (#2068) shipped a genuinely useful prompt and its Codex-fix
follow-up (#2069) caught a real prompt-injection vector — good end-to-end. It again
hand-assembled its close-out rather than using `/session-close`, and again tripped the
docs-reachability check pattern (this session pre-empted that by homing the doc *before*
push — the lesson is finally sticking). **System improvement:** the recurring "orphaned
planning doc" trip across #2066/#2068/#2070 is now a clear pattern — `docs/planning/` and
`docs/owner/` docs need a read-path link, and I keep learning it at CI instead of at write
time. That's a candidate for a **pre-commit reachability hint** (a checker line in the
born-red flow that names the orphan before the flip), which is a stronger version of this
session's manual pre-check.

## Docs audit (Q-0104)

- Reachability pre-checked BEFORE push this time (the #2066/#2068 lesson): homed in
  `docs/current-state/S5-ops.md` next to the #2066 data-plane entry; `check_docs --strict`
  confirmed exit 0 before commit (real exit code).
- Telemetry row appended (Q-0194, opus-4.8 canonical). Claim deleted at close.
- Note: PR #2070 lands on the recon-boundary number, but a manual session does not run the
  Q-0107 pass (Q-0124) — the routine owns it; flagged only.
- Nothing valuable chat-only: full findings in the committed doc; chat carries the summary.
