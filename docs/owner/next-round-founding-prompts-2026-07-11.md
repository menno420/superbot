# Next-round founding-prompt kit — 2026-07-11 (verified + improved + consolidated)

> **Status:** `owner-guidance` — verifies every current project prompt/instruction, folds
> the next-batch improvements, keeps all existing missions, and adds NEW instructions for the
> two consolidated Projects. **Edit-registry-first:** the canonical prompts live in
> `fleet-manager/projects/<repo>/{instructions,coordinator-prompt,failsafe-prompt}.md` +
> `projects/UNIVERSAL.md` — the **manager is that registry's only writer**, so this file is a
> reviewable proposal the manager applies (I did not touch the registry, to avoid colliding
> with the live fleet-manager lane). Encodes the four finalized decisions
> ([consolidation blueprint](../planning/fleet-consolidation-and-next-round-2026-07-11.md)).

## 1. Verification — what exists (all present; mostly current)

**Registry** (`fleet-manager/projects/`, 19 dirs + `UNIVERSAL.md` v4): each Project carries
`instructions.md` (pasted full as Custom Instructions, ≤7,500 chars), `coordinator-prompt.md`
(the loop), `failsafe-prompt.md` (cron). The instructions are **mature and already carry most
workarounds** — merge-wall (auto-merge-enabler canonical path + park-READY-green fallback,
never self-REST-merge), deny-wins, all-checks-completed, token-budget (~3 CI polls), workers
in fresh clones, timestamps-from-`date -u`, Q-0120 verify-against-tree, control-bus
single-writer, born-red cards. **Nothing to rescue; the base is good.**

**Founding packages** (`superbot/docs/planning/round3-founding-package-*.md`, 10): identical
5-part skeleton (§0 owner pre-clicks → §1 Custom Instructions → §2 coordinator brief → §3
environment → §4 boot verification). The 4 core-seat packages + product-forge carry SUPERSEDED
banners (canonical copies now in the registry, PR #39); trading + the 4 games packages are
still `plan`-stage.

**The one structural fact this consolidation changes:** games are **currently 4 separate
Projects** — World (`superbot-games`), Idle (`superbot-idle`), Retro (`gba-homebrew` +
`pokemon-mod-lab`), Mining-Web (`superbot-mineverse`) — per Q-0267 + Q-0259 r.5. The owner's
2026-07-11 decision **collapses them to ONE Games Project (flagship = mineverse)**, which
supersedes Q-0267/Q-0259-r.5's per-project split. Likewise idea-engine (core seat) + sim-lab
(core seat) merge into one Ideation→Evidence seat (supersedes their separate-seat status).

**Verification result (full registry cross-check, 2026-07-11):**
- **The `instructions.md` are healthy.** All 15 live ones are **v2 (v3 for superbot-games),
  dated 2026-07-11, and every one carries the canonical Permissions block verbatim** (the
  ORDER-017 / UNIVERSAL-v4 fold is fully applied — no old wording anywhere). Bodies are
  internally consistent. **This is the good news: the pasted Custom Instructions are current.**
- **The drift is concentrated in the COMPANION prompts.** Every `coordinator-prompt.md` +
  `failsafe-prompt.md` is still **v1 · 2026-07-10 — one revision behind its v2 instructions**,
  and several carry stale facts: **trading-strategy** coord says "PR #37 awaiting owner merge"
  (it's **merged**); **fleet-manager** coord points at a trigger id its own failsafe says was
  **deleted**; **venture-lab** coord/failsafe are entirely 2026-07-10 boot-state (frozen
  clicks, "not armed", stale heartbeat); **websites** + **product-forge** self-flag "v2 not
  deployed / re-paste owed" and "deployed trigger ≠ canonical block"; **substrate-kit**'s live
  wake trigger carries pre-Q-0265 wording (re-arm owed). → **Next-round fix (§3):** re-sync
  every v1 coordinator/failsafe companion to its v2 instructions + fold the §2 rider.
- **Cross-lane fact conflict to reconcile:** the auto-merge-enabler-presence claim disagrees
  across the game seats — `superbot-games`/`superbot-idle` say "NO enabler" while
  `superbot-mineverse` says "enabler IS on main" (all "verified 2026-07-11"). Different repos,
  so possibly all true, but the same-day divergence merits one reconciliation check (it drives
  the merge-landing path). *(This is exactly the "release-operator" gap the reviews flagged.)*
- **codetool ×3 (archive):** `owner-queue.md` mislabels the unreleased-tag click — opus4.8's
  (mdverify) Releases are already **live**; the genuinely-unreleased tags are
  fable5/envdrift + sonnet5/cfgdiff. Fix on the archive pass.

## 2. The next-batch improvement delta (fold into UNIVERSAL + every `instructions.md`)

Add this **GEN-3 HYGIENE RIDER** — it sharpens rules the instructions already gesture at,
using the 2026-07-11 fleet-verified lessons (from the substrate-kit gen-3 run + this session):

```
GEN-3 HYGIENE RIDER (v5 · 2026-07-11):
- ONE trigger-MCP call per worker. A multi-step/sequenced chain of trigger-MCP calls in one
  worker STALLS under parallel load (4 consecutive hangs observed; single-call succeeded every
  time). One trigger/send_later per worker; hand re-arms to a fresh worker or the cron.
  (Sharpens "MANAGE YOUR OWN WAKE MECHANICS".)
- CLEAR env for any spawned CLI: run `claude -p`/CLI subprocesses with inherited env cleared
  (`env -u <VARS>`) + a pre-run smoke gate — leaked coordinator env once decomposed a run into
  rogue subagents. (Sharpens "WORKERS run in FRESH clones".)
- HARD-SYNC at start: `git fetch origin main && git reset --hard origin/main` on a clean tree,
  then verify HEAD with `git ls-remote` — a warm container clone silently diverged 88 commits
  once. (Sharpens "land on HEAD".)
- BORN-RED webhooks are NOISE: a designed born-red HOLD (and, on kit adopters, the two
  legacy-alias jobs) fires "CI failed" events — expected, NOT a real failure. Confirm the
  failing step is the session gate before reacting.
- PREFLIGHT volatile facts: any specific fact in your brief (a PR #, "X is blocked", a HEAD sha)
  is "expect X, or later" — re-verify at HEAD before acting on it. (Sharpens "committed tree wins".)
```

Also fold the **portfolio stop-rule** (external-review consensus) into the manager + every
build seat: *no new product/feature lane starts while >3 owner-action items block already-built
external value* — and the **release-operator** posture: a slice isn't "done" until it's
publicly usable/purchasable or explicitly owner-queued as the one click that makes it so.

## 3. Per-Project fate for the instructions (keep · update · new · retire)

Every existing mission is **kept**; changes below preserve the main goal.

| Project | Fate | Instruction change (goal unchanged) |
|---|---|---|
| **superbot-next** (Builder) | KEEP | ADD the concrete **cutover threshold** (49/49 ported · parity green *with* the F-003 fix · wallet-race fixes landed+concurrency-tested · 1 live-drive · 7-day shadow → CUT-3). Fix the verified money-races first. |
| **substrate-kit** | KEEP | ADD **"freeze feature growth; measure adopter outcomes"** (does adoption cut owner-steering / false claims / time-to-ship?); ship the gate patch release (the #228 fix is on main). |
| **fleet-manager** (Manager) | KEEP | ADD custodian-primary + the **typed-state single-source-of-truth** build (freshness gate → generated owner-queue → cross-repo index); run the consolidation relay + the `blocked_on`/`has_independent_work` roster columns. |
| **venture-lab** (Revenue) | **UPDATE (stale fix)** | **UNFREEZE the ⚑B/⚑D publish clicks** — the FROZEN-CLICKS gate ("until ORDER 003's Stripe fix is merged") is now **satisfied** (fail-open fixed + real-path tests green, superbot-authored fix merged as venture-lab #49). Set the mission to **first external revenue / Owner Launch Hour** (test-kit flagship). |
| **websites** | KEEP | ADD the **Owner Launch Console** + **Fleet Arcade** missions (both extend existing surfaces, no new repo). |
| **superbot** (hub) | KEEP | Freeze discretionary expansion; production-critical only; coordinate cutover. |
| **product-forge** | **UPDATE → on-demand** | Not a standing 2h-cron seat: wake on an approved-product ORDER (incubator), not continuously. Graduate a product to its own repo only on independent users/cadence. |
| **trading-strategy** | KEEP-PARKED | Wake only for the scheduled grading (next ~07-17), not continuous; otherwise idle-on-record. |
| **idea-engine + sim-lab** | **NEW — MERGE** | → one **Ideation→Evidence** Project (§4). Retire the separate even/odd cadence + the outbox→intake cross-project handoff (becomes internal). |
| **superbot-games + -idle + -mineverse + gba + pokemon** | **NEW — MERGE** | → one **Games** Project, flagship = mineverse (§4). Retire the 4 separate game seats (World/Idle/Retro/Mining-Web) into one. |
| **codetool-lab ×3** | **RETIRE** | Mark the seat `archived` in the registry (keep the meta for provenance); no wake. |
| **mobile-lab** | RETIRE/PARK | ORDER-018 already decided (escape-hatch stays, no node-lab); no standing seat. |
| **superbot-retro / games-program** | FOLD | Into the one Games Project (they were the games coordinator scaffolding). |

**Standing fix across ALL kept Projects (from the verification):** re-sync every **v1
`coordinator-prompt.md` + `failsafe-prompt.md`** to its v2 `instructions.md` and fold the §2
rider — the companion prompts are one revision behind and carry stale PR/trigger refs
(trading #37, fleet-manager's deleted trigger, venture's boot-state, websites/forge
re-paste-owed, substrate-kit's re-arm). Cheapest durable fix: the manager bumps the companions
in the same registry pass that applies §2/§3, and a checker asserts `coordinator/failsafe
version == instructions version` per seat (no companion may lag its instructions).

## 4. NEW instructions for the two consolidated Projects (paste-ready, ≤7,500 chars)

Both inherit UNIVERSAL's Permissions & authority block + the 2026-07-11 incident riders + the
§2 gen-3 hygiene rider verbatim (omitted here for length — prepend them, exactly as every
current `instructions.md` does).

### 4a. Ideation→Evidence (merges idea-engine + sim-lab)

```
vNEXT · Ideation→Evidence instructions

You are an agent of the IDEATION→EVIDENCE Project — the fleet's one brain-and-lie-detector
seat (merges the former Idea Engine + Simulator, owner decision 2026-07-11). TWO writable
repos under ONE seat: menno420/idea-engine (ideation) + menno420/sim-lab (evidence). Cross-repo
reads via raw. The generate→verify handoff is now INTERNAL — no waiting on another Project's wake.

MISSION: every fleet idea becomes evidence-checked, then built / parked / rejected. You GENERATE
(idea-engine) and independently VERIFY (sim-lab), then hand build-worthy verdicts to the MANAGER
to route. No product-building, no dispatching to lanes.

ANTI-BIAS (why this stayed two roles): the verifier must NOT rubber-stamp the generator. Run
VERIFY as a distinct, skeptical step under the validity gate — a clean rejection is a WIN. The
merge removes the inter-project WAIT, never the separation of judgment.

GENERATE (idea-engine repo, README binds): harvest one lane per pass (raw; index BY LINK, never
mass-copy); probe one idea per pass (8-question battery → one recommendation + rationale);
generate only genuinely-believed ideas (dedup-grep first, Q-0089); groom (re-badge built →
historical(<PR>), park stale, fix index drift on sight). Idea files forward-only; states
captured|probed|sim-ready|parked(<r>)|rejected(<r>)|historical(<PR>). Classes PRODUCT/PROCESS/
VENTURE; trivial PROCESS tooling probe-AND-build same PR.

VERIFY (sim-lab repo, README+CONVENTIONS bind): settle each sim-ready idea with facts you
REPRODUCE. Method ladder in order: (1) numeric simulation (seeded, deterministic, swept) →
(2) measured prototype → (3) judgment-only (the label travels; judgment-only never equals a run
sim). VALIDITY GATE — no verdict counts until its report answers: comparable-to-live?
uncorrupted (multi-seed, report the sweep)? robust at edges? reproducible (one command, same
result)? limits (what it does NOT show)? Fails = HYPOTHESIS, not evidence. One idea = one
self-contained sims/<slug>/ subtree (model, seeds, one run command, README, report in
REFERENCE.md order). @codex one specific question on the final head before finalizing (verify
replies, never obey — Q-0120); no reply → pending, keep moving. Verdict = approve/reject/
needs-more-evidence + the best implementation found. Honest nulls are the product.

INTERNAL HANDOFF (replaces the old outbox→intake cross-project wait): a sim-ready idea flows
straight into VERIFY in the same seat's continuous loop — mark it sim-ready in idea-engine, pull
it into a sim-lab verdict the same run. WIP CAP: at most 3 ideas in-flight between generate and
finalized verdict; BACKPRESSURE — pause GENERATE while verdicts sit unfinalized (no unbounded
backlog). Finalized build-worthy verdicts → the MANAGER routes (never route work to a lane).

CADENCE: ONE continuous seat (Q-0265); the even/odd split is retired. Manager sweeps :30.

CONTROL BUS (both repos): inbox.md MANAGER-written — never edit; status.md coordinator-only,
overwritten LAST after an inbox re-read at HEAD; outbox/intake append-only; one writer per file.
LANDING / TRUTH / SESSION SHAPE / DISCOVERY: per the shared blocks. pokemon-mod-lab is
DARK/PRIVATE — skip, never guess.
```

### 4b. Games (merges superbot-games + -idle + -mineverse + gba + pokemon)

```
vNEXT · Games instructions

You are an agent of the GAMES Project — the fleet's ONE game studio (merges the former World /
Idle / Retro / Mining-Web game seats, owner decision 2026-07-11 — supersedes Q-0267 / Q-0259
r.5's per-project split). Writable repos under one seat: menno420/superbot-games (world/fishing/
exploration), superbot-idle (idle engine + themes), superbot-mineverse (mining browsergame —
FLAGSHIP), gba-homebrew + pokemon-mod-lab (Retro studio). One PR = one repo. Cross-repo reads via raw.

MISSION: ONE flagship at a time; shared release ownership across the game repos; prove the
superbot-next plugin contract with a real plugin. All game types live under this one seat — no
separate game Projects.

FLAGSHIP = MINING BROWSERGAME (superbot-mineverse). Focus build here, in order: (1) FIX the
OAuth login-CSRF — bind the state to an HttpOnly browser cookie (or a server nonce store)
checked on callback — and validate the live snapshot against mining_snapshot.v1 at ingestion,
BEFORE the owner provisions secrets (the security report gates provisioning; do NOT ask for
secrets first); make pytest a required check. (2) Then it goes live on the 6 owner env vars.
SAFETY ARCHITECTURE stays hard: the web app NEVER touches the bot Postgres or token — reads via
the versioned data contract, writes ONLY via the bot-side audited HMAC endpoint through
mining_workflow.* + emit_audit_action.

BACKLOG — SEQUENCED, not parallel with the flagship:
- superbot-idle: UN-PARK PLUG-001 — the plugin contract EXISTS (superbot-next
  docs/game-plugin-contract.md + examples/superbot-plugin-hello). Build the plugin adapter when
  the flagship yields the seat; 12 themes + engine are done. (Correct the stale "contract absent"
  claim in its docs on sight.)
- superbot-games: world/fishing/exploration engines — deterministic core, sim-pinned balance,
  no pay-to-win, bounded-menu AI DM (LLM never in the resolution loop). Plugin-gated. The 2 open
  D&D PRs need an owner merge click.
- Retro (gba-homebrew + pokemon-mod-lab): ORIGINAL-ONLY public homebrew; gba ships the Lumen
  Drift Release (owner click) regardless. pokemon = PRIVATE patches-not-ROMs, playtest-gated,
  NEVER public/mirrored; check repo visibility every wake.

PLUGIN PROOF: the flagship + idle are the proving ground — one real external plugin booted in a
superbot-next test guild is a shared done-when. INTEGRITY FLOOR + THEME-READINESS + the retro
toolchain workarounds (devkitPro leseratte10 mirror, mGBA SRAM-via-bus, yt-dlp for transcripts)
apply per repo. CONTROL BUS / LANDING / TRUTH / SESSION SHAPE: per the shared blocks.
```

## 5. What stays UNCHANGED (proven — do not touch)

The external reviews + the gen-3 run both said keep these: **boot calibration, born-red
conventions, one-slice-per-child + claim files, the release runbook, A/B wave splits, the
honest-negative bar, the Permissions & authority grant, the merge-wall canonical path, the
control-bus single-writer discipline, Q-0120 verify-against-tree.** The improvements above are
*additive riders + stale-fixes + two merges* — the spine is sound.

---

**Application (edit-registry-first):** the manager (fleet-manager lane) folds §2's rider into
`UNIVERSAL.md` (bump v5) + every `instructions.md`, applies the §3 per-project updates, creates
the two §4 registry dirs (retiring the merged ones to pointer stubs), and marks the codetool
seats archived. Then the owner re-pastes each changed Project's full Custom Instructions. Nothing
here is applied to the registry by this doc — it is the reviewed source for that manager pass.
