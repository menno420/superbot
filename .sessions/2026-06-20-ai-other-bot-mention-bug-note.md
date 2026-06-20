# 2026-06-20 — BUG note: AI replies to other bots' mentions + Pokétwo demand signal

> **Status:** `complete`

## Arc

Follow-up to the Pokétwo/MusicBot feature-mapping plan (#1180, merged). The owner shared a
Discord screenshot showing two things: **(1)** a live bug — SuperBot's AI replied *"Hey! You've
just pinged me…"* to a message that pinged **`@Carl-bot`**, not SuperBot; owner: *"make a note of
this."* **(2)** a product signal — a real user runs **multiple bots** (poketwo + music) because we
lack those features; owner: *"make sure we have a similar/better version of the Pokémon system."*

Docs-only. The AI engagement path is gated/sensitive (Q-0086 wants a runtime walk) and the core
fix carries an owner behavior fork, so this **notes** the bug to the repo standard rather than
speculatively patching the gated path.

## Shipped (PR #1182, docs-only)

- **`docs/health/bug-book.md` — BUG-0019 (OPEN, root cause identified).** Two independent
  mechanisms: **(1)** `always_reply` ambient mode answers *every* message — including ones aimed at
  other bots — and the model hallucinates a "you pinged me" greeting because **other** users'
  mention tokens aren't stripped before the prompt (only SuperBot's own is, via
  `_strip_bot_mention`); **(2)** `natural_language_stage.py:229` uses `mentioned_in`, which
  discord.py returns True for on `@everyone`/`@here`, so a server-wide ping reads as a personal
  one. Proposed fix: the `@everyone` exclusion is an unambiguous hardening (direct-mention check +
  regression test); the `always_reply` behavior is a **fork routed to the owner** (stay silent when
  addressed to another bot · strip all mentions + never claim a ping · leave as power-user opt-in).
  Agent recommendation: option (a) + the `@everyone` hardening.
- **`docs/planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md`** — added the **live demand
  signal** callout (a real user runs multiple bots for these features) and a one-screen
  **"what Pokétwo actually does"** reference + parity map (the owner noted he's unsure what poketwo
  does; this makes the plan self-contained for his design call).

Verification: `check_docs.py --strict` ✓ · `check_plan_homing.py` ✓. No `disbot/` code touched.

## Why not patch the AI path this turn

The owner asked to *note* it; the AI engagement behavior is gated (Q-0086 — live AI changes want a
runtime walk with provider keys), and the central fix (`always_reply` semantics) is a genuine
design tradeoff — suppressing replies when other users are mentioned could break legitimate
always_reply use (*"hey @friend look — SuperBot what do you think?"*). Shipping a speculative
behavior change would risk either not fixing the screenshot (if it's the ambient path) or breaking
intended use. The faithful move is a precise note + a routed decision, ready to execute on his call.

## Decisions made alone

- Marked BUG-0019 **OPEN** (not a same-PR fix) — justified: the root fix needs an owner behavior
  decision + a runtime-verified session. Recorded the recommended fix so it's turn-key once decided.
- Filed the `@everyone` footgun in the **same** entry rather than a separate bug — same "false
  personal ping" class, same code stage.

## Flagged for maintainer

- **BUG-0019 behavior decision:** in `always_reply` channels, should SuperBot stay silent when a
  message is addressed to another user/bot (recommended), strip-all-mentions + drop the "pinged me"
  framing, or stay as-is? Plus: which channel mode is `goals-for-now` actually on? (confirms whether
  the `@everyone` hardening alone resolves the screenshot). I can implement immediately on his call.
- **Pokétwo priority:** the live demand signal raises the Pokétwo half's priority — pairs with the
  open **Q-0186** (which net-new lane first; recommend Lane A Wild Encounters).

## 💡 Session idea (Q-0089)

**An ambient-mode "addressed-to-someone-else" guard as a reusable predicate.** BUG-0019 is really a
missing primitive: *"is this message directed at a party other than us?"* (mentions another
user/bot, is a reply to another user, or is a recognized other-bot command-prefix like Carl-bot's
`?`/`!`). A small pure helper `utils/ai/addressing.py:is_addressed_elsewhere(message, bot_user)`
would let the natural-language stage cheaply skip barge-ins **and** be unit-tested offline, turning
a fuzzy behavior call into a testable rule. Genuinely useful beyond this bug (any future ambient
feature wants it); lane = ai/runtime. (Not built — BUG-0019's fix is owner-gated; captured here.)

## ⟲ Previous-session review (Q-0102)

The previous session (this same chain, #1180 — the feature-mapping plan) did the mapping well and
correctly respected the owner's plan-only / arch-review-pack steer. **What it could've anticipated:**
it treated Pokétwo as a "nice extension" lane; one screenshot later the owner reframed it as a
*real* competitive gap (users leaving for other bots). The plan would have been stronger had it
asked **"is any of this load-bearing for retention?"** up front — a competitive-gap lens, not just
an architecture-fit lens. **System improvement it surfaces:** feature-mapping plans should carry a
short *"demand/retention signal"* field per lane (why does a user want this, what do they use
instead today?) so priority isn't purely an internal architecture judgment. I added exactly that
signal to the plan this run; worth making it a standard section in future mapping plans.

## 📤 Run report

- **Did:** root-caused + recorded BUG-0019 (AI replies to other bots' mentions); added the live
  Pokétwo demand signal + reference to the feature-mapping plan · **Outcome:** shipped (docs-only)
- **Shipped:** #1182 — BUG-0019 (OPEN, routed) + Pokétwo demand signal/reference
- **Run type:** `manual · owner-task (bug note + product signal)`
- **⚑ Owner decisions needed:** BUG-0019 `always_reply` behavior fork (+ which mode `goals-for-now`
  uses) · Q-0186 Pokétwo lane priority (demand signal raises it)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (owner-directed: "make a note" + "ensure a Pokémon-system equivalent")
- **↪ Next:** on the owner's BUG-0019 call → a runtime-verified session ships the fix + guard;
  on Q-0186 → build Lane A (Wild Encounters)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (#1182, docs-only, auto-merge on green) |
| Runtime (`disbot/`) code changed | 0 (bug noted, not patched — gated AI path + owner fork) |
| Bugs recorded | 1 (BUG-0019, OPEN, root-caused) |
| CI-red rounds | 1 (by-design born-red session gate only) |
| New ideas contributed | 1 (addressed-elsewhere ambient guard predicate) |
