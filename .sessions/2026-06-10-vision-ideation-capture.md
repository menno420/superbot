# 2026-06-10 — Vision ideation + capture session

**PR:** #680 (draft at first push per Q-0052; docs-only). **Prompt:** the
maintainer wrote a long product-vision statement ("I want superbot to be the
best bot ever made") and asked for (1) a review, (2) the agent's own creative
thinking about the perfect SuperBot, (3) using the session to generate new
ideas and improvements for existing and new functions.

## Arc

Pure ideation/capture session — the Q-0015 conveyor doing its intake step on a
big owner-voice drop. The vision turned out to stand ~70% on already-shipped or
already-decided ground (character platform §7 waves, Q-0040 bounded-menu AI DM,
pets plan, help projection seam #657/#659, setup advisor seam), so the real
work was the **dedup map** — separating "this exists", "this is decided", and
"this is genuinely new" so future sessions neither re-litigate nor duplicate.

## Shipped

**`docs/ideas/superbot-vision-2026-06-10.md`** — owner-voice vision (§1),
dedup map (§2), new owner items **V-01…V-12** (§3), agent creative response
**AG-01…AG-15** (§4), honest tensions **T-1…T-5** (§5), routing ledger (§6).
Indexed in `ideas/README.md`, `roadmap.md` Someday, brainstorm §7.8 pointer.
Highest-leverage new items: per-user preferences as a third settings scope
(V-04/AG-04, converges with wizard PR4 `/myprofile`), the deterministic quest
engine + "Story Actions" view as the concrete Q-0040-compliant AI-DM mechanism
(AG-08/AG-09), and the ≤3-clicks/2-minute UX laws as checkable invariants
(AG-01).

## Decisions + grooming (after the capture)

One structured-choices round (protocol 6a) → **Q-0078** (router §34), all four
answered: **one-way ascent** difficulty switching (T-3) · **both pet paths**
(T-1; pets plan amended in place) · the **4-button Help Home** layout (T-4) ·
next planning targets = **RPG survival design + help home/navigation**. The
grooming move executed the first pick:
`docs/planning/rpg-survival-difficulty-design-2026-06-10.md` (difficulty
contract D1, lazy-clock energy/hunger D2/D3, fishing/cooking D3/D4,
encounters D4, death-as-rescue D5, duel-XP quick-win D6; P1–P5 phasing;
gates G1–G3; Easy-mode byte-identical as the headline pin). The
help-home/navigation plan is the named next grooming target, sequenced with
the Help lane's overlay editor UI.

Follow-up owner correction → **Q-0079**: no per-panel button caps ("the 3
buttons per panel is never going to work"); cleaner UX = fewer or
**better-defined** buttons (labels/grouping/placement); removal only for
genuine redundancy — almost all current buttons are useful. The vision's "≤3"
is navigation depth only. Routed into the capture doc (§1/V-03/AG-01/§6) +
the roadmap interface row; binds the upcoming help-home/navigation plan.

## Context delta (reflection interview)

- **Route miss:** none serious — CLAUDE.md → current-state → ideas/README →
  the three capture docs was the right route and `ideas/README.md` correctly
  named `owner-vision-ideas-2026-06-08.md` as "start here".
- **Route excess:** current-state's ▶ header block is very dense for a
  non-implementation session; the ideas-lane reader mostly needs "what game/UX
  state shipped" which lives clearer in the Recently-shipped list.
- **Discovered by hand:** that `services/setup_ai_advisor.py` already exists
  (a schema-validated GuildSnapshot→plan advisor) — no orientation doc connects
  the "smart setup" idea space to that seam; the §2 dedup row now records it.
  Also: survival stats were *explicitly deferred* in brainstorm §6 with
  reserved columns — found only by grepping the brainstorm body.
- **Decisions made alone:** numbered the vision delta (V/AG/T scheme) and
  flagged tensions instead of silently merging the pets vision into the pets
  plan; deferred all promotion decisions to owner picks (routing rule).
- **Weak point:** the survival plan's contract-table numbers are placeholders
  by design (gate G2 owner-confirm) — don't read them as decided balance.
- **One change that would have helped:** a one-line "owner-voice capture
  template" in ideas/README (sections: owner-voice · dedup map · new items ·
  response · tensions · routing) — this session derived it; next drop should
  just follow it.
