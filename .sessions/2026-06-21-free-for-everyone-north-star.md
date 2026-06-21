# 2026-06-21 — "Free for everyone, forever": codify the product North Star

> **Status:** `complete` — owner set a new project North Star in-session (completely free,
> all-inclusive bot; no paywalls / premium tiers / freemium feature-gating). Codified durably across
> the router (Q-0190), a mission doc, and roadmap / current-state / ideas-index cross-refs. Docs-only,
> owner is the live reviewer → auto-merge on green.

> **Run type:** `manual`

## Arc

The owner dropped a new top-level goal: SuperBot becomes a **completely free, all-inclusive bot** — no
paywalls, premium tiers, or freemium feature-gating — because paywalling online functions "isn't
fair," with the ambition that one free all-in-one bot replaces 5+ paywalled bots ("a revolution").

Researched first: this is an **elevation, not a reversal** — Q-0039 (cosmetic-only donations / no
bot-side billing / no-P2W), Q-0108 (paid moderation tiers declined), and Q-0080 (public bot goal)
already leaned this way. The new goal generalizes them into one binding principle and closes the
freemium-feature-tier door the owner had been considering.

One genuine fork — the **T-6** tension (public scale × ~zero revenue × fixed Q-0082 AI ceiling), which
the repo explicitly flags as "owner's call, don't resolve silently" — was put to the owner via the
question panel: **"Allow voluntary support"** (no feature-gating ever, but a voluntary zero-benefit
support link to offset hosting + AI cost stays allowed, extending Q-0039).

## Shipped (all docs-only, PR #1226)

- **Router Q-0190** — the canonical owner-decision record (relates Q-0039/Q-0080/Q-0082/Q-0087/Q-0108;
  resolves T-6).
- **`docs/ideas/free-for-everyone-mission-2026-06-21.md`** — the mission doc: owner-voice rationale
  (fairness + consolidation + "revolution"), the precise forbid/permit boundary, why it's an
  elevation, the resolved T-6 + sustainability reality, and open questions.
- **`docs/roadmap.md`** — a ▶ Product North Star principle callout + a Q-0039 gate cross-ref.
- **`docs/current-state.md`** — an Off-limits enforceable bullet (no feature-gating monetization).
- **`docs/ideas/README.md`** — index entry.

## Decisions made alone (owner-ratifiable)

- The **forbid/permit boundary** wording — *money may change recognition, never capability* — a precise
  restatement of owner intent; flag if he'd draw it elsewhere.
- Two **open questions** I left captured-not-asked (neither blocks anything): (a) open-source /
  self-host posture (I read "free" = free-to-*use*, and flagged its tension with the "revolution"
  goal), (b) whether to build an anti-paywall-creep lint.

## Context delta

- **Needed but not pointed to:** the **T-6 tension** (vision doc §5 + router §35) is the single most
  relevant prior context for any monetization/free/public-scale decision, but nothing in the
  orientation route points a monetization-shaped task at it — I found it via a grep for monetization
  terms. The new mission doc + Q-0190 now *are* the single "monetization posture" home, and both link
  back to T-6.
- **Pointed to but didn't need:** nothing wasted — as a capture/route task it correctly skipped the
  binding-contract docs (architecture/ownership) and the code-change orientation route.
- **Discovered by hand:** the "free" direction was already ~80% decided, but scattered across
  Q-0039/Q-0108/Q-0080/Q-0087 in the router + roadmap with **no single posture home**. That absence is
  what let it read as a "new" goal rather than a codification.

## ⟲ Previous-session review (Q-0102)

Previous session = the **Q-0189 "open the session PR FAST"** workflow change (#1224). **Did well:**
pinned the *timing* half (≤2 min) of the early-PR rule with crisp provenance (the #1221 duplicate-PR
lesson) — and I directly benefited, opening #1226 as my first action after scoping. **Could improve /
system improvement:** Q-0189 ships "no new tooling" and leans on the agent *remembering* to open
fast — the very memory-dependence that made the rule necessary. The concrete improvement (which the
Q-block itself defers): a **SessionStart soft nudge** — a one-line `PR: not yet opened — target ≤2 min`
banner that clears once a `claude/*` PR exists for the branch — would make the rule self-enforcing
rather than discipline-dependent. Candidate only (SessionStart hook is owner-wired per Q-0106).

## 💡 Session idea (Q-0089)

**Anti-paywall-creep lint** — a disposable (Q-0105) soft `check_docs` / AST guard that flags new
"premium / paywall / paid-tier-gate / subscription"-shaped language entering docs or `disbot/`, behind
a careful allowlist (since "free"/"premium"/"paid" have innocent uses). It's the *product-wide*
extension of the Q-0039 economy CI invariant (no supporter predicate in odds/reward/cooldown/fee
paths), turning the new Q-0190 North Star from prose into an executable guard. Captured in the mission
doc §5.2 — genuinely useful, not filler, but wants the allowlist designed before it's worth building.

## 🔎 Doc audit (Q-0104)

`check_docs --strict` ✓ · `check_current_state_ledger --strict` exit 0 (19 newer merges = benign lag,
recorded by the next reconciliation pass — #1230). New owner decision recorded in the router (Q-0190);
new mission doc reachable via the README index + roadmap + current-state + router. Both owner messages
(the goal + the fairness/"revolution" rationale) are preserved as owner-voice in the mission doc §1 —
nothing consequential left only in chat.

## 📤 Run report

- **Did:** codified the owner's new "free for everyone, forever" North Star across the router + a
  mission doc + roadmap/current-state/ideas-index · **Outcome:** shipped
- **Shipped:** #1226 — Q-0190 + mission doc + 3 cross-refs (docs-only)
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none blocking — two captured open questions for *whenever* (not now):
  open-source/self-host posture, and whether to build the anti-paywall lint (Q-0190 § "Open").
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none — the entire change was owner-directed in-session (the new goal + the live
  question-panel ratification of the funding fork).
- **↪ Next:** unchanged band queue (reconciliation due at #1230). When the voluntary-support surface is
  wanted it needs its own small plan (a `/support` link, zero-benefit) — mission doc §5.3.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 at write (PR #1226 auto-merges on green) |
| CI-red rounds | 0 (born-red by the session gate until this card flips `complete`) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (anti-paywall-creep lint, Q-0089) |
| Ideas groomed | 1 (owner vision → decided North Star + mission doc + roadmap horizon — top-of-lifecycle routing, Q-0015) |
