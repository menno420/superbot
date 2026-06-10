# 2026-06-10 — BTD6 Ask parity + the dark-render fixes (PR #658)

**Task:** "continue from where you left off" after #655 merged — the
decode-status ⭐ answerability backlog (items 5 + 6d).
**Shipped:** PR #658 — the deterministic Ask path (panel **Ask** / `!btd6 ask`,
no AI key) now answers every domain the AI tools can, and the Pro-stats views
render the decoded effects/minions that were dark on every surface.

- **Item 5 (Ask parity), three root causes:** the resolver matched bloons but
  `deterministic_answer` had no bloon branch (new `for_bloon`, lowest
  precedence — pinned); powers/MK/bosses were never grounded by the shared
  pipeline (new context-service **Pass 3e** name-matches all three catalogs;
  MK gated on a knowledge/MK keyword because its names are generic English);
  facts found with no intent were buried under the refusal headline (new
  `for_reference_facts`, keyed on the exported `UNRESOLVED_TITLE`).
- **Item 6d (dark renders):** the buff/zone renderers + `tier_effect_lines`
  moved to **`utils/btd6/effect_lines.py`** per helper-policy (needed by
  services AND utils); `_stat_node_embed` gained 🌀 Effects + 🤖 Minions, so
  tower/hero/paragon Pro views all render them; the hero grounding emits
  change-only `[btd6_hero_buff]` lines.

## Process learnings

- **Making dark data visible immediately exposed a semantics bug**: Striker's
  Bomb buff rendered "×0.25 pierce, ×0.05 range" — the dump's `*Multiplier`
  field names are misleading fractions, kept verbatim by both the wiki rows
  and my #655 decode ("field-name identity" was the wrong call; the absurdity
  test — a ×0.05 range aura — should have triggered then). Remapped to the
  `*Percentage` family with `_CUTOVER_TRANSPLANT_SKIP` entries so the old
  committed fields can't transplant back (the skip table exists for exactly
  this). **Render a thing before declaring it decoded.**
- **Change-only emission needs order-insensitive comparison** — the decoded
  buff list's order shifts between hero levels; tuple comparison double-emitted
  an "order-only change". Compare frozensets, emit sorted.
- An in-place extraction that leaves the import mid-module fights isort/ruff
  (E402) — move shared-helper imports straight to the top block; the layering
  was already legal.
- `answer_question` already fetched the context facts (`live_facts`) — the
  recorded item-5 "root-cause direction" (add a fallback consumer) was nearly
  built; verifying what existed before designing saved a second router.

## Grooming pass (Q-0015)

Items 5 + 6d struck through in decode-status ⭐ (this session WAS the backlog
work). Remaining there: item 3 (buff/zone `$type` tail, demand-driven),
item 4 (maintainer live spot-check — now including the new Effects/Minions
fields and the Ask answers), item 6 a–c (minion-name aliases · the
`fixture/btd6_data` label · `source_summary` claim).

**Resume point:** decode-status ⭐ — item 6 a–c are the next contained slices;
item 3 waits on real questions. PR #658 review = the diff.
