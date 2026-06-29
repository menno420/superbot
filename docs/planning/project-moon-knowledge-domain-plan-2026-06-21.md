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

> **▶ Ingestion approach corrected by the pre-build recon** (2026-06-21,
> [`project-moon-prebuild-recon-2026-06-21.md`](project-moon-prebuild-recon-2026-06-21.md)): the Limbus
> wiki **has no Cargo** (verified), so the source for *exact numbers* is the game's **StaticData dump**
> (the true BTD6-dump analogue), not a wiki scrape. The wiki (standard no-Cargo API) is for *prose/lore*.

> **▶ Progress (2026-06-25 dispatch run, PR #1453): Slice A PR 1 SHIPPED.** Built the standalone
> Limbus domain *minus the fragile exact-number ingest* — committed **structural/lore** facts
> (`disbot/data/projmoon/limbus/`: 12 Sinners · 7 Sins · 3 damage types · 5 E.G.O grades · status
> keywords, provenance-tagged), a typed `services/projmoon_data_service.py` (loader + resolver),
> `utils/projmoon/keywords.py` (`has_limbus_context`), and a browsable `!pm` / `/pm` surface
> (`views/projmoon/`, its own top-level **Project Moon** Help hub like BTD6). Read-only; **no AI
> hot-path change** (deliberate: the StaticData numbers + the `natural_language_stage` grounding wiring
> are PR 2, which wants prod creds / a runtime walk). **▶ Next = Slice A item 2 (the grounding path).**

> **▶ Progress (2026-06-25 dispatch run, PR #1456): Slice A lore-depth follow-on SHIPPED.** Each of the
> 12 Sinners now carries a provenanced **`literary_origin`** (`{work, author}` — the canonical literary
> source each Sinner is drawn from: Faust→Goethe, Outis→Homer's *Odyssey*, Gregor→Kafka, Rodion→
> Dostoevsky, …), validated by `projmoon_data_service`, exposed via a typed `sinner_origins()` accessor,
> and surfaced in the `!pm` detail card + a new **Origins** cross-reference embed (`!pm origins` + a
> browse-panel button). Read-only/offline, no AI hot-path change.

> **▶ Progress (2026-06-26 dispatch run, PR #1467): Slice A item 2 — the GROUNDING PATH — SHIPPED.**
> A message that looks like a Limbus question now routes to the new **`AITask.PROJMOON_ANSWER`**
> (`ai_task_router.classify` → `has_limbus_context`, checked after BTD6 / before video), and a thin
> **`services/projmoon_context_service.build()`** resolves the named Limbus entities + bounded roster
> queries into provenanced grounding fact lines that `natural_language_stage._gather_feature_facts`
> injects as `retrieved_facts` — the BTD6 grounding seam, mirrored. **Default-preserving:** only
> Limbus-detected messages change; the BTD6 path stays byte-identical (its faithfulness guard / refusal
> floor are unchanged and never fire for projmoon). Offline-unit-tested (27 tests: router priority,
> per-entity + roster grounding, ambiguous-bare-token exclusion, provenance survival, the fact cap, the
> `_gather_feature_facts` seam). **Deliberately deferred (documented in-module):** the prose-faithfulness
> *validation* guard (the §6 "hardest correctness risk") — this slice injects grounded facts but does
> **not** yet post-verify the reply against them. **▶ Next:** (a) the live **Q-0086 runtime walk** (owner —
> the gated AI stage now grounds Limbus; confirm a real Limbus Q&A grounds + reads well on both
> providers); (b) the projmoon **faithfulness guard** follow-up; (c) Slice A item 1 — the StaticData
> exact-number ingest; then **Slice B** — extract the shared `KnowledgeDomain` seam from BTD6 + Limbus.

> **▶ Progress (2026-06-26 dispatch run, PR #1469): Slice A follow-up (b) — the FAITHFULNESS GUARD —
> SHIPPED.** Closes the §6 "hardest correctness risk" deferred by PR #1467. New
> **`services/projmoon_grounding_service.py`** is the projmoon analogue of
> `btd6_grounding_service.validate_btd6_reply`: it reuses the domain-agnostic `utils.btd6.name_guard`
> matchers and the shared `GroundingResult` dataclass (so Slice B's seam folds them with no contract
> change), indexes the **distinctive** Limbus proper names (the 12 Sinners + the ZAYIN/TETH/WAW/ALEPH
> E.G.O grades) and **skips** the common-English categories (Sins / damage types / statuses) so ordinary
> prose never false-positives — mirroring BTD6's hero/boss-vs-generic discipline. **Names-only** (Limbus
> exact numbers aren't ingested yet — item c). Wired into `natural_language_stage` as a `PROJMOON_ANSWER`
> block parallel to the BTD6 one (reject → regenerate-once with a do-not-state constraint → floor to a
> deterministic, never-model-prose Limbus refusal). **Posture divergence from BTD6 (documented):** a
> verifier *exception* fails **open** (projmoon faithfulness is additive hardening, not a hard numeric
> safety floor); a genuine unsupported-name finding fails **closed**. Default-preserving (BTD6 / general
> paths byte-identical); offline-unit-tested (12 service tests + 4 NL-stage wiring tests). **▶ Next:**
> (a) the live **Q-0086 runtime walk** (owner); (c) Slice A item 1 — the StaticData exact-number ingest;
> then **Slice B** — extract the shared `KnowledgeDomain` seam from BTD6 + Limbus.

> **▶ Progress (2026-06-26 dispatch run, PR #1470): Slice B *prep* — the CROSS-DOMAIN OVER-ROUTE GUARD —
> SHIPPED.** The over-route harness flagged by PR #1453 / #1469's session ideas. `ai_task_router.classify`
> checks BTD6 then Limbus on the bare comment *"BTD6 keywords never collide with the distinctive Limbus
> tokens"* — asserted, never tested, and the two detectors don't even share match semantics
> (`has_btd6_context` is a substring scan; `has_limbus_context` is word-boundary). New
> **`tests/unit/runtime/ai/test_domain_routing_disjoint.py`** is a registry-driven guard pinning three
> properties (routing · token disjointness across every ordered domain pair · priority total-order) so the
> next reference domain (LoR / LobCorp) is a one-line `DOMAINS` registration, not a re-derivation from
> source. Paired with a durable **detector-curation recipe** in the [ai folio](../subsystems/ai.md)
> § "Adding a knowledge domain" (the "distinctive vs generic token" + cross-domain disjointness discipline
> that was re-derived from source twice). Offline, **no runtime behaviour change** — de-risks Slice B's
> seam extraction without touching the gated BTD6 hot path. **▶ Next unchanged:** (a) the live
> **Q-0086 runtime walk** (owner); (c) Slice A item 1 — StaticData numbers; then **Slice B** proper.

> **▶ Progress (2026-06-29 manual session, PR #1549): Slice A item 1 — the COMBAT-MECHANICS
> *rules* half — SHIPPED.** Owner-directed ("check how Project Moon is going and continue it"); a
> Project Moon community member's screenshot named the missing "majority" as **clashing · IDs and
> passives · speed · enemy stats and passives**. This ships the *stable, hand-authorable, correct*
> half: a new **`mechanic`** entity kind (`disbot/data/projmoon/limbus/mechanics.json`, 13 entries
> with a `category` group) covering the core combat **rules** — Clash · Coin (heads/Sanity) · Speed ·
> Sanity · Stagger · damage-resistance levels · Resonance · Skills & replacement · Defensive skills ·
> Identity (rarity 0/00/000) · Passives & support passives · E.G.O/Corrosion. Browsable
> (`!pm mechanic <name>` + a Mechanics button), and **grounded through the already-wired
> `projmoon_context_service.build()` seam** (per-entity match + a "combat mechanics" roster trigger +
> a `(combat mechanic — <group>)` body enrichment) — so a Limbus-routed question grounds the
> mechanic. **No change** to the router, the NL-stage wiring, the faithfulness guard (mechanics are
> common-word names, never indexed → no false refusals), or the BTD6 path. Routing keyword list
> **unchanged** on purpose: mechanic words ("clash"/"speed"/"sanity") are ordinary English, so — like
> the Sins — they ground via co-occurrence with a distinctive token, not by routing bare (the same
> over-route discipline). **Deliberately deferred (the numeric tail of item 1):** exact per-Identity /
> per-enemy **stat numbers** (HP, speed *values*, coin power) — those need the **StaticData** ingest
> lane; hand-committing them would risk ungrounded numbers (ADR-006). Offline-unit-tested (data,
> context, cog, grounding). **▶ Next:** (a) the live **Q-0086 runtime walk** (owner); (c-numbers) the
> StaticData exact-number ingest; then **Slice B** — extract the shared `KnowledgeDomain` seam.

**Slice A (next session, 2–3 PRs):**
1. **Ingestion:** a `scripts/fetch_pm_limbus.py` that parses the **StaticData identity JSON** (clean,
   bounded — Identities + Sinners + E.G.O index) into committed JSON under
   `disbot/data/projmoon/limbus/` with provenance, **plus** a thin lore pull from `limbuscompany.wiki.gg`
   via the standard MediaWiki API (`action=raw`/`parse` — *not* Cargo). See the recon doc §1 for the
   per-data-type source matrix.
2. **Grounding path:** a thin `projmoon_context_service` + `AITask.PROJMOON_ANSWER` + a
   `has_projmoon_context` detector wired into `core/runtime/ai/natural_language_stage.py`, reusing the
   tag/cap/provenance render and the answer-validation guard.
3. **One user surface:** lore/identity Q&A working end-to-end for Limbus, plus a minimal `/pm identity`
   lookup.

**Slice B (after Slice A proves the shape):** extract the `KnowledgeDomain` seam from BTD6 + Limbus
(Phase 0), then expand Limbus to full structured parity (Phase 1 tail).

## 6. Dependencies & risks (honest)

- **Source selection per game** — **Limbus is now resolved** by the pre-build recon (StaticData dump for
  numbers + wiki.gg no-Cargo API for prose; see the recon doc §1). LoR / LobCorp source choice across
  `*.wiki.gg`, `projectmoon.fandom.com` (lore), `projectmoon.miraheze.org` (Cogitopedia), and community
  datamines stays an open owner/design question (§7) for their phases.
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

[**pre-build recon**](project-moon-prebuild-recon-2026-06-21.md) (data sources + seam contract +
Limbus domain model) · [idea capture](../ideas/project-moon-wiki-knowledge-domain-2026-06-21.md) ·
router **Q-0192** · [btd6 folio](../subsystems/btd6.md) · [ai folio](../subsystems/ai.md) ·
[ai-btd6-answerability-roadmap](ai-btd6-answerability-roadmap-2026-06-09.md) · ADR-006
(`../decisions/006-btd6-data-provenance-ownership.md`).
