# 2026-06-20 — AI self-introduction: advertise capabilities + available games

> **Status:** `complete`

## Arc
Owner asked (via Discord screenshot): when the bot is asked to *introduce itself* (or
similar), it should briefly explain its capabilities **and** the general things the bot
can do itself — e.g. which games are available. The screenshotted reply was a generic
"server management + BTD6 support" blurb that never mentioned games, economy, or
progression.

**Root cause:** `@SuperBot introduce yourself` routes to `general.nl_answer` and matches
no command-catalog trigger in `bot_knowledge_service`, so the only thing reaching the
model is the static persona (`_BOT_AI_POLICY` / `_TASK_CONTRACT`) — which frames scope as
BTD6 + server management only. Nothing told the model the bot runs games, an economy, or
progression, so it couldn't mention them.

## Shipped
- **`disbot/services/ai_instruction_service.py`** — new always-assembled system layer
  `_CAPABILITIES_OVERVIEW` (joins `_SYSTEM_SAFETY` / `_BOT_AI_POLICY` / `_TASK_CONTRACT`).
  It tells the model how to introduce itself (brief, grouped, invite follow-up, ground
  command names in the `bot_command_catalog` span when present, don't invent) and lists
  the **real** feature areas: general assistant + BTD6 expertise; the available **games**
  (Blackjack, Rock Paper Scissors incl. tournaments, Deathmatch, Counting, Chain, the
  Mining adventure, Fishing); economy + progression (coins, daily/work, XP, levels,
  leaderboards, profiles); server management. Explicitly steers the BTD6 mention to
  *general terms* (no ungrounded tower/hero/paragon names or numbers) so the intro is not
  floored by the faithfulness guard.
- **`disbot/services/bot_knowledge_service.py`** — added introduction phrasings
  (`introduce`, `who are you`, `what are you`, `what do you do`, `what do you offer`,
  `tell me about yourself`) to `_CATALOG_SUBSTRING_TRIGGERS` so an introduction also
  injects the live command catalog (an intro *is* a capability question).
- **Tests:** `tests/unit/services/test_ai_instruction_capabilities.py` (pins the overview
  content, games list, BTD6-grounding-safety wording, and its presence in every assembled
  system prompt) + intro phrasings added to `test_bot_knowledge_service`'s trigger matches.
- **Docs:** `docs/subsystems/ai.md` "Current state" note — where the bot's self-description
  lives (the static overview layer, *not* a DB instruction profile).

## Findings / verification
- `python3.10 scripts/check_quality.py --full` → **10956 passed, 44 skipped**, lint + mypy
  clean. `check_architecture.py --mode strict` → exit 0 (only pre-existing `[known]`
  warns). `check_docs.py --strict` → green. Doc-pinning tests green.
- Faithfulness-guard trace: an intro says "Bloons TD 6" → `general_path_should_verify`
  fires → `validate_btd6_reply` runs over the reply. None of the game names (Blackjack,
  Mining, Chain, …) are BTD6 *entity* proper names in the grounding name index, so a
  general-terms intro has zero offending names → passes. The new "keep BTD6 general"
  instruction is what keeps it that way if the model is tempted to name an entity.

## Context delta
- **Needed but not pointed to:** the *introduction* text is model-generated from the
  instruction stack — there is no canned intro string. Tracing it meant reading
  `ai_instruction_service.assemble` → `bot_knowledge_service.gather` (trigger gating) →
  `natural_language_stage` (assembly order) → `btd6_grounding_service` (why a BTD6-themed
  general reply can be floored). The AI folio now records where the self-description lives.
- **Pointed to but didn't need:** `ai_introspection_service` / `ai_tool_catalogue` — they
  model AI *lookup tools*, not the bot's games/commands, so they aren't the right home for
  a capability overview (and `get_ai_tool_catalog` isn't offered when AI tools are off).
- **Discovered by hand:** the interaction between a capability overview that mentions BTD6
  and the general-path faithfulness floor — naming a specific BTD6 entity in an
  ungrounded intro would floor the whole reply. The fix is prompt discipline, captured in
  both the constant and a pinning test.
- **Decisions made alone:** (1) curated overview in the *static* system layer rather than
  a new DB-owned block or a generated feature manifest — the games list is low-drift and
  this is the same pattern `_BOT_AI_POLICY` already uses for scope; (2) games named at the
  category level (no exact command syntax) to avoid drift + the "don't invent commands"
  trap, with `!help`/the catalog for specifics.
- **Flagged for maintainer / known limits:** the games list in `_CAPABILITIES_OVERVIEW` is
  hand-curated — if a *new* game ships, add a word to that constant (the pinning test lists
  the current set). Not runtime-verified against a live provider this session (offline +
  unit only); the prompt-discipline guard against name-dropping a BTD6 entity in an intro
  is best-effort (retry-then-floor remains the backstop).

## 💡 Session idea (Q-0089)
A tiny **stdlib guard that pins `_CAPABILITIES_OVERVIEW`'s game list to the real game
cogs** — e.g. assert each named game has a corresponding loaded cog / `parent_hub="games"`
subsystem entry, so the curated intro can't silently claim a game that was removed (or
omit one that's the whole point of the ask). Captured as a candidate; not built this run
(the current list is correct and the test pins it), but it would make the overview
self-auditing the way the catalogue/ledger guards already are.

## ⟲ Previous-session review (Q-0102)
Reviewed the website two-site-split **ultracode review-refactor** session
(`2026-06-19-website-split-review-refactor.md`). **Did well:** it declared file-disjoint
refactor units up front in the born-red card and found a genuine *cross-app* CI bug
(bare-name `sys.modules` collision between `botsite/` and `dashboard/`) that only surfaces
when both apps load in one test process — exactly the kind of latent defect a careful
read-every-line pass should catch. **Could improve / system note:** that bare-sibling-
import pattern (deploy with Root Directory = the app folder, import siblings by bare name
+ a `sys.path` shim) is a recurring footgun across the two web apps; it deserves a one-line
entry in the journal's "recurring problems" so the *next* web-app author designs around it
instead of rediscovering it via a flaky cross-suite failure. The improvement I initiated
this session is the smaller analogue: documenting in the folio *where* a behaviour lives so
the next agent doesn't have to re-trace the stack.

## 📤 Run report
- **Did:** make the bot's self-introduction advertise its real capabilities + available
  games · **Outcome:** shipped
- **Shipped:** PR (this session) — `_CAPABILITIES_OVERVIEW` instruction layer + intro
  catalog triggers + tests + AI-folio note
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (merge auto-deploys to Railway; the new behaviour is live
  on the next mention after deploy)
- **⚑ Self-initiated:** none (direct owner request)
- **↪ Next:** unchanged — the current-state ▶ Next ungated startable (consistency-linter
  AI-nav PR 1 / procedures→skills Batch 2 / a fresh `docs/ideas/` promotion)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (PR opened; auto-merge on green) |
| CI-red rounds | 0 (green on first full local mirror) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (Q-0089 — game-list/cog parity guard) |
| Ideas groomed | 0 |
