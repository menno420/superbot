# 2026-06-09 — Consolidated productive-session plan (verification + reconciliation)

Maintainer-requested Opus/Fable planning+revision session: verify the same-day audit
burst (#625 settings / #627 help / #628 memory) against live GitHub + source, reconcile
it with current-state / roadmap / the multi-lane scoreboard, and produce **one**
consolidated plan for the next implementation sessions. Docs-only; plan revised once
against a maintainer-forwarded ChatGPT grounding report before approval (its two real
catches — the existing settings-roadmap banner and the BTD6 cron residue — are folded in).

## Shipped (PR #629, draft→ready per Q-0052)

- **`docs/planning/consolidated-productive-session-plan-2026-06-09.md`** — verification
  snapshot (live API + file:line source checks) · executive recommendation (**next
  implementation session = scoreboard Lane 2, Adaptive P1B**) · 9-area plan with
  greppable item IDs · priority rollup (zero critical blockers) · session sequence
  S1–S7 + gated tail · one-fact-one-home cleanup table · question routing ·
  copy-paste Lane-2 prompt.
- **Scoreboard extended, not superseded** (memory-review one-pointer rule): stale
  "After all six" tail repointed (it named #624's already-shipped Workshop/durability
  as *future* frontier); **Lanes 7–8 appended** (settings Phases 0+1; help bounded
  counts+characterization) marked *agent-recommended, not owner-ordered* — position =
  **Q-0065** (new, router §28; next free Q-0066).
- **Reconciliation pass** (all source/live-verified first): current-state ▶ Next action
  (#620–#628 all merged, zero open PRs; "verify merged" hedges on #624/#626 dropped;
  Spotlight "Still open: not registered" contradiction fixed; stamp) · roadmap Next row
  (Spotlight item → shipped #626; Lanes 7–8 line; settings-area Lane 7 bullet; stamp) ·
  settings-customization-roadmap banner extended (S7–S12 *sequencing* → audit §11) ·
  post-merge notes on both audits (#626 reality) · six "(this session)" markers → real
  PR #s (#612/#616/#618/#619) in the three AI docs · BTD6 refresh plan cron residue
  annotated (Q-0049 = dispatch-only; sketch + open-decision 1 + status line).

## Verification

`check_docs.py --strict` green · full `tests/unit/docs/` doc-pin suite green (incl. the
two settings-roadmap pins) · zero open PRs re-checked pre-push · no runtime code touched.

## Unresolved / open

- **Q-0063/Q-0064** (settings Phases 2/3 gates) and **Q-0055–Q-0059** (help overlay)
  remain open — safe defaults bind; offered with Q-0065 in the end-of-session
  structured-choices round (Protocol END 6a).
- Help-surface-map preamble counts still stale **by design** — test-coupled, queued as
  Lane 8 (don't "fix" the prose without its pin tests).
- check_docs freshness gate (repo-review R3) groomed into a Future tooling item
  (consolidated plan DOC-2) — executable config, still needs an ask before building.

## Context delta

- **Needed but not pointed to:** the **final** Q-numbering after the §9 collision
  renumbers lives only in merge-commit messages + the #628 PR body — the session
  prompt's numbers (Q-0055–57 = memory batch) were two renumbers stale. Routers's
  current state had to be re-derived before anything else made sense.
- **Discovered by hand:** (a) the real Lane-2 governance seam is
  `governance/resolver.py:379` + `governance/models.py:83` — `services/
  governance_service.py` is a decoy with no defs; (b) two *different* AI projection
  artifacts exist and scouts conflated them: the read-only
  `ai_config_projection_service` (AST-pinned non-mutating) vs the real write-side
  dual-write at `settings_mutation.py:335` → `project_from_legacy_settings`; (c) the
  settings-customization-roadmap is pinned by **two** tests
  (`test_settings_customization_doc.py` + `test_settings_manager_live_surface_doc.py:76`).
- **Pointed to but didn't need:** adaptive plan §16.8 already records the Q-0045
  decision at line 587 (the planned "add Q-0045 note" edit was a no-op); the
  agent-workflow-spec re-read added nothing the journal Protocol didn't already bind.
- **Cross-agent verify rule paid again:** one scout reported `scripts/new_subsystem.py`
  missing (it exists) and the dual-write "not confirmed" (it is) — both settled by
  direct grep before they could distort sequencing.

## Post-merge follow-up (same evening, PR #630)

#629 merged within minutes; the Protocol END 6a round fired after ready-marking and the
maintainer answered **everything** — then asked "any more questions?" and took a second
round:

- **Round 1:** Q-0065 **end-of-queue** · Q-0063 **converge gradually** (projected keys
  frozen; typed-panel convergence at settings Phase 3) · Q-0064 **binding + guided
  flow** · Q-0055 **display-only** — all the recommended options.
- **Round 2 (Q-0056–Q-0059):** Help-only names · panel-local order · custom+default in
  admin — and **Q-0059 = embed builder**, the one deviation from a recommendation: the
  Help Home message gets structured title/description/color fields, which settles the
  audit's storage question (structured overlay model, not a scalar; bounds/sanitation/
  preview mandatory; variables not chosen).

Routed in this PR: router §25/§27/§28 (verbatim + answer-scope lines) · consolidated
plan §1/§2/§3/§4/§5/§7 · scoreboard lane notes (position ratified) · both audits'
post-merge notes · `ai-config-ownership.md` frozen-keys note · roadmap settings bullet ·
current-state stamp. Remaining open questions after today: **only Q-0038–Q-0042** (the
vision batch, deliberately reserved for Lane 6's draft-answers session per Q-0051).
Next free: **Q-0066**.
