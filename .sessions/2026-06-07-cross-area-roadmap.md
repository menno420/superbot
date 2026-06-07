# 2026-06-07 — Cross-area implementation roadmap + AI-roadmap reconciliation

- **Arc:** maintainer wanted the 16-doc `plan` pile "refreshed into something manageable":
  a single cross-area roadmap index, by code area, short description + link per plan, with
  a rough timeline. Branch `claude/dazzling-noether-SkuC4` (continues the docs sessions
  that shipped #563/#564). A 2-question batch chose **relative horizons + gates** (not
  dates — matches the associative working profile) and **include the ideas backlog, marked
  not-approved**.
- **Built `docs/roadmap.md`** — by-area sections (the 7 folios + building/UI), each row a
  one-liner + link to the authoritative plan + folio, with Now/Next/Later/Someday horizons
  + per-item gates, a "Someday/ideas (not approved)" section, and an "Adding a plan" slot.
  Framed as an evolving cut on purpose.
- **Triaged the 16 plans** from their self-declared status: re-badged 2 mis-badged
  historical plans (`phase_2b_bindings_plan` = shipped #73; `btd6-game-file-extraction-plan`
  = historical roadmap); the rest placed by area + horizon + gate. Wired the roadmap into
  `current-state` "Next candidates" + `AGENT_ORIENTATION` (reachable + catalogued).
- **Mid-session: Codex opened #565** (AI roadmap `docs/planning/ai-roadmap-2026-06-07.md`
  Phase 0–11 + a 10-question router batch). Maintainer flagged it ("don't make it too
  definitive"). Chose: **review #565 + digest the 10 Qs**, and **hold my roadmap until #565
  merged**.
  - **Review verdict: sound.** It verified against current `main` (cites #564), preserves
    the read-only AI boundary, reuses existing owners ("no second system"), defers actions,
    and honestly flags its gaps. No overreach.
  - **Digested the 10 Qs**; only AR-10 truly gated the next move. Maintainer answered the 3
    foundational ones (all = safe defaults): **AR-10** lock orchestration foundation,
    **AR-08** tiered audience, **AR-09** explanation-only now (report-draft first if
    revisited). AR-01–07 hold at defaults until their lanes activate.
- **Finalized after the maintainer merged #565:** merged `main` into the branch, hard-linked
  the AI roadmap from `roadmap.md`'s AI section + the AI folio (AI-area authority), and
  recorded the 3 answers in the router (**new §18**). Cross-area roadmap's AI section now
  defers to the AI roadmap (one home).
- **Gates:** `check_docs --strict` clean (badges + links + reachability, 0 orphans);
  `check_architecture --mode strict` exit 0. Docs-only. **State: `docs/current-state.md`.**
