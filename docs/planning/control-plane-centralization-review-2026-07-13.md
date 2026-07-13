# Control-plane live review — what's still not centralized

> **Status:** `plan` — a live gap-analysis of the deployed control-plane, feeding the
> **websites lane** (routes as a manager ORDER). **Provenance:** owner ask, owner-live hub
> chat 2026-07-13 (PR #2070): *"it still seems like not everything is properly centralized
> on the website — thoroughly review this and tell me what could be made better."*
> **Evidence basis:** a live crawl 2026-07-13 ~12:40Z of
> `https://control-plane-production-abb0.up.railway.app/` (homepage + `/fleet` `/freshness`
> `/projects` `/prompts` `/queue` `/directory`), cross-referenced with the code architecture
> mapped in [`websites-fleet-data-plane-2026-07-13.md`](websites-fleet-data-plane-2026-07-13.md)
> (PR #2066). This doc is the **live confirmation** of that design plus three findings the
> design didn't name.

## TL;DR — the fleet has six different sizes depending on the page

This one table is the whole problem, and it is exactly what the owner is sensing:

| Page | "The fleet" is… | Source it derives from |
|---|---|---|
| **homepage** (readiness board) | **4 repos** | `app/config.py` `REPOS` — a hand-picked subset |
| **/prompts** | **9 seats** | fleet-manager `projects/` registry artifacts |
| **/projects** | **11 seats** | fleet-manager `projects/` dir listing |
| **/directory** | **15 service entries** | committed `web_presence.json` + probes |
| **/fleet** | **18 lanes** | fleet-manager `gen_roster.py` `LANES` literal |
| **/freshness** | **18 repos** | same roster, re-derived |

Six surfaces, six answers to "how big is the fleet?" — **not because the data disagrees,
but because every page has its own list.** That is the definition of not-centralized, and
it's why no single page feels like *the* source of truth. Everything below is a
consequence of this root cause.

## The findings

### 1 · One fleet, six source-of-truth lists (root cause)

`/fleet` and `/freshness` agree (18) because they share the roster; everything else drifts
off its own list. The homepage's 4-repo board is the worst offender — it silently watches
**4 of 18 lanes**. The fix is already designed (#2066 §2.1): a single **derived manifest**
(`lanes.json` × each repo's `substrate.config.json` × a kind table) that every page reads,
so the count is computed once. Until then, adding or renaming a seat means editing up to
five lists, and they will keep disagreeing.

### 2 · The homepage says "all quiet" while the fleet is not (false reassurance)

The landing page's headline — *"all quiet — no broken checks, deploy drift, or stale
heartbeats"* — is scoped to its 4 repos. Meanwhile `/fleet` reports **8 stale lanes + 10
outstanding orders**, and `/projects` flags **venture-lab LIVE-BUT-DARK with three
unexecuted orders**. An owner who trusts the homepage is told all-clear while a lane is
dark. This is the most dangerous symptom of finding 1: the summary you read first is blind
to most of the fleet. **Fix:** either the readiness board watches all lanes, or its
headline states its scope honestly (*"all quiet across the 4 core repos — see /fleet for
all 18"*). The honest-scope version is a one-line change and worth doing immediately.

### 3 · The Railway estate is doubled — and it's now visible on /directory

`/directory` shows two full, live copies of the review/botsite/dashboard trio:
`superbot-websites` (control-plane, review-…f027) **and** `reliable-grace`
(review-…fc91, botsite-…cfd7, dashboard-…a91b) — both HTTP 200. This is the known
`OQ-RAILWAY-PROJECT-SPLIT` drift hazard, but it has crossed from "hazard" to
"user-visible confusion": which review site is canonical? The EAP email links the
`reliable-grace` URLs; the control-plane itself lives in `superbot-websites`. Two live
copies of the same service is a centralization failure by definition. **Owner decision**
(the queue already parks it frozen until after the 07-14 EAP window — correct; then pick
one project and retire the other set).

### 4 · Seat names vs repo names, no crosswalk

`/projects` and `/prompts` speak in **seat names** (`superbot-world`, `superbot-2.0`,
`ideas-lab`, `self-improvement`, `game-lab`); `/fleet` and `/freshness` speak in **repo
names** (`superbot-mineverse`, `superbot-next`, `idea-engine`+`sim-lab`, `substrate-kit`,
`gba-homebrew`). The same entity wears a different name on different pages, with no visible
mapping — so "is superbot-world healthy?" can't be answered by moving between the projects
page and the fleet page. **Fix:** the derived manifest (finding 1) carries a `seat ↔
repo(s)` crosswalk, and every page shows both labels (a seat like Ideas Lab spans two
repos — the crosswalk must be one-to-many).

### 5 · Deploy state is blind (everything "unknown")

The homepage shows all four services' deploy state as **unknown**, with *"signals marked
unknown could not be fetched with current token"*; `/directory` had to HTTP-probe URLs to
learn anything. Deploy drift is a headline the homepage advertises but cannot actually
compute. **Fix:** wire the Railway deploy-state read (the estate detail already uses
`RAILWAY_TOKEN` for `/owner/environments`) into the public board, and the queued **B#49
read-PAT** lifts the anonymous 60-req/h API ceiling that starves the check-run/secret
signals.

### 6 · Why re-pasting the prompts still looks un-synced

The owner re-pasted every seat's ender + boot prompt, yet `/prompts` still shows **5 stale,
1 drift, 13 "not recorded"** against canonical. The reason is structural: the site compares
the canonical registry against a **recorded** deployment snapshot
(`telemetry/triggers-snapshot.json` / a deploy record), and **it cannot observe what you
paste into a Claude console** — no API exposes that. So a re-paste doesn't move the drift
row unless the *record* is also updated. "Not recorded" (13 of ~29) means those seats have
no deployment record at all, so they can never show "in sync." **Fix options, cheapest
first:** (a) treat "not recorded" honestly in the UI as *"deployment not tracked"* rather
than implying drift; (b) add a one-line owner/coordinator step that stamps *"pasted seat X
= vN on <date>"* into a small deploy-record file when a paste happens; (c) accept it as a
known blind spot and document it on the page. Without one of these, the drift row will keep
telling the owner his re-pastes "didn't take" when they did.

## What is already centralized well (fair credit)

- **/prompts** renders 29 artifacts live from **one** source (fleet-manager `main`) with
  per-seat version history, copy controls, and superseded-demotion — this page *is* the
  centralization pattern done right, and it's the model the other pages should follow.
- **/queue** genuinely dedupes two sources (every lane's `⚑ needs-owner` heartbeat asks +
  the manager's curated owner-queue) into one newest-first list with stable `OQ-` slugs —
  real consolidation.
- **/directory** is honest about absence (marks unrecorded URLs as "honest absence," probes
  live ones) rather than faking data — the right posture.
- **/fleet** + **/freshness** already share the roster (the two pages that agree) — proof
  the derived-manifest approach works when two surfaces read one list.

## The fix is mostly already designed

Findings 1, 4, 5 are precisely what the #2066 data-plane design addresses (derived
manifest, one fetch core, deploy-state wiring). This review adds three the design didn't
name: **finding 2** (homepage false-"all quiet" scope), **finding 3** (the doubled Railway
estate as live confusion), **finding 6** (the un-observable-paste drift gap). Fold these
into the #2066 build order.

## Prioritized recommendations

**Do now (cheap, high-value, agent-shippable):**
1. **Homepage honesty** (finding 2) — make the "all quiet" headline state its scope, or
   point to /fleet. One-line change; removes a real false-reassurance risk today.
2. **/prompts "not recorded" wording** (finding 6a) — stop implying drift where there's
   simply no record; label it "deployment not tracked."

**Ship as the #2066 build (P1–P2):**
3. The **derived manifest** → every page reads one fleet list (findings 1, 4). The homepage
   board becomes fleet-complete for free.
4. **Seat↔repo crosswalk** in the manifest; show both names everywhere (finding 4).

**Owner / token-gated:**
5. **B#49 read-PAT** → lifts the API ceiling feeding deploy/check/secret signals (finding 5).
6. **Railway estate de-dup** (finding 3) — after the 07-14 EAP window; pick one project,
   retire the parallel copy.
7. **Deploy-record step** (finding 6b) if the owner wants the prompt drift row to reflect
   re-pastes.

The single most valuable one is #3 (the manifest): it collapses the six-sizes problem at
the root, and #1/#2 are honest stopgaps until it lands.
