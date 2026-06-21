# Project Moon wiki as a bot knowledge domain — feasibility (2026-06-21)

> **Status:** `ideas` — owner-dropped product request (2026-06-21), captured as a **feasibility
> finding**. Not a plan, not approval. The scope fork is routed to the owner-designer in-session
> (§ "Open question — owner's call"). Source code + the binding contracts win over anything here.
> **Subsystem:** ai, btd6 *(proposes a second knowledge/grounding domain modeled on the BTD6 stack
> and consumed by the AI grounding path; it would eventually earn its own subsystem key).*

## The request

The owner relayed a request from a community member: have the **"Project Moon wiki" available in the
bot "in one area," the same way BTD6 data is available today.** Caveat from the owner: *"supposedly
it's a lot."*

"Project Moon" is the Korean studio behind a shared sci-fi universe ("the City") spanning three games
— **Lobotomy Corporation**, **Library of Ruina**, **Limbus Company** (the live-service gacha) — plus
webcomics/novels (Leviathan, Distortion Detective, Wonderlab).

## Verdict

**Achievable, and a genuinely good architectural fit — but a real build, not a drop-in.** The bot
already does exactly this shape of thing for one game (BTD6), and the *reusable* half of that work
(wiki ingestion + a generic fact store + AI grounding) transfers. The hard part is that the BTD6
knowledge stack is **bespoke to BTD6** (~12k+ lines of `btd6_*` services), and Project Moon's data is
**more fragmented and more prose-heavy** than BTD6's clean numeric game dump. So the right move is to
**generalize the BTD6 knowledge seam into a domain-agnostic "knowledge domain," with Project Moon as
its first second instance** — rather than copy-paste a parallel `projmoon_*` stack.

## What "available like BTD6" actually means (two layers)

BTD6 is not one feature — it's two, and which one the request wants changes the size a lot:

1. **AI Q&A grounding** (the headline). The natural-language stage detects BTD6 keywords
   (`utils/btd6/keywords.has_btd6_context`) → routes to `AITask.BTD6_ANSWER` →
   `btd6_context_service.from_intent()` renders **tagged, length-capped, provenance-labelled** grounding
   lines into the LLM prompt → `btd6_grounding_service` validates the answer is supported before it
   sends. This is "ask the bot a BTD6 question and it answers, grounded."
2. **Browsable structured lookups.** `/btd6 tower|hero|round|bloon|…` commands backed by committed JSON
   (`disbot/data/btd6/`, ~7 MB / 70 files) served through `btd6_data_service` (typed dataclasses,
   validation, caching), plus live event/leaderboard **facts** in Postgres (`btd6_facts`).

Data gets in two ways, and **both have a Project Moon analogue**:

- **Primary — a clean machine-readable dump:** `Btd6ModHelper/btd6-game-data` (~320 MB decrypted game
  JSON), parsed by `scripts/parse_gamedata.py` (4,434 lines) with **anchor validation** + **fidelity
  audits**. This obsessive numeric discipline exists because BTD6 data is exact game numbers.
- **Secondary — a wiki scraper:** `scripts/fetch_bloonswiki.py` pulls the BTD6 Fandom wiki via the
  **MediaWiki API** (`api.php`, `action=cargoquery` over the **Cargo** extension, `action=raw` for
  Scribunto modules). **This is the part that maps most directly to "ingest the Project Moon wiki."**

Refresh is a manual `workflow_dispatch` GitHub Action (`btd6-data-refresh.yml`): clone dump → overlay →
audit → open a reviewable PR. Copyable pattern for a frequently-updated game like Limbus.

## What maps cleanly vs. what's harder for Project Moon

**Maps cleanly (the encouraging half):**

- The **wiki-ingestion path already exists and transfers.** The Project Moon wikis run MediaWiki (and
  several expose Cargo), so the `fetch_bloonswiki.py` MediaWiki/Cargo/`action=raw` approach is
  conceptually reusable against `limbuscompany.wiki.gg` etc.
- The **fact store is already generic** in shape: `(fact_type, entity_kind, entity_key, body_json,
  confidence, version, provenance)`. Project Moon facts (`pm_identity`, `pm_ego`, `pm_abnormality`,
  `pm_story`, …) fit it with no schema change.
- The **grounding render pattern is generic**: tag + cap + provenance line. The AI consumes it
  domain-blind.
- **Multi-domain "context service" precedent already exists** — `ai_context_service`,
  `youtube_context_service`, and `btd6_context_service` show the grounding seam is meant for more than
  one domain.
- The **refresh-workflow pattern** (manual dispatch → overlay → audit → PR) is copyable for Limbus's
  ~2–3-week content cadence.

**Harder than BTD6 (the honest caveats):**

1. **No single canonical dump.** BTD6 had one clean source of truth. Project Moon's data is spread
   across wiki.gg (Limbus, Library of Ruina migrated off Fandom), `projectmoon.fandom.com` (lore for all
   works), `projectmoon.miraheze.org` ("Cogitopedia"), and community datamines
   (`limbus-datamines`, `retcons.github.io` story/identity logs, wiki.gg "Datamined Info" pages). We'd
   pick authoritative sources **per game**.
2. **Much of the value is prose/lore, not numeric tables.** BTD6's grounding discipline is built for
   exact numbers; reliably grounding *narrative* (characters, story, abnormalities) without
   hallucination is a harder quality problem and wants its own guardrails. This is the main risk.
3. **The stack is bespoke `btd6_*`.** A second domain is either (a) a parallel `projmoon_*` stack
   (faster, but doubles the maintenance surface) or (b) a **generalized knowledge-domain seam** with
   BTD6 + Project Moon both as instances (more up-front work, pays down the bespoke-ness — the
   "build the substrate" move this project prefers). **Recommend (b).**
4. **AI routing wiring.** Needs a Project Moon entity/keyword detector + a new `AITask`
   (`PROJMOON_ANSWER`) + a grounding path in `core/runtime/ai/natural_language_stage.py`.
5. **Volume + cadence.** It genuinely is "a lot," and Limbus updates constantly → the refresh workflow
   isn't optional.
6. **Licensing.** Wiki content is CC-BY-SA (Fandom) / wiki.gg varies. The BTD6 CSV README already shows
   the team is licensing-aware (*"do NOT copy/paste from the wiki… copying verbatim creates an
   attribution obligation"*). Same discipline: store **summarized/structured facts with provenance +
   attribution**, not verbatim wiki dumps. Worth an explicit owner nod.

## Recommended phasing (escalating fidelity)

- **Phase 1 (recommended start) — Limbus Company lore + wiki Q&A grounding.** Ingest the active
  `limbuscompany.wiki.gg` corpus into the (generalized) fact store; the bot answers grounded Project
  Moon questions in chat. Bounded to **one game** to keep grounding quality high. This is the truest
  match to "have the wiki available" and reuses the existing wiki-ingestion + grounding pattern.
- **Phase 2 — structured stat lookups.** Browsable `/pm identity|ego|enemy` commands + cards from
  datamine sources (BTD6-style typed data service).
- **Phase 3 — expand** to Library of Ruina + Lobotomy Corporation; calculators/parity if wanted.
- **Cross-cutting:** do Phase 1 *as* the first instance of a generalized knowledge-domain seam extracted
  from BTD6, so the second domain reduces (not duplicates) the bespoke surface.

## Open question — owner's call (routed in-session 2026-06-21)

The feasibility is settled (yes); the **scope is the owner-designer's decision** and sizes the build.
Asked in-session via the three options:

1. **Lore & wiki Q&A grounding** *(recommended)* — broadest coverage, lightest; start Limbus, expand.
2. **+ Structured stat lookups** — also browsable `/pm …` commands from datamines, Limbus first.
3. **Full BTD6-grade parity** across all three games (exact numbers + calculators) — largest build.

Until answered, this stays a capture; the answer promotes it to a `docs/planning/` plan for the chosen
scope.

## Related

`docs/subsystems/btd6.md` (the template subsystem) · `docs/subsystems/ai.md` (the grounding consumer) ·
`scripts/fetch_bloonswiki.py` / `scripts/parse_bloonswiki.py` (the reusable wiki-ingestion path) ·
`disbot/services/btd6_context_service.py` · `disbot/services/btd6_fact_store.py` ·
`disbot/core/runtime/ai/natural_language_stage.py` (routing integration point) ·
`.github/workflows/btd6-data-refresh.yml` (the refresh pattern) · ADR-006 (provenance/ownership).
