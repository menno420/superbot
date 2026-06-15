# Session: Routine workflow canon — foolproof prompts + idea→plan promotion

> **Status:** `complete` — PR #899; born-red card flipped as the deliberate final step (Q-0133).

**Branch:** `claude/routine-workflow-canon-2026-06-15` · **Date:** 2026-06-15 · **Type:** workflow/docs (S3 mechanism) · **Trigger:** owner-directed in-session (live conversation)

## What shipped

Owner-directed overhaul of the autonomous-routine prompts so they run **completely without
guidance** and are **foolproof against bad dispatch input** (the "write a story about chickens"
test). Provenance: a long live owner session (his verbatim 12-step lifecycle) + an independent
review from a Hermes-dispatched routine. Recorded as router **Q-0144**.

- **Dispatch prompt** (`hermes-dispatch-bridge.md`) and **night-executor prompt**
  (`autonomous-routines.md`) rewritten onto the 12-step lifecycle, now explicit on: **never-stop /
  completion bias** (a routine always ships *something real* — dispatched work or the next plan
  slice), **sync-first**, **work-order-is-a-hint** (off-plan nonsense → do the plan; never invent),
  the **scope-brake vs safety-brake** split (phase gate = scope brake for self-invented features
  only; it does **not** apply to dispatched work; irreversible safety brakes never bend),
  **authorization** (dispatched = owner asking = build it), **2–3 slices bounded by ~700K**,
  born-red mock PR, judgment-over-plan, bugs-first, and the standing enders.
- **Reconciliation prompt** gained the owner's **idea→plan promotion**: when executable plans run
  low on real work, review `docs/ideas/` and promote the best owner-aligned idea into a complete
  executable plan, indexed so it becomes the executor's next ▶ Next action. Plus sync-first.
- **`ai-project-workflow.md` §10** bounded-session: "~2 substantial tasks" → "2–3 slices,
  ~700K-bounded."
- Router **Q-0144** records the decision + provenance; current-state stamp-line updated.

The in-repo prompts are the **canonical mirror** — the owner re-pastes the final text into each
routine's console config to take effect. `check_docs --strict` ✓. Docs only (no `disbot/`).

## 💡 Session idea (Q-0089)

**Paste-ready routine-prompt files** — extract each routine prompt into its own standalone
`docs/operations/routine-prompts/{dispatch,executor,reconciliation}.txt` that the owner copies
*wholesale* into the console, instead of hand-extracting it from prose inside a larger doc. Kills
copy/paste errors, makes the repo-canonical ↔ console-live drift a clean `diff`, and (optional
follow-on) lets a checker assert the load-bearing invariants — sync-first, never-stop, scope-vs-
safety-brake — are present in each, so a future edit can't silently drop them. Small, docs-only.

## ⟲ Previous-run review (Q-0102)

#898 did the right thing recording the dispatched-vs-self-originated phase-gate clarification in
two canonical homes (router Q-0114 + `check_phase_gate.py`'s docstring) so the fix didn't depend
on a grep into the ideas backlog. But it fixed the **cross-reference docs**, not the **routine
prompt itself** — and the prompt is the *first and most authoritative* thing a routine reads, so
the literal prompt kept fighting the intent (it still said "feature (agent-originated) → DO NOT
build", with the escape hatch buried in a parenthetical). The lesson this session acts on: **when
a fix is about agent behavior, fix the PROMPT first** (it outranks a referenced doc), not only the
cross-reference. This PR closes that gap — the authorization rule now lives in the prompt where the
routine actually reads it.

## Handoff

The prompts are canonical in-repo; **owner action: re-paste the three updated prompt blocks into
the routine console configs** for them to take effect (the full text is in the PR + surfaced in
chat). Natural next slice: the Q-0089 paste-ready-files extraction (makes the re-paste foolproof).
Separately, the executor's GitHub-`schedule:` trigger is unreliable (fires ~1×/night, hours late —
proven from run history); the owner is moving the reliable cadence to Hermes' VPS cron
(`routine_fire.py`) — that control-plane migration is owner-led and out of scope here.
