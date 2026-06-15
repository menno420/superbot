# Session — Hermes retune for gpt-5.4-mini + memory/base cleanup

> **Status:** `in-progress`

## Goal

Owner-directed, live session. Now that **gpt-5.4-mini is confirmed working** (the model arc
#913→#921 closed), re-tune the Hermes control-plane base for the *capable* model and prune what was
built defensively around the old weak free model (`stepfun/step-3.7-flash:free`, ~256K). Goal: a
**cleaner base configured to the owner's wish** + a recorded understanding of gpt-5.4-mini's real
capabilities.

## What I'm doing

1. **SOUL.md retune** (`hermes-operating-prompt.md`) — replace the weak-model framing
   ("you forget after ~15 tool calls / ~256K window") with the capable-model reality (400K reasoning
   model; bounded sessions are now a **cost + re-grounding** habit, not a weakness crutch). Fix the
   dispatch bullet's stale "you're weaker on long loops" → the real reason (Claude Code runs the CI
   mirror Hermes can't).
2. **gpt-5.4-mini specs recorded** (`hermes-control-plane.md` § Model/provider) — verified
   2026-06-15: **400K ctx / 128K out, $0.75/$4.50 per 1M, Aug-2025 cutoff, reasoning model**, +
   `agent.reasoning_effort` tuning lever, + cost-not-window framing.
3. **Hermes memory cleanup** (owner applies on the VPS) — the owner shared the 4 live memory
   entries; 3 of 4 duplicate SOUL.md / the `dispatch` skill / current-state. Recommended lean
   replacement set (infra stickies + one behavioral sticky only).
4. **Deeper base cleanup** (in progress) — archive/demote the token-efficiency investigation doc
   (its conclusion was "it's the model"), slim `apply_context_fixes.sh` (compaction tuning now
   secondary to the capability fix), prune the long completed "Suggested next steps".

## Findings surfaced

- **Python pin drift — investigated, ALREADY TRACKED (no action needed this session).**
  `.python-version` = **3.13.13** (Railway/prod) vs CI `code-quality.yml` = **3.10**. Hermes'
  memory flagged it correctly, but it is **not a hidden bug** — it is documented in
  `operations/production-deployment.md` § "Python version" and tracked as **router Q-0085**
  (Open, awaiting owner). History: prod has *always* run 3.13 (unpinned railpack default); the
  `3.13.13` pin (PR #863, 2026-06-14) was a *fix* for a railpack build-race outage, not the cause
  of the drift. CI/tooling stayed on 3.10 (pyproject `target-version = py310`, mypy
  `python_version = 3.10`, the repo-wide `python3.10 -m` rule). **Recommendation (already on
  record in Q-0085): option 1 — align CI/local UP to 3.13 as its own dedicated toolchain-migration
  session, not a rider on anything.** Until then the documented drift is accepted. → This means it
  can safely **drop from Hermes' memory** (point it at Q-0085 / production-deployment.md instead).

## Hermes memory — recommended lean set (owner applies on the VPS)

The owner shared Hermes' 4 live memory entries. Per SOUL.md's own rule — *"direct memory is a tiny
sticky note; the real memory is the repo"* — 3 of 4 duplicate SOUL.md / the `dispatch` skill /
current-state.md and should be **deleted** (they burn context and risk drifting from the docs).

**KEEP (rewritten lean — the genuinely non-repo stickies):**

```
[infra] SuperBot deploys on merge → Railway project reliable-grace / service "superbot".
        Hermes model = gpt-5.4-mini on the owner's own OpenAI key (custom OpenAI provider,
        base https://api.openai.com/v1). Dispatch cron job id = 8c02f8431f37.
[rule]  Bug reports / notes go to docs/health/bug-book.md or docs/current-state.md —
        NEVER docs/ideas/* (ideas are for genuine new features). Hermes tripped on this (#888).
[prefs] <owner working style / nicknames only — keep here and nowhere else>
```

**DELETE (redundant with durable docs that load every session):**
- *Dispatch bridge* → fully in the `dispatch` skill + `hermes-dispatch-bridge.md`.
- *SuperBot memory summary* (orientation / read-path / next-action source) → all in SOUL.md.
  Its Python-drift fact → now Q-0085 / `production-deployment.md` (see Findings above), so drop it.
- *Overseer model* (role, born-red-PR-per-session) → SOUL.md "WHO YOU ARE" + Q-0133; only the cron
  id was worth keeping (folded into `[infra]` above).
- *Dispatch bridge pattern* (the four-section TASK/CONTEXT/ACCEPTANCE/NOTES + `routine_fire.py`
  format) → verbatim in `dispatch.md` lines 65–79.

### USER.md (the "about you / this workspace" file) — separate from MEMORY.md above

The owner also shared the 8 `USER.md` entries. Mostly good (it already carries the `[infra]` +
bug-location stickies), but:
- **WRONG / stale — must fix:** *"default to read-only inspection unless you explicitly ask for
  modifications."* This is the OLD safety model; SOUL.md's "WHAT YOU MAY WRITE" (Q-0140/0141/0117)
  now lets Hermes author PRs + merge via the review gate. A wrong memory actively misleads — delete it.
- **Conflicting:** *"capture ideas in docs/ideas/"* (alone) contradicts the bug-location entry —
  merge into one rule: ideas → `docs/ideas/`; bugs/notes → bug-book / current-state, NEVER ideas.
- **Redundant with SOUL.md (drop):** the oversight-rules block (sync-first, review, dispatch,
  concise comms, reconciliation-is-automatic), the dispatch-workflow entry, and the work-order
  grounding entry are all in SOUL.md + the `dispatch` skill.
- **Keep:** the `[infra]` note (Railway reliable-grace/superbot · gpt-5.4-mini on owner's key · cron
  `8c02f8431f37`) and the bug-location rule.

Recommended lean USER.md: genuine owner **preferences** (concise/direct comms; owner can't code →
relies on agents for correct end-to-end work) + the `[infra]` sticky + the merged ideas/bugs rule.
On Hermes' offer to split into prefs / repo-conventions / runtime: yes for prefs + runtime, but
**drop the repo-conventions** — they live in SOUL.md, which reloads every session, so memory copies
only risk drift.

## Hermes skills — prune the catalogue (79 → ~30; owner runs `hermes skills uninstall`)

Skills load by progressive disclosure — the Level-0 list (all names+descriptions, ~3k+ tokens) is
injected every turn, so 79 skills is real per-turn bloat + choice-noise. Keep only what the
oversight/dispatch/review control plane uses:

- **KEEP:** all `superbot/*` (13); `github/*` (6 — PR/issue/review/repo); `autonomous-ai-agents/`
  claude-code · codex · hermes-agent · supervised-repo-oversight (it dispatches to these / is its
  role); `software-development/` plan · requesting-code-review · simplify-code · systematic-debugging
  · hermes-agent-skill-authoring.
- **PRUNE (whole categories — nothing to do with SuperBot):** `creative/*`, `media/*`,
  `productivity/*`, `smart-home/*`, `mlops/*`, `note-taking/*`, `social-media/*`, `data-science/*`,
  `email/*`, `research/*`, `yuanbao`, plus `software-development/` node-inspect-debugger (SuperBot is
  Python). ~46–50 skills.
- **Your call:** `opencode`, `software-development/` spike · test-driven-development · python-debugpy
  (Hermes dispatches code rather than debugging it live — lean prune).

Cheatsheet now documents the principle + `hermes skills uninstall` (the repo only had install).

## 💡 Session idea (Q-0089)

**A repeatable "Hermes base hygiene" check.** This session audited Hermes' live state against the
repo's intent **by hand** — found 79 installed skills (only ~30 relevant), 4 MEMORY.md entries that
duplicate SOUL.md/the dispatch skill, and a stale "read-only default" USER.md entry that now
contradicts SOUL.md. All three are *drift between Hermes' live config and the durable docs*. Idea: a
small read-only helper/skill (`hermes-base-hygiene`) that flags this drift — e.g. "installed skills ≫
the focused set," "a memory entry's text substring-matches SOUL.md (likely redundant)," "a USER.md
line contradicts WHAT YOU MAY WRITE." Worth having because the base will re-drift every time bundled
skills update or memory accretes; doing the audit by hand each time is the waste it removes.

## ⟲ Previous-session review (Q-0102)

Previous session = **#921** (Hermes model-swap RESOLVED). **Did well:** cleanly closed the long
model arc and captured the genuinely-useful propagation-flap lesson (don't conclude "not propagation"
at 15 min). **Missed / could've done better:** it confirmed the *capable* model worked but stopped
there — it left the entire Hermes base (SOUL.md, control-plane doc, the token-efficiency
investigation) still written defensively for the **old weak model**, so the docs actively
contradicted the live reality until this session caught it. **System improvement:** the
**model-switch playbook should end with a "sweep the base for old-model assumptions" step** — a model
swap isn't done when the model answers; it's done when the prompt/docs written around the *prior*
model are re-tuned. (This is the same drift the 💡 idea above would automate.)

## Status

All Hermes-base files reviewed (SOUL.md · control-plane · investigation · cheatsheet ·
`apply_context_fixes.sh` · skills · memories · `hermes_cog.py`). PR #923 held **born-red** (Q-0133)
per owner's "keep open" — flips to `complete` (→ auto-merge on green) on the owner's word; enders +
docs audit are done, so it is merge-ready.
