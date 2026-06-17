# 2026-06-17 — Character preview tool + vault-cap decision

> **Status:** `in-progress`
> Manual session (owner-live). **Born-red per Q-0133.** Flip to `complete` when CI is green.
> The preview tool is **self-initiated** under the new Q-0172 gate (built to solve a pain the owner
> described, not explicitly requested) — flagged in the run report for review.

**Branch:** `claude/character-preview-tool`

## Goal

The owner described the sprite workflow as brutal: ~40 ChatGPT tries to get the art right, then
**100+ more rounds** on positioning — each a manual upload-to-Discord-and-eyeball. Positioning is now
data (`manifest.json`), but there was **no local preview**, so the loop stayed manual. This adds one.

## What was done

- **`scripts/preview_character.py`** (NEW — self-initiated, Q-0172) — renders the **live** V-16
  compositor (`disbot/utils/character_render.py`) to a PNG locally: a single tier, a custom loadout,
  or a **contact sheet of all five tiers**; `--asset-dir` previews an alternate candidate pack. It
  reuses the real renderer, so the preview is the exact image the bot ships. This kills the manual
  loop — render → look → tune `manifest.json` → re-render in seconds. Crucially, an agent can *see*
  the rendered PNG, so positioning tuning no longer needs the owner to upload test files. Q-0105 dev
  tool, disposable.
- **Vault hard-cap follow-up → DECLINED (owner, 2026-06-17):** recorded in the mining-structures
  plan. The owner chose to keep the soft / warning-only cap ("just keep a warning for now"). One
  mining owner-gate closed.

## Decisions recorded

- Owner: keep the vault cap **soft / warning-only**, no hard enforcement (fits Q-0087
  "never mandatory-feeling"). Mining-structures plan updated.

## Left open / next session

- The remaining mining sprite gate is purely the owner's **art** — drop the PNGs into
  `disbot/assets/gear/` (same names); the preview tool + manifest handle the rest. Once art lands I
  can tune any off positioning via the preview loop.
- **Mining feature roadmap (awaiting owner steer):** hub declutter (PR 2 — confirmed/turn-key, 16
  buttons → 6 + sub-hubs) · grid Mine (PR 3 — new mechanic, needs design sign-off) · open-world
  Explore incl. **fishing** (future design pass; also the Q-0172 fishing-plan candidate).

## 💡 Session idea

**Idea:** generalize the preview into a `scripts/preview_cards.py` family — local PNG previews for
**every** bot image card (welcome card, inventory card, stat card, character doll), each reusing its
live renderer. **Why:** the character-preview win (fast art/layout loop without deploying) applies to
all the PIL surfaces; one small dev tool would give every future card-art or layout change the same
seconds-not-hours loop. Disposable (Q-0105).

## ⟲ Previous-session review

The previous run (the Hermes house-style rollout, #1030) made the right architectural call —
centralizing the 5 rules into one `_house-style.md` that skills *cite*, rather than copying the rules
into each skill (so the next skill author inherits the style for free). **Improvement it surfaces:**
it converted 5 of ~9 owner-facing skills and parked the rest in the card's "left open" — but a
card's left-open list is easy to lose. Partial rollouts should also leave a one-line breadcrumb in
`current-state.md ▶ Next action` (or an idea file), so the remainder is visible to the *next* session,
not just buried in a closed card.

## 📤 Run report

- **Did:** built a local character-render preview tool (kills the sprite-positioning loop) + recorded the vault-cap decision · **Outcome:** shipped
- **Shipped:** (this PR) — `scripts/preview_character.py` + the vault-cap-declined record
- **Run type:** `manual`
- **⚑ Owner decisions needed:** `none` (vault cap decided this session)
- **⚑ Owner manual steps:** provide the **sprite art** — paint/commission the ~37 PNGs (per `disbot/assets/gear/README.md`) and drop them into `disbot/assets/gear/`; ping me to tune positioning
- **⚑ Self-initiated:** `scripts/preview_character.py` — local character-render preview, built to solve the owner's stated sprite-positioning pain (no explicit request) (Q-0172)
- **↪ Next:** owner picks the mining feature lane (hub declutter / grid Mine / fishing); I tune sprite positioning once art lands

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 2 (#1029, #1030); this is the 3rd |
| CI-red rounds | TBD (filled at flip-to-complete) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`preview_cards.py` family) |
| Ideas groomed | 1 (vault-cap gate resolved; sprite gate clarified to art-only) |
