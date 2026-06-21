# 2026-06-21 — Project Moon: pre-build reconnaissance (data sources + seam contract)

> **Status:** `complete`

> Third deliverable of the Project Moon session (after #1238 feasibility, #1239 plan). The owner asked
> "anything else you can already find out and document before we start executing?" — so this is a
> pre-execution recon pass, docs-only, to make the first build slice turn-key.

## Arc

Two parallel research streams: (1) a web recon of the actual Limbus data sources, and (2) an Explore-agent
audit of the BTD6 knowledge stack's public API surface to define the generalised `KnowledgeDomain`
contract. Both produced findings that change the build, captured in a `reference` doc + folded back into
the plan.

## Findings (the decision-relevant ones)

- **✓ The Limbus wiki has no Cargo** (verified via `siteinfo` API) — Scribunto + DPL3 only. So
  `fetch_bloonswiki.py`'s `action=cargoquery` path does **not** transfer; the plan's §5 ingestion sketch
  was corrected.
- **✓ The real BTD6-dump analogue exists:** Limbus ships **StaticData** that the community dumps to JSON
  (Lethe modding framework; server reimplementations FurinaLC / limbus-server; `meatpnppet/limbus_data_analysis`;
  `bw1nd/limbus_helper`). So Project Moon has the **same two-source shape** as BTD6 — clean game dump for
  numbers + wiki for prose — the architecture fits *better* than first assumed; only the wiki mechanism differs.
- **Seam audit:** the fact store schema + provider abstraction are **already domain-agnostic** (reuse as-is);
  the grounding line *shape* + resolver matching logic are reusable; entity dataclasses, vocabulary, keyword
  detector, fixture renderers, and the `AITask` member are **per-domain**. **Do NOT generalise** BTD6's
  upgrade-path / crosspath / paragon-degree / mode-taxonomy code (leave in a `BTD6Domain`). PM resolver must
  be **Sinner-namespaced** (100+ Identities, repeating nicknames) — BTD6's flat alias-collision check won't scale.

## Shipped (docs-only)

- **`docs/planning/project-moon-prebuild-recon-2026-06-21.md`** (`reference`) — data-source matrix per
  data type, the `KnowledgeDomain` 6-pillar contract + reuse/keep/never-generalise split with file:line
  refs, a first-cut Limbus domain model, sources.
- Patched the plan: §5 ingestion corrected (StaticData-first, not Cargo), §6 Limbus source resolved, recon
  linked in Related.

Verification: `check_docs --strict` · `check_session_gate`.

## 📤 Run report

- **Did:** verified Limbus data sources (no-Cargo wiki; StaticData dump is the clean stat source) + audited
  the BTD6 seam into a concrete `KnowledgeDomain` contract; documented both · **Outcome:** shipped; Slice A
  ingestion design de-risked before any code
- **Run type:** `owner-directed · pre-build recon (docs-only)`
- **⚑ Owner decisions needed:** none new (the 3 plan §7 design Qs still stand for LoR/LobCorp phases)
- **⚑ Self-initiated:** none (owner asked for pre-execution research)
- **↪ Next:** build Slice A from the corrected design — StaticData identity JSON → `projmoon` data +
  `projmoon_context_service` + `AITask.PROJMOON_ANSWER` → Limbus lore-Q&A + `/pm identity`.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session (3rd) | 1 (docs-only recon) |
| Runtime (`disbot/`) code changed | 0 |
| Research streams | 2 (web data-source recon + BTD6 seam audit) |
| Plan corrections folded back | 2 (Cargo→StaticData ingestion; Limbus source resolved) |
