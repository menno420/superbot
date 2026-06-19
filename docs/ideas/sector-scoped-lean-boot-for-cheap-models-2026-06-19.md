# Sector-scoped lean boot — make cheap models (Sonnet) usable by cutting the orientation tax

> **Status:** `ideas` — **owner-directed (2026-06-19, brainstorm). B1-priority for the next session.**
> Source + the binding contracts win. **Subsystem:** none — agent-workflow / orientation system (no bot subsystem).

## The problem (owner-felt, recurring)

On the x20 plan the maintainer still runs short on the **weekly all-models** bucket, while the separate
**Sonnet** bucket sits nearly unused — because Sonnet can't work here: the mandatory boot (CLAUDE.md +
collaboration-model + current-state + journal + plan index + binding docs + CodeGraph) **fills Sonnet's
context before it can do anything**, so it compacts on arrival. The orientation tax effectively costs an
entire weekly bucket every week.

## The foundation already exists (owner-built)

The maintainer already did the hard part: the repo is partitioned into **5 planning sectors**
(S1 bot · S2 btd6 · S3 ai-memory · S4 docs · S5 ops — Q-0137, `repo-sector-map.md`), **explicitly to make
the repo Sonnet-ready**. That partition is the prerequisite for scoped boot — it is done.

## The last mile: a sector-scoped lean boot pack

A session **declares its sector** and boots from a **single lean pack** = { the binding invariants +
that sector's folio + its active plan + `current-state.md` ▶ Next action } — **skipping** the roadmap,
historical docs, and every other sector. Generate one pack per sector via the **existing agent-context
compiler** (`docs/agent/index.yml` → `docs/agent/generated/*.context.md`); the index already encodes
folio / binding-docs / source-roots per area, so this is *wiring*, not new infrastructure.

Pairs with **procedures→skills** (`procedures-to-skills-conversion-plan`, lane B1): moving ~25% of the
always-loaded CLAUDE.md into on-demand skills lowers the always-loaded floor for *every* model.

## Payoff

Unlocks the **separate Sonnet weekly bucket** for bounded, plan-driven sector work (most B-lane tasks),
and stops burning the all-models bucket on orientation — directly addressing the maintainer's recurring
limit shortage.

## Build note (next session)

B1-priority. **Done =** a **Sonnet** session can load a sector pack + complete a bounded sector task
**without compacting during orientation**. Check each pack's size against Sonnet's window; keep the
invariants subset truly minimal (the must-not-break rules only, not the whole CLAUDE.md).

**Also verify the file-ignore mechanism** (owner flagged 2026-06-19): confirm what Claude Code actually
honors — a `.claudeignore` (if supported), `.claude/settings.json` permission **deny-globs**, and/or
`.gitignore` — and use it to keep **tests, data, and generated files** out of context by default. **Do
not assume `.claudeignore` is read until verified against the live tool** (it may be a `.cursorignore`
lookalike, not a Claude Code feature); deny-globs in `settings.json` are the known-supported path.

→ relates `planning/procedures-to-skills-conversion-plan` · `.claude/rules/context-compiler.md` ·
`docs/agent/index.yml` · `repo-sector-map.md` · Q-0137.
