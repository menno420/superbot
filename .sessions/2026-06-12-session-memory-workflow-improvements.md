# 2026-06-12 — Session/memory/workflow improvements (hooks, plugins, OSS vision)

> **Status:** `audit`

**PR:** _(this batch)_ — workflow rule Q-0102 + hooks-and-plugins doc + OSS-memory idea
**Branch:** `claude/session-memory-workflow-improvements`

## Context

Continuation of the Hermes/autonomy conversation. Maintainer (a) granted full freedom +
invited guardrail-improvement suggestions, (b) **directed a new standing rule**: every
session reviews the previous session and surfaces a system improvement (don't hallucinate if
genuinely none), (c) asked for a **hooks/plugins doc + brainstorm**, (d) floated a strategic
direction: an **open-source package** capturing the consistent-memory + autonomous-workflow
system, refocusing priority on the substrate so sessions auto-execute bot work.

## What was done

- **New binding rule Q-0102** — `⟲ Previous-session review` as a mandatory session-ender in
  `.claude/CLAUDE.md` § Session & plan workflow; recorded as an owner directive in the
  question router. Each session now reviews its predecessor + surfaces one system/workflow
  improvement (anti-hallucination guard included). The internal mirror of the
  Hermes-as-reviewer seam.
- **`docs/operations/claude-code-hooks-and-plugins.md`** (new `reference` doc) — first
  documentation of the 5 wired hooks (what fires when), a brainstorm of candidate new hooks
  scoped to memory/workflow consistency (session-close completeness gate, previous-session
  surfacing, pre-compaction handoff, …), and a plugins posture section pointing to the
  Q-0096 evaluation (no duplication). Wired into `repo-navigation-map.md`.
- **`docs/ideas/portable-agent-memory-package-2026-06-12.md`** (new) — captures the OSS
  memory/workflow-package direction: what it generalizes from SuperBot, the core
  mechanism-vs-content separation problem, the "harden in-repo first, extract later"
  sequencing, and the priority reorientation. Routed discuss; indexed in ideas README.
- **Session-close completeness gate — WIRED (the guardrail suggestion, owner-approved).**
  `scripts/check_session_log.py` (+ test) validates the current session's log (git-selected,
  not filename) carries the Q-0089 idea + Q-0102 review + Status badge. Wired non-blocking
  into `claude_post_edit.py` (warns on session-log edits) and `claude_stop_check.py`
  (advisory when commits exist but the log is incomplete), and run `--strict` by
  `/session-close`. Turns the session-ender conventions into a checked signal.
- **Draft-first PRs dropped → Q-0103 (owner question).** Open the session PR **ready, not
  draft** (the draft state added no benefit in our self-merge flow and became a forgotten
  step → abandoned drafts; the early *open* for the PR number is what mattered). Added a
  hard **terminal-state** requirement: every session merges or closes its PR, never leaves
  it open. Updated CLAUDE.md (Q-0052 refined), router (Q-0103), and the `/session-close` skill.

## Verification

- `check_docs --strict` ✓ (200 docs, gates green). No `disbot/` changes (mypy scope untouched).

## Grooming move

Gave the just-directed Q-0102 rule a concrete **enforcement destination** rather than leaving
it rule-on-paper: routed hooks-brainstorm #1+#2 (session-close completeness gate +
previous-session surfacing at boot) as the proposed mechanism to make the Q-0089/Q-0102
session-enders *consistent* (the maintainer's stated pain). Executable-config → ask-first, so
it's proposed in the new hooks doc, not wired.

## ⟲ Previous-session review (Q-0102 — reviewing the #730 session)

- **What it did well:** shipped the Hermes skill-pack installability end-to-end (builder +
  installer + test + log-triage + operating prompt) and captured two strong forward visions
  with verified facts (Routines), not hand-wave.
- **What it could have done better:** it pushed **single commits four times** to the same PR,
  triggering four separate CI runs for one logical change — wasteful and slow to merge.
- **System improvement surfaced:** *batch session-close doc edits (log, grooming, idea) and
  push once* before the first CI-triggering push, so one PR = ideally one or two CI runs.
  Candidate to encode later as guidance in the session-close skill. (Applied this session:
  all edits batched into a single pre-push.)

## 💡 Session idea

**Idea:** Context-pack staleness flag in the SessionStart banner.
**Why:** `docs/agent/generated/*.context.md` are built from `docs/agent/index.yml`; if the
index changes and the packs aren't rebuilt, a session can orient off **stale** packs without
knowing. The boot banner already runs — have it flag when any generated pack is older than
its `index.yml` source (a one-line mtime check), so a session distrusts stale orientation
before relying on it. Small, memory-system-aligned, closes a silent-misinformation gap.
_Dedup-checked: not in the hooks brainstorm (#1–#5) or the ideas backlog._
