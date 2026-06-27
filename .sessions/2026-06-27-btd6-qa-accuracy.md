# 2026-06-27 — BTD6 QA accuracy: damage-type/status-effect interaction grounding + verified Q&A corpus

> **Status:** `complete`

**Run type:** owner-directed (session prompt + live Discord screenshots)

## What this run did

Owner reported the bot still answers many BTD6 questions wrong (screenshots: the Glue Strike / Avenger /
DDT thread). I replayed the exact failing messages through `scripts/btd6_probe.py` and found the root
cause: **the data dump's bloon immunities are correct** (they're game-data-sourced), but there was **no
grounding for damage-type ↔ bloon-property INTERACTION**. The model gets bloon immunities and tower
descriptions *separately*, so it invents the connecting rule — e.g. it confidently said *"Lead resists
glue"* (false: glue is a status effect that ignores damage-type immunity; MOAB-class just needs MOAB
Glue 0-0-3 to be *targeted*).

**PR #1487 — damage-type/status interaction grounding + verified corpus.**

1. **`disbot/data/btd6/damage_types.json`** — curated, wiki-verified interaction layer: the 11 damage
   types (which bloon properties block each), 4 status effects (glue/ice/knockback/stun — NOT damage,
   how they hit Lead/MOAB-class/BAD), and a per-property pop-guide. Every damage type's
   `blocked_by_properties` is **cross-checked against the game-sourced `immune_to` data** so a curated
   typo or a future re-seed fails CI (Q-0120 principle).
2. **`disbot/services/btd6_interaction_service.py`** — loads it and emits `[btd6_damage_type]` /
   `[btd6_interaction]` facts for interaction questions; a verb-gate + two-entities rule keeps cost /
   definition / upgrade-listing lookups from firing.
3. **`btd6_context_service.build()` Pass 3g** — wires the interaction facts (isolated like its siblings).
4. **Bloon prose fixes** (`bloons.json`) — Lead/DDT descriptions listed only "Sharp"; now list all
   immunities + that glue/status still works.
5. **`docs/btd6/qa-accuracy-corpus-2026-06-27.md`** — the "large list of questions" the owner asked for:
   ~90 categorized questions with verified answers, tagged `[dump ✓]` / `[wiki]` / `[fixed]`.
6. **Tests** — `tests/unit/services/test_btd6_interaction_service.py` (18): the cross-check guard, the
   fire/suppress gate, the specific screenshot corrections, and an end-to-end `build()` wiring test.

**Verification discipline (the point of the task):** I treated the background research agent's 164-Q
corpus as *input to verify*, not truth. Caught real errors by checking the dump: it claimed **Sniper is
Normal damage and pops Lead at base** — the game export says **Sharp, `cannot pop Lead or frozen`**
(owner confirmed in-session). Also corrected Embrittlement code (4-0-0, not "2-x-x") and the innate
camo/lead tower lists (camo = Ninja/Spike/Desperado; lead = Bomb/Mortar/Alch — Sniper needs FMJ 1-0-0
for lead, Night Vision 0-1-0 for camo). The probe now grounds all of these correctly.

CI: `check_quality --check-only` green, `mypy disbot/` clean (847 files), arch strict = pre-existing
warnings only, full pytest green.

## ⚑ Self-initiated

None unprompted — this is owner-directed work (session prompt + screenshots). The `damage_types.json`
interaction layer is the implementation path to the stated goal (Q-0014: approving the goal approves the
prerequisite step it didn't name).

## 💡 Session idea (Q-0089)

*A `btd6-accuracy-probe` CI smoke that replays a fixed list of interaction questions through
`btd6_context_service.build()` and asserts each grounds ≥1 `[btd6_interaction]`/`[btd6_damage_type]`
fact (offline, no creds).* This session's whole diagnosis was "replay the exact text, read what
grounds" — but that's manual. A tiny offline harness over ~20 canonical interaction questions (the
corpus's Category 1) would turn "does the bot ground the right facts for the error-prone class?" into a
live CI signal, catching a future resolver/alias regression that silently stops an interaction question
from firing. Cheap (build() is sync-friendly + DB-degrading), genuinely tied to this run, routed as an
idea rather than built so the corpus lands first.

## ⟲ Previous-session review (Q-0102)

Prev session (`2026-06-27-youtube-fetch-renderer-tests`) did a clean job closing two Media/YouTube
test-coverage gaps and correctly de-drifted a stale readiness row. **What it missed:** it declared the
"BTD6 / fishing offline product lanes **exhausted**" and fell back to test coverage — yet this session
found a high-value, fully-offline BTD6 accuracy lane (interaction grounding) worth a whole PR. The gap
wasn't in the decode-status backlog because it surfaced from **live screenshots**, not the planned
data-decode queue. **Workflow improvement (initiated, not just noted):** the new
`qa-accuracy-corpus-2026-06-27.md` is exactly the missing artifact — a standing, probe-able BTD6
*accuracy* backlog distinct from the *data-decode* backlog, so a future empty-fire run can pick "make
the next wrong-answer class right" instead of concluding BTD6 is done. The Q-0089 idea above would make
it executable-by-CI. Lesson: "lane exhausted" should mean "the *accuracy probe corpus* is green," not
"the decode backlog is drained."

## 🧾 Doc audit (Q-0104)

`check_docs --strict` green (corpus doc reachable via the btd6 README index). `check_consistency` green.
New facts homed: the interaction layer in `docs/btd6/` + the corpus doc; S2 sector state updated. No
new owner *decision* to route (owner's in-session Sniper correction is a fact-verification, already
captured in the corpus + the data — not a CLAUDE.md rule change). Ledger: PR #1487 will be added to the
living ledger by the next reconciliation pass (merged-PRs-only convention); not back-dated here.
