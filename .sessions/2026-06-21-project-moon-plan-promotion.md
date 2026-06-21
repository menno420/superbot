# 2026-06-21 — Project Moon knowledge domain: idea → program plan (owner picked full parity)

> **Status:** `complete`

> Continuation of `.sessions/2026-06-21-project-moon-wiki-feasibility.md` (PR #1238, merged). The
> mandatory session enders (Q-0089 idea, Q-0102 prev-session review, Q-0104 doc audit) live in that
> first card; this card records the **second deliverable** of the same session — the idea→plan promotion
> after the owner answered the scope question.

## Arc

After the feasibility finding merged (#1238), I asked the owner the scope fork via `AskUserQuestion`.
They picked **(3) full parity, all games** — the maximal build. Per the working agreement (owner answer
+ "ideas exist to be built" → promote freely), I promoted the idea into a sequenced **program plan** and
recorded the owner decision. **Docs-only — no runtime code** (the build is the next session's work).

## Shipped (docs-only)

- **`docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md`** — the program plan: goal
  (Q-0192 full parity), why it's a program not a 2–3-PR plan, the **architecture call** (generalise a
  domain-agnostic `KnowledgeDomain` seam with BTD6 as instance #0, **proof-first** via a minimal Limbus
  vertical before refactoring BTD6), 5-phase sequencing, a concrete **first buildable slice** (Slice A:
  Limbus wiki ingest → `projmoon_context_service` + `AITask.PROJMOON_ANSWER` → lore Q&A + `/pm identity`),
  honest dependencies/risks, and 3 follow-up design Qs routed to the owner.
- **Router `Q-0192`** — owner decision (full parity) with its bounds (north-star scope, not a one-shot
  refactor licence; owner-directed → auto-merge; generalise-not-fork is the agent's engineering call).
- **Promotion wiring** — idea doc re-statused (open question RESOLVED → links plan); ideas-index entry +
  `planning/README.md` S2 row + active-work claim updated.

Verification: `check_docs --strict` · `check_quality --check-only` · `check_session_gate`.

## Decisions made alone (Q-0102 interview Q4)

- **Generalise the BTD6 stack into a `KnowledgeDomain` seam** rather than a parallel `projmoon_*` copy,
  and build it **proof-first** (minimal Limbus vertical first, extract the seam second — rule-of-three).
  This is an engineering call, not the owner's; recorded in the plan + Q-0192 for conscious ratification.
- **Slice-A defaults** (source = `limbuscompany.wiki.gg`; start with Limbus) chosen so the 3 open design
  Qs don't block the first build.

## 📤 Run report

- **Did:** asked the owner the scope fork (answered: full parity, all games) → promoted the feasibility
  idea into a program plan + recorded Q-0192 · **Outcome:** shipped (docs-only); first build slice queued
- **Run type:** `owner-directed · idea→plan promotion (docs-only)`
- **⚑ Owner decisions needed:** 3 follow-up design Qs in the plan §7 (source per game · lore depth ·
  `/pm` hub vs per-game) — non-blocking for Slice A
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (owner-directed promotion)
- **↪ Next:** build **Slice A** — proof-first minimal Limbus lore-Q&A vertical (`fetch_pm_limbus.py` →
  `projmoon_context_service` + `AITask.PROJMOON_ANSWER` → `/pm identity`), a focused runtime session.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session (2nd) | 1 (docs-only plan promotion) |
| Runtime (`disbot/`) code changed | 0 |
| Plans promoted | 1 (idea → program plan) |
| Owner decisions recorded | 1 (Q-0192 full parity) |
