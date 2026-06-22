# 2026-06-22 — route the mining-grid-encounters design to the owner (Q-0198)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Routine · dispatch ("Continue from where you left off"; grooming-routes an owner-reserved idea).
> PR #1325 → auto-merges on green (Q-0123).

## Arc

Six PRs already merged this session (#1305 React foundation, #1308 contract guard, #1317 ledger/CI
hygiene, #1320 tool-pin CI guard, #1322 migration-collision guard — and #1279's reaction-roles PR 6
landed mid-session). Four of those were infra/guards because **every product lane is gated** — I
flagged that infra-bound drift myself last turn. This turn deliberately breaks the pattern: instead
of building a 7th guard, advance the highest-value **product** item as far as is safe.

That item is **mining-grid encounters** — the *one owner-named* grid follow-up
([idea](../docs/ideas/mining-grid-encounters-2026-06-22.md), origin Q-0173). The owner shipped the
grid Mine *encounter-free by explicit decision* and said encounters "ARE wanted, as a separate later
session." The idea file itself instructs: **"route to a router Q before building, don't decide
unprompted"** (4 open design questions). So the sanctioned grooming step (Q-0015: route an ambiguous
idea to a router discussion) — **not** an unprompted build — is to pose those decisions to the owner
with concrete recommended defaults, so on his return he can ✓/adjust in minutes and the next session
builds immediately. (Q-0172 "build freely" yields here to the owner's explicit design reservation +
the idea's own route-first instruction.)

This PR (docs-only):
1. **Router Q-0198 (DISCUSS)** — the 4 design decisions (depth threshold/chance/cooldown · encounter
   content & combat engine · determinism · resolution UI), each with a recommended default + rationale
   grounded in the shipped systems, so it's a quick approve-or-tweak, not an open essay.
2. **Idea status** → routed to Q-0198 (so the lifecycle pointer resolves both ways).

## Shipped (PR #1325)

- **Router Q-0198 (DISCUSS)** in `docs/owner/maintainer-question-router.md` — poses the 4
  mining-grid-encounter design decisions to the owner, each with a concrete recommended default +
  rationale grounded in shipped systems: (1) depth z≥10 / ~8% per action / ~5-action cooldown, all
  config-driven; (2) loot/flavour-only v1, reuse creature/deathmatch engine if combat is added (never
  a third model); (3) live roll gated by depth (terrain deterministic, events live); (4) buttons on
  the existing navigator embed. Cross-links Q-0173 (grid design) + Q-0186 (wild-encounters — the
  *shared resolution engine* opportunity) + the anti-mandatory (Q-0087) / atomic-workflow (Q-0071) rails.
- **Idea status** — `mining-grid-encounters-2026-06-22.md` Open-questions section now marked ROUTED
  to Q-0198 (lifecycle pointer resolves both ways; "don't build ahead of the answer" noted).
- **Verification:** `check_docs --strict` ✓. Docs-only; no runtime/CI scope.

## Session enders

- **♻ Grooming (Q-0015):** this turn *was* the grooming task in its "route an ambiguous idea to a
  router discussion" form — advanced the one owner-named product follow-up toward buildability without
  deciding its design unprompted. Deliberately chose this over a 7th infra guard to break the
  infra-bound pattern.
- **💡 Session idea (Q-0089):** *Build the shared `utils/.../encounter.py` resolution engine once, two
  triggers.* Q-0198 (grid/exploration-triggered) and Q-0186 (chat-activity-triggered) both need an
  encounter table + an audited resolution op; the only real difference is the *trigger*. When the
  owner greenlights either, design the pure engine (table → roll → audited `*_workflow` reward op) as a
  shared `utils` module both cogs call, so the second trigger is a thin add, not a second engine.
  Logged in both idea files' "shared engine" notes; this elevates it to a build-time directive.
- **⟲ Previous-session review:** the run of turns before this one (5 PRs, 4 infra) was *individually*
  sound — each guard fixed a real recurring tax — but *collectively* drifted infra-bound while the
  product roadmap sat untouched. **This turn is the correction:** when the only "decided/small" ideas
  left are guards, the right move isn't a 7th guard — it's to *unblock* the gated product work
  (route the owner's decision), which is higher leverage than building more scaffolding around an
  un-advancing product. **System note (carried from last turn):** a dispatch run still can't *see* "0
  ungated product lanes" vs "I judged them gated" — a `current-state`/`dispatch_menu` signal that
  distinguishes them would let a run pick "route the gated item to the owner" *deliberately* instead
  of discovering it by exhaustion.
- **🧾 Doc audit (Q-0104):** `check_docs --strict` ✓; the router Q + idea pointer cross-resolve; no
  current-state change needed (an open design question, not shipped state); ledger auto-updates for
  #1325 on merge. Nothing left only in chat.

## ⚑ Self-initiated: yes (Q-0172) — grooming-routed an owner-reserved idea (mining-grid encounters) to
   a router DISCUSS Q-0198 with recommended defaults; no dispatch/owner ask. Docs-only, no design
   *decided* (the idea + Q-0173 explicitly reserve the design for the owner) — it poses, doesn't decide.
   Fully reversible.

## 📤 Run report

- **Did:** routed the one owner-named mining-grid follow-up (encounters) to the owner as router DISCUSS **Q-0198** — 4 design decisions with recommended defaults — instead of building a 7th infra guard, so the highest-value gated *product* item is ready for his quick approve-or-tweak. · **Outcome:** shipped
- **Shipped:** #1325 — Q-0198 (DISCUSS) + the idea status → routed. Docs-only.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** **Q-0198** — mining-grid encounters: depth threshold/chance/cooldown · loot-vs-combat (+ engine) · determinism · resolution UI (defaults proposed; a quick ✓/tweak unblocks the build).
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** **yes** — grooming-routed an owner-reserved idea to the router (poses, doesn't decide); docs-only, reversible.
- **↪ Next:** **the fleet is product-gated and the owner is the unblock.** Top items needing him: (1) **botsite React-SPA PR 2** — the live `/` cutover; needs a browser look (verify locally via `npm --prefix design-system run dev:app`, its data side de-risked by #1305/#1308/#1317/#1320); (2) **Q-0198** — answer the encounter design to unblock that build; (3) optional ops: mark the new `tool-pins` check *required* + the Dependabot-ignore policy call (#1320). Still gated without him: Project Moon ingestion (network/IP → ask-first), BUG-0009 (data/provenance + creds), BUG-0019 (ambient-AI design fork). The docs reconciliation (Recon DUE at #1320) is the separate routine's job (Q-0124), not a dispatch session's.
