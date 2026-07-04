# 2026-07-02 — Daily review + architecture brainstorm ahead of the rebuild gate

> **Status:** `complete` — ready to merge (Q-0133). Docs-only session; no `disbot/` changes.
> `check_docs --strict` ✓.

**Branch:** `claude/daily-review-brainstorm-rcyar3` (synced to `main` @ #1657 before this commit).

## What I'm about to do (intentions — as declared born-red)

Owner asked for a plain-language review of everything shipped/decided today (13 sessions, the
rebuild-strategy → design-spec → linchpin-validation → substrate-kit-finalize → retention-policy →
Railway-ops → HQ-guild arc), a brainstorm of anything forgotten, and specific thinking on unifying
the bot's memory/context systems. Follow-up turned into two concrete architecture decisions the
owner wants folded into the rebuild spec before Phase 3: (1) presets-with-custom-escape-hatch
generalized to every text-valued setting, not just numeric ones; (2) multi-select promoted from a
bot-code convention (Q-0205) to a rebuild-grammar compile rule. Owner also asked that all useful
findings from the conversation get durably documented, not just left in chat.

## What shipped

1. **Research-only synthesis** (4 parallel agents) of today's session logs, `current-state.md` +
   planning docs, the substrate-kit vs. existing `docs/agent/` context-compiler overlap, and the
   idea backlog — delivered to the owner as a plain-language summary (not written to a file; the
   session logs it summarizes are already the durable record).
2. **Q-0215** (router): generalizes Q-0070's already-decided "presets everywhere, manual entry
   always available" posture into the rebuild grammar — new `SettingSpec.preset_kind` field
   (§2.5), a compile rule that `str`-typed specs with presets must declare `preset_kind="text"`.
3. **Q-0216** (router): promotes Q-0205's "multi-select is the preferred idiom" from a per-PR bot
   convention into a `SelectorSpec` compile-time default (§2.4) — `max_values` defaults to a
   binding's declared multiplicity instead of Discord's single-select default.
4. Both folded into `docs/planning/rebuild-design-spec-2026-07-02.md` (top-of-doc addendum + the
   two section edits) with cross-references to their precedent Q-numbers, so the spec doesn't
   silently re-decide something already settled.
5. Verified the developer-website question the owner raised ("finish the website first?") is
   **already correctly tracked** — `current-state.md` S5/Next-candidates already carries the
   website rollout as a separate, non-blocking ops item, and the design spec §6 already requires a
   versioned control-API contract before the interaction runtime lands. No doc drift found; no
   edit needed there.
6. Owner asked which plan steps remain and which gate Phase 3 — surfaced that the
   linchpin-validation's own "GO with amendments" verdict (#1639) had never actually been folded
   into the spec. Owner approved folding it in now. **Q-0217** (router): executed all six grammar
   amendments (`GatewayListenerSpec`, list-valued settings, `AnnouncementRouteSpec`,
   `CommandSpec.cooldown`, declarative validator bounds, per-kind command-pool scoping) plus five
   spec corrections (harness-mechanism naming, evals/harness composition, K10 Postgres CI
   requirement, determinism-pinning budget, clock+RNG as injectable kernel services) into
   `docs/planning/rebuild-design-spec-2026-07-02.md` §1.2/§2.2/§2.5/§2.8/§3.1/§6, source-verified
   against the linchpin-validation doc's own tables.

## Context delta

- Two owner-raised "new" architecture questions turned out to both already have an owner-decided
  posture on the books (Q-0070, Q-0205) that simply hadn't been carried into the *new* rebuild
  grammar yet. The pattern worth naming: when the owner raises a UX principle during rebuild
  planning, check the router for prior art before treating it as a fresh decision — the rebuild
  spec is a **consolidation** of standing decisions as much as it is new design, and it's easy for
  a verbatim-ported field (like the shipped numeric-only `presets`) to quietly under-carry a
  broader posture that was already settled for the old code.

## 🛠 Friction → guard

None new. The existing router-search-before-deciding habit (used here manually) is the guard; no
checker gap surfaced this session.

## 💡 Session idea (Q-0089)

An idea worth having: a small `check_router_precedent.py`-style grep helper that, given a proposed
new Q-number's topic keywords, surfaces prior router entries with textual overlap (e.g. "preset",
"multi-select") before a new decision is recorded — would have made today's "is this already
decided?" check (which I did by hand) a 5-second command instead of reading two full research-agent
reports. Small, deferred — not built this session.

## ⟲ Previous-session review (Q-0102)

Previous session (`#1657`, review-recent-session) — hadn't read its log in detail before this one
started since this branch was cut independently; nothing to flag against it specifically. General
observation across today's 13-session arc: the design spec's "Revision" addendum pattern (a dated
callout at the top of the doc summarizing what changed and why) is a genuinely good convention this
session reused directly — it makes a 150KB+ living document skimmable without re-reading it end to
end. Worth keeping as the default way to layer late-arriving decisions onto any long-lived planning
doc, not just this one.

## 📤 Run report

- **Did:** reviewed today's full session arc for the owner in plain language, researched two
  owner-raised architecture questions against the design spec + current bot code, folded both
  into the rebuild grammar as compile rules with router provenance (Q-0215/Q-0216); then, on
  owner request, audited remaining plan steps and found + executed the linchpin-validation's
  never-folded-in amendments (Q-0217).
- **Outcome:** shipped (docs-only), two PRs (#1658 merged; this session's remaining work follows
  in the next push).
- **Run type:** `manual` (owner-directed, live conversation).
- **⚑ Owner decisions needed:** none new — Q-0215/Q-0216/Q-0217 record decisions/executions the
  owner already directed live in this conversation.
- **⚑ Owner manual steps:** none.
- **⚑ Self-initiated:** none (every doc change traces to an explicit owner ask this session).
- **↪ Next:** design-spec owner gate (Phase 3 start) still pending; Phase 2.5 cold-start A/B test
  for substrate-kit still not run — these are now the only two items left before Phase 3.
