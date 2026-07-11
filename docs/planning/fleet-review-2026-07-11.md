# Fleet review + triage — 2026-07-11

> **Status:** `reference` — owner-directed verified full-fleet review + keep/replace/delete
> triage. Built from a 19-agent discovery fan-out (14 repo scans + 5 cross-cutting probes,
> ~2.9M tokens) whose every load-bearing claim was verified **against live source**, not
> against status/report text (Q-0120). Companion to the [centralization
> plan](fleet-centralization-plan-2026-07-11.md) and the [dispatch
> kit](../owner/dispatch-prompts-2026-07-11.md). Verify anything you act on; two agents
> already diverged on one PR (substrate-kit #228, §3) — flagged, not silently resolved.

## 0. TL;DR — my opinion, bottom line

**The fleet is strong and the diagnosis has not changed since the night review: the
bottleneck is realization, not production — plus a thin layer of drift that all lives in
one place (`fleet-manager`, the hub everyone reads first).** 15 active lanes, every one
green and heartbeating; **zero repos need deleting**; the only archive candidates are the
3 wound-down codetool-labs. The single most important *new* finding: **this round's Codex
reviews are trustworthy (no phantom commits this time) and they surfaced real, live,
high-stakes bugs — including a real-money publish-blocker in venture-lab** that is one
owner click away from shipping to paying customers. Three of the four Codex report PRs are
still open and **docs-only, so those code bugs are LIVE and unfixed.**

Six things that matter:

1. **🔴 URGENT / real money:** `venture-lab` membership-kit ($49) **fails OPEN** on a
   partial Stripe config — with `STRIPE_SECRET_KEY` set but `STRIPE_WEBHOOK_SECRET` unset,
   `/webhook` grants paid membership from **unsigned JSON**, silently (no MOCK banner).
   Verified in `app.py`. **Must fail-closed before publishing.** The lane's own status
   already marks the publish gate "UNFROZEN ✅" — so the guardrail is *off* while the bug
   is *live*.
2. **🟠 Before games go live:** `superbot-next` has **two verified wallet-race bugs**
   (blackjack solo double-settle, PvP double-escrow) in already-`ported` domains, plus a
   **latent parity-gate false-green** that undermines the "218/218 green" the cutover
   rests on. All three are real, all three are unfixed (Codex PR #196 is docs-only).
3. **🟠 Fleet blast-radius:** `substrate-kit`'s session-card gate has a verified
   false-green (advisory-sibling shadowing + deletion-exclusion) that ships in v1.12.0 to
   **all 7 adopters**, and the open PR that claims to fix it (#228) **contains no fix
   code**. Two agents disagree on whether the G-2 half already landed on main — **re-verify
   before trusting the kit gate.**
4. **🟡 The drift is concentrated and cheap to fix:** every live drift instance is in
   `fleet-manager` — the generated roster is **~13h stale under its own 24h alarm** (so a
   fresh session gets no warning), the owner-queue's top-3 merge clicks are **already
   merged**, and item 13 is doubly stale (claims UNIVERSAL.md is "still v3" when v4 is
   live). Guards proposed in the [centralization plan](fleet-centralization-plan-2026-07-11.md).
5. **🟢 Value stranded behind a short owner-click queue** (unchanged, and it's the real
   story): revenue ($0), Lumen Drift Release, product-forge Pages, mineverse secrets, the
   plugin seed. The fleet's leverage today is **clearing clicks, not building more.**
6. **The two platform bugs you flagged are confirmed real and the fix works:** `add_repo`
   "[Unauthorized Persistence]" denials (~1-in-3) and the model config-vs-actual mismatch —
   and attaching the repo to the routine config is **confirmed working** (pokemon logged 14
   clean wake cycles after the fix). Both are baked into the [dispatch
   kit](../owner/dispatch-prompts-2026-07-11.md).

**On "which projects to replace or delete":** none. This is a coherent portfolio, not a
sprawl. The honest moves are *archive* (3 codetool-labs → read-only reference once gen-3
succession settles), *seed* (`superbot-plugin-hello`, one word — it unblocks two finished
engines), and *park the loop* (pokemon-mod-lab is idle-gated; stop burning ~1 no-op
session/hour). Everything else earns its keep.

## 1. Triage register — keep / replace / archive / delete (verified)

Verdict legend: **KEEP** (active, earns its place) · **KEEP-SEQUENCE** (keep, mid-build,
defined next step) · **KEEP-PARKED** (keep the asset, park the loop) · **ARCHIVE**
(finished, make read-only, lose nothing) · **SEED** (empty, one action to activate) ·
**DELETE** (none).

| Repo | Health | Verdict | One-line rationale | The single next action |
|---|---|---|---|---|
| **superbot** (hub / prod bot) | 🟢 | KEEP | The oracle + the live product; the whole program's substrate | Normal live-verify of merges; fix the Rule-6 false-green checker (§3) |
| **superbot-next** (rebuild) | 🟡 | KEEP-SEQUENCE | Flagship build, 37/49 ported, boots on real PG; 2 money races to fix pre-cutover | Fix F-001/F-002 wallet races + F-003 parity false-green, then continue ports |
| **substrate-kit** (fleet foundation) | 🟡 | KEEP | 7 adopters run on it; gate false-green ships in v1.12.0; #228 is an empty fix | Land the *real* gate fix on `adopt.py`+`ci.yml`, cut a patch release, close #228 |
| **websites** (oversight/control-plane) | 🟢 | KEEP | 4 real services, 3 live; the fleet's visual control plane; backlog drained | Owner: merge #141 + create the `review` Railway service |
| **venture-lab** (first revenue) | 🟡 | KEEP | 3 real built products; **critical Stripe fail-open** before publish | 🔴 Fail-closed on partial Stripe config, then publish |
| **superbot-mineverse** (web game) | 🟡 | KEEP | Real read-only demo; login-CSRF + pytest-not-required before secrets | Bind OAuth state to browser + schema-validate; make pytest required |
| **superbot-games** (game engines) | 🟢 | KEEP | Pure-domain, green, DM-clamp verified; parked on plugin contract (correct) | Owner merge #49 then rebase+merge #50; refresh stale status |
| **superbot-idle** (idle engine) | 🟡 | KEEP-SEQUENCE | 827 tests, 12 themes; **self-parked on a blocker that's already resolved** | Lift PLUG-001 (contract EXISTS in superbot-next), build the adapter; land SIM-001 |
| **product-forge** (web-product forge) | 🟢 | KEEP | Real games-web, 22 PRs, foundational infra ("home to homeless projects") | Owner: enable GitHub Pages (one toggle) |
| **gba-homebrew** (GBA game) | 🟢 | KEEP | Playable committed ROM, reproducible CI build; low-maintenance | Owner: create the Lumen Drift v1.3 Release |
| **pokemon-mod-lab** (private ROM mod) | 🟢 | KEEP-PARKED | Real 16-patch mod, private, copyright-safe; idle ~18 sessions, all owner-gated | **Pause/slow the hourly wake**; owner playtest verdict unblocks it |
| **trading-strategy** (quant research) | 🟢 | KEEP-PARKED | Honestly complete (holdout spent, 0/13 cleared); paper lane in warm-up | Fix 1 stale kit-version line; leave parked until 7/17 grading |
| **sim-lab** (evidence/lie-detector) | 🟢 | KEEP | 10 verdicts, self-checks caught a real bug; idle-by-design not stuck | Owner: enable Codex integration (OA-002) so verdicts get reviewed |
| **idea-engine** (ideation) | 🟢 | KEEP | 193 PRs, reports verify true; surfaced a real superbot false-green | Split the 25KB status.md; lift the ≤07-13 owner decision out of the bloat |
| **fleet-manager** (coordination substrate) | 🟡 | KEEP | The de-facto SSOT; roster/queue/inbox real; but ledgers drift + stubs unfilled | Merge #77; close the drift + build the centralization gaps (see plan) |
| **superbot-plugin-hello** | ⚪ empty | **SEED** | Empty repo gating two finished engines (idle + games) | 🟢 One word: "push the plugin seed" |
| **codetool-lab-fable5** (envdrift) | ⚫ parked | **ARCHIVE** | Finished CLI, wound-down ~32h, no mission | Archive after gen-3 succession settles; pending tag/Release clicks |
| **codetool-lab-opus4.8** (mdverify) | ⚫ parked | **ARCHIVE** | Finished CLI, releases live, wound-down, no mission | Archive after gen-3 succession settles |
| **codetool-lab-sonnet5** (cfgdiff) | ⚫ parked | **ARCHIVE** | Finished CLI, wound-down, no mission | Archive after gen-3 succession settles; pending v0.1.1 tag |

**19 repos · 15 active (all KEEP-family) · 3 ARCHIVE · 1 SEED · 0 DELETE.**

## 2. Codex review verdict — "fully review the codex PRs" (verified against source)

**Bottom line: this round is trustworthy.** Across all 4 dispatched repos, every file /
function / behavior Codex cited was confirmed present and behaving as described — a marked
contrast to the earlier phantom-commit episodes (#144/#160/#178) the prompt warned about.
The **only** inaccurate finding in the batch was substrate-kit **B-1** (a "missing
completeness checker" that in fact exists — `test_module_order_covers_every_engine_module`),
which the fleet had already refuted correctly. Each report also correctly named genuine
"verified clean" areas rather than manufacturing findings. **Treat this round's findings as
actionable leads that survive verification.**

| Codex PR | Status | Top finding | Verified? | Live? |
|---|---|---|---|---|
| venture-lab **#38** | OPEN, docs-only | Stripe **fail-open** on partial config → unsigned grants | ✅ CONFIRMED in `app.py` | 🔴 **LIVE** |
| superbot-next **#196** | OPEN, docs-only | 2 wallet races (F-001/F-002) + parity false-green (F-003) | ✅ CONFIRMED in source | 🟠 **LIVE** |
| superbot-mineverse **#31** | OPEN, docs-only | OAuth **login-CSRF** (state not browser-bound) + no runtime schema validation | ✅ CONFIRMED in `auth.py` | 🟡 dormant (secrets unset) |
| substrate-kit **#226** | CLOSED | 2 real gate bugs (G-1/G-2) + 1 false (B-1) | ✅ G-1/G-2 real, B-1 refuted | ⚠️ **see §3** |

**Action gap:** #196, #38, #31 each add **only a report markdown file** — none of the code
defects are fixed. The findings must become tracked fix-work, not orphaned open PRs.

## 3. Verified errors to fix — ranked (all confirmed against source)

1. **🔴 venture-lab — Stripe fail-open (real money, about to publish).**
   `candidates/membership-kit/server/app.py`: `/create-checkout-session` enables the live
   Stripe path on `_stripe_secret_key()` alone, but `/webhook` only verifies the signature
   `if secret := _webhook_secret()` — its `else` branch `json.loads()` an unsigned body and
   calls `handle_purchase_event → store.grant()`. Config with the secret key set + webhook
   secret unset ⇒ any internet user POSTs `{type:'checkout.session.completed', …email…}` and
   mints free paid membership. `_is_mock()` is False in that state, so no MOCK banner fires
   — **silent** fail-open. The signature verifier itself is correct (timing-safe, 300s
   tolerance, raw-body-first). **Fix:** if *either* Stripe var is set, require *both*; never
   grant from unsigned JSON outside explicit full-no-keys mock mode. Also: a test
   (`test_mock_mode_loud_warning`) actively **asserts** the unsigned grant as intended mock
   behavior — that's why 35/35 green + a 9/9 adversarial pass both missed it (honest
   coverage gap, not a false-green checker). Correct the test + 2 `LISTING.md` overclaims
   (Discord delivery; v0.1→v0.2).
2. **🟠 superbot-next — two wallet races + parity false-green (before games go live).**
   `sb/domain/games/store.py` `fetch_user_checkpoint` (solo) and `fetch_checkpoint` (pvp
   pending) are plain `SELECT`s with **no `FOR UPDATE`**; blackjack ops declare
   `IdempotencyPosture.NATURAL_KEY` with `dedup_key=None`, and `engine.py` mints a key +
   runs `once()` *only* for `DURABLE_ONCE` and locks *only* for `SINGLE_FLIGHT` — so these
   ops get **neither** fence. **F-001:** concurrent solo terminal actions both settle →
   double coin mint/burn. **F-002:** concurrent PvP accepts both escrow → double-debit,
   stake stranded. (`wager.py`'s docstring claims a "K7 once() fence" that the NATURAL_KEY
   posture does not provide.) **F-003 (latent):** `run_golden_parity.run_gate` never checks
   replayed-count == golden-count per ported subsystem; `load_replay_cases` silently drops
   unreconstructable goldens — a false-green in the acceptance oracle gating cutover
   (latent today: the one unreconstructable golden is covered by CURATED_CASES).
   **Fix:** `SELECT … FOR UPDATE` on both loads (or move the ops to `SINGLE_FLIGHT`/
   `DURABLE_ONCE`); make `run_gate` fail-closed on a replayed-vs-golden count mismatch.
3. **🟠 substrate-kit — gate false-green (7-adopter blast radius) + an empty fix PR.**
   **G-1 (HIGH):** the generated adopter gate `live_ci_workflow()` (`src/engine/adopt.py`)
   treats a session card *modified* in a diff that also *adds* a card as advisory-only —
   a PR that adds one good card AND flips a sibling to `in-progress` still exits 0 and
   merges. **G-2 (MEDIUM):** both the kit's `ci.yml` and the generated gate build the card
   list with `--diff-filter=d` (lowercase = deletions excluded), so a delete-only PR can
   merge while erasing session memory. **⚠️ CONTRADICTION TO RESOLVE:** the codex-verify
   agent read `ci.yml` on main and found the **G-2 deletion hard-red already live**, citing
   review #226; the substrate-kit scan agent read **PR #228's diff** and found it contains
   **only two new files (zero fix code)** and is still open. Safe synthesis: **the fix is at
   best partial** (kit's own `ci.yml` may have G-2; the *generated adopter gate* and G-1 do
   not), and **PR #228 does not carry the fix** — do not let #228 flip green/merge as-is.
   **Re-verify both surfaces**, complete the real fix on `adopt.py` + `ci.yml`, add
   deletion-shaped + broken-sibling tests, regen `dist` (byte-pin), cut a patch release.
4. **🟡 superbot-mineverse — OAuth login-CSRF + no runtime schema validation.**
   `server/auth.py` `make_state()` signs `{purpose,nonce,exp}` with **no browser-bound
   cookie / server-side nonce store** — a stateless bearer token ⇒ classic login-CSRF
   (attacker logs a victim in as the attacker). Dormant now (OAuth env vars unset) but
   **must be fixed before the 6 secrets are provisioned.** Also `_serve_views`/`_serve_snapshot`
   only `isinstance(dict)`/`json.loads` — validate against `mining_snapshot.v1` at
   ingestion. And **pytest is not a required check** (PR #16 merged **28s before pytest
   finished**, verified to the second) — an owner one-click ruleset fix.
5. **🟡 superbot — a false-green checker in THIS repo (surfaced by idea-engine, verified).**
   `scripts/check_consistency.py` Rule 6 `settle_once_adoption` is `severity="warning"` (so
   it **never reds** `code-quality`, which fails on `error` only), AND the #1781 `cogs/`-scope
   widening is **inert** because the registry invokes it with `roots=("views/","services/")`
   so the `cogs/` default never flows. Confirmed at superbot HEAD `2c7d2de` via code search: a
   new unguarded `cogs/`-layer settle site would ship **unscanned**. This is a bugs-first,
   fix-on-sight item (routed to the superbot Codex prompt with a verify+fix instruction).
6. **🟡 superbot-idle — self-imposed HOLD on a resolved blocker + a dangling claim.**
   `docs/plugin-adapter-scoping.md` + `control/status.md` declare PLUG-001 "evidence-BLOCKED
   / no contract / empty exemplar" — **both false as of review:**
   `superbot-next/docs/game-plugin-contract.md` is a binding contract (D-0056, predates the
   probe) and `superbot-next/examples/superbot-plugin-hello/` is a complete plugin package.
   The probe checked the wrong filenames (`docs/plugins.md`/`docs/plugin-contract.md`, both
   404) + the not-yet-created standalone repo. Net: the lane's headline deliverable idles
   unnecessarily. Also `control/claims/sim-harness.md` merged (PR #52) but `tools/simulate.py`
   never landed — a dangling claim contradicting "zero parked."

Lower-severity / cosmetic (full detail in the fan-out journal): superbot-games #49/#50
`EXPECTED_MIN_TESTS.txt` floor collision (trivial rebase); product-forge future-dated
heartbeat; parity.yml duplicate corpus-dir naming; several stale-doc lines.

## 4. Drift found (all live at HEAD, all in `fleet-manager`) + the cheapest guard

| Drift (verified) | Why it misleads | Cheapest durable guard |
|---|---|---|
| **Generated roster is ~13h stale** (gen #5 @ 04:28Z, HEAD 17:05Z) but its kill-switch only warns >24h | superbot now redirects **all** fleet-state reads here; a fresh session trusts a stale roster with no warning | `check_roster_freshness.py` reds at >2× cadence (~4h); make roster regen a **required** wake step |
| **Owner-queue top-3 merges (games #27/#32/#38) already merged** 14:56Z | a fresh owner session clicks "merge" on 3 done PRs | `check_owner_queue.py` probes each item's cited PR state at every wake |
| **Item 13 (Blocking:YES) claims UNIVERSAL.md "still v3 / #47 open / fold LOST"** — v4 is live, #47+#76 merged | manager re-attempts a done landing; treats ORDER 017 as still-gated | auto-close/flag an item the moment its cited PR merges (don't strand the resolving edit in #77) |
| **idea-engine cites "owner-queue item 3"** for pokemon verdicts — the rewrite renumbered it to 28(2) | cross-repo follower lands on the wrong item | stable slug IDs (e.g. `OQ-GAMES-MERGE`) instead of positional numbers |
| **product-forge heartbeat future-dated** (`updated: 12:00:00Z`, ~7.5h ahead) | defeats staleness math / monotonic tripwires | reject `updated:` > now at push time (heartbeat guard) |

These are exactly the drift classes the [centralization plan](fleet-centralization-plan-2026-07-11.md)
converts into generators/guards so the fleet catches its own drift (Q-0194 friction→guard).

## 5. Products — built vs live (the conversion queue)

The `product-catalog.md` is **unusually honest** — on every claim spot-checked it matched
source (zips real, ROM real, Stripe crypto real, demo-mode real). The real value: the 3
venture-lab kits, Lumen Drift, substrate-kit, the live bot, websites, superbot-next,
product-forge games-web. The conversion queue (built → live), highest leverage first:

1. **Revenue (after the fail-closed fix):** publish membership-kit $49 · test-kit $29 ·
   template-packs $19 — all dist zips built, crypto verified — Stripe test keys + Gumroad
   clicks + the gotcha article. **Highest revenue leverage in the fleet.**
2. **Plugin seed** ("push the plugin seed"): unstrands **two** finished engines
   (superbot-idle 827 tests + superbot-games).
3. **Lumen Drift Release** (one click; ROM committed + CI-cross-checked).
4. **product-forge Pages** (one toggle → live public games-web).
5. **mineverse secrets** — *after* the CSRF fix + pytest-required (do not provision first).

## 6. Recommended next-action sequence

**This session (planning, docs-only):** land this review + the centralization plan + the
7-prompt dispatch kit (all on PR #1998).

**Immediately after (fixes — agent-doable, some cross-repo → owner-authorized):**
- 🔴 `venture-lab` fail-closed fix **before any publish** (offer to do it live this session
  if you authorize the cross-repo write).
- 🟠 `superbot-next` F-001/F-002/F-003 → the **Sonnet 5 ultracode** dispatch session.
- 🟠 `substrate-kit` real gate fix + patch release → its lane wake (re-verify #228 first).
- 🟡 `superbot-mineverse` CSRF + schema + pytest-required.
- 🟡 `superbot` Rule-6 checker fix → the **superbot Codex** dispatch (verify+fix).
- 🟡 `superbot-idle` lift PLUG-001, build the adapter.

**The short owner-click queue (converts built → live):** the 5-item conversion queue in §5
+ attach-repo-to-routine + set-model-per-routine + pytest-required sweep. Canonical list:
`fleet-manager docs/owner-queue.md` (rewritten today; note the §4 drift before clicking).

---

**Provenance & verification.** 19 subagents, 0 errors, ~2.9M tokens, 2026-07-11; every
finding above carries a source citation in the run's journal
(`.../workflows/wf_796edbd3-38a/journal.jsonl`). Load-bearing claims were confirmed against
the live tree per Q-0120. **One unresolved divergence (substrate-kit #228, §3) is flagged
for re-verification, not resolved from memory.** Unverified-this-pass items are marked so
(product-forge future stamp; superbot-plugin-hello empty state — the repo was out of the
agent's session scope).
