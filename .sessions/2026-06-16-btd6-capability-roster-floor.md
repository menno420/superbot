# Session — BTD6 property/capability roster floors (AI §7.6 new family)

> **Status:** `complete` — work done, PR #975, self-merge on green (Q-0113: small/contained,
> read-only deterministic floors).
> **Date:** 2026-06-16 · **Branch:** `claude/magical-rubin-pimgyi` · **PR:** #975

## What I did

Scheduled dispatch, empty work order → advance the next plan slice. The §7.5 multi-entity
*comparison* family is COMPLETE (#946/#950/#955/#962); the live ▶ NEXT named "a *new* AI §7 workflow
family beyond §7.5 (plan-first)". I opened that family — the **property/capability roster** floor (a
*list-by-property*, not a rank/diff) — the same BUG-0009 wrong-assembly class on the roster side: the
model assembles the list itself and can include/exclude the wrong entity, and because every name is
grounded the value-only faithfulness guard never catches a mis-*roster*. The authoritative answers
already exist deterministically; this fronts them as pre-emptive floors on the shared
`_BTD6_LIST_BUILDERS` seam. **Two complete slices:**

1. **Tower capability roster** (`deterministic_capability_roster_reply`) — fronts
   `services.btd6_capability_service` ("which towers can pop lead / detect camo / pop
   black-white-purple?"). Base 0-0-0 scope by default; an explicit "with upgrades" signal flips to the
   earliest-upgrade roster; a `paragon` cue answers the per-paragon camo roster (the only per-paragon
   capability the service verifies). It was previously reachable only as a model-callable tool
   (`btd6_capability_lookup`), never as a floor.
2. **Bloon roster** (`deterministic_bloon_roster_reply`) — fronts the committed `bloons.json` fields
   ("what are all the MOAB-class bloons", "which bloons are immune to sharp/cold/explosion?") via
   `category` + `immune_to`, modifier pseudo-bloons excluded. This is the bloon side the sibling
   `deterministic_roster_reply` (heroes/towers/paragons/maps) never covered.

Both are read-only deterministic (Q-0048, no prod-check), held to the
`test_btd6_floor_builder_exclusivity.py` one-fires invariant (corpus + defer-set extended for both).
Docs de-staled: AI plan §7.6 added, current-state ledger entry + archived the two oldest (#910/#906)
to hold the ratchet at 20.

## Verification

- `python3.10 scripts/check_quality.py --full` → green (10184 passed, +40 new tests; black/isort/ruff/
  mypy clean).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (exit 0).
- `python3.10 scripts/check_docs.py --strict` → green (ledger back to 20).
- Tests: `tests/unit/services/test_btd6_capability_roster.py` ·
  `tests/unit/services/test_btd6_bloon_roster.py` · exclusivity corpus.

## Handoff — ▶ next

The §7.6 roster family is OPEN with two members. Clean turn-key continuations, same shape:
- **More §7.6 roster members:** hero capability rosters (which heroes detect/grant camo), CT-relic
  property lists, or a tower-by-category-with-property roster. Each fronts an existing deterministic
  service via a new `_BTD6_LIST_BUILDERS` member + an exclusivity-corpus entry.
- **A *new* family beyond rosters+comparison** (plan-first): the §7 `optimization` / `round_analysis`
  intents are still unbuilt deterministic families.
- **Reconciliation is DUE** (SessionStart `Recon: DUE`, marker #930, latest merged past #960; the
  ledger guard lists ~12 unreconciled merged PRs — #959/#963/#964/#965/#966/#968/#974…). That is the
  **docs-reconciliation routine's** job (Q-0124 — a dispatch session does not run the pass), auto-fired
  by the `reconcile`-issue trigger. Left untouched apart from this PR's own entry.
- Open PRs at session end (left alone): #974 (another session's docs/dashboard handoff, born-red),
  #941 + #929 (`needs-hermes-review` carve-outs).

## 💡 Session idea (Q-0089)

**A generated "deterministic floor catalogue" index.** The `_BTD6_LIST_BUILDERS` family now grows ~one
member per dispatch, and deciding "what's the next unbuilt roster/comparison?" each session means
grepping the dispatcher + reading every builder to see which data surfaces are already fronted (I did
exactly that this run). A tiny stdlib script that introspects the live tuple + maps each builder to
the service/data surface it fronts (and flags roster-shaped services with NO floor yet — e.g. hero
capabilities) would make that decision instant and keep the family's coverage visible rather than
tribal. Captured for `docs/ideas/` (dedup-checked: no existing floor-catalogue idea). Genuine — it
directly removes the navigation cost I just paid.

## ⟲ Previous-session review (Q-0102)

Previous: `2026-06-16-hermes-efficiency-skills.md` (#959) — Hermes control-plane efficiency skills
(idea-spotlight + morning-briefing + dispatch-resolve) + a 6h auto-reset. **Did well:** tightly
owner-steered — it asked two `AskUserQuestion` steering questions before building and recorded the
answer as Q-0153, so the scope matched intent exactly; good test coverage on each new script; it was
honest about the one UNVERIFIED knob (`HERMES_RESET_CMD`). **Could improve / system surface:** it left
one knob unverifiable in the sandbox and documented it as such — correct, but the recurring pattern
across sessions is *several* such "unverified, owner must confirm" artifacts accumulating with no
single place that tracks which ones are still unconfirmed. **Improvement:** a lightweight
"unverified-knob register" (a section in the ops docs or a `docs/health/` checklist) that each session
appends its UNVERIFIED items to and the owner ticks off — so a convenience knob that proves wrong is
found and removed (the Q-0105 disposable-tool discipline) rather than silently trusted. Small, and it
makes the human-verification backlog legible instead of scattered across session logs.

## Doc audit (Q-0104)

`check_docs --strict` green; AI §7 plan + current-state ledger updated for #975; no new owner decision
to route (Q-0048 already covers read-only deterministic floors). The reconciliation-drift the ledger
guard reports is pre-existing and owned by the docs-reconciliation routine, not this session.
No bug-book entries changed (no runtime bug surfaced this run).
