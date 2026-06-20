# 2026-06-20 — Creature roster sizing + music-bot legal findings (documentation)

> **Status:** `complete`

## Arc

Continuation of the Pokétwo / creature-game + music lane. In conversation the owner asked four
things and then said *"document all the useful findings of today"*:

1. *"How many creatures should we use? How many does Pokétwo use? What kind?"*
2. *"How is it possible that Pokétwo can use the original names?"*
3. *"What happened to the music bots and why weren't they allowed?"*
4. *"How would we create a music bot while staying within the rules?"*

This session routes the useful findings into their durable homes. **Docs only — no `disbot/`
runtime code.**

## Shipped (PR #1185, docs only)

- **Creature design doc §1** — *why Pokétwo "can" use real names*: **survivorship, not permission**
  (no license; selective enforcement economics; too-small-to-bother, strikeable at any time). States
  the load-bearing principle: **growth/visibility is the enforcement trigger; publish-safe = a
  design that doesn't depend on staying invisible** — cross-linked to the music decision.
- **Creature design doc §2 + new §2a** — roster sizing: Pokétwo ~1,000+ real species (+ forms +
  shinies); ours = **sim-core 12 → v1 launch ~30–40 → growth in waves**, with a **data-driven JSON
  catalog** (towers/fish-roster pattern) + **text/emoji-first art** so a bigger roster is cheap and
  every creature is sim-validated before it ships.
- **Q-0187** — added sub-decision **(d) roster size** (the tiered/data-driven model, recommended).
- **Voice/music decision pack — new §1a** — the concrete **L2 compliant-source menu** (royalty-free
  catalogs · Spotify-Connect remote · preview clips · file jukebox · podcast RSS) + a
  **cost-per-lane table** + the **royalty-free-radio + Spotify-Connect sweet spot** recommendation;
  wired into §6 decision-#2 (narrows the open L1/L2/L3 fork to "pick a lane"). Enriched the §1
  history (Groovy + Rythm Sept-2021 shutdowns, the ToS-not-just-copyright cause, the scale trigger).

Verification: `check_docs --strict` ✓ · `check_plan_homing` ✓ (39/39) · `check_quality --check-only`
✓ (the 3 `edit_in_place` WARNs are the pre-existing `views/ai/` AI-nav findings, untouched here).

## Decisions made alone

None binding — all findings are *recommendations routed to the owner* (Q-0187d roster size; Q-0041
music legal-lane menu). Editorial choices only (where each finding's durable home is). Reversible.

## Flagged for maintainer

- **Q-0187(d)** — confirm the tiered/data-driven roster model (sim-core 12 → v1 ~30–40 → waves).
- **Q-0041 decision #2** — the music legal lane is now a concrete menu; the agent recommendation is
  **royalty-free radio + Spotify-Connect remote** (low-cost, publish-safe).

## 💡 Session idea (Q-0089)

**A one-page `docs/research/ip-and-tos-safety.md` "publish-safe checklist" for any feature that
wraps a third-party service or IP.** Today the same principle — *growth/visibility is the
enforcement trigger; don't depend on invisibility* — independently governed two unrelated decisions
(creature names, music sourcing), and each doc re-derived it from scratch. A tiny shared checklist
("does survival depend on staying small/unpromoted? does it breach a ToS/copyright? is there a
licensed/original alternative?") would let the *next* such feature (e.g. a future API integration)
get the answer in one read instead of re-litigating the music-bot history each time. Lane =
research/docs. (Captured, not built this run — dedup-checked `docs/research/`:
`external-systems-watchlist.md` is agent-workflow-focused, not this product/legal axis.)

## ⟲ Previous-session review (Q-0102)

The previous run (#1183, the creature sim + design) did the **hard part right**: it built a runnable
simulator that *proved* playability and surfaced the level-normalization rule before any `disbot/`
code — exactly the balance-before-build discipline. **What it left on the table:** it fixed the
roster at "12 for v1" without distinguishing *balance-core* from *launch collection* size — so when
the owner asked "how many creatures?", the doc had no answer and this session had to add §2a. The
lesson: a design doc that picks a number should say **what the number is for** (validation vs.
launch vs. growth), because the next person will ask. **System improvement:** the
balance-before-build idea (#1183's Q-0089) is stronger if it's explicit that the *sim roster* and
the *launch roster* are different artifacts — the sim validates a small representative set, but the
plan must also name the launch-scale target and how it grows. Folded that distinction into §2a so
the convention is concrete, not implied.

## 📤 Run report

- **Did:** documented the day's creature-roster + music-legal findings into their durable homes ·
  **Outcome:** shipped (docs only)
- **Shipped:** #1185 — creature design §1/§2/§2a + Q-0187(d) + voice/music §1a menu & cost table
- **Run type:** `manual · owner-task (document findings)`
- **⚑ Owner decisions needed:** Q-0187(d) roster model · Q-0041 #2 music legal lane (menu provided)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (owner-directed: "document all the useful findings of today")
- **↪ Next:** build the **~30–40 original creature JSON catalog** + sim-validate it (the named §2a
  next design step), then the catch half (Lane A / Q-0186); music stays gated on Q-0041 #2.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (#1185, docs only, auto-merge on green) |
| Runtime (`disbot/`) code changed | 0 |
| Docs updated | 3 (creature design+sim plan · voice/music pack · question router) |
| Findings documented | 5 (roster size · Pokétwo-name survivorship · music history · legal-music menu · the shared publish-safe principle) |
| New owner sub-decisions routed | 1 (Q-0187d) + 1 narrowed (Q-0041 #2) |
| CI-red rounds | 1 (by-design born-red session gate only) |
| New ideas contributed | 1 (`ip-and-tos-safety.md` publish-safe checklist) |
