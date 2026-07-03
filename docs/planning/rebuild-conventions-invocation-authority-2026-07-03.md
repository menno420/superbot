# Rebuild Phase A — conventions freeze: naming · invocation · authority (2026-07-03)

> **Status:** `plan` — **Phase-A companion decisions log #2**, the "conventions freeze" the
> [Stage-1 global review](rebuild-stage1-global-review-2026-07-03.md) §6 recommended before the
> subsystem walk. Records the owner-live decisions on the cross-cutting contracts every subsystem
> plan inherits: **command naming, the invocation ladder (incl. the fuzzy typo matcher + AI
> orchestration), mod-actions-as-data, and the authority model.** Plus a set of **proposed**
> invocation-stack centralizations (§6 — pending owner reaction, not yet decided).
> **Provenance:** owner + agent live session 2026-07-03 (PR #1680), continuing #1679. Owner
> rulings → **Q-0224…Q-0228**. Frozen capstone artifacts unedited; deltas feed Gate-0. Source
> wins over this doc (Q-0120).

---

## 1. Command naming — namespace by *shared verb*, computed from the corpus (Q-0224)

**Decision.** Not blanket-grouped, not blanket-flat. A command takes an explicit grouped form
`/area verb` (`/ticket close`) **only when its verb is shared across 2+ subsystems**; a verb used
by exactly one subsystem stays a flat top-level command (`/balance`). Wherever there is an obvious
primary use, the command **works with no arguments** via a sensible default.

**The anti-liability rule (why this never forces a retroactive rename).** The liability with
"namespace when reused" is a command shipping flat (`/close`) then being *forced* into
`/area close` when a second `close` appears — a breaking rename. The rebuild dodges it entirely:
**the full 271-command corpus is already known**, so the "shared-verb set" is computed **once, at
design time** — every verb used by ≥2 areas is namespaced from day one, every unique verb is flat
from day one. No collision is ever discovered at runtime. The namespace registry (K1) then
**permanently reserves each flat name** so nothing can later claim it. The rule is mechanical, not
a per-command judgment call.

**Safe-default guardrail.** No-argument defaults are for **read / common** actions
(`/balance` = your own, `/leaderboard` = the main board). A **destructive or ambiguous** action
(ban, purge, delete) **never** has a default that acts — it requires explicit arguments.

**Consumes:** the shared-verb computation is a concrete Stage-2 input (run it over the corpus and
publish the flat-vs-grouped list per subsystem). Feeds K1's reservation set.

---

## 2. The invocation ladder — four front-ends into one command engine (Q-0225)

Every way to invoke the bot sorts into four rungs, most-deterministic (cheapest, always-on) at the
bottom to most-powerful (AI) at the top. **All four resolve to the same declared commands** through
one resolution + authority + validation point (§6 C-1). The bottom two need **no AI**, so the bot
is fully usable with AI off or the provider down — this preserves the plan's deterministic-first
ordering (AI is L4, on top of the L0–L3 deterministic platform; the parser is **never a dependency**
of a core command).

| Rung | What | Determinism | Notes |
|---|---|---|---|
| **1 — exact** | slash · classic prefix · additive custom trigger strings | deterministic | §2.1 |
| **2 — fuzzy** ("the global parser") | a typo / near-miss → the nearest real command | deterministic, no AI | §2.2 |
| **3 — NL intent** | plain language → *one* command (`"how much do I have?"` → `/balance`) | AI | §2.3 |
| **4 — NL orchestration** | a *goal* → a *multi-step draft* → preview → Accept → atomic execute | AI + draft lane | §2.4 |

### 2.1 Exact — slash + prefix + additive custom triggers

- **Slash** is the discoverable default (autocomplete, native permission gating, can't be typed
  wrong). **Classic prefix** stays supported.
- **Custom triggers are additive, never overriding.** A guild / channel / user may set custom
  invocation strings (the Dank-Memer-style `pls <command>` idea, but the word is configurable and
  scoped). For any message the bot checks the **union** of {global default, guild words, this
  channel's words, this author's words} — a narrower scope only ever *adds* a way to invoke; it can
  never disable a broader one. Setting a trigger is therefore always safe and reversible.
- **Validated when set:** minimum length + a common-word blocklist + a small per-scope cap, so a
  guild can't set `the` and make the bot fire on half of chat. (Set-time checks only; they don't
  touch the additive runtime behavior.)
- **Silent on no-match:** input after a string/prefix trigger that does **not** resolve to a valid
  command is **silently ignored** — no "unknown command" reply, no reaction. Because triggers can
  be ordinary words, a non-match is treated as normal chat. (Slash is exempt — Discord validates it
  before it arrives.)

### 2.2 Fuzzy — the typo matcher ("the global parser" the owner originally meant)

Its job: decide **when a typo is a real command.** Deterministic, cheap, AI-free. *State today:*
fuzzy matching exists **scattered** (setup advisor, preset service, channel recommender) but there
is **no central command-typo resolver** — a prime centralization target (§6 C-5).

**Three confidence tiers:**
- **Very close** (1–2 chars off, unambiguous) → **run it directly** — but **only for safe
  commands.** A destructive command is **never** auto-run from a guess.
- **Close but uncertain** → **a private "did you mean `/balance`?" prompt** to that user, one tap
  to confirm.
- **Not close** → **silent** (the no-spam rule — treat as chat).

*Owner-confirmed* including the "very-close + safe = run directly, no prompt" tier.

### 2.3 NL intent — language → one command

The existing central natural-language stage (`core/runtime/ai/natural_language_stage.py`) —
already general ("one pipeline owns 'should the bot reply?' for every handler"), already audited
(one `ai_decision_audit` row per message), today mostly used by BTD6 and behind AI gates. **"Make
it mainstream"** = elevate it to a first-class invocation path across all domains. Payoff: because
every command is declared, **the NL router can be generated from the same manifests** — each
command's description *is* the intent surface — so it inherits every command automatically instead
of being hand-wired. Obeys the same silent-unless-confident rule.

### 2.4 NL orchestration — goal → draft → preview → Accept → execute

The owner's target: *"create 10 game channels for a D&D tournament for teams of 4"* → the AI
composes a **template / plan** → shows a **preview of exactly what will happen** → the user presses
**Accept** → it executes atomically.

**This is not new architecture — it is the already-designed draft lane with a new producer.** The
draft lane (proposed operations → Final Review preview → confirm → one audited atomic apply)
already exists in the design. The only new idea is **who produces the draft**: today a human clicks
through setup; here the AI composes the same draft from one sentence. **One pipe, two producers
(human or AI)** — same preview, same Accept, same atomic apply, same audit. It is also the concrete
form of the plan's flagged **compound-composition** uncertainty (the farm-`collect` canary) — this
example becomes a canary for it.

**Default posture (owner-decided): the hybrid.** The parser may **answer freely** (low-risk,
read-only) but must require a clear signal (mention / reply / designated channel) before it
**acts** — and any action always runs through the rung-4 confirm. This gives the "always-there"
feel without the bot barging into every conversation or burning AI cost on messages never meant for
it (the free-for-everyone cost posture). Destructive actions reached by any AI rung **always**
confirm.

---

## 3. Moderator actions — declared as data (Q-0226)

**Decision.** A moderator action (warn / timeout / kick / ban) is expressed as a **declarative
envelope** — target, role-hierarchy check, DM-to-user, message cleanup, audit row, log route — that
the engine executes; **only the "how far to escalate" decision remains a small handler.** Chosen
for **testability**: a declared action is simulable and golden-testable; hand-written code is not.
This lifts moderation from the audit's 64% toward the generated-quality of the rest of the bot, and
puts "what a mod action does" in one place. **Grammar-level → decided before the Gate-0 freeze.**
The plan's ~1-hour spot-check (express one real action — e.g. a timeout — against the grammar and
confirm the envelope fits) is the confirmation step before the freeze; it resolves the FINAL-REVIEW
`ModerationActionSpec` uncertainty in favor of the envelope.

---

## 4. Authority — one layer, plus a bot-owner global override (Q-0227)

**Decision.** One authority layer for the whole bot: **every action carries a single declared
authority label** (e.g. `moderation.ban`) mapped to roles / Discord permissions **in one place**
and **re-checked at execution time**. On top of it sits a **global bot-owner override**: the bot
owner (by ID, as in the current bot — Q-0212) can run **any** command in **any** server, including
things normally locked to the server owner (setup, etc.), so the owner can help friends configure
their servers.

- **Verification requirement (a concrete acceptance test):** a **"bot-owner can run everything,
  everywhere" check** walks every command and asserts it succeeds for the bot-owner identity in any
  guild. Mechanical, part of parity.
- **Transparency guardrail:** when the bot owner runs an action in *someone else's* server, that
  action is **loudly written to that server's audit log** — never silent. Full reach for the owner,
  full visibility for the server owner.

Consistent with Q-0212 (already the current bot's decision); this pins it as a rebuild grammar
contract and adds the verification + transparency clauses.

---

## 5. How this all rides the generalization standard (S-1, Q-0219)

Each of the above is **one engine steered by data**, per the Stage-1 keystone:

- **Invocation:** one invocation engine; the four rungs are front-ends; per-scope trigger settings
  are the data. Adding a rung or a trigger scope doesn't touch any command.
- **Naming:** the K1 registry is the one engine; the shared-verb set + reservations are the data.
- **Mod actions:** one action engine; each action is a declared envelope (data); escalation is the
  lone Tier-3 handler.
- **Authority:** one authority engine; the label→roles map is the data; the bot-owner override is a
  single top-tier rule.

---

## 6. Invocation-stack centralizations — owner-endorsed foundations (Q-0228)

Owner asked "what else related to this could we centralize?" then confirmed: *"yes all the things
you mentioned are good candidates to further think about and properly decide upon, your
recommendations are good foundations and should be documented."* So the seven below are
**endorsed directions to build toward**, documented here as the foundations; each item's *detailed*
contract (scope, exact shape) is decided in its Gate-0 / Phase-B plan. (Applies the second-consumer
rule to the invocation/command area.)

- **C-1 — The command resolver (the convergence point).** *Strongly recommend.* All four rungs
  must funnel through **one** resolver that takes "a candidate command + args" and applies
  authority (§4), argument validation/coercion, cooldowns, and audit — then runs it. Without this,
  each rung re-implements auth/validation and they drift. This is the single most important
  centralization in the stack.
- **C-2 — One preview/confirm/apply (draft) pipeline, two producers.** The rung-4 AI drafts, the
  fuzzy-corrected destructive action, the NL-triggered action, **and** human setup all use the
  *same* preview → Accept → atomic-audited-apply path (§2.4). One confirmation UX, one apply seam.
- **C-3 — A template primitive.** The AI's "10 channels for a D&D tournament" is a **template** — a
  named, reusable draft. Templates exist today scattered (`setup_role_templates`,
  `automation_templates`, channel recommenders). Centralize into **one template primitive** a human
  *or* the AI can instantiate → feeds C-2. Directly serves the owner's D&D example and unifies
  existing setup templates.
- **C-4 — One response / result grammar.** How the bot reports success / failure / denial / "here's
  the result" — one consistent vocabulary (the `WorkflowResult` shape) so every command, however
  invoked, looks and behaves the same, and the silent-vs-reply decision lives in one place.
- **C-5 — One fuzzy/"did-you-mean" engine.** Fold the scattered `difflib` uses (§2.2) into one
  matcher used by the typo rung, presets, recommenders, and error suggestions. One threshold
  policy, one private-suggestion renderer.
- **C-6 — One cooldown / rate-limit engine.** Per-user / per-guild / per-command limits in one
  place instead of per-command ad hoc — also the free-for-everyone abuse posture's natural home.
- **C-7 — One description surface, many consumers** (already implied by the manifest bet, named
  here for completeness): each command's manifest description feeds the slash help, the help
  projection, the NL router's intent surface, the fuzzy candidate set, and the "did you mean" text.
  Write it once.

---

## 7. What this closes / what's next

- **Closes** the Stage-1 §6 "conventions freeze" agenda items: naming scheme + slash/prefix policy
  + collision rule (§1–2), the `ModerationActionSpec` uncertainty (§3, envelope), the authority
  model (§4). **Still open from §6:** the G-22 staging-lanes standardization (untouched here).
- **Feeds Gate-0:** §1–4 are grammar/contract decisions to fold; §6 proposals become contracts on
  owner blessing.
- **Next (Stage 2 — the subsystem walk):** run the shared-verb computation over the corpus; per
  subsystem set exact command names + kind + hub placement + outperform list + the D-5 triage
  verdict; write the method/seam vocabulary as S-1 applications.

## 8. Pointers

- Stage-1 log (this doc's parent): [`rebuild-stage1-global-review-2026-07-03.md`](rebuild-stage1-global-review-2026-07-03.md)
- Generalization standard: Q-0219 (§2 S-1 of the Stage-1 log)
- The NL stage this builds on: `disbot/core/runtime/ai/natural_language_stage.py`
- Owner rulings: **Q-0224 (naming) · Q-0225 (invocation ladder) · Q-0226 (mod-actions-as-data) ·
  Q-0227 (authority + bot-owner override) · Q-0228 (centralization proposals)** in
  [`../owner/maintainer-question-router.md`](../owner/maintainer-question-router.md)
- Session log: `.sessions/2026-07-03-rebuild-conventions-freeze.md` (PR #1680)
