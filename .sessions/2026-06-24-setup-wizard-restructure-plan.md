# Session — 2026-06-24 · setup-wizard restructure plan

> **Status:** `complete` — research + simulator + plan. Docs + sim only; no runtime change.

**Trigger:** owner redirected mid-session (chat): the setup wizard "has never been completely working as
intended"; now that nearly all setup-worthy functions exist, produce **a good plan on what to include and
which step order**, with **thorough research + possibly a simulator**, so it's quick, intuitive, needs
**zero Discord/bot knowledge, no jargon**, button/dropdown-driven, and **each step is one complete action
that actually completes a setup step properly**.

## What changed

- **New plan** [`docs/planning/setup-wizard-restructure-plan-2026-06-24.md`](../docs/planning/setup-wizard-restructure-plan-2026-06-24.md)
  — four design laws (one real action per step · zero jargon · bot auto-creates what a step needs · short
  linear button-only spine) → a **6-step essentials spine** (server type → greet members → moderators →
  block spam → logs → rewards → help desk → done) applied **per-step via the direct lane**, with
  diagnostics + the long tail moved to an **Extras** menu + a single **"Check my setup"** button. Includes
  a full current→disposition table for all 18 existing sections, a jargon→plain-language rename table, the
  one architectural decision (direct-apply per step, surfaced as Q-A), and a 3-PR build path with a
  banned-jargon CI guard.
- **New simulator** [`tools/sim/setup_wizard_sim.py`](../tools/sim/setup_wizard_sim.py) — deterministic
  drop-off model (dead steps + jargon + dead-ends + length). Result: **current standard flow ~4% modelled
  finish** (17 screens · 6 dead · 2 dead-ends · 44 jargon) → **proposed ~79%** (8 screens · 0 · 0 · 0),
  verdict PASS. Mirrors the `tools/sim/` convention (claim_layout_sim/fishing_minigame_sim).
- **Plan index** — S1 row added; **folio** link via `settings-bindings-provisioning`.
- CI caught the doc-orphan (check_docs reachable) on the first push; fixed by the README link, re-green.

## Research (3 parallel Explore sweeps, source-grounded)

1. Current wizard mapped: 18 `SetupSection`s, depth-filtered, draft → Final Review pipeline, owner-gated
   hub. 2. Full setup-worthy inventory across `subsystem_registry` + every `*_config` service +
   `settings_keys` — surfaced that **welcome, automod, security, counters, starboard, image-mod, karma**
   are configurable but **absent from the wizard**. 3. Problems confirmed: ~half the steps complete no
   action (owner's P0), pervasive jargon (verbatim quotes captured), dead-ends (roles needs pre-existing
   roles), and prior plans (adaptive-setup historical; consolidation §3.5 U10; cog-improvement-audit).

## 💡 Session idea (Q-0089)

**`check_setup_copy.py` — a banned-jargon CI guard for operator-facing setup strings.** Already written
into the plan (PR 1) but worth flagging as a reusable idea on its own: a stdlib check (Q-0105 disposable
header) that scans setup section labels/embed copy and fails on any term from a banned list (draft,
operation, bind, cog, scope, resolver, threshold, seam, pipeline, guild, …). It makes "no jargon" a
*ratchet* instead of a one-time cleanup that silently rots as new sections land — the same
guard-the-invariant pattern as the existing `check_dashboard_data`/ledger guards. Genuinely believe in it:
the jargon problem recurred precisely because nothing enforced plain language.

## ⟲ Previous-session review (Q-0102)

Previous `.sessions/` log: the **bot-migration-assistant plan** (PR #1416, merged). Did well: grounded
every layering claim in verified seams before writing, opened born-red fast, clean auto-merge. What it
could have done better: it picked a docs-home default (catalog shared with V-14) and listed it as an open
Q, but didn't *check whether a V-14 teardown catalog file already exists* to share with — a 30-second grep
that would have made the recommendation concrete instead of conditional. **System improvement this
surfaces:** when a plan recommends "reuse/share with existing artifact X", the plan-writing step should
verify X exists (and cite its path) rather than leave it as an assumption — a small grounding discipline
that turns a soft recommendation into a checkable one. Applied the spirit here: this plan cites the exact
config services (`welcome_config`, `automod_config`, …) the spine reuses, verified present in the
inventory sweep.

## 📋 Doc audit (Q-0104)

Plan + sim + index + folio link all in place; `check_docs --strict` green. No owner *decision* was made
(the owner set direction + asked for a plan; the 5 design Qs are routed in the plan body for his answer,
not yet decisions) → no router Q-block owed yet. No `current-state.md` ledger change (no merged runtime PR
— this session is docs/sim only). The bot-migration plan is correctly cross-linked from this plan's Extras
menu ("Replace another bot").

## Context delta

- **Surprise:** the wizard's *engine* is genuinely good — the pain is entirely structure + copy + missing
  steps, not architecture. The restructure is mostly composition of existing audited services + the
  direct lane (which the ticket section already proves), so PR 1 needs **no new mutation primitives**.
- **Biggest single win available:** adding the **welcome/greeting** step — the most universal first-run
  task is currently absent from setup entirely.
- **For next session (if greenlit):** start PR 1 (essentials spine), resolve Q-A first (confirm
  direct-apply per step) — it shapes whether each step writes immediately or stages. Q-A is the one
  decision with architectural weight; the other four (Qs B–E) are taste/scope.

## ⚑ Self-initiated: none — owner-directed (the restructure, the research, and the simulator were all
explicitly requested in chat). Plan-first; build needs a greenlight. The session's *first* framing
(building bot-migration PR 1) was correctly abandoned when the owner redirected to the wizard plan.
