# Handoff — AI provider-switch + BTD6 grounding fix plan

> **Status:** `plan` — working handoff for the *next* session (not a binding contract).
> Written 2026‑05‑29 after a long live‑testing session. **The code is always the
> source of truth — verify before trusting any BTD6 fact stated here.** The prior
> session made mistakes precisely by trusting memory over the data; don't repeat that.

---

## 0. For the executor — read this first

1. Read `.claude/CLAUDE.md` and `docs/AGENT_ORIENTATION.md` (binding workflow + reading order).
2. **Standing authorization to open PRs** (CLAUDE.md §Session workflow) — open a PR at the end of each unit of work without re‑asking.
3. **One PR per *fresh* branch.** Do NOT reuse a single branch across multiple sequential PRs — last session did, and it muddied history and the chat PR‑card UI. Use the branch this session is assigned; if you do multiple PRs, branch fresh from `main` for each (merge/rebase as needed).
4. **Gates before every push** (CI parity — always `python3.10 -m`):
   ```
   python3.10 scripts/check_architecture.py --mode strict \
     && python3.10 scripts/check_quality.py --check-only \
     && python3.10 -m pytest tests/ -q
   ```
5. **Do the PRs in order (PR1 → PR2 → PR3).** PR1 unblocks Claude; while the bot is stuck on `gpt-4o-mini`, most "hallucination" is just model quality and you'll be chasing noise.
6. If something is ambiguous or architecturally significant, **leave it and note it** in the PR rather than guessing.

---

## 1. Why this exists — live testing (2026‑05‑29)

Real users tested the bot for hours (full transcript was provided as a one‑sided eval). Two compounding failures:

- **The bot can't be switched to Claude** — the settings UI only offers `openai`, and the guild policy overrides any env routing.
- **`gpt-4o-mini` hallucinates BTD6 facts constantly** — wrong MOAB/BFB/BAD HP, wrong RBE, "MOABs need special damage" (false), Desperado miscategorised, contradictory answers to the same question, identifies as "created by OpenAI". The *deterministic* stat embeds are correct, which proves **the data is fine and the AI grounding/retrieval path is the problem.**

---

## 2. Verified root causes (with file:line)

### Problem 1 — trapped on OpenAI
- `disbot/cogs/ai/schemas.py:50` `_validate_provider` and `:147` `allowed_values=("deterministic","openai")` → the `!ai` provider dropdown can never offer `anthropic`.
- `disbot/services/ai_policy_mutation.py:139` — same allowlist; the mutation **rejects** `anthropic`.
- `disbot/core/runtime/ai/gateway.py` `_overlay_guild_policy` — a non‑empty guild `default_provider` (DB) **overrides** env `AI_ROUTING_*` / `AI_DEFAULT_PROVIDER`. The guild is set to `openai`, so env vars are silently ignored.
- No **provider‑aware model validation** → a wrong id like `sonnet-4-6` (correct is `claude-sonnet-4-6`) slips through → 404 → degraded. Live symptom seen: `default provider=anthropic / active=deterministic / failures 2/2`.
- The runtime **does** support anthropic: `gateway.py:151` registers `AnthropicProvider`; `routing.py` has correct `claude-sonnet-4-6` / `claude-haiku-4-5` per task. **Only the policy/settings layer blocks it.**

### Problem 2 — grounding is gated behind a keyword router that was over‑slimmed
- BTD6 grounding only runs when the task router returns `BTD6_ANSWER`:
  `disbot/core/runtime/ai/natural_language_stage.py:618` (`btd6_context_service.build`) and `:427` (knowledge‑block enrichment).
- PR **#388** (prior session) slimmed `disbot/services/ai_task_router.py` `_BTD6_KEYWORDS` (removed `obyn`, `psi`, `ezili`, `geraldo`, `etienne`, mode phrases) on the theory the model self‑fetches via the `btd6_lookup` tool. **`gpt-4o-mini` does not reliably call tools** → those questions route to `general.nl_answer` → **no grounding injected** → it answers from memory. **This is a likely regression from last session — own it.**
- `ai_natural_language_enabled = False` (guild) → bot only answers @mentions. That's fine; just know passive replies are off.

### The data is (mostly) correct — do NOT "fix" it from memory
- `disbot/data/btd6/bloons.json`: MOAB 200, BFB 700, ZOMG 4000, BAD 20000; all paragons incl. **Dart Monkey paragon = "Apex Plasma Master", 150000** (it IS in the data — last session wrongly called this a hallucination).
- Likely **genuinely missing**: ability sub‑stats (ability uptime, crit damage, DoT). The "I don't have verified info" answers for Grand Saboteur uptime / Tech Terror Annihilation crit / Blazing Sun burn may be *correct*. Verify against the stats files before adding anything.

---

## 3. The plan

### PR 1 — Unblock Anthropic (FIRST, highest value)
**Files:** `disbot/cogs/ai/schemas.py`, `disbot/services/ai_policy_mutation.py` (+ tests).
1. Add `"anthropic"` to `_validate_provider` and `allowed_values` (schemas.py) and the mutation validator (`ai_policy_mutation.py:139`).
2. Make model validation **provider‑aware**: if provider is anthropic, reject non‑claude ids; **prefer leaving the model empty → routing auto‑picks** `claude-sonnet-4-6` / `claude-haiku-4-5` per task (`routing.default_model_for`). Stops the `openai + sonnet-4-6` mismatch.
3. Confirm/​document precedence: guild policy is the source of truth and overrides env (`_overlay_guild_policy`).
4. **Tests:** `set_policy(provider="anthropic")` succeeds and resolves a valid claude model; `provider="bogus"` still rejected; empty model auto‑picks.
5. **Acceptance:** in `!ai` settings you can pick Anthropic, it sticks, `!ai` shows active provider `anthropic` + a `claude-*` model, and an @mentioned BTD6 question answers correctly.

### PR 2 — Fix the grounding‑gating regression
**Files:** `disbot/services/ai_task_router.py`, `disbot/core/runtime/ai/natural_language_stage.py` (+ tests, + `tests/evals/cases.py`).
1. **Decouple grounding from the keyword router**: run `btd6_context_service.build` whenever the resolver finds a BTD6 entity — even on `general.nl_answer` — and/or re‑widen the `_BTD6_KEYWORDS`/entity set that #388 cut. Goal: a BTD6 question **always** gets grounding injected, independent of model. (Re‑verify the router's existing pinned tests in `tests/unit/services/test_ai_task_router_btd6_natural.py` still pass.)
2. Confirm the verify‑or‑disclaim discipline (`ai_instruction_service._TASK_CONTRACT`) still holds on the chosen model.
3. Investigate the **two contradictory answers to one question** (Boomerang "Glaive Lord" vs "Perma Charge" double reply) — likely `_split_for_discord` or a tool‑loop duplicating output in `natural_language_stage`.
4. **Encode the transcript failures as permanent eval cases** — *verify each correct answer from the data, not memory*: MOAB/BFB/ZOMG/BAD HP; "can every weapon type damage MOABs" (answer: yes — MOAB‑class has no damage‑type immunity); Desperado is its **own** tower (not a Sniper Monkey upgrade); tier‑5 ability names; RBE of a MOAB + children.

### PR 3 — Coverage + self‑knowledge
1. **Ability sub‑stats**: verify whether stats files carry ability uptime/crit/DoT; if absent, extend `scripts/fetch_bloonswiki.py` to ingest. Ensure upgrade/ability **names** are grounded (tier‑5 names were wrong).
2. **Command‑catalog mis‑scoping**: "what are the AI commands" returned BTD6 commands; "AI_cog commands" failed. Trace catalog retrieval + subsystem/access filtering (`bot_knowledge_service` / command catalog) and fix.
3. **RBE**: the bot can't compute RBE. Add RBE + children data (extend `bloons.json`?) and expose via a tool or grounding.
4. **"list only 3"**: a `limit` param was added to `btd6_superlative_lookup` (#392, on `main`). **Verify it works in prod AND hunt for any other hard 3‑cap** in user‑facing lists (this is the item the user said may have been missed).
5. **Identity**: bot should identify as **SuperBot** (optionally the model), not "created by OpenAI". Check the system prompt / identity handling.

---

## 4. Immediate no‑code unblock (only if PR1 isn't deployed yet)
Direct DB edit on the guild policy:
```sql
UPDATE ai_guild_policy SET default_provider='anthropic', default_model='' WHERE guild_id=<id>;
```
(empty model → auto‑picks `claude-sonnet-4-6`). Or `NULL` `default_provider` so the `AI_DEFAULT_PROVIDER=anthropic` env finally applies.

---

## 5. Reference
- **Model IDs:** reasoning → `claude-sonnet-4-6`; light → `claude-haiku-4-5` (if it 404s, the dated id is `claude-haiku-4-5-20251001`); OpenAI default → `gpt-4o-mini` (weak). User is trialing **`gpt-5.4-mini`** — it may require `max_completion_tokens` instead of `max_tokens` in `OpenAIProvider`; test one task and adapt the provider if it errors on params.
- **Provider precedence:** guild policy (DB) > env `AI_ROUTING_<TASK>` > env `AI_DEFAULT_PROVIDER` > `deterministic`.
- **Per‑task routing env** (the recommended split, set on Railway): default `openai` + `AI_ROUTING_GENERAL_NL_ANSWER`, `AI_ROUTING_BTD6_ANSWER`, `AI_ROUTING_BTD6_STRATEGY_REVIEW`, `AI_ROUTING_MODERATION_ASSIST`, `AI_ROUTING_SETTINGS_PROPOSE`, `AI_ROUTING_SETUP_SUGGEST`, `AI_ROUTING_LOGS_TRIAGE`, `AI_ROUTING_CODE_CONTEXT_EXPLAIN` = `anthropic`.
- **Evals harness** (`tests/evals/`, opt‑in `RUN_EVALS=1` + API keys, or GitHub Action `ai-evals.yml`) — the A/B tool; run openai vs anthropic vs gpt‑5.4‑mini.
- **Related docs:** `docs/btd6-data-pipeline.md`, `docs/btd6-ai-tool-calling-plan.md`, `docs/audits/repo-wide-audit-2026-05-29.md`.

## 6. Lessons from last session (don't repeat)
- **Verify against data/code; never assert BTD6 facts from memory.** (Last session wrongly flagged a correct Dart‑paragon answer as a hallucination because a diagnostic used `limit=12` against a 13‑item list.)
- One PR per fresh branch.
- Long sessions degrade quality — keep scope tight, gates green, verify every claim before stating it.
