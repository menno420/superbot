# Fleet consolidation + next-round dispatch blueprint — 2026-07-11

> **Status:** `plan` — owner-directed. Encodes the four finalized decisions (AskUserQuestion,
> 2026-07-11) and turns them into each project's fate + new instructions + the cutover
> threshold. **To be confirmed by the projects' wrap-up replies** (the
> [archive-prep prompt](../owner/dispatch-prompts-2026-07-11.md) — each project reports
> whether it's idle/waiting/blocked, which confirms the merges below). Companion to the
> [review](fleet-review-2026-07-11.md), [strategy synthesis](fleet-strategy-synthesis-2026-07-11.md),
> and [centralization plan](fleet-centralization-plan-2026-07-11.md).
>
> **Repos vs Projects:** we consolidate **Projects** (the claude.ai dispatch seats), NOT
> repos. Code stays in its repo; a consolidated Project owns *prioritization + dispatch +
> release* across its repos (memo rule: "merge prioritization and release ownership, not code
> prematurely").

## 1. The four finalized decisions (owner, 2026-07-11)

1. **Next-round primary objective = first external revenue.** The $29 Stripe Webhook Test Kit
   is the one-week flagship, run as an **Owner Launch Hour** (one pre-filled atomic packet).
2. **Core 6 → 5:** merge **idea-engine + sim-lab** into one **Ideation→Evidence** seat
   (generate→verify split kept internal for anti-bias; kills the idea→sim inter-project wait).
3. **All games → one Games Project**, one flagship at a time. **Flagship = the Mining
   browsergame (superbot-mineverse).**
4. **superbot-next cutover = a concrete threshold** (defined in §4), not a by-feel call.

## 2. Fate of every current lane (the leaner fleet)

| Current lane | Fate | Notes |
|---|---|---|
| **superbot** (prod bot / oracle) | **KEEP — hub** | Freeze discretionary expansion; production-critical fixes only. Coordinated with superbot-next by the SuperBot hub Project. |
| **superbot-next** (rebuild) | **KEEP — Builder core** | Cutover threshold now defined (§4). Fix the verified money-races first (in-flight via Sonnet-5). |
| **substrate-kit** | **KEEP — core foundation** | **Freeze feature growth; measure adopter outcomes** (memo consensus). Cut the pending patch release (gate fix). |
| **fleet-manager** | **KEEP — Manager core** | Custodian-primary; build the centralization (typed-state model, §centralization plan). |
| **venture-lab** | **KEEP — Revenue core (next-round PRIMARY)** | Runs the Owner Launch Hour. Fail-open already fixed (#49). |
| **websites** | **KEEP — control-plane** | Home of the **Owner Launch Console** + the **Fleet Arcade** portal (next batch). |
| **idea-engine** | **MERGE → Ideation→Evidence** | With sim-lab, one Project, WIP-capped. |
| **sim-lab** | **MERGE → Ideation→Evidence** | With idea-engine. Ends its "idle-waiting-on-idea-engine" state (the wait you named). |
| **superbot-games** | **MERGE → Games Project** | World/fishing/exploration engines; backlog under the one Games Project. |
| **superbot-idle** | **MERGE → Games Project** | Idle engine; un-park PLUG-001 (contract exists). Not the first flagship. |
| **superbot-mineverse** | **MERGE → Games Project — FLAGSHIP** | Fix CSRF + provision the 6 env vars, then live. Also the plugin-contract proving ground. |
| **gba-homebrew** | **MERGE → Games Project (Retro studio)** | Ship the Lumen Drift Release regardless (free win). Low-maintenance. |
| **pokemon-mod-lab** | **MERGE → Games Project (Retro studio)** | PRIVATE, playtest-gated; never public. |
| **product-forge** | **ON-DEMAND** (not a standing seat) | Incubator invoked when an approved product needs building; graduate to its own repo only on independent users/cadence. |
| **trading-strategy** | **KEEP — PARKED** | Scheduled grading only (next ~07-17); not a continuous wake. |
| **codetool-lab ×3** | **ARCHIVE** | Wound-down finished CLIs; make read-only. A few pending tag/Release clicks first. |
| **superbot-plugin-hello** | **SEED** (one owner word) → then the Plugin Activation exemplar | Unblocks the idle/games plugin work. |

**Result:** ~14 active dispatch seats → **7 standing** (SuperBot hub · substrate-kit ·
fleet-manager · Ideation→Evidence · venture-lab · Games · websites) **+ parked/on-demand**
(trading scheduled · product-forge on-demand · codetool-labs archived). The two problems you
named are directly resolved: the idea→sim wait (merged) and the scattered game seats with no
single launch target (one Games Project, one flagship).

## 3. New one-line mission per standing Project (for the next-round founding prompts)

- **SuperBot hub** — keep prod live + drive superbot-next to the §4 cutover threshold; freeze old-bot discretionary work.
- **substrate-kit** — *freeze features; measure adopter outcomes* (does adoption reduce owner-steering / false claims / time-to-ship?); ship the gate patch release.
- **fleet-manager** — custodian-primary: build the typed-state single-source-of-truth (freshness gate → generated owner-queue → cross-repo index); run the consolidation relay.
- **Ideation→Evidence** — one funnel, WIP-capped: generate ideas → verify with sims → route build-worthy ones with evidence; internal generate/verify split; no unbounded backlog.
- **venture-lab** — **first external revenue**: fix-then-publish the test-kit, one real outside purchase, then measure visit→checkout→purchase. Owner Launch Hour is the vehicle.
- **Games** — one Project, one flagship (**mineverse**): get it live (CSRF fix + env vars), ship the Lumen Drift Release, hold idle/world/retro as sequenced backlog; shared release ownership; prove the plugin contract with one real plugin.
- **websites** — build the **Owner Launch Console** (turn owner-actions into a preflighted, auto-verified lifecycle) + the **Fleet Arcade** front door for the games.

## 4. superbot-next cutover threshold (decision 4, concrete)

Cut over from `superbot` to `superbot-next` when **all** hold, in order:

1. **All 49 subsystems ported** at golden parity (12 remain).
2. **Parity gate green *with* the false-green fix landed** (F-003 — `run_gate` asserts
   replayed-count == golden-count per ported subsystem). A green gate only counts once it
   can't silently drop a golden.
3. **The wallet-race fixes landed + concurrency-tested** (F-001/F-002 + the farm/mining
   same-class sites from Codex #206) — no money path double-settles under a race.
4. **One live-drive pass** on a real test guild (the AI + money + setup surfaces exercised).
5. **A 7-day shadow run** — both bots live, behavior compared, zero parity regressions
   (reuses the rebuild plan's shadow-first / N=7d rollback valve).
6. Then **CUT-3 token swap** (owner-gated destructive step) — the reversible reverse-import
   valve stays open for the rollback window.

When 1–5 are green, the cutover is *mechanical* (owner does CUT-3); no by-feel call, no
permanent dual maintenance.

## 5. Sequencing (the order everything happens)

1. **Now — parallel:** the wrap-up/archive-prep prompt goes to every project; they close out
   + report (idle/waiting/blocked). *(This confirms the §2 merges.)*
2. **Now — done:** the four decisions finalized (§1).
3. **On wrap-up replies:** confirm §2 (any surprise "I still have clear work" adjusts a merge);
   then dispatch the leaner next round with the §3 missions + the [permissions
   block](../owner/dispatch-prompts-2026-07-11.md) baked in.
4. **Next round, revenue-first:** venture-lab fix-then-publish (Owner Launch Hour) is slice 1;
   the four critical fixes are the admission gate (3 of 4 already done — only mineverse CSRF
   remains before the Games flagship goes live).

## 6. What the wrap-up replies confirm (expected)

- **sim-lab** reports idle-waiting-on-idea-engine → confirms the Ideation→Evidence merge.
- **superbot-idle / superbot-games** report blocked-on-plugin-contract (which exists) →
  confirms un-park + the Games merge.
- **product-forge** reports waiting-on-a-superbot-read-API → confirms on-demand.
- **mineverse** reports blocked-on-owner-secrets + the CSRF fix → confirms flagship sequencing.
- Any project that reports **clear, independent, ongoing work** is a signal to *not* fold it —
  reconcile against this plan before dispatching.
