# SuperBot's product North Star — free for everyone, forever

> **Status:** `ideas` — **but the core principle is an owner-decided North Star** (router
> **Q-0190**, 2026-06-21) and is binding like any routed decision. Only the *strategy and tactics*
> below (competitive framing, enforcement ideas, open questions) remain capture-only — route them
> through [`README.md`](README.md) before implementing. Source code, binding contracts, and
> `docs/current-state.md` win over anything here.
>
> **Subsystem:** none  *(product-wide principle — touches every subsystem, maps to no single one)*
>
> **Captured / decided:** 2026-06-21 (owner-directed, in-session; the agent recorded it and the
> owner ratified the one open fork live via the question panel).

## 1. The North Star (owner-voice, 2026-06-21)

> *"The new goal will be to become a completely free all-inclusive bot, because I believe that
> online functions should be available for anyone — so maybe we can eventually make all Discord
> bots go out of business because ours is free and better."*

The owner had been considering a limited/freemium model ("monetize it somehow, but only for
limited features") and **deliberately rejected it.** The decision: **SuperBot is free for everyone,
forever.** Every function is available to every user — **no paywalls, no premium tiers, no freemium
feature-gating, no subscriptions, no pay-to-win.**

**The deeper rationale (owner-voice, 2026-06-21):**

> *"The main reason I'm locking in this decision is because I don't think it's fair that people are
> paying for functions like this. I really hope that eventually people will realize that instead of
> 5+ bots with paywalls, they can just use 1 free bot that takes care of everything — so maybe we can
> start a 'revolution' that makes everyone abandon their old bots so none of them make any money
> anymore."*

So the goal is **values-first** (it isn't *fair* to paywall basic online functions) with a
**competitive thesis** attached: a single **free, all-inclusive** bot that does what **5+ paywalled
bots** do removes every reason to pay for any of them. *Free **and** better — and all-in-one* is the
wedge; the ambition is a "revolution" where the paywalled incumbents lose their revenue base. This is
why **"all-inclusive" is load-bearing, not decoration**: the strategy is **consolidation** — SuperBot
must eventually cover the big bots' headline features (the **V-14 feature-mining** lane is exactly
this), because *"just use one free bot for everything"* only works if the one bot really does
everything.

## 2. What it forbids / what it permits (the precise boundary)

**Forbidden — never propose or build:**
- Paywalls, premium/VIP **feature** tiers, freemium gating of any function.
- Subscriptions or per-feature unlocks.
- Pay-to-win: no real-money benefit touches XP, coins, drops, odds, cooldowns, market access/fees,
  guild power, or any game outcome (the standing **Q-0039** rule).
- Bot-side billing / payment processing / stored donor or payment data (**Q-0039**).
- Gating a *core capability* behind a purchase or another ecosystem (the **Q-0087** boundary).

**Permitted — the only money surface:**
- A **voluntary, zero-benefit** "support us" / sponsor / donation link, purely to offset hosting +
  AI cost, granting **nothing functional** (owner's live pick, 2026-06-21, resolving tension **T-6**
  — see §4). Cosmetic-only supporter recognition remains allowed exactly as **Q-0039** specifies (a
  badge/title/flair read from an externally-managed Discord role; the bot stores no payment data).

The line is simple: **money may never change what the bot can do for you — only, optionally, say
"thanks."**

## 3. Why this is an elevation, not a reversal

The codebase already leaned free; the North Star consolidates scattered per-feature calls into one
binding principle and closes the one door left ajar (a freemium *feature-tier* model):

| Existing decision | Relationship to the North Star |
|---|---|
| **Q-0039** — donations cosmetic-only · no bot-side billing · hard no-P2W; premium currency rejected | The North Star **generalizes** Q-0039 from *the economy* to *the whole product* — no feature-gating anywhere, not just in games. |
| **Q-0108** — paid moderation tiers **declined** | A concrete instance of the North Star, now the general rule. |
| **Q-0080** — public bot is the goal | The North Star is the *product posture* for the public push: free is the adoption engine. |
| **Q-0087** — no core capability gated behind cross-ecosystem investment | The same "core stays ungated" principle, applied to the open-world design. |
| **V-14 / competitive-teardown** — harvest the best features from the big bots | Supplies the "**and better**" half of "free and better": SuperBot offers *their* best features, free. |

## 4. The resolved tension (T-6) and the sustainability reality

The vision doc + router already flagged **T-6**: a public bot's AI cost grows with guild count,
while revenue is pinned near zero and the **Q-0082** AI-spend ceiling is fixed. The North Star
**commits to keeping revenue at (near) zero permanently**, so the Q-0082 degradation grammar is now
the *primary* sustainability lever, not a fallback:

- AI **default-off** per guild (**Q-0040**); tiny derived per-guild budgets; heavy
  caching/templating; **visible, in-world** degradation ("the storyteller is resting") rather than
  silent overspend.
- The owner consciously accepts that hosting + base AI cost is owner-funded, offset only by the
  voluntary support surface in §2. This is the deliberate trade for the values goal — recorded here
  so no future session "resolves it silently" by reaching for a paywall (the explicit T-6 warning).

## 5. Open questions (captured, not blockers)

1. **Open-source / self-host? — ANSWERED (owner, 2026-06-21).** The repo is **already public and
   MIT-licensed** (`LICENSE`, © Menno van Hattum), so the source is *legally* reusable by anyone
   **right now** — and that is the "free for everyone" ethos taken to its conclusion, not a threat to
   it. The owner's position: reuse should **eventually be easy, but is not recommended yet** —
   *"there's still a lot of moving around to do before this code is actually solid."* So the gate is
   **code maturity, not licensing**: the road to recommend-able reuse is the ongoing repo-organization
   work (architecture atlas · consistency linter · the repo-structure-improvement plan) maturing — not
   a license or policy change. No "self-host / quickstart" docs until the structure settles.
2. **Enforcement tooling.** Should a disposable lint (**Q-0105**) flag any new
   "premium/paywall/paid-tier-gate" language creeping into docs or code? The Q-0039 CI invariant
   already guards the *economy* (no supporter predicate in odds/reward/cooldown/fee paths); a
   product-wide guard would need a careful allowlist (the words "free"/"premium"/"paid" have many
   innocent uses). Captured as this session's idea — see the session log.
3. **The voluntary-support surface itself** (a `/support` command / footer link) is *allowed* but
   **not yet designed or built** — it ships only with its own small plan when wanted.

## 6. For agents — how to apply this

- Treat "free for everyone" as a **binding design filter** every new plan inherits (like Q-0080's
  public-bot filter). If a feature's design implies gating it behind payment, that design is wrong —
  find the free shape.
- The enforceable form lives in `docs/current-state.md` ▶ Off-limits and **router Q-0190**; the
  positive principle lives in `docs/roadmap.md`. This doc is the full *why*.
- Do **not** restate the whole mission elsewhere (one-fact-one-home) — link here.

---

*Cross-links: router **Q-0190** (the decision) · **Q-0039** (fairness boundary) · **Q-0080** (public
goal) · **Q-0082** (AI ceiling) · **Q-0087** (no core-gating) · the vision doc
[`superbot-vision-2026-06-10.md`](superbot-vision-2026-06-10.md) (tension T-6) · the
[`competitive-teardown-2026-06-10.md`](competitive-teardown-2026-06-10.md) (the "and better" half).*
