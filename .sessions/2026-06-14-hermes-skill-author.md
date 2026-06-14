# Session: Hermes skill-author meta-skill + docs-only-PR write scope (Q-0140)

> **Status:** `complete`

**Branch:** `claude/hermes-skill-author` · **PR:** #863 · **Date:** 2026-06-14 · **Type:** owner-directed agent-substrate (manual)

## What this session did
Built the Hermes self-extension layer + recorded the write-scope expansion the owner directed in
his Telegram chat with Hermes.

### Shipped
1. **`superbot-skill-author` meta-skill** (`docs/operations/hermes-skills/skill-author.md` + generated
   `SKILL.md`; registered in `build_skills.py` EXTRAS → 11 skills). Guides Hermes to design a new
   skill (atom or thin composite), write it in the canonical format, regenerate the artifact, and
   **commit it as a docs-only PR** — closing the "Hermes-authored skills are VPS-only" round-trip gap.
   The bootstrap for "ask Hermes to make skills" (next: the `tick` overseer composite).
2. **Q-0140** — Hermes' write scope expands to **two** sanctioned writes: review-merge (Q-0117) **+
   docs-only PRs** (work summary / bug report / new skill source). Code still goes via dispatch.
3. **`hermes-operating-prompt.md` refreshed** to the current model: 5-sector map (mechanism vs
   content), verify-don't-assume (+ Railway read Q-0130), always-a-next-thing + the continuation
   handoff (current-state ▶ + newest `.sessions/`), reconciliation-is-automated, doc-awareness via
   AGENT_ORIENTATION, and the new write scope. README "Shared operating rule" updated to match.

### Verified
`build_skills --check` ✓ (11) · `test_build_skills` 14 ✓ · `check_docs --strict` ✓ · `check_quality --check-only` ✓.

## 💡 Session idea (Q-0089)
**A `build_skills` lint: warn when a `hermes-skills/*.md` source has no matching `EXTRAS` entry** —
right now a new skill without a registered stem silently falls back to `tags=["SuperBot"]` (no
window/related metadata), easy to forget (I added the `skill-author` entry by hand). A one-line check
(every non-README source stem ∈ EXTRAS) turns a silent default into a caught omission. Small; rides
in `build_skills --check`. Dedup-checked: the freshness test checks artifact staleness, not EXTRAS
coverage — no overlap.

## ⟲ Previous-session review (Q-0102)
Reviewing the **#862 backup pg18 fix:** exemplary — drove a real prod bug to ground in two layers
(URL template → version mismatch → PATH shadowing) and **verified each fix live on the branch ref**
before merging. **What it could improve:** diagnosis cost several full workflow dispatches + heavy
status polling (large JSON each). **System improvement:** have `backup-db.yml` echo `pg_dump --version`
and the **server version** as its first dump-step line (cheap up-front diagnostic), so a mismatch is
obvious on line 1 instead of after a full dump attempt.

## Doc audit (Q-0104)
`check_docs --strict` ✓ (new skill doc + refreshed operating-prompt reachable; README table updated)
· Q-0140 recorded with provenance · operating-prompt / README / skill-author mutually consistent on
the two-sanctioned-writes model. **Grooming (Q-0015):** advanced the `autonomous-improvement-loop` +
Hermes-skills ideas — `skill-author` is the concrete self-extension seam those visions named; the
`tick` / `triage-and-fix` composites are now buildable *by Hermes*.
