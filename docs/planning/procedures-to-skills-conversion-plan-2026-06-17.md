# Plan — Convert procedural prose into on-demand skills (slim the always-loaded context)

> **Status:** `plan` — executable. Owner-directed + approved in-session 2026-06-17 (extends **Q-0170**;
> the [agent-tooling shortlist](../ideas/agent-tooling-automation-shortlist-2026-06-17.md) is the idea).
> Owner's framing: *"they won't be completely gone, but they will not waste so much space anymore and
> only get loaded when necessary."* Source code + the binding contracts win over this file.

## Goal

Move the **procedural runbooks** ("do these steps to accomplish X") out of always-loaded context
(`.claude/CLAUDE.md`, `docs/AGENT_ORIENTATION.md`) into **on-demand skills** (`.claude/skills/*`) and
the routine prompts, so every session loads a leaner core. **Relocate, don't delete:** the knowledge
still lives in the repo — it's just pulled when needed instead of read top-to-bottom every session.

## The one rule that makes this safe — thin pointer + fat skill

For each converted procedure, CLAUDE.md **keeps**:
- the **owner directive + its Q-number** (so cross-references and provenance still resolve),
- a **one-line WHAT** (so the agent knows the procedure exists and when to run it),
- any **binding bar** that is a *rule*, not a step (e.g. "never forced filler", Q-0089),
- a **pointer** to the skill/doc that holds the HOW.

CLAUDE.md **loses**: the step-by-step detail (it moves to the skill/doc).

> Net: the *rule* stays ambient; the *runbook* loads on demand. A converted bullet shrinks from
> ~15–25 lines to ~2–4.

**Enforcement caveat (important).** A skill only runs if it's *invoked*. For **mandatory-at-a-moment**
procedures (the session enders), the trigger is already the **hook** (`scripts/claude_stop_check.py`)
+ the thin pointer — not the agent's memory. Do **not** convert a mandatory step into a skill *without*
leaving the pointer + keeping the hook reminder. Pure "always behave this way" rules are **not**
convertible at all (see the safety list).

## Inventory (from the 2026-06-17 audit — 33 procedures)

| Bucket | Count | Meaning |
|---|---|---|
| **A — already a skill** | 3 | `/pre-pr` · `/session-close` · `/architecture-review` |
| **A — already a routine** | 2 | docs-reconciliation · dispatch (the autonomous form of a skill) |
| **B — strong skill candidates** | ~13 | the procedural runbooks below |
| **C — must stay always-loaded** | ~9 | the safety list below |

**Realistic context win:** converting the B-bucket slims `.claude/CLAUDE.md` by **~100–120 lines
(~25%)**, leaving the binding rules + architecture table + CodeGraph false-positive guide + orientation
index in always-loaded context.

## ⛔ Must NOT move (the C-bucket safety list)

These shape behavior *continuously* or are *glob-triggered* — a skill (invoked at one moment) can't
replace them. **A future session must not strip these from CLAUDE.md to "save space."**

- The **architecture layer table** + the DB/Views/Mutations/Helpers invariants (binding rules).
- The **Working agreement** principles (act-vs-ask, bugs-first, drift-on-sight Q-0166, "a new idea is
  not a new priority").
- The **CodeGraph false-positive rules** (`dead-unresolved`, name-collision, decorator entry points,
  empty-callees, invisible edges) — safety-critical tool-use guardrails.
- The **reading-order router** (`Read first` + AGENT_ORIENTATION's per-task routes) — orientation that
  must be in-context before any task.
- **ownership.md / runtime_contracts.md** references and the **question-router format** (governs owner
  communication).
- The **`.claude/rules/*.md`** files (mutation-and-db, discord-views, context-compiler) — already the
  right mechanism: **glob-triggered**, so they load exactly when you edit the matching files.

## Destinations + build order (each batch a real PR)

| Batch | Convert | Destination | Risk | CLAUDE.md win |
|---|---|---|---|---|
| **1** | Q-0107 **reconciliation pass** bullet | the docs-reconciliation **routine prompt** (already owns the full procedure; manual sessions don't run it, Q-0124) → thin pointer | **low** (redundant with the routine doc) | ~20 lines |
| **2** | session **enders** (Q-0015 groom · Q-0089 idea · Q-0102 review · Q-0104 audit) + born-red/PR-lifecycle (Q-0133/Q-0103) + claim-work (Q-0126) | **`/session-close`** (already holds most) + thin pointers; keep the Stop-hook reminder | med (mandatory, cross-referenced) | ~40 lines |
| **3** | **new standalone skills** (no current home): `/pre-edit-check <file>` (context_map + arch), `/verify-bot` (boot + smoke), `/groom-ideas` | new `.claude/skills/*` + thin pointers from CLAUDE.md / journal | low (additive) | ~15 lines + journal |
| **4** | the rest of the §A shortlist: `/route-idea` · `/cog-review` · `/plan-band` · `/fix-drift` · `/new-subsystem` | new skills (mostly *new capability*, little CLAUDE.md slimming) | low | small |

**CLAUDE.md is the owner's core instruction file → every batch that edits it is held born-red for
owner review** (the same posture #1026 used for the governance edits). Batches 3–4 that only *add*
skills can merge on green.

## Skill template (matches the existing `.claude/skills/*/SKILL.md` shape)

```markdown
# /skill-name
<one-line purpose>

## What this does
<the procedure summary — points back to the CLAUDE.md directive + Q-number it implements>

## Invocation
/skill-name [args]

## Instructions for Claude
### Step 1 … (the runbook that USED to live in CLAUDE.md, verbatim + commands)
```

## Concrete before→after (Batch 1 sample — the reconciliation bullet)

**BEFORE** (`.claude/CLAUDE.md`, ~28 lines): the full Q-0107 bullet — cadence history, the two-part
reconcile+plan procedure, open-PR disposition, the band-depth + `PLAN BACKLOG THIN` flag, the
auto-trigger workflow, the manual-session carve-out, the marker reset.

**AFTER** (~6 lines):

```markdown
- **Reconciliation + planning pass — every 30th PR (Q-0107; cadence 30 per Q-0134).** A docs-only
  review + next-band planning pass. **Run automatically by the docs-reconciliation routine — a
  manually-started session does NOT run it unless the owner asks (Q-0124).** Full procedure (reconcile
  ledger/docs/open-PRs · plan the full band, depth ≥ cadence + the ⚠️ PLAN BACKLOG THIN flag, Q-0164 ·
  reset the marker): `docs/operations/autonomous-routines.md` (the routine's saved prompt), fired by
  `.github/workflows/reconciliation-trigger.yml`. `scripts/check_reconciliation_due.py` flags when due.
```

The binding bits (cadence = 30, routine-owns-it, manual-doesn't, every Q-number) stay; the 20 lines of
*how* move to the routine doc that already executes them.

## Verification (per batch)

- The moved procedure exists **verbatim** in its destination (no detail lost).
- CLAUDE.md keeps the directive + Q-number + pointer; `grep` the moved Q-numbers across `docs/` to
  confirm no cross-reference is orphaned.
- `python3.10 scripts/check_docs.py --strict` + `check_session_log` + `check_quality.py --check-only`
  green; the CLAUDE.md line-count drop is recorded in the PR.
- (Idea: a `check_pointer_integrity` lint asserting each "full procedure: <target>" pointer resolves
  to a target that still contains the procedure — captured in this session's log.)

## Rollback

Fully reversible (docs/skills only). If a converted procedure proves to be needed in always-loaded
context after all, restore the prose from git history and drop the pointer.
