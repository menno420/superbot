# 2026-06-10 — Production eval checklist (eval-session support)

**PR:** #673 (draft at first push per Q-0052). **Prompt:** "continue with the
plan / what previous agents suggested; meanwhile, what do I manually need to
test in the server?"

## Arc

The two halves of the prompt converged: the EOD audit §6 + the #671/#672
session log both name the **maintainer's production walk** as the single
highest-value next action (it gates AI §7.5 and mining structures §7.5), and
the maintainer's "what do I test?" is that walk asking for its working doc.
So the eval checklist *is* the plan continuation, not a side errand.

## Shipped

**`docs/audits/production-eval-checklist-2026-06-10.md`** — every
user-visible surface from the #606–#672 burst, tiered by who can verify:

1. **Tier 1 — AI model loops** (sandbox has no provider key; sign-off
   un-gates §7.5): the $19,840 inclusive round-cash anchor (Q-0043) ·
   profile setup via `!aimenu` → Tools + the #634 workflow + dry-run
   analyzer · the three #639 self-awareness questions with audience-tier
   checks · the Navarch/carryover/minion/diacritic grounding class
   (#662/#668), phrased in the deliberately-sloppy forms that broke live.
2. **Tier 2 — mining economy** (balance verdict gates structures §7.5):
   panel walk (new 🧰 Gear / 📖 Recipes), atomic-purchase rejection check,
   the diamond-lantern→MAGMA run, duels wear, game-XP boards, PIL cards.
3. **Tier 3 — BTD6 spot-check** — closes decode-status **item 4**; every
   expected answer re-probed against source via `scripts/btd6_probe.py`
   this session (Orca · Wall Street $4,000/round · Navarch $3,200
   end-of-round · Mini Sun Avatar → Sun Temple · Pouākai sans diacritic).
4. **Tier 4/5** — Settings hub (12 groups incl. new proof_channel),
   `!prizemenu` unbound-identical check, staff-hub Access Map / Help
   Preview, chain modals (the #671 "service-verified, never human-clicked"
   debt), Help paths, regression sweep (dropped `!hub`/`!server` aliases).

Linked from EOD audit §6 (its companion) + current-state Last-updated.

## Context delta

- **Needed but not pointed to:** the #634 workflow's *activation condition*
  (`workflow="analyze_execute_verify"` only on `btd6_grounded`/`_strict`
  presets — the default profile never runs it) lives only in
  `ai_orchestration_presets.py` source. Every "awaits prod check" banner
  says *that* it needs checking, none says *how to arm it*. The checklist
  now carries it; if a future doc wants it, the orchestration plan's Phase 4
  section is the home.
- **Pointed to but didn't need:** nothing significant; audit §6 + the
  session-log "flagged for maintainer" lines were exactly the right trail.
- **Discovered by hand:** `!mineinv` is a thin alias for `!inventory` (the
  PIL card renders from the panel's 📦 button path); leaderboard category
  spellings (`gamexp`/`crafting` + aliases) come from `rank_providers`.
- **Decisions made alone:** checklist lives in `docs/audits/` with badge
  `audit` (it's the walk's result ledger, companion to the EOD audit, not a
  plan); tiered by *who can verify* rather than by subsystem — the
  maintainer's scarce capability (model loops, clicks, feel) goes first.
- **Weak point of what shipped:** expected values are source/probe-verified,
  but panel *click* flows are described from code reading — a button label
  drift would only surface during the walk itself (acceptable: that's what
  the walk is for).
- **One change that would have helped:** nothing structural — this was the
  fastest orientation yet (≈15 min to full picture); the per-lane bullets +
  audit §6 + session-log flag lines composed perfectly.

## Open after this session

Unchanged queue (Batch 9 RS05/RS10 · Help overlay editor UI plan-first ·
setup PR4 planning · AI §7.5 post-prod-check) — plus the eval itself, now
armed. This session stays live as the ride-along fixer for eval findings.

---

## Continuation (same session): Help overlay editor UI plan — PR #674

#673 merged within minutes; while the maintainer walks the checklist, the
session took the queue's next non-colliding item — the **Help overlay
editor UI (plan-first)** — and produced
`docs/planning/help-overlay-editor-ui-plan-2026-06-10.md`.

**Why this item:** all owner decisions answered (Q-0055/56/58/59), zero
overlap with the surfaces under eval (the editor *writes* through the
#659-verified seam; the eval walks *read* paths), and the EOD audit lists
it among "most ready for further work". RS05/RS10 still want their own
focused session; setup PR4 planning needs the wizard plan re-read first.

**Plan shape:** 2 PRs. **A** (low risk, no migration): `views/help/editor.py`
on BaseView; entry points = staff-hub `✏️ Help editor` button +
`cogs/help/schemas.py` `DomainPanelSpec` ("Help appearance", capability
`help.settings.configure`, Settings taxonomy 12 → 13); every action = one
`set_overlay_fields` call. **B** (medium): migration widening the 064
`entity_kind` CHECK with `'home'` (exactly as 064's header pre-plans) +
bounded home-only columns; `set_home_message`; Home render consumption
(absence byte-identical, pinned); `HomeMessageBuilderView` with
**Save-disabled-until-previewed** enforcement of Q-0059's mandatory preview.

**Context delta (continuation):**

- **Needed but not pointed to:** nothing — migration 064's header comment
  literally pre-planned the Q-0059 widening, and `DomainPanelSpec`'s
  docstring + the cleanup example made the Settings integration turn-key.
  The substrate docs from #654/#657/#659 are exemplary; this plan mostly
  *collects* decisions rather than making them.
- **Decisions made alone:** (1) setup/final-review integration **deferred**
  (audit marks it optional; direct-lane is the right lane for a focused,
  reversible single-domain edit per `ownership.md` — revisit on ask);
  (2) named colors only in the v1 color picker (no hex parsing);
  (3) staff-hub button beside 👁 Help Preview so edit + verify sit together.
- **Flagged for maintainer:** none blocking — the plan executes on existing
  authority once an implementation session picks it up.

---

## Continuation 2 (same session): the live walk fired — ride-along fixes (PR #675)

The maintainer started the walk and screenshots arrived in real time. The
ride-along role the audit prescribed became the session's main work.

**Triage sequence that worked:** every refusal stamped "(55.0)" → that
version string is read live from `towers.json`, whose 55.1 stamp landed in
**#655 (same day)** → the prod deploy predated the whole day's burst →
"redeploy first" was the time-critical call (the empty boss roster + stale
version were yesterday's code, not bugs). After redeploy, "(55.1)" refusals
confirmed the **real** current-main bugs; the Railway log nailed the floor
mechanism live (`btd6_faithfulness: blocked … numbers=['2440','2440','12200']`
— the verifier blocking the model's own derived arithmetic, 5×2,440).

**Shipped (PR #675):** (1) deterministic meta-floor — capability questions
("what do you know about btd6") get a code-built answerability summary, the
roster-floor pattern extended; + the broadened #639 clause; (2) qualifier-
tolerant `find_boss` ("tier 4 elite lych") + per-tier HP grounding + the
Elite-not-in-dataset honesty note; (3) crosspath VALIDITY rules in the
guidance block (the model had denied crosspathing exists, live); (4) the
`!restart` relaunch bug — `main()` exited 0 with a restart pending, Railway's
on-failure policy never relaunched; pending restart now exits 42, startup
crash exits 1 (also fell through to 0 before). 12 tests pin the exact live
phrasings. Checklist gained **Step 0: verify the build** + live-walk deltas
(Tier 1.1 round-cash **PASSED**).

**Context delta (continuation 2):**

- **Needed but not pointed to:** nothing in docs says *where the prod bot
  runs or how it deploys* (Railway, auto-deploy-on-main-merge, on-failure
  restart policy). Diagnosing both the stale deploy and the !restart bug
  required inferring it from a screenshot + log. → Routed: a short
  "production deployment" note belongs in the journal Runbook or a folio.
- **Discovered by hand:** the faithfulness floor's refusal is the answer of
  last resort for EVERY healthy-but-ungroundable BTD6 turn — meta-questions
  included; the answer-guidance block taught crosspath *notation* but not
  *validity*; `main()` had no exit-code contract at all.
- **Decisions made alone:** meta detection anchored on a btd6/bloons token
  (precision over recall — general "what can you do" stays with the catalog
  tool); RESTART_EXIT_CODE=42 (≠0 done, ≠1 crash); Elite HP honesty note
  rather than silently applying the user's multiplier.
- **Weak point:** the §7.5 composition family ("cash left after buying
  N towers") now has live acceptance cases but still no workflow — expect
  honest partials there until §7.5 ships.

---

## Continuation 3 (same session): the 55.0 mystery corrected + the data lane fixed (PR #676)

**Correction of continuation 2:** the "prod deploy predated the burst" claim
was WRONG — the maintainer challenged it ("my bot auto-deploys every merge")
and the Railway log proves a new container (the #674 auto-deploy) served a
"(55.0)" answer at 18:36. The stale thing was the **data, not the code**:
prod runs `BTD6_DATA_BACKEND=postgres`, fixtures come from `btd6_data_blobs`
(warmed at boot), and **merged data PRs never refresh that table**. The
maintainer's own `!btd6ops seed-data` (18:43) is what flipped 55.0 → 55.1;
the restart they correctly tried next died on the exit-0 bug. Lesson
recorded: when a hypothesis contradicts a platform behavior the owner
states, re-derive from the logs before asserting — the "(55.0) on the NEW
container" line was sitting in the evidence the whole time.

**Shipped (PR #676):** seed-data is now **self-applying** (re-warm + cache
drop — one command, immediate effect); **drift surfacing** (boot-log warning
+ `!btd6 status` ⚠️ Data-drift field when the store lags the bundled files);
seed-embed copy rewritten; checklist Step 0 corrected to the data-lane
truth; prod-operations note added to the BTD6 folio + journal Runbook;
**Q-0077** (auto-seed-on-boot posture) routed. Plus the post-restart
screenshots' one holdout: "What **csn** you tell me about btd6" (typo) slips
the meta-detector's `can you tell` shape — the tell/ask shapes are now
auxiliary-verb-free and target-anchored ("ask **you/this bot**", so "ask a
friend" stays out), pinned by the typo'd phrasing in the test matrix.

**Post-restart screenshot verdicts (after seed + manual redeploy):** Navarch
income ✅ (the #662 fix live-verified: $3,200/round + Trade Empire lines) ·
crossbow-master cumulative cost ✅ · **the remaining-cash composition ✅**
($650 + $37,660 − $21,500 = $16,810 — composed correctly without the §7.5
workflow; better than predicted) · capability meta-question ❌ (the typo +
possible pre-#675 timing) → the floor now catches it deterministically.

---

## Continuation 4 (same session): Help editor PR A built + live-verified (PR #677)

With the eval steady (4 PRs merged) the session resumed the queue item the
screenshots had interrupted — **plan §5 PR A**, same-day execution of the
morning's own plan doc:

- `views/help/editor.py` — home (override counts) → kind picker (paginated,
  Q-0058 labels: custom label + default · stable key, 🙈 prefix) → per-entity
  editor (hide-toggle-to-inherit · rename/re-describe modals · per-field +
  entity + guild reset w/ confirm). Every action = exactly ONE
  `set_overlay_fields`/`reset_guild_overlay` call (AST-pinned: no `utils.db`
  import); admin floor re-checked per interaction (access_map pattern);
  modals never deferred first.
- Entry points: staff-hub `✏️ Help editor` (row 2, beside 👁 Help Preview —
  edit + verify together) + `cogs/help/schemas.py` "Help appearance"
  `DomainPanelSpec` (capability `help.settings.configure`; actionable
  taxonomy 12 → 13; domain-panel invariant updated {cleanup} → {cleanup,
  help}). Bonus generic fix: the settings subsystem page now renders
  declared **Domain configuration** destinations (cleanup's group no longer
  lands on bare "*none declared*").
- 12 new tests + hub custom_id pin; CI mirror green; arch 0 errors; clean
  boot (catalogue findings 53 → 52 — the schema resolved a schema-less
  finding); **live Postgres round-trip through the real callbacks**: hide →
  row · rename via modal submit · Help Preview shows the overlay-hidden
  bucket · reset-all → 0 rows.
- Bonus live proof: the crashed first boot attempt (Postgres down) exited
  **code 1** — the #675 exit-code contract observed working.

**Open after this:** the editor's **PR B** (Q-0059 Home embed builder — plan
§4.3) · Batch 9 RS05/RS10 · setup PR4 planning · §7.5 (eval Tier-1 sign-off
still the gate; three of its four live questions already passed).
