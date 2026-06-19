# 2026-06-19 — Open-question sweep (question panel)

> **Status:** `complete`
> **Run type:** `manual`

## Arc

Owner-directed interactive session: *"ask me all currently open questions with your
question panel and include a recommended option, also come up with any new questions
that might be useful for the next parts of the plan."* Mapped the 180 Q-blocks in
`docs/owner/maintainer-question-router.md`, isolated the genuinely-open set, and put
them to the owner in **3 question panels** (each with a recommended option), folding in
forward-looking new questions for the active website two-site-split wave. Recorded every
answer back into the router (faithful preservation — the answers' durable home).

## Answers captured (owner, question panel, 2026-06-19)

**Parked product lanes**
- **Q-0175 fishing v1** — leveling = **both** (a fishing skill off `game_xp` unlocks the
  size tier *and* rod tier boosts catch quality; gear never *required*, only a bonus) ·
  fish value/use = **sell + cook** (a deliberate Phase-1 economy *reconnect* — re-introduces
  a coin/consumable path #1039 removed, so it needs its own balance plan, not a silent
  revert) · catch mechanic = **instant deterministic roll for v1** (minigame deferred).
  *Still open:* loadout-preset UI · boat travel.
- **Q-0173 mining grid** — **one shared seed-deterministic grid** (same world for everyone,
  shareable). *Still open:* move-cost/encounters · cell-yield→depth-band mapping.

**Workflow / infra**
- **Q-0077 BTD6 auto-seed** — **(b) auto-seed when bundled files are strictly newer** (true
  zero-touch; never clobbers a deliberately-newer store). Build beside the #676 drift warning.
- **Q-0171 Codex** — **augment only, no merge authority** (advisory second reviewer; routines
  verify-then-fix; humans/Hermes keep merge authority).
- **Q-0176 auto-merge skip `needs-hermes-review`** — **deferred** (born-red gate stays the
  single safeguard for now).
- **Q-0177 #1 dependency-lock** — **(a) pip-tools compiled lockfiles, dashboard first** (own
  2-PR plan).

**Tooling + website wave**
- **Q-0096 plugins** — **stay as-is, Context7 only** (Postgres-MCP / pyright-lsp declined for now).
- **Website (Q-0178/Q-0179)** — bot changelog **seeded from shipped-feature/ledger history** ·
  v1 launch-wave must-haves = **command reference + `/submit` form + changelog** (showcase +
  status widget follow) · control-API public-exposure security review = **external / Codex
  pass + human sign-off**, after the first additive wave.

## Shipped

- `docs/owner/maintainer-question-router.md` — recorded all answers into their Q-blocks across
  three commits: (1) the 9 panel answers (`08ea68a` — flipped the two literal `Status: Open` blocks
  Q-0077/Q-0096; appended decisions to Q-0171/Q-0176/Q-0177/Q-0179); (2) the 4 single-clean-answer
  follow-ups (`7e44778` — Q-0175 loadout UI/boat, Q-0177 #2 control-API hardening, Q-0177 #4
  roadmap-mirror); (3) the two mining-grid forks (Q-0173 — grid scope, depth mapping, movement/
  encounters), routed into `docs/planning/mining-hub-redesign-2026-06-15.md` as their build home.

### Follow-up answers (owner, second round, same session)

- **Q-0173 mining grid (the two genuine forks, panel):** grid scope = **one shared grid** · depth
  mapping = **vertical axis = existing depth bands** (preserves the tuned economy + descent metaphor;
  per-cell seeded variety within a band) · movement = **free, no encounters in v1**; encounters are
  **wanted as a later own-session layer**, shaped **depth-gated + sparse** ("after a certain depth,
  not too many"). Routed to the mining-hub-redesign plan.
- **Single-clean-answer records (no panel, per owner directive):** Q-0175 loadout UI = **reuse the
  Gear-panel pattern + `!loadout`, manual swap v1** · Q-0175 boat = **Phase-2 deferred** · Q-0177 #2
  control-API hardening = **security gate: no public exposure of writes without signing + idempotency
  + rotation, folded into the Q-0179 migration** · Q-0177 #4 roadmap→issue mirror = **do not adopt**
  (one source of truth; public visibility already covered). Q-0177 #3 pointer README left untouched
  (owner's prior "optional, not now").

## Decisions made alone

- None of product substance — the substantive choices are the owner's panel answers. Judgment
  calls limited to *how to record*: flag the fishing "sell + cook" answer as a **deliberate
  economy reconnect needing its own plan** (rather than silently overwriting the #1039 no-coins
  design), and record the recommended option's provenance on each block.

## Flagged for maintainer / known limits

- The answers are **recorded, not yet built**. Each unblocks a lane that is its own future
  session: fishing-plan update (skill+rod leveling, sell+cook economy reconnect, instant-roll
  v1) · BTD6 boot auto-seed (runtime, `btd6_cog.cog_load`) · pip-tools lockfile 2-PR plan ·
  website wave build · the small `code-quality` deps lockfile follow-ups.
- Still-open sub-parts remain owner-deciding: Q-0173 (move-cost · yield mapping), Q-0175
  (loadout-preset UI · boat travel). Not resolved unprompted.

## Context delta

- **Needed but not pointed to:** the router has no machine-readable "open vs answered" index —
  open questions are found only by grepping `Status:` lines + reading recent Q-blocks, and
  several "open" items are *sub-parts* of otherwise-DIRECTED blocks (Q-0173/Q-0175 "still open"
  lists), which a status grep misses. A `scripts/check_open_questions.py` that lists unanswered
  Q-blocks (incl. "still open" sub-lists) would make this sweep one command.
- **Pointed to but didn't need:** the bulk of `current-state.md` (413 lines) — the open-question
  set lives in the router, not the ledger; the ▶ Next-action line alone gave the wave context.
- **Discovered by hand:** Q-0121 and Q-0147 read as "open" in `current-state` prose but are both
  DECIDED in the router — current-state references them as *gate provenance*, not open items.

## 💡 Session idea (Q-0089) — BUILT this session

The idea: surface every genuinely-open question in one command — including the **sub-part** opens
parked inside otherwise-decided blocks (the Q-0173/Q-0175 case a `Status:` grep misses). I proposed
a new `scripts/check_open_questions.py`, but the **do-not-duplicate gate (Q-0170) redirected it**:
`scripts/router_status.py` already digests the router (next-number + leading-marker OPEN/DECIDED).
Its real gap was *exactly* the sub-part case — it reads each block's **leading** marker only. So
rather than clone it, I **extended `router_status.py`** with a conservative open-sub-part detector
(a new `PARTIAL` bucket + `--subparts`), root-fixing the gap in the existing tool instead of adding
a second one. Verified live: it reports the now-resolved Q-0173/Q-0175 as clean and immediately
surfaced the one remaining genuine open block (**Q-0137**, Hermes-dispatch wiring). Tests cover
open / resolved / struck / prose-mention + a live-file invariant. Disposable (Q-0105).

## ⟲ Previous-session review (Q-0102)

Previous session (#1123, website-split next-steps) cleanly advanced the two-site-split foundation
and kept `current-state` ▶ Next-action sharp — good. What it (and the band before it) **missed**:
the router's open-question backlog had quietly grown to ~9 genuinely-open items spread across
product/workflow/website lanes with no single surface listing them, so it took a full grep-and-read
sweep to assemble — exactly the gap the session idea above closes. **System improvement surfaced:**
the open-question set deserves a generated index (and a dashboard inbox card), so "what still needs
the owner?" is answerable without a manual router crawl.

## 📤 Run report

- **Did:** asked the router's open questions via 3 recommendation-bearing panels + new website-wave
  questions, recorded every answer into the router, then built the open-sub-part detector into
  `router_status.py` (the Q-0089 idea) · **Outcome:** shipped
- **Shipped:** no PR yet — pushed to `claude/charming-hypatia-a5qhku`: the router/plan recordings
  (`08ea68a`, `7e44778`, `e5c30f7`) + the `router_status.py` open-sub-part detector + tests; owner
  to confirm opening the session PR
- **Run type:** `manual`
- **⚑ Owner decisions needed:** `none` — every open question + sub-part is now resolved (panel or
  single-clean-option record). The tool confirms only **Q-0137** (Hermes-dispatch wiring, "PARTLY
  DECIDED") remains genuinely open — a design conversation, not a panel question. Owner's own
  explicit deferrals also stay parked: Q-0175 boat travel (Phase 2), Q-0177 #3 pointer README, the
  *later* depth-gated encounters session
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** `router_status.py` open-sub-part detector — the Q-0089 idea promoted to a
  build (owner authorized open-ended "work on something of your choice"; flagged here for
  transparency per Q-0172). Read-only/stdlib/disposable; no runtime/`disbot/` code
- **↪ Next:** build the now-unblocked lanes in their own sessions — BTD6 boot auto-seed (contained,
  one file) · pip-tools dashboard lockfile · website additive wave (cmd-ref + `/submit` + seeded
  changelog) · fishing-plan update (skill+rod · sell+cook economy reconnect · instant-roll v1)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (recording pushed to branch; PR pending owner go) |
| CI-red rounds | 0 |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`check_open_questions.py`) |
| Ideas groomed | 0 |
