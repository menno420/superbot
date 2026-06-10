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
- **Weak point:** the routing ledger's "suggested next steps" are my judgment
  — the owner's actual cluster priorities were captured via the end-of-session
  structured-choices round (see Q-0078 in the router if answered).
- **One change that would have helped:** a one-line "owner-voice capture
  template" in ideas/README (sections: owner-voice · dedup map · new items ·
  response · tensions · routing) — this session derived it; next drop should
  just follow it.
