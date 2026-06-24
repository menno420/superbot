# Session — 2026-06-24 · setup-copy jargon guard (PR 1a)

> **Status:** `complete` — tooling + test + plan note. No runtime behaviour change.

**Trigger:** "continue from where you left off" after the setup-wizard restructure plan (#1418) merged.
The spine (PR 1 proper) is gated on the owner's architectural Q-A (direct-apply lane); the **jargon
guard** is the slice of PR 1 that is Q-A-independent, contained, reversible, and test-covered — so I
built it now (⚑ self-initiated, advancing the owner-directed plan).

## What changed

- **`scripts/check_setup_copy.py`** — Q-0105 warn-first disposable guard (provenance + kill-switch
  header, mirrors `check_settings_reachability.py`). AST-scans **operator-facing** strings in
  `disbot/views/setup/` (UI kwargs + `send`/`followup` args; **excludes docstrings + logging calls**) for
  the plan §4 banned-jargon list. `--strict` / `--json` modes.
- **`tests/unit/invariants/test_setup_copy_jargon.py`** — ratchet: total-count ceiling (regression guard)
  + new-dirty-file guard (new sections must ship plain-language) + a guard-sanity case. 3/3 pass.
- **Plan updated** — records PR 1a shipped + the **measured baseline: 207 jargon strings across 33
  files** (top: `stage`×66, `guild`×58, `final review`×46, `operation`×40), vs the sim's modelled 44.
- CI mirror green (`check_quality --check-only`), `check_docs --strict` green.

## Measurement (the real deliverable beyond the tool)

The plan *modelled* 44 jargon hits on the standard-depth spine. The guard measured **207 across the whole
setup surface (33 files)** — the jargon problem is ~5× larger than the spine-only model suggested. This
is the ground-truth baseline the spine rewrite drives to zero, and the number that justifies an *enforced*
ratchet rather than a one-time cleanup.

## 💡 Session idea (Q-0089)

**Generalise the plain-language guard beyond setup → a `check_ui_copy.py` for all `views/`.** The jargon
problem isn't unique to the wizard; the same banned-term scan (with a surface-specific allowlist) would
catch jargon leaking into hub embeds, game panels, and error messages bot-wide. The setup guard is the
proof-of-concept; if it proves reliable over a few sessions (per its own kill-switch clause), promoting
the AST UI-string extractor into a shared helper and pointing it at `disbot/views/` would make
"plain-language everywhere" a project-wide ratchet. Captured here, not built — it should wait until the
setup guard has earned trust. (Dedup-checked `docs/ideas/`: no existing UI-copy-linter idea.)

## ⟲ Previous-session review (Q-0102)

Previous `.sessions/` log: the **setup-wizard restructure plan + simulator** (PR #1418). Did well: the
simulator was the right move (the owner asked for one), and the research → sim → plan chain was tight and
source-grounded. What it missed: it pushed the new `setup_wizard_sim.py` without running the formatters on
it, so CI red-flagged black+ruff and cost a fix round — the second formatting miss in two sessions on a
*new Python file added in a docs-focused session*. **System improvement this surfaced (and I acted on it
this session):** when a "docs/tooling" session adds *any* `.py`, run the full `check_quality --check-only`
before the first push, not just `check_docs` — I did exactly that here, caught black+ruff locally, and
pushed clean. Worth promoting into the Stop-hook reminder or the session-close skill: *"new `.py` this
session? run check_quality --check-only before pushing, even if the session is 'just docs'."* Routing this
as a candidate rule in the journal Quick-reference.

## 📋 Doc audit (Q-0104)

Guard + test + plan note in place; plan already linked from index + folio (last session). No owner
*decision* made (still advancing the plan; Q-A–E remain open for the owner). No `current-state.md` ledger
entry needed until the PR merges (the ledger checker keys off merged PRs; PR #1420 will be picked up by
the next reconciliation/ledger pass). `check_docs --strict` + `check_quality --check-only` green.

## Context delta

- **Surprise:** the jargon surface is ~5× the spine-only model (207 vs 44) — most of it in the
  draft/Final-Review machinery (`wizard.py`, `final_review.py`, `role_templates.py`) and the recurring
  `"…requires a guild context"` error strings (`guild`×58). Those error strings are a cheap early win:
  s/guild/server/ across setup error copy would clear ~58 findings with near-zero risk, independent of
  the spine rebuild.
- **For next session:** the spine (PR 1) still needs Q-A. A zero-risk pre-step available *now*: the
  guild→server error-copy sweep (~58 findings) — pure string edits, no behaviour change, lowers the
  ratchet immediately. Could be the next "continue" slice if the owner doesn't answer Q-A.

## ⚑ Self-initiated: YES — building the jargon guard now (PR 1a) was my initiative, advancing the
owner-directed setup-wizard plan via its Q-A-independent slice. Contained / reversible / test-covered;
warn-first (no runtime or CI-blocking behaviour change). The plan itself remains owner-directed and
plan-first; the architectural Q-A (direct-apply lane) is still the owner's to answer before the spine.
