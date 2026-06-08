# 2026-06-08 — Adaptive Setup/Access/Routine Platform: pre-Codex clarification session

No code shipped this session. Pure Q-capture and owner-decision work before sending the
Adaptive Setup, Access, Preset, and Routine Platform concept to Codex for planning.

## What happened

The maintainer shared a large planning brief (Adaptive Setup, Access, Preset, and Routine
Platform) and asked for any clarifying questions before forwarding it to Codex.

Two rounds of questions were asked and answered:

**Round 1 — Planning structure and product direction (Q-0017–Q-0020)**
- Q-0017: One comprehensive planning doc in `docs/planning/` (not separate docs per concept).
- Q-0018: Guild Feature Profiles starter set — let Codex revise against subsystem registry
  (6 proposed profiles are a starting suggestion, not fixed; BTD6-Focused may be deferred).
- Q-0019: Routine Engine default safety posture — progressive (low-risk auto-applies,
  medium/high-risk creates approval draft). Risk classification table required in the plan.
- Q-0020: Personal Setup Wizard — full Phase 5 spec depth, including data model, privacy
  layering, /my-setup, /my-preferences, timezone, help ordering, DM settings, account links.

**Round 2 — Architecture decisions from repo inspection (Q-0021–Q-0024)**
Discovered by actually reading the repo before asking:

- Q-0021: Routine Engine framing — extend the **existing** `automation_scheduler` /
  `automation_executor` / `automation_registry` (already has triggers: scheduled_time,
  interval, member_join, setup_readiness_below, binding_missing; and actions: send_message,
  assign_role, notify_owner, bind_channel). The brief's "Low readiness" rating was wrong.
  Gap is config-mutation action kinds + a condition model. Not a new engine.
- Q-0022: Naming — **"Guild Feature Profile"** is canonical for server config bundles.
  **"Preset"** stays reserved for existing `ServerPreset` automation templates. Never use
  "preset" in new code symbols or UI strings for the new concept.
- Q-0023: Help Preview access — **staff and admins only**. Not self-serve for regular users.
- Q-0024: Access Map Phase 2 scope — **read-only diagnostic** in Phase 2. Editing surface
  (generating setup draft operations from the map) belongs in Phase 3.

**Round 3 — Friction log from PR14 session (Q-0025–Q-0027)**
The maintainer shared a screenshot of genuine frictions hit in the PR14 session:

- Q-0025: Subsystem/hub addition — **build `scripts/new_subsystem.py`** scaffold script
  (not just a doc checklist). Decided, not yet implemented. Added to `current-state.md`.
- Q-0026: `cog_name_to_subsystem` CamelCase fix — **fix the function** to do proper
  CamelCase→snake_case; rename `"servermanagement"` → `"server_management"` everywhere.
  Medium-risk refactor. Added to `current-state.md`. Not yet implemented.
- Q-0027: Session prompt contradictions — **maintainer will update ChatGPT template**
  to remove the branch-lock line and the PR-on-request line. No repo change needed;
  binding docs already win.

## Files changed

- `docs/owner/maintainer-question-router.md` — Q-0017 through Q-0027 (11 new entries)
- `docs/current-state.md` — new "Near-term technical debt" section (Q-0025, Q-0026)

## Key takeaways for the next session

1. **The Codex prompt needs a Q-decisions addendum** before being sent. The original
   prompt doesn't include Q-0017–Q-0024; without them, Codex will plan against wrong
   assumptions (wrong readiness rating for routines, wrong naming for profiles, wrong
   Phase 2 scope for Access Map, wrong Help Preview access model).

2. **`cog_name_to_subsystem` is a concrete near-term task** (Q-0026) — fix + rename
   before the next multi-word subsystem is added.

3. **`new_subsystem.py` scaffold is decided** (Q-0025) — good candidate for a
   focused tooling session.

4. **The Routine Engine is not starting from scratch** — the existing automation
   system handles scheduling and content actions. Phase 4 adds config-mutation
   action kinds and a condition model on top.

## Context delta

- **Needed but not pointed to:** that the repo already has a live automation scheduler
  with trigger/action kinds (missed by the brief's "Low readiness" rating). This is the
  most consequential discovery of the session.
- **Pointed to but didn't need:** nothing.
- **Discovered by hand:** `ServerPreset` in `automation_templates.py` means "automation
  rule template," not "server configuration profile" — the naming collision would have
  caused real implementation confusion without Q-0022.

## Maintainer action item

Update the ChatGPT session prompt template (Q-0027):
1. Remove/replace the "develop only on branch X / never push elsewhere" line.
2. Remove/replace the "don't open a PR unless explicitly asked" line.
