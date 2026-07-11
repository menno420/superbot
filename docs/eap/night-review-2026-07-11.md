# Fleet night review — 2026-07-11

> **Status:** `reference` — owner-directed independent night review of the whole
> SuperBot EAP fleet for the night of **2026-07-10 ~18:00Z → 2026-07-11 ~11:40Z**.
> Built from the fleet-manager machine roster (gen #5) + three read-only survey agents
> over 13 active lanes (GitHub MCP, per-lane PRs/reports/status/model self-report).
> Verify load-bearing claims against the tree (Q-0120). Companion to
> [`fleet-overnight-review-2026-07-10.md`](fleet-overnight-review-2026-07-10.md).

## 0. TL;DR — the six things that matter

1. **The night went well on output, poorly on realization.** Every active lane is
   green and shipped hard (superbot-next 30/49 parity; substrate-kit 5 releases;
   mineverse 0→live in ~3h; ~15–30 PRs/lane), and nearly every lane delivered its
   owner-directed self-review. **But almost none of the value is live** — it's stuck
   behind a short queue of owner clicks (revenue, Pages, env vars, a Release).
2. **You can actually play a game tonight:** `gba-homebrew/dist/lumen-drift.gba` **v1.3
   is committed and runs in any GBA emulator now** — it only needs you to click "create
   Release." That's the fastest tangible win in the fleet.
3. **Both platform bugs you flagged are real and evidenced** (§4): (a) `add_repo`
   "[Unauthorized Persistence]" denials ~1-in-2 to 1-in-3 on wake-fired sessions → some
   wake hours produce *no session at all*; (b) configured-vs-actual **model mismatch** —
   and pokemon-mod-lab genuinely self-reports **sonnet-5**. Your fix (attach repos to the
   routines) is the correct one and you've already started it.
4. **The fleet already ran a coordinated model-attribution order tonight** and ruled
   "the committed card self-report is authoritative, the Routines screen is unreliable" —
   but that ruling is **resolved-by-rule, not verified-by-evidence** (§4.2). Worth one
   owner-vs-harness spot-check.
5. **Gate integrity is reactive.** Two CI loopholes shipped live and were closed the
   *same day* (substrate-kit tail-1 shadowing, born-red card-only); mineverse's PR #16
   auto-merged **28 s before pytest finished** because pytest isn't a required check.
6. **Two lanes bury their self-review inside `control/status.md`** (overwritten each
   wake) instead of a durable `docs/retro/` file — websites' `docs/retro/self-review-2026-07-11.md`
   is the model everyone should copy.

## 1. Per-lane digest

| Lane | Tonight (headline) | Report? | Health | Model (self-report) | Top flag |
|---|---|---|---|---|---|
| **superbot-next** | 30/49 subsystems ported, byte-level goldens green, 1356 tests; dozens of PRs (#167–#176) | in-status (buried) | green, shipping | fable-5 | self-review in overwritten status.md; 2 codex "phantom-artifact" claims |
| **substrate-kit** | **5 releases** v1.7.1→v1.10.1; grammar module, claims convention, gate fixes; 852→995 tests | ✅ `docs/reports/…t5-rescope-analysis.md` | green | fable-5 ×3 | gate integrity reactive (2 loopholes closed same-day); B1 bench still 1 PASS/4 FAIL |
| **websites** | ~22 slices; time-bomb defuse → 17-site class guard; every-card gate port; 237 tests | ✅ **best** `docs/retro/self-review-2026-07-11.md` | green | fable-5 | **routine-fired wakes unreliable** (2 silent windows); DATABASE_URL + GITHUB_TOKEN owner-gated |
| **venture-lab** | 15 PRs; **Stripe Webhook Test Kit v0.1** (new product); Supabase store | ✅ `docs/research/venture-eval-001.md` + launch docs | green | **BOTH** (opus-4.8 builder / fable-5 coord) | **budget overran 2.3×** (~284k tok); revenue 100% owner-click-gated, $0 sold |
| **product-forge** | 15 PRs; 2nd character + switcher; a11y; Pages deploy wired | in-status (buried) | green | opus-4.8 | **Pages not enabled (OA-003)** → games-web preview stuck; future-dated heartbeat bug (fixed) |
| **superbot-games** | shared-inventory seam, fishing skeleton, theme-leak extraction; 257 tests | ✅ `docs/audit/theme-slot-readiness-2026-07-11.md` | green | opus | **status ~9h stale** while main advanced on kit/fm PRs; not playable (library) |
| **superbot-idle** | persistence engine, **12 theme packs**, 24→**827 tests** | ✅ in-status + `docs/plugin-adapter-scoping.md` | green, **HOLD** | fable-5 | capped by **PLUG-001** (superbot-next has no plugin contract; `superbot-plugin-hello` empty) + SIM-001 |
| **superbot-mineverse** | **new seat booted 0→live in ~3h**, ~30 PRs, full read+write ladder, 191 tests | ✅ `docs/live-prod-cutover.md` + `mining-data-contract.md` | green, engaged | fable-5 | live needs 6 owner env vars + make pytest required (PR #16 merged 28s before pytest) |
| **gba-homebrew** | **`dist/lumen-drift.gba` v1.3 committed + playable**; reproducible CI ROM build | ✅ `docs/PLATFORM-LIMITS.md` (dated) | green, idle-ok | Fable | needs **Release click** to publish; logs the add_repo + model bugs (§4) |
| **pokemon-mod-lab** | 16 QoL patches, byte-identical vanilla anchor; per-preset build recipe | ✅ in-status + `docs/qol-patches.md` | green, idle-ok | **sonnet-5** | **add_repo denied 2/4 wakes**; wake sessions have **no PR tooling** (9/15 stranded) |
| **sim-lab** | VERDICT 006 idle-economy kernel (SIM-PINNED) + 007 games-web REDIRECT; harness v0.1.0 | ✅ per-verdict `REPORT.md` | green, **idle-by-design** | "Opus 4.x" | genuinely idle (queue empty, waiting on idea-engine) — not stuck |
| **idea-engine** | probe closures across lanes; supersession sweep; 147-PR fleet tally | in-status | green | fable-5 | one owner decision bundle due ≤07-14; status.md enormous/dense |
| **trading-strategy** | paper lane opened; Round-2 closed (5 KEEP/9 KILL); kit→v1.10.1 | ✅ `docs/final-report.md` + `research-round-2-results.md` | green, **parked** | fable-5 | parked-green (next grading ~07-17); status kit-line stale vs its merges |
| fleet-manager | roster mechanized (`gen_roster.py`), ORDER-010 relay 14/14, my ORDER 016 merged | (roster + status) | green | fable-5 | inbox clear; coordinator chain deliberately idled on empty work |

## 2. What's genuinely valuable tonight

- **Playable now:** gba-homebrew ships a committed, hash-pinned `dist/lumen-drift.gba`
  v1.3 (runs in any emulator) — the single most tangible artifact in the fleet;
  pokemon-mod-lab builds a real 16-patch Emerald ROM; mineverse's browsergame runs
  **live in degraded read-only mode** already.
- **Real product:** venture-lab's Stripe Webhook Test Kit v0.1 (a sellable dev tool).
- **Real infrastructure:** superbot-next's parity engine (30/49, byte-level goldens),
  substrate-kit's 5 releases (every downstream lane upgraded), superbot-idle's 827-test
  engine + 12 theme packs.
- **Best-in-fleet report:** websites `docs/retro/self-review-2026-07-11.md` — own
  mistakes first, each tied to a PR/commit/run. Make this the fleet template.

## 3. Concerning patterns (ranked)

1. **Value stranded behind owner clicks.** The fleet *built* a great deal and *shipped*
   almost none of it live. Revenue ($0), the games-web preview, mineverse read-write, the
   Lumen Drift Release, the public botsite — all gated on a short click queue (§6).
2. **`add_repo` denials + no-PR-tooling strand unattended lanes** (§4.1). The retro/game
   wake sessions lose ~⅓ of their hours to `add_repo` denials and, when they do run,
   often can't open/merge PRs (pokemon 9/15 stranded).
3. **Model attribution is resolved-by-rule but unverified** (§4.2) — and at least one lane
   is genuinely on a different model than intended (pokemon self-reports sonnet-5).
4. **Reactive gate integrity.** Loopholes ship live, get closed same-day; a real PR merged
   before its tests finished. The safety net trails the velocity.
5. **Self-reviews buried in overwritten `status.md`** (superbot-next, product-forge,
   idea-engine, superbot-idle, pokemon) — they won't survive the next wake.
6. **Time/clock fragility:** a future-dated heartbeat corrupted freshness ranking; a
   time-bomb test detonated on an untouched tree. The freshness checker catches *stale*,
   never *future*; aged-fixture time-bombs likely exist in sibling lanes.
7. **venture-lab overran its token budget 2.3×** on one product (~90k of it on CI polling).

## 4. The two platform bugs (your findings — evidenced)

### 4.1 `add_repo` "Unauthorized Persistence" denials → routines spawn without their repo

**Evidence (verbatim from lane records):**
- pokemon-mod-lab `control/status.md`: `add_repo` denied on **2 of the last 4 wakes**
  (~09:02Z deny · ~09:2x grant · 10:03Z deny · 10:37Z grant), each citing
  **"[Unauthorized Persistence]"** — "roughly 1-in-2 to 1-in-3." Compounded by
  **OWNER-ACTION 4**: wake sessions have **no GitHub PR tooling** (`gh` absent,
  `api.github.com`→403, no `mcp__github__*`) — "9 of this window's 15 sessions hit the
  identical wall"; branches strand until a shepherd/owner merges.
- gba-homebrew `docs/PLATFORM-LIMITS.md` (your ~10:36–11:05Z live-debug session): the
  same `add_repo` denial pattern, and you have **already added both gba + pokemon repos to
  the hourly-wake routine config** — first PR-capable wake pending verification.

**Diagnosis:** this is *not* a generic "routine forgets the repo" — it's the auto-mode
safety classifier **denying the wake session's `add_repo` call** ~⅓ of the time. So an
agent-side self-heal (retry `add_repo`) **cannot fix it** — the call is being refused, not
failing transiently. **The only reliable fix is yours: attach the repo(s) to the routine
config** so the session is *born* with the repo and never needs `add_repo`. You've started
this correctly. The second wall (no PR tooling in wake sessions) is separate and arguably
bigger — see §6.

### 4.2 Model config-vs-actual mismatch — resolved by rule, not by evidence

**What the fleet did tonight:** a coordinated model-attribution order (substrate-kit ORDER
012 → doctrine in kit v1.9.0; trading ORDER 009; sim-lab ORDER 001). Conclusion: **the
committed session card's `📊 Model:` self-report is the only reliable attribution; the
Routines/schedule screen is unreliable; capturing model from an external surface is
impossible (only the session can read its own harness).**

**What cards actually self-report this window:** superbot-next, websites, substrate-kit,
trading, idea-engine, superbot-idle, mineverse, gba → **fable-5**; product-forge → **opus-4.8**;
sim-lab → "Opus 4.x"; venture-lab → **both**; **pokemon-mod-lab → sonnet-5**. Your Routines
screen shows fable-5 / opus-4.8 and your default is opus-4.8.

**The unresolved crux (my flag):** the doctrine names the card as authoritative, but that
*assumes* the card reads the live harness value rather than habitually writing a configured
string — and that isn't independently proven. If a wake session is truly running sonnet-5
while its card says fable-5, either the card is transcribing the config (a doctrine
violation the order can't detect) or the screen is stale. **pokemon self-reporting sonnet-5
is the one lane that breaks the "everyone says fable-5" pattern — that's your smoking gun.**
Recommend: on one lane, compare what the card claims vs what you can independently verify,
and set the model explicitly on each routine (§6) so config and intent stop diverging.

## 5. Fix-first — priority order for today

1. **Attach repos to every project routine** (you can; you did gba+pokemon). Kills the
   `add_repo`-denial no-session-hours class fleet-wide. **First thing.**
2. **Set the model explicitly on each routine** to the family you intend, and do one
   card-vs-harness spot-check (pokemon = sonnet-5 is the lead).
3. **Clear the owner-click queue** (§6) — it's the only path from "built" to "live/selling."
4. **Give wake sessions PR tooling** — the game/retro wakes stranding branches (pokemon
   9/15) is a bigger throughput loss than the add_repo denials.
5. **Make `pytest` a required check where it isn't** (mineverse first) — a PR merged before
   its tests finished tonight.
6. **Move buried self-reviews to `docs/retro/`** — a one-line manager order (websites is the
   template).

## 6. Owner-action queue (only you can do these)

**Routines (the fix for your findings):**
- [ ] **Attach the lane repo to each routine** (born-with-repo → no add_repo needed). Table:
  | Routine (trigger) | Cron | Attach repo(s) |
  |---|---|---|
  | Builder failsafe wake | `0 */2` | superbot-next |
  | substrate-kit failsafe wake | `0 */2` | substrate-kit |
  | websites lane wake | `0 */4` | websites |
  | trading-strategy failsafe wake | `0 */2` | trading-strategy |
  | venture-lab failsafe wake | `0 */2` | venture-lab |
  | superbot-games failsafe wake | `15 */2` | superbot-games |
  | superbot-idle failsafe wake | `45 */2` | superbot-idle |
  | superbot-mineverse failsafe wake | `20 */2` | superbot-mineverse |
  | product-forge failsafe wake | `0 */2` | product-forge |
  | idea-engine failsafe wake | `0 */2` | idea-engine |
  | sim-lab failsafe wake | `0 1-23/2` | sim-lab |
  | fleet-manager failsafe wake | `30 */2` | fleet-manager (+ program repos it coordinates) |
  | gba-homebrew hourly wake | `0 * * * *` | gba-homebrew ✅ (done) |
  | pokemon-mod-lab hourly wake | `30 * * * *` | pokemon-mod-lab ✅ (done) |
  | **retro-games coordinator (NO repo)** | `50 */2` | gba + pokemon — **or retire it** (redundant now that both hourly wakes carry their repos) |
- [ ] **Set each routine's model** to the intended family (your default is opus-4.8; the
  founding packages intend family-level names — reconcile). Spot-check pokemon (sonnet-5).

**Unblock the value (one sitting, mostly one-paste each):**
- [ ] gba-homebrew: **create the Lumen Drift v1.3 Release** (the playable ROM is committed).
- [ ] venture-lab: Stripe **test keys** (⚑A) + the **publish clicks** ⚑B/⚑D (now unfrozen) — the revenue path.
- [ ] product-forge: **Settings → Pages → Source: GitHub Actions** (OA-003) — unstucks games-web preview.
- [ ] mineverse: provision **6 host env vars** (Discord OAuth ×4 + write pair) + make **pytest a required check**.
- [ ] websites: **botsite `DATABASE_URL`** (public /submit) + a **`GITHUB_TOKEN`** for the pages (off the 60-req/hr anonymous ceiling).
- [ ] substrate-kit: retire the **legacy alias CI jobs** (OA-2 — causes false red-pings) + ratify parked T5 pin **PR #181**.
- [ ] Delete stale merged branches (agents 403 on ref deletes) — small cleanup fleet-wide.

## 7. Lessons + what went well (repeat these)

**Repeat:**
- The **new-seat seeding recipe works** — mineverse went 0→live-with-contracts in ~3h.
- **Honest idling** — sim-lab / trading / gba / pokemon idled correctly instead of
  manufacturing busywork (the Q-0089 honesty guard is holding).
- **Coordinated fleet-wide orders** (the model-attribution relay) executed across lanes —
  the manager's inbox relay mechanism is reliable.
- **Self-auditing guard work** (websites' time-bomb → 17-site class guard) and **kit
  velocity** (5 releases, all lanes upgraded same night).

**Lessons:**
- **Build-vs-realize gap:** the fleet's bottleneck is no longer *producing* — it's the
  owner-click queue. The single highest-leverage thing today is clearing it, not building
  more. Consider a standing "owner-action queue" doc the manager keeps ruthlessly short.
- **A capability wall the agent can't fix (classifier-denied add_repo) must route to you
  fast and clearly** — it silently ate wake-hours before your live-debug caught it. The
  routine-repo attach is the durable answer; make it a founding-package default for new seats.
- **Durable > in-status for anything you'll want later** — reviews and findings belong in
  `docs/`, not an overwritten heartbeat.
- **Required checks must actually be required** — "green" meant less than it should on the
  lanes where pytest wasn't gating.

## 8. My opinion (bottom line)

This was a genuinely strong night of *production* and a weak night of *shipping*. The
agents built real, tested, honest work at high volume with almost no stuck or abandoned
lanes — that's the hard part working. The gap is entirely at the human gate: a dozen
built-and-green things are one click each from being live, and two platform bugs (add_repo
denials, model mismatch) quietly taxed the unattended lanes. If you spend today doing two
things — (1) attach repos + set models on the routines, (2) clear the owner-click queue —
the fleet converts a night of *potential* into a day of *live results*, and the next night
runs cleaner. The one thing I'd watch beyond the clicks: verify the model a lane actually
runs vs what its card claims (pokemon=sonnet-5 says the attribution doctrine isn't as
settled as the fleet decided).
