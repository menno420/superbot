# Session — Rebuild Project kickoff (Custom Instructions + startup prompt)

> **Status:** `complete`

## What this session did
Owner-directed: the owner is moving from *evaluating* Claude Code Projects to *using* one for real
production work — the SuperBot rebuild. Produced the kickoff artifact
`docs/planning/rebuild-project-kickoff-2026-07-08.md`: paste-in **Custom Instructions** + **startup
prompt** for a fresh Project that autonomously builds canonical-plan §5 steps 7–13, forward-only,
build-first / test-later.

Key decisions (grounded in `rebuild-canonical-plan-2026-07-06.md` §5):
- **Scope = steps 7–13** (populate substrate-kit → superbot-next adopts from it → kernel K0→K8 →
  K9+strand-3 → layer-V files → K10 → port bands 1–7). **Steps 14–17 + repo settings/secrets/Railway
  are owner-only/destructive → flagged, never executed.**
- **Forward-only mechanics from the resolved probe findings:** Contents API for first-publish (git-push
  walled); fresh branch + PR + squash-merge after; no force-push/branch-delete; **no scheduled Routines
  mid-run** (they raise the operator prompt that stalls unattended sessions).
- **Repo list = three:** superbot (read), substrate-kit + superbot-next (write). Coordinator reads the
  kickoff doc rather than cramming the 4 KB spawn cap.
- **Fresh Project recommended** over archiving the current EAP coordinator (clean context + correct
  repo list).
- Build-first/test-later reconciled with the architecture: kernel/scaffold (7–12) is greenfield;
  parity/verification belongs to the port bands (13), which is where cog-by-cog testing lives.

Docs-only, `check_docs --strict` green.

## ⚑ Open for the owner
Create the fresh Project (3-repo list), paste the Custom Instructions, send the startup prompt. Owner-
only checklist + honest expectations (days-long, runs past the free 7/10 window) are in the doc.

## 💡 Session idea (Q-0089)
The kickoff pattern here — a committed `*-project-kickoff.md` the coordinator *reads* (thin pointer)
instead of a bloated Custom-Instructions field — is the clean answer to the 4 KB spawn cap we filed
as EAP friction. Worth a substrate-kit template: `PROJECT_KICKOFF.md.tmpl` (scope · orientation route ·
forward-only rails · owner-only checklist), so every future repo's Project starts from a known-good,
repo-resident brief. Distinct from CONSTITUTION.md.tmpl (agent conventions) — this is the *Project
coordinator's* entry doc.

## ⟲ Previous-session review (Q-0102)
Previous session (sign Part 2 as Claude, #1866) was a clean one-line fix but exposed a real footgun:
I reset local to origin/main while my own PR was still open, briefly moving off unmerged work. It
recovered, but the lesson is worth enforcing: **verify a PR is merged before `git reset --hard
origin/main`** — a stale-branch banner is not proof the last PR landed. Candidate journal Rule /
Stop-hook check ("open PR on this branch + about to reset to main → warn").

## 📋 Doc audit (Q-0104)
`check_docs --strict` green. Kickoff doc reachable and cross-links resolve (canonical plan, steps-6-8
brief, coordinator-kickoff, S0–S15 build order all verified present on disk this session). Nothing
lives only in chat. This is a plan doc, not a binding-rule change → no router Q.
