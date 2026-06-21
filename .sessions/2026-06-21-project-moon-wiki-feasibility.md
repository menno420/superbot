# 2026-06-21 — Project Moon wiki feasibility (can we serve it like BTD6 data?)

> **Status:** `complete`

## Arc

Owner relayed a community request: have the **"Project Moon wiki" available in one area, the way BTD6
data is available** ("supposedly it's a lot"). This is a **feasibility question**, so the deliverable is
an honest assessment + a durable capture, not an implementation. Mapped the BTD6 knowledge stack
end-to-end (Explore agent), checked for any existing multi-domain/knowledge generalization, confirmed
the Project Moon data landscape via web, and routed the scope fork to the owner.

## Findings

- **BTD6 = two layers fed two ways.** (1) AI Q&A grounding: `natural_language_stage` keyword-detects →
  `AITask.BTD6_ANSWER` → `btd6_context_service.from_intent()` renders tagged/capped/provenance lines →
  `btd6_grounding_service` validates. (2) Browsable `/btd6` lookups over committed JSON
  (`disbot/data/btd6/`, ~7 MB) via `btd6_data_service` + live `btd6_facts` in Postgres. Data in via a
  clean machine dump (`parse_gamedata.py`, anchor-validated) **and** a wiki scraper
  (`fetch_bloonswiki.py`, MediaWiki `api.php`/Cargo/`action=raw`).
- **The reusable half transfers.** The wiki-ingestion path, the generic fact-store schema
  `(fact_type, entity_kind, entity_key, body_json, provenance)`, the grounding render, the
  manual-dispatch refresh workflow, and the multi-"context service" precedent
  (`ai_`/`youtube_`/`btd6_context_service`) all carry over.
- **The hard part is bespoke-ness + data shape.** The stack is ~12k+ lines of `btd6_*` with no generic
  knowledge-domain abstraction; Project Moon's sources are fragmented (wiki.gg migration off Fandom +
  `projectmoon.fandom.com` lore + Miraheze Cogitopedia + community datamines) and **prose-heavy** (lore),
  which is harder to ground than exact numbers. Recommend **generalizing the seam**, Project Moon as the
  first second instance.
- **Confirmed "it's a lot":** 3 games + webtoons/novels, Limbus is live-service (~2–3-week cadence).
- **No prior capture** — grep for moon/limbus/lobotomy/ruina was empty; this is genuinely new.

## Shipped (docs-only, no runtime code)

- `docs/ideas/project-moon-wiki-knowledge-domain-2026-06-21.md` — the feasibility finding (verdict,
  two-layer BTD6 mapping, maps-cleanly vs harder, data-source landscape, licensing, recommended phasing,
  routed scope question).
- Indexed it at the top of `docs/ideas/README.md`; claimed + cleared `docs/owner/active-work.md`.

Verification: `check_docs --strict` (reachability) · `check_quality --check-only`.

## ⚑ Self-initiated (Q-0172)

None beyond the owner-dropped task itself. Capturing the research as a routed idea doc (rather than
leaving it in chat) is the mandated idea-capture, not a self-initiated build. No idea was promoted to a
plan — the scope fork is the owner's to answer first.

## 💡 Session idea (Q-0089)

**Extract a domain-agnostic "knowledge domain" seam from the BTD6 stack** (`KnowledgeDomain` =
{ wiki-ingestion source(s), fact namespace, resolver vocabulary, grounding renderer, AI task }), so a
new reference domain (Project Moon, a future game, a rules wiki) is a *registration*, not a parallel
`*_*` copy of ~12k lines. The forcing function is this very request; the precedent is that
`ai_`/`youtube_`/`btd6_context_service` already prove the grounding seam is multi-domain in spirit. Lane:
ai/architecture. (Captured inside the feasibility doc as the recommended cross-cutting approach.)

## ⟲ Previous-session review (Q-0102)

The `website-count-and-pin-fixes` session modelled the right instinct for *this* one: it shipped a
**slimmed, honest** deliverable (deferred to merged work, kept only net-new value) instead of forcing
scope. Applied here by **not** over-building — a feasibility question gets a feasibility finding +
routed decision, not a speculative `projmoon_*` stack the owner hasn't scoped. **System improvement:**
there is no "knowledge domain" entry in the orientation route — adding BTD6 to `AGENT_ORIENTATION.md` as
the *template* for "add a new reference/grounding domain" would route a future build session directly;
filed as the session idea above rather than edited blind into orientation this run.

## 📤 Run report

- **Did:** assessed feasibility of serving the Project Moon wiki like BTD6 data; captured the finding as
  a routed idea + indexed it · **Outcome:** answered (feasible) + routed scope fork to owner
- **Run type:** `owner-directed · research/feasibility (docs-only)`
- **⚑ Owner decisions needed:** **yes** — scope fork (lore Q&A grounding / + structured lookups / full
  parity), asked in-session via `AskUserQuestion`. Answer promotes the idea → a `docs/planning/` plan.
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (idea capture is mandated, not self-initiated build)
- **↪ Next:** on the owner's scope pick, promote the idea → a scoped plan (Phase 1 = Limbus lore Q&A
  grounding, built on a generalized knowledge-domain seam).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (docs-only feasibility capture) |
| Runtime (`disbot/`) code changed | 0 |
| Docs added | 1 idea doc + index entry |
| New ideas contributed | 1 (generalized knowledge-domain seam) |
| Owner decisions routed | 1 (Project Moon scope fork) |
