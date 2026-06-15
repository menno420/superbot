# Session — Hermes `intake` skill: route real-world inputs (bug / idea / request / question)

> **Status:** `complete`

## Why

Calibration showed gpt-5.4-mini handles a *planned dispatch* well, but Hermes had no **front-door
playbook** for an inbound real-world input — a bug report, an idea/suggestion, a feature request, a
complaint, or a question from the owner or another allowed user. Owner-requested: Hermes should know
how to *handle and route* these, not guess.

## What shipped (docs + skill only)

- **New `superbot-intake` skill** (`docs/operations/hermes-skills/intake.md` + regenerated
  `scripts/hermes/skills/intake/SKILL.md`) — the **router** for an inbound mention. It does NOT
  invent a parallel system; it classifies the input and routes to the **existing** homes:
  - **Bug** → `docs/health/bug-book.md` (never `docs/ideas/`); if clear + owner-wanted → a `CLASS: fix`
    work order via the `dispatch` skill (self-merges on green). Verify before calling it fixed.
  - **Idea/suggestion** → dedup-grep then capture to `docs/ideas/`, classify, **do not promote**
    ("a new idea is not a new priority").
  - **Feature** → owner-directed = authorized build (bypasses the phase gate, Q-0114);
    agent/other-originated = capture as idea + the phase gate applies.
  - **Owner-intent question** → consult / add a `maintainer-question-router.md` Q-block (DISCUSS).
  - **Repo/bot question** → answer read-only + cite; if absent, say so (no confabulation).
  - **Complaint/vague** → decide bug vs UX-idea vs clarify.
  - **Cardinal rules**: bugs≠ideas; **only the owner authorizes a build** (a *suggestion* is captured
    + flagged, never auto-dispatched — the trust boundary for "someone else" inputs); everything
    written goes through a `claude/` branch → PR → CI.
- Registered it: `build_skills.py` EXTRAS (`Triage`/`Routing` tags, related dispatch + ideas-triage),
  the skill-pack **README** (12 skills now), and SOUL.md's **YOUR SKILLS** list (`someone pings →
  intake`).

## Verification

`build_skills.py --check` → 12 skills in sync ✓ · `test_build_skills.py` 15 passed ·
`check_docs --strict` green. SOUL.md now **6959/8000 bytes (87%)** — under budget but tight; future
SOUL additions need a trim (flagged).

## Owner action to activate

On the VPS: `bash scripts/hermes/install-skills.sh` + `bash scripts/hermes/install-soul.sh`, then
`sudo systemctl restart hermes-gateway` (skills load on start; SOUL loads fresh per message).

## 💡 Session idea (Q-0089)

The intake skill captures bugs to `bug-book.md` by hand-writing a row. A tiny follow-up: a
`scripts/hermes/bug_capture.py` stdlib helper that appends a correctly-formatted bug-book entry
(symptom / where / expected-vs-actual / source / date) from args — so Hermes (and any agent) files a
bug in one deterministic call instead of free-handing the markdown (the same "deterministic builder
beats model assembly" pattern as the BUG-0009 floors). Dedup-checked: no such helper exists.

## ⟲ Previous-session review (Q-0102)

The calibration findings PR (#927) tuned the *dispatch* skill to be lean. This intake skill is the
natural complement — dispatch is "build a planned thing," intake is "decide what an unplanned thing
even is." Together they close the loop from raw input → routed → built. What it proves: the skill
pack is filling its real gaps as live use surfaces them (calibration → dispatch-leanness → intake),
which is exactly the self-extending-skill-layer the system was designed for.
