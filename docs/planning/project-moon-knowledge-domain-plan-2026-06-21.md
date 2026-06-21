# Project Moon knowledge domain — full-parity program plan (2026-06-21)

> **Status:** `plan` — promoted from
> [`ideas/project-moon-wiki-knowledge-domain-2026-06-21.md`](../ideas/project-moon-wiki-knowledge-domain-2026-06-21.md)
> by the owner's in-session scope decision **Q-0192 ("full parity, all games")**. **Owner-directed.**
> This is a **PROGRAM** (multi-PR, multi-session), not a 2–3-PR plan: it fixes the end state, the
> foundation, and the **first buildable slice**; later phases are sketched, not fully specified. Source
> code + the binding contracts (architecture / ownership / runtime_contracts / ADR-006) win over this
> file. **Subsystem:** btd6, ai.

## 1. The goal (owner decision Q-0192)

**Full BTD6-grade parity for the entire Project Moon universe** — all three games (**Lobotomy
Corporation**, **Library of Ruina**, **Limbus Company**) plus the shared "City" lore: **AI Q&A
grounding _and_ browsable structured lookups _and_ calculators**, every major entity, exact numbers
where they exist, all "in one area." The owner picked the maximal of the three scope options
(`AskUserQuestion`, 2026-06-21).

This is the north-star. The plan below makes it **buildable in value-shipping slices** — full parity is
the destination, not the first PR.

## 2. Why it is a program, not a single plan

- The existing BTD6 knowledge stack is **~12k+ lines of bespoke `btd6_*`** (data service, context
  service, fact store, grounding, resolver, vocabulary, knowledge APIs, cogs, views, db, settings).
- "Full parity × 3 games + lore" is a multi-month build with real per-game data-sourcing work.
- So we **sequence**: each phase ships a usable increment; nothing blocks on "all of it."

## 3. Architecture decision — generalise the seam (not a parallel stack)

**Decision (agent's engineering call, 2026-06-21):** extract a **domain-agnostic `KnowledgeDomain`
seam** from the BTD6 stack rather than copy a parallel `projmoon_*` stack. A `KnowledgeDomain` bundles:

| Capability | BTD6 today | Generalised |
|---|---|---|
| Committed structured data + typed service | `btd6_data_service` | `KnowledgeDomain.data` |
| Fact store (live/dynamic) | `btd6_fact_store` (already generic schema) | shared, namespaced by domain |
| Entity resolver + vocabulary | `btd6_resolver_service` / `_vocabulary` | per-domain vocabulary |
| Grounding renderer (tag/cap/provenance) | `btd6_context_service` (already ~generic) | shared renderer |
| AI task + keyword detector | `AITask.BTD6_ANSWER` + `has_btd6_context` | per-domain task + detector |
| Refresh workflow | `btd6-data-refresh.yml` | per-domain copy |

BTD6 becomes `KnowledgeDomain` **instance #0**; the three Project Moon games are instances #1–#3.
**Rationale:** a parallel copy doubles ~12k lines of maintenance per game; generalising pays the
bespoke-ness down so each future reference domain is a *registration*. **Hard constraint:** the
generalisation must **not regress BTD6's groundedness / absence-claim guards** (ADR-006,
`btd6-derived-value-groundedness-finding.md`) — BTD6 behaviour stays byte-identical through the refactor
(golden tests).

## 4. Phasing (sequenced; each ships value)

- **Phase 0 — Foundation: the `KnowledgeDomain` seam.** Refactor BTD6 to instance #0, **no behaviour
  change**. Risky runtime refactor of gated code → focused, **runtime-verified** session(s), small PRs.
- **Phase 1 — Limbus Company** (active game, most demand): wiki ingestion + lore Q&A grounding, then
  structured Identity / E.G.O / enemy lookups + cards + a `/pm` surface. Proves the seam end-to-end.
- **Phase 2 — Library of Ruina:** combat/key pages, Abnormalities, story.
- **Phase 3 — Lobotomy Corporation:** Abnormalities (lore + mechanics), departments/agents.
- **Phase 4 — Cross-game lore + calculators + parity polish** (the "full parity" tail).

## 5. First buildable slice — **proof-first, not seam-first** (recommended order)

Do **not** open with the BTD6 refactor. Build a **minimal standalone Limbus domain** as a vertical
proof, then extract the shared seam once two concrete examples (BTD6 + Limbus) exist — the rule-of-three
argument: generalising from a single example tends to produce the wrong abstraction.

**Slice A (next session, 2–3 PRs):**
1. **Ingestion:** a `scripts/fetch_pm_limbus.py` modelled on `fetch_bloonswiki.py` (MediaWiki API /
   Cargo / `action=raw`) pulling a bounded first cut from `limbuscompany.wiki.gg` (Identities + Sinners
   + E.G.O index), writing committed JSON under `disbot/data/projmoon/limbus/` with provenance.
2. **Grounding path:** a thin `projmoon_context_service` + `AITask.PROJMOON_ANSWER` + a
   `has_projmoon_context` detector wired into `core/runtime/ai/natural_language_stage.py`, reusing the
   tag/cap/provenance render and the answer-validation guard.
3. **One user surface:** lore/identity Q&A working end-to-end for Limbus, plus a minimal `/pm identity`
   lookup.

**Slice B (after Slice A proves the shape):** extract the `KnowledgeDomain` seam from BTD6 + Limbus
(Phase 0), then expand Limbus to full structured parity (Phase 1 tail).

## 6. Dependencies & risks (honest)

- **Source selection per game** — Project Moon data is fragmented across `*.wiki.gg` (Limbus / LoR
  migrated off Fandom), `projectmoon.fandom.com` (lore), `projectmoon.miraheze.org` (Cogitopedia), and
  community datamines (`limbus-datamines`, `retcons.github.io`). *Which sources are authoritative* is an
  open owner/design question (§7).
- **Licensing** — wiki content is CC-BY-SA (Fandom) / varies (wiki.gg). Store **summarised / structured
  facts with provenance + attribution**, not verbatim dumps (the BTD6 CSV README already sets this norm).
- **Prose-grounding quality** — lore/story is narrative, not numbers; grounding it without hallucination
  is the hardest correctness risk and wants explicit guards.
- **BTD6 regression** — the Phase-0 refactor touches gated, groundedness-critical runtime; golden parity
  is mandatory.
- **Live-service cadence** — Limbus ships content every ~2–3 weeks → a per-domain refresh workflow.

## 7. Open design questions routed to the owner (Q-0192 follow-ups; non-blocking for Slice A)

1. **Authoritative source per game** — prefer `wiki.gg` (active, community-run) over Fandom, and use
   datamines for exact numbers? (Default assumed for Slice A: `limbuscompany.wiki.gg`.)
2. **Lore depth** — full story-text Q&A (spoiler surface), or mechanics + character/abnormality
   summaries only?
3. **Command surface** — one unified `/pm` hub, or per-game (`/limbus`, `/ruina`, `/lobcorp`)?

These refine later phases; Slice A proceeds on the defaults above.

## 8. House-style anchors (so an executor builds it cold)

- Ingestion: `scripts/fetch_bloonswiki.py` + `scripts/parse_bloonswiki.py` (MediaWiki/Cargo pattern).
- Data service shape: `disbot/services/btd6_data_service.py`; committed data: `disbot/data/btd6/`.
- Grounding: `disbot/services/btd6_context_service.py`, `disbot/services/btd6_grounding_service.py`,
  `disbot/services/btd6_fact_store.py`.
- AI routing integration point: `disbot/core/runtime/ai/natural_language_stage.py`,
  `disbot/core/runtime/ai/contracts.py` (`AITask`), `disbot/utils/btd6/keywords.py`.
- Refresh workflow: `.github/workflows/btd6-data-refresh.yml`.
- Pre-edit (every `disbot/` file): `python3.10 scripts/context_map.py <file>` +
  `check_architecture.py --mode strict`. Mutation/grounding rules: ADR-006, `docs/ownership.md`.

## Related

[idea capture](../ideas/project-moon-wiki-knowledge-domain-2026-06-21.md) · router **Q-0192** ·
[btd6 folio](../subsystems/btd6.md) · [ai folio](../subsystems/ai.md) ·
[ai-btd6-answerability-roadmap](ai-btd6-answerability-roadmap-2026-06-09.md) · ADR-006
(`../decisions/006-btd6-data-provenance-ownership.md`).
